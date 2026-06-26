# Factor 4：换结构，不调参数

> 反复卡住时，换环境或结构框架——不是调参数。并且记忆要跨环境隔离。

## 动机

当一个搜索在一个框架里停滞，决定性的收益通常来自纠正*环境*本身，不是在现有框架里更努力地调策略（cf. Deli_AutoResearch：*"换结构，不调参数"*）。具体说：如果一个信号在一个市场反复失败，问题可能是市场的性质——不是信号。在死池塘里调 decay/窗口/中性化，正是这个 factor 要打破的失败模式。

这是项目里叙事最强的 factor——也老实说，是和人机协同判断纠缠最深的。

## 案例（真实领域，脱敏）

一个因子表达式 body：

```
0.5*group_rank(ts_rank(operating_income/close,126),industry)
+ 0.5*group_rank(ts_rank(free_cash_flow_reported_value/close,126),industry)
```

| 池塘 | 状态 | Sharpe | self_corr | 结果 |
|---|---|---|---|---|
| TOP3000（大盘） | rejected | 2.15 | 0.78 | SELF_CORR_FAIL（拥挤） |
| TOP1000（中小盘） | **submitted** | 2.15 | 0.68 | checks clear |

**因子没变。Sharpe 没变（两边都 2.15）。唯一动的是 self_corr——拥挤度指标。** 在 TOP3000 里调参数永远修不好一个拥挤问题。agent 的洞察是*"不是因子死了——是池塘对它不对"*，于是它提议换池塘。完整时间线 + 诚实的"不是换了就活"细节 → [案例研究](../examples/case-study-pond-switch.md)。

## 核心原语

`Evolver`（`core/evolver.py`）——检测框架耗尽（N 个策略类被 strike，或一个失败 motif 在当前 universe 命中 ≥ 阈值次）并产出一条*建议*。它**不**决定换到哪；那留给 adapter / 人。

```python
from core.evolver import Evolver

ev = Evolver(family_strike_count=2, motif_strike_count=3)
if ev.should_pivot(mem, "TOP3000", family_scores):
    print(ev.pivot_recommendation(mem, "TOP3000", family_scores))
    # "2 个策略类在 'TOP3000' 被 strike（cashflow, sentiment）——
    #  换结构框架，不是调参数。"
```

这个拆分是故意的：**agent 提议 / 人批准**。agent 观察到了停滞、说出了结构性原因；人放行了 universe 切换。公开披露——这不是自主的。

独立印证：另一个项目发现 INDUSTRY（vs SUBINDUSTRY）中性化是关键的结构切换——同一个"换结构"模式，换了个参数。

## 反模式

在死池塘里继续调 decay / 窗口 / 中性化——越陷越深进局部最优，而不是质疑框架。调参数感觉很有产出（你"在做事"），但正是陷阱。

## 跨领域

超参搜索卡在一个模型族上：修法可能是换*数据表示*，不是调模型。prompt 调优卡住：换*任务分解*，不是改措辞。信号永远是"一个框架里反复停滞"→ 质疑框架。

## 诚实价值层

**已观察，未对照——且人机协同。** 这个 factor *叙事上*最强（换池塘是真的，带验证过的数字），但带一个诚实边界：agent **提议**了 pivot，人 **批准**了。质量提升和机制相关，没被因果隔离。我们披露这个，而不是把它打扮成自主自进化。
