#!/usr/bin/env python3
"""
viewpoints.py - "look around" stops along a route, built from Mapillary photos.

Mapillary photos are fixed snapshots, so this can't rotate a camera. Instead, every --step metres
along the route it picks, from ANY drive that passed, the best photo facing each direction
relative to the road: ahead, right, behind, left. Directions nobody photographed stay empty
and are reported as gaps.

Usage:
  python viewpoints.py --name r1_stops --route "lat,lon;lat,lon;..." [--step 50] [--radius 30] --out <folder>

Output: <out>/<name>/
  images/<name>_s012_ahead_<lat>_<lon>_h<heading>_<date>.jpg
  manifest.json / manifest.csv (same format as streetref.py, plus stop, view, stop_lat, stop_lon)
  STOPS.md          which directions each stop has
  ATTRIBUTION.md    photographer credits (CC BY-SA 4.0)
"""
import argparse, csv, datetime as dt, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import streetref as sr  # reuse API, geometry and download helpers

VIEWS = {"ahead": 0, "right": 90, "behind": 180, "left": 270}


def point_at(pts, d):
    """Point d metres along the route, and the road bearing there."""
    run = 0.0
    for a, b in zip(pts, pts[1:]):
        L = sr.haversine(a, b)
        if run + L >= d or b == pts[-1]:
            t = 0 if L == 0 else max(0.0, min(1.0, (d - run) / L))
            return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])), sr.bearing(a, b)
        run += L
    return pts[-1], sr.bearing(pts[-2], pts[-1])


def angdiff(a, b):
    return abs(((a - b) + 180) % 360 - 180)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--route", required=True, help='"lat,lon;lat,lon;..."')
    ap.add_argument("--step", type=float, default=50, help="metres between stops")
    ap.add_argument("--radius", type=float, default=30, help="max metres from a stop to a usable photo")
    ap.add_argument("--sector", type=float, default=45, help="max degrees off the wanted direction")
    ap.add_argument("--views", default="ahead,right,behind,left")
    ap.add_argument("--exclude-seq", default="", help="comma-separated sequence ids/prefixes to ignore")
    ap.add_argument("--size", default="2048", choices=["256", "1024", "2048", "original"])
    ap.add_argument("--out", default="refs")
    ap.add_argument("--notes", default="")
    args = ap.parse_args()

    token = sr.load_token()
    if not token:
        sys.exit("No Mapillary token found (see Tools/StreetRef/config.json).")
    pts = [sr.parse_pt(x) for x in args.route.split(";") if x.strip()]
    views = [v.strip() for v in args.views.split(",") if v.strip() in VIEWS]
    excl = [x.strip() for x in args.exclude_seq.split(",") if x.strip()]

    dlat, dlon = sr.metres_to_deg(args.radius + 10, pts[0][0])
    bbox = [min(p[0] for p in pts) - dlat, min(p[1] for p in pts) - dlon,
            max(p[0] for p in pts) + dlat, max(p[1] for p in pts) + dlon]
    total = sum(sr.haversine(a, b) for a, b in zip(pts, pts[1:]))
    print(f"[{args.name}] route {total:.0f} m, a stop every {args.step:.0f} m, views: {', '.join(views)}")

    cands = []
    for img in sr.fetch_candidates(bbox, token, pts, args.radius + 10):
        if img.get("is_pano"): continue
        if excl and any((img.get("sequence") or "").startswith(x) for x in excl): continue
        lon, lat = img["geometry"]["coordinates"]
        img["_p"] = (lat, lon)
        img["_h"] = (img.get("computed_compass_angle", img.get("compass_angle", 0)) or 0) % 360
        cands.append(img)
    print(f"  {len(cands)} usable photos near the route")
    newest = max((c.get("captured_at", 0) for c in cands), default=0)

    picks, gaps, n_stops = [], [], int(total // args.step) + 1
    used = set()
    for s in range(n_stops):
        d = min(s * args.step, total)
        stop, _ = point_at(pts, d)
        # road direction measured over ~150 m so short GPS wiggles in the route don't skew it
        a, _ = point_at(pts, max(0.0, d - 75)); b, _ = point_at(pts, min(total, d + 75))
        road = sr.bearing(a, b)
        row = {"stop": s + 1, "along_m": round(d), "lat": stop[0], "lon": stop[1], "road_bearing": round(road)}
        taken = []  # headings already used at this stop
        for v in sorted(views, key=lambda x: ["ahead", "behind", "right", "left"].index(x)):
            want = (road + VIEWS[v]) % 360
            best, best_score = None, None
            for c in cands:
                if c["id"] in used: continue
                dist = sr.haversine(stop, c["_p"])
                if dist > args.radius: continue
                off = angdiff(c["_h"], want)
                if off > args.sector: continue
                # only use a photo for the direction it is closest to (no "right" that is really "behind")
                if any(angdiff(c["_h"], (road + VIEWS[o]) % 360) < off for o in VIEWS if o != v): continue
                # views at one stop must face clearly different ways (no near-duplicate scenes)
                if any(angdiff(c["_h"], t) < 60 for t in taken): continue
                years_old = (newest - c.get("captured_at", 0)) / (365.25 * 86400000)
                score = dist + off * 0.3 + years_old * 4  # near, well aimed, recent
                if best_score is None or score < best_score:
                    best, best_score = c, score
            row[v] = best
            if best:
                used.add(best["id"])
                taken.append(best["_h"])
                picks.append((row, v, best))
        gaps.append(row)
    print(f"  {len(gaps)} stops, {len(picks)} views found out of {len(gaps) * len(views)} possible")

    root = os.path.join(args.out, args.name)
    img_dir = os.path.join(root, "images")
    os.makedirs(img_dir, exist_ok=True)
    size_key = "thumb_original_url" if args.size == "original" else f"thumb_{args.size}_url"
    manifest = []
    for n, (row, v, img) in enumerate(picks, 1):
        lat, lon = img["_p"]
        h = int(round(img["_h"])) % 360
        date = dt.datetime.fromtimestamp(img.get("captured_at", 0) / 1000, dt.timezone.utc).date().isoformat()
        fname = f"{args.name}_s{row['stop']:03d}_{v}_{lat:.5f}_{lon:.5f}_h{h:03d}_{date}.jpg"
        print(f"  [{n}/{len(picks)}] {fname}", end="\r")
        path = os.path.join(img_dir, fname)
        if not os.path.exists(path):
            url = img.get(size_key) or img.get("thumb_2048_url")
            if not url or not sr.download(url, path):
                continue
        manifest.append({
            "file": f"images/{fname}", "index": n, "stop": row["stop"], "view": v,
            "stop_lat": round(row["lat"], 6), "stop_lon": round(row["lon"], 6),
            "lat": round(lat, 6), "lon": round(lon, 6), "heading_deg": h, "facing": sr.heading_name(h),
            "captured": date, "along_route_m": row["along_m"], "bearing_from_centre": None,
            "is_pano": False, "camera": f"{img.get('make', '')} {img.get('model', '')}".strip(),
            "author": (img.get("creator") or {}).get("username", "unknown"),
            "mapillary_id": img["id"], "sequence": img.get("sequence", ""),
            "link": f"https://www.mapillary.com/app/?pKey={img['id']}",
            "google_maps_pin": f"https://www.google.com/maps?q={lat:.6f},{lon:.6f}",
        })
    print()

    keep = {os.path.basename(m["file"]) for m in manifest}
    stale = [f for f in os.listdir(img_dir) if f.lower().endswith(".jpg") and f not in keep]
    for f in stale:
        os.remove(os.path.join(img_dir, f))
    if stale:
        print(f"  removed {len(stale)} old images from a previous run")

    desc = f"{len(gaps)} stops every {args.step:.0f} m along the route; views {', '.join(views)}"
    with open(os.path.join(root, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"area": args.name, "description": desc, "generated": dt.datetime.now().isoformat(timespec="seconds"),
                   "images": manifest}, f, indent=2)
    if manifest:
        with open(os.path.join(root, "manifest.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(manifest[0].keys())); w.writeheader(); w.writerows(manifest)

    got = {(m["stop"], m["view"]): os.path.basename(m["file"]) for m in manifest}
    lines = [f"# Look-around stops: {args.name}", "", args.notes, "",
             f"A stop every {args.step:.0f} m. Each view is the best real photo from any drive within "
             f"{args.radius:.0f} m, facing within {args.sector:.0f}° of that direction (relative to the road). "
             "'—' means nobody photographed that direction there.", "",
             "Note: side-window shots record the direction of travel, so some 'ahead' or 'behind' views "
             "actually look out of a side window.", "",
             "| Stop | Along route | Position | " + " | ".join(v.capitalize() for v in views) + " |",
             "|---|---|---|" + "---|" * len(views)]
    for r in gaps:
        cells = [("✓" if (r["stop"], v) in got else "—") for v in views]
        lines.append(f"| {r['stop']} | {r['along_m']} m | [{r['lat']:.5f}, {r['lon']:.5f}]"
                     f"(https://www.google.com/maps?q={r['lat']:.6f},{r['lon']:.6f}) | " + " | ".join(cells) + " |")
    counts = {v: sum(1 for r in gaps if (r["stop"], v) in got) for v in views}
    lines += ["", "Coverage: " + ", ".join(f"{v} {counts[v]}/{len(gaps)}" for v in views), ""]
    with open(os.path.join(root, "STOPS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    authors = sorted({m["author"] for m in manifest})
    with open(os.path.join(root, "ATTRIBUTION.md"), "w", encoding="utf-8") as f:
        f.write(f"# Reference imagery: {args.name}\n\nStreet-level photos from Mapillary, licensed CC BY-SA 4.0. "
                f"Used as modelling reference only.\n\nContributors: {', '.join(authors)}\n\n")
        for m in manifest:
            f.write(f"- {m['file']} by {m['author']} - {m['link']} (CC BY-SA 4.0)\n")
    print("  coverage: " + ", ".join(f"{v} {counts[v]}/{len(gaps)}" for v in views))
    print(f"Done: {root}  ({len(manifest)} images, see STOPS.md)")


if __name__ == "__main__":
    main()
