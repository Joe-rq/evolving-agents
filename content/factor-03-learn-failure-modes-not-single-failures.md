# Factor 3：学失败模式，不是单个失败

> 从一次失败降权整个类——别只屏蔽那一个候选。

## 动机

屏蔽单个死候选是浅的：它的兄弟和变体继续烧配额。一次自相关失败的持久教训通常是整个 motif 的属性（比如"close 分母的收益信号太拥挤"），不是某一个表达式的。从单个实例学到类，是真正样本效率的来源——一次失败教会你一个邻域。

## 案例（真实领域，脱敏）

一次混合 `operating_income/close + FCF/close` 因子的自相关 FAIL 之后，整个 close-yield motif 类被降权（`operating_cashflow_close_mix` −0.8、`cashflow_close_yield` −0.65、`operating_income_close_yield` −0.35），把正交的 sentiment/growth 探针推到拥挤变体前面。惩罚是从账本*投影*出来的，靠 `strategy_memory.project_strategy_rules`——没有手写规则，从观察到的失败里 agent 自作（commit `3a38a52`）。

## 核心原语

两块，在 `core/rules.py`：

- `Rule` / `RuleSpec`——一条声明式规则带 `motif`、`action`（block/penalize/cooldown）、`score_adjustment`，关键的是还有 `confidence` + `evidence_ids`。置信度随证据数增长；evidence id 把规则追回到*哪几次具体失败*诱发了它。
- `project_rules(attempts, specs)`——通过领域的 `RuleSpec` 把账本转成 `Rule`。adapter 拥有*哪些* motif、*多狠*（领域 IP）；引擎拥有投影机制。

```python
from core.rules import RuleSpec, project_rules

specs = [RuleSpec(motif="close_yield", evidence_kind="corr_failed",
                  min_evidence=1, action="block", adjustment=-0.8, reason="crowded")]
rules = mem.project_rules(specs, universe="TOP3000")
# Rule(motif="close_yield", action="block", confidence=0.55,
#     evidence_ids=("cy_expr_1", "cy_expr_2"))  ← 可审计
```

可审计的 `evidence_ids` 是诚实的优势：当引擎屏蔽一个候选时，它能回答*"因为这几条具体的历史失败"*，不是"信我"。

## 反模式

按候选的黑名单——同一个 motif 没测过的变体继续一个个烧配额，直到每个被独立拒绝。一次失败应该教你一个类，不只是教你一个实例。

## 跨领域

触发拒答的 prompt：一个坏措辞不该只是被避开——它的*类别*（过长指令、歧义否定）该被降权。崩溃复现：一个失败输入教你输入*形状*（深嵌套、含 unicode）值得类级防护。

## 诚实价值层

**已观察，未对照。** 类级防止比按实例（Factor 1）严格更强，且在账本投影里可观察。但这里的"更强"是结构推理，不是测出来的差值。
