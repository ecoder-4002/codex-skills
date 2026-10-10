# Codex Skills by ecoder-4002

一组面向 OpenAI Codex 的可复用 Skills。每个 Skill 都能单独安装；以后新增的 Skill 会继续放在 `skills/` 目录。

## 当前收录

### ai-broll-fuke

把一段参考视频或动效镜头拆解为可复现的视觉逻辑与运动语法：

- 第一阶段先交付干净静态母版、背景板、独立可控图层、manifest 和可见预览；
- 静态素材得到明确批准后，第二阶段才制作 Remotion 动效原型；
- 用精确帧对照检查轮廓、遮挡、枢轴、时序、接缝与最终对齐；
- 只有用户明确要求时才渲染完整视频。

适合复刻、模仿、还原或拆解已有 B-roll / motion-design 镜头。它不会把无参考的生成式视频请求误路由进来。

### hot-news-carousel

把热点、新闻链接或原始素材变成可信的中文竖版新闻图文：

- 浏览并交叉验证时效性事实；
- 先写事实账本和母稿，再按内容决定页数；
- 生成 1080 × 1440 的多页图文；
- 同步生成带独立标题的详细发布文案；
- 校验所有 PNG 尺寸，以及 Markdown/TXT 文案一致性和末尾五个话题标签。

适用于抖音图文、科技新闻海报、小红书新闻长图、AI 热点图文等场景。

### hot-news-carousel-cocreate

共创版热点图文工作流。保留自动调研、写稿、分页、渲染和检查，只在三个真正影响成片的节点依次暂停：

1. 选择叙事角度；
2. 决定立场、表达强度和封面标题；
3. 从可见的视觉方向板中选择或混合最终方向。

三个决定完成后，Skill 会自动交付 1080 × 1440 成图、逐页文案、来源说明和可直接发布的详细简介。适合希望自己担任“主编”，但不想逐步盯制作流程的用户。

### video-chai｜视频拆

把一条公开 B站、抖音或 X/Twitter 视频链接拆解成一篇飞书文档：

- 保留用户原始要求，结合本机转录和代表性关键帧整理内容；
- 首次使用由 Agent 检查并引导配置媒体、转录与飞书能力；
- 支持独立运行，也可连接兼容的本地内容工作台；
- 只处理公开可访问的视频，任务结束后清理临时媒体。

使用 Agent 当前可用的分析与飞书能力，不绑定指定模型 API 服务。详见 [VideoChai 使用与部署说明](skills/video-chai/README.md)。该 Skill 使用 GPL-3.0-only 许可。

## 用 Codex 安装

在 Codex 中发送：

> 使用 `$skill-installer` 安装 https://github.com/ecoder-4002/codex-skills/tree/main/skills/hot-news-carousel

安装共创版：

> 使用 `$skill-installer` 安装 https://github.com/ecoder-4002/codex-skills/tree/main/skills/hot-news-carousel-cocreate

安装 AI B-roll 复刻：

> 使用 `$skill-installer` 安装 https://github.com/ecoder-4002/codex-skills/tree/main/skills/ai-broll-fuke

安装 VideoChai：

> 使用 `$skill-installer` 安装 https://github.com/ecoder-4002/codex-skills/tree/main/skills/video-chai

安装完成后，该 Skill 会在下一轮对话中可用。VideoChai 首次处理视频时会运行 doctor 检查所需依赖；安装 Skill 本身不会自动创建飞书文档。

也可以手动运行 Codex 自带的安装脚本：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo ecoder-4002/codex-skills \
  --path skills/hot-news-carousel
```

将最后一行改为 `--path skills/hot-news-carousel-cocreate`、`--path skills/ai-broll-fuke` 或 `--path skills/video-chai` 即可安装对应 Skill。

## ai-broll-fuke 依赖说明

Skill 本身只包含 Markdown/YAML 指令与参考资料，不包含 npm 包，也不需要上传 `node_modules`。

- 第一阶段：需要能读取参考视频和图片；本机有 FFmpeg/ffprobe 时，抽帧和元数据检查更稳定。
- 第二阶段：需要可用的 Node.js LTS 环境。生成的 Remotion 工程应在自己的 `package.json` 中声明 `remotion`、`@remotion/cli`、React、React DOM、Zod 及实际用到的 `@remotion/*` 包，并提交锁文件。
- Remotion 版本：`remotion` 与所有 `@remotion/*` 包应固定为完全相同的版本，避免 CLI、Studio 和渲染器不匹配。
- 可选增强：本地若已有 `broll-video` 与 Remotion best-practices Skills，Codex 会加载它们；没有时仍可使用本 Skill 自带的运动模式参考完成流程。
- 不应提交：`node_modules/`、Remotion 下载的浏览器/缓存、渲染输出、`.env`、API 密钥和其他本地凭据。

一个可分享的 Remotion 子项目至少应保留 `package.json`、对应锁文件、源码、静态资源、`.gitignore` 和启动说明。同学 clone 后按锁文件使用 `npm ci`、`pnpm install --frozen-lockfile` 或等价命令安装即可。

## 使用示例

安装后可以直接对 Codex 说：

- “用今天最值得讲的 AI 热点做一套抖音图文，页数根据内容决定。”
- “把这个新闻链接做成 1080×1440 的杂志感图文，并生成可直接发布的详细简介。”
- “先完成搜索、事实账本、母稿和分页结构，暂时不出图。”
- “用共创版做一期这个新闻，先让我选叙事、标题和视觉，再自动出完整图。”
- “用 `$ai-broll-fuke` 复刻这段参考动效，先给我静态母版和分层预览，素材确认后再进入 Remotion。”
- “用 `$video-chai` 拆一下这个视频，只提炼方法，并生成飞书文档：<公开视频链接>”

## 可选署名配置

Skill 默认不添加任何账号署名。需要署名时，在当前内容项目根目录创建 `hot-news-carousel.config.yaml`：

```yaml
account_attribution: "@你的账号"
```

也可以在单次提示中直接指定署名；单次指令优先于项目配置。示例文件见 [`examples/hot-news-carousel.config.example.yaml`](examples/hot-news-carousel.config.example.yaml)。

## 关于产出一致性

Skill 固化了研究、事实边界、母稿、分页、视觉层级、交付物和校验标准，因此不同 Codex 用户可以复用同一套生产方法。具体图片不会逐像素一致；最终效果还会受所用模型、联网能力、图片生成能力、可用字体和本地渲染环境影响。

当前版本面向 Codex 用户，不捆绑固定的跨平台渲染模板。它优先让 Codex 根据当前环境选择可靠的 HTML/CSS、SVG、Canvas 或其他确定性排版路径，并用内置脚本检查最终交付物。

## 仓库结构

```text
codex-skills/
├── skills/
│   ├── ai-broll-fuke/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   └── references/
│   ├── hot-news-carousel/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   ├── references/
│   │   └── scripts/
│   ├── hot-news-carousel-cocreate/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   ├── references/
│   │   └── scripts/
│   └── video-chai/
│       ├── SKILL.md
│       ├── README.md
│       ├── LICENSE
│       ├── THIRD_PARTY_NOTICES.md
│       ├── agents/openai.yaml
│       ├── references/
│       ├── scripts/
│       ├── tests/
│       └── assets/
└── examples/
```

## License

仓库根目录及其他未另行声明的内容使用 [MIT](LICENSE)。

`skills/video-chai/` 使用 [GPL-3.0-only](skills/video-chai/LICENSE)，其外部依赖说明见 [THIRD_PARTY_NOTICES.md](skills/video-chai/THIRD_PARTY_NOTICES.md)。
