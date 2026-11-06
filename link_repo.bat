@echo off
setlocal
cd /d "%~dp0"
where git >nul 2>&1 || (echo Git is not installed. Install it from git-scm.com & pause & exit /b 1)
where gh >nul 2>&1 || (echo GitHub CLI is not installed. & pause & exit /b 1)

gh auth status >nul 2>&1 || gh auth login
gh auth setup-git

if not exist .git (git init -q -b main) else (echo This folder is already a Git repo.)
git remote get-url origin >nul 2>&1 || git remote add origin https://github.com/varunbhardwaj-gmail/game-dev-manager.git
git fetch -q origin || (echo Could not reach the GitHub repo. & pause & exit /b 1)
rem Point local main at GitHub's main without touching any files on disk
git reset -q origin/main
git branch -q -u origin/main main

rem Commit identity: use your GitHub no-reply address if Git has none set
git config user.name >nul 2>&1 || (for /f "usebackq delims=" %%n in (`gh api user --jq .login`) do git config user.name "%%n")
git config user.email >nul 2>&1 || (for /f "usebackq delims=" %%e in (`gh api user --jq "(.id|tostring) + \"+\" + .login + \"@users.noreply.github.com\""`) do git config user.email "%%e")

echo.
echo Linked to https://github.com/varunbhardwaj-gmail/game-dev-manager
call "%~dp0push.bat" "Add StreetRef tool, DelhiWalker capture plan and docs"
