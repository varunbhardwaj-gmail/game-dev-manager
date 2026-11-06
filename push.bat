@echo off
setlocal
cd /d "%~dp0"
git add -A
rem --- safety: refuse to push anything that looks like a Mapillary token ---
git grep --cached -I -E -l "MLY[|][0-9]{6,}[|][0-9a-fA-F]{16,}" >nul 2>&1
if %errorlevel%==0 (
  echo.
  echo STOP: a Mapillary token was found in these files. Nothing was pushed.
  git grep --cached -I -E -l "MLY[|][0-9]{6,}[|][0-9a-fA-F]{16,}"
  git reset -q
  pause
  exit /b 1
)
echo Files changed:
git status --short
set "MSG=%~1"
if "%MSG%"=="" set /p "MSG=Commit message: "
if "%MSG%"=="" set "MSG=Update"
git diff --cached --quiet || git commit -q -m "%MSG%"
git push -u origin main
echo.
echo Done.
pause
