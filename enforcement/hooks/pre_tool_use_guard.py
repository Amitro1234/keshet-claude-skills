#!/usr/bin/env python3
"""
Keshet PreToolUse guard hook.

Purpose
-------
Semantic checks that plain settings.json glob rules can't express:
  1. Block MCP tool calls to connectors not on docs/approved-mcp-connectors.md,
     even if the *server* name looks fine but the specific tool/scope doesn't.
  2. Block shell commands that read/print secret-like files by content
     pattern, not just by filename (settings.json already denies Read(.env)
     etc. -- this catches `cat .env`, `grep -r API_KEY .`, `printenv`,
     base64 tricks, and their PowerShell equivalents like `Get-Content .env`
     or `Select-String -Pattern API_KEY`).
  3. Block destructive-by-semantics shell commands that don't match a simple
     glob (alternate syntaxes for rm -rf, disk formatting, history wiping,
     and PowerShell equivalents like `Remove-Item -Recurse -Force`).

Covers both the "Bash" tool (POSIX/WSL sessions) and the "PowerShell" tool
(native Windows sessions). Each has its own pattern lists below -- a pattern
tuned for one shell's syntax will not match the other, so both need upkeep.

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
# Bash/POSIX shells.
SECRET_CONTENT_PATTERNS = [
    r"\bcat\s+.*\.env",
    r"\bgrep\s+.*(API_KEY|SECRET|PASSWORD|TOKEN|PRIVATE_KEY)",
    r"\bprintenv\b",
    r"\benv\s*\|\s*grep",
    r"\bbase64\s+.*\.env",
    r"\baws\s+configure\s+list\b",
]

# Destructive commands that don't fit a clean settings.json glob. Bash/POSIX.
# NOTE: the original rm -rf pattern only matched a bare "rm -rf /" (root,
# nothing after). "rm -rf /home", "rm -rf /etc", "rm -rf ~", "rm -rf .",
# "rm -rf $HOME" are equally destructive and were previously (wrongly)
# allowed through -- see enforcement/README.md. This deliberately does NOT
# block every "rm -rf <relative-subpath>" (e.g. "rm -rf ./node_modules" is a
# normal, safe operation and must stay allowed -- see test suite).
_RM_RF = r"\brm\s+-[a-z]*r[a-z]*f[a-z]*\s+"
DESTRUCTIVE_PATTERNS = [
    _RM_RF + r"/\s*($|\s)",                            # rm -rf / (bare root)
    _RM_RF + r"/(bin|boot|dev|etc|home|lib|lib64|opt|proc|root|sbin|srv|sys|usr|var)(/\S*)?\s*($|\s)",
    _RM_RF + r"~(/\S*)?\s*($|\s)",                     # rm -rf ~ or ~/anything
    _RM_RF + r"\.\s*($|\s)",                           # rm -rf . (cwd wipe)
    _RM_RF + r"\.\.\s*($|\s)",                          # rm -rf .. (parent wipe)
    _RM_RF + r"\$HOME\b",                              # rm -rf $HOME
    r"\bmkfs\.",                                      # format a filesystem
    r"\bdd\s+if=.*of=/dev/",                          # raw disk write
    r":\(\)\{\s*:\|:&\s*\};:",                        # fork bomb
    r"\bhistory\s+-c\b",
    r"\bshred\s+",
]

# Same two categories, for the PowerShell tool. Claude Code exposes a
# distinct "PowerShell" tool on Windows sessions (see PowerShell tool docs);
# the checks above only ever fired on tool_name == "Bash", so a Windows
# Builder session had no coverage at all until this was added.
SECRET_CONTENT_PATTERNS_PWSH = [
    r"\bGet-Content\s+.*\.env",
    r"\btype\s+.*\.env",
    r"\bSelect-String\s+.*(API_KEY|SECRET|PASSWORD|TOKEN|PRIVATE_KEY)",
    r"\bgci\s+env:",
    r"\bGet-ChildItem\s+env:",
    r"(?<!\$)\benv:\w*(API_KEY|SECRET|PASSWORD|TOKEN)",
    r"\[Environment\]::GetEnvironmentVariables",
]

# Deliberately stricter than the Bash rm -rf patterns: this blocks EVERY
# `Remove-Item -Recurse -Force`, including scoped ones like `.\node_modules`,
# rather than trying to allowlist "safe" relative targets. Two reasons:
#   1. The environment's own Bash tool documentation says Bash runs Git Bash
#      (POSIX sh) even on Windows -- so a routine scoped recursive delete
#      (e.g. clearing node_modules) has a working non-blocked path via the
#      Bash tool's `rm -rf`. PowerShell's Remove-Item is the less-common
#      route and mostly shows up for Windows-specific targets, which skews
#      the risk/annoyance tradeoff toward blocking.
#   2. Replicating the Bash allowlist logic (block absolute/home/system
#      roots, allow relative subpaths) in PowerShell syntax is meaningfully
#      harder to get right with a plain regex (drive letters, UNC paths,
#      $env: expansions) -- a stricter blanket rule is safer than a shakier
#      attempt at parity. Revisit if this proves too disruptive in practice.
DESTRUCTIVE_PATTERNS_PWSH = [
    r"\bRemove-Item\b.*-Recurse\b.*-Force\b",
    r"\bRemove-Item\b.*-Force\b.*-Recurse\b",
    r"\brd\s+/s\s+/q\b",                              # cmd-style recursive delete
    r"\bFormat-Volume\b",
    r"\bClear-History\b",
    r"\bRemove-Item\s+Env:",
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

    # --- 2 & 3. Shell command content checks ------------------------------
    # Claude Code exposes more than one shell-execution tool -- "Bash" on
    # POSIX/WSL sessions, "PowerShell" on native Windows sessions (this org's
    # primary platform per templates/global.CLAUDE.md). Both need the same
    # secret-content / destructive-command coverage; only checking "Bash"
    # left every Windows Builder session with zero enforcement.
    SHELL_PATTERNS = {
        "Bash": (SECRET_CONTENT_PATTERNS, DESTRUCTIVE_PATTERNS),
        "PowerShell": (SECRET_CONTENT_PATTERNS_PWSH, DESTRUCTIVE_PATTERNS_PWSH),
    }

    if tool_name in SHELL_PATTERNS:
        command = str(tool_input.get("command", ""))
        secret_patterns, destructive_patterns = SHELL_PATTERNS[tool_name]

        for pattern in secret_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                deny(
                    "SECURITY_BLOCK: SECRET_EXPOSURE -- this command appears to "
                    "read or print secret-like content. Blocked per "
                    "keshet-builder-skills/security/SKILL.md. If this is a false "
                    "positive, ask a human to run it manually outside Claude's "
                    "context."
                )
                return

        for pattern in destructive_patterns:
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
