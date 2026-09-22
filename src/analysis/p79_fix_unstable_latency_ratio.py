"""The plugin-vs-wall-clock latency ratio: stop printing a point the artifact contradicts.

WHY (this is a defect the re-run created, not one ERRATA 10.3 recorded)
----------------------------------------------------------------------
`results/RERUN-RATIO-INSTABILITY.md` (re-run campaign) reports it and deliberately left the
text alone. The paper prints the ratio as **1.94x** in three Chinese and three English places.
That 1.94 is `1851 / 956.2`, and 956.2 ms is the size-matched rung of the P27c latency ladder.
The ladder was re-measured, that rung is now **1,244.8 ms**, and the live artifact
`results/P27b-plugin-crossval.json` therefore reads **1.49**. So the manuscript prints a number
its own artifact contradicts -- the exact defect class this paper documents, in the paper's own
hand. Leaving it while fixing everyone else's would be indefensible.

WHAT REPLACES IT, AND WHY A RANGE IS THE HONEST FORM
----------------------------------------------------
Not a new point value. The denominator is a LATENCY measurement, and this project has just
measured -- twice, with artifacts -- that Jev's latency does not reproduce while its answers do:

    same script, same state, same n=20:  p50 1,191.8 -> 952.9 ms (-20%)
                                         max 4,018.6 -> 6,360.4 ms (+58%)
    answers, costs, token counts:        identical

So the ratio is 1.94 against the pre-rerun artifact and 1.49 against the live one, and the text
now says so, with both artifacts named. A range with a stated cause reads as a measurement; a
bare range reads as sloppiness.

THE FINDING THAT SURVIVES IS STATED SEPARATELY
----------------------------------------------
The ladder's SHAPE reproduces even though its level moves: p50 is roughly flat across a 127x
state increase in both runs (published +12%, re-run -10%), and the per-rung level moves
+4.0%...+32.6%. That is the difference between "our number was wrong" and "our finding holds and
the absolute level is environment-dependent" -- and the second is what the artifacts show. All
six numbers are computed from the two `P27c` artifacts by this script and asserted, so none of
them is transcribed.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER, ROOT  # noqa: E402

# ------------------------------------------------------------------ arithmetic from artifacts
BASE = ROOT / "rerun" / "baseline"
LIVE = ROOT / "results"


def ladder(path: Path) -> dict[int, float]:
    d = json.loads(path.read_text(encoding="utf-8"))
    return {r["state_chars"]: r["latency_ms_wall"]["p50"] for r in d["by_size"]}


lb, ll = ladder(BASE / "P27c-jev-latency-sweep.json"), ladder(LIVE / "P27c-jev-latency-sweep.json")
sizes = sorted(lb)
shape_pub = (lb[sizes[-1]] / lb[sizes[0]] - 1) * 100
shape_re = (ll[sizes[-1]] / ll[sizes[0]] - 1) * 100
span = sizes[-1] / sizes[0]
level = sorted((ll[s] / lb[s] - 1) * 100 for s in sizes)

p27b_live = json.loads((LIVE / "P27b-plugin-crossval.json").read_text(encoding="utf-8"))
p27b_base = json.loads((BASE / "P27b-plugin-crossval.json").read_text(encoding="utf-8"))
lat_live = p27b_live["latency_self_report_vs_wall_clock"]
lat_base = p27b_base["latency_self_report_vs_wall_clock"]
r_live = lat_live["ratio_of_medians_matched"]
r_base = lat_base["ratio_of_medians_matched"]
d_live = lat_live["matched_direct_wall_ms"]["p50"]
d_base = lat_base["matched_direct_wall_ms"]["p50"]
ru_live = lat_live["ratio_of_medians_unmatched"]
ru_base = lat_base["ratio_of_medians_unmatched"]
du_live = lat_live["unmatched_direct_for_reference"]["p50_ms"]
du_base = lat_base["unmatched_direct_for_reference"]["p50_ms"]

plugin_p50 = lat_live["plugin_latencyMs"]["p50"]
p27_base = json.loads((BASE / "P27-jev-live.json").read_text(encoding="utf-8"))["latency"]
p27_live = json.loads((LIVE / "P27-jev-live.json").read_text(encoding="utf-8"))["latency"]
sm_base = json.loads((BASE / "P27-summary.json").read_text(encoding="utf-8"))["latency_wall_ms_combined"]
sm_live = json.loads((LIVE / "P27-summary.json").read_text(encoding="utf-8"))["latency_wall_ms_combined"]

print(f"  matched ratio: baseline {r_base} (denominator {d_base}) -> live {r_live} "
      f"(denominator {d_live})")
print(f"  unmatched ratio: baseline {ru_base} (denom {du_base}) -> live {ru_live} (denom {du_live})")
print(f"  P27 n=20: p50 {p27_base['p50_ms']} -> {p27_live['p50_ms']}, "
      f"max {p27_base['max_ms']} -> {p27_live['max_ms']}")
print(f"  pooled n=35: p50 {sm_base['p50']} -> {sm_live['p50']}, "
      f"max {sm_base['max']} -> {sm_live['max']}")
print(f"  ladder span {span:.0f}x; shape published {shape_pub:+.1f}% / re-run {shape_re:+.1f}%; "
      f"per-rung level moves {level[0]:+.1f}%..{level[-1]:+.1f}%")

# the numbers the text will print, checked rather than assumed
assert r_base == 1.94 and round(r_live, 2) == 1.49, (r_base, r_live)
assert round(ru_base, 2) == 1.55 and round(ru_live, 2) == 1.94, (ru_base, ru_live)
assert d_base == 956.2 and d_live == 1244.8, (d_base, d_live)
assert round(span) == 127
assert abs(shape_pub - 12.3) < 0.2 and abs(shape_re + 10.3) < 0.2, (shape_pub, shape_re)
assert 3.9 < level[0] < 4.2 and 32.4 < level[-1] < 32.9, level

ZH = {
    "04-method-draft.md": [(
        # A CONCURRENT EDITOR'S GLOBAL REPLACE HIT A PER-ARTIFACT VALUE HERE: this sentence
        # reports what the ratio READS AGAINST EACH ARTIFACT (1.94 against the baseline, 1.49
        # against the live one). Replacing the first with the range makes it say the ratio
        # reads "1.5-1.9 ... and 1.49", which is not a sentence. Restored to the value the
        # baseline artifact actually records.
        "分别读作 **1.5–1.9**（`rerun\\baseline\\P27b-plugin-crossval.json`",
        "分别读作 **1.94**（`rerun\\baseline\\P27b-plugin-crossval.json`",
        "§4: restore the per-artifact value the range replaced"),
    ],
    "05-results-A-draft.md": [(
        "对修复前产物为 **1.94**，对当前产物为 **1.49**。",
        "对 `rerun\\baseline\\P27b-plugin-crossval.json` 为 **1.94**（分母 p50 **956.2 ms**），"
        "对 `results\\P27b-plugin-crossval.json` 为 **1.49**（分母 p50 **1,244.8 ms**）。",
        "§5: name the two artifacts behind the range"),
    ],
    "06-results-B-draft.md": [(
        "⇒ **附带一项待验证旗标**：插件的 `latencyMs`（n=7，p50 **1,851 ms**）约为独立墙钟的 **1.5–1.9 倍**（**尺寸匹配**的 126 字符 / 347 token 类，n=5，p50 956 ms；"
        "若改用不匹配的当前 n=20 运行则读作 **1.55 倍**——比值本身取决于是否匹配状态，故两个数都必须给出）；两组非同批采集，故记为旗标而非结论（§5.2）。",
        "⇒ **附带一项待验证旗标**：插件的 `latencyMs`（n=7，p50 **1,851 ms**）**高于**独立墙钟，但**比值不稳定，故报约 1.5–1.9 倍并列出两次产物**——"
        "**尺寸匹配**（126 字符 / 347 token 类，n=5）分母 p50 **956.2 → 1,244.8 ms**（`rerun\\baseline\\P27b-plugin-crossval.json` → **1.94**；`results\\P27b-plugin-crossval.json` → **1.49**）；"
        "不匹配的当前 n=20 运行分母 p50 **1,191.8 → 952.9 ms**（→ **1.55 / 1.94**）。"
        "**⚠️ 第九轮更正**：此处原印单值 1.94 倍；**原因写在同一句里**——该比值的分母是一次**延迟测量**，而 Jev 的延迟**不复现**（同一脚本、同一状态、同一 n：p50 −20%、max +58%），**只有答案逐位相同**。"
        "**⚠️ 但形状可复现、移动的只是绝对水平**：p50 在 **127×** 的 state 跨度（126 → 15,999 字符）上基本持平——published **+12%**、re-run **−10%**（`rerun\\baseline\\P27c-jev-latency-sweep.json` / `results\\P27c-jev-latency-sweep.json`），"
        "逐档水平移动 **+4.0% … +32.6%**；故「延迟不由状态大小主导」这一读法在两次产物中都成立。两组非同批采集，故记为旗标而非结论（§5.2）。",
        "§6: the latency flag"),
    ],
}

EN = {
    "03-04-systems-method.md": [(
        "- **Latency must be reported with its heavy tail, and with its measurement point**: in Jev's independent\n"
        "  wall-clock measurements (pooled n=35) the median is **1,073.4 ms** while the **maximum is 4,018.6 ms**\n"
        "  (about 3.7× the median); the ratio of its **self-reported** `latencyMs` to wall clock depends on whether\n"
        "  the state is size-matched — **1.5-1.9× when size-matched** (the 126-character / 347-token class), **1.55×\n"
        "  when not matched** (for the current n=20 run) — using the self-reported value for capacity planning\n"
        "  overestimates, while using the median underestimates the tail. **And that column is itself a single\n"
        "  sampling**: two runs of the same script differ by 30% in p50 and by 123% in max, so the paper reports an\n"
        "  interval rather than a single value.",
        "- **Latency must be reported with its heavy tail, and with its measurement point**: in Jev's independent\n"
        "  wall-clock measurements (pooled n=35) the median is **1,073.4 / 1,116.1 ms** and the **maximum is\n"
        "  4,018.6 / 6,360.4 ms** (two runs, see below); the ratio of its **self-reported** `latencyMs` to wall\n"
        "  clock depends on whether the state is size-matched — **about 1.5-1.9× when size-matched** (the\n"
        "  126-character / 347-token class), **about 1.6-1.9× when not matched** (for the current n=20 run) — using\n"
        "  the self-reported value for capacity planning overestimates, while using the median underestimates the\n"
        "  tail. **⚠️ And that ratio is itself unstable (ninth-round correction)**: its **denominator is a latency\n"
        "  measurement**, and latency is precisely the quantity this project measures as **not reproducing** —\n"
        "  same script, same state, same n=20: **p50 1,191.8 -> 952.9 ms (-20%)**, **max 4,018.6 -> 6,360.4 ms\n"
        "  (+58%)**, while the **answers are bit-identical** (truth battery 8/8, same `noul`, same cost, same\n"
        "  token counts). So the same \"size-matched\" ratio reads **1.94** against\n"
        "  `rerun\\baseline\\P27b-plugin-crossval.json` (denominator p50 **956.2 ms**) and **1.49** against\n"
        "  `results\\P27b-plugin-crossval.json` (denominator p50 **1,244.8 ms**). **The paper therefore reports an\n"
        "  interval and names both artifacts, not a three-significant-figure point value.**",
        "en §3-4: the latency row (ratio + pooled level)"),
    ],
    "05-results-A.md": [(
        "**1.94** against the pre-repair artifact and **1.49** against the current one.",
        "**1.94** against `rerun\\baseline\\P27b-plugin-crossval.json` (denominator p50 **956.2 ms**) and **1.49**\n"
        "against `results\\P27b-plugin-crossval.json` (denominator p50 **1,244.8 ms**).",
        "en §5: name the two artifacts behind the range"),
    ],
    "06-07-results-BC.md": [(
        "⇒ **One flag awaiting verification attached**: the plugin's `latencyMs` (n=7, p50 **1,851 ms**) is about **1.5-1.9×** the independent wall clock "
        "(the **size-matched** 126-character / 347-token class, n=5, p50 956 ms; switching to the unmatched current n=20 run reads it as **1.55×** — "
        "the ratio itself depends on whether the state is matched, so both numbers must be given); the two groups were not collected in the same batch, "
        "so this is recorded as a flag rather than a conclusion (§5.2).",
        "⇒ **One flag awaiting verification attached**: the plugin's `latencyMs` (n=7, p50 **1,851 ms**) is **above** the independent wall clock, but the "
        "**ratio is unstable, so we report about 1.5-1.9× and name both artifacts** — for a **size-matched** state (the 126-character / 347-token class, "
        "n=5) the denominator's p50 goes **956.2 -> 1,244.8 ms** (`rerun\\baseline\\P27b-plugin-crossval.json` -> **1.94**; `results\\P27b-plugin-crossval.json` "
        "-> **1.49**); for the unmatched current n=20 run the denominator's p50 goes **1,191.8 -> 952.9 ms** (-> **1.55 / 1.94**). "
        "**⚠️ Ninth-round correction**: this sentence printed the single value 1.94×; **the reason is stated in the same sentence** — the ratio's "
        "denominator is a **latency measurement**, and Jev's latency **does not reproduce** (same script, same state, same n: p50 -20%, max +58%), while "
        "**only the answers are bit-identical**. **⚠️ But the shape does reproduce and only the level moves**: p50 is roughly flat across a **127×** state "
        "span (126 -> 15,999 characters) — published **+12%**, re-run **-10%** (`rerun\\baseline\\P27c-jev-latency-sweep.json` / "
        "`results\\P27c-jev-latency-sweep.json`) — with the per-rung level moving **+4.0% … +32.6%**; so \"latency is not dominated by state size\" holds "
        "in both runs. The two groups were not collected in the same batch, so this is recorded as a flag rather than a conclusion (§5.2).",
        "en §6: the latency flag"),
    ],
}


def apply(edits: dict, root: Path) -> int:
    miss = 0
    for fname, pairs in edits.items():
        p = root / fname
        t = p.read_text(encoding="utf-8")
        for old, new, label in pairs:
            if old in t:
                t = t.replace(old, new, 1)
                print(f"  ok    {label}")
            elif new in t:
                print(f"  ok    {label} (already applied)")
            else:
                print(f"  MISS  {label}")
                miss += 1
        p.write_text(t, encoding="utf-8")
    return miss


def main() -> int:
    # Printing a child process's output on this host can raise UnicodeEncodeError: the console
    # is GBK and a lenient decode leaves U+FFFD. Reconfigure before anything prints.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                            # noqa: BLE001
        pass

    miss = apply(ZH, PAPER)
    miss += apply(EN, PAPER / "en")

    for cmd in ([sys.executable, str(PAPER / "_assemble.py")],
                [sys.executable, str(PAPER / "en" / "_assemble.py")]):
        # the Chinese assembler prints Chinese; on this host the child's stdout is GBK, so a
        # strict utf-8 decode raises INSIDE subprocess and kills the check before it can read
        # the return code. Decode leniently and judge on the return code.
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", cwd=str(PAPER.parent))
        if r.returncode != 0:
            print(r.stdout, r.stderr)
            miss += 1

    # no unqualified single value may survive in either language
    import re
    for lang, root in (("zh", PAPER), ("en", PAPER / "en")):
        bad = []
        for f in sorted(root.glob("*.md")):
            if f.name.startswith(("MANUSCRIPT", "12-", "13-")):
                continue
            for i, line in enumerate(f.read_text(encoding="utf-8").split("\n"), 1):
                if re.search(r"1\.94\s*(倍|×|x)", line) and "更正" not in line and "correction" not in line:
                    bad.append(f"{f.name}:{i}")
        if bad:
            print(f"  MISS  {lang}: an unqualified 1.94 ratio survives at {bad}")
            miss += 1
        else:
            print(f"  ok    {lang}: no unqualified 1.94 ratio in any draft")

    print(f"\n{miss} problems")
    return 1 if miss else 0


if __name__ == "__main__":
    sys.exit(main())
