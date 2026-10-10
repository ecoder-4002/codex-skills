#!/usr/bin/env python3
"""Submit one Bilibili, Douyin, or X link to a compatible VideoChai workbench."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from typing import Any, Callable, Dict, Mapping, Optional, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://127.0.0.1:8765"
DEFAULT_INSTRUCTION = "完整拆解这个视频，说明核心内容、关键证据、可复用信息、适用边界和下一步。"
TERMINAL_STATUSES = {"completed", "failed"}
ALLOWED_BILIBILI_HOSTS = {"bilibili.com", "www.bilibili.com", "m.bilibili.com", "b23.tv"}
ALLOWED_DOUYIN_HOSTS = {
    "douyin.com", "www.douyin.com", "v.douyin.com",
    "iesdouyin.com", "www.iesdouyin.com", "v.iesdouyin.com",
}
ALLOWED_TWITTER_HOSTS = {
    "x.com", "www.x.com", "m.x.com", "mobile.x.com",
    "twitter.com", "www.twitter.com", "m.twitter.com", "mobile.twitter.com",
}
TWITTER_STATUS_PATH = re.compile(
    r"^/(?:[^/]+/status|i/web/status)/(\d+)(?:/|$)", re.IGNORECASE,
)
STAGE_LABELS = {
    "queued": "已排队", "resolving": "正在解析链接",
    "downloading": "正在临时获取视频", "transcribing": "正在本机转录",
    "extracting_keyframes": "正在读取代表性关键帧", "analyzing": "正在融合分析",
    "syncing": "正在写入来源资料", "publishing_feishu": "正在发布飞书文档",
    "syncing_feishu_link": "正在登记飞书链接", "waiting_analysis": "等待分析服务重试",
    "waiting_publish": "等待飞书发布重试", "waiting_quota": "等待视觉额度重试",
    "completed": "处理完成", "failed": "处理失败",
}


class VideoChaiError(RuntimeError):
    pass


def _safe_text(value: object, limit: int = 500) -> str:
    text = " ".join(str(value or "").replace("\n", " ").split()).strip()
    return re.sub(r"https?://\S+", lambda match: match.group(0).split("?", 1)[0], text)[:limit]


def validate_video_url(value: object) -> str:
    url = str(value or "").strip()
    if re.fullmatch(r"BV[0-9A-Za-z]{10}", url, flags=re.IGNORECASE):
        url = "https://www.bilibili.com/video/{}".format(url)
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except ValueError as exc:
        raise VideoChaiError("视频链接格式无效") from exc
    if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
        raise VideoChaiError("只接受公开的 HTTP(S) 视频链接")
    if port not in {None, 80, 443}:
        raise VideoChaiError("视频链接不能使用自定义端口")
    if host not in ALLOWED_BILIBILI_HOSTS | ALLOWED_DOUYIN_HOSTS | ALLOWED_TWITTER_HOSTS:
        raise VideoChaiError("只支持 B站、抖音或 X/Twitter 公开视频链接")
    if host in ALLOWED_BILIBILI_HOSTS - {"b23.tv"} and not parsed.path.startswith("/video/"):
        raise VideoChaiError("请提供 B站视频页链接")
    if host in ALLOWED_TWITTER_HOSTS and not TWITTER_STATUS_PATH.match(parsed.path or ""):
        raise VideoChaiError("请提供 X/Twitter 推文链接")
    return url


def normalize_payload(payload: Mapping[str, Any]) -> Dict[str, str]:
    instruction = str(payload.get("instruction") or "").strip() or DEFAULT_INSTRUCTION
    if len(instruction) > 8_000:
        raise VideoChaiError("处理要求不能超过 8000 个字符")
    return {"url": validate_video_url(payload.get("url")), "instruction": instruction}


class WorkbenchClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise VideoChaiError("工作台地址无效")
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str,
                payload: Optional[Mapping[str, Any]] = None,
                timeout: float = 15) -> Dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = Request(self.base_url + path, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=timeout) as response:
                decoded = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            try:
                detail = json.loads(exc.read().decode("utf-8")).get("error") or exc.reason
            except Exception:
                detail = exc.reason
            raise VideoChaiError("工作台请求失败（HTTP {}）：{}".format(
                exc.code, _safe_text(detail),
            )) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise VideoChaiError("无法连接兼容工作台：{}".format(_safe_text(exc))) from exc
        except json.JSONDecodeError as exc:
            raise VideoChaiError("工作台返回了无效 JSON") from exc
        if not isinstance(decoded, dict):
            raise VideoChaiError("工作台返回格式无效")
        return decoded


def _find_item(client: WorkbenchClient, item_id: str) -> Dict[str, Any]:
    if not item_id:
        return {}
    items = client.request("GET", "/api/items").get("items")
    if not isinstance(items, list):
        return {}
    return next((dict(item) for item in items
                 if isinstance(item, dict) and str(item.get("id") or "") == item_id), {})


def _result(job: Mapping[str, Any], item: Mapping[str, Any], *, ok: bool,
            pending: bool = False) -> Dict[str, Any]:
    feishu = item.get("feishu_document") if isinstance(item.get("feishu_document"), dict) else {}
    return {
        "ok": ok, "pending": pending,
        "job_id": str(job.get("id") or ""),
        "status": str(job.get("status") or ""),
        "stage": str(job.get("stage") or ""),
        "stage_label": STAGE_LABELS.get(str(job.get("stage") or ""), str(job.get("stage") or "")),
        "item_id": str(job.get("item_id") or item.get("id") or ""),
        "title": str(item.get("title") or ""),
        "source_url": str(job.get("source_url") or item.get("source_url") or ""),
        "instruction": str(job.get("user_instruction") or item.get("user_instruction") or ""),
        "retry_at": str(job.get("retry_at") or ""),
        "error_code": str(job.get("error_code") or ""),
        "error": _safe_text(job.get("error")),
        "feishu_document": {
            "title": str(feishu.get("title") or ""),
            "url": str(feishu.get("url") or job.get("feishu_doc_url") or ""),
        },
    }


def run_pipeline(payload: Mapping[str, Any], *, base_url: str = DEFAULT_BASE_URL,
                 timeout_seconds: int = 3_600, poll_seconds: float = 2,
                 client_factory: Callable[[str], WorkbenchClient] = WorkbenchClient) -> Dict[str, Any]:
    normalized = normalize_payload(payload)
    client = client_factory(base_url)
    ready = client.request("GET", "/api/short-video-jobs", timeout=2)
    if not isinstance(ready.get("jobs"), list):
        raise VideoChaiError("目标不是兼容的 VideoChai 工作台")
    response = client.request("POST", "/api/short-videos/intake", normalized)
    job = response.get("job") if isinstance(response.get("job"), dict) else {}
    job_id = str(job.get("id") or "")
    if not job_id:
        raise VideoChaiError("工作台没有返回任务 ID")
    print("[video-chai] 已提交任务 {}。".format(job_id), file=sys.stderr, flush=True)
    deadline = time.monotonic() + max(1, timeout_seconds)
    last_stage = ""
    last_report = 0.0
    while True:
        response = client.request("GET", "/api/short-video-jobs/{}".format(job_id))
        current = response.get("job") if isinstance(response.get("job"), dict) else {}
        if not current:
            raise VideoChaiError("工作台找不到已提交任务")
        job = current
        status = str(job.get("status") or "")
        stage = str(job.get("stage") or status)
        now = time.monotonic()
        if stage != last_stage or now - last_report >= 30:
            print("[video-chai] {}（{}）".format(
                STAGE_LABELS.get(stage, stage or "处理中"), job_id,
            ), file=sys.stderr, flush=True)
            last_stage, last_report = stage, now
        if status in TERMINAL_STATUSES:
            return _result(job, _find_item(client, str(job.get("item_id") or "")), ok=status == "completed")
        if status == "waiting_retry":
            return _result(job, _find_item(client, str(job.get("item_id") or "")), ok=False, pending=True)
        if now >= deadline:
            timed_out = dict(job)
            timed_out.update({
                "status": "timed_out", "error_code": "VIDEO_CHAI_TIMEOUT",
                "error": "前台等待超时；后台任务仍会继续运行",
            })
            return _result(timed_out, _find_item(client, str(job.get("item_id") or "")), ok=False, pending=True)
        time.sleep(max(0.2, poll_seconds))


def _read_payload(args: argparse.Namespace) -> Dict[str, Any]:
    if args.stdin:
        try:
            payload = json.loads(sys.stdin.readline())
        except json.JSONDecodeError as exc:
            raise VideoChaiError("标准输入不是有效 JSON") from exc
        if not isinstance(payload, dict):
            raise VideoChaiError("标准输入 JSON 必须是对象")
        return payload
    return {"url": args.url, "instruction": args.instruction}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Submit video to a compatible VideoChai workbench")
    parser.add_argument("url", nargs="?")
    parser.add_argument("--instruction", default="")
    parser.add_argument("--stdin", action="store_true")
    parser.add_argument("--timeout", type=int, default=3_600)
    parser.add_argument("--base-url", default=os.environ.get("VIDEO_CHAI_WORKBENCH_URL", DEFAULT_BASE_URL))
    args = parser.parse_args(argv)
    try:
        result = run_pipeline(_read_payload(args), base_url=args.base_url, timeout_seconds=args.timeout)
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0 if result.get("ok") else 3 if result.get("pending") else 1
    except VideoChaiError as exc:
        print(json.dumps({
            "ok": False, "pending": False,
            "error_code": "VIDEO_CHAI_ERROR", "error": _safe_text(exc),
        }, ensure_ascii=False, separators=(",", ":")))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
