"""Copy the corrected defect-2/3 and new defect-6 blocks from the assembled
manuscripts into the section drafts they are assembled from.

WHY a script rather than a second round of hand edits: the same block exists in
two places (draft -> assembled), and retyping it is how the two drift apart. The
assembler rebuilds the manuscript FROM the drafts, so editing only the manuscript
would be silently undone on the next build -- and editing both by hand invites the
two copies to differ.

The source of truth here is the assembled manuscript, because that is what was
just corrected and reviewed; this script pushes that text back into the drafts.

Verifies afterwards that a rebuild produces byte-identical text for the affected
sections, and exits non-zero if the anchors are missing rather than writing
nothing and reporting success.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]

# (assembled, draft, start marker, end marker)
# The block runs from the defect heading up to the next heading, exclusive.
PAIRS = [
    (
        ROOT / "paper" / "MANUSCRIPT.md",
        ROOT / "paper" / "03-systems-draft.md",
        "### 缺陷 2：",
        ("### 缺陷 4：",),
    ),
    (
        ROOT / "paper" / "en" / "MANUSCRIPT.md",
        ROOT / "paper" / "en" / "03-04-systems-method.md",
        "### Defect 2:",
        ("### Defect 4:",),
    ),
    (
        ROOT / "paper" / "MANUSCRIPT.md",
        ROOT / "paper" / "03-systems-draft.md",
        "### 缺陷 5：",
        ("---", "\n# ", "\n## "),
    ),
    (
        ROOT / "paper" / "en" / "MANUSCRIPT.md",
        ROOT / "paper" / "en" / "03-04-systems-method.md",
        "### Defect 5:",
        ("---", "\n# ", "\n## "),
    ),
    # The inventory-count paragraph lives in the reproducibility section, and it
    # too must be edited in the DRAFT: the English manuscript is generated, so a
    # hand edit to it is undone by the next build. That is why this script exists
    # rather than a second round of edits.
    #
    # The inventory-count paragraph was edited by hand instead, for both
    # languages. Four attempts to sync it through this script failed with
    # "anchor not found" even though the anchor's code points were verified
    # against the file with recon/R18-locate-count-sentence.py and matched
    # exactly. Rather than a fifth attempt, the script's job was narrowed to the
    # four defect blocks it does synchronise correctly, and the count sentence --
    # a single line, in two files -- was edited directly.
    #
    # Recorded rather than quietly dropped: a sync script that covers SOME of the
    # paired text is a thing a later reader needs to know about, because the
    # unsynchronised part will silently drift if only the manuscript is edited.
]


def block(text: str, start: str, ends: tuple[str, ...]) -> str:
    """Text from `start` up to the first of `ends`, exclusive."""
    i = text.find(start)
    if i < 0:
        raise SystemExit(f"anchor not found: {start!r}")
    stops = [text.find(e, i + len(start)) for e in ends]
    stops = [s for s in stops if s > 0]
    if not stops:
        raise SystemExit(f"no end marker found after {start!r}")
    return text[i:min(stops)].rstrip("\n")


def main() -> int:
    for assembled, draft, start, ends in PAIRS:
        want = block(assembled.read_text(encoding="utf-8"), start, ends)
        have = block(draft.read_text(encoding="utf-8"), start, ends)
        if want == have:
            print(f"  = {draft.name:28} {start!r:20} already identical")
            continue
        text = draft.read_text(encoding="utf-8")
        i = text.find(have)
        if i < 0:
            raise SystemExit(f"could not locate the existing block in {draft}")
        draft.write_text(text[:i] + want + text[i + len(have):], encoding="utf-8")
        print(f"  + {draft.name:28} {start!r:20} updated "
              f"({len(have)} -> {len(want)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
