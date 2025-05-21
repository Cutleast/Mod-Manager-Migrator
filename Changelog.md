# v3.0.1

- Fix separators losing their loadorder position when migrating from MO2 -> MO2
- Fix "What are Hardlinks?" button in settings
- Fix migration of tools if the mapped mod is not installed
- Fix "Load selected instance..." button not being disabled when loading a global MO2 instance without a profile selected

# v3.0.0

* Rewrite the entire codebase
* Add automated tests
* Rework entire UI
* Add support for portable MO2 instances
  * Add option to automatically download and install MO2 for portable instances
* Add support for Root Builder plugin (MO2)
* Add support for migrating into existing instances
  * This is considered experimental and should be used at your own risk!
* Add support for migrating tools
* Add limited support for MO2's overwrite folder (only when migrating to other MO2 instances)
* Improve UX and error messages

# v2.5

- Fix AV detections by changing the builder from Nuitka to cx_Freeze
- Add support for FO3, FO:NV and Oblivion
- Improve installation path detection
- Improve conflict rule sorting for Vortex -> MO2 (thanks to [FORMless000](https://github.com/Cutleast/Mod-Manager-Migrator/commits?author=FORMless000)!)
- Fix "continue" localisation
- Fix game dialog layout
- Fix TypeError when hashing utilities.mod.Mod
- Fix "{USERDATA}" not resolving when migrating to Vortex
- Fix migration to Vortex if there are no profiles
- Fix UnboundLocalError when loading a mod with an incomplete meta.ini (MO2)

# v2.41

- (Hopefully) fixed Virus warning

# v2.40

- Catch shutil copy errors for root files
- Major code formatting and update
- Improved visual style
- Reworked localisation handler
- Fixed Enderal Special Edition in Vortex
- Fixed case where migrated folder name would end with a dot
- Replaced "Keep Log File" setting with setting for number of latest log files

# v2.31

- Fixed migration to Vortex if Vortex has no mods installed for that game

# v2.30

- Re-added Vortex as destination
- Fixed Vortex database processing

# v2.26

- Fixed migration to MO2 when using hardlink mode (hardlinks were not created)

# v2.25

- Temporarily disabled Vortex as migration destination due to extreme long database saving
- Fixed loading instance (Vortex & MO2)
- Fixed duplicate conflict rules
- Fixed loadorder sorting

# v2.24

- Fixed loading Vortex instance

# v2.23

- Fixed datetime.datetime exception when migrating to Vortex

# v2.22

- Fixed sorting issue

# v2.21

- Fixed existing but incomplete mod metadata (MO2)

# v2.16

- Fixed illegal characters in mod names (e.g., ":")

# v2.15

- Hotfix for v2.14 (there was a misplaced bracket in source)

# v2.14

- Fixed unknown rule type: conflicts

# v2.13

- Fixed separate file conflicts
- Fixed install state of mods that were migrated to Vortex

# v2.12

- Fixed (possible) issues with too large Vortex database by just reading what's necessary

# v2.11

- Fixed missing install paths in Vortex's database (again)

# v2.03

- Fixed wrong default mods folder for Vortex

# v2.02

- Fixed too long paths (> 260 characters) for ini parser

# v2.01

- Fixed "dead links" in Vortex's database

# v2.00

- Added Vortex as destination
- Added support for Fallout 4, Skyrim, Enderal, and Enderal SE
- Added feature to select mods that should be migrated
- Fixed too long paths (> 260 characters)
- Fixed missing keys in database due to standard paths

# v2.10

- Added support for separate file conflicts

# v2.02

- Fixed wrong default mods folder for Vortex

# v1.10

- Complete rework of load order generation
- Huge performance improvement
- Increased load order reliability
- Switched from deployment files as source to Vortex's level database
- Vortex does not have to be deployed anymore
- Any Vortex profile (if it has mods installed) can be migrated (only enabled mods get migrated!)
- Temporarily removed download folder migration (planned return for v2.0)

# v1.04

- Fixed crash while attempting to migrate '.gitattributes'
- Updated Chinese translation

# v1.03

- Fixed crash if LOOT is installed but there is no userlist.yaml
- Fixed crash for outdated localisations by adding a fallback to English strings
- Log file gets saved if at least one uncaught exception occurs (user setting is ignored, then)
- Added input dialog for manual game path selection if path could not be found in registry

# v1.02

- 'userlist.yaml' is now copied from Vortex's LOOT to installed LOOT (existing 'userlist.yaml' gets renamed)
- Improved update check
- Updated update link to new mod page
- Improved game path detection (now supports GOG version)

# v1.01

- Added Chinese translation by Abab-bk

# v1.00

- First initial release
- Vortex -> MO2 Migration
- Hardlink mode & Copy mode
