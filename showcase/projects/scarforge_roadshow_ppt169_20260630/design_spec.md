# 痕进 Scarforge 路演 - Design Spec

> 人类可读的设计叙事——理由、受众、风格、配色、内容大纲。下游角色读一次获取上下文。
> 机器可读执行契约：`spec_lock.md`（color / typography / icon / image 短表）。Executor 每页生成前重读 spec_lock.md。两者保持同步；冲突时 spec_lock.md 为准。

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | 痕进 Scarforge 路演（evolving-agents / 乔木计划） |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 10 |
| **Design Style** | mode: narrative + visual style: soft-rounded（浅色柔和） |
| **Target Audience** | 投资人 / 路演评委 / 无技术背景观众 —— 技术+非技术都要看得懂（5–7 分钟快速评判） |
| **Use Case** | 创业路演投屏演示 |
| **Delivery Purpose** | `presentation` —— 投影、每页一个观点、大留白、大字号 |
| **Content Strategy** | balanced —— 沿用源 HTML 的 10 页叙事结构与措辞，保留全部事实，仅在 PPT 呈现上调结构与节奏 |
| **Created Date** | 2026-06-30 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | 左右 60px / 上下 50px |
| **Content Area** | 1160×620（安全区） |

---

## III. Visual Theme

### Theme Style

- **Mode**: narrative —— 故事弧（现状痛点 → 张力 → 论点 → 沙盘验证 → 可审计性 → 架构 → 应用 → 诚实边界 → 收尾），说服性路演
- **Visual style**: soft-rounded —— 浅色画布 + 柔和圆角卡片 + 温和阴影，最贴近原 HTML 视觉语言
- **Theme**: Light theme（浅色）
- **Tone**: 清爽、可信、技术但不冷峻；蓝为主、绿橙红做语义状态

### Color Scheme

> 直接迁移源 HTML 的 CSS 变量语义色到浅底，confirmed at item e (方案 A 蓝白清爽)。

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#F4F9FF` | 页面底（原 `--bg`） |
| **Secondary bg** | `#EAF3FF` | 卡片次底/面板（原 `--panel-2`） |
| **Panel** | `#FFFFFF` | 卡片主底（原 `--panel`） |
| **Primary** | `#1D70D6` | 蓝，标题装饰/主色（原 `--blue`） |
| **Accent** | `#31B67A` | 叶绿，成功/scar-line（原 `--leaf`） |
| **Green** | `#15956B` | 成功/PASS（原 `--green`） |
| **Secondary accent** | `#E47B2C` | 橙，转折/强调（原 `--orange`） |
| **Purple** | `#7F5AF0` | 紫，次要强调（原 `--purple`） |
| **Red** | `#D94B4B` | 警告/FAIL（原 `--red`） |
| **Body text** | `#122033` | 主文字（原 `--text`） |
| **Secondary text** | `#52657D` | 注释（原 `--muted`） |
| **Tertiary text** | `#7B8DA3` | 补充/页脚（原 `--subtle`） |
| **Border/divider** | `#C9D9EA` | 卡片边/分隔线（原 `--line`） |

> 无 AI 图片，故无 AI Image Strategy 小节。

### Gradient Scheme

scar-line 渐变（贯穿全 deck 的视觉母题，源自原 HTML 的 `.scar-line`）：

```xml
<linearGradient id="scarLine" x1="0%" y1="0%" x2="100%" y2="0%">
  <stop offset="0%" stop-color="#31B67A" stop-opacity="0"/>
  <stop offset="35%" stop-color="#31B67A"/>
  <stop offset="65%" stop-color="#1D70D6"/>
  <stop offset="90%" stop-color="#E47B2C"/>
  <stop offset="100%" stop-color="#E47B2C" stop-opacity="0"/>
</linearGradient>
```

---

## IV. Typography System

### Font Plan

**Typography direction**: 黑体标题（技术力量感）+ 雅黑正文（清晰易读）+ Consolas 代码/标签（模块名、变量名）。confirmed at item g (方案 A 黑体力量)。全部 PPT-safe 预装字体。

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | 黑体 `SimHei` | `Arial Black` | `sans-serif` |
| **Body** | 微软雅黑 `"Microsoft YaHei"` | `Arial` | `sans-serif` |
| **Emphasis** | 黑体 `SimHei` | `Arial Black` | `sans-serif` |
| **Code/标签** | — | `Consolas`, `"Courier New"` | `monospace` |

**Per-role font stacks**:

- Title: `SimHei, "Microsoft YaHei", sans-serif`
- Body: `"Microsoft YaHei", "PingFang SC", Arial, sans-serif`
- Emphasis: 同 Title
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline (px)**: Body = **32**（presentation 投屏）。用户在确认 UI 中调大了 title/subtitle/annotation（投屏让非技术观众看清）。

| Role | Ratio | Locked px | Weight |
| ------- | ----- | --------- | ------ |
| Cover title (hero) | ~1.75× title | 98 | Bold |
| Page title | 1.75× body | 56 | Bold |
| Subtitle | 1.375× body | 44 | SemiBold |
| Subheading | — | 40 | SemiBold |
| **Body content** | **1×** | **32** | Regular |
| Annotation/caption | 0.75× body | 24 | Regular |
| Code/标签 | 0.625× body | 20 | Regular (mono) |
| Page number/footnote | 0.5× body | 16 | Regular (mono) |

---

## V. Layout Principles

### Page Structure

- **Header area**: ~50px，kicker（英文小标题，mono 字体，蓝色）+ 页码
- **Content area**: ~580px，主体
- **Footer area**: ~40px，scar-line 渐变线 + 页脚文字（mono）

### Layout Pattern Library

| Pattern | 用在哪页 |
| ------- | ------- |
| **Single column centered（留白驱动）** | P01 封面、P02 承诺、P10 收尾（breathing/anchor） |
| **Asymmetric split（4:6 / 6:4）** | P03 问题（左论点右痛点列表）、P06 可审计性（左规则卡右解读） |
| **Five column cards（5 并列卡）** | P04 五机制（5 个 principle）、P08 应用场景（5 个 use-case） |
| **Symmetric split（5:5 对比）** | P05 沙盘（左死池塘右活池塘对比）、P09 诚实边界（claim / 不 claim） |
| **Two layer stack（上下两层架构）** | P07 架构（core / adapter） |

### Spacing Specification

**Universal**:
- 安全边距：左右 60px / 上下 50px
- 内容块间距：32px
- 图标-文字间距：12px

**Card-based**:
- 卡片间距：24px
- 卡片内边距：24–32px
- 卡片圆角：**16px**（soft-rounded 全 deck 统一）
- 单行卡片高度：受内容驱动（5 列卡约 200–260px）
- 卡片阴影：温和（`shadow` 原值 `rgba(29,77,130,0.13)`，约 0.1–0.13 不透明）

---

## VI. Icon Usage Specification

### Source

- **Built-in icon library**: `tabler-outline`（描边线条，适配浅色柔和+精确几何感）
- **Stroke width**: 2（全 deck 统一）
- **Usage method**: SVG placeholder `<use data-icon="tabler-outline/<name>" .../>`

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| 失败/痛点 | `tabler-outline/bug` | P03 |
| 只记成功 | `tabler-outline/database` | P03 |
| 只调参数 | `tabler-outline/adjustments` | P03 |
| 只追最优 | `tabler-outline/focus-2` | P03 |
| 记住失败 | `tabler-outline/database` | P04 |
| 评分搜索 | `tabler-outline/search` | P04 |
| 学习模式 | `tabler-outline/schema` | P04 |
| 换结构 | `tabler-outline/git-branch` | P04 |
| 避拥挤 | `tabler-outline/sparkles` | P04 |
| 沙盘/转折 | `tabler-outline/route` | P05 |
| 可审计/证据 | `tabler-outline/file-search` | P06 |
| 架构层 | `tabler-outline/stack-2` | P07 |
| 代码场景 | `tabler-outline/code` | P08 |
| 自动化场景 | `tabler-outline/robot` | P08 |
| 检索场景 | `tabler-outline/search` | P08 |
| 教育场景 | `tabler-outline/school` | P08 |
| 模拟场景 | `tabler-outline/telescope` | P08 |
| claim | `tabler-outline/circle-check` | P09 |
| 不 claim | `tabler-outline/alert-triangle` | P09 |
| 箭头/转折 | `tabler-outline/arrow-right` | P05 |
| 进化/循环 | `tabler-outline/arrow-loop-right` | P02, P10 |

---

## VII. Visualization Reference List

> 源内容是文字+数据+结构，多页匹配结构型模板（不是数值图表）。

Catalog read: 71 templates

| Page | Template | Path | Summary-quote (verbatim from `charts_index.json`) | Usage |
| ---- | -------- | ---- | ------------------------------------------------- | ----- |
| P04 | vertical_list | `templates/charts/vertical_list.svg` | "Pick for 3-6 numbered key points each with a short description — design principles, core tenets, action items, key takeaways, recommendations, executive summary points." | 5 机制——5 个编号原则，各带一句描述。改造成 5 列横排卡（icon_grid 气质），但保留 numbered + 描述结构 |
| P05 | butterfly_chart | `templates/charts/butterfly_chart.svg` | "Pick for two mirrored datasets sharing a common axis (age pyramid, A/B, income vs expense)." | 死/活池塘两组镜像数据（Sharpe / self_corr / result），中央转折轴。Skip 镜像数值，取"双对比卡"结构 |
| P07 | layered_architecture | `templates/charts/layered_architecture.svg` | "Pick for 3-4 horizontal architecture layers (presentation/service/data), 2-4 module cards per layer, each card = title + 1-line description (description required, even if source brief)." | core/adapter 两层架构，每层 3 个模块卡（memory.py/meta_learner.py/rules.py 与 classify/motif_of/execute） |
| P08 | icon_grid | `templates/charts/icon_grid.svg` | "Pick for 4-9 parallel features/capabilities/services as icon cards — feature grid, service lineup, benefits matrix, brand values, product highlights." | 5 个应用场景并列卡（code/ops/search/tutor/sim），每卡 icon+标题+描述 |
| P09 | pros_cons_chart | `templates/charts/pros_cons_chart.svg` | "Pick for bilateral pros/cons list, 2-5 items per side." | claim / 不 claim 双栏，左绿右橙，各 3 条 |

**Runners-up considered**:

- `icon_grid` | rejected for P04: P04 的 5 机制带编号叙事（01–05）和"先持久化→后评分→后学习→后换结构→后避拥挤"的递进感，`vertical_list` 的 numbered + 描述结构比纯并列 icon_grid 更贴；但视觉上借 icon_grid 的 5 列横排卡形式
- `comparison_table` | rejected for P05: 沙盘是两组共 6 个指标的镜像对比，不是多行多列的功能矩阵；butterfly 的"共享中轴两侧镜像"结构更准
- `module_composition` | rejected for P07: P07 是横向分层（core/adapter 两层），不是单容器套多子卡；layered_architecture 的水平分层贴

---

## VIII. Image Resource List

> **无图片**（image_usage: none，confirmed）。全部用 SVG 原生绘制（图标、卡片、图表）。

---

## IX. Content Outline

> 受众含非技术观众：术语降门槛，关键概念配图标/可视化，数据用对比卡呈现。每页保留源 HTML 措辞，仅在 PPT 呈现上调结构。

### Part 1: 开场 —— 痕进是什么

#### Slide 01 - 封面

- **Cover impact**: 核心钩子="把失败变成下一次行动的约束"——这是反直觉的命题（多数人把失败当垃圾，痕进把失败当资产）。构图策略：**typographic poster（排版海报）**——巨大"痕进"二字作视觉主体，Scarforge 英文作次层，scar-line 渐变线贯穿，右上一组几何叠层（三层方框，呼应"进化层"概念）。不用通用"标题+副标题+装饰背景"。
- **Layout**: 留白驱动；左下 team-badge"乔木计划"+ kicker；中央巨大标题；底部 scar-line + 页码
- **Title**: 痕进
- **Subtitle**: Scarforge / Evolving Agents
- **Core message**: 一个给 Agent 装上的进化层：把失败变成下一次行动的约束。
- **Info**: 乔木计划 · 01 / 10

#### Slide 02 - 承诺（THE PROMISE）

- **Layout**: breathing，单栏居中；左上 team-badge；右上几何叠层装饰
- **Title**: 失败留痕，凭痕而进。
- **Core message**: 痕进不是让 Agent 背更多上下文，而是让它学会长记性——错在哪、为什么错、下次避开哪条路，都留下可追溯的痕迹。
- **Content**: 这是一句完整的命题句，prose 呈现，不做 bullet 拆解

### Part 2: 问题与论点

#### Slide 03 - 问题（THE PROBLEM）

- **Layout**: asymmetric 4:6 —— 左论点 + lead，右三条痛点卡（红左边框）
- **Title**: 今天的 Agent，太容易反复犯同一个错。
- **Core message**: 一次失败修掉了，下一次换个壳又回来——问题不只是记忆不够，而是失败没有进入决策系统。
- **Content**:
  - lead: 客服、代码、搜索、研究都一样：一次失败修掉了，下一次换个壳又回来。
  - 痛点 1（icon bug）只记成功：正确答案进了记忆库，错误路径却被当成垃圾清掉。
  - 痛点 2（icon adjustments）只调参数：prompt 改来改去，但真正该换的是任务结构和搜索路径。
  - 痛点 3（icon focus-2）只追最优：大家挤向看起来最好的方向，新路线还没被试就被放弃。

#### Slide 04 - 论点 / 五机制（THE THESIS）

- **Layout**: dense，5 列横排卡（numbered 01–05，每卡 icon + 标题 + 一句描述）
- **Title**: 不是修 prompt。是让失败变成系统资产。
- **Core message**: 一次失败只停在对话窗口里就是噪音；写进账本、归成模式、投影成规则、影响下一轮搜索，它才开始产生复利。
- **Visualization**: vertical_list（5 编号点，改横排卡）
- **Content**: 5 机制各一句
  - 01 记住失败（icon database）：失败持久化，别把配额烧在已知死路上。
  - 02 评分搜索（icon search）：评估"怎么找答案"，而不只评估最后答案。
  - 03 学习模式（icon schema）：从"这次错了"升级到"这类情况都会错"。
  - 04 换结构（icon git-branch）：方法反复失败时，换路径，不在旧路上微调。
  - 05 避拥挤（icon sparkles）：奖励新颖探索，防止集体挤进局部最优。

### Part 3: 沙盘验证

#### Slide 05 - 首个沙盘（FIRST SANDBOX）

- **Layout**: symmetric 5:5 双对比卡（左红死池塘，右绿活池塘），底部转折箭头 + 关键转折注
- **Title**: 交易不是终点，只是第一个可验证沙盘。
- **Core message**: 量化交易是第一个沙盘——反馈明确、失败可追溯。案例证明的不是"会交易"，而是 Agent 学会了换搜索结构。
- **Visualization**: butterfly_chart（双镜像对比，取结构）
- **Content**:
  - 死池塘 TOP3000 / 大盘池塘：Sharpe 2.15 | self_corr 0.78 | result **FAIL**
  - 活池塘 TOP1000 / 中小盘池塘：Sharpe 2.15 | self_corr 0.68 | result **PASS**
  - 转折：`agent proposes` → `human approves`
  - 关键转折：**答案没变，环境变了。**

### Part 4: 可信度与架构

#### Slide 06 - 可审计性（AUDITABILITY）

- **Layout**: asymmetric 6:4 —— 左规则卡（红边，PENALIZE + 三指标），右解读
- **Title**: 为什么这不是黑箱学习？因为每条规则都能追到证据。
- **Core message**: 真正的差异不在"Agent 好像学到了"，而在它能回答：是哪几次具体失败，教会了这条惩罚。
- **Content**:
  - 规则卡：PENALIZE `cashflow_close_yield` | scope: TOP3000
    - score adjustment **−0.65**（红）
    - confidence **0.75**（蓝）
    - evidence ids **3**（橙）
  - 解读 prose：真正的差异不在"Agent 好像学到了"，而在它能回答：是哪几次具体失败，教会了这条惩罚。

#### Slide 07 - 产品形态（PRODUCT SHAPE）

- **Layout**: dense，上下两层架构卡（core / adapter），每层 3 模块
- **Title**: 它是一个可嵌入的进化层，不是又一个 Agent 平台。
- **Core message**: 你的 Agent 继续负责做事；痕进负责让它从失败中更新搜索方式。换领域时只换 adapter，进化循环留在 core。
- **Visualization**: layered_architecture（两层，每层 3 模块）
- **Content**:
  - core / universal loop（蓝）：通用进化逻辑——记录失败、学习模式、更新规则、奖励新颖探索。模块：`memory.py` / `meta_learner.py` / `rules.py`
  - adapter / domain knowledge（紫）：领域知识薄层——解释什么叫失败、什么叫好结果、什么动作能执行。模块：`classify` / `motif_of` / `execute`

### Part 5: 应用与收尾

#### Slide 08 - 应用场景（WHERE IT APPLIES）

- **Layout**: dense，5 列横排卡（每卡 tag + 标题 + 描述）
- **Title**: 凡是会试错的 Agent，都需要一套失败进化机制。
- **Core message**: 量化交易只是第一个沙盘。痕进真正服务的是"可重复试错"的工作流——失败能被定义、反馈能被记录、下一次行动能被改变。
- **Visualization**: icon_grid（5 并列卡）
- **Content**: 5 场景
  - code（icon code）代码 Agent：编译错误、测试失败被归成模式，下次调整代码结构而不是重复补丁。
  - ops（icon robot）自动化 Agent：表格、API、浏览器操作失败后，记住哪类输入容易触发问题。
  - search（icon search）检索 Agent：搜索结果差时，进化查询路径，而不是只换几个关键词。
  - tutor（icon school）教育 Agent：学生反复出错时，识别错误类型，调整讲解顺序和例题。
  - sim（icon telescope）模拟 Agent：在游戏、仿真、策略环境里积累试错痕迹，更新下一轮策略。

#### Slide 09 - 诚实边界（HONEST BOUNDARY）

- **Layout**: symmetric 5:5 双卡（左绿 claim，右橙 不 claim）
- **Title**: 真正的可信感，来自边界说清楚。
- **Core message**: 这不是软弱，这是可信产品该有的边界——讲一个可追溯的进化事件，不把它包装成万能神话。
- **Visualization**: pros_cons_chart（双栏）
- **Content**:
  - 我们 claim（icon circle-check，绿）：5 个机制都已实现 · 观察到一次真实换结构事件 · 部分学习来自账本投影，不是手写规则。
  - 我们不 claim（icon alert-triangle，橙）：没有有效性的对照证明 · 没有量化收益曲线 · 还没有跨领域规模化验证结论。
  - lead：这不是软弱，这是可信产品该有的边界。

#### Slide 10 - 收尾（CLOSING）

- **Closing impact**: 收尾钩子="痕进把失败变成下一次行动的路标"——对比开篇"多数 Agent 把失败当垃圾"，形成闭环。构图策略：**typographic poster + 留白驱动**，巨大命题句作视觉主体，scar-line 收束。
- **Layout**: breathing，单栏居中留白
- **Title**: 大多数 Agent 把失败当垃圾。
- **Core message**: 痕进把失败变成下一次行动的路标。
- **Content**: 真正的智能，不是第一次就做对，而是第一次做错之后，第二次少走同一条错路。

---

## X. Speaker Notes Requirements

每页一个 speaker note 文件，存 `notes/`：

- **Filename**: 匹配 SVG 名（`01_cover.svg` → `notes/01_cover.md`）
- **Total duration**: 5–7 分钟（presentation 路演）
- **Notes style**: conversational（narrative mode register——像跟观众说话，不是念报告）
- **Purpose**: persuade（说服投资人/评委）
- **结构**: 每页 scenario-conflict-resolution + 与上页的桥接句；口语化数据（"近三分之二"而非"0.68"）

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:

1. viewBox: `0 0 1280 720`
2. 背景用 `<rect>`
3. 文本换行用 `<tspan>`（`<foreignObject>` 禁用）
4. 透明用 `fill-opacity` / `stroke-opacity`；`rgba()` 禁用
5. 禁用：`mask`, `<style>`, `class`, `foreignObject`, `textPath`, `animate*`, `script`
6. 文本字符用原始 Unicode（`—` `→` `©` 等）；HTML 命名实体（`&nbsp;` `&mdash;`…）禁用；XML 保留字 `& < > " '` 转义为 `&amp; &lt; &gt; &quot; &apos;`（如 `R&amp;D`）
7. `marker` 条件允许：须在 `<defs>`，`orient="auto"`，形状为三角/菱形/圆
8. `clipPath` 仅允许用于 `<image>`（本 deck 无图片，基本用不到）

### PPT Compatibility Rules:

- `<g opacity="...">` 禁用（组透明度）；在每个子元素上单独设
- 内联样式 only；外部 CSS 和 `@font-face` 禁用
