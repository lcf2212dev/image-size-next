#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from image_size_range import extract_declared_range, resolved_major

CASES = {
    "^1.0.2": "1",
    "~1.2.1": "1",
    "1.2.1": "1",
    "^2.0.2": "2",
    "2.0.2": "2",
    "*": None,
    "latest": None,
    ">=1": None,
    ">=1.2.1": None,
    ">1": None,
    "^1.0.2 || ^2.0.2": None,
    "npm:image-size-next@1.2.2": "1",
}


def main() -> int:
    failed = 0
    for spec, expected in CASES.items():
        got = resolved_major(spec)
        if got != expected:
            print(f"FAIL {spec!r} -> {got!r} expected {expected!r}")
            failed += 1
    assert extract_declared_range({"dependencies": {"image-size": "^1.0.2"}}) == "^1.0.2"
    if failed:
        return 1
    print(f"ok {len(CASES)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
