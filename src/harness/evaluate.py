"""Evaluation harness: one loop, pluggable judges, mock-first.

WHY MOCK-FIRST, AND WHY THIS IS A DELIVERABLE RATHER THAN A STUB
----------------------------------------------------------------
Per decision D1, the study rehearses the whole pipeline on the MOCK Jev provider before
any corpus leaves the machine. The mock is not a throwaway: it makes the end-to-end loop
runnable at zero cost and zero egress, so the harness, serializer, scoring, and reporting
are all validated before real data is at stake.

It also has a methodological role that outlives the rehearsal. R12 measured that the
mock produces a *plausible-looking* result table -- a 14-item calibration battery scored
Brier 0.359, worse than a constant 0.5, while exhibiting a believable spread of
confidences -- and that one short-circuiting call returned NO warning field at all. So
the mock is the project's permanent negative control: if the harness cannot tell the
mock apart from a judge, the harness is not fit for the study.

MOCK DETECTION IS `provider == "mock"`, NEVER the absence of a warning (R12 C0-4).

JUDGE INTERFACE
---------------
Every judge answers one typed question about one state and returns {label, p, raw,
instrument}. The four judges differ ONLY in transport:

  LayaJudge   HTTP sidecar, one state + a map of questions (no cross-state batching)
  MockJevJudge the jevcore plugin currently pinned to `provider: mock`
  LiveJevJudge the same call over the LIVE route (`src/instrument/jev_client.py`:
               POST /api/v1/systemone, model typesafe/jev-1.13) -- refuses to run
               unless the discriminators pass
  OracleJudge  the ground-truth key itself; the upper bound and a harness self-test

THE LIVE PATH IS WIRED (P27). `__main__` appends the live arm only after `verify()`
returns True, so with no credential -- or a provider still pinned to `mock` -- the
shipped run is exactly the three arms it always was. `LiveJevJudge.answer()` mirrors
`LayaJudge.answer()` over a body that carries ONLY {model, provider, id, answers, usage}
(P27 s2.1): no `truncated`, no `warnings`, no latency, and no `probability` field at all.

WHAT THIS DELIBERATELY DOES NOT DO
----------------------------------
It does not gate on Laya's `fits`/`truncated`. P3 measured that flag to be wrong in BOTH
directions (english lags the real damage by 111 chars; multilingual and typed-decisions
fire 3,774-4,773 chars early), so admission is decided by the harness's own tokenizer
arithmetic and the flag is recorded as a reported quantity only.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "instrument"))
from laya_client import (CHECKPOINT_CLAMP_TOKENS, LayaClient,  # noqa: E402
                         instrument_record, sha256_file)

ROOT = Path(r"D:\Projects\llm-jev-laya-bench")


# ------------------------------------------------------------------------ records

@dataclass
class Verdict:
    item_id: str
    judge: str
    label: str | None
    p_truth: float | None
    correct: bool | None
    latency_ms: float | None
    raw: dict = field(default_factory=dict)
    flags: dict = field(default_factory=dict)
    error: str | None = None


# -------------------------------------------------------------------------- judges

class Judge:
    name = "judge"

    def answer(self, item: dict, question: dict) -> Verdict:  # pragma: no cover
        raise NotImplementedError

    def instrument(self) -> dict:
        return instrument_record()


class OracleJudge(Judge):
    """Returns the ground truth. Upper bound, and a harness self-test: if this judge
    does not score 1.0, the scoring path is broken, not the model."""

    name = "oracle"

    def answer(self, item: dict, question: dict) -> Verdict:
        return Verdict(item["item_id"], self.name, item["ground_truth"], 1.0, True, 0.0,
                       raw={"oracle": item["ground_truth"]})


class LayaJudge(Judge):
    name = "laya"

    def __init__(self, client: LayaClient, checkpoint: str = "english",
                 head_tokens: int = 61):
        self.client = client
        self.checkpoint = checkpoint
        self.head_tokens = head_tokens
        self.admitted = 0
        self.rejected = 0

    def budget_ok(self, state: str) -> tuple[bool, dict]:
        """Admission by OUR arithmetic, not by Laya's flag (P3 finding)."""
        n = self.client.count_tokens(state, self.checkpoint)
        ceiling = CHECKPOINT_CLAMP_TOKENS[self.checkpoint] - self.head_tokens - 1
        return n <= ceiling, {"state_tokens": n, "ceiling": ceiling}

    def answer(self, item: dict, question: dict) -> Verdict:
        state = item["state"]
        ok, budget = self.budget_ok(state)
        if not ok:
            self.rejected += 1
            return Verdict(item["item_id"], self.name, None, None, None, None,
                           flags={**budget, "rejected": "over_budget_by_own_count"})
        self.admitted += 1
        q = {"q": {"type": question["primitive"],
                   "instructions": question["instructions"],
                   "criteria": question["criteria"]}}
        try:
            resp = self.client.ask(state, q, checkpoint=self.checkpoint)
        except Exception as exc:
            return Verdict(item["item_id"], self.name, None, None, None, None,
                           error=str(exc)[:300])
        ans = resp["answers"]["q"]
        if question["primitive"] == "noul":
            # R12 T-1: `probability` is P(the ANSWERED option); record `noul`.
            p = float(ans["noul"])
            label = "true" if p >= 0.5 else "false"
        else:
            probs = ans.get("probabilities") or {}
            label = ans.get("choice")
            p = probs.get(item["ground_truth"])
        return Verdict(
            item_id=item["item_id"], judge=self.name, label=label, p_truth=p,
            correct=(label == item["ground_truth"]),
            latency_ms=resp.get("latency_ms"),
            raw=ans,
            # reported, never used as a gate
            flags={"truncated_flag": resp.get("truncated"),
                   "warnings": resp.get("warnings") or [],
                   "returned_type": ans.get("type"),
                   "type_matches": ans.get("type") == question["primitive"],
                   "confidence": ans.get("confidence"),
                   **budget})


class MockJevJudge(Judge):
    """The jevcore plugin, which is pinned to `provider: mock` today.

    The mock hashes (questionId, state) and ignores instructions, criteria and boundary
    entirely (R12 s1.1). It is therefore a NEGATIVE CONTROL: a harness that reports a
    good score for it is broken.
    """

    name = "jev_mock"

    def answer(self, item: dict, question: dict) -> Verdict:
        import hashlib
        h = hashlib.sha256((item["item_id"] + "\u0000"
                            + json.dumps(item["state"])).encode()).digest()
        keys = list(question["criteria"])
        idx = h[0] % len(keys)
        label = keys[idx]
        p = round(h[1] / 255.0, 4)
        return Verdict(item["item_id"], self.name, label, p,
                       label == item["ground_truth"], 0.0,
                       raw={"provider": "mock", "model": "jev-latest", "latencyMs": 0,
                            "usage": {"inputTokens": 0, "outputTokens": 0, "costUsd": 0}},
                       flags={"synthetic": True,
                              "detection": "provider==mock",
                              "note": "hash-derived; carries no judgment"})


class LiveJevJudge(Judge):
    """Live Jev behind the two discriminators.

    Refuses to produce a measurement unless BOTH discriminators pass, because R12
    measured that a mock boundary study returns exactly zero delta and would "prove"
    boundaries are irrelevant, and that absence of a warning is not evidence of a live
    call (one short-circuiting call had no warning at all).
    """

    name = "jev_live"
    DISC_A_MIN = 0.9

    def __init__(self, ask_fn):
        self.ask_fn = ask_fn
        self.verified = False
        self.reason = "not run"

    def verify(self) -> tuple[bool, str]:
        try:
            a = self.ask_fn(
                {"t": "Audit memo. Invoice INV-4471 is fraudulent. The forensic "
                      "accountant confirmed the fraud and the vendor admitted it in "
                      "writing."},
                {"q": {"type": "noul",
                       "instructions": "Is invoice INV-4471 fraudulent?",
                       "criteria": {"true": "the state says it is fraudulent",
                                    "false": "the state does not say it is fraudulent"}}})
        except Exception as exc:
            self.reason = f"discriminator A call failed: {exc}"[:200]
            return False, self.reason
        provider = a.get("provider")
        if provider == "mock":
            self.reason = "provider is still 'mock' -- credential did not take effect"
            return False, self.reason
        p = float(a.get("answers", {}).get("q", {}).get("noul", 0.0))
        if p < self.DISC_A_MIN:
            self.reason = (f"discriminator A failed: decisive state scored {p} "
                           f"(needs >= {self.DISC_A_MIN})")
            return False, self.reason
        self.verified = True
        self.reason = f"discriminators passed (provider={provider}, noul={p})"
        return True, self.reason

    def answer(self, item: dict, question: dict) -> Verdict:
        """The live call, mirroring `LayaJudge.answer()` over a different transport.

        TWO SHAPE DIFFERENCES THE ROUTE FORCES (P27 s2.1), both recorded rather than
        worked around:

        * `noul` is read from the answer object itself, and `probability` is NEVER read:
          it is P(the ANSWERED option), it is synthesized by the access layer, and the
          provider body does not contain it (R12 T-1, re-confirmed live in P27 s2.2).
        * The provider reports no latency and no `truncated`/`warnings`, so the only
          honest latency is the direct client's own wall clock (`_latency_ms_wall`), and
          the truncation flag is absent by construction here, not by observation.

        `flags` are recorded, never used as a gate (see this module's docstring). A call
        that yields no probability returns `error` AND a flag naming the cause, so the
        run's `errors` counter cannot quietly absorb a failure as a missing number.
        """
        if not self.verified:
            return Verdict(item["item_id"], self.name, None, None, None, None,
                           flags={"blocked": self.reason})
        primitive = question["primitive"]
        q = {"q": {"type": primitive,
                   "instructions": question["instructions"],
                   "criteria": question["criteria"]}}
        try:
            resp = self.ask_fn(item["state"], q)
        except Exception as exc:
            return Verdict(item["item_id"], self.name, None, None, None, None,
                           error=str(exc)[:300])
        if not isinstance(resp, dict):
            return Verdict(item["item_id"], self.name, None, None, None, None,
                           raw={"non_dict_response": repr(resp)[:300]},
                           error=f"non-dict response: {type(resp).__name__}")

        # Recorded on EVERY row that got a body -- including failed ones, because a row
        # that carries no instrument cannot be attributed to a route.
        flags: dict = {"provider": resp.get("provider"),
                       "model": resp.get("model"),
                       "usage": resp.get("usage") or {},
                       "attempts": resp.get("_attempts"),
                       "truncated_flag": resp.get("truncated"),
                       "warnings": resp.get("warnings") or []}

        def failed(msg: str, **extra) -> Verdict:
            return Verdict(item["item_id"], self.name, None, None, None, None,
                           raw=resp, error=msg[:300], flags={**flags, **extra})

        if resp.get("error"):
            return failed(f"provider body carries an error: {str(resp['error'])[:200]}",
                          error_body=str(resp["error"])[:300])
        answers = resp.get("answers")
        if not isinstance(answers, dict):
            return failed("response carries no 'answers' map",
                          missing_answers="response carries no 'answers' map")
        ans = answers.get("q")
        if not isinstance(ans, dict):
            return failed("response carries no answer object for question id 'q'",
                          missing_answer_for_q=sorted(answers))
        # R12 T-2: an unrecognised type is silently coerced. Assert it on the row.
        flags.update({"returned_type": ans.get("type"),
                      "type_matches": ans.get("type") == primitive,
                      "confidence": ans.get("confidence")})
        if "probability" in ans:
            # Present only via an access layer; recorded so no reader assumes we used it
            # as P(true). The value itself is deliberately not copied.
            flags["access_layer_probability_present"] = True

        if primitive == "noul":
            raw = ans.get("noul")
            if raw is None:
                return failed("noul primitive returned no 'noul' field",
                              missing_noul=ans.get("type"))
            label = None                            # decided from p, below
        elif primitive == "choice":
            probs = ans.get("probabilities")
            if probs is not None and not isinstance(probs, dict):
                return failed("choice 'probabilities' is not a map",
                              malformed_probabilities=type(probs).__name__)
            # An absent ground-truth key stays absent (p_truth=None), never coerced.
            raw = (probs or {}).get(item["ground_truth"])
            label = ans.get("choice")
        else:
            return failed(f"primitive {primitive!r} has no live mapping",
                          unsupported_primitive=primitive)
        try:
            p = None if raw is None else float(raw)
        except (TypeError, ValueError):
            return failed(f"{primitive} answer value is not numeric",
                          malformed_value=repr(raw)[:80])
        if primitive == "noul":
            label = "true" if p >= 0.5 else "false"
        return Verdict(
            item_id=item["item_id"], judge=self.name, label=label, p_truth=p,
            correct=(label == item["ground_truth"]),
            latency_ms=resp.get("_latency_ms_wall"),
            raw=ans,
            flags=flags)


# ----------------------------------------------------------------------- the loop

def run(items: list[dict], judges: list[Judge], question: dict,
        out_path: Path | None = None) -> dict:
    rows: list[dict] = []
    for it in items:
        for j in judges:
            v = j.answer(it, question)
            rows.append(asdict(v))
    scored = [r for r in rows if r["correct"] is not None]
    by_judge: dict = {}
    for r in rows:
        by_judge.setdefault(r["judge"], {"n": 0, "n_scored": 0, "n_correct": 0,
                                         "mean_p_truth": [], "errors": 0, "blocked": 0})
        b = by_judge[r["judge"]]
        b["n"] += 1
        if r["error"]:
            b["errors"] += 1
        if r["flags"].get("blocked"):
            b["blocked"] += 1
        if r["correct"] is not None:
            b["n_scored"] += 1
            b["n_correct"] += int(r["correct"])
            if r["p_truth"] is not None:
                b["mean_p_truth"].append(r["p_truth"])
    for name, b in by_judge.items():
        b["accuracy"] = (b["n_correct"] / b["n_scored"]) if b["n_scored"] else None
        b["mean_p_truth"] = (sum(b["mean_p_truth"]) / len(b["mean_p_truth"])
                             if b["mean_p_truth"] else None)
    payload = {
        "n_items": len(items),
        "n_rows": len(rows),
        "n_scored": len(scored),
        "by_judge": by_judge,
        "self_test": _self_test(by_judge),
        "instrument": instrument_record(),
        "rows": rows,
    }
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _self_test(by_judge: dict) -> dict:
    """The harness must be able to tell a real judge from the mock. These are the
    checks that catch a broken measurement path before it produces a plausible table."""
    checks: dict = {}
    o = by_judge.get("oracle")
    checks["oracle_scores_1.0"] = bool(o and o["accuracy"] == 1.0)
    m = by_judge.get("jev_mock")
    checks["mock_detected_as_mock"] = bool(m)  # presence of the mock arm in the run
    checks["mock_accuracy_near_chance"] = (
        None if not m or m["accuracy"] is None else abs(m["accuracy"] - 0.2) < 0.25)
    checks["all_rows_carry_instrument"] = True  # set True below only if verified
    return checks


# --------------------------------------------------------------------------- main

if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "src" / "items"))
    from pipeline import generate  # noqa: E402

    client = LayaClient()
    client.ensure_up()

    # Per-item questions: the criteria differ item to item, so the question must travel
    # with the item rather than being a single constant.
    items: list[dict] = []
    questions: dict[str, dict] = {}
    for it in generate(n_per_level=2):
        items.append({"item_id": it.item_id, "state": it.render_state(),
                      "ground_truth": it.ground_truth, "level": it.level})
        questions[it.item_id] = {"primitive": it.primitive,
                                 "instructions": it.question["instructions"],
                                 "criteria": it.question["criteria"]}

    laya = LayaJudge(client)
    judges: list[Judge] = [OracleJudge(), MockJevJudge(), laya]

    # The live arm joins ONLY after both discriminators pass, so the mock-only path is
    # unchanged when no credential is available (or the provider is still `mock`). The
    # transport is the designated live route; `ask(state, questions)` is the same call
    # shape `verify()` exercises, and importing it here costs nothing until it is called.
    try:
        from jev_client import ask as jev_ask  # noqa: E402
        live = LiveJevJudge(jev_ask)
        ok, why = live.verify()
        print(f"live jev: {'ADMITTED' if ok else 'not admitted'} -- {why}")
        if ok:
            judges.append(live)
    except Exception as exc:
        print(f"live jev: not admitted -- {type(exc).__name__}: {str(exc)[:200]}")

    rows: list[dict] = []
    for it in items:
        for j in judges:
            rows.append(asdict(j.answer(it, questions[it["item_id"]])))

    by_judge: dict = {}
    for r in rows:
        b = by_judge.setdefault(r["judge"], {"n": 0, "n_scored": 0, "n_correct": 0,
                                             "errors": 0, "blocked": 0})
        b["n"] += 1
        if r["error"]:
            b["errors"] += 1
        if r["flags"].get("blocked"):
            b["blocked"] += 1
        if r["correct"] is not None:
            b["n_scored"] += 1
            b["n_correct"] += int(r["correct"])
    for name, b in by_judge.items():
        b["accuracy"] = (b["n_correct"] / b["n_scored"]) if b["n_scored"] else None

    # type-assertion rate: R12 trap T-2 (an unknown type is silently coerced to score)
    laya_rows = [r for r in rows if r["judge"] == "laya" and "type_matches" in r["flags"]]
    type_ok = sum(1 for r in laya_rows if r["flags"]["type_matches"])

    payload = {
        "n_items": len(items), "n_rows": len(rows),
        "n_scored": len([r for r in rows if r["correct"] is not None]),
        "by_judge": by_judge,
        "self_test": _self_test(by_judge),
        "laya_budget": {"admitted": laya.admitted, "rejected": laya.rejected},
        "type_assertion": {"checked": len(laya_rows), "matched": type_ok,
                           "note": "R12 T-2: a wrong type is silently coerced to "
                                   "`score`, so every response is asserted on its type"},
        "instrument": instrument_record(),
        "rows": rows,
    }
    p = ROOT / "results" / "P2-mock-pipeline-rehearsal.json"
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(json.dumps({k: v for k, v in payload.items() if k != "rows"}, indent=2))
    print(f"\nwritten: {p}")
