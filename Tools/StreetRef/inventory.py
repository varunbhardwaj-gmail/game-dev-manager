#!/usr/bin/env python3
"""
inventory.py - write INVENTORY.md for a folder of StreetRef captures.

Usage:
  python inventory.py <references_folder> [--title "..."]

If <references_folder>/capture_plan.json defines "groups" (e.g. one per route), photos are listed
per group: <folder>/<group>/<capture>/manifest.json. Otherwise every sub-folder with a
manifest.json is listed on its own.
"""
import argparse, collections, datetime as dt, json, math, os


def human(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024: return f"{n:.0f} {u}"
        n /= 1024
    return f"{n:.1f} TB"


def hav(a, b):
    R = 6371000.0
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def route_pts(args):
    if "--route" in args:
        return [tuple(map(float, p.split(","))) for p in args[args.index("--route") + 1].split(";")]
    return None


def load(root, rel):
    path = os.path.join(root, rel, "manifest.json")
    if not os.path.isfile(path): return None
    m = json.load(open(path, encoding="utf-8"))
    for im in m.get("images", []):
        p = os.path.join(root, rel, im["file"])
        im["_exists"] = os.path.isfile(p)
        im["_bytes"] = os.path.getsize(p) if im["_exists"] else 0
        im["_rel"] = os.path.join(rel, im["file"]).replace("/", "\\")
    return m


def file_table(imgs, mode):
    extra_h = {"route": " Along route |", "point": " Side of building | View |"}.get(mode, "")
    extra_s = {"route": "---|", "point": "---|---|"}.get(mode, "")
    out = [f"| # | File | Lat, Lon | Facing |{extra_h} Taken | Author | Size | Links |",
           f"|---|---|---|---|{extra_s}---|---|---|---|"]
    sides = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    for im in imgs:
        fn = os.path.basename(im["file"]) + ("" if im["_exists"] else " ⚠ missing")
        extra = ""
        if mode == "route":
            extra = f" {im.get('along_route_m', '')} m |"
        elif mode == "point":
            b = im.get("bearing_from_centre")
            side = sides[int(((b or 0) + 22.5) // 45) % 8]
            extra = f" {side} ({b}°) | {im.get('view', '')} |"
        out.append(f"| {im['index']} | `{fn}` | {im['lat']}, {im['lon']} | {im['heading_deg']}° {im['facing']} |"
                   f"{extra} {im['captured']} | {im['author']} | {human(im['_bytes'])} | "
                   f"[Mapillary]({im['link']}) · [Map]({im['google_maps_pin']}) |")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--title", default="Reference inventory")
    a = ap.parse_args()
    root = os.path.abspath(a.folder)
    plan = {}
    if os.path.isfile(os.path.join(root, "capture_plan.json")):
        plan = json.load(open(os.path.join(root, "capture_plan.json"), encoding="utf-8"))

    groups = plan.get("groups")
    if not groups:  # flat layout fallback
        groups = [{"folder": "", "title": "All captures", "summary": ""}]
        caps = [{"name": n, "group": "", "description": "", "args": []}
                for n in sorted(os.listdir(root)) if os.path.isfile(os.path.join(root, n, "manifest.json"))]
    else:
        caps = plan["captures"]

    out = [f"# {a.title}", "",
           f"Generated {dt.datetime.now():%Y-%m-%d %H:%M} · Folder `{root}`", ""]
    overview = ["## Overview", "", "| Route | Folder | Length | Photos | Years | Size |", "|---|---|---|---|---|---|"]
    body = []
    grand_n = grand_b = 0

    for g in groups:
        gcaps = [c for c in caps if c.get("group", "") == g["folder"]]
        loaded = [(c, load(root, os.path.join(g["folder"], c["name"]) if g["folder"] else c["name"])) for c in gcaps]
        loaded = [(c, m) for c, m in loaded if m]
        imgs_all = [im for _, m in loaded for im in m["images"]]
        n, b = len(imgs_all), sum(im["_bytes"] for im in imgs_all)
        grand_n += n; grand_b += b
        years = collections.Counter(im["captured"][:4] for im in imgs_all)
        ystr = ", ".join(f"{y} ({k})" for y, k in sorted(years.items())) or "-"
        rp = next((route_pts(c["args"]) for c, _ in loaded if route_pts(c.get("args", []))), None)
        length = f"{sum(hav(p, q) for p, q in zip(rp, rp[1:])) / 1000:.2f} km" if rp else "-"
        overview.append(f"| {g['title']} | `{g['folder'] or '.'}\\` | {length} | {n} | {ystr} | {human(b)} |")

        body += [f"## {g['title']}", ""]
        if g.get("summary"): body += [g["summary"], ""]
        facts = [f"- **Folder:** `{g['folder'] or '.'}\\`",
                 f"- **Photos:** {n} ({human(b)}), taken {min((i['captured'] for i in imgs_all), default='-')} to "
                 f"{max((i['captured'] for i in imgs_all), default='-')}",
                 f"- **Photos by year:** {ystr}"]
        if rp:
            facts += [f"- **Route length:** {length}, {len(rp)} waypoints",
                      f"- **Start:** {rp[0][0]:.5f}, {rp[0][1]:.5f} ([map](https://www.google.com/maps?q={rp[0][0]},{rp[0][1]}))",
                      f"- **End:** {rp[-1][0]:.5f}, {rp[-1][1]:.5f} ([map](https://www.google.com/maps?q={rp[-1][0]},{rp[-1][1]}))"]
        drives = collections.Counter(im.get("sequence", "")[:8] for im in imgs_all if im.get("sequence"))
        if drives:
            facts.append("- **Source drives (Mapillary sequences):** " + ", ".join(f"`{s}` ({k})" for s, k in drives.most_common()))
        authors = sorted({im["author"] for im in imgs_all})
        if authors: facts.append(f"- **Photographers:** {', '.join(authors)} (CC BY-SA 4.0; credits in each ATTRIBUTION.md)")
        if g.get("look_for"): facts.append(f"- **What to look for:** {g['look_for']}")
        body += facts + [""]

        if not loaded:
            body += ["_No photos captured yet. Run capture.bat._", ""]
            continue

        body += ["### Sections", "", "| Section | Sub-folder | Photos | Notes |", "|---|---|---|---|"]
        for c, m in loaded:
            body.append(f"| {c.get('section', c['name'])} | `{c['name']}\\` | {len(m['images'])} | {m.get('description', '')} |")
        body.append("")

        for c, m in loaded:
            imgs = m["images"]
            mode = "route" if any(i.get("along_route_m") is not None for i in imgs) else \
                   ("point" if any(i.get("bearing_from_centre") is not None for i in imgs) else "")
            body += [f"### {c.get('section', c['name'])}", "",
                     f"Sub-folder `{(g['folder'] + chr(92)) if g['folder'] else ''}{c['name']}\\images\\` · "
                     f"also `manifest.csv`, `manifest.json`, `ATTRIBUTION.md`, `CLAUDE_BRIEF.md`", ""]
            if mode == "route" and imgs:
                bands = collections.OrderedDict()
                for im in imgs:
                    k = int((im.get("along_route_m") or 0) // 250)
                    bands.setdefault(k, []).append(im)
                body += ["Photos per 250 m stretch (start of the route = 0 m):", "",
                         "| Stretch | Photos | First file |", "|---|---|---|"]
                for k, ims in bands.items():
                    body.append(f"| {k*250}–{(k+1)*250} m | {len(ims)} | `{os.path.basename(ims[0]['file'])}` |")
                body.append("")
            if mode == "point" and imgs:
                sides = collections.Counter(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
                                            [int(((i.get("bearing_from_centre") or 0) + 22.5) // 45) % 8] for i in imgs)
                body += ["Photos by side of the building: " +
                         ", ".join(f"{s} {sides.get(s, 0)}" for s in ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]) +
                         " (sides with 0 need your own photos)", ""]
            body += file_table(imgs, mode) + [""]

    overview += ["", f"**Total:** {grand_n} photos, {human(grand_b)}", ""]
    naming = ["## How files are named", "",
              "`<section>_<nnnn>_<lat>_<lon>_h<heading>_<date>.jpg`", "",
              "- `nnnn`: order of travel along the route, or clockwise around Building 5",
              "- `lat`, `lon`: where the photo was taken",
              "- `h<heading>`: direction of travel/camera in degrees (0 N, 90 E, 180 S, 270 W)",
              "- `date`: when the photo was taken", ""]
    lic = ["## Licence", "",
           "All photos are from Mapillary under CC BY-SA 4.0. Use them as modelling reference; keep each "
           "ATTRIBUTION.md and credit Mapillary contributors in the game credits.", ""]
    with open(os.path.join(root, "INVENTORY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out + overview + naming + body + lic))
    print(f"Wrote {os.path.join(root, 'INVENTORY.md')} ({grand_n} photos)")


if __name__ == "__main__":
    main()
