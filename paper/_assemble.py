"""Assemble the manuscript from section drafts.

Written as a script because assembling it by hand produced two real errors:
PowerShell's `Get-Content -Raw` read the UTF-8 drafts as ANSI and garbled every CJK
character, and a sloppy regex renumbering dropped the `## ` prefix and the dot from 26
subheadings (`## 3.0` became `60`). Both are the same failure class this paper documents:
a mechanical step silently corrupting output while still producing a plausible-looking
file. So the assembly is now a checked script rather than a command line.

VERIFICATION BUILT IN:
  * every source file must exist, or the build fails loudly;
  * the output must contain no heading whose text starts with two bare digits (the
    signature of the corrupted renumbering);
  * section and subsection numbering is asserted to run 1..11 with the expected
    subsection prefixes, so a mismatch fails the build instead of shipping;
  * in-text `§N` references are remapped alongside the headings they point at (a third
    instance of the same failure class: the first version renumbered headings only, so
    25 cross-references silently pointed at the wrong sections);
  * every `§` reference must resolve to an existing heading, or the build reports it.
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
from bench_env import PAPER  # noqa: E402


import io
import re
import sys
from pathlib import Path


# In-text cross references. `own` is the section number the draft was AUTHORED under, so
# only references to the draft's own section are rewritten; references to other sections
# (§4.9 from a results draft, say) are left alone.
REF = re.compile(r"§(\d+(?:\.\d+)*)(?:\s*[–-]\s*(\d+(?:\.\d+)*))?")

# (source file, human title). Order IS the manuscript order, and the numbers follow the
# R9 outline: 1 intro, 2 related, 3 systems, 4 method, 5-8 results A-D, 9-11 discussion,
# limitations, reproducibility.
SECTIONS = [
    ("00-abstract-draft.md", "摘要"),
    ("01-intro-02-related-draft.md", "§1 引言 / §2 背景与相关工作"),
    ("03-systems-draft.md", "§3 被测系统与仪器缺陷"),
    ("04-method-draft.md", "§4 方法"),
    ("05-results-A-draft.md", "§5 结果 A"),
    ("06-results-B-draft.md", "§6 结果 B"),
    ("07-results-C-draft.md", "§7 结果 C"),
    ("08-results-D-draft.md", "§8 结果 D"),
    ("09-10-11-discussion-limits-repro-draft.md", "§9-§11 讨论 / 局限 / 可复现性"),
]

# The result drafts were authored against the ORIGINAL outline numbers and are remapped
# here to their manuscript positions. Applied to headings and in-text references.
#
# AUDIT FIX (round 5): `01` and `09-10-11` were MISSING from this map even though they
# cite the old outline throughout (old §3 = results-B, old §6 = results-C, old §7 =
# results-D). Twelve references therefore shipped pointing at the wrong sections, and
# the dangling-reference check could not catch them because §3, §6 and §7 all exist in
# the final manuscript with DIFFERENT meanings. Their own headings are §1/§2 and
# §9/§10/§11, which none of these keys touch, so the mapping is safe for headings.
RENUMBER = {
    "01-intro-02-related-draft.md": {"3": "6", "6": "7", "7": "8"},
    "05-results-A-draft.md": {"5": "5"},   # already correct
    "06-results-B-draft.md": {"3": "6"},   # authored as §3
    "07-results-C-draft.md": {"6": "7"},   # authored as §6
    "08-results-D-draft.md": {"7": "8"},   # authored as §7
    "09-10-11-discussion-limits-repro-draft.md": {"3": "6", "6": "7", "7": "8"},
}

HEAD = (
    "# 当判定层的自报字段说谎\n\n"
    "**三个判定层的接入路径在相同条目上的代价、延迟与失效边界**\n\n"
    "*由分节源文件汇编（`paper/_assemble.py`）· 每个数字标注 n 与出处*\n\n"
    "> **本文的定位是测量与刻画，不是算法论文。**\n"
    "> 四条主张中三条独立成立（成本不是约束；接入层自报字段不可信；能力塌缩），\n"
    "> **第四条——异种判定器提供增量覆盖——在三个任务区制上未获支持**\n"
    "> （前两个区制因 LLM 触顶而不可测，第三个区制效力不足；§8）。\n\n---\n"
)


def remap_headings(text: str, mapping: dict[str, str]) -> str:
    """Rewrite section numbering to the manuscript's positions.

    Two shapes must be handled, and missing the second is what left the H1 labels
    carrying their original numbers (`# §3 结果 B` sitting at position 6):
      * `## N.M title`  -- subsections
      * `# §N title`    -- top-level section headings
    """
    out_lines = []
    for line in text.split("\n"):
        m = re.match(r"^(#{1,3}) (\d+)\.(\d+)(.*)$", line)
        if m and m.group(2) in mapping:
            hashes, _, sub, rest = m.groups()
            line = f"{hashes} {mapping[m.group(2)]}.{sub}{rest}"
        else:
            m2 = re.match(r"^(#{1,3}) §(\d+)(\s.*)$", line)
            if m2 and m2.group(2) in mapping:
                hashes, _, rest = m2.groups()
                line = f"{hashes} §{mapping[m2.group(2)]}{rest}"
        out_lines.append(line)
    return "\n".join(out_lines)


def remap_refs(text: str, own: str | None, new: str | None) -> str:
    """Rewrite in-text `§N` / `§N.M` / `§N.M–N.K` refs to the draft's own section.

    Only the draft's OWN section number is rewritten. A results-B draft authored as §3
    must have its `§3.2` become `§6.2`, but its `§4.9` (pointing at the method section)
    must survive untouched.
    """
    if not own or not new or own == new:
        return text

    def conv(num: str) -> str:
        parts = num.split(".")
        if parts[0] == own:
            parts[0] = new
        return ".".join(parts)

    def sub(m: re.Match) -> str:
        out = "§" + conv(m.group(1))
        if m.group(2):
            out += "–" + conv(m.group(2))
        return out

    return REF.sub(sub, text)


def main() -> int:
    check_only = "--check" in sys.argv
    missing = [fn for fn, _ in SECTIONS if not (PAPER / fn).exists()]
    if missing:
        print("MISSING SOURCE FILES:", missing, file=sys.stderr)
        return 2

    # AUDIT FIX (round 5): a STALENESS guard. A draft was once edited and the manuscript
    # not rebuilt, so the shipped file silently lagged its sources by 26 s and still
    # passed every check. `--check` fails without writing when that has happened.
    out_path = PAPER / "MANUSCRIPT.md"
    if check_only:
        if not out_path.exists():
            print("STALE: MANUSCRIPT.md does not exist")
            return 1
        newest = max((PAPER / fn).stat().st_mtime for fn, _ in SECTIONS)
        if out_path.stat().st_mtime < newest:
            print("STALE: MANUSCRIPT.md is older than at least one source draft -- "
                  "rebuild required")
            return 1
        print("fresh: MANUSCRIPT.md is newer than every source draft")
        return 0

    parts = [HEAD]
    remapped_refs: list[str] = []
    for fn, title in SECTIONS:
        text = io.open(PAPER / fn, encoding="utf-8").read()
        mapping = RENUMBER.get(fn, {})
        text = remap_headings(text, mapping)
        for own, new in mapping.items():
            before = text
            text = remap_refs(text, own, new)
            # ADVISORY: a bare `§N` in a draft whose own old number is N is AMBIGUOUS --
            # it may mean "this section" (remap it) or "the section that is now N"
            # (leave it). This bit us once: a note in the results-C draft referring to
            # results-B was silently rewritten to point at results-C. Every remap is
            # therefore listed so the ambiguity is reviewable rather than invisible.
            if text != before:
                for m in REF.finditer(before):
                    if m.group(1).split(".")[0] == own:
                        remapped_refs.append(f"{fn}: §{m.group(1)} -> "
                                             f"§{remap_refs(m.group(0), own, new)[1:]}")
        parts.append(f"<!-- ===== {title} · 源 {fn} ===== -->\n\n{text.strip()}\n\n---\n")

    doc = "\n".join(parts)

    # ---- verification runs BEFORE the write, so a broken build cannot overwrite the paper
    problems: list[str] = []
    lines = doc.split("\n")
    for line in lines:
        if re.match(r"^\d{2} ", line) or re.match(r"^#+ \d{2} ", line):
            problems.append(f"glued-digit heading: {line[:60]}")
    h2 = [l for l in lines if re.match(r"^## \d+\.\d+", l)]
    secs = sorted({int(re.match(r"^## (\d+)\.", l).group(1)) for l in h2})
    seen: dict[str, int] = {}
    for l in h2:
        num = re.match(r"^## (\d+\.\d+)", l).group(1)
        seen[num] = seen.get(num, 0) + 1
    for num, count in sorted(seen.items()):
        if count > 1:
            problems.append(f"duplicate subsection number ## {num} appears {count}x")

    # every section 1..11 must be present and numbered
    missing_secs = [s for s in range(1, 12)
                    if not any(l.startswith(f"## {s}.") for l in h2)]
    if missing_secs:
        problems.append(f"sections with no ## N.x subsections: {missing_secs}")
    for s in range(1, 12):
        if not any(l.startswith(f"# §{s} ") for l in lines):
            problems.append(f"H1 '# §{s} ' heading missing")

    # ---- cross-reference resolution
    targets = set()
    for l in lines:
        m = re.match(r"^#+ §(\d+(?:\.\d+)*)", l)
        if m:
            targets.add(m.group(1))
        m = re.match(r"^#+ (\d+(?:\.\d+)*)", l)
        if m:
            targets.add(m.group(1))

    def resolves(ref: str) -> bool:
        return ref in targets or any(t.startswith(ref + ".") for t in targets)

    dangling: list[str] = []
    for i, l in enumerate(lines, 1):
        for m in REF.finditer(l):
            # skip refs into other artifacts of this project, e.g. "R15 §0.2", "P3 §2"
            if re.search(r"[A-Za-z]\d+\s*$", l[:m.start()]):
                continue
            for grp in (m.group(1), m.group(2)):
                if grp and not resolves(grp):
                    dangling.append(f"L{i}: §{grp} has no matching heading")

    print(f"MANUSCRIPT.md: {len(doc):,} chars, {doc.count(chr(10)) + 1:,} lines")
    print(f"H1 sections: {len([l for l in lines if l.startswith('# §')])}")
    print(f"H2 subsections: {len(h2)} across sections {secs}")

    if dangling:
        print(f"\nDANGLING CROSS-REFERENCES ({len(dangling)}):")
        for d in dangling[:40]:
            print("  ", d)
    else:
        print("\ncross-references: all §N references resolve to a heading")

    if remapped_refs:
        print(f"\nin-text refs remapped by the draft's own renumbering "
              f"({len(remapped_refs)}) -- check none meant another section:")
        for r in remapped_refs[:40]:
            print("  ", r)

    if problems:
        print("\nBUILD PROBLEMS (manuscript NOT written):")
        for p in problems[:10]:
            print("  ", p)
        return 1

    # AUDIT FIX (round 5, F4): a dangling reference used to be reported and then WRITTEN
    # anyway (`return 1` after the write). A probe demonstrated it by injecting
    # "§99.9" -- the file was overwritten despite the failure. Dangling references now
    # block the write like any other build problem, so a broken cross-reference cannot
    # ship behind a non-zero exit code nobody reads.
    if dangling:
        print(f"\nDANGLING REFERENCES BLOCK THE WRITE ({len(dangling)}):")
        for d in dangling[:20]:
            print("  ", d)
        print("manuscript NOT written")
        return 1

    io.open(out_path, "w", encoding="utf-8", newline="\n").write(doc)
    print("\nverification: PASS (no glued headings, sections 1-11 numbered)")
    print("P22 evidence present in §8:", "CHAIN-AUDIT" in doc and "0.0062" in doc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
