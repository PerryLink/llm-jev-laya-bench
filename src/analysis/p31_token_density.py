"""P31: measure the real characters-per-token density of the Laya encoders.

WHY THIS EXISTS. The paper states, in its access-layer defect list:

    planning.py estimates tokens with chars / 4.0 x 1.15, i.e. an implied 3.478
    chars/token; whereas that encoder measures ~6.33 chars/token on English prose
    -> the planner overestimates the token count by about 1.8x

The 6.33 was taken from recon/R13-laya-probe.md, which measured it on the state
the clamp sweep builds: `DECOY + FILLER * reps + CORRECTION`, i.e. one filler
sentence repeated dozens of times. This script asks what the encoder actually
delivers on text types that are not a repeated sentence, because if the ratio
depends on the text type then "on English prose" names the wrong object, and if
the ratio is BELOW 3.478 for some real input type then the planner errs in the
dangerous direction rather than the safe one.

Both directions matter and they are not symmetric: an over-estimate makes the
preflight refuse work that would have fitted (annoying), an under-estimate makes
it report `fits` for a state the model will silently truncate (the exact failure
the preflight exists to prevent).

Runs on a bare Python 3.12 + `tokenizers`, loaded from the Hugging Face cache,
so it needs no GPU and no model weights:

    uv run --quiet --no-project --with tokenizers python src/analysis/p31_token_density.py

Writes results/P31-token-density.json and exits non-zero if the tokenizers
cannot be loaded, so a silent zero-row result cannot be mistaken for a finding.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
from typing import Any

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "P31-token-density.json"

#: The three checkpoints the instrument snapshot loads. Vocab sizes differ, and
#: a ratio is a property of a tokenizer, so each has to be measured separately.
TOKENIZERS = {
    "english": "tokenizer/tokenizer.json",
    "multilingual": "multilingual/tokenizer/tokenizer.json",
    "typed-decisions": "typed-decisions/tokenizer/tokenizer.json",
}

#: The planner's assumption, from planning.py: _CHARS_PER_TOKEN / _SAFETY.
PLANNER_ASSUMED = 4.0 / 1.15      # 3.478 effective chars/token


def find_encoder_dir() -> pathlib.Path:
    """Locate the cached Laya checkpoint without needing the model weights."""
    cache = pathlib.Path.home() / ".cache" / "huggingface" / "hub"
    root = cache / "models--convaiinnovations--laya" / "snapshots"
    if not root.is_dir():
        raise SystemExit(f"no cached Laya snapshot under {root}")
    snaps = sorted(p for p in root.iterdir() if p.is_dir())
    if not snaps:
        raise SystemExit(f"snapshot directory is empty: {root}")
    return snaps[-1]


def strip_markdown(text: str) -> str:
    """Crude, and deliberately so: the point is prose, not a renderer."""
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"[*#`_>\[\]()|-]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def build_samples(enc: pathlib.Path) -> dict[str, str]:
    """The text types a state can plausibly be, plus the paper's own test state."""
    samples: dict[str, str] = {}

    prose = ROOT / "paper" / "en" / "MANUSCRIPT.md"
    if prose.exists():
        samples["english_prose"] = strip_markdown(
            prose.read_text(encoding="utf-8")
        )[:40000]

    md = ROOT / "paper" / "en" / "MANUSCRIPT.md"
    if md.exists():
        samples["english_markdown"] = md.read_text(encoding="utf-8")[:40000]

    jsons = sorted((ROOT / "results").glob("*.json"))
    if jsons:
        biggest = max(jsons, key=lambda p: p.stat().st_size)
        samples["json_artifact"] = biggest.read_text(encoding="utf-8")[:40000]
        samples["json_artifact_name"] = ""      # placeholder, filled below

    py = ROOT / "paper" / "verify_all.py"
    if py.exists():
        samples["python_source"] = py.read_text(encoding="utf-8")[:40000]

    zh = ROOT / "paper" / "MANUSCRIPT.md"
    if zh.exists():
        samples["chinese_manuscript"] = zh.read_text(encoding="utf-8")[:20000]

    # The state the paper's own defect claim was measured on.
    #
    # The three strings must be VERBATIM from src/instrument/p3_clamp_calibration.py
    # lines 57-60. An earlier version of this file paraphrased them ("...and
    # nothing was flagged." for FILLER, a different CORRECTION), which changed the
    # measured density from 6.78 to 5.85 and would have put a figure in the paper
    # that its own artifact did not support. Same state or no comparison.
    #
    # TWO sizes because density is not constant in length and the paper quotes a
    # specific row: the R13 table's largest row targeted 5086 chars.
    decoy = "The vault access code is AAA-1111."
    filler = (
        "Quarterly logistics review. The warehouse processed routine shipments "
        "and filed standard compliance paperwork. "
    )
    correction = " Correction: the vault access code is now ZQX-4471."

    def paper_state(target: int) -> str:
        b = max(0, target - len(decoy) - len(correction))
        return decoy + filler * (b // len(filler)) + correction

    samples["paper_test_state_5086"] = paper_state(5086)
    samples["paper_test_state_5000"] = paper_state(5000)

    # The compressibility ladder, because the paper's correction cites it: the
    # same sentence repeated 1 / 100 / 1000 times, to show that the test state's
    # high density comes from REPETITION and not from the text being English.
    for n in (1, 100, 1000):
        samples[f"filler_repeated_x{n}"] = filler * n

    # TWO CONSTRUCTED samples, deliberately, and labelled as such wherever their
    # numbers are quoted. They exist because the two densest realistic input types
    # -- a numeric CSV table and a server log with a traceback -- have no verbatim
    # file in the tree to measure, and leaving them out was how the first version
    # of this script under-reported the planner's dangerous direction. Their shape
    # is taken from the independent audit in D:\Projects\planner-token-audit
    # (final.py: csvrows / log lines), so the two measurements agree by
    # construction rather than by coincidence.
    csv_rows = ["arm,n,correct,accuracy,mean_latency_ms,p95_latency_ms,clamp_tokens"] + [
        f"FULL-{i:03d},10,{i % 11},{(i % 11) / 10:.3f},"
        f"{412.5 + i * 3.7:.1f},{901.2 + i * 5.1:.1f},512"
        for i in range(60)
    ]
    samples["csv_metrics_table_CONSTRUCTED"] = "\n".join(csv_rows)

    log_lines = [
        "2026-09-23 04:12:37 INFO  laya_mcp.server starting sidecar on 127.0.0.1:8791",
        "2026-09-23 04:12:37 INFO  laya_mcp.worker loading checkpoint english",
        "2026-09-23 04:12:41 INFO  laya_mcp.worker checkpoint english ready device=cuda",
        "2026-09-23 04:12:44 WARN  laya_mcp.worker max_len override requested=512 actual=512",
        "2026-09-23 04:13:02 ERROR laya_mcp.server unhandled failure in ask",
        "Traceback (most recent call last):",
        '  File "src/laya_mcp/server.py", line 157, in do_POST',
        "    response = self.worker.ask(request)",
        '  File "src/laya_mcp/worker.py", line 499, in ask',
        "    return self._run(request, checkpoint, capability, plan)",
        '  File "src/laya_mcp/worker.py", line 612, in _run',
        "    result = agent.system_one(state, questions)",
        '  File "laya/agent.py", line 388, in system_one',
        "    raise RuntimeError(marker count mismatch)",
        "RuntimeError: marker count mismatch: 2 markers for 3 rendered options",
    ]
    samples["server_log_traceback_CONSTRUCTED"] = "\n".join(log_lines * 8)
    samples.pop("json_artifact_name", None)
    return samples


def main() -> int:
    try:
        from tokenizers import Tokenizer
    except ImportError:
        print("tokenizers is not installed; run under "
              "`uv run --with tokenizers`", file=sys.stderr)
        return 2

    enc = find_encoder_dir()
    print(f"encoder dir : {enc}")
    samples = build_samples(enc)
    print(f"samples     : {len(samples)}")
    print(f"planner assumes {PLANNER_ASSUMED:.3f} chars/token "
          f"(4.0 / 1.15), i.e. estimate = int(chars / 4.0 * 1.15)")
    print()

    records: list[dict[str, Any]] = []
    tokenizer_hashes: dict[str, Any] = {}
    header = (f"{'tokenizer':17} {'sample':34} {'chars':>7} {'tokens':>7} "
              f"{'chars/tok':>9} {'planner est':>11} {'real/est':>8}  direction")
    print(header)
    print("-" * len(header))

    for name, rel in TOKENIZERS.items():
        path = enc / rel
        if not path.exists():
            print(f"{name:17} MISSING {rel}")
            continue
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        tokenizer_hashes[f"tokenizer.{name}.tokenizer.json"] = digest
        tok = Tokenizer.from_file(str(path))
        for sname, text in samples.items():
            if not text:
                continue
            n_tok = len(tok.encode(text).ids)
            if n_tok == 0:
                continue
            chars = len(text)
            ratio = chars / n_tok
            est = int(chars / 4.0 * 1.15)
            rel_err = n_tok / est if est else float("nan")
            # Under-estimate is the dangerous direction: the preflight says a
            # state fits when the model will in fact drop part of it.
            if est < n_tok:
                direction = "UNDER (dangerous)"
            else:
                direction = "over (safe)"
            print(f"{name:17} {sname:34} {chars:>7,} {n_tok:>7,} {ratio:>9.2f} "
                  f"{est:>11,} {rel_err:>8.3f}  {direction}")
            records.append({
                "tokenizer": name,
                "vocab": tok.get_vocab_size(),
                "sample": sname,
                "chars": chars,
                "real_tokens": n_tok,
                "chars_per_token": round(ratio, 4),
                "planner_estimate": est,
                "real_over_estimate": round(rel_err, 4),
                "direction": direction,
            })
        print()

    if not records:
        print("no measurements produced -- refusing to write an empty result")
        return 1

    # The payoff: where does the preflight start lying in the dangerous
    # direction? Solve int(chars/4.0*1.15) <= 512 < real_tokens per sample.
    boundary: dict[str, int | None] = {}
    for r in records:
        if r["direction"].startswith("UNDER"):
            # chars at which the planner still says fits
            boundary[r["sample"]] = int(512 / 1.15 * 4.0)
    payload = {
        "_note": (
            "Real characters-per-token for the three Laya encoders, measured "
            "from the cached tokenizer.json files (no GPU, no weights). "
            "Establishes whether planning.py's 3.478 chars/token assumption errs "
            "in the safe direction (over-estimate -> refuses work that fits) or "
            "the dangerous one (under-estimate -> reports fits for a state the "
            "model silently truncates)."
        ),
        "_generated_by": "src/analysis/p31_token_density.py",
        # The provenance record for this file is unusual and worth stating plainly:
        # its instrument is NOT the laya-mcp server. No model was loaded, no HTTP
        # entry point was used and no question was asked. The measurement is a
        # pure function of (tokenizer file x text), so the instrument to attribute
        # it to is the three tokenizer files themselves, by content hash.
        "instrument_hashes": tokenizer_hashes,
        "pinned_revision": "protocol/instrument-snapshot",
        "encoder_snapshot": str(enc),
        "measured_how": (
            "tokenizers.Tokenizer.from_file(...).encode(text).ids, no "
            "add_special_tokens, offline from the Hugging Face cache"
        ),
        "planner_assumed_chars_per_token": round(PLANNER_ASSUMED, 4),
        "measurements": records,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print()
    print("=== summary ===")
    under = [r for r in records if r["direction"].startswith("UNDER")]
    over = [r for r in records if not r["direction"].startswith("UNDER")]
    print(f"  under-estimates (dangerous): {len(under)}")
    for r in under:
        print(f"    {r['tokenizer']:16} {r['sample']:34} "
              f"real {r['real_tokens']:,} vs est {r['planner_estimate']:,}")
    print(f"  over-estimates (safe):      {len(over)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
