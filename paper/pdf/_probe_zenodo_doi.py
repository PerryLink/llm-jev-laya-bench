"""Ask the Zenodo API which metadata field it considers required.

WHY: the deposit form says "Basic information 1 Error(s) -- Missing DOI for
required field", and Publish is disabled. The obvious reading is "the DOI box
must be filled", but filling it with a DOI you do not have would be wrong, and
the actual InvenioRDM rule may be narrower -- e.g. the DOI field is only
validated when some toggle is on.

Zenodo's REST API runs the SAME validation as the form, so posting a minimal
metadata payload and reading the 400 response names the offending field
directly. This is a read-only diagnostic: it POSTs to /api/records with no
token, so the request cannot create anything. Any answer we get is either
"Authentication required" (no information) or a validation error (information).

Runs the probe three ways so the missing/empty/present cases can be compared:
  A. no `pids` block at all
  B. explicit empty doi
  C. a dummy doi
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

URL = "https://sandbox.zenodo.org/api/records"

BASE = {
    "metadata": {
        "title": "probe",
        "publication_date": "2026-09-22",
        "resource_type": {"id": "publication-preprint"},
        "creators": [{"person_or_org": {
            "type": "personal",
            "family_name": "Link", "given_name": "Perry"}}],
        "description": "probe",
        "publisher": "Zenodo",
    }
}

CASES = {
    "A no pids block": {},
    "B pids with empty doi": {"pids": {"doi": {"identifier": "", "provider": "external"}}},
    "C pids with dummy doi": {"pids": {"doi": {"identifier": "10.1234/probe.test", "provider": "external"}}},
}

for label, extra in CASES.items():
    body = json.loads(json.dumps(BASE))
    body.update(extra)
    req = urllib.request.Request(
        URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    print(f"\n=== {label} ===")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"  HTTP {r.status} -- request ACCEPTED (unexpected without a token)")
            print("  " + r.read()[:300].decode(errors="replace"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        print(f"  HTTP {e.code}")
        try:
            j = json.loads(raw)
            print(f"  status : {j.get('status')}")
            print(f"  message: {j.get('message')}")
            errs = j.get("errors")
            if errs:
                for err in errs:
                    print(f"    field={err.get('field')!r}  messages={err.get('messages')}")
            else:
                print("  (no per-field errors)")
        except json.JSONDecodeError:
            print("  " + raw[:400])
    except Exception as e:                                   # pragma: no cover
        print(f"  {type(e).__name__}: {e}")
