# game-dev-manager

Shared workspace for my hobby game projects: reusable tools, per-game capture plans and dev docs.
Only code and docs live in Git. Photos, generated data and secrets stay on the local PC (see `.gitignore`).

## Layout
- `Projects\` : one folder per game (e.g. `Projects\DelhiWalker`)
- `Tools\` : reusable scripts shared across games
  - `StreetRef\` : collects street-level reference photos from Mapillary (CC BY-SA 4.0) and writes inventories
- `Docs\` : dev log and asset licence tracker (`asset_licences.csv`)

## First-time setup on a PC
1. Copy `Tools\StreetRef\config.example.json` to `config.json` in the same folder and paste your Mapillary Client Token.
   `config.json` is git-ignored.
2. Install Python 3.10+ (no extra packages needed).

## Git workflow
- `link_repo.bat` : one-time: links this folder to GitHub and pushes the first commit
- `push.bat "message"` : commits and pushes. It refuses to push if a Mapillary token is found in any file.

Keep every shipped asset traceable: note its source and licence in `Docs\asset_licences.csv`.
