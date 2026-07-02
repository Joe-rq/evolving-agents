乔木计划

PROJECT NAME

# 痕进

**Scarforge**
/
Evolving Agents

一个给 Agent 装上的进化层：把失败变成下一次行动的约束。

乔木计划 · Scarforge / evolving-agents01 / 10

乔木计划

THE PROMISE

# 失败留痕， 凭痕而进。

痕进不是让 Agent 背更多上下文，而是让它学会长记性：错在哪里、为什么错、下次该避开哪条路，都留下可追溯的痕迹。

乔木计划 · roadshow preview02 / 10

THE PROBLEM

## 今天的 Agent，太容易反复犯同一个错。

客服、代码、搜索、研究都一样：一次失败修掉了，下一次换个壳又回来。问题不只是记忆不够，而是失败没有进入决策系统。

**只记成功**正确答案进了记忆库，错误路径却被当成垃圾清掉。

**只调参数**prompt 改来改去，但真正该换的是任务结构和搜索路径。

**只追最优**大家挤向看起来最好的方向，新路线还没被试就被放弃。

乔木计划 · failure becomes signal03 / 10

THE THESIS

## 不是修 prompt。 是让失败变成系统资产。

一次失败如果只停在对话窗口里，就是噪音；写进账本、归成模式、投影成规则、影响下一轮搜索，它才开始产生复利。

01

### 记住失败

失败持久化，别把配额烧在已知死路上。

02

### 评分搜索

评估“怎么找答案”，而不只评估最后答案。

03

### 学习模式

从“这次错了”升级到“这类情况都会错”。

04

### 换结构

方法反复失败时，换路径，不在旧路上微调。

05

### 避拥挤

奖励新颖探索，防止集体挤进局部最优。

乔木计划 · five mechanisms, one loop04 / 10

FIRST SANDBOX

## 交易不是终点， 只是第一个可验证沙盘。

量化交易是第一个沙盘：反馈明确，失败可追溯。这个案例证明的不是“会交易”，而是 Agent 学会了换搜索结构。

TOP3000 / 大盘池塘

Sharpe**2.15**

self\_corr**0.78**

result**FAIL**

TOP1000 / 中小盘池塘

Sharpe**2.15**

self\_corr**0.68**

result**PASS**

agent proposes→human approves

**关键转折**答案没变，环境变了。

乔木计划 · first sandbox, not final domain05 / 10

AUDITABILITY

## 为什么这不是黑箱学习？ 因为每条规则都能追到证据。

PENALIZE
cashflow\_close\_yield
scope: TOP3000

score adjustment**-0.65**

confidence**0.75**

evidence ids**3**

真正的差异不在“Agent 好像学到了”，而在它能回答：是哪几次具体失败，教会了这条惩罚。

乔木计划 · rules with evidence, not vibes06 / 10

PRODUCT SHAPE

## 它是一个可嵌入的进化层， 不是又一个 Agent 平台。

你的 Agent 继续负责做事；痕进负责让它从失败中更新搜索方式。换领域时只换 adapter，进化循环留在 core。

### core / universal loop

通用进化逻辑：记录失败、学习模式、更新规则、奖励新颖探索。

memory.py

meta\_learner.py

rules.py

### adapter / domain knowledge

领域知识薄层：解释什么叫失败、什么叫好结果、什么动作能执行。

classify

motif\_of

execute

乔木计划 · evolution layer, not platform07 / 10

WHERE IT APPLIES

## 凡是会试错的 Agent， 都需要一套失败进化机制。

量化交易只是第一个沙盘。痕进真正服务的是“可重复试错”的工作流：失败能被定义，反馈能被记录，下一次行动能被改变。

code

### 代码 Agent

编译错误、测试失败被归成模式，下次调整代码结构而不是重复补丁。

ops

### 自动化 Agent

表格、API、浏览器操作失败后，记住哪类输入容易触发问题。

search

### 检索 Agent

搜索结果差时，进化查询路径，而不是只换几个关键词。

tutor

### 教育 Agent

学生反复出错时，识别错误类型，调整讲解顺序和例题。

sim

### 模拟 Agent

在游戏、仿真、策略环境里积累试错痕迹，更新下一轮策略。

乔木计划 · transferable failure evolution08 / 10

HONEST BOUNDARY

## 真正的可信感，来自边界说清楚。

### 我们 claim

- 5 个机制都已实现。
- 观察到一次真实换结构事件。
- 部分学习来自账本投影，不是手写规则。

### 我们不 claim

- 没有有效性的对照证明。
- 没有量化收益曲线。
- 还没有跨领域规模化验证结论。

这不是软弱，这是可信产品该有的边界。我们讲一个可追溯的进化事件，不把它包装成万能神话。

乔木计划 · mechanism + observed behavior + disclosed boundary09 / 10

乔木计划

CLOSING

## 大多数 Agent 把失败当垃圾。 痕进把失败变成下一次行动的路标。

真正的智能，不是第一次就做对，而是第一次做错之后，第二次少走同一条错路。

乔木计划 · Scarforge / evolving-agents10 / 10
