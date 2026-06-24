#!/usr/bin/env python3
"""
Build a Subway Builder buildings_index.json from a building-footprint GeoJSON
(exported from OSM via osmium/overpass), with size-reduction options so the
result stays in the range the game loads (keep gzip output under ~50 MB).

Output schema (Subway Builder "optimized" index):
{
  "cs": <cell size deg>, "bbox": [minlon,minlat,maxlon,maxlat], "grid": [nx,ny],
  "cells": [[cellX, cellY, buildingIdx, ...], ...],
  "buildings": [{"b": [minlon,minlat,maxlon,maxlat], "f": depth, "p": [[lon,lat],...]}],
  "stats": {"count": N, "maxDepth": d}
}

Usage:
  python3 build_buildings_index.py buildings.geojson buildings_index.json \
      --bbox -88.3768 41.3778 -87.2205 42.4949 \
      --cell 0.01 --min-area 150 --precision 5 --simplify 0.00004 --exclude-stations
  gzip -f buildings_index.json

Size levers: --min-area (drop small structures), --simplify (fewer vertices),
--precision (fewer digits). --cell is a performance knob, not a size lever.
--exclude-stations drops railway/transit station buildings so you can build there.
"""
import argparse, json, math, sys


def foundation_depth(props):
    levels = props.get("building:levels") or props.get("levels")
    height = props.get("height")
    try:
        if height is not None:
            h = float(str(height).split()[0])
            return -min(30.0, max(5.0, round(h * 0.12, 1)))
        if levels is not None:
            return -min(30.0, max(5.0, 4.0 + float(levels)))
    except (ValueError, TypeError):
        pass
    return -5.0


def is_station(props):
    """True for railway/transit station buildings (excluded so you can build there)."""
    if props.get("building") in ("train_station", "transportation"):
        return True
    if props.get("railway") in ("station", "halt"):
        return True
    if props.get("public_transport") == "station":
        return True
    if props.get("station") in ("subway", "train", "light_rail"):
        return True
    return False


def exterior_ring(geom):
    if geom["type"] == "Polygon":
        return geom["coordinates"][0]
    if geom["type"] == "MultiPolygon":
        return max((poly[0] for poly in geom["coordinates"]), key=len)
    return None


def bbox_area_m2(min_lon, min_lat, max_lon, max_lat):
    latmid = math.radians((min_lat + max_lat) / 2.0)
    m_lat = 111320.0
    m_lon = 111320.0 * math.cos(latmid)
    return abs((max_lon - min_lon) * m_lon) * abs((max_lat - min_lat) * m_lat)


def simplify_ring(ring, tol):
    """Radial-distance simplification; keeps the ring closed and valid (>=4 pts)."""
    if tol <= 0 or len(ring) <= 5:
        return ring
    out = [ring[0]]
    for pt in ring[1:-1]:
        last = out[-1]
        if abs(pt[0] - last[0]) > tol or abs(pt[1] - last[1]) > tol:
            out.append(pt)
    out.append(ring[-1])
    return out if len(out) >= 4 else ring


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("infile")
    ap.add_argument("outfile")
    ap.add_argument("--bbox", nargs=4, type=float, required=True,
                    metavar=("MINLON", "MINLAT", "MAXLON", "MAXLAT"))
    ap.add_argument("--cell", type=float, default=0.01)
    ap.add_argument("--min-area", type=float, default=0.0,
                    help="skip buildings with footprint bbox < this many m^2")
    ap.add_argument("--precision", type=int, default=6,
                    help="decimal places for coordinates")
    ap.add_argument("--simplify", type=float, default=0.0,
                    help="merge polygon vertices closer than this (degrees)")
    ap.add_argument("--exclude-stations", action="store_true",
                    help="skip railway/transit station buildings (no collision there)")
    args = ap.parse_args()

    min_lon, min_lat, max_lon, max_lat = args.bbox
    cs = args.cell
    prec = args.precision
    nx = max(1, math.ceil((max_lon - min_lon) / cs))
    ny = max(1, math.ceil((max_lat - min_lat) / cs))

    with open(args.infile) as f:
        gj = json.load(f)

    buildings = []
    cell_map = {}
    max_depth = 0.0
    skipped_small = 0
    skipped_stations = 0

    for feat in gj.get("features", []):
        geom = feat.get("geometry")
        if not geom:
            continue
        props = feat.get("properties", {})
        if args.exclude_stations and is_station(props):
            skipped_stations += 1
            continue
        ring = exterior_ring(geom)
        if not ring or len(ring) < 4:
            continue
        lons = [c[0] for c in ring]
        lats = [c[1] for c in ring]
        bmin_lon, bmax_lon = min(lons), max(lons)
        bmin_lat, bmax_lat = min(lats), max(lats)
        if bmax_lon < min_lon or bmin_lon > max_lon or bmax_lat < min_lat or bmin_lat > max_lat:
            continue
        if args.min_area > 0 and bbox_area_m2(bmin_lon, bmin_lat, bmax_lon, bmax_lat) < args.min_area:
            skipped_small += 1
            continue

        ring = simplify_ring(ring, args.simplify)
        fdepth = foundation_depth(props)
        max_depth = min(max_depth, fdepth)
        idx = len(buildings)
        buildings.append({
            "b": [round(bmin_lon, prec), round(bmin_lat, prec), round(bmax_lon, prec), round(bmax_lat, prec)],
            "f": fdepth,
            "p": [[round(x, prec), round(y, prec)] for x, y in ring],
        })

        cx0 = max(0, int((bmin_lon - min_lon) / cs))
        cx1 = min(nx - 1, int((bmax_lon - min_lon) / cs))
        cy0 = max(0, int((bmin_lat - min_lat) / cs))
        cy1 = min(ny - 1, int((bmax_lat - min_lat) / cs))
        for cx in range(cx0, cx1 + 1):
            for cy in range(cy0, cy1 + 1):
                cell_map.setdefault((cx, cy), []).append(idx)

    cells = [[cx, cy, *idxs] for (cx, cy), idxs in sorted(cell_map.items())]
    out = {
        "cs": cs,
        "bbox": [min_lon, min_lat, max_lon, max_lat],
        "grid": [nx, ny],
        "cells": cells,
        "buildings": buildings,
        "stats": {"count": len(buildings), "maxDepth": max_depth},
    }
    with open(args.outfile, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print(f"Wrote {len(buildings)} buildings (skipped {skipped_small} small, "
          f"{skipped_stations} stations), grid {nx}x{ny} -> {args.outfile}", file=sys.stderr)


if __name__ == "__main__":
    main()
