"""Repeat the attribution test: does :8787 ever serve from more than one process?

Also reads /health between calls: with two servers behind one port the `calls` counter
would move non-monotonically (each process keeps its own). Read-only.
"""
from __future__ import annotations

import json
import subprocess
import time
import urllib.request

PIDS = [22316, 7156]


def cpu() -> dict:
    ps = ("Get-Process -Id " + ",".join(str(p) for p in PIDS) +
          " -ErrorAction SilentlyContinue | ForEach-Object { "
          "\"$($_.Id) $($_.TotalProcessorTime.TotalSeconds)\" }")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True).stdout
    d = {}
    for line in out.splitlines():
        a = line.split()
        if len(a) == 2:
            try:
                d[int(a[0])] = float(a[1])
            except ValueError:
                pass
    return d


def health() -> dict:
    with urllib.request.urlopen("http://127.0.0.1:8787/health", timeout=10) as r:
        return json.loads(r.read())


def ask(i: int) -> dict:
    body = json.dumps({
        "state": {"body": f"Note {i}: the vault access code is AAA-1111."},
        "questions": {"q": {"type": "noul",
                            "instructions": "Is the vault access code AAA-1111?",
                            "criteria": {"true": "the state says AAA-1111",
                                         "false": "the state does not say AAA-1111"}}},
    }).encode()
    req = urllib.request.Request("http://127.0.0.1:8787/ask", data=body,
                                headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


print("health before:", {k: health().get(k) for k in ("calls", "uptime_s", "loaded")})
for i in range(3):
    b = cpu()
    r = ask(i)
    time.sleep(0.6)
    a = cpu()
    h = health()
    d = {p: round(a.get(p, 0) - b.get(p, 0), 3) for p in PIDS}
    print(f"call {i}: noul={r['answers']['q']['noul']} cpu_delta={d} "
          f"| health calls={h.get('calls')} uptime={h.get('uptime_s')}")
