# Greater Chicagoland — Custom Map Runbook (Railyard + depot)

Build/update the **Greater Chicagoland** map (city code **`GCHI`**) for Subway Builder, played through the **Railyard** mod manager.

Covers Cook, DuPage, Will, Lake County IL, Lake County IN, and the Fox River Valley communities.

## Bounding box (everything shares this)

| edge | value |
|------|-------|
| west (min lon)  | -88.3768 |
| south (min lat) | 41.3778 |
| east (max lon)  | -87.2205 |
| north (max lat) | 42.4949 |

- list form: `[-88.3768, 41.3778, -87.2205, 42.4949]`  ·  center ≈ `41.93635, -87.79865`

Change the bbox → regenerate demand (rebuild OSRM), depot tiles/roads/runways, and the buildings index.

## How it works (hard-won)

A playable map is a flat **ZIP package** imported via **Railyard → Library → Import Asset**. Railyard unpacks it to `%APPDATA%\metro-maker4\cities\data\GCHI\` and serves it; on launch the game downloads/loads it. The ZIP has exactly six files (no subfolders):

`config.json` · `GCHI.pmtiles` · `demand_data.json` · `buildings_index.json` · `roads.geojson` · `runways_taxiways.geojson`

Three tools make these, and the **schema/format details matter**:

1. **`depot`** (github.com/Subway-Builder-Modded/depot) → `GCHI.pmtiles`, `roads.geojson`, `runways_taxiways.geojson`. Tiles MUST be **OpenMapTiles schema** (roads in a `transportation` layer, etc.) — depot produces this. Do NOT use raw Planetiler/Protomaps tiles; the game won't style them and roads/water won't render.
2. **`build_buildings_index.py`** (this folder) → a **slim, station-excluded `buildings_index.json`**. We do NOT use depot's buildings: Railyard's importer **requires `buildings_index.json` and rejects depot's `.bin`**, and depot's `.json` is far too large to load (a too-big buildings file 404s at launch / black screen). Keep the gzipped size under ~50 MB.
3. **demand generator** (github.com/rslurry/subwaybuilder-US-demand-data) → `demand_data.json`.

Run everything in **WSL/Ubuntu** unless noted.

## One-time setup

**Demand env:** from the demand repo, `conda env create -f environment.yml`.

**depot + CLI tools:**

```bash
sudo apt update && sudo apt install -y nodejs npm sqlite3 jq build-essential libsqlite3-dev zlib1g-dev osmium-tool openjdk-21-jre-headless
sudo npm install -g mapshaper
cd ~ && git clone https://github.com/felt/tippecanoe.git && cd tippecanoe && make -j$(nproc) && sudo make install
# Linux pmtiles (the Windows pmtiles.exe does NOT work in WSL)
cd ~ && wget https://github.com/protomaps/go-pmtiles/releases/latest/download/go-pmtiles_1.30.3_Linux_x86_64.tar.gz
tar xzf go-pmtiles_1.30.3_Linux_x86_64.tar.gz && sudo mv pmtiles /usr/local/bin/ && sudo chmod +x /usr/local/bin/pmtiles
# planetiler.jar must be on PATH and executable
wget https://github.com/onthegomap/planetiler/releases/latest/download/planetiler.jar
sudo cp planetiler.jar /usr/local/bin/ && sudo chmod +x /usr/local/bin/planetiler.jar
# depot
cd ~ && git clone https://github.com/Subway-Builder-Modded/depot.git && cd depot
conda env create -f environment.yml && conda activate $(head -1 environment.yml | cut -d' ' -f2)
pip install .
```

**OSM extracts** (used by demand/OSRM and the buildings step):

```bash
mkdir -p ~/chicagoland && cd ~/chicagoland
wget https://download.geofabrik.de/north-america/us/illinois-latest.osm.pbf
wget https://download.geofabrik.de/north-america/us/indiana-latest.osm.pbf
osmium merge illinois-latest.osm.pbf indiana-latest.osm.pbf -o il_in.osm.pbf
osmium extract -b -88.3768,41.3778,-87.2205,42.4949 il_in.osm.pbf -o chicagoland.osm.pbf --overwrite
```

**Docker** for OSRM (Docker Desktop + WSL integration, or Docker Engine in WSL).

---

## Step 1 — Demand (LODES + OSRM)

Input: `chicagoland_demand_input.json` (states il+in, bbox, airports ORD/MDW, 10 universities, 39 entertainment venues, Naval Station Great Lakes). For routed demand (`"CALCULATE_ROUTES": true`), start OSRM first:

```bash
cd ~/chicagoland
docker stop $(docker ps -q --filter ancestor=osrm/osrm-backend) 2>/dev/null
docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-extract -p /opt/car.lua /data/chicagoland.osm.pbf
docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-partition /data/chicagoland.osrm
docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-customize /data/chicagoland.osrm
docker run -t -p 5000:5000 -v "${PWD}:/data" osrm/osrm-backend osrm-routed --algorithm mld /data/chicagoland.osrm   # leave running
```

Then in another terminal:

```bash
cd "/mnt/c/Users/tonyt/Downloads/subwaybuilder-US-demand-data-main"
conda activate $(head -1 environment.yml | cut -d' ' -f2)
python3 create_US_demand_file.py "/mnt/c/Users/tonyt/Claude/Projects/Subway Builder Greater Chicagoland/chicagoland_demand_input.json"
```

Output: `demand_data/Chicagoland/demand_data.json`. (Routing takes hours for this metro; `CALCULATE_ROUTES: false` for a fast test pass. Don't run two demand jobs at once.)

## Step 2 — Tiles + roads + runways (depot)

`build_cgl_map.py` (this folder, `city="GCHI"`):

```bash
conda activate depot
mkdir -p ~/cgl-depot
python3 "/mnt/c/Users/tonyt/Claude/Projects/Subway Builder Greater Chicagoland/build_cgl_map.py"
```

Produces in `~/cgl-depot/GCHI/`: `GCHI.pmtiles`, `roads.geojson`, `runways_taxiways.geojson`, **and `buildings_index.json`** — depot's buildings index **is** the collision index the game uses (a hand-rolled vanilla-format index loads but does NOT collide). Needs internet (Overture buildings + Natural Earth) and lots of RAM — `RAM=12` in the script (raise WSL's memory in `.wslconfig` if you hit "JavaScript heap out of memory"). `outputdir` must exist; `planetiler.jar` must be on PATH.

## Step 3 — Re-tune buildings only (optional)

Step 2 already produced a working collision `buildings_index.json`. Use this only to re-tune the buildings WITHOUT rebuilding tiles. `build_buildings_depot.py` runs just depot's buildings stage:

```bash
conda activate depot
python3 "/mnt/c/Users/tonyt/Claude/Projects/Subway Builder Greater Chicagoland/build_buildings_depot.py"
gzip -kc ~/cgl-depot/GCHI/buildings_index.json | wc -c
```

Tuning (in `build_buildings_depot.py`): `building_index_filter_size` (~40 = SFL; buildings smaller than this get no collision — raise to exclude more small buildings) and `building_index_simplification` (raise to shrink the file). ~86 MB gz loads fine; if a larger area pushes it too high, raise simplification (4–5). Re-runs reuse the cached Overture `buildings.geojson` in `GCHI/`, so comment out `extract_base_data()` to make it just the quick mapshaper pass.

> Note: `build_buildings_index.py` (the OSM/hand-rolled one) does **not** drive collision in the Railyard build — keep buildings on depot's index.

## Step 4 — Package + import

```bash
cd ~/cgl-depot/GCHI
cp "/mnt/c/Users/tonyt/Claude/Projects/Subway Builder Greater Chicagoland/config.json" .
cp "/mnt/c/Users/tonyt/Downloads/subwaybuilder-US-demand-data-main/demand_data/Chicagoland/demand_data.json" .
rm -f ~/Downloads_GCHI.zip
zip -j ~/Downloads_GCHI.zip config.json GCHI.pmtiles demand_data.json buildings_index.json roads.geojson runways_taxiways.geojson
cp ~/Downloads_GCHI.zip /mnt/c/Users/tonyt/Downloads/GCHI.zip
unzip -l ~/Downloads_GCHI.zip   # 6 files, no folders, all non-zero
```

Then **Railyard → Library → Import Asset → `C:\Users\tonyt\Downloads\GCHI.zip`**, replace if prompted, launch. Remove any old map with a different code (e.g. `CGL`) from the Library.

## Troubleshooting

- **Roads / water don't render** → tiles aren't OpenMapTiles. Use depot (Step 2). Verify: `pmtiles show GCHI.pmtiles` → attribution should say OpenMapTiles.
- **Import "missing required files"** → a file is absent, OR you shipped `buildings_index.bin` instead of `buildings_index.json` (Railyard requires the `.json`).
- **"Failed to load buildings … 404" / black screen** → buildings file too big; slim it (Step 3).
- **depot "JavaScript heap out of memory"** → raise `RAM` in `build_cgl_map.py`; if WSL itself is capped low, raise `memory=` in `C:\Users\tonyt\.wslconfig`, then `wsl --shutdown`.
- **depot "Missing required CLI tools: planetiler.jar"** → put it on PATH (`/usr/local/bin`) + `chmod +x`.
- **depot "outputdir must be a valid directory"** → `mkdir -p` it first.
- **`cannot import name MapGen`** → `from depot.maps import MapGen`.
- **OSRM "port 5000 already allocated"** → `docker stop $(docker ps -q --filter ancestor=osrm/osrm-backend)`.
- **Building collision only works underground** → by design; the index stores foundation depth only (no above-ground height), so at-grade/elevated track is blocked by roads, not buildings.
- **Bash commands fail in PowerShell** (`~/…`, `osmium`, `zip` not found) → run them in WSL.

## Files in this folder

- `chicagoland_demand_input.json` — demand generator input (bbox + all demand magnets)
- `config.json` — map package metadata (code `GCHI`)
- `build_cgl_map.py` — depot full build: tiles + roads + runways + collision buildings index (`run_all`)
- `build_buildings_depot.py` — re-tune just the depot buildings/collision index (no tile rebuild)
- `README.md` — map description for the publish repo (lists + credits; stats auto-render)
- `build_buildings_index.py` — DEPRECATED: hand-rolled index; loads but does NOT collide in Railyard. Don't ship.

## Open items & Publishing (→ 1.0.0)

Current build is **v0.9.0** and now feature-complete (tiles, routed demand, **working building collision**). Remaining items are publish prep.

**1. Building collision — ✅ DONE.** Fixed by shipping **depot's** `buildings_index.json` (`build_buildings_depot.py`, `building_index_filter_size=40`, `building_index_simplification=3`). The hand-rolled vanilla-format index loaded but didn't collide; depot's does. ~86 MB gz loads fine. (`building_index_filter_size` ≈ 40 = SFL's small-building threshold.)

**2. (Optional) station-exclusion variant.** depot has no station filter. To drop stations from collision, post-process depot's index by spatially subtracting OSM station footprints (`railway=station` / `building=train_station`) — Overture has no station tags, so match by geometry, not tag. Optional; SFL keeps station collision.

**3. Attribution + license.** Tiles are OpenMapTiles (CC-BY) — display "© OpenMapTiles © OpenStreetMap contributors". Add a LICENSE to the repo.

**4. Gallery.** Add screenshots (SFL ships `gallery/screenshot1.webp`, etc.).

**5. Bump version.** `config.json` `"version"` → `v1.0.0`.

**6. Publish to Railyard:** (Railyard hosts nothing — the registry stores only metadata + a pointer to YOUR GitHub Release, so you host the ZIP.)
- Create a GitHub repo (e.g. `subway-builder-gchi`) with `README.md` (+ optional source). Add a LICENSE.
- Create a **Release** tagged `v1.0.0`; upload `GCHI.zip` as a **release asset** (flat ZIP, no nested folders). Maps are **exempt** from the separate-`manifest.json` rule that mods require.
- Open the **Publish a New Map** issue template:
  `https://github.com/Subway-Builder-Modded/registry/issues/new?template=publish-map.yml`
  Fill: repo / release / asset, version (semver `vX.Y.Z` — required), **data source** (LODES) + **data quality** (see Data Quality guide), and **tags** (see Tagging guide — e.g. `north-america`, `airports`, `entertainment`, `universities`), plus gallery image(s).
- CI validates → **auto-opens a PR** → a maintainer reviews/merges → live in Railyard. If validation fails, edit the auto-generated message and comment `revalidate`.

**Stats are auto-generated — don't hand-write them.** The registry derives the map-page panel from your ZIP: `population`, `residents_total`, `points_count`, `population_count`, `file_sizes`, a demand `grid.geojson`, and `grid_statistics` (playable area, etc.). Your `README.md` is just prose + the added-data lists; the Coverage / Population Summary / Map Statistics / Special Demand panel is generated by the registry, not authored. (The registry is flagged "Work in Progress" — submission schema/process may still change, so re-check the docs at publish time.)

Guides to read before submitting: Data Quality (https://subwaybuildermodded.com/railyard/docs/v0.2/developers/data-quality/) and Tagging (https://subwaybuildermodded.com/railyard/docs/v0.2/developers/tagging/).

## Sources

- depot — https://github.com/Subway-Builder-Modded/depot
- Railyard docs — https://subwaybuildermodded.com/railyard/docs/v0.2/
- Demand generator — https://github.com/rslurry/subwaybuilder-US-demand-data
- Publishing — https://subwaybuildermodded.com/railyard/docs/v0.2/developers/publishing-projects/
