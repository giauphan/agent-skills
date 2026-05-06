---
name: gemini-subagent
description: Call Gemini CLI as a subagent for second opinions, code review, file analysis, git diff review, session resuming, structured JSON output, or agent-delegation. Use when the main agent needs help with image analysis, long document summarization, batch refactoring, or cross-model verification. Works from any AI IDE that can execute shell commands.
subagent_required: true
routing: SKILLS_ROUTER.md
max_timeout: 120
retry_policy: max_2_with_backoff
compatibility: "Requires Gemini CLI v0.40.0+ (`npm i -g @google/gemini-cli`), authenticated (`gemini auth`), workspace trusted."
license: MIT
allowed-tools: Bash
metadata:
  triggers:
    - need_second_opinion
    - cross_model_verification
    - image_analysis
    - long_document_summary
    - code_review
    - git_diff_review
    - batch_refactoring
    - session_resume
    - structured_output
  token-cost: ~200
  openclaw:
    requires:
      bins:
        - gemini
    homepage: https://github.com/giauphan/agent-skills
---

# Gemini Subagent — Full Feature Guide (v0.40.0 tested)

## Tool Priority (Use This Order)

> **ALWAYS prefer `@generalist` for any task involving files or multi-step work.**
> Only fall back to simple prompt for pure Q&A or analysis with no file changes.

| Priority | Use Case | Tool |
|---|---|---|
| 🥇 1st | Multi-file edits, batch tasks, anything touching files | `@generalist` (ask_gemini_agent) |
| 🥈 2nd | Content already available (git diff, logs) | stdin pipe (ask_gemini_pipe) |
| 🥉 3rd | Pure Q&A, architecture opinions, code review read-only | simple prompt (ask_gemini) |

## Available Agents

| Agent | Headless | Use For |
|---|---|---|
| `@generalist` | ✅ **Works** | Batch refactoring, multi-file tasks, full tooling |
| `@codebase_investigator` | ❌ Interactive-only | AbortError in headless — skip |
| `@cli_help` | ❌ Interactive-only | Timeout in headless — skip |

## When to Use (by scenario)
| Scenario | Pattern to Use |
|---|---|
| Second opinion on code/architecture | [Simple Prompt](#1-simple-prompt) |
| Code review with focus areas | [Code Review](#2-code-review) |
| **ANY task touching files** | [**@generalist Agent ← PREFER THIS**](#3-generalist-agent) |
| Batch refactoring / complex multi-step | [**@generalist Agent ← PREFER THIS**](#3-generalist-agent) |
| Git diff review before commit | [Stdin Pipe](#4-stdin-pipe--git-diff) |
| Structured output with token stats | [Stream JSON](#5-stream-json-output) |
| Continue task from previous session | [Resume Session](#6-resume-session) |
| List available sessions | [List Sessions](#7-list-sessions) |
| Fast model for simple task | [Model Selection](#8-model-selection) |

---

## Step 1: Pre-Flight Check

```bash
which gemini && echo "✅ Gemini CLI found" || echo "❌ Not installed: npm i -g @google/gemini-cli"
gemini --version  # Should be 0.40.0+
```

---

## Feature Catalog (All Verified Working)

### 1. Simple Prompt
```bash
timeout 90 gemini --yolo -p "Your prompt here" 2>&1 | \
  grep -v "YOLO\|Ripgrep\|Falling\|_Gaxios\|at Gaxios\|at async\|at process\|status: 429\|error: undefined\|Symbol(" | tail -20
```

### 2. Code Review
```bash
# Review a specific file
timeout 90 gemini --yolo -p "Read the file 'src/auth.py' and review it. Focus on: security. List issues with line numbers." 2>&1 | \
  grep -v "YOLO\|Ripgrep\|Falling\|_Gaxios\|at Gaxios\|at async\|at process\|status: 429\|error: undefined\|Symbol(" | tail -30
```

### 3. @generalist Agent
Use for batch refactoring, multi-file edits, turn-intensive tasks.
The generalist agent has access to ALL tools and keeps main session lean.

```bash
timeout 120 gemini --yolo -p "@generalist Fix all TypeScript errors in src/ directory" 2>&1 | \
  grep -v "YOLO\|Ripgrep\|Falling\|_Gaxios\|at Gaxios\|at async\|at process\|status: 429\|error: undefined\|Symbol(" | tail -30
```

### 4. Stdin Pipe / Git Diff
Pipe ANY content directly into Gemini — git diffs, logs, JSON, code snippets.

```bash
# Git diff review before commit
git diff HEAD | timeout 90 gemini --yolo -p "Review these changes for bugs and issues" 2>&1 | \
  grep -v "YOLO\|Ripgrep\|Falling\|_Gaxios\|at Gaxios\|at async\|at process\|status: 429\|error: undefined\|Symbol(" | tail -20

# Pipe a file
cat src/auth.py | timeout 90 gemini --yolo -p "Find security vulnerabilities in this code" 2>&1 | tail -20

# Pipe logs
cat error.log | timeout 90 gemini --yolo -p "Analyze these errors and suggest fixes" 2>&1 | tail -20
```

### 5. Stream JSON Output
Returns structured JSON with token stats, session ID, model info. Best for machine-readable output or when you need metadata.

```bash
timeout 90 gemini --yolo --output-format stream-json -p "Your prompt" 2>&1 | \
  grep -E '"type":"(message|result)"' | \
  python3 -c "import sys,json; [print(json.loads(l).get('content','') or json.dumps(json.loads(l).get('stats',{}))) for l in sys.stdin if l.strip()]"
```

Raw stream-json format:
```json
{"type":"init","session_id":"...","model":"auto-gemini-3"}
{"type":"message","role":"assistant","content":"Hello!","delta":true}
{"type":"result","status":"success","stats":{"total_tokens":10988,"input_tokens":10671,"output_tokens":42,"duration_ms":5820}}
```

### 6. Resume Session
Gemini CLI saves sessions per-directory. Resume any previous session by index or "latest".

```bash
# Resume most recent session
timeout 90 gemini --yolo --resume latest -p "Continue the refactoring from where we left off" 2>&1 | \
  grep -v "YOLO\|Ripgrep\|Falling\|_Gaxios\|at Gaxios\|at async\|at process\|status: 429\|error: undefined\|Symbol(" | tail -20

# Resume by session index (see list-sessions)
timeout 90 gemini --yolo --resume 2 -p "What was the plan you outlined?" 2>&1 | tail -10
```

### 7. List Sessions
```bash
gemini --yolo --list-sessions 2>&1 | grep -v "YOLO mode"
# Output: Available sessions (4):
#   1. Task name (time ago) [session-uuid]
#   2. ...
```

### 8. Model Selection
Default is `auto-gemini-3`. Use specific models for speed/quality tradeoff.

```bash
# Best quality — Gemini 3.1 Pro (gemini-3.1-pro-preview) ✅ CONFIRMED
timeout 90 gemini --yolo -m gemini-3.1-pro-preview -p "Complex reasoning or deep analysis" 2>&1 | tail -20

# Fast + good quality ✅ CONFIRMED
timeout 60 gemini --yolo -m gemini-3-flash-preview -p "Regular tasks" 2>&1 | tail -10

# Fastest / cheapest ✅ CONFIRMED (auto-routing uses this internally)
timeout 30 gemini --yolo -m gemini-2.5-flash-lite -p "Simple quick task" 2>&1 | tail -5

# Default (auto-selects best model per task)
timeout 90 gemini --yolo -p "Any task" 2>&1 | tail -20
```

> **Note:** Model names `gemini-3.1-pro` and `gemini-2.0-flash` return 404. Use the preview names above.

---

## Error Handling

| Error | Cause | Fix |
|---|---|---|
| `not running in a trusted directory` | Workspace not trusted | `export GEMINI_CLI_TRUST_WORKSPACE=true` |
| `429 / RESOURCE_EXHAUSTED` | Rate limited | Wait 30-60 seconds, retry |
| `command not found` | CLI not installed | `npm i -g @google/gemini-cli && gemini auth` |
| `Timeout (exit 143)` | Prompt too complex or interactive-only mode | Simplify prompt or use `--yolo` |
| `404 error` | Wrong model name | Use `gemini-3.1-pro-preview` or `gemini-3-flash-preview` (not `gemini-3.1-pro` or `gemini-2.0-flash`) |
| `exit 130` | Feature requires interactive mode | Use headless-compatible alternatives |

## ❌ Features That Require Interactive Mode (Do NOT use headless)

- `--approval-mode plan` — only works interactively
- `@codebase_investigator` — requires interactive session
- `--acp` mode — requires interactive

---

## Environment Setup

```bash
# ~/.bashrc — permanent workspace trust
export GEMINI_CLI_TRUST_WORKSPACE=true
```

## Subagent Protocol (MANDATORY)

### Rule: 100% Routing Compliance

Every call MUST be routed through `SKILLS_ROUTER.md`. Direct invocation without routing is PROHIBITED.

### Execution Contract

1. Pre-flight → `which gemini` must succeed
2. Timeout → Always set (default: 90s, max: 120s)
3. Output → Always clean boilerplate before returning
4. Attribution → Always credit "According to Gemini subagent: ..."
5. Error → Follow ERROR RECOVERY in AGENTS.md
