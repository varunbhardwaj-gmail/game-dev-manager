# DelhiWalker

Realistic game set in Delhi NCR. First area: Gurugram, entering from Delhi on NH-48 around Shankar Chowk and DLF Cyber City.

## Reference photos (local only, not in Git)
Start with `References/INVENTORY.md`. It lists every photo by route and section with position, heading, date and links.

| Route | Folder | Contents |
|---|---|---|
| Route 1: Entry to Flyover | `References/Route1_Entry_to_Flyover/r1_main/` | ~96 photos, NH-48 southbound up and over the Shankar Chowk flyover, ends just after it. One 2016 drive, so buildings/signage may have changed. |
| Route 2: Entry to Building No. 5 | `References/Route2_Entry_to_Building5/r2_main/` | ~207 photos, same entry, left before the flyover, under it, curving left into Cyber City (mostly 2021 and 2025). |
| Building 5, all angles | `References/Route2_Entry_to_Building5/r2_building5_all_angles/` | ~27 photos pointing at DLF Building 5. Only N/NW/W sides covered; other sides need my own photos. |

- File names: `<section>_<nnnn>_<lat>_<lon>_h<heading>_<date>.jpg`; `nnnn` is driving order (or clockwise around Building 5).
- Each section folder also has `manifest.csv` (details per photo) and `CLAUDE_BRIEF.md`.
- Don't load all photos at once: sample ~8 spread along the stretch you're working on, then zoom in.
- Refresh or change captures: edit `References/capture_plan.json`, run `References/capture.bat`. Check coverage with `survey.bat`.

## Local facts to get right
- Left-hand traffic. Lanes ~3.5 m. Kerbs ~15 cm, often painted yellow-black; yellow-black concrete dividers and barriers.
- NH-48 here is a wide expressway with an elevated flyover at Shankar Chowk; high-tension pylons and wires run alongside.
- Cyber City: glass office towers, landscaped medians, autos and e-rickshaws, Cyber Hub signage, dust and haze.

## Build approach
1. Road layout from OpenStreetMap at true scale.
2. Blockout one short stretch (~100-200 m) from photos; propose dimensions first and wait for approval.
3. Compare with photos, then materials/decals, props and clutter, lighting and atmosphere.
