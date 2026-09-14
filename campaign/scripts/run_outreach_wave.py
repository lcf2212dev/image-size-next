#!/usr/bin/env python3
"""Run Phase D outreach for a range of batches.

Default is dry-run. Pass --execute to write. Parallelism defaults to 1;
--execute refuses workers > 1 (GitHub AUP / secondary rate limits).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "open_discussion.py"


def run_one(batch_id: int, execute: bool) -> tuple[int, int, str]:
    cmd = [sys.executable, str(SCRIPT), "--batch", str(batch_id)]
    if execute:
        cmd.append("--execute")
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = (r.stdout or "") + (("\n" + r.stderr) if r.stderr else "")
    return batch_id, r.returncode, out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="from_id", type=int, required=True)
    ap.add_argument("--to", dest="to_id", type=int, required=True)
    ap.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Parallel batch processes (default 1; must be 1 with --execute)",
    )
    ap.add_argument(
        "--execute",
        action="store_true",
        help="Pass --execute to open_discussion.py (default: dry-run)",
    )
    ap.add_argument("--dry-run", action="store_true", help="Force dry-run (default)")
    args = ap.parse_args()

    execute = bool(args.execute) and not args.dry_run
    if execute and args.workers > 1:
        print("Refusing --execute with workers>1 (GitHub AUP). Use --workers 1.", file=sys.stderr)
        return 2
    ids = list(range(args.from_id, args.to_id + 1))
    print(
        f"Outreach batches {ids[0]}..{ids[-1]} workers={args.workers} execute={execute}",
        flush=True,
    )
    failed = []
    summaries = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs = {ex.submit(run_one, bid, execute): bid for bid in ids}
        for fut in as_completed(futs):
            bid, code, out = fut.result()
            # parse last JSON summary if present
            summary_line = ""
            if "---" in out:
                tail = out.split("---")[-1].strip()
                summary_line = tail[:500]
                try:
                    summaries.append(json.loads(tail[tail.find("{") :]))
                except Exception:
                    pass
            status = "OK" if code == 0 else f"FAIL({code})"
            print(f"[{status}] batch {bid:03d} {summary_line[:200]}", flush=True)
            if code != 0:
                failed.append(bid)
                print(out[-2000:], file=sys.stderr)

    # aggregate actions
    actions: dict[str, int] = {}
    total = 0
    for s in summaries:
        total += s.get("count") or 0
        for k, v in (s.get("actions") or {}).items():
            actions[k] = actions.get(k, 0) + v
    print("--- wave summary ---")
    print(json.dumps({"batches": len(ids), "failed": failed, "packages_seen": total, "actions": actions}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
