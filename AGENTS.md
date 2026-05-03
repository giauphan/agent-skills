# Agent Skills

> Universal agent instructions following [agentskills.io](https://agentskills.io) standard.
> Auto-detected by: Claude Code, Gemini CLI, GitHub Copilot, Cursor, Kiro, Codex, and 30+ tools.

## ROUTING (On-Demand Skill Loading)

At conversation start, read `SKILLS_ROUTER.md` for the full routing table.
Match each task against trigger conditions. Load skills ONLY when triggered.

| Trigger | Action |
|---|---|
| Need second opinion / "ask gemini" | Load `skills/gemini-subagent/SKILL.md` |
| Need code review via different model | Load `skills/gemini-subagent/SKILL.md` |
| Image/screenshot analysis needed | Load `skills/gemini-subagent/SKILL.md` |
