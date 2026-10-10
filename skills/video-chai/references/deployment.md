# 本机依赖配置

仅在 doctor 报告缺少依赖或首次运行失败时读取。全部脚本使用同一个 Python 解释器。

## 按任务安装

- 基础：Python 3.9+，`ffmpeg` 与 `ffprobe`。
- B站：`uvx`，运行时自动调用固定版本 `yutto==2.3.0`。
- 抖音、X/Twitter：当前 Python 可导入 `yt_dlp`。
- 抖音可选兜底：`playwright`，以及系统 Chrome 或 Playwright Chromium。包存在不代表浏览器已安装，首次实际运行仍须检查。
- 语音总结：Apple Silicon 可用 `mlx-whisper`，其他环境可用 `faster-whisper`。仅下载或只分析无声视频时无需安装。

先运行 `doctor.py --json --platform bilibili|douyin|twitter --mode download|summarize`。下载模式只要求媒体依赖；总结模式额外检查本机转录依赖。`ok` 表示本机依赖齐备，不证明网络、平台访问或模型权重已可用。抖音浏览器兜底为可选项，不阻塞匿名下载器的就绪检查。

## 常见配置

macOS 可通过 Homebrew 安装 `ffmpeg` 和 `uv`。把需要的 Python 包装到独立虚拟环境中，避免改变其他项目：

```text
python3 -m venv <video-chai-runtime>
<video-chai-runtime>/bin/pip install yt-dlp          # 抖音和 X/Twitter
<video-chai-runtime>/bin/pip install playwright     # 可选抖音兜底
<video-chai-runtime>/bin/pip install mlx-whisper    # Apple Silicon 语音总结
<video-chai-runtime>/bin/pip install faster-whisper # 其他平台语音总结
```

只运行需要的安装命令。后续全部脚本使用 `<video-chai-runtime>/bin/python`；Windows 对应 `<video-chai-runtime>/Scripts/python.exe`。MLX 模型和 faster-whisper 模型首次使用会下载权重，需要网络和足够磁盘空间。

抖音兜底使用任务目录中的全新浏览器档案，默认尝试系统 Chrome。如果只有 Playwright Chromium，设置 `VIDEO_CHAI_BROWSER_CHANNEL=chromium`；尚未安装时用当前解释器运行 `python -m playwright install chromium`。不读取个人浏览器档案，也不导入登录数据。

按当前任务已有授权配置最小依赖，不把系统级安装、全局配置变更或登录当成默认步骤。先验证短视频的下载和真实媒体轨道；需要总结时再验证本机转录、抽帧和 Agent 的图片读取。缺少语音或视觉能力时说明实际覆盖范围，不声称已完整理解视频。
