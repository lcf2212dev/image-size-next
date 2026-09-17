#!/usr/bin/env python3
"""Close campaign PRs still OPEN after 14 days, then forks are deleted by cleanup_closed_forks.

Never closes github/advisory-database or lcf2212dev/image-size-next.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "ledger.jsonl"
CLOSE = ROOT / "templates" / "close.md"
PR_URL = re.compile(r"https://github.com/([^/]+)/([^/]+)/pull/(\d+)")
ACCOUNT = "lcf2212dev"
KEEP_REPOS = {"github/advisory-database", "lcf2212dev/image-size-next"}


def gh(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], capture_output=True, text=True)


def gh_json(args: list[str]):
    r = gh(*args)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout)[:400])
    return json.loads(r.stdout) if r.stdout.strip() else None


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
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--days", type=int, default=14)
    args = ap.parse_args()

    who = gh("api", "user", "--jq", ".login")
    if (who.stdout or "").strip() != ACCOUNT:
        print(f"active gh user is {(who.stdout or '').strip()!r}, need {ACCOUNT}", file=sys.stderr)
        return 2

    body = CLOSE.read_text(encoding="utf-8").strip()
    urls = load_pr_urls()
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    closed = 0
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    for url in urls:
        if closed >= args.limit:
            break
        m = PR_URL.match(url)
        if not m:
            continue
        owner, repo, number = m.groups()
        full = f"{owner}/{repo}"
        if full in KEEP_REPOS:
            continue
        try:
            pr = gh_json(
                [
                    "pr",
                    "view",
                    number,
                    "--repo",
                    full,
                    "--json",
                    "state,createdAt,url,isDraft",
                ]
            )
        except RuntimeError as e:
            print(json.dumps({"url": url, "action": "skip", "error": str(e)[:200]}))
            continue
        if not pr or pr.get("state") != "OPEN":
            continue
        created = parse_dt(pr.get("createdAt"))
        if not created or created > cutoff:
            continue

        rec = {
            "url": pr.get("url") or url,
            "createdAt": pr.get("createdAt"),
            "execute": args.execute,
            "action": "pr_would_close" if not args.execute else "pr_closed_stale",
            "ts": now,
        }
        if not args.execute:
            print(json.dumps(rec, ensure_ascii=False))
            closed += 1
            continue
        r = gh("pr", "close", number, "--repo", full, "--comment", body)
        rec["ok"] = r.returncode == 0
        rec["stderr"] = (r.stderr or "")[:300]
        if r.returncode == 0:
            closed += 1
            rec["action"] = "pr_closed_stale"
            append_ledger(
                {
                    "package": repo,
                    "repo": full,
                    "url": rec["url"],
                    "ts": now,
                    "execute": True,
                    "action": "pr_closed_stale",
                    "ok": True,
                }
            )
        else:
            rec["action"] = "pr_close_failed"
        print(json.dumps(rec, ensure_ascii=False), flush=True)
        time.sleep(2)

    print(json.dumps({"closed": closed, "execute": args.execute, "days": args.days}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
