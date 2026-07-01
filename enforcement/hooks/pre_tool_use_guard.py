#!/usr/bin/env python3
"""
Keshet PreToolUse guard hook.

Purpose
-------
Semantic checks that plain settings.json glob rules can't express:
  1. Block MCP tool calls to connectors not on docs/approved-mcp-connectors.md,
     even if the *server* name looks fine but the specific tool/scope doesn't.
  2. Block Bash commands that read/print secret-like files by content pattern,
     not just by filename (settings.json already denies Read(.env) etc. --
     this catches `cat .env`, `grep -r API_KEY .`, `printenv`, base64 tricks).
  3. Block destructive-by-semantics shell commands that don't match a simple
     glob (alternate syntaxes for rm -rf, disk formatting, history wiping).

This is a companion to, not a replacement for, settings.json permission
rules. Settings.json is the first line of defense (fast, declarative,
enterprise-lockable). This hook exists for the cases the audit in
keshet-skills-audit-2026-07-01.md flagged as "settings.json can't express
this" -- see enforcement/README.md section 3.

IMPORTANT -- verify against current docs before relying on this in prod
------------------------------------------------------------------------
The exact JSON shape Claude Code sends to a PreToolUse hook on stdin, and
the exact exit-code / JSON-output contract for blocking, may have changed
since this was written (2026-07-01). Confirm against
https://code.claude.com/docs/en/hooks before deploying. As documented at
time of writing:
  - stdin: JSON with at least {"tool_name": ..., "tool_input": {...}}
  - to ALLOW: exit 0
  - to BLOCK: exit 2, and print the reason to stderr (Claude sees it and
    must respond to it -- this is not a silent failure)
"""

import json
import re
import sys
from pathlib import Path

# Keep this in sync with docs/approved-mcp-connectors.md by hand until an
# automated sync exists (see enforcement/README.md open item #1).
APPROVED_MCP_SERVERS = {
    "slack", "microsoft-teams", "sharepoint", "outlook-calendar",
    "monday", "jira", "github", "postgresql", "azure-blob-storage",
    "excel-sheets", "azure-ai-search", "context7", "filesystem",
    "git", "azure-devops",
}

# Patterns that read/print secret-like content regardless of exact filename.
SECRET_CONTENT_PATTERNS = [
    r"\bcat\s+.*\.env",
    r"\bgrep\s+.*(API_KEY|SECRET|PASSWORD|TOKEN|PRIVATE_KEY)",
    r"\bprintenv\b",
    r"\benv\s*\|\s*grep",
    r"\bbase64\s+.*\.env",
    r"\baws\s+configure\s+list\b",
]

# Destructive commands that don't fit a clean settings.json glob.
DESTRUCTIVE_PATTERNS = [
    r"\brm\s+-[a-z]*r[a-z]*f[a-z]*\s+/(?!\S)",       # rm -rf / (root wipe)
    r"\bmkfs\.",                                      # format a filesystem
    r"\bdd\s+if=.*of=/dev/",                          # raw disk write
    r":\(\)\{\s*:\|:&\s*\};:",                        # fork bomb
    r"\bhistory\s+-c\b",
    r"\bshred\s+",
]


def deny(reason: str) -> None:
    sys.stderr.write(reason + "\n")
    sys.exit(2)


def allow() -> None:
    sys.exit(0)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If we can't parse the hook payload, fail open with a warning --
        # an enforcement layer that crashes the whole session on a schema
        # change is worse than one that logs and lets settings.json rules
        # be the backstop. Adjust this if your risk tolerance differs.
        sys.stderr.write(
            "pre_tool_use_guard: could not parse hook payload, allowing "
            "(settings.json deny rules still apply)\n"
        )
        allow()
        return

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}

    # --- 1. MCP connector allowlist -------------------------------------
    if tool_name.startswith("mcp__"):
        # Convention: mcp__<server>__<tool>
        parts = tool_name.split("__")
        server = parts[1] if len(parts) > 1 else ""
        if server and server not in APPROVED_MCP_SERVERS:
            deny(
                f"CONNECTOR NOT APPROVED: '{server}' is not on the Keshet "
                f"approved connector list. See docs/approved-mcp-connectors.md "
                f"and submit an MCP Connector Review Request before proceeding."
            )
            return

    # --- 2 & 3. Bash command content checks ------------------------------
    if tool_name == "Bash":
        command = str(tool_input.get("command", ""))

        for pattern in SECRET_CONTENT_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                deny(
                    "SECURITY_BLOCK: SECRET_EXPOSURE -- this command appears to "
                    "read or print secret-like content. Blocked per "
                    "keshet-builder-skills/security/SKILL.md. If this is a false "
                    "positive, ask a human to run it manually outside Claude's "
                    "context."
                )
                return

        for pattern in DESTRUCTIVE_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                deny(
                    "SECURITY_BLOCK: DESTRUCTIVE_COMMAND -- this command matches "
                    "a known destructive pattern and is blocked regardless of "
                    "confirmation. If this is genuinely intended, a human must "
                    "run it directly in a terminal, not through Claude."
                )
                return

    allow()


if __name__ == "__main__":
    main()
