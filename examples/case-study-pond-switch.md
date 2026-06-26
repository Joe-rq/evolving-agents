# 案例研究：换结构 — TOP3000 → TOP1000

> 一次真实的换结构事件：agent 提议换池塘，去救活一个因*拥挤*而非*质量*濒死的因子。

这是 demo 唯一最硬的证据。每个数字都对照本地 scoreboard 核验过（50 条记录的数据集，私有宿主 repo，2026-06）。

## 因子（一个表达式 body）

```
0.5*group_rank(ts_rank(operating_income/close,126),industry)
+ 0.5*group_rank(ts_rank(free_cash_flow_reported_value/close,126),industry)
```

## 两个池塘

| 池塘 | 状态 | Sharpe | self_corr | 结果 |
|---|---|---|---|---|
| TOP3000（大盘） | rejected | **2.15** | **0.78** | SELF_CORR_FAIL |
| TOP1000（中小盘） | **submitted** | **2.15** | **0.68** | checks clear |

**因子没变。Sharpe 没变（两边都 2.15）。唯一动的是 self_corr——拥挤度指标——从 0.78（太拥挤 → fail）到 0.68（clear → pass）。**

这是 Factor 4 最干净的例证：问题是*环境*，不是*因子*。在 TOP3000 里更努力地调 decay/窗口/中性化永远修不好一个拥挤问题——agent 拒绝去试，转而提议换池塘。

## 诚实细节：TOP1000 不是"换了就活"

agent **没有**第一次就猜对。在 TOP1000 它跑了同一个 body 的几个变体：

| 变体 | self_corr | 结果 |
|---|---|---|
| A | 0.92 | SELF_CORR_FAIL |
| B | 0.83 | SELF_CORR_FAIL |
| C | **0.68** | pass → submitted |

换池塘*把拥挤基线降到了让"通过"变得可能的程度*——但只有一个具体变体过了。agent 仍得在新池塘里搜。我们公开披露这点：这不是"换了就复活"的童话。

## 谁决定了什么（人机协同，已披露）

- **agent** 积累失败记忆（yield / sentiment / growth 在 TOP3000 全 fail）并产出 evolution action：*"别只改窗口——换数据源 / 经济族。"*
- **agent** 提议把 universe 切换作为结构性 pivot。
- **人** 批准了切换（commit `b38ce00`，2026-06-24）。
- **agent** 随后为新池塘自动应用结构松弛（commit `23ac8a1`：TOP1000 放松 TOP3000 强制的 leverage/ROA 硬屏蔽）。

这是 **agent 提议 / 人批准**，不是自主的。公开披露。

## 时间线（commit 链，2026-06）

| commit | 做了什么 | 动作方 |
|---|---|---|
| `e1937ed` | universe 级记忆（TOP3000 疤痕不污染 TOP1000） | agent 系统 |
| `3a38a52` | self-corr 失败后 close-yield motif 软惩罚 | agent 自作 |
| `b38ce00` | 切换默认 universe TOP3000 → TOP1000 | **agent 提议，人批准** |
| `23ac8a1` | TOP1000 结构松弛 + 探索通道 | agent 系统 |
| 06-24 | 因子在 TOP1000 通过（self_corr 0.68）→ submitted | — |

## 这证明了什么 / 没证明什么

- ✅ **证明了**：一次真实的换结构事件发生了；"换环境、不调参数"这个洞察在这里是对的；因子的质量（Sharpe 2.15）和环境无关。
- ❌ **没证明**：进化机制*导致*了这次胜利（没有失忆组 vs 完整组对照——见 [诚实边界](../content/honest-boundary.md)）；它在这一个事件之外能泛化。

## demo 钩子（pitch 那句）

> "同一条因子。同一个 Sharpe——2.15。在 TOP3000 它死了：self_corr 0.78，太拥挤。agent 没让我调得更狠，它让我换池塘。在 TOP1000，self_corr 降到 0.68，它上线了。**因子从来不是问题。池塘才是。**"
