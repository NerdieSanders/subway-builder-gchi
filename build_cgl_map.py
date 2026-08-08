#!/usr/bin/env python3
"""
Generate the map tiles + roads + runways for Greater Chicagoland (GCHI) using
the official `depot` library, which outputs them in the OpenMapTiles schema
Subway Builder actually renders.

Run inside the `depot` conda env, from WSL. Requires depot >= 1.2.0.
Produces, under OUTPUT_DIR/GCHI/:
    GCHI.pmtiles, GCHI_foundations.pmtiles, buildings_index.bin (+ .json, .bin.gz),
    roads.geojson, runways_taxiways.geojson

Buildings: ship depot's buildings_index.BIN — game 1.4.0+ requires it and rejects
the legacy .json. Foundation depths live in the .bin, not the tiles, so collision
does not depend on GCHI_foundations.pmtiles (that drives the visual layer only).

Station collision: run_all() builds the index from ALL buildings on purpose, so
stations stay VISIBLE in the tiles. build_buildings_nostations.py then regenerates
the index alone from station-filtered footprints. Run it after this script — never
pass buildings_geojson here, or stations vanish from the map.

Then package SEVEN files -> ZIP -> Railyard Import Asset:
    config.json, GCHI.pmtiles, GCHI_foundations.pmtiles, demand_data.json,
    buildings_index.bin, roads.geojson, runways_taxiways.geojson
"""
from depot.maps import MapGen

mg = MapGen(
    city="GCHI",
    bbox=[-88.3768, 41.3778, -87.2205, 42.4949],
    # depot does its own osmium extract from these state files:
    osmpbf=[
        "/home/tonyt/chicagoland/illinois-latest.osm.pbf",
        "/home/tonyt/chicagoland/indiana-latest.osm.pbf",
    ],
    outputdir="/home/tonyt/cgl-depot",

    # Label categories (depot README's US-map recommendation):
    cities=["city", "borough", "town"],
    suburbs=["suburb", "village"],
    neighborhoods=["neighbourhood", "hamlet", "quarter", "locality"],

    # Size/quality knobs — raise the filters if the buildings index is too big:
    building_index_filter_size=40,        # m^2; <this size = no collision (SFL uses ~40)
    building_index_simplification=3,      # m between building nodes; higher = smaller file
    # building_tile_filter_size=None,     # defaults to index filter size

    # MUST stay set. depot 1.2.x flipped this default 450 -> None, which swaps
    # tippecanoe's --drop-smallest-as-needed cap for --no-tile-size-limit. depot
    # neither checks nor warns, so uncapped dense-downtown tiles would sail through
    # the build and only show up as rendering stalls in game. 450 = the 1.1.x default
    # this map was tuned and play-tested against.
    max_building_tile_size=450,           # KB/tile cap for buildings

    # Collision layers (depot 1.1.x+):
    create_building_foundations=True,     # per-building foundation depth (10-80 m) — better tunnel collision
    create_ocean_foundations=False,       # OFF: free building in/under water (Lake Michigan + rivers). Skips GEBCO/bathymetry.

    ncores=None,   # use all cores
    RAM=12,        # GB for mapshaper; WSL has ~23 GB. Held at the v1.2.0 value to keep this rebuild comparable.
    verb=True,
)

# Runs: extract_base_data -> process_buildings -> process_roads_and_aeroways
#       -> generate_pmtiles -> add_labels
mg.run_all()

print("Done. Outputs in /home/tonyt/cgl-depot/GCHI/")
