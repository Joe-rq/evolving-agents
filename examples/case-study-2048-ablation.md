# 案例研究：2048 失忆组对照 — 公开、可复现的有效性测试

> 本框架诚实边界的最大软肋是「有效性未对照」。这个案例在一个公开领域补上它。
> 配图：[demo/05](../demo/05-ablation-result.zh.html)。完整协议：[experiments/pre_registration.md](../experiments/pre_registration.md)。

## 为什么需要这个案例

换池塘 case study 是真实事件，但有两个限制：保密（私有量化数据）、无对照。`honest-boundary` 公开承认「没有有效性的对照证明」。本案例换了一个**公开、可批量、零 API 成本**的领域来补：

- 公开：任何人可复现 — `bash experiments/run_ablation.sh`
- 可批量：M=30 配对复制，纯本地，无 LLM、无 GPU
- 真对照：失忆组（amnesic）vs 完整组（full），唯一变量是 Memory 是否累积

## 实验设计（预注册于结果观察之前）

唯一处理变量：**传给 Engine 的 Memory 实例是否跨 round 累积**。

| 组 | 配置 | 等价于 |
|---|---|---|
| 完整组（full） | 一个 Memory 跑完全部 R round | 真·自进化 |
| 失忆组（amnesic） | 每 round 新建 Memory | 每次 from scratch |

engine **一行未改**——所有学习只从 Memory 账本读。配对设计：每 round 共享候选池 + 确定性 execute seed（两组对同一 (body, round) 跑相同棋盘轨迹）。分析单元 = replicate（30 次独立复制，各不同全局 seed），防 pseudo-replication。

预热 2 round（执行全部候选池，让每个 family 积累失败证据）+ 测试 6 round（max_execute=3，靠 family/motif 导向）。主检验：Wilcoxon signed-rank（配对、双尾、α=0.05）。

## 2048 ↔ 5 factor 映射

| 概念 | 量化领域（私有） | 2048 领域（公开） |
|---|---|---|
| 候选 | 因子表达式 body | 参数化策略（5 启发式权重） |
| family（F2） | 经济族 technical/profitability… | 策略派别 corner / space / snake / merge / … |
| motif（F3） | close_yield 类风险族 | unanchored_mono / aggressive_merge / shallow_random |
| universe（F4） | TOP3000 / TOP1000 | 棋盘大小（本实验固定 4×4） |
| 成功判定 | Sharpe + self_corr gate | 达到 1024 tile（max over K 局） |
| **Factor 4 表现** | **换池塘救活死因子** | **pivot 建议触发**（见下方诚实修正） |

## 结果

**verdict: NULL（按预注册 α=0.05 严格判定）**。

| 量 | 值 |
|---|---|
| 配对差中位数（完整 − 失忆，后 4 round mean log₂ tile） | **+0.083** |
| bootstrap 95% CI | **[0.000, 0.167]** |
| Wilcoxon signed-rank p（双尾） | **0.079** |
| 为正的复制数 | **19 / 30** |
| 最小可检测效应 MDE | ≈ 0.10 |

方向一致、接近显著但未跨 0.05 阈值——按预注册诚实判为 null。观测的中位数 0.083 低于 MDE 0.10，即"效应小到这套装置检不出"。

## 机制层证据（即使 primary 指标 null，这一节也成立）

「机制作为代码可观察地工作」与「学习增益被统计检出」是两件事，分开报告：

- **Factor 1/3 — block**：完整组屏蔽已知失败候选（已测 + 同 motif 规则），失忆组不屏蔽。
- **Factor 4 — pivot**：完整组的 Evolver 触发结构性 pivot 建议（family 被 strike / motif 重复失败），失忆组不触发。
- **Factor 3 — 可审计规则**：完整组从账本投影出带 `evidence_ids` 的 Rule（可追到具体哪几次失败教的）。

| 机制（M=30 累计） | 完整组 | 失忆组 |
|---|---|---|
| Factor 1/3 — block 候选 | **452** | 0 |
| Factor 4 — pivot 建议触发 | **131** | 3（单 round 偶发） |
| Factor 3 — 投影出带 evidence_ids 的 Rule（均值） | **1.7 条** | 0 |

机制作为代码可观察地工作；失忆组几乎为零。但这一节与上方的 primary null **不矛盾**——见下方"证明了/没证明什么"。

## 两个诚实修正（数据驱动，非结果后改）

1. **Factor 4 在 2048 不 claim「换池塘」**。预实验发现：2048 大棋盘（6×6）对策略**更有利**（空间多、分数天花板更高），不存在量化里「换池塘救活死策略」的现象。Factor 4 在此的可观察证据是 Evolver 的 pivot_recommendation 触发（family struck + motif 重复失败）——同一机制，不同表现。我们不强行编造换池塘故事。

2. **2048 是全自动，无人参与**。量化 case 是 agent-proposes / human-approves（人批准换池塘）；2048 对照实验从头到尾无人介入。我们不把「自主自进化」的 claim 从量化 case 偷渡到 2048——两个案例的人机协同边界不同，分开讲。

## 这证明了 / 没证明什么

- ✅ **证明了**：5 个机制在一个全新公开领域（2048）端到端跑通；机制作为代码**可观察地工作**（block 452 / pivot 131 / 规则 1.7，失忆组为零）；"跨领域验证"从 roadmap 变成 done；引擎一行未改就接上新领域。
- ⚠️ **没证明**：累积 memory 带来**统计显著**的执行质量提升（p=0.079 > 0.05）。机制工作 ≠ 增益被统计检出。
- 🧭 **诚实解读**：在 2048 depth=0 + 当前候选池下，导向带来的提升（中位数 ~0.08 log₂，约 max tile 半档）低于这套装置的最小可检测效应（MDE≈0.10）。原因可解释：depth=0 下高产 family 多（corner/space/random 都能达 1024），导向避开 snake/merge 的收益有限。这区分了「机制存在」与「机制有效」——我们不把前者打扮成后者。
