#!/usr/bin/env python3
"""Phase A: fetch all npm packages that depend on image-size; batch by 20."""

from __future__ import annotations

import json
import math
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = (
    "https://packages.ecosyste.ms/api/v1/registries/npmjs.org"
    "/packages/image-size/dependent_packages"
)
PER_PAGE = 100
BATCH_SIZE = 20
UA = "image-size-next-campaign/1.0 (+https://github.com/lcf2212dev/image-size-next)"

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BATCHES = DATA / "batches"


def fetch_page(page: int) -> list[dict]:
    url = f"{API}?per_page={PER_PAGE}&page={page}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    BATCHES.mkdir(parents=True, exist_ok=True)

    # clear old batches
    for old in BATCHES.glob("batch-*.json"):
        old.unlink()

    by_name: dict[str, dict] = {}
    page = 1
    while True:
        try:
            rows = fetch_page(page)
        except urllib.error.HTTPError as e:
            print(f"HTTP error page {page}: {e}", file=sys.stderr)
            if e.code == 429:
                time.sleep(30)
                continue
            raise
        if not rows:
            break
        for row in rows:
            name = row.get("name")
            if not name:
                continue
            by_name[name] = row
        print(f"page {page}: +{len(rows)} (unique so far {len(by_name)})", flush=True)
        if len(rows) < PER_PAGE:
            break
        page += 1
        time.sleep(0.15)

    packages = list(by_name.values())
    packages.sort(
        key=lambda p: (
            -(p.get("downloads") or 0),
            (p.get("name") or "").lower(),
        )
    )

    raw_path = DATA / "dependents.raw.jsonl"
    with raw_path.open("w", encoding="utf-8") as f:
        for p in packages:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    # slim records for batches
    slim: list[dict] = []
    with_repo = 0
    with_maintainers = 0
    unpublished = 0
    for p in packages:
        repo = (p.get("repository_url") or "").strip()
        maintainers = p.get("maintainers") or []
        if repo:
            with_repo += 1
        if maintainers:
            with_maintainers += 1
        if p.get("status") == "unpublished":
            unpublished += 1
        slim.append(
            {
                "package": p.get("name"),
                "downloads": p.get("downloads") or 0,
                "downloads_period": p.get("downloads_period"),
                "repository_url": repo or None,
                "registry_url": p.get("registry_url"),
                "status": p.get("status"),
                "latest_release_number": p.get("latest_release_number"),
                "maintainers": [
                    {
                        "login": m.get("login"),
                        "email": m.get("email"),
                        "html_url": m.get("html_url"),
                    }
                    for m in maintainers
                    if isinstance(m, dict)
                ],
                "description": p.get("description") or "",
                "status_campaign": "pending",
            }
        )

    n_batches = math.ceil(len(slim) / BATCH_SIZE) if slim else 0
    for i in range(n_batches):
        chunk = slim[i * BATCH_SIZE : (i + 1) * BATCH_SIZE]
        out = {
            "batch_id": i,
            "batch_file": f"batch-{i:03d}.json",
            "count": len(chunk),
            "packages": chunk,
        }
        path = BATCHES / f"batch-{i:03d}.json"
        path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    summary = {
        "total_packages": len(slim),
        "with_repository_url": with_repo,
        "without_repository_url": len(slim) - with_repo,
        "with_maintainers": with_maintainers,
        "unpublished": unpublished,
        "batch_size": BATCH_SIZE,
        "batch_count": n_batches,
        "raw_path": str(raw_path.relative_to(ROOT)),
        "batches_dir": str(BATCHES.relative_to(ROOT)),
        "top_10": [
            {"package": s["package"], "downloads": s["downloads"], "repo": s["repository_url"]}
            for s in slim[:10]
        ],
    }
    (DATA / "inventory_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
