"""Verify the two Zenodo records after the in-place file edit.

Checks the files by md5 AND size against the values computed from the local
files, not from recollection -- the same discipline the rest of this project
uses, and the reason a wrong-language upload is caught here rather than by a
reader.

Also reports whether the DOI changed. The whole point of the in-place route is
that it does not, so if it did, every document citing it needs revisiting.

Exit code is non-zero if any check fails.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

ROOT = pathlib.Path(__file__).resolve().parents[1]

# What each record SHOULD hold after the edit. The local files are the source of
# truth for the hashes; nothing here is typed from memory except which file goes
# where, and that is the fact being checked.
EXPECT = {
    "22901853": {
        "label": "English record",
        "doi": "10.5281/zenodo.22901853",
        "concept": "10.5281/zenodo.22901852",
        "files": {
            "paper-en.pdf": ROOT / "paper" / "pdf" / "paper-en.pdf",
            "MANUSCRIPT.md": ROOT / "paper" / "en" / "MANUSCRIPT.md",
        },
    },
    "22902025": {
        "label": "Chinese record",
        "doi": "10.5281/zenodo.22902025",
        "concept": "10.5281/zenodo.22902024",
        "files": {
            "paper-zh.pdf": ROOT / "paper" / "pdf" / "paper-zh.pdf",
            "MANUSCRIPT.md": ROOT / "paper" / "MANUSCRIPT.md",
        },
    },
}

# v1 sizes, so "still the old file" is distinguishable from "wrong new file".
V1_SIZES = {
    "22901853": {"paper-en.pdf": 3_202_893, "MANUSCRIPT.md": 272_899},
    "22902025": {"paper-zh.pdf": 6_924_090, "MANUSCRIPT.md": 227_497},
}

fails: list[str] = []


def local(rel: pathlib.Path) -> tuple[int, str]:
    b = rel.read_bytes()
    return len(b), hashlib.md5(b).hexdigest()


for rec, spec in EXPECT.items():
    d = json.loads(
        urllib.request.urlopen(f"https://zenodo.org/api/records/{rec}", timeout=60)
        .read().decode()
    )
    m = d["metadata"]
    print("=" * 76)
    print(f"{spec['label']}   https://zenodo.org/records/{rec}")
    print("=" * 76)

    # --- DOI must be unchanged -------------------------------------------------
    got_doi = d.get("doi")
    got_concept = d.get("conceptdoi")
    if got_doi == spec["doi"]:
        print(f"  ok   DOI unchanged: {got_doi}")
    else:
        fails.append(f"{rec}: DOI changed to {got_doi}, expected {spec['doi']}")
        print(f"  FAIL DOI is {got_doi}, expected {spec['doi']}")
    if got_concept == spec["concept"]:
        print(f"  ok   concept DOI unchanged: {got_concept}")
    else:
        fails.append(f"{rec}: concept DOI changed to {got_concept}")
        print(f"  FAIL concept DOI is {got_concept}")

    # --- metadata sanity ------------------------------------------------------
    if rec == "22902025":
        t = m.get("title") or ""
        c = t[12] if len(t) > 12 else ""
        if c == "\uff1a":
            print("  ok   title colon is FULL-WIDTH (U+FF1A)")
        else:
            print(f"  note title colon is {c!r} (U+{ord(c):04X} if set) -- "
                  f"author has ruled this out of scope; recorded, not failed")
    print(f"       title: {(m.get('title') or '')[:70]}")
    print(f"       language: {m.get('language')}  license: {(m.get('license') or {}).get('id')}")

    # --- files ----------------------------------------------------------------
    remote = {f["key"]: (f["size"], (f.get("checksum") or "").replace("md5:", ""))
              for f in (d.get("files") or [])}
    print(f"       files on record: {sorted(remote)}")
    for key, rel in spec["files"].items():
        if key not in remote:
            fails.append(f"{rec}: {key} missing from the record")
            print(f"  FAIL {key} missing")
            continue
        rsize, rmd5 = remote[key]
        lsize, lmd5 = local(rel)
        if rsize == lsize and rmd5 == lmd5:
            print(f"  ok   {key:16} {rsize:>9,} bytes  md5 matches local")
        elif rsize == V1_SIZES[rec].get(key):
            fails.append(f"{rec}: {key} is still the v1 file ({rsize} bytes)")
            print(f"  FAIL {key:16} {rsize:>9,} bytes is the OLD v1 size")
        else:
            fails.append(
                f"{rec}: {key} is {rsize} bytes / {rmd5[:12]}, "
                f"expected {lsize} / {lmd5[:12]}"
            )
            print(f"  FAIL {key:16} {rsize:>9,} md5 {rmd5[:12]} != local "
                  f"{lsize:>9,} md5 {lmd5[:12]}")
    extra = set(remote) - set(spec["files"])
    if extra:
        print(f"  note unexpected extra file(s) on the record: {sorted(extra)}")

    # --- related works --------------------------------------------------------
    rel_ids = [(r.get("relation"), r.get("identifier"))
               for r in (m.get("related_identifiers") or [])]
    print(f"       related works: {rel_ids}")
    print()

print("=" * 76)
if fails:
    print(f"RESULT: {len(fails)} problem(s)")
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print("RESULT: both records carry the corrected files, and both DOIs are unchanged")
