#!/usr/bin/env python3
"""
Remove train-station structures from GCHI's collision set.

depot has no station filter and Overture footprints carry no station tags, so we
identify station structures by GEOMETRY using OSM features and drop any Overture
footprint that overlaps them. The output feeds depot's process_buildings via
`buildings_geojson=`, so the regenerated buildings_index.bin excludes stations
(collision only — tiles are untouched, so stations stay visible).

Matching:
  1. station POLYGONS (building=train_station/transportation, public_transport=station)
     -> remove any footprint that intersects.
  2. PLATFORM polygons (railway=platform) -> remove any footprint that intersects.
  3. TRAIN SHEDS: building=roof polygons that overlap a platform -> remove any
     footprint that intersects.
  4. station POINTS (railway=station nodes, etc.) -> remove the footprint that
     CONTAINS the node; if none contains it, fall back to a small buffer.
     **Capped by area** — see below.

SIZE CAP ON THE NODE RULES (added v1.4.1). The point rules are fuzzy: the extract
includes `public_transport=station`, which in OSM covers BUS stations, so a single
bus bay used to delete whatever building it sat in or beside. That silently stripped
collision from Gurnee Mills (204,612 m2), the United Center, Midway's terminal,
Stroger Hospital, and two high schools — all shipped that way since v1.2.0.

Node matches therefore only remove footprints below NODE_REMOVAL_MAX_AREA_M2.
Rules 1-3 are exact geometry matches against rail features and are NOT capped.

LARGE_REMOVAL_ALLOWLIST exempts named complexes that genuinely host a rail station
and should stay buildable despite their size. McCormick Place is the case in point:
its Metra Electric stop is inside the complex, and OSM gives it only station POINTS
(no station polygon), so without the exemption the cap would make all four of its
buildings solid. Add further entries here rather than raising the cap.

Rules 2 and 3 were added in v1.4.1. Without them the platform canopies and train
sheds at Union Station, LaSalle Street, and Ogilvie stayed collidable: OSM tags
them `railway=platform` (with NO building tag) and `building=roof`, so they carry
neither a station building tag nor a contained station node, and rules 1 and 4
could never see them. Union Station alone had 16 such footprints.

Rule 3 deliberately requires a roof to OVERLAP A PLATFORM. `building=roof` is a
generic tag — carports, awnings, bandstands — and matching it outright would strip
collision from unrelated structures citywide. In the Loop terminal area only 17 of
76 roofs sit over a platform.

The OSM extract MUST include platforms and roofs or rules 2-3 match nothing:
    osmium tags-filter <city>.osm.pbf \
      nwr/railway=station,halt,platform nwr/public_transport=station \
      w/building=train_station,transportation,roof \
      -o stations.osm.pbf --overwrite
    osmium export stations.osm.pbf -o stations.geojson --overwrite

Inputs:
  argv[1] buildings.geojson  depot's cached Overture footprints
                             (default: ~/cgl-depot/GCHI/buildings.geojson)
  argv[2] stations.geojson   OSM rail features (see the osmium step above)
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

STATION_BUILDING_VALUES = ("train_station", "transportation")

# A station NODE may not delete a footprint bigger than this. Real station
# buildings are small; anything larger is a mall/arena/school/terminal that
# merely has a bus bay in it.
NODE_REMOVAL_MAX_AREA_M2 = 5000

# Name substrings exempt from the cap — complexes that really do host a rail
# station and should stay buildable at any size. Matched case-insensitively;
# "McCormick Place" covers the Convention Center and its South/West/North buildings.
LARGE_REMOVAL_ALLOWLIST = ("mccormick place",)


def col(df, name):
    """Tag column as a string Series, or empty strings if the tag is absent."""
    if name in df.columns:
        return df[name].astype("string").fillna("")
    return pd.Series([""] * len(df), index=df.index, dtype="string")


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

building_tag = col(st, "building")
railway_tag = col(st, "railway")
ptransport_tag = col(st, "public_transport")

is_poly = st.geom_type.isin(["Polygon", "MultiPolygon"])
station_poly = st[is_poly & (building_tag.isin(STATION_BUILDING_VALUES)
                             | (ptransport_tag == "station"))]
platform_poly = st[is_poly & (railway_tag == "platform")]
roof_poly = st[is_poly & (building_tag == "roof")]
pts = st[st.geom_type == "Point"]

print(f"station polygons: {len(station_poly)} | platforms: {len(platform_poly)} | "
      f"roofs: {len(roof_poly)} | station points: {len(pts)}")

bld_m = bld.to_crs(CRS_M)
remove = pd.Index([], dtype="int64")

# Footprints a station NODE is allowed to delete: small ones, plus allowlisted
# complexes at any size.
_area = bld_m.geometry.area
_name = col(bld, "name").str.lower()
_allowed = _area < NODE_REMOVAL_MAX_AREA_M2
for _sub in LARGE_REMOVAL_ALLOWLIST:
    _allowed |= _name.str.contains(_sub, na=False)
NODE_ELIGIBLE = bld_m.index[_allowed]
print(f"node-rule eligible footprints: {len(NODE_ELIGIBLE):,} of {len(bld_m):,} "
      f"(area < {NODE_REMOVAL_MAX_AREA_M2:,} m2, plus allowlist)")


def drop_intersecting(target, label):
    """Remove footprints intersecting `target`; returns the projected target."""
    global remove
    if not len(target):
        print(f"  {label}: none found")
        return None
    tgt_m = target.to_crs(CRS_M)[["geometry"]].reset_index(drop=True)
    hit = gpd.sjoin(bld_m, tgt_m, predicate="intersects", how="inner")
    n = len(hit.index.unique())
    remove = remove.union(hit.index.unique())
    print(f"  removed via {label}: {n}")
    return tgt_m


# 1) footprints intersecting station building polygons
drop_intersecting(station_poly, "station polygons")

# 2) footprints intersecting platforms
platforms_m = drop_intersecting(platform_poly, "platforms")

# 3) train sheds — roofs that sit over a platform (NOT every building=roof)
if len(roof_poly) and platforms_m is not None:
    roofs_m = roof_poly.to_crs(CRS_M)[["geometry"]].reset_index(drop=True)
    over = gpd.sjoin(roofs_m, platforms_m, predicate="intersects", how="inner")
    sheds_m = roofs_m.loc[over.index.unique()]
    print(f"  roofs over a platform (= train sheds): {len(sheds_m)} of {len(roofs_m)}")
    if len(sheds_m):
        hit = gpd.sjoin(bld_m, sheds_m.reset_index(drop=True),
                        predicate="intersects", how="inner")
        remove = remove.union(hit.index.unique())
        print(f"  removed via train sheds: {len(hit.index.unique())}")

# 4) footprints containing a station node (+ buffer fallback for stray nodes).
#    Both are CAPPED by area — a bus bay must not delete a mall.
if len(pts):
    pts_m = pts.to_crs(CRS_M)[["geometry"]].reset_index(drop=True)

    cont = gpd.sjoin(bld_m, pts_m, predicate="contains", how="inner")
    cont_hits = cont.index.unique()
    cont_kept = cont_hits.intersection(NODE_ELIGIBLE)
    remove = remove.union(cont_kept)
    matched = pd.Index(cont["index_right"].unique())   # node matched regardless of cap
    print(f"  removed via containing a station node: {len(cont_kept)} "
          f"({len(cont_hits) - len(cont_kept)} skipped by size cap)")

    stray = pts_m[~pts_m.index.isin(matched)].copy()
    if len(stray):
        stray["geometry"] = stray.geometry.buffer(POINT_BUFFER_M)
        hit2 = gpd.sjoin(bld_m, stray, predicate="intersects", how="inner")
        buf_hits = hit2.index.unique()
        buf_kept = buf_hits.intersection(NODE_ELIGIBLE)
        remove = remove.union(buf_kept)
        print(f"  station nodes with no containing footprint: {len(stray)} "
              f"-> removed {len(buf_kept)} via {POINT_BUFFER_M} m buffer "
              f"({len(buf_hits) - len(buf_kept)} skipped by size cap)")

keep = bld.drop(index=remove)
print(f"\nbuildings total: {len(bld)} | removed (stations): {len(remove)} | kept: {len(keep)}")

keep.to_file(OUT, driver="GeoJSON")
print(f"wrote {OUT}")
