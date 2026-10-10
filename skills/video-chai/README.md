# VideoChai

一个可安装的 Agent Skill：输入一条公开 B 站、抖音或 X/Twitter 推文视频链接，临时取得媒体并在本机转录、读取代表性关键帧，最后只生成一篇飞书文档。

## 使用

给支持 Skill 和本地终端的 Agent 发送这一句话：

> 请安装这个 VideoChai Skill：https://github.com/ecoder-4002/codex-skills/tree/main/skills/video-chai ，读取 SKILL.md，并在首次使用时检查和配置缺少的依赖。

在 Codex 中也可以使用自带安装器：

> 使用 `$skill-installer` 安装 https://github.com/ecoder-4002/codex-skills/tree/main/skills/video-chai

也可以把完整 `video-chai` 目录交给 Agent，说“安装这个 Skill”。安装完成后，在下一轮对话中使用：

```text
$video-chai 拆一下这个视频，只分析人物和氛围：https://www.bilibili.com/video/BV...
```

第一次运行时，Agent 会：

1. 识别平台与操作系统，执行只读 doctor。
2. 只安装本次链接缺少的媒体和本机转录依赖。
3. 引导你在官方交互页完成飞书授权。
4. 用一条短公开视频做冒烟测试，然后才处理长视频。

它不会要求你在聊天里粘贴密钥或 Cookie。需要系统级安装或登录时，Agent 会先取得确认。

## 两种模式

- 工作台模式：连接兼容的本地内容工作台，支持持久任务、失败续跑及更成熟的抖音匿名兜底。
- 独立模式：只依赖本目录脚本、ffmpeg、本机 Whisper 和 Agent 自己的视觉/飞书能力。抖音先用匿名`yt-dlp`，失败时自动使用临时隔离 Playwright 浏览器，不读取个人档案或 Cookie。

X/Twitter 公开推文视频使用匿名`yt-dlp`；不读取浏览器 Cookie，需登录或受保护推文会明确报错。

## 依赖与费用

Skill 本身不销售模型额度，也不内置 API Key。独立模式使用本机 Whisper 转录、Agent 自己的分析能力和已有的飞书文档能力；是否消耗订阅额度或产生 API 费用，取决于接收方 Agent 与服务的配置。支持的环境和部署步骤见 [references/deployment.md](references/deployment.md)。

## 验证

在 Skill 目录运行已有测试：

```bash
python3 -m unittest discover -s tests -v
```

测试覆盖 URL 校验、匿名媒体适配、抖音音画合并、转录时间戳、抽帧清单及用户要求保留。平台访问与飞书发布仍需在接收方环境中完成首次冒烟验证。

## 隐私边界

媒体、音频和关键帧只存在于任务临时目录，成功或失败后删除。Skill 只处理公开可访问的视频，不绕过登录、付费或会员权限。

## License

GPL-3.0-only。B 站媒体准备通过独立进程调用同为 GPL-3.0 的 [yutto](https://github.com/yutto-dev/yutto)，未复制或内嵌其源码。详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
