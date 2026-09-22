"""ATTRIBUTION TEST: does the clamp difference come from the REVISION or from the
LAUNCH ARGUMENTS?

WHY THIS EXISTS
---------------
P16 re-ran the clamp calibration against the pinned snapshot revision and found NO clamp
at 512: `input_tokens_padded` reached 791 and kept growing, where P3 (on the then-current
working tree) had reported a hard 512 clamp with an 111-character silent window. That
looked like a revision effect, and the obvious conclusion would be "the revision matters,
re-run everything pre-snapshot".

But P16 and P3 did not launch identically. P3 started the sidecar with
`--model english --also multilingual --also typed-decisions`; P16 started it with
`--model english` only. A difference in loaded checkpoints can change resident-model
handling and therefore the budget that is actually enforced, so the two runs confound
revision with arguments -- the same class of mistake as attributing a truncated answer to
a model when the cause was the serializer.

This runs the pinned revision with P3's EXACT argument set. The logic is a 2x2:

                        P3 args                 P16 args
    P3 revision     512 clamp (measured)      (not run)
    P16 revision    ?  <-- THIS RUN           no clamp (measured)

  If the pinned revision WITH P3's args also fails to clamp -> the difference is the
  REVISION, and pre-snapshot Laya measurements must be re-run.
  If it clamps at 512 again -> the difference was the ARGUMENTS, not the code, and the
  P3 result stands as measured (with the argument set recorded).
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
from bench_env import MODEL_ROOT, VENV_PYTHON  # noqa: E402


import json
import os
import subprocess
import sys
import time
from pathlib import Path


sys.path.insert(0, str(ROOT / "src" / "instrument"))
from laya_client import LayaClient, instrument_hashes  # noqa: E402

PORT = 8792
RESULTS = ROOT / "results"
SNAPSHOT_SRC = ROOT / "protocol" / "instrument-snapshot" / "src"

DECOY = "The vault access code is AAA-1111."
CORRECTION = " Correction: the vault access code is now ZQX-4471."
FILLER = ("Quarterly logistics review. The warehouse processed routine shipments "
          "and filed standard compliance paperwork. ")
# Distinct character counts only: indexing the filler by count avoids the duplicate
# grid points that made P16's output look denser than it was.
GRID = [2800, 2950, 3050, 3100, 3150, 3200, 3300, 3500, 4000, 5000, 6500, 8000]


def make_state(n: int) -> str:
    # round DOWN to a whole number of filler blocks so the grid has no collisions, then
    # trim the remainder off the END of the filler so CORRECTION still sits last
    payload = max(0, n - len(DECOY) - len(CORRECTION))
    blocks = payload // len(FILLER)
    return DECOY + FILLER * blocks + CORRECTION


def launch(args: list[str]) -> subprocess.Popen:
    guard = (
        "import sys, os\n"
        "sys.modules.pop('laya_mcp', None)\n"
        "import laya_mcp\n"
        f"snap = os.path.normcase(r'{SNAPSHOT_SRC}')\n"
        "got = os.path.normcase(os.path.dirname(laya_mcp.__file__))\n"
        "if not got.startswith(snap):\n"
        "    raise SystemExit('WRONG REVISION: ' + got)\n"
        "print('[pin] ' + got, flush=True)\n"
        "from laya_mcp.cli import main\n"
        "sys.exit(main())\n"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SNAPSHOT_SRC) + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return subprocess.Popen(
        [str(VENV_PYTHON), "-c", guard, *args],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


ARGSETS = {
    "p3_args_three_checkpoints": [
        "serve", "--model", "english", "--also", "multilingual",
        "--also", "typed-decisions",
        "--model-root", str(MODEL_ROOT),
        "--device", "cuda", "--port", str(PORT),
        "--max-len", "1024", "--head-max-len", "512"],
    "p16_args_english_only": [
        "serve", "--model", "english",
        "--model-root", str(MODEL_ROOT),
        "--device", "cuda", "--port", str(PORT),
        "--max-len", "1024", "--head-max-len", "512"],
}

Q = {"code": {"type": "noul",
              "instructions": "According to the state, is the vault access code ZQX-4471?",
              "criteria": {"true": "the state gives ZQX-4471 as the vault access code",
                           "false": "the state does not give ZQX-4471 as the vault "
                                    "access code"}}}


def measure(args: list[str], label: str) -> dict:
    proc = launch(args)
    client = LayaClient(autostart=False, port=PORT)
    deadline = time.time() + 240
    while time.time() < deadline:
        h = client.health()
        if h and h.get("ok") and h.get("loaded"):
            break
        if proc.poll() is not None:
            return {"argset": label, "error": "sidecar exited: "
                    + (proc.stdout.read() if proc.stdout else "")[:600]}
        time.sleep(2)
    else:
        proc.kill()
        return {"argset": label, "error": "never ready"}

    health = client.health()
    rows = []
    try:
        for n in GRID:
            s = make_state(n)
            try:
                resp = client.ask(s, Q)
                ans = resp["answers"]["code"]
                rows.append({"chars": len(s),
                             "in_pad": (resp.get("usage") or {}).get("input_tokens_padded"),
                             "noul": float(ans["noul"]),
                             "truncated": bool(resp.get("truncated"))})
            except Exception as exc:
                rows.append({"chars": len(s), "error": str(exc)[:200]})
    finally:
        proc.kill()
    time.sleep(2)

    ok = [r for r in rows if "error" not in r]
    cap = max((r["in_pad"] or 0) for r in ok) if ok else None
    clamp_chars = next((r["chars"] for r in ok if r["in_pad"] == cap), None)
    trunc_chars = next((r["chars"] for r in ok if r["truncated"]), None)
    return {
        "argset": label,
        "checkpoints_loaded": list((health.get("checkpoints") or {}).keys()),
        "measured_clamp_tokens": cap,
        "real_clamp_onset_chars": clamp_chars,
        "truncated_first_fires_chars": trunc_chars,
        "unwarned_gap_chars": (trunc_chars - clamp_chars)
        if (trunc_chars and clamp_chars) else None,
        "clamped_at_512": cap == 512,
        "rows": rows,
    }


if __name__ == "__main__":
    out = {"instrument_hashes": instrument_hashes(), "runs": {}}
    for label, args in ARGSETS.items():
        print(f"\n=== {label} ===")
        res = measure(args, label)
        out["runs"][label] = res
        for r in res.get("rows", []):
            print(f"  chars={r['chars']:>5} in_pad={r.get('in_pad')} "
                  f"noul={r.get('noul')} truncated={r.get('truncated')}")
        print(f"  -> clamp={res.get('measured_clamp_tokens')} "
              f"onset={res.get('real_clamp_onset_chars')} "
              f"trunc@{res.get('truncated_first_fires_chars')} "
              f"clamped_at_512={res.get('clamped_at_512')}")

    a = out["runs"]["p3_args_three_checkpoints"].get("clamped_at_512")
    b = out["runs"]["p16_args_english_only"].get("clamped_at_512")
    if a and not b:
        out["verdict"] = ("ARGUMENTS, NOT REVISION: with three checkpoints loaded the "
                          "pinned revision clamps at 512 exactly as P3 measured; with one "
                          "it does not. The clamp depends on the loaded checkpoint set, so "
                          "P3's result stands WITH its argument set recorded.")
    elif not a and not b:
        out["verdict"] = ("REVISION: the pinned revision does not clamp at 512 under "
                          "either argument set, so P3's 512 measurement came from a "
                          "different revision and pre-snapshot Laya results must be re-run.")
    elif a and b:
        out["verdict"] = ("NO DIFFERENCE: both argument sets clamp at 512, so P16's "
                          "no-clamp finding was caused by something else not controlled "
                          "here and must be investigated before it is reported.")
    else:
        out["verdict"] = "INCONCLUSIVE: inspect the rows"

    p = RESULTS / "P17-clamp-attribution.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== VERDICT ===")
    print(out["verdict"])
    print(f"written: {p}")
