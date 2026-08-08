#!/usr/bin/env python3
"""
Remove phantom demand points — points with zero residents AND zero jobs.

The Railyard registry's `demand_phantom_points` integrity check is zero-tolerance:

    phantoms = points.filter(p => p.residents === 0 && p.jobs === 0)
    pass = phantoms.length === 0

A release that fails is excluded from downloads until fixed. v1.3.0 shipped 1,374
such points (8.5%) but is grandfathered — the check landed one day after it
released. Any NEW tag gets inspected, so this must run before packaging.

Surgical by design: drops only orphaned points and rewrites nothing else. depot's
DemandData.sanitize() would also do this, but it recomputes every point's
jobs/residents from the pops and trips a schema guard on our UNI_/AIR_/ENT_ ids.

Usage:  python3 strip_phantom_points.py <in.json> <out.json>
"""
import json
import sys

if len(sys.argv) != 3:
    sys.exit(__doc__.strip().splitlines()[-1])

SRC, OUT = sys.argv[1], sys.argv[2]

with open(SRC) as f:
    d = json.load(f)

points, pops = d["points"], d["pops"]

phantoms = [p for p in points if p.get("residents", 0) == 0 and p.get("jobs", 0) == 0]
phantom_ids = {p["id"] for p in phantoms}

# Safety gate: a phantom referenced by any pop would mean real demand is attached
# and the point is not actually orphaned. Bail rather than silently drop demand.
referenced = {p["residenceId"] for p in pops} | {p["jobId"] for p in pops}
collisions = phantom_ids & referenced
if collisions:
    sys.exit(f"ABORT: {len(collisions)} phantom points are referenced by pops, "
             f"e.g. {sorted(collisions)[:3]}. Not safe to drop.")

d["points"] = [p for p in points if p["id"] not in phantom_ids]

print(f"points:  {len(points)} -> {len(d['points'])}  (removed {len(phantoms)})")
print(f"pops:    {len(pops)} (unchanged)")

# The registry also runs demand_residents_match: sum(point.residents) must equal
# sum(pop.size) exactly, with no epsilon. Verify we did not disturb it.
by_point = sum(p.get("residents", 0) for p in d["points"])
by_pop = sum(p["size"] for p in pops)
print(f"residents_match: points={by_point} pops={by_pop} delta={by_point - by_pop}")
if by_point != by_pop:
    sys.exit("ABORT: residents_match would fail — refusing to write.")

remaining = [p for p in d["points"] if p.get("residents", 0) == 0 and p.get("jobs", 0) == 0]
print(f"phantoms remaining: {len(remaining)}")
if remaining:
    sys.exit("ABORT: phantoms still present — refusing to write.")

with open(OUT, "w") as f:
    json.dump(d, f)
print(f"wrote {OUT}")
