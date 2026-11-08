#!/usr/bin/env python3
"""Maps where Mapillary photos exist in one survey area (no images downloaded).
Areas are listed in capture_plan.json under "survey_areas": each is a list of small boxes
(south,west,north,east). Writes survey_<area>.json and opens coverage_map_<area>.html.
Usage: python survey.py [area] [--map]   (default: gurugram; --map only redraws the map
from the saved survey, e.g. after editing routes in capture_plan.json)"""
import json, os, subprocess, sys, webbrowser
here = os.path.dirname(os.path.abspath(__file__))
tools = os.path.normpath(os.path.join(here, "..", "..", "..", "Tools", "StreetRef"))
plan = json.load(open(os.path.join(here, "capture_plan.json"), encoding="utf-8"))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
area = args[0] if args else "gurugram"
if area not in plan["survey_areas"]:
    sys.exit(f"Unknown area '{area}'. Choose from: {', '.join(k for k in plan['survey_areas'] if not k.startswith('_'))}")
boxes = plan["survey_areas"][area]
saved = os.path.join(here, f"survey_{area}.json")


def survey():
    """Runs StreetRef's survey on each box and merges the results."""
    parts = os.path.join(here, "_survey")  # one file per box
    log = open(os.path.join(here, f"survey_{area}_log.txt"), "w", encoding="utf-8")
    photos, failed = {}, []
    for i, box in enumerate(boxes, 1):
        print(f"\n--- {area}: box {i} of {len(boxes)} ({box}) ---"); log.write(f"box {i}: {box}\n")
        name = f"survey_{area}_{i:02d}"
        cmd = [sys.executable, "-u", os.path.join(tools, "streetref.py"), "--name", name, "--survey",
               "--bbox", box, "--out", parts]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        for line in p.stdout:
            print(line.rstrip()); log.write(line.split("\r")[-1])
        if p.wait() != 0:
            failed.append(i); continue
        for q in json.load(open(os.path.join(parts, f"{name}_coverage.json"), encoding="utf-8"))["photos"]:
            photos[q["id"]] = q  # boxes overlap a little, so de-duplicate by photo id
    photos = list(photos.values())
    summary = (f"{area}: {len(photos)} photo positions, {len({q['seq'] for q in photos})} drives, "
               f"{sum(q['pano'] for q in photos)} panoramas" + (f". Failed boxes: {failed}" if failed else ""))
    print("\n" + summary); log.write(summary + "\n"); log.close()
    json.dump({"area": area, "boxes": boxes, "photos": photos}, open(saved, "w", encoding="utf-8"))
    return photos


photos = json.load(open(saved, encoding="utf-8"))["photos"] if "--map" in sys.argv else survey()

html = open(os.path.join(here, "coverage_template.html"), encoding="utf-8").read()
html = html.replace("__PHOTOS__", json.dumps([[q["lat"], q["lon"], q["date"], q["h"], int(q["pano"])] for q in photos]))
html = html.replace("__PLAN__", json.dumps(plan)).replace("__BOXES__", json.dumps(boxes))
out = os.path.join(here, f"coverage_map_{area}.html")
open(out, "w", encoding="utf-8").write(html)
print(f"Opened {out}")
webbrowser.open("file:///" + out.replace("\\", "/"))
