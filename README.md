# Agent Skills

> Universal AI agent skills following [agentskills.io](https://agentskills.io) standard.
> Auto-detected by: Claude Code, Gemini CLI, GitHub Copilot, Cursor, Kiro, Codex, and 30+ tools.

## 🧩 Available Skills

| Skill | Description | Trigger |
|---|---|---|
| [`gemini-subagent`](skills/gemini-subagent/SKILL.md) | Call Gemini CLI as a subagent for second opinions, code review, image analysis | "ask gemini", need second opinion |

## 🏗️ Architecture

```
agent-skills/
├── AGENTS.md              # Entry point (auto-detected by 30+ AI tools)
├── SKILLS_ROUTER.md       # Dynamic routing index (load-on-demand)
├── skills/
│   └── gemini-subagent/
│       └── SKILL.md       # Skill definition + protocol
├── scripts/
│   └── mcp_gemini_subagent.py  # MCP server for native tool calls
├── rules/
│   └── self-check.md      # Pre-execution validation
├── .cursorrules            # Cursor IDE rules
├── .windsurfrules          # Windsurf IDE rules
└── .clinerules             # Cline IDE rules
```

### Routing Flow
1. Agent starts → reads `AGENTS.md` (auto-detected)
2. `AGENTS.md` → points to `SKILLS_ROUTER.md`
3. Router matches task → loads specific `SKILL.md`
4. Skill executes with pre-flight + timeout + cleanup
5. 100% subagent calls go through this pipeline

## 🔌 MCP Server

For Claude Code / MCP-compatible IDEs, use the MCP server for native function calling:

```json
{
  "mcpServers": {
    "gemini-subagent": {
      "command": "python3",
      "args": ["scripts/mcp_gemini_subagent.py"]
    }
  }
}
```

**Available tools via MCP:**
| Tool | Description |
|---|---|
| `ask_gemini` | Ask Gemini CLI any question or task |
| `ask_gemini_review` | Ask Gemini to review a specific file |

## 📦 Installation

### Shell Method (Any IDE)
```bash
git clone https://github.com/giauphan/agent-skills.git
cp -r agent-skills/skills/gemini-subagent your-project/skills/
```

### MCP Method (Claude Code)
Add to your `.claude/claude.json`:
```json
{
  "mcpServers": {
    "gemini-subagent": {
      "command": "python3",
      "args": ["/absolute/path/to/scripts/mcp_gemini_subagent.py"]
    }
  }
}
```

### Prerequisites
```bash
npm i -g @google/gemini-cli
gemini auth
export GEMINI_CLI_TRUST_WORKSPACE=true  # Add to ~/.bashrc
```

## 🔗 Related

- [gemini-browser-agent-skills](https://github.com/giauphan/gemini-browser-agent-skills) — Browser lifecycle management skills (preflight, cleanup, heavy-cleanup)
- [agentskills.io](https://agentskills.io) — Agent Skills specification
- [anthropics/skills](https://github.com/anthropics/skills) — Official Anthropic skills

## License

MIT
