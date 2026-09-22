"""READ-ONLY probe of the live sidecar: is there more than one server behind :8787?

Does not restart, reconfigure or kill anything. It only reads /health repeatedly and
records the process-level facts that are visible from outside.
"""
from __future__ import annotations

import json
import time
import urllib.request

BASE = "http://127.0.0.1:8787"


def health() -> dict:
    with urllib.request.urlopen(BASE + "/health", timeout=8) as r:
        return json.loads(r.read())


print("repeat /health reads (uptime_s and calls identify a PROCESS):")
seen = {}
for i in range(8):
    try:
        h = health()
    except Exception as exc:
        print(f"  [{i}] ERROR {exc}")
        continue
    key = (h.get("uptime_s"), h.get("calls"))
    seen.setdefault(key, 0)
    seen[key] += 1
    print(f"  [{i}] ok={h.get('ok')} loaded={h.get('loaded')} calls={h.get('calls')} "
          f"uptime_s={h.get('uptime_s')} checkpoints={sorted((h.get('checkpoints') or {}).keys())}")
    time.sleep(0.4)

print()
print("distinct (uptime_s, calls) tuples seen:", len(seen))
for k, v in seen.items():
    print("   ", k, "x", v)

try:
    with urllib.request.urlopen(BASE + "/version", timeout=8) as r:
        print("\n/version:", r.read().decode()[:300])
except Exception as exc:
    print("\n/version ERROR:", exc)
