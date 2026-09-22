"""Measure the marker duplication left behind by p76/p77's append-style edits.

p76 and p77 tested `old` before `new`, and their edits APPEND a marker to an existing sentence.
On the re-run the original text was still present, so the marker was appended again. p84 fixed
the guards; the already-written duplicates are still in the drafts, and duplicated disclosure
text is worse than none: a reader cannot tell whether a number carries two caveats or one.

This script only measures. The repair is p89, which reconstructs each appended tail from the
fix scripts themselves rather than by pattern-matching prose.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER, ROOT  # noqa: E402


def load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "src" / "analysis" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# this host's console is GBK and the marker text contains U+26A0; without this the MEASUREMENT
# crashes while printing, which is how verify_all died too (fixed there in p81)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                                # noqa: BLE001
    pass


total = 0
for mod_name, sub in (("p76_mark_untraceable_numbers", None),
                      ("p77_sync_english_untraceable", "en")):
    mod = load(mod_name)
    root = PAPER / sub if sub else PAPER
    print(f"=== {mod_name}")
    for entry in mod.EDITS:
        fname, old, new = entry[0], entry[1], entry[2]
        # the appended text is whichever side of `new` is not part of `old`
        if new.startswith(old):
            tail = new[len(old):]
        elif new.endswith(old):
            tail = new[:-len(old)]
        else:
            tail = new
        if not tail.strip():
            continue
        t = (root / fname).read_text(encoding="utf-8")
        n = t.count(tail)
        if n != 1:
            print(f"  {fname:42s} x{n}  {tail.strip()[:64]!r}")
            total += n - 1
    print()
print(f"duplicated marker copies to remove: {total}")
