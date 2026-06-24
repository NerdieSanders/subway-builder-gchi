#!/usr/bin/env python3
"""
Regenerate ONLY depot's buildings_index.json for GCHI (collision fix), without
rebuilding the tiles. depot's buildings index is the format the game's collision
system actually uses (the hand-rolled one loads but doesn't collide).

Goal: get buildings_index.json small enough to load. Tune via:
  building_index_simplification  (raise to shrink: 3 -> 4 -> 5)
  building_index_filter_size     (raise to drop more small buildings; ~40 = SFL)

Run in the depot conda env, from WSL. Output: ~/cgl-depot/GCHI/buildings_index.json
Then check the gzipped size and, if good, swap it into the package ZIP.
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
    ncores=None,
    RAM=12,
    verb=True,
)

mg.extract_base_data()      # prerequisite (osmium extract); quick
mg.process_buildings()      # fetches Overture, writes buildings_index.json/.bin
print("Done. buildings_index.json in /home/tonyt/cgl-depot/GCHI/")
