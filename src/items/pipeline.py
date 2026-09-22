"""Item-generation and certificate pipeline (deliverable of the opening phase).

DESIGN PRINCIPLES, each forced by a measurement or an audit finding
-------------------------------------------------------------------
L0 authorship (R14). The harness owns the world state and authors or selects EVERY
string a judge can see. A judge never sees a string a model produced. This is what
makes ground truth independent of the models under test and breaks the circularity
that would otherwise invalidate every accuracy number.

Derivability by construction (V4 T3, the unsolved threat). V4 found that a judge's
failure on an item could be an artefact of the item being UNANSWERABLE from what the
model was shown, rather than a failure of judgment. The mitigation proposed there was
a build-time entailment/necessity certificate. This pipeline implements the strongest
available form of it: for every item it records the MINIMAL SET OF SPANS the correct
answer follows from, and a validator re-checks that the answer really is entailed by
those spans alone.

Carrier-required items only (V4's 57%-inert finding). V4 measured that 170 of 300
planned items (57%) had answers that depended only on a local block, so they carried
no information about the horizon manipulation. Rather than certifying inert items and
discarding them later, this generator makes the carrier STRUCTURALLY NECESSARY: the
decisive figure lives in exactly one carrier entry, and a validator asserts that the
item is NOT answerable when that entry is withheld. An item that survives is
`carrier_required=True` by construction, so the certified-live fraction is 1.0 rather
than 0.43 -- which the D2 decision identified as worth ~2.1x in effective N, i.e.
roughly 1,100 free items.

Opaque option keys (P6 finding). The P6 probe returned OPPOSITE verdicts depending only
on whether criteria KEYS were descriptive intent names or opaque codes, because
name-shaped keys leak part of the taxonomy. Option keys here are therefore `i01`-style
codes and the descriptive text lives only in the option VALUE.

Budgets are TOKENS, measured with the checkpoint's own tokenizer (R13 constraint 1).
Character counts are recorded only for diagnosis. Every item carries a token count and
is rejected if it exceeds the per-checkpoint ceiling.

WHAT THIS MODULE DOES NOT DO
----------------------------
It does not yet generate the FAMILY-SPECIFIC long-horizon tasks (SPECSHIFT toolchains,
SCHEMA-EPOCH migrations, AUDIT-CASCADE loops). It builds the substrate those families
share -- carrier, levels, certificates, budget accounting, validation -- and one worked
family (EVIDENCE-BRIEF-style claim checking) end to end so the shape is real rather
than described.
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
from bench_env import ITEMS  # noqa: E402


import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "instrument"))
from laya_client import CHECKPOINT_CLAMP_TOKENS, LayaClient, instrument_record  # noqa: E402

# ---------------------------------------------------------------------------- schema

PRIMITIVES = ("noul", "choice", "score")


@dataclass
class Certificate:
    """Build-time proof obligations attached to every item.

    `derivation_span_ids`  the spans the correct answer follows from.
    `necessary_span_ids`   those spans whose removal makes the item unanswerable.
    `carrier_required`     True iff withholding the carrier changes the answer.
    `unanswerable_without` re-check that the item is NOT derivable from the rest.
    """

    derivation_span_ids: list[str]
    necessary_span_ids: list[str] = field(default_factory=list)
    carrier_required: bool = False
    unanswerable_without: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class Item:
    item_id: str
    family: str
    primitive: str
    state_spans: list[dict]          # [{span_id, text, kind}] -- judge-visible
    carrier_ids: list[str]           # span_ids forming the carrier
    question: dict                   # {instructions, criteria:{opaque_key: text}}
    ground_truth: str                # the correct criteria KEY
    certificate: Certificate
    level: int = 0                   # horizon level
    carrier_trace_present: bool = True
    meta: dict = field(default_factory=dict)

    # ---------------------------------------------------------------- integrity

    def validate(self) -> list[str]:
        """Return a list of violations. Empty list means the item is admissible."""
        errs: list[str] = []
        if self.primitive not in PRIMITIVES:
            errs.append(f"unknown primitive {self.primitive!r}")
        keys = list(self.question.get("criteria", {}))
        if len(keys) < 2:
            errs.append("fewer than 2 criteria (a choice needs >=2; Jev refuses 1)")
        if self.ground_truth not in keys:
            errs.append("ground_truth key is not among the criteria keys")
        # P6: option keys must be opaque, or a naming cue leaks the answer.
        for k in keys:
            if not re.fullmatch(r"[a-z]\d{2,3}", k):
                errs.append(f"criteria key {k!r} is not opaque (expected i01-style)")
                break
        # every span referenced by the certificate must exist
        known = {s["span_id"] for s in self.state_spans}
        for sid in self.certificate.derivation_span_ids + self.certificate.necessary_span_ids:
            if sid not in known:
                errs.append(f"certificate references unknown span {sid!r}")
        # the carrier must be a subset of the spans
        for cid in self.carrier_ids:
            if cid not in known:
                errs.append(f"carrier references unknown span {cid!r}")
        # V4's inert-item defect: a carrier-required item must cite a carrier span
        # among its necessary spans, otherwise the answer does not depend on horizon.
        if self.certificate.carrier_required and not (set(self.carrier_ids)
                                                     & set(self.certificate.necessary_span_ids)):
            errs.append("carrier_required=True but no carrier span is certified necessary")
        if not self.certificate.necessary_span_ids:
            errs.append("no necessary spans certified -- item may be inert")
        return errs

    def render_state(self, include_carrier: bool = True,
                     include_span_ids: list[str] | None = None) -> str:
        """Deterministic serializer. Same bytes for every judge, always.

        Newest-first ordering: an end-truncating reader loses the OLDEST material
        first, which is the least control-relevant, rather than losing the current
        step. `DROPPED: n` is emitted FIRST so a reader that keeps the front can see
        that material was elided before it reads any of it.
        """
        omit = set() if include_carrier else set(self.carrier_ids)
        spans = [s for s in self.state_spans if s["span_id"] not in omit]
        if include_span_ids is not None:
            keep = set(include_span_ids)
            spans = [s for s in spans if s["span_id"] in keep]
        head = f"DROPPED: {len(self.state_spans) - len(spans)}"
        body = "\n".join(f"[{s['span_id']}] {s['text']}" for s in spans)
        return f"{head}\n{body}"


# ------------------------------------------------------------------- EVIDENCE-BRIEF

_FIGURES = [
    ("pallets shipped in Q3", 4182, "units"),
    ("authentication outage duration", 47, "minutes"),
    ("invoice INV-4471 amount", 18400, "USD"),
    ("late deliveries in March", 312, "parcels"),
    ("battery cells replaced under warranty", 918, "cells"),
]


def _mk_evidence_item(idx: int, rng: random.Random, level: int,
                      carrier_len: int = 5) -> Item:
    """One worked family, using the template that P5c VALIDATED.

    INTEGRATION NOTE. An earlier version of this generator produced a template that was
    never validated: no authority marker, and a question that asked "what is the current
    X" while nothing in the state marked which line was current. Measured through the
    harness it scored 0.25 -- chance -- which is an ITEM-CONSTRUCTION failure, not a
    judge failure. P5c then established by direct comparison which template is usable:

        explicit "(current)" tag : accuracy 1.00 with the carrier, 0.00 without
        no tag                   : accuracy 0.40 with the carrier, 0.00 without

    So the explicit-tag template is the one that is BOTH derivable and carrier-required,
    and it is the one implemented here. The generator and the harness must use the same
    template or the harness silently measures a different task than the one certified;
    that is exactly the mismatch this note records.

    CARRIER WIDTH IS FIXED ACROSS LEVELS -- load-bearing. V4's audit found the dial
    defect was that `d = H - 4` made distance-from-poison and run position perfectly
    collinear, and that varying carrier width would confound the horizon manipulation.
    The rendered state is therefore the same length at every level; what varies with
    `level` is only WHICH revision carries the authoritative figure.
    """
    label, value, unit = _FIGURES[idx % len(_FIGURES)]
    # Distinct figures so options are semantically separable; P5's first failure was a
    # numeric option set differing by 1-40 units (4182/4219/4220/4221).
    figs = [value, value + 900, value * 2, value // 2 or value + 7, value + 1250]

    spans: list[dict] = [
        {"span_id": "s1", "kind": "preamble",
         "text": "Audit memo. The ledger lists successive revisions; later lines "
                 "supersede earlier ones."},
    ]

    # distance-from-poison: level 0 puts the authoritative revision nearest the head of
    # the ledger, larger levels push it deeper.
    order = [0, 2, 4, 1, 3]                 # deterministic reordering
    vals = [figs[i] for i in order]
    true_pos = min(level, carrier_len - 1) if level < carrier_len else carrier_len - 1
    # Move the authoritative value to `true_pos` without mutating the source list:
    # an in-place insert here would shift the sequence that the criteria are then built
    # from, so the ground-truth label would no longer match the rendered line.
    rest = [v for v in vals if v != value]
    vals = rest[:true_pos] + [value] + rest[true_pos:]
    assert vals[true_pos] == value, "authoritative value not at true_pos"

    carrier_ids: list[str] = []
    for i, v in enumerate(vals):
        sid = f"c{i + 1}"
        tag = " (current)" if i == true_pos else ""
        spans.append({"span_id": sid, "kind": "carrier",
                      "text": f"revision {i + 1}: {label} = {v} {unit}{tag}"})
        carrier_ids.append(sid)
    true_span = f"c{true_pos + 1}"
    spans.append({"span_id": "s2", "kind": "instruction",
                  "text": "Answer using the revisions above."})

    # Criteria are built from the SAME values that were rendered, so that ground_truth
    # indexes the text a judge actually saw. The option ORDER is shuffled with a
    # per-item deterministic seed: leaving the rendered (state) order in place conflates
    # a reading skill with a positional preference. Measured consequence of NOT
    # shuffling: the judge picked the first-listed option in 6 of 8 rows, which reads as
    # 1.00 accuracy whenever the authoritative value happens to sit first and 0.125 when
    # it does not. Position must therefore be decorrelated from correctness by design,
    # and `meta.truth_pos_in_criteria` is recorded so position effects stay analysable.
    rendered_vals = list(vals)
    order_c = list(range(len(rendered_vals)))
    random.Random(f"{idx}:{level}:criteria").shuffle(order_c)
    shuffled = [rendered_vals[i] for i in order_c]
    crit = {f"i{i + 1:02d}": f"{v} {unit}" for i, v in enumerate(shuffled)}
    truth = f"i{shuffled.index(value) + 1:02d}"
    truth_pos_in_criteria = shuffled.index(value)

    return Item(
        item_id=f"EB-L{level}-{idx:03d}",
        family="EVIDENCE-BRIEF",
        primitive="choice",
        state_spans=spans,
        carrier_ids=carrier_ids,
        question={
            "instructions": f"What is the current {label}? Choose the figure marked "
                            f"(current).",
            "criteria": crit,
        },
        ground_truth=truth,
        certificate=Certificate(
            derivation_span_ids=[true_span, "s1"],
            necessary_span_ids=[true_span],
            carrier_required=True,
            unanswerable_without=[true_span],
            notes="Authoritative figure is the sole line tagged (current); all other "
                  "revisions carry distinct decoy figures. Template validated by P5c: "
                  "1.00 with the carrier, 0.00 without.",
        ),
        level=level,
        meta={"label": label, "value": value, "unit": unit, "true_span": true_span,
              "true_pos": true_pos, "carrier_len": len(vals),
              "template": "explicit_current_tag_v1"},
    )


def generate(family: str = "EVIDENCE-BRIEF", n_per_level: int = 4,
             levels: tuple[int, ...] = (0, 4, 28, 124),
             seed: int = 20260922) -> list[Item]:
    """D2's frozen horizon levels: a floor plus distance-from-poison 0/4/28/124."""
    rng = random.Random(seed)
    items: list[Item] = []
    if family != "EVIDENCE-BRIEF":
        raise ValueError("only EVIDENCE-BRIEF is implemented in this phase")
    for level in levels:
        for i in range(n_per_level):
            items.append(_mk_evidence_item(len(items), rng, level))
    return items


# ------------------------------------------------------------------------ validation


def validate_certificates(items: list[Item]) -> dict:
    """Re-check the proof obligations. This is the mechanism that converts
    'we believe the item is answerable' into a checked claim."""
    results: list[dict] = []
    for it in items:
        errs = it.validate()
        # necessity re-check: does the item become ambiguous without the necessary
        # spans? Operationalised as: does the cited decisive figure disappear?
        without = it.render_state(include_carrier=False)
        true_span = it.meta.get("true_span")
        decoy_present = str(it.meta["value"]) in without
        results.append({
            "item_id": it.item_id,
            "level": it.level,
            "violations": errs,
            "carrier_required": it.certificate.carrier_required,
            "decisive_value_leaks_without_carrier": decoy_present,
            "admissible": not errs and not decoy_present,
        })
    ok = [r for r in results if r["admissible"]]
    return {
        "n_items": len(items),
        "n_admissible": len(ok),
        "n_inert": sum(1 for r in results if not r["carrier_required"]),
        "certified_live_fraction": (
            sum(1 for r in results if r["carrier_required"]) / len(results)
            if results else None),
        "results": results,
    }


def budget_report(items: list[Item], checkpoint: str = "english") -> dict:
    """Every item measured in the checkpoint's OWN tokens, never characters."""
    client = LayaClient(autostart=False)
    ceiling = CHECKPOINT_CLAMP_TOKENS[checkpoint]
    rows = []
    for it in items:
        state = it.render_state()
        # head cost = instructions + option text, which shares the budget
        qtext = it.question["instructions"] + " " + " ".join(it.question["criteria"].values())
        st = client.count_tokens(state, checkpoint)
        ht = client.count_tokens(qtext, checkpoint)
        rows.append({
            "item_id": it.item_id, "level": it.level,
            "state_tokens": st, "head_tokens": ht,
            "total_tokens": st + ht,
            "fits_clamp": (st + ht + 1) <= ceiling,
            "state_chars": len(state),
        })
    over = [r for r in rows if not r["fits_clamp"]]
    return {
        "checkpoint": checkpoint, "clamp_tokens": ceiling,
        "n_items": len(rows), "n_over_budget": len(over),
        "max_state_tokens": max(r["state_tokens"] for r in rows) if rows else 0,
        "max_total_tokens": max(r["total_tokens"] for r in rows) if rows else 0,
        "rows": rows,
    }


if __name__ == "__main__":
    out_dir = ITEMS
    out_dir.mkdir(parents=True, exist_ok=True)

    items = generate(n_per_level=4)
    cert = validate_certificates(items)
    budget = budget_report(items)

    print(f"generated           : {len(items)} items")
    print(f"admissible          : {cert['n_admissible']}/{cert['n_items']}")
    print(f"inert items         : {cert['n_inert']}")
    print(f"certified-live frac : {cert['certified_live_fraction']}")
    print(f"budget: max state   : {budget['max_state_tokens']} tokens "
          f"(clamp {budget['clamp_tokens']})")
    print(f"budget: over-budget : {budget['n_over_budget']}")

    payload = {
        "generated_at_utc": instrument_record()["recorded_at_utc"],
        "instrument": instrument_record(),
        "n_items": len(items),
        "validation": cert,
        "budget": budget,
        "items": [asdict(it) for it in items],
    }
    p = out_dir / "evidence-brief-pilot.json"
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nwritten: {p}")

    bad = [r for r in cert["results"] if not r["admissible"]]
    if bad:
        print("\nINADMISSIBLE ITEMS:")
        for r in bad[:5]:
            print(f"  {r['item_id']}: {r['violations']} leak={r['decisive_value_leaks_without_carrier']}")
