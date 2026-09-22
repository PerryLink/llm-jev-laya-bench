"""Fetch and verify the Banking77 item pool.

WHY A SCRIPT RATHER THAN A VENDORED COPY
----------------------------------------
Banking77 is CC-BY-4.0, which permits redistribution with attribution, so committing the
CSVs would be lawful. It is still the wrong default:

  * a vendored copy becomes a second source of truth that silently goes stale;
  * it adds a licence chain to track for no reproducibility gain;
  * the thing that actually makes the pool reproducible is the HASH, not the file's
    presence -- and a hash can be checked against upstream in one command.

`.gitignore` therefore excludes `data/banking77/*.csv` by default. Set `BENCH_VENDOR_DATA=1`
if you deliberately want them committed.

WHY THE HASHES ARE PINNED HERE
------------------------------
The published numbers were measured on one particular revision of the CSVs. "We used
Banking77" is not reproducible; "we used the file whose SHA256 is 430F6795..." is. If
upstream ever reissues the dataset, this script tells you instead of quietly changing every
downstream number.

    python src/analysis/fetch_data.py --check      # verify what is on disk (offline)
    python src/analysis/fetch_data.py --fetch      # download what is missing, then verify

Upstream: https://github.com/PolyAI-LDN/task-specific-datasets
Licence:  CC-BY-4.0
Cite:     Casanueva et al. (2020), arXiv:2003.04807
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import DATA  # noqa: E402

TARGET = DATA / "banking77"
BASE = ("https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets"
        "/master/banking_data")

# SHA256 of the revision every published number in this repository was measured against.
PINNED: dict[str, dict] = {
    "categories.json": {
        "sha256": "AA9816A222577ECE5399307478787A732BFCBEF5411A1079836C093559EC254A",
        "bytes": 2039,
        "note": "carries a UTF-8 BOM; read it with encoding='utf-8-sig'",
    },
    "train.csv": {
        "sha256": "430F67959418D85742B7B8D18D3D10A3DC507A922F7D150E37BB6FB5CB52D20A",
        "bytes": 839076},
    "test.csv": {
        "sha256": "06DF876211F53776F7B9DD743F914E91900682A9D99E1B7C2BA24685FCF72D4D",
        "bytes": 239964},
}

LICENCE_NOTE = """\
# Banking77 -- data/banking77/

**Licence: CC-BY-4.0** (Creative Commons Attribution 4.0 International).
Upstream: <https://github.com/PolyAI-LDN/task-specific-datasets>

The dataset is used **unmodified**, solely as an evaluation item pool.

## Citation

> Inigo Casanueva, Tadas Temcinas, Daniela Gerz, Matthew Henderson, Ivan Vulic.
> *Efficient Intent Detection with Dual Sentence Encoders.*
> Proceedings of the 2nd Workshop on NLP for ConvAI, ACL 2020.
> <https://arxiv.org/abs/2003.04807>

## Reproduce this exact revision

```bash
python src/analysis/fetch_data.py --check     # verify the hashes below
python src/analysis/fetch_data.py --fetch     # download if missing
```

| file | bytes | SHA256 |
|---|---|---|
"""


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def check(verbose: bool = True) -> tuple[list[str], list[str]]:
    ok, bad = [], []
    for name, rec in PINNED.items():
        p = TARGET / name
        if not p.exists():
            bad.append(f"{name}: MISSING")
            continue
        h = sha256_file(p)
        if h == rec["sha256"]:
            ok.append(name)
            if verbose:
                print(f"  ok    {name:18s} {p.stat().st_size:>9d} bytes  {h[:16]}...")
        else:
            bad.append(f"{name}: hash {h[:16]}... != pinned {rec['sha256'][:16]}...")
            if verbose:
                print(f"  BAD   {name:18s} {p.stat().st_size:>9d} bytes  {h[:16]}...")
    return ok, bad


def fetch() -> None:
    TARGET.mkdir(parents=True, exist_ok=True)
    for name in PINNED:
        dest = TARGET / name
        if dest.exists() and sha256_file(dest) == PINNED[name]["sha256"]:
            print(f"  have  {name}")
            continue
        url = f"{BASE}/{name}"
        print(f"  get   {name}  <- {url}")
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                dest.write_bytes(r.read())
        except Exception as exc:
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
            print("        download it by hand from the upstream repository and place it in")
            print(f"        {TARGET}")


def write_readme() -> None:
    rows = "".join(
        f"| `{n}` | {r['bytes']} | `{r['sha256']}` |\n" for n, r in PINNED.items())
    extra = ("\n## Note\n\n`categories.json` carries a **UTF-8 BOM**. Read it with "
             "`encoding=\"utf-8-sig\"` or `json.loads` raises on the first character.\n\n"
             "## Contamination\n\nBanking77 is in the judge's prior training set, and the "
             "paper records that the *generator's* exposure is stronger still -- so "
             "contamination runs **with** the negative result rather than against it. No "
             "accuracy claim in this repository should be read without that caveat.\n")
    (TARGET / "README.md").write_text(LICENCE_NOTE + rows + extra, encoding="utf-8")
    print(f"  wrote {TARGET / 'README.md'}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fetch", action="store_true", help="download missing files")
    ap.add_argument("--check", action="store_true", help="verify only (default)")
    a = ap.parse_args()

    if a.fetch:
        print("fetching:")
        fetch()
    print("verifying against the pinned revision:")
    ok, bad = check()
    if not a.fetch:
        write_readme()
    print(f"\n{len(ok)}/{len(PINNED)} files match the pinned revision")
    for b in bad:
        print(f"  ! {b}")
    if bad:
        print("\nA mismatch means the item pool is NOT the one the paper measured.")
        print("Do not re-run a published battery against it without re-deriving the numbers.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
