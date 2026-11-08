# DelhiWalker

Realistic game set in Delhi NCR. First area: driving into Gurugram from Delhi on NH-48 (old NH-8),
around Shankar Chowk and DLF Cyber City. Current goal: make it as close to the real place as possible.
No damage, wrecks or post-apocalyptic look yet; that comes later.

## Reference photos: what we have and why

- Source: **Mapillary** street-level photos (CC BY-SA 4.0), collected with `C:\GameDev\Tools\StreetRef`.
  They are **not** Google Street View.
- Google Street View/Maps imagery and YouTube frames are **never saved or used**; their terms forbid
  capturing them. Looking at Street View live in a browser while modelling is fine.
- All photos are **reference only**: rebuild everything from scratch. Never project them or use them
  as textures, decals, skyboxes, or photogrammetry/splat input.
- Mapillary has no 360° panoramas here, so "look around" views are assembled from different drives
  (see stops below). For true 360° views, the plan is my own drive with a roof-mounted 360° camera.

Start with `References/INVENTORY.md`. It lists every photo by route and section with position,
heading, date, author and links.

| Folder | Contents |
|---|---|
| `References/Route1_Entry_to_Flyover/r1_main/` | ~124 photos in driving order. NH-48 southbound: the Delhi-side flyover comes down, a very wide open stretch (old toll plaza area), Ambience Mall and glass offices ahead/left, then up and over the Shankar Chowk flyover, ending just after it (~2.4 km). |
| `References/Route1_Entry_to_Flyover/r1_stops/` | A stop every 50 m with the best photo facing ahead/behind/right/left where one exists. `STOPS.md` shows which directions each stop has. |
| `References/Route2_Entry_to_Building5/r2_main/` | ~215 photos. Same start, keep left before the Shankar Chowk flyover, under it, curving left into Cyber City to DLF Building 5 (~3 km). |
| `References/Route2_Entry_to_Building5/r2_stops/` | Look-around stops for Route 2, same format. |
| `References/Route2_Entry_to_Building5/r2_building5_all_angles/` | 27 photos pointing at DLF Building 5. Only N/NW/W sides covered; other sides need my own photos. |
| `References/NoidaExpressway_Route1/ne_r1_main/` | **Second level.** 482 photos, towards DND only: Pari Chowk along the Noida-Greater Noida Expressway, over the Mahamaya flyover, Dadri Main Road past Film City to the DND Flyway entry (~26 km). One 2019 dashboard-phone drive: a photo every ~60 m to Sector 137, every ~35 m after. None for the first ~2.3 km from Pari Chowk; one 460 m gap at ~14.8 km. No look-around stops (compass headings unreliable, all photos face forward). |

Reading the photos:
- File names: `<section>_<nnnn>_<lat>_<lon>_h<heading>_<date>.jpg`. `nnnn` is driving order (or
  clockwise around Building 5); stops use `_s<stop>_<view>_`. `manifest.csv` has details per photo.
- Mixed years: Route 1's first ~600 m is from 2022, the Shankar Chowk flyover section from 2016,
  extra views from 2021; Route 2 is mostly 2021 and 2025. Prefer the newest where they disagree,
  and flag differences.
- Some are side-window shots: the heading is the travel direction, not always where the camera points.
  Stops mix drives, so lighting and season vary; use them for layout and objects, not light matching.
- Don't load all photos at once: sample ~8-10 spread along the stretch, then zoom in.
- Exact road widths, lane counts and junction shapes come from OpenStreetMap, not photo estimates.

## Legal clean-up (always)
- Invented number plates in the correct Haryana/Delhi format; never real ones.
- No real brand names or logos (shops, billboards, fuel stations, gantry text, car badges): invent our own.
- No recognisable people.
- Vehicles are generic designs inspired by common Indian types, not copies of real branded models.
- Log every shipped asset's source and licence in `C:\GameDev\Docs\asset_licences.csv`.

## What to take seriously from the photos
Road layout and proportions, lane markings, kerbs and yellow-black/black-white dividers, crash
barriers and flyover parapets, flyover pillars, deck and ramps, gantry signs (design and colour,
invented text), street lights, high-tension pylons and wires, roadside walls, trees, dust, building
types and heights, haze and light. Local facts: left-hand traffic, lanes ~3.5 m, kerbs ~15 cm.

Vehicles: catalogue the types seen, how common each is, and their look (colours, dirt, loads,
roof racks, painted truck art, green CNG buses, autos, e-rickshaws, two-wheelers with riders,
hatchbacks, MPVs/SUVs, taxis). Use this for in-game vehicle design and mix, not exact traffic.

## How we work
- I'm learning, so explain before acting and wait for my OK at each step.
- Write findings to `Docs/route1_reference_notes.md` (route sections with distances, road
  cross-section, flyover structure, roadside elements, buildings/landmarks, materials and colours,
  vehicle catalogue, open questions) before building.
- Build one stretch at a time. First: the Shankar Chowk flyover with its approach. Propose a
  blockout with real dimensions (Blender via MCP, for Unreal Engine 5), build only after approval,
  then compare with the photos. Then materials/decals, props and clutter, lighting and atmosphere.

## Refreshing or extending the references
All in `References/` (photos and generated files stay local; only scripts and the plan go to Git):
- `capture_plan.json`: routes (traced from real photo tracks), drive filters and sections
- `capture.bat`: re-download everything and rebuild INVENTORY.md; `capture_stops.bat`: stops only
- `survey.bat [area]` (or `survey_noida_expressway.bat`): map where photos exist (no downloads), shown in
  `coverage_map_<area>.html`. Areas (`gurugram`, `noida_expressway`) are lists of small boxes under
  `survey_areas` in `capture_plan.json`. `python survey.py <area> --map` redraws the map without re-surveying.
- Noida Expressway Route 1 follows the OpenStreetMap towards-DND carriageway (one-way ways), resampled every 100 m.
- `rebuild_inventory.bat`: rebuild INVENTORY.md only
- Mapillary token lives in `C:\GameDev\Tools\StreetRef\config.json` (git-ignored, never print or commit it)
