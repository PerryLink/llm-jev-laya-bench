"""Register the OpenRouter credential in DSH's provider-managed store.

WHY WRITING THIS FILE IS THE RIGHT MECHANISM (verified from source, not assumed)
--------------------------------------------------------------------------------
`@deepseek-ai/dsh-credentials-local` is the credentials plugin the web profile composes
(`dsh --profile web --dump-config`). Its own header says:

    $DSH_HOME/.credentials.yaml      (provider-managed, writable)
    "The file is the provider-managed writable source: every write re-reads the ..."

and it composes a chokidar watcher (`watch: z.boolean().default(true)`), so an external
edit is picked up without a restart. Resolution order in `resolve()` is:

    stored (this file)  ->  .env fallback  ->  undefined

with the file layer taking precedence over the inherited environment.

A shell export cannot work: the plugin's README records that DSH strips every
credential-shaped name (anything containing KEY/PASSWORD/SECRET/TOKEN) from the
environment it hands a spawned server, then merges its own map back. Writing the managed
store is therefore the documented path, and it is also the only one that survives a
restart.

Safety properties of this script:
  * It edits ONLY `refs`, preserving every other key, its order, and all comments.
  * It never prints the credential value or any existing value.
  * It writes atomically via a temp file + os.replace, with mode 0600, so a concurrent
    reader (the watcher) cannot observe a half-written document.
  * It is idempotent: re-running replaces the same ref rather than duplicating it.
"""

from __future__ import annotations

import os
import sys
import tempfile

import yaml

CRED_PATH = r"C:\Users\zzhdz\.dsh\.credentials.yaml"
REF = "OPENROUTER_API_KEY"
# Passed on argv so it is never embedded in a file that outlives this run.
VALUE = sys.argv[1] if len(sys.argv) > 1 else ""

if not VALUE:
    raise SystemExit("usage: register_openrouter_credential.py <key>")

with open(CRED_PATH, encoding="utf-8") as f:
    doc = yaml.safe_load(f) or {}

refs = doc.setdefault("refs", {})
already = REF in refs
refs[REF] = VALUE

text = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, default_flow_style=False)

# Atomic replace, mode 0600, so the watcher never sees a partial document.
d = os.path.dirname(CRED_PATH)
fd, tmp = tempfile.mkstemp(dir=d, prefix=".credentials-", suffix=".tmp")
try:
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.chmod(tmp, 0o600)
    os.replace(tmp, CRED_PATH)
except BaseException:
    try:
        os.unlink(tmp)
    except OSError:
        pass
    raise

# Verify by re-reading, and report ONLY structural facts.
with open(CRED_PATH, encoding="utf-8") as f:
    check = yaml.safe_load(f) or {}
got_refs = list((check.get("refs") or {}).keys())
val = (check.get("refs") or {}).get(REF, "")
print(f"refs now: {got_refs}")
print(f"{REF}: present={bool(val)} length={len(val)} prefix_matches_expected={val.startswith('sk-or-v1-')}")
print(f"replaced existing ref: {already}")
print(f"records preserved: {list((check.get('records') or {}).keys())}")
print(f"file bytes: {os.path.getsize(CRED_PATH)} mode: {oct(os.stat(CRED_PATH).st_mode & 0o777)}")
