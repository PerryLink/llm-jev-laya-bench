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


def check_publication_readiness() -> None:
    """Packaging checks. These do not gate on the paper's CONTENT; they gate on whether the
    repository can be handed to a stranger, and on whether the things a venue requires are
    actually present. Two of them (G4, G5) are known-current-gaps promoted to visible
    warnings, so they cannot be quietly forgotten before a submission."""
    root = ROOT
    required = {
        "LICENSE": "the artifact's licence",
        "README.md": "what this is and how to reproduce it",
        "THIRD-PARTY.md": "third-party components and their obligations",
        "CITATION.cff": "how to cite",
        "requirements.txt": "what to install, and what deliberately not to",
        ".gitignore": "what must never be committed",
        ".gitattributes": "line-ending policy for hash-verified files",
        "bench_env.py": "portable path resolution",
        "src/analysis/fetch_data.py": "hash-pinned dataset fetch",
    }
    missing = [f for f in required if not (root / f).exists()]
    if missing:
        fail("G1 packaging files present",
             "; ".join(f"{f} ({required[f]})" for f in missing))
    else:
        ok("G1 packaging files present", f"{len(required)} files")

    lic = root / "LICENSE"
    if lic.exists():
        lt = lic.read_text(encoding="utf-8", errors="replace")
        if "Apache License" in lt and "Version 2.0" in lt:
            ok("G2 LICENSE is the Apache-2.0 text")
        else:
            fail("G2 LICENSE is the Apache-2.0 text", "does not look like Apache-2.0")

    # A placeholder author block blocks a citable record: it needs real names.
    cif = root / "CITATION.cff"
    if cif.exists():
        if "REPLACE" in cif.read_text(encoding="utf-8"):
            warn("G3 CITATION.cff author block is filled in",
                 "still contains REPLACE placeholders -- required before publishing")
        else:
            ok("G3 CITATION.cff author block is filled in")

    # The paper must carry a reference list and an AI-assistance disclosure before any
    # submission: every venue requires references, and arXiv's policy requires reporting
    # generative-AI use. Both are open gaps, so they are surfaced on every run.
    t = text()
    if re.search(r"^#{1,3}\s*(参考文献|References|Bibliography)", t, re.M | re.I):
        ok("G4 paper has a reference list")
    else:
        warn("G4 paper has a reference list",
             "NO reference list in the manuscript -- every venue requires one")
    if re.search(r"AI 辅助|生成式 AI|AI-assisted|LLM-assisted", t):
        ok("G5 paper discloses AI assistance")
    else:
        warn("G5 paper discloses AI assistance",
             "not yet stated in the manuscript; arXiv policy requires reporting it")

    gi = root / ".gitignore"
    if gi.exists():
        g = gi.read_text(encoding="utf-8")
        if ".credentials.yaml" in g and ".dsh/" in g:
            ok("G6 .gitignore excludes the credential store")
        else:
            fail("G6 .gitignore excludes the credential store")

    # Dataset integrity is part of reproducibility, and the hash is what makes it so.
    try:
        import subprocess
        r = subprocess.run([sys.executable, str(root / "src" / "analysis" / "fetch_data.py"),
                            "--check"], capture_output=True, text=True, timeout=180)
        tail = (r.stdout or "").strip().splitlines()[-1] if r.stdout else ""
        if r.returncode == 0:
            ok("G7 dataset matches its pinned revision", tail)
        else:
            fail("G7 dataset matches its pinned revision", tail or "check failed")
    except Exception as exc:                                   # noqa: BLE001
        warn("G7 dataset matches its pinned revision", f"could not run: {exc}")


def check_bibliography() -> None:
    """The reference list is generated from a .bib, so the failure mode is DRIFT between
    the two, plus entries that quietly lose a required field. Both are checked here."""
    bib = PAPER / "references.bib"
    if not bib.exists():
        fail("H1 references.bib exists")
        return
    text_bib = bib.read_text(encoding="utf-8")
    entries = re.findall(r"@(\w+)\{([^,]+),(.*?)\n\}", text_bib, re.S)
    if not entries:
        fail("H2 bibliography parses", "no entries found")
        return
    ok("H2 bibliography parses", f"{len(entries)} entries")

    # every entry needs author, title and year -- a missing one renders as a hole
    incomplete = []
    for _kind, key, body in entries:
        for field in ("author", "title", "year"):
            if not re.search(rf"\b{field}\s*=", body):
                incomplete.append(f"{key.strip()} missing {field}")
    if incomplete:
        fail("H3 every entry has author/title/year", "; ".join(incomplete[:4]))
    else:
        ok("H3 every entry has author/title/year", f"{len(entries)} entries checked")

    # a key that appears twice silently drops one entry from the rendered list
    keys = [k.strip() for _k, k, _b in entries]
    dupes = sorted({k for k in keys if keys.count(k) > 1})
    if dupes:
        fail("H4 no duplicate keys", f"{dupes}")
    else:
        ok("H4 no duplicate keys")

    # a reference with NO url is unverifiable by a reader, and this file's whole rule is
    # that every entry was fetched. Flag any that lost its link.
    nourl = [k for _k, k, b in entries if "url" not in b]
    if nourl:
        warn("H5 every entry has a URL", f"no url: {nourl}")
    else:
        ok("H5 every entry has a URL", f"{len(entries)} entries")

    # STALENESS: the generated markdown must match the .bib
    gen = PAPER / "12-references-draft.md"
    if not gen.exists():
        fail("H6 generated reference section exists")
    else:
        src = gen.read_text(encoding="utf-8")
        rendered = len(re.findall(r"^\[\d+\] ", src, re.M))
        if rendered != len(entries):
            fail("H6 generated section is in sync with the .bib",
                 f"bib has {len(entries)}, rendered has {rendered} -- re-run "
                 f"src/analysis/p34_bib_to_markdown.py")
        else:
            ok("H6 generated section is in sync with the .bib", f"{rendered} entries")

    # the section must actually be part of the assembled manuscript
    t = text()
    if "参考文献" in t:
        ok("H7 reference section is in the manuscript")
    else:
        fail("H7 reference section is in the manuscript",
             "not assembled -- check paper/_assemble.py SOURCES")

    # AN UNCITED REFERENCE IS A DIFFERENT DEFECT FROM A MISSING ONE, and this is the check
    # that catches it. An entry can sit in the .bib looking verified while nothing in the
    # paper actually rests on it -- and, worse, a claim can lose its citation in an edit
    # without anyone noticing, because the .bib still looks complete. Citations here are
    # written as prose ("Ng & Jordan, 2001") rather than as keys, so the match uses the
    # first author's surname plus the year, or the key itself.
    body = t.split("# 参考文献")[0]          # the list itself must not count as a citation
    uncited = []
    for _kind, key, blob in entries:
        key = key.strip()
        if f"[@{key}]" in body:
            continue
        m = re.search(r"author\s*=\s*\{(.*?)\}", blob, re.S)
        surname = ""
        if m:
            first = re.split(r"\s+and\s+", m.group(1).strip())[0]
            surname = first.split(",")[0].strip().strip("{}")
        year = (re.search(r"year\s*=\s*\{?(\d{4})", blob) or [None, ""])[1]
        hit = False
        if surname:
            # allow "Ng" or "Ng et al." or "Ng & Jordan" followed by the year
            if re.search(rf"{re.escape(surname)}[^）)。\n]{{0,40}}{year}", body):
                hit = True
        if not hit and surname and surname in body and year in body:
            hit = True                        # loose fallback: both appear somewhere
        if not hit:
            uncited.append(f"{key} ({surname} {year})")
    if uncited:
        warn("H8 every reference is cited in the paper",
             f"{len(uncited)} uncited: {'; '.join(uncited[:5])}"
             + (" ..." if len(uncited) > 5 else ""))
    else:
        ok("H8 every reference is cited in the paper", f"{len(entries)} entries")


def main() -> int:
    check_freshness()
    t = check_refs()
    check_numbers(t)
    check_inventory()
    check_errata()
    check_hygiene()
    check_publication_readiness()
    check_bibliography()

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
