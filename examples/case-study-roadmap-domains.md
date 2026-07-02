# 案例研究：三个 Roadmap 场景的验证 — SQL / 代码生成 / RAG

> 评委问"Roadmap 的场景能不能做？"——我们做完了三个。从规划变成了已验证。
> 配图：[demo/09](../demo/09-sql-evolution.zh.html)（SQL）· [demo/10](../demo/10-codegen-evolution.zh.html)（代码）· [demo/11](../demo/11-rag-evolution.zh.html)（RAG）

## 为什么做这三个

符号回归和正则合成证明了"agent 能从成功里造新东西"——但它们是**搜索任务**（猜公式、猜规则）。评委的下一个问题是：**"生产相关的场景呢？我每天写的 SQL、代码、RAG，能用吗？"**

我们挑了三个最常见的生产场景，全部用同一套引擎接入，验证进化链是否可观察。

## 共同模式：三个领域都是"修复链"

和符号回归的"加性嫁接"（公式越长越接近）不同，这三个领域的进化方向是**"收紧修复"**——从一个有问题的版本出发，每一步修掉一个缺陷。

| 领域 | 起点 | 终点 | 进化步数 | graft 操作 |
|---|---|---|---|---|
| **SQL** | cost=24（4 个反模式） | cost=1（最优） | 3 步 | +ON / *→id / +LIMIT |
| **代码生成** | score=0.25（1/4 测试过） | score=1.00（全过） | 1 步 | x*2→x**2 |
| **RAG** | score=0.00（全错配置） | score=1.00（最优） | 5 步 | chunk→150 / th→0.7 / k→4 / +rerank / +expand |

## 领域一：SQL 查询优化

### 进化链
```
SELECT * FROM orders JOIN customers                          cost=24.0
  → graft: +ON (消除笛卡尔积)
SELECT * FROM orders JOIN customers ON orders.id=...         cost=8.0
  → graft: *→id (SELECT * 改 SELECT id)
SELECT id FROM orders JOIN customers ON ...                  cost=3.0
  → graft: +LIMIT
SELECT id FROM orders JOIN customers ON ... LIMIT 1          cost=1.0 ✓
```

### graft 操作是真实 SQL 优化手段
- `+ON`：给 JOIN 加连接条件（DBA 每天做的事）
- `*→id`：指定列替代 SELECT *（减少 I/O）
- `+LIMIT`：限制结果集

### 评估器
代价模型基于反模式检测（SELECT */笛卡尔 JOIN/前缀 LIKE 等），非真实执行计划。这是简化版——真实 DB 的代价取决于数据分布、索引、统计信息。

## 领域二：代码生成

### 进化链（两条路径修复同一个 bug）
```
路径一: sum(x*2 for x in lst)    score=0.25  → graft x*2→x**2 → sum(x**2 for x in lst)  score=1.00 ✓
路径二: sum(x for x in lst)      score=0.50  → graft +**2    → sum(x**2 for x in lst)  score=1.00 ✓
```

### 评估器
用 Python `exec` 执行候选代码，跑测试用例——能抓语义错误（TypeError/NameError/wrong_answer），不只是语法错误。

### 和 LLM 的配合
引擎不替代 LLM——它帮 LLM 避免重复犯错。LLM 生成候选，引擎屏蔽已知会错的写法，记录失败模式，下一轮 LLM 自动跳过。

## 领域三：RAG 检索

### 进化链
```
chunk=1000, no rerank, th=0.3, k=20     score=0.00 (全错)
  → graft: chunk 1000→150               score=0.35
  → graft: threshold 0.3→0.7            score=0.60
  → graft: top_k 20→4                   score=0.80
  → graft: +rerank                      score=0.95
  → graft: +expand                      score=1.00 ✓
```

### 关键洞察
RAG 的进化空间**不是"选关键词"**（太粗——一个关键词就拉满），是**"调检索流水线的结构"**（分块大小/重排序/阈值/召回数/查询扩展）。5 个参数各有最优区间，从全错到最优有连续梯度。

### 评估器
基于 RAG best practices 的规则模拟，非真实 embedding 检索。

## 这证明了 / 没证明什么

- ✅ **证明了**：同一套引擎在三个生产相关场景上跑通，进化链清晰可观察；SQL/代码/RAG 都从 Roadmap 变成了已验证。
- ⚠️ **局限**：三个领域都用**简化评估器**（规则估算/玩具测试用例），非真实生产环境。SQL 是规则代价模型非执行计划，代码是 LeetCode easy 非生产代码库，RAG 是规则模拟非真实向量库。
- 🧭 **定位**：这三个领域的价值不是"最强进化案例"（那是符号回归），而是**"这套机制能接入你每天用的场景"**的直接证据。生产级集成需要对接真实编译/测试/检索流水线，但引擎的 adapter 协议已经验证可行。
