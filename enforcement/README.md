# Keshet Rules — Enforcement Layer

This folder is the technical half of `docs/rules-policy.md`. The policy doc says *what* is required; this folder is *how much of it can actually be enforced, and with what config* — verified against current Claude Code hooks/permissions documentation (2026-07-01).

## Why two documents, not one

A rule that's only written in `CLAUDE.md` is an instruction Claude reads and (almost always) follows — but nothing stops a Builder from deleting that line, or Claude from making a judgment call under pressure. A rule enforced here is checked by Claude Code itself, independent of what any prompt says. `docs/rules-policy.md` states the org's actual policy; this folder implements the subset of it that's genuinely enforceable, and is explicit about the subset that isn't.

## The three enforcement tiers (weakest to strongest)

| Tier | Where it lives | Who can change it | Can a Builder bypass it? |
|---|---|---|---|
| **Instruction-level** | `CLAUDE.md`, skill files, system prompt | Anyone who can edit those files | Yes — it's guidance, not enforcement |
| **Project settings** | `.claude/settings.json` + `.claude/hooks/` in each Builder repo (`project-settings.example.json` here) | The Builder, but changes are visible in git history / PRs | Technically yes (they own the file), but it's auditable |
| **Managed settings** | (a) `managed-settings.json` on disk, pushed via any IT tooling (Intune/GPO/Jamf) — **works on any Claude plan, including Team**; or (b) server-managed push from the claude.ai admin console — requires Team or Enterprise, Team already qualifies | Only whoever controls IT deployment or the admin console (Admin Panel Owner / CISO) | **No** — this is the one tier Claude Code itself will not let a Builder override |

Only the managed tier is "cannot be bypassed" in the strict sense. Project-tier settings.json rules are still real enforcement (Claude Code itself blocks the action, not just a suggestion) — they're just editable by the person they're meant to constrain, so use them for things where visibility/audit is the goal, and reserve the managed tier for anything that must hold even against a compromised or careless Builder machine.

## What's genuinely hard-enforceable today, and what isn't

Verified against Claude Code's hooks and permissions docs:

- **Hard, via `permissions.deny` + managed settings:** blocking specific file-read patterns (`.env`, `.ssh/**`, `.aws/**`), blocking specific Bash command patterns (`git push --force`, `sudo *`, `curl | sh`), enforcing an MCP server allowlist (`allowedMcpServers` / `deniedMcpServers`).
- **Hard, via a `PreToolUse` hook (`pre_tool_use_guard.py`):** semantic checks a glob can't express — e.g. `cat .env` isn't a `Read` tool call, it's a `Bash` call, so the file-glob deny rule doesn't catch it; the hook inspects the command string instead. Same for MCP-tool-level allowlisting (a server can be "approved" but a specific tool on it might still need review) and destructive commands with unusual syntax. Covers both the `Bash` tool (POSIX/WSL) and the `PowerShell` tool (native Windows sessions) with separate pattern lists for each — the hook originally only matched `Bash`, which meant zero coverage on Windows Builder machines until this was fixed; the `PreToolUse` matcher in `project-settings.example.json` must include both tool names or the hook never runs for PowerShell calls at all.
- **Partially hard:** anything syntactic can be worked around by a sufficiently motivated Claude finding an alternate syntax (Python's `os.remove` instead of `rm`, a different MCP server that does the same thing). Layering settings.json + hooks closes most, not all, of this gap. This is exactly the limitation `company-agent-guardrails/SKILL.md` already states in its own text ("guardrail files guide behavior but do not enforce it at the OS level") — the hooks/settings layer is what actually closes part of that gap, but not all of it.
- **Not enforceable at all today, anywhere:** "announce the model tier before starting work" (`model-router-skill`'s core behavior) — there's no hook that fires at "before Claude starts reasoning about a task," only before/after specific tool calls. This stays instruction-level no matter what. Same for most of the FinOps skills' actual guidance (context hygiene, output discipline) — they shape *how* Claude behaves, not *what tools* it's allowed to call, so hooks/permissions have nothing to grab onto.
- **Cowork and Claude.ai Chat have neither hooks nor settings.json.** Everything in this folder applies to Claude Code CLI on Builder machines only. For Cowork/Safe-Use users, the only real technical enforcement points are: which MCP connectors are enabled for their workspace (an admin-console setting, not a file here), and the sandboxed-VM isolation Cowork already provides by default. Everything else for that population is instruction-level (`CLAUDE.md`, skill guidance) — see `docs/rules-policy.md` §4 for what that means in practice.

## Files here

- `managed-settings.example.json` — deploy via IT tooling (any plan) or Claude admin console (Team+). Locks the MCP allowlist and the hard security denies org-wide.
- `project-settings.example.json` — ship this as the default `.claude/settings.json` in the org repo template (Builder Flow Step 3), covers the "Ask" tier (git push, deploys, installs, migrations) plus wires in the hook below.
- `hooks/pre_tool_use_guard.py` — the semantic hook referenced from `project-settings.example.json`. Copy to `.claude/hooks/pre_tool_use_guard.py` in the org template repo.
- `hooks/post_tool_use_compressor.py` — PostToolUse hook that compresses verbose Bash output (git status/diff/log, pytest, npm test, eslint, ruff) before it enters Claude's context. Fail-open: any parser error means untouched passthrough, never altered output. Opt-in per project via the PostToolUse block in `project-settings.example.json`. Design: `docs/superpowers/specs/2026-07-02-command-output-compressor-design.md`.
- `compression/` — the parser package behind the hook above (`dispatch.py` routing, `formats/` parsers, `stats.py` local JSONL logging, `report.py` savings report, `tests/` incl. golden-file no-information-loss tests). Deploy alongside the hook: copy to `.claude/compression/`. In the target project, add `.claude/compression-stats.jsonl` to that project's `.gitignore` (it's per-machine measurement data, not shared state), and run `python .claude/compression/report.py` from the project root (the stats path is CWD-relative).
- `tests/test_pre_tool_use_guard.py` — real, automated, repeatable tests for the hook above (33 cases, including PowerShell-tool coverage and the broadened `rm -rf` destructive-target checks; run with `python3 tests/test_pre_tool_use_guard.py` or via pytest). Includes one intentional `xfail` documenting a known bypass (obfuscated `.env` reads via inline Python) rather than hiding it. **Run this after every edit to the hook or to `docs/approved-mcp-connectors.md`.**
- `tests/behavioral-scenarios.md` — the non-executable counterpart: scenario tests for skills that are advisory-only (no hook/settings.json backing). 3 scenarios validated 2026-07-01 (security-secret-catch, spec-pack-gate, model-router+connector-block — all passed), 4 more scaffolded for the next pass.

## Runtime prerequisite on Builder machines

Both hooks (`pre_tool_use_guard.py`, `post_tool_use_compressor.py`) run on
Python — meaning **every Builder machine needs a Python interpreter
installed, regardless of what language the Builder's own project uses** (a
C#/Node Builder still needs Python for the enforcement layer). Add this to
the Builder Flow Step 2 (Local environment) checklist.

Three ways to remove or soften that dependency, if it becomes a rollout
blocker:

1. **Ship the runtime with the artifact (no rewrite):** Python's official
   "embeddable package" for Windows (~15 MB of files, no installer, no
   admin rights, no PATH changes) can be dropped into `.claude/runtime/`
   and the hook command pointed at `.claude/runtime/python.exe`. Removes
   the installation dependency entirely while keeping the existing code
   and tests.
   **Validated 2026-07-02** with a self-built portable copy (the corporate
   proxy blocks the python.org zip — IT will need to whitelist or mirror
   it for real distribution; the interim recipe that produced identical
   results: copy `python.exe`, `python3.dll`, `python312.dll`,
   `vcruntime140*.dll`, `DLLs\`, and `Lib\` **excluding site-packages**
   from an existing install — 70 MB vs ~1 GB installed): hook runs
   end-to-end, all 9 integration tests + all 33 guard tests pass on the
   portable runtime, and bare-startup latency measured ~1.0-1.5s — at or
   below the installed interpreter, even though `.claude\runtime\` is NOT
   in the Trend Real-Time exclusion (caveat: AV verdict cache was warm
   from the copy itself; re-measure after a reboot before quoting these
   numbers). If this becomes the deployment mechanism, ask security to
   extend the Real-Time exclusion to the deployed `.claude\runtime\` path.
   The runtime directory is gitignored — it's a deploy artifact, never
   repo content.
2. **Use what Windows already has (rewrite to PowerShell):** zero install
   on the org's primary platform, but `powershell.exe` startup (-NoProfile
   still pays .NET init + the same EDR process tax) is typically no faster
   than Python here, PS 5.1 quirks apply, and all parser code + tests
   would need porting. Weakest option.
3. **Compiled static binary (Go/Rust):** one self-contained .exe, no
   runtime at all — the cleanest "works regardless of installed languages"
   answer, already discussed under open item 4. Pays the build-pipeline,
   signing, and code-transparency costs listed there, and still sits on
   the ~1s per-process floor this machine showed.

Recommendation: option 1 (embeddable runtime) is the cheap, immediate
answer to "generic across Builder machines" — it turns deployment into
pure file-copy with zero prerequisites and postpones the binary question
until Phase 1 data justifies it.

## Open items before this is production-ready

1. **MCP allowlist duplication risk:** the approved-connector list is now hand-maintained in three places — `docs/approved-mcp-connectors.md` (source of truth), `managed-settings.example.json`, and `pre_tool_use_guard.py`. If one is updated and the others aren't, they drift silently. Worth writing a small script that generates the JSON/Python list from the markdown table so there's one source of truth — flagging this rather than building it now, since it's a repo-tooling decision, not a policy one.
2. **Schema verification:** the exact hook stdin JSON shape and the managed-settings key names were verified against Claude Code docs as of 2026-07-01 but this is an area that changes; confirm against `https://code.claude.com/docs/en/hooks` and `https://code.claude.com/docs/en/admin-setup` before deploying to real Builder machines, and definitely before deploying the managed tier (a typo'd key there could silently do nothing rather than error).
3. **The hook itself is now unit-tested (`tests/test_pre_tool_use_guard.py`, 33/33 passing) and 3 of the advisory skills have been behaviorally validated (`tests/behavioral-scenarios.md`)** — but none of this has run inside a real Claude Code CLI session on an actual Builder machine yet, only via direct subprocess calls and simulated sessions. Recommend a dry run on one Builder machine (`.claude/settings.json` only, no managed tier yet) before wider rollout. **This is doubly important on Windows**: `project-settings.example.json`'s hook command (`python3 ...`) assumes a `python3` alias that stock Windows doesn't ship by default — verify the interpreter invocation resolves on an actual Windows Builder machine before rollout, not just that the JSON schema is valid (see `_comment_5` in that file).
4. **Compressor Phase 1 gates not yet measured on a real machine:** the spec defines four success criteria (≥60% savings on covered commands, ≤100ms p95 hook overhead including Python startup, zero information loss, <1% parser error rate). The golden-file tests cover criterion 3 structurally (plus a passed task-outcome parity check: a blind agent given compressed-only pytest output correctly identified both failures, exact file:line, and root causes); criteria 1, 2, and 4 need a week of real Builder-session stats (`python enforcement/compression/report.py`) before org-wide rollout. **⚠ Latency baseline + root-cause diagnosis (2026-07-02, Windows 11 corporate machine, CPython 3.12):** hook invocation ≈2-3.3s end-to-end — but bare `python -c "pass"` is ≈3.6s and even a native exe spawn (`cmd /c exit`, `git --version`) is ≈0.8-1.0s on the same machine. Breakdown: ~0.9s is a per-process tax every new process pays (almost certainly EDR real-time scanning), and ~2.7s is Python interpreter startup amplified by EDR scanning every DLL/pyd Python opens. **Implications:** (a) this is a fleet/machine issue, not hook code — parser work is negligible; (b) it equally affects the existing `pre_tool_use_guard.py` on every call; (c) even a compiled Go/Rust rewrite would only reach the ~1s native-spawn floor on this machine — no per-call hook implementation can meet 100ms here. Mitigation order: (1) measure on 1-2 real Builder machines — this laptop's EDR profile may be an outlier; (2) if fleet-wide, evaluate a narrow EDR exclusion for the `.claude\hooks\` path with the CISO (note: the guard hook is itself a security control — the exclusion serves the defense layer); (3) only then consider a compiled-binary rewrite; (4) apply a split cost-benefit: the guard's latency buys security (risk decision), the compressor's latency must be paid back by measured token savings (economics decision — the per-event `duration_ms` + report data answer this). **Exclusion test result (2026-07-02, Trend Micro, Real-Time Scan exclusion on the Python install dir, approved by security):** bare python 3.6s → ~1.4-2.1s (≈50% recovered; control `cmd /c exit` unchanged at ~1s, confirming the exclusion was correctly scoped). The remaining ~1s is the per-process tax every new process pays — likely Trend's Behavior Monitoring layer, a separate exclusion category from Real-Time Scan; that's the next lever if sub-second latency is required. Note: the exclusion covers real-time only — scheduled scans still cover the excluded path, which keeps the security posture reasonable.
