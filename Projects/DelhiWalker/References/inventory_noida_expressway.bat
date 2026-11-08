@echo off
cd /d "%~dp0"
python "..\..\..\Tools\StreetRef\inventory.py" . --group NoidaExpressway_Route1 --title "Noida Expressway Route 1 inventory (Pari Chowk to DND)"
pause
