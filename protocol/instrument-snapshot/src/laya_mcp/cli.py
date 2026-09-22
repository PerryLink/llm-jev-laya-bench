"""``laya-mcp`` - one command, several jobs.

The subcommands exist because a caller arrives with one of four intents, and
making them choose a package before they can start is the main reason a
Python-backed MCP server is annoying to install:

``serve``
    Run the persistent HTTP sidecar. The model loads **once** and stays warm.
    This is what a harness, a DSH plugin, or any long-lived client should point
    at, and it is the only mode where the expensive part is paid once. Laya's own
    cold build is seconds to tens of seconds, and its own documentation measures
    7-15 s per reload on a language switch under the default lazy router.

``mcp``
    Speak the Model Context Protocol over stdio, for a harness that spawns a
    server per session. Thin: it forwards to a sidecar when one is reachable, and
    otherwise hosts the model in-process.

``doctor``
    Report what is installed, what is loadable, what device inference would
    actually use, and what the checkpoint's real limits are - **without loading
    the model**. Importing torch is deliberately avoided here so the diagnosis is
    instant and works even when the install is broken, which is exactly when a
    diagnosis is wanted.

``install``
    Write this server into the config of whichever agent harness is present. Each
    harness uses a different file, format and key; see :mod:`laya_mcp.harnesses`.

Every subcommand keeps stdout clean for its own protocol and sends diagnostics to
stderr, because a stdio MCP server that prints a banner to stdout is a server
that fails to handshake.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional, Sequence

from . import __version__

#: Environment flags applied before anything imports transformers. The upstream
#: test suite sets the same ones: resolving the TensorFlow/Keras backend can hang
#: on some Windows installs, and hf-xet has been a source of transfer stalls.
_IMPORT_ENV = {
    "USE_TF": "0",
    "USE_TORCH": "1",
    "TOKENIZERS_PARALLELISM": "false",
}


def _prepare_environment() -> None:
    for key, value in _IMPORT_ENV.items():
        os.environ.setdefault(key, value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="laya-mcp",
        description=(
            "Typed decisions from Laya, over MCP or HTTP. Laya answers noul / choice / score "
            "questions and returns probabilities; it does not write prose."
        ),
    )
    parser.add_argument("--version", action="version", version=f"laya-mcp {__version__}")
    sub = parser.add_subparsers(dest="command")

    # -- serve ---------------------------------------------------------------
    serve = sub.add_parser(
        "serve",
        help="run the persistent HTTP sidecar (loads the model once and keeps it warm)",
    )
    serve.add_argument("--host", default="127.0.0.1", help="bind address (default: 127.0.0.1)")
    serve.add_argument("--port", type=int, default=8787, help="bind port (default: 8787)")
    serve.add_argument(
        "--model", default="english",
        help="checkpoint to preload: english, multilingual, or typed-decisions",
    )
    serve.add_argument(
        "--also", action="append", default=[],
        help="an additional checkpoint to preload (repeatable)",
    )
    serve.add_argument("--device", default=None, help="cpu, cuda, or mps (default: auto)")
    serve.add_argument(
        "--model-root", default=None,
        help="a local checkpoint directory; avoids any Hub access",
    )
    serve.add_argument(
        "--max-len", type=int, default=None,
        help="override the checkpoint's total token budget",
    )
    serve.add_argument(
        "--head-max-len", type=int, default=None,
        help="override the per-question option+instruction token budget",
    )
    serve.add_argument(
        "--calibration", default=None,
        help="path to a calibration store JSON (applied on top of the checkpoint's own)",
    )
    serve.add_argument(
        "--concurrency", type=int, default=1,
        help=(
            "how many requests may run a forward pass at once (default: 1). Laya is not "
            "thread-safe: its Agent mutates self.device on an OOM, so the default serialises."
        ),
    )
    serve.add_argument(
        "--truncate-left",
        action="store_true",
        help=(
            "keep the TAIL of an oversized state instead of its head. Laya's default keeps "
            "the front and silently discards the end, which for a contract, a log thread or "
            "an email chain with the correction appended at the bottom is often where the "
            "answer is. Measured: one 16958-character state scored a noul 0.0706 with the "
            "front kept and 0.8341 with the tail kept. Off by default because it changes "
            "which part of a long document the model reads."
        ),
    )
    serve.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"])

    # -- mcp -----------------------------------------------------------------
    mcp = sub.add_parser("mcp", help="speak MCP over stdio (for a harness that spawns per session)")
    mcp.add_argument(
        "--sidecar", default=None,
        help=(
            "base URL of a running `laya-mcp serve`, e.g. http://127.0.0.1:8787. "
            "Faster when you have one: a single model load shared by every session. "
            "Without it this process hosts the model itself, which is slower per session "
            "but works with nothing else running."
        ),
    )
    mcp.add_argument(
        "--filter", default=None,
        help="expose only these tools, comma separated (e.g. noul,choice)",
    )
    # The model options are mirrored from `serve` on purpose. A harness registers
    # this command in a config file it never revisits, so anything it cannot pass
    # here it cannot configure at all - and the failure is silent, because the
    # process starts, reaches for the Hub, and only then disappoints. `mcp` had
    # none of these while the bundle that mounts it passed `--model-root`, which
    # would have failed at startup with "unrecognized arguments".
    mcp.add_argument(
        "--model", default="english",
        help="checkpoint to host when there is no sidecar: english, multilingual, typed-decisions",
    )
    mcp.add_argument(
        "--also", action="append", default=[],
        help="an additional checkpoint to host (repeatable)",
    )
    mcp.add_argument("--device", default=None, help="cpu, cuda, or mps (default: auto)")
    mcp.add_argument(
        "--model-root", default=None,
        help=(
            "a local checkpoint directory; avoids any Hub access. Worth setting even when the "
            "weights are cached: without it the server reaches the Hub and re-verifies every "
            "file on each start, and on a cold cache downloads ~800 MB."
        ),
    )
    mcp.add_argument("--max-len", type=int, default=None, help="override the token budget")
    mcp.add_argument(
        "--head-max-len", type=int, default=None,
        help="override the per-question option+instruction budget (the high-cardinality fix)",
    )
    mcp.add_argument("--calibration", default=None, help="path to a calibration store JSON")
    mcp.add_argument(
        "--truncate-left",
        action="store_true",
        help=(
            "keep the TAIL of an oversized state instead of its head, when this process hosts "
            "the model. Ignored with --sidecar, where the other process decides."
        ),
    )

    # -- doctor --------------------------------------------------------------
    doctor = sub.add_parser(
        "doctor",
        help="report what is installed and what a checkpoint can do, without loading it",
    )
    doctor.add_argument("--model-root", default=None, help="a local checkpoint directory to inspect")
    doctor.add_argument(
        "--model", default="english",
        help="which checkpoint the root holds: english, multilingual, or typed-decisions",
    )
    doctor.add_argument("--device", default=None, help="the device you intend to use")
    doctor.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    # -- install -------------------------------------------------------------
    install = sub.add_parser("install", help="register this server with the agent harnesses you have")
    install.add_argument(
        "--harness", default=None,
        help="target one harness by id; default is every harness detected",
    )
    install.add_argument("--name", default="laya", help="the server name to register (default: laya)")
    install.add_argument(
        "--url", default=None,
        help="register a remote/HTTP endpoint instead of a local stdio command",
    )
    install.add_argument(
        "--python", default=None,
        help="the interpreter a stdio entry should use (default: this one)",
    )
    install.add_argument("--dry-run", action="store_true", help="print the change, write nothing")
    install.add_argument("--project", default=None, help="write into a project-local config too")

    return parser


def _cmd_serve(args: argparse.Namespace) -> int:
    _prepare_environment()
    from .server import serve

    return serve(
        host=args.host,
        port=args.port,
        model=args.model,
        also=tuple(args.also),
        device=args.device,
        model_root=args.model_root,
        max_len=args.max_len,
        head_max_len=args.head_max_len,
        calibration_path=args.calibration,
        concurrency=args.concurrency,
        log_level=args.log_level,
        truncate_left=args.truncate_left,
    )


def _cmd_mcp(args: argparse.Namespace) -> int:
    _prepare_environment()
    from .errors import LayaMcpError
    from .mcp_server import run_stdio
    from .worker import WorkerConfig

    # The model options are only meaningful without a sidecar, but they are
    # accepted either way and simply unused when one is configured: a harness
    # writes this command into a config file once, and rejecting an argument it
    # passes would turn a harmless redundancy into a server that will not start.
    config = WorkerConfig(
        model=args.model,
        also=tuple(args.also or ()),
        device=args.device,
        model_root=args.model_root,
        max_len=args.max_len,
        head_max_len=args.head_max_len,
        calibration_path=args.calibration,
        truncate_left=args.truncate_left,
    )

    try:
        return run_stdio(
            sidecar=args.sidecar, tools=_parse_filter(args.filter), config=config
        )
    except LayaMcpError as exc:
        # A structured failure still has to reach the client as a structured
        # failure; MCP carries the message, so print it to stderr and exit
        # non-zero rather than emitting a malformed frame.
        print(f"laya-mcp: {exc}", file=sys.stderr)
        return 2


def _parse_filter(raw: Optional[str]) -> Optional[tuple[str, ...]]:
    if not raw:
        return None
    tools = tuple(part.strip() for part in raw.split(",") if part.strip())
    return tools or None


def _cmd_doctor(args: argparse.Namespace) -> int:
    """Report the environment without importing torch.

    ``import laya`` at module scope pulls torch, which costs seconds and fails
    loudly on a broken install - the two cases where you most want a diagnosis.
    So every import here is inside a try, and the report is built from what
    succeeded.
    """
    report: dict[str, object] = {
        "laya_mcp_version": __version__,
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "platform": sys.platform,
    }

    def probe(module: str) -> dict[str, object]:
        try:
            imported = __import__(module)
        except Exception as exc:  # noqa: BLE001 - any import failure is the diagnosis
            return {"installed": False, "error": f"{type(exc).__name__}: {exc}"}
        return {"installed": True, "version": getattr(imported, "__version__", "unknown")}

    report["packages"] = {name: probe(name) for name in ("laya", "torch", "transformers")}

    cuda: dict[str, object] = {"available": False}
    try:
        import torch

        cuda["available"] = bool(torch.cuda.is_available())
        if cuda["available"]:
            capability = torch.cuda.get_device_capability(0)
            cuda["device"] = torch.cuda.get_device_name(0)
            cuda["capability"] = f"sm_{capability[0]}{capability[1]}"
            # is_available() True does not prove this GPU's kernels are compiled
            # into this build. The only honest test is to run an op. This is the
            # exact failure that silently demotes a Blackwell card to CPU.
            try:
                probe_tensor = torch.zeros(8, device="cuda")
                (probe_tensor + 1).sum().item()
                cuda["kernel_ok"] = True
            except Exception as exc:  # noqa: BLE001
                cuda["kernel_ok"] = False
                cuda["kernel_error"] = f"{type(exc).__name__}: {exc}"
                cuda["note"] = (
                    "torch.cuda.is_available() is True but a real op failed, which is the "
                    "signature of a wheel built without this card's architecture. Inference "
                    "would silently fall back to CPU."
                )
    except Exception as exc:  # noqa: BLE001
        cuda["error"] = f"{type(exc).__name__}: {exc}"
    report["cuda"] = cuda

    # Checkpoint inspection: only runs if a root was given, and never loads weights.
    if args.model_root:
        from .capability import find_model_root, normalise_checkpoint, read_capability

        try:
            checkpoint = normalise_checkpoint(args.model or "english")
        except KeyError:
            checkpoint = "english"
        root = find_model_root(args.model_root)
        capability = read_capability(
            root,
            checkpoint=checkpoint,
            device=args.device or "auto",
            requested_device=args.device,
        )
        report["capability"] = capability.to_dict()

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    print(f"laya-mcp {report['laya_mcp_version']}")
    print(f"python   {report['python']}  ({report['executable']})")
    print(f"platform {report['platform']}")
    print("\npackages")
    for name, info in report["packages"].items():  # type: ignore[union-attr]
        if info.get("installed"):
            print(f"  {name:<14} {info.get('version')}")
        else:
            print(f"  {name:<14} NOT INSTALLED - {info.get('error')}")
    print("\ndevice")
    cuda = report["cuda"]  # type: ignore[assignment]
    if cuda.get("available"):
        print(f"  cuda            {cuda.get('device')} ({cuda.get('capability')})")
        if cuda.get("kernel_ok") is False:
            print("  kernel          FAILED - inference would fall back to CPU")
            print(f"                  {cuda.get('kernel_error')}")
        else:
            print("  kernel          ok (a real op ran on the device)")
    else:
        print("  cuda            unavailable, inference would run on CPU")
        if cuda.get("error"):
            print(f"                  {cuda['error']}")
    if "capability" in report:
        cap = report["capability"]  # type: ignore[assignment]
        print("\ncheckpoint")
        print(f"  name            {cap.get('checkpoint')}")
        print(f"  encoder         {cap.get('encoder')}")
        print(f"  max_len         {cap.get('max_len')}")
        print(f"  head_max_len    {cap.get('head_max_len')}")
        print(f"  state budget    ~{cap.get('state_budget_tokens')} tokens")
        print(f"  max options     {cap.get('max_options_8_tokens_each')} stay distinguishable")
        print(f"  fitted temps    {cap.get('fitted_temperature_buckets')} bucket(s)")
        if cap.get("language_caveat"):
            print(f"  caveat          {cap['language_caveat']}")
    return 0


def _cmd_install(args: argparse.Namespace) -> int:
    from .harnesses import install

    return install(
        harness=args.harness,
        name=args.name,
        url=args.url,
        python=args.python or sys.executable,
        dry_run=args.dry_run,
        project=args.project,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        # No subcommand: the most useful default is to be an MCP server, because
        # that is how every harness spawns this. `--help` still works.
        if sys.stdin.isatty():
            parser.print_help()
            return 0
        return _cmd_mcp(argparse.Namespace(sidecar=None, filter=None))

    handlers = {
        "serve": _cmd_serve,
        "mcp": _cmd_mcp,
        "doctor": _cmd_doctor,
        "install": _cmd_install,
    }
    handler = handlers.get(args.command)
    if handler is None:  # pragma: no cover - argparse prevents this
        parser.print_help()
        return 2
    return handler(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
