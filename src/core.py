"""
Part of MMM. Contains core classes and functions
"""

import os
import queue
import shutil
import sys
import threading
import time
import winreg
from datetime import datetime
from glob import glob

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
        self.name = instance.get('name', "")
        self.mods = instance.get('mods', [])
        self.paths = instance.get('paths', {})
        self.metadata = {} # full modname: {name, modid, fileid, version}
        self.loadorder = []
        self.size = 0
    
    def __repr__(self):
        return "ModInstance"
    
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


# Create class for Vortex instance ###################################
class VortexInstance(ModInstance):
    """
    General class for mod manager instances.
    """

    def __init__(self, app: MainApp, instance: dict):
        super().__init__(app, instance)

        self.stagefile = StageFile(self.paths['stagefile'])
        self.stagefile.parse_file()
        self.stagefile.get_modlist()
        self.mods = self.stagefile.modfiles

        # Scan for other deployment files
        self.stagefiles = [] # List of other stagefiles
        for file in glob(os.path.join(self.stagefile.dir, 'vortex.deployment.*.msgpack')):
            if os.path.isfile(file) and (file != self.stagefile):
                stagefile = StageFile(file)
                stagefile.parse_file()
                stagefile.get_modlist()
                self.stagefiles.append(stagefile)
                self.app.log.debug(f"Found stagefile: {os.path.basename(stagefile.path)}")
    
    def __repr__(self):
        return "VortexInstance"
    
    @staticmethod
    def get_mod_metadata(modname: str):
        metadata = {}
        data = [int(split) for split in modname.split("-") if split.isnumeric()]
        try:
            modid = data.pop(0)
            fileid = data.pop(-1)
            data = [str(d) for d in data]
            version = ".".join(data)
            name = modname.split(str(modid))[0].strip("-")
            metadata = {
                'name': name,
                'modid': modid,
                'fileid': fileid,
                'version': version,
            }
        except IndexError:
            print(f"Failed to get metadata from '{modname}': Insufficient data to parse!")
            metadata = {
                'name': modname,
                'modid': 0,
                'fileid': 0,
                'version': ""
            }

        return metadata
    
    def sort_loadorder(self, stagefile: StageFile, psignal: qtc.Signal=None):
        self.app.log.debug("Scanning mods...")

        new_loadorder = stagefile.loadorder.copy()
        overwrites = ""
        for c, mod in enumerate(stagefile.loadorder):
            self.app.log.debug(f"Scanning mod '{mod}'... ({c}/{len(stagefile.loadorder)})")
            if psignal is not None:
                progress = {
                    'value': c,
                    'max': len(stagefile.loadorder),
                    'text': f"{self.app.lang['sorting_loadorder']} ({c}/{len(stagefile.loadorder)})",
                    'show2': True,
                    'value2': 0,
                    'max2': 0,
                    'text2': mod
                }
                psignal.emit(progress)
            overwriting_mods = []
            overwritten_files = []
            
            modfiles = stagefile.all_modfiles[mod]

            # skip mod if all files get deployed
            overwritten_count = len(modfiles) - len(stagefile.modfiles[mod])
            if not overwritten_count:
                self.app.log.debug(f"Skipped mod: all files get deployed.")
                continue
            else:
                self.app.log.debug(f"Overwritten files: {overwritten_count} (Total: {len(modfiles)})")

            q = queue.Queue()
            for file in modfiles:
                q.put(file)

            def thread():
                while len(overwritten_files) < overwritten_count:
                    file = q.get()
                    q.task_done()
                    overwriting_mod = stagefile.get_mod_by_filename(file)
                    if (overwriting_mod is not None) and (overwriting_mod != mod) and (overwriting_mod not in overwriting_mods):
                        overwriting_mods.append(overwriting_mod)
                        overwritten_files.append(file)
                with q.mutex:
                    q.queue.clear()
                    q.all_tasks_done.notify_all()
                    q.unfinished_tasks = 0
            
            for t in range(NUMBER_OF_THREADS):
                worker = threading.Thread(target=thread, daemon=True, name=f"SortThread-{t+1}")
                worker.start()
            
            def pthread():
                while q.qsize():
                    if psignal:
                        progress = {
                            'value': c,
                            'max': len(stagefile.loadorder),
                            'text': f"{self.app.lang['sorting_loadorder']} ({c}/{len(stagefile.loadorder)})",
                            'show2': True,
                            'value2': int(len(modfiles) - q.unfinished_tasks),
                            'max2': len(modfiles),
                            'text2': f"{mod} ({len(modfiles) - q.unfinished_tasks}/{len(modfiles)})"
                        }
                        psignal.emit(progress)
                        time.sleep(.5)
                    #print(f"{q.unfinished_tasks = } ({((len(modfiles) - q.unfinished_tasks) / len(modfiles))*100:.3f}%) (Found: {len(overwritten_files)}/{overwritten_count})                           ", end='\r')
            pthread()
            
            q.join()
            
            if overwriting_mods:
                _overwriting_mods = '\n    '.join(overwriting_mods)
                overwrites += f"\nMod: {mod}\nOverwritten by:\n    {_overwriting_mods}\n{'-'*100}"

                self.app.log.debug(f"Sorting mod '{mod}'...")

                old_index = index = new_loadorder.index(mod)

                # get smallest index of all overwriting mods
                index = min([new_loadorder.index(overwriting_mod) for overwriting_mod in overwriting_mods])
                self.app.log.debug(f"Current index: {old_index} | Minimal index of overwriting mods: {index}")

                if old_index > index:
                    new_loadorder.insert(index, new_loadorder.pop(old_index))
                    self.app.log.debug(f"Moved mod '{mod}' from index {old_index} to {index}.")
        
        if psignal is not None:
            psignal.emit({
                'text': self.app.lang['sorting_loadorder'],
                'value': 0,
                'max': 0})

        stagefile_files = {}
        for file in stagefile.data['files']:
            stagefile_files[file['relPath'].lower()] = file['source']
        while different_files := self.check_loadorder(stagefile, new_loadorder):
            loadorder_files = {}
            for c, mod in enumerate(new_loadorder):
                files = stagefile.all_modfiles[mod]
                for file in files:
                    loadorder_files[file.lower()] = mod

            for file in different_files:
                mod = loadorder_files[file]
                old_index = new_loadorder.index(mod)
                new_index = new_loadorder.index(stagefile_files[file])
                if old_index > new_index:
                    new_loadorder.insert(new_index, new_loadorder.pop(old_index))
                    self.app.log.debug(f"Moved mod '{mod}' from index {old_index} to {new_index}.")
        
        new_loadorder.reverse()

        self.app.log.info("Created loadorder from Vortex deployment file.")

        return new_loadorder

    def check_loadorder(self, stagefile: StageFile, loadorder: list):
        self.app.log.info("Checking loadorder...")
        stagefile_files = {}
        for file in stagefile.data['files']:
            stagefile_files[file['relPath'].lower()] = file['source']
        
        loadorder_files = {}
        for c, mod in enumerate(loadorder):
            files = stagefile.all_modfiles[mod]
            for file in files:
                loadorder_files[file.lower()] = mod
        
        q = queue.Queue()

        different_files = []
        for file in loadorder_files:
            q.put(file.lower())
        
        def thread():
            while True:
                file = q.get()
                mod = loadorder_files[file]
                if file not in stagefile_files:
                    self.app.log.debug(f"File: {file}")
                    self.app.log.debug(f"Loadorder mod: {mod} ({loadorder.index(mod)})")
                    self.app.log.debug(f"Stagefile mod: NOT FOUND!")
                    #self.app.log.debug("-"*50)
                    different_files.append(file)
                elif mod != stagefile_files[file]:
                    self.app.log.debug(f"File: {file}")
                    self.app.log.debug(f"Loadorder mod: {mod} ({loadorder.index(mod)})")
                    self.app.log.debug(f"Stagefile mod: {stagefile_files[file]} ({loadorder.index(stagefile_files[file])})")
                    #self.app.log.debug("-"*50)
                    different_files.append(file)
                
                q.task_done()
        
        for t in range(NUMBER_OF_THREADS):
            worker = threading.Thread(target=thread, daemon=True, name=f"CheckThread-{t+1}")
            worker.start()
        
        q.join()

        self.app.log.info(f"Found {len(different_files)} difference(s).")

        return different_files

    def get_loadorder(self, psignal: qtc.Signal=None):
        self.app.log.debug("Reading mod files...")
        starttime = time.time()
        for mod in self.stagefile.modfiles.keys():
            self.stagefile.all_modfiles[mod] = create_folder_list(os.path.join(self.stagefile.dir, mod))

        loadorder = self.sort_loadorder(self.stagefile, psignal)
    
        #loadorder.reverse()
        #self.check_loadorder(self.stagefile, loadorder)
        #loadorder.reverse()

        self.app.log.debug(f"Sorting took {(time.time() - starttime):.2f} second(s). ({((time.time() - starttime) / 60):.2f} minute(s))")

        return loadorder

    def get_size(self):
        self.app.log.debug(f"Calculating size of Vortex instance...")
        
        # Calculate size of staging folder
        size = 0
        for file in self.stagefile.data['files']:
            size += os.path.getsize(os.path.join(self.paths['staging_folder'], file['source'], file['relPath']))

        # Add size of download folder if one is given
        if self.paths['download_path']:
            size += get_folder_size(self.paths['download_path'])

        self.size = size
        self.app.log.debug(f"Calculation complete. Instance size: {get_size(self.size)}")
        return super().get_size()


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
        skyrim_path = os.path.join(get_steam_path(), 'steamapps', 'common', 'Skyrim Special Edition').replace('\\', '/')
        with open(os.path.join(appdata_path, 'ModOrganizer.ini'), 'w') as inifile:
            ini = f"""
[General]
gameName=Skyrim Special Edition
selected_profile=@ByteArray(Default)
gamePath={skyrim_path}
version=2.4.4
first_start=true

[Settings]
base_directory={instance_path}
download_directory={download_path}
style=Paper Dark.qss

[customExecutables]
size=1
1\\arguments=
1\\binary={skyrim_path}/skse64_loader.exe
1\\hide=false
1\\ownicon=true
1\\steamAppID=
1\\title=SKSE
1\\toolbar=false
1\\workingDirectory={skyrim_path}

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

        # Copy ini files from User\Documents\My Games\Skyrim Special Edition
        ini_path = self.app.doc_path
        shutil.copy(os.path.join(ini_path, 'Skyrim.ini'), os.path.join(prof_path, 'skyrim.ini'))
        shutil.copy(os.path.join(ini_path, 'SkyrimCustom.ini'), os.path.join(prof_path, 'skyrimcustom.ini'))
        shutil.copy(os.path.join(ini_path, 'SkyrimPrefs.ini'), os.path.join(prof_path, 'skyrimprefs.ini'))
        self.app.log.debug("Copied ini files from Skyrim folder.")

        # Copy loadorder.txt and plugins.txt from User\AppData\Local\Skyrim Special Edition
        if self.app.source == 'Vortex':
            path = os.path.join(os.getenv('LOCALAPPDATA'), 'Skyrim Special Edition')
            shutil.copy(os.path.join(path, 'loadorder.txt'), os.path.join(prof_path, 'loadorder.txt'))
            shutil.copy(os.path.join(path, 'plugins.txt'), os.path.join(prof_path, 'plugins.txt'))
            self.app.log.debug("Copied loadorder.txt and plugins.txt from Skyrim LocalAppData Folder.")

        self.app.log.info(f"Created MO2 instance.")
    
    def import_mod(self, folder: str, psignal: qtc.Signal=None):
        # Get metadata
        metadata = self.metadata[os.path.basename(folder)]
        modpath = os.path.join(self.paths['mods_path'], metadata['name'])

        # Copy folder if a migrate mode is 'copy'
        if self.app.mode == 'copy':
            shutil.copytree(folder, modpath)
        # Create hardlinks otherwise
        else:
            files = create_folder_list(folder, lower=False)
            for c, file in enumerate(files):
                if psignal is not None:
                    progress = {
                        'show2': True,
                        'text2': f"{metadata['name']} ({c}/{len(files)})",
                        'value2': c,
                        'max2': len(files),
                    }
                    psignal.emit(progress)
                os.makedirs(os.path.join(modpath, os.path.dirname(file)), exist_ok=True)
                os.link(os.path.join(folder, file), os.path.join(modpath, file))

        # Write metadata to meta.ini
        with open(os.path.join(modpath, 'meta.ini'), 'w') as metafile:
            metafile.write(f"""
[General]
gameName=SkyrimSE
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

    @staticmethod
    def get_instances(app: MainApp):
        """
        Create a list with all ModOrganizer instances at %LOCALAPPDATA%\\ModOrganizer
        """
        instances_path = os.path.join(os.getenv('LOCALAPPDATA'), 'ModOrganizer')
        instances = []
        # Check if path exists
        if os.path.isdir(instances_path):
            # Filter for folders and ignore files
            instances = [obj for obj in os.listdir(instances_path) if os.path.isdir(os.path.join(instances_path, obj))]
            app.log.info(f"Found {len(instances)} instance(s).")
        # Show error message otherwise
        else:
            app.log.error("Failed to load instances from ModOrganizer: Found no instances.")
        
        # Return list with found instances
        return instances


# Read folder and save files with relative paths to list #############
def create_folder_list(folder, lower=True):
    """
    Creates a list with all files with relative paths to <folder> and returns it.

    Lowers filenames if <lower> is True.
    """
    files = []

    for root, dirs, _files in os.walk(folder):
        for f in _files:
            if f not in ['.gitignore', 'meta.ini']: # check if in blacklist
                path = os.path.join(root, f)
                path = path.removeprefix(f"{folder}\\")
                if lower:
                    path = path.lower()
                files.append(path)

    return files

# Define function to round bytes #####################################
def get_size(bytes: int | float, suffix="B"):
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

# Define function to calculate folder size
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

# Define function get Steam installation path from registry ##########
def get_steam_path():
    steam_path = ""

    # Get Steam key in registry
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\WOW6432Node\\Valve\\Steam") as hkey:
        # Get installation path from key
        steam_path = os.path.normpath(winreg.QueryValueEx(hkey, "installPath")[0])
    
    return steam_path

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

# Define function to get difference between two times ######
def get_diff(start_time, end_time, format="%H:%M:%S"):
    """Returns difference between 'start_time' and 'end_time' in 'format'."""
    tdelta = (datetime.strptime(end_time, format) - datetime.strptime(start_time, format))
    return tdelta

