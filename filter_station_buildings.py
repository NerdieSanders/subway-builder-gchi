#!/usr/bin/env python3
"""
v1.2.0 — Remove train-station buildings from GCHI's collision set.

depot has no station filter and Overture footprints carry no station tags, so we
identify station buildings by GEOMETRY using OSM station features and drop any
Overture footprint that overlaps them. The output feeds depot's process_buildings
via `buildings_geojson=`, so the regenerated buildings_index.bin excludes stations
(collision only — tiles are untouched, so stations stay visible).

Matching:
  - station POLYGONS (building=train_station/transportation): remove any footprint
    that intersects them.
  - station POINTS (railway=station nodes, etc.): remove the footprint that CONTAINS
    the node; if no footprint contains it, fall back to a small buffer.

Inputs:
  argv[1] buildings.geojson  depot's cached Overture footprints
                             (default: ~/cgl-depot/GCHI/buildings.geojson)
  argv[2] stations.geojson   OSM rail-station features (see osmium step in RUNBOOK)
                             (default: ~/chicagoland/stations.geojson)
  argv[3] output             (default: ~/cgl-depot/GCHI/buildings_nostations.geojson)

Run in the `depot` conda env (has geopandas/shapely).
"""
import sys
import geopandas as gpd
import pandas as pd

BUILDINGS = sys.argv[1] if len(sys.argv) > 1 else "/home/tonyt/cgl-depot/GCHI/buildings.geojson"
STATIONS  = sys.argv[2] if len(sys.argv) > 2 else "/home/tonyt/chicagoland/stations.geojson"
OUT       = sys.argv[3] if len(sys.argv) > 3 else "/home/tonyt/cgl-depot/GCHI/buildings_nostations.geojson"

CRS_M = 32616          # UTM zone 16N — meters, covers Greater Chicagoland
POINT_BUFFER_M = 25    # fallback radius for station nodes not inside any footprint

print(f"Reading buildings: {BUILDINGS}")
bld = gpd.read_file(BUILDINGS)
if bld.crs is None:
    bld = bld.set_crs(4326)
bld = bld.reset_index(drop=True)

print(f"Reading stations:  {STATIONS}")
st = gpd.read_file(STATIONS)
if st.crs is None:
    st = st.set_crs(4326)
st = st[st.geometry.notna() & ~st.geometry.is_empty]

poly = st[st.geom_type.isin(["Polygon", "MultiPolygon"])]
pts  = st[st.geom_type == "Point"]
print(f"station polygons: {len(poly)} | station points: {len(pts)}")

bld_m = bld.to_crs(CRS_M)
remove = pd.Index([], dtype="int64")

# 1) footprints intersecting station building polygons
if len(poly):
    poly_m = poly.to_crs(CRS_M)[["geometry"]].reset_index(drop=True)
    hit = gpd.sjoin(bld_m, poly_m, predicate="intersects", how="inner")
    remove = remove.union(hit.index.unique())
    print(f"  removed via station polygons: {len(hit.index.unique())}")

# 2) footprints containing a station node (+ 3) buffer fallback for stray nodes)
if len(pts):
    pts_m = pts.to_crs(CRS_M)[["geometry"]].reset_index(drop=True)
    cont = gpd.sjoin(bld_m, pts_m, predicate="contains", how="inner")
    remove = remove.union(cont.index.unique())
    matched = pd.Index(cont["index_right"].unique())
    print(f"  removed via containing a station node: {len(cont.index.unique())}")

    stray = pts_m[~pts_m.index.isin(matched)].copy()
    if len(stray):
        stray["geometry"] = stray.geometry.buffer(POINT_BUFFER_M)
        hit2 = gpd.sjoin(bld_m, stray, predicate="intersects", how="inner")
        remove = remove.union(hit2.index.unique())
        print(f"  station nodes with no containing footprint: {len(stray)} "
              f"-> removed {len(hit2.index.unique())} via {POINT_BUFFER_M} m buffer")

keep = bld.drop(index=remove)
print(f"\nbuildings total: {len(bld)} | removed (stations): {len(remove)} | kept: {len(keep)}")

keep.to_file(OUT, driver="GeoJSON")
print(f"wrote {OUT}")
