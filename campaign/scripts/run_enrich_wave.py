#!/usr/bin/env python3
"""Run enrichment for a range of batches with up to N parallel workers (default 20)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).resolve().parent / "enrich_batch.py"


def run_one(batch_id: int, force: bool) -> tuple[int, int, str]:
    cmd = [sys.executable, str(SCRIPT), "--batch", str(batch_id)]
    if force:
        cmd.append("--force")
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = (r.stdout or "") + (r.stderr or "")
    return batch_id, r.returncode, out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="from_id", type=int, required=True)
    ap.add_argument("--to", dest="to_id", type=int, required=True)
    ap.add_argument("--workers", type=int, default=20)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    ids = list(range(args.from_id, args.to_id + 1))
    print(f"Enriching batches {ids[0]}..{ids[-1]} with {args.workers} workers ({len(ids)} batches)")
    failed = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_one, bid, args.force): bid for bid in ids}
        for fut in as_completed(futs):
            bid, code, out = fut.result()
            status = "OK" if code == 0 else f"FAIL({code})"
            print(f"[{status}] batch {bid:03d}", flush=True)
            if code != 0:
                failed.append(bid)
                print(out[-1500:], file=sys.stderr)
    if failed:
        print(f"Failed batches: {failed}", file=sys.stderr)
        return 1
    print("All batches in wave completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
