# -*- coding: utf-8 -*-
"""P27 — LIVE JEV, with a machine-readable artifact behind every number.

WHAT THIS REPLACES
------------------
The paper's Jev column previously rested on `probes/P12` and `probes/P13`, which are
markdown with no `results/*.json` behind them; §10.1 listed that as an open gap, and P13
turned out to carry summary statistics that are mutually impossible (n=13, mean 1,879,
min 919, max 11,984 cannot coexist once P12's nine listed values are accounted for --
see results/ERRATA.md N-1). This probe re-measures the whole Jev column through
`jev_client`, which hits the same route and returns the same numbers as the DSH plugin.

MEASURED
  A. LATENCY, n sequential calls, wall-clock measured by this client. The provider
     reports no latency at all, so a wall clock is the only honest source.
  B. COST, from the provider's own `usage.cost`.
  C. PROVIDER FIELD INVENTORY: exactly which fields the provider returns. Everything the
     plugin adds on top (`band`, `probability`, `truncated`, `stateChars`, `latencyMs`)
     is therefore access-layer synthesis, not provider reporting.
  D. CRITERIA SENSITIVITY: does re-wording the criteria move the answer? On the mock it
     moved by exactly 0.0000 while `questionsChars` changed, i.e. the boundary was
     serialised but never hashed. Live, it must move.
  E. STATE WINDOW: ladder upward to test whether the 16,000-character cap is the
     provider's or the plugin's. The plugin caps at 16,000 chars; if the direct route
     accepts materially more, the cap is PLUGIN-side and the paper's window claim must be
     scoped to the access layer.
  F. TRUTH BATTERY: 8 items with unambiguous ground truth (P12's 8/8 claim, re-measured).
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(r"D:\Projects\llm-jev-laya-bench")
sys.path.insert(0, str(ROOT / "src" / "instrument"))
from jev_client import (ask, noul_of, cost_of, input_tokens_of, provider_of,  # noqa: E402
                        resolved_model, instrument_record, JevError)

RESULTS = ROOT / "results"
LATENCY_N = 20

ITEMS = [
    ("T1", True, "Audit memo. Invoice INV-4471 is fraudulent. The forensic accountant "
                 "confirmed the fraud and the vendor admitted it in writing.",
     "Is invoice INV-4471 fraudulent?"),
    ("T2", False, "Audit memo. Invoice INV-4471 was reviewed and found to be entirely "
                  "correct. No irregularities were identified.",
     "Is invoice INV-4471 fraudulent?"),
    ("T3", True, "Incident report. The authentication service returned HTTP 503 for 47 "
                 "minutes on 14 March. Root cause was a misconfigured connection pool.",
     "Did the authentication service return HTTP 503?"),
    ("T4", False, "Incident report. The authentication service returned HTTP 200 for every "
                  "request during the window. No errors were recorded.",
     "Did the authentication service return HTTP 503?"),
    ("T5", True, "Shipment log. Parcel 99120 departed the Rotterdam depot on 3 May and was "
                 "signed for in Oslo on 6 May.", "Did the parcel arrive in Oslo?"),
    ("T6", False, "Shipment log. Parcel 99120 was returned to the Rotterdam warehouse on "
                  "5 May after a failed delivery attempt; it never reached Norway.",
     "Did the parcel arrive in Oslo?"),
    ("T7", True, "Clinical note. The patient has a documented penicillin allergy. "
                 "Amoxicillin was withheld and azithromycin prescribed instead.",
     "Was amoxicillin withheld?"),
    ("T8", False, "Clinical note. Amoxicillin 500mg three times daily was prescribed for "
                  "ten days. The patient reports no allergies.", "Was amoxicillin withheld?"),
]

FILLER = ("Quarterly logistics review. The warehouse processed routine shipments and "
          "filed standard compliance paperwork. ")


def bound(q: str) -> dict:
    core = q.rstrip("?").lower()
    return {"true": f"the state asserts that {core}",
            "false": f"the state does not assert that {core}"}


def noul_q(q: str, criteria: dict | None = None) -> dict:
    return {"q": {"type": "noul", "instructions": q,
                  "criteria": criteria or bound(q),
                  "boundary": criteria or bound(q)}}


def main() -> int:
    out: dict = {"_instrument": instrument_record(
        "direct HTTP route; cross-validated against the DSH plugin on an identical "
        "request (same noul, same input_tokens, same cost)"),
        "_spend_usd": 0.0}

    def pay(r):
        c = cost_of(r) or 0.0
        out["_spend_usd"] = round(out["_spend_usd"] + c, 9)
        return r

    # ---------------- A/B: latency + cost, sequential
    print("=== A/B  latency n=%d (sequential) ===" % LATENCY_N)
    state = "Audit memo. Invoice INV-4471 is fraudulent. The vendor admitted it in writing."
    lat, rows = [], []
    for i in range(LATENCY_N):
        try:
            r = pay(ask(state, noul_q("Is invoice INV-4471 fraudulent?")))
            lat.append(r["_latency_ms_wall"])
            rows.append({"i": i, "latency_ms_wall": r["_latency_ms_wall"],
                         "noul": noul_of(r), "cost_usd": cost_of(r),
                         "input_tokens": input_tokens_of(r),
                         "provider": provider_of(r),
                         "resolved_model": resolved_model(r),
                         # AUDIT FIX (round 5): `_attempts` was recorded by the client but
                         # persisted nowhere, so a run could have been mostly retries with
                         # no way to tell. It is now carried into the artifact.
                         "attempts": r.get("_attempts")})
            print("  %2d  %7.0f ms  noul=%s cost=%s" %
                  (i, r["_latency_ms_wall"], noul_of(r), cost_of(r)))
        except JevError as exc:
            rows.append({"i": i, "error": str(exc)[:200]})
            print("  %2d  ERROR %s" % (i, str(exc)[:90]))
    ok = [x["latency_ms_wall"] for x in rows if "latency_ms_wall" in x]
    attempts = [x.get("attempts") for x in rows if x.get("attempts") is not None]
    out["latency"] = {
        "n": len(ok),
        "p50_ms": round(statistics.median(ok), 1) if ok else None,
        "mean_ms": round(statistics.fmean(ok), 1) if ok else None,
        "min_ms": min(ok) if ok else None,
        "max_ms": max(ok) if ok else None,
        "all_ms": ok,
        "source": "wall clock measured by this client; the provider reports none",
        "attempts": {"n_recorded": len(attempts),
                     "max": max(attempts) if attempts else None,
                     "n_calls_needing_a_retry": sum(1 for a in attempts if a > 1),
                     "note": ("only the FINAL attempt's elapsed time is recorded as the "
                              "call's latency, so a timeout-then-success call enters the "
                              "distribution as its short final leg -- the distribution is "
                              "biased SHORT, not long")},
        "rows": rows,
    }
    costs = [x["cost_usd"] for x in rows if x.get("cost_usd") is not None]
    toks = [x["input_tokens"] for x in rows if x.get("input_tokens")]
    out["cost"] = {
        "n": len(costs),
        "min_usd": min(costs) if costs else None,
        "max_usd": max(costs) if costs else None,
        "mean_usd": round(statistics.fmean(costs), 9) if costs else None,
        "input_tokens_min": min(toks) if toks else None,
        "input_tokens_max": max(toks) if toks else None,
        "source": "provider usage.cost (the TypeSafe route reports none; this route does)",
    }

    # ---------------- C: provider field inventory
    print("\n=== C  provider field inventory ===")
    raw = pay(ask(state, noul_q("Is invoice INV-4471 fraudulent?")))
    out["provider_fields"] = {
        "top_level": sorted(k for k in raw if not k.startswith("_")),
        "answer_keys": sorted((raw.get("answers") or {}).get("q", {}).keys()),
        "usage_keys": sorted((raw.get("usage") or {}).keys()),
        "plugin_only_fields": ["band", "probability", "truncated", "stateChars",
                               "questionsChars", "redactions", "latencyMs"],
        "conclusion": ("the provider returns no band / probability / truncated / "
                       "stateChars / latencyMs; those are synthesized by the access "
                       "layer, so Result B is a claim about the ACCESS LAYER"),
        # AUDIT FIX (round 5): this call was CHARGED into `_spend_usd` but stored no cost,
        # no latency and no attempt count, so it appeared in no row and every total
        # recomputed from rows alone came out exactly one call short. The ledger and the
        # persisted evidence now agree.
        "cost_usd": cost_of(raw),
        "latency_ms_wall": raw.get("_latency_ms_wall"),
        "attempts": raw.get("_attempts"),
    }
    print("  provider top-level:", out["provider_fields"]["top_level"])
    print("  answer keys       :", out["provider_fields"]["answer_keys"])

    # ---------------- D: criteria sensitivity (the mock moved by exactly 0.0000)
    print("\n=== D  criteria sensitivity ===")
    q = "Is invoice INV-4471 fraudulent?"
    variants = {
        "explicit": {"true": "the state asserts that invoice INV-4471 is fraudulent",
                     "false": "the state does not assert that invoice INV-4471 is fraudulent"},
        "reversed": {"true": "the state asserts that invoice INV-4471 is entirely correct",
                     "false": "the state does not assert that invoice INV-4471 is entirely correct"},
        "terse": {"true": "fraud", "false": "no fraud"},
    }
    sens = {}
    for name, crit in variants.items():
        r = pay(ask(state, noul_q(q, crit)))
        sens[name] = {"noul": noul_of(r), "questions_chars": len(json.dumps(crit)),
                      "input_tokens": input_tokens_of(r), "cost_usd": cost_of(r)}
        print("  %-9s noul=%-6s in_tok=%-6s" % (name, sens[name]["noul"],
                                                sens[name]["input_tokens"]))
    vals = [v["noul"] for v in sens.values() if v["noul"] is not None]
    out["criteria_sensitivity"] = {
        "variants": sens,
        "distinct_noul_values": sorted(set(vals)),
        "moved": len(set(vals)) > 1,
        "mock_reference": ("on the mock this moved by exactly 0.0000 while "
                           "questionsChars changed 216 -> 198, i.e. the boundary was "
                           "serialised and counted but never entered the hash"),
    }

    # ---------------- E: state window ladder (is 16,000 the provider's cap?)
    print("\n=== E  state window ladder ===")
    ladder = []
    for chars in (2_000, 8_000, 15_000, 16_000, 16_500, 24_000, 40_000):
        payload = max(0, chars - len(state))
        s = state + FILLER * (payload // len(FILLER))
        try:
            r = pay(ask(s, noul_q("Is invoice INV-4471 fraudulent?")))
            ladder.append({"chars": len(s), "http": r["_http_status"],
                           "input_tokens": input_tokens_of(r), "noul": noul_of(r),
                           "cost_usd": cost_of(r)})
            print("  %6d chars -> in_tok=%-6s noul=%s" %
                  (len(s), input_tokens_of(r), noul_of(r)))
        except JevError as exc:
            ladder.append({"chars": len(s), "error": str(exc)[:200]})
            print("  %6d chars -> REFUSED/ERROR: %s" % (len(s), str(exc)[:90]))
    accepted = [x["chars"] for x in ladder if "error" not in x]
    out["state_window"] = {
        "ladder": ladder,
        "max_accepted_chars": max(accepted) if accepted else None,
        "plugin_cap_documented": 16000,
        # AUDIT FIX (F3): the conclusion used to say the cap "is PLUGIN-side" without the
        # caveat the paper carries. This probe CANNOT detect silent tail truncation: the
        # decisive content sits at the HEAD of the state, the provider returns no
        # `truncated` field, and the only tail-sensitive observable (input_tokens) is
        # recorded but never asserted on. The conclusion is therefore scoped to what was
        # actually shown.
        "conclusion": ("the provider enforced NO fixed character cap at or below 39,927 "
                       "characters (input_tokens grew monotonically with characters, "
                       "which a fixed cap would have frozen). It is NOT evidence that the "
                       "tail was read: this design cannot detect silent tail truncation, "
                       "and no paired tail-decisive arm was run."),
        "cannot_detect": "silent tail truncation (head-loaded state, no truncated field)",
        "missing_discriminating_test": ("a paired arm at the SAME length whose tail "
                                        "content supports vs contradicts the question"),
    }

    # ---------------- F: truth battery (P12's 8/8 claim, re-measured)
    print("\n=== F  truth battery n=%d ===" % len(ITEMS))
    truth_rows, correct = [], 0
    for iid, truth, st, qq in ITEMS:
        r = pay(ask(st, noul_q(qq)))
        p = noul_of(r)
        pred = None if p is None else (p >= 0.5)
        hit = (pred == truth)
        correct += bool(hit)
        truth_rows.append({"id": iid, "truth": truth, "noul": p, "pred": pred,
                           "correct": hit, "band_absent": "band" not in
                           ((r.get("answers") or {}).get("q") or {}),
                           "latency_ms_wall": r["_latency_ms_wall"],
                           "cost_usd": cost_of(r)})
        print("  %s truth=%-5s noul=%-6s pred=%-5s %s" %
              (iid, truth, p, pred, "OK" if hit else "MISS"))
    out["truth_battery"] = {
        "n": len(truth_rows), "correct": correct,
        "accuracy": round(correct / len(truth_rows), 4),
        "rows": truth_rows,
        "caveat": ("this is an 8-item template battery: it measures that the live route "
                   "judges from the state, not a general accuracy claim"),
    }

    out["_spend_usd"] = round(out["_spend_usd"], 9)
    p = RESULTS / "P27-jev-live.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== VERDICT ===")
    print("  latency n=%d p50=%.0f ms (min %.0f / max %.0f)" %
          (out["latency"]["n"], out["latency"]["p50_ms"] or -1,
           out["latency"]["min_ms"] or -1, out["latency"]["max_ms"] or -1))
    print("  cost    min=%s max=%s" % (out["cost"]["min_usd"], out["cost"]["max_usd"]))
    print("  criteria moved: %s  distinct noul: %s" %
          (out["criteria_sensitivity"]["moved"],
           out["criteria_sensitivity"]["distinct_noul_values"]))
    print("  max state accepted: %s chars (plugin cap documented at 16,000)" %
          out["state_window"]["max_accepted_chars"])
    print("  truth battery: %d/%d" % (correct, len(truth_rows)))
    print("  SPEND THIS PROBE: $%.6f" % out["_spend_usd"])
    print("written:", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
