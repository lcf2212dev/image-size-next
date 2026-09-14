#!/usr/bin/env python3
"""Send campaign messages via X API (OAuth 1.0a user context).

Modes:
  --mode dm       Direct Message (requires DM permission + recipient accepts DMs)
  --mode mention  Public reply-style tweet mentioning @handle (default fallback)

Loads credentials from image-size-next/.env:
  X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET

Reads unique handles from campaign/data/x_queue.jsonl (or --from-targets).
Writes results to campaign/data/x_send_ledger.jsonl

Usage:
  # dry-run
  python campaign/scripts/send_x_messages.py --limit 5

  # send DMs (falls back to mention if DM fails)
  python campaign/scripts/send_x_messages.py --execute --mode auto --limit 20

  # mentions only
  python campaign/scripts/send_x_messages.py --execute --mode mention --workers 1
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG_ROOT = ROOT.parent
DATA = ROOT / "data"
QUEUE = DATA / "x_queue.jsonl"
TARGETS = DATA / "targets.jsonl"
LEDGER = DATA / "x_send_ledger.jsonl"
ENV_PATH = PKG_ROOT / ".env"


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def oauth_session():
    from requests_oauthlib import OAuth1Session

    key = os.environ.get("X_API_KEY") or os.environ.get("TWITTER_API_KEY")
    secret = os.environ.get("X_API_SECRET") or os.environ.get("TWITTER_API_SECRET")
    token = os.environ.get("X_ACCESS_TOKEN") or os.environ.get("TWITTER_ACCESS_TOKEN")
    token_secret = os.environ.get("X_ACCESS_TOKEN_SECRET") or os.environ.get(
        "TWITTER_ACCESS_TOKEN_SECRET"
    )
    missing = [
        n
        for n, v in [
            ("X_API_KEY", key),
            ("X_API_SECRET", secret),
            ("X_ACCESS_TOKEN", token),
            ("X_ACCESS_TOKEN_SECRET", token_secret),
        ]
        if not v
    ]
    if missing:
        raise SystemExit(f"Missing env: {', '.join(missing)} (see {ENV_PATH})")
    return OAuth1Session(
        key,
        client_secret=secret,
        resource_owner_key=token,
        resource_owner_secret=token_secret,
    )


def verify(oauth) -> dict:
    r = oauth.get("https://api.twitter.com/1.1/account/verify_credentials.json")
    if r.status_code != 200:
        r2 = oauth.get(
            "https://api.twitter.com/2/users/me",
            params={"user.fields": "username,name,id"},
        )
        return {
            "ok": False,
            "status": r.status_code,
            "body": r.text[:500],
            "v2": {"status": r2.status_code, "body": r2.text[:300]},
        }
    data = r.json()
    return {
        "ok": True,
        "id": str(data.get("id_str") or data.get("id")),
        "username": data.get("screen_name"),
        "name": data.get("name"),
    }


def _is_dm_closed_error(row: dict) -> bool:
    body = (row.get("body") or "") + (row.get("error") or "")
    body_l = body.lower()
    return (
        "permission to dm" in body_l
        or "do not have permission to dm" in body_l
        or "this operation is not permitted" in body_l
    )


def already_sent(handle: str, require_mode: str | None = "dm") -> bool:
    """Skip if DM delivered OR recipient permanently rejects DMs from us."""
    if not LEDGER.exists():
        return False
    h = handle.lstrip("@").lower()
    with LEDGER.open(encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (row.get("handle") or "").lstrip("@").lower() != h:
                continue
            if row.get("dry_run"):
                continue
            # Permanent: inbox closed / not allowed
            if row.get("mode") == "dm" and _is_dm_closed_error(row):
                return True
            if row.get("reason") in {"dm_closed", "org_handle"}:
                return True
            if row.get("ok") is True and (
                require_mode is None or row.get("mode") == require_mode
            ):
                return True
    return False


def render_dm_text(package: str, repo: str | None) -> str:
    """Fresh template each send (includes live announce URL from config)."""
    cfg = {}
    cfg_path = ROOT / "templates" / "config.json"
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    xurl = cfg.get("x_announce_url") or "https://github.com/lcf2212dev/image-size-next"
    tpl = (ROOT / "templates" / "x_dm.md").read_text(encoding="utf-8")
    return (
        tpl.replace("{{PACKAGE_NAME}}", package or "your package")
        .replace("{{REPO}}", repo or "your repository")
        .replace("{{X_ANNOUNCE_URL}}", xurl)
        .strip()
    )


def append_ledger(row: dict) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_unique_targets(limit: int = 0) -> list[dict]:
    """Prefer x_queue; dedupe by handle (first text wins = higher-download packages first if queue order)."""
    by_handle: dict[str, dict] = {}
    if QUEUE.exists():
        with QUEUE.open(encoding="utf-8") as f:
            for line in f:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                h = (row.get("handle") or "").lstrip("@")
                if not h:
                    continue
                key = h.lower()
                if key not in by_handle:
                    by_handle[key] = {
                        "handle": h,
                        "package": row.get("package"),
                        "repo": row.get("repo"),
                        "text": row.get("text") or "",
                    }
    elif TARGETS.exists():
        rows = []
        with TARGETS.open(encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                for xh in r.get("x_handles") or []:
                    if xh.get("confidence") != "profile":
                        continue
                    rows.append(
                        (
                            r.get("downloads") or 0,
                            {
                                "handle": xh["handle"],
                                "package": r.get("package"),
                                "repo": r.get("repo"),
                                "text": (
                                    f"Heads-up: image-size (dep of {r.get('package')}) is archived "
                                    f"with CVE-2025-71329/71330. Drop-in: image-size-next@2.1.0 "
                                    f"https://www.npmjs.com/package/image-size-next "
                                    f"https://github.com/lcf2212dev/image-size-next"
                                ),
                            },
                        )
                    )
        rows.sort(key=lambda x: -x[0])
        for _, item in rows:
            key = item["handle"].lstrip("@").lower()
            if key not in by_handle:
                by_handle[key] = item

    out = list(by_handle.values())
    if limit:
        out = out[:limit]
    return out


def lookup_user_id(oauth, handle: str) -> str | None:
    h = handle.lstrip("@")
    r = oauth.get(
        f"https://api.twitter.com/2/users/by/username/{h}",
        params={"user.fields": "id,username,protected"},
    )
    if r.status_code != 200:
        return None
    data = r.json().get("data") or {}
    return data.get("id")


def send_dm(oauth, user_id: str, text: str) -> dict:
    # X API v2 DM
    r = oauth.post(
        f"https://api.twitter.com/2/dm_conversations/with/{user_id}/messages",
        json={"text": text[:10000]},
    )
    ok = r.status_code in (200, 201)
    return {"ok": ok, "status": r.status_code, "body": r.text[:500], "mode": "dm"}


def send_mention_tweet(oauth, handle: str, text: str) -> dict:
    # Keep under 280; X free/basic may allow longer on some tiers — stay safe
    mention = f"@{handle.lstrip('@')}"
    body = f"{mention} {text}".strip()
    if len(body) > 270:
        # prefer links
        body = (
            f"{mention} image-size archived + CVE-2025-71329/71330. "
            f"Drop-in: image-size-next@2.1.0 "
            f"npm.im/image-size-next github.com/lcf2212dev/image-size-next"
        )
    r = oauth.post(
        "https://api.twitter.com/2/tweets",
        json={"text": body},
    )
    ok = r.status_code in (200, 201)
    url = None
    if ok:
        try:
            tid = r.json()["data"]["id"]
            # username filled later
            url = f"https://x.com/i/web/status/{tid}"
        except Exception:
            pass
    return {
        "ok": ok,
        "status": r.status_code,
        "body": r.text[:500],
        "mode": "mention",
        "url": url,
        "text": body,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument(
        "--mode",
        choices=["dm", "mention", "auto"],
        default="auto",
        help="auto = try DM then mention",
    )
    ap.add_argument("--limit", type=int, default=0, help="Max unique handles (0=all)")
    ap.add_argument("--sleep", type=float, default=3.0, help="Seconds between sends")
    ap.add_argument("--skip-orgs", action="store_true", help="Skip likely org handles")
    ap.add_argument(
        "--abort-on-lock",
        action="store_true",
        default=True,
        help="Stop immediately if account is locked (default: on)",
    )
    ap.add_argument(
        "--no-abort-on-lock",
        action="store_true",
        help="Continue even if account lock errors appear",
    )
    args = ap.parse_args()
    abort_on_lock = args.abort_on_lock and not args.no_abort_on_lock

    load_env(ENV_PATH)

    try:
        oauth = oauth_session()
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 2

    auth = verify(oauth)
    print("auth:", json.dumps(auth, indent=2))
    if not auth.get("ok"):
        print(
            "\nX API authentication FAILED (code 32 / 401).\n"
            "Consumer Key/Secret and/or Access Token are invalid or out of sync.\n\n"
            "Fix in https://developer.x.com/en/portal/dashboard :\n"
            "  1. Open your app → Keys and tokens\n"
            "  2. Regenerate **API Key + API Key Secret** (Consumer)\n"
            "  3. Regenerate **Access Token + Access Token Secret** (same app, Read+Write+DMs)\n"
            "  4. Update image-size-next/.env (X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)\n"
            "  5. Ensure app has elevated/DM permissions if using --mode dm\n"
            "  6. Re-run this script with --execute\n",
            file=sys.stderr,
        )
        return 1

    me = auth.get("username")
    # Load all unique first; apply --limit only to not-yet-sent (after org filter)
    targets = load_unique_targets(0)
    org_block = {
        "metaopensource",
        "vercel",
        "electronjs",
        "astrodotbuild",
        "keystonejs",
        "openatmicrosoft",
        "plotlygraphs",
        "ghost",
        "lumieducation",
    }

    pending: list[dict] = []
    for t in targets:
        handle = t["handle"].lstrip("@")
        if args.skip_orgs and handle.lower() in org_block:
            continue
        # Only skip if a successful DM was already delivered
        if already_sent(handle, require_mode="dm"):
            continue
        pending.append(t)
    if args.limit:
        pending = pending[: args.limit]
    print(f"pending_to_send={len(pending)} (limit={args.limit or 'none'})", flush=True)

    stats = {"attempted": 0, "sent": 0, "skipped": 0, "failed": 0}
    for t in pending:
        handle = t["handle"].lstrip("@")
        if already_sent(handle, require_mode="dm"):
            stats["skipped"] += 1
            continue

        # Always use current security DM template (not stale queue text)
        text = render_dm_text(t.get("package") or "", t.get("repo"))
        row = {
            "handle": handle,
            "package": t.get("package"),
            "repo": t.get("repo"),
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "execute": args.execute,
        }

        if not args.execute:
            row.update({"ok": True, "dry_run": True, "mode": args.mode, "text_preview": text[:180]})
            print(json.dumps(row, ensure_ascii=False))
            stats["attempted"] += 1
            continue

        stats["attempted"] += 1
        result = None
        if args.mode in ("dm", "auto"):
            uid = lookup_user_id(oauth, handle)
            if uid:
                result = send_dm(oauth, uid, text)
                row["user_id"] = uid
            else:
                result = {"ok": False, "status": 0, "body": "user_lookup_failed", "mode": "dm"}

        if (not result or not result.get("ok")) and args.mode in ("mention", "auto"):
            result = send_mention_tweet(oauth, handle, text)

        row.update(result or {"ok": False, "error": "no_result"})
        if me and row.get("url") and "/i/web/status/" in (row.get("url") or ""):
            row["url"] = row["url"].replace("/i/web/status/", f"/{me}/status/")

        append_ledger(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
        if row.get("ok"):
            stats["sent"] += 1
        else:
            stats["failed"] += 1
            body = (row.get("body") or "") + (row.get("error") or "")
            if abort_on_lock and (
                "temporarily locked" in body.lower()
                or "account is locked" in body.lower()
                or (row.get("status") == 403 and "locked" in body.lower())
            ):
                print(
                    "ABORT: account locked by X — unlock at https://x.com and re-run later.",
                    file=sys.stderr,
                )
                stats["aborted"] = True
                break
            if abort_on_lock and row.get("status") == 402:
                print("ABORT: credits depleted.", file=sys.stderr)
                stats["aborted"] = True
                break
            if abort_on_lock and row.get("status") == 429:
                print(
                    "ABORT: rate limited (429 Too Many Requests). Wait 15–60 min then re-run.",
                    file=sys.stderr,
                )
                stats["aborted"] = True
                break
        time.sleep(args.sleep)

    print("---")
    print(json.dumps(stats, indent=2))
    return 0 if auth.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
