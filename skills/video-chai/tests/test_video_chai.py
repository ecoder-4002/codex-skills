import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location("video_chai_" + name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


doctor = load_script("doctor")
douyin_browser = load_script("douyin_browser")
frames = load_script("extract_frames")
media = load_script("prepare_media")
transcription = load_script("transcribe")


class VideoChaiTests(unittest.TestCase):
    def test_accepts_public_bilibili_douyin_and_x_urls(self):
        platform_name, url = media.normalize_url(
            "https://www.bilibili.com/video/BV1xx411c7mD?p=2&utm_source=x"
        )
        self.assertEqual(platform_name, "bilibili")
        self.assertEqual(url, "https://www.bilibili.com/video/BV1xx411c7mD?p=2")
        self.assertEqual(
            media.normalize_url("https://v.douyin.com/abc123/?foo=bar"),
            ("douyin", "https://v.douyin.com/abc123/"),
        )
        self.assertEqual(
            media.normalize_url(
                "https://x.com/alextalksai/status/2093583622691283018?s=46"
            ),
            ("twitter", "https://x.com/i/web/status/2093583622691283018"),
        )

    def test_rejects_credentials_custom_ports_and_other_hosts(self):
        for url in (
            "https://user:pass@www.bilibili.com/video/BV1xx411c7mD",
            "https://www.bilibili.com:8443/video/BV1xx411c7mD",
            "https://example.com/video/BV1xx411c7mD",
        ):
            with self.assertRaises(media.MediaPreparationError):
                media.normalize_url(url)

    def test_bilibili_adapter_is_pinned_and_anonymous(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calls = []

            def runner(command, **kwargs):
                calls.append((list(command), kwargs))
                output = root / "bilibili" / "sample.mp4"
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(b"video")
                return types.SimpleNamespace(returncode=0, stdout="", stderr="")

            with mock.patch.dict(media.os.environ, {"VIDEO_CHAI_UVX": "/tmp/uvx"}):
                video, _metadata = media._download_bilibili(
                    "https://www.bilibili.com/video/BV1xx411c7mD", root, runner
                )
            command, kwargs = calls[0]
            self.assertEqual(video.name, "sample.mp4")
            self.assertIn("yutto==2.3.0", command)
            self.assertIn("--auth-file", command)
            self.assertFalse(kwargs["shell"])
            self.assertNotIn("BILI_SESSDATA", kwargs["env"])

    def test_twitter_adapter_is_anonymous_and_uses_resilient_fragment_retries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calls = []

            def runner(command, **kwargs):
                calls.append((list(command), kwargs))
                template = command[command.index("--output") + 1]
                Path(template.replace("%(ext)s", "mp4")).write_bytes(b"video")
                return types.SimpleNamespace(
                    returncode=0,
                    stdout=json.dumps({"id": "asset", "title": "X 公开视频"}),
                    stderr="",
                )

            video, metadata = media._download_twitter(
                "https://x.com/i/web/status/2093583622691283018", root, runner,
            )

        command, kwargs = calls[0]
        self.assertTrue(video.name.endswith(".mp4"))
        self.assertEqual(metadata["title"], "X 公开视频")
        self.assertEqual(command[command.index("--fragment-retries") + 1], "10")
        self.assertNotIn("cookies", " ".join(command).lower())
        self.assertFalse(kwargs["shell"])

    def test_transcript_normalization_keeps_timestamps(self):
        result = transcription._normalize_result({
            "text": " ",
            "language": "zh",
            "segments": [{"start": 1.23456, "end": 2.5, "text": " 你好 "}],
        }, "mlx-whisper", "zh")
        self.assertEqual(result["text"], "你好")
        self.assertEqual(result["segments"][0]["start"], 1.235)

    def test_douyin_browser_fallback_merges_split_audio_and_video(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def downloader(url, destination):
                destination.write_bytes(url.encode("utf-8"))
                return destination

            def stream_probe(path):
                content = path.read_text(encoding="utf-8")
                if content == "merged":
                    return {"audio", "video"}
                return {"video"} if "video" in content else {"audio"}

            def merger(_video, _audio, destination):
                destination.write_text("merged", encoding="utf-8")
                return destination

            provider = douyin_browser.PlaywrightMediaProvider(
                downloader=downloader, stream_probe=stream_probe,
                media_merger=merger,
            )
            result = provider.materialize_candidates([
                {"url": "https://example.invalid/video", "length": 20},
                {"url": "https://example.invalid/audio", "length": 10},
            ], root)
            self.assertEqual(result.name, "browser-capture-merged.mp4")
            self.assertEqual(result.read_text(encoding="utf-8"), "merged")
            self.assertEqual(list(root.glob("browser-capture-[12].mp4")), [])

    def test_douyin_browser_rejects_private_and_non_allowlisted_media(self):
        public = lambda _host, _port: [
            (None, None, None, None, ("8.8.8.8", 443)),
        ]
        private = lambda _host, _port: [
            (None, None, None, None, ("127.0.0.1", 443)),
        ]
        self.assertEqual(
            douyin_browser.validate_public_media_url(
                "https://v1.douyinvod.com/media.mp4", public,
            ),
            "https://v1.douyinvod.com/media.mp4",
        )
        with self.assertRaises(douyin_browser.DouyinBrowserError):
            douyin_browser.validate_public_media_url(
                "https://v1.douyinvod.com/media.mp4", private,
            )
        with self.assertRaises(douyin_browser.DouyinBrowserError):
            douyin_browser.validate_public_media_url(
                "https://douyinvod.com.example.org/media.mp4", public,
            )

    def test_frame_extraction_covers_runtime_and_writes_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "source.mp4"
            video.write_bytes(b"video")

            def runner(command, **_kwargs):
                if Path(command[0]).name == "ffprobe":
                    return types.SimpleNamespace(returncode=0, stdout="60\n", stderr="")
                Path(command[-1]).write_bytes(b"jpeg")
                return types.SimpleNamespace(returncode=0, stdout="", stderr="")

            result = frames.extract_frames(
                video, root / "frames", max_frames=3,
                ffmpeg="ffmpeg", ffprobe="ffprobe", runner=runner,
            )
            self.assertEqual(result["frame_count"], 3)
            self.assertEqual(
                [value["timestamp_seconds"] for value in result["frames"]],
                [10.0, 30.0, 50.0],
            )
            self.assertTrue(Path(result["manifest_path"]).is_file())

    def test_download_ready_without_transcription_or_browser(self):
        with mock.patch.object(doctor, "_command", side_effect=lambda name: "/bin/" + name), \
                mock.patch.object(doctor, "_module", side_effect=lambda name: name == "yt_dlp"):
            download = doctor.diagnose("douyin", "download")
            summary = doctor.diagnose("douyin", "summarize")
        self.assertTrue(download["ok"])
        self.assertEqual(download["missing"], [])
        self.assertFalse(summary["ok"])
        self.assertEqual(len(summary["missing"]), 1)
        self.assertFalse(download["secrets_checked"])

    def test_doctor_checks_only_requested_platform(self):
        with mock.patch.object(doctor, "_command", side_effect=lambda name: "/bin/" + name), \
                mock.patch.object(doctor, "_module", return_value=False):
            self.assertTrue(doctor.diagnose("bilibili", "download")["ok"])
            self.assertFalse(doctor.diagnose("twitter", "download")["ok"])

    def test_download_only_skips_audio_even_for_video_with_sound(self):
        self._check_audio_preparation(has_audio=True, download_only=True, expected_audio=False)

    def test_silent_video_can_be_prepared_for_visual_summary(self):
        self._check_audio_preparation(has_audio=False, download_only=False, expected_audio=False)

    def test_summary_extracts_audio_when_present(self):
        self._check_audio_preparation(has_audio=True, download_only=False, expected_audio=True)

    def _check_audio_preparation(self, *, has_audio, download_only, expected_audio):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "sample.mp4"
            video.write_bytes(b"video")
            info = {"duration_seconds": 12.0, "width": 1280, "height": 720, "has_audio": has_audio}
            with mock.patch.object(media, "_download_bilibili", return_value=(video, {})), \
                    mock.patch.object(media, "_probe_media", return_value=info), \
                    mock.patch.object(media, "_extract_audio", return_value=root / "audio.m4a") as extract:
                result = media.prepare("BV1xx411c7mD", root, download_only=download_only)
            self.assertEqual(result["media"]["has_audio"], has_audio)
            self.assertEqual(bool(result["audio_path"]), expected_audio)
            self.assertEqual(extract.call_count, int(expected_audio))

    def test_media_probe_rejects_audio_only_and_invalid_files(self):
        for payload in ({"streams": [{"codec_type": "audio"}]}, {}, []):
            runner = lambda *_args, **_kwargs: types.SimpleNamespace(
                returncode=0, stdout=json.dumps(payload), stderr="")
            with mock.patch.object(media.shutil, "which", return_value="ffprobe"):
                with self.assertRaises(media.MediaPreparationError) as error:
                    media._probe_media(Path("sample.mp4"), runner)
                self.assertEqual(error.exception.code, "INVALID_MEDIA")


if __name__ == "__main__":
    unittest.main()
