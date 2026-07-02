#!/usr/bin/env python3
"""Aggregate .claude/compression-stats.jsonl into a summary table.

Usage: python enforcement/compression/report.py [path-to-stats.jsonl]

The 'TOTAL INVOCATIONS' line is the denominator — how many tool calls the
hook saw at all, compressed or not. Savings % without that number is
marketing, not measurement.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

DEFAULT_PATH = ".claude/compression-stats.jsonl"


def load(path):
    events = []
    p = Path(path)
    if not p.exists():
        return events
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue  # a torn/corrupt line shouldn't kill the report
        if isinstance(obj, dict):
            events.append(obj)
    return events


def summarize(events):
    total = len(events)
    per_kind = defaultdict(lambda: {"calls": 0, "raw": 0, "comp": 0, "errors": 0})
    skips = defaultdict(int)
    for e in events:
        if e.get("skipped"):
            skips[e["skipped"]] += 1
        kind = e.get("kind")
        if kind is None:
            continue
        row = per_kind[kind]
        row["calls"] += 1
        row["raw"] += e.get("raw_tokens_est") or 0
        row["comp"] += e.get("compressed_tokens_est") or 0
        if e.get("error"):
            row["errors"] += 1
    return total, dict(per_kind), dict(skips)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    events = load(path)
    total, per_kind, skips = summarize(events)
    print("=== Compression Report ===")
    print(f"Stats file        : {path}")
    print(f"TOTAL INVOCATIONS : {total}")
    if not per_kind:
        print("No parser-matched events yet.")
        return
    print(f"\n{'Kind':<12}{'Calls':>7}{'Raw tok':>10}{'Comp tok':>10}{'Saved':>8}{'Errors':>8}")
    t_raw = t_comp = t_errors = 0
    for kind in sorted(per_kind):
        r = per_kind[kind]
        saved = f"{-100 * (1 - r['comp'] / r['raw']):+.0f}%" if r["raw"] else "n/a"
        print(f"{kind:<12}{r['calls']:>7}{r['raw']:>10}{r['comp']:>10}{saved:>8}{r['errors']:>8}")
        t_raw += r["raw"]
        t_comp += r["comp"]
        t_errors += r["errors"]
    total_saved = f"{-100 * (1 - t_comp / t_raw):+.0f}%" if t_raw else "n/a"
    print(f"{'TOTAL':<12}{'':>7}{t_raw:>10}{t_comp:>10}{total_saved:>8}{t_errors:>8}")
    if skips:
        print("\nSkip reasons: " + ", ".join(f"{k}={v}" for k, v in sorted(skips.items())))


if __name__ == "__main__":
    main()
