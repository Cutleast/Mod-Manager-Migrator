"""
Part of MMM. Contains classes for mod manager instances.

Falls under license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

# Import libraries ###################################################
import logging
import os
import random
import shutil
import string
import time
from pathlib import Path
from typing import Dict, List

import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

from loadingdialog import LoadingDialog
from main import MainApp, qtc, qtg, qtw
from utils import (IniParser, Mod, ModItem, UiException, VortexDatabase,
                   create_folder_list, get_folder_size, scale_value)


# Create class for modding instance ##################################
class ModInstance:
    """
    General class for mod manager instances.
    """

    icon_name = ""

    def __init__(self, app: MainApp):
        self.app = app

        # Initialize class specific logger
        self.log = logging.getLogger(self.__repr__())
        self.log.addHandler(self.app.log_str)
        self.log.setLevel(self.app.log.level)

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

    def load_instance(self, name: str, ldialog: LoadingDialog = None):
        """
        Loads instance with name <name>.
        """

        self.name = name

    def copy_mods(self, ldialog: LoadingDialog = None):
        """
        Copies mods from source instance to destination instance.
        
        Gets called by destination instance.
        """

        return

    def copy_files(self, ldialog: LoadingDialog = None):
        """
        Copies additional files from source instance
        to destination instance.

        Gets called by destination instance.
        """

        return

    def show_src_widget(self):
        """
        Shows widget with instance details and mods
        at source position.        
        """

        self._show_widget('src')

    def show_dst_widget(self):
        """
        Shows widget with instance details and mods
        at source position.
        """

        self._show_widget('dst')

    def _show_widget(self, pos: str):
        """
        Shows widget. Internal use only!
        
        Use 'show_src_widget' or 'show_dst_widget' instead!        
        """

        # Create widget with instance details
        self.widget = qtw.QWidget()
        self.widget.setObjectName("panel")

        # Create layout
        layout = qtw.QGridLayout()
        layout.setAlignment(qtc.Qt.AlignmentFlag.AlignTop)
        layout.setColumnStretch(2, 1)
        self.widget.setLayout(layout)

        # Add label with mod manager icon
        label = qtw.QLabel(f"{self.app.lang['mod_manager']}:")
        layout.addWidget(label, 0, 0)
        icon = qtg.QPixmap(os.path.join(
                self.app.ico_path,
                self.icon_name
            )
        )
        label = qtw.QLabel()
        label.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter)
        size = qtc.QSize(375, 125)
        label.resize(size)
        label.setFixedSize(size)
        icon = icon.scaled(size, qtc.Qt.AspectRatioMode.KeepAspectRatio)
        label.setPixmap(icon)
        layout.addWidget(label, 0, 1)

        # Add label with instance name
        label = qtw.QLabel(f"{self.app.lang['instance_name']}:")
        layout.addWidget(label, 1, 0)
        label = qtw.QLabel(self.name)
        layout.addWidget(label, 1, 1)

        # Add label with game name
        label = qtw.QLabel(f"{self.app.lang['game']}:")
        layout.addWidget(label, 2, 0)
        label = qtw.QLabel(self.app.game_instance.name)
        layout.addWidget(label, 2, 1)

        # Add label with mods path
        label = qtw.QLabel(f"{self.app.lang['mods_path']}:")
        layout.addWidget(label, 3, 0)
        self.mods_count_label = qtw.QLabel(str(self.mods_path))
        layout.addWidget(self.mods_count_label, 3, 1)
        
        # Add label with instance size
        if pos == 'src':
            label = qtw.QLabel(f"{self.app.lang['size']}:")
            layout.addWidget(label, 4, 0)
            label = qtw.QLabel(scale_value(self.size))
            layout.addWidget(label, 4, 1)
        else:
            label = qtw.QLabel(f"{self.app.lang['mode']}:")
            layout.addWidget(label, 4, 0)
            label = qtw.QLabel(self.app.lang[f'{self.app.mode}_mode'])
            layout.addWidget(label, 4, 1)

        # Add label with mods count
        label = qtw.QLabel(f"{self.app.lang['number_of_mods']}:")
        layout.addWidget(label, 5, 0)
        self.mods_count_label = qtw.QLabel(str(len(self.mods)))
        layout.addWidget(self.mods_count_label, 5, 1)

        # Add listbox for source mods
        if pos == 'src':
            label = qtw.QLabel(self.app.lang['mods_to_migrate'])
        else:
            label = qtw.QLabel(self.app.lang['mods_to_enable'])
        layout.addWidget(label, 6, 0)
        self.mods_box = qtw.QListWidget()
        self.mods_box.setSelectionMode(
            qtw.QListWidget.SelectionMode.MultiSelection
        )
        self.mods_box.setHorizontalScrollBarPolicy(
            qtc.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.mods_box.itemDoubleClicked.connect(
            lambda item: item.onClick()
        )
        self.mods_box.setContextMenuPolicy(
            qtc.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.mods_box.customContextMenuRequested.connect(
            lambda pos: self._contextmenu(self.mods_box.mapToGlobal(pos))
        )
        layout.addWidget(self.mods_box, 7, 0, 1, 3)

        # Add mods to listbox
        self._update_listbox(pos)

        # Show widget as source
        if pos == 'src':
            self.mods_box.itemChanged.connect(
                lambda item: self.app.migrate_mods_change_sign.emit()
            )
            if self.app.src_widget is not None:
                self.app.src_widget.destroy()
            self.app.mainlayout.addWidget(self.widget, 1, 0)
            self.app.src_widget = self.widget

        # Or show widget as destination
        elif pos == 'dst':
            try:
                self.app.migrate_mods_change_sign.disconnect()
            except:
                pass
            self.app.migrate_mods_change_sign.connect(
                lambda: self._update_listbox(pos)
            )
            if self.app.dst_widget is not None:
                self.app.dst_widget.destroy()
            self.app.mainlayout.addWidget(self.widget, 1, 2)
            self.app.dst_widget = self.widget

    def _contextmenu(self, pos: qtc.QPoint):
        """
        Shows context menu. Internal use only!        
        """

        select_action = qtg.QAction(self.app.lang['enable_selected'])
        select_action.triggered.connect(self._enable_selected)
        unselect_action = qtg.QAction(self.app.lang['disable_selected'])
        unselect_action.triggered.connect(self._disable_selected)
        unsel_all_action = qtg.QAction(self.app.lang['unselect_all'])
        unsel_all_action.triggered.connect(self._unselect_all)
        context_menu = qtw.QMenu()
        context_menu.setWindowFlags(
            qtc.Qt.WindowType.FramelessWindowHint
            | qtc.Qt.WindowType.Popup
            | qtc.Qt.WindowType.NoDropShadowWindowHint
        )
        context_menu.setAttribute(
            qtc.Qt.WidgetAttribute.WA_TranslucentBackground,
            on=True
        )
        context_menu.setStyleSheet(self.app.stylesheet)
        context_menu.addAction(select_action)
        context_menu.addAction(unselect_action)
        context_menu.addAction(unsel_all_action)

        # Show context menu
        context_menu.exec(pos)

    def _enable_selected(self):
        """
        Enables selected mods. Internal use only!        
        """

        for item in self.mods_box.selectedItems():
            if item.checkState() != qtc.Qt.CheckState.Checked:
                self.mods_box.itemDoubleClicked.emit(item)

    def _disable_selected(self):
        """
        Disables selected mods. Internal use only!        
        """

        for item in self.mods_box.selectedItems():
            if item.checkState() != qtc.Qt.CheckState.Unchecked:
                self.mods_box.itemDoubleClicked.emit(item)
    
    def _unselect_all(self):
        """
        Unselects all mods. Internal use only!        
        """

        for item in self.mods_box.selectedItems():
            item.setSelected(False)

    def _update_listbox(self, pos: str):
        """
        Updates listbox. Internal use only!
        """

        if self.widget is not None:
            try:
                self.mods_box.itemChanged.disconnect()
            except:
                pass
            self.mods_box.clear()
            for mod in self.loadorder:
                if not mod.selected and pos == 'dst':
                    continue
                item = ModItem(
                    mod,
                    pos,
                    mod.name,
                    self.mods_box
                )
                item.setFlags(item.flags() | qtc.Qt.ItemFlag.ItemIsUserCheckable)
                if pos == 'dst':
                    if mod.enabled:
                        item.setCheckState(qtc.Qt.CheckState.Checked)
                    else:
                        item.setCheckState(qtc.Qt.CheckState.Unchecked)
                else:
                    mod.selected = True
                    item.setCheckState(qtc.Qt.CheckState.Checked)
                self.mods_box.addItem(item)

            self.mods_count_label.setText(str(self.mods_box.count()))

            self.mods_box.itemChanged.connect(
                lambda item: item.onClick()
            )

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
    def loadorder(self, loadorder: list, ldialog: LoadingDialog = None):
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

    icon_name = "Vortex-Label.png"

    def __init__(self, app: MainApp):
        super().__init__(app)

        # Initialize Vortex specific attributes
        try:
            self.db = VortexDatabase(app)
            self.database = self.db.load_db()
        except:
            raise UiException(\
"[vortex_running] Failed to access Vortex database: \
Vortex is running!"
            )
        self.profiles: Dict[str, str] = {}

        # Files and overwrites
        self.overwrites: Dict[Mod, List[Mod]] = {} # mod: [overwriting mod, overwriting mod, etc...]
        self.modfiles: Dict[Path, List[Mod]] = {} # file: [origin mod, origin mod, etc...]

        # Current profile
        self.profname: str = None
        self.profid: str = None

        # Get settings from database
        settings = self.database['settings']

        game = self.app.game.lower()

        # Get paths from settings
        apppath = Path(os.getenv('APPDATA')) / 'Vortex'
        modspath: str = settings['mods']['installPath'].get(game, str(apppath / game))
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

        self.log.info(
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

        self.log.info(
            f"Created Vortex profile '{profname}' with id '{profid}'."
        )

    def load_instances(self):
        if not self.profiles:
            self.log.debug("Loading profiles from database...")

            persistent: Dict[str, dict] = self.database['persistent']
            profiles: Dict[str, dict] = persistent['profiles']
            for profid, profdata in profiles.items():
                # Check if profile is from selected game
                if ((profdata['gameId'] == self.app.game.lower())
                    # And if it has mods installed
                    and ('modState' in profdata.keys())):

                    profname = profdata['name']
                    self.profiles[profname] = profid

            self.log.debug(
                f"Loaded {len(self.profiles)} profile(s) from database."
            )

        return list(self.profiles.keys())

    def load_instance(self, name: str, ldialog: LoadingDialog = None):
        self.log.info(f"Loading profile '{name}'...")

        self.mods = []
        self._loadorder = []

        # Update progress bar
        if ldialog:
            ldialog.updateProgress(
                text1=self.app.lang['loading_instance']
            )

        # Raise exception if profile is not found
        if name not in self.profiles:
            raise ValueError(
                f"Profile '{name}' not found in database!"
            )

        # Load profile
        game = self.app.game.lower()
        profid = self.profiles[name]
        profile = self.database['persistent']['profiles'][profid]
        apppath = Path(os.getenv('APPDATA')) / 'Vortex'

        # Load mods from profile and their data from database
        profmods: dict = profile['modState']
        persistent: dict = self.database['persistent']
        modsdata: dict = persistent['mods'][game]
        for modindex, (modname, modstate) in enumerate(profmods.items()):
            # Update progress bar
            if ldialog:
                ldialog.updateProgress(
                    text1=\
f"{self.app.lang['loading_instance']} ({modindex}/{len(profmods)})",
                    value1=modindex,
                    max1=len(profmods)
                )

            moddata = modsdata[modname]
            attributes: Dict[str, str] = moddata['attributes']
            filename = modname
            modname = attributes.get('customFileName', modname)
            modname = modname.strip("-").strip(".").strip()

            # Update progress bar
            if ldialog:
                ldialog.updateProgress(
                    show2=True,
                    text2=modname
                )

            modpath = self.mods_path / filename
            modid = attributes.get('modId', None)
            fileid = attributes.get('fileId', None)
            version = attributes.get('version', None)
            enabled = modstate['enabled']
            if 'modSize' in attributes:
                modsize = attributes['modSize']
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
        profpath = apppath / game / 'profiles' / profid
        self.additional_files = [
            profpath / file
            for file in profpath.iterdir()
            if file.is_file()
        ]
        userlist_path = apppath / game / 'userlist.yaml'
        self.additional_files.append(userlist_path)

        self.name = name

        self.log.info(f"Loaded profile '{name}' with id '{profid}'.")

    def copy_mods(self, ldialog: LoadingDialog = None):
        self.log.info("Migrating mods to instance...")

        game = self.app.game.lower()
        installed_mods = self.database['persistent']['mods'][game]

        # Check installed mods
        for mod in self.mods:
            mod.installed = mod.metadata['filename'] in installed_mods

        maximum = len(self.mods)
        for modindex, mod in enumerate(self.mods):
            self.log.debug(
                f"Migrating mod '{mod.name}' ({modindex}/{maximum})..."
            )

            # Skip mod if it is not selected in source box
            if not mod.selected:
                self.log.debug("Skipped mod: Mod is not selected.")
                continue
            
            # Update progress bars
            if ldialog:
                ldialog.updateProgress(
                    # Update first progress bar
                    text1=\
f"{self.app.lang['migrating_instance']} ({modindex}/{maximum})",
                    value1=modindex,
                    max1=maximum,

                    # Display and update second progress bar
                    show2=True,
                    text2=mod.metadata['name'],
                    value2=0,
                    max2=0
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
                self.log.debug("Skipped mod: Mod is already installed.")
                continue
            
            # Link or copy mod to destination
            for fileindex, file in enumerate(mod.files):
                # Update progress bars
                if ldialog:
                    ldialog.updateProgress(
                        text2=\
f"{mod.metadata['name']} ({fileindex}/{len(mod.files)})",
                        value2=fileindex,
                        max2=len(mod.files),

                        show3=True,
                        text3=\
f"{file.name} ({scale_value(os.path.getsize(mod.path / file))})"
                    )

                src_path = mod.path / file
                dst_path = modpath / file
                dst_dirs = dst_path.parent

                # Fix too long paths (> 260 characters)
                dst_dirs = f"\\\\?\\{dst_dirs}"
                src_path = f"\\\\?\\{src_path}"
                dst_path = f"\\\\?\\{dst_path}"

                # Create directory structure and hardlink file
                os.makedirs(dst_dirs, exist_ok=True)

                # Copy file
                if self.app.mode == 'copy':
                    shutil.copyfile(src_path, dst_path)
                # Link file
                else:
                    os.link(src_path, dst_path)

        self.log.debug("Saving database...")
        self.db.save_db()

        self.log.info("Mod migration complete.")

    def copy_files(self, ldialog: LoadingDialog = None):
        # Copy additional files like inis
        additional_files = self.app.src_modinstance.additional_files
        if additional_files:
            self.log.info(
                "Copying additional files from source to destination..."
            )

            # Get paths
            game = self.app.game.lower()
            app_dir = Path(os.getenv('APPDATA')) / 'Vortex' / game
            dst_dir = app_dir / 'profiles' / self.profid

            # Copy files
            maximum = len(additional_files)
            for fileindex, file in enumerate(additional_files):
                # Skip file if it does not exist
                if not file.is_file():
                    self.log.error(
                        f"Failed to copy '{file.name}': File does not exist!"
                    )
                    continue

                # Update progress bars
                if ldialog:
                    ldialog.updateProgress(
                        # Update first progress bar
                        text1=\
f"{self.app.lang['copying_files']} ({fileindex}/{maximum})",
                        value1=fileindex,
                        max1=maximum,

                        # Display and update second progress bar
                        show2=True,
                        text2=file.name,
                        value2=0,
                        max2=0
                    )

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

                        self.log.debug(
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

                self.log.debug(f"Copied '{filename}' to destination.")

    @property
    def loadorder(self, ldialog: LoadingDialog = None):
        if not self._loadorder:
            self.log.info("Creating loadorder from conflict rules...")

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
                    #self.log.debug(f"Sorting mod '{mod}'...")

                    old_index = index = new_loadorder.index(mod)

                    # Get smallest index of all overwriting mods
                    overwriting_mods = [
                        new_loadorder.index(overwriting_mod)
                        for overwriting_mod in mod.overwriting_mods
                    ]
                    index = min(overwriting_mods)
                    #self.log.debug(
                    #    f"Current index: {old_index} | Minimal index of overwriting_mods: {index}"
                    #)

                    if old_index > index:
                        new_loadorder.insert(index, new_loadorder.pop(old_index))
                        #self.log.debug(f"Moved mod '{mod}' from index {old_index} to {index}.")

            # Replace Vortex's full mod names displayed name
            final_loadorder = []
            for mod in new_loadorder:
                modname = mod.metadata['name']
                final_loadorder.append(modname)

            self._loadorder = new_loadorder
            self.log.info("Created loadorder from conflicts.")

        return self._loadorder

    @loadorder.setter
    def loadorder(self, loadorder: List[Mod], ldialog: LoadingDialog = None):
        self.log.info("Creating conflict rules from loadorder...")

        self.log.debug("Scanning mods for file conflicts...")
        for mod in self.mods:
            for file in mod.files:
                # Make all files lowercase
                file = Path(str(file).lower())
                if file in self.modfiles:
                    self.modfiles[file].append(mod)
                else:
                    self.modfiles[file] = [mod]

        self.log.debug("Creating conflict rules...")
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

        self._loadorder = loadorder

        self.log.info("Created conflict rules.")


# Create class for MO2 instance ######################################
class MO2Instance(ModInstance):
    """
    Class for ModOrganizer ModInstance. Inherited from ModInstance class.
    """

    icon_name = "MO2-Label.png"

    def __repr__(self):
        return "MO2Instance"

    def setup_instance(self):
        game_path = self.app.game_instance.get_install_dir()
        name = self.instance_data['name']

        self.log.info(f"Setting up MO2 instance '{name}'...")

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
        self.log.debug("Created instance folders.")

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
        self.log.debug("Created 'ModOrganizer.ini'.")

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
        self.log.debug("Created 'initweaks.ini'.")

        # Create modlist.txt
        modlist = Path(os.path.join(prof_dir, 'modlist.txt'))
        loadorder = self.loadorder.copy()
        loadorder.reverse()
        with open(modlist, 'w', encoding='utf8') as file:
            mods = "# This file was automatically generated by Mod Organizer"
            for mod in loadorder:
                # Skip mod if is not selected in source box
                if not mod.selected:
                    continue

                # Enable mod in destination
                if mod.enabled:
                    mods += "\n+" + mod.metadata['name']

                # Disable mod in destination
                else:
                    mods += "\n-" + mod.metadata['name']
            mods = mods.strip()
            file.write(mods)
        self.log.debug("Created 'modlist.txt'.")

        self.log.info("Created MO2 instance.")

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
                self.log.debug(f"Found {len(instances)} instance(s).")
            # Show error message otherwise
            else:
                raise ValueError("Found no instances!")

        return self.instances

    def load_instance(self, name: str, ldialog: LoadingDialog = None):
        self.log.info(f"Loading instance '{name}'...")

        self._loadorder = []
        self.mods = []

        # Update progress bar
        if ldialog:
            ldialog.updateProgress(
                text1=self.app.lang['loading_instance']
            )

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
        if not modlist.is_file():
            raise UiException(f"[no_mods] Instance '{name}' has no mods!")
        with open(modlist, 'r', encoding='utf8') as modlist:
            lines = modlist.readlines()

        for modindex, line in enumerate(lines):
            line = line.strip()
            if ((line.startswith("+") or line.startswith("-"))
                and (not line.endswith("_separator"))):
                modname = line[1:]
                modpath = self.mods_path / modname

                # Update progress bar
                if ldialog:
                    ldialog.updateProgress(
                        text1=\
f"{self.app.lang['loading_instance']} ({modindex}/{len(lines)})",
                        value1=modindex,
                        max1=len(lines),

                        show2=True,
                        text2=modname
                    )

                # Load mod metadata from meta.ini
                metaini = modpath / 'meta.ini'
                if metaini.is_file():
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

                # Create metadata if 'meta.ini' does not exist
                else:
                    self.log.warning(f"Found no 'meta.ini' for mod '{modname}'!")
                    self.log.debug("Creating empty metadata...")

                    modid = 0
                    fileid = 0
                    version = '1.0'
                    filename = f"{modname}-1-0"
                
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

        self.log.info("Loaded instance.")

    def copy_mods(self, ldialog: LoadingDialog = None):
        self.log.info("Migrating mods to instance...")

        maximum = len(self.mods)
        for modindex, mod in enumerate(self.mods):
            self.log.debug(
                f"Migrating mod '{mod.name}' ({modindex}/{len(self.mods)})..."
            )

            # Skip mod if it is not selected in source box
            if not mod.selected:
                self.log.debug("Skipped mod: Mod is not selected.")
                continue
            
            # Update progress bars
            if ldialog:
                ldialog.updateProgress(
                    # Update first progress bar
                    text1=\
f"{self.app.lang['migrating_instance']} ({modindex}/{maximum})",
                    value1=modindex,
                    max1=maximum,

                    # Display and update second progress bar
                    show2=True,
                    text2=mod.metadata['name'],
                    value2=0,
                    max2=0
                )

            # Copy mod to mod path
            modpath: Path = self.mods_path / mod.metadata['name']
            for fileindex, file in enumerate(mod.files):
                # Update progress bars
                if ldialog:
                    ldialog.updateProgress(
                        text2=\
f"{mod.metadata['name']} ({fileindex}/{len(mod.files)})",
                        value2=fileindex,
                        max2=len(mod.files),

                        show3=True,
                        text3=\
f"{file.name} ({scale_value(os.path.getsize(mod.path / file))})"
                    )

                src_path = mod.path / file
                dst_path = modpath / file
                dst_dirs = dst_path.parent

                # Fix too long paths (> 260 characters)
                dst_dirs = f"\\\\?\\{dst_dirs}"
                src_path = f"\\\\?\\{src_path}"
                dst_path = f"\\\\?\\{dst_path}"

                # Create directory structure
                os.makedirs(dst_dirs, exist_ok=True)

                # Copy file
                if self.app.mode == 'copy':
                    shutil.copyfile(src_path, dst_path)
                # Link file
                else:
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

        self.log.info("Mod migration complete.")

    def copy_files(self, ldialog: LoadingDialog = None):
        # Copy additional files like inis
        additional_files = self.app.src_modinstance.additional_files
        if additional_files:
            self.log.info(
                "Copying additional files from source to destination..."
            )

            game = self.app.game_instance.name
            paths = self.paths
            app_dir = Path(os.getenv('LOCALAPPDATA')) / 'LOOT' / game
            dst_dir = paths['prof_dir']

            # Copy files
            maximum = len(additional_files)
            for fileindex, file in enumerate(additional_files):
                # Skip file if it does not exist
                if not file.is_file():
                    self.log.error(
                        f"Failed to copy '{file.name}': File does not exist!"
                    )
                    continue

                # Update progress bars
                if ldialog:
                    ldialog.updateProgress(
                        # Update first progress bar
                        text1=\
f"{self.app.lang['copying_files']} ({fileindex}/{maximum})",
                        value1=fileindex,
                        max1=maximum,

                        # Display and update second progress bar
                        show2=True,
                        text2=file.name,
                        value2=0,
                        max2=0
                    )

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

                        self.log.debug(
                            "Created backup of installed LOOT's 'userlist.yaml'."
                        )

                    # Copy userlist.yaml from source to destination
                    shutil.copyfile(file, dst_path)
                else:
                    # Copy additional files like ini files to profile folder
                    dst_path = dst_dir / filename.lower()
                    shutil.copyfile(file, dst_path)

                self.log.debug(f"Copied '{filename}' to destination.")
