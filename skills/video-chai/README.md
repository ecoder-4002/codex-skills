# VideoChai｜视频链接下载与总结

给 Agent 一条公开 B站、抖音或 X/Twitter 视频链接，把视频下载到本地；也可以在本机转录和抽帧后，由 Agent 总结内容。支持仅下载、仅总结，以及下载并总结。

## 一句话安装

> 请安装这个视频链接下载与总结 Skill：https://github.com/ecoder-4002/codex-skills/tree/main/skills/video-chai ，读取 SKILL.md，并检查本次任务需要的依赖。

Codex 也可以使用自带安装器：

> 使用 `$skill-installer` 安装 https://github.com/ecoder-4002/codex-skills/tree/main/skills/video-chai

## 使用示例

```text
$video-chai 下载这个视频：https://www.bilibili.com/video/BV...
$video-chai 总结这个视频，重点提炼方法：https://v.douyin.com/...
$video-chai 下载并总结这个视频：https://x.com/username/status/...
```

下载结果保存为本地视频，总结会在对话中给出并保存为本地 Markdown。支持抖音分享文本中的短链接、B站 BV 号及分集参数；本版本以已给定的视频链接为入口，不提供关键词搜索。

## 依赖与费用

需要 Python 3.9+、FFmpeg/ffprobe 和对应平台下载器。仅下载不需要 Whisper；语音总结使用本机 Whisper，画面和内容理解使用接收方 Agent 的能力。模型权重首次使用可能需要下载，Agent 的使用额度或费用取决于自己的订阅或 API 配置。Skill 本身不销售 token，也不内置模型 API Key。

首次使用先检查本次平台和模式：

```bash
python3 scripts/doctor.py --json --platform bilibili --mode download
python3 scripts/doctor.py --json --platform douyin --mode summarize
```

具体配置见 [部署说明](references/deployment.md)。只处理公开可访问的视频，不读取个人浏览器登录数据。默认优先选择 720p 档位，实际分辨率以输出文件为准。无声视频可以下载，并通过画面总结。

## 验证

```bash
python3 -m unittest discover -s tests -v
```

测试覆盖 URL 校验、匿名下载命令、抖音音画合并、无声视频、下载与总结的依赖区分、转录时间戳及抽帧清单。平台访问受源站限制，下载失败会明确报告；接收方环境仍需实际验证下载及本机模型可用性。

临时音频、关键帧和未要求保留的媒体在交付后清理；用户下载的视频和本地总结保留。

## License

GPL-3.0-only。外部工具单独安装，未内嵌其源码，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
