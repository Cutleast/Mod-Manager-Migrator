@echo off
uv run scripts\generate_qt_lupdate_file.py ^
--include-directory=src ^
--exclude-file=src/resources_rc.py ^
--relative-to=. ^
--add-translation=res/loc/de.ts ^
--out-file=qt_lupdate.json ^
--include-path=src
