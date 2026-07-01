# 痕进 · evolving-agents

> **失败留痕，凭痕而进。**
> 造能**从自己的失败里学习**的 agent 的一组原则。
> *致敬 [12-factor agents](https://github.com/humanlayer/12-factor-agents)。*

> 参赛名 **痕进**（Scarforge）；仓库 evolving-agents 是其开源引擎。

12-factor agents 讲的是怎么造**可靠**的 agent。
这个项目讲的是怎么造会**进化**的 agent——靠记住什么失败了，在搜索这件事上越做越好，而不是每次都从零开始。

> ⚠️ **WIP** — 黑客松构建（2026-06）。核心引擎能在 mock 领域跑通；一个真实领域在私有仓库验证过。

## 核心论点

大多数"agentic"搜索循环其实不会学习。它们要么：
- 每次从零开始（同样的死路反复探索），要么
- 把历史塞进 prompt 碰运气（RAG 式召回——我们实测发现对常规场景零增量）。

真正会越变越好的 agent 做的事不一样：**它们给搜索策略本身打分，学习失败*模式*而非单个失败，卡住时换结构而非调参数。** 这个项目给这些机制命名、实现成领域无关的引擎，并在一个真实领域上验证架构。

## 这里有什么——三条腿

1. **引擎**（`core/`）——领域无关的自进化循环：memory / rules / meta_learner / evolver / novelty，由 `engine.py` 编排。配 mock adapter 可独立跑通。
2. **一个真实领域**（私有）——一个量化因子挖掘的宿主实现了 5 个 adapter 协议、对接真实数据。机制是在这里**观察到的**，不是构造出来的。脱敏证据 → [案例研究](examples/case-study-pond-switch.md)。
3. **诚实披露 + 公开对照 + 可观察进化**——每条 claim 都有边界。我们说机制做了什么，也公开说我们*证明不了*什么；并在公开的 2048 领域跑了一个预注册的失忆组对照——结果 **null（p=0.079）**：机制可观察地工作，但增益未被统计证明。我们还在符号回归领域展示了**生成器从成功嫁接出新公式的可观察进化**——回答"agent 能不能造出新东西"（能），但同样是单轨迹、非统计证明。→ [诚实声明边界](content/honest-boundary.md) · [2048 对照案例](examples/case-study-2048-ablation.md) · [符号回归进化案例](examples/case-study-symreg-evolution.md)

## 5 个 Factor

| # | Factor |
|---|---|
| 1 | [记住你的失败](content/factor-01-remember-your-failures.md)（Remember your failures） |
| 2 | [给搜索打分，不是给候选打分](content/factor-02-score-the-search-not-the-candidate.md)（Score the search, not the candidate） |
| 3 | [学失败模式，不是单个失败](content/factor-03-learn-failure-modes-not-single-failures.md)（Learn failure modes, not single failures） |
| 4 | [换结构，不是调参数](content/factor-04-pivot-structure-not-tactics.md)（Pivot structure, not tactics） |
| 5 | [追新颖，避拥挤](content/factor-05-seek-novelty-avoid-crowding.md)（Seek novelty, avoid crowding） |

**五个机制都实现了，都产生了可观察的进化行为。** 量化领域（私有）的失忆组对照因数据量太小跑不了；我们在公开的 2048 领域补上了它——**结果 null（p=0.079）**：机制作为代码可观察地工作（block / pivot / 规则全部触发，失忆组为零），但学习增益未被统计证明。我们区分「机制存在」与「机制有效」，如实报告 null。完整披露 → [诚实声明边界](content/honest-boundary.md)。

## 仓库布局

```
content/      # 5 篇 factor 文档 + honest-boundary（CC BY-SA 4.0）
core/         # 领域无关引擎（Apache 2.0）：
              #   protocols · memory · rules · meta_learner · evolver · novelty · engine
adapters/     # reference adapter：mock（玩具）+ game2048（公开对照）+ maze（机制接入，未 claim 进化）+ symreg（可观察进化）；
              #   真实量化 adapter 在私有宿主
experiments/  # 2048 失忆组对照（ablation_runner）+ 符号回归进化轨迹（symreg_evolution，2 个目标）；纯 stdlib
examples/     # 脱敏案例研究（换池塘 + 2048 对照 + 符号回归进化 + 迷宫失败记录）
demo/         # demo 图（01-05 对照结果 + 06 符号回归进化）
img/          # 图
```

## 定位（以及它*不是*什么）

自进化 agent 是个拥挤的赛道——[EvoMap/evolver](https://github.com/EvoMap/evolver)、[AgentEvolver](https://github.com/modelscope/AgentEvolver)、ExpeL、Reflexion、Voyager 都沾边。这个项目不 claim 机制是新的。

它提供的是：
- **引擎，不是平台。** EvoMap 是 A2A 跨节点经验共享的*平台*（我们用过它的 memory 层）。evolving-agents 是本地、可嵌入的*引擎*——不同的抽象层，更简单，用五个命名的 factor 可教。
- **可审计的规则。** 每个候选受到的惩罚都能追到具体的历史失败（`evidence_ids`），不是黑箱"agent 学到了"。
- **有边界的诚实。** 我们不营销自己证明不了的学习曲线。诚实边界*本身*就是差异化——大多数"自进化"demo 回答不了"这是进化还是 in-context learning？"

## 状态与诚实边界

在**三个领域**验证过：量化因子挖掘（私有，真实案例）+ 2048（公开，带失忆组对照）+ 符号回归（公开，可观察的生成器进化）。2048 对照结果 null（p=0.079）——机制可观察地工作，但有效性增益未被统计证明；符号回归展示了生成器从成功嫁接出新公式的可观察进化，但是单轨迹、非统计证明。跨领域泛化仍是 roadmap，不是 claim。→ [诚实声明边界](content/honest-boundary.md)

## License

- 代码（`core/`、`adapters/`）：Apache 2.0 — 见 [LICENSE](LICENSE)
- 内容（`content/`）：CC BY-SA 4.0 — 见 [content/LICENSE.md](content/LICENSE.md)
