# Factor 2：给搜索打分，不是给候选打分

> 别只评估每个候选好不好——评估*哪个方向值得继续搜*。给策略打分，不是给解打分。

## 动机

标准优化（含贝叶斯优化）给候选打分、挑最好的。它永远学不到*"这里 technical 因子通过率最低——先搜 profitability。"* 搜索循环里持久的知识是 meta 的：哪些 family、维度、结构真的有回报。捕获它就是策略空间上的元学习——比候选打分高一个层次。

这是区分"一个会跑的 agent"和"一个越跑越好的 agent"的 factor。候选打分告诉你试什么；搜索策略打分告诉你往哪看。

## 案例（真实领域，脱敏）

`score_families` 按 `0.5·命中率 + 0.2·近期性 + 0.3·新鲜度` 给经济族排序，带 strike 规则（≥ N 次尝试、零 candidate → 分数 −1，整体排除）。`technical` 经验上通过率最低，所以冷启动排序自动把它放最后——没有任何人硬编码"避开 technical"。agent 从自己的账本学到这个顺序。

## 核心原语

`MetaLearner.score_families`（`core/meta_learner.py`）——从 `Memory` 账本给搜索分支打分，把生成导向高 EV 方向。

```python
from core.meta_learner import MetaLearner

ml = MetaLearner(strike_threshold=5)
scores = ml.score_families(mem, universe="TOP3000", known_families=["technical", "profitability", ...])
# {'profitability': 0.61, 'analyst': 0.55, ..., 'technical': -1.0}  ← struck，停止搜索
```

被 strike 的分支（−1.0）在引擎生成任何候选之前就被排除——搜索预算花在高 EV 方向上。

## 反模式

只给候选打分的优化反复进入低产区域，因为它没有"按方向的产出"记忆；每次运行都像第一次。一个只打分候选的循环是"逐个聪明、整体犯傻"。

## 跨领域

测试用例生成：给哪些*属性类别*（边界 / 等价 / 错误路径）找到过 bug 打分，不只是哪个单个测试好。超参搜索：给哪些*模型族*（GBM / DNN / 线性）在这类数据集上有回报打分。meta 层永远是"哪个分支值得更多样本"。

## 诚实价值层

**已观察，未对照。** 提升搜索*质量*在实践中是真的，但它的可测收益必须用一个我们跑不了的对照来和 in-context learning 隔离。我们 claim 相关性（family 排序跟踪了经验通过率），不 claim 因果。
