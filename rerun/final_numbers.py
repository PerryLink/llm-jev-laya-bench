"""Final numbers for the report: the specific published-vs-re-run values quoted in the text."""
from __future__ import annotations

import json

print("=== P21 thinking-mode cost multiples ===")
for lbl, p in (("published", "rerun/baseline/P21-thinking-mode-cost.json"),
               ("re-run", "results/P21-thinking-mode-cost.json")):
    d = json.load(open(p, encoding="utf-8"))
    s = d["summary"]
    print(f"  {lbl}: cost_ratio_vs_non_thinking = "
          f"{json.dumps(s.get('cost_ratio_vs_non_thinking'), ensure_ascii=False)}")
    print(f"          verdict = {str(s.get('verdict'))[:200]}")

print()
print("=== P23 logprob vs verbal ===")
for lbl, p in (("published", "rerun/baseline/P23-llm-logprobs.json"),
               ("re-run", "results/P23-llm-logprobs.json")):
    s = json.load(open(p, encoding="utf-8"))["summary"]
    print(f"  {lbl}: verbal_acc={s.get('verbal_accuracy')} logit_acc={s.get('logit_accuracy')} "
          f"mean_abs_diff={s.get('mean_abs_diff_confidence')} "
          f"mean_verbal_conf={s.get('mean_verbal_confidence_on_chosen')}")
    print(f"          verdict = {str(s.get('verdict'))[:160]}")

print()
print("=== P24 ===")
b = json.load(open("rerun/baseline/P24-reduced-horizon.json", encoding="utf-8"))
n = json.load(open("results/P24-reduced-horizon.json", encoding="utf-8"))
print("  published verdict:", b["summary"]["verdict"])
print("  re-run    verdict:", n["summary"]["verdict"])

print()
print("=== P27d bit-for-bit check ===")
b = json.load(open("rerun/baseline/P27d-primitive-fields.json", encoding="utf-8"))
n = json.load(open("results/P27d-primitive-fields.json", encoding="utf-8"))
print("  never_returned_by_provider published:", b.get("never_returned_by_provider"))
print("  never_returned_by_provider re-run   :", n.get("never_returned_by_provider"))

print()
print("=== P27c cost-per-size, published vs re-run ===")
b = json.load(open("rerun/baseline/P27c-jev-latency-sweep.json", encoding="utf-8"))
n = json.load(open("results/P27c-jev-latency-sweep.json", encoding="utf-8"))
for rb, rn in zip(b["by_size"], n["by_size"]):
    print(f"  {rb['state_chars']:>6} chars / {rb['input_tokens_median']:>5} tok : "
          f"cost ${rb['cost_usd_mean']:.9f} -> ${rn['cost_usd_mean']:.9f}   "
          f"p50 {rb['latency_ms_wall']['p50']:>7} -> {rn['latency_ms_wall']['p50']:>7} ms")

print()
print("=== P26 control (rerun/) ===")
c = json.load(open("rerun/P26-control-low-window.json", encoding="utf-8"))
print("  state tokens:", c["state_tokens"], " inside window:", c["all_states_inside_window"])
print("  full arm laya:", c["full_arm_laya"])
print("  full arm llm :", c["full_arm_llm"])
print("  fisher p     :", c["fisher_exact_two_sided_low_vs_high_window"])
print("  withdrawn claim:", c["withdrawn_claim_in_paper"])
