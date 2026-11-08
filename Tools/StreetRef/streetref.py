#!/usr/bin/env python3
"""
streetref.py - collect street-level reference photos for a game area from Mapillary.

Images are CC BY-SA 4.0 (faces/plates auto-blurred by Mapillary). Use them as
REFERENCE for modelling. Credits are written to ATTRIBUTION.md automatically.

Setup (once):
  1. Create a free account at mapillary.com -> Dashboard -> Developers -> register app
  2. Copy the "Client Token" (starts with MLY|) into config.json next to this script:
       { "mapillary_token": "MLY|xxxx" }
     (The MAPILLARY_TOKEN environment variable also works.)

Examples:
  # 200 m around a point
  python streetref.py --name cyber_hub --point 28.4950,77.0890 --radius 200

  # A rectangle (south,west,north,east)
  python streetref.py --name golf_course_rd --bbox 28.4580,77.0950,28.4680,77.1050

  # Along a route: list of lat,lon points, collects within --radius of the path
  python streetref.py --name mg_road --route "28.4800,77.0800;28.4790,77.0900;28.4780,77.1000" --radius 40

Useful options:
  --max 150          stop after this many images
  --spacing 15       keep at most one photo every N metres (avoids near-duplicates)
  --since 2023-01-01 only photos taken on/after this date (roads change!)
  --no-pano          skip 360-degree panoramas
  --size 2048        image size: 256, 1024, 2048 or original
  --out refs         output root folder

Output:  refs/<name>/
  images/<name>_0001_28.49501_77.08903_h145_2024-03-02.jpg
  manifest.csv / manifest.json   one row per image (coords, heading, date, author, link)
  ATTRIBUTION.md                 credits you must keep with the project
  CLAUDE_BRIEF.md                ready-made context to paste/attach for Claude
"""
import argparse, csv, datetime as dt, json, math, os, sys, time, urllib.error, urllib.parse, urllib.request

API = "https://graph.mapillary.com/images"
FIELDS = ("id,captured_at,compass_angle,computed_compass_angle,geometry,is_pano,"
          "sequence,width,height,make,model,creator,thumb_256_url,thumb_1024_url,"
          "thumb_2048_url,thumb_original_url")
TILE_DEG = 0.004  # Mapillary rejects large boxes; query in small tiles


# ---------- geometry helpers ----------
def haversine(a, b):
    R = 6371000.0
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def metres_to_deg(m, lat):
    return m / 111320.0, m / (111320.0 * max(math.cos(math.radians(lat)), 1e-6))


def dist_to_segment(p, a, b):
    # local flat approximation, fine at street scale
    lat0 = math.radians(p[0])
    def xy(q): return (q[1] * 111320 * math.cos(lat0), q[0] * 110540)
    px, py = xy(p); ax, ay = xy(a); bx, by = xy(b)
    dx, dy = bx - ax, by - ay
    t = 0 if dx == dy == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


ROUTE_PTS = None   # set when --route is used
CENTRE = None      # set when --point is used


def bearing(a, b):
    la1, la2 = math.radians(a[0]), math.radians(b[0])
    dl = math.radians(b[1] - a[1])
    y = math.sin(dl) * math.cos(la2)
    x = math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def along_route(p, pts):
    """Distance in metres from the route start to the point's nearest spot on the route."""
    best, best_d, run = 0.0, float("inf"), 0.0
    lat0 = math.radians(p[0])
    def xy(q): return (q[1] * 111320 * math.cos(lat0), q[0] * 110540)
    for a, b in zip(pts, pts[1:]):
        (px, py), (ax, ay), (bx, by) = xy(p), xy(a), xy(b)
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
        d = math.hypot(px - (ax + t * dx), py - (ay + t * dy))
        if d < best_d:
            best_d, best = d, run + t * math.sqrt(L2)
        run += math.sqrt(L2)
    return best


def parse_pt(s):
    lat, lon = (float(v) for v in s.strip().split(","))
    return lat, lon


# ---------- area definition ----------
def build_area(args):
    """Returns (bbox [s,w,n,e], filter_fn(lat,lon)->bool, description)."""
    if args.point:
        global CENTRE
        c = parse_pt(args.point)
        CENTRE = c
        dlat, dlon = metres_to_deg(args.radius, c[0])
        bbox = [c[0] - dlat, c[1] - dlon, c[0] + dlat, c[1] + dlon]
        return bbox, lambda p: haversine(c, p) <= args.radius, f"{args.radius} m around {c[0]},{c[1]}"
    if args.bbox:
        s, w, n, e = (float(v) for v in args.bbox.split(","))
        return [s, w, n, e], lambda p: True, f"box S{s} W{w} N{n} E{e}"
    if args.route:
        global ROUTE_PTS
        pts = [parse_pt(x) for x in args.route.split(";") if x.strip()]
        if len(pts) < 2:
            sys.exit("--route needs at least two points")
        ROUTE_PTS = pts
        dlat, dlon = metres_to_deg(args.radius, pts[0][0])
        bbox = [min(p[0] for p in pts) - dlat, min(p[1] for p in pts) - dlon,
                max(p[0] for p in pts) + dlat, max(p[1] for p in pts) + dlon]
        segs = list(zip(pts, pts[1:]))
        return bbox, (lambda p: min(dist_to_segment(p, a, b) for a, b in segs) <= args.radius), \
            f"route of {len(pts)} points, {args.radius} m either side"
    sys.exit("Give one of --point, --bbox or --route")


def tiles(bbox):
    s, w, n, e = bbox
    lat = s
    while lat < n:
        lon = w
        while lon < e:
            yield [lon, lat, min(lon + TILE_DEG, e), min(lat + TILE_DEG, n)]  # API order: w,s,e,n
            lon += TILE_DEG
        lat += TILE_DEG


# ---------- network ----------
def get_json(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as ex:
            body = ex.read().decode("utf-8", "replace")[:300]
            if ex.code in (401, 403):
                sys.exit(f"Mapillary refused the token (HTTP {ex.code}): {body}\n"
                         "Check config.json has the Client Token (starts with MLY|), not the secret.")
            if i == tries - 1:
                sys.exit(f"Mapillary error HTTP {ex.code}: {body}")
            print(f"  retry (HTTP {ex.code})", file=sys.stderr)
            time.sleep(2 * (i + 1))
        except Exception as ex:
            if i == tries - 1:
                raise
            print(f"  retry ({ex})", file=sys.stderr)
            time.sleep(2 * (i + 1))


def download(url, path, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r, open(path, "wb") as f:
                f.write(r.read())
            return True
        except Exception as ex:
            if i == tries - 1:
                print(f"  failed: {ex}", file=sys.stderr)
                return False
            time.sleep(2 * (i + 1))


def tile_near_route(t, route, radius):
    """True if tile t (w,s,e,n) could hold a photo within `radius` m of the route:
    its centre is within radius + half the tile's diagonal of some route segment."""
    w, s, e, n = t
    c = ((s + n) / 2, (w + e) / 2)
    half_diag = haversine((s, w), (n, e)) / 2
    return any(dist_to_segment(c, a, b) <= radius + half_diag for a, b in zip(route, route[1:]))


def fetch_candidates(bbox, token, route=None, radius=0):
    """All photos in bbox, searched tile by tile. With a route, only tiles near it are searched."""
    seen = {}
    all_tiles = list(tiles(bbox))
    if route:
        n_all = len(all_tiles)
        all_tiles = [t for t in all_tiles if tile_near_route(t, route, radius)]
        print(f"  searching {len(all_tiles)} of {n_all} tiles (only those near the route)")
    for k, t in enumerate(all_tiles, 1):
        q = urllib.parse.urlencode({"access_token": token, "fields": FIELDS,
                                    "bbox": ",".join(f"{v:.6f}" for v in t), "limit": 2000})
        print(f"  searching tile {k}/{len(all_tiles)}", end="\r")
        for img in get_json(f"{API}?{q}").get("data", []):
            seen[img["id"]] = img
    print()
    return list(seen.values())


# ---------- config ----------
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_token():
    """Token from config.json next to this script; falls back to the MAPILLARY_TOKEN env variable."""
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding="utf-8-sig") as f:
                tok = (json.load(f).get("mapillary_token") or "").strip()
            if tok.startswith("MLY|"):
                return tok
            if tok and "PASTE" not in tok:
                print("Warning: token in config.json doesn't start with MLY| - is it the Client Token?", file=sys.stderr)
                return tok
        except json.JSONDecodeError as ex:
            sys.exit(f"config.json is not valid JSON ({ex}). Keep the quotes and comma exactly as in the example.")
    return os.environ.get("MAPILLARY_TOKEN", "").strip() or None


# ---------- main ----------
def heading_name(deg):
    return ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][int(((deg % 360) + 22.5) // 45) % 8]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help="short area name, used for folder and file names")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--point", help="lat,lon")
    g.add_argument("--bbox", help="south,west,north,east")
    g.add_argument("--route", help='"lat,lon;lat,lon;..."')
    ap.add_argument("--radius", type=float, default=150, help="metres (for --point / --route)")
    ap.add_argument("--max", type=int, default=150)
    ap.add_argument("--spacing", type=float, default=15, help="min metres between kept photos")
    ap.add_argument("--since", help="YYYY-MM-DD")
    ap.add_argument("--no-pano", action="store_true")
    ap.add_argument("--size", default="2048", choices=["256", "1024", "2048", "original"])
    ap.add_argument("--out", default="refs")
    ap.add_argument("--notes", default="", help="your own notes about the area, added to the brief")
    ap.add_argument("--facing-centre", type=float, default=None, metavar="DEG",
                    help="with --point: keep only photos whose camera points at the centre (within DEG degrees)")
    ap.add_argument("--only-seq", default="", help="comma-separated Mapillary sequence ids (or prefixes) to keep; others dropped")
    ap.add_argument("--exclude-seq", default="", help="comma-separated sequence ids (or prefixes) to drop")
    ap.add_argument("--survey", action="store_true",
                    help="don't download images; save every photo position in the area to <out>/<name>_coverage.json")
    args = ap.parse_args()

    token = load_token()
    if not token:
        sys.exit("No Mapillary token found. Put it in " + CONFIG_PATH +
                 " (\"mapillary_token\": \"MLY|...\") or set MAPILLARY_TOKEN.")

    name = "".join(c if c.isalnum() or c in "-_" else "_" for c in args.name.lower())
    bbox, inside, desc = build_area(args)
    since_ms = int(dt.datetime.fromisoformat(args.since).timestamp() * 1000) if args.since else 0

    print(f"[{name}] {desc}")
    cands = fetch_candidates(bbox, token, ROUTE_PTS if args.route else None, args.radius)
    print(f"  {len(cands)} photos found in search box")
    if args.survey:
        os.makedirs(args.out, exist_ok=True)
        pts = [{"id": i["id"], "lat": round(i["geometry"]["coordinates"][1], 6),
                "lon": round(i["geometry"]["coordinates"][0], 6),
                "h": int(round(i.get("computed_compass_angle", i.get("compass_angle", 0)) or 0)) % 360,
                "date": dt.datetime.fromtimestamp(i.get("captured_at", 0) / 1000, dt.timezone.utc).date().isoformat(),
                "seq": i.get("sequence", ""), "pano": bool(i.get("is_pano"))} for i in cands]
        path = os.path.join(args.out, f"{name}_coverage.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"area": desc, "bbox_swne": bbox, "photos": pts}, f)
        print(f"Survey saved: {path} ({len(pts)} photo positions, {len({p['seq'] for p in pts})} sequences)")
        return

    rows = []
    n_area = n_pano = n_date = n_face = n_seq = 0
    only_seq = [x.strip() for x in args.only_seq.split(',') if x.strip()]
    excl_seq = [x.strip() for x in args.exclude_seq.split(',') if x.strip()]
    for img in cands:
        lon, lat = img["geometry"]["coordinates"]
        if not inside((lat, lon)): n_area += 1; continue
        if args.no_pano and img.get("is_pano"): n_pano += 1; continue
        if img.get("captured_at", 0) < since_ms: n_date += 1; continue
        seq = img.get("sequence", "") or ""
        if (only_seq and not any(seq.startswith(x) for x in only_seq)) or \
           (excl_seq and any(seq.startswith(x) for x in excl_seq)):
            n_seq += 1; continue
        if args.facing_centre is not None and CENTRE:
            h = img.get("computed_compass_angle", img.get("compass_angle", 0)) or 0
            if not img.get("is_pano") and abs(((h - bearing((lat, lon), CENTRE)) + 180) % 360 - 180) > args.facing_centre:
                n_face += 1; continue
        rows.append(img)
    print(f"  dropped: {n_area} outside area, {n_date} older than --since, {n_pano} panoramas, {n_face} not facing the centre, {n_seq} from other drives")
    if cands:
        lats = [i["geometry"]["coordinates"][1] for i in cands]; lons = [i["geometry"]["coordinates"][0] for i in cands]
        print(f"  photos in box span lat {min(lats):.5f}-{max(lats):.5f}, lon {min(lons):.5f}-{max(lons):.5f}")

    # newest first, then thin out near-duplicates
    rows.sort(key=lambda i: i.get("captured_at", 0), reverse=True)
    kept = []
    for img in rows:
        lon, lat = img["geometry"]["coordinates"]
        head = img.get("computed_compass_angle", img.get("compass_angle", 0)) or 0
        too_close = any(haversine((lat, lon), (k["lat"], k["lon"])) < args.spacing
                        and abs(((head - k["heading"]) + 180) % 360 - 180) < 45 for k in kept)
        if too_close: continue
        kept.append({"img": img, "lat": lat, "lon": lon, "heading": head})
        if len(kept) >= args.max: break

    # order so numbering follows the street (route), goes round the spot (point), or W->E (bbox)
    for k in kept:
        k["along_m"] = along_route((k["lat"], k["lon"]), ROUTE_PTS) if ROUTE_PTS else None
        k["bearing_from_centre"] = bearing(CENTRE, (k["lat"], k["lon"])) if CENTRE else None
    if ROUTE_PTS:
        kept.sort(key=lambda k: k["along_m"])
    elif CENTRE:
        kept.sort(key=lambda k: k["bearing_from_centre"])
    else:
        kept.sort(key=lambda k: (round(k["lon"], 4), k["lat"]))
    print(f"  keeping {len(kept)} after area/date/spacing filters")
    if not kept:
        sys.exit("Nothing to download. Try a bigger radius, older --since, or check coverage at mapillary.com/app")

    root = os.path.join(args.out, name)
    img_dir = os.path.join(root, "images")
    os.makedirs(img_dir, exist_ok=True)
    size_key = "thumb_original_url" if args.size == "original" else f"thumb_{args.size}_url"

    manifest = []
    for n, k in enumerate(kept, 1):
        img = k["img"]
        date = dt.datetime.fromtimestamp(img.get("captured_at", 0) / 1000, dt.timezone.utc).date().isoformat()
        h = int(round(k["heading"])) % 360
        fname = f"{name}_{n:04d}_{k['lat']:.5f}_{k['lon']:.5f}_h{h:03d}_{date}.jpg"
        url = img.get(size_key) or img.get("thumb_2048_url")
        print(f"  [{n}/{len(kept)}] {fname}", end="\r")
        if not os.path.exists(os.path.join(img_dir, fname)):
            if not url or not download(url, os.path.join(img_dir, fname)):
                continue
        creator = (img.get("creator") or {}).get("username", "unknown")
        manifest.append({
            "file": f"images/{fname}", "index": n, "lat": round(k["lat"], 6), "lon": round(k["lon"], 6),
            "heading_deg": h, "facing": heading_name(h), "captured": date,
            "along_route_m": None if k["along_m"] is None else round(k["along_m"]),
            "bearing_from_centre": None if k["bearing_from_centre"] is None else round(k["bearing_from_centre"]),
            "view": ("towards centre" if CENTRE and abs(((h - bearing((k["lat"], k["lon"]), CENTRE)) + 180) % 360 - 180) < 60
                     else ("away from centre" if CENTRE else "")),
            "is_pano": bool(img.get("is_pano")), "camera": f"{img.get('make', '')} {img.get('model', '')}".strip(),
            "author": creator, "mapillary_id": img["id"], "sequence": img.get("sequence", ""),
            "link": f"https://www.mapillary.com/app/?pKey={img['id']}",
            "google_maps_pin": f"https://www.google.com/maps?q={k['lat']:.6f},{k['lon']:.6f}",
        })
    print()

    # remove images left over from an earlier run of this same capture
    keep = {os.path.basename(m["file"]) for m in manifest}
    stale = [f for f in os.listdir(img_dir) if f.lower().endswith(".jpg") and f not in keep]
    for f in stale:
        os.remove(os.path.join(img_dir, f))
    if stale:
        print(f"  removed {len(stale)} old images from a previous run")

    with open(os.path.join(root, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"area": name, "description": desc, "bbox_swne": bbox,
                   "generated": dt.datetime.now().isoformat(timespec="seconds"), "images": manifest}, f, indent=2)
    with open(os.path.join(root, "manifest.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(manifest[0].keys()))
        w.writeheader(); w.writerows(manifest)

    authors = sorted({m["author"] for m in manifest})
    with open(os.path.join(root, "ATTRIBUTION.md"), "w", encoding="utf-8") as f:
        f.write(f"# Reference imagery: {name}\n\nStreet-level photos from Mapillary, licensed CC BY-SA 4.0.\n"
                f"Used as modelling reference only.\n\nContributors: {', '.join(authors)}\n\n")
        for m in manifest:
            f.write(f"- {m['file']} by {m['author']} - {m['link']} (CC BY-SA 4.0)\n")

    dates = sorted(m["captured"] for m in manifest)
    with open(os.path.join(root, "CLAUDE_BRIEF.md"), "w", encoding="utf-8") as f:
        f.write(f"""# Build brief: {name}

Area: {desc}
Bounding box (S,W,N,E): {', '.join(f'{v:.5f}' for v in bbox)}
Photos: {len(manifest)}, taken {dates[0]} to {dates[-1]}
Location context: Delhi NCR, India. Left-hand traffic. Lanes ~3.5 m, kerbs ~15 cm.

{('My notes: ' + args.notes) if args.notes else ''}

## How to use these photos
- File names encode position and camera direction: <area>_<n>_<lat>_<lon>_h<heading>_<date>.jpg
  (heading 0 = north, 90 = east). manifest.csv has the full details.
- Images are numbered roughly along the street, so neighbouring numbers are neighbouring spots.
- Use them as REFERENCE ONLY: rebuild geometry, props and materials; do not project the photos into the scene.
- For exact road widths and junction shapes, prefer OpenStreetMap data over estimates from photos.

## Suggested first pass
1. Look at 5-10 photos spread across the area and list: road type, lanes, dividers, kerb style,
   footpaths, street furniture, signage, vegetation, building heights and typical materials.
2. Propose a blockout plan with dimensions before building anything.
3. Build one short stretch first, then compare it against the photos.
""")

    print(f"Done: {root}  ({len(manifest)} images)")
    print("Keep ATTRIBUTION.md with your project and add Mapillary contributors to your game credits if you ship anything derived closely from these.")


if __name__ == "__main__":
    main()
