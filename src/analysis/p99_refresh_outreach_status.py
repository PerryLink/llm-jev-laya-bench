"""Regenerate OUTREACH.md's status block from the live APIs, so the statuses cannot rot.

WHY THIS EXISTS
---------------
`OUTREACH.md` lists six posts and their outcomes. That table was written by hand with every row
reading `OPEN`; four of the six had been merged the same day. It was then corrected by hand, and
went stale again within two days, this time because the whole upstream situation had moved: one
issue closed, another was closed as `not_planned` against the wrong project, and the account's
footprint in that repository grew from four merged PRs to twenty-four.

That is the same lesson as `results/ERRATA.md` section 13, applied to a second document: **a status
that is typed will rot, because nothing reads it.** So this script reads it. It queries GitHub and
Zenodo and rewrites the block between the two markers in `OUTREACH.md`, and it derives even the
descriptions from the live titles rather than restating them.

WHAT IT WRITES, AND WHAT IT REFUSES TO WRITE
--------------------------------------------
Only the text between
    <!-- BEGIN GENERATED: status ... -->
    <!-- END GENERATED: status -->
is replaced. If any line outside that block would change, the script refuses and says so -- the same
guard `p97_sync_declared_counts.py` uses, and for the same reason: a rewrite that moves lines it was
not asked to touch is the signature of a line-ending or encoding change, not of an update. Files are
opened with `newline=""` so a read-modify-write cannot convert LF to CRLF.

If any API call fails, nothing is written. A partial block would replace a stale-but-true status with
a fresh-but-wrong one, which is worse than leaving it alone.

Usage:
    python src/analysis/p99_refresh_outreach_status.py            # rewrite the block
    python src/analysis/p99_refresh_outreach_status.py --check     # report only; non-zero if stale
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import ROOT  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

DOC = ROOT / "OUTREACH.md"
BEGIN = "<!-- BEGIN GENERATED: status"
END = "<!-- END GENERATED: status -->"

ZENODO = {22901853: "English paper", 22902025: "Chinese paper", 22901248: "artifact"}

# The six posts, as (label, owner, repo, kind, number). The TITLES are read from the API, not typed
# here, so a renamed pull request cannot leave this table describing something that no longer exists.
POSTS = [
    ("**Defect report**", "NandhaKishorM", "laya", "issues", 174),
    ("**Defect report**", "typesafe-ai", "typesafe-sdk-python", "issues", 11),
    ("One entry, *Open reproductions and research*", "cobanov", "awesome-jev", "pulls", 77),
    ("One entry, *Evaluations and independent research*",
     "AbdelStark", "awesome-typesafe-jev", "pulls", 99),
    ("One table row, *Benchmarks, calibration, and open reproductions*",
     "Anil-matcha", "awesome-jev-by-typesafe", "pulls", 63),
    ("One entry, *Calibration & Research* (source file and README mirror)",
     "yibie", "awesome-jev", "pulls", 155),
]

FOOTPRINT_REPO = ("NandhaKishorM", "laya")
FOOTPRINT_USER = "PerryLink"
OWN_REPO = "PerryLink/llm-jev-laya-bench"

errors: list[str] = []


def gh(path: str):
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    if out.returncode != 0:
        errors.append(f"gh api {path}: {(out.stderr or '').strip()[:120]}")
        return None
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError as exc:
        errors.append(f"gh api {path}: {exc}")
        return None


def zenodo(record: int):
    req = urllib.request.Request(f"https://zenodo.org/api/records/{record}",
                                 headers={"User-Agent": "p99-outreach-status/1"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
    except Exception as exc:  # noqa: BLE001
        errors.append(f"zenodo {record}: {type(exc).__name__}")
        return None


def stamp(iso: str | None) -> str:
    """`2026-09-23T13:43:43Z` -> `2026-09-23 13:43 UTC`."""
    if not iso:
        return "?"
    return f"{iso[:10]} {iso[11:16]} UTC"


def _style(text: str) -> str:
    """LF, CRLF or MIXED -- so a rewrite cannot quietly convert the whole file."""
    crlf = text.count("\r\n")
    lone_lf = text.count("\n") - crlf
    if crlf and lone_lf:
        return "MIXED"
    return "CRLF" if crlf else "LF"


def approx(n: int | None) -> str:
    """A star count rounded to the nearest hundred.

    Exact counts would make this block stale every few minutes on a repository that is being
    starred, and a status table that always reads STALE is one nobody regenerates. The rounding is
    marked, so nothing here claims a precision it does not have.
    """
    if n is None:
        return "?"
    return f"≈{round(n, -2):,}"


def status_cell(item: dict, kind: str) -> str:
    if kind == "pulls":
        if item.get("merged_at"):
            who = (item.get("merged_by") or {}).get("login", "?")
            return f"✅ **MERGED** {stamp(item['merged_at'])} by `{who}`"
        if item["state"] == "closed":
            return f"**CLOSED, not merged** {stamp(item.get('closed_at'))}"
        return f"**OPEN** — {item['comments']} comment(s)"
    if item["state"] == "closed":
        reason = item.get("state_reason") or "closed"
        return f"**CLOSED** (`{reason}`) {stamp(item.get('closed_at'))}"
    return f"**OPEN** — {item['comments']} comment(s), last change {stamp(item.get('updated_at'))}"


def main() -> int:
    check_only = "--check" in sys.argv

    rows, seen_times = [], []
    for i, (label, owner, repo, kind, num) in enumerate(POSTS, 1):
        item = gh(f"repos/{owner}/{repo}/{kind}/{num}")
        if item is None:
            continue
        seen_times.append(item.get("updated_at") or item.get("closed_at") or "")
        title = " ".join((item.get("title") or "").split())
        url = item.get("html_url") or f"https://github.com/{owner}/{repo}"
        rows.append(f"| {i} | {label} — {title} | [{owner}/{repo}#{num}]({url}) "
                    f"| {status_cell(item, kind)} |")

    # --- this account's footprint in the repository the reports went to ----------------------
    owner, repo = FOOTPRINT_REPO
    items = []
    for state in ("open", "closed"):
        page = gh(f"repos/{owner}/{repo}/issues?state={state}&creator={FOOTPRINT_USER}"
                  f"&per_page=100")
        if page is None:
            continue
        if len(page) == 100:
            errors.append(f"{owner}/{repo}: 100 results, pagination needed")
        items.extend(page)
    merged = sorted(i["number"] for i in items
                    if "pull_request" in i and i["pull_request"].get("merged_at"))
    open_prs = sorted(i["number"] for i in items
                      if "pull_request" in i and i["state"] == "open")
    dead_prs = sorted(i["number"] for i in items
                      if "pull_request" in i and i["state"] == "closed"
                      and not i["pull_request"].get("merged_at"))
    closed_iss = sorted(i["number"] for i in items if "pull_request" not in i
                        and i["state"] == "closed")
    open_iss = sorted(i["number"] for i in items if "pull_request" not in i and i["state"] == "open")
    for i in items:
        seen_times.append(i.get("updated_at") or "")

    repo_info = gh(f"repos/{owner}/{repo}") or {}
    stars = repo_info.get("stargazers_count")

    # --- reach ------------------------------------------------------------------------------
    zrows, zmax = [], ""
    for rec, name in ZENODO.items():
        d = zenodo(rec)
        if d is None:
            continue
        st = d.get("stats", {})
        zmax = max(zmax, d.get("updated") or "")
        zrows.append(f"| Zenodo, {name} | [{rec}](https://zenodo.org/records/{rec}) — "
                     f"{st.get('unique_views')} views · {st.get('unique_downloads')} downloads |")
    clones = gh(f"repos/{OWN_REPO}/traffic/clones") or {}

    if errors:
        print("REFUSING to write -- not every source answered:")
        for e in errors:
            print("  - " + e)
        print("\nA partial block would replace a stale-but-true status with a fresh-but-wrong one.")
        return 2

    as_of = stamp(max(t for t in seen_times + [zmax] if t))
    body = f"""### Status, regenerated from the live APIs

*Derived by `src/analysis/p99_refresh_outreach_status.py`; the most recent change among these items
is {as_of}. Nothing in this block is typed by hand.*

| # | What was sent | Where | Status |
|---|---|---|---|
{chr(10).join(rows)}

### This account's footprint in `{owner}/{repo}`

| | count |
|---|---|
| PRs **merged** | **{len(merged)}** |
| PRs open | {len(open_prs)} |
| PRs closed unmerged | {len(dead_prs)} |
| issues closed | {len(closed_iss)} |
| issues open | {len(open_iss)} |

**Merged:** {", ".join(f"#{n}" for n in merged) or "—"}

**Open now:** {", ".join(f"#{n}" for n in sorted(open_prs + open_iss)) or "—"}

### Reach

| | value |
|---|---|
| `{owner}/{repo}` | {approx(stars)} stars |
{chr(10).join(zrows)}
| this repository, clones (last 14 days) | {clones.get('count')} ({clones.get('uniques')} unique) |
| this repository | {approx(gh(f"repos/{OWN_REPO}").get('stargazers_count'))} stars |
"""

    with DOC.open(encoding="utf-8", newline="") as fh:
        text = fh.read()

    start = text.find(BEGIN)
    end = text.find(END)
    if start == -1 or end == -1 or end < start:
        print(f"REFUSING to write -- markers not found in {DOC.name}")
        return 2
    end += len(END)
    new = text[:start] + BEGIN + " -->\n" + body + END + text[end:]

    if new == text:
        print("  status block is already current")
        print(f"  {len(merged)} PRs merged, {len(open_prs)} open, "
              f"{len(closed_iss)} issues closed, {len(open_iss)} open; ★{stars:,}")
        return 0

    # This is a splice, not a substitution, so the file legitimately grows and a line-count guard
    # like p97's would be wrong here. What must hold is narrower and checkable: the text outside the
    # block is carried over byte for byte, and the file's newline style does not move. The second
    # matters because `.gitattributes` sets `* -text`, so in this repository an ending change is a
    # real change touching every line rather than a normalisation.
    if not (new.startswith(text[:start]) and new.endswith(text[end:])):
        print("REFUSING to write -- the splice would alter text outside the block")
        return 2
    if _style(text) != _style(new):
        print(f"REFUSING to write -- newline style would change "
              f"({_style(text)} -> {_style(new)})")
        return 2

    if check_only:
        print(f"STALE -- regenerating would rewrite the {body.count(chr(10))}-line status block "
              f"in {DOC.name}")
        return 1

    with DOC.open("w", encoding="utf-8", newline="") as fh:
        fh.write(new)
    print(f"  rewrote the status block in {DOC.name} ({body.count(chr(10))} lines)")
    print(f"  {len(merged)} PRs merged, {len(open_prs)} open, "
          f"{len(closed_iss)} issues closed, {len(open_iss)} open; ★{stars:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
