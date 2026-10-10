#!/usr/bin/env python3
"""Report VideoChai readiness without reading or printing credentials."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import sys
from typing import Any, Dict
from urllib.error import URLError
from urllib.request import Request, urlopen


DEFAULT_WORKBENCH_URL = "http://127.0.0.1:8765"


def _module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _command(name: str) -> str:
    return shutil.which(name) or ""


def _workbench(url: str) -> Dict[str, Any]:
    endpoint = url.rstrip("/") + "/api/short-video-jobs"
    try:
        request = Request(endpoint, headers={"Accept": "application/json"})
        with urlopen(request, timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
        ready = isinstance(payload, dict) and isinstance(payload.get("jobs"), list)
    except (OSError, URLError, TimeoutError, json.JSONDecodeError):
        ready = False
    return {"ready": ready, "url": url}


def diagnose(workbench_url: str = DEFAULT_WORKBENCH_URL,
             platform_name: str = "") -> Dict[str, Any]:
    ffmpeg = _command("ffmpeg")
    ffprobe = _command("ffprobe")
    uvx = _command("uvx")
    yt_dlp = _module("yt_dlp")
    playwright = _module("playwright")
    mlx_whisper = _module("mlx_whisper")
    faster_whisper = _module("faster_whisper")
    apple_silicon = platform.system() == "Darwin" and platform.machine() == "arm64"
    lark_cli = _command("lark-cli")
    transcription_backend = (
        "mlx-whisper" if mlx_whisper and apple_silicon
        else "faster-whisper" if faster_whisper else ""
    )
    standalone = {
        "bilibili_ready": bool(ffmpeg and ffprobe and uvx),
        "douyin_ready": bool(ffmpeg and ffprobe and yt_dlp and playwright),
        "twitter_ready": bool(ffmpeg and ffprobe and yt_dlp),
        "douyin_anonymous_primary_ready": bool(yt_dlp),
        "douyin_isolated_browser_ready": bool(playwright),
        "transcription_ready": bool(transcription_backend),
        "transcription_backend": transcription_backend,
        "feishu_cli_available": bool(lark_cli),
        "agent_feishu_connector_required_if_no_cli": not bool(lark_cli),
    }
    missing = []
    if not ffmpeg:
        missing.append("ffmpeg")
    if not ffprobe:
        missing.append("ffprobe")
    if platform_name in {"", "bilibili"} and not uvx:
        missing.append("uvx (B站)")
    if platform_name in {"", "douyin"} and not yt_dlp:
        missing.append("Python package yt-dlp (抖音)")
    if platform_name in {"", "douyin"} and not playwright:
        missing.append("Python package playwright + Chrome/Chromium (抖音兜底)")
    if platform_name in {"", "twitter"} and not yt_dlp:
        missing.append("Python package yt-dlp (X/Twitter)")
    if not transcription_backend:
        missing.append("mlx-whisper 或 faster-whisper")
    workbench = _workbench(workbench_url)
    requested_media_ready = (
        standalone["bilibili_ready"] if platform_name == "bilibili"
        else standalone["douyin_ready"] if platform_name == "douyin"
        else standalone["twitter_ready"] if platform_name == "twitter"
        else standalone["bilibili_ready"] and standalone["douyin_ready"]
             and standalone["twitter_ready"]
    )
    standalone["requested_platform"] = platform_name or "all"
    standalone["requested_media_ready"] = bool(requested_media_ready)
    return {
        "ok": bool(workbench["ready"] or (
            requested_media_ready
            and standalone["transcription_ready"]
        )),
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
            "system": platform.system(),
            "machine": platform.machine(),
        },
        "workbench": workbench,
        "commands": {
            "ffmpeg": ffmpeg, "ffprobe": ffprobe,
            "uvx": uvx, "lark_cli": lark_cli,
        },
        "python_packages": {
            "yt_dlp": yt_dlp,
            "playwright": playwright,
            "mlx_whisper": mlx_whisper,
            "faster_whisper": faster_whisper,
        },
        "standalone": standalone,
        "missing": missing,
        "secrets_checked": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check VideoChai deployment readiness")
    parser.add_argument("--json", action="store_true", help="emit compact JSON")
    parser.add_argument(
        "--workbench-url",
        default=os.environ.get("VIDEO_CHAI_WORKBENCH_URL", DEFAULT_WORKBENCH_URL),
    )
    parser.add_argument("--platform", choices=("bilibili", "douyin", "twitter"), default="")
    args = parser.parse_args()
    result = diagnose(args.workbench_url, args.platform)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
