#!/usr/bin/env python3
"""
v1.2.0 — Regenerate depot's buildings_index.bin from a station-EXCLUDED footprint
set, without rebuilding the tiles.

Feed depot the filtered footprints from filter_station_buildings.py via
`buildings_geojson=`. depot then writes a fresh buildings_index.bin/.json that has
no collision on train-station buildings. Tiles (GCHI.pmtiles) are NOT rebuilt, so
stations remain visible on the map but become buildable (visible, non-colliding).

Keeps the v1.1.0 building settings (filter 40, simplification 3, foundation depth ON)
so only the station removal differs.

Order of operations:
  1. run filter_station_buildings.py  -> buildings_nostations.geojson
  2. run THIS script                  -> new buildings_index.bin
  3. swap the .bin into the package, bump to v1.2.0, re-zip

Run in the `depot` conda env, from WSL.
"""
from depot.maps import MapGen

mg = MapGen(
    city="GCHI",
    bbox=[-88.3768, 41.3778, -87.2205, 42.4949],
    osmpbf=[
        "/home/tonyt/chicagoland/illinois-latest.osm.pbf",
        "/home/tonyt/chicagoland/indiana-latest.osm.pbf",
    ],
    outputdir="/home/tonyt/cgl-depot",

    building_index_filter_size=40,
    building_index_simplification=3,
    create_building_foundations=True,   # keep v1.1.0 foundation-depth collision

    # station-excluded footprints from filter_station_buildings.py:
    buildings_geojson="/home/tonyt/cgl-depot/GCHI/buildings_nostations.geojson",
    redownload_buildings=False,         # use the provided geojson, don't fetch Overture

    ncores=None,
    RAM=12,
    verb=True,
)

mg.extract_base_data()      # prerequisite osmium extract (quick / idempotent)
mg.process_buildings()      # writes station-excluded buildings_index.json/.bin
print("Done. Station-excluded buildings_index.bin in /home/tonyt/cgl-depot/GCHI/")
