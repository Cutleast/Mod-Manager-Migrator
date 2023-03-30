"""
Part of MMM. Contains classes for mod manager instances.

Falls under license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import random
import string
import time
import os
import shutil
from pathlib import Path
from typing import List, Dict

from main import MainApp, qtc
from utils import (
    Mod,
    VortexDatabase,
    get_folder_size,
    create_folder_list,
    IniParser
)


# Create class for modding instance ##################################
class ModInstance:
    """
    General class for mod manager instances.
    """

    icon_name = ""

    def __init__(self, app: MainApp):
        self.app = app

        # Name of current instance/profile
        self.name: str = None

        # list of installed mods
        self.mods: List[Mod] = []

        # list of mods that must be copied
        # directly to the game folder
        self.root_mods: List[Mod] = []

        # size in bytes as integer
        self._size: int = 0

        # list of mods sorted in loadorder
        self._loadorder: List[Mod] = []

        # loadorder.txt, plugins.txt, game inis, etc.
        self.additional_files: List[Path] = []

        # path to mod folder
        self.mods_path: Path = ""

        # list of existing instances
        self.instances: List[str] = []

        # contains additional paths like download folder
        self.paths: Dict[str, Path] = {}

        # instance data like name, paths
        self.instance_data = {}

    def __repr__(self):
        return "ModInstance"

    def setup_instance(self):
        """
        Sets up instance files and configures instance.

        Takes data from self.instance_data.
        """

        return

    def load_instances(self):
        """
        Gets list of instances and returns it.
        """

        return self.instances

    def load_instance(self, name: str):
        """
        Loads instance with name <name>.
        """

        self.name = name

    def copy_mods(self, psignal: qtc.Signal=None):
        """
        Copies mods from source instance to destination instance.
        
        Gets called by destination instance.
        """

        return

    def copy_files(self, psignal: qtc.Signal=None):
        """
        Copies additional files from source instance
        to destination instance.

        Gets called by destination instance.
        """

        return

    @property
    def loadorder(self):
        """
        Gets sorted loadorder.
        """

        if not self._loadorder:
            self._loadorder = self.mods.copy()
            self._loadorder.sort(
                key=lambda mod: mod.name
            )
        return self._loadorder

    @loadorder.setter
    def loadorder(self, loadorder: list, psignal: qtc.Signal=None):
        """
        Sets loadorder.
        """

        self._loadorder = loadorder

    @property
    def size(self):
        """
        Calculates total size of mods. Returns it in bytes as integer.
        """

        self._size = sum([mod.size for mod in self.loadorder])

        return self._size


# Create class for Vortex instance ###################################
class VortexInstance(ModInstance):
    """
    Class for Vortex ModInstance. Inherited from ModInstance class.
    """

    icon_name = "Vortex.svg"

    def __init__(self, app: MainApp):
        super().__init__(app)

        # Initialize Vortex specific attributes
        self.db = VortexDatabase(app)
        self.database = self.db.load_db()
        self.profiles: Dict[str, str] = {}

        # Files and overwrites
        self.overwrites: Dict[Mod, List[Mod]] = {} # mod: [overwriting mod, overwriting mod, etc...]
        self.modfiles: Dict[Path, List[Mod]] = {} # file: [origin mod, origin mod, etc...]

        # Current profile
        self.profname: str = None
        self.profid: str = None

        # Get settings from database
        settings = self.database['settings']

        # Get paths from settings
        apppath = Path(os.getenv('APPDATA')) / 'Vortex'
        modspath: str = settings['mods']['installPath'][self.app.game.lower()]
        modspath = Path(modspath.replace('{game}', self.app.game.lower()))
        dlpath: str = settings['downloads']['path']
        dlpath = Path(dlpath.replace('{USERDATA}', str(apppath)))

        self.mods_path = modspath
        self.paths['download_dir'] = dlpath

    def __repr__(self):
        return "VortexInstance"

    def setup_instance(self):
        game = self.app.game.lower()
        profname = self.instance_data['name']

        self.app.log.info(
            f"Setting up Vortex profile with name '{profname}'..."
        )

        # Generate unique profile id
        self.load_instances()
        profids = list(self.profiles.values())
        while (profid := ''.join([
                random.choice(
                    string.ascii_letters
                    + string.digits
                ) for n in range(9)
            ])
        ) in profids:
            pass
        self.profid = profid
        self.profiles[profname] = profid

        # Configure profile data
        ini_files = [
            os.path.basename(file).lower()
            for file in self.app.src_modinstance.additional_files
            if str(file).endswith('.ini')
        ]
        local_game_settings = str(bool(ini_files)).lower()
        profile = {
            'features': {
                'local_game_settings': local_game_settings,
                'local_saves': 'false',
            },
            'gameId': game,
            'modState': {},
            'id': profid,
            'lastActivated': time.time(),
            'name': profname,
        }

        # Add profile to database
        self.database['persistent']['profiles'][profid] = profile

        # Create profile folder
        apppath = Path(os.path.join(os.getenv('APPDATA'), 'Vortex'))
        profpath = Path(os.path.join(apppath, game, 'profiles', profid))
        os.mkdir(profpath)

        self.app.log.info(
            f"Created Vortex profile '{profname}' with id '{profid}'."
        )

    def load_instances(self):
        if not self.profiles:
            self.app.log.debug("Loading profiles from database...")

            persistent: Dict[str, dict] = self.database['persistent']
            profiles: Dict[str, dict] = persistent['profiles']
            for profid, profdata in profiles.items():
                # Check if profile is from selected game
                if ((profdata['gameId'] == self.app.game.lower())
                    # And if it has mods installed
                    and ('modState' in profdata.keys())):

                    profname = profdata['name']
                    self.profiles[profname] = profid

            self.app.log.debug(
                f"Loaded {len(self.profiles)} profile(s) from database."
            )

        return list(self.profiles.keys())

    def load_instance(self, name: str):
        self.app.log.info(f"Loading profile '{name}'...")

        # Raise exception if profile is not found
        if name not in self.profiles:
            raise ValueError(
                f"Profile '{name}' not found in database!"
            )

        # Load profile
        profid = self.profiles[name]
        profile = self.database['persistent']['profiles'][profid]
        apppath = Path(os.getenv('APPDATA')) / 'Vortex'

        # Load mods from profile and their data from database
        profmods: dict = profile['modState']
        persistent: dict = self.database['persistent']
        modsdata: dict = persistent['mods'][self.app.game.lower()]
        for modname, modstate in profmods.items():
            moddata = modsdata[modname]
            attributes: Dict[str, str] = moddata['attributes']
            filename = modname
            modname = attributes.get('customFileName', modname)
            modname = modname.strip("-").strip(".").strip()
            modpath = self.mods_path / filename
            modid = attributes.get('modId', None)
            fileid = attributes.get('fileId', None)
            version = attributes.get('version', None)
            enabled = modstate['enabled']
            if 'size' in attributes:
                modsize = attributes['size']
            else:
                modsize = get_folder_size(modpath)
            modfiles = create_folder_list(modpath, lower=False)

            mod = Mod(
                name=modname,
                path=modpath,
                metadata={
                    'name': modname,
                    'modid': modid,
                    'fileid': fileid,
                    'version': version,
                    'filename': filename,
                },
                files=modfiles,
                size=modsize,
                enabled=enabled,
                installed=False
            )
            self.mods.append(mod)

        # Get additional files
        profpath = apppath / self.app.game.lower() / 'profiles' / profid
        self.additional_files = [
            profpath / file
            for file in os.listdir(profpath)
        ]
        userlist_path = apppath / self.app.game.lower() / 'userlist.yaml'
        self.additional_files.append(userlist_path)

        self.name = name

        self.app.log.info(f"Loaded profile '{name}' with id '{profid}'.")

    def copy_mods(self, psignal: qtc.Signal = None):
        self.app.log.info("Migrating mods to instance...")

        game = self.app.game.lower()
        installed_mods = self.database['persistent']['mods'][game]

        # Check installed mods
        for mod in self.mods:
            mod.installed = mod.metadata['filename'] in installed_mods

        for index, mod in enumerate(self.mods):
            self.app.log.debug(
                f"Migrating mod '{mod.name}' ({index}/{len(self.mods)})..."
            )

            # Merge rules if mod is already installed
            if mod.installed:
                moddata = installed_mods[mod.metadata['filename']]
                rules: list = moddata.get('rules', [])
                # Check for rules
                for overwriting_mod in mod.overwriting_mods:
                    overwriting_mod_filename = overwriting_mod.metadata['filename']

                    # Skip mod if both mods already exist in database
                    # since rule is very likely to exist, too
                    #if overwriting_mod_filename in installed_mods:
                    if overwriting_mod.installed:
                        continue
                    
                    # Merge rules
                    rule = {
                        'reference': {
                            'id': overwriting_mod_filename,
                            'idHint': overwriting_mod_filename,
                            'versionMatch': '*'
                        },

                        'type': 'before'
                    }
                    rules.append(rule)

                installed_mods[mod.metadata['filename']]['rules'] = rules

            # Add mod to database otherwise
            else:
                source = 'nexus' if mod.metadata['modid'] else 'other'
                moddata = {
                    'attributes': {
                        'customFileName': mod.metadata['name'],
                        'downloadGame': game,
                        'fileId': mod.metadata['fileid'],
                        'modId': mod.metadata['modid'],
                        'logicalFileName': mod.metadata['filename'],
                        'version': mod.metadata['version'],
                        'source': source,
                    },

                    'id': mod.metadata['filename'],
                    'installationPath': mod.metadata['filename'],
                    'state': 'installed',
                    'type': None,
                }

                # Add rules
                rules = []
                for overwriting_mod in mod.overwriting_mods:
                    overwriting_mod_filename = overwriting_mod.metadata['filename']

                    rule = {
                        'reference': {
                            'id': overwriting_mod_filename,
                            'idHint': overwriting_mod_filename,
                            'versionMatch': '*',
                        },

                        'type': 'before',
                    }
                    rules.append(rule)

                moddata['rules'] = rules
                installed_mods[mod.metadata['filename']] = moddata

            # Add mod to profile
            profiles = self.database['persistent']['profiles']
            profile_mods = profiles[self.profid]['modState']
            modstate = {
                'enabled': True,
                'enabledTime': time.time(),
            }
            profile_mods[mod.metadata['filename']] = modstate

            # Skip mod if it is already installed
            modpath: Path = self.mods_path / mod.metadata['filename']
            if modpath.is_dir():
                if list(modpath.iterdir()):
                    mod.installed = True
            if mod.installed:
                self.app.log.debug("Skipped mod: Mod is already installed.")
                continue

            # Copy mod to staging path
            # if mode is 'copy'
            if self.app.mode == 'copy':
                # Fix too long paths (> 260 characters)
                src_path = f"\\\\?\\{mod.path}"
                dst_path = f"\\\\?\\{modpath}"

                # Copy whole mod folder
                shutil.copytree(src_path, dst_path)

            # Create hardlinks otherwise
            else:
                for file in mod.files:
                    src_path = mod.path / file
                    dst_path = modpath / file
                    dst_dirs = dst_path.parent

                    # Fix too long paths (> 260 characters)
                    dst_dirs = f"\\\\?\\{dst_dirs}"
                    src_path = f"\\\\?\\{src_path}"
                    dst_path = f"\\\\?\\{dst_path}"

                    # Create directory structure and hardlink file
                    os.makedirs(dst_dirs, exist_ok=True)
                    os.link(src_path, dst_path)

        self.app.log.debug("Saving database...")
        self.db.save_db()

        self.app.log.info("Mod migration complete.")

    def copy_files(self, psignal: qtc.Signal = None):
        # Copy additional files like inis
        additional_files = self.app.src_modinstance.additional_files
        if additional_files:
            self.app.log.info(
                "Copying additional files from source to destination..."
            )

            # Get paths
            game = self.app.game.lower()
            app_dir = Path(os.getenv('APPDATA')) / 'Vortex' / game
            dst_dir = app_dir / 'profiles' / self.profid

            # Copy files
            for file in additional_files:
                filename = file.name
                if filename == "userlist.yaml":
                    dst_path = app_dir / filename

                    # Skip if source and destination file are the same
                    if file == dst_path:
                        continue

                    # Create 'userlist.yaml' backup if it already exists
                    userlists = list(app_dir.glob('userlist.yaml.mmm_*'))
                    c = len(userlists) + 1
                    if dst_path.is_file():
                        old_name = dst_path
                        new_name = app_dir / f'userlist.yaml.mmm_{c}'
                        os.rename(old_name, new_name)

                        self.app.log.debug(
                            "Created backup of Vortex's userlist.yaml."
                        )

                    # Copy userlist.yaml from source to destination
                    if not app_dir.is_dir():
                        os.makedirs(app_dir)
                    shutil.copyfile(file, dst_path)
                else:
                    # Copy additional files like ini files to profile folder
                    dst_path = dst_dir / filename.lower()
                    if not dst_dir.is_dir():
                        os.makedirs(dst_dir)
                    shutil.copyfile(file, dst_path)

                self.app.log.debug(f"Copied '{filename}' to destination.")

    @property
    def loadorder(self, psignal: qtc.Signal = None):
        if not self._loadorder:
            self.app.log.info("Creating loadorder from conflict rules...")

            new_loadorder = self.mods.copy()
            new_loadorder.sort(key=lambda mod: mod.name)

            game = self.app.game.lower()
            installed_mods: Dict[str, dict] = self.database['persistent']['mods'][game]
            for mod in self.mods.copy():
                modtype = installed_mods[mod.metadata['filename']]['type']

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
                rules = installed_mods[mod.metadata['filename']].get('rules', [])
                for rule in rules:
                    reference = rule['reference']
                    if 'id' in reference:
                        ref_mod = reference['id'].strip()
                    elif 'fileExpression' in reference:
                        ref_mod = reference['fileExpression'].strip()
                    # Skip mod if reference mod does not exist
                    else:
                        continue

                    # Check if mod is in migrated mods
                    for _mod in self.mods:
                        if _mod.metadata['filename'] == ref_mod:
                            ref_mod = _mod
                            break
                    else:
                        ref_mod = None
                    if ref_mod in self.mods:
                        ruletype = rule['type']
                        # Before
                        if ruletype == 'before':
                            mod.overwriting_mods.append(ref_mod)
                        # After
                        elif ruletype == 'after':
                            ref_mod.overwriting_mods.append(mod)
                        # Ignore if it is dependency
                        elif ruletype == 'requires':
                            continue
                        # Raise error if rule type is unknown
                        else:
                            print(f"Mod: {mod}")
                            print(f"Ref mod: {ref_mod}")
                            print(f"Rule type: {rule['type']}")
                            print(f"Rule reference attrs: {rule['reference'].keys()}")
                            print(f"Rule reference: {rule['reference']}")
                            raise ValueError(f"Invalid rule type '{rule['type']}'!")

                # Sort mod
                if mod.overwriting_mods:
                    self.app.log.debug(f"Sorting mod '{mod}'...")

                    old_index = index = new_loadorder.index(mod)

                    # Get smallest index of all overwriting mods
                    overwriting_mods = [
                        new_loadorder.index(overwriting_mod)
                        for overwriting_mod in mod.overwriting_mods
                    ]
                    index = min(overwriting_mods)
                    self.app.log.debug(
                        f"Current index: {old_index} | Minimal index of overwriting_mods: {index}"
                    )

                    if old_index > index:
                        new_loadorder.insert(index, new_loadorder.pop(old_index))
                        self.app.log.debug(f"Moved mod '{mod}' from index {old_index} to {index}.")

            # Replace Vortex's full mod names displayed name
            final_loadorder = []
            for mod in new_loadorder:
                modname = mod.metadata['name']
                final_loadorder.append(modname)

            self._loadorder = new_loadorder
            self.app.log.info("Created loadorder from conflicts.")

        return self._loadorder

    @loadorder.setter
    def loadorder(self, loadorder: List[Mod], psignal: qtc.Signal = None):
        self.app.log.info("Creating conflict rules from loadorder...")

        self.app.log.debug("Scanning mods for file conflicts...")
        for mod in self.mods:
            for file in mod.files:
                # Make all files lowercase
                file = Path(str(file).lower())
                if file in self.modfiles:
                    self.modfiles[file].append(mod)
                else:
                    self.modfiles[file] = [mod]

        self.app.log.debug("Creating conflict rules...")
        for file, mods in self.modfiles.items():
            # Skip file if it comes from a single mod
            if len(mods) == 1:
                continue
            

            # Get indices of overwriting mods
            overwriting_mods = mods.copy()

            # Sort overwriting mods after loadorder index
            overwriting_mods.sort(key=loadorder.index)

            # Create rules for all mods
            while len(overwriting_mods) > 1:
                # Process and remove first mod from list
                mod = overwriting_mods.pop(0)

                # Add rest of the mods to its overwriting list
                mod.overwriting_mods.extend(overwriting_mods)

            # Remove duplicates
            mod.overwriting_mods = list(set(mod.overwriting_mods))

            print(f"Mod: {mod.name}")
            print(f"Gets overwritten by: {mod.overwriting_mods}")
            print("-" * 20)

        self._loadorder = loadorder

        self.app.log.info("Created conflict rules.")


# Create class for MO2 instance ######################################
class MO2Instance(ModInstance):
    """
    Class for ModOrganizer ModInstance. Inherited from ModInstance class.
    """

    icon_name = "MO2.svg"

    def __repr__(self):
        return "MO2Instance"

    def setup_instance(self):
        game_path = self.app.game_instance.get_install_dir()
        name = self.instance_data['name']

        self.app.log.info(f"Setting up MO2 instance '{name}'...")

        # Get paths from instance data
        appdata_path = Path(os.path.join(
            os.getenv('LOCALAPPDATA'),
            'ModOrganizer',
            name
        ))
        base_dir = Path(self.instance_data['paths']['base_dir'])
        dl_dir = Path(self.instance_data['paths']['download_dir'])
        mods_dir = Path(self.instance_data['paths']['mods_dir'])
        profs_dir = Path(self.instance_data['paths']['profiles_dir'])
        prof_dir = Path(os.path.join(profs_dir, 'Default'))
        overw_dir = Path(self.instance_data['paths']['overwrite_dir'])
        self.paths = {
            'base_dir': base_dir,
            'dl_dir': dl_dir,
            'mods_dir': mods_dir,
            'profs_dir': profs_dir,
            'prof_dir': prof_dir,
            'overw_dir': overw_dir,
        }

        # Create directories
        os.makedirs(appdata_path)
        os.makedirs(base_dir, exist_ok=True)
        os.makedirs(dl_dir, exist_ok=True)
        os.makedirs(mods_dir, exist_ok=True)
        os.makedirs(prof_dir, exist_ok=True)
        os.makedirs(overw_dir, exist_ok=True)
        self.app.log.debug("Created instance folders.")

        # Create ini file with instance configuration
        inipath = Path(os.path.join(appdata_path, 'ModOrganizer.ini'))
        iniparser = IniParser(inipath)
        iniparser.data = {
            'General': {
                'gameName': self.app.game_instance.name,
                'selected_profile': "@ByteArray(Default)",
                'gamePath': str(game_path).replace('\\', '/'),
                'first_start': 'true'
            },

            'Settings': {
                'base_directory': str(base_dir).replace('\\', '/'),
                'download_directory': str(dl_dir).replace('\\', '/'),
                'mod_directory': str(mods_dir).replace('\\', '/'),
                'profiles_directory': str(profs_dir).replace('\\', '/'),
                'overwrite_directory': str(overw_dir).replace('\\', '/'),
                'style': 'Paper Dark.qss'
            }
        }
        iniparser.save_file()
        self.app.log.debug("Created 'ModOrganizer.ini'.")

        # Create profile files
        # Create initweaks.ini
        inipath = Path(os.path.join(prof_dir, 'initweaks.ini'))
        iniparser = IniParser(inipath)
        iniparser.data = {
            'Archive': {
                'InvalidateOlderFiles': 1
            }
        }
        iniparser.save_file()
        self.app.log.debug("Created 'initweaks.ini'.")

        # Create modlist.txt
        modlist = Path(os.path.join(prof_dir, 'modlist.txt'))
        loadorder = self.loadorder.copy()
        loadorder.reverse()
        with open(modlist, 'w', encoding='utf8') as file:
            mods = "# This file was automatically generated by Mod Organizer"
            for mod in loadorder:
                if mod.enabled:
                    mods += "\n+" + mod.metadata['name']
                else:
                    mods += "\n-" + mod.metadata['name']
            mods = mods.strip()
            file.write(mods)
        self.app.log.debug("Created 'modlist.txt'.")

        self.app.log.info("Created MO2 instance.")

    def load_instances(self):
        if not self.instances:
            instances_path = Path(os.path.join(
                os.getenv('LOCALAPPDATA'),
                'ModOrganizer'
                )
            )
            # Check if there are any instances
            if instances_path.is_dir():
                # Get all instance folders
                instances = [
                    obj for obj in os.listdir(instances_path)
                    if Path(os.path.join(instances_path, obj)).is_dir()
                ]
                self.instances = instances
                self.app.log.debug(f"Found {len(instances)} instance(s).")
            # Show error message otherwise
            else:
                raise ValueError("Found no instances!")

        return self.instances

    def load_instance(self, name: str):
        self.app.log.info(f"Loading instance '{name}'...")

        # Raise exception if instance is not found
        app_path = Path(os.getenv('LOCALAPPDATA')) / 'ModOrganizer'
        instance_path = app_path / name
        if (name not in self.instances) or (not instance_path.is_dir()):
            raise ValueError(f"Instance '{name}' not found!")
        
        # Load settings from ini
        inifile = instance_path / 'ModOrganizer.ini'
        iniparser = IniParser(inifile)
        data = iniparser.load_file()
        settings: Dict[str, str] = data['Settings']

        # Get instance paths from ini
        base_dir = Path(settings['base_directory'])
        dl_dir = settings.get('download_directory', None)
        dl_dir = Path((base_dir / 'downloads')
                        if dl_dir is None
                        else dl_dir.replace(
                            "%BASE_DIR",
                            str(base_dir)
                        )
        )
        mods_dir = settings.get('mod_directory', None)
        mods_dir = Path((base_dir / 'mods')
                        if mods_dir is None
                        else mods_dir.replace(
                            "%BASE_DIR",
                            str(base_dir)
                        )
        )
        profs_dir = settings.get('profiles_directory', None)
        profs_dir = Path((base_dir / 'profiles')
                            if profs_dir is None
                            else profs_dir.replace(
                                "%BASE_DIR",
                                str(base_dir)
                            )
        )
        prof_dir = profs_dir / 'Default'
        overw_dir = settings.get('overwrite_directory', None)
        overw_dir = Path((base_dir / 'overwrite')
                            if overw_dir is None
                            else overw_dir.replace(
                                "%BASE_DIR",
                                str(base_dir)
                            )
        )

        self.mods_path = mods_dir
        self.paths = {
            'base_dir': base_dir,
            'dl_dir': dl_dir,
            'mods_dir': mods_dir,
            'profs_dir': profs_dir,
            'prof_dir': prof_dir,
            'overw_dir': overw_dir,
        }

        # Load mods from modlist.txt and their data from meta.ini
        mods = []
        modlist = prof_dir / 'modlist.txt'
        with open(modlist, 'r', encoding='utf8') as modlist:
            lines = modlist.readlines()
            for line in lines:
                if line.startswith("+") or line.startswith("-"):
                    modname = line[1:].strip("\n")
                    modpath = self.mods_path / modname
                    metaini = modpath / 'meta.ini'
                    iniparser = IniParser(metaini)
                    data = iniparser.load_file()
                    general = data['General']
                    installedfiles = data['installedFiles']
                    modid = general.get('modid', 0)
                    fileid = installedfiles.get('1\\fileid', 0)
                    version = general.get('version', '1.0')
                    _ver = '-'.join(version.split('.'))
                    filename = general.get(
                        'installationFile',
                        f"{modname}-{modid}-{_ver}-{fileid}.7z"
                    )
                    filename = filename.rsplit(".", 1)[0] # remove file type
                    modfiles = create_folder_list(modpath, lower=False)
                    modsize = get_folder_size(modpath)
                    enabled = line.startswith('+')

                    mod = Mod(
                        name=modname,
                        path=modpath,
                        metadata={
                            'name': modname,
                            'modid': modid,
                            'fileid': fileid,
                            'version': version,
                            'filename': filename,
                        },
                        files=modfiles,
                        size=modsize,
                        enabled=enabled,
                        installed=True
                    )
                    mods.append(mod)
        self.mods = mods
        self._loadorder = self.mods.copy()
        self._loadorder.reverse()

        # Get additional files
        self.additional_files = [
            (prof_dir / file)
            for file in prof_dir.iterdir()
            if (file.name != 'initweaks.ini'
            and file.name != 'modlist.txt'
            and file.name != 'archives.txt'
            and file.name != 'settings.ini')
        ]
        userlist_path = Path(os.getenv('LOCALAPPDATA')) / 'LOOT' / 'games'
        userlist_path = userlist_path / self.app.game_instance.name
        userlist_path = userlist_path / 'userlist.yaml'
        self.additional_files.append(userlist_path)

        self.name = name

        self.app.log.info("Loaded instance.")

    def copy_mods(self, psignal: qtc.Signal = None):
        self.app.log.info("Migrating mods to instance...")

        for index, mod in enumerate(self.mods):
            self.app.log.debug(
                f"Migrating mod '{mod.name}' ({index}/{len(self.mods)})..."
            )

            # Copy mod to mod path
            modpath: Path = self.mods_path / mod.metadata['name']
            if self.app.mode == 'copy':
                # Fix too long paths (> 260 characters)
                src_path = f"\\\\?\\{mod.path}"
                dst_path = f"\\\\?\\{modpath}"

                # Copy whole mod folder
                shutil.copytree(src_path, dst_path)
            # Create hardlinks
            else:
                for file in mod.files:
                    src_path = mod.path / file
                    dst_path = modpath / file
                    dst_dirs = dst_path.parent

                    # Fix too long paths (> 260 characters)
                    dst_dirs = f"\\\\?\\{dst_dirs}"
                    src_path = f"\\\\?\\{src_path}"
                    dst_path = f"\\\\?\\{dst_path}"

                    # Create directory structure and hardlink file
                    os.makedirs(dst_dirs, exist_ok=True)
                    os.link(src_path, dst_path)

            # Write metadata to 'meta.ini' in destination mod
            metaini = IniParser(modpath / 'meta.ini')
            metaini.data = {
                'General': {
                    'gameName': self.app.game,
                    'modid': mod.metadata['modid'],
                    'version': mod.metadata['version'],
                    'installationFile': f"{mod.metadata['filename']}.7z",
                    'repository': 'Nexus'
                },

                'installedFiles': {
                    '1\\modid': mod.metadata['modid'],
                    '1\\fileid': mod.metadata['fileid']
                }
            }
            metaini.save_file()

        self.app.log.info("Mod migration complete.")

    def copy_files(self, psignal: qtc.Signal = None):
        # Copy additional files like inis
        additional_files = self.app.src_modinstance.additional_files
        if additional_files:
            self.app.log.info(
                "Copying additional files from source to destination..."
            )

            game = self.app.game_instance.name
            paths = self.paths
            app_dir = Path(os.getenv('LOCALAPPDATA')) / 'LOOT' / game
            dst_dir = paths['prof_dir']

            for file in additional_files:
                filename = file.name
                if filename == "userlist.yaml":
                    dst_path = app_dir / filename

                    # Skip if source and destination file are the same
                    if file == dst_path:
                        continue

                    # Create userlist.yaml backup if it already exists
                    userlists = list(app_dir.glob('userlist.yaml.mmm_*'))
                    c = len(userlists) + 1
                    if dst_path.is_file():
                        old_name = app_dir / 'userlist.yaml'
                        new_name = app_dir / f'userlist.yaml.mmm_{c}'
                        os.rename(old_name, new_name)

                        self.app.log.debug(
                            "Created backup of installed LOOT's 'userlist.yaml'."
                        )

                    # Copy userlist.yaml from source to destination
                    shutil.copyfile(file, dst_path)
                else:
                    # Copy additional files like ini files to profile folder
                    dst_path = dst_dir / filename.lower()
                    shutil.copyfile(file, dst_path)

                self.app.log.debug(f"Copied '{filename}' to destination.")
