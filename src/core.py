"""
Part of MMM. Contains core classes and functions.
"""

import os
import queue
import requests
import plyvel as leveldb
import shutil
import subprocess
import sys
import threading
import time
import winreg
from datetime import datetime
from glob import glob
from typing import Union

import msgpack

from main import NUMBER_OF_THREADS, MainApp, qtw, qtc


# Create class to copy stdout to log file ############################
class StdoutPipe:
    def __init__(self, app: MainApp, tag="stdout", encoding="utf8"):
        self.app = app
        self.tag = tag
        self.encoding = encoding
        self.file = open(self.app.log_path, "a")
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
    def __del__(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        self.file.close()
    def write(self, string):
        if string not in self.app.protocol:
            self.app.protocol += string
            try:
                self.file.write(string)
            except Exception as ex:
                print(f"Logging error occured: {str(ex)}")
        try:
            self.stdout.write(string)
        except AttributeError:
            pass
    def flush(self):
        self.file.flush()


# Create class for modding instance ##################################
class ModInstance:
    """
    General class for mod manager instances.
    """

    def __init__(self, app: MainApp, instance: dict):
        self.app = app
        self.instance = instance
        
        self.set_instance_data(self.instance)
    
    def __repr__(self):
        return "ModInstance"
    
    def set_instance_data(self, instance: dict):
        self.instance = instance
        self.name = instance.get('name', "")
        self.mods = instance.get('mods', [])
        self.paths = instance.get('paths', {})
        self.metadata = {} # full modname: {name, modid, fileid, version}
        self.loadorder = []
        self.modnames = [] # list of parsed modnames to avoid duplicates
        self.size = 0

    def get_loadorder(self, psignal: qtc.Signal=None):
        """
        Returns loadorder.
        """

        return self.mods
    
    def create_instance(self):
        """
        Create instance. Steps depend on mod manager.
        """

        return
    
    def get_size(self):
        """
        Calculates total size in bytes of instance files.
        """

        return self.size
    
    def get_mod_metadata(self, modname: str):
        """
        Gets mod metadata (name, version, modid, fileid) and returns it.
        """
        return {}
    
    def import_mod(self, folder: str, psignal: qtc.Signal=None):
        return

    def get_instances(self):
        """
        Gets list of instances and returns it.
        """

        return []


# Create class for Vortex commandline interface ######################
class VortexDatabase:
    """
    Class for Vortex level database. Use only one instance at a time!
    """
    
    def __init__(self, app: MainApp):
        self.app = app
        self.data = {}
        self.appdir = os.path.join(os.getenv('APPDATA'), 'Vortex')
        self.db_path = os.path.join(self.appdir, 'state.v2')
        
        # Delete old backup
        backup_path = f"{self.db_path}.mmm_backup"
        if os.path.isdir(backup_path):
            shutil.rmtree(backup_path)
        # Create new backup
        shutil.copytree(self.db_path, f"{self.db_path}.mmm_backup")

        # Initialize database
        self.db = leveldb.DB(self.db_path)
    
    def open_db(self):
        if self.db.closed:
            self.db = leveldb.DB(self.db_path)
    
    def close_db(self):
        if not self.db.closed:
            self.db.close()
    
    def load_db(self):
        self.app.log.debug(f"Loading Vortex database...")

        self.open_db()
        lines = []
        for keys, value in self.db:
            keys, value = keys.decode(), value.decode()
            lines.append(f"{keys} = {value}")
        self.close_db()

        data = self.parse_string_to_dict(lines)
        self.data = data

        self.app.log.debug(f"Loaded Vortex database.")
        return data
    
    def save_db(self):
        self.app.log.debug(f"Saving Vortex database...")

        lines = self.convert_nested_dict_to_text(self.data)

        self.open_db()
        with self.db.write_patch() as batch:
            for line in lines:
                path, line = line.split(" = ", 1)
                path, line = path.encode(), line.encode()
                batch.put(path, line)
        self.close_db()

        self.app.log.debug(f"Saved to database.")
    
    @staticmethod
    def convert_nested_dict_to_text(nested_dict: dict) -> str:
        """
        This function takes a nested dictionary and converts it back to a string of text in the format of
        'key1.subkey1.subsubkey1.subsubsubkey1 = subsubsubvalue1'. Each key-value pair is represented on a separate line,
        and the keys are separated by dots to indicate nesting.

        Parameters:
            nested_dict: dict (nested dictionary)
        Returns:
            str (string of text in the specified format.)
        """

        def flatten_dict(d: dict, prefix=""):
            lines = []
            for key, value in d.items():
                full_key = f"{prefix}###{key}" if prefix else key
                if isinstance(value, dict):
                    lines.extend(flatten_dict(value, prefix=full_key))
                else:
                    lines.append(f"{full_key} = {value}")
            return lines

        flat_dict = flatten_dict(nested_dict)
        return flat_dict
    
    @staticmethod
    def parse_string_to_dict(text: Union[str, list]):
        """
        This method takes a string of text in the
        format of 'key1.subkey1.subsubkey1.subsubsubkey1 = subsubsubvalue1'
        and converts it into a nested dictionary.
        The text must have a key-value pair on each line and
        each key must be separated by dots to indicate nesting.
        Empty lines are ignored.

        Parameters:
            text: str or list (text which lines are in specified format above)
        
        Returns:
            result: dict (nested dictionary)
        """

        result = {}

        if isinstance(text, str):
            lines = text.split("\n")
        else:
            lines = text
        
        for line in lines:
            try:
                line = line.strip()
                if not line:
                    continue
                keys, value = line.split("=", 1)
                keys = keys.strip().split("###")
                current = result
                for key in keys[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                try:
                    value = eval(value.strip())
                except:
                    value = value.strip()
                current[keys[-1]] = value
            except ValueError:
                print(f"Failed to process line: {line:20}...")
                continue
        return result


# Create class for Vortex stagefile ##################################
class StageFile:
    def __init__(self, path: str):
        self.path = path
        self.dir = os.path.dirname(path)
        self.data = {}
        self.loadorder = []
        self.modfiles = {} # mod: files
        self.all_modfiles = {} # mod: all files (overwritten files, too)
    
    def parse_file(self):
        with open(self.path, 'rb') as file:
            data = msgpack.load(file)
        
        self.data = data
    
    def get_modlist(self):
        loadorder = []
        modfiles = {}
        for file in self.data['files']:
            mod = file['source']
            if mod not in loadorder:
                loadorder.append(mod)
            if mod not in modfiles.keys():
                modfiles[mod] = [file['relPath'].lower()]
            else:
                modfiles[mod].append(file['relPath'].lower())
        
        self.loadorder = loadorder
        self.modfiles = modfiles
    
    def get_mod_by_filename(self, filename: str):
        """
        Returns modname as string or None if nothing is found.
        Parameters:
            filename: relative path to file
        """

        for mod, files in self.modfiles.items():
            if filename.lower() in files:
                return mod
        else:
            print(f"File '{filename}' not found!")
        
            return None


# Create new class for Vortex instance ###############################
class VortexInstance(ModInstance):
    """
    Class for Vortex ModInstance. Inherited from ModInstance class.
    
    Uses level database instead of Vortex's deployment files.
    """

    def __init__(self, app: MainApp, instance: dict):
        super().__init__(app, instance)

        self.db = VortexDatabase(app)
        self.database = self.db.load_db()

        self.profiles = {} # profile name: id
        self.overwrites = {} # mod: [overwriting mod, overwriting mod, etc...]
        self.root_mods = [] # list of mods that must be copied directly to the game folder
    
    def __repr__(self):
        return "VortexInstance"

    def get_size(self):
        self.app.log.debug(f"Calculating size of Vortex profile...")
        
        # Calculate size of mods in staging folder
        size = 0
        for mod in self.mods:
            size += get_folder_size(os.path.join(self.paths['mods_path'], mod))

        # Add size of download folder if one is given
        if (dlpath := self.paths.get('download_path', None)) is not None:
            size += get_folder_size(dlpath)

        self.size = size
        self.app.log.debug(f"Calculation complete. Profile size: {get_size(self.size)}")
        return super().get_size()

    def set_instance_data(self, instance: dict):
        profname = instance.get('name', None)
        if profname is not None:
            profid = self.profiles[profname]

            mods = []
            for modname, modstate in self.database['persistent']['profiles'][profid]['modState'].items():
                if modstate['enabled'] == 'true':
                    mods.append(modname)
            instance['mods'] = mods
            instance['paths']['mods_path'] = self.database['settings']['mods']['installPath'][self.app.game.lower()]
            instance['paths']['instance_path'] = instance['paths']['mods_path']
            profpath = os.path.join(os.getenv('APPDATA'), 'Vortex', self.app.game.lower(), 'profiles', str(profid))
            instance['paths']['plugin_files'] = [
                os.path.join(profpath, 'loadorder.txt'),
                os.path.join(profpath, 'plugins.txt')
            ]
            
        super().set_instance_data(instance)
    
    def sort_loadorder(self, psignal: qtc.Signal=None):
        self.app.log.debug("Scanning mods...")

        new_loadorder = self.mods.copy()
        new_loadorder.sort()
        
        for mod in self.mods.copy():
            modtype = self.database['persistent']['mods'][self.app.game.lower()][mod]['type'].strip()
            # Skip mod if it is a root mod
            if modtype and modtype != 'collection':
                print(f"{mod}: {modtype}")
                self.root_mods.append(mod)
                self.mods.remove(mod)
                new_loadorder.remove(mod)
                continue
            # Ignore collection bundle
            elif modtype == 'collection':
                self.mods.remove(mod)
                new_loadorder.remove(mod)
                continue
            # Get rules of mod
            rules = self.database['persistent']['mods'][self.app.game.lower()][mod].get('rules', [])

            for rule in rules:
                if 'id' in rule['reference']:
                    ref_mod = rule['reference']['id'].strip()
                elif 'fileExpression' in rule['reference']:
                    ref_mod = rule['reference']['fileExpression'].strip()
                # Skip mod if reference mod does not exist
                else:
                    continue
                if ref_mod in self.mods:
                    if rule['type'] == 'before':
                        overwrites = self.overwrites.get(mod, [])
                        overwriting_mod = ref_mod
                        if overwriting_mod in self.mods:
                            overwrites.append(overwriting_mod)
                            self.overwrites[mod] = overwrites
                    elif rule['type'] == 'after':
                        overwriting_mod = ref_mod
                        if overwriting_mod in self.mods:
                            overwrites = self.overwrites.get(overwriting_mod, [])
                            overwrites.append(mod)
                            self.overwrites[overwriting_mod] = overwrites
                    elif rule['type'] == 'requires':
                        continue
                    else:
                        print(f"Mod: {mod}")
                        print(f"Rule type: {rule['type']}")
                        print(f"Rule reference attrs: {rule['reference'].keys()}")
                        print(f"Rule reference: {rule['reference']}")
                        raise ValueError(f"Invalid rule type '{rule['type']}'!")
            
            overwriting_mods = self.overwrites.get(mod, [])
            
            if overwriting_mods:
                #_overwriting_mods = '\n    '.join(overwriting_mods)
                #overwrites = ""
                #overwrites += f"\nMod: {mod}\nOverwritten by:\n    {_overwriting_mods}\n{'-'*100}"
                #print(overwrites)

                self.app.log.debug(f"Sorting mod '{mod}'...")

                old_index = index = new_loadorder.index(mod)

                # get smallest index of all overwriting mods
                index = min([new_loadorder.index(overwriting_mod) for overwriting_mod in overwriting_mods])
                self.app.log.debug(f"Current index: {old_index} | Minimal index of overwriting mods: {index}")

                if old_index > index:
                    new_loadorder.insert(index, new_loadorder.pop(old_index))
                    self.app.log.debug(f"Moved mod '{mod}' from index {old_index} to {index}.")
        
        new_loadorder.reverse()

        # Replace Vortex's full mod names by <modname> - <filename>
        final_loadorder = []
        for mod in new_loadorder:
            modname = self.get_mod_metadata(mod)['name']
            final_loadorder.append(modname)

        self.app.log.info("Created loadorder from Vortex rules.")

        return final_loadorder
    
    def get_mod_metadata(self, modname: str):
        if (metadata := self.metadata.get(modname, None)) is None:
            attrs = self.database['persistent']['mods'][self.app.game.lower()][modname]['attributes']
            #print(modname)
            modid = attrs.get('modId', 0)
            fileid = attrs.get('fileId', 0)
            version = attrs['version']
            if 'customFileName' in attrs:
                name = attrs['customFileName'].strip("-").strip(".").strip()
            elif 'name' in attrs:
                name = attrs['name'].strip("-").strip(".").strip()
            else:
                name = modname.strip("-").strip(".").strip()
            if len(name) > 75:
                if str(modid) in modname:
                    name = modname.split(str(modid))[0].removesuffix("-").strip()
                else:
                    name = modname.strip("-").strip(".").strip()
            metadata = {
                'name': name,
                'modid': modid,
                'fileid': fileid,
                'version': version,
            }
            self.modnames.append(metadata['name'])
            self.metadata[modname] = metadata

        return metadata
    
    def get_loadorder(self, psignal: qtc.Signal=None):
        starttime = time.time()

        self.loadorder = self.sort_loadorder(psignal)
    
        #loadorder.reverse()
        #self.check_loadorder(self.stagefile, loadorder)
        #loadorder.reverse()

        self.app.log.debug(f"Sorting took {(time.time() - starttime):.2f} second(s). ({((time.time() - starttime) / 60):.2f} minute(s))")

        return self.loadorder

    def get_instances(self):
        self.app.log.debug(f"Loading profiles from database...")

        for profid, profdata in self.database['persistent']['profiles'].items():
            if (profdata['gameId'] == self.app.game.lower()) and ('modState' in profdata.keys()):
                profname = profdata['name']
                self.profiles[profname] = profid
        
        self.app.log.debug(f"Loaded {len(self.profiles)} profile(s) from database.")
        return list(self.profiles.keys())


# Create class for MO2 instance ######################################
class MO2Instance(ModInstance):
    """
    Class for ModOrganizer ModInstance. Inherited from ModInstance class.
    """

    def __repr__(self):
        return "MO2Instance"

    def create_instance(self):
        self.app.log.info(f"Creating MO2 instance '{self.name}' in '{self.paths['instance_path']}'...")

        # Create directories
        self.app.log.debug(f"Creating directories...")
        appdata_path = os.path.join(os.getenv('LOCALAPPDATA'), 'ModOrganizer', self.name)
        os.makedirs(appdata_path) # raise exception if instance does already exist
        os.makedirs(self.paths['instance_path'], exist_ok=True)
        os.makedirs(self.paths['download_path'], exist_ok=True)
        os.makedirs(self.paths['mods_path'], exist_ok=True)
        os.makedirs(self.paths['profiles_path'], exist_ok=True)
        os.makedirs(os.path.join(self.paths['profiles_path'], 'Default'), exist_ok=True)
        os.makedirs(self.paths['overwrite_path'], exist_ok=True)
        self.app.log.debug(f"Created instance folders.")

        # Create ini file with instance paths
        instance_path = self.paths['instance_path'].replace('\\', '/')
        download_path = self.paths['download_path'].replace('\\', '/')
        game_path = self.app.game_instance.get_install_dir().replace('\\', '/')
        with open(os.path.join(appdata_path, 'ModOrganizer.ini'), 'w') as inifile:
            ini = f"""
[General]
gameName={self.app.game_instance.name}
selected_profile=@ByteArray(Default)
gamePath={game_path}
version=2.4.4
first_start=true

[Settings]
base_directory={instance_path}
download_directory={download_path}
style=Paper Dark.qss

[customExecutables]
size=1
1\\arguments=
1\\binary={game_path}/skse64_loader.exe
1\\hide=false
1\\ownicon=true
1\\steamAppID=
1\\title=SKSE
1\\toolbar=false
1\\workingDirectory={game_path}

[PluginPersistance]
Python%20Proxy\\tryInit=false

[recentDirectories]
size=0
""".strip()
            inifile.write(ini)
        self.app.log.debug(f"Created 'ModOrganizer.ini'.")

        # Create profile files
        prof_path = os.path.join(self.paths['profiles_path'], 'Default')
        # Create initweaks.ini
        with open(os.path.join(prof_path, 'initweaks.ini'), 'w') as inifile:
            inifile.write("""[Archive]\nbInvalidateOlderFiles=1""".strip())
        self.app.log.debug("Created 'initweaks.ini'.")

        # Create modlist.txt
        with open(os.path.join(prof_path, 'modlist.txt'), 'w') as file:
            mods = ""
            for mod in self.loadorder:
                mods += "\n+" + os.path.basename(mod)
            mods = mods.strip()
            file.write(f"# This file was automatically generated by Mod Organizer.\n{mods}")
        self.app.log.debug("Created 'modlist.txt'.")

        # Copy ini files from game's ini folder
        ini_path = self.app.game_instance.inidir
        ini_files = self.app.game_instance.inifiles
        for ini_file in ini_files:
            shutil.copy(os.path.join(ini_path, ini_file), os.path.join(prof_path, ini_file.lower()))
        self.app.log.debug("Copied ini files from game's ini folder.")

        # Copy loadorder.txt and plugins.txt from source instance
        for plugin_file in self.app.src_modinstance.paths.get('plugin_files', []):
            shutil.copy(plugin_file, os.path.join(prof_path, os.path.basename(plugin_file)))
        self.app.log.debug("Copied 'loadorder.txt' and 'plugins.txt' from source instance.")

        self.app.log.info(f"Created MO2 instance.")
    
    def import_mod(self, folder: str, psignal: qtc.Signal=None):
        # Get metadata
        metadata = self.metadata[os.path.basename(folder)]
        modpath = os.path.join(self.paths['mods_path'], metadata['name'])

        # Copy folder if a migrate mode is 'copy'
        if self.app.mode == 'copy':
            shutil.copytree(f"\\\\?\\{folder}", f"\\\\?\\{modpath}")
        # Create hardlinks otherwise
        else:
            files = create_folder_list(folder, lower=False)
            for c, file in enumerate(files):
                if psignal is not None:
                    _string = self.app.lang['linking_mod'].replace("[MOD]", f"'{metadata['name']}'")
                    progress = {
                        'show2': True,
                        'text2': f"{_string} ({c}/{len(files)})",
                        'value2': c,
                        'max2': len(files),
                    }
                    psignal.emit(progress)
                os.makedirs(f"\\\\?\\{os.path.join(modpath, os.path.dirname(file))}", exist_ok=True)
                os.link(f"\\\\?\\{os.path.join(folder, file)}", f"\\\\?\\{os.path.join(modpath, file)}")

        # Write metadata to meta.ini
        with open(os.path.join(modpath, 'meta.ini'), 'w') as metafile:
            metafile.write(f"""
[General]
gameName={self.app.game}
modid={metadata['modid']}
version={metadata['version']}
repository=Nexus

[installedFiles]
1\\modid={metadata['modid']}
1\\fileid={metadata['fileid']}
""".strip())
    
    def get_mod_metadata(self, modname: str):
        metadata = {}
        metafile = os.path.join(self.paths['mods_path'], modname, 'meta.ini')
        if os.path.isfile(metafile):
            with open(metafile, 'rb') as file:
                pass
        
        return metadata
    
    def get_size(self):
        self.app.log.debug(f"Calculating size of MO2 instance...")

        # WORK IN PROGRESS!!
        # Calculate size for each instance subfolder
        # because they can be at different locations

        self.app.log.debug(f"Calculation complete. Instance size: {self.size}")

        return super().get_size()

    def get_instances(self):
        instances_path = os.path.join(os.getenv('LOCALAPPDATA'), 'ModOrganizer')
        instances = []
        # Check if path exists
        if os.path.isdir(instances_path):
            # Filter for folders and ignore files
            instances = [obj for obj in os.listdir(instances_path) if os.path.isdir(os.path.join(instances_path, obj))]
            self.app.log.info(f"Found {len(instances)} instance(s).")
        # Show error message otherwise
        else:
            self.app.log.error("Failed to load instances from ModOrganizer: Found no instances.")
        
        # Return list with found instances
        return instances


# Define function to get latest version from version file in repo ####
def get_latest_version():
    try:
        url = "https://raw.githubusercontent.com/Cutleast/Mod-Manager-Migrator/main/version"
        #url = "https://raw.githubusercontent.com/Cutleast/Test/main/version" # test url
        response = requests.get(url)
        if response.status_code == 200:
            new_version = response.content.decode(encoding='utf8', errors='ignore').strip()
            new_version = float(new_version)
            return new_version
        else:
            raise Exception(f"Status code: {response.status_code}")
    except Exception:
        return 0.0

# Read folder and save files with relative paths to list #############
def create_folder_list(folder, lower=True):
    """
    Creates a list with all files with relative paths to <folder> and returns it.

    Lowers filenames if <lower> is True.
    """
    files = []

    for root, dirs, _files in os.walk(folder):
        for f in _files:
            blacklist = []
            with open('.\\data\\blacklist', 'r') as file:
                for line in file.readlines():
                    if line.strip():
                        blacklist.append(line)
            if f not in blacklist: # check if in blacklist
                path = os.path.join(root, f)
                path = path.removeprefix(f"{folder}\\")
                if lower:
                    path = path.lower()
                files.append(path)

    return files

# Define function to round bytes #####################################
def get_size(bytes: Union[int, float], suffix="B"):
    """
    Scale bytes to their proper format; for e.g:
    1253656 => '1.20MB'
    1253656678 => '1.17GB'
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P", "H"]:
        if bytes < factor:
            if f"{bytes:.2f}".split(".")[1] == "00":
                return f"{int(bytes)}{unit}{suffix}"
            else:
                return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor
    else:
        return str(bytes)

# Define function to calculate folder size ###########################
def get_folder_size(start_path: str):
    total_size = 0
    i = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                try:
                    total_size += os.path.getsize(fp)
                except Exception as ex:
                    pass
                i += 1
                #print(f"{f'''Calculating size of '{start_path}'... ({get_size(total_size)})''':100}", end='\r')
    return total_size

# Define function to move windows to center of parent ################
def center(widget: qtw.QWidget, referent: qtw.QWidget=None):
    """
    Moves <widget> to center of its parent.
    
    Parameters:
        widget: QWidget (widget to move)
        referent: QWidget (widget reference for center coords; use widget.parent() if None)
    """

    size = widget.size()
    w = size.width()
    h = size.height()
    if referent is None:
        rsize = widget.parent().size()
    else:
        rsize = referent.size()
    rw = rsize.width()
    rh = rsize.height()
    x = int((rw / 2) - (w / 2))
    y = int((rh / 2) - (h / 2))
    widget.move(x, y)

# Define function to get difference between two times ################
def get_diff(start_time, end_time, format="%H:%M:%S"):
    """Returns difference between 'start_time' and 'end_time' in 'format'."""
    tdelta = (datetime.strptime(end_time, format) - datetime.strptime(start_time, format))
    return tdelta

