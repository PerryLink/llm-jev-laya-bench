"""Central environment resolution for the benchmark.

WHY THIS EXISTS
---------------
Every probe script used to hardcode its own absolute paths:

    ROOT = Path(r"D:\\Projects\\llm-jev-laya-bench")
    MODEL_ROOT = Path(r"D:\\Projects\\laya-family\\_models\\laya")
    CRED_PATH = Path(r"C:\\Users\\zzhdz\\.dsh\\.credentials.yaml")

61 such literals across 48 files. The consequence was that a reader who cloned the
repository could not run a single script: the paths named one particular machine and one
particular user's home directory. That is a reproducibility defect of exactly the kind this
project exists to document -- the artifact silently encoded an assumption about its
environment that was never stated.

WHAT IT RESOLVES
----------------
  ROOT          this repository, found by walking up from this file (no configuration)
  RESULTS       ROOT/results, and the other in-repo directories
  LAYA_ROOT     the sibling `laya-family` checkout that holds the sidecar, venv and models
  VENV_PYTHON   the Python interpreter that can import `laya_mcp`
  MODEL_ROOT    the directory holding the three checkpoint snapshots
  CREDENTIALS   the DSH credential store (read-only; values are never logged)
  LAYA_WORKTREE the mutable sidecar source tree (hashed, for drift detection)

Everything except ROOT is overridable by environment variable, and every default is
printed by `python bench_env.py` so a reader can see exactly what was resolved.

ON DEFAULTS
-----------
The defaults still point at the original machine, because that is where the published
measurements were taken and keeping them makes the recorded artifacts re-runnable as-is.
They are DEFAULTS, not requirements: set the variables to run elsewhere. Nothing here reads
or prints a credential VALUE -- only whether the store exists and which refs it holds.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _find_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "bench_env.py").exists():
            return candidate
    raise RuntimeError(f"could not locate the repository root above {here}")


ROOT = _find_root()

# ----------------------------------------------------------------- in-repo directories
RESULTS = ROOT / "results"
PAPER = ROOT / "paper"
PROTOCOL = ROOT / "protocol"
SRC = ROOT / "src"
ITEMS = SRC / "items"
INSTRUMENT = SRC / "instrument"
ANALYSIS = SRC / "analysis"
HARNESS = SRC / "harness"
SNAPSHOT = PROTOCOL / "instrument-snapshot"
SNAPSHOT_PKG = SNAPSHOT / "src" / "laya_mcp"
DATA = ROOT / "data"
PROBES = ROOT / "probes"
RECON = ROOT / "recon"


def _env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name)
    return Path(raw).expanduser() if raw else default


# ----------------------------------------------------------------- the sibling checkout
# The sidecar is a SEPARATE project (its own repository, published on PyPI as `laya-mcp`).
# It is not vendored: `protocol/instrument-snapshot/` holds a frozen COPY of the revision
# the measurements are attributed to, and this points at the live tree only for the two
# places that genuinely need it (launching the server, and drift detection).
LAYA_ROOT = _env_path("LAYA_ROOT", Path(r"D:\Projects\laya-family"))
VENV_PYTHON = _env_path("LAYA_VENV_PYTHON",
                        LAYA_ROOT / ".venv-laya" / "Scripts" / "python.exe")
MODEL_ROOT = _env_path("LAYA_MODEL_ROOT", LAYA_ROOT / "_models" / "laya")
LAYA_WORKTREE = _env_path("LAYA_WORKTREE", LAYA_ROOT / "laya-mcp-pkg" / "src" / "laya_mcp")

# ----------------------------------------------------------------- credentials
# Read-only. `deepseek_client` and `jev_client` pull a ref from this store; they never log
# or persist a value. See protocol/INCIDENT-credential-echo.md for why that rule is strict.
CREDENTIALS_PATH = _env_path("DSH_CREDENTIALS",
                             Path.home() / ".dsh" / ".credentials.yaml")

# ----------------------------------------------------------------- the sidecar endpoint
LAYA_PORT = int(os.environ.get("LAYA_PORT", "8787"))
LAYA_BASE = f"http://127.0.0.1:{LAYA_PORT}"
PINNED_PORT = int(os.environ.get("LAYA_PINNED_PORT", "8791"))
PINNED_BASE = f"http://127.0.0.1:{PINNED_PORT}"


def describe() -> str:
    """Human-readable resolution report. Never prints a credential value."""
    creds_state = "present" if CREDENTIALS_PATH.exists() else "MISSING"
    lines = [
        ("repository root", ROOT),
        ("results", RESULTS),
        ("pinned snapshot", SNAPSHOT),
        ("laya checkout", LAYA_ROOT),
        ("  venv python", VENV_PYTHON),
        ("  model root", MODEL_ROOT),
        ("  worktree", LAYA_WORKTREE),
        ("credentials", f"{CREDENTIALS_PATH}  [{creds_state}]"),
        ("sidecar", LAYA_BASE),
        ("pinned sidecar", PINNED_BASE),
    ]
    width = max(len(k) for k, _ in lines)
    out = [f"{k:<{width}}  {v}" for k, v in lines]
    missing = [k for k, v in lines[3:6] if not Path(v).exists()]
    if missing:
        out.append("")
        out.append("WARNING: these paths do not exist on this machine: "
                   + ", ".join(missing))
        out.append("         set LAYA_ROOT / LAYA_VENV_PYTHON / LAYA_MODEL_ROOT to run "
                   "the sidecar probes here.")
        out.append("         Probes that only re-derive statistics (src/analysis/) need "
                   "none of them.")
    return "\n".join(out)


if __name__ == "__main__":
    env_used = {k: v for k, v in os.environ.items()
                if k in ("LAYA_ROOT", "LAYA_VENV_PYTHON", "LAYA_MODEL_ROOT",
                         "LAYA_WORKTREE", "DSH_CREDENTIALS", "LAYA_PORT",
                         "LAYA_PINNED_PORT")}
    print(describe())
    print()
    if env_used:
        print("overridden by environment:")
        for k, v in sorted(env_used.items()):
            print(f"  {k} = {v}")
    else:
        print("no overrides in effect (all defaults)")
    sys.exit(0)
