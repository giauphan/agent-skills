---
name: gemini-subagent
description: Call Gemini CLI as a subagent for second opinions, code review, file analysis, or tasks that benefit from a different LLM perspective. Use when the main agent needs help with image analysis, long document summarization, regex generation, or wants a cross-model verification of its own output. Works from any AI IDE that can execute shell commands.
subagent_required: true
routing: SKILLS_ROUTER.md
max_timeout: 120
retry_policy: max_2_with_backoff
compatibility: "Requires Gemini CLI installed (`npm i -g @google/gemini-cli`), authenticated (`gemini auth`), and workspace trusted. Works from Claude Code, Cursor, Windsurf, Antigravity, Codex, or any agent with shell access."
license: MIT
allowed-tools: Bash
metadata:
  triggers:
    - need_second_opinion
    - cross_model_verification
    - image_analysis
    - long_document_summary
    - code_review
  token-cost: ~200
  openclaw:
    requires:
      bins:
        - gemini
    homepage: https://github.com/giauphan/agent-skills
---

# Gemini Subagent — Call Gemini CLI from Any AI IDE

## When to Use

- You need a **second opinion** on code logic or architecture
- You need **image/screenshot analysis** (Gemini has vision)
- You need to **summarize a very long document** without consuming your own context
- You want **cross-model verification** of your output
- The user explicitly asks to "ask Gemini" or "check with Gemini"

## Step 1: Pre-Flight Check

```bash
which gemini && echo "✅ Gemini CLI found" || echo "❌ Not installed: npm i -g @google/gemini-cli"
```

## Step 2: Call Gemini CLI

### Simple prompt
```bash
gemini --yolo -p "Your prompt here" 2>&1 | tail -20
```

### With file reading (project-aware)
```bash
cd /path/to/project && gemini --yolo -p "Read file.py and suggest improvements" 2>&1 | tail -30
```

### With timeout (safety)
```bash
timeout 90 gemini --yolo -p "Your prompt" 2>&1 | tail -20
```

## Step 3: Filter Boilerplate

```bash
timeout 90 gemini --yolo -p "prompt" 2>&1 | \
  grep -v "YOLO mode\|Ripgrep\|Falling back\|_GaxiosError\|at Gaxios\|at async\|at process" | \
  tail -20
```

## Step 4: Handle Errors

| Error | Cause | Fix |
|---|---|---|
| `not running in a trusted directory` | Workspace not trusted | `export GEMINI_CLI_TRUST_WORKSPACE=true` |
| `429 / RESOURCE_EXHAUSTED` | Rate limited | Wait 30-60 seconds, retry |
| `command not found` | CLI not installed | `npm i -g @google/gemini-cli && gemini auth` |
| Timeout | Prompt too complex | Simplify prompt or increase timeout |

## Step 5: Integration Pattern

```
1. Formulate a SPECIFIC, CONCISE prompt for Gemini
2. Run: timeout 90 gemini --yolo -p "<prompt>" 2>&1 | tail -20
3. Read stdout output
4. Integrate Gemini's answer into your own response
5. Credit: "According to Gemini subagent: ..."
```

## Environment Setup

```bash
# ~/.bashrc — permanent trust
export GEMINI_CLI_TRUST_WORKSPACE=true

# ~/.gemini/trustedFolders.json — per-folder trust
{
  "/home/user/projects": "TRUST_PARENT"
}
```

## Subagent Protocol (MANDATORY)

### Rule: 100% Routing Compliance

Every call to this skill MUST be routed through `SKILLS_ROUTER.md`.
Direct invocation without routing is PROHIBITED.

### Execution Contract

1. Pre-flight → `which gemini` must succeed
2. Timeout → Always set (default: 90s, max: 120s)
3. Output → Always clean boilerplate before returning
4. Attribution → Always credit "According to Gemini subagent: ..."
5. Error → Follow ERROR RECOVERY in AGENTS.md
