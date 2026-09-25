"""Verify the two Zenodo records against the revision that was actually uploaded.

WHY THIS NO LONGER COMPARES AGAINST THE LOCAL FILE
--------------------------------------------------
The first version of this script took the local files as its source of truth, which was right
while the local files were the uploaded ones and wrong the moment they moved ahead. After the
revision-3 rebuild (the stated counts, `results/ERRATA.md` section 13) the local PDFs no longer
match the records, so a local-truth comparison would have reported "the upload failed" when in
fact the upload was correct and the working tree had simply advanced.

That is this project's own named defect -- a correct value attached to the wrong object -- so the
expectation now comes from a RECORDED MANIFEST per revision, and the local files are reported
separately: the script tells you both what the record holds and which revision your working tree
is on, and fails only when the record disagrees with the revision it is supposed to hold.

  python recon/R19-verify-zenodo-edit.py            # check the deposited revision (default)
  python recon/R19-verify-zenodo-edit.py --rev 3    # check revision 3, i.e. after you upload it
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
UA = {"User-Agent": "llm-jev-laya-bench R19/2 (+https://github.com/PerryLink/llm-jev-laya-bench)"}

# Which file of which record lives at which local path. This mapping is the fact being checked
# (a wrong-language upload is caught here rather than by a reader).
LOCAL = {
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

# (bytes, md5) PER RECORD, PER FILE, PER REVISION -- measured, not remembered: revision 2 was
# read off the live records, revision 3 off the rebuilt files.
REVISIONS: dict[int, dict[str, dict[str, tuple[int, str]]]] = {
    1: {  # original deposit, 97 / 79 pp
        "22901853": {"paper-en.pdf": (3_202_893, "?"), "MANUSCRIPT.md": (272_899, "?")},
        "22902025": {"paper-zh.pdf": (6_924_090, "?"), "MANUSCRIPT.md": (227_497, "?")},
    },
    2: {  # erratum revision, in place, 2026-09-23 (100 / 80 pp); this is what Zenodo holds now
        "22901853": {
            "paper-en.pdf": (3_303_623, "e2df8e260850731b6564cc593f6ed758"),
            "MANUSCRIPT.md": (280_617, "761801c8f4de27d4330b4e151e5311eb"),
        },
        "22902025": {
            "paper-zh.pdf": (7_038_415, "b87f99acaad538449afde2b1b996a091"),
            "MANUSCRIPT.md": (234_119, "c9abe32ac003a128a5fff66d8768b833"),
        },
    },
    3: {  # rebuilt 2026-09-23 (ERRATA 13, the stated counts) and 2026-09-25 (ERRATA 14, the
          # #156 status). NOT uploaded as of this writing.
        "22901853": {
            "paper-en.pdf": (3_316_673, "06e6fab7c40cf149912ad11535b66538"),
            "MANUSCRIPT.md": (281_775, "8ab389a583913f38b76fe6f6e7405115"),
        },
        "22902025": {
            "paper-zh.pdf": (7_048_126, "f1b586bd8574b5c8b879d19020c70da9"),
            "MANUSCRIPT.md": (235_173, "91705a1c1f3132de3e619bc75618e67a"),
        },
    },
}

REV_NOTES = {
    1: "original deposit (97 / 79 pp)",
    2: "erratum revision (100 / 80 pp) -- DEPOSITED",
    3: "stated counts and the #156 status corrected (100 / 81 pp) -- rebuilt, NOT yet uploaded",
}

DEPOSITED = 2


def local(rel: pathlib.Path) -> tuple[int, str]:
    b = rel.read_bytes()
    return len(b), hashlib.md5(b).hexdigest()


def local_revision(size: int, md5: str) -> str:
    """Which revision a local file is, so 'the tree moved on' is stated rather than inferred."""
    for rev, recs in REVISIONS.items():
        for files in recs.values():
            for want in files.values():
                if want == (size, md5):
                    return f"revision {rev}"
    return "no recorded revision (uncommitted change?)"


def main() -> int:
    rev = DEPOSITED
    if "--rev" in sys.argv:
        try:
            rev = int(sys.argv[sys.argv.index("--rev") + 1])
        except (IndexError, ValueError):
            print("usage: R19-verify-zenodo-edit.py [--rev N]")
            return 2
    if rev not in REVISIONS:
        print(f"unknown revision {rev}; known: {sorted(REVISIONS)}")
        return 2

    print(f"Checking that each record holds REVISION {rev} ({REV_NOTES[rev]}).")
    print(f"Recorded manifest for revision {rev} is the expectation; the local files are not.\n")

    fails: list[str] = []
    for rec, spec in LOCAL.items():
        want = REVISIONS[rev][rec]
        try:
            req = urllib.request.Request(f"https://zenodo.org/api/records/{rec}", headers=UA)
            d = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
        except Exception as exc:  # noqa: BLE001
            fails.append(f"{rec}: could not reach Zenodo ({type(exc).__name__}: {exc})")
            print(f"  FAIL {spec['label']}: {type(exc).__name__}: {str(exc)[:80]}")
            continue

        m = d["metadata"]
        print("=" * 76)
        print(f"{spec['label']}   https://zenodo.org/records/{rec}")
        print("=" * 76)

        # --- DOI must be unchanged -------------------------------------------------
        if d.get("doi") == spec["doi"]:
            print(f"  ok   DOI unchanged: {d.get('doi')}")
        else:
            fails.append(f"{rec}: DOI is {d.get('doi')}, expected {spec['doi']}")
            print(f"  FAIL DOI is {d.get('doi')}, expected {spec['doi']}")
        if d.get("conceptdoi") == spec["concept"]:
            print(f"  ok   concept DOI unchanged: {d.get('conceptdoi')}")
        else:
            fails.append(f"{rec}: concept DOI is {d.get('conceptdoi')}")
            print(f"  FAIL concept DOI is {d.get('conceptdoi')}")

        # --- metadata sanity (recorded, not gated) ---------------------------------
        t = m.get("title") or ""
        colon = t[12] if len(t) > 12 else ""
        if rec == "22902025" and colon != "\uff1a":
            print("  note title colon is half-width; author has ruled this out of scope")
        print(f"       title: {(t)[:70]}")
        print(f"       language: {m.get('language')}  license: {(m.get('license') or {}).get('id')}")

        # --- files, against the RECORDED manifest ----------------------------------
        remote = {f["key"]: (f["size"], (f.get("checksum") or "").replace("md5:", ""))
                  for f in (d.get("files") or [])}
        print(f"       files on record: {sorted(remote)}")
        for key, rel in spec["files"].items():
            if key not in remote:
                fails.append(f"{rec}: {key} missing from the record")
                print(f"  FAIL {key} missing")
                continue
            rsize, rmd5 = remote[key]
            wsize, wmd5 = want[key]
            lsize, lmd5 = local(rel)
            mine = local_revision(lsize, lmd5)
            if rsize == wsize and rmd5 == wmd5:
                print(f"  ok   {key:16} {rsize:>9,} bytes  md5 {rmd5[:12]} = revision {rev}")
            else:
                fails.append(f"{rec}: {key} is {rsize} bytes / {rmd5[:12]}, "
                             f"revision {rev} is {wsize} / {wmd5[:12]}")
                print(f"  FAIL {key:16} {rsize:>9,} md5 {rmd5[:12]} != revision {rev} "
                      f"{wsize:>9,} md5 {wmd5[:12]}")
            print(f"       {'':16} local file is {mine} "
                  f"({'matches the record' if mine == f'revision {rev}' else 'differs from the record'})")

        extra = set(remote) - set(spec["files"])
        if extra:
            print(f"  note unexpected extra file(s) on the record: {sorted(extra)}")

        rel_ids = [(r.get("relation"), r.get("identifier"))
                   for r in (m.get("related_identifiers") or [])]
        print(f"       related works: {rel_ids}")
        print()

    print("=" * 76)
    if fails:
        print(f"RESULT: {len(fails)} problem(s)")
        for f in fails:
            print("  - " + f)
        return 1
    print(f"RESULT: both records hold revision {rev}, and both DOIs are unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
