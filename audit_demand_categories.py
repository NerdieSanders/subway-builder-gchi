#!/usr/bin/env python3
"""
Break a demand_data.json down by demand category, so special-demand weighting can
be compared against a reference map (e.g. the base game's own CHI).

Pops are residence->job flows. Special-demand points carry prefixed ids -- AIR_,
UNI_, ENT_, and so on -- while ordinary census points are numeric, or `merged_*`
once consolidation has run. Attributing each pop's size to the prefix on its
endpoints gives per-category demand.

Military bases are the exception: they get a BARE name as their id (e.g.
`NSGreatLakes`), with no prefix. Anything non-numeric that matches no known
prefix is therefore treated as special demand rather than census -- otherwise a
base's demand silently disappears into the census bucket.

A pop is counted once. If both endpoints are special (rare), it is attributed to
the job side, since that is the trip's purpose.

Usage:  python3 audit_demand_categories.py <demand_data.json> [more.json ...]
"""
import collections
import json
import sys

if len(sys.argv) < 2:
    sys.exit(__doc__.strip().splitlines()[-1])

# Prefixes the demand generator emits for special demand.
LABELS = {
    "AIR": "airports",
    "UNI": "universities/colleges",
    "ENT": "entertainment",
    "BASE": "military bases",
    "MIL": "military bases",
    "SCH": "schools",
    "HOS": "hospitals",
    "PRK": "parks",
}


def category(point_id):
    """Special-demand key for an id, or None for ordinary census demand."""
    pid = str(point_id)
    parts = pid.split("_")
    head = parts[0]
    if head in LABELS:
        return head
    # consolidation rewrites ids as merged_<something>; the something may itself
    # be a special id, e.g. merged_UNI_1. Otherwise it is census (merged_SO_*,
    # merged_<census block id>).
    if head == "merged":
        return parts[1] if len(parts) > 1 and parts[1] in LABELS else None
    if head.isdigit():
        return None
    # Non-numeric, unrecognized prefix -> a bare-name special, i.e. a military
    # base. Reported under its own id so it stays visible instead of vanishing
    # into census demand.
    return pid


for path in sys.argv[1:]:
    with open(path) as f:
        d = json.load(f)
    pops = d["pops"]

    totals = collections.Counter()
    counts = collections.Counter()
    for p in pops:
        # job side wins -- it is the trip's purpose
        cat = category(p["jobId"]) or category(p["residenceId"]) or "CENSUS"
        totals[cat] += p["size"]
        counts[cat] += 1

    grand = sum(totals.values())
    print(f"\n{path}")
    print(f"  points {len(d['points']):,} | pops {len(pops):,} | total demand {grand:,}")
    print(f"  {'category':<24} {'demand':>12} {'share':>7} {'pops':>8}")
    for cat, size in totals.most_common():
        name = "ordinary (census)" if cat == "CENSUS" else LABELS.get(cat, cat)
        print(f"  {name:<24} {size:>12,} {size / grand:>6.1%} {counts[cat]:>8,}")
