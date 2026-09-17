#!/usr/bin/env python3
"""Comment once on open campaign PRs with no human reply after 7 days.

Only if the upstream owner is a GitHub User (not an Organization).
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
BUMP = ROOT / "templates" / "bump.md"
PR_URL = re.compile(r"https://github.com/([^/]+)/([^/]+)/pull/(\d+)")
ACCOUNT = "lcf2212dev"
BOT_HINTS = (
    "[bot]",
    "dependabot",
    "renovate",
    "github-actions",
    "coderabbit",
    "socket-security",
    "imgbot",
    "linear-app",
    "cla-bot",
    "semantic-release",
    "allcontributors",
    "snyk-bot",
    "deepsource",
    "sonarcloud",
)
STALE = timedelta(days=7)


def gh(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], capture_output=True, text=True)


def gh_json(args: list[str]):
    r = gh(*args)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout)[:400])
    return json.loads(r.stdout) if r.stdout.strip() else None


def load_ledger() -> tuple[list[str], set[str]]:
    urls: list[str] = []
    seen: set[str] = set()
    bumped: set[str] = set()
    if not LEDGER.exists():
        return urls, bumped
    with LEDGER.open(encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            url = row.get("url")
            action = row.get("action")
            if action == "bump_commented" and isinstance(url, str):
                bumped.add(url)
            if action in {"pr_opened", "pr_updated"} and isinstance(url, str) and url not in seen:
                seen.add(url)
                urls.append(url)
    return urls, bumped


def append_ledger(row: dict) -> None:
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def is_bot(login: str | None) -> bool:
    if not login:
        return True
    low = login.lower()
    if login.endswith("[bot]") or low.endswith("-bot"):
        return True
    return any(h in low for h in BOT_HINTS)


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def humans_replied(owner: str, repo: str, number: str) -> bool:
    issue_comments = gh_json(["api", f"repos/{owner}/{repo}/issues/{number}/comments?per_page=100"]) or []
    review_comments = gh_json(["api", f"repos/{owner}/{repo}/pulls/{number}/comments?per_page=100"]) or []
    reviews = gh_json(["api", f"repos/{owner}/{repo}/pulls/{number}/reviews?per_page=100"]) or []
    for item in list(issue_comments) + list(review_comments) + list(reviews):
        user = (item.get("user") or {}).get("login")
        if user == ACCOUNT or is_bot(user):
            continue
        body = (item.get("body") or "").strip()
        state = item.get("state")
        # empty pending reviews from GitHub UI don't count
        if not body and state in {None, "PENDING", "COMMENTED"}:
            continue
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--days", type=int, default=7)
    args = ap.parse_args()

    who = gh("api", "user", "--jq", ".login")
    if (who.stdout or "").strip() != ACCOUNT:
        print(f"active gh user is {(who.stdout or '').strip()!r}, need {ACCOUNT}", file=sys.stderr)
        return 2

    body = BUMP.read_text(encoding="utf-8").strip() + "\n"
    urls, already = load_ledger()
    stale_after = datetime.now(timezone.utc) - timedelta(days=args.days)
    posted = 0
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    for url in urls:
        if posted >= args.limit:
            break
        if url in already:
            continue
        m = PR_URL.match(url)
        if not m:
            continue
        owner, repo, number = m.groups()
        try:
            pr = gh_json(
                [
                    "pr",
                    "view",
                    number,
                    "--repo",
                    f"{owner}/{repo}",
                    "--json",
                    "state,createdAt,url,isDraft",
                ]
            )
            repo_info = gh_json(["api", f"repos/{owner}/{repo}", "--jq", "{login:.owner.login,type:.owner.type}"])
        except RuntimeError as e:
            print(json.dumps({"url": url, "action": "skip", "error": str(e)[:200]}))
            continue
        if not pr or pr.get("state") != "OPEN" or pr.get("isDraft"):
            continue
        created = parse_dt(pr.get("createdAt"))
        if not created or created > stale_after:
            continue
        owner_type = (repo_info or {}).get("type")
        if owner_type != "User":
            print(json.dumps({"url": url, "action": "skip", "reason": f"owner_{owner_type}"}))
            continue
        try:
            if humans_replied(owner, repo, number):
                print(json.dumps({"url": url, "action": "skip", "reason": "has_reply"}))
                continue
        except RuntimeError as e:
            print(json.dumps({"url": url, "action": "skip", "error": str(e)[:200]}))
            continue

        rec = {
            "url": pr.get("url") or url,
            "owner": owner,
            "owner_type": owner_type,
            "createdAt": pr.get("createdAt"),
            "execute": args.execute,
            "action": "bump_would_comment" if not args.execute else "bump_commented",
            "ts": now,
        }
        if not args.execute:
            print(json.dumps(rec, ensure_ascii=False))
            posted += 1
            continue
        r = gh("pr", "comment", number, "--repo", f"{owner}/{repo}", "--body", body)
        rec["ok"] = r.returncode == 0
        rec["stderr"] = (r.stderr or "")[:300]
        if r.returncode == 0:
            posted += 1
            rec["action"] = "bump_commented"
            append_ledger(
                {
                    "package": repo,
                    "repo": f"{owner}/{repo}",
                    "url": rec["url"],
                    "ts": now,
                    "execute": True,
                    "action": "bump_commented",
                    "ok": True,
                }
            )
        else:
            rec["action"] = "bump_failed"
        print(json.dumps(rec, ensure_ascii=False), flush=True)
        time.sleep(2)

    print(json.dumps({"posted": posted, "execute": args.execute, "days": args.days}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
