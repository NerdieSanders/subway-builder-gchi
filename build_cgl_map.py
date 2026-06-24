#!/usr/bin/env python3
"""
Generate the map tiles + roads + runways for Greater Chicagoland (GCHI) using
the official `depot` library, which outputs them in the OpenMapTiles schema
Subway Builder actually renders.

Run inside the `depot` conda env (see depot README), from WSL.
Produces, under OUTPUT_DIR/GCHI/:
    GCHI.pmtiles, roads.geojson, runways_taxiways.geojson
    (also buildings_index.json/.bin — but we do NOT ship depot's buildings; see below)

Buildings note: Railyard's importer requires buildings_index.JSON (it rejects
depot's .bin), and depot's .json is too large to load. So ship a SLIM
buildings_index.json from build_buildings_index.py (--exclude-stations) instead.

Then package: config.json + GCHI.pmtiles + demand_data.json (demand repo) +
buildings_index.json (build_buildings_index.py) + roads.geojson +
runways_taxiways.geojson -> ZIP -> Railyard Import Asset.
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

    # Size/quality knobs — raise the filters if buildings_index.json is too big:
    building_index_filter_size=40,        # m^2; <this size = no collision (SFL uses ~40)
    building_index_simplification=3,      # m between building nodes; higher = smaller file
    # building_tile_filter_size=None,     # defaults to index filter size
    # max_building_tile_size=450,         # KB/tile cap for buildings

    ncores=None,   # use all cores
    RAM=12,        # GB for mapshaper (WSL has ~13 GB available); lower if less
    verb=True,
)

# Runs: extract_base_data -> process_buildings -> process_roads_and_aeroways
#       -> generate_pmtiles -> add_labels
mg.run_all()

print("Done. Outputs in /home/tonyt/cgl-depot/GCHI/")
