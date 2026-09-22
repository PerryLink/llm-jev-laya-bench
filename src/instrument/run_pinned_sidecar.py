"""Run the Laya sidecar from the FROZEN SNAPSHOT instead of the live working tree.

THE PROBLEM THIS SOLVES (issue 2 of the three the human asked me to resolve)
---------------------------------------------------------------------------
`laya_mcp` is an EDITABLE install pointing at D:\\Projects\\laya-family\\laya-mcp-pkg\\
src\\laya_mcp, i.e. the live development tree. During this project that tree was
rewritten under measurement: `worker.py` changed three times in one session, and at one
point two live hosts (an HTTP sidecar and the DSH-spawned stdio server) were serving two
DIFFERENT revisions simultaneously. All measurements therefore carried an attribution
risk that no amount of documentation fully removes, because the code being measured was
whatever happened to be on disk when a process started.

The fix is to stop measuring the working tree at all. `protocol/instrument-snapshot/`
holds a byte-frozen copy (13 .py files + 2 checkpoint configs, each SHA256'd in
PIN.json). This launcher makes the sidecar import from that snapshot and then PROVES it
did, so a measurement either runs on the pinned revision or refuses to run.

HOW IT PINS THE IMPORT
----------------------
`laya_mcp` is installed editable, so it is importable from the venv. This launcher runs
with PYTHONPATH=<snapshot>/src FIRST and additionally removes any already-resolved
`laya_mcp` from sys.modules, then asserts that `laya_mcp.__file__` lies inside the
snapshot. If it does not, the process exits rather than measuring the wrong code.

It also re-verifies the snapshot files against PIN.json before launching, so a corrupted
or edited snapshot is caught rather than silently trusted.
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
from bench_env import MODEL_ROOT, SNAPSHOT, VENV_PYTHON  # noqa: E402


import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


SNAP_SRC = SNAPSHOT / "src"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def verify_snapshot() -> tuple[bool, list[str]]:
    """Re-hash every snapshot file against PIN.json. A tampered snapshot must not run."""
    pin_path = SNAPSHOT / "PIN.json"
    if not pin_path.exists():
        return False, [f"missing {pin_path}"]
    pin = json.loads(pin_path.read_text(encoding="utf-8-sig"))
    problems: list[str] = []
    for entry in pin["files"]:
        p = SNAP_SRC / "laya_mcp" / entry["file"]
        if not p.exists():
            problems.append(f"missing {entry['file']}")
            continue
        got = sha256(p)
        if got != entry["sha256"]:
            problems.append(f"{entry['file']}: {got[:16]} != pinned {entry['sha256'][:16]}")
    return (not problems), problems


def launch(extra_args: list[str] | None = None) -> int:
    ok, problems = verify_snapshot()
    if not ok:
        print("SNAPSHOT VERIFICATION FAILED -- refusing to launch:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 2

    env = dict(os.environ)
    # Snapshot source first on the path, and keep the venv's site-packages available for
    # third-party dependencies.
    env["PYTHONPATH"] = os.pathsep.join(
        [str(SNAP_SRC)] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))

    # Guard program: drop any resolved laya_mcp, import it, and assert the snapshot won.
    # Written as a single literal so the quoting is unambiguous.
    guard = (
        "import sys, os\n"
        "sys.modules.pop('laya_mcp', None)\n"
        "import laya_mcp\n"
        f"snap = os.path.normcase(r'{SNAP_SRC}')\n"
        "got = os.path.normcase(os.path.dirname(laya_mcp.__file__))\n"
        "if not got.startswith(snap):\n"
        "    raise SystemExit('WRONG REVISION: laya_mcp resolved to ' + got)\n"
        "print('[pin] laya_mcp from', got, flush=True)\n"
        "from laya_mcp.cli import main\n"
        "sys.exit(main())\n"
    )

    args = [str(VENV_PYTHON), "-c", guard] + (extra_args or [
        "serve", "--model", "english", "--also", "multilingual",
        "--also", "typed-decisions", "--model-root", str(MODEL_ROOT),
        "--device", "cuda", "--port", "8787",
        "--max-len", "1024", "--head-max-len", "512",
    ])

    print(f"[pin] launching sidecar from pinned snapshot {SNAPSHOT.name}")
    return subprocess.call(args, env=env)


if __name__ == "__main__":
    sys.exit(launch(sys.argv[1:] or None))
