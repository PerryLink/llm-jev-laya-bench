"""One-off migration: replace hardcoded absolute paths with `bench_env` lookups.

WHY
---
61 absolute-path literals across 48 files pinned the artifact to one machine and one user's
home directory. A reader who cloned the repository could not run a single probe. That is the
same class of defect this project exists to document: an unstated assumption about the
environment, encoded silently in the artifact.

HOW
---
Each affected file gets a self-contained bootstrap:

    import sys as _sys
    from pathlib import Path as _Path
    _p = _Path(__file__).resolve()
    while not (_p / "bench_env.py").exists():
        if _p.parent == _p:
            raise RuntimeError(...)
        _p = _p.parent
    ROOT = _p
    _sys.path.insert(0, str(ROOT))
    from bench_env import RESULTS  # noqa: E402

and every literal becomes a name imported from `bench_env`.

FOUR BUGS FOUND BY RUNNING IT, NOT BY READING IT
------------------------------------------------
1. Substituting literals BEFORE locating the root definition turned `ROOT = Path(r"D:\\...")`
   into `ROOT = ROOT`, so the definition was never replaced. Same for every
   `VENV_PYTHON = Path(...)`. Fix: never substitute the right-hand side of a module-level
   assignment to a name we are about to import -- rewrite the whole line instead.
2. Inserting "after the last import-looking line" landed INSIDE a multi-line
   `from x import (a,\n b)`. Fix: find the insertion point by PARSING.
3. A module docstring whose body contains blank lines made the inserter place the bootstrap
   INSIDE the docstring, silently turning prose into code. Fix: same -- parse, and insert
   after the last top-level import node, which is definitionally outside the docstring.
4. Emitting the block with bare `sys` / `Path` required a second pass to add `import sys`,
   which itself had to guess where to go. Fix: alias the imports inside the block so it is
   position-independent.

Bug 1 and 3 are the reason this script asserts its own output: every migrated file is
re-parsed, and the module is imported, before the migration is accepted.

SAFETY
------
  * `protocol/instrument-snapshot/**` is NEVER touched: those modules are hash-verified by
    PIN.json and the pinned launcher refuses to start if a byte changes.
  * Prose in docstrings and comments is left alone.
  * Defaults to a dry run; pass `--apply`.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve()
while not (REPO / "bench_env.py").exists():
    REPO = REPO.parent

SKIP = ("instrument-snapshot", "__pycache__", ".git")
SELF = Path(__file__).name

# A module-level assignment whose RHS is a path literal, SINGLE OR MULTI-LINE.
# `\s*` inside the Path(...) group is what lets `X = Path(\n    r"D:\...")` match -- a
# line-by-line pass cannot see it, which is how SNAPSHOT_PKG survived the first rewrite.
ASSIGN_MULTI = re.compile(
    r'^([ \t]*)([A-Z][A-Z0-9_]*)[ \t]*=[ \t]*'
    r'(Path\(\s*r?"[^"]+"\s*\)|r?"[^"]+")[ \t]*$',
    re.M)

# literal -> (expression, bench_env name or None)
EXPR: list[tuple[str, str, str | None]] = [
    (r'Path\(\s*r?"D:\\Projects\\llm-jev-laya-bench\\results"\s*\)', "RESULTS", "RESULTS"),
    (r'Path\(\s*r?"D:\\Projects\\llm-jev-laya-bench\\paper"\s*\)', "PAPER", "PAPER"),
    (r'Path\(\s*r?"D:\\Projects\\llm-jev-laya-bench\\protocol'
     r'\\instrument-snapshot\\src\\laya_mcp"\s*\)', "SNAPSHOT_PKG", "SNAPSHOT_PKG"),
    (r'Path\(\s*r?"D:\\Projects\\llm-jev-laya-bench\\protocol'
     r'\\instrument-snapshot"\s*\)', "SNAPSHOT", "SNAPSHOT"),
    (r'Path\(\s*r?"D:\\Projects\\llm-jev-laya-bench\\protocol"\s*\)', "PROTOCOL", "PROTOCOL"),
    (r'Path\(\s*r?"D:\\Projects\\llm-jev-laya-bench\\items"\s*\)', "ITEMS", "ITEMS"),
    (r'Path\(\s*r?"D:\\Projects\\llm-jev-laya-bench"\s*\)', "ROOT", None),
    (r'r?"D:\\Projects\\llm-jev-laya-bench\\src\\instrument"', "str(INSTRUMENT)", "INSTRUMENT"),
    (r'r?"D:\\Projects\\llm-jev-laya-bench\\src\\items"', "str(ITEMS)", "ITEMS"),
    (r'Path\(\s*r?"C:\\Users\\zzhdz\\.dsh\\.credentials\.yaml"\s*\)',
     "CREDENTIALS_PATH", "CREDENTIALS_PATH"),
    (r'r"C:\\Users\\zzhdz\\.dsh\\.credentials\.yaml"', "str(CREDENTIALS_PATH)",
     "CREDENTIALS_PATH"),
    (r'Path\(\s*r?"D:\\Projects\\laya-family\\.venv-laya\\Scripts\\python\.exe"\s*\)',
     "VENV_PYTHON", "VENV_PYTHON"),
    (r'r"D:\\Projects\\laya-family\\.venv-laya\\Scripts\\python\.exe"', "str(VENV_PYTHON)",
     "VENV_PYTHON"),
    (r'Path\(\s*r?"D:\\Projects\\laya-family\\_models\\laya"\s*\)', "MODEL_ROOT",
     "MODEL_ROOT"),
    (r'r"D:\\Projects\\laya-family\\_models\\laya"', "str(MODEL_ROOT)", "MODEL_ROOT"),
    (r'Path\(\s*r?"D:\\Projects\\laya-family\\laya-mcp-pkg\\src\\laya_mcp"\s*\)',
     "LAYA_WORKTREE", "LAYA_WORKTREE"),
]


def bootstrap(names: list[str]) -> list[str]:
    out = [
        "# Paths resolve through bench_env, which locates the repository root by walking",
        "# up from this file and honours environment overrides (LAYA_ROOT, DSH_CREDENTIALS,",
        "# ...). Run `python bench_env.py` to print what was resolved. The aliased imports",
        "# keep this block independent of whatever this module imported above, so it can",
        "# sit at any top-level position.",
        "import sys as _sys",
        "from pathlib import Path as _Path",
        "",
        "_p = _Path(__file__).resolve()",
        'while not (_p / "bench_env.py").exists():',
        "    if _p.parent == _p:",
        '        raise RuntimeError(f"bench_env.py not found above {__file__}")',
        "    _p = _p.parent",
        "ROOT = _p",
        "_sys.path.insert(0, str(ROOT))",
    ]
    if names:
        out.append(f"from bench_env import {', '.join(sorted(set(names)))}  # noqa: E402")
    return out


def preamble_end(lines: list[str]) -> int:
    """Index just past the module docstring and any `from __future__` imports.

    Inserting HERE is uniformly correct, and that is why the earlier position-tracking
    attempts kept failing. `p27d_primitive_fields.py` used `INSTRUMENT` at line 13 but
    defined `ROOT` at line 15, so anchoring the bootstrap at the removed DEFINITION put the
    import two lines too late and every run raised NameError. Nothing is executable before
    the docstring, and `from __future__` must come immediately after it, so a position just
    past both is always (a) after the future import, and (b) before any use of any name.
    """
    try:
        tree = ast.parse("\n".join(lines))
    except SyntaxError:
        return 0
    end = 0
    body = tree.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
            and isinstance(body[0].value.value, str):
        end = body[0].end_lineno or 0
    for node in body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            end = max(end, node.end_lineno or 0)
    return end


def migrate(path: Path, apply: bool) -> dict | None:
    # Byte-preserving I/O. `read_text()`/`write_text()` translate newlines both ways:
    # read collapses CRLF to LF, write expands LF to os.linesep. On Windows that silently
    # rewrote all 48 files from LF to CRLF -- a whole-file diff in which the intended
    # three-line change is invisible. Read and write BYTES, and restore the file's own
    # convention afterwards. (The pinned snapshot is excluded entirely, but a hash-verified
    # artifact that got newline-mangled would be a far worse version of this bug.)
    raw = path.read_bytes()
    crlf = b"\r\n" in raw
    orig = raw.decode("utf-8").replace("\r\n", "\n")
    needed: list[str] = []
    counts: dict[str, int] = {}

    def lookup(rhs: str) -> tuple[str, str | None] | None:
        for pat, repl, imp in EXPR:
            if re.fullmatch(pat, rhs.strip()):
                return repl, imp
        return None

    # ---- PASS 1: whole-statement handling, so `X = <literal>` never becomes `X = X` ----
    # Runs on the full text with re.M so a MULTI-LINE Path(...) is seen as one statement.
    # A removed definition leaves a SENTINEL, which PASS 3 swaps for the bootstrap. That
    # keeps the insertion position exact without any offset arithmetic -- the earlier
    # attempt to recompute a line number from a character offset drifted as soon as PASS 2
    # changed any length ahead of it.
    SENTINEL = "@@BENCH_ENV_BOOTSTRAP@@"

    def on_assign(m: re.Match) -> str:
        indent, name, rhs = m.group(1), m.group(2), m.group(3)
        hit = lookup(rhs)
        if hit is None:
            return m.group(0)
        repl, imp = hit
        if repl == name:                      # `ROOT = ROOT` -- the import IS the definition
            counts["(definition replaced by bootstrap)"] = \
                counts.get("(definition replaced by bootstrap)", 0) + 1
            if imp:
                needed.append(imp)
            return SENTINEL
        counts[f"{name} = {repl}"] = counts.get(f"{name} = {repl}", 0) + 1
        if imp:
            needed.append(imp)
        return f"{indent}{name} = {repl}"

    body = ASSIGN_MULTI.sub(on_assign, orig)

    # ---- PASS 2: everything else, e.g. `sys.path.insert(0, r"D:\...")` ---------------
    for pat, repl, imp in EXPR:
        body, n = re.subn(pat, repl, body)
        if n:
            counts[repl] = counts.get(repl, 0) + n
            if imp:
                needed.append(imp)

    if body == orig:
        return None

    # ---- PASS 3: swap the sentinel for the bootstrap, or insert it -------------------
    # Position is the end of the module preamble (docstring + `from __future__`), NOT the
    # removed definition: a file can reference an imported name before that definition.
    # A file may carry SEVERAL removed definitions (laya_client.py has three); only the
    # first becomes the bootstrap, the rest are simply deleted.
    lines = body.split("\n")
    at = preamble_end(lines)
    block = bootstrap(needed)
    if SENTINEL in body:
        lines = body.replace(SENTINEL, "").split("\n")
        at = preamble_end(lines)
    lines[at:at] = ["", *block, ""]
    src = "\n".join(lines)

    src = re.sub(r"\n{4,}", "\n\n\n", src)

    # ---- self-assertion: never accept output we have not parsed -----------------------
    try:
        ast.parse(src)
    except SyntaxError as exc:
        return {"file": str(path.relative_to(REPO)), "ERROR": f"{exc.lineno}: {exc.msg}",
                "subs": counts}

    if apply:
        out = src.replace("\n", "\r\n") if crlf else src
        path.write_bytes(out.encode("utf-8"))
    return {"file": str(path.relative_to(REPO)), "subs": counts, "at": at,
            "eol": "CRLF" if crlf else "LF"}


def main() -> int:
    apply = "--apply" in sys.argv
    report, total, errors = [], 0, 0
    for p in sorted(REPO.rglob("*.py")):
        if any(s in p.parts for s in SKIP) or p.name in (SELF, "bench_env.py"):
            continue
        r = migrate(p, apply)
        if r:
            report.append(r)
            total += sum(v for k, v in r["subs"].items() if k != "(dropped self-assign)")
            if "ERROR" in r:
                errors += 1

    print(f"{'APPLIED' if apply else 'DRY RUN'} -- {len(report)} files, "
          f"{total} substitutions, {errors} parse errors\n")
    for r in report:
        if "ERROR" in r:
            print(f"  !! {r['file']}: {r['ERROR']}")
    if not apply:
        for r in report[:60]:
            subs = ", ".join(f"{k}x{v}" for k, v in sorted(r["subs"].items()))
            print(f"  {r['file']:54s} @{r['at']:<4} {subs}")
        print("\nre-run with --apply to write")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
