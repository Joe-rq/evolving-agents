# evolving-agents state.md — 黑客松 SSOT

> 唯一状态源（Single Source of Truth）。每次变更追加更新，不删历史。每次 session 从此文件恢复上下文。

## 项目基本信息

| 属性 | 内容 |
|---|---|
| 产品 | evolving-agents — 5-Factor Self-Evolving Agents（机制开源） |
| 赛道 | **自进化智能体** |
| 底座 | alpha-mining（私有，脱敏讲 case study） |
| 长期方向 | B：把自进化机制做成领域无关开源引擎 |
| 时间线 | 7/1 开发截止，7/2 下午提交 |
| 仓库 | `/Users/qrq/AI/code/02-work/evolving-agents` |
| 私有底座 | `/Users/qrq/AI/code/02-work/alpha-mining`（不公开） |
| 当前 | 2026-06-27 Day 1 |

## 战略决策锁定（勿忘）

1. **赛道：自进化智能体**（放弃深度研究/多智能体/coding/computer-use）
2. **底座：alpha-mining**（不是 harness-lab/evomap）；私有，脱敏讲 case study
3. **长期方向 B**：机制开源化 = content（5 factor 文档，CC）+ core（引擎，Apache）+ wq reference adapter
4. **路 1：诚实 case study**（不是对照实验）
   - 对照实验**作废**：alpha-mining 进化机制 06-24 才上线，进化后数据仅 2-3 天（50 条总），对照做不出
   - demo 证据 = 换池塘 case study（真实事件）+ 5 factor 机制展示 + 诚实边界
5. **5 Factor**：① Remember failures ② Score the search ③ Learn failure modes ④ Pivot structure ⑤ Seek novelty
6. **诚实边界**（`content/honest-boundary.md`）：能说"机制已实现 + 换池塘真实事件"，**不能说**"对照证明有效 / 量化收益 / 跨领域"
7. **不套 harness-lab**（它自己 README 说不适合 demo），用本 state.md 治理
8. **wq adapter 放置**待定（脱敏进 repo vs 独立私有），Day 2 切 adapter 时定
9. **竞品参照**：QuantML 的 `wq-alpha-research`（同方向、已开源、营销吹无对照）—— 差异化靠：对照披露 + 机制通用化 + 诚实
10. **strategy_memory 吸收**（6/27 定）：记忆层从"隐式打分函数"升级到"显式可审计 Rule 对象"（带 confidence + evidence_ids）。抽象结构进 `core/rules.py`，量化知识（具体 motif 权重）留 wq adapter。强化 honest-boundary 的可审计性。

## 进度

### ✅ Day 0（6/26）— 8 commit
`136bb10` 骨架 · `6e25507` 诚实边界 · `1582532` case study · `b152ba5` protocols · `9490bba` memory · `21333de` meta_learner · `00f4ad9` evolver · `eaf6f11` novelty

### ✅ Day 1（6/27）— 3 commit（含 strategy_memory 吸收）
- `bc1fd74` **rules.py** — Rule + RuleSpec + project_rules（Factor 1/3 可审计升级）
- `11eea95` memory 接入（Attempt.evidence_kinds + Memory.project_rules）
- `1a65373` **engine.py** — 编排 5 factor + rules 成一个 loop（v0.1 能跑，2 轮 learn-and-block 闭环验证）

### 引擎模块状态（7/7 全齐，core/ v0.1 能跑）

| 模块 | Factor | 状态 |
|---|---|---|
| protocols.py | 5 接口 | ✅ |
| memory.py | F1（+evidence_kinds +project_rules） | ✅ 升级 |
| rules.py | F1/3 审计（Rule+confidence+evidence_ids） | ✅ 新 |
| meta_learner.py | F2/3（score_families+strike） | ✅（motif_penalty 标 legacy） |
| evolver.py | F4 | ✅ |
| novelty.py | F5 | ✅ |
| **engine.py** | 编排（综合打分+主循环） | ✅ v0.1 能跑 |
| adapters/wq/ | 量化 reference | ⬜ Day 2 |

## 风险（重要：已降低）

**engine + mock adapter 已能 demo 5-factor 闭环**（learn → rule → block，2 轮验证通过），**不依赖 wq/alpha-mining 私有数据**。所以：
- Day 4 demo 有保底（mock adapter 跑闭环机制）
- wq adapter（真实量化数据）是**强化**，不是必需——即使 wq 没做完，demo 也能站住
- 两条腿互不为依赖：机制展示（mock，确定能跑）+ 真实案例（换池塘 case study，已验证）

## Day 2-6 剩余 plan

| 日期 | 任务 | 验证 |
|---|---|---|
| **6/28 D2** | wq adapter：从 alpha-mining `research_state.py` / `strategy_memory.py` 抠 5 协议 + RuleSpec；定 wq 放置（脱敏进 repo vs 私有） | 通用核心 + wq adapter 在真实 scoreboard 上复现换池塘决策 |
| **6/29 D3** | factor 文档扩写（5 篇，诚实标注）+ README 精修（套 Dex 叙事） | 非量化背景能懂 |
| **6/30 D4** | demo 可视化（case study 回放 + engine mock 闭环）+ 录 dry-run | 5 分钟进化弧线 |
| **7/1 D5** | pitch（诚实 framing）+ 演练 + 缓冲 | 扛住三记质疑 |
| **7/2 D6** | 上午演练，下午提交 | 提交物齐 |

## 三记质疑话术（D5 必须备好）

1. **"这是策略系统不是 agent"** → agent 自主决策挖什么方向（Factor 2）+ 自主提议换池塘（Factor 4）；回测器跑人写的策略
2. **"它学的到底是什么"** → 学的是搜索策略本身（往哪搜、避开什么），不是某个具体解 = meta-learning over strategy space
3. **"原创性/都是 agent 干的"** → 量化沙盘是 agent 跑的，5 factor 机制 + Rule 投影是工程设计的，是我的核心作品。**且每条 Rule 带 evidence_ids 可追溯**（QuantML 没有）

## demo 主证据（case study 要点，背熟）

同一条因子 `0.5*group_rank(ts_rank(operating_income/close,126),industry)+0.5*group_rank(ts_rank(free_cash_flow_reported_value/close,126),industry)`：

- **TOP3000**：Sharpe **2.15**，self_corr **0.7844** → SELF_CORR_FAIL（拥挤）
- **TOP1000**：Sharpe **2.15**，self_corr **0.6768** → checks clear → **submitted**（`RRp81Ev1`）
- **Sharpe 没变（因子质量同），self_corr 变（环境拥挤度）= 环境问题不是因子问题 = Factor 4 干净例证**
- 诚实：TOP1000 不是"换就活"——3 变体里 2 仍 fail（0.916/0.825），只 1 条（0.6768）过
- agent 提议换池塘，人批准（agent-proposes / human-approves）

**一句话 pitch**（边界内）："5 个机制都实现了，有一次 agent 提议换池塘救活死因子的真实事件。我们公开承认有效性证明还在 roadmap——因为另一种选择是营销。"

## 关键约束

- **诚实边界是差异化**（vs QuantML）：不吹对照证明，披露机制 06-24 上线、数据规模小
- **IP**：alpha-mining 量化层私有；core/ 机制层开源；`.gitignore` 防 secrets
- **不套 harness-lab**：用 state.md（复用 PaperSwarm PDCA 风格）
- **核心武器**："我不懂量化，但 agent 自己学会换池塘"——不依赖对照
- **Rule 可审计**（strategy_memory 吸收后）：每条惩罚带 evidence_ids，能答"为什么"

## Changelog

| 时间 | 变更 |
|---|---|
| 2026-06-26 | Day 0：战略全部锁定；路 1 确定（对照作废）；建仓库 + 8 commit（5 factor 种子 + 诚实边界 + case study + core 5 模块） |
| 2026-06-27 | Day 1：吸收 strategy_memory（决策 #10，记忆层升级 Rule-based）+ engine.py v0.1（7 模块串成能跑引擎，2 轮闭环验证）；core/ v0.1 能 demo（mock adapter 保底，wq adapter 降为强化项） |
