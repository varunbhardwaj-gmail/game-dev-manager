# StreetRef

Collects street-level reference photos for any area from Mapillary (CC BY-SA 4.0),
names them by position/heading/date, and writes a brief that Claude can build from.

## One-time setup
1. Install Python 3.10+ (python.org) if you don't have it. No extra packages needed.
2. Create a free account at mapillary.com -> Dashboard -> Developers -> Register application.
3. Copy the **Client Token** (starts with `MLY|`) and run once in a terminal:
   `setx MAPILLARY_TOKEN "MLY|your_token_here"`
   Close and reopen the terminal afterwards.

## Usage
From this folder:

    python streetref.py --name cyber_hub --point 28.4950,77.0890 --radius 200
    python streetref.py --name golf_course_rd --bbox 28.4580,77.0950,28.4680,77.1050
    python streetref.py --name mg_road --route "28.4800,77.0800;28.4790,77.0900" --radius 40 --since 2023-01-01

Run `python streetref.py --help` for every option.
Tip: get coordinates by right-clicking a spot in Google Maps (the first menu item copies lat,lon).

Output goes to `C:\GameDev\References\<name>\` when run through `capture.bat`,
or `refs\<name>\` when run directly:
- `images\` - photos named `<name>_<n>_<lat>_<lon>_h<heading>_<date>.jpg`
- `manifest.csv` / `manifest.json` - details per photo, with Mapillary and Google Maps links
- `ATTRIBUTION.md` - photographer credits (keep it; credit Mapillary contributors in the game)
- `CLAUDE_BRIEF.md` - hand this plus a few images to Claude to start the build

## Rules
- Photos are reference only: rebuild geometry and materials, don't project the photos into the game.
- Use OpenStreetMap for exact road widths and junctions.
- Check coverage first at mapillary.com/app (green lines = photos available).
