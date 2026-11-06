#!/usr/bin/env python3
"""Runs every capture in capture_plan.json with StreetRef (one folder per route group),
then writes INVENTORY.md. Everything printed is also saved to capture_log.txt.
Usage: python run_captures.py [capture_name ...]   (no names = run all)"""
import datetime as dt, json, os, shutil, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
tools = os.path.normpath(os.path.join(here, "..", "..", "..", "Tools", "StreetRef"))
plan = json.load(open(os.path.join(here, "capture_plan.json"), encoding="utf-8"))
only = sys.argv[1:]
log = open(os.path.join(here, "capture_log.txt"), "w", encoding="utf-8")


def say(text):
    print(text); log.write(text + "\n"); log.flush()


def run(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                         encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    for line in p.stdout:
        line = line.rstrip("\n"); print(line); log.write(line.split("\r")[-1] + "\n")
    log.flush()
    return p.wait()


say(f"Run started {dt.datetime.now():%Y-%m-%d %H:%M:%S}, Python {sys.version.split()[0]}")
# remove folders from the older layout (generated output only)
for old in plan.get("legacy_folders", []):
    path = os.path.join(here, old)
    if os.path.isfile(os.path.join(path, "manifest.json")):
        shutil.rmtree(path); say(f"Removed old-layout folder {old}")

failed = []
for c in plan["captures"]:
    if only and c["name"] not in only:
        continue
    out = os.path.join(here, c["group"])
    say(f"\n=== {c['group']} / {c['name']} ===\n{c['description']}")
    cmd = [sys.executable, "-u", os.path.join(tools, "streetref.py"), "--name", c["name"], "--out", out,
           "--notes", c["description"]] + c["args"]
    code = run(cmd)
    if code != 0:
        failed.append(c["name"]); say(f"!! {c['name']} exited with code {code}")
run([sys.executable, os.path.join(tools, "inventory.py"), here, "--title", f"{plan['project']} reference inventory"])
say("\nDone." + (f" Failed: {', '.join(failed)}" if failed else " All captures succeeded."))
