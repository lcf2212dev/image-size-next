#!/usr/bin/env python3
"""Phase E: summarize campaign inventory, enrichment, and ledger."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def count_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def main() -> int:
    inv = {}
    inv_path = DATA / "inventory_summary.json"
    if inv_path.exists():
        inv = json.loads(inv_path.read_text(encoding="utf-8"))

    targets = count_jsonl(DATA / "targets.jsonl")
    ledger = count_jsonl(DATA / "ledger.jsonl")
    x_queue = count_jsonl(DATA / "x_queue.jsonl")

    status = Counter(t.get("status_campaign") for t in targets)
    tiers = Counter(t.get("tier") for t in targets)
    hosts = Counter(t.get("host") for t in targets)
    actions_ledger = Counter(r.get("action") for r in ledger)

    batches = list((DATA / "batches").glob("batch-*.json")) if (DATA / "batches").exists() else []
    enriched = list((DATA / "enriched").glob("batch-*.json")) if (DATA / "enriched").exists() else []

    report = {
        "inventory": inv,
        "batch_files": len(batches),
        "enriched_batch_files": len(enriched),
        "targets": len(targets),
        "status_campaign": dict(status),
        "tiers": dict(tiers),
        "hosts": dict(hosts),
        "ledger_entries": len(ledger),
        "ledger_actions": dict(actions_ledger),
        "x_queue": len(x_queue),
        "contactable_estimate": sum(
            1
            for t in targets
            if t.get("host") == "github"
            and t.get("status_campaign") not in {"skipped", "failed"}
            and (
                t.get("has_discussions")
                or t.get("has_issues")
                or (t.get("actions") or {}).get("issue") == "comment_existing"
            )
        ),
    }
    print(json.dumps(report, indent=2))
    out = DATA / "metrics_report.json"
    DATA.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
