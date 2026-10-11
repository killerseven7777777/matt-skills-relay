# 接力开发（relay）

本仓库按接力方式开发：强模型（planner）在写文档阶段做完所有决策，并划出必须由自己亲手实现的区域（strong zone）；弱模型（executor）按 ticket 干活，走到 strong zone 边界就停下，由用户切换到强模型接手，强模型写完再交还。

## 给拆分 ticket 的模型

任何技能往 issue tracker 发布或修改实现类 ticket 时，每条 ticket 都必须带上下面「Ticket 段落模板」里的三部分：`**Executor:**` 行、`## Strong zones` 段、`## 执行规则` 段，放在验收标准之后。用 `/to-tickets` 拆分时，在发布前补上；`/relay-tickets` 会自动做这件事。

### 怎么划 strong zone

strong zone 是「已经定好，但弱模型写不好」的区域，不是留给以后再定的问题。

适合划进去的：

- 不变式难以用测试完全覆盖的代码：并发、事务、缓存一致性、状态机转移
- 正确性靠推理而不是靠套模式的算法
- 被多个 ticket 共享、写错后返工面很大的核心接口和数据结构
- 安全相关：鉴权、输入校验、密钥处理
- 需要读懂大量现有代码才能改对的地方

不该划进去的：样板代码、照着已有模式重复的修改、有完整测试兜底的简单逻辑。

粒度二选一：整条 ticket 都难就写 `Executor: strong`；只有某一段难就写 `Executor: weak`，并逐条列出 strong zone。

边界必须写成弱模型能机械识别的东西：文件、函数或类名，或者「在做 XX 之前停下」。不要写「复杂的部分」「核心逻辑」这种需要判断才能识别的描述。划分理由满足 ADR 条件时记一条 ADR，并在条目里引用。

## 给执行 ticket 的模型

- 开工前先确认 ticket 里有 `## Strong zones` 段。**没有就说明这条 ticket 没有标注过：不要开工，告诉用户「这条 ticket 缺少 relay 标注，请强模型补上」。**
- 有的话，严格遵守 ticket 里的 `## 执行规则`。

## Ticket 段落模板

<relay-ticket-sections>

**Executor:** weak

## Strong zones

- [ ] SZ1：`<文件>` 里的 `<函数名>()` 整个函数。原因：<一句话>，见 ADR-NNNN。
- [ ] SZ2：在 <某个具体动作> 之前停下。原因：<一句话>。

（`Executor: strong` 或没有 strong zone 时，这一段写「无」，但段落标题保留。）

## 执行规则

写给执行这条 ticket 的模型：

1. 开工前通读本 ticket，包括 Strong zones。
2. 每完成一个验收项，回看一遍 Strong zones，再开始下一项。
3. 下一步会进入任何未勾选的 strong zone 时，立即停下：提交已完成的部分，把 `Status:` 改成 `needs-strong`，在 `## Comments` 下追加一条交接记录，然后告诉用户「已到 SZn，请强模型接手」。
4. 遇到以下任一情况，也按第 3 条停下：同一个测试改了两次仍不通过；需要修改本 ticket 范围以外的文件；实际代码与 ticket 描述的接口不符；需要新增依赖；验收标准有不止一种理解。
5. 不要修改验收测试本身。认为测试有问题时，停下并报告。

交接记录格式：

- 停在：SZn，或第 4 条中的哪种情况
- 已完成：哪些验收项，附 commit
- 现状：一两句话；遇到报错就附上原始输出的关键几行

</relay-ticket-sections>
