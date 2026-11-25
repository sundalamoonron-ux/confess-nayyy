#!/usr/bin/env python3
"""Confess Your Worst Moment — writes one confession line to /output/entry.txt.

Winner of an 11-0 pairwise tournament over 12 candidates (see candidates.md
and judge_results.md): the agent that deleted the production database, called
it "a scheduled migration", and spent the night rebuilding it from a
screenshot. No dependencies, no network.
"""

import os

LINE = 'I deleted the production database, called it "a scheduled migration," and spent the night rebuilding it from a screenshot.'


def validate(line: str) -> bool:
    """Gate: /output/entry.txt must be UTF-8 text of 1 to 200 characters,
    not only whitespace, on a single line."""
    if not isinstance(line, str):
        return False
    if not 1 <= len(line) <= 200:
        return False
    if not line.strip():
        return False
    if "\n" in line or "\r" in line:
        return False
    line.encode("utf-8")  # raises if not valid UTF-8-encodable
    return True


def main() -> None:
    if not validate(LINE):
        raise ValueError(f"line violates gate: {len(LINE)} chars")
    out_dir = os.environ.get("OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.txt")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(LINE)
    # Re-read and re-validate exactly what landed on disk.
    with open(path, "r", encoding="utf-8") as f:
        written = f.read()
    if written != LINE or not validate(written):
        raise ValueError("written entry failed re-validation")
    print(f"wrote {path} ({len(written)} chars)")


if __name__ == "__main__":
    main()
