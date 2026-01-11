@echo off
uv run core-lib\src\cutleast_core_lib\scripts\generate_qt_lupdate_file.py ^
--include-directory=src ^
--include-directory=core-lib\src\cutleast_core_lib ^
--include-directory=mod-manager-lib\src\mod_manager_lib ^
--exclude-file=src/resources_rc.py ^
--relative-to=. ^
--add-translation=res/loc/de.ts ^
--add-translation=res/loc/pt_BR.ts ^
--out-file=qt_lupdate.json ^
--include-path=src ^
--include-path=core-lib\src\cutleast_core_lib ^
--include-path=mod-manager-lib\src\mod_manager_lib
