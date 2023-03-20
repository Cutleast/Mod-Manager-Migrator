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
<a href="https://www.nexusmods.com/skyrimspecialedition/mods/87160"><img src="misc_assets/GiO_NM.png" height="60px"/> </a>
<a href="https://ko-fi.com/cutleast"><img src="misc_assets/KoFi.png" height="60px"/> </a>
<br>
MMM - for a better modding environment.
</p>


# ❗WARNING!!!

**This is in a very early Alpha stage and issues/errors are very likely to occur! Use at your own risk!**


# 📄Description

This is a tool for migrating modding instances between various mod managers (currently only Vortex to MO2). This program is in a very early Alpha stage and feedback is crucial for me to continue developing. Currently only Skyrim SE from Vortex to ModOrganizer 2 (MO2) is supported with support for more games and mod managers planned. **Only Windows is supported!**


# 🕹Features

- create mod order from Vortex conflict rules
- fully automated migration
- new instance is customizable

### Planned Features

- Vortex as migration destination
- hardlink method to use same files between mod managers
- support for more games (suggestions are welcome)
- support for more mod managers (suggestions are also welcome)


# 🔧Usage

To migrate an instance from Vortex to MO2, for example, follow these steps:

1. Start Vortex and make sure that the profile you want to migrate is deployed.
2. Close Vortex and start MMM (Mod Manager Migrator).
3. Click on "Add source", select Vortex and click on "Next".
4. Select the staging folder of Vortex and click on "Done".
5. Click on "Add destination", select MO2 and click on "Next".
6. Set paths name as you like it and click on "Done".
7. Click on "Migrate" and wait for it to finish.
8. After migration is done, open Vortex and purge game folder.
9. Close Vortex, open it never again and you're done!


# 🫶Contributing

### 1. Translations

Create your translation for your desired language from en-US.json under `<Path to MMM>`/data/locales and give it a proper name: for example: "en-US.json" or "de-DE.json". Send it to me (cutleast@gmail.com) and I will add it as soon as I can.

### 2. Feedback (Suggestions/Issues)

If you encountered an issue/error or have a suggestion, create a issue with sufficient information.

### 3. Code contributions

1. Install Python 3.10 (Make sure that you add it to PATH!)
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


# 🔗Credits

- Code by Cutleast ([GitHub](https://github.com/Cutleast) | [NexusMods](https://www.nexusmods.com/users/65733731))
- Program icon and idea by Wuerfelhusten ([NexusMods](https://www.nexusmods.com/users/122160268))
- Qt by The [Qt Company Ltd](https://qt.io)
- Material icons by [Google LLC](https://github.com/Templarian/MaterialDesign)
- Elusive Icons von [Team Redux](https://reduxframework.com/)
- FontAwesome Icons von [FontAwesome](https://github.com/FortAwesome/Font-Awesome)
