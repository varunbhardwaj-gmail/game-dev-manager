@echo off
cd /d "%~dp0"
python "..\..\..\Tools\StreetRef\streetref.py" --name north_preview --out _preview --route "28.53490,77.11090;28.53350,77.10800;28.53180,77.10520;28.53000,77.10410;28.52850,77.10300;28.52700,77.10200;28.52470,77.10050;28.52210,77.09880;28.51970,77.09710;28.51710,77.09530;28.51420,77.09350;28.51300,77.09310" --radius 30 --only-seq PfhSTFRl,LEAbmTO9 --spacing 80 --size 1024 > _preview_log.txt 2>&1
type _preview_log.txt
pause
