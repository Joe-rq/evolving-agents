# 10 分钟复现路径

这条路径用于第一次 clone 后快速确认：项目能安装、测试能跑、2048 对照装置能产出结果表。

## 1. 准备环境

```bash
git clone https://github.com/Joe-rq/evolving-agents.git
cd evolving-agents
uv venv
uv sync --dev
```

## 2. 跑最小测试

```bash
uv run pytest
```

覆盖范围：

- `Memory`：append-only 账本与 universe 隔离
- `Rule`：失败证据投影、`evidence_ids`、block/penalize 行为
- `Engine.run`：评分、执行、记录、已测候选屏蔽
- `2048`：完整组与失忆组的最小烟测

## 3. 跑快速复现

```bash
uv run evolving-agents-smoke
```

这会执行一个很小的 2048 ablation，并写出：

```text
experiments/_smoke_result.json
```

终端会打印 `=== RESULT ===`，包含 primary 指标、verdict 和机制层计数。
这个 smoke 只验证端到端连通性；因为参数很小，部分机制计数可能为 0。完整机制证据看预注册配置。

## 4. 跑预注册配置

```bash
uv run evolving-agents-ablation -M 30 -R 8 -K 20 --size 4
```

结果写入：

```text
experiments/_ablation_result.json
```

快速调试时可以缩小参数：

```bash
uv run evolving-agents-ablation -M 1 -R 4 -K 2 --size 4 --out experiments/_quick_result.json
```

## 读结果

重点看三行：

- `primary`：完整组减失忆组的 tail4 mean log2(max_tile)
- `verdict`：按预注册 alpha=0.05 判定 `POSITIVE` 或 `NULL`
- `mechanism`：block、pivot、rule 等机制层证据
