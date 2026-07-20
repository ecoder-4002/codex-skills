# Co-create checkpoint templates

Use these compact structures. Replace placeholders with topic-specific, source-backed content. Do not expose internal chain-of-thought; show conclusions, evidence boundaries, and tradeoffs.

## Checkpoint 1: narrative angle

```markdown
## A. 方向名

- 核心问题：
- 主要受众：
- 用户收获：
- 可能结论：
- 主动弱化：
- 机会：
- 风险：
```

End with one recommendation and one question:

> 请选择 A / B / C，或直接说怎样混合，例如“B 为主，吸收 C 的结论”。

## Checkpoint 2: stance and title

Show the editorial layers first:

```markdown
### 事实层
- ...（来源类型）

### 推演层
- ...（推导依据与不确定性）

### 观点层
- ...（价值判断）
```

Then show title candidates:

```markdown
## 1. 稳健新闻型

- 标题：
- 副标题：
- 表达强度：克制 / 鲜明 / 尖锐
- 传播优势：
- 事实风险：
- 前景层级：事实 / 推演 / 观点
```

End with one combined question:

> 请选择表达强度和标题，可直接修改措辞，例如“鲜明 + 标题 2，但删掉‘终于’”。

## Checkpoint 3: visual direction

Render each board before presenting the comparison. Then use:

```markdown
## A. 方向名

![A 方向板](/absolute/path/previews/direction-a.png)

- 字体关系：
- 深浅节奏：
- 页面结构：
- 信息密度：
- 图片处理：
- 强调色：
- 优势：
- 代价：
- 适配原因：
```

Use the same selected title, copy excerpt, and three page roles in every board. Differences must be visible rather than merely described.

End with one question:

> 请选择 A / B / C，也可以混合，例如“A 的字体和留白，B 的图片处理，C 的深浅节奏”。

## Selection handling

- Quote the user's chosen or mixed direction in `cocreate-state.md`.
- Do not treat unselected candidates as explicit rejections.
- If the user rejects an option and gives a reason, add only that explicit negative choice to the project log.
- If a selection is ambiguous but a safe interpretation exists, state the interpretation and continue. Ask a follow-up only when different interpretations would materially change the work.
