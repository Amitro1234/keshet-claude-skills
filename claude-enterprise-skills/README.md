# Keshet Claude Enterprise — Cost Management Skills

Skills and tools for controlling Claude Enterprise spend at the organizational level.
Maintained by AI Architecture (Amit Rosen, CIO division).

---

## Repository structure

```
claude-enterprise-skills/
├── README.md                    ← this file
├── model-router-skill/
│   └── SKILL.md                 ← routes tasks to cheapest capable model (−35% on API)
├── context-hygiene/
│   └── SKILL.md                 ← prevents context bloat (−15% to −25%)
├── output-discipline/
│   └── SKILL.md                 ← reduces output token waste (−10% to −20%)
├── prompt-caching/
│   └── SKILL.md                 ← 90% discount on repeated context (NEW)
├── agentic-loop-guard/
│   └── SKILL.md                 ← prevents runaway agents from consuming budget (NEW)
└── batch-detector/
    └── SKILL.md                 ← routes jobs to Batch API (50% discount)
```

Also in this repository:
- `claude-enterprise-calculator.html` — standalone cost estimator and CAP planner

---

## Cost model

Claude Enterprise bills in two components:

```
Monthly Total = Seat Fees (fixed) + API Usage (variable)

Seat Fees  = (N_developers × $20) + (N_business × $10)
API Usage  = N_developers × adoption_rate × daily_cost × 22 days × concurrency_factor
```

**Concurrency factor** (0.75 for Keshet): not all users are active simultaneously.
Anthropic uses 0.55 for orgs >250 users, 0.45 for >500. At ~70 users, 0.75 is conservative.

**Daily cost benchmarks** (Anthropic official):
- Average developer day: $6
- Intensive developer day: $13

---

## Optimization layers

Each skill targets a different source of waste:

| Layer | Skill | Mechanism | Expected saving |
|---|---|---|---|
| 1 | model-router | Route tasks to cheapest capable model (Haiku → Sonnet → Opus) | −35% on API |
| 2 | context-hygiene | Exclude junk files, compress history, enforce per-file limits | −15% to −25% |
| 3 | output-discipline | Diffs over full files, no padding, proportional responses | −10% to −20% |
| 4 | prompt-caching | 90% discount on repeated context (Spec Pack, CLAUDE.md, schemas) | −10% to −30% |
| 5 | batch-detector | 50% Batch API discount on all non-real-time workloads | −5% to −15% |
| 6 | agentic-loop-guard | Checkpoints + hard stops prevent runaway agent spend | Prevents spikes |

Combined saving potential: **50–65%** vs. unoptimized baseline.

---

## Calculation methodology (calculator.html)

### Baseline scenario
No optimization applied. All API calls use whichever model the user defaults to,
full file outputs, no caching, all calls synchronous.

### Model Router scenario (−35% on API)
Assumes the model-router skill is active for all Claude Code users.
Based on empirical distribution: ~60% of tasks are Tier 1 (Haiku), ~35% Tier 2 (Sonnet),
~5% Tier 3 (Opus). Haiku costs $1/M input vs. Sonnet's $3/M — average blended cost
is ~65% of a pure-Sonnet baseline.

### Router + Caching scenario (−18% additional)
Context caching provides ~90% discount on repeated system prompt tokens.
Assumes a 50K-token system prompt hit 500 times/day across the dev team.
Cache writes cost 1.25× but break even after ~2 reads. The 18% figure accounts
for the fact that not all calls benefit from caching (one-off queries still pay full price).

### Full optimization scenario (−12% additional)
Batch API discount applied to pipeline and automation workloads.
Assumes 20–30% of developer API calls are non-interactive (CI, nightly jobs, evaluations).
50% discount on that fraction = ~12% reduction on total API costs.

---

## CAP configuration guide

Claude Enterprise supports three levels of spend limits:

### 1. Org-level cap
- Acts as a hard ceiling for the entire organization
- When reached: ALL users are blocked immediately
- Set this high enough that it is never hit under normal operation
- Recommended: Baseline × 1.2 (20% buffer)
- Use this as a safety net, not the primary control mechanism

### 2. Group-level cap
- Applies to a defined set of users (e.g., "Engineering", "Business")
- Primary control point — this is where you should manage spend actively
- Recommended for developers: variable API cost estimate × 1.15
- Recommended for business users: seat cost × 1.2

### 3. User-level cap
- Per-individual monthly limit
- Critical for preventing agentic loops from consuming org budget
- Recommended for developers: daily_intensity × 22 × 1.2
- Recommended for business users: $25–30/month

---

## Installation

### Per-project (Claude Code only)

Copy the skills you want into your project:

```
your-project/
└── .claude/
    └── skills/
        ├── context-hygiene/
        │   └── SKILL.md
        ├── output-discipline/
        │   └── SKILL.md
        └── batch-detector/
            └── SKILL.md
```

Reference the skills in your project's `CLAUDE.md`:

```markdown
## Active org skills

Before starting any task, the following org-level skills are active:
- Cost discipline: `.claude/skills/context-hygiene/SKILL.md`
- Output rules: `.claude/skills/output-discipline/SKILL.md`
- Batch routing: `.claude/skills/batch-detector/SKILL.md`
- Model selection: `.claude/skills/model-router-skill/SKILL.md`
```

### Global (applies to all projects on a machine)

Copy skills to:
- macOS/Linux: `~/.claude/skills/`
- Windows: `%USERPROFILE%\.claude\skills\`

Add references to `~/.claude/CLAUDE.md`.

