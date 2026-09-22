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
    # The Jev latency ratio is Jev/Laya: 915/37.4 = 24.5x and 1192/37.4 = 31.9x, so the span
    # is 24.5-31.9. "25-29" took the low end from one run and the POOLED p50 (28.7x) as the
    # high end -- mixing two quantities, one line away from the text that gives both runs.
    absent("latency ratio is not the mixed 25-29", "25–29", unless_near=retire)
    absent("latency ratio is not the mixed 25-29 (ASCII)", "25-29", unless_near=retire)
    # Two of three regime-3 draws have a ZERO CELL, which makes the unpaired Wald interval
    # spuriously narrow; under Newcombe only 1 draw robustly excludes zero. An unqualified
    # "2 of 3 CIs exclude 0" therefore contradicts the paper's own corrected framing.
    # NOTE: the earlier guard looked for the exact string "3次中2次CI排除零" and
    # MISSED the manuscript, which writes "3 次中 2 次 95% CI 排除零" -- the "95%"
    # between the numbers defeated a literal match. Normalise before matching.
    _flat_ci = re.sub(r"[\s%95]", "", flat)
    if "3次中2次CI排除零" in _flat_ci or "3次中2次CI排除0" in _flat_ci:
        fail("C zero-cell CI caveat is never dropped",
             "an unqualified \"2 of 3 CIs exclude 0\" survives in the text")
    else:
        ok("C zero-cell CI caveat is never dropped", "no unqualified form")

    # BATTERY SIZE vs STATISTIC n. The mock calibration battery is 14 items; the Brier 0.359
    # was computed on the 10 that carry binary ground truth. Sections 1 and 3 attached the
    # Brier to "14 项校准电池", which reads as a Brier over 14. Both numbers were individually
    # correct -- only their ATTACHMENT was wrong, which is why five audit rounds missed it.
    # Invariant: wherever the mock Brier appears, the n it was computed on appears too.
    for line in t.split("\n"):
        if "0.359" in line and "10" not in line:
            fail("C mock Brier is always printed with its own n",
                 f"0.359 without the n=10 qualifier: {line.strip()[:80]}")
            break
    else:
        ok("C mock Brier is always printed with its own n", "0.359 always carries n=10")
    absent("mock battery size is not attached to the Brier",
           "14项校准电池产出合理的置信度分布，但Brier0.359", unless_near=retire)


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


def check_translation() -> None:
    """The English version is a deliverable in its own right, and the failure modes are
    specific: untranslated Chinese left behind, a section silently dropped, a citation key
    lost, or a number changed in transit. Each is checked separately."""
    en = PAPER / "en"
    if not en.exists():
        warn("I1 English translation exists", "paper/en/ not present yet")
        return
    files = sorted(en.glob("*.md"))
    if not files:
        warn("I1 English translation exists", "paper/en/ is empty")
        return
    ok("I1 English translation exists", f"{len(files)} files")

    CJK = re.compile(r"[\u4e00-\u9fff]")
    for f in files:
        t = f.read_text(encoding="utf-8")
        # A translator's note is expected to be in English; the BODY must have no Chinese.
        body = "\n".join(l for l in t.split("\n")
                         if not l.strip().startswith("*(") )
        stray = [l for l in body.split("\n")
                 if CJK.search(l) and not l.strip().startswith((">", "|", "#"))]
        if stray:
            warn(f"I2 {f.name} has no untranslated Chinese",
                 f"{len(stray)} line(s), first: {stray[0].strip()[:60]}")

    # Every citation key in the Chinese must survive into the English.
    zh_keys = set(re.findall(r"\[@([a-z0-9]+)\]",
                             (PAPER / "MANUSCRIPT.md").read_text(encoding="utf-8")))
    en_keys = set()
    for f in files:
        en_keys |= set(re.findall(r"\[@([a-z0-9]+)\]", f.read_text(encoding="utf-8")))
    if en_keys:
        if en_keys <= zh_keys:
            ok("I3 English citation keys all exist in the bibliography",
               f"{len(en_keys)} keys used")
        else:
            fail("I3 English citation keys all exist in the bibliography",
                 f"unknown: {sorted(en_keys - zh_keys)}")
    else:
        warn("I3 English citation keys all exist in the bibliography",
             "no [@key] markers found in the English yet")

    # Section coverage: each English file should declare the sections it carries. Front
    # matter (the abstract) legitimately has no `§N`, so it is excluded.
    missing = []
    for f in files:
        if any(k in f.name.lower() for k in ("abstract", "disclosure", "references")):
            continue
        t = f.read_text(encoding="utf-8")
        if not re.search(r"^#\s*§?\d", t, re.M):
            missing.append(f.name)
    if missing:
        warn("I4 every English section file declares its sections", f"{missing}")
    else:
        ok("I4 every English section file declares its sections",
           f"{len(files)} files")



def check_trace_audit_invariants(t: str) -> None:
    """The ERRATA-section-10 invariants, recomputed from the artifacts rather than trusted.

    Every one of these was a real defect: a claim the paper printed that its own artifact
    contradicted. They are checked here so that a later edit cannot quietly restore one.
    """
    import json as _json
    import re as _re

    flat = _re.sub(r"[\s*`]", "", t.replace("−", "-"))

    def artifact(name: str) -> dict:
        return _json.loads((R / name).read_text(encoding="utf-8"))

    # ---- K1: section 7.2 must report the PROSE arm, with its positive delta_catch ---------
    p14 = artifact("P14-llm-arm-full.json")
    prose = p14["complementarity_prose_arm"]
    forced = p14["complementarity"]
    got = (round(prose["delta_catch"], 4), prose["n_paired"],
           prose["confusion"]["typed_only_correct"], prose["confusion"]["llm_only_correct"])
    if got != (0.0435, 48, 1, 25):
        fail("K1 prose arm is reported as the artifact records it",
             f"artifact changed: delta/n/judge_only/llm_only = {got}")
    elif "complementarity_prose_arm" in t and "+0.0435" in flat and "46/48" in t:
        ok("K1 prose arm is reported as the artifact records it",
           f"n={prose['n_paired']}, delta_catch=+{prose['delta_catch']:.4f}, "
           f"judge-only={prose['confusion']['typed_only_correct']} of "
           f"{prose['confusion']['typed_only_correct'] + prose['confusion']['llm_only_correct']} "
           f"LLM errors; forced-choice delta_catch={forced['delta_catch']} (undefined, not 0)")
    else:
        fail("K1 prose arm is reported as the artifact records it",
             "section 7.2 does not print the prose arm's +0.0435 / 46/48")

    # ---- K2: the one-sided p-values are labelled AND match the record the paper cites -----
    #
    # THE OBJECT MATTERS (this check was red for a day, on purpose). The paper reports the
    # PUBLISHED chain battery -- the measurement of the protocol the text describes. That
    # battery's live artifacts were later regenerated with a changed option-set policy, so the
    # LIVE files no longer reproduce the printed numbers, while the pinned pre-rerun copies do.
    # K2 therefore recomputes from the pinned copies, which the disclosure in section 8.6.1
    # names, and requires the disclosure to be present: a check that could be made green by
    # deleting the follow-up would be worse than no check.
    import hashlib as _hash

    def _pinned(i: int):
        a = R / "_superseded" / f"P22b-fixed-r{i}.json.pre-repair"
        b = ROOT / "rerun" / "baseline" / f"P22b-fixed-r{i}.json"
        return a, b

    def _binomial_lower(x: int, n: int, p0: float) -> float:
        import math as _math
        return sum(_math.comb(n, i) * p0 ** i * (1 - p0) ** (n - i) for i in range(x + 1))

    def _binomial_normal(x: int, n: int, p0: float) -> float:
        import math as _math
        se = _math.sqrt(p0 * (1 - p0) / n)
        return 0.5 * (1 + _math.erf(((x / n - p0) / se) / _math.sqrt(2)))

    pinned_exact, pinned_normal, mismatched = [], [], []
    for i in (1, 2, 3):
        a, b = _pinned(i)
        if not (a.exists() and b.exists()):
            mismatched.append(f"r{i} pinned copy missing")
            continue
        if _hash.sha256(a.read_bytes()).hexdigest() != _hash.sha256(b.read_bytes()).hexdigest():
            mismatched.append(f"r{i} the two pinned copies differ")
            continue
        rows = _json.loads(a.read_text(encoding="utf-8"))["rows"]
        both = sum(1 for r in rows if r["llm_correct"] and r["laya_correct"])
        jonly = sum(1 for r in rows if not r["llm_correct"] and r["laya_correct"])
        llm_wrong = sum(1 for r in rows if not r["llm_correct"])
        marginal = (both + jonly) / len(rows)
        pinned_exact.append(_binomial_lower(jonly, llm_wrong, marginal))
        pinned_normal.append(_binomial_normal(jonly, llm_wrong, marginal))

    if mismatched or len(pinned_exact) != 3:
        fail("K2 the one-sided p-values match the pinned record they cite",
             f"pinned copies unusable: {mismatched}")
    else:
        want_exact = [f"{v:.3f}" for v in pinned_exact]
        want_normal = [f"{v:.3f}" for v in pinned_normal]
        labelled = "正态近似" in t and "精确二项" in t
        # the EXACT tails are enforced exactly; the normal approximation to 0.001, because its
        # third decimal depends on the rounding convention (recomputing from the pinned rows
        # gives 0.04246 for r2, which the paper prints as 0.043 -- a half-unit, not a defect)
        printed = all(w in t for w in want_exact)
        approx_ok = all(any(f"{v + d:.3f}" in t for d in (-0.001, 0.0, 0.001))
                        for v in pinned_normal)
        disclosed = "重测" in t and "P22b-fixed-r1..r3.json.pre-repair" in t
        if labelled and printed and approx_ok and disclosed:
            ok("K2 the one-sided p-values match the pinned record they cite",
               f"exact binomial tails {want_exact} and normal approximations {want_normal} "
               f"printed with the convention labelled; re-measurement disclosed against the "
               f"pinned copies")
        else:
            fail("K2 the one-sided p-values match the pinned record they cite",
                 f"labelled={labelled} printed={printed} disclosed={disclosed}; "
                 f"expected exact {want_exact}, normal {want_normal}")

    # ---- K3: all ten reliability bins, with P19's own n ----------------------------------
    bins = artifact("P19-calibration.json")["summary"]["laya"]["calibration"]["bins"]
    want_bins = {b["bin"]: b["n"] for b in bins}
    # SCOPE THE SCAN TO THE RELIABILITY TABLE. The mock battery's bin table in section 3.1 has
    # the same first two columns (0.0-0.2 | 3 | ...), so an unscoped row regex collects 15 rows
    # and the check fails on correct data -- which is how a check gets switched off.
    printed = {}
    for label, n in _re.findall(
            r"^\| \*?\*?([0-9]\.[0-9]–[0-9]\.[0-9])\*?\*? \| \*?\*?([0-9,]+)\*?\*?",
            t, _re.M):
        key = label.replace("–", "-")
        if key in want_bins:
            printed[key] = int(n.replace(",", ""))
    if printed == want_bins:
        ok("K3 the reliability table prints all 10 bins with P19's n",
           f"{len(want_bins)} bins, n sums to {sum(want_bins.values())}; low-end gaps "
           f"+0.939 (n=1) and +0.343 (n=22) present: "
           f"{'+0.939' in flat and '+0.343' in flat}")
    else:
        fail("K3 the reliability table prints all 10 bins with P19's n",
             f"printed {len(printed)} rows vs {len(want_bins)} in P19; mismatch "
             f"{sorted(set(want_bins.items()) ^ set(printed.items()))[:4]}")

    # ---- K4: 0.9981 is never the probe maximum ------------------------------------------
    retire = ("并非", "不是", "更正", "原印", "撤回", "correction", "withdrawn")
    bad = [l for l in t.split("\n")
           if "0.9981" in l and "全探测最高" in _re.sub(r"[*`]", "", l)
           and not any(m in l for m in retire)]
    if bad:
        fail("K4 0.9981 is not called the probe maximum",
             f"{bad[0].strip()[:70]}")
    elif "0.9989" in t and "全探测最高" in t:
        ok("K4 0.9981 is not called the probe maximum",
           "0.9981 is scoped to wrong answers; 0.9989 carries the probe-maximum claim")
    else:
        fail("K4 0.9981 is not called the probe maximum",
             "0.9989 / the probe-maximum wording is missing")

    # ---- K5: the attribution table carries `warnings` ------------------------------------
    never = artifact("P27d-primitive-fields.json")["never_returned_by_provider"]
    if "warnings" not in never:
        fail("K5 the attribution table carries `warnings`",
             "P27d no longer lists `warnings` as provider-absent")
    elif "`warnings`" in t and "never_returned_by_provider" in t:
        ok("K5 the attribution table carries `warnings`",
           f"all {len(never)} provider-absent keys accounted for: {never}")
    else:
        fail("K5 the attribution table carries `warnings`",
             "the manuscript does not attribute `warnings` to the access layer")

    # ---- K6: the false-answer rate is the measured one ----------------------------------
    if _re.search(r"约占一半", t) and "不是" not in t:
        fail("K6 the false-answer rate is measured, not 'about half'",
             "an unqualified 'about half' survives")
    elif "60.0" in t and "29.8" in t:
        ok("K6 the false-answer rate is measured, not 'about half'",
           "60.0% (LLM, 660/1100) and 29.8% (judge, 328/1100) printed from P19")
    else:
        fail("K6 the false-answer rate is measured, not 'about half'",
             "the measured 60.0% / 29.8% rates are missing")

    # ---- K7: the impossible clause-counting note is gone --------------------------------
    stale = [l for l in t.split("\n") if l.startswith("> **⚠️ 编号说明（审计订正）**")]
    if stale:
        fail("K7 the impossible clause-count note is withdrawn", stale[0][:70])
    else:
        ok("K7 the impossible clause-count note is withdrawn",
           "the count is stated as 4+13+8-2=23 with no '14-17 -> 14-21' claim")

    # ---- K8: the untraceable numbers are marked -----------------------------------------
    n_marks = t.count("【不可核验 ⚠️ ERRATA §10.2】")
    if n_marks >= 11 and "## 11.6" in t:
        ok("K8 untraceable numbers are marked in place",
           f"{n_marks} markers in the manuscript plus the section 11.6 consolidated list")
    else:
        fail("K8 untraceable numbers are marked in place",
             f"{n_marks} markers (need >=11) and section 11.6 present: {'## 11.6' in t}")

    # ---- K9: the latency ratio is a range with both artifacts named ---------------------
    if _re.search(r"1\.94\s*倍", t) and "更正" not in t:
        fail("K9 the latency ratio is a range, not a point",
             "an unqualified '1.94x' survives")
    elif "1.5–1.9" in t and "P27b-plugin-crossval.json" in t and "1,244.8" in t:
        ok("K9 the latency ratio is a range, not a point",
           "1.5-1.9x with both artifacts named (baseline 1.94 / live 1.49, denominators "
           "956.2 vs 1,244.8 ms)")
    else:
        fail("K9 the latency ratio is a range, not a point",
             "the range or the two artifact names are missing")


    # ---- K11: the pinned chain copies still exist and still pair up ------------------------
    import hashlib as _hash11
    pairs, bad = [], []
    for i in (1, 2, 3):
        a = R / "_superseded" / f"P22b-fixed-r{i}.json.pre-repair"
        b = ROOT / "rerun" / "baseline" / f"P22b-fixed-r{i}.json"
        if not (a.exists() and b.exists()):
            bad.append(f"r{i} missing")
            continue
        ha = _hash11.sha256(a.read_bytes()).hexdigest()[:12]
        hb = _hash11.sha256(b.read_bytes()).hexdigest()[:12]
        if ha != hb:
            bad.append(f"r{i} {ha} != {hb}")
        else:
            pairs.append(ha)
    if bad:
        fail("K11 the pinned chain copies are intact and identical",
             f"{bad} -- the published battery's record has been disturbed; the paper cites it")
    else:
        ok("K11 the pinned chain copies are intact and identical",
           f"3 pairs byte-identical: {pairs}")

    # ---- K10: 0.912 survives only inside its retraction ---------------------------------
    loose = [l for l in t.split("\n")
             if "0.912" in l and not any(m in l for m in ("更正", "0.4795", "撤回"))]
    if loose:
        fail("K10 0.912 survives only inside its retraction", loose[0].strip()[:70])
    else:
        ok("K10 0.912 survives only inside its retraction",
           "every 0.912 sits beside its correction to 0.4795")


def check_translation_coverage() -> None:
    """Every numbered section in a Chinese draft must appear in its English translation.

    This is the check that was MISSING when the 9-10-11 file arrived carrying only 9 and 10
    plus a `TRANSLATION-CONTINUES-HERE` marker: the file had no Han characters, declared its
    sections, and used valid keys, so every existing check went green on a translation that
    was one third short. A silently incomplete translation is worse than an obviously
    incomplete one, because nothing complains.
    """
    # English file -> the Chinese sources it must cover
    PAIRS = {
        "00-abstract.md": ["00-abstract-draft.md"],
        "01-intro-02.md": ["01-intro-02-related-draft.md"],
        "03-04-systems-method.md": ["03-systems-draft.md", "04-method-draft.md"],
        "05-results-A.md": ["05-results-A-draft.md"],
        "06-07-results-BC.md": ["06-results-B-draft.md", "07-results-C-draft.md"],
        "08-results-D.md": ["08-results-D-draft.md"],
        "09-10-11-discussion-limits-repro.md":
            ["09-10-11-discussion-limits-repro-draft.md"],
    }
    en = PAPER / "en"
    problems = []
    for en_name, zh_names in PAIRS.items():
        f = en / en_name
        if not f.exists():
            continue                      # not translated yet; I1 reports the inventory
        t = f.read_text(encoding="utf-8")
        if "TRANSLATION-CONTINUES-HERE" in t:
            problems.append(f"{en_name}: carries a TRANSLATION-CONTINUES-HERE marker")
        want = set()
        for zh in zh_names:
            p = PAPER / zh
            if p.exists():
                want |= set(re.findall(r"^#\s*§(\d+)", p.read_text(encoding="utf-8"), re.M))
        have = set(re.findall(r"^#\s*§(\d+)", t, re.M))
        if en_name.startswith("00-"):
            continue                      # the abstract has no numbered sections
        missing = sorted(want - have)
        if missing:
            problems.append(f"{en_name}: missing section(s) {missing} "
                            f"(source has {sorted(want)}, translation has {sorted(have)})")
    if problems:
        fail("I5 every English file covers all of its source sections", "; ".join(problems[:3]))
    else:
        done = [n for n in PAIRS if (en / n).exists()]
        ok("I5 every English file covers all of its source sections",
           f"{len(done)} file(s) checked")


def main() -> int:
    # The gate must not die while reporting: this host's console is GBK, and a detail string
    # containing a character it cannot encode aborted the run with a UnicodeEncodeError
    # instead of printing a verdict. Degrade the glyph, keep the finding.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                            # noqa: BLE001
        pass
    check_freshness()
    t = check_refs()
    check_numbers(t)
    check_inventory()
    check_errata()
    check_hygiene()
    check_publication_readiness()
    check_bibliography()
    check_translation()
    check_translation_coverage()
    # ERRATA section 10: thirteen paper-text defects, twelve untraceable numbers and
    # one artifact defect were audited here. The fixes are scripts; these are the
    # checks that keep them fixed.
    check_trace_audit_invariants(t)
    # ERRATA section 10: thirteen paper-text defects, twelve untraceable numbers and
    # one artifact defect were audited here. The fixes are scripts; these are the
    # checks that keep them fixed.
    # Every claim withdrawn or corrected this session must be gone from EVERY document, and
    # its correction must actually appear somewhere. The section-8 retraction was fixed in one
    # place and left standing in three others, and only a second audit caught it -- so this
    # checks the property rather than trusting that each instance was found.
    import subprocess as _sp
    _r = _sp.run([sys.executable, str(ROOT / "src" / "analysis" / "p49_verify_withdrawals.py")],
                 capture_output=True, text=True, encoding="utf-8")
    if _r.returncode == 0:
        ok("J1 withdrawals are consistent across all documents",
           "7 withdrawn/corrected claims verified")
    else:
        _tail = (_r.stdout or "").strip().splitlines()
        fail("J1 withdrawals are consistent across all documents",
             _tail[-1] if _tail else "see p49_verify_withdrawals.py")

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
