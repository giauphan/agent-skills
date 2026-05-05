---
trigger: always_on
priority: critical
weight: minimal
---

# SKILLS ROUTER — Dynamic Context Index

> Load ONLY what you need, WHEN you need it. NEVER preload all files.

## Routing Table

| # | Trigger Condition | Load File | Est. Tokens |
|---|---|---|---|
| 1 | Need second opinion / "ask gemini" | `skills/gemini-subagent/SKILL.md` | ~200 |
| 2 | Need code review via different model | `skills/gemini-subagent/SKILL.md` | ~200 |
| 3 | Image/screenshot analysis needed | `skills/gemini-subagent/SKILL.md` | ~200 |
| 4 | Long document summarization | `skills/gemini-subagent/SKILL.md` | ~200 |
| 5 | Cross-model output verification | `skills/gemini-subagent/SKILL.md` | ~200 |
| 6 | Before writing ANY code (self-check) | `rules/self-check.md` | ~150 |

## How to Use

1. **Match** current task against Trigger Condition column
2. **Read** the file using `read_file` / `view_file` / `@filename`
3. **Execute** instructions in that file
4. **No match** → proceed normally (0 extra tokens)

## CRITICAL: Subagent Protocol

ALL skill calls MUST follow this sequence:
1. Pre-flight → verify tool availability
2. Execute → run with timeout
3. Post-process → clean output, verify result
4. Credit → "According to Gemini subagent: ..."

## Token Budget

| State | Cost |
|---|---|
| Idle (no subagent call) | ~100 tokens (this file only) |
| Single subagent call | ~300 tokens (router + skill) |
| All preloaded (old way) | ~500+ tokens |
