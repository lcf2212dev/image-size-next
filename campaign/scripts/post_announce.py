#!/usr/bin/env python3
"""Post the main image-size-next security announcement on X (thread)."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG_ROOT = ROOT.parent
ENV_PATH = PKG_ROOT / ".env"
CONFIG_PATH = ROOT / "templates" / "config.json"
DATA = ROOT / "data"


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

    return OAuth1Session(
        os.environ["X_API_KEY"],
        client_secret=os.environ["X_API_SECRET"],
        resource_owner_key=os.environ["X_ACCESS_TOKEN"],
        resource_owner_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )


POST1 = """Heads up for the Node.js ecosystem:

npm `image-size` (tens of millions of weekly downloads) is archived — and 2.0.2 is still open to CVE-2025-71329 / CVE-2025-71330 (DoS infinite loops on crafted images).

Community drop-in with fixes, same API:

image-size-next@2.1.0
https://www.npmjs.com/package/image-size-next
https://github.com/lcf2212dev/image-size-next

MIT · overrides-friendly · not affiliated with the original maintainer"""

POST2 = """Quick migrate:

npm i image-size-next

// force transitive deps (npm 8.3+):
"overrides": {
  "image-size": "npm:image-size-next@2.1.0"
}

Import: image-size → image-size-next
fromFile: image-size/fromFile → image-size-next/fromFile

npm audit fix will NOT rename the package automatically.
If you maintain a package that depends on image-size, please consider bumping or overriding."""


def main() -> int:
    load_env(ENV_PATH)
    dry = "--execute" not in sys.argv
    oauth = oauth_session()
    me = oauth.get("https://api.twitter.com/1.1/account/verify_credentials.json")
    if me.status_code != 200:
        print("auth failed", me.status_code, me.text[:300], file=sys.stderr)
        return 1
    username = me.json().get("screen_name")
    print("as", username)

    if dry:
        print("DRY RUN — pass --execute to post")
        print("--- post 1 ---")
        print(POST1)
        print("--- post 2 ---")
        print(POST2)
        return 0

    r1 = oauth.post("https://api.twitter.com/2/tweets", json={"text": POST1})
    print("post1", r1.status_code, r1.text[:400])
    if r1.status_code not in (200, 201):
        return 1
    id1 = r1.json()["data"]["id"]
    url1 = f"https://x.com/{username}/status/{id1}"

    time.sleep(2)
    r2 = oauth.post(
        "https://api.twitter.com/2/tweets",
        json={
            "text": POST2,
            "reply": {"in_reply_to_tweet_id": id1},
        },
    )
    print("post2", r2.status_code, r2.text[:400])
    id2 = None
    if r2.status_code in (200, 201):
        id2 = r2.json()["data"]["id"]

    # update config with live URL
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    cfg["x_announce_url"] = url1
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    DATA.mkdir(parents=True, exist_ok=True)
    rec = {
        "url": url1,
        "id": id1,
        "reply_id": id2,
        "username": username,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (DATA / "x_announce.json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print("ANNOUNCE_URL", url1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
