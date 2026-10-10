#!/usr/bin/env python3
"""Transcribe one local audio file without sending it to a remote API."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


DEFAULT_MLX_MODEL = "mlx-community/whisper-large-v3-turbo"
DEFAULT_FASTER_MODEL = "large-v3-turbo"
MAX_AUDIO_BYTES = 1_500_000_000


class TranscriptionError(RuntimeError):
    pass


def available_backend() -> str:
    """Choose the local backend most appropriate for the current machine."""
    apple_silicon = platform.system() == "Darwin" and platform.machine() == "arm64"
    if apple_silicon and importlib.util.find_spec("mlx_whisper") is not None:
        return "mlx-whisper"
    if importlib.util.find_spec("faster_whisper") is not None:
        return "faster-whisper"
    return ""


def _clean_segments(values: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    segments: List[Dict[str, Any]] = []
    for value in values:
        text = str(value.get("text") or "").strip()
        if not text:
            continue
        try:
            start = round(float(value.get("start") or 0), 3)
            end = round(float(value.get("end") or start), 3)
        except (TypeError, ValueError):
            start, end = 0.0, 0.0
        segments.append({"start": start, "end": end, "text": text})
    return segments


def _normalize_result(result: Mapping[str, Any], backend: str,
                      language: str) -> Dict[str, Any]:
    segments = _clean_segments(
        value for value in (result.get("segments") or []) if isinstance(value, Mapping)
    )
    text = str(result.get("text") or "").strip()
    if not text and segments:
        text = "".join(value["text"] for value in segments).strip()
    if not text:
        raise TranscriptionError("转录完成但没有生成文字")
    return {
        "ok": True,
        "backend": backend,
        "language": str(result.get("language") or language),
        "text": text,
        "segments": segments,
    }


def _transcribe_mlx(audio: Path, model: str, language: str) -> Dict[str, Any]:
    if not (platform.system() == "Darwin" and platform.machine() == "arm64"):
        raise TranscriptionError("mlx-whisper 只支持 Apple Silicon Mac")
    try:
        module = importlib.import_module("mlx_whisper")
    except ImportError as exc:
        raise TranscriptionError("未安装 mlx-whisper") from exc
    raw = module.transcribe(str(audio), path_or_hf_repo=model, language=language)
    if not isinstance(raw, Mapping):
        raise TranscriptionError("mlx-whisper 返回了无法识别的结果")
    return _normalize_result(raw, "mlx-whisper", language)


def _transcribe_faster(audio: Path, model: str, language: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module("faster_whisper")
    except ImportError as exc:
        raise TranscriptionError("未安装 faster-whisper") from exc
    whisper_model = module.WhisperModel(model, device="auto", compute_type="auto")
    raw_segments, info = whisper_model.transcribe(
        str(audio), language=language, vad_filter=True,
    )
    segments = [
        {
            "start": getattr(segment, "start", 0),
            "end": getattr(segment, "end", 0),
            "text": getattr(segment, "text", ""),
        }
        for segment in raw_segments
    ]
    return _normalize_result({
        "text": "".join(str(value.get("text") or "") for value in segments),
        "segments": segments,
        "language": getattr(info, "language", language),
    }, "faster-whisper", language)


def transcribe(audio_path: Path, *, backend: str = "auto", model: str = "",
               language: str = "zh") -> Dict[str, Any]:
    audio = Path(audio_path).expanduser().resolve()
    if not audio.is_file():
        raise TranscriptionError("本地音频不存在")
    if audio.stat().st_size > MAX_AUDIO_BYTES:
        raise TranscriptionError("音频超过 1.5GB 本机转录上限")
    selected = available_backend() if backend == "auto" else backend
    if selected == "mlx-whisper":
        return _transcribe_mlx(audio, model or DEFAULT_MLX_MODEL, language)
    if selected == "faster-whisper":
        return _transcribe_faster(audio, model or DEFAULT_FASTER_MODEL, language)
    raise TranscriptionError("没有可用的本机转录后端")


def _write_result(path: Path, result: Mapping[str, Any]) -> None:
    output = Path(path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(dict(result), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.chmod(temporary, 0o600)
    temporary.replace(output)
    os.chmod(output, 0o600)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Transcribe temporary audio locally")
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--backend", choices=("auto", "mlx-whisper", "faster-whisper"),
        default="auto",
    )
    parser.add_argument("--model", default="")
    parser.add_argument("--language", default="zh")
    args = parser.parse_args(argv)
    try:
        print("[video-chai] 正在本机转录。", file=sys.stderr, flush=True)
        result = transcribe(
            args.audio, backend=args.backend, model=args.model,
            language=args.language,
        )
        _write_result(args.output, result)
        print(json.dumps({
            "ok": True,
            "backend": result["backend"],
            "language": result["language"],
            "output_path": str(args.output.expanduser().resolve()),
            "segment_count": len(result["segments"]),
        }, ensure_ascii=False, separators=(",", ":")))
        return 0
    except (OSError, TranscriptionError) as exc:
        print(json.dumps({
            "ok": False, "error_code": "TRANSCRIPTION_FAILED", "error": str(exc),
        }, ensure_ascii=False, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
