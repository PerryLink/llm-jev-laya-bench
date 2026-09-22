"""Structural diff of two JSON artifacts: field paths whose values differ.

Usage:
    python rerun/jsondiff.py <old.json> <new.json> [--max N] [--skip-prefix P ...]

Prints, for every leaf that differs, the JSON path and both values. Key ORDER and
timestamps are reported separately, because a re-run naturally changes mtime-derived
provenance fields while a measurement must not change.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

VOLATILE_HINTS = ("recorded_at", "timestamp", "generated_at", "mtime", "elapsed",
                  "latency", "cold_start", "uptime", "run_at", "wall", "duration")


def leaves(node, path="$"):
    """Yield (path, value) for every scalar leaf."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield from leaves(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from leaves(v, f"{path}[{i}]")
    else:
        yield path, node


def main() -> int:
    argv = sys.argv[1:]
    args, opts, i = [], [], 0
    while i < len(argv):
        if argv[i] == "--max":
            opts.append(argv[i])
            i += 1
        elif argv[i] == "--skip-prefix":
            opts.append(argv[i])
            i += 1
        elif argv[i].startswith("--"):
            opts.append(argv[i])
        else:
            args.append(argv[i])
        i += 1
    maxn = 200
    skip = []
    for j, o in enumerate(opts):
        if o == "--max" and j + 1 < len(opts):
            maxn = int(opts[j + 1])
        if o == "--skip-prefix" and j + 1 < len(opts):
            skip.append(opts[j + 1])
    old = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    new = json.loads(Path(args[1]).read_text(encoding="utf-8"))

    lo = dict(leaves(old))
    ln = dict(leaves(new))
    only_old = sorted(set(lo) - set(ln))
    only_new = sorted(set(ln) - set(lo))
    diffs = [(p, lo[p], ln[p]) for p in sorted(set(lo) & set(ln)) if lo[p] != ln[p]]
    diffs = [d for d in diffs if not any(d[0].startswith(s) for s in skip)]

    print(f"OLD {args[0]}")
    print(f"NEW {args[1]}")
    print(f"leaves: old={len(lo)} new={len(ln)}  differing={len(diffs)}  "
          f"only_in_old={len(only_old)}  only_in_new={len(only_new)}")
    vol = [d for d in diffs if any(h in d[0].lower() for h in VOLATILE_HINTS)]
    print(f"   of which path names suggest a volatile/provenance field: {len(vol)}")
    show = [d for d in diffs if d not in vol] + vol
    for p, a, b in show[:maxn]:
        print(f"  ~ {p}\n      old={json.dumps(a, ensure_ascii=False)[:200]}\n"
              f"      new={json.dumps(b, ensure_ascii=False)[:200]}")
    if len(show) > maxn:
        print(f"  ... {len(show) - maxn} more differing leaves suppressed")
    for p in only_old[:40]:
        print(f"  - only in OLD: {p} = {json.dumps(lo[p], ensure_ascii=False)[:160]}")
    for p in only_new[:40]:
        print(f"  + only in NEW: {p} = {json.dumps(ln[p], ensure_ascii=False)[:160]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
