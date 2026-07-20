# Codex Skills by ecoder-4002

一组面向 OpenAI Codex 的可复用 Skills。每个 Skill 都能单独安装；以后新增的 Skill 会继续放在 `skills/` 目录。

## 当前收录

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

## 用 Codex 安装

在 Codex 中发送：

> 使用 `$skill-installer` 安装 https://github.com/ecoder-4002/codex-skills/tree/main/skills/hot-news-carousel

安装共创版：

> 使用 `$skill-installer` 安装 https://github.com/ecoder-4002/codex-skills/tree/main/skills/hot-news-carousel-cocreate

安装完成后，该 Skill 会在下一轮对话中可用。

也可以手动运行 Codex 自带的安装脚本：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo ecoder-4002/codex-skills \
  --path skills/hot-news-carousel
```

将最后一行改为 `--path skills/hot-news-carousel-cocreate` 即可手动安装共创版。

## 使用示例

安装后可以直接对 Codex 说：

- “用今天最值得讲的 AI 热点做一套抖音图文，页数根据内容决定。”
- “把这个新闻链接做成 1080×1440 的杂志感图文，并生成可直接发布的详细简介。”
- “先完成搜索、事实账本、母稿和分页结构，暂时不出图。”
- “用共创版做一期这个新闻，先让我选叙事、标题和视觉，再自动出完整图。”

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
│   ├── hot-news-carousel/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   ├── references/
│   │   └── scripts/
│   └── hot-news-carousel-cocreate/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       ├── references/
│       └── scripts/
└── examples/
```

## License

[MIT](LICENSE)
