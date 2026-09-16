#!/usr/bin/env python3
"""Delete lcf2212dev forks whose campaign PRs are MERGED or CLOSED.

Keeps the fork while any campaign PR on it is still OPEN.
Never deletes image-size-next.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "ledger.jsonl"
PR_URL = re.compile(r"https://github.com/([^/]+)/([^/]+)/pull/(\d+)")
KEEP = {"lcf2212dev/image-size-next"}
ACCOUNT = "lcf2212dev"


def gh(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], capture_output=True, text=True)


def load_pr_urls() -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    if not LEDGER.exists():
        return urls
    with LEDGER.open(encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("action") not in {"pr_opened", "pr_updated"}:
                continue
            url = row.get("url")
            if isinstance(url, str) and url not in seen:
                seen.add(url)
                urls.append(url)
    return urls


def append_ledger(row: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def pr_head(url: str) -> dict | None:
    m = PR_URL.match(url)
    if not m:
        return None
    owner, repo, number = m.groups()
    r = gh(
        "pr",
        "view",
        number,
        "--repo",
        f"{owner}/{repo}",
        "--json",
        "state,mergedAt,url,headRepository,headRepositoryOwner",
    )
    if r.returncode != 0:
        return {"url": url, "error": (r.stderr or r.stdout)[:300]}
    d = json.loads(r.stdout)
    ho = (d.get("headRepositoryOwner") or {}).get("login")
    hn = (d.get("headRepository") or {}).get("name")
    head = f"{ho}/{hn}" if ho and hn else None
    return {
        "url": d.get("url") or url,
        "state": d.get("state"),
        "mergedAt": d.get("mergedAt"),
        "head": head,
        "upstream": f"{owner}/{repo}",
    }


def delete_fork(full_name: str) -> subprocess.CompletedProcess[str]:
    return gh("repo", "delete", full_name, "--yes")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true", help="Actually delete forks")
    args = ap.parse_args()

    who = gh("api", "user", "--jq", ".login")
    login = (who.stdout or "").strip()
    if login != ACCOUNT:
        print(f"active gh user is {login!r}, need {ACCOUNT}", file=sys.stderr)
        return 2

    urls = load_pr_urls()
    by_head: dict[str, list[dict]] = defaultdict(list)
    errors = []
    for url in urls:
        info = pr_head(url)
        if not info or info.get("error"):
            errors.append(info or {"url": url, "error": "parse"})
            continue
        head = info.get("head")
        if not head or not head.startswith(f"{ACCOUNT}/"):
            continue
        if head in KEEP:
            continue
        by_head[head].append(info)

    deleted = 0
    kept_open = 0
    skipped = 0
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for head, prs in sorted(by_head.items()):
        states = {p.get("state") for p in prs}
        if "OPEN" in states:
            kept_open += 1
            print(json.dumps({"head": head, "action": "keep", "reason": "open_pr", "n": len(prs)}))
            continue
        if not states <= {"MERGED", "CLOSED"}:
            skipped += 1
            print(json.dumps({"head": head, "action": "skip", "states": sorted(states)}))
            continue
        outcome = "merged" if "MERGED" in states else "closed"
        rec = {
            "fork": head,
            "action": "fork_deleted" if args.execute else "fork_would_delete",
            "reason": outcome,
            "prs": [p["url"] for p in prs],
            "execute": args.execute,
            "ts": now,
        }
        if not args.execute:
            print(json.dumps(rec, ensure_ascii=False))
            continue
        r = delete_fork(head)
        rec["ok"] = r.returncode == 0
        rec["stderr"] = (r.stderr or "")[:400]
        rec["stdout"] = (r.stdout or "")[:200]
        if r.returncode == 0:
            deleted += 1
            rec["action"] = "fork_deleted"
        else:
            rec["action"] = "fork_delete_failed"
        append_ledger(
            {
                "package": head.split("/", 1)[-1],
                "repo": head,
                "ts": now,
                "execute": True,
                "action": rec["action"],
                "reason": outcome,
                "urls": rec["prs"],
                "ok": rec["ok"],
            }
        )
        print(json.dumps(rec, ensure_ascii=False), flush=True)

    print(
        json.dumps(
            {
                "prs": len(urls),
                "forks": len(by_head),
                "kept_open": kept_open,
                "deleted": deleted,
                "skipped": skipped,
                "errors": len(errors),
                "execute": args.execute,
            }
        )
    )
    if errors:
        for e in errors:
            print(json.dumps({"error": e}, ensure_ascii=False), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
