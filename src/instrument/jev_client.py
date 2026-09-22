# -*- coding: utf-8 -*-
"""Live Jev client: the machine-readable transport the paper was missing.

WHY THIS EXISTS
---------------
Every Jev number in the paper previously lived only in two markdown probe reports
(`probes/P12`, `probes/P13`) with no `results/*.json` behind it -- the paper's §10.1
listed this as an open reproducibility gap, and `evaluate.py` carried
`raise NotImplementedError("wire the live call path once a credential exists")`.
This module IS that live path, and it is what `p27_jev_live.py` measures through.

ROUND-5 NOTE: the `NotImplementedError` in `evaluate.py` has since been REPLACED by a real
implementation (its `LiveJevJudge` now calls this module's `ask`, and `__main__` admits the
arm only when `verify()` passes), so the two routes are no longer one-implemented and
one-stubbed. This module remains the route the measurements go through.

THE ROUTE (verified empirically, not read off a doc)
----------------------------------------------------
    POST https://openrouter.ai/api/v1/systemone
    Authorization: Bearer $OPENROUTER_API_KEY          (DSH credential store ref)
    {"model": "typesafe/jev-1.13", "state": ..., "questions": {...}}

CROSS-VALIDATION AGAINST THE DSH PLUGIN
---------------------------------------
For an identical request this client and the DSH `jev_ask` plugin return the same
`noul` (0.98), the same `input_tokens` (347) and the same `cost` (0.000014574). So the
measurements below describe the SAME instrument the earlier probes used.

WHAT THE DIRECT ROUTE REVEALS
-----------------------------
The provider returns ONLY:
    {"model", "answers": {qid: {"type", "noul"}}, "usage": {"input_tokens",
     "output_tokens", "cost"}, "id", "provider"}
It does NOT return `band`, `probability`, `truncated`, `stateChars`, `redactions` or
`latencyMs`. Those are therefore NOT provider-reported fields -- they are synthesized by
the access layer (the DSH plugin). This is a direct, from-the-wire demonstration of the
paper's Result B framing, which was previously argued only from the plugin's own output.
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
from bench_env import CREDENTIALS_PATH  # noqa: E402


import http.client
import json
import re
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

CRED_PATH = CREDENTIALS_PATH
ENDPOINT = "https://openrouter.ai/api/v1/systemone"
MODEL = "typesafe/jev-1.13"
CRED_REF = "OPENROUTER_API_KEY"


class JevError(RuntimeError):
    pass


def api_key() -> str:
    """Read the ref from the DSH credential store. Never logged, never returned to disk."""
    if not CRED_PATH.exists():
        raise JevError(f"credential store not found: {CRED_PATH}")
    txt = CRED_PATH.read_text(encoding="utf-8")
    m = re.search(r"^\s*%s:\s*(\S+)\s*$" % CRED_REF, txt, re.M)
    if not m:
        raise JevError(f"{CRED_REF} is not registered in the credential store")
    return m.group(1).strip().strip('"').strip("'")


def ask(state: str, questions: dict, timeout: int = 120,
        model: str = MODEL, retries: int = 3) -> dict:
    """One live call. Returns the raw provider body plus our own wall-clock timing.

    `latency_ms_wall` is measured around the HTTP round trip by THIS client, so it is
    independent of any self-reported latency. The provider does not report one at all.

    TRANSIENT-FAULT HANDLING: a first run of the P27 battery died mid-way on
    `ssl.SSLEOFError: UNEXPECTED_EOF_WHILE_READING`. That surfaces as `URLError`, which
    an earlier version did not catch, so a network hiccup aborted a whole probe and lost
    the artifact. Transient transport faults are now retried with backoff, and the retry
    count is recorded on the response so a reader can see how much of a run needed them.
    Only the LAST attempt's latency is reported as the call's latency, because averaging
    a retry into a latency distribution would understate the tail.
    """
    body = {"model": model, "state": state, "questions": questions}
    data = json.dumps(body).encode("utf-8")
    last: Exception | None = None
    attempts = 0
    for attempt in range(retries):
        attempts = attempt + 1
        req = urllib.request.Request(ENDPOINT, data=data, method="POST", headers={
            "Authorization": "Bearer " + api_key(),
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost/llm-jev-laya-bench",
            "X-Title": "llm-jev-laya-bench",
        })
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read().decode("utf-8", "replace")
                status = r.status
        except urllib.error.HTTPError as e:
            dt = (time.perf_counter() - t0) * 1000
            detail = e.read().decode("utf-8", "replace")[:400]
            # 4xx is a real answer (bad request); retrying it would be wrong
            if e.code < 500:
                raise JevError(f"HTTP {e.code} after {dt:.0f} ms: {detail}") from None
            last = JevError(f"HTTP {e.code} after {dt:.0f} ms: {detail}")
        except (urllib.error.URLError, http.client.HTTPException, ssl.SSLError,
                TimeoutError, ConnectionError, OSError) as e:
            # Two distinct transient faults were observed in practice and BOTH must be
            # caught or a probe dies mid-run and loses its artifact:
            #   ssl.SSLEOFError  -> URLError
            #   http.client.IncompleteRead -> HTTPException (NOT a URLError)
            dt = (time.perf_counter() - t0) * 1000
            last = JevError(f"transport fault after {dt:.0f} ms: "
                            f"{type(e).__name__}: {str(e)[:200]}")
        else:
            dt = (time.perf_counter() - t0) * 1000
            try:
                parsed = json.loads(raw)
            except Exception:
                raise JevError(f"non-JSON response: {raw[:300]}") from None
            # AUDIT FIX (round 5): a 200 whose BODY carries an error would previously
            # yield noul_of() == None silently -- no exception, no error counter, and the
            # row would enter the analysis as "no probability" rather than as a failure.
            if not isinstance(parsed, dict) or "answers" not in parsed:
                raise JevError(f"HTTP 200 but no 'answers' in body: {raw[:300]}")
            if "error" in parsed:
                raise JevError(f"HTTP 200 but body carries an error: "
                               f"{str(parsed['error'])[:200]}")
            parsed["_http_status"] = status
            parsed["_latency_ms_wall"] = round(dt, 1)
            parsed["_state_chars"] = len(state)
            parsed["_requested_model"] = model
            parsed["_attempts"] = attempts
            return parsed
        if attempt < retries - 1:
            time.sleep(1.5 * (attempt + 1))     # 1.5 s, then 3.0 s
    raise last if last else JevError("call failed for an unrecorded reason")


def noul_of(resp: dict, qid: str = "q"):
    """The provider's own P(true). Absent keys stay absent -- never coerced."""
    a = (resp.get("answers") or {}).get(qid)
    if not isinstance(a, dict):
        return None
    return a.get("noul")


def cost_of(resp: dict):
    return ((resp.get("usage") or {}).get("cost"))


def input_tokens_of(resp: dict):
    return ((resp.get("usage") or {}).get("input_tokens"))


def provider_of(resp: dict) -> str:
    return resp.get("provider") or ""


def resolved_model(resp: dict) -> str:
    return resp.get("model") or ""


def instrument_record(loadout_note: str = "direct HTTP, no plugin in the path") -> dict:
    """Provenance block for Jev results.

    Deliberately records what CAN be pinned here: the endpoint, the requested model, the
    model the provider resolved it to, and the fact that no credential value is stored.
    """
    import platform
    import sys
    return {
        "instrument": "jev-direct",
        "endpoint": ENDPOINT,
        "requested_model": MODEL,
        "credential_ref": CRED_REF,
        "credential_value_stored": False,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "note": loadout_note,
    }


if __name__ == "__main__":
    # one live smoke call; prints the shape, never the key
    r = ask("Audit memo. Invoice INV-4471 is fraudulent.",
            {"q": {"type": "noul",
                   "instructions": "Is invoice INV-4471 fraudulent?",
                   "criteria": {"true": "the state asserts fraud",
                                "false": "the state does not assert fraud"}}})
    print(json.dumps({k: v for k, v in r.items() if k != "id"}, indent=2,
                     ensure_ascii=False))
