---
name: relay-tickets
description: 接力开发（强模型规划、弱模型执行）的拆单入口，接力模式下代替 /to-tickets 使用。按 /to-tickets 的流程拆分，同时把每条 ticket 写成有序步骤、标出必须由强模型亲手实现的 strong 步骤并写入执行规则，让弱模型按顺序执行、走到 strong 步骤就停下，由用户请强模型接手。也用于给已存在的 tickets 补标注。
disable-model-invocation: true
---

# Relay Tickets

接力开发：强模型（planner）在写文档阶段就做完所有决策，把每条 ticket 写成有序步骤，标出必须由自己亲手实现的 strong 步骤；弱模型（executor）按顺序一步一步做，走到 strong 步骤就停下，由用户切换到强模型接手，强模型只做完这几步就交还，弱模型从下一步继续。

本技能是接力模式下的拆单入口，负责 planner 一侧。接手一侧见 `/relay-takeover`。

执行步骤的写法、strong zone 的划分标准、ticket 段落模板和执行规则都在本技能目录的 [relay.md](./relay.md) 里。动手前通读它。

## 门槛：谁来执行？

动手前先确认 executor 是谁。

- 全部由你自己，或一个至少同样强的模型执行：停止，本技能不适用，直接用 `/to-tickets` 和 `/implement`。标注 strong zone 是有成本的，executor 足够强时这份成本什么也换不来。
- 有更弱的模型参与执行（另一个工具里的模型、更便宜的模型、本地模型）：继续。
- 不确定：问用户 executor 是哪个模型、在哪个工具里运行，然后等回答。

## 流程

### 1. 在项目里启用 relay（每个项目只做一次）

检查仓库里有没有 `docs/agents/relay.md`。已经有了，就和本技能目录的 [relay.md](./relay.md) 比对：内容一致就跳到步骤 2；项目里的是旧版本（例如没有 `## 执行步骤`），就把下面三处改动按新版本起草出来，给用户看过、确认后再写入，并告诉用户已经发布的 ticket 要按新规则补标注（步骤 2 的第二种情况）。

没有的话，起草下面三处改动，给用户看过、确认后再写入：

1. **`docs/agents/relay.md`**：以本技能目录的 [relay.md](./relay.md) 为种子原样写入。这是项目里关于 relay 的唯一来源：executor 可能在另一个工具里运行，看不到 Claude 的技能，但读得到仓库里的文件。
2. **`docs/agents/issue-tracker.md`**：在末尾追加下面这一节。任何技能发布 ticket 时都会读这个文件，原版 `/to-tickets` 被直接调用时，会在发布这一步被这一节拦下来补标注。

    ```markdown
    ## 接力开发（relay）

    本仓库启用了接力开发。发布或修改实现类 ticket 时，每条 ticket 都必须带有 `**Executor:**` 行、`## 执行步骤` 段、`## Strong zones` 段和 `## 执行规则` 段。规则和模板见 `docs/agents/relay.md`，发布前按它补上。
    ```

    这个文件不存在，说明 `/setup-matt-pocock-skills` 还没跑过：先让用户运行它，再回到这里。
3. **`AGENTS.md` 或 `CLAUDE.md`**：选文件的规则同 `/setup-matt-pocock-skills`，哪个存在改哪个，都不存在就问用户。在 `## Agent skills` 块下加：

    ```markdown
    ### Relay execution

    本仓库按接力方式开发，见 `docs/agents/relay.md`。执行任何 ticket 前，先确认它带有 `## 执行步骤` 和 `## Strong zones` 两段：缺一段就不要开工，请用户找强模型补标注；都有就严格遵守 ticket 里的 `## 执行规则`：按编号顺序一次做一步，下一步是 `[strong]` 步骤或碰到 strong zone 的触发条件时立即停下交接，不跳过、不绕开。
    ```

### 2. 拆分

- tickets 还不存在：找到 `/to-tickets` 的技能文件，按它的步骤 1 到 3 起草拆分。用户调用本技能，就是要求用 relay 的方式拆单，所以这里读取 `/to-tickets` 的文件来执行它的步骤，是在执行用户的指令；它不允许模型调用，不要尝试用 Skill 工具。找文件的顺序：
    1. 本技能目录旁边的 `../to-tickets/SKILL.md`（本技能和 Matt Pocock 技能集装在同一个插件里时）
    2. 在当前仓库的 `.claude/skills/`、`.agents/skills/`，以及 `~/.claude/plugins/`、`~/.claude/skills/` 下搜索 `to-tickets/SKILL.md`；找到多份时，优先用户正在使用的那一套（中文版或英文版）
    3. 都找不到：请用户先输入 `/to-tickets`。步骤 1 已经在 tracker 配置里写好了挂钩，`/to-tickets` 发布时会补上标注；发布完再运行本技能检查一遍。
- tickets 已经存在（包括被原版 `/to-tickets` 发布、缺少标注的，以及按旧规则标注、没有 `## 执行步骤` 段的）：直接读取，跳到步骤 3。已经有人动过的 ticket，已完成的部分写成已勾选的步骤，保留原有的 `## Comments`。

### 3. 写执行步骤，划出 strong zone

按 [relay.md](./relay.md) 里的标准，给每条 ticket：

1. 定 Executor。
2. 拆成有序的执行步骤，每步标 `[weak]` 或 `[strong]`，strong 步骤放在开发顺序里它本来的位置。
3. 查清前置条件：步骤要用到的函数、接口、夹具和工具能力，到代码里确认是否已经存在。缺的、又落在 strong zone 里的，写成排在使用它之前的 `[strong]` 步骤。
4. 列出 Strong zones：顺序型对应哪一步；触发型写清触发条件和禁止的绕法。

划得太多，接力就退化成强模型独自干活，还白白多出交接成本。拿不准某个区域该不该划时，问自己：弱模型照着 ticket 写错了，强模型接手时能不能很快发现并修好？能，就不划。

划得含糊同样有害。触发型条目只写「在修改某文件之前停下」，弱模型可以在别的文件里写一份等价实现，永远走不到边界；所以每条触发型条目都要写出禁止的绕法。

### 4. 呈现给用户

这一步代替 `/to-tickets` 的步骤 4：拆分方案和 strong zone 一起呈现、一起批准。对每条 ticket 展示：

- **Title**、**Blocked by**、**What it delivers**（同 `/to-tickets`）
- **Executor**：strong 还是 weak
- **执行步骤**：按顺序列出，标明哪几步是 `[strong]`
- **Strong zones**：逐条列出（顺序型写第几步，触发型写触发条件和禁止的绕法），或写「无」

问用户：

- 粒度和 blocking edges 对不对？（同 `/to-tickets`）
- 步骤顺序对不对？strong 步骤是不是放在了它该在的位置？
- strong zone 有没有划多或划少的？
- 边界是否写得足够清楚，弱模型不用做判断就能识别出来，也绕不过去？

反复迭代，直到用户批准。

### 5. 发布

按 `/to-tickets` 的步骤 5 发布，每条 ticket 在验收标准之后加上 [relay.md](./relay.md) 里的四部分。`Executor: strong` 或没有 strong zone 的 ticket，Strong zones 段写「无」，执行步骤和执行规则段照样保留：按顺序执行和兜底停下的规则对所有 ticket 都有效。

tracker 是 GitHub 或 GitLab 时：`Status: needs-strong` 改用同名 label，`## Comments` 改用 issue 评论。

本插件带有一个 hook：在 Claude Code 里写入 `.scratch/*/issues/*.md` 后，会检查这四部分是否齐全，缺了会提示你补上（`Status: done` 的 ticket 不查）。看到提示就照做。这个 hook 只覆盖本地 markdown tracker；用 GitHub 或 GitLab 时要自己检查。
