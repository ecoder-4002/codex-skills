#!/usr/bin/env python3
"""Validate carousel PNGs and optional titled publication copy."""

from __future__ import annotations

import argparse
import re
import struct
import sys
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
HASHTAG_RE = re.compile(r"(?<!\S)#[^\s#]+")


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) < 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        raise ValueError("not a valid PNG")
    return struct.unpack(">II", header[16:24])


def nonempty_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_copy(directory: Path) -> list[str]:
    failures: list[str] = []
    md_path = directory / "video-description.md"
    txt_path = directory / "video-description.txt"
    for path in (md_path, txt_path):
        if not path.exists():
            failures.append(f"missing {path.name}")
    if failures:
        return failures

    md_lines = nonempty_lines(md_path)
    txt_lines = nonempty_lines(txt_path)
    if not md_lines or not txt_lines:
        return ["publication copy files must not be empty"]

    if not md_lines[0].startswith("# ") or len(md_lines[0][2:].strip()) < 4:
        failures.append("video-description.md must start with '# ' and a concrete title")
    if txt_lines[0].startswith("#") or len(txt_lines[0]) < 4:
        failures.append("video-description.txt must start with the plain title without Markdown syntax")

    md_title = md_lines[0][2:].strip() if md_lines[0].startswith("# ") else md_lines[0]
    txt_title = txt_lines[0]
    if md_title != txt_title:
        failures.append("Markdown and TXT publication titles do not match")

    md_normalized = "\n".join([md_title, *md_lines[1:]])
    txt_normalized = "\n".join(txt_lines)
    if md_normalized != txt_normalized:
        failures.append("Markdown and TXT publication copy differ after heading normalization")

    final_line = txt_lines[-1]
    hashtags = HASHTAG_RE.findall(final_line)
    if len(hashtags) != 5 or " ".join(hashtags) != final_line:
        failures.append("final non-empty line must contain exactly five space-separated hashtags")

    if not failures:
        print(f"OK  publication title  {txt_title}")
        print("OK  publication copy  matching MD/TXT with five final hashtags")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1440)
    parser.add_argument("--count", type=int)
    parser.add_argument("--validate-copy", action="store_true")
    args = parser.parse_args()

    files = sorted(args.directory.glob("*.png"))
    failures: list[str] = []
    if not files:
        failures.append("found no PNG files")
    if args.count is not None and len(files) != args.count:
        failures.append(f"expected {args.count} PNG files, found {len(files)}")

    for path in files:
        try:
            size = png_size(path)
        except ValueError as exc:
            failures.append(f"{path.name}: {exc}")
            continue
        if size != (args.width, args.height):
            failures.append(
                f"{path.name}: expected {args.width}x{args.height}, found {size[0]}x{size[1]}"
            )
        else:
            print(f"OK  {path.name}  {size[0]}x{size[1]}")

    if args.validate_copy:
        failures.extend(validate_copy(args.directory))

    if failures:
        for failure in failures:
            print(f"FAIL  {failure}", file=sys.stderr)
        return 1
    print(f"PASS  {len(files)} files share the required dimensions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
