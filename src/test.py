"""
No part of MMM. For testing and debuggin purposes.
"""

# Import libraries ###################################################
import argparse
import ctypes
import json
import logging
import os
import platform
import shutil
import sys
import time
from locale import getlocale
from shutil import disk_usage

import main
import core


# Create stripped MainApp class for testing ##########################
class MainApp:
    def __init__(self):
        # Initialize variables #######################################
        self.version = "1.0"
        self.name = f"Mod Manager Migrator"
        # check if compiled with nuitka (or in general)
        self.compiled = ("__compiled__" in globals()) or (sys.argv[0].endswith('.exe'))
        self._imgdata = None
        self.encrypt_key = None
        self.unsaved_changes = False
        self.unsaved_settings = False
        self.source = None
        self.destination = None
        self.stagefile = None
        self.src_modinstance = None # VortexInstance or MO2Instance
        self.dst_modinstance = None # VortexInstance or MO2Instance
        self.mode = 'hardlink' # 'copy' or 'hardlink'
        self.load_order = []
        self.start_date = time.strftime("%d.%m.%Y")
        self.start_time = time.strftime("%H:%M:%S")
        self.os_type = "linux" if "Linux" in platform.system() else "windows"
        print(f"Current datetime: {self.start_date} {self.start_time}")
        # paths
        self.cur_path = os.path.dirname(__file__)
        self.app_path = os.path.join(os.getenv('APPDATA'), self.name)
        self.con_path = os.path.join(self.app_path, 'config.json')
        self.res_path = os.path.join(self.cur_path, 'data')
        self.ico_path = os.path.join(self.res_path, 'icons')
        self.theme_path = os.path.join(self.res_path, 'theme.json')
        self.qss_path = os.path.join(self.res_path, 'style.qss')
        _buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, _buf)
        self.doc_path = os.path.normpath(os.path.join(_buf.value, 'My Games', 'Skyrim Special Edition'))
        # logging
        self.log_name = f"{self.name}_{self.start_date}_-_{self.start_time.replace(':', '.')}.log"
        #self.log_path = os.path.join(self.res_path, 'logs', self.log_name)
        self.log_path = os.path.join(os.getenv('APPDATA'), self.name, 'logs', self.log_name)
        if not os.path.isdir(os.path.join(os.getenv('APPDATA'), self.name)):
            os.mkdir(os.path.join(os.getenv('APPDATA'), self.name))
        if not os.path.isdir(os.path.dirname(self.log_path)):
            os.mkdir(os.path.dirname(self.log_path))
        self.protocol = ""
        # config
        self.default_conf = {
            'save_logs': False, 
            'log_level': 'info',
            'ui_mode': 'System',
            'language': 'System',
            'accent_color': '#d78f46',
        }

        # Create or load config file #################################
        try:
            # load config
            config = json.load(open(self.con_path, 'r'))

            if len(config.keys()) < len(self.default_conf.keys()):
                # update outdated config
                print(f"Detected incomplete (outdated) config file. Updating with default config...")
                new_keys = [key for key in self.default_conf.keys() if key not in config.keys()]
                for key in new_keys:
                    config[key] = self.default_conf[key]

                # try to save updated config to config file
                try:
                    with open(self.con_path, "w") as conffile:
                        json.dump(config, conffile, indent=4)
                    print(f"Saved updated config to config file.")
                # ignore if access denied by os
                except OSError:
                    print(f"Failed to update config file: Access denied.")

            # apply config
            self.config = config
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            # apply default config
            self.config = self.default_conf

            # save default config to config file
            with open(self.con_path, "w") as conffile:
                json.dump(self.config, conffile, indent=4)
        
        # Set up protocol structure ##################################
        self.log = logging.getLogger(self.__repr__())
        log_fmt = "[%(asctime)s.%(msecs)03d][%(levelname)s][%(threadName)s.%(name)s.%(funcName)s]: %(message)s"
        self.log_fmt = logging.Formatter(log_fmt, datefmt="%d.%m.%Y %H:%M:%S")
        self.stdout = main.StdoutPipe(self)
        self.log_str = logging.StreamHandler(self.stdout)
        self.log_str.setFormatter(self.log_fmt)
        self.log.addHandler(self.log_str)
        self.log_level = getattr(logging, self.config['log_level'].upper(), 20) # info level
        self.log.setLevel(self.log_level)

        # Parse commandline arguments ################################
        help_msg = f"{self.name} v{self.version} by Cutleast"
        if self.compiled:
            parser = argparse.ArgumentParser(prog=os.path.basename(sys.executable), description=help_msg)
        else:
            parser = argparse.ArgumentParser(prog=f"{os.path.basename(sys.executable)} {__file__}", description=help_msg)
        parser.add_argument("-l", "--log-level", help="Specify logging level.", choices=list(main.LOG_LEVELS.values()))
        parser.add_argument("--no-log", help="Disable log file.", action="store_true")
        parser.add_argument("--keep-log", help="Keep log file. (Overwrites --no-log)", action="store_true")
        self.args = parser.parse_args()
        if self.args.no_log:
            self.config['save_logs'] = False
        if self.args.keep_log:
            self.config['save_logs'] = True
        if self.args.log_level:
            self.log_level = getattr(logging, self.args.log_level.upper(), 20)
            self.log.setLevel(self.log_level)
        
        # Start by logging basic information #########################
        log_title = "-" * 40 + f" {self.name} " + "-" * 40
        self.log.info(f"\n{'-' * len(log_title)}\n{log_title}\n{'-' * len(log_title)}")
        self.log.info(f"Starting program...")
        self.log.info(f"{'Executable name':22}: {sys.executable}")
        self.log.info(f"{'Executable path':22}: {self.cur_path}")
        self.log.debug(f"{'Compiled':21}: {self.compiled}")
        self.log.info(f"{'Command line arguments':22}: {sys.argv}")
        self.log.info(f"{'Resource path':22}: {self.res_path}")
        self.log.info(f"{'Config path':22}: {self.con_path}")
        self.log.info(f"{'Log path':22}: {self.log_path}")
        self.log.info(f"{'Log level':22}: {main.LOG_LEVELS[self.log.level]}")
        self.log.info(f"{'UI mode':22}: {self.config['ui_mode']}")
        self.log.info(f"{'System language':22}: {getlocale()[0]}")
        self.log.debug(f"{'Detected platform':21}: {platform.system()} {platform.version()} {platform.architecture()[0]}")

    def __repr__(self):
        return "MainApp"
       
    # Core function to migrate #######################################
    def migrate(self):
        self.log.info(f"Migrating instance from {self.source} to {self.destination}...")

        # Calculate free and required disk space if copy mode
        if self.mode == 'copy':
            self.fspace = 0 # free space
            self.rspace = 0 # required space
            self.fspace = disk_usage(os.path.splitdrive(self.dst_modinstance.paths['instance_path'])[0])[2]
            self.rspace = self.src_modinstance.get_size()
            self.log.debug(f"Free space: {core.get_size(self.fspace)} | Required space: {core.get_size(self.rspace)}")

            # Check if there is enough free space
            if self.fspace <= self.rspace:
                self.log.error(f"Migration failed: not enough free space!")
                return

        # Create destination mod instance with ini files and loadorder
        self.dst_modinstance.loadorder = self.src_modinstance.get_loadorder()
        # Fetch and copy metadata
        for i, mod in enumerate(self.dst_modinstance.loadorder):
            data = self.src_modinstance.get_mod_metadata(mod)
            self.dst_modinstance.loadorder[i] = data['name']
            self.dst_modinstance.metadata[mod] = data
        self.dst_modinstance.create_instance()

        # Check for files that have to be copied
        # directly into the skyrim folder
        # since MO2 cannot manage those
        if self.source == 'Vortex':
            if self.src_modinstance.stagefiles:
                self.log.info("Found root files!")

        # Copy mods to new instance
        for c, mod in enumerate(self.src_modinstance.mods.keys()):
            self.dst_modinstance.import_mod(os.path.join(self.src_modinstance.paths['instance_path'], mod))

        # Copy downloads if given to new instance
        if self.src_modinstance.paths.get('download_path', None):
            for c, archive in enumerate(os.listdir(self.src_modinstance.paths['download_path'])):
                src_path = os.path.join(self.src_modinstance.paths['download_path'], archive)
                dst_path = os.path.join(self.dst_modinstance.paths['download_path'], archive)
                if self.mode == 'copy':
                    shutil.copyfile(src_path, dst_path)
                else:
                    os.link(src_path, dst_path)

        self.log.info("Migration complete.")


# Define function to test loading dialog #############################
def test_ld(max: int, interval: int):
    qapp = main.qtw.QApplication([])
    root = main.qtw.QWidget()
    root.setStyleSheet("QWidget { background-color: #101010; color: #ffffff; }")
    #root.hide()
    root.showMaximized()

    def process(psignal: main.qtc.Signal):
        for i in range(max):
            for i2 in range(int(max/10)):
                progress = {
                    'value': i,
                    'max': max,
                    'text': f"Doing a big process... ({i}/{max})",
                    'show2': True,
                    'value2': i2,
                    'max2': int(max/10),
                    'text2': f"Doing process '{i}'..."
                }
                psignal.emit(progress)
                time.sleep(interval/10)
            #time.sleep(interval)
    ld = main.LoadingDialog(root, app, process)
    ld.setStyleSheet("""
QProgressBar {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 0px solid;
    border-radius: 8px;
    height: 2px;
}
QProgressBar::chunk {
    background-color: #d78f46;
    border-radius: 8px;
}
""")
    ld.exec()


if __name__ == '__main__':
    starttime = time.time()
    app = MainApp()

    # Parameters
    # SET BEFORE USE!
    mode = 'hardlink' # 'hardlink' or 'copy'
    source = 'Vortex' # has to be in main.SUPPORTED_MODMANAGERS
    destination = 'ModOrganizer' # has to be in main.SUPPORTED_MODMANAGERS
    staging_folder = "C:\\Modding\\Skyrim\\Vortex" # only if source is 'Vortex'
    instance_path = "C:\\Modding\\Skyrim\\Vortex"
    download_path = "" # only if you want it to get copied
    instance_name = "Migrated Vortex Instance"
    dst_instance_path = f"C:\\Modding\\{instance_name}"

    # Set mode
    app.mode = mode
    app.log.debug(f"Mode: {app.mode}")
    # Set source
    app.source = source
    app.log.debug(f"Source: {app.source}")
    # Set destination
    app.destination = destination
    app.log.debug(f"Destination: {app.destination}")

    # Load instance
    app.log.debug(f"Creating source instance...")
    instance_data = {} # keys: name, paths, mods, loadorder, custom executables
    if app.source == 'Vortex':
        instance_data['name'] = "Migrated Vortex Instance"
        app.log.debug("Loading active Vortex profile...")
        instance_data['paths'] = {
            'staging_folder': staging_folder,
            'instance_path': instance_path,
            'download_path': download_path,
            'skyrim_ini': os.path.join(app.doc_path, 'Skyrim.ini'),
            'skyrim_prefs_ini': os.path.join(app.doc_path, 'SkyrimPrefs.ini')
        }
        stagefile = os.path.join(instance_data['paths']['staging_folder'], 'vortex.deployment.msgpack')
        if os.path.isfile(stagefile):
            instance_data['paths']['stagefile'] = stagefile
            app.src_modinstance = core.VortexInstance(app, instance_data)
        else:
            raise Exception(f"Invalid stagingfolder: {staging_folder}")
        #instance_data['mods'] = stagefile.mods
        app.log.debug(f"Staging folder: {instance_data['paths']['staging_folder']}")
    elif app.source == 'ModOrganizer':
        instance_data['name'] = instance_name
        app.log.debug(f"Loading mod instance '{instance_data['name']}'...")
        app.log.debug(f"Mod manager: {app.source}")
        instance_path = os.path.join(os.getenv('LOCALAPPDATA'), 'ModOrganizer', instance_data['name'])
        instance_data['paths'] = {}
        # Get paths from instance ini file
        ini_file = os.path.join(instance_path, 'ModOrganizer.ini')
        with open(ini_file, 'r') as file:
            for line in file.readlines():
                if line.startswith("base_directory="):
                    instance_data['paths']['instance_path'] = os.path.normpath(line.split("=", 1)[1].strip())
                    instance_path = instance_data['paths']['instance_path']
                elif line.startswith("download_directory="):
                    instance_data['paths']['download_path'] = os.path.normpath(line.split("=", 1)[1])
        # Get mods from mods folder
        mods = [os.path.join(instance_path, 'mods', mod) for mod in os.listdir(os.path.join(instance_path, 'mods')) if os.path.isdir(os.path.join(instance_path, 'mods', mod))]
        instance_data['mods'] = mods
        app.src_modinstance = core.MO2Instance(app, instance_data)
        app.log.debug(f"Instance path: {instance_data['paths']['instance_path']}")
    else:
        raise Exception(f"Mod manager '{app.source}' is unsupported!")
    # Create destination instance
    app.log.debug(f"Creating destination instance...")
    if app.destination == 'Vortex':
        instance_data = {
            'name': "",
            'paths': {
                'staging_folder': ""
            }
        }
        app.dst_modinstance = core.VortexInstance(app, instance_data)
    elif app.destination == 'ModOrganizer':
        dst_instance_data = {
            'name': instance_name,
            'paths': {
                'instance_path': dst_instance_path,
                'download_path': f"{dst_instance_path}\\downloads",
                'mods_path': f"{dst_instance_path}\\mods",
                'profiles_path': f"{dst_instance_path}\\profiles",
                'overwrite_path': f"{dst_instance_path}\\overwrite"
            },
            'mods': app.src_modinstance.mods
        }
        app.dst_modinstance = core.MO2Instance(app, instance_data)
        appdata_path = os.path.join(os.getenv('LOCALAPPDATA'), 'ModOrganizer', instance_name)
        if os.path.isdir(appdata_path):
            app.log.debug("Wiping existing instance...")
            shutil.rmtree(appdata_path)
        if os.path.isdir(dst_instance_path):
            app.log.debug("Wiping existing instance data...")
            shutil.rmtree(dst_instance_path)
    else:
        raise Exception(f"Mod manager '{app.destination}' is unsupported!")
    
    app.log.debug(f"Done.")

    # console
    print("Type 'continue' to continue with automated testing.\nOr type another command to test a specific part of code.")
    while True:
        inpt = input("\n>>> ")
        if inpt == "continue":
            break
        else:
            eval(inpt)

    # Migrate
    app.migrate()

    # Print execution time to log
    app.log.debug(f"Testing took {time.time() - starttime} second(s). ({(time.time() - starttime) / 60} minute(s))")
