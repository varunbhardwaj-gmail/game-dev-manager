#!/usr/bin/env python3
"""Maps where Mapillary photos exist around the DelhiWalker area (no images downloaded).
Writes survey_coverage.json and opens coverage_map.html on top of the planned routes."""
import json, os, subprocess, sys, webbrowser
here = os.path.dirname(os.path.abspath(__file__))
tools = os.path.normpath(os.path.join(here, "..", "..", "..", "Tools", "StreetRef"))
log = open(os.path.join(here, "survey_log.txt"), "w", encoding="utf-8")
cmd = [sys.executable, "-u", os.path.join(tools, "streetref.py"), "--name", "survey", "--survey",
       "--bbox", "28.4900,77.0820,28.5130,77.1080", "--out", here]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
for line in p.stdout:
    print(line.rstrip()); log.write(line.split("\r")[-1])
code = p.wait()
log.write(f"exit code {code}\n"); log.close()
if code == 0:
    data = json.load(open(os.path.join(here, "survey_coverage.json"), encoding="utf-8"))
    plan = json.load(open(os.path.join(here, "capture_plan.json"), encoding="utf-8"))
    html = open(os.path.join(here, "coverage_template.html"), encoding="utf-8").read()
    html = html.replace("__PHOTOS__", json.dumps([[q["lat"], q["lon"], q["date"], q["h"]] for q in data["photos"]]))
    html = html.replace("__PLAN__", json.dumps(plan))
    out = os.path.join(here, "coverage_map.html")
    open(out, "w", encoding="utf-8").write(html)
    print(f"\nOpened {out}")
    webbrowser.open("file:///" + out.replace("\\", "/"))
