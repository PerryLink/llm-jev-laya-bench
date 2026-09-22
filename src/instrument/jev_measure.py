"""Jev live measurements: the numbers that were blocked on a credential.

Everything here was previously impossible. Until the OpenRouter credential was
registered, every Jev call returned `provider: "mock"`, `latencyMs: 0`,
`inputTokens: 0`, `costUsd: 0` and answers derived from a hash of the input, so the Jev
column of the cost table, the latency ladder, the state cap, the rank batch cap and the
calibration state were all unwritable.

WHAT THIS MEASURES, AND WHY EACH ONE MATTERS
  1. LATENCY, sequentially, n calls. R13 measured this host's floor for an
     UNAUTHENTICATED refusal at 1011-2349 ms and explicitly warned that this is a floor
     and must not be published as Jev's latency. A real distribution is now obtainable.
     Sequential deliberately: R11 measured that parallel tool calls share one result
     timestamp, so a batched loop yields batch wall-time, not per-call latency.
  2. COST, from the provider's own `usage.costUsd`. This is the first time a Jev cost
     figure exists that is not an inference from a published price list. D1 declined to
     put a Jev row in the cost table partly BECAUSE the TypeSafe route reports no cost;
     the OpenRouter route does.
  3. STATE CAP. The plugin caps `state` at 16,000 characters and truncates rather than
     refusing (R12). Whether that holds live is unverified.
  4. `noul` vs `probability` semantics (R12 trap T-1): `probability` is P(the ANSWERED
     option). A live check is that `answer == "false"` implies `probability == 1 - noul`.
  5. BOUNDARY SENSITIVITY, now that the mock's structural zero is gone. The mock gave
     exactly 0.0000 because the boundary never entered its hash.

DESIGN NOTE: every request sets an explicit boundary on noul questions. R2 originally
recommended this as a confound control and R12 then showed the recommendation had NO
measurement basis, because the mock cannot exhibit a boundary effect. It can now be
tested rather than assumed.
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
import statistics
import sys
from pathlib import Path


RESULTS = ROOT / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

# Eight items with unambiguous ground truth, spread across easy/hard and true/false so
# the battery is not all one class.
ITEMS: list[dict] = [
    {"id": "T1", "truth": True,
     "state": "Audit memo. Invoice INV-4471 is fraudulent. The forensic accountant "
              "confirmed the fraud and the vendor admitted it in writing.",
     "q": "Is invoice INV-4471 fraudulent?"},
    {"id": "T2", "truth": False,
     "state": "Audit memo. Invoice INV-4471 was reviewed and found to be entirely "
              "correct. No irregularities were identified.",
     "q": "Is invoice INV-4471 fraudulent?"},
    {"id": "T3", "truth": True,
     "state": "Incident report. The authentication service returned HTTP 503 for 47 "
              "minutes on 14 March. Root cause was a misconfigured connection pool.",
     "q": "Did the authentication service return HTTP 503?"},
    {"id": "T4", "truth": False,
     "state": "Incident report. The authentication service returned HTTP 200 for every "
              "request during the window. No errors were recorded.",
     "q": "Did the authentication service return HTTP 503?"},
    {"id": "T5", "truth": True,
     "state": "Shipment log. Parcel 99120 departed the Rotterdam depot on 3 May and was "
              "signed for in Oslo on 6 May.",
     "q": "Did the parcel arrive in Oslo?"},
    {"id": "T6", "truth": False,
     "state": "Shipment log. Parcel 99120 was returned to the Rotterdam warehouse on "
              "5 May after a failed delivery attempt; it never reached Norway.",
     "q": "Did the parcel arrive in Oslo?"},
    {"id": "T7", "truth": True,
     "state": "Clinical note. The patient has a documented penicillin allergy. "
              "Amoxicillin was withheld and azithromycin prescribed instead.",
     "q": "Was amoxicillin withheld?"},
    {"id": "T8", "truth": False,
     "state": "Clinical note. Amoxicillin 500mg three times daily was prescribed for "
              "ten days. The patient reports no allergies.",
     "q": "Was amoxicillin withheld?"},
]

FILLER = ("Quarterly logistics review. The warehouse processed routine shipments and "
          "filed standard compliance paperwork. ")


def boundary(q: str) -> dict:
    return {"true": f"the state asserts that {q.rstrip('?').lower()}",
            "false": f"the state does not assert that {q.rstrip('?').lower()}"}


def main() -> int:
    """Print the payloads to send. The agent holds the Jev tools, so it executes them
    and writes the responses back; this script owns the analysis, not the transport."""
    mode = sys.argv[1] if len(sys.argv) > 1 else "payloads"
    if mode == "payloads":
        print(json.dumps([{"id": it["id"],
                           "state": it["state"],
                           "questions": {"q": {"type": "noul",
                                               "instructions": it["q"],
                                               "criteria": boundary(it["q"])}}}
                          for it in ITEMS], indent=2))
        print("\nLATENCY_STATE " + json.dumps({"filler": FILLER * 3}))
        return 0
    if mode == "harness":
        from jev_harness import run_all  # noqa
        return run_all()
    raise SystemExit(f"unknown mode {mode!r}")


def analyse(records: list[dict]) -> dict:
    """Compute everything from recorded live responses. Mechanical, not eyeballed."""
    lat = [r["latencyMs"] for r in records if r.get("latencyMs")]
    cost = [(r.get("usage") or {}).get("costUsd") for r in records]
    cost = [c for c in cost if c is not None]
    tin = [(r.get("usage") or {}).get("inputTokens") for r in records]
    tin = [t for t in tin if t]
    per_item = []
    for r in records:
        a = (r.get("answers") or {}).get("q", {})
        noul = a.get("noul")
        prob = a.get("probability")
        ans = a.get("answer")
        per_item.append({"id": r.get("id"), "noul": noul, "probability": prob,
                         "answer": ans, "band": a.get("band"),
                         # R12 T-1: probability is P(the ANSWERED option)
                         "prob_is_p_answered": (
            None if (noul is None or prob is None) else
            (abs(prob - noul) < 1e-9 if ans == "true" else abs(prob - (1 - noul)) < 1e-9))})
    return {
        "n_calls": len(records),
        "latency_ms": {"p50": statistics.median(lat) if lat else None,
                       "mean": statistics.fmean(lat) if lat else None,
                       "min": min(lat) if lat else None,
                       "max": max(lat) if lat else None},
        "cost_usd": {"mean": statistics.fmean(cost) if cost else None,
                     "total": sum(cost) if cost else None},
        "input_tokens": {"mean": statistics.fmean(tin) if tin else None,
                         "min": min(tin) if tin else None,
                         "max": max(tin) if tin else None},
        "probability_semantics_all_correct": all(
            p["prob_is_p_answered"] for p in per_item
            if p["prob_is_p_answered"] is not None),
        "per_item": per_item,
    }


if __name__ == "__main__":
    sys.exit(main())
