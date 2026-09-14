#!/usr/bin/env python3
"""Classify a dependent's image-size major (1 vs 2) from an npm range."""

from __future__ import annotations

import re
from typing import Any

RANGE_RE = re.compile(
    r"""
    ^\s*
    (?P<op>>=|<=|>|<|=|~|\^)?
    \s*
    v?
    (?P<major>0|[1-9]\d*)
    """,
    re.VERBOSE,
)


def extract_declared_range(manifest: dict[str, Any] | None) -> str | None:
    """Return the image-size range from a package.json / npm version document."""
    if not isinstance(manifest, dict):
        return None
    for key in ("dependencies", "optionalDependencies", "peerDependencies", "devDependencies"):
        deps = manifest.get(key)
        if isinstance(deps, dict) and "image-size" in deps:
            spec = deps.get("image-size")
            if isinstance(spec, str) and spec.strip():
                return spec.strip()
    return None


def resolved_major(range_spec: str | None) -> str | None:
    """Return '1', '2', or None if the range is missing/ambiguous.

    Never maps a 1.x consumer onto 2.x. Ranges that can satisfy both majors
    (e.g. ``*``, ``>=1``, ``>=0``) return None so outreach must not guess.
    """
    if not range_spec:
        return None
    spec = range_spec.strip()
    if spec.startswith("npm:"):
        # already aliased; still parse trailing version if present
        spec = spec.split("@")[-1]

    if spec in {"*", "x", "X", "latest"}:
        return None

    # Union ranges: only accept if every clause agrees on one major.
    majors: set[str] = set()
    for clause in re.split(r"\s*\|\|\s*", spec):
        clause = clause.strip()
        if not clause:
            continue
        # hyphen ranges / space AND: inspect the first version token
        token = clause.split()[0] if clause.split() else clause
        m = RANGE_RE.match(token.lstrip("="))
        if not m:
            return None
        major = m.group("major")
        op = m.group("op") or ""
        if major in {"0", "1"}:
            if op in {">", ">="}:
                # >=1 / >0 also matches 2.x
                return None
            majors.add("1")
        elif major == "2":
            if op in {">", ">="}:
                # >=2 is still 2.x for this package (no 3.x line)
                majors.add("2")
            elif op in {"<", "<="}:
                return None
            else:
                majors.add("2")
        else:
            return None
    if majors == {"1"}:
        return "1"
    if majors == {"2"}:
        return "2"
    return None


def line_for_major(config: dict[str, Any], major: str) -> dict[str, Any]:
    lines = config.get("lines") or {}
    line = lines.get(str(major))
    if not isinstance(line, dict):
        raise KeyError(f"config.lines[{major}] missing")
    return line
