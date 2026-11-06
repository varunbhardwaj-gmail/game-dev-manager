@echo off
REM Usage: capture.bat <name> <lat,lon> [radius_m]
REM Example: capture.bat cyber_hub 28.4950,77.0890 200
if "%~2"=="" (
  echo Usage: capture.bat ^<name^> ^<lat,lon^> [radius_m]
  exit /b 1
)
set R=%~3
if "%R%"=="" set R=150
python "%~dp0streetref.py" --name %1 --point %2 --radius %R% --out "%~dp0..\..\References"
