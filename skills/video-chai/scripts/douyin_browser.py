#!/usr/bin/env python3
"""Isolated public-page fallback for Douyin media preparation.

The browser uses a brand-new task-scoped profile. It never reads an existing
browser profile or exports cookies, and only downloads allowlisted public CDN
responses that resolve to public IP addresses.
"""

from __future__ import annotations

import ipaddress
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


DOUYIN_HOSTS = {
    "douyin.com", "www.douyin.com", "v.douyin.com",
    "iesdouyin.com", "www.iesdouyin.com", "v.iesdouyin.com",
}
MEDIA_HOST_SUFFIXES = (
    "douyinvod.com", "bytecdntp.com", "bytecdn.cn", "douyincdn.com",
)
MAX_MEDIA_BYTES = 500 * 1024 * 1024
MAX_BROWSER_CANDIDATES = 8
CANDIDATE_SETTLE_SECONDS = 1.5
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
)


class DouyinBrowserError(RuntimeError):
    pass


def _resolver(host: str, port: int) -> Sequence[Any]:
    return socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)


def _public_host(host: str, port: int,
                 resolver: Callable[[str, int], Sequence[Any]]) -> None:
    try:
        addresses = resolver(host, port)
    except (OSError, socket.gaierror) as exc:
        raise DouyinBrowserError("无法解析公开媒体主机") from exc
    seen = set()
    for entry in addresses:
        address = entry[4][0] if isinstance(entry, tuple) and len(entry) > 4 else str(entry)
        address = address.split("%", 1)[0]
        if address in seen:
            continue
        seen.add(address)
        try:
            is_global = ipaddress.ip_address(address).is_global
        except ValueError as exc:
            raise DouyinBrowserError("公开媒体主机返回无效地址") from exc
        if not is_global:
            raise DouyinBrowserError("拒绝下载回环、内网或链路本地媒体")
    if not seen:
        raise DouyinBrowserError("公开媒体主机没有可用公网地址")


def validate_public_douyin_url(value: object,
                               resolver: Callable[[str, int], Sequence[Any]] = _resolver) -> str:
    raw = str(value or "").strip()
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower().rstrip(".")
    try:
        port = parsed.port
    except ValueError as exc:
        raise DouyinBrowserError("抖音链接端口无效") from exc
    if (parsed.scheme not in {"http", "https"} or host not in DOUYIN_HOSTS
            or parsed.username or parsed.password or port not in {None, 80, 443}):
        raise DouyinBrowserError("只接受不含账号信息的公开抖音链接")
    _public_host(host, port or (443 if parsed.scheme == "https" else 80), resolver)
    return raw


def _allowed_media_host(host: str) -> bool:
    normalized = str(host or "").lower().rstrip(".")
    return any(
        normalized == suffix or normalized.endswith("." + suffix)
        for suffix in MEDIA_HOST_SUFFIXES
    )


def validate_public_media_url(value: object,
                              resolver: Callable[[str, int], Sequence[Any]] = _resolver) -> str:
    raw = str(value or "").strip()
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower().rstrip(".")
    try:
        port = parsed.port
    except ValueError as exc:
        raise DouyinBrowserError("抖音媒体地址端口无效") from exc
    if (parsed.scheme != "https" or not _allowed_media_host(host)
            or parsed.username or parsed.password or port not in {None, 443}):
        raise DouyinBrowserError("拒绝访问非抖音公开媒体域名")
    _public_host(host, port or 443, resolver)
    return raw


class _ValidatedMediaRedirect(HTTPRedirectHandler):
    def __init__(self, resolver: Callable[[str, int], Sequence[Any]]) -> None:
        super().__init__()
        self.resolver = resolver

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str,
                         headers: Any, newurl: str) -> Any:
        safe = validate_public_media_url(urljoin(req.full_url, newurl), self.resolver)
        return super().redirect_request(req, fp, code, msg, headers, safe)


def download_public_media(url: str, destination: Path,
                          resolver: Callable[[str, int], Sequence[Any]] = _resolver) -> Path:
    safe_url = validate_public_media_url(url, resolver)
    target = Path(destination)
    opener = build_opener(_ValidatedMediaRedirect(resolver))
    request = Request(safe_url, headers={
        "User-Agent": BROWSER_USER_AGENT,
        "Referer": "https://www.douyin.com/",
        "Accept": "video/*,audio/*,*/*;q=0.5",
    })
    written = 0
    try:
        with opener.open(request, timeout=60) as response:
            content_type = str(response.headers.get("Content-Type") or "").lower()
            length = response.headers.get("Content-Length")
            if length and int(length) > MAX_MEDIA_BYTES:
                raise DouyinBrowserError("抖音临时媒体超过大小上限")
            if not any(value in content_type for value in (
                    "video/", "audio/", "octet-stream")):
                raise DouyinBrowserError("抖音媒体地址未返回音视频")
            with target.open("wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > MAX_MEDIA_BYTES:
                        raise DouyinBrowserError("抖音临时媒体超过大小上限")
                    output.write(chunk)
    except DouyinBrowserError:
        target.unlink(missing_ok=True)
        raise
    except (HTTPError, URLError, OSError, ValueError) as exc:
        target.unlink(missing_ok=True)
        raise DouyinBrowserError("无法下载抖音临时播放流") from exc
    if written <= 0:
        target.unlink(missing_ok=True)
        raise DouyinBrowserError("抖音临时播放流为空")
    return target


def _runner(command: Sequence[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(command), **kwargs)


def probe_media_streams(path: Path, *, runner: Callable[..., Any] = _runner,
                        ffprobe: str = "") -> frozenset[str]:
    executable = ffprobe or shutil.which("ffprobe") or ""
    if not executable:
        raise DouyinBrowserError("系统找不到 ffprobe")
    try:
        completed = runner([
            executable, "-v", "error", "-show_entries", "stream=codec_type",
            "-of", "json", str(path),
        ], capture_output=True, text=True, timeout=60, check=False, shell=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DouyinBrowserError("无法探测抖音临时媒体轨道") from exc
    if int(getattr(completed, "returncode", 1)) != 0:
        raise DouyinBrowserError("抖音临时播放流不是有效媒体")
    try:
        payload = json.loads(str(getattr(completed, "stdout", "") or "{}"))
    except json.JSONDecodeError as exc:
        raise DouyinBrowserError("无法识别抖音临时媒体轨道") from exc
    streams = payload.get("streams") if isinstance(payload, dict) else []
    return frozenset({
        str(stream.get("codec_type") or "").strip().lower()
        for stream in streams if isinstance(stream, dict)
    }.intersection({"audio", "video"}))


def merge_media(video: Path, audio: Path, destination: Path, *,
                runner: Callable[..., Any] = _runner, ffmpeg: str = "") -> Path:
    executable = ffmpeg or shutil.which("ffmpeg") or ""
    if not executable:
        raise DouyinBrowserError("系统找不到 ffmpeg")
    target = Path(destination)
    try:
        completed = runner([
            executable, "-y", "-v", "error", "-i", str(video), "-i", str(audio),
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(target),
        ], capture_output=True, text=True, timeout=300, check=False, shell=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        target.unlink(missing_ok=True)
        raise DouyinBrowserError("抖音临时音画合并失败") from exc
    if int(getattr(completed, "returncode", 1)) != 0 or not target.is_file():
        target.unlink(missing_ok=True)
        raise DouyinBrowserError("抖音临时音画合并失败")
    return target


class PlaywrightMediaProvider:
    """Capture a public Douyin video in a new, task-scoped browser profile."""

    def __init__(self, *, downloader: Callable[[str, Path], Path] = download_public_media,
                 channel: str = "chrome", wait_seconds: int = 12,
                 stream_probe: Callable[[Path], Sequence[str]] = probe_media_streams,
                 media_merger: Callable[[Path, Path, Path], Path] = merge_media) -> None:
        self.downloader = downloader
        self.channel = channel
        self.wait_seconds = max(3, min(int(wait_seconds), 30))
        self.stream_probe = stream_probe
        self.media_merger = media_merger

    @staticmethod
    def _remove(paths: Sequence[Path], keep: Optional[Path] = None) -> None:
        for path in paths:
            if keep is not None and path == keep:
                continue
            path.unlink(missing_ok=True)

    def materialize_candidates(self, candidates: Sequence[Mapping[str, Any]],
                               directory: Path) -> Path:
        unique: Dict[str, int] = {}
        for candidate in candidates:
            url = str(candidate.get("url") or "")
            if url:
                unique[url] = max(unique.get(url, 0), int(candidate.get("length") or 0))
        if not unique:
            raise DouyinBrowserError("抖音页面未返回公开播放流")
        downloaded: List[Path] = []
        video_path: Optional[Path] = None
        audio_path: Optional[Path] = None
        failures = 0
        for index, (url, _length) in enumerate(
                sorted(unique.items(), key=lambda value: value[1], reverse=True)
                [:MAX_BROWSER_CANDIDATES], start=1):
            destination = directory / "browser-capture-{}.mp4".format(index)
            try:
                self.downloader(url, destination)
                kinds = frozenset(str(value).lower() for value in self.stream_probe(destination))
            except DouyinBrowserError:
                failures += 1
                self._remove([destination])
                continue
            downloaded.append(destination)
            if {"audio", "video"}.issubset(kinds):
                self._remove(downloaded, keep=destination)
                return destination
            if "video" in kinds and video_path is None:
                video_path = destination
            elif "audio" in kinds and audio_path is None:
                audio_path = destination
            else:
                self._remove([destination])
                downloaded.remove(destination)
            if video_path is not None and audio_path is not None:
                merged = directory / "browser-capture-merged.mp4"
                self.media_merger(video_path, audio_path, merged)
                if not {"audio", "video"}.issubset(
                        str(value).lower() for value in self.stream_probe(merged)):
                    self._remove(downloaded + [merged])
                    raise DouyinBrowserError("抖音临时音画合并结果无效")
                self._remove(downloaded)
                return merged
        self._remove(downloaded)
        if video_path is not None:
            raise DouyinBrowserError("抖音公开播放流缺少可转录音轨")
        if audio_path is not None:
            raise DouyinBrowserError("抖音公开播放流缺少可分析画面")
        raise DouyinBrowserError(
            "抖音免登录播放流下载失败（{}个候选）".format(failures)
        )

    def _launch(self, playwright: Any, profile: Path) -> Any:
        options = {
            "user_data_dir": str(profile), "headless": True,
            "user_agent": BROWSER_USER_AGENT, "locale": "zh-CN",
            "viewport": {"width": 1280, "height": 800}, "accept_downloads": False,
        }
        if self.channel:
            try:
                return playwright.chromium.launch_persistent_context(
                    channel=self.channel, **options,
                )
            except Exception:
                pass
        return playwright.chromium.launch_persistent_context(**options)

    def __call__(self, url: str, work_directory: Path) -> Dict[str, Any]:
        canonical = validate_public_douyin_url(url)
        directory = Path(work_directory).resolve()
        profile = directory / "anonymous-browser-profile"
        profile.mkdir(parents=True, exist_ok=True)
        os.chmod(profile, 0o700)
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise DouyinBrowserError("未安装 playwright 抖音免登录兜底") from exc
        candidates: List[Dict[str, Any]] = []
        observed = set()
        first_candidate_at = 0.0
        last_candidate_at = 0.0
        title = ""
        context: Any = None
        try:
            with sync_playwright() as playwright:
                context = self._launch(playwright, profile)
                page = context.pages[0] if context.pages else context.new_page()

                def observe(response: Any) -> None:
                    nonlocal first_candidate_at, last_candidate_at
                    try:
                        response_url = str(response.url or "")
                        parsed = urlparse(response_url)
                        content_type = str(response.headers.get("content-type") or "").lower()
                        if (not _allowed_media_host(parsed.hostname or "")
                                or not any(value in content_type for value in (
                                    "video", "audio", "octet-stream",
                                )) or int(response.status) not in {200, 206}
                                or response_url in observed):
                            return
                        try:
                            length = int(response.headers.get("content-length") or 0)
                        except (TypeError, ValueError):
                            length = 0
                        observed.add(response_url)
                        candidates.append({"url": response_url, "length": length})
                        last_candidate_at = time.monotonic()
                        if first_candidate_at <= 0:
                            first_candidate_at = last_candidate_at
                    except Exception:
                        return

                page.on("response", observe)
                try:
                    page.goto(canonical, wait_until="domcontentloaded", timeout=30_000)
                except Exception:
                    pass
                try:
                    video = page.query_selector("video")
                    if video:
                        video.evaluate("""
                            (node) => {
                                node.volume = 0.01;
                                node.muted = false;
                                node.play().catch(() => {
                                    node.muted = true;
                                    node.play().then(() => {
                                        setTimeout(() => { node.muted = false; }, 250);
                                    }).catch(() => {});
                                });
                            }
                        """)
                except Exception:
                    pass
                deadline = time.monotonic() + self.wait_seconds
                while time.monotonic() < deadline:
                    page.wait_for_timeout(250)
                    now = time.monotonic()
                    if (first_candidate_at > 0
                            and now - first_candidate_at >= CANDIDATE_SETTLE_SECONDS
                            and now - last_candidate_at >= CANDIDATE_SETTLE_SECONDS):
                        break
                try:
                    title = str(page.title() or "").strip()[:300]
                except Exception:
                    pass
        except DouyinBrowserError:
            raise
        except Exception as exc:
            raise DouyinBrowserError("无法建立抖音免登录临时浏览器") from exc
        finally:
            if context is not None:
                try:
                    context.close()
                except Exception:
                    pass
            shutil.rmtree(profile, ignore_errors=True)
        video_path = self.materialize_candidates(candidates, directory)
        return {"video_path": str(video_path.resolve()), "title": title}
