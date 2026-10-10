#!/usr/bin/env python3
"""Extract evenly distributed, ephemeral frames from one local video."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Callable, Dict, List, Optional, Sequence


class FrameExtractionError(RuntimeError):
    pass


def _runner(command: Sequence[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(command), **kwargs)


def _duration(video: Path, ffprobe: str, runner: Callable[..., Any]) -> float:
    try:
        completed = runner([
            ffprobe, "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(video),
        ], capture_output=True, text=True, timeout=60, check=False, shell=False)
        if int(getattr(completed, "returncode", 1)) == 0:
            return max(0.0, float(str(getattr(completed, "stdout", "") or "0").strip()))
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    return 0.0


def extract_frames(video_path: Path, output_directory: Path, *, max_frames: int = 12,
                   ffmpeg: str = "", ffprobe: str = "",
                   runner: Callable[..., Any] = _runner) -> Dict[str, Any]:
    video = Path(video_path).expanduser().resolve()
    if not video.is_file():
        raise FrameExtractionError("本地视频不存在")
    directory = Path(output_directory).expanduser().resolve()
    if directory in {Path("/"), Path.home().resolve()}:
        raise FrameExtractionError("拒绝把宽泛目录用作关键帧目录")
    directory.mkdir(parents=True, exist_ok=True)
    os.chmod(directory, 0o700)
    ffmpeg_bin = ffmpeg or shutil.which("ffmpeg") or ""
    ffprobe_bin = ffprobe or shutil.which("ffprobe") or ""
    if not ffmpeg_bin or not ffprobe_bin:
        raise FrameExtractionError("系统找不到 ffmpeg/ffprobe")
    duration = _duration(video, ffprobe_bin, runner)
    count = max(3, min(int(max_frames), 16))
    if duration > 0:
        count = min(count, max(3, int(duration // 20) + 1))
        points = [duration * (index + 0.5) / count for index in range(count)]
    else:
        points = [float(index * 10) for index in range(count)]
    frames: List[Dict[str, Any]] = []
    for index, second in enumerate(points, start=1):
        target = directory / "frame-{:02d}-{:08.2f}s.jpg".format(index, second)
        command = [
            ffmpeg_bin, "-y", "-v", "error", "-ss", "{:.3f}".format(second),
            "-i", str(video), "-frames:v", "1", "-vf",
            "scale='min(1280,iw)':-2", "-q:v", "3", str(target),
        ]
        try:
            completed = runner(
                command, capture_output=True, text=True, timeout=90,
                check=False, shell=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise FrameExtractionError("ffmpeg 抽帧失败") from exc
        if int(getattr(completed, "returncode", 1)) == 0 and target.is_file() and target.stat().st_size:
            os.chmod(target, 0o600)
            frames.append({
                "path": str(target.resolve()),
                "timestamp_seconds": round(second, 2),
            })
    if not frames:
        raise FrameExtractionError("视频没有生成可读取的关键帧")
    manifest = {
        "ok": True,
        "duration_seconds": round(duration, 3),
        "frame_count": len(frames),
        "frames": frames,
    }
    manifest_path = directory / "frames.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.chmod(manifest_path, 0o600)
    manifest["manifest_path"] = str(manifest_path.resolve())
    return manifest


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Extract temporary representative frames")
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--max-frames", type=int, default=12)
    args = parser.parse_args(argv)
    try:
        result = extract_frames(
            args.video, args.output_directory, max_frames=args.max_frames,
        )
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0
    except (OSError, FrameExtractionError) as exc:
        print(json.dumps({
            "ok": False, "error_code": "FRAME_EXTRACTION_FAILED", "error": str(exc),
        }, ensure_ascii=False, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
