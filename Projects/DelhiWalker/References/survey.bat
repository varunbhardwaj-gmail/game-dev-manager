@echo off
cd /d "%~dp0"
rem Usage: survey.bat [area]   e.g. survey.bat noida_expressway (default: gurugram)
python survey.py %1
pause
