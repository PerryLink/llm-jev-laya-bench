"""Pre-push scan: make sure the 11 commits about to go public carry no credential.

The repository already has a credential-echo incident on record
(protocol/INCIDENT-credential-echo.md), and this push is the first one in this
session, so the scan runs against the tree being pushed rather than against
memory. Checks three things:

  1. the tracked tree at HEAD contains no key-shaped string;
  2. the 11 outgoing commits touch no path that could carry one;
  3. .gitignore still excludes the credential store.

Exit non-zero if anything looks like a credential, so a push cannot proceed on
a false assumption.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]

# Shapes that would indicate a real secret. Deliberately narrow: this must not
# fire on the many prose mentions of "credential" in the incident write-up.
PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9_\-]{20,}"), "OpenAI/DeepSeek-style key"),
    (re.compile(r"sk-or-v1-[A-Za-z0-9]{32,}"), "OpenRouter key"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key id"),
    (re.compile(r"ghp_[A-Za-z0-9]{36}"), "GitHub PAT"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{22,}"), "GitHub fine-grained PAT"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key block"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "Slack token"),
]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                          text=True, encoding="utf-8", errors="replace").stdout


def main() -> int:
    fails: list[str] = []

    files = [f for f in git("ls-files").splitlines() if f.strip()]
    print(f"tracked files: {len(files)}")
    hits = 0
    for f in files:
        p = ROOT / f
        try:
            b = p.read_bytes()
        except OSError:
            continue
        if b"\x00" in b[:4096]:            # skip binaries
            continue
        t = b.decode("utf-8", "replace")
        for pat, label in PATTERNS:
            m = pat.search(t)
            if m:
                hits += 1
                fails.append(f"{f}: {label} -- {m.group(0)[:12]}...")
                print(f"  HIT {f}: {label}")
    print(f"  key-shaped strings in tree: {hits}")

    commits = git("log", "--oneline", "origin/master..HEAD").splitlines()
    print(f"\noutgoing commits: {len(commits)}")
    changed = set()
    for line in commits:
        sha = line.split()[0]
        for f in git("show", "--pretty=format:", "--name-only", sha).splitlines():
            if f.strip():
                changed.add(f.strip())
    print(f"  distinct paths touched: {len(changed)}")
    suspicious = [f for f in changed
                  if re.search(r"\.env|credential|secret|\.key$|\.pem$|token",
                               f, re.I)]
    if suspicious:
        fails.append(f"outgoing commits touch sensitive-looking paths: {suspicious}")
        print(f"  FAIL sensitive paths: {suspicious}")
    else:
        print("  ok   no credential-shaped path among the changed files")

    gi = git("check-ignore", "-v", ".dsh/.credentials.yaml")
    if gi.strip():
        print(f"  ok   credential store ignored: {gi.strip().splitlines()[0]}")
    else:
        fails.append(".dsh/.credentials.yaml is NOT ignored")
        print("  FAIL credential store is not ignored")

    print()
    if fails:
        print(f"RESULT: {len(fails)} PROBLEM(S) -- do not push")
        for f in fails:
            print("  - " + f)
        return 1
    print("RESULT: clean -- safe to push")
    return 0


if __name__ == "__main__":
    sys.exit(main())
