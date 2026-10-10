#!/usr/bin/env python3
"""Check local download/transcription dependencies without accessing credentials."""
from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import shutil
import sys
from typing import Any, Dict


def _module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _command(name: str) -> str:
    return shutil.which(name) or ""


def diagnose(platform_name: str = "", mode: str = "summarize") -> Dict[str, Any]:
    if platform_name not in {"", "bilibili", "douyin", "twitter"}:
        raise ValueError("Unsupported platform")
    if mode not in {"download", "summarize"}:
        raise ValueError("Unsupported mode")
    commands = {name: _command(name) for name in ("ffmpeg", "ffprobe", "uvx")}
    packages = {name: _module(name) for name in (
        "yt_dlp", "playwright", "mlx_whisper", "faster_whisper",
    )}
    apple_silicon = platform.system() == "Darwin" and platform.machine() == "arm64"
    backend = (
        "mlx-whisper" if packages["mlx_whisper"] and apple_silicon
        else "faster-whisper" if packages["faster_whisper"] else ""
    )
    base_ready = bool(commands["ffmpeg"] and commands["ffprobe"])
    media_ready = {
        "bilibili": bool(base_ready and commands["uvx"]),
        "douyin": bool(base_ready and packages["yt_dlp"]),
        "twitter": bool(base_ready and packages["yt_dlp"]),
    }
    requested_ready = media_ready[platform_name] if platform_name else all(media_ready.values())
    missing = [name for name in ("ffmpeg", "ffprobe") if not commands[name]]
    if platform_name in {"", "bilibili"} and not commands["uvx"]:
        missing.append("uvx (B站)")
    if platform_name in {"", "douyin", "twitter"} and not packages["yt_dlp"]:
        missing.append("Python package yt-dlp")
    if mode == "summarize" and not backend:
        missing.append("mlx-whisper 或 faster-whisper (语音总结)")
    return {
        "ok": bool(requested_ready and (mode == "download" or backend)),
        "mode": mode,
        "requested_platform": platform_name or "all",
        "python": {
            "version": platform.python_version(), "executable": sys.executable,
            "system": platform.system(), "machine": platform.machine(),
        },
        "commands": commands,
        "python_packages": packages,
        "media_ready": media_ready,
        "transcription_backend": backend,
        "optional_douyin_browser_package_available": packages["playwright"],
        "missing": missing,
        "secrets_checked": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check local VideoChai dependencies")
    parser.add_argument("--json", action="store_true", help="emit compact JSON")
    parser.add_argument("--platform", choices=("bilibili", "douyin", "twitter"), default="")
    parser.add_argument("--mode", choices=("download", "summarize"), default="summarize")
    args = parser.parse_args()
    result = diagnose(args.platform, args.mode)
    print(json.dumps(result, ensure_ascii=False, **(
        {"separators": (",", ":")} if args.json else {"indent": 2}
    )))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
