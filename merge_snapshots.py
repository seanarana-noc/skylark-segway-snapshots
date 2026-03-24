"""
merge_snapshots.py
Runs inside GitHub Actions after any push to eu/*/latest.json or na/*/latest.json.
Merges all operators' latest.json for each region into combined_latest.json.
"""
import json
import os
from pathlib import Path


def merge_region(region):
    region_dir = Path(region)
    if not region_dir.exists():
        print(f"[{region}] directory not found, skipping")
        return

    # Find all operator latest.json files (skip combined_latest.json itself)
    latest_files = [
        p for p in region_dir.glob("*/latest.json")
        if p.parent.name != "combined"
    ]

    if not latest_files:
        print(f"[{region}] no operator latest.json files found")
        return

    seen = {}          # (lon, lat) → feature  — last-write-wins by timestamp
    operators = []

    for f in latest_files:
        operator = f.parent.name
        operators.append(operator)
        try:
            data = json.loads(f.read_text())
        except Exception as e:
            print(f"[{region}] skipping {f} — {e}")
            continue

        for feature in data.get("features", []):
            coords = tuple(feature["geometry"]["coordinates"])
            ts = feature["properties"].get("timestamp", "")
            if coords not in seen or ts > seen[coords]["properties"]["timestamp"]:
                seen[coords] = feature

    combined = {
        "type": "FeatureCollection",
        "metadata": {
            "region": region.upper(),
            "operators": sorted(operators),
            "point_count": len(seen),
        },
        "features": list(seen.values()),
    }

    out_path = region_dir / "combined_latest.json"
    out_path.write_text(json.dumps(combined, indent=2))
    print(f"[{region}] combined_latest.json — {len(seen)} points from {sorted(operators)}")


if __name__ == "__main__":
    merge_region("eu")
    merge_region("na")
