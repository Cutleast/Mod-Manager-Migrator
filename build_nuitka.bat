@echo off
nuitka --msvc="latest" --standalone --disable-console --include-data-dir=".\src\data=.\data" --enable-plugin=pyqt6 --nofollow-import-to=tkinter --windows-icon-from-ico=".\src\icons\mmm.ico" --output-filename="MMM.exe"  ".\src\main.py"
echo Compilation complete. Press a key to exit.
pause > nul