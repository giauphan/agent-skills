#!/usr/bin/env python3
"""
MCP Server: Gemini CLI Subagent
================================
Wraps Gemini CLI as an MCP tool so any MCP-compatible agent
(Claude Code, Cursor, Antigravity, etc.) can call it natively
via Function Calling instead of shell parsing.

Usage:
  # Register in Claude Code's MCP config:
  {
    "mcpServers": {
      "gemini-subagent": {
        "command": "python3",
        "args": ["path/to/mcp_gemini_subagent.py"]
      }
    }
  }

  # Or run standalone for testing:
  python3 mcp_gemini_subagent.py
"""

import subprocess
import json
import sys
import os
import re
from typing import Optional


def clean_gemini_output(raw: str) -> str:
    """Remove Gemini CLI boilerplate from output."""
    lines = raw.split("\n")
    cleaned = []
    skip_patterns = [
        "YOLO mode",
        "Ripgrep is not",
        "Falling back to",
        "_GaxiosError",
        "at Gaxios",
        "at async",
        "at process",
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
    for line in lines:
        if any(p in line for p in skip_patterns):
            continue
        # Skip JSON error blocks
        if line.strip().startswith('"error"') or line.strip().startswith('"code"'):
            continue
        cleaned.append(line)

    return "\n".join(cleaned).strip()


def call_gemini(prompt: str, timeout: int = 90, cwd: Optional[str] = None) -> dict:
    """
    Call Gemini CLI and return structured result.

    Args:
        prompt: The prompt to send to Gemini CLI
        timeout: Max seconds to wait (default: 90)
        cwd: Working directory for file-aware prompts

    Returns:
        dict with 'success', 'output', 'error', 'raw_output'
    """
    env = os.environ.copy()
    env["GEMINI_CLI_TRUST_WORKSPACE"] = "true"

    cmd = ["gemini", "--yolo", "-p", prompt]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or os.getcwd(),
            env=env,
        )

        raw = result.stdout + result.stderr
        cleaned = clean_gemini_output(raw)

        # Check for rate limit
        if "429" in raw and "RESOURCE_EXHAUSTED" in raw:
            return {
                "success": False,
                "output": "",
                "error": "Rate limited (429). Wait 30-60 seconds and retry.",
                "raw_output": raw[:500],
            }

        # Check for trust error
        if "not running in a trusted directory" in raw:
            return {
                "success": False,
                "output": "",
                "error": "Workspace not trusted. Run: export GEMINI_CLI_TRUST_WORKSPACE=true",
                "raw_output": raw[:500],
            }

        return {
            "success": True,
            "output": cleaned,
            "error": None,
            "raw_output": raw[:500] if len(raw) > 500 else raw,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": f"Timeout after {timeout}s. Simplify prompt or increase timeout.",
            "raw_output": "",
        }
    except FileNotFoundError:
        return {
            "success": False,
            "output": "",
            "error": "Gemini CLI not found. Install: npm i -g @google/gemini-cli",
            "raw_output": "",
        }


# ============================================
# MCP Server Protocol (stdio JSON-RPC)
# ============================================
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
                "serverInfo": {
                    "name": "gemini-subagent",
                    "version": "1.0.0",
                },
            },
        }

    elif method == "notifications/initialized":
        return None  # No response needed for notifications

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "ask_gemini",
                        "description": "Ask Gemini CLI a question or give it a task. Use for second opinions, code review, image analysis, or cross-model verification. Gemini can read files in the current project directory.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "description": "The prompt/question to send to Gemini",
                                },
                                "timeout": {
                                    "type": "integer",
                                    "description": "Max seconds to wait (default: 90)",
                                    "default": 90,
                                },
                                "project_dir": {
                                    "type": "string",
                                    "description": "Project directory for file-aware prompts (optional)",
                                },
                            },
                            "required": ["prompt"],
                        },
                    },
                    {
                        "name": "ask_gemini_review",
                        "description": "Ask Gemini CLI to review code changes. Automatically includes file reading instructions.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Path to the file to review",
                                },
                                "focus": {
                                    "type": "string",
                                    "description": "What to focus on: 'bugs', 'security', 'performance', 'style', or 'all'",
                                    "default": "all",
                                },
                            },
                            "required": ["file_path"],
                        },
                    },
                ]
            },
        }

    elif method == "tools/call":
        tool_name = request.get("params", {}).get("name", "")
        args = request.get("params", {}).get("arguments", {})

        if tool_name == "ask_gemini":
            result = call_gemini(
                prompt=args.get("prompt", ""),
                timeout=args.get("timeout", 90),
                cwd=args.get("project_dir"),
            )
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result["output"]
                            if result["success"]
                            else f"Error: {result['error']}",
                        }
                    ]
                },
            }

        elif tool_name == "ask_gemini_review":
            file_path = args.get("file_path", "")
            focus = args.get("focus", "all")
            prompt = f"Read the file '{file_path}' and review it. Focus on: {focus}. List issues with line numbers."
            result = call_gemini(prompt=prompt, timeout=120)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result["output"]
                            if result["success"]
                            else f"Error: {result['error']}",
                        }
                    ]
                },
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"},
    }


def run_mcp_server():
    """Run as MCP stdio server."""
    sys.stderr.write("Gemini Subagent MCP Server started\n")
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
# CLI Mode (for direct testing)
# ============================================
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != "--mcp":
        # Direct CLI mode: python3 mcp_gemini_subagent.py "prompt"
        prompt = " ".join(sys.argv[1:])
        result = call_gemini(prompt)
        if result["success"]:
            print(result["output"])
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
    else:
        # MCP server mode
        run_mcp_server()
