"""Fix the English assembler's section-numbering expectation.

The section drafts use their OWN numbering, which collides across files: 03-systems-draft
is section 3, and 06-results-B-draft is ALSO section 3. The Chinese `_assemble.py` resolves
this with a RENUMBER map (06-B: 3->6, 6->7, 7->8), and the translations carry the DRAFT
numbering so the same remap can be applied to them.

The English assembler was written expecting the MANUSCRIPT numbering (6 and 7 for results B
and C) while the file it is checking carries the DRAFT numbering (3 and 6). So it reported a
complete translation as incomplete -- a false alarm in the one check whose job is to be
believed when it alarms.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

A = PAPER / "en" / "_assemble.py"
t = A.read_text(encoding="utf-8")

OLD = '    ("06-07-results-BC.md", ["6", "7"], "Results B and C"),'
NEW = ('    # DRAFT numbering, not manuscript numbering: these two drafts use section 3 and\n'
       '    # section 6 internally, colliding with the systems and discussion drafts. The Chinese\n'
       '    # _assemble.py remaps them (3->6, 6->7, 7->8); carrying the draft numbers here is what\n'
       '    # lets the same remap apply to the English.\n'
       '    ("06-07-results-BC.md", ["3", "6"], "Results B and C"),')

if OLD in t:
    A.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("  ok    assembler numbering corrected")
else:
    print("  MISS  anchor not found")
    sys.exit(1)

# also add a note to the header so the next reader is not caught by the same thing
NOTE = ('    numbering here is the DRAFT numbering, which collides across files (two different\n'
        '    drafts both call themselves section 3). See the results-B/C entry.\n')
t2 = A.read_text(encoding="utf-8")
anchor = "# (file, sections it must contain, human label) -- in manuscript order.\n"
if anchor in t2 and "collides across files" not in t2:
    A.write_text(t2.replace(anchor, anchor + NOTE, 1), encoding="utf-8")
    print("  ok    header note added")
