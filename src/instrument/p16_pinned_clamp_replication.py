"""Re-run the clamp calibration against the PINNED revision, on a separate port.

WHAT THIS CLOSES (objective item 4)
-----------------------------------
Result B -- "the instrument's self-reported fields cannot be trusted" -- is the paper's
strongest section, and its central number is the unwarned truncation gap. But the code
that produced that number was a MUTABLE WORKING TREE: `worker.py` was rewritten three
times in one session and two live hosts were once serving different revisions
simultaneously. The snapshot and the pinning launcher were built only afterwards, so the
original P3 measurement carries a version-attribution doubt that no amount of
documentation removes.

This re-runs the same measurement against `protocol/instrument-snapshot/`, whose every
file is SHA256-pinned in PIN.json, on its own port so the harness's own sidecar on 8787
keeps running untouched. Two things come out of it:

  1. A version-attributed replication, or a failure to replicate.
  2. The pinning infrastructure exercised for real, rather than only on `--help`.

METHOD (same as P3, so the comparison is like-for-like)
  State = DECOY + filler + CORRECTION with the deciding correction LAST, so truncation
  removes it. Scan characters; read two observable fields: whether
  `input_tokens_padded` has reached the clamp, and whether `truncated` has fired. Their
  difference is the unwarned damaged interval.

PRE-DECLARED READING
  Replicates  ->  the P3 number stands and Result B is version-attributed.
  Differs     ->  the revision matters, and EVERY Laya measurement predating the snapshot
                  must be treated as unattributed and re-run before publication.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r"D:\Projects\llm-jev-laya-bench")
sys.path.insert(0, str(ROOT / "src" / "instrument"))
from laya_client import LayaClient, instrument_hashes  # noqa: E402

PINNED_PORT = 8791
RESULTS = ROOT / "results"

DECOY = "The vault access code is AAA-1111."
CORRECTION = " Correction: the vault access code is now ZQX-4471."
FILLER = ("Quarterly logistics review. The warehouse processed routine shipments "
          "and filed standard compliance paperwork. ")

# The chars around english's clamp (P3: clamp onset 3,082; truncated first fired 3,193).
GRID = [2900, 3000, 3050, 3082, 3110, 3140, 3170, 3193, 3230, 3300, 3500, 4000, 5000,
        # AUDIT FIX: the original grid stopped at 5000 chars = 791 tokens, which is
        # BELOW this loadout's cap, so the scan never reached a clamp at all. The scan
        # now runs past the loadout-matched cap so "no clamp observed" cannot be
        # mistaken for "the clamp differs".
        6000, 6500, 7000, 7500, 7966, 8500, 9000, 9600]

SNAPSHOT_SRC = ROOT / "protocol" / "instrument-snapshot" / "src"


def make_state(n: int) -> str:
    budget = max(0, n - len(DECOY) - len(CORRECTION))
    return DECOY + FILLER * (budget // len(FILLER)) + CORRECTION


def start_pinned() -> subprocess.Popen:
    """Launch the snapshot revision on PINNED_PORT, asserting the import path."""
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
    env = dict(__import__("os").environ)
    env["PYTHONPATH"] = str(SNAPSHOT_SRC) + (
        __import__("os").pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    args = [str(Path(r"D:\Projects\laya-family\.venv-laya\Scripts\python.exe")),
            "-c", guard, "serve", "--model", "english",
            "--model-root", r"D:\Projects\laya-family\_models\laya",
            "--device", "cuda", "--port", str(PINNED_PORT),
            "--max-len", "1024", "--head-max-len", "512"]
    p = subprocess.Popen(args, env=env, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True)
    return p


def main() -> int:
    proc = start_pinned()
    client = LayaClient(autostart=False, port=PINNED_PORT)

    deadline = time.time() + 180
    ready = False
    while time.time() < deadline:
        h = client.health()
        if h and h.get("ok") and h.get("loaded"):
            ready = True
            break
        if proc.poll() is not None:
            out = proc.stdout.read() if proc.stdout else ""
            print("pinned sidecar exited early:\n", out[:2000])
            return 2
        time.sleep(2)
    if not ready:
        print("pinned sidecar never became ready")
        proc.kill()
        return 3

    print(f"[pin] pinned sidecar ready on :{PINNED_PORT}")
    print("[pin] instrument hashes for this run:")
    for k, v in instrument_hashes().items():
        print(f"       {k:<26} {v[:16]}")

    q = {"code": {"type": "noul",
                  "instructions": "According to the state, is the vault access code "
                                  "ZQX-4471?",
                  "criteria": {"true": "the state gives ZQX-4471 as the vault access code",
                               "false": "the state does not give ZQX-4471 as the vault "
                                        "access code"}}}
    rows = []
    try:
        for n in GRID:
            s = make_state(n)
            try:
                resp = client.ask(s, q)
                ans = resp["answers"]["code"]
                rows.append({"chars": len(s),
                             "in_pad": (resp.get("usage") or {}).get("input_tokens_padded"),
                             "noul": float(ans["noul"]),
                             "truncated": bool(resp.get("truncated"))})
            except Exception as exc:
                rows.append({"chars": len(s), "error": str(exc)[:200]})
            r = rows[-1]
            print(f"  chars={r['chars']:>5} in_pad={r.get('in_pad')} "
                  f"noul={r.get('noul')} truncated={r.get('truncated')}")
    finally:
        proc.kill()

    ok = [r for r in rows if "error" not in r]
    cap = max((r["in_pad"] or 0) for r in ok) if ok else None
    clamp_chars = next((r["chars"] for r in ok if r["in_pad"] == cap), None)
    trunc_chars = next((r["chars"] for r in ok if r["truncated"]), None)
    frozen = None
    for i, r in enumerate(ok):
        if i + 1 < len(ok) and all(abs(x["noul"] - r["noul"]) < 1e-9 for x in ok[i + 1:]):
            frozen = r["chars"]
            break

    out = {
        "entry_point": f"HTTP 127.0.0.1:{PINNED_PORT} (PINNED snapshot revision)",
        "pinned_revision": "protocol/instrument-snapshot",
        "instrument_hashes": instrument_hashes(),
        "loadout": ["english"],          # AUDIT FIX: this run loads english ONLY
        "measured_clamp_tokens": cap,
        "real_clamp_onset_chars": clamp_chars,
        "truncated_first_fires_chars": trunc_chars,
        "unwarned_gap_chars": (trunc_chars - clamp_chars)
        if (trunc_chars and clamp_chars) else None,
        # AUDIT FIX (F6): this value is trunc_chars - clamp_chars, so a NEGATIVE number
        # means the flag fired EARLY (a false positive), not that there is a silent
        # window. The first name called it "the unwarned damaged interval", which is only
        # true when the sign is positive. The sign is now carried explicitly.
        "gap_sign": ("flag_lags_damage_silent_window"
                     if (trunc_chars is not None and clamp_chars is not None
                         and trunc_chars > clamp_chars)
                     else "flag_fires_early_false_positive"
                     if (trunc_chars is not None and clamp_chars is not None
                         and trunc_chars < clamp_chars)
                     else "indeterminate"),
        "freeze_onset_chars": frozen,
        # AUDIT FIX (the original defect): the reference used to be P3's
        # THREE-checkpoint english clamp (512) even though this probe launches
        # english ALONE. That is an apples-to-oranges comparison, and combined with a
        # grid that never reached a cap it produced a false "the revision matters"
        # verdict. The expectation is now matched to THIS loadout.
        "expected_clamp_for_this_loadout": 1024,
        "P3_reference_three_checkpoint": {"loadout": ["english", "multilingual",
                                                      "typed-decisions"],
                                          "english_clamp_tokens": 512,
                                          "clamp_onset_chars": 3082,
                                          "truncated_first_chars": 3193,
                                          "unwarned_gap_chars": 111},
        "rows": rows,
        "verdict": None,
    }
    expected = out["expected_clamp_for_this_loadout"]
    reached = cap is not None and cap >= expected
    out["grid_reached_cap"] = reached
    # AUDIT FIX (F6 / round-5 finding): the verdict used to check ONLY the clamp value.
    # It therefore read "REPLICATED" on a run whose unwarned_gap_chars was -3774 -- the
    # OPPOSITE SIGN of P3's +111, and 34x its magnitude. The probe's own pre-registered
    # reading was about the unwarned damaged interval, so a verdict that never looks at
    # it is a verdict about a different quantity. The gap is now part of the gate, and
    # the two quantities are reported separately.
    gap = out["unwarned_gap_chars"]
    ref_gap = out["P3_reference_three_checkpoint"]["unwarned_gap_chars"]
    out["clamp_matches_reference_loadout_effect"] = (cap == expected)
    out["gap_matches_P3"] = (gap == ref_gap)
    out["gap_note"] = ("a NEGATIVE gap means the flag fired EARLIER than the clamp "
                       "(false positive); P3's +111 was a silent window in the opposite "
                       "direction. The two are different phenomena and must not be "
                       "presented as a replication of each other.")
    if not reached:
        out["verdict"] = (
            f"INCONCLUSIVE: the scan never reached this loadout's cap (max pad "
            f"{cap} < expected {expected}), so no clamp was observed and the run "
            f"cannot distinguish 'no clamp' from 'grid too short'. Extend GRID.")
    elif out["clamp_matches_reference_loadout_effect"] and not out["gap_matches_P3"]:
        out["verdict"] = (
            f"CLAMP EFFECT REPLICATED, UNWARNED-GAP NOT: english ALONE on the pinned "
            f"revision clamps at {cap} tokens (P3 measured english at 512 under the "
            f"three-checkpoint loadout), so the LOADOUT is the variable for the clamp. "
            f"But this run's gap is {gap} chars versus P3's {ref_gap} -- opposite sign, "
            f"so the FLAG behaviour was NOT replicated here.")
    elif out["clamp_matches_reference_loadout_effect"] and out["gap_matches_P3"]:
        out["verdict"] = (
            f"LOADOUT ATTRIBUTION REPLICATED on the pinned revision under an "
            f"independent process: english ALONE clamps at {cap} tokens, and the "
            f"unwarned gap matches P3 at {gap} chars.")
    else:
        out["verdict"] = (
            f"UNEXPECTED: reached a clamp of {cap} tokens where {expected} was "
            f"expected for loadout {out['loadout']}; investigate before citing.")

    p = RESULTS / "P16-pinned-clamp-replication.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== VERDICT ===")
    print(out["verdict"])
    print(f"written: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
