#!/usr/bin/env python3
"""Read-only: set declared_range / resolved_major on targets from the npm registry.

Does not write to GitHub. Safe to re-run. Default: T0 and T1 only.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TARGETS = DATA / "targets.jsonl"
UA = "image-size-next-campaign/1.0 (+https://github.com/lcf2212dev/image-size-next)"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from image_size_range import extract_declared_range, resolved_major  # noqa: E402


def load_targets() -> list[dict]:
    if not TARGETS.exists():
        return []
    rows = []
    with TARGETS.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def npm_manifest(package: str) -> dict | None:
    enc = urllib.parse.quote(package, safe="@")
    url = f"https://registry.npmjs.org/{enc}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    latest = (data.get("dist-tags") or {}).get("latest")
    versions = data.get("versions") or {}
    if latest and latest in versions and isinstance(versions[latest], dict):
        return versions[latest]
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiers", default="T0,T1", help="Comma-separated tiers (default T0,T1)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sleep", type=float, default=0.2)
    ap.add_argument("--force", action="store_true", help="Re-query even if resolved_major is set")
    args = ap.parse_args()
    want = {t.strip() for t in args.tiers.split(",") if t.strip()}

    rows = load_targets()
    selected = [r for r in rows if (r.get("tier") in want) or (not want)]
    if args.limit:
        selected = selected[: args.limit]

    stats = {"seen": 0, "major_1": 0, "major_2": 0, "unknown": 0, "failed": 0, "skipped": 0}
    by_name = {r.get("package"): r for r in rows}

    for pkg in selected:
        name = pkg.get("package")
        if not name:
            continue
        stats["seen"] += 1
        if pkg.get("resolved_major") in {"1", "2"} and not args.force:
            stats["skipped"] += 1
            stats[f"major_{pkg['resolved_major']}"] += 1
            continue
        manifest = npm_manifest(name)
        time.sleep(args.sleep)
        if not manifest:
            stats["failed"] += 1
            pkg["range_error"] = "npm_lookup_failed"
            by_name[name] = pkg
            print(json.dumps({"package": name, "ok": False, "error": "npm_lookup_failed"}), flush=True)
            continue
        declared = extract_declared_range(manifest)
        major = resolved_major(declared)
        pkg["declared_range"] = declared
        pkg["resolved_major"] = major
        by_name[name] = pkg
        if major == "1":
            stats["major_1"] += 1
        elif major == "2":
            stats["major_2"] += 1
        else:
            stats["unknown"] += 1
        print(
            json.dumps(
                {
                    "package": name,
                    "tier": pkg.get("tier"),
                    "declared_range": declared,
                    "resolved_major": major,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    ordered = sorted(
        by_name.values(),
        key=lambda r: (-(r.get("downloads") or 0), r.get("package") or ""),
    )
    tmp = TARGETS.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for r in ordered:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(TARGETS)
    print("---")
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
