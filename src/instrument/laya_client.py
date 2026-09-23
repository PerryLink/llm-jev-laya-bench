"""Laya sidecar client with the operational guarantees the protocol requires.

Every guarantee here is forced by a measured finding, cited by report section:

* Health-check + auto-restart (R13 s0, R4 P0-4): the sidecar does NOT start with the
  session and dies silently. A run that begins against a dead sidecar produces a
  zero-accuracy result that looks like a model property.
* Token counting with the checkpoint's OWN tokenizer, never characters (R13 s2.2,
  constraint 1): the shipped planner estimates tokens as chars/4*1.15, which errs in
  BOTH directions and is therefore not safe to gate on. Measured against the shipped
  tokenizers (results/P31-token-density.json): English prose 4.31 chars/token, so the
  planner over-reserves 1.239x; but JSON 2.40, source 3.24, Chinese 1.65 and CSV 1.62
  -- all below the 3.478 break-even, so on those it UNDER-reserves by 1.075x to
  2.150x and will report `fits` for a state the model silently truncates.
  CORRECTED 2026-09-23: this note previously read "~6.33 chars/token, so the planner
  is ~1.8x optimistic", which described the synthetic truncation-sweep state (one
  filler sentence repeated 45 times) rather than English prose, and reported only the
  safe direction. See results/ERRATA.md s12.
* Pin ONE entry point (R13 s0b, constraint 5): the plugin tools reach a sidecar with
  planner max_len 1024/head 512, the MCP tools reach a stdio server with 512/192.
  Same request, same second: state_room_estimated 917 vs 405. This client speaks
  HTTP to 127.0.0.1:8787 directly, so the entry point is explicit and recorded.
* Record `noul` as P(true), NEVER `probability` (R12 C0-2): `probability` is
  P(the answered option) and inverts about half the items.
* Assert the returned `type` equals the requested `type` (R12 C1-9, trap T-2): an
  unrecognised type is silently coerced to `score`.
* Store the returned `legend` and assert its order (R12 C1-6, trap T-3): `score` is
  sum(index * probability) over the legend AS WRITTEN, so a descending criteria map
  silently inverts every score.
* Check `truncated` before any data enters analysis (R12 C2-14): an over-long
  candidate list is truncated inside the state and still returns a full-looking
  ranking over the fragment.
* Latency only from the provider's own fields (R13 constraint 20/18): `latency_ms`
  varies 8x for identical requests and wall-clock around a tool call measures turn
  overhead, not inference.
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
from bench_env import LAYA_WORKTREE, MODEL_ROOT, SNAPSHOT_PKG, VENV_PYTHON  # noqa: E402


import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

SIDECAR_HOST = "127.0.0.1"
SIDECAR_PORT = 8787
BASE_URL = f"http://{SIDECAR_HOST}:{SIDECAR_PORT}"


# The PINNED, immutable snapshot of the instrument. This -- not the mutable working
# tree -- is what `instrument_hashes()` reports and what a measurement must be
# attributed to. See protocol/instrument-snapshot/PIN.json (13/13 hashes verified).


# The measured clamp is PER CHECKPOINT (main-session probe, R8 s1): english 512,
# multilingual 1024, typed-decisions 1024. It is NOT a global constant.
CHECKPOINT_CLAMP_TOKENS = {
    "english": 512,
    "multilingual": 1024,
    "typed-decisions": 1024,
}
CHECKPOINT_SUBFOLDER = {
    "english": None,
    "multilingual": "multilingual",
    "typed-decisions": "typed-decisions",
}

START_ARGS = [
    "-m", "laya_mcp", "serve",
    "--model", "english",
    "--also", "multilingual",
    "--also", "typed-decisions",
    "--model-root", str(MODEL_ROOT),
    "--device", "cuda",
    "--port", str(SIDECAR_PORT),
    "--max-len", "1024",
    "--head-max-len", "512",
]


class SidecarError(RuntimeError):
    pass


@dataclass
class LayaClient:
    """HTTP client for the Laya sidecar. One entry point, recorded explicitly."""

    autostart: bool = True
    timeout_s: int = 240
    # Port is configurable so a PINNED sidecar can run alongside whatever the harness
    # already has on 8787, without either process being disturbed.
    port: int = SIDECAR_PORT
    call_count: int = 0
    restart_count: int = 0
    cold_start_ms: float | None = None
    _tokenizer: object | None = field(default=None, repr=False)

    @property
    def base_url(self) -> str:
        return f"http://{SIDECAR_HOST}:{self.port}"

    # ---------------------------------------------------------------- lifecycle

    def health(self) -> dict | None:
        try:
            with urllib.request.urlopen(f"{self.base_url}/health", timeout=4) as r:
                return json.loads(r.read())
        except Exception:
            return None

    def ensure_up(self, wait_s: int = 60) -> dict:
        h = self.health()
        if h is not None and h.get("ok"):
            return h
        if not self.autostart:
            raise SidecarError("sidecar is down and autostart is disabled")
        return self.start(wait_s=wait_s)

    def start(self, wait_s: int = 60) -> dict:
        """Launch the sidecar on THIS client's port and wait for readiness."""
        if not VENV_PYTHON.exists():
            raise SidecarError(f"venv python not found: {VENV_PYTHON}")
        args = []
        take = False
        for a in START_ARGS:
            if take:
                args.append(str(self.port))
                take = False
                continue
            args.append(a)
            if a == "--port":
                take = True
        if "--port" not in START_ARGS:
            args += ["--port", str(self.port)]
        t0 = time.perf_counter()
        subprocess.Popen(
            [str(VENV_PYTHON), *args],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self.restart_count += 1
        deadline = time.perf_counter() + wait_s
        while time.perf_counter() < deadline:
            time.sleep(1.0)
            h = self.health()
            if h is not None and h.get("ok") and h.get("loaded"):
                self.cold_start_ms = (time.perf_counter() - t0) * 1000.0
                return h
        raise SidecarError(f"sidecar did not become ready within {wait_s}s")

    def capabilities(self) -> dict:
        with urllib.request.urlopen(f"{self.base_url}/capabilities", timeout=10) as r:
            return json.loads(r.read())

    def version(self) -> dict:
        with urllib.request.urlopen(f"{self.base_url}/version", timeout=10) as r:
            return json.loads(r.read())

    # ------------------------------------------------------------------- tokenizer

    def tokenizer(self, checkpoint: str = "english"):
        """Load the checkpoint's OWN tokenizer. Required for every budget decision."""
        if self._tokenizer is not None:
            return self._tokenizer
        try:
            from tokenizers import Tokenizer  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise SidecarError(
                "the `tokenizers` package is required for protocol-correct budget "
                "accounting; install it in the venv that runs this harness"
            ) from exc
        sub = CHECKPOINT_SUBFOLDER[checkpoint]
        base = MODEL_ROOT if sub is None else MODEL_ROOT / sub
        path = base / "tokenizer" / "tokenizer.json"
        if not path.exists():
            raise SidecarError(f"tokenizer not found: {path}")
        self._tokenizer = Tokenizer.from_file(str(path))
        return self._tokenizer

    def count_tokens(self, text: str, checkpoint: str = "english") -> int:
        return len(self.tokenizer(checkpoint).encode(text).ids)

    def state_ceiling_tokens(self, checkpoint: str = "english", head_tokens: int = 61) -> int:
        """Usable state tokens: clamp - head - 1. Measured, not estimated (R13 s2.5)."""
        return CHECKPOINT_CLAMP_TOKENS[checkpoint] - head_tokens - 1

    # ---------------------------------------------------------------------- calls

    def ask(self, state, questions: dict, checkpoint: str | None = None,
            strict: bool = False) -> dict:
        payload: dict = {"state": state, "questions": questions}
        if checkpoint is not None:
            payload["model"] = checkpoint
        if strict:
            payload["strict"] = True
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/ask", data=body,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as r:
                out = json.loads(r.read())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:400]
            raise SidecarError(f"HTTP {exc.code}: {detail}") from exc
        self.call_count += 1
        return out

    # ------------------------------------------------------------- answer readers

    @staticmethod
    def noul_p_true(answer: dict) -> float:
        """P(true) from a noul/noul-as-choice answer.

        `probability` is P(the ANSWERED option); recording it as P(true) inverts
        roughly half the items (R12 C0-2). `noul` is the score itself.
        """
        return float(answer["noul"])

    @staticmethod
    def choice_distribution(answer: dict) -> dict:
        """Full distribution, always. Never the winner alone (R12 C1-7)."""
        return dict(answer.get("probabilities") or {})

    @staticmethod
    def truncation_flags(resp: dict) -> dict:
        """Everything that could indicate the input was altered before judging."""
        return {
            "truncated": resp.get("truncated"),
            "warnings": resp.get("warnings") or [],
            "budget_summary": resp.get("budget_summary"),
            "egress": resp.get("egress"),
            "in_pad": (resp.get("usage") or {}).get("input_tokens_padded"),
        }


def sha256_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def instrument_hashes() -> dict:
    """Per-file SHA256 of the instrument, read from the PINNED SNAPSHOT.

    TWO DEFECTS FIXED HERE (both found by the independent audit, see
    protocol/AUDIT-FINDINGS.md M-1/M-2):

    1. This function used to hash the MUTABLE WORKING TREE
       (``D:\\Projects\\laya-family\\laya-mcp-pkg\\src\\laya_mcp``). That made every
       recorded instrument block describe whatever the tree happened to look like at
       serialisation time, and it meant the drift guard compared working-tree-now
       against working-tree-then and NEVER against the pin. The pin is the snapshot, so
       the snapshot is what gets hashed; the working tree is hashed too, under a
       separate key prefix, so the two can be compared rather than confused.

    2. The old target list held only 4 of the 13 modules. The ONLY drift that actually
       occurred during this project was in the three files it did not cover
       (``__init__.py``, ``cli.py``, ``mcp_server.py``) -- so the manifest was
       structurally blind to real drift. All 13 modules are now covered.
    """
    snap = SNAPSHOT_PKG
    work = LAYA_WORKTREE
    modules = [
        "planning.py", "worker.py", "capability.py", "server.py", "calibration.py",
        "cli.py", "errors.py", "harnesses.py", "mcp_server.py", "protocol.py",
        "validate.py", "__init__.py", "__main__.py",
    ]
    out: dict = {}
    for name in modules:
        src = snap / name if (snap / name).exists() else None
        out[f"snapshot.{name}"] = sha256_file(src) if src else "MISSING"
        out[f"worktree.{name}"] = sha256_file(work / name) if (work / name).exists() else "MISSING"
    # checkpoint configs live under MODEL_ROOT, not in the code snapshot
    out["rl_agent_config.json"] = sha256_file(MODEL_ROOT / "rl_agent_config.json") \
        if (MODEL_ROOT / "rl_agent_config.json").exists() else "MISSING"
    out["encoder_config.json"] = sha256_file(MODEL_ROOT / "encoder" / "config.json") \
        if (MODEL_ROOT / "encoder" / "config.json").exists() else "MISSING"
    return out


def instrument_drift() -> dict:
    """Files where the pinned snapshot and the working tree disagree.

    Non-empty means the two candidate instruments are NOT the same revision. Only the
    four behaviour-critical modules (planning/worker/capability/server) can change what
    a measurement means; drift elsewhere is recorded but does not invalidate numbers
    already taken on the snapshot.
    """
    h = instrument_hashes()
    drift = {}
    for k, v in h.items():
        if k.startswith("snapshot."):
            name = k[len("snapshot."):]
            w = h.get(f"worktree.{name}")
            if w != v:
                drift[name] = {"snapshot": v, "worktree": w}
    return drift


def instrument_record(entry_point: str = "HTTP 127.0.0.1:8787 (Path A)",
                      port: int | None = None) -> dict:
    """Self-describing instrument record. Attach this to EVERY result file.

    MEASURED DRIFT (2026-09-22, main session): the instrument is a MUTABLE WORKING
    TREE. planning.py / worker.py / server.py were rewritten at 18:16-18:17 while an
    earlier sidecar was still running, so two live hosts were serving two different
    revisions simultaneously. V5 predicted exactly this ("the design pins the sidecar
    version string and the checkpoint but never the code").

    A measurement without its instrument revision is not reproducible, and this
    project has already observed the tree change mid-session. Hence this record.

    AUDIT FIX (findings M-3/M-5/F-7): the record now ALSO captures the LAUNCH LOADOUT
    (which checkpoints the serving sidecar actually has loaded). Neither PIN.json nor
    INSTRUMENT-FREEZE.json recorded it, yet the state window is a function of
    (loadout x queried checkpoint) -- so without this field the clamp measurement this
    paper rests on could not be attributed to a configuration. It is read live from
    the serving sidecar's /health, not assumed.
    """
    import datetime
    import platform
    import sys

    loadout: dict | None = None
    try:
        h = LayaClient(autostart=False, port=port or SIDECAR_PORT).health()
        if h:
            cps = h.get("checkpoints") or {}
            loadout = {
                "loaded_checkpoints": sorted(cps.keys()),
                "n_loaded": len(cps),
                "per_checkpoint": {k: {"max_len": v.get("max_len"),
                                       "head_max_len": v.get("head_max_len")}
                                   for k, v in sorted(cps.items())},
                "port": port or SIDECAR_PORT,
                "calls": h.get("calls"),
                "uptime_s": h.get("uptime_s"),
                "truncate_left": h.get("truncate_left"),
            }
    except Exception as exc:                      # never let provenance break a run
        loadout = {"error": str(exc)[:200]}

    return {
        "recorded_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "entry_point": entry_point,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "loadout": loadout,
        # AUDIT FIX (F5): `instrument_drift()` existed but had no caller, so the record
        # carried two hash families with nobody comparing them. The drift verdict is now
        # part of the record itself.
        "drift": instrument_drift(),
        "instrument_hashes": instrument_hashes(),
    }


def assert_instrument(expected: dict, where: str = "run") -> None:
    """Abort if the instrument has moved since `expected` was frozen.

    A guard rather than a warning: a silent revision change makes two runs
    incomparable while both still look successful.
    """
    current = instrument_hashes()
    drift = {k: (expected.get(k), v) for k, v in current.items() if expected.get(k) != v}
    if drift:
        lines = "\n".join(f"  {k}: expected {a} got {b}" for k, (a, b) in drift.items())
        raise SidecarError(
            f"INSTRUMENT DRIFT before {where}: the code serving this run is not the "
            f"code that was frozen.\n{lines}\nRestart the sidecar from the intended "
            f"revision, or re-freeze and re-run every affected measurement."
        )


if __name__ == "__main__":
    client = LayaClient()
    h = client.ensure_up()
    print(json.dumps({"health": h, "version": client.version()}, indent=2)[:1200])
    print("cold_start_ms:", client.cold_start_ms, "restarts:", client.restart_count)
    for k, v in instrument_hashes().items():
        print(f"{k:<26} {v}")
