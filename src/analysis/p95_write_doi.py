"""Write the Zenodo DOI back into the paper, and fix the doubled author name.

The DOI now exists, so the paper may cite it. The order matters and this is the step it was
waiting for: a paper that claims a citable DOI before the DOI exists is making a claim it
cannot support, in a paper about claims that cannot be supported.

Cites the CONCEPT DOI (10.5281/zenodo.22901248), not the version DOI, because the concept DOI
always resolves to the latest release -- so a future v1.0.2 does not invalidate the citation.

Also fixes a cosmetic defect in CITATION.cff: the author publishes under a handle with no
separate given/family split, so putting it in both fields made Zenodo render "PerryLink,
PerryLink". CFF has a `name` field for exactly this case.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER, ROOT  # noqa: E402

CONCEPT = "10.5281/zenodo.22901248"
VERSION = "10.5281/zenodo.22901249"
URL = "https://doi.org/10.5281/zenodo.22901248"

ok = miss = 0


def sub(path: Path, old: str, new: str, label: str) -> None:
    global ok, miss
    if not path.exists():
        print(f"  SKIP  {label} (no file)")
        return
    t = path.read_text(encoding="utf-8")
    if old in t:
        path.write_text(t.replace(old, new, 1), encoding="utf-8")
        print(f"  ok    {label}")
        ok += 1
    else:
        print(f"  MISS  {label}")
        miss += 1


# ---- 1. CITATION.cff: the DOI, and a clean author name ------------------------------
c = ROOT / "CITATION.cff"
t = c.read_text(encoding="utf-8")
t = t.replace(
    'authors:\n'
    '  - family-names: "PerryLink"\n'
    '    given-names: "PerryLink"\n'
    '    alias: "PerryLink"\n'
    '    affiliation: "Independent Researcher"',
    '# The author publishes under a handle with no separate given/family split, so `name` is\n'
    '# used rather than the two fields -- putting the handle in both made Zenodo render it as\n'
    '# "PerryLink, PerryLink".\n'
    'authors:\n'
    '  - name: "PerryLink"\n'
    '    alias: "PerryLink"\n'
    '    affiliation: "Independent Researcher"', 1)
t = t.replace(
    '# NOTE: `version` and `date-released` are set by the release tag, not guessed here.\n'
    '# `doi` is added after the first Zenodo archive of a GitHub release.',
    f'doi: "{CONCEPT}"\n'
    'version: "v1.0.1"\n'
    'date-released: "2026-09-22"\n'
    '# The CONCEPT DOI, which always resolves to the latest release. The version DOI for\n'
    f'# v1.0.1 is {VERSION}.', 1)
c.write_text(t, encoding="utf-8")
print("  ok    CITATION.cff: DOI + clean author name")

# ---- 2. README -----------------------------------------------------------------------
r = ROOT / "README.md"
t = r.read_text(encoding="utf-8")
import re  # noqa: E402
m = re.search(r"Zenodo DOI, added at the\s*\n?first tagged release", t)
if m:
    t = t[:m.start()] + f"archived at [{CONCEPT}]({URL})" + t[m.end():]
    r.write_text(t, encoding="utf-8")
    print("  ok    README: DOI reference")
else:
    print("  MISS  README DOI anchor")

# ---- 3. the paper's data availability, both languages --------------------------------
ZH_OLD = "`results\\` 下 **42** 个 JSON"
ZH_NEW = (f"**制品已存档并带 DOI：[{CONCEPT}]({URL})**（concept DOI，永远指向最新版本）。\n\n"
          "`results\\` 下 **42** 个 JSON")
sub(PAPER / "09-10-11-discussion-limits-repro-draft.md", ZH_OLD, ZH_NEW, "paper zh: DOI")

EN = PAPER / "en" / "09-10-11-discussion-limits-repro.md"
te = EN.read_text(encoding="utf-8") if EN.exists() else ""
if EN.exists() and "zenodo" not in te.lower():
    # insert before the first heading of section 11's artifacts list
    anchor = "## 11.1"
    if anchor in te:
        te = te.replace(anchor, f"**The artifact is archived and has a DOI: "
                                f"[{CONCEPT}]({URL})** (concept DOI, always resolving to the "
                                f"latest release).\n\n" + anchor, 1)
    else:
        i = te.find("# §11")
        j = te.find("\n", i) + 1
        te = te[:j] + f"\n**The artifact is archived and has a DOI: [{CONCEPT}]({URL})** " \
                      f"(concept DOI, always resolving to the latest release).\n" + te[j:]
    EN.write_text(te, encoding="utf-8")
    print("  ok    paper en: DOI")
else:
    print("  MISS  paper en: DOI")

print(f"\n{ok} applied, {miss} not found")
print(f"  concept DOI : {CONCEPT}")
print(f"  version DOI : {VERSION}")
