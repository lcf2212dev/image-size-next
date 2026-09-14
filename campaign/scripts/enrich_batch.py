#!/usr/bin/env python3
"""Phase B: enrich one or more batches (GitHub repo, discussions, X handles).

Read-only against GitHub when GH_TOKEN or gh auth is available.
Safe to run in parallel: one process per batch_id.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from image_size_range import extract_declared_range, resolved_major  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BATCHES = DATA / "batches"
TARGETS = DATA / "targets.jsonl"
UA = "image-size-next-campaign/1.0 (+https://github.com/lcf2212dev/image-size-next)"

GITHUB_RE = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/([^/\s]+)/([^/\s?#]+)",
    re.I,
)


def gh_json(args: list[str]) -> Any | None:
    env = os.environ.copy()
    try:
        r = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return {"_error": str(e)}
    if r.returncode != 0:
        return {"_error": (r.stderr or r.stdout or f"exit {r.returncode}").strip()}
    if not r.stdout.strip():
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"_raw": r.stdout}


def http_json(url: str) -> Any | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"_error": str(e)}


def parse_github(url: str | None) -> tuple[str, str] | None:
    if not url:
        return None
    m = GITHUB_RE.search(url.replace(".git", ""))
    if not m:
        return None
    owner, repo = m.group(1), m.group(2)
    if owner.lower() in {"gist"}:
        return None
    return owner, repo


def npm_registry_doc(package: str) -> dict[str, Any] | None:
    enc = urllib.parse.quote(package, safe="@")
    data = http_json(f"https://registry.npmjs.org/{enc}")
    if not data or "_error" in data:
        return None
    return data


def npm_repository_from_doc(data: dict[str, Any] | None) -> str | None:
    if not data:
        return None
    repo = data.get("repository")
    if isinstance(repo, dict):
        return repo.get("url") or repo.get("directory")
    if isinstance(repo, str):
        return repo
    bugs = data.get("bugs")
    if isinstance(bugs, dict) and bugs.get("url"):
        return bugs["url"]
    homepage = data.get("homepage")
    return homepage if isinstance(homepage, str) else None


def npm_range_from_doc(data: dict[str, Any] | None) -> tuple[str | None, str | None]:
    if not data:
        return None, None
    latest = (data.get("dist-tags") or {}).get("latest")
    versions = data.get("versions") or {}
    manifest = versions.get(latest) if latest else None
    declared = extract_declared_range(manifest if isinstance(manifest, dict) else None)
    return declared, resolved_major(declared)


def npm_repository(package: str) -> str | None:
    return npm_repository_from_doc(npm_registry_doc(package))


def tier_for(downloads: int, special: bool = False) -> str:
    if special or downloads >= 100_000:
        return "T0"
    if downloads >= 1_000:
        return "T1"
    if downloads > 0:
        return "T2"
    return "T3"


def enrich_one(pkg: dict) -> dict:
    name = pkg["package"]
    downloads = int(pkg.get("downloads") or 0)
    repo_url = pkg.get("repository_url")
    errors: list[str] = []

    npm_doc = npm_registry_doc(name)
    declared_range, major = npm_range_from_doc(npm_doc)
    time.sleep(0.05)
    if not repo_url:
        npm_repo = npm_repository_from_doc(npm_doc)
        if npm_repo:
            repo_url = npm_repo

    host = "none"
    owner_repo = None
    gh = parse_github(repo_url or "")
    if gh:
        host = "github"
        owner_repo = f"{gh[0]}/{gh[1]}"
    elif repo_url:
        if "gitlab" in repo_url.lower():
            host = "gitlab"
        elif "bitbucket" in repo_url.lower():
            host = "bitbucket"
        else:
            host = "other"

    result: dict[str, Any] = {
        **pkg,
        "repository_url": repo_url,
        "host": host,
        "repo": owner_repo,
        "has_discussions": None,
        "has_issues": None,
        "archived": None,
        "stars": None,
        "existing_threads": [],
        "gh_owner_type": None,
        "x_handles": [],
        "tier": tier_for(downloads),
        "declared_range": declared_range,
        "resolved_major": major,
        "status_campaign": "enriched",
        "actions": {
            "discussion": "pending",
            "issue": "n/a",
            "gh_ping": "pending",
            "x_dm": "skipped",
            "pr": "optional",
        },
        "errors": errors,
        "enriched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    if host != "github" or not owner_repo:
        result["actions"]["discussion"] = "skipped"
        result["actions"]["issue"] = "skipped"
        result["actions"]["gh_ping"] = "skipped"
        if host == "none":
            result["status_campaign"] = "skipped"
            result["skip_reason"] = "no_repository"
        else:
            result["status_campaign"] = "skipped"
            result["skip_reason"] = f"non_github_host:{host}"
        return result

    owner, repo = owner_repo.split("/", 1)
    info = gh_json(["api", f"repos/{owner}/{repo}"])
    if not info or info.get("_error"):
        errors.append(f"repo_lookup: {(info or {}).get('_error', 'unknown')}")
        result["status_campaign"] = "failed"
        result["actions"]["discussion"] = "skipped"
        result["actions"]["issue"] = "skipped"
        return result

    result["has_discussions"] = bool(info.get("has_discussions"))
    result["has_issues"] = bool(info.get("has_issues"))
    result["archived"] = bool(info.get("archived"))
    result["stars"] = info.get("stargazers_count")
    result["default_branch"] = info.get("default_branch")
    result["gh_owner_type"] = (info.get("owner") or {}).get("type")

    if result["has_discussions"]:
        result["actions"]["discussion"] = "pending"
        result["actions"]["issue"] = "n/a"
    elif result["has_issues"] and not result["archived"]:
        result["actions"]["discussion"] = "n/a"
        result["actions"]["issue"] = "pending"
    else:
        result["actions"]["discussion"] = "skipped"
        result["actions"]["issue"] = "skipped"
        result["status_campaign"] = "skipped"
        result["skip_reason"] = "no_discussion_or_issues"
        return result

    # search existing related issues (best effort)
    q = f"repo:{owner_repo} image-size-next OR CVE-2025-71329 OR CVE-2025-71330"
    search = gh_json(["api", f"search/issues?q={urllib.parse.quote(q)}&per_page=5"])
    if search and not search.get("_error") and search.get("items"):
        result["existing_threads"] = [
            {"url": it.get("html_url"), "title": it.get("title"), "number": it.get("number")}
            for it in search["items"][:5]
        ]
        if result["existing_threads"]:
            result["actions"]["discussion"] = "n/a"
            result["actions"]["issue"] = "comment_existing"
            result["actions"]["gh_ping"] = "comment_existing"

    # owner twitter
    owner_info = gh_json(["api", f"users/{owner}"])
    if owner_info and not owner_info.get("_error"):
        tw = owner_info.get("twitter_username")
        if tw:
            result["x_handles"].append({"handle": tw, "confidence": "profile", "source": f"gh:{owner}"})
            result["actions"]["x_dm"] = "pending"

    # npm maintainers already on pkg; keep
    if result["tier"] == "T3" and (result.get("stars") or 0) == 0 and downloads == 0:
        result["status_campaign"] = "skipped"
        result["skip_reason"] = "tier_t3_zero_signal"
        result["actions"]["discussion"] = "skipped"
        result["actions"]["issue"] = "skipped"

    return result


def load_targets_unlocked() -> dict[str, dict]:
    out: dict[str, dict] = {}
    if TARGETS.exists():
        with TARGETS.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                key = row.get("package")
                if key:
                    out[key] = row
    return out


def merge_into_targets(updates: dict[str, dict]) -> None:
    """Merge package updates into targets.jsonl with exclusive file lock (parallel-safe)."""
    import fcntl

    DATA.mkdir(parents=True, exist_ok=True)
    lock_path = DATA / "targets.lock"
    with lock_path.open("a+", encoding="utf-8") as lockf:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
        try:
            targets = load_targets_unlocked()
            targets.update(updates)
            rows = sorted(
                targets.values(),
                key=lambda r: (-(r.get("downloads") or 0), r.get("package") or ""),
            )
            tmp = TARGETS.with_suffix(".jsonl.tmp")
            with tmp.open("w", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            tmp.replace(TARGETS)
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)


def process_batch(batch_id: int, force: bool = False) -> dict:
    path = BATCHES / f"batch-{batch_id:03d}.json"
    if not path.exists():
        raise FileNotFoundError(path)
    batch = json.loads(path.read_text(encoding="utf-8"))
    # read existing under lock for skip decisions
    import fcntl

    DATA.mkdir(parents=True, exist_ok=True)
    lock_path = DATA / "targets.lock"
    with lock_path.open("a+", encoding="utf-8") as lockf:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_SH)
        try:
            existing = load_targets_unlocked()
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)

    stats = {"batch_id": batch_id, "ok": 0, "skipped": 0, "failed": 0, "packages": []}
    updates: dict[str, dict] = {}

    for pkg in batch["packages"]:
        name = pkg["package"]
        if not force and name in existing and existing[name].get("status_campaign") in {
            "enriched",
            "contacted",
            "skipped",
            "done",
        }:
            stats["packages"].append(name)
            updates[name] = existing[name]
            if existing[name].get("status_campaign") == "skipped":
                stats["skipped"] += 1
            else:
                stats["ok"] += 1
            continue

        enriched = enrich_one(pkg)
        updates[name] = enriched
        st = enriched.get("status_campaign")
        if st == "failed":
            stats["failed"] += 1
        elif st == "skipped":
            stats["skipped"] += 1
        else:
            stats["ok"] += 1
        stats["packages"].append(name)
        # light pacing for gh secondary limits
        time.sleep(0.25)

    merge_into_targets(updates)
    # also write enriched batch snapshot (per-batch, no race)
    out_path = DATA / "enriched" / f"batch-{batch_id:03d}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "batch_id": batch_id,
        "packages": [updates[n] for n in stats["packages"] if n in updates],
    }
    out_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description="Enrich dependent package batches")
    ap.add_argument("--batch", type=int, help="Single batch id")
    ap.add_argument("--from", dest="from_id", type=int, help="Start batch id inclusive")
    ap.add_argument("--to", dest="to_id", type=int, help="End batch id inclusive")
    ap.add_argument("--force", action="store_true", help="Re-enrich even if present")
    args = ap.parse_args()

    if args.batch is not None:
        ids = [args.batch]
    elif args.from_id is not None and args.to_id is not None:
        ids = list(range(args.from_id, args.to_id + 1))
    else:
        ap.error("Provide --batch N or --from A --to B")
        return 2

    all_stats = []
    for bid in ids:
        print(f"=== enrich batch {bid} ===", flush=True)
        try:
            st = process_batch(bid, force=args.force)
            print(json.dumps(st, indent=2), flush=True)
            all_stats.append(st)
        except Exception as e:
            print(f"batch {bid} error: {e}", file=sys.stderr)
            all_stats.append({"batch_id": bid, "error": str(e)})
    (DATA / "last_enrich_stats.json").write_text(
        json.dumps(all_stats, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
