# Agent-led deployment

只在 `scripts/doctor.py --json` 显示工作台不可用或独立模式缺少依赖时读取。

## 部署目标

独立模式需要：

- Python 3.9+
- `ffmpeg` 与 `ffprobe`
- B站：`uvx`，运行时固定调用 `yutto==2.3.0`
- 抖音：当前 Python 可导入 `yt_dlp` 和 `playwright`；优先复用系统 Chrome，没有时可在确认后安装 Playwright Chromium
- X/Twitter：当前 Python 可导入 `yt_dlp`；只处理匿名可访问的公开推文视频
- 本机转录：Apple Silicon 优先 `mlx-whisper`；其他平台可用 `faster-whisper`
- 飞书：当前 Agent 有飞书文档连接器/Skill，或本机已经完成 `lark-cli` 用户授权

## Agent 的引导顺序

1. 先根据用户链接运行 `doctor.py --json --platform bilibili|douyin|twitter`，报告已满足和缺失项，不要直接批量安装。
2. 根据操作系统给出最小安装命令，并在执行系统级安装前取得用户确认。
3. 依赖安装后重新运行 doctor，直到媒体与转录均 ready。
4. 飞书授权必须在官方交互页或凭据管理工具中完成；不要要求用户把 App Secret、access token 或 Cookie 发到聊天里。
5. 用一条短公开视频完成冒烟：只验证临时下载、短转录、1–3帧和测试文档。用户确认后再处理长视频。

## 常见安装提示

macOS 可优先使用 Homebrew 安装 `ffmpeg` 和 `uv`。Python 集成依赖安装到隔离虚拟环境：

```text
python3 -m venv <video-chai-runtime>
<video-chai-runtime>/bin/pip install yt-dlp             # 抖音和 X/Twitter
<video-chai-runtime>/bin/pip install playwright          # 只有抖音兜底需要
<video-chai-runtime>/bin/pip install mlx-whisper     # 仅 Apple Silicon
<video-chai-runtime>/bin/pip install faster-whisper  # 其他平台备选
```

后续独立模式的 `doctor.py`、`prepare_media.py` 和 `transcribe.py` 必须都用 `<video-chai-runtime>/bin/python` 运行；不要用另一个 Python 而导致 doctor 看不到刚安装的包。Windows 的对应解释器为 `<video-chai-runtime>\\Scripts\\python.exe`。

不要静默安装浏览器扩展、读取个人浏览器档案或导入 Cookie。抖音先使用公开匿名 `yt-dlp`；失败时使用任务目录内全新 Playwright 档案，只下载白名单 CDN 播放流，并用 ffprobe 确认音画轨道。本机无 Chrome 且内置 Chromium 也未安装时，Agent 可在用户确认后运行`<video-chai-runtime>/bin/python -m playwright install chromium`。

## 工作台兼容契约

若用户已有服务，只需提供：

- `GET /api/short-video-jobs`
- `POST /api/short-videos/intake`
- `GET /api/short-video-jobs/{job_id}`
- `GET /api/items`

通过 `VIDEO_CHAI_WORKBENCH_URL` 指定地址，默认 `http://127.0.0.1:8765`。只应连接用户明确部署的可信本机或私有服务。
