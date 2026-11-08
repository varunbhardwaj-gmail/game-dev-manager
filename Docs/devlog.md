# Dev log

## 2026-11-06
- Set up GameDev workspace and StreetRef tool (Mapillary reference photos).

## 2026-11-06 (evening)
- DelhiWalker references captured with StreetRef (Mapillary, CC BY-SA 4.0): 330 photos.
  - Route 1 Entry to Flyover: 96 photos, one 2016 drive that stays on the flyover.
  - Route 2 Entry to Building 5: 207 drive photos (mostly 2021 and 2025) + 27 Building 5 photos.
- Decision: routes traced from real photo tracks via survey.bat, after guessed waypoints missed the roads.
- Gap: Building 5 has no public photos from NE, SE, S or SW. Shoot those myself.
- Linked C:\GameDev to GitHub (game-dev-manager); added CLAUDE.md (workspace + DelhiWalker) and push.bat token guard.

## 2026-11-08
- New level for DelhiWalker: **Noida Expressway Route 1**, Pari Chowk to the DND Flyway entry (~26 km), towards DND only.
- Survey: `survey.py` now takes an area name; areas are lists of small boxes in `capture_plan.json` (`survey_areas`).
  Noida boxes hug the OpenStreetMap expressway line. Map zooms to the area, shows 360° panoramas in blue; `--map` redraws only.
- Route traced from the OSM towards-DND carriageway (not guessed); 2019 photo tracks sit a median 6 m from it.
- Downloaded 482 Mapillary photos (one 2019 dashboard-phone drive) into `NoidaExpressway_Route1/ne_r1_main`.
- StreetRef: route searches now only query tiles near the route (same results, ~10x faster on long routes).
- Decision: no look-around stops for this route; compass headings are unreliable and all photos face forward.
- Gaps: no photos for the first ~2.3 km from Pari Chowk, a 460 m gap at ~14.8 km, photos are 7 years old,
  no panoramas. Plan my own 360° camera drive for the whole route.
