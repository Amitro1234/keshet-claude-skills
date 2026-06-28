# validate-skills.ps1
# Structural validator for keshet-claude-skills
# Run from the repo root: .\tools\validate-skills.ps1
# Checks every SKILL.md for required structure and produces a pass/fail report.

param(
    [string]$RepoRoot = (Split-Path $PSScriptRoot -Parent)
)

# ─── Required elements per skill type ────────────────────────────────────────

$RequiredSections = @(
    "## Purpose",
    "## Trigger Conditions",
    "## What NOT to do"
)

$RequiredOutputFormat = @(
    "PASS",
    "VERDICT"
)

$FrontmatterFields = @("name:", "description:")

# ─── Helpers ─────────────────────────────────────────────────────────────────

function Test-Frontmatter {
    param([string[]]$Lines)
    if ($Lines[0].Trim() -ne "---") { return $false }
    $closeIdx = ($Lines | Select-Object -Skip 1).IndexOf("---")
    return $closeIdx -ge 0
}

function Get-FrontmatterBlock {
    param([string[]]$Lines)
    if ($Lines[0].Trim() -ne "---") { return @() }
    $block = @()
    for ($i = 1; $i -lt $Lines.Count; $i++) {
        if ($Lines[$i].Trim() -eq "---") { break }
        $block += $Lines[$i]
    }
    return $block
}

function Test-Section {
    param([string[]]$Lines, [string]$Section)
    return ($Lines | Where-Object { $_ -match [regex]::Escape($Section) }).Count -gt 0
}

function Test-OutputFormat {
    param([string[]]$Lines)
    $content = $Lines -join "`n"
    foreach ($keyword in $RequiredOutputFormat) {
        if ($content -match $keyword) { return $true }
    }
    return $false
}

function Write-Pass { param([string]$msg) Write-Host "  [PASS] $msg" -ForegroundColor Green }
function Write-Fail { param([string]$msg) Write-Host "  [FAIL] $msg" -ForegroundColor Red }
function Write-Warn { param([string]$msg) Write-Host "  [WARN] $msg" -ForegroundColor Yellow }
function Write-Header { param([string]$msg) Write-Host "`n$msg" -ForegroundColor Cyan }

# ─── Find all SKILL.md files ──────────────────────────────────────────────────

$skillFiles = Get-ChildItem -Path $RepoRoot -Recurse -Filter "SKILL.md" | Sort-Object FullName

if ($skillFiles.Count -eq 0) {
    Write-Host "No SKILL.md files found under $RepoRoot" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor White
Write-Host "  keshet-claude-skills — Skill Validator" -ForegroundColor White
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm')" -ForegroundColor White
Write-Host "========================================" -ForegroundColor White
Write-Host "Repo root : $RepoRoot"
Write-Host "Skills found: $($skillFiles.Count)"

# ─── Validate each skill ──────────────────────────────────────────────────────

$totalPass = 0
$totalFail = 0
$totalWarn = 0
$failedSkills = @()

foreach ($file in $skillFiles) {
    $relativePath = $file.FullName.Replace($RepoRoot, "").TrimStart("\", "/")
    Write-Header "[$relativePath]"

    $lines = Get-Content $file.FullName -Encoding UTF8
    $content = $lines -join "`n"
    $filePass = $true

    # Check: not empty
    if ($lines.Count -lt 5) {
        Write-Fail "File is too short (< 5 lines) — likely empty or placeholder"
        $totalFail++
        $filePass = $false
        $failedSkills += $relativePath
        continue
    }

    # Check: YAML frontmatter
    if (Test-Frontmatter $lines) {
        $fm = Get-FrontmatterBlock $lines
        $fmText = $fm -join "`n"
        $hasFmIssue = $false
        foreach ($field in $FrontmatterFields) {
            if ($fmText -notmatch [regex]::Escape($field)) {
                Write-Fail "Frontmatter missing field: $field"
                $totalFail++
                $filePass = $false
                $hasFmIssue = $true
            }
        }
        if (-not $hasFmIssue) {
            Write-Pass "YAML frontmatter present with name + description"
            $totalPass++
        }
    } else {
        Write-Fail "Missing YAML frontmatter (---name:/description:---)"
        $totalFail++
        $filePass = $false
    }

    # Check: required sections
    foreach ($section in $RequiredSections) {
        if (Test-Section $lines $section) {
            Write-Pass "Section found: $section"
            $totalPass++
        } else {
            Write-Fail "Missing section: $section"
            $totalFail++
            $filePass = $false
        }
    }

    # Check: output format (PASS/VERDICT keyword — builder skills only)
    $isBuilderSkill = $relativePath -match "keshet-builder-skills"
    if ($isBuilderSkill) {
        if (Test-OutputFormat $lines) {
            Write-Pass "Output format block present (PASS/VERDICT keyword found)"
            $totalPass++
        } else {
            Write-Warn "No output format block found (expected PASS/VERDICT) — builder skills should have a review checklist"
            $totalWarn++
        }
    }

    # Check: minimum length (skills should have substance)
    $wordCount = ($content -split '\s+').Count
    if ($wordCount -lt 150) {
        Write-Warn "Skill is very short ($wordCount words) — may lack sufficient guidance"
        $totalWarn++
    } else {
        Write-Pass "Content length adequate ($wordCount words)"
        $totalPass++
    }

    # Check: contains a code example (most skills should have at least one)
    if ($content -match '```') {
        Write-Pass "Contains code/format examples"
        $totalPass++
    } else {
        Write-Warn "No code or format examples found — consider adding concrete examples"
        $totalWarn++
    }

    if (-not $filePass) {
        $failedSkills += $relativePath
    }
}

# ─── Summary ─────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "========================================" -ForegroundColor White
Write-Host "  SUMMARY" -ForegroundColor White
Write-Host "========================================" -ForegroundColor White
Write-Host "Skills validated : $($skillFiles.Count)"
Write-Host "Checks passed    : $totalPass" -ForegroundColor Green
Write-Host "Checks failed    : $totalFail" -ForegroundColor $(if ($totalFail -gt 0) { "Red" } else { "Green" })
Write-Host "Warnings         : $totalWarn" -ForegroundColor $(if ($totalWarn -gt 0) { "Yellow" } else { "Green" })

if ($failedSkills.Count -gt 0) {
    Write-Host ""
    Write-Host "Skills with failures:" -ForegroundColor Red
    foreach ($s in ($failedSkills | Sort-Object -Unique)) {
        Write-Host "  - $s" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "RESULT: NEEDS REVISION" -ForegroundColor Red
    exit 1
} else {
    Write-Host ""
    Write-Host "RESULT: ALL SKILLS PASS" -ForegroundColor Green
    exit 0
}
