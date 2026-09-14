#!/usr/bin/env python3
"""Phase D: open GitHub Discussion or Issue for packages in a batch.

Default is dry-run. Pass --execute to create threads (requires `gh auth`).
"""

from __future__ import annotations

import argparse
import fcntl
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TEMPLATES = ROOT / "templates"
LEDGER = DATA / "ledger.jsonl"
X_QUEUE = DATA / "x_queue.jsonl"
LOCK = DATA / "outreach.lock"
CONFIG_PATH = TEMPLATES / "config.json"
SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from image_size_range import line_for_major  # noqa: E402

WRITE_ACTIONS = {"discussion_created", "issue_created", "comment_existing"}


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def write_pacing_s(config: dict) -> float:
    try:
        return max(60.0, float(config.get("write_pacing_s") or 300))
    except (TypeError, ValueError):
        return 300.0


def daily_write_cap(config: dict) -> int:
    try:
        return max(1, int(config.get("daily_write_cap") or 5))
    except (TypeError, ValueError):
        return 5


def ledger_writes_today() -> int:
    if not LEDGER.exists():
        return 0
    today = time.strftime("%Y-%m-%d", time.gmtime())
    n = 0
    with LEDGER.open(encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = str(row.get("ts") or "")
            if (
                ts.startswith(today)
                and row.get("execute")
                and row.get("action") in WRITE_ACTIONS
                and row.get("ok") is not False
            ):
                n += 1
    return n


def render(
    template_name: str,
    package: str,
    repo: str | None,
    config: dict,
    extras: dict[str, str] | None = None,
) -> str:
    text = (TEMPLATES / template_name).read_text(encoding="utf-8")
    xurl = config.get("x_announce_url") or "REPLACE_WITH_PINNED_X_THREAD_URL"
    hub = config.get("hub_discussion_url") or config.get("github_url") or ""
    mapping = {
        "{{PACKAGE_NAME}}": package,
        "{{REPO}}": repo or "the repository",
        "{{X_ANNOUNCE_URL}}": xurl,
        "{{HUB_DISCUSSION_URL}}": hub,
    }
    if extras:
        mapping.update(extras)
    for key, val in mapping.items():
        text = text.replace(key, val)
    return text


def line_placeholders(pkg: dict, config: dict) -> dict[str, str] | None:
    major = str(pkg.get("resolved_major") or "")
    if major not in {"1", "2"}:
        return None
    line = line_for_major(config, major)
    declared = pkg.get("declared_range") or f"^{line['upstream_version']}"
    return {
        "{{DECLARED_RANGE}}": str(declared),
        "{{FORK_VERSION}}": str(line["fork_version"]),
        "{{UPSTREAM_VERSION}}": str(line["upstream_version"]),
        "{{DIST_TAG}}": str(line.get("dist_tag") or ""),
        "{{COMPARE_URL}}": str(line.get("compare_url") or ""),
        "{{API_NOTE}}": str(line.get("api_note") or ""),
    }


def _with_lock(exclusive: bool = True):
    DATA.mkdir(parents=True, exist_ok=True)
    lockf = LOCK.open("a+", encoding="utf-8")
    fcntl.flock(lockf.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
    return lockf


def ledger_has(package: str) -> bool:
    """True if package already has a terminal ledger action (skip or successful write)."""
    if not LEDGER.exists():
        return False
    lockf = _with_lock(exclusive=False)
    try:
        with LEDGER.open(encoding="utf-8") as f:
            for line in f:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if row.get("package") != package:
                    continue
                action = row.get("action")
                if action in {"skipped", "already_in_ledger", "repo_mismatch"}:
                    return True
                if action in {
                    "discussion_created",
                    "issue_created",
                    "comment_existing",
                } and row.get("ok") is not False:
                    return True
    finally:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
        lockf.close()
    return False


# High-star monorepos that wrong npm metadata often points at.
MEGA_REPOS = {
    "vercel/next.js",
    "facebook/react-native",
    "facebook/react",
    "nodejs/node",
    "microsoft/typescript",
    "webpack/webpack",
    "angular/angular",
    "vuejs/core",
    "vuejs/vue",
    "mui/material-ui",
    "vercel/vercel",
    "nrwl/nx",
    "remix-run/remix",
    "remix-run/react-router",
}


def package_matches_repo(package: str, owner: str, repo: str, stars: int | None) -> bool:
    """Reject wrong repository_url mappings (e.g. random pkg → next.js)."""
    full = f"{owner}/{repo}".lower()
    bare = package.split("/")[-1].lower()
    r = repo.lower()
    bare_norm = bare.replace("_", "-")
    r_norm = r.replace("_", "-")

    exact = bare_norm == r_norm or bare_norm == r_norm.replace(".js", "")
    if full in MEGA_REPOS:
        return exact
    if stars is not None and stars >= 5000:
        return exact or bare_norm.startswith(r_norm) or r_norm.startswith(bare_norm)
    # Trust low-star / normal packages with any recorded github repo.
    return True


def gh_with_retry(*args: str, retries: int = 4) -> subprocess.CompletedProcess[str]:
    delay = 2.0
    last: subprocess.CompletedProcess[str] | None = None
    for attempt in range(retries):
        last = gh(*args)
        err = ((last.stderr or "") + (last.stdout or "")).lower()
        if last.returncode == 0:
            return last
        if "too quickly" in err or "secondary rate limit" in err or "403" in err and "rate" in err:
            time.sleep(delay)
            delay = min(delay * 2, 60)
            continue
        if "502" in err or "503" in err:
            time.sleep(delay)
            delay = min(delay * 2, 30)
            continue
        return last
    assert last is not None
    return last


def append_ledger(row: dict) -> None:
    lockf = _with_lock(exclusive=True)
    try:
        with LEDGER.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    finally:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
        lockf.close()


def append_x_queue(row: dict) -> None:
    lockf = _with_lock(exclusive=True)
    try:
        with X_QUEUE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    finally:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
        lockf.close()


def gh(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        timeout=90,
    )


def discussion_category_id(owner: str, repo: str) -> str | None:
    """Return first suitable discussion category node id."""
    query = """
    query($owner:String!,$repo:String!) {
      repository(owner:$owner, name:$repo) {
        discussionCategories(first: 20) {
          nodes { id name slug isAnswerable }
        }
      }
    }
    """
    r = gh(
        "api",
        "graphql",
        "-f",
        f"query={query}",
        "-F",
        f"owner={owner}",
        "-F",
        f"repo={repo}",
    )
    if r.returncode != 0:
        return None
    try:
        data = json.loads(r.stdout)
        nodes = (
            data.get("data", {})
            .get("repository", {})
            .get("discussionCategories", {})
            .get("nodes")
            or []
        )
    except json.JSONDecodeError:
        return None
    if not nodes:
        return None
    preferred = ("general", "announcements", "ideas", "q-a", "show-and-tell")
    by_slug = {n.get("slug", "").lower(): n for n in nodes}
    for slug in preferred:
        if slug in by_slug:
            return by_slug[slug]["id"]
    return nodes[0]["id"]


def repo_node_id(owner: str, repo: str) -> str | None:
    r = gh("api", f"repos/{owner}/{repo}", "--jq", ".node_id")
    if r.returncode != 0:
        return None
    return r.stdout.strip() or None


def create_discussion(owner: str, repo: str, title: str, body: str) -> dict[str, Any]:
    cat = discussion_category_id(owner, repo)
    rid = repo_node_id(owner, repo)
    if not cat or not rid:
        return {"ok": False, "error": "missing_category_or_repo_id"}
    mutation = """
    mutation($repo:ID!,$category:ID!,$title:String!,$body:String!) {
      createDiscussion(input:{repositoryId:$repo,categoryId:$category,title:$title,body:$body}) {
        discussion { url number }
      }
    }
    """
    r = gh_with_retry(
        "api",
        "graphql",
        "-f",
        f"query={mutation}",
        "-F",
        f"repo={rid}",
        "-F",
        f"category={cat}",
        "-F",
        f"title={title}",
        "-F",
        f"body={body}",
    )
    if r.returncode != 0:
        return {"ok": False, "error": (r.stderr or r.stdout).strip()}
    try:
        data = json.loads(r.stdout)
        if data.get("errors"):
            return {"ok": False, "error": json.dumps(data["errors"])[:500]}
        d = data["data"]["createDiscussion"]["discussion"]
        return {"ok": True, "url": d["url"], "number": d["number"]}
    except Exception as e:
        return {"ok": False, "error": f"parse: {e} raw={(r.stdout or '')[:500]}"}


def create_issue(owner: str, repo: str, title: str, body: str) -> dict[str, Any]:
    # Prefer REST API — more reliable under parallel load than `gh issue create` stdout.
    r = gh_with_retry(
        "api",
        f"repos/{owner}/{repo}/issues",
        "-f",
        f"title={title}",
        "-f",
        f"body={body}",
    )
    out = (r.stdout or "").strip()
    err = (r.stderr or "").strip()
    if r.returncode != 0:
        return {"ok": False, "error": err or out or f"exit {r.returncode}"}
    try:
        data = json.loads(out)
        url = data.get("html_url")
        if url:
            return {"ok": True, "url": url, "number": data.get("number")}
    except json.JSONDecodeError:
        pass
    # Fallback: scrape URL from mixed stdout/stderr
    import re

    blob = f"{out}\n{err}"
    m = re.search(r"https://github\.com/[^\s]+/issues/\d+", blob)
    if m:
        return {"ok": True, "url": m.group(0)}
    return {"ok": False, "error": err or out or "empty response from create issue"}


def comment_on_issue(owner: str, repo: str, number: int, body: str) -> dict[str, Any]:
    r = gh_with_retry(
        "issue",
        "comment",
        str(number),
        "--repo",
        f"{owner}/{repo}",
        "--body",
        body,
    )
    if r.returncode != 0:
        return {"ok": False, "error": (r.stderr or r.stdout or "").strip()}
    return {"ok": True, "url": (r.stdout or "").strip()}


def load_enriched_batch(batch_id: int) -> list[dict]:
    path = DATA / "enriched" / f"batch-{batch_id:03d}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8")).get("packages") or []
    # fallback: filter targets.jsonl by batch file membership
    batch_path = DATA / "batches" / f"batch-{batch_id:03d}.json"
    if not batch_path.exists():
        return []
    names = {p["package"] for p in json.loads(batch_path.read_text())["packages"]}
    targets_path = DATA / "targets.jsonl"
    if not targets_path.exists():
        return []
    out = []
    with targets_path.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if row.get("package") in names:
                out.append(row)
    return out


def process_package(pkg: dict, config: dict, execute: bool) -> dict:
    name = pkg.get("package")
    repo = pkg.get("repo")
    actions = pkg.get("actions") or {}
    row: dict[str, Any] = {
        "package": name,
        "repo": repo,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "execute": execute,
    }

    if ledger_has(name):
        row["action"] = "already_in_ledger"
        row["ok"] = True
        return row

    extras = line_placeholders(pkg, config)
    if extras is None:
        row["action"] = "skipped"
        row["reason"] = "unknown_major"
        row["ok"] = True
        if execute:
            append_ledger(row)
        return row
    row["resolved_major"] = pkg.get("resolved_major")
    row["declared_range"] = pkg.get("declared_range")

    if pkg.get("status_campaign") == "skipped" or not repo:
        row["action"] = "skipped"
        row["reason"] = pkg.get("skip_reason") or "no_repo"
        if execute:
            append_ledger(row)
        return row

    owner, rname = repo.split("/", 1)
    if not package_matches_repo(name, owner, rname, pkg.get("stars")):
        row["action"] = "repo_mismatch"
        row["reason"] = f"package {name} does not match high-star/mega repo {repo}"
        row["ok"] = True
        if execute:
            append_ledger(row)
        return row

    title = config.get("discussion_title") or config.get("issue_title")
    body_disc = render("discussion.md", name, repo, config, extras)
    body_issue = render("issue.md", name, repo, config, extras)
    body_comment = render("maintainer_comment.md", name, repo, config, extras)

    # @maintainers from npm logins is weak; prefer gh owner if user
    mentions = []
    if pkg.get("gh_owner_type") == "User":
        mentions.append(f"@{owner}")
    if mentions:
        body_disc = body_disc + "\n\ncc " + " ".join(mentions)
        body_issue = body_issue + "\n\ncc " + " ".join(mentions)

    if actions.get("issue") == "comment_existing" and pkg.get("existing_threads"):
        thr = pkg["existing_threads"][0]
        number = thr.get("number")
        row["action"] = "comment_existing"
        row["target"] = thr.get("url")
        if execute and number:
            res = comment_on_issue(owner, rname, int(number), body_comment)
            row.update(res)
            append_ledger(row)
        else:
            row["ok"] = True
            row["dry_run_body_preview"] = body_comment[:200]
        return row

    if actions.get("discussion") == "pending" and pkg.get("has_discussions"):
        row["action"] = "discussion_created"
        if execute:
            res = create_discussion(owner, rname, title, body_disc)
            row.update(res)
            append_ledger(row)
        else:
            row["ok"] = True
            row["dry_run"] = {"title": title, "body_preview": body_disc[:240]}
        return row

    if actions.get("issue") == "pending" and pkg.get("has_issues"):
        row["action"] = "issue_created"
        if execute:
            res = create_issue(owner, rname, title, body_issue)
            row.update(res)
            append_ledger(row)
        else:
            row["ok"] = True
            row["dry_run"] = {"title": title, "body_preview": body_issue[:240]}
        return row

    row["action"] = "skipped"
    row["reason"] = "no_actionable_surface"
    if execute:
        append_ledger(row)
    return row


def maybe_queue_x(pkg: dict, config: dict, execute: bool) -> None:
    extras = line_placeholders(pkg, config)
    if extras is None:
        return
    for h in pkg.get("x_handles") or []:
        if h.get("confidence") != "profile":
            continue
        text = render("x_dm.md", pkg["package"], pkg.get("repo"), config, extras)
        entry = {
            "package": pkg["package"],
            "repo": pkg.get("repo"),
            "handle": h["handle"],
            "confidence": h["confidence"],
            "text": text,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "queued" if execute else "dry_run_queue",
        }
        if execute:
            append_x_queue(entry)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, required=True)
    ap.add_argument(
        "--execute",
        action="store_true",
        help="Actually create GitHub Discussion/Issue (default: dry-run)",
    )
    ap.add_argument("--limit", type=int, default=0, help="Max packages in this run (0=all)")
    args = ap.parse_args()

    config = load_config()
    if args.execute and "REPLACE" in (config.get("x_announce_url") or ""):
        print(
            "WARNING: x_announce_url still placeholder — set campaign/templates/config.json",
            file=sys.stderr,
        )

    packages = load_enriched_batch(args.batch)
    if not packages:
        print(f"No enriched packages for batch {args.batch}. Run enrich_batch.py first.", file=sys.stderr)
        return 1

    pacing = write_pacing_s(config)
    cap = daily_write_cap(config)
    writes_today = ledger_writes_today()
    if args.execute:
        print(
            json.dumps(
                {
                    "pacing_s": pacing,
                    "daily_write_cap": cap,
                    "writes_today": writes_today,
                }
            ),
            flush=True,
        )

    results = []
    for i, pkg in enumerate(packages):
        if args.limit and i >= args.limit:
            break
        if args.execute and writes_today >= cap:
            results.append(
                {
                    "package": pkg.get("package"),
                    "action": "capped",
                    "reason": f"daily_write_cap {cap}",
                    "ok": True,
                }
            )
            print(json.dumps(results[-1], ensure_ascii=False), flush=True)
            continue
        res = process_package(pkg, config, args.execute)
        maybe_queue_x(pkg, config, args.execute)
        results.append(res)
        print(json.dumps(res, ensure_ascii=False), flush=True)
        if args.execute and res.get("action") in WRITE_ACTIONS and res.get("ok") is not False:
            writes_today += 1
            time.sleep(pacing)


    summary = {
        "batch": args.batch,
        "execute": args.execute,
        "count": len(results),
        "actions": {},
    }
    for r in results:
        a = r.get("action") or "unknown"
        summary["actions"][a] = summary["actions"].get(a, 0) + 1
    print("---")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
