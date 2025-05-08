<p align="center">
<picture>
  <img alt="" src="res/icons/mmm.svg" width=256 height=256>
</picture>
</p>
<p align="center">
<picture>
  <img alt="" src="misc_assets/HeadLineGH.svg" width=512>
</picture>
<br>
<a href="https://discord.gg/pqEHdWDf8z"><img src="https://i.imgur.com/VMdA0q7.png" height="60px"/> </a>
<a href="https://www.nexusmods.com/site/mods/545/"><img src="misc_assets/GiO_NM.png" height="60px"/> </a>
<a href="https://ko-fi.com/cutleast"><img src="misc_assets/KoFi.png" height="60px"/> </a>
<br>
<strong>MMM - Move Mods Masterfully.</strong>
</p>

# 📄Description

This is a tool for migrating modding instances (modlists) between mod managers.

**Only Windows is supported!**

# 🕹Features

- Fully automated migration
- Automatic detection of used game folder
- New instance is customizable
- Migrate to existing instances to merge two instances into one (experimental)
- Support for global and portable MO2 instances
  - Automatically download and install MO2 for portable MO2 instances
- Automatically converts Vortex conflict rules to a MO2 loadorder and vice versa
  - Also supports separate file conflicts and .mohidden files
- Uses hardlinks by default when source and destination are on the same disk to save on space
  - Can be disabled in *File* > *Settings* > *Use hardlinks [...]*
  - [What are hardlinks?](./Hardlinks.md)
- Automatic detection of Windows path length limit
  - Windows paths are limited to 255 characters which can cause issues for mods with long paths
  - MMM will ask at the start to disable that limit when not already disabled

### What gets migrated and what not

| Migrated                                                                                                                            | Not Migrated                                                                         |
| ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Mods including basic metadata required for the link to Nexus Mods: version, file name, mod id, file id, game id                     | Advanced metadata not required for link to Nexus Mods: author, description, category |
| Tools/Executables (eg. xEdit, Bodyslide, SSE-AT, etc.) including link to installed mod (if any), working directory, start arguments | Custom tool icons                                                                    |
| Conflict rules                                                                                                                      | Overwrite folder (MO2 -> Vortex)                                                     |
| Separate file conflict rules                                                                                                        | LOOT rules (Vortex -> MO2 and vice versa)                                            |
| Plugin loadorder: plugins.txt and loadorder.txt                                                                                     | Downloads and link to download folder                                                |

### Supported Games

- Enderal (+ Special Edition)
- Fallout 3
- Fallout 4
- Fallout: New Vegas
- Oblivion (not the Remastered version)
- Skyrim (all versions incl. VR and GOG)

### Supported Mod Managers

- Vortex
- Mod Organizer 2

### Known Issues/Limitations

- Cannot migrate from/to Vortex if it is used in "Shared" mode ([Vortex &gt; Settings &gt; Vortex](https://imgur.com/fyKAgK7))

# 🔧Usage

To migrate an instance, follow these steps:

1. Select the game of the instance you want to migrate.
2. Select the source mod manager.
3. Enter the required information for the respective mod manager.
4. Click on "Load instance..." to load and display the source instance.
5. Select whether you want to create a new instance or want to migrate to an existing one (experimental).
6. Select the destination mod manager (may be the source mod manager to duplicate an instance).
7. Either customize the destination instance as desired or select one similar to the source.
8. Click on "Migrate" and wait for it to finish.
9. If there are errors, check them carefully and (where appropiate) follow their recommendations and instructions.

# ❓Frequently Asked Questions (FAQ)

### Can I delete the old instance after the migration is complete?

Yes, but before deleting the old instance make sure that the migrated instance works fine and that there were no errors during the migration.
**I take no responsibility for modlists that get deleted without verifying that the destination instance works!**

### I got an OverwriteModNotSupportedError for a mod called "Overwrite" when migrating an MO2 instance

This is fully intentional and expected when migrating a MO2 instance with a non-empty overwrite folder to Vortex, as Vortex does not have anything similar (generated files stay in the game folder).
As suggested in the error message, to solve this, create a mod from the files in the overwrite folder and rerun the migration. Do this by right-click > *Create mod from overwrite* on the mod "Overwrite" at the very bottom of your modlist in MO2.

### I got a FileNotFoundError for one or multiple mods

Please check the length of the mentioned file path: If it is longer than 255 characters, you didn't fix the path limit when prompted after starting MMM.
If the path is shorter than 255 characters, please create an issue or create a post in #support on our [Discord server](https://discord.gg/pqEHdWDf8z).

### Are my LOOT rules migrated from Vortex to MO2 or vice versa?

No, not at the moment. Please see [What gets migrated and what not](#what-gets-migrated-and-what-not) for a full up-to-date list.

# 🫶Contributing

## Feedback (Suggestions/Issues)

If you encountered an issue/error or have a suggestion, open an issue with sufficient information.

## Code contributions

### 1. Install requirements

1. Install [Python 3.12](https://www.python.org/downloads/) (Make sure that you add it to PATH!)
2. Install [uv](https://github.com/astral-sh/uv#installation)
3. Clone repository
4. Open a terminal in the cloned repository folder
5. Run the following command to init your local environment and to install all dependencies
   `uv sync`

### 2. Execute from source

1. Open a terminal in the root folder of this repo
2. Execute main file with uv
   `uv run src\main.py`

### 3. Compile and build executable

1. Run `build.bat` from the root folder of this repo.
2. The executable and all dependencies are built in the `dist/MMM`-Folder and get packed in a `dist/Mod Manager Migrator v[version].zip`.

## Translations

Make sure to follow the steps under [Code contributions](#code-contributions) above to install all requirements, including the Qt tools to translate this app.

1. To generate a translation file for a new language, copy the following line in [update_lupdate_file.bat](./update_lupdate_file.bat):
`--add-translation=res/loc/de.ts ^`, insert it directly beneath it and change the `de` value to the short code of your language.
For example, to generate a file for French, the new line would look like this: `--add-translation=res/loc/fr.ts ^`
2. Run `update_lupdate_file.bat && update_qts.bat` to generate the translation file for your language.
3. Open the translation file in Qt Linguist with `uv run pyside6-linguist res/loc/<language>.ts`, eg. `uv run pyside6-linguist res/loc/fr.ts`.
4. Translate MMM and save the file with Ctrl+S.
5. For your language to show up in MMM's settings: add a line, similar to the existing languages, under `class Language(BaseEnum):` in [localisation.py](./src/core/utilities/localisation.py). For example, for French: `French = "fr_FR"`.
6. Optional: Run `compile_qts.bat && uv run src\main.py` and change the language in *Settings* to your translation (and restart) to see your translation in action.
7. Create a pull request from your changes and I will check over it and merge it if there are no issues with it.

# 🔗Credits

- Code by Cutleast ([GitHub](https://github.com/Cutleast) | [NexusMods](https://next.nexusmods.com/profile/Cutleast))
- Icon, modpage images and idea by Wuerfelhusten ([NexusMods](https://next.nexusmods.com/profile/Wuerfelhusten))
- Qt by The [Qt Company Ltd](https://qt.io)
- FontAwesome Icons by [FontAwesome](https://github.com/FortAwesome/Font-Awesome)

See [licenses.py](./src/core/utilities/licenses.py) for a full list of used libraries, dependencies and their respective licenses.
