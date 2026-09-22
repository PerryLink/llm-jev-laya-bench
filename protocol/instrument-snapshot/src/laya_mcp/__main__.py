"""Entry point for ``python -m laya_mcp``.

This file is load-bearing rather than a convenience, which is worth stating
because its absence is invisible until someone else's machine breaks.

Every harness registration this package writes invokes the server as
``python -m laya_mcp mcp`` rather than through the ``laya-mcp`` console script.
That choice is deliberate: on Windows a console script is a ``.cmd`` shim, and the
MCP SDK spawns stdio servers with ``shell: false``, which cannot execute a shim -
measured on Node v22, ``spawn("npx", {shell:false})`` fails with ``ENOENT`` and
``spawn("npx.cmd", ...)`` with ``EINVAL``, while ``spawn("cmd", ["/c", ...])``
works. An interpreter invocation sidesteps the whole class of problem.

``python -m package`` requires exactly this module. Without it Python reports
"No module named laya_mcp.__main__; 'laya_mcp' is a package and cannot be directly
executed", so a package that installed cleanly and passed its own tests would
still fail to start in every harness it had just registered itself with.
"""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
