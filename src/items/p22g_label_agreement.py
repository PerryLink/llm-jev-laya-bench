"""P22g: provenance of the item-level label-agreement figures, and the confound inside them.

The paper reports item-level LLM label agreement of 86.8% / 86.8% / 89.7% between the three
temperature-pinned draws of the chain battery, and "only 58% when temperature was not
pinned". A prior audit claimed the 58% had no artifact behind it. This script settles it.

FINDING 1 -- the 58% IS artifact-backed. It is `P22-chain-audit` (the unpinned pilot) against
`P22b-fixed-r1`: 40/68 = 0.5882.

FINDING 2 -- but it is CONFOUNDED, and the confound was not previously noticed. The pilot was
generated before the M-20 truth fix, so its `simulate(ignore_superseded=True)` -- and hence
its `alt` value, and hence THE OPTION SET ITSELF -- differs on 7 of the 68 shared items. On
those items the two runs did not offer the same menu, so a label difference there is not a
sampling difference. The confounded items are

    CH-K8-011, CH-K8-012, CH-K8-023, CH-K16-001, CH-K16-004, CH-K16-007, CH-K16-018

which is DISJOINT from the 7 items where `alt` was never offered at all (see
`p22f_repair_denominator.py`) -- two separate 7-item defects that happen to have the same
size, and would be easy to conflate.

FINDING 3 -- excluding the confounded items sharpens the conclusion rather than weakening it.
The LLM's agreement moves 58.8/63.2/60.3 -> 60.7/63.9/62.3 percent, so the "unpinned sampling
destroys reproducibility" reading survives. But the LAYA arm moves 67/68 = 98.5% ->
**61/61 = 100.0%** in all three draws: every single disagreement with the pilot sits on an
item whose option set had changed. That is the sharpest evidence in the project that the
judge arm is a deterministic function of (state, options) -- it is not merely "reproducible
in practice", it is invariant to sampling whenever the question is held fixed.
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


import importlib.util
import json
from itertools import combinations
from pathlib import Path


RESULTS = ROOT / "results"

PILOT = "P22-chain-audit.json"          # temperature NOT pinned, 69 items, pre-M-20 simulate
DRAWS = ["P22b-fixed-r1.json", "P22b-fixed-r2.json", "P22b-fixed-r3.json"]


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "p22_chain_audit", ROOT / "src" / "items" / "p22_chain_audit.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rows_of(name: str) -> dict:
    doc = json.loads((RESULTS / name).read_text(encoding="utf-8"))
    return {r["item_id"]: r for r in doc["rows"]}


def agreement(a: dict, b: dict, arm: str, restrict: set | None = None):
    key = f"{arm}_label"
    shared = [i for i in a if i in b and a[i].get(key) is not None
              and b[i].get(key) is not None]
    if restrict is not None:
        shared = [i for i in shared if i in restrict]
    same = sum(1 for i in shared if a[i][key] == b[i][key])
    return same, len(shared), (round(same / len(shared), 4) if shared else None)


def main() -> None:
    mod = load_generator()
    pilot_items = {it["item_id"]: it
                   for it in mod.build_items(legacy_options=True, legacy_simulate=True)}
    fixed_items = {it["item_id"]: it for it in mod.build_items(legacy_options=True)}

    confounded = sorted(i for i in set(pilot_items) & set(fixed_items)
                        if pilot_items[i]["criteria"] != fixed_items[i]["criteria"])
    clean = set(pilot_items) & set(fixed_items) - set(confounded)

    docs = {n: rows_of(n) for n in [PILOT] + DRAWS}

    print("=== CONFOUND: items whose OPTION SET differs between pilot and fixed draws ===")
    print(f"  {len(confounded)} items: {', '.join(confounded)}")
    print(f"  (this set is DISJOINT from the 7 items where `alt` was never offered)")
    for i in confounded:
        print(f"    {i}: pilot {sorted(int(v) for v in pilot_items[i]['criteria'].values())}"
              f"  ->  fixed {sorted(int(v) for v in fixed_items[i]['criteria'].values())}")

    print("\n=== PAIRWISE ITEM-LEVEL LABEL AGREEMENT ===")
    print(f"{'pairing':40s} {'LLM all':>14s} {'LLM clean':>14s} "
          f"{'Laya all':>14s} {'Laya clean':>14s}")
    pairings = []
    for x, y in combinations([PILOT] + DRAWS, 2):
        e = {}
        for arm in ("llm", "laya"):
            sa, na, ra = agreement(docs[x], docs[y], arm)
            if x == PILOT:
                sc, nc, rc = agreement(docs[x], docs[y], arm, restrict=clean)
            else:                       # no confound between two post-fix draws
                sc, nc, rc = sa, na, ra
            e[arm] = {"all": [sa, na, ra], "unconfounded": [sc, nc, rc]}
        tag = "  <- unpinned vs pinned" if PILOT in (x, y) else ""
        print(f"{x[:-5]+' vs '+y[:-5]:40s} "
              f"{e['llm']['all'][0]:>3d}/{e['llm']['all'][1]:<3d}{e['llm']['all'][2]:>7.3f} "
              f"{e['llm']['unconfounded'][0]:>3d}/{e['llm']['unconfounded'][1]:<3d}"
              f"{e['llm']['unconfounded'][2]:>7.3f} "
              f"{e['laya']['all'][0]:>3d}/{e['laya']['all'][1]:<3d}{e['laya']['all'][2]:>7.3f} "
              f"{e['laya']['unconfounded'][0]:>3d}/{e['laya']['unconfounded'][1]:<3d}"
              f"{e['laya']['unconfounded'][2]:>7.3f}{tag}")
        pairings.append({"pair": [x, y], **e})

    print("\n=== THE PAPER'S THREE PINNED FIGURES (86.8 / 86.8 / 89.7) ===")
    for x, y in combinations(DRAWS, 2):
        s, n, r = agreement(docs[x], docs[y], "llm")
        print(f"  {x[:-5]} vs {y[:-5]}: LLM {s}/{n} = {r:.4f}")

    print("\n=== WHERE THE PILOT'S LAYA DISAGREEMENTS SIT ===")
    for y in DRAWS:
        s, n, r = agreement(docs[PILOT], docs[y], "laya")
        dis = [i for i in docs[PILOT] if i in docs[y]
               and docs[PILOT][i].get("laya_label") and docs[y][i].get("laya_label")
               and docs[PILOT][i]["laya_label"] != docs[y][i]["laya_label"]]
        print(f"  pilot vs {y[:-5]}: {s}/{n} = {r:.4f}; disagreements {dis} "
              f"(all in confounded set: {set(dis) <= set(confounded)})")

    out = RESULTS / "P22g-label-agreement-provenance.json"
    out.write_text(json.dumps({
        "_generated_by": "src/items/p22g_label_agreement.py",
        "_pure_derivation": True,
        "_why_no_instrument_record": (
            "This file makes NO measurement and no model call. It compares labels already "
            "recorded in artifacts that carry their own instrument records."),
        "pilot": PILOT,
        "draws": DRAWS,
        "confounded_items": confounded,
        "n_confounded": len(confounded),
        "confound_note": (
            "Items whose OPTION SET differs between the unpinned pilot and the pinned draws, "
            "because the pilot predates the M-20 truth fix and its `alt` value -- hence its "
            "option set -- changed on these items. Label differences here are not sampling "
            "differences. DISJOINT from the 7 items where `alt` was never offered."
        ),
        "pairings": pairings,
        "headline": {
            "llm_pinned_agreement": [0.8676, 0.8676, 0.8971],
            "llm_unpinned_vs_pinned_all": [0.5882, 0.6324, 0.6029],
            "llm_unpinned_vs_pinned_unconfounded": [0.6066, 0.6393, 0.6230],
            "laya_unpinned_vs_pinned_all": [0.9853, 0.9853, 0.9853],
            "laya_unpinned_vs_pinned_unconfounded": [1.0, 1.0, 1.0],
        },
        "_note": ("The 58% figure IS artifact-backed (pilot vs r1 = 40/68 = 0.5882). It is "
                  "reported to three significant figures as 58.8%. Excluding the confounded "
                  "items the LLM figure is 60.7-63.9%, and the Laya figure is 100% (61/61) "
                  "in all three draws."),
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwritten: {out}")


if __name__ == "__main__":
    main()
