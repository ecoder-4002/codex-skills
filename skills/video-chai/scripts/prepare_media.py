#!/usr/bin/env python3
"""Prepare ephemeral video and audio for one public Bilibili, Douyin, or X URL."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


YUTTO_VERSION = "2.3.0"
MAX_MEDIA_BYTES = 2 * 1024 * 1024 * 1024
BILIBILI_HOSTS = {"bilibili.com", "www.bilibili.com", "m.bilibili.com", "b23.tv"}
DOUYIN_HOSTS = {
    "douyin.com", "www.douyin.com", "v.douyin.com",
    "iesdouyin.com", "www.iesdouyin.com", "v.iesdouyin.com",
}
TWITTER_HOSTS = {
    "x.com", "www.x.com", "m.x.com", "mobile.x.com",
    "twitter.com", "www.twitter.com", "m.twitter.com", "mobile.twitter.com",
}
TWITTER_STATUS_PATH = re.compile(
    r"^/(?:[^/]+/status|i/web/status)/(\d+)(?:/|$)", re.IGNORECASE,
)
MEDIA_SUFFIXES = {".mp4", ".mkv", ".mov", ".webm"}


class MediaPreparationError(RuntimeError):
    def __init__(self, message: str, code: str = "MEDIA_PREPARATION_FAILED") -> None:
        super().__init__(message)
        self.code = code


def normalize_url(value: object) -> Tuple[str, str]:
    raw = str(value or "").strip().rstrip(".,;:!?，。；：！？、)]}）】》」'\"")
    if re.fullmatch(r"BV[0-9A-Za-z]{10}", raw, flags=re.IGNORECASE):
        raw = "https://www.bilibili.com/video/{}".format(raw)
    try:
        parsed = urlparse(raw)
        host = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except ValueError as exc:
        raise MediaPreparationError("视频链接格式无效", "INVALID_VIDEO_URL") from exc
    if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
        raise MediaPreparationError("只接受公开 HTTP(S) 视频链接", "INVALID_VIDEO_URL")
    if port not in {None, 80, 443}:
        raise MediaPreparationError("视频链接不能使用自定义端口", "INVALID_VIDEO_URL")
    if host in BILIBILI_HOSTS:
        query = ""
        part = next((item for key, item in parse_qsl(parsed.query) if key == "p"), "")
        if part.isdigit() and int(part) >= 1:
            query = urlencode({"p": str(int(part))})
        return "bilibili", urlunparse((parsed.scheme, host, parsed.path or "/", "", query, ""))
    if host in DOUYIN_HOSTS:
        return "douyin", urlunparse((parsed.scheme, host, parsed.path or "/", "", "", ""))
    if host in TWITTER_HOSTS:
        match = TWITTER_STATUS_PATH.match(parsed.path or "")
        if not match:
            raise MediaPreparationError(
                "请提供 X/Twitter 推文链接", "INVALID_VIDEO_URL",
            )
        return "twitter", "https://x.com/i/web/status/{}".format(match.group(1))
    raise MediaPreparationError("只支持公开 B站、抖音或 X/Twitter 链接", "UNSUPPORTED_VIDEO_URL")


def _runner(command: Sequence[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(command), **kwargs)


def _safe_environment() -> Dict[str, str]:
    allowed = {
        "HOME", "PATH", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR",
        "SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE",
        "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
        "http_proxy", "https_proxy", "all_proxy", "no_proxy",
        "UV_CACHE_DIR", "XDG_CACHE_HOME",
    }
    return {key: value for key, value in os.environ.items() if key in allowed}


def _last_json_mapping(value: str) -> Mapping[str, Any]:
    for line in reversed(str(value or "").splitlines()):
        try:
            candidate = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            return candidate
    return {}


def _find_media(root: Path) -> Path:
    candidates = [
        path for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in MEDIA_SUFFIXES
        and not path.name.endswith((".part", ".ytdl"))
    ]
    if not candidates:
        raise MediaPreparationError("下载器没有生成可分析的视频", "MEDIA_DOWNLOAD_FAILED")
    selected = max(candidates, key=lambda path: path.stat().st_size)
    try:
        selected.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise MediaPreparationError("下载器返回了任务目录外路径", "UNSAFE_MEDIA_PATH") from exc
    if selected.stat().st_size > MAX_MEDIA_BYTES:
        raise MediaPreparationError("临时视频超过 2GB 上限", "MEDIA_TOO_LARGE")
    return selected.resolve()


def _download_bilibili(url: str, root: Path,
                        runner: Any = _runner) -> Tuple[Path, Mapping[str, Any]]:
    uvx = os.environ.get("VIDEO_CHAI_UVX") or shutil.which("uvx")
    if not uvx:
        raise MediaPreparationError("系统找不到 uvx", "BILIBILI_ADAPTER_UNAVAILABLE")
    output = root / "bilibili"
    temporary = root / "bilibili-tmp"
    output.mkdir(parents=True, exist_ok=True)
    temporary.mkdir(parents=True, exist_ok=True)
    config = root / "anonymous-yutto.toml"
    config.write_text("", encoding="utf-8")
    os.chmod(config, 0o600)
    auth_file = root / "no-yutto-auth.toml"
    auth_file.unlink(missing_ok=True)
    command = [
        str(uvx), "--from", "yutto=={}".format(YUTTO_VERSION), "yutto", "download",
        "--config", str(config), "--auth-file", str(auth_file),
        "--no-color", "--no-progress", "--no-danmaku", "--no-subtitle",
        "--no-cover", "--no-chapter-info", "--video-quality", "64",
        "--audio-quality", "30232", "--vcodec", "avc:copy",
        "--acodec", "mp4a:copy", "--output-format", "mp4",
        "--dir", str(output), "--tmp-dir", str(temporary), url,
    ]
    try:
        completed = runner(
            command, capture_output=True, text=True, timeout=3_600,
            check=False, shell=False, cwd=str(root), env=_safe_environment(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MediaPreparationError("B站下载器无法完成任务", "BILIBILI_DOWNLOAD_FAILED") from exc
    if completed.returncode != 0:
        raise MediaPreparationError(
            "B站匿名下载失败（退出码 {}）".format(completed.returncode),
            "BILIBILI_DOWNLOAD_FAILED",
        )
    return _find_media(output), {}


def _download_douyin(url: str, root: Path,
                      runner: Any = _runner) -> Tuple[Path, Mapping[str, Any]]:
    output = root / "douyin"
    output.mkdir(parents=True, exist_ok=True)
    template = output / "source.%(ext)s"
    command = [
        sys.executable, "-m", "yt_dlp", "--no-config", "--no-playlist",
        "--quiet", "--no-warnings", "--format",
        "bv*[height<=720]+ba/b[height<=720]/b", "--merge-output-format", "mp4",
        "--max-filesize", str(MAX_MEDIA_BYTES), "--socket-timeout", "30",
        "--retries", "2", "--fragment-retries", "2", "--print-json",
        "--output", str(template), url,
    ]
    try:
        completed = runner(
            command, capture_output=True, text=True, timeout=3_600,
            check=False, shell=False, cwd=str(root),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MediaPreparationError("抖音匿名下载无法完成", "DOUYIN_DOWNLOAD_FAILED") from exc
    if completed.returncode == 0:
        return _find_media(output), _last_json_mapping(completed.stdout)
    try:
        from douyin_browser import DouyinBrowserError, PlaywrightMediaProvider
    except ImportError as exc:
        raise MediaPreparationError(
            "抖音匿名下载失败，且隔离浏览器兜底不可用",
            "DOUYIN_DOWNLOAD_FAILED",
        ) from exc
    try:
        provider = PlaywrightMediaProvider(
            channel=os.environ.get("VIDEO_CHAI_BROWSER_CHANNEL", "chrome"),
        )
        metadata = provider(url, output)
        video = Path(str(metadata.get("video_path") or "")).resolve()
        video.relative_to(output.resolve())
        if not video.is_file() or video.stat().st_size > MAX_MEDIA_BYTES:
            raise DouyinBrowserError("隔离浏览器没有生成有效媒体")
        return video, metadata
    except (OSError, ValueError, DouyinBrowserError) as exc:
        raise MediaPreparationError(
            "抖音匿名下载与隔离浏览器兜底均未完成",
            "DOUYIN_DOWNLOAD_FAILED",
        ) from exc


def _download_twitter(url: str, root: Path,
                      runner: Any = _runner) -> Tuple[Path, Mapping[str, Any]]:
    output = root / "twitter"
    output.mkdir(parents=True, exist_ok=True)
    template = output / "source.%(ext)s"
    command = [
        sys.executable, "-m", "yt_dlp", "--no-config", "--no-playlist",
        "--quiet", "--no-warnings", "--format",
        "bv*[height<=720]+ba/b[height<=720]/b", "--merge-output-format", "mp4",
        "--max-filesize", str(MAX_MEDIA_BYTES), "--socket-timeout", "30",
        "--retries", "3", "--fragment-retries", "10", "--print-json",
        "--output", str(template), url,
    ]
    try:
        completed = runner(
            command, capture_output=True, text=True, timeout=3_600,
            check=False, shell=False, cwd=str(root),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MediaPreparationError(
            "X 公开视频下载无法完成", "TWITTER_DOWNLOAD_FAILED",
        ) from exc
    if completed.returncode == 0:
        return _find_media(output), _last_json_mapping(completed.stdout)
    diagnostic = "{} {}".format(completed.stdout, completed.stderr).casefold()
    if any(marker in diagnostic for marker in (
            "login", "cookie", "not authorized", "protected", "403", "401", "sign in")):
        raise MediaPreparationError(
            "X 内容需要登录态或不是公开推文；VideoChai 不读取浏览器 Cookie",
            "TWITTER_AUTH_REQUIRED",
        )
    raise MediaPreparationError(
        "X 公开视频下载失败（退出码 {}）".format(completed.returncode),
        "TWITTER_DOWNLOAD_FAILED",
    )


def _extract_audio(video: Path, root: Path, runner: Any = _runner) -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise MediaPreparationError("系统找不到 ffmpeg", "FFMPEG_UNAVAILABLE")
    audio = root / "source-audio.m4a"
    command = [
        ffmpeg, "-y", "-v", "error", "-i", str(video),
        "-vn", "-c:a", "aac", "-b:a", "96k", str(audio),
    ]
    try:
        completed = runner(
            command, capture_output=True, text=True, timeout=3_600,
            check=False, shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MediaPreparationError("视频音轨提取失败", "AUDIO_EXTRACTION_FAILED") from exc
    if completed.returncode != 0 or not audio.is_file():
        raise MediaPreparationError("视频没有可转录音轨", "AUDIO_EXTRACTION_FAILED")
    return audio.resolve()


def _probe_media(video: Path, runner: Any = _runner) -> Dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise MediaPreparationError("系统找不到 ffprobe", "FFPROBE_UNAVAILABLE")
    try:
        completed = runner([
            ffprobe, "-v", "error", "-show_entries",
            "stream=codec_type,width,height:format=duration", "-of", "json", str(video),
        ], capture_output=True, text=True, timeout=60, check=False, shell=False)
        if completed.returncode != 0:
            raise ValueError("ffprobe failed")
        payload = json.loads(completed.stdout)
        streams = payload.get("streams", [])
        video_stream = next(stream for stream in streams if stream.get("codec_type") == "video")
        return {
            "duration_seconds": round(float(payload.get("format", {}).get("duration") or 0), 3),
            "width": int(video_stream.get("width") or 0),
            "height": int(video_stream.get("height") or 0),
            "has_audio": any(stream.get("codec_type") == "audio" for stream in streams),
        }
    except (OSError, subprocess.TimeoutExpired, ValueError, TypeError,
            AttributeError, StopIteration) as exc:
        raise MediaPreparationError("下载文件没有有效视频轨道", "INVALID_MEDIA") from exc


def prepare(url: str, directory: Path, runner: Any = _runner,
            *, download_only: bool = False) -> Dict[str, Any]:
    platform, normalized = normalize_url(url)
    root = Path(directory).expanduser().resolve()
    if root in {Path("/"), Path.home().resolve()}:
        raise MediaPreparationError("拒绝把宽泛目录用作任务临时目录", "UNSAFE_TASK_DIRECTORY")
    root.mkdir(parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    if platform == "bilibili":
        video, metadata = _download_bilibili(normalized, root, runner)
    elif platform == "douyin":
        video, metadata = _download_douyin(normalized, root, runner)
    else:
        video, metadata = _download_twitter(normalized, root, runner)
    media_info = _probe_media(video, runner)
    audio = _extract_audio(video, root, runner) if media_info["has_audio"] and not download_only else None
    raw_id = str(metadata.get("id") or "").strip()
    if platform == "bilibili":
        match = re.search(r"BV[0-9A-Za-z]+", normalized, flags=re.IGNORECASE)
        raw_id = match.group(0) if match else raw_id
        part = next((value for key, value in parse_qsl(urlparse(normalized).query)
                     if key == "p" and value.isdigit()), "1")
        raw_id = "{}-p{}".format(raw_id, int(part)) if raw_id else ""
    elif not raw_id:
        match = TWITTER_STATUS_PATH.match(urlparse(normalized).path or "") \
            if platform == "twitter" else re.search(r"/(?:video|note)/(\d+)", normalized)
        raw_id = match.group(1) if match else ""
    content_id = re.sub(r"[^A-Za-z0-9_-]+", "-", raw_id).strip("-")
    if not content_id:
        content_id = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:20]
    return {
        "ok": True, "platform": platform, "content_id": content_id,
        "canonical_url": normalized,
        "title": str(metadata.get("title") or video.stem).strip()[:300],
        "author": str(metadata.get("uploader") or metadata.get("creator") or "").strip()[:120],
        "video_path": str(video), "audio_path": str(audio) if audio else "",
        "media": media_info,
        "temporary_directory": str(root),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare temporary VideoChai media")
    parser.add_argument("--url", required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--download-only", action="store_true", help="skip audio extraction")
    args = parser.parse_args()
    try:
        result = prepare(args.url, args.directory, download_only=args.download_only)
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0
    except MediaPreparationError as exc:
        print(json.dumps({
            "ok": False, "error_code": exc.code, "error": str(exc),
        }, ensure_ascii=False, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
