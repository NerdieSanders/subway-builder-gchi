# Greater Chicagoland (GCHI)

A Subway Builder map covering the Chicago metropolitan area from the Wisconsin
state line down through Will County, west to the Fox River Valley, and east
across the Indiana line into the Calumet region — **Cook, DuPage, Will, Lake
County (IL), and Lake County (IN)**, plus the Fox River Valley communities.

Built with [`depot`](https://github.com/Subway-Builder-Modded/depot); demand
from U.S. Census **LODES** origin–destination data.

---

## Coverage

- **Bounding box:** `-88.3768, 41.3778, -87.2205, 42.4949`
- **Playable Area:** _auto-computed by Railyard on publish_
- **Counties:** Cook, DuPage, Will, Lake (IL), Lake (IN)
- **Notable communities:** Chicago, Evanston, Aurora, Elgin, Joliet, Naperville,
  Waukegan, Gary, Hammond, Crown Point

## Population Summary

- **Total Modeled Demand:** _<fill>_
- **Modeled Normal Demand:** _<fill>_
- **Modeled Special Demand:** _<fill>_

## Map Statistics

- **Demand Points:** _<fill>_
- **Populations:** _<fill>_

## Special Demand

### Airports
- O'Hare International Airport (ORD)
- Midway International Airport (MDW)

### Universities
- University of Chicago
- University of Illinois Chicago (UIC)
- Northwestern University
- DePaul University
- Loyola University Chicago
- Illinois Institute of Technology
- Purdue University Northwest
- Indiana University Northwest
- College of Lake County
- Lake Forest College

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

### Military Bases
- Naval Station Great Lakes

## Data & Credits

- Demand: U.S. Census **LODES** (2022)
- Buildings: **Overture** / **OpenStreetMap**
- Tiles: **© OpenMapTiles © OpenStreetMap contributors** (CC-BY)
- Map by **NerdieSanders**

---

<details>
<summary>Computing the demand stats locally</summary>

Run against the uncompressed `demand_data.json` (in your demand-repo output):

```python
import json
d = json.load(open("demand_data.json"))
pops = d["pops"]
print("Demand Points:", len(d["points"]))
print("Populations:  ", len(pops))
print("Total Modeled Demand:", sum(p["size"] for p in pops))
```

Per-category Special Demand totals (Airports/Universities/Entertainment/
Military) are computed and displayed automatically by Railyard from the
published manifest.
</details>
