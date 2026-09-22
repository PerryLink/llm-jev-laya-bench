"""Is Laya's answer to an IDENTICAL request bit-reproducible?

This matters more than any single artifact: every Laya arm in the paper is a single call
per cell, so if the engine samples, the Laya numbers are draws and not measurements.

Sends the SAME state, the SAME question and the SAME criteria several times, for both
primitives the project uses. Read-only; local sidecar; $0.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src" / "instrument"))
from laya_client import LayaClient  # noqa: E402

STATE = ("Ledger, oldest first.\n"
         "[r1] opening statement: pallets shipped in Q3 = 4182 units\n"
         "[r2] note: the figure was recorded at intake\n"
         "[c1] Correction: the authoritative pallets shipped in Q3 is 5310 units.\n"
         "[r4] sign-off: review closed")

NOUL = {"q": {"type": "noul",
              "instructions": "Is the authoritative pallets shipped in Q3 equal to 5310?",
              "criteria": {"true": "the state says 5310", "false": "the state does not"}}}
CHOICE = {"q": {"type": "choice",
                "instructions": "What is the authoritative pallets shipped in Q3?",
                "criteria": {"o01": "4182 units", "o02": "4182 units",
                             "o03": "5310 units", "o04": "5387 units"}}}
CHOICE = {"q": {"type": "choice",
                "instructions": "What is the authoritative pallets shipped in Q3?",
                "criteria": {"o01": "4182 units", "o02": "5255 units",
                             "o03": "5310 units", "o04": "5387 units"}}}

REPS = 6

client = LayaClient()
client.ensure_up()

for label, q in (("noul", NOUL), ("choice", CHOICE)):
    vals = []
    for i in range(REPS):
        r = client.ask(STATE, q)
        a = r["answers"]["q"]
        if label == "noul":
            vals.append(a.get("noul"))
        else:
            vals.append((a.get("choice"),
                         (a.get("probabilities") or {}).get(a.get("choice"))))
    print(f"--- {label}: {REPS} identical requests")
    for v in vals:
        print(f"      {v}")
    print(f"    distinct outcomes : {len(set(vals))}  -> "
          f"{'DETERMINISTIC' if len(set(vals)) == 1 else 'NOT DETERMINISTIC'}")
    print()
