"""CHAIN-AUDIT: multi-hop chained verification, built to break the LLM ceiling.

WHY THIS BATTERY EXISTS
-----------------------
The complementarity result (P14, P15) is currently unusable as a claim, because on every
battery built so far the LLM either hit 1.00 (authority location, 48/48; calibration
1100/1100) or scored 0.75 with the difference dominated by task difficulty rather than by
error structure. You cannot measure whether two judges fail in DIFFERENT places when one
of them does not fail. The ceiling has to be broken before the architecture claim can be
settled either way.

Swapping items does not help: every existing item is "template matching plus single-hop
verification" -- the answer is stated explicitly, the reasoning depth is one, and the
distractors differ by orders of magnitude so they need no elimination. That is exactly
the shape the LLM is built for. The battery has to differ in STRUCTURE.

THE STRUCTURE
-------------
An audit trail of K operation lines, each of the form `value := value <op> <d>`, with a
seed value on the first line, plus a subset of lines marked `SUPERSEDED` which must NOT
be applied. The question asks for the value after the last non-superseded step.

    truth = simulate(steps, ignore_superseded=False)   # derivable from the rendered state

Three properties make this hard for a model in a way template matching is not:
  1. MULTI-HOP. A value must be carried through K steps; one slip is terminal.
  2. AN ABSENCE TO NOTICE. `SUPERSEDED` lines must be SKIPPED. This is the same
     "notice what is absent / does not apply" axis on which the judge collapsed in
     P19 (no_support) and P3 (silent truncation), so the battery tests the paper's
     central hypothesis in a task where the LLM might also fail.
  3. NUMERIC PRECISION. Doubling amplifies an error; halving can produce fractions.

DIFFICULTY IS A CONTROLLED KNOB: K in {2,4,8,16} crossed with the superseded-line rate,
so a cost/quality curve can be plotted against depth rather than asserted.

CERTIFICATE (reusing the P5 mechanism)
--------------------------------------
For every item the generator asserts:
    simulate(seed, steps)                     != simulate(seed, steps, ignore_superseded)
so the `SUPERSEDED` marks are LOAD-BEARING rather than decorative. An item whose answer
is the same either way is rejected -- that is the `no_support` lesson applied at build
time. It also asserts the value never goes non-positive, so no item turns into a
fraction-formatting puzzle.

CHEAP: generation is pure Python, so the only spend is model calls. 4 chain lengths x
24 items = 96 items, each answered by the LLM (non-thinking) and by Laya.
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
import random
import statistics
import sys
from pathlib import Path


sys.path.insert(0, str(ROOT / "src" / "instrument"))
from deepseek_client import chat, parse_label, parse_prob, prompt_forced_choice  # noqa: E402
from laya_client import LayaClient, instrument_record  # noqa: E402

RESULTS = ROOT / "results"

OPS = ["add", "sub", "mul", "div"]
KS = [2, 4, 8, 16]
SUPERSEDED_RATE = 0.25
N_PER_K = 24


def apply_op(v: int, op: str, d: int) -> int:
    if op == "add":
        return v + d
    if op == "sub":
        return v - d
    if op == "mul":
        return v * 2
    return v // 2          # integer division; generator guarantees divisibility


def make_chain(rng: random.Random, k: int) -> tuple[list[dict], int]:
    seed = rng.choice([120, 240, 480, 960, 1920])
    steps: list[dict] = []
    v = seed
    for i in range(k):
        op = rng.choice(OPS)
        d = rng.choice([6, 12, 24, 48])
        sup = rng.random() < SUPERSEDED_RATE
        # choose d so subtraction stays positive and division is exact
        if op == "sub":
            d = min(d, max(1, v // 4))
        parity_fix = False
        if op == "div":
            while v % 2 != 0:
                v += 1
                parity_fix = True
                if steps:
                    steps[-1]["result"] += 1
        nxt = apply_op(v, op, d)
        if nxt <= 0:
            op, d, nxt = "add", 48, v + 48
            parity_fix = False
        # AUDIT FIX (M-20): the parity adjustment is now RECORDED, so `simulate()` can
        # reproduce it. Previously it was invisible to simulate(), so for 11 of 69 items
        # the scored truth could not be derived from the rendered state at all (and the
        # "faithful reading" was not even offered among the options).
        steps.append({"i": i + 1, "op": op, "d": d, "superseded": sup,
                      "parity_fix": parity_fix, "before": v, "result": nxt})
        if not sup:
            v = nxt
        else:
            steps[-1]["result"] = v      # a skipped step does not change the value
    return steps, v


def simulate(steps: list[dict], ignore_superseded: bool) -> int:
    """Authoritative truth. `ignore_superseded=True` treats every line as applied.

    AUDIT FIX (M-20): two things were wrong before.
      1. The generator's divisibility adjustment was invisible here; it is now recorded
         per step and replayed.
      2. The adjustment is applied BEFORE the superseded check, because `make_chain`
         mutates its live value while *evaluating* a step even when that step is later
         discarded (`if steps: steps[-1]["result"] += 1` ... then `result = v`). Skipping
         a superseded div step therefore also skipped an adjustment that had already
         changed the generator's state. That ordering was the residual divergence on
         4 of 69 items.
    """
    v = steps[0]["before"]
    for s in steps:
        if s.get("parity_fix") and v % 2 != 0:
            v += 1                       # divisibility adjustment, made before the op
        if s["superseded"] and not ignore_superseded:
            continue
        v = apply_op(v, s["op"], s["d"])
    return v


def render(steps: list[dict], seed: int) -> str:
    lines = [f"Audit trail. Start value: {seed}."]
    for s in steps:
        tag = " [SUPERSEDED - DO NOT APPLY]" if s["superseded"] else ""
        sym = {"add": "+", "sub": "-", "mul": "x2", "div": "/2"}[s["op"]]
        arg = "" if s["op"] in ("mul", "div") else f" {s['d']}"
        lines.append(f"step {s['i']}: value = value {sym}{arg}{tag}")
    lines.append("Report the value after the last step that is not superseded.")
    return "\n".join(lines)


def choose_options(rng: random.Random, truth: int, alt: int,
                   legacy: bool = False) -> tuple[list[int], bool]:
    """Return `(options, alt_in_options)` -- four options, shuffled.

    AUDIT FIX (round 5, the load-bearing-distractor defect). `alt` is the value a model
    reaches by IGNORING the SUPERSEDED marks: it is the ONE error this battery exists to
    measure. It was being dropped from the option set on 7 of 68 items, by two mechanisms:

      A. `alt <= 0` was removed by the `v > 0` filter (2 items: CH-K16-000, CH-K16-008).
      B. `alt` is the LARGEST candidate and `sorted(...)[:4]` keeps the four SMALLEST, so
         it was truncated (5 items). The bitter detail: `truth * 2` is also a candidate and
         is usually nearly equal to `alt`, so the item kept a *nearby doubling* decoy while
         discarding the *exact* ignore-superseded answer.

    A model that could not express the error was still counted as not making it, so the
    rate was attenuated by construction (ceiling 61/68 = 0.897, not 1.0). The distractor is
    now inserted FIRST and is never truncated; decoys fill the remaining slots. Items where
    `alt <= 0` cannot offer it plausibly, so they are FLAGGED (`alt_in_options=False`) and
    excluded from the rate's denominator rather than silently deflating it.

    `legacy=True` replays the old construction. It exists so the published draws -- which
    were generated with it -- stay exactly reproducible for audit; it must not be used for
    new measurements.
    """
    if legacy:
        opts = {truth, alt, truth + 6, truth - 12, truth * 2}
        opts = [v for v in sorted(opts) if v > 0][:4]
        if truth not in opts:
            opts = [truth, alt, truth + 6, truth - 12]
        rng.shuffle(opts)
        return opts, str(alt) in {str(v) for v in opts}

    alt_in = alt > 0 and alt != truth
    # `truth` and `alt` first: neither may be displaced by a decoy.
    ordered = [truth] + ([alt] if alt_in else [])
    decoys = [truth + 6, truth - 12, truth * 2, truth + 24, truth - 6, truth + 12]
    ordered += sorted((v for v in decoys if v > 0),
                      key=lambda v: (abs(v - truth), v))
    seen: set[int] = set()
    opts = []
    for v in ordered:
        if v not in seen:
            seen.add(v)
            opts.append(v)
    opts = opts[:4]
    assert truth in opts, "truth displaced from its own option set"
    rng.shuffle(opts)
    return opts, alt_in


def simulate_prefix_fix(steps: list[dict], ignore_superseded: bool) -> int:
    """Faithful replay of the PRE-M-20 `simulate()`, for reproducing the old pilot only."""
    v = steps[0]["before"]
    for s in steps:
        if s["superseded"] and not ignore_superseded:
            continue
        v = apply_op(v, s["op"], s["d"])
    return v


def build_items(legacy_options: bool = False,
                legacy_simulate: bool = False) -> list[dict]:
    """Build the battery.

    `legacy_options` / `legacy_simulate` reproduce, respectively, the pre-round-5 option
    construction and the pre-M-20 truth function. Both are OFF by default: they exist only
    so the published artifacts (generated under those behaviours) remain exactly
    reconstructible. `src/items/p22f_repair_denominator.py` uses them to backfill the
    option-availability flag into the published draws without re-measuring anything.
    """
    sim = simulate_prefix_fix if legacy_simulate else simulate
    items: list[dict] = []
    for k in KS:
        for j in range(N_PER_K):
            rng = random.Random(f"chain:{k}:{j}")
            steps, truth = make_chain(rng, k)
            # CERTIFICATE (AUDIT FIX, M-20): the scored truth MUST be derivable from the
            # rendered state. This assertion is the one the docstring always claimed and
            # the code never performed; it failed on 11/69 items before the fix.
            if not legacy_simulate:
                derivable = simulate(steps, ignore_superseded=False)
                if derivable != truth:
                    raise AssertionError(
                        f"{k}:{j} scored truth {truth} is not derivable from the state "
                        f"(faithful reading = {derivable})")
            alt = sim(steps, ignore_superseded=True)
            if alt == truth:
                continue                     # superseded marks not load-bearing
            seed = steps[0]["before"]
            opts, alt_in_options = choose_options(rng, truth, alt, legacy=legacy_options)
            crit = {f"o{i+1:02d}": str(v) for i, v in enumerate(opts)}
            truth_key = next(kk for kk, vv in crit.items() if vv == str(truth))
            items.append({
                "item_id": f"CH-K{k}-{j:03d}", "k": k, "seed": seed,
                "state": render(steps, seed),
                "criteria": crit, "truth": truth, "truth_key": truth_key,
                "alt_ignore_superseded": alt,
                "alt_in_options": alt_in_options,
                "n_superseded": sum(1 for s in steps if s["superseded"]),
            })
    return items


def run(temperature: float | None = 0.0, replication: str = "") -> dict:
    """`temperature` is now passed EXPLICITLY.

    AUDIT FIX: the first run passed no temperature, and the client only sets it when
    given, so the recorded numbers were a single draw of the API's default sampler.
    Two independent replications moved the LLM headline 0.5942 -> 0.5217, kappa
    0.0062 -> 0.0322/0.2030 and delta_catch -0.0070 -> -0.0328/-0.2071. Pinning
    temperature makes the arm reproducible, and `replication` labels the draw so
    agreement between draws can be measured rather than assumed.
    """
    client = LayaClient()
    client.ensure_up()
    items = build_items()
    print(f"built {len(items)} items across K={KS} (temperature={temperature})")

    rows: list[dict] = []
    for it in items:
        q = ("What is the value after the last step that is not superseded?")
        rec = {"item_id": it["item_id"], "k": it["k"],
               "n_superseded": it["n_superseded"], "truth": it["truth"],
               "alt_in_options": it["alt_in_options"],
               "state_tokens_laya": client.count_tokens(it["state"])}
        # ---- LLM, non-thinking, forced choice
        try:
            r = chat(prompt_forced_choice(it["state"], q, it["criteria"]),
                     effort="none", json_mode=True, max_tokens=256,
                     **({"temperature": temperature} if temperature is not None else {}))
            lab = parse_label(r, it["criteria"])
            rec["llm_label"] = lab
            rec["llm_value"] = it["criteria"].get(lab) if lab else None
            rec["llm_correct"] = (lab == it["truth_key"])
            rec["llm_picked_ignore_superseded"] = (
                it["criteria"].get(lab) == str(it["alt_ignore_superseded"]))
            rec["llm_cost"] = r.cost.get("off_peak_usd")
            rec["llm_latency_ms"] = round(r.latency_ms, 1)
        except Exception as exc:
            rec["llm_error"] = str(exc)[:160]
        # ---- Laya, noul? no: same forced choice so the comparison is like-for-like
        try:
            lr = client.ask(it["state"], {"q": {"type": "choice",
                                                "instructions": q,
                                                "criteria": it["criteria"]}})
            a = lr["answers"]["q"]
            rec["laya_label"] = a.get("choice")
            rec["laya_value"] = it["criteria"].get(a.get("choice"))
            rec["laya_correct"] = a.get("choice") == it["truth_key"]
            rec["laya_picked_ignore_superseded"] = (
                it["criteria"].get(a.get("choice")) == str(it["alt_ignore_superseded"]))
        except Exception as exc:
            rec["laya_error"] = str(exc)[:160]
        rows.append(rec)
        print(f"K={it['k']:<3} sup={it['n_superseded']} truth={it['truth']:<6} "
              f"llm={rec.get('llm_correct')} laya={rec.get('laya_correct')}")

    def by(pred) -> dict:
        d: dict = {}
        for k in KS:
            sub = [r for r in rows if r["k"] == k and pred(r) is not None]
            if sub:
                d[k] = {"n": len(sub),
                        "accuracy": round(sum(1 for r in sub if pred(r)) / len(sub), 4)}
        return d

    llm_by_k = by(lambda r: r.get("llm_correct"))
    laya_by_k = by(lambda r: r.get("laya_correct"))

    # paired complementarity over all items
    pairs = [(r.get("llm_correct"), r.get("laya_correct")) for r in rows
             if r.get("llm_correct") is not None and r.get("laya_correct") is not None]
    both = sum(1 for a, b in pairs if a and b)
    typed_only = sum(1 for a, b in pairs if b and not a)
    llm_only = sum(1 for a, b in pairs if a and not b)
    neither = len(pairs) - both - typed_only - llm_only
    llm_wrong = [b for a, b in pairs if not a]
    llm_right = [b for a, b in pairs if a]
    p_wrong = (sum(1 for b in llm_wrong if b) / len(llm_wrong)) if llm_wrong else None
    p_right = (sum(1 for b in llm_right if b) / len(llm_right)) if llm_right else None

    llm_acc = (sum(1 for a, _ in pairs if a) / len(pairs)) if pairs else None
    def ignore_superseded_rate(arm: str) -> dict:
        """Rate on the ELIGIBLE denominator -- items where `alt` was actually offered.

        AUDIT FIX (round 5): the former denominator was every row carrying a judgement,
        including the 7 items on which the ignore-SUPERSEDED answer was not among the
        options and the error is therefore UNEXPRESSIBLE. Dividing by those attenuates the
        rate by construction. Both denominators are reported so the attenuation stays
        visible rather than being corrected away silently.
        """
        answered = [r for r in rows if r.get(f"{arm}_correct") is not None]
        eligible = [r for r in answered if r.get("alt_in_options")]
        hits = sum(1 for r in eligible if r.get(f"{arm}_picked_ignore_superseded"))
        return {
            "hits": hits,
            "n_eligible": len(eligible),
            "rate": round(hits / len(eligible), 4) if eligible else None,
            "n_all_answered": len(answered),
            "rate_all_answered": (round(hits / len(answered), 4) if answered else None),
        }

    llm_ig = ignore_superseded_rate("llm")
    laya_ig = ignore_superseded_rate("laya")
    n_alt_offered = sum(1 for r in rows if r["alt_in_options"])

    summary = {
        "n_items": len(rows),
        "ks": KS,
        "llm_accuracy_by_k": llm_by_k,
        "laya_accuracy_by_k": laya_by_k,
        "llm_overall_accuracy": round(llm_acc, 4) if llm_acc is not None else None,
        "llm_ceiling_broken": (llm_acc is not None and llm_acc < 0.95),
        "llm_picked_ignore_superseded_rate": llm_ig["rate"],
        "laya_picked_ignore_superseded_rate": laya_ig["rate"],
        "llm_picked_ignore_superseded": llm_ig,
        "laya_picked_ignore_superseded": laya_ig,
        "alt_option_availability": {
            "n_items": len(rows),
            "n_alt_offered": n_alt_offered,
            "n_alt_not_offered": len(rows) - n_alt_offered,
            "rate_ceiling": round(n_alt_offered / len(rows), 4) if rows else None,
            "not_offered_item_ids": sorted(r["item_id"] for r in rows
                                           if not r["alt_in_options"]),
            "_note": ("`alt` is the value reached by ignoring the SUPERSEDED marks. It is "
                      "offered whenever it is positive; on the remaining items the error "
                      "is unexpressible and those items are excluded from the rate "
                      "denominator."),
        },
        "confusion": {"both_correct": both, "typed_only_correct": typed_only,
                      "llm_only_correct": llm_only, "neither_correct": neither},
        "P_typed_correct_given_llm_wrong": p_wrong,
        "P_typed_correct_given_llm_right": p_right,
        "delta_catch": (None if (p_wrong is None or p_right is None) else p_wrong - p_right),
        "instrument": instrument_record(),
        "llm_sampling": {"temperature": temperature, "replication": replication},
        "caveat": (f"{N_PER_K} items per chain length, single sample per judge. "
                   f"Generation is programmatic so ground truth is exact; the sample "
                   f"sizes support a depth trend and a paired contrast, not fine "
                   f"per-cell estimates."),
        "verdict": None,
    }
    if not summary["llm_ceiling_broken"]:
        summary["verdict"] = (
            f"LLM CEILING INTACT ({summary['llm_overall_accuracy']}): it still answers "
            f"these correctly, so complementarity remains unmeasurable even on multi-hop "
            f"chained verification. Per the pre-declared reading, the architecture claim "
            f"is abandoned rather than left open.")
    elif summary["delta_catch"] is not None and summary["delta_catch"] > 0.10:
        summary["verdict"] = (
            f"CEILING BROKEN AND COMPLEMENTARITY FOUND: LLM {summary['llm_overall_accuracy']} "
            f"with delta_catch={summary['delta_catch']:+.3f}, so the typed judge IS more "
            f"reliable where the LLM fails -- the architecture claim is revived")
    else:
        summary["verdict"] = (
            f"CEILING BROKEN (LLM {summary['llm_overall_accuracy']}) BUT NO "
            f"COMPLEMENTARITY: delta_catch={summary['delta_catch']}, so even with the LLM "
            f"failing, the typed judge does not cover its errors")
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    # usage: p22_chain_audit.py [outname] [temperature] [replication_tag]
    import sys as _sys
    outname = _sys.argv[1] if len(_sys.argv) > 1 else "P22-chain-audit.json"
    temp = float(_sys.argv[2]) if len(_sys.argv) > 2 else 0.0
    tag = _sys.argv[3] if len(_sys.argv) > 3 else ""
    out = run(temperature=temp, replication=tag)
    p = RESULTS / outname

    # ---- HISTORICAL-RECORD GUARD -------------------------------------------------------
    # This generator now builds the FIXED 68-item battery, but `P22-chain-audit.json` is the
    # n=69 PILOT -- the recorded draw whose item-level agreement with the pinned draws is a
    # published reproducibility claim, and whose `_repair` note is the origin of the 61-item
    # denominator the paper uses. Running this file used to overwrite it with a different
    # battery; `results/RERUN-P22-PILOT-OVERWRITTEN.md` records that it happened once. A
    # generator may not silently destroy the record it is named after.
    if p.exists():
        try:
            existing_n = json.loads(p.read_text(encoding="utf-8"))["summary"]["n_items"]
        except Exception:                                        # noqa: BLE001
            existing_n = None
        new_n = out["summary"]["n_items"]
        if existing_n is not None and existing_n != new_n and not _sys.argv[4:]:
            raise SystemExit(
                f"REFUSING to overwrite {p.name}: it holds n={existing_n} and this run would "
                f"write n={new_n}. That artifact is a historical record (see ERRATA and "
                f"results/RERUN-P22-PILOT-OVERWRITTEN.md). Pass a 4th argument (any value) to "
                f"force, or write to a different outname."
            )
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    s = out["summary"]
    print("\n=== ACCURACY BY CHAIN LENGTH ===")
    for k in KS:
        a = s["llm_accuracy_by_k"].get(k, {})
        b = s["laya_accuracy_by_k"].get(k, {})
        print(f"  K={k:<3} LLM={a.get('accuracy')} (n={a.get('n')})   "
              f"Laya={b.get('accuracy')} (n={b.get('n')})")
    print(f"\n  LLM overall: {s['llm_overall_accuracy']}  ceiling broken: {s['llm_ceiling_broken']}")
    av = s["alt_option_availability"]
    print(f"  ignore-SUPERSEDED answer offered on {av['n_alt_offered']}/{av['n_items']} items "
          f"(rate ceiling {av['rate_ceiling']})")
    for arm in ("llm", "laya"):
        d = s[f"{arm}_picked_ignore_superseded"]
        print(f"  {arm.upper():4s} picked the ignore-SUPERSEDED answer: {d['rate']} "
              f"({d['hits']}/{d['n_eligible']} eligible; {d['rate_all_answered']} on the "
              f"old {d['n_all_answered']}-row denominator)")
    print(f"  confusion: {s['confusion']}")
    print(f"  delta_catch: {s['delta_catch']}")
    print(f"\n=== VERDICT ===\n{s['verdict']}")
    print(f"written: {p}")
