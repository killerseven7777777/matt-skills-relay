# matt-skills-relay

中文 | [English](./README.en.md)

给 [Matt Pocock 的工程技能集](https://github.com/mattpocock/skills) 补上两块：

- **`/develop`**：开发流程路由器。开工前、每做完一步、流程卡住时都可以调用，它侦察项目状态，告诉你下一步该走哪个技能。
- **`/relay-tickets` + `/relay-takeover`**：接力开发。强模型把 ticket 写成有序步骤并标出「必须由强模型亲手写」的几步，弱模型按顺序做，走到这几步就停下，由你请强模型接手，写完再交还给弱模型继续。

技能正文是简体中文，术语、技能名和文件名保留英文，所以和英文原版技能集也能直接配合。

> English summary: add-ons for Matt Pocock's skills. `develop` is a router you call throughout development: it inspects your repo and tells you which skill to run next. `relay-tickets` / `relay-takeover` support a planner-executor workflow: a strong model writes each ticket as ordered steps and marks the *strong* steps it must implement itself; a cheaper model works through the steps in order, stops at the first strong step, and the strong model does just that step and hands back. Skill bodies are in Simplified Chinese. Full English README: [README.en.md](./README.en.md).

## 为什么需要接力开发

当今我们倾向于为顶级模型设计精简提示词来部署开发任务。但由于开发过程中有大量普通模型也能完美解决的工作，所以为了节省成本，很多人仍然选择这么干：

- 用 Claude Fable 或 Opus 讨论方案、拆 ticket，再交给 Astra、Sol 这类更快更便宜的模型写代码
- 在 Claude Code 里用强模型规划，然后把执行交给另一个工具里的模型
- 规划用订阅额度，执行走按量计费的便宜模型

问题在于，**计划写在纸上的永远只是一部分**。强模型规划时脑子里有很多没写出来的判断，执行模型碰到难点只能自己补，常见的结果是：悄悄简化实现、按字面硬套、和计划对不上时自己发挥。

一种做法是让强模型把计划写得越来越细，但开发是线性的，难点不可能全部提前解决。`relay` 换了个思路：**强模型在拆 ticket 时就把它写成一串有序步骤，并判断哪几步必须自己写，标成 strong 步骤；弱模型按顺序一步一步做，走到 strong 步骤就停，强模型只做完这几步就交还，弱模型从下一步接着做。**

strong zone 不是「留着以后再定的问题」。所有决策在写文档阶段就已经由强模型做完了，strong zone 是「已经定好，但弱模型写不好」的部分，比如：

- 并发、事务、缓存一致性这类不变式难以用测试完全覆盖的代码
- 正确性靠推理而不是靠套模式的算法
- 被多个 ticket 共享、写错后返工面很大的核心接口
- 鉴权、输入校验这类安全相关代码

## 一次接力是什么样子

假设你在做一个带缓存的导出功能，用 Opus 规划，用 Sol 执行。

1. **Opus：`/relay-tickets`**。按 `/to-tickets` 的方式拆出几条 tracer-bullet ticket，同时给每条定执行者、写成有序步骤、标出 strong 步骤。拆分方案、步骤和 strong zone 一起给你过目、一起批准。其中一条大概长这样：

    ```markdown
    # 03: 导出报表支持分页

    **What to build:** 用户导出大报表时按页拉取，不再一次性加载。
    **Blocked by:** 02
    **Status:** ready-for-agent

    - [ ] 导出接口接受 cursor 参数
    - [ ] 前端分页拉取并拼接结果

    **Executor:** weak

    ## 执行步骤

    - [ ] 1. [weak] 导出接口接受 cursor 参数，先原样透传。
    - [ ] 2. [strong · SZ1] 实现 `encode_cursor()` / `decode_cursor()`。
    - [ ] 3. [weak] 接口改用第 2 步的 cursor 分页。
    - [ ] 4. [weak] 前端分页拉取并拼接结果。

    ## Strong zones

    - SZ1：第 2 步。原因：要和 02 的缓存失效策略对齐，见 ADR-0004。
    - SZ2：触发型。需要修改 `src/cache/` 下任何文件时停下。禁止的绕法：在 `src/export/` 里另写一份缓存逻辑。

    ## 执行规则

    1. 开工前通读本 ticket……
    2. 严格按编号顺序执行，一次只做一步……
    3. 下一步是 `[strong]` 步骤时，立即停下交接。后面还有你能做的 `[weak]` 步骤也不要先做。
    4. 碰到触发条件立即停下，不要绕开……
    ```

2. **Sol：照着 ticket 干活**。做完第 1 步，下一步是 `[strong]`，于是停下：不先去做第 4 步的前端，提交已完成部分，把 `Status:` 改成 `needs-strong`，在 `## Comments` 下留一条交接记录，告诉你「已停在第 2 步（SZ1），请强模型接手」。
3. **Opus：`/relay-takeover 03`**。只读交接记录和 git diff，不重读整个项目。检查 Sol 有没有越界、跳步或绕开，只做第 2 步，跑测试，把状态改回 `ready-for-agent`，交还，写明「从第 3 步继续」。
4. **Sol：从第 3 步继续**，做完剩下的步骤。

为什么要有序步骤：只写「碰到某个文件就停」的话，弱模型会先把能做的全做完，碰到难点时也常常换个文件写一份等价实现，结果一次都没停。我们在真实项目里遇到过：弱模型把 strong zone 要求的回读函数改成在场景文件里直接调接口，设备辅助函数也写进了允许改动的文件，整张单子做完，strong zone 一次都没触发。所以触发型 strong zone 必须同时写出禁止的绕法。

弱模型偶尔还是会忘了停、跳步或绕开。这没关系：`/relay-takeover` 会把这些都当草稿审一遍，对就留，不对就按原定要求重做。

除了 strong zone，执行规则里还有一组客观的兜底条件：同一个测试改两次还不过、需要改 ticket 范围外的文件、接口和描述对不上、需要新增依赖、步骤或验收标准有歧义、上下文快用完。碰到任何一条，弱模型同样停下来交给强模型。这些条件都是能机械判断的，因为弱模型最大的毛病就是不知道自己不会。

## 怎么保证弱模型真的会停

不靠「记得调用某个技能」，而是把规则放在流程一定会经过的地方，四层互相兜底：

1. **入口**：接力模式下用 `/relay-tickets` 代替 `/to-tickets` 拆单。
2. **项目配置挂钩**：第一次在项目里启用时，`/relay-tickets` 会（经你确认后）写入三处：
    - `docs/agents/relay.md`：规则和 ticket 模板的唯一来源，弱模型在别的工具里也读得到
    - `docs/agents/issue-tracker.md` 末尾一节：任何技能发布 ticket 都会读这个文件，所以就算直接用了原版 `/to-tickets`，也会在发布时被拦下来补标注
    - `AGENTS.md` 或 `CLAUDE.md` 里一段 `### Relay execution`
3. **执行侧兜底**：ticket 里缺 `## 执行步骤` 或 `## Strong zones` 段，弱模型就不开工，请你找强模型补标注。
4. **hook**：插件自带一个 `PostToolUse` hook。Claude Code 每次写入 `.scratch/*/issues/*.md` 后，检查 `**Executor:**`、`## 执行步骤`、`## Strong zones`、`## 执行规则` 四部分是否齐全，缺了就提示模型补上（`Status: done` 的 ticket 不查）。

规则写进 ticket 文件本身，而不只写在技能里，是因为执行模型可能根本不在 Claude Code 里跑，看不到 Claude 的技能，但它一定会读自己正在执行的那条 ticket。

## 关于 `/develop`

Matt Pocock 的技能集很好用，但二十多个技能，新手往往不知道现在该用哪个。`/develop` 贯穿整个开发过程：开工前、每做完一步、流程卡住时都可以调用它。它只负责路由，不自己写代码。每次调用它会：

1. 侦察项目状态：git、issue tracker 配置、`CONTEXT.md`、ADR、已有的 spec 和 ticket、是否启用了 relay
2. 对照决策表判断你处在哪一步，给出一个明确推荐，并点破相邻技能的区别（比如想法还模糊时就上 `/to-spec` 是错的，应该先 `/grill-with-docs`）
3. 对接目标技能：能由模型调用的直接调用；设置了 `disable-model-invocation` 的（`/to-spec`、`/to-tickets`、`/implement` 等），告诉你该输入哪个命令

检测到项目启用了 relay，或有 ticket 处于 `needs-strong` 状态时，它会把你路由到 `/relay-tickets` 或 `/relay-takeover`。

说「开工」「下一步做什么」「该用哪个技能」就会触发，也可以直接输入 `/develop`。

## 使用

前置：装好 Matt Pocock 的技能集，并在项目里跑过一次 `/setup-matt-pocock-skills`。

把 `skills/` 下的三个目录放到你的 agent 读取技能的位置就行，交给 agent 自己放也可以。

<details>
<summary>想让第 4 层 hook 也生效（仅 Claude Code）</summary>

hook 随插件分发，需要按插件安装：

```
/plugin marketplace add killerseven7777777/matt-skills-relay
/plugin install matt-skills-relay@matt-skills-relay
```

hook 需要 PATH 上有 `python3` 或 `python`，只用标准库。不装 hook，前三层保证照样有效。

</details>

## 局限

- 这是 v0.2，还没有在大量项目里验证过。strong zone 划得准不准，取决于规划模型的判断。
- hook 只检查本地 markdown tracker（`.scratch/`）。用 GitHub 或 GitLab issue 时，靠前三层保证。
- 接力不总是更省钱。小任务直接让一个模型做完更便宜；值不值得拆，取决于两边模型的价差和执行模型的一次通过率。`/relay-tickets` 一开始会确认执行者是谁，执行者和规划者一样强时会直接告诉你不必用它。

## 相近的项目

这个方向最近有不少人在探索，各有侧重，值得一看：

- [hayate/plan-for-weaker-models](https://github.com/hayate/plan-for-weaker-models)：教强模型给弱模型写计划。「只写接口契约、不写函数体」「用检查脚本定义完成、弱模型不准改」这几条规则非常扎实。
- [shipshitdev/skills#156](https://github.com/shipshitdev/skills/pull/156)：执行者先扫描计划里的未决选择标记，碰到就按固定字段上报规划者。
- [mbdwey/opus-plan-sonnet-execute](https://github.com/mbdwey/opus-plan-sonnet-execute)：Opus 规划、自动派 Sonnet 子代理并行执行。
- Claude Code 内置的 `opusplan` 模型别名：计划模式用 Opus，执行时切到 Sonnet。

本项目的不同之处：接在 Matt Pocock 的 ticket 体系上；由人来调度，执行模型可以在任何工具里、来自任何厂商；预设的 strong zone 和客观兜底条件并存。

## 致谢与许可

基于 [Matt Pocock 的 skills](https://github.com/mattpocock/skills)（MIT）的工作流与约定构建。本仓库同样以 [MIT](./LICENSE) 许可发布。
