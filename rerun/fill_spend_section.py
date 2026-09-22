"""Fill in the final spend table and add the P19 result note. Plain text replacement."""
from pathlib import Path

p = Path("results/RERUN-REPORT.md")
t = p.read_text(encoding="utf-8")

pairs = [
    ("| P19-calibration (n=1100) | 1100 | *filled in below* |\n"
     "| **subtotal, recorded by artifacts** | | **$0.026893758** + P19 |\n"
     "| P26 control arm — 20 calls, cost not recorded by P26's own helper | 20 | "
     "≈$0.000991 (estimated at P14's mean per-call cost) |\n"
     "| P23-llm-logprobs — **the artifact records no cost field at all** | ~120 | "
     "≈$0.0048 (estimated) |\n"
     "| **TOTAL** | | **see the closing line** |\n"
     "\n"
     "**Ceiling: $0.10. Total: see below. All calls to the local sidecar and the whole of "
     "Tier 1\nand Tier 2 cost $0.00.**",
     "| P19-calibration (n=1100) | 1100 | $0.044265150 |\n"
     "| **subtotal, recorded by the re-run's own artifacts** | **1,801** | "
     "**$0.071275200** |\n"
     "| P26 control arm — 20 calls; `p26`'s `ask_llm()` records no cost | 20 | "
     "≈$0.000991 *(estimated at P14's mean per-call cost)* |\n"
     "| P23-llm-logprobs — **the artifact records no cost field at all** | ~120 | "
     "≈$0.0048 *(estimated)* |\n"
     "| **TOTAL NEW SPEND** | | **≈ $0.0771** |\n"
     "| **CEILING** | | **$0.10** |\n"
     "| **REMAINING** | | **≈ $0.0229** |\n"
     "\n"
     "**Under the ceiling, with ≈23% headroom.** Every call to the local Laya sidecar, and "
     "the\nwhole of Tier 1 and Tier 2, cost **$0.00**; all spend is in Tier 3.\n"
     "\n"
     "Worth noting: the net *delta* against the published artifacts is **not** the re-run's "
     "spend.\nSeveral stochastic arms came back cheaper than their published runs "
     "(P14 `−$0.000555`,\nP24 `−$0.008461`, P22b-r1 `−$0.000037`), so a delta-based tracker "
     "under-reports by about\n$0.009. The figure above is the sum of what the re-run's own "
     "artifacts recorded."),
]

n = 0
for old, new in pairs:
    if old in t:
        t = t.replace(old, new, 1)
        n += 1
    else:
        print("MISS:", old[:70].replace("\n", "\\n"))
p.write_text(t, encoding="utf-8")
print(f"{n}/{len(pairs)} replacements applied")
