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
| 1 | Need second opinion / "ask gemini" | `skills/gemini-subagent/SKILL.md` | ~300 |
| 2 | Need code review via different model | `skills/gemini-subagent/SKILL.md` | ~300 |
| 3 | Image/screenshot analysis needed | `skills/gemini-subagent/SKILL.md` | ~300 |
| 4 | Long document summarization | `skills/gemini-subagent/SKILL.md` | ~300 |
| 5 | Cross-model output verification | `skills/gemini-subagent/SKILL.md` | ~300 |
| 6 | Batch refactoring / multi-file edits | `skills/gemini-subagent/SKILL.md` → **`@generalist` (1st priority)** | ~300 |
| 7 | Git diff review before commit | `skills/gemini-subagent/SKILL.md` → use stdin pipe | ~300 |
| 8 | Continue task from previous session | `skills/gemini-subagent/SKILL.md` → use `--resume` | ~300 |
| 9 | Need structured output with token stats | `skills/gemini-subagent/SKILL.md` → use stream-json | ~300 |
| 10 | Complex reasoning / need best model | `skills/gemini-subagent/SKILL.md` → use `gemini-3.1-pro-preview` | ~300 |
| 11 | **ANY task that touches files** | `skills/gemini-subagent/SKILL.md` → **use `@generalist` first** | ~300 |
| 12 | Before writing ANY code (self-check) | `rules/self-check.md` | ~150 |

## How to Use

1. **Match** current task against Trigger Condition column
2. **Read** the file using `read_file` / `view_file` / `@filename`
3. **Execute** instructions in that file
4. **No match** → proceed normally (0 extra tokens)

## CRITICAL: Subagent Protocol

ALL skill calls MUST follow this sequence:
1. Pre-flight → verify `which gemini` succeeds
2. Execute → run with timeout (max 120s)
3. Post-process → clean output, verify result
4. Credit → "According to Gemini subagent: ..."

## Confirmed Working Models (v0.40.0 tested)

| Model | Flag | Use Case |
|---|---|---|
| `gemini-3.1-pro-preview` | `-m gemini-3.1-pro-preview` | Complex reasoning, best quality (Pro plan) |
| `gemini-3-flash-preview` | `-m gemini-3-flash-preview` | Fast, good quality |
| `gemini-2.5-flash-lite` | `-m gemini-2.5-flash-lite` | Fastest, cheapest |
| auto | (no flag) | CLI auto-selects best model |

## Confirmed Working Features (v0.40.0 tested)

| Feature | Command Pattern |
|---|---|
| Simple prompt | `gemini --yolo -p "..."` |
| @generalist agent | `gemini --yolo -p "@generalist ..."` |
| Stdin pipe (git diff, logs) | `cat file \| gemini --yolo -p "..."` |
| Stream JSON + token stats | `gemini --yolo --output-format stream-json -p "..."` |
| Resume session | `gemini --yolo --resume latest -p "..."` |
| List sessions | `gemini --yolo --list-sessions` |
| Model selection | `gemini --yolo -m gemini-3.1-pro-preview -p "..."` |

## ❌ Interactive-Only (NOT usable from subagent)

- `--approval-mode plan` — requires interactive TTY
- `@codebase_investigator` — AbortError in headless (interactive-only)
- `@cli_help` — Timeout in headless (interactive-only)
- `gemini-3.1-pro` — wrong name (use `gemini-3.1-pro-preview`)
- `gemini-2.0-flash` — wrong name (use `gemini-3-flash-preview`)

## Agent Priority Rule

```
1. @generalist (ask_gemini_agent) — ANY task with file operations
2. stdin pipe (ask_gemini_pipe)   — if content already available
3. simple prompt (ask_gemini)     — Q&A only, no file changes
```

## Token Budget

| State | Cost |
|---|---|
| Idle (no subagent call) | ~100 tokens (this file only) |
| Single subagent call | ~400 tokens (router + skill) |
| All preloaded (old way) | ~500+ tokens |
