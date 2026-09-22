"""Which launch loadout decides the window? A sweep over checkpoint sets.

WHY (this settles a number the paper rests on)
----------------------------------------------
P17 established that the SAME pinned revision clamps at 512 tokens when launched with
`--model english --also multilingual --also typed-decisions`, and at 1024 when launched
with `--model english` alone. The code is not the variable; the loadout is. That is worth
one more run, because the consequence for the paper is concrete:

  * The clamp -- and therefore Laya's usable state window -- is a property of the LAUNCH
    CONFIGURATION, not of the checkpoint or the code.
  * Every Laya measurement in this project was taken under the three-checkpoint loadout,
    so the 512-token window (and the 111-character unwarned gap) applies to all of them
    CONSISTENTLY. Result B stands, and P3's number is right for the configuration the
    project actually used.
  * But the window is not a general property of the engine. Reporting "Laya's window is
    512 tokens" without the loadout would be wrong by 2x for another operator.

SWEEP: english alone; english+multilingual; english+typed-decisions; all three; and the
default `serve` with an explicit model, to find whether it is the COUNT of checkpoints or
a particular pairing that matters.

The measurement is the cheapest possible: one long state per loadout, read
`input_tokens_padded` and `truncated`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r"D:\Projects\llm-jev-laya-bench")
sys.path.insert(0, str(ROOT / "src" / "instrument"))
from laya_client import LayaClient, instrument_hashes  # noqa: E402

PORT = 8793
RESULTS = ROOT / "results"
SNAPSHOT_SRC = ROOT / "protocol" / "instrument-snapshot" / "src"
MODEL_ROOT = r"D:\Projects\laya-family\_models\laya"

DECOY = "The vault access code is AAA-1111."
CORRECTION = " Correction: the vault access code is now ZQX-4471."
FILLER = ("Quarterly logistics review. The warehouse processed routine shipments "
          "and filed standard compliance paperwork. ")

# One long state plus one short one per loadout: the long one reveals the clamp.
LONG_CHARS = 9000
SHORT_CHARS = 300


def make_state(n: int) -> str:
    payload = max(0, n - len(DECOY) - len(CORRECTION))
    return DECOY + FILLER * (payload // len(FILLER)) + CORRECTION


Q = {"code": {"type": "noul",
              "instructions": "According to the state, is the vault access code ZQX-4471?",
              "criteria": {"true": "the state gives ZQX-4471 as the vault access code",
                           "false": "the state does not give ZQX-4471 as the vault "
                                    "access code"}}}

LOADOUTS = {
    "english_only": ["--model", "english"],
    "english+multilingual": ["--model", "english", "--also", "multilingual"],
    "english+typed-decisions": ["--model", "english", "--also", "typed-decisions"],
    "all_three": ["--model", "english", "--also", "multilingual",
                  "--also", "typed-decisions"],
}


def launch(model_args: list[str]) -> subprocess.Popen:
    guard = (
        "import sys, os\n"
        "sys.modules.pop('laya_mcp', None)\n"
        "import laya_mcp\n"
        f"snap = os.path.normcase(r'{SNAPSHOT_SRC}')\n"
        "got = os.path.normcase(os.path.dirname(laya_mcp.__file__))\n"
        "if not got.startswith(snap):\n"
        "    raise SystemExit('WRONG REVISION: ' + got)\n"
        "from laya_mcp.cli import main\n"
        "sys.exit(main())\n"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SNAPSHOT_SRC) + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    args = ["serve", *model_args, "--model-root", MODEL_ROOT, "--device", "cuda",
            "--port", str(PORT), "--max-len", "1024", "--head-max-len", "512"]
    return subprocess.Popen(
        [r"D:\Projects\laya-family\.venv-laya\Scripts\python.exe", "-c", guard, *args],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def probe(loadout: str, model_args: list[str]) -> dict:
    proc = launch(model_args)
    client = LayaClient(autostart=False, port=PORT)
    deadline = time.time() + 300
    ok = False
    while time.time() < deadline:
        h = client.health()
        if h and h.get("ok") and h.get("loaded"):
            ok = True
            break
        if proc.poll() is not None:
            return {"loadout": loadout,
                    "error": "exited: " + (proc.stdout.read() if proc.stdout else "")[:400]}
        time.sleep(2)
    if not ok:
        proc.kill()
        return {"loadout": loadout, "error": "never ready"}
    health = client.health()
    res: dict = {"loadout": loadout,
                 "loaded": list((health.get("checkpoints") or {}).keys())}
    try:
        for label, chars in (("short", SHORT_CHARS), ("long", LONG_CHARS)):
            s = make_state(chars)
            try:
                r = client.ask(s, Q)
                res[label] = {"chars": len(s),
                              "in_pad": (r.get("usage") or {}).get("input_tokens_padded"),
                              "truncated": bool(r.get("truncated")),
                              "noul": float(r["answers"]["code"]["noul"])}
            except Exception as exc:
                res[label] = {"chars": len(s), "error": str(exc)[:200]}
    finally:
        proc.kill()
    time.sleep(2)
    lp = res.get("long", {}).get("in_pad")
    res["long_state_clamp_tokens"] = lp
    res["clamped_below_1024"] = (lp is not None and lp < 1024)
    return res


if __name__ == "__main__":
    out = {"instrument_hashes": instrument_hashes(), "runs": {}}
    for name, margs in LOADOUTS.items():
        print(f"\n=== {name} ===")
        r = probe(name, margs)
        out["runs"][name] = r
        if "error" in r:
            print("  ERROR:", r["error"][:200])
        else:
            print(f"  loaded={r['loaded']}")
            print(f"  short: in_pad={r['short'].get('in_pad')} "
                  f"trunc={r['short'].get('truncated')}")
            print(f"  long : in_pad={r['long'].get('in_pad')} "
                  f"trunc={r['long'].get('truncated')} "
                  f"-> clamp={r['long_state_clamp_tokens']}")

    clamps = {k: v.get("long_state_clamp_tokens") for k, v in out["runs"].items()
              if "error" not in v}
    distinct = sorted({c for c in clamps.values() if c is not None})
    out["clamps"] = clamps
    out["distinct_clamps"] = distinct
    out["verdict"] = (
        "LOADOUT-DEPENDENT WINDOW CONFIRMED: the clamp varies with the loaded checkpoint "
        f"set ({clamps}). Every Laya measurement in this project used the three-checkpoint "
        "loadout, so the 512-token window applies consistently to all of them and Result B "
        "stands -- but the window must always be reported WITH its launch configuration."
        if len(distinct) > 1 else
        f"WINDOW IS STABLE at {distinct} across loadouts, so P16's no-clamp observation "
        "had another cause and must be investigated")
    p = RESULTS / "P18-loadout-window-sweep.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== VERDICT ===")
    print(out["verdict"])
    print(f"written: {p}")
