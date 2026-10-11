"""PostToolUse hook for relay-tickets.

After Claude writes or edits a local ticket file (.scratch/<feature>/issues/*.md)
in a repo that has relay enabled (docs/agents/relay.md exists), check that the
ticket carries the three relay sections. If any is missing, feed a reminder back
to Claude. Never fails the tool call: any error exits 0 silently.

Source is UTF-8 (Python 3 default). The JSON output uses ensure_ascii, so the
Windows console code page cannot garble the Chinese text on the way out.
"""
import json
import os
import re
import sys

TICKET_PATH = re.compile(r"^(?P<root>.*)/\.scratch/[^/]+/issues/[^/]+\.md$")

REQUIRED = [
    "**Executor:**",
    "## Strong zones",
    "## 执行规则",
]

# Wayfinder child tickets share the issues/ folder but are not implementation tickets.
NON_IMPL_TYPE = re.compile(r"^Type:\s*(research|prototype|grilling)\b", re.MULTILINE | re.IGNORECASE)


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") not in ("Write", "Edit", "MultiEdit"):
        return
    path = (data.get("tool_input") or {}).get("file_path") or ""
    path = path.replace("\\", "/")
    m = TICKET_PATH.match(path)
    if not m:
        return
    root = m.group("root")
    if not os.path.isfile(os.path.join(root, "docs", "agents", "relay.md")):
        return
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    if NON_IMPL_TYPE.search(text):
        return
    missing = [s for s in REQUIRED if s not in text]
    if not missing:
        return
    reason = (
        "relay: 这条 ticket 缺少接力标注："
        + "、".join("`" + s + "`" for s in missing)
        + "。按 docs/agents/relay.md 的 Ticket 段落模板补上（"
        + os.path.basename(path)
        + "）。"
    )
    out = {"decision": "block", "reason": reason}
    sys.stdout.write(json.dumps(out, ensure_ascii=True))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
