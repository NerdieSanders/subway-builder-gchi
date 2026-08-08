# Greater Chicagoland (GCHI)

A Subway Builder map covering the Chicago metropolitan area — from the Wisconsin
state line down through Will County, west to the Fox River Valley, and east
across the Indiana line into the Calumet region: **Cook, DuPage, Will, Lake
County (IL), and Lake County (IN)**, plus the Fox River Valley communities.

Built with [`depot`](https://github.com/Subway-Builder-Modded/depot); demand from
U.S. Census **LODES 2023** origin–destination data. **Requires Subway Builder 1.4.5+.**

---

## Coverage

- **Bounding box:** `-88.3768, 41.3778, -87.2205, 42.4949`
- **Counties:** Cook, DuPage, Will, Lake (IL), Lake (IN)
- **Notable communities:** Chicago, Evanston, Aurora, Elgin, Joliet, Naperville,
  Waukegan, Gary, Hammond, Crown Point

> Playable area and demand stats (points, populations, totals) are **auto-derived
> by the registry** from the map package and shown on the map's Railyard page —
> they are not hand-listed here.

## Features

- **Consolidated routed demand (~75k pops)** — LODES 2023 origin–destination
  demand routed via OSRM, then aggressively consolidated for smooth in-game
  performance while preserving total ridership.
- **Building collision with foundation depth** — per-building foundation depths
  (10–80 m), so deep tunnels interact with building foundations realistically.
- **Buildable train stations** — real Metra / CTA 'L' / Amtrak / South Shore
  station buildings are excluded from collision, so you can place stations there.
- **Free water building** — no collision restriction in Lake Michigan or the
  rivers; bridge or tunnel across freely.
- **Neighborhood labels** — municipal and neighborhood labels from administrative
  boundary data.
- **College campuses on the map** — campus polygons render in game, so the 44
  institutions driving education demand are visible where you're routing to them.

## Special Demand

### Airports
- O'Hare International Airport (ORD)
- Midway International Airport (MDW)

### Universities & Colleges

**44 institutions, ~370,000 students** — the region's full higher-education
footprint, not just the flagship campuses. Community colleges are included
because they generate substantial commuter demand across the suburbs.

*Major universities* — University of Illinois Chicago · Northwestern · DePaul ·
University of Chicago · Loyola Chicago · Illinois Institute of Technology ·
Purdue University Northwest · Indiana University Northwest · Northeastern
Illinois · Roosevelt · Chicago State · Governors State · Lewis · Aurora ·
Concordia Chicago · Saint Xavier · Elmhurst · Dominican · Benedictine ·
North Park · Wheaton · North Central · Lake Forest

*Community colleges* — College of DuPage · Joliet Junior · College of Lake
County · Harper · Moraine Valley · Triton · Elgin · Oakton · Waubonsee ·
McHenry County · Morton · South Suburban · Prairie State · Ivy Tech East
Chicago · and the seven City Colleges of Chicago (Harold Washington, Wilbur
Wright, Malcolm X, Truman, Daley, Kennedy-King, Olive-Harvey)

### Entertainment & Attractions
- Soldier Field
- Wrigley Field
- Guaranteed Rate Field (White Sox)
- United Center
- Wintrust Arena
- Allstate Arena
- NOW Arena
- SeatGeek Stadium
- Credit Union 1 Arena
- McCormick Place
- Donald E. Stephens Convention Center
- Art Institute of Chicago
- Field Museum
- Museum of Science and Industry
- Shedd Aquarium
- Adler Planetarium
- Museum of Contemporary Art Chicago
- Chicago History Museum
- Lincoln Park Zoo
- Brookfield Zoo
- Chicago Botanic Garden
- Morton Arboretum
- Cantigny Park
- Navy Pier
- Six Flags Great America
- Millennium Park
- Magnificent Mile
- Woodfield Mall
- Oakbrook Center
- Gurnee Mills
- Westfield Old Orchard
- Fashion Outlets of Chicago
- Southlake Mall
- Rivers Casino Des Plaines
- Horseshoe Hammond
- Hard Rock Casino Northern Indiana
- Ameristar Casino East Chicago
- North Avenue Beach
- Illinois Beach State Park
- Obama Presidential Center

### Military Bases
- Naval Station Great Lakes

## Data & Credits

- Demand: U.S. Census **LODES 2023** (routed via OSRM)
- Buildings: **Overture** / **OpenStreetMap**
- Tiles: **© OpenMapTiles © OpenStreetMap contributors** (CC-BY)
- Built with **depot 1.2.7**
- Map by **NerdieSanders**
