# Agent Skills

> Universal AI agent skills following [agentskills.io](https://agentskills.io) standard.
> Auto-detected by: Claude Code, Gemini CLI, GitHub Copilot, Cursor, Kiro, Codex, and 30+ tools.

## 🧩 Available Skills

| Skill | Description | Trigger |
|---|---|---|
| [`gemini-subagent`](skills/gemini-subagent/SKILL.md) | Call Gemini CLI as a subagent for second opinions, code review, image analysis | "ask gemini", need second opinion |

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
