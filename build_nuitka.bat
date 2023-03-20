@echo off
nuitka --msvc="latest" --standalone --disable-console --include-data-dir=".\src\data=.\data" --include-data-dir=".\src\venv\Lib\site-packages\qtawesome=.\qtawesome" --enable-plugin=pyside6 --nofollow-import-to=tkinter --windows-icon-from-ico=".\src\data\icons\mmm.ico" --output-filename="MMM.exe"  ".\src\main.py"
echo Compilation complete. Press a key to exit.
pause > nul