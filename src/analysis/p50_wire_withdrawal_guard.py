"""Wire the withdrawal guard into verify_all.py as check J1."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER, ROOT  # noqa: E402

V = PAPER / "verify_all.py"
t = V.read_text(encoding="utf-8")

ANCHOR = "    check_translation_coverage()"

BLOCK = ANCHOR + "\n" + '''    # Every claim withdrawn or corrected this session must be gone from EVERY document, and
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
             _tail[-1] if _tail else "see p49_verify_withdrawals.py")'''

if "J1 withdrawals" in t:
    print("  already wired")
elif ANCHOR in t:
    V.write_text(t.replace(ANCHOR, BLOCK, 1), encoding="utf-8")
    print("  ok    verify_all.py: J1 wired in")
else:
    print("  MISS  anchor not found")
    sys.exit(1)
