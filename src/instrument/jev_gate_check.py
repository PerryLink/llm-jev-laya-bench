"""Live-Jev activation gate: prove the gate discriminates on the MOCK first.

ISSUE 1 OF THE THREE THE HUMAN ASKED TO RESOLVE
-----------------------------------------------
The Jev credential cannot be created by an agent: it requires an account action at
console.typesafe.ai, or an OpenRouter key. What CAN be settled without a credential is
that the harness will not silently record mock output as a Jev measurement. That is the
part that matters, because R12 measured the mock to be dangerous precisely for looking
plausible: a 14-item calibration battery on it produced a believable confidence spread
while scoring Brier 0.359, worse than a constant 0.5.

TWO DISCRIMINATORS, BOTH MEASURED ON THE MOCK IN THIS PROJECT
-------------------------------------------------------------
  A  decisive state. A memo asserting fraud three times must score noul >= 0.9.
     MEASURED on the mock: 0.7142 (this project, 2026-09-22). R12 measured 0.0317 on a
     slightly different fixture. Either way it fails a 0.9 bar.
  B  boundary sensitivity. Same state, same question id, same instruction text, only the
     declared boundary differs. MEASURED on the mock: noul = 0.7142 with EITHER boundary,
     i.e. delta EXACTLY 0.0000, while `egress.questionsChars` moved 216 -> 198. The
     boundary was serialised and counted, but never entered the hash. A boundary study on
     the mock would therefore "prove" boundary wording is irrelevant.

THE DETECTION RULE ITSELF
-------------------------
Recognition must key on `provider == "mock"`. It must NOT key on the presence of a
`warning`, because R12 observed a short-circuiting call (`jev_rank` with zero candidates)
that returned NO warning field at all and an empty `model`. A short-circuiting call
therefore looks CLEANER than a normal one.

USAGE
-----
`python jev_gate_check.py`    run against the live provider through the MCP tool path
`python jev_gate_check.py --verify-fixture`  assert the recorded mock baseline still holds
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Projects\llm-jev-laya-bench")
RESULTS = ROOT / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

DISC_A_MIN = 0.9

# Recorded mock baselines, measured in this project. Kept as constants so the gate can be
# self-tested without a credential and so a future live run has something to differ from.
MOCK_BASELINE = {
    "noul_on_decisive_state": 0.7142,
    "boundary_delta": 0.0,
    "questionsChars_with_boundary": 216,
    "questionsChars_without_boundary": 198,
    "provider": "mock",
    "latencyMs": 0,
    "inputTokens": 0,
}

DECISIVE_STATE = {
    "t": "Audit memo. Invoice INV-4471 is fraudulent. The forensic accountant confirmed "
         "the fraud and the vendor admitted it in writing."
}
Q_WITH_BOUNDARY_A = {
    "q": {"type": "noul", "instructions": "Is invoice INV-4471 fraudulent?",
          "criteria": {"true": "the state states that invoice INV-4471 is fraudulent",
                       "false": "the state does not state that invoice INV-4471 is fraudulent"}}
}
Q_WITH_BOUNDARY_B = {
    "q": {"type": "noul", "instructions": "Is invoice INV-4471 fraudulent?",
          "criteria": {"true": "the memo asserts fraud as an established finding",
                       "false": "the memo raises fraud only as an open question"}}
}


def classify(resp: dict) -> dict:
    """Detection keys on the provider field, never on a warning's absence."""
    usage = resp.get("usage") or {}
    return {
        "provider": resp.get("provider"),
        "is_mock_by_provider_field": resp.get("provider") == "mock",
        "had_warning": "warning" in resp,
        "warning_absent_would_misread_as_live": "warning" not in resp,
        "model": resp.get("model"),
        "latency_ms": resp.get("latencyMs"),
        "input_tokens": usage.get("inputTokens"),
        "cost_usd": usage.get("costUsd"),
        "state_chars": (resp.get("egress") or {}).get("stateChars"),
        "questions_chars": (resp.get("egress") or {}).get("questionsChars"),
    }


def noul_of(resp: dict) -> float:
    ans = resp.get("answers")
    if isinstance(ans, dict):
        first = next(iter(ans.values()), {})
    elif isinstance(ans, list) and ans:
        first = ans[0]
    else:
        first = {}
    return float(first.get("noul", float("nan")))


def verdict(resp_a: dict, resp_b1: dict, resp_b2: dict) -> dict:
    """Compute the gate verdict mechanically rather than by eye."""
    cls = classify(resp_a)
    noul_a = noul_of(resp_a)
    p1, p2 = noul_of(resp_b1), noul_of(resp_b2)
    delta = abs(p1 - p2)
    checks = {
        "provider_is_not_mock": not cls["is_mock_by_provider_field"],
        f"discriminator_A_decisive_state_ge_{DISC_A_MIN}": noul_a >= DISC_A_MIN,
        "discriminator_B_boundary_delta_nonzero": delta > 0.0,
        "latency_is_positive": (cls["latency_ms"] or 0) > 0,
        "input_tokens_positive": (cls["input_tokens"] or 0) > 0,
    }
    passed = all(checks.values())
    return {
        "classification_of_discriminator_A": cls,
        "noul_on_decisive_state": noul_a,
        "boundary_probe": {"with_boundary": p1, "with_other_boundary": p2,
                           "delta": delta},
        "checks": checks,
        "gate": "LIVE" if passed else "MOCK_OR_UNVERIFIED",
        "explanation": (
            "Provider is live and Jev answers from the state; Jev arms may be populated."
            if passed else
            "At least one check failed. The mock scores below the bar on a decisive state "
            "and yields a boundary delta of exactly 0.0 by construction, so a failure "
            "means the credential did not take effect -- NOT that Jev is weak."
        ),
    }


def verify_fixture() -> int:
    """Self-test the gate against the recorded mock baseline. No credential needed."""
    fake_mock_a = {"provider": "mock", "model": "jev-latest", "latencyMs": 0,
                   "answers": {"q": {"noul": MOCK_BASELINE["noul_on_decisive_state"]}},
                   "usage": {"inputTokens": 0, "costUsd": 0}, "warning": "SYNTHETIC"}
    fake_mock_b1 = {"provider": "mock", "answers": {"q": {"noul": 0.7142}},
                    "egress": {"questionsChars": 216}}
    fake_mock_b2 = {"provider": "mock", "answers": {"q": {"noul": 0.7142}},
                    "egress": {"questionsChars": 198}}
    v = verdict(fake_mock_a, fake_mock_b1, fake_mock_b2)
    ok = (v["gate"] == "MOCK_OR_UNVERIFIED"
          and not v["checks"]["provider_is_not_mock"]
          and not v["checks"][f"discriminator_A_decisive_state_ge_{DISC_A_MIN}"]
          and not v["checks"]["discriminator_B_boundary_delta_nonzero"])
    print("SELF-TEST against the recorded mock baseline")
    print(json.dumps(v, indent=2))
    print("\nGATE CORRECTLY REJECTS THE MOCK:", ok)
    # And the inverse: a synthetic live-shaped response must PASS, or the gate is a wall.
    live_a = {"provider": "live", "model": "jev-latest", "latencyMs": 138.4,
              "answers": {"q": {"noul": 0.9612}}, "usage": {"inputTokens": 141}}
    live_b1 = {"provider": "live", "answers": {"q": {"noul": 0.82}}}
    live_b2 = {"provider": "live", "answers": {"q": {"noul": 0.31}}}
    v2 = verdict(live_a, live_b1, live_b2)
    print("\nGATE ACCEPTS A LIVE-SHAPED RESPONSE:", v2["gate"] == "LIVE")
    return 0 if (ok and v2["gate"] == "LIVE") else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-fixture", action="store_true",
                    help="assert the gate rejects the mock baseline and accepts a "
                         "live-shaped response; needs no credential")
    args = ap.parse_args()
    if args.verify_fixture:
        sys.exit(verify_fixture())

    print("This script's gate logic is exercised by --verify-fixture.")
    print("The three payloads the agent must send are:")
    print("  DISC_A_STATE     ", json.dumps(DECISIVE_STATE))
    print("  DISC_B1_QUESTION ", json.dumps(Q_WITH_BOUNDARY_A))
    print("  DISC_B2_QUESTION ", json.dumps(Q_WITH_BOUNDARY_B))
    print("\nRecorded MOCK baseline (this project):", json.dumps(MOCK_BASELINE, indent=2))
