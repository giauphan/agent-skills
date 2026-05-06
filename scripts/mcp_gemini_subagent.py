#!/usr/bin/env python3
"""
MCP Server: Gemini CLI Subagent (v2 — Full Feature)
====================================================
Wraps Gemini CLI (v0.40.0+) as an MCP tool so any MCP-compatible agent
(Claude Code, Cursor, Antigravity, etc.) can call it natively via
Function Calling instead of shell parsing.

Tools exposed:
  ask_gemini           — Simple prompt (baseline)
  ask_gemini_review    — Code file review with focus areas
  ask_gemini_agent     — Delegate to @generalist agent (batch tasks)
  ask_gemini_pipe      — Pipe content (git diff, logs, code) to Gemini
  ask_gemini_structured — Get stream-json output with token stats
  ask_gemini_resume    — Resume a previous session by index or "latest"
  ask_gemini_sessions  — List available sessions for current project

Usage:
  # Register in Claude Code / Antigravity MCP config:
  {
    "mcpServers": {
      "gemini-subagent": {
        "command": "python3",
        "args": ["path/to/mcp_gemini_subagent.py"]
      }
    }
  }

  # Direct CLI test:
  python3 mcp_gemini_subagent.py "your prompt here"
"""

import subprocess
import json
import sys
import os
import re
from typing import Optional


# ============================================
# Output Cleanup
# ============================================
BOILERPLATE_PATTERNS = [
    "YOLO mode",
    "Ripgrep is not",
    "Falling back to",
    "_GaxiosError",
    "at Gaxios",
    "at async",
    "at process",
    "status: 429",
    "error: undefined",
    "Symbol(",
    "config:",
    "response:",
    "headers:",
    "Attempt",
    "retryWithBackoff",
    "GeminiChat",
    "CodeAssistServer",
    "  url:",
    "  method:",
    "  params:",
    "  body:",
    "  signal:",
    "  retry:",
    "paramsSerializer",
    "validateStatus",
    "errorRedactor",
    "responseType",
    "Content-Type",
    "User-Agent:",
    "Authorization:",
    "x-goog",
    "content-length",
    "content-type:",
    "  date:",
    "  server:",
    "server-timing",
    "  vary:",
    "x-cloud",
    "x-content",
    "x-frame",
    "x-xss",
    "alt-svc",
    "statusText",
    "responseURL",
    "Symbol(",
]


def clean_gemini_output(raw: str) -> str:
    """Remove Gemini CLI boilerplate from output."""
    lines = raw.split("\n")
    cleaned = []
    for line in lines:
        if any(p in line for p in BOILERPLATE_PATTERNS):
            continue
        if line.strip().startswith('"error"') or line.strip().startswith('"code"'):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


# ============================================
# Core Call Function
# ============================================
def call_gemini(
    prompt: str,
    timeout: int = 90,
    cwd: Optional[str] = None,
    extra_args: Optional[list] = None,
    stdin_content: Optional[str] = None,
    model: Optional[str] = None,
    output_format: str = "text",
) -> dict:
    """
    Call Gemini CLI and return structured result.

    Args:
        prompt: Prompt to send
        timeout: Max seconds (default: 90)
        cwd: Working directory for file-aware prompts
        extra_args: Additional CLI flags
        stdin_content: Content to pipe via stdin
        model: Model name (e.g. 'gemini-3-flash-preview')
        output_format: 'text', 'json', or 'stream-json'

    Returns:
        dict with 'success', 'output', 'error', 'raw_output', 'stats'
    """
    env = os.environ.copy()
    env["GEMINI_CLI_TRUST_WORKSPACE"] = "true"

    cmd = ["gemini", "--yolo"]

    if model:
        cmd += ["-m", model]

    if output_format != "text":
        cmd += ["--output-format", output_format]

    cmd += ["-p", prompt]

    if extra_args:
        cmd += extra_args

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or os.getcwd(),
            env=env,
            input=stdin_content,
        )

        raw = result.stdout + result.stderr

        # Check for rate limit
        if "429" in raw and "RESOURCE_EXHAUSTED" in raw:
            return {
                "success": False,
                "output": "",
                "error": "Rate limited (429). Wait 30-60 seconds and retry.",
                "raw_output": raw[:500],
                "stats": None,
            }

        # Check for trust error
        if "not running in a trusted directory" in raw:
            return {
                "success": False,
                "output": "",
                "error": "Workspace not trusted. Run: export GEMINI_CLI_TRUST_WORKSPACE=true",
                "raw_output": raw[:500],
                "stats": None,
            }

        # Parse stream-json format
        if output_format == "stream-json":
            return _parse_stream_json(raw)

        cleaned = clean_gemini_output(raw)
        return {
            "success": True,
            "output": cleaned,
            "error": None,
            "raw_output": raw[:500] if len(raw) > 500 else raw,
            "stats": None,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": f"Timeout after {timeout}s. Simplify prompt or increase timeout.",
            "raw_output": "",
            "stats": None,
        }
    except FileNotFoundError:
        return {
            "success": False,
            "output": "",
            "error": "Gemini CLI not found. Install: npm i -g @google/gemini-cli",
            "raw_output": "",
            "stats": None,
        }


def _parse_stream_json(raw: str) -> dict:
    """Parse stream-json output into structured result."""
    messages = []
    stats = None
    session_id = None

    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if obj.get("type") == "init":
                session_id = obj.get("session_id")
            elif obj.get("type") == "message" and obj.get("role") == "assistant":
                content = obj.get("content", "")
                if content:
                    messages.append(content)
            elif obj.get("type") == "result":
                stats = obj.get("stats", {})
        except json.JSONDecodeError:
            pass

    output = "\n".join(messages).strip()
    stats_summary = ""
    if stats:
        duration_s = stats.get("duration_ms", 0) / 1000
        stats_summary = (
            f"\n[Stats] tokens={stats.get('total_tokens', '?')} "
            f"| duration={duration_s:.1f}s "
            f"| session={session_id or 'n/a'}"
        )

    return {
        "success": bool(output),
        "output": output + stats_summary if output else "",
        "error": None if output else "No assistant content in stream-json output",
        "raw_output": raw[:500],
        "stats": stats,
        "session_id": session_id,
    }


def call_gemini_list_sessions(cwd: Optional[str] = None) -> dict:
    """List available Gemini CLI sessions for the current project."""
    env = os.environ.copy()
    env["GEMINI_CLI_TRUST_WORKSPACE"] = "true"

    try:
        result = subprocess.run(
            ["gemini", "--yolo", "--list-sessions"],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=cwd or os.getcwd(),
            env=env,
        )
        raw = result.stdout + result.stderr
        cleaned = "\n".join(
            l for l in raw.split("\n")
            if l.strip() and "YOLO mode" not in l
        ).strip()
        return {"success": True, "output": cleaned, "error": None}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e)}


# ============================================
# MCP Server Protocol (stdio JSON-RPC)
# ============================================
TOOLS = [
    {
        "name": "ask_gemini",
        "description": (
            "Ask Gemini CLI a question or give it a task. Use for second opinions, "
            "architecture review, or cross-model verification. Gemini can read files "
            "in the current project directory."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "The prompt/question to send to Gemini"},
                "timeout": {"type": "integer", "description": "Max seconds to wait (default: 90)", "default": 90},
                "model": {"type": "string", "description": "Model name. Confirmed: 'gemini-3.1-pro-preview' (Pro plan, best quality), 'gemini-3-flash-preview' (fast), 'gemini-2.5-flash-lite' (fastest). Leave empty for auto."},
            "required": ["prompt"],
        },
    },
    {
        "name": "ask_gemini_review",
        "description": (
            "Ask Gemini CLI to review a code file. Automatically builds file reading "
            "instructions. Focus can be: 'bugs', 'security', 'performance', 'style', or 'all'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file to review"},
                "focus": {
                    "type": "string",
                    "description": "What to focus on: 'bugs', 'security', 'performance', 'style', or 'all'",
                    "default": "all",
                },
                "project_dir": {"type": "string", "description": "Project root directory (optional)"},
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "ask_gemini_agent",
        "description": (
            "Delegate a complex, turn-intensive task to the @generalist Gemini agent. "
            "The generalist has access to all tools (read/write files, run commands, search). "
            "Best for: batch refactoring across multiple files, fixing many errors at once, "
            "high-volume data processing. Keeps the main session history lean."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "The task to delegate to the generalist agent"},
                "timeout": {"type": "integer", "description": "Max seconds (default: 120 for complex tasks)", "default": 120},
                "project_dir": {"type": "string", "description": "Project directory to work in"},
            },
            "required": ["task"],
        },
    },
    {
        "name": "ask_gemini_pipe",
        "description": (
            "Pipe content directly to Gemini CLI for analysis. Use for: git diff review, "
            "log analysis, code snippet review without reading from disk. "
            "Content is passed via stdin."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Content to pipe to Gemini (git diff, logs, code, JSON, etc.)"},
                "prompt": {"type": "string", "description": "What to do with the piped content"},
                "timeout": {"type": "integer", "description": "Max seconds (default: 90)", "default": 90},
                "project_dir": {"type": "string", "description": "Project directory (optional)"},
            },
            "required": ["content", "prompt"],
        },
    },
    {
        "name": "ask_gemini_structured",
        "description": (
            "Call Gemini CLI with stream-json output format. Returns the response plus "
            "token usage stats (total tokens, duration, model used, session ID). "
            "Use when you need structured output or want to track usage."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "The prompt to send"},
                "timeout": {"type": "integer", "description": "Max seconds (default: 90)", "default": 90},
                "project_dir": {"type": "string", "description": "Project directory (optional)"},
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "ask_gemini_resume",
        "description": (
            "Resume a previous Gemini CLI session and continue from where it left off. "
            "Gemini saves sessions per-directory. Use 'latest' or a session index number. "
            "Call ask_gemini_sessions first to see available sessions."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Follow-up prompt to send to the resumed session"},
                "session": {
                    "type": "string",
                    "description": "Session to resume: 'latest' or a number like '1', '2', '3'",
                    "default": "latest",
                },
                "timeout": {"type": "integer", "description": "Max seconds (default: 90)", "default": 90},
                "project_dir": {"type": "string", "description": "Project directory (optional)"},
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "ask_gemini_sessions",
        "description": (
            "List all available Gemini CLI sessions for the current project. "
            "Sessions are stored per-directory. Use the index numbers with ask_gemini_resume."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {"type": "string", "description": "Project directory to list sessions for (optional)"},
            },
        },
    },
]


def handle_mcp_request(request: dict) -> dict:
    """Handle MCP JSON-RPC requests."""
    method = request.get("method", "")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "gemini-subagent", "version": "2.0.0"},
            },
        }

    elif method == "notifications/initialized":
        return None

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOLS},
        }

    elif method == "tools/call":
        tool_name = request.get("params", {}).get("name", "")
        args = request.get("params", {}).get("arguments", {})
        text_output = _dispatch_tool(tool_name, args)

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": text_output}]
            },
        }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"},
    }


def _dispatch_tool(tool_name: str, args: dict) -> str:
    """Dispatch to the correct tool and return string output."""

    if tool_name == "ask_gemini":
        result = call_gemini(
            prompt=args.get("prompt", ""),
            timeout=args.get("timeout", 90),
            cwd=args.get("project_dir"),
            model=args.get("model"),
        )
        return result["output"] if result["success"] else f"Error: {result['error']}"

    elif tool_name == "ask_gemini_review":
        file_path = args.get("file_path", "")
        focus = args.get("focus", "all")
        prompt = (
            f"Read the file '{file_path}' and review it carefully. "
            f"Focus on: {focus}. List all issues with line numbers and suggested fixes."
        )
        result = call_gemini(prompt=prompt, timeout=120, cwd=args.get("project_dir"))
        return result["output"] if result["success"] else f"Error: {result['error']}"

    elif tool_name == "ask_gemini_agent":
        task = args.get("task", "")
        prompt = f"@generalist {task}"
        result = call_gemini(
            prompt=prompt,
            timeout=args.get("timeout", 120),
            cwd=args.get("project_dir"),
        )
        return result["output"] if result["success"] else f"Error: {result['error']}"

    elif tool_name == "ask_gemini_pipe":
        result = call_gemini(
            prompt=args.get("prompt", ""),
            timeout=args.get("timeout", 90),
            cwd=args.get("project_dir"),
            stdin_content=args.get("content", ""),
        )
        return result["output"] if result["success"] else f"Error: {result['error']}"

    elif tool_name == "ask_gemini_structured":
        result = call_gemini(
            prompt=args.get("prompt", ""),
            timeout=args.get("timeout", 90),
            cwd=args.get("project_dir"),
            output_format="stream-json",
        )
        return result["output"] if result["success"] else f"Error: {result['error']}"

    elif tool_name == "ask_gemini_resume":
        session = args.get("session", "latest")
        result = call_gemini(
            prompt=args.get("prompt", ""),
            timeout=args.get("timeout", 90),
            cwd=args.get("project_dir"),
            extra_args=["--resume", str(session)],
        )
        return result["output"] if result["success"] else f"Error: {result['error']}"

    elif tool_name == "ask_gemini_sessions":
        result = call_gemini_list_sessions(cwd=args.get("project_dir"))
        return result["output"] if result["success"] else f"Error: {result['error']}"

    return f"Error: Unknown tool '{tool_name}'"


# ============================================
# MCP stdio Server
# ============================================
def run_mcp_server():
    """Run as MCP stdio server."""
    sys.stderr.write("Gemini Subagent MCP Server v2 started\n")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_mcp_request(request)
            if response:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError:
            sys.stderr.write(f"Invalid JSON: {line[:100]}\n")
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")


# ============================================
# CLI Mode (direct testing)
# ============================================
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != "--mcp":
        prompt = " ".join(sys.argv[1:])
        result = call_gemini(prompt)
        if result["success"]:
            print(result["output"])
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
    else:
        run_mcp_server()
