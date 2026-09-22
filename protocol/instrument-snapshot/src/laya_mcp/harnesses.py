"""Register ``laya-mcp`` with whichever agent harness you actually have.

There is no portable way to do this. Measured against real installed harnesses,
they disagree on everything:

===========  ==========================================  =========  ==========================
harness      config file                                 format     the key
===========  ==========================================  =========  ==========================
Claude Code  ``~/.claude.json`` (or a project ``.mcp.json``)  JSON   ``mcpServers``
Codex        ``~/.codex/config.toml``                     TOML       ``[mcp_servers.<name>]``
opencode     ``~/.config/opencode/opencode.json[c]``      JSON       ``mcp``
OpenClaw     ``~/.openclaw/openclaw.json``                JSON       ``mcp.servers``
Hermes       ``<hermes home>/config.yaml``               YAML       ``mcp_servers``
===========  ==========================================  =========  ==========================

Four different top-level keys, three serializations, and opencode disagrees three
more times inside its own entry: ``command`` is an **array** holding the
executable *and* its arguments rather than a string with a separate ``args``; the
environment key is ``environment`` rather than ``env``; and the toggle is
``enabled`` rather than ``disabled`` - setting ``disabled: true`` there is
silently ignored, which would be an invisible bug in a naive writer.

So each harness gets its own adapter, and the honest ones say what they cannot do:

* **Hermes** is written directly rather than through its CLI. Its local-stdio CLI
  flags are undocumented, and the package on a stock Windows install was observed
  failing outright (``Hermes Agent isolated runtime is not ready``), so the
  documented YAML is the reliable path.
* **pi** is not supported, and not because of an oversight: ``pi`` has no native
  MCP support at all. Its settings reference contains no MCP key, and its own
  upstream feature request for MCP is titled "Add MCP extension example" - MCP
  there is an extension you build. An installer cannot configure a format that
  does not exist, so this module detects it and says so.

Every writer merges rather than replaces, backs the file up before changing it,
and refuses to touch a file it cannot parse. A harness config holds the user's
other state - ``~/.claude.json`` in particular is a large shared file with history
and per-project data - and clobbering it to install a decision model would be a
catastrophic trade.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

#: What we register as, unless the caller renames it.
DEFAULT_SERVER_NAME = "laya"

#: Launchers that are shell shims rather than executables. On Windows these are
#: ``.cmd``/``.ps1`` scripts, and the MCP SDK spawns stdio servers with
#: ``shell: false``. Measured on Node v22: ``spawn("npx", {shell:false})`` fails
#: with ENOENT and ``spawn("npx.cmd", {shell:false})`` fails with EINVAL, while
#: ``spawn("cmd", ["/c", "npx", ...])`` works. So any shim must be wrapped.
_SHIM_LAUNCHERS = frozenset({"npx", "npm", "pnpm", "yarn", "uvx", "uv", "pipx"})


@dataclass
class Entry:
    """One stdio server registration, in harness-neutral terms."""

    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)

    def windows_safe(self) -> "Entry":
        """Wrap a shell shim in ``cmd /c`` when running on Windows.

        Only needed for shim launchers. A real executable - ``python.exe``,
        ``node.exe``, ``uvx.exe`` - spawns fine with ``shell: false`` and must not
        be wrapped, because ``cmd`` mangles arguments containing spaces.
        """
        if os.name != "nt":
            return self
        stem = Path(self.command).stem.lower()
        if stem in _SHIM_LAUNCHERS and not self.command.lower().endswith(".exe"):
            return Entry(
                name=self.name,
                command="cmd",
                args=["/c", self.command, *self.args],
                env=self.env,
            )
        return self


@dataclass
class Harness:
    """How to detect and configure one agent harness."""

    id: str
    label: str
    #: Where the user config lives. ``None`` means there is no config surface.
    config_path: Optional[Callable[[], Optional[Path]]]
    #: How to serialize. One of ``json``, ``toml``, ``yaml``.
    fmt: str
    #: Human-readable description of where the entry goes, for the report.
    location: str
    #: Builds the config fragment for a stdio entry.
    write: Callable[[Path, Entry], None]
    #: The command that proves the harness sees the server, if one exists.
    verify: Optional[Sequence[str]] = None
    #: An executable whose presence on PATH means the harness is installed.
    detect: Sequence[str] = ()
    #: A reason this harness cannot be configured by writing a file.
    unsupported_reason: Optional[str] = None


# --------------------------------------------------------------------------- #
# serialization helpers
# --------------------------------------------------------------------------- #


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{path} is not valid JSON ({exc}); refusing to rewrite a config this tool cannot "
            "read, because doing so would discard whatever else it holds"
        ) from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} does not contain a JSON object")
    return loaded


def _read_jsonc(path: Path) -> dict[str, Any]:
    """JSON with comments and trailing commas, which is what opencode writes.

    A real parser is not worth a dependency here: the only constructs opencode's
    own template uses are ``//`` and ``/* */`` comments and trailing commas, and
    stripping them is enough to read the file. A file that still fails to parse is
    refused rather than guessed at.
    """
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    stripped_lines = []
    for line in text.splitlines():
        # Do not strip "//" inside a string. Counting quotes is crude but this is
        # only used to *read* a config we then rewrite as plain JSON, and getting
        # it wrong fails loudly at json.loads rather than silently.
        in_string = False
        cut = None
        index = 0
        while index < len(line) - 1:
            char = line[index]
            if char == '"' and (index == 0 or line[index - 1] != "\\"):
                in_string = not in_string
            elif not in_string and line[index : index + 2] == "//":
                cut = index
                break
            index += 1
        stripped_lines.append(line if cut is None else line[:cut])
    text = "\n".join(stripped_lines)
    # Trailing commas before a closing bracket or brace.
    import re

    text = re.sub(r",(\s*[}\]])", r"\1", text)
    if not text.strip():
        return {}
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON-with-comments ({exc})") from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} does not contain a JSON object")
    return loaded


def _backup(path: Path) -> Optional[Path]:
    """Copy an existing config aside, once per day per file.

    Not a substitute for version control, but a config that a tool rewrote is a
    config the user wants back, and the cost of keeping a copy is a few kilobytes.
    """
    if not path.is_file():
        return None
    stamp = datetime.now().strftime("%Y%m%d")
    target = path.with_suffix(path.suffix + f".bak-{stamp}")
    if target.exists():
        return target
    shutil.copy2(path, target)
    return target


def _write_atomic(path: Path, text: str) -> None:
    """Write via a temporary file in the same directory, then rename.

    Prevents a crash mid-write from leaving a truncated config that the harness
    would then refuse to start with - the failure mode that turns a convenience
    tool into an outage.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def _toml_string(value: str) -> str:
    """A TOML basic string.

    Written by hand rather than with a library: the standard library can *read*
    TOML but not write it, and adding a writer dependency to configure five
    harnesses is not a trade worth making. Escaping the two characters that
    actually appear in a Windows path plus the quote itself covers the real input.
    """
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def _toml_array(values: Sequence[str]) -> str:
    return "[" + ", ".join(_toml_string(v) for v in values) + "]"


def _toml_table_exists(text: str, name: str) -> bool:
    return any(line.strip() == f"[mcp_servers.{name}]" for line in text.splitlines())


def _write_codex(path: Path, entry: Entry) -> None:
    """Merge one ``[mcp_servers.<name>]`` table into a Codex TOML config.

    Appends rather than parses-and-reserializes. Round-tripping the whole file
    through a TOML writer would reformat everything the user has, which makes a
    one-line install show up as a hundred-line diff - and this file is shared with
    other tools. Appending is both safer here and easier to review. An existing
    table for the same name is replaced in place, because ``codex mcp add`` does
    the same and a duplicate table is a TOML error.
    """
    blocks = [
        f"[mcp_servers.{entry.name}]",
        f"command = {_toml_string(entry.command)}",
    ]
    if entry.args:
        blocks.append(f"args = {_toml_array(entry.args)}")
    if entry.env:
        blocks.append("")
        blocks.append(f"[mcp_servers.{entry.name}.env]")
        for key, value in entry.env.items():
            blocks.append(f"{key} = {_toml_string(value)}")
    block = "\n".join(blocks)

    if not path.is_file():
        _write_atomic(path, block + "\n")
        return

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    out: list[str] = []
    skipping = False
    replaced = False
    header = f"[mcp_servers.{entry.name}]"
    header_env = f"[mcp_servers.{entry.name}.env]"
    for line in lines:
        stripped = line.strip()
        if stripped == header:
            skipping = True
            replaced = True
            out.append(block)
            continue
        if skipping:
            # The table ends at the next table header, or at a line that is not a
            # key/value pair belonging to it.
            if stripped == header_env or stripped.startswith("["):
                skipping = False
            elif not stripped or "=" in stripped or stripped.startswith("#"):
                continue
            else:
                skipping = False
        out.append(line)

    result = "\n".join(out)
    if not replaced:
        if result and not result.endswith("\n"):
            result += "\n"
        result += ("\n" if result.strip() else "") + block + "\n"
    _write_atomic(path, result)


def _yaml_scalar(value: str) -> str:
    """A double-quoted YAML scalar, which is always valid for a string."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _write_hermes(path: Path, entry: Entry) -> None:
    """Merge one server into Hermes's ``mcp_servers`` YAML mapping.

    Rewritten from a parsed mapping rather than appended to, because YAML has no
    equivalent of a TOML table header to anchor a surgical edit. Comments in an
    existing file are therefore lost - stated plainly in the report rather than
    discovered by a surprised user.
    """
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "writing a Hermes config needs PyYAML, which is not installed. "
            "Install it with `pip install pyyaml`, or add this entry by hand."
        ) from exc

    data: dict[str, Any] = {}
    if path.is_file():
        text = path.read_text(encoding="utf-8")
        if text.strip():
            loaded = yaml.safe_load(text)
            if loaded is not None and not isinstance(loaded, dict):
                raise ValueError(f"{path} does not contain a YAML mapping")
            data = loaded or {}

    servers = data.setdefault("mcp_servers", {})
    if not isinstance(servers, dict):
        raise ValueError(f"{path}: `mcp_servers` exists but is not a mapping")
    block: dict[str, Any] = {"command": entry.command}
    if entry.args:
        block["args"] = list(entry.args)
    if entry.env:
        block["env"] = dict(entry.env)
    block["enabled"] = True
    servers[entry.name] = block

    _write_atomic(path, yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


# --------------------------------------------------------------------------- #
# per-harness writers
# --------------------------------------------------------------------------- #


def _write_claude(path: Path, entry: Entry) -> None:
    """Claude Code: top-level ``mcpServers``.

    ``type`` is written explicitly even though it defaults to stdio, because the
    file is hand-read often enough that being explicit is worth the byte. Note
    what is *absent*: ``alwaysAllow`` is not a valid MCP server key in Claude Code.
    It belongs to the separate permission-rule system, and the binary contains only
    ``alwaysAllowRules``/``alwaysDenyRules``/``alwaysAskRules``. Emitting it would
    look reasonable and do nothing.
    """
    data = _read_json(path)
    servers = data.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        raise ValueError(f"{path}: `mcpServers` exists but is not an object")
    block: dict[str, Any] = {"type": "stdio", "command": entry.command}
    if entry.args:
        block["args"] = list(entry.args)
    if entry.env:
        block["env"] = dict(entry.env)
    servers[entry.name] = block
    _write_atomic(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def _write_opencode(path: Path, entry: Entry) -> None:
    """opencode: ``mcp``, and three ways it differs from everyone else.

    ``command`` is a single array of executable + arguments; the environment key is
    ``environment``; and the toggle is ``enabled``. Getting any of these wrong
    produces a config that validates and silently does nothing.
    """
    data = _read_jsonc(path)
    servers = data.setdefault("mcp", {})
    if not isinstance(servers, dict):
        raise ValueError(f"{path}: `mcp` exists but is not an object")
    block: dict[str, Any] = {
        "type": "local",
        "command": [entry.command, *entry.args],
        "enabled": True,
    }
    if entry.env:
        block["environment"] = dict(entry.env)
    servers[entry.name] = block
    _write_atomic(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def _write_openclaw(path: Path, entry: Entry) -> None:
    """OpenClaw: ``mcp.servers``."""
    data = _read_json(path)
    mcp = data.setdefault("mcp", {})
    if not isinstance(mcp, dict):
        raise ValueError(f"{path}: `mcp` exists but is not an object")
    servers = mcp.setdefault("servers", {})
    if not isinstance(servers, dict):
        raise ValueError(f"{path}: `mcp.servers` exists but is not an object")
    block: dict[str, Any] = {"command": entry.command}
    if entry.args:
        block["args"] = list(entry.args)
    if entry.env:
        block["env"] = dict(entry.env)
    servers[entry.name] = block
    _write_atomic(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def _write_project_json(path: Path, entry: Entry) -> None:
    """A project-local ``.mcp.json``, which is the same shape as Claude's."""
    _write_claude(path, entry)


# --------------------------------------------------------------------------- #
# path resolution
# --------------------------------------------------------------------------- #


def _home() -> Path:
    return Path(os.path.expanduser("~"))


def _claude_path() -> Optional[Path]:
    return _home() / ".claude.json"


def _codex_path() -> Optional[Path]:
    # CODEX_HOME relocates the whole config directory, verified against the CLI.
    root = os.environ.get("CODEX_HOME")
    return (Path(root) if root else _home() / ".codex") / "config.toml"


def _opencode_path() -> Optional[Path]:
    """Prefer an existing config file over creating a second one.

    This machine has ``opencode.jsonc`` and no ``opencode.json``. Creating the
    latter would leave two global configs with unclear precedence, so the existing
    file wins; the ``.json`` name is only used when neither exists.
    """
    base = Path(os.environ.get("XDG_CONFIG_HOME") or (_home() / ".config")) / "opencode"
    for name in ("opencode.jsonc", "opencode.json"):
        candidate = base / name
        if candidate.is_file():
            return candidate
    return base / "opencode.json"


def _openclaw_path() -> Optional[Path]:
    override = os.environ.get("OPENCLAW_CONFIG_PATH")
    if override:
        return Path(override)
    return _home() / ".openclaw" / "openclaw.json"


def _hermes_path() -> Optional[Path]:
    """Where Hermes keeps its config, which is *not* ``~/.hermes`` on Windows.

    Read from Hermes' own ``hermes_constants._get_platform_default_hermes_home``:

        if sys.platform == "win32":
            return Path(os.environ["LOCALAPPDATA"]) / "hermes"
        return Path.home() / ".hermes"

    and ``HERMES_HOME`` overrides both. Writing ``~/.hermes/config.yaml`` on
    Windows produces a file the harness never reads, which is the worst version of
    this failure: the installer reports success, the file looks right, and
    `hermes mcp list` says "No MCP servers configured" with nothing to explain the
    gap. Verified by writing the file and asking Hermes to list it.
    """
    override = os.environ.get("HERMES_HOME", "").strip()
    if override:
        return Path(override) / "config.yaml"
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA", "").strip()
        base = Path(local) if local else _home() / "AppData" / "Local"
        return base / "hermes" / "config.yaml"
    return _home() / ".hermes" / "config.yaml"


# --------------------------------------------------------------------------- #
# the registry
# --------------------------------------------------------------------------- #

HARNESSES: tuple[Harness, ...] = (
    Harness(
        id="claude",
        label="Claude Code",
        config_path=_claude_path,
        fmt="json",
        location="top-level `mcpServers` in ~/.claude.json",
        write=_write_claude,
        verify=("claude", "mcp", "list"),
        detect=("claude",),
    ),
    Harness(
        id="codex",
        label="Codex CLI",
        config_path=_codex_path,
        fmt="toml",
        location="`[mcp_servers.<name>]` in ~/.codex/config.toml",
        write=_write_codex,
        verify=("codex", "mcp", "list"),
        detect=("codex",),
    ),
    Harness(
        id="opencode",
        label="opencode",
        config_path=_opencode_path,
        fmt="json",
        location="`mcp.<name>` in ~/.config/opencode/opencode.json",
        write=_write_opencode,
        verify=("opencode", "mcp", "list"),
        detect=("opencode",),
    ),
    Harness(
        id="openclaw",
        label="OpenClaw",
        config_path=_openclaw_path,
        fmt="json",
        location="`mcp.servers.<name>` in ~/.openclaw/openclaw.json",
        write=_write_openclaw,
        verify=("openclaw", "mcp", "list"),
        detect=("openclaw",),
    ),
    Harness(
        id="hermes",
        label="Hermes",
        config_path=_hermes_path,
        fmt="yaml",
        location="`mcp_servers.<name>` in the Hermes home (`HERMES_HOME`, else the platform default)",
        write=_write_hermes,
        # Verifiable after all. This used to be None, on the grounds that the
        # runtime is not always present - and that is how a wrong config path
        # survived: the installer reported success, the file looked right, and
        # nothing ever asked Hermes whether it could see the server. It could not.
        verify=("hermes", "mcp", "list"),
        detect=("hermes",),
    ),
    Harness(
        id="pi",
        label="pi",
        config_path=None,
        fmt="none",
        location="no config surface exists",
        write=lambda path, entry: None,
        verify=None,
        detect=("pi",),
        unsupported_reason=(
            "pi has no native MCP support. Its settings reference contains no MCP key and its "
            "own feature request for MCP is titled 'Add MCP extension example' - MCP in pi is an "
            "extension you build, so there is no config file an installer can write."
        ),
    ),
)

_BY_ID: Mapping[str, Harness] = {h.id: h for h in HARNESSES}


def _which(executable: str) -> Optional[str]:
    return shutil.which(executable)


def detect_harnesses() -> list[tuple[Harness, bool, Optional[Path]]]:
    """Every known harness, whether it is installed, and its config path."""
    found = []
    for harness in HARNESSES:
        installed = any(_which(exe) for exe in harness.detect) if harness.detect else False
        if not installed and harness.config_path is not None:
            # A config file that already exists is proof enough, even if the
            # executable is off this shell's PATH.
            try:
                path = harness.config_path()
            except Exception:  # noqa: BLE001
                path = None
            if path is not None and path.is_file():
                installed = True
        try:
            path = harness.config_path() if harness.config_path else None
        except Exception:  # noqa: BLE001
            path = None
        found.append((harness, installed, path))
    return found


def build_entry(
    name: str,
    *,
    python: str,
    url: Optional[str] = None,
) -> Entry:
    """The stdio entry that runs this package as an MCP server.

    Points at the interpreter directly rather than at a console script. A console
    script on Windows is a ``.cmd`` shim, and the MCP SDK spawns with
    ``shell: false``, so the shim cannot be executed - the interpreter is the only
    form that works everywhere without a wrapper. ``-m laya_mcp`` is used rather
    than the ``laya-mcp`` script for the same reason.
    """
    if url:
        # An HTTP endpoint is not a stdio entry; the caller is expected to know
        # that only the streamable-http harnesses can take it. Handled by the
        # caller, which is why this raises rather than guessing at a schema.
        raise ValueError(
            "registering an HTTP endpoint needs a per-harness transport key; "
            "run without --url for a stdio registration"
        )
    return Entry(name=name, command=python, args=["-m", "laya_mcp", "mcp"]).windows_safe()


def install(
    *,
    harness: Optional[str] = None,
    name: str = DEFAULT_SERVER_NAME,
    url: Optional[str] = None,
    python: Optional[str] = None,
    dry_run: bool = False,
    project: Optional[str] = None,
) -> int:
    """Write the registration into every detected harness. Returns an exit code."""
    interpreter = python or sys.executable
    try:
        entry = build_entry(name, python=interpreter, url=url)
    except ValueError as exc:
        print(f"laya-mcp: {exc}", file=sys.stderr)
        return 2

    targets = detect_harnesses()
    if harness:
        wanted = {part.strip() for part in harness.split(",") if part.strip()}
        unknown = wanted - set(_BY_ID)
        if unknown:
            print(
                f"laya-mcp: unknown harness {', '.join(sorted(unknown))}; "
                f"known: {', '.join(sorted(_BY_ID))}",
                file=sys.stderr,
            )
            return 2
        targets = [t for t in targets if t[0].id in wanted]

    print(f"registering `{entry.name}` -> {entry.command} {' '.join(entry.args)}")
    if dry_run:
        print("(dry run: nothing will be written)\n")

    configured = 0
    skipped = 0
    failed = 0

    for target, present, path in targets:
        if target.unsupported_reason is not None:
            if present:
                print(f"  {target.label:<12} SKIPPED - {target.unsupported_reason}")
                skipped += 1
            continue
        if not present:
            continue
        if path is None:
            continue

        print(f"  {target.label:<12} {path}")
        if dry_run:
            print(f"               would write {target.location}")
            configured += 1
            continue

        try:
            backup = _backup(path)
            target.write(path, entry)
        except Exception as exc:  # noqa: BLE001 - one harness failing must not stop the rest
            print(f"               FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
            failed += 1
            continue

        where = f"{target.location}"
        if backup is not None:
            where += f"  (backup: {backup.name})"
        print(f"               wrote {where}")
        configured += 1

        if target.verify and _which(target.verify[0]):
            _report_verification(target)

    # A project-local file, if asked for. Separate from the global write because
    # it is a different file with a different lifetime.
    if project and not dry_run:
        project_file = Path(project) / ".mcp.json"
        try:
            backup = _backup(project_file)
            _write_project_json(project_file, entry)
            print(f"  {'project':<12} {project_file}")
            if backup is not None:
                print(f"               (backup: {backup.name})")
            configured += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  project      FAILED: {exc}", file=sys.stderr)
            failed += 1

    print()
    if configured == 0 and skipped == 0:
        print("no supported harness was detected; nothing was written.")
        print("Run `laya-mcp install --harness <id> --dry-run` to see the target paths.")
        return 1
    print(f"{configured} harness(es) configured, {skipped} skipped, {failed} failed.")
    if failed:
        return 1
    print(
        "\nVerify with the harness's own lister - re-reading the file only proves it was "
        "written, not that the harness accepted it."
    )
    return 0


def _report_verification(harness: Harness) -> None:
    """Ask the harness itself whether it sees the server.

    Best-effort and quiet: the lister may be slow, may prompt, or may not exist in
    this build. A failure here is not a failure of the install, so it is reported
    without changing the exit code.
    """
    assert harness.verify is not None
    argv = _launchable(list(harness.verify))
    try:
        completed = subprocess.run(  # noqa: S603 - a fixed argv from our own table
            argv,
            capture_output=True,
            text=True,
            # These CLIs print UTF-8 - box drawing, check marks, non-ASCII paths -
            # and without this, `text=True` decodes with the console code page
            # instead. On a GBK console that raises inside subprocess's reader
            # thread, stdout comes back empty, and the verification reports "ran
            # but did not list" for a server the harness had just listed.
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"               (could not run `{' '.join(harness.verify)}`: {exc})")
        return
    if completed.returncode != 0:
        print(f"               (`{' '.join(harness.verify)}` exited {completed.returncode})")
        return
    output = (completed.stdout or "").strip().splitlines()
    for line in output[:20]:
        if DEFAULT_SERVER_NAME in line:
            print(f"               harness reports: {line.strip()}")
            return
    print(f"               `{' '.join(harness.verify)}` ran but did not list `{DEFAULT_SERVER_NAME}`")


def _launchable(argv: list[str]) -> list[str]:
    """Make a harness lister actually runnable on Windows.

    Every one of these CLIs is installed by npm, and npm writes a ``.cmd`` shim
    next to the real entry point. ``shutil.which`` finds it - ``.CMD`` is in
    PATHEXT - but ``CreateProcess`` cannot execute it, so the call fails with
    ``WinError 2``: "the system cannot find the file specified", for a file that
    plainly exists. This is the same trap the MCP registration already avoids by
    pointing harnesses at ``python -m laya_mcp`` rather than the console script.

    The cost of not handling it was concrete: the verification step silently
    degraded to "(could not run ...)", which is why nothing noticed that Hermes
    reads its config from a different directory on Windows.
    """
    if sys.platform != "win32" or not argv:
        return argv
    resolved = shutil.which(argv[0])
    if resolved and resolved.lower().endswith((".cmd", ".bat")):
        return ["cmd.exe", "/c", resolved, *argv[1:]]
    return argv


def describe_targets() -> int:
    """Print what would be configured, without writing anything."""
    for harness, present, path in detect_harnesses():
        mark = "installed" if present else "-"
        print(f"{harness.id:<12} {mark:<10} {path if path else '-'}")
        print(f"{'':<12} {'':<10} {harness.location}")
        if harness.unsupported_reason:
            print(f"{'':<12} {'':<10} NOTE: {harness.unsupported_reason}")
    return 0
