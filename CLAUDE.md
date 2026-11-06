# GameDev workspace

Hobby game-dev workspace (repo: varunbhardwaj-gmail/game-dev-manager). Tools: Unreal Engine 5, Blender with Blender MCP, Python.
Goal across projects: realistic visuals (not "PS2-looking"), with every asset legally usable in a released game.

## How I want to work
- I'm learning, so explain before acting: say what you'll create, the settings, and why, then wait for my OK.
- One step at a time (e.g. road surface, then kerbs, then materials). Show the result before moving on.
- Prefer clear, simple solutions I can understand and repeat myself over clever automation.
- At the end of a session, add a short entry to `Docs/devlog.md` (what we did, decisions, open gaps).

## Layout
- `Projects/<Game>/` : one folder per game. Each may have its own CLAUDE.md with game-specific context.
- `Tools/StreetRef/` : `streetref.py` (Mapillary reference photos), `inventory.py` (INVENTORY.md builder)
- `Docs/` : `devlog.md`, `asset_licences.csv`

## Hard rules
- Never commit or print secrets. The Mapillary token lives in `Tools/StreetRef/config.json` (git-ignored).
- Git holds code and docs only. Photos, generated data, media, .blend/.fbx and Unreal content stay local (see `.gitignore`).
  Commit/push with `push.bat "message"`, which blocks pushes containing a token.
- Asset sources allowed in the game: my own photos/footage, OpenStreetMap (credit "© OpenStreetMap contributors"),
  Fab/Megascans under their licence, and models built from scratch.
- Mapillary photos (CC BY-SA 4.0) and any Google Maps/Street View or YouTube imagery are REFERENCE ONLY:
  never use their pixels as textures, decals, skyboxes, or photogrammetry/splat input.
- Replace real brand logos with invented ones, don't reproduce real people's faces, use fake number plates.
- Record every asset that ships in `Docs/asset_licences.csv` (asset, used_in, source, licence, attribution_needed, notes).

## Modelling conventions
- Real-world scale in metres in Blender; check scale and units when exporting to Unreal (Unreal uses cm).
- Take exact road widths and junction shapes from OpenStreetMap; use photos for look, clutter and proportions.
- Realism comes mostly from lighting (Lumen), PBR materials with roughness variation, imperfection decals,
  clutter, atmosphere/haze, and correct proportions, so prioritise those over polygon detail.
