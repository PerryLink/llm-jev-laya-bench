"""TOTAL NEW SPEND of the re-measurement.

The published spend is SUNK: the ledger that matters for the ceiling is what this re-run
itself spent, not the delta against the old artifact (which is negative for several arms,
because a stochastic arm can come back cheaper).

Every figure below is the sum of per-call costs recorded by the re-run's own artifact.
"""
from __future__ import annotations

import json
from pathlib import Path

KEYS = ("off_peak_usd", "cost_usd", "llm_cost_usd", "llm_cost", "costUsd",
        "cost_off", "cost_usd_mean", "mean_cost_usd", "cost")


def total(node) -> tuple[float, int]:
    s, n = 0.0, 0
    if isinstance(node, dict):
        for k, v in node.items():
            if k in KEYS and isinstance(v, (int, float)):
                s += float(v)
                n += 1
            else:
                a, b = total(v)
                s += a
                n += b
    elif isinstance(node, list):
        for v in node:
            a, b = total(v)
            s += a
            n += b
    return s, n


# artifact -> (label, source path)
ITEMS = [
    ("P27-jev-live (Jev)", "results/P27-jev-live.json", "_spend_usd"),
    ("P27c-jev-latency-sweep (Jev)", "results/P27c-jev-latency-sweep.json", "_spend_usd"),
    ("P27d-primitive-fields (Jev)", "results/P27d-primitive-fields.json", "_spend_usd"),
    ("P27b-plugin-crossval (Jev, derived - no calls)", "results/P27b-plugin-crossval.json", None),
    ("P14-llm-arm-full", "results/P14-llm-arm-full.json", None),
    ("P21-thinking-mode-cost", "results/P21-thinking-mode-cost.json", None),
    ("P23-llm-logprobs (NO cost recorded)", "results/P23-llm-logprobs.json", None),
    ("P15-complementarity", "results/P15-complementarity-strong-regime.json", None),
    ("P15b-rep-r1", "results/P15b-rep-r1.json", None),
    ("P15b-rep-r2", "results/P15b-rep-r2.json", None),
    ("P15b-rep-r3", "results/P15b-rep-r3.json", None),
    ("P22b-fixed-r1", "results/P22b-fixed-r1.json", None),
    ("P22b-fixed-r2", "results/P22b-fixed-r2.json", None),
    ("P22b-fixed-r3", "results/P22b-fixed-r3.json", None),
    ("P22 PILOT re-measure (rerun/)", "rerun/P22-chain-audit-PILOT-rerun.json", None),
    ("P24-reduced-horizon", "results/P24-reduced-horizon.json", None),
    ("P19-calibration (n=1100)", "results/P19-calibration.json", None),
]

print(f"{'arm':50s} {'calls':>6} {'spend_usd':>13}")
print("-" * 74)
run = 0.0
for label, path, spend_key in ITEMS:
    p = Path(path)
    if not p.exists():
        print(f"{label:50s} {'-':>6} {'(missing)':>13}")
        continue
    d = json.loads(p.read_text(encoding="utf-8"))
    if spend_key:
        s, n = float(d.get(spend_key) or 0.0), None
        # count calls from the persisted rows, but report the artifact's own ledger
        _s2, n2 = total(d)
        print(f"{label:50s} {str(n2):>6} {s:>13.9f}   <- artifact's own {spend_key}")
        run += s
        continue
    s, n = total(d)
    print(f"{label:50s} {n:>6} {s:>13.9f}")
    run += s

print("-" * 74)
print(f"{'RECORDED NEW SPEND':50s} {'':>6} {run:>13.9f}")

# P26 control: 20 DeepSeek calls, ask_llm() does not record cost -> estimate from the
# cheapest comparable arm's mean per-call cost.
p21 = json.loads(Path("results/P21-thinking-mode-cost.json").read_text(encoding="utf-8"))
_s, n21 = total(p21)
p14 = json.loads(Path("results/P14-llm-arm-full.json").read_text(encoding="utf-8"))
_s14, n14 = total(p14)
mean14 = _s14 / n14
p26_calls = 20
est = mean14 * p26_calls
print(f"{'P26 control arm (20 calls, unrecorded)':50s} {p26_calls:>6} {est:>13.9f}   "
      f"<- ESTIMATE at P14 mean ${mean14:.8f}/call")
print(f"{'P23 (calls not cost-recorded)':50s} {'~120':>6} {'~0.0048':>13}   <- ESTIMATE")
print()
print(f"{'TOTAL (recorded + estimates)':50s} {'':>6} {'~%.4f' % (run + est + 0.0048):>13}")
print(f"{'CEILING':50s} {'':>6} {0.10:>13.2f}")
print(f"{'REMAINING':50s} {'':>6} {'~%.4f' % (0.10 - run - est - 0.0048):>13}")
