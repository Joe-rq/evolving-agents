# 预注册协议 — 2048 失忆组(amnesic) vs 完整组(full) 对照实验

> **本文件在跑全量实验（M=30）之前写死，先于任何结果观察。**
> 这是防 p-hacking 嫌疑的护城河——与项目「诚实边界」差异化一致。
> 锁定时间：2026-06-30（初版）；装置修正见文末（smoke 后、正式跑前）。

## 背景与动机

evolving-agents 的 honest-boundary 当前最大软肋是「有效性未对照」（原失忆组对照因私有量化数据量太小而作废）。本实验在公开、可批量、零 API 成本的 2048 领域补上这个对照。

唯一处理变量：传给 Engine 的 **Memory 实例是否跨 round 累积**。
- 完整组（full）：一个 Memory 跑完全部 R round。
- 失忆组（amnesic）：每 round 新建 Memory（疤痕清零）。

engine 本身一行不改；候选生成器与 execute callback 均确定性、memory-independent。两组共享同一候选池 + 同一 seed 派生的棋盘轨迹。

## 假设

- **H1（备择）**：完整组的 primary 指标显著高于失忆组（累积 memory 帮助 agent 把执行预算导向更好候选）。
- **H0（零）**：两组无显著差异。
- **承诺**：若 p ≥ 0.05，按 null 诚实报告，**不**事后换指标/换载体重跑直到显著（那是 p-hacking，会摧毁诚实差异化）。

## 锁定参数（不可事后改）

| 参数 | 值 | 说明 |
|---|---|---|
| M（replicate 数） | 30 | 各不同全局 seed；这是分析单元 |
| R（每 replicate round 数） | 8 | 含 2 round 预热 + 6 round 测试 |
| K（每候选 execute 局数） | 10 | max_tile 取 K 局最大 |
| max_execute | 3 | **测试期**每 round 执行的候选数 |
| WARMUP | 2 | 前 2 round 执行全部池（探索），让每个 family 积累失败证据；后 6 round 用 max_execute（利用/导向） |
| size（棋盘） | 4 | universe 固定 4×4 |
| 后 H round 窗口 | 4 | primary 取后 4 round（round 4-7，全在测试期）均值 |
| 候选池大小 | 15 | generate_pool，memory-independent，跨 round 全 unique（jitter） |
| engine weights | 默认（family .3 / novelty .3 / rule 1.0 / crowding 1.0） | 两组相同 |

## Primary 指标（主检验对象）

每个 replicate 产出两条曲线（每 round 一个值）：
```
per-round mean log2(max_tile) = mean(log2(max_tile of the round's executed candidates))
```
- **primary 配对差** = `mean(full_curve[-4:]) − mean(amn_curve[-4:])`
- log2 是天然标度（512=9, 1024=10, 2048=11），比二值 success 敏感得多。

M=30 个配对差值进入检验。

## 统计检验

1. **主检验**：Wilcoxon signed-rank test（配对、双尾、α=0.05）。非参数，不假设正态，适配小样本 + 偏态。
2. **效应量**：配对差中位数 + bootstrap 95% CI（B=2000）。
3. **MDE**：若 null，报告最小可检测效应 `(z₀.₉₇₅+z₀.₈)·sd/√M`，否则「没发现」无法解读。

## 机制层证据（独立报告，即使 primary null 必报）

与因果增益**分离**——证明「机制作为代码可观察地工作」：
- (a) 完整组 block 的候选数 vs 失忆组（Factor 1/3：已测 + 同 motif 规则）
- (b) 完整组 family 分数演化（snake/merge 是否被 strike）（Factor 2/3）
- (c) 投影出几条带 evidence_ids 的 Rule（Factor 3 可审计）
- (d) Evolver pivot_recommendation 触发次数（Factor 4）

## 判据

- p < 0.05 且配对差中位数 > 0 → **positive**：honest-boundary「有效性未对照」→「已对照」。
- p ≥ 0.05 → **null**：诚实报告 null + MDE + 机制层证据；claim 变「机制已实现 + 跨领域跑通 + 对照未检出增益」。
- 全量未跑完 → **保底**：至少 claim「跨领域验证」（机制在新领域端到端跑通）。

## 关于 Factor 4 的诚实修正（数据驱动，非预注册后改）

预实验发现：2048 大棋盘（6×6）对策略**更有利**（空间多、分数天花板更高），不存在量化领域的「换池塘救活死策略」现象。因此本实验**不 claim** Factor 4 的换池塘叙事；Factor 4 在 2048 的可观察证据是 Evolver 的 pivot_recommendation 触发（family struck + motif 重复失败），是同一机制的不同表现。

## 装置修正（smoke 后、正式跑前 — 2026-06-30）

三处 smoke（M=1/M=3）暴露的**装置缺陷**，在跑正式 M=30 前修正。这些是实验装置问题（非结果驱动），修正并公开记录符合预注册精神：
1. **候选池跨 round 全 unique**：原固定 archetype 每 round 重复 → 完整组 block 已测好候选反被惩罚（指标被重测混淆）。修正：archetype 加小 jitter，body 跨 round 唯一。这样两组都不重测，唯一区别是 family/motif 导向。
2. **WARMUP=2 预热期**：原全程 max_execute=3 → engine 导向后避开 snake → snake 从不被执行 → 无失败记录 → 规则不投影（chicken-and-egg）。修正：前 2 round 执行全部池（探索），让每个 family 积累失败证据；后 6 round 导向。
3. **K: 20 → 10**：加速（36min→18min）。K=3 已能区分 corner vs snake，K=10 区分度充足。
4. **lookahead depth: 混合{0,1} → 全 0（贪心评估）**：family 信号在 depth=0 已验证保留（corner/space 达 1024 约 11/30，snake/merge 约 0/30）；去掉 depth=1 expectimax 把单局成本从 ~100ms 降到 ~10ms，全量从 ~48min 降到 ~5min。对照逻辑（导向 vs 随机）与 depth 无关。

## 不可事后改的承诺

1. primary 指标、检验、M、H、WARMUP 锁定后不改。
2. 不因结果不显著而换载体/换阈值/增 M 重跑。
3. 无论结果如何，写入 examples/case-study-2048-ablation.md 并更新 honest-boundary。
