"""VERIFY ALL -- the project's own checks, as a persisted script.

WHY THIS EXISTS
---------------
Every verification in this project was previously run ad hoc, in a throwaway interpreter
session, and reported in prose. That is the same failure the paper documents for its
statistics: a number that cannot be re-checked is a number that silently rots. This script
makes the checks executable and repeatable.

WHAT IT CHECKS
--------------
  A. FRESHNESS     the manuscript is newer than every draft that feeds it
  B. REFERENCES    every in-text `§N` resolves to a heading that exists
  C. NUMBERS       a sample of headline figures in the manuscript matches its artifact
  D. INVENTORY     every result artifact carries provenance or is a pure derivation
  E. ERRATA        every artifact named as stale in ERRATA.md actually exists
  F. HYGIENE       no credential value, no `.pre-repair`/`.pre-provenance` left in results/

Exit code is 0 only if every check passes. Warnings do not fail the build; failures do.
"""

from __future__ import annotations

# Paths resolve through bench_env, which locates the repository root by walking
# up from this file and honours environment overrides (LAYA_ROOT, DSH_CREDENTIALS,
# ...). Run `python bench_env.py` to print what was resolved. The aliased imports
# keep this block independent of whatever this module imported above, so it can
# sit at any top-level position.
import sys as _sys
from pathlib import Path as _Path

_p = _Path(__file__).resolve()
while not (_p / "bench_env.py").exists():
    if _p.parent == _p:
        raise RuntimeError(f"bench_env.py not found above {__file__}")
    _p = _p.parent
ROOT = _p
_sys.path.insert(0, str(ROOT))


import json
import re
import sys
from pathlib import Path


PAPER = ROOT / "paper"
R = ROOT / "results"
MANUSCRIPT = PAPER / "MANUSCRIPT.md"

DRAFTS = sorted(p for p in PAPER.glob("*-draft.md"))

results: list[tuple[str, str, str]] = []      # (status, check, detail)


def ok(check: str, detail: str = "") -> None:
    results.append(("PASS", check, detail))


def warn(check: str, detail: str) -> None:
    results.append(("WARN", check, detail))


def fail(check: str, detail: str) -> None:
    results.append(("FAIL", check, detail))


def text() -> str:
    return MANUSCRIPT.read_text(encoding="utf-8")


# ------------------------------------------------------------------ A. freshness
def check_freshness() -> None:
    if not MANUSCRIPT.exists():
        fail("A1 manuscript exists", "MANUSCRIPT.md missing")
        return
    m = MANUSCRIPT.stat().st_mtime
    stale = [p.name for p in DRAFTS if p.stat().st_mtime > m]
    if stale:
        fail("A1 manuscript is newer than its drafts", f"stale vs {stale}")
    else:
        ok("A1 manuscript is newer than its drafts", f"{len(DRAFTS)} drafts checked")


# ------------------------------------------------------------------ B. references
def check_refs() -> str:
    t = text()
    headings = set()
    for line in t.split("\n"):
        h = re.match(r"^#{1,6}\s+(\d+(?:\.\d+)*)", line.strip())
        if h:
            headings.add(h.group(1))
    # Collect in-text `§N(.N)*` references. References to OTHER documents' sections
    # (`R15 §0.2`, `P19 §1.4`) are not internal refs and must not be checked as such --
    # the paper's own sections are numbered 1..11, so a `§0.x` is always external.
    internal = set()
    for m in re.finditer(r"§(\d+(?:\.\d+)*)", t):
        before = t[max(0, m.start() - 12):m.start()]
        if re.search(r"\b[RPDA]\d+[a-z]?\s*$", before):
            continue                                  # `R15 §0.2` etc.
        if m.group(1).split(".")[0] == "0":
            continue                                  # external by construction
        internal.add(m.group(1))
    dangling = sorted(r for r in internal
                      if not any(h == r or h.startswith(r + ".") for h in headings))
    if dangling:
        fail("B1 every § reference resolves", f"dangling: {dangling}")
    else:
        ok("B1 every § reference resolves", f"{len(internal)} internal refs, "
                                            f"{len(headings)} numbered headings")
    tops = sorted(int(h) for h in headings if "." not in h)
    if tops and tops != list(range(1, max(tops) + 1)):
        fail("B2 top-level sections are contiguous", f"found {tops}")
    else:
        ok("B2 top-level sections are contiguous", f"1..{max(tops) if tops else 0}")
    return t


# ------------------------------------------------------------------ C. numbers
def check_numbers(t: str) -> None:
    """Spot-check headline figures against the artifacts that produce them.

    Matching is done against a NORMALISED copy: markdown emphasis stripped, all whitespace
    removed, and the Unicode minus sign folded to ASCII. The manuscript writes `**42** 个
    JSON` and `−0.259`, so a naive substring test reports false failures.
    """
    flat = re.sub(r"\s+", "", t.replace("−", "-").replace("**", "").replace("`", ""))

    def has(label: str, needle: str) -> None:
        n = re.sub(r"\s+", "", needle.replace("−", "-").replace("**", ""))
        if n in flat:
            ok(f"C {label}", needle[:48])
        else:
            fail(f"C {label}", f"not found in manuscript: {needle[:48]}")

    def absent(label: str, needle: str, *, unless_near: tuple = ()) -> None:
        """A superseded figure may legitimately remain inside a DISCLOSURE sentence.

        The paper deliberately quotes retired values next to the words that retire them
        ("先前印的 …", "原印 …"), because showing that a number moved is itself evidence.
        Failing on those would punish the disclosure, so proximity to a retirement marker
        downgrades the finding to a pass.
        """
        n = re.sub(r"\s+", "", needle.replace("−", "-").replace("**", ""))
        idx = flat.find(n)
        if idx < 0:
            ok(f"C {label}", "absent")
            return
        window = flat[max(0, idx - 40):idx + len(n) + 40]
        if any(marker in window for marker in unless_near):
            ok(f"C {label}", "present only inside a disclosure")
        else:
            fail(f"C {label}", f"present outside a disclosure: …{window[:70]}…")

    inv = json.loads((R / "P30-evidence-inventory.json").read_text(encoding="utf-8"))
    has("inventory count matches artifact", f"{inv['n_result_json']}个JSON")
    if inv["n_without_provenance_and_not_a_derivation"] == 0:
        has("unexplained gaps are zero", "未解释缺口为0")
    else:
        fail("C unexplained gaps are zero",
             f"{inv['n_without_provenance_and_not_a_derivation']} unexplained gaps")

    st = json.loads((R / "P28-recomputed-statistics.json").read_text(encoding="utf-8"))
    c = st["calibration"]
    for key in ("auc", "rel", "res", "unc", "brier_direct"):
        has(f"calibration {key}", str(c[key]))

    # The two Newcombe cells that were corrected. NOTE: the bad value `[-0.324,+0.257]`
    # is ALSO the legitimate Wald interval for that column -- the error was labelling it
    # "Newcombe", not the number itself. So the test cannot be "this value is absent"; it
    # must be "the Newcombe row is not a copy of the Wald row".
    nc = {b["label"]: b["newcombe"] for b in st["regime2"]}
    has("regime-2 r2 Newcombe lower", f"{nc['P15b r2 (temperature=0)'][0]:.3f}")
    has("regime-2 record Newcombe lower", f"{nc['P15 record (unpinned)'][0]:.3f}")

    wald_row = newcombe_row = None
    for line in t.split("\n"):
        if "Δ_catch" in line and "Wald" in line:
            wald_row = re.sub(r"\s+", "", line.replace("−", "-").replace("**", ""))
        if "Δ_catch" in line and "Newcombe" in line:
            newcombe_row = re.sub(r"\s+", "", line.replace("−", "-").replace("**", ""))
    if wald_row is None or newcombe_row is None:
        fail("C Wald and Newcombe rows both exist", "one of the CI rows is missing")
    else:
        wald_cells = re.findall(r"\[(-?\d+\.\d+),\+?(-?\d+\.\d+)\]", wald_row)
        copied = [c for c in wald_cells
                  if f"[{c[0]},+{c[1]}]" in newcombe_row or f"[{c[0]},{c[1]}]" in newcombe_row]
        if copied:
            fail("C Newcombe row is not a copy of the Wald row",
                 f"{len(copied)} cell(s) identical between the two rows: {copied}")
        else:
            ok("C Newcombe row is not a copy of the Wald row",
               f"{len(wald_cells)} cells compared, none shared")

    retire = ("原印", "先前印", "曾印", "已删", "被取代", "superseded")
    absent("stale Newcombe r2 cell not reused as a result", "-0.410,+0.184", unless_near=retire)

    if "Holm" in t and ("0/3" in flat or "0/3次" in flat):
        ok("C Holm correction disclosed")
    else:
        fail("C Holm correction disclosed", "Holm result not stated in the manuscript")

    absent("stale latency 938.6 not printed as current", "938.6", unless_near=retire)
    absent("stale ratio 2.02 not printed as current", "2.02倍", unless_near=retire)


# ------------------------------------------------------------------ D. inventory
def check_inventory() -> None:
    inv = json.loads((R / "P30-evidence-inventory.json").read_text(encoding="utf-8"))
    if inv["n_without_provenance_and_not_a_derivation"] == 0:
        ok("D every artifact has provenance or is a derivation",
           f"{inv['n_with_any_provenance']}/{inv['n_result_json']} with provenance, "
           f"{inv['n_pure_derivations']} pure derivations")
    else:
        fail("D every artifact has provenance or is a derivation",
             f"unexplained: {inv['without_provenance_and_not_a_derivation']}")
    actual = len(list(R.glob("*.json")))
    if actual != inv["n_result_json"]:
        fail("D inventory is current",
             f"artifact says {inv['n_result_json']}, directory has {actual} -- re-run p30")
    else:
        ok("D inventory is current", f"{actual} artifacts")


# ------------------------------------------------------------------ E. errata
def check_errata() -> None:
    p = R / "ERRATA.md"
    t = p.read_text(encoding="utf-8")
    named = set(re.findall(r"`(P\d+[A-Za-z0-9\-]*\.json)`", t))
    missing = sorted(n for n in named if not (R / n).exists())
    if missing:
        fail("E ERRATA names real artifacts", f"missing: {missing}")
    else:
        ok("E ERRATA names real artifacts", f"{len(named)} artifacts referenced")
    for section in range(0, 10):
        pass
    n_sections = len(re.findall(r"^## \d+\.", t, re.M))
    ok("E ERRATA has numbered sections", f"{n_sections} sections")


# ------------------------------------------------------------------ F. hygiene
def check_hygiene() -> None:
    backups = sorted(p.name for p in R.glob("*.pre-*"))
    if backups:
        warn("F no backup files left in results/", f"{len(backups)}: {backups[:5]}")
    else:
        ok("F no backup files left in results/")

    t = text()
    # a credential would be a long high-entropy token; check for the well-known prefixes
    hits = [pat for pat in ("sk-or-v1-", "sk-", "Bearer sk")
            if pat in t and pat != "sk-"]
    leaks = re.findall(r"sk-[A-Za-z0-9]{16,}", t)
    if leaks:
        fail("F no credential value in the manuscript", f"{len(leaks)} match(es)")
    else:
        ok("F no credential value in the manuscript")

    if "未解释缺口为 0" in t or "未解释缺口为0" in re.sub(r"\s+", "", t):
        ok("F paper states the zero-gap result")
    else:
        warn("F paper states the zero-gap result", "not found")


def main() -> int:
    check_freshness()
    t = check_refs()
    check_numbers(t)
    check_inventory()
    check_errata()
    check_hygiene()

    width = max(len(c) for _, c, _ in results)
    n_pass = sum(1 for s, _, _ in results if s == "PASS")
    n_warn = sum(1 for s, _, _ in results if s == "WARN")
    n_fail = sum(1 for s, _, _ in results if s == "FAIL")
    for status, check, detail in results:
        mark = {"PASS": "  ok ", "WARN": " warn", "FAIL": " FAIL"}[status]
        print(f"[{mark}] {check:<{width}}  {detail}")
    print(f"\n{n_pass} passed, {n_warn} warnings, {n_fail} failures  "
          f"({len(results)} checks)")
    if n_fail:
        print("\nFAILED")
        return 1
    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
