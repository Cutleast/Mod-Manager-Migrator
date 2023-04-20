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

**I take no responsibility for any problems that may occur.**

# 📄Description

This is a tool for migrating modding instances between various mod managers.

**Only Windows is supported!**

# 🕹Features

- Fully automated migration
- New instance is customizable
- Hardlink and copy method

### Supported Games

- Skyrim (Special Edition)
- Enderal (Special Edition)
- Fallout 4

#### Planned games

- Oblivion
- Nehrim
- Morrowind
- Fallout 3
- Fallout: New Vegas
- You (the community) decide, feel free to suggest

### Supported Mod Managers

- Vortex
- Mod Organizer 2

#### Planned Mod Managers

- Nexus Mod Manager Community Edition
- Feel free to suggest

### Known Issues

- Cannot migrate from Vortex if it is used in "Shared" mode ([Vortex &gt; Settings &gt; Vortex](https://imgur.com/fyKAgK7))
- Some Windows Defender versions detect MMM as malware and delete the executable

# 🔧Usage

### To migrate an instance, follow these steps:

1. Click on "Add source", select your source and click on "Next".
2. Select the instance you want to migrate and click on "Done".
3. Click on "Add destination", select your destination and click on "Next".
4. Set paths as you like it and click on "Done".
5. Click on "Migrate" and wait for it to finish.

# 🫶Contributing

### 1. Translations

Create your translation for your desired language from en-US.json under `<Path to MMM>`/data/locales and give it a proper name: for example: "en-US.json" or "de-DE.json". Put it in the locales folder and make a pull request.

### 2. Feedback (Suggestions/Issues)

If you encountered an issue/error or have a suggestion, open an issue with sufficient information.

### 3. Code contributions

1. Install Python 3.9 (Make sure that you add it to PATH!)
2. Clone repository
3. Open terminal in repository folder
4. Type in following command to set up virtual environment and install all requirements:
   `setup_venv.bat`
5. Activate virtual environment by typing:
   `src\venv\Scripts\activate`

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

### Mod order from Vortex conflict rules:

1. It reads Vortex's level database
2. Creates dict of mods and overwriting mods
3. A load order is constructed according to the overwrites

### Vortex conflict rules from mod order

1. Scans all files in all mods
2. Checks for overwritten mods
3. Creates a rule for every overwritten mod

# 🔗Credits

- Code by Cutleast ([GitHub](https://github.com/Cutleast) | [NexusMods](https://www.nexusmods.com/users/65733731))
- Design and idea by Wuerfelhusten ([NexusMods](https://www.nexusmods.com/users/122160268))
- Qt by The [Qt Company Ltd](https://qt.io)
- FontAwesome Icons by [FontAwesome](https://github.com/FortAwesome/Font-Awesome)
