# matt-skills-relay

[中文](./README.md) | English

Add-ons for [Matt Pocock's skills](https://github.com/mattpocock/skills):

- **`/develop`**: a workflow router. Call it before you start, after each step, or whenever you're stuck. It inspects your repo and tells you which skill to run next.
- **`/relay-tickets` + `/relay-takeover`**: relay development. A strong model plans, a cheaper model writes the code, and the cheaper model stops on its own when it reaches a region the strong model must implement itself. You switch to the strong model, it writes that part, and hands back.

> **Note:** the skill bodies are written in Simplified Chinese. Skill names, terms, file names and field names stay in English, so they work alongside the original English skill set. Modern models follow Chinese instructions fine; this README is for you, not for them.

## Why relay development

A lot of people already work this way:

- Discuss the design and split tickets with Claude Fable or Opus, then hand the tickets to a faster, cheaper model such as Astra or Sol
- Plan with a strong model in Claude Code, then run the implementation in a different tool
- Spend subscription quota on planning and pay-as-you-go tokens on cheap execution

The problem: **a written plan is only part of the plan.** The strong model carries many judgements it never wrote down. When the executor hits a hard spot it fills the gap itself, and the usual results are quiet simplifications, literal readings that miss the intent, and improvising when the code doesn't match the plan.

One answer is to make the plan ever more detailed. But development is linear, and you can't solve every hard spot up front. Relay takes a different route: **while splitting tickets, the strong model decides which regions it must write itself and marks them as strong zones. The executor stops at the boundary and doesn't touch them.**

A strong zone is not "a question to settle later". Every decision was made by the strong model during planning. A strong zone is a part that is **decided, but that a weaker model won't get right**, for example:

- Code whose invariants are hard to cover fully with tests: concurrency, transactions, cache consistency
- Algorithms whose correctness comes from reasoning rather than from following a pattern
- Core interfaces shared by several tickets, where a mistake means wide rework
- Security-sensitive code: authentication, input validation

## What a relay looks like

Say you're building a cached report export, with Opus planning and Sol executing.

1. **Opus: `/relay-tickets`.** It splits the work into tracer-bullet tickets the way `/to-tickets` does, and also assigns an executor and marks strong zones for each one. You review and approve the split and the strong zones together. One ticket might look like this:

    ```markdown
    # 03: Paginated report export

    **What to build:** large reports are exported page by page instead of loading at once.
    **Blocked by:** 02
    **Status:** ready-for-agent

    - [ ] The export endpoint accepts a cursor parameter
    - [ ] The frontend fetches pages and concatenates the results

    **Executor:** weak

    ## Strong zones

    - [ ] SZ1: `encode_cursor()` / `decode_cursor()` in `src/export/cursor.py`. Reason: must line up with the cache invalidation strategy from 02, see ADR-0004.

    ## 执行规则 (execution rules)

    1. Read the whole ticket before starting, including Strong zones.
    2. After each acceptance item, re-read Strong zones before starting the next.
    3. If the next step would enter an unchecked strong zone, stop immediately...
    ```

2. **Sol works through the ticket.** It adds the endpoint parameter, reaches the cursor encoding, and hits SZ1. It commits what it has, sets `Status:` to `needs-strong`, leaves a handoff note under `## Comments`, and tells you "reached SZ1, please bring in the strong model".
3. **Opus: `/relay-takeover 03`.** It reads only the handoff note and the git diff, not the whole project. It checks whether Sol overstepped, implements SZ1, runs the tests, sets the status back to `ready-for-agent`, and hands back.
4. **Sol continues from where the note says**, and finishes the frontend part.

Sometimes the executor forgets to stop and writes a strong zone anyway. That's fine: `/relay-takeover` reviews it as a draft, keeps it if it's right, and rewrites it if not.

Besides strong zones, the execution rules include objective fallback triggers: the same test still fails after two fixes, a file outside the ticket's scope needs changing, the code doesn't match the interface the ticket describes, a new dependency is needed, or an acceptance criterion can be read more than one way. Any of these also makes the executor stop. They are deliberately mechanical, because a weak model's biggest flaw is not knowing what it doesn't know.

## How the executor is made to stop

Instead of relying on someone remembering to call a skill, the rules sit where the workflow is guaranteed to pass. Four layers back each other up:

1. **Entry point:** in relay mode, use `/relay-tickets` instead of `/to-tickets`.
2. **Project configuration hooks:** the first time it runs in a project, `/relay-tickets` writes three things (after you confirm):
    - `docs/agents/relay.md`: the single source of the rules and ticket template, readable by an executor in any tool
    - a section at the end of `docs/agents/issue-tracker.md`: every skill reads this file before publishing tickets, so even a plain `/to-tickets` run gets stopped at publish time and adds the markings
    - a `### Relay execution` section in `AGENTS.md` or `CLAUDE.md`
3. **Executor-side fallback:** if a ticket has no `## Strong zones` section, the executor doesn't start. It asks you to have the strong model mark the ticket first.
4. **Hook:** the plugin ships a `PostToolUse` hook. Every time Claude Code writes `.scratch/*/issues/*.md`, it checks that `**Executor:**`, `## Strong zones` and `## 执行规则` are all present, and tells the model to add whatever is missing.

The rules live in the ticket files themselves, not only in the skills, because the executor may not run in Claude Code at all. It can't see Claude's skills, but it always reads the ticket it is working on.

## About `/develop`

Matt Pocock's skills are great, but with twenty-odd of them, newcomers often don't know which one to use right now. `/develop` is meant for the whole development process: call it before you start, after each step, or when the flow stalls. It only routes; it never writes code. Each time it:

1. Inspects the project: git, issue tracker configuration, `CONTEXT.md`, ADRs, existing specs and tickets, and whether relay is enabled
2. Works out where you are from a decision table, gives one clear recommendation, and explains how it differs from neighbouring skills (for example, jumping to `/to-spec` while the idea is still vague is a mistake; `/grill-with-docs` comes first)
3. Hands off: skills the model can invoke are invoked directly; for skills with `disable-model-invocation` (`/to-spec`, `/to-tickets`, `/implement` and others), it tells you which command to type

When relay is enabled, or a ticket is in `needs-strong`, it routes you to `/relay-tickets` or `/relay-takeover`.

## Usage

Prerequisite: Matt Pocock's skills, with `/setup-matt-pocock-skills` run once in your project.

Put the three directories under `skills/` wherever your agent reads skills from, or let your agent do it.

<details>
<summary>To enable the layer 4 hook (Claude Code only)</summary>

The hook ships with the plugin, so install it as a plugin:

```
/plugin marketplace add killerseven7777777/matt-skills-relay
/plugin install matt-skills-relay@matt-skills-relay
```

The hook needs `python3` or `python` on PATH and uses only the standard library. Without the hook, the first three layers still apply.

</details>

## Limitations

- This is v0.1 and hasn't been validated across many projects. How well strong zones are chosen depends on the planning model's judgement.
- The hook only checks the local markdown tracker (`.scratch/`). With GitHub or GitLab issues, the first three layers carry the guarantee.
- Relay isn't always cheaper. Small tasks are cheaper done by one model; whether splitting pays off depends on the price gap between the two models and how often the executor gets it right first time. `/relay-tickets` asks who the executor is up front, and tells you to skip it when the executor is as strong as the planner.

## Related projects

Several people are exploring this space, each with a different focus:

- [hayate/plan-for-weaker-models](https://github.com/hayate/plan-for-weaker-models): teaches a strong model to write plans for a weaker one. Its rules ("name the contract, not the body", "an executable definition of done the implementer can't edit") are excellent.
- [shipshitdev/skills#156](https://github.com/shipshitdev/skills/pull/156): the executor scans the plan for unresolved-choice markers and escalates them to the planner in fixed fields.
- [mbdwey/opus-plan-sonnet-execute](https://github.com/mbdwey/opus-plan-sonnet-execute): Opus plans and dispatches Sonnet subagents to execute in parallel.
- Claude Code's built-in `opusplan` model alias: Opus in plan mode, Sonnet for execution.

What's different here: it builds on Matt Pocock's ticket workflow; a human does the dispatching, so the executor can run in any tool from any vendor; and pre-marked strong zones sit alongside objective fallback triggers.

## Credits and license

Built on the workflow and conventions of [Matt Pocock's skills](https://github.com/mattpocock/skills) (MIT). This repository is also released under the [MIT](./LICENSE) license.
