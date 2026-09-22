"""Which PID actually serves :8787? Attribution by CPU-time delta, read-only.

Sends ONE tiny typed query and measures each candidate process's CPU time before and
after. The server that answers is the one whose CPU time moves. Nothing is restarted,
reconfigured or killed.
"""
from __future__ import annotations

import json
import subprocess
import time
import urllib.request

PIDS = [22148, 22316, 20892, 7156, 25972, 26068]


def cpu_times() -> dict[int, float]:
    ps = ("Get-Process -Id " + ",".join(str(p) for p in PIDS) +
          " -ErrorAction SilentlyContinue | "
          "ForEach-Object { \"$($_.Id) $($_.TotalProcessorTime.TotalSeconds)\" }")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True).stdout
    d = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 2:
            try:
                d[int(parts[0])] = float(parts[1])
            except ValueError:
                pass
    return d


def ask() -> dict:
    body = json.dumps({
        "state": {"body": "The vault access code is AAA-1111."},
        "questions": {"q": {"type": "noul",
                            "instructions": "Is the vault access code AAA-1111?",
                            "criteria": {"true": "the state says AAA-1111",
                                         "false": "the state does not say AAA-1111"}}},
    }).encode()
    req = urllib.request.Request("http://127.0.0.1:8787/ask", data=body,
                                headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


before = cpu_times()
t0 = time.perf_counter()
resp = ask()
wall = (time.perf_counter() - t0) * 1000
time.sleep(1.0)
after = cpu_times()

print("one noul query returned:", json.dumps(resp)[:260])
print(f"wall {wall:.0f} ms")
print()
print(f"{'pid':>7} {'cpu_before':>12} {'cpu_after':>12} {'delta_s':>9}")
for p in PIDS:
    b, a = before.get(p), after.get(p)
    if b is None or a is None:
        print(f"{p:>7} {'-':>12} {'-':>12} {'gone':>9}")
        continue
    print(f"{p:>7} {b:>12.3f} {a:>12.3f} {a - b:>9.3f}")
