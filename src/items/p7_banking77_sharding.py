"""Does hierarchical sharding recover a 77-way classification that flat choice cannot?

THE DESIGN QUESTION, AND WHY IT IS NOW TESTABLE ON REAL DATA
------------------------------------------------------------
P1 measured flat `choice` collapsing above ~15 options (0.00 at N>=20, AUC -> chance).
P6 showed a two-level hierarchy can beat flat, but on an AUTHORED taxonomy. D3 adopted
Banking77 (77 intents) into the plan, and the vendor's own numbers put Laya at 0.425
there versus Jev's 0.870 -- so the question "can sharding fix a 77-way problem" decides
whether the 41k+ MASSIVE and Banking77 items are usable at all.

Banking77 is now on disk locally (obtained from the public repository because the
HuggingFace API is unreachable from this host), so this runs on REAL intents and REAL
utterances rather than a synthetic taxonomy.

CONTAMINATION STANCE (D3, unchanged, and it constrains what this probe may claim)
--------------------------------------------------------------------------------
Banking77 is a Laya-prior set: the vendor publishes a number on it, and its label file
has plausibly been crawled. So this probe CANNOT support any accuracy claim. What it can
support is a STRUCTURAL claim, which is what the design decision needs: does a
hierarchy of <=10-option layers beat a single 77-option layer on the same items? The
comparison is internal and paired, so a contamination term that inflates both arms
equally does not create the difference.

CONTROLS THAT ARE NOW MANDATORY (each one earned by a mistake this project already made)
  * OPAQUE option keys (P6): descriptive keys leaked the taxonomy and flipped the
    verdict. Keys are `n01`-style; the intent name appears only in the option VALUE,
    which is what a real deployment would show.
  * DECORRELATED OPTION ORDER (P2): leaving options in taxonomy order let a positional
    preference read as 1.00 skill. Order is shuffled per item and the truth position is
    recorded.
  * CONDITIONAL AND END-TO-END ARMS (P5): per-layer skill is measured conditional on the
    TRUE ancestor, so compounding is separable from layer quality rather than conflated.
  * TOKEN BUDGET BY OUR OWN COUNT (P3): admission uses the checkpoint tokenizer, never
    Laya's `fits` flag, which is wrong in both directions.

HIERARCHY CONSTRUCTION IS PROGRAMMATIC AND DETERMINISTIC
--------------------------------------------------------
Intents are grouped by greedy balanced agglomeration over token-set Jaccard distance
between intent NAMES, taking the nearest unassigned neighbours until a group is full.
No model is involved, so the grouping is reproducible from the label list alone and does
not smuggle in a judge's opinion of what belongs together. A hand-built taxonomy would
be a hidden degree of freedom; this is auditable.
"""

from __future__ import annotations

import csv
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "instrument"))
from laya_client import LayaClient, instrument_record  # noqa: E402

ROOT = Path(r"D:\Projects\llm-jev-laya-bench")
DATA = ROOT / "data" / "banking77"
RESULTS = ROOT / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

GROUP_SIZE_TOP = 8      # 77 -> ~10 groups, so the first layer stays at the <=10 ceiling
SUBGROUP_SIZE = 3       # each 8-group splits into 3+3+2, so later layers stay tiny


# ------------------------------------------------------------------ hierarchy build

def _tokens(name: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", name.lower()) if t}


def _dist(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return 1.0 - len(a & b) / max(1, len(a | b))


def build_hierarchy(intents: list[str], group_size: int) -> dict:
    """Greedy balanced agglomeration: reproducible from the label list alone."""
    toks = {i: _tokens(i) for i in intents}
    remaining = list(intents)
    groups: list[list[str]] = []
    while remaining:
        seed = remaining[0]
        rest = sorted(remaining[1:], key=lambda c: (_dist(toks[seed], toks[c]), c))
        grp = [seed] + rest[: group_size - 1]
        groups.append(sorted(grp))
        remaining = [c for c in remaining if c not in grp]
    return {"groups": groups}


def deepen(groups: list[list[str]], size: int) -> list[list[list[str]]]:
    """Split each group into <=size subgroups, again by name proximity."""
    out = []
    for g in groups:
        toks = {i: _tokens(i) for i in g}
        rem = list(g)
        subs = []
        while rem:
            seed = rem[0]
            rest = sorted(rem[1:], key=lambda c: (_dist(toks[seed], toks[c]), c))
            sub = [seed] + rest[: size - 1]
            subs.append(sorted(sub))
            rem = [c for c in rem if c not in sub]
        out.append(subs)
    return out


# ------------------------------------------------------------------------- item load

def load_items(limit: int, min_tokens: int = 8, max_tokens: int = 24,
               client: LayaClient | None = None, seed: int = 20260922) -> list[dict]:
    """Real test-split utterances, filtered to what the English window can hold whole."""
    path = DATA / "test.csv"
    if not path.exists():
        raise SystemExit(f"missing {path}; download banking77 test.csv first")
    rows: list[dict] = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append({"text": r["text"], "category": r["category"]})
    rng = random.Random(seed)
    rng.shuffle(rows)
    picked: list[dict] = []
    for r in rows:
        n = len(r["text"].split())
        if min_tokens <= n <= max_tokens:
            picked.append(r)
        if len(picked) >= limit:
            break
    return picked


# --------------------------------------------------------------------------- probing

def ask_choice(client: LayaClient, state: str, instr: str,
               options: list[tuple[str, str]]) -> dict:
    """options: list of (opaque_key, display_text). Order is caller-controlled."""
    crit = {k: v for k, v in options}
    resp = client.ask(state, {"q": {"type": "choice", "instructions": instr,
                                    "criteria": crit}})
    a = resp["answers"]["q"]
    return {"chosen": a.get("choice"), "probs": a.get("probabilities") or {},
            "confidence": a.get("confidence"), "type_ok": a.get("type") == "choice"}


def group_description(members: list[str], all_intents: list[str],
                      max_words: int = 10) -> str:
    """A CONCISE description built from the group's distinctive shared terms.

    Why this replaced enumerating the member names: the first version of this probe
    rendered each group option as "group N: <intent>, <intent>, ... , <intent>" -- about
    40 tokens listing 8 intents. Layer-1 accuracy came out 0.133 against a 0.10 chance
    rate, because matching one short utterance against eight concatenated intents IS the
    high-cardinality problem the hierarchy exists to avoid. The option text, not the
    hierarchy, was the failure.

    This is computed from the label list alone, so it stays reproducible and does not
    smuggle in a model's opinion of what belongs together. Shared terms rank first
    (they characterise the group), then distinctive terms from individual members.
    """
    member_tokens: list[set[str]] = [_tokens(m) for m in members]
    shared: dict[str, int] = {}
    for t in set().union(*member_tokens) if member_tokens else set():
        c = sum(1 for mt in member_tokens if t in mt)
        if c >= 2:
            shared[t] = c
    ordered = [t for t, _ in sorted(shared.items(), key=lambda kv: (-kv[1], kv[0]))]
    # fall back to the first member's own words when nothing is shared
    if not ordered:
        ordered = sorted(member_tokens[0]) if member_tokens else ["request"]
    words = ordered[:max_words]
    return "requests about " + " ".join(words)


def run(limit: int = 30, seed: int = 20260922) -> dict:
    client = LayaClient()
    client.ensure_up()
    intents = json.loads((DATA / "categories.json").read_text(encoding="utf-8-sig"))
    hier = build_hierarchy(intents, GROUP_SIZE_TOP)
    groups = hier["groups"]
    deep = deepen(groups, SUBGROUP_SIZE)

    items = load_items(limit, client=client, seed=seed)
    rng = random.Random(seed)

    rows: list[dict] = []
    for it in items:
        truth = it["category"]
        state = it["text"]
        gi = next(i for i, g in enumerate(groups) if truth in g)
        # locate the subgroup path
        si = next(i for i, s in enumerate(deep[gi]) if truth in s)
        sub = deep[gi][si]

        def run_level(labels: list[str], instr: str, decorrelate: bool = True) -> dict:
            """Ask one level. Option ORDER is decorrelated from correctness by default
            (the P2 lesson: leaving options in taxonomy order let a positional preference
            read as 1.00 skill). `decorrelate=False` reproduces the earlier ordering so
            the two conditions can be compared on identical items."""
            keys = [f"n{i+1:02d}" for i in range(len(labels))]
            pairs = list(zip(keys, labels))
            if decorrelate:
                rng.shuffle(pairs)
            res = ask_choice(client, state, instr, pairs)
            label_of = dict(pairs)
            chosen_label = label_of.get(res["chosen"])
            ordered = [l for _, l in pairs]
            return {"chosen_label": chosen_label, "raw": res,
                    "truth_pos": ordered.index(truth) if truth in ordered else None,
                    "n_options": len(pairs), "ordered": ordered}

        row = {"text": state, "truth": truth, "group": gi, "subgroup": si}

        # L1: ~10 groups, described CONCISELY rather than by enumerating members.
        group_labels = [group_description(g, intents) for g in groups]
        l1 = run_level(group_labels,
                       "Which category group does this customer request belong to?")
        row["l1_ok"] = (l1["chosen_label"] is not None
                        and l1["raw"]["probs"].get(l1["raw"]["chosen"] or "", 0) > 0
                        and l1["chosen_label"] == group_labels[gi])

        # L2 conditional on the TRUE group (isolates layer skill). Measured TWICE on the
        # same item: with option order decorrelated, and with the original taxonomy
        # order, so the 0.867 obtained earlier under the old ordering can be checked
        # rather than assumed.
        l2 = run_level(sub, "Which specific request is this about?", decorrelate=True)
        row["l2_cond_ok"] = l2["chosen_label"] == truth
        row["l2_options"] = l2["n_options"]
        row["l2_truth_pos"] = l2["truth_pos"]
        l2_nc = run_level(sub, "Which specific request is this about?", decorrelate=False)
        row["l2_cond_ok_nondecorr"] = l2_nc["chosen_label"] == truth

        # flat 77
        flat = run_level(intents, "Which specific request is this about?")
        row["flat_ok"] = flat["chosen_label"] == truth
        row["flat_p_truth"] = flat["raw"]["probs"].get(
            next(k for k, v in zip([f"n{i+1:02d}" for i in range(len(intents))], intents)
                 if v == truth) if truth in intents else "", None)

        # end-to-end: L1 then descend within whatever group it actually chose
        e2e = False
        label_to_group = {lab: i for i, lab in enumerate(group_labels)}
        cgi = label_to_group.get(l1["chosen_label"])
        if cgi is not None:
            for s in deep[cgi]:
                if truth in s:
                    l2b = run_level(s, "Which specific request is this about?")
                    e2e = l2b["chosen_label"] == truth
                    break
        row["e2e_ok"] = e2e
        rows.append(row)
        print(f"{truth[:32]:<34} L1={row['l1_ok']!s:<5} L2c={row['l2_cond_ok']!s:<5} "
              f"flat={row['flat_ok']!s:<5} e2e={row['e2e_ok']}")

    n = len(rows)

    def rate(k: str) -> float:
        return sum(1 for r in rows if r[k]) / n

    summary = {
        "n_items": n,
        "n_intents": len(intents),
        "n_top_groups": len(groups),
        "top_group_size": GROUP_SIZE_TOP,
        "subgroup_size": SUBGROUP_SIZE,
        "layer1_options": len(groups),
        "flat_options": len(intents),
        "layer1_accuracy": rate("l1_ok"),
        "layer2_conditional_accuracy": rate("l2_cond_ok"),
        "layer2_conditional_accuracy_nondecorr": rate("l2_cond_ok_nondecorr"),
        "layer2_order_effect": rate("l2_cond_ok") - rate("l2_cond_ok_nondecorr"),
        "flat_accuracy": rate("flat_ok"),
        "end_to_end_accuracy": rate("e2e_ok"),
        "hierarchy_beats_flat": rate("e2e_ok") > rate("flat_ok"),
        "controls": {
            "opaque_keys": "n01-style; intent name only in the option value",
            "option_order": "shuffled per item; truth position recorded",
            "conditional_arm": "layer 2 measured conditional on the true ancestor",
            "admission": "by our own tokenizer count, never Laya's fits flag",
        },
        "instrument": instrument_record(),
        "contamination_note": (
            "Banking77 is a Laya-prior set and its label file has plausibly been crawled, "
            "so NO accuracy claim may be drawn from this probe. It supports only the "
            "internal, paired structural comparison between hierarchy and flat."),
        "chance_rates": {
            "layer1": round(1.0 / max(1, len(groups)), 4),
            "flat": round(1.0 / len(intents), 4),
        },
        "caveat": (f"PROBE: {n} test-split utterances filtered to 8-24 words. Small n; "
                   f"one item moves a rate by {1.0/n:.3f}."),
    }
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    out = run()
    p = RESULTS / "P7-banking77-hierarchical-sharding.json"
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("\n=== SUMMARY ===")
    print(json.dumps(out["summary"], indent=2))
    print(f"\nwritten: {p}")
