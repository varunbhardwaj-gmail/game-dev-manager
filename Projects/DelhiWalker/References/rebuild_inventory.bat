@echo off
cd /d "%~dp0"
python "..\..\..\Tools\StreetRef\inventory.py" . --title "DelhiWalker reference inventory"
pause
