# Agent Skills

> Universal agent instructions following [agentskills.io](https://agentskills.io) standard.
> Auto-detected by: Claude Code, Gemini CLI, GitHub Copilot, Cursor, Kiro, Codex, and 30+ tools.

## CRITICAL RULES (Always Active)

1. **NEVER** preload all skill/rule files — use dynamic routing via `SKILLS_ROUTER.md`
2. **ALWAYS** route subagent calls through `SKILLS_ROUTER.md` — 100% compliance required
3. **ALWAYS** run pre-flight check before calling Gemini subagent
4. **ALWAYS** clean Gemini output boilerplate before presenting to user
5. **ALWAYS** credit subagent source: "According to Gemini subagent: ..."
6. **NEVER** call Gemini subagent without timeout (max 120s)
7. **ALWAYS** verify Gemini CLI exists before attempting shell calls
8. **ALWAYS** re-read `SKILLS_ROUTER.md` every 15 messages to refresh routing

## ROUTING (On-Demand Skill Loading)

At conversation start, read `SKILLS_ROUTER.md` for the full routing table.
Match each task against trigger conditions. Load skills ONLY when triggered.

| Trigger | Action |
|---|---|
| Need second opinion / "ask gemini" | Load `skills/gemini-subagent/SKILL.md` |
| Need code review via different model | Load `skills/gemini-subagent/SKILL.md` |
| Image/screenshot analysis needed | Load `skills/gemini-subagent/SKILL.md` |
| Long document summarization | Load `skills/gemini-subagent/SKILL.md` |
| Cross-model output verification | Load `skills/gemini-subagent/SKILL.md` |
| Before writing code | Load `rules/self-check.md` (verify rule compliance) |
| Every 15 messages | Re-read `SKILLS_ROUTER.md` to refresh routing |

## SELF-CHECK (Before Every Action)

Before executing skill calls:
```
📋 Active Rules: [list top 3 applicable rules]
📂 Pre-flight: [gemini CLI status]
⏱️ Timeout: [configured timeout value]
```

## ERROR RECOVERY

- `command not found` → Report install instructions, do NOT retry
- `429 / RESOURCE_EXHAUSTED` → Wait 30-60s, retry max 2 times
- `Timeout` → Simplify prompt, retry with increased timeout
- Context stale (>15 messages) → Re-read `SKILLS_ROUTER.md`
