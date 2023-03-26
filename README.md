<p align="center">
<picture>
  <img alt="" src="src/data/icons/mmm.svg" width=256 height=256>
</picture>
</p>
<p align="center">
<picture>
  <img alt="" src="misc_assets/HeadLineGH.svg" width=512>
</picture>
<br>
<a href="https://www.nexusmods.com/site/mods/545/"><img src="misc_assets/GiO_NM.png" height="60px"/> </a>
<a href="https://ko-fi.com/cutleast"><img src="misc_assets/KoFi.png" height="60px"/> </a>
<br>
<strong>MMM - Move Mods Masterfully.</strong>
</p>


# ❗Please note!!!

**This is the first initial release of this tool. I take no responsibility for any problems that may occur. In the current version everything works relatively stable. But to get a clear picture, I depend on more extensive testing from the community.**


# 📄Description

This is a tool for migrating modding instances between various mod managers (currently only Vortex to MO2). This program is in a very early Alpha stage and feedback is crucial for me to continue developing. Currently only Skyrim SE from Vortex to ModOrganizer 2 (MO2) is supported with support for more games and mod managers planned. **Only Windows is supported!**


# 🕹Features

- Create mod order from Vortex conflict rules
- Fully automated migration
- New instance is customizable
- Hardlink and copy method
- Custom LOOT rules (userlist.yaml) are migrated

### Planned Features
- Vortex as migration destination
- Support for more games (suggestions are welcome)
- Support for more mod managers (NMM (CE) is the next, but suggestions are welcome)


# 🔧Usage

### To migrate an instance from Vortex to MO2, for example, follow these steps:

1. Make sure that Vortex is not running and start MMM (Mod Manager Migrator).
3. Click on "Add source", select Vortex and click on "Next".
4. Select the profile you want to migrate and click on "Done".
5. Click on "Add destination", select MO2 and click on "Next".
6. Set paths name as you like it and click on "Done".
7. Click on "Migrate" and wait for it to finish.


# 🫶Contributing

### 1. Translations

Create your translation for your desired language from en-US.json under `<Path to MMM>`/data/locales and give it a proper name: for example: "en-US.json" or "de-DE.json". Put it in the locales folder and make a pull request.

### 2. Feedback (Suggestions/Issues)

If you encountered an issue/error or have a suggestion, open an issue with sufficient information.

### 3. Code contributions

1. Install Python 3.9 (Make sure that you add it to PATH!)
2. Clone repository
3. Open terminal in repository folder
4. Type in following command to set up virtual environment:
   `python -m venv src\venv`
5. Activate virtual environment by typing:
   `src\venv\Scripts\activate`
6. Run setup_venv.bat by typing:
   `setup_venv.bat`

### 4. Execute from source

1. If virtual environment not already set up follow steps under "3. Code contributions"
2. Open terminal in src folder
3. Type following command to activate virtual environment:
   `venv\Scripts\activate`
4. Execute main file:
   `python main.py`

### 5. Compile and build executable

1. Follow the steps on this page [Nuitka.net](https://nuitka.net/doc/user-manual.html#usage) to install a C Compiler
2. Run `build_nuitka.bat` with activated virtual environment from the root folder of this repo.
3. The executable and its dependencies are created in the main.dist-Folder.


# 💻How it works

### Mod order reconstruction from Vortex conflict rules:

1. It reads Vortex's level database
2. Creates dict of mods and overwriting mods
3. A load order is constructed according to the overwrites


# 🔗Credits

- Code by Cutleast ([GitHub](https://github.com/Cutleast) | [NexusMods](https://www.nexusmods.com/users/65733731))
- Program icon and idea by Wuerfelhusten ([NexusMods](https://www.nexusmods.com/users/122160268))
- Qt by The [Qt Company Ltd](https://qt.io)
- Material icons by [Google LLC](https://github.com/google/material-design-icons)
- Elusive Icons by [Redux Framework](http://elusiveicons.com/)
- FontAwesome Icons by [FontAwesome](https://github.com/FortAwesome/Font-Awesome)
