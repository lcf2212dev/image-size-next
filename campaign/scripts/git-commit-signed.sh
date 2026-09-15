#!/usr/bin/env bash
# Sign as lcf2212dev (SSH key already uploaded to GitHub as a signing key).
# Usage: git-commit-signed.sh -m "message"   (any git commit args after)
set -euo pipefail
KEY="${ISN_SIGNING_KEY:-$HOME/.ssh/id_ed25519_lcf2212.pub}"
if [[ ! -f "$KEY" ]]; then
  echo "missing signing key: $KEY" >&2
  exit 1
fi
exec git \
  -c user.name=lcf2212dev \
  -c user.email=lcf2212dev@users.noreply.github.com \
  -c gpg.format=ssh \
  -c user.signingkey="$KEY" \
  -c commit.gpgsign=true \
  commit "$@"
