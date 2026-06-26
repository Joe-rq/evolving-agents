# Factor 1：记住你的失败

> 把每一次失败持久化到存储里，不是留在对话记忆中。记忆是所有进化的前提。

## 动机

纯 prompt agent 每次运行都从零开始。它反复探索同一条死路、反复误用同一个字段、反复提交同一个拥挤信号。"在上下文里记住"撑不过一个会话——一旦上下文窗口滚动或压缩触发，教训就没了。进化只有在一件事被写下来之后才开始：写到文件、表、账本里，让它比任何一次运行都活得长。

这是地基 factor：Factor 2–5 都从记忆读、往记忆写。没有持久化，就没有学习。

## 案例（真实领域，脱敏）

`research_state` 表持久化每个 family / 每个 field 的命中率。`scl12_buzz`（Sharpe −0.73）和 `sales_growth`（Sharpe −0.13）被记录为死的，再也不会被当作高质量线索挑出来。`candidate_block_reason` 硬屏蔽任何已测过的候选 body，所以评估配额永远不会被重新烧在一个已知结果上。

## 核心原语

`Memory`（`core/memory.py`）——一个 append-only、按 universe 隔离的 `Attempt` 账本。每条 attempt 带结果，外加 adapter 协议分类出来的东西（family、features、motif、evidence_kinds）。

```python
from core.memory import Memory, Attempt

mem = Memory()
mem.record(Attempt(body="ts_corr(close,volume,5)", universe="TOP3000",
                   success=False, family="technical",
                   motif="pure_ts_corr_volume", evidence_kinds={"weak"}))

# "这个我在这个池塘试过没？" —— 永远不把配额重新烧在已知 body 上
mem.has_tested("ts_corr(close,volume,5)", "TOP3000")  # True
```

universe 隔离（见 Factor 4）意味着一个环境的疤痕不会污染另一个——`has_tested` 是按池塘的。

## 反模式

纯 prompt agent 每次运行都重新踩同一个坑；它唯一的"记忆"就是这一轮上下文窗口里能装下的东西。RAG 式召回（把历史塞进 prompt 碰运气）是同一个反模式的弱化版：它撑得过会话，但我们实测发现对常规场景零增量（见 [诚实边界](honest-boundary.md)）。

## 跨领域

任何搜索可能重复已知坏动作的地方：超参搜索重试 OOM 过的配置、测试生成重新发射会让解析器崩的结构、prompt 调优重发已经被评分拒绝的变体。动作都一样——把失败写下来、按相关上下文隔离、拒绝重试。

## 诚实价值层

**已观察，未对照。** 防止已知失败在原则上是确定性*价值*——失忆组会重新犯完整记忆组已记录的失败。但我们在这里没跑那个对照（机制 2026-06-24 才上线；进化后数据太少）。我们 claim 机制已实现、可观察，不 claim 它的收益被测过。
