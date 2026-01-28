@echo off
echo Building Windows Update Controller EXE...
echo.

cd /d "C:\Users\mazen\Projects\Systems\WindowsUpdateDisabler"

echo Using PyInstaller to create standalone executable...
python -m PyInstaller --onefile --windowed --name "WindowsUpdateController" --icon="" windows_update_disabler.py

echo.
echo Build complete! 
echo Executable location: dist\WindowsUpdateController.exe
echo.
pause