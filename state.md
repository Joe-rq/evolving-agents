# evolving-agents state.md — 黑客松 SSOT

> 唯一状态源（Single Source of Truth）。每次变更追加更新，不删历史。明天 session 从此文件恢复上下文。

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

## 战略决策锁定（6/26 Day 0 定，勿忘）

1. **赛道：自进化智能体**（放弃深度研究/多智能体/coding/computer-use）
2. **底座：alpha-mining**（不是 harness-lab/evomap）；私有，脱敏讲 case study
3. **长期方向 B**：机制开源化 = content（5 factor 文档，CC）+ core（引擎，Apache）+ wq reference adapter
4. **路 1：诚实 case study**（不是对照实验）
   - 对照实验**作废**：alpha-mining 进化机制 06-24 才上线，进化后数据仅 2-3 天（50 条总），对照做不出
   - demo 证据 = 换池塘 case study（真实事件）+ 5 factor 机制展示 + 诚实边界
5. **5 Factor**：① Remember failures ② Score the search ③ Learn failure modes ④ Pivot structure ⑤ Seek novelty
6. **诚实边界**（`content/honest-boundary.md`）：能说"机制已实现 + 换池塘真实事件"，**不能说**"对照证明有效 / 量化收益 / 跨领域"
7. **不套 harness-lab**（它自己 README 说不适合 demo），用本 state.md 治理（PDCA 风格）
8. **wq adapter 放置**待定（脱敏进 repo vs 独立私有），Day 2 切 adapter 时定
9. **竞品参照**：QuantML 的 `wq-alpha-research`（同方向、已开源、营销吹无对照）—— 差异化靠：对照披露 + 机制通用化 + 诚实

## 进度（6/26）

### ✅ 完成 — 8 commit

| commit | 内容 |
|---|---|
| `136bb10` | 初始骨架（5 factor 种子 + 仓库布局 + 双许可） |
| `6e25507` | 诚实边界（claim 降级 observed-only） |
| `1582532` | case study 换池塘（demo 唯一硬证据，数字全验证） |
| `b152ba5` | core/protocols（5 adapter 协议） |
| `9490bba` | core/memory（Factor 1，universe-scoped ledger） |
| `21333de` | core/meta_learner（Factor 2/3，family 打分 + strike + motif penalty） |
| `00f4ad9` | core/evolver（Factor 4，frame 竭尽检测 + pivot 建议） |
| `eaf6f11` | core/novelty（Factor 5，novelty + crowding + exploration lane） |

### 引擎模块状态

| 模块 | Factor | 状态 |
|---|---|---|
| protocols.py | 5 接口 | ✅ 验证通过 |
| memory.py | F1 | ✅ 验证通过 |
| meta_learner.py | F2/3 | ✅ 验证通过 |
| evolver.py | F4 | ✅ 验证通过 |
| novelty.py | F5 | ✅ 验证通过 |
| **engine.py** | 编排（综合打分 + 主循环） | ⬜ **Day 1 第一件事** |
| adapters/wq/ | 量化 reference | ⬜ Day 2 |

## Day 1-6 剩余 plan

| 日期 | 任务 | 验证 |
|---|---|---|
| **6/27 D1** | `engine.py` 编排：综合打分公式（family_score + novelty + motif_penalty + crowding）+ 主循环骨架 + **mock adapter 集成验证**（跑完整 loop） | mock adapter 跑通一次 generate→score→filter→record→pivot-check |
| **6/28 D2** | wq adapter 起步（5 协议实现，从 alpha-mining `research_state.py` 抠）+ 定 wq 放置 | 通用核心 + wq adapter 在真实 scoreboard 上复现换池塘决策 |
| **6/29 D3** | factor 文档扩写（5 篇，诚实标注）+ README 精修（套 Dex 叙事） | 非量化背景能懂 |
| **6/30 D4** | demo 可视化（case study 回放：Sharpe 不变/self_corr 0.78→0.68）+ 录 dry-run | 5 分钟进化弧线 |
| **7/1 D5** | pitch（诚实 framing）+ 演练 + 缓冲 | 扛住三记质疑（见下） |
| **7/2 D6** | 上午演练，下午提交 | 提交物齐：factor 文档 + core + case study + demo 视频 |

## 三记质疑话术（D5 必须备好）

1. **"这是策略系统不是 agent"** → agent 自主决策挖什么方向（Factor 2）+ 自主提议换池塘（Factor 4）；回测器跑人写的策略
2. **"它学的到底是什么"** → 学的是搜索策略本身（往哪搜、避开什么），不是某个具体解 = meta-learning over strategy space
3. **"原创性/都是 agent 干的"** → 量化沙盘是 agent 跑的，5 factor 机制是工程设计的，是我的核心作品

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

## Changelog

| 时间 | 变更 |
|---|---|
| 2026-06-26 | Day 0：战略全部锁定（赛道/底座/方向/路1/5 factor/诚实边界）；路 1 确定（对照实验作废，数据不够）；建 evolving-agents 仓库 + 8 commit（5 factor 种子 + 诚实边界 + case study + core/ 5 引擎模块全验证）；state.md 建 |
