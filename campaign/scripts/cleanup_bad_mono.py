#!/usr/bin/env python3
"""Close mistaken issues/discussions opened on mega-repos due to bad npm metadata."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "ledger.jsonl"

MEGA = {
    "facebook/react-native",
    "vercel/next.js",
    "facebook/react",
}

COMMENT = (
    "Closing: this was opened by mistake due to incorrect npm `repository` metadata "
    "on an unrelated package that listed this monorepo as its source. "
    "Apologies for the noise — not a real security report against this repository. "
    "The maintained fork notice belongs on packages that actually depend on `image-size` "
    "with a correct source repo: https://www.npmjs.com/package/image-size-next"
)


def gh(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], capture_output=True, text=True, timeout=60)


def main() -> int:
    dry = "--execute" not in sys.argv
    seen: set[str] = set()
    closed = 0
    if not LEDGER.exists():
        print("no ledger")
        return 1
    for line in LEDGER.open(encoding="utf-8"):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        repo = (row.get("repo") or "").lower()
        if repo not in MEGA:
            continue
        if row.get("action") not in {"issue_created", "discussion_created"}:
            continue
        if row.get("ok") is False:
            continue
        url = row.get("url") or ""
        if not url or url in seen:
            continue
        seen.add(url)
        # parse number
        m = re.search(r"/(issues|discussions)/(\d+)", url)
        if not m:
            print("skip unparseable", url)
            continue
        kind, num = m.group(1), m.group(2)
        owner, name = row["repo"].split("/", 1)
        # URL host may redirect react/react-native → facebook/react-native
        if "react-native" in url and "facebook" not in url:
            owner, name = "facebook", "react-native"
        print(f"{'DRY' if dry else 'CLOSE'} {kind} {owner}/{name}#{num} pkg={row.get('package')}")
        if dry:
            continue
        if kind == "issues":
            r = gh(
                "issue",
                "close",
                num,
                "--repo",
                f"{owner}/{name}",
                "--comment",
                COMMENT,
            )
            print(" ", r.returncode, (r.stderr or r.stdout or "")[:200])
            if r.returncode == 0:
                closed += 1
        else:
            # Discussions: use GraphQL update + optional delete not available; comment + lock via API
            r = gh(
                "api",
                "-X",
                "POST",
                f"repos/{owner}/{name}/discussions/{num}/comments",
                "-f",
                f"body={COMMENT}",
            )
            # try minimize/close via graphql if available
            print("  comment", r.returncode, (r.stderr or r.stdout or "")[:150])
            # GitHub has no simple close discussion CLI; leave apology comment
            closed += 1 if r.returncode == 0 else 0
    print(f"done closed_or_commented={closed} dry={dry}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
