# Factor 5：追新颖，避拥挤

> 偏好新颖而非重复开采，并且即使分数低也要保护正交探索。

## 动机

纯 exploit 会收敛到局部最优——认知循环这个失败模式：连续迭代尝试相似方向、收益递减。一个自进化搜索必须主动避免重新找到已有的东西，并为结构不同的候选保留一条探索通道。没有它，Factor 1–3（关于*避开已知坏*）会把搜索坍缩到它找到的第一个还行的区域。

## 案例（真实领域，脱敏）

- **新颖性分数**——候选与历史的字段重叠度；约占候选分数的 30%，所以一个被充分探索的方向会自然衰减。
- **拥挤惩罚**——motif 已经产出过 ACTIVE alpha 的候选被惩罚；重新找到一个已知赢家是低价值的。
- **探索通道**——为低分但*正交*标记的候选降低执行分数门槛，让一个结构不同的探针仍能浮出来跑。

## 核心原语

`core/novelty.py`——三个函数，都是对已提取的 features/motifs 做纯打分：

```python
from core.novelty import novelty_score, crowding_penalty, qualifies_exploration_lane

nov = novelty_score(candidate_features, mem, universe="TOP3000")     # 1.0 = 全新
pen = crowding_penalty(candidate_motif, mem, universe="TOP3000")     # <0 如果 motif 已产出过
run = qualifies_exploration_lane(score=0.18, main_threshold=0.20,
                                  exploration_threshold=0.15, is_orthogonal=True)  # True
```

探索通道是对抗贪婪 exploit 的受控逃生口：一个没过主门槛的候选，如果结构正交且过了更低的门槛，仍可能跑。

## 反模式

贪婪 exploit——认知循环、收益递减、搜索永远逃不出自己的簇。任何新东西都被罚为"分数比已有的低"，于是新的永远不跑。

## 跨领域

任何 explore/exploit 张力：测试用例生成（别一直发同一个 bug 类）、配置搜索（为未见过的区域预留预算）、研究 agent（Deli_AutoResearch 的"方向多样性"——新方向必须和每个试过的都不同）。机制都一样：给新颖打分、惩罚拥挤、保护正交。

## 诚实价值层

**已观察，未对照。** explore/exploit 平衡在原则上有价值，但它的定量贡献和 MetaLearner（Factor 2）纠缠，难单独归因。我们 claim 它已实现、可观察，不 claim 被测过。
