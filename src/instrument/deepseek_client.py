"""DeepSeek-V4.1-Flash client for the LLM arm, with the four arms the design requires.

WHY A DIRECT CLIENT RATHER THAN A SUBAGENT
------------------------------------------
The protocol needs the SAME items, the SAME questions and the SAME option ordering that
Laya and Jev already answered, plus per-call latency measured by us. A subagent answers
in prose and reports nothing about tokens or cache behaviour, and R11 measured that
parallel tool calls share a single result timestamp, so latency cannot be recovered from
a transcript. A direct HTTP call to /chat/completions gives all of it.

WHAT THE API DOCUMENT SAYS, AND WHICH PARTS CONSTRAIN THE DESIGN (verified 2026-09-22)
-------------------------------------------------------------------------------------
  model                 `deepseek-flash` (this is DeepSeek-V4.1-Flash)
  thinking.reasoning_effort   none | low | high | max; default high. `none` disables
                        thinking. Aliases: minimal->low, medium/xhigh->high.
  max_tokens            default 8K non-thinking, 64K thinking (128K at effort max)
  response_format       {type: "json_object"} guarantees valid JSON, but the doc warns
                        you must ALSO instruct the model to emit JSON or it can stream
                        whitespace until the token limit.
  temperature           has NO effect in thinking mode
  top_p                 only applies in thinking mode, floored at 0.95; fixed at 1.0 in
                        non-thinking mode and ignored
  tool_choice required  returns 400 in thinking mode
  logprobs/top_logprobs supported (top_logprobs <= 20), so the LOGIT-STYLE readout R16
                        asked for is real rather than hypothetical
  usage                 prompt_cache_hit_tokens / prompt_cache_miss_tokens and
                        completion_tokens_details.reasoning_tokens -> cost is directly
                        computable, INCLUDING the reasoning tokens that carry the
                        expensive output price

Three consequences the design has to respect:
  1. A k-sample self-consistency arm CANNOT be run as "temperature 0 vs 0.7" inside
     thinking mode, because temperature has no effect there. It must run non-thinking.
  2. Reasoning tokens are billed as output and are invisible in `content`, so pricing a
     call from the visible answer alone understates it -- V3 measured outputTokens
     demonstrably including reasoning.
  3. The model emits `reasoning_content` separately; anything that parses only `content`
     is parsing the answer, which is what we want, but must not assume `content` is
     non-empty when the budget was consumed by reasoning.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import yaml

CRED_PATH = Path(r"C:\Users\zzhdz\.dsh\.credentials.yaml")
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-flash"


def api_key() -> str:
    """Read the key from DSH's managed store. Never logged, never printed."""
    doc = yaml.safe_load(CRED_PATH.read_text(encoding="utf-8")) or {}
    key = (doc.get("refs") or {}).get("DEEPSEEK_API_KEY") or ""
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY is not registered in the credential store")
    return key


# Verified prices, USD per 1M tokens, off-peak and peak (R2 section A, first-party).
PRICE = {
    "in_hit_off": 0.003, "in_hit_peak": 0.006,
    "in_miss_off": 0.15, "in_miss_peak": 0.30,
    "out_off": 0.60, "out_peak": 1.20,
}


def token_cost(usage: dict, peak: bool = False) -> dict:
    """Cost from the provider's own token accounting, in both price regimes.

    Reported for both regimes deliberately: R2 measured peak at exactly 2x off-peak on
    every line, so publishing only the flattering one would be a choice the reader
    cannot audit.
    """
    hit = usage.get("prompt_cache_hit_tokens", 0) or 0
    miss = usage.get("prompt_cache_miss_tokens", 0) or 0
    out = usage.get("completion_tokens", 0) or 0
    reasoning = ((usage.get("completion_tokens_details") or {})
                 .get("reasoning_tokens", 0) or 0)

    def cost(regime: str) -> float:
        return (hit * PRICE[f"in_hit_{regime}"]
                + miss * PRICE[f"in_miss_{regime}"]
                + out * PRICE[f"out_{regime}"]) / 1e6

    return {
        "off_peak_usd": cost("off"),
        "peak_usd": cost("peak"),
        "cache_hit_tokens": hit,
        "cache_miss_tokens": miss,
        "completion_tokens": out,
        "reasoning_tokens": reasoning,
        "cache_hit_rate": (hit / (hit + miss)) if (hit + miss) else None,
    }


@dataclass
class LLMResponse:
    text: str
    reasoning: str | None
    latency_ms: float
    usage: dict
    cost: dict
    finish_reason: str | None
    model: str | None
    logprobs: list | None = None
    raw_status: int | None = None
    error: str | None = None


def _post(body: dict, timeout_s: int = 180) -> tuple[int, dict]:
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key()}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:600]
        try:
            return exc.code, json.loads(detail)
        except Exception:
            return exc.code, {"error": detail}


def chat(messages: list[dict], *, effort: str = "none", json_mode: bool = False,
         logprobs: bool = False, top_logprobs: int = 20, max_tokens: int | None = None,
         temperature: float | None = None, timeout_s: int = 180) -> LLMResponse:
    """One completion. `effort="none"` is non-thinking, which is REQUIRED for sampling."""
    body: dict = {"model": MODEL, "messages": messages}
    if effort == "none":
        body["thinking"] = {"type": "disabled"}
    else:
        body["thinking"] = {"type": "enabled", "reasoning_effort": effort}
        # temperature has no effect in thinking mode; omit it rather than imply control
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    if logprobs:
        body["logprobs"] = True
        body["top_logprobs"] = max(0, min(20, top_logprobs))
    if max_tokens:
        body["max_tokens"] = max_tokens
    if temperature is not None and effort == "none":
        body["temperature"] = temperature

    t0 = time.perf_counter()
    status, payload = _post(body, timeout_s=timeout_s)
    lat = (time.perf_counter() - t0) * 1000.0

    if status != 200:
        return LLMResponse("", None, lat, {}, {}, None, None, raw_status=status,
                           error=json.dumps(payload)[:400])
    ch = (payload.get("choices") or [{}])[0]
    msg = ch.get("message") or {}
    usage = payload.get("usage") or {}
    lp = None
    if logprobs and ch.get("logprobs"):
        lp = (ch["logprobs"] or {}).get("content")
    return LLMResponse(
        text=msg.get("content") or "",
        reasoning=msg.get("reasoning_content"),
        latency_ms=lat,
        usage=usage,
        cost=token_cost(usage),
        finish_reason=ch.get("finish_reason"),
        model=payload.get("model"),
        logprobs=lp,
        raw_status=status,
    )


# --------------------------------------------------------------- the four LLM arms
# Each builds a prompt for the SAME question shape the typed judges received, so the
# comparison is of judges rather than of prompt styles. R16's mandatory anti-straw-man
# package: prose / forced-choice / logit / self-consistency, with the best variant as
# the headline.

def prompt_prose(state: str, instructions: str, criteria: dict[str, str]) -> list[dict]:
    """A0: free prose self-assessment, the way an agent actually behaves."""
    opts = "\n".join(f"- {k}: {v}" for k, v in criteria.items())
    return [
        {"role": "system", "content":
         "You are reviewing a piece of work. Think it through, then state your answer "
         "and how confident you are in ordinary prose."},
        {"role": "user", "content":
         f"STATE:\n{state}\n\nQUESTION: {instructions}\n\nOPTIONS:\n{opts}\n\n"
         f"Answer in prose."},
    ]


def prompt_forced_choice(state: str, instructions: str,
                         criteria: dict[str, str], declare_boundary: bool = True) -> list[dict]:
    """A1: the honest rung. A single label and a stated probability, JSON-constrained.

    The boundary sentence mirrors the typed services' semantics so that the LLM is not
    disadvantaged by an unstated boundary that the typed judges are given.
    """
    opts = "\n".join(f"- {k}: {v}" for k, v in criteria.items())
    boundary = ("\nNote: something is only supported if the STATE actually says so. "
                "Absence of a statement is NOT evidence for it.\n"
                if declare_boundary else "")
    return [
        {"role": "system", "content":
         "You answer multiple-choice questions about a supplied state. Reply with JSON "
         'only, exactly: {"label": "<one of the option keys>", "prob": <0..1>} '
         "where prob is your probability that the chosen label is correct. "
         "No other keys, no explanation."},
        {"role": "user", "content":
         f"STATE:\n{state}\n\nQUESTION: {instructions}\n{boundary}\nOPTIONS:\n{opts}\n\n"
         f"Reply with JSON only."},
    ]


def prompt_logit(state: str, instructions: str, criteria: dict[str, str]) -> list[dict]:
    """The logit-style readout: one letter, so top_logprobs can be read off it.

    R16 verified logprobs are supported, so this rung is real rather than hypothetical.
    A single-token answer is required for the logprob to be about the choice itself.
    """
    letters = {chr(65 + i): k for i, k in enumerate(criteria)}
    opts = "\n".join(f"{L}. {criteria[k]}" for L, k in letters.items())
    return [
        {"role": "system", "content":
         "You answer multiple-choice questions about a supplied state. "
         "Reply with exactly one letter and nothing else."},
        {"role": "user", "content":
         f"STATE:\n{state}\n\nQUESTION: {instructions}\n\nOPTIONS:\n{opts}\n\n"
         f"Reply with the single letter only."},
    ]


def parse_label(resp: LLMResponse, criteria: dict[str, str]) -> str | None:
    """Extract the chosen key. Returns None rather than guessing.

    ORDER MATTERS, and getting it wrong produced a real error in this project: an
    earlier version tried the single-letter branch BEFORE looking for the option key, so
    a prose answer of "the answer is **47 minutes**, corresponding to revision 3" -- which
    names the value but not the key -- hit the letter branch, matched the "4" of "47" as
    index 3, and returned the WRONG key. That made the prose arm look like 0.50 accuracy
    when the model had actually answered correctly in prose.

    So the order is now most-specific-first: explicit JSON, then the literal key, then a
    key named in prose ("option k04", "answer is k04"), then the value text, and only
    then a single letter. Each branch is only reachable when the earlier ones failed, so
    a wrong-but-confident match is much harder to produce.
    """
    if not resp.text:
        return None
    t = resp.text.strip()
    keys = list(criteria)

    # 1. JSON form
    try:
        obj = json.loads(t)
        lab = obj.get("label")
        if isinstance(lab, str) and lab in criteria:
            return lab
    except Exception:
        pass

    # 2. the literal key anywhere
    for k in keys:
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(k)}(?![0-9])", t):
            return k

    # 3. the option VALUE appearing verbatim -- the model often answers in words
    for k, v in criteria.items():
        if v and v in t:
            return k

    # 4. a letter, but only as a standalone token or after an explicit cue
    m = re.search(r"\b(?:option|answer is|choose)\s*\(?([A-Za-z])\)?\b", t, re.I)
    if m:
        idx = ord(m.group(1).upper()) - 65
        if 0 <= idx < len(keys):
            return keys[idx]
    m = re.fullmatch(r"\s*\(?([A-Za-z])\)?[.)]?\s*", t)
    if m:
        idx = ord(m.group(1).upper()) - 65
        if 0 <= idx < len(keys):
            return keys[idx]
    return None


def parse_prob(resp: LLMResponse) -> float | None:
    try:
        obj = json.loads(resp.text.strip())
        p = obj.get("prob")
        return float(p) if isinstance(p, (int, float)) else None
    except Exception:
        return None


if __name__ == "__main__":
    r = chat([{"role": "user", "content": "Reply with the single word: ready"}],
             effort="none", max_tokens=16)
    print("status:", r.raw_status, "model:", r.model, "finish:", r.finish_reason)
    print("text:", repr(r.text[:80]))
    print("latency_ms:", round(r.latency_ms, 1))
    print("cost:", json.dumps(r.cost, indent=2))
    if r.error:
        print("ERROR:", r.error)
