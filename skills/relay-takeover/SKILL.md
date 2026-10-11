---
name: relay-takeover
description: 接力开发中，弱模型在 strong zone 边界停下后由强模型接手：读交接记录，检查弱模型有没有越界，实现 strong zone 或处理意外情况，然后交还执行。配合 /relay-tickets 使用。
disable-model-invocation: true
---

# Relay Takeover

用户会传入一条 ticket 的路径或编号。这条 ticket 应该处于 `Status: needs-strong`，由 `/relay-tickets` 标注过。relay 的规则和 ticket 模板见仓库里的 `docs/agents/relay.md`。

## 流程

### 1. 读状态，不重读全部

- 读 ticket 正文，以及 `## Comments` 下最新一条交接记录。
- 读 executor 开工以来的 `git log` 和 `git diff`，只看和这条 ticket 相关的部分。

交接记录加 diff 就够你接手了。不要从头通读整个项目：省下这部分 token 正是接力开发的意义。

### 2. 检查越界

弱模型有时会忘记停下，直接动手写了 strong zone。对照 diff 检查每个未勾选的 strong zone：

- 没碰过：正常。
- 已经写了：当作草稿审查，对就保留，不对就重写。这不算事故，接手本来就要兜住这种情况。

同时检查已完成的部分有没有偏离 ticket，比如悄悄简化了实现、改了接口、换了做法。发现就一并修正，并记进第 4 步的记录里。

### 3. 处理停下的原因

- **停在 strong zone**：按 ticket 和相关 ADR 里的既定决策实现它，尽可能用 `/tdd`。实现完勾选这条 strong zone。
- **停在执行规则第 4 条（意外情况）**：先判断是执行问题还是计划问题。
    - 执行问题：直接修。
    - 计划问题：修改本 ticket。如果影响到后续 tickets，一并修改，并告诉用户改了哪几条。如果这个新决定满足 ADR 的三个条件（见 `/domain-modeling`），提议记一条 ADR。

### 4. 交还

- 运行这条 ticket 相关的测试，确认通过。
- 提交。
- 把 `Status:` 改回 `ready-for-agent`；如果整条 ticket 已经完成，按 tracker 的约定标记完成。
- 在 `## Comments` 下追加一条记录：做了什么、修正了哪些偏离、executor 接下来从哪一步继续。
- 告诉用户可以切回 executor 了。
