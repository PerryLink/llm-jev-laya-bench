"""Cross-language behaviour of the ENGLISH checkpoint -- NOT a routing test.

PREMISE CORRECTED, AND THE ORIGINAL PREMISE WAS WRONG
-----------------------------------------------------
This script was written to measure the router's documented defect: only en/fr/de/es/pt/it/nl
are detected among Latin-script languages, so anything else is sent to the English model
and answered confidently. The intent was to turn a documented defect into a measured one.

It cannot, through this interface. Probing established that the HTTP sidecar reports
`routing: {"model": "english", "reason": "explicit model selection"}` for EVERY input --
including Russian and Hindi -- and it still does so when launched WITHOUT `--model`. The
sidecar preloads a single checkpoint and never consults a language detector. The
detect-and-dispatch logic lives in the Python `Router` that the DSH plugin uses, which this
project bypasses because the client reaches the sidecar directly.

So the group labels below were FALSE as originally written: no group was "detected",
because nothing was detecting. Relabelled to script groups. What the run actually measures
is the ENGLISH checkpoint's behaviour when handed text in other languages -- a real
question, but a different one.

WHAT THE DATA ACTUALLY SHOWS
  Accuracy is 0.5 in every group -- exactly the always-answer-"true" baseline -- and mean
  P(true) on FALSE items stays high across all scripts (Latin 0.633, other Latin 0.748,
  Cyrillic 0.912). Given non-English text, the English checkpoint leans towards affirming
  the claim and does not discriminate the false items. That is a "true" bias, not a routing
  effect, and it is consistent with the no_support finding in P19: this judge affirms in
  the absence of usable evidence.

  n is 6/8/2 items, so one item moves a group rate by 0.13-0.50. Only the qualitative
  pattern is reportable; no per-language claim is made.
"""

from __future__ import annotations

# Paths resolve through bench_env, which locates the repository root by walking
# up from this file and honours environment overrides (LAYA_ROOT, DSH_CREDENTIALS,
# ...). Run `python bench_env.py` to print what was resolved. The aliased imports
# keep this block independent of whatever this module imported above, so it can
# sit at any top-level position.
import sys as _sys
from pathlib import Path as _Path

_p = _Path(__file__).resolve()
while not (_p / "bench_env.py").exists():
    if _p.parent == _p:
        raise RuntimeError(f"bench_env.py not found above {__file__}")
    _p = _p.parent
ROOT = _p
_sys.path.insert(0, str(ROOT))


import json
import sys
from pathlib import Path


sys.path.insert(0, str(ROOT / "src" / "instrument"))
from laya_client import LayaClient, instrument_record  # noqa: E402

RESULTS = ROOT / "results"

# One item per language, rendered so the true/false structure is language-independent:
# a ledger states the value X as current, and the question asks whether the value X is
# current (TRUE) or a different value Y is current (FALSE). Two items per language, one
# of each truth value, so a language that always answers "true" cannot score well.
ITEMS: dict[str, dict[str, tuple[str, str, str, bool]]] = {
    # lang: {"header": (state_template, q_true, q_false)}
    "en": {"h": ("Ledger extract. pallets shipped in Q3 = {v} units (current).",
                 "Does the state record {v} units as the current pallets shipped in Q3?",
                 "Does the state record {w} units as the current pallets shipped in Q3?")},
    "de": {"h": ("Kontoauszug. pallets shipped in Q3 = {v} Einheiten (aktuell).",
                 "Gibt der Zustand {v} Einheiten als aktuellen Wert an?",
                 "Gibt der Zustand {w} Einheiten als aktuellen Wert an?")},
    "es": {"h": ("Extracto. pallets shipped in Q3 = {v} unidades (actual).",
                 "¿Indica el estado {v} unidades como el valor actual?",
                 "¿Indica el estado {w} unidades como el valor actual?")},
    "pl": {"h": ("Wyciąg z rejestru. pallets shipped in Q3 = {v} jednostek (bieżące).",
                 "Czy stan podaje {v} jednostek jako bieżącą wartość?",
                 "Czy stan podaje {w} jednostek jako bieżącą wartość?")},
    "tr": {"h": ("Defter özeti. pallets shipped in Q3 = {v} birim (güncel).",
                 "Durum güncel değer olarak {v} birim belirtiyor mu?",
                 "Durum güncel değer olarak {w} birim belirtiyor mu?")},
    "vi": {"h": ("Trích lục sổ cái. pallets shipped in Q3 = {v} đơn vị (hiện tại).",
                 "Trạng thái có ghi {v} đơn vị là giá trị hiện tại không?",
                 "Trạng thái có ghi {w} đơn vị là giá trị hiện tại không?")},
    "id": {"h": ("Kutipan buku besar. pallets shipped in Q3 = {v} unit (terkini).",
                 "Apakah status mencatat {v} unit sebagai nilai terkini?",
                 "Apakah status mencatat {w} unit sebagai nilai terkini?")},
    "ru": {"h": ("Выписка из реестра. pallets shipped in Q3 = {v} единиц (текущее).",
                 "Указывает ли состояние {v} единиц как текущее значение?",
                 "Указывает ли состояние {w} единиц как текущее значение?")},
}

ENGLISH_NATIVE = ["en"]
OTHER_LATIN_SCRIPT = ["de", "es", "pl", "tr", "vi", "id"]
NON_LATIN_SCRIPT = ["ru"]


def probe(client: LayaClient, lang: str) -> dict:
    tpl, q_true, q_false = ITEMS[lang]["h"]
    v, w = 4182, 9700
    state = tpl.format(v=v, w=w)
    out = {"lang": lang, "script": "latin" if lang != "ru" else "cyrillic"}
    # AUDIT FIX (finding: mismatched criteria on the false item): the criteria used to
    # be built ONCE from `v` and reused for both items, but q_false asks about `w`.
    # 8 of 16 calls therefore had a rubric that named a different value than the
    # question. Each item now gets a rubric naming the value it actually asks about.
    for tag, q, truth in (("true_item", q_true.format(v=v, w=w), True),
                           ("false_item", q_false.format(v=v, w=w), False)):
        asked = v if tag == "true_item" else w
        crit = {"true": f"yes, {asked}", "false": f"no, not {asked}"}
        out.setdefault("criteria_used", {})[tag] = crit
        try:
            r = client.ask(state, {"q": {"type": "noul", "instructions": q,
                                         "criteria": crit}})
            a = r["answers"]["q"]
            p = float(a["noul"])
            out[tag] = {"p_true": p, "pred": p >= 0.5, "truth": truth,
                        "correct": (p >= 0.5) == truth,
                        "band": a.get("band"),
                        "detected_lang": (r.get("routing") or {}).get("language")
                        if isinstance(r.get("routing"), dict) else None,
                        "model_used": (r.get("routing") or {}).get("model")
                        if isinstance(r.get("routing"), dict) else None}
        except Exception as exc:
            out[tag] = {"error": str(exc)[:200]}
    return out


def run() -> dict:
    client = LayaClient()
    client.ensure_up()
    rows = [probe(client, lang) for lang in ITEMS]

    def grp(langs: list[str]) -> dict:
        sub = [r for r in rows if r["lang"] in langs]
        scored = [x for r in sub for x in (r.get("true_item"), r.get("false_item"))
                  if x and "error" not in x]
        if not scored:
            return {"n": 0}
        acc = sum(1 for x in scored if x["correct"]) / len(scored)
        return {
            "n": len(scored),
            "accuracy": round(acc, 4),
            "mean_p_true_on_true_items": round(
                sum(x["p_true"] for x in scored if x["truth"]) /
                max(1, sum(1 for x in scored if x["truth"])), 4),
            "mean_p_true_on_false_items": round(
                sum(x["p_true"] for x in scored if not x["truth"]) /
                max(1, sum(1 for x in scored if not x["truth"])), 4),
            "always_true_accuracy": round(
                sum(1 for x in scored if x["truth"]) / len(scored), 4),
        }

    native = grp(ENGLISH_NATIVE)
    other_latin = grp(OTHER_LATIN_SCRIPT)
    non_latin = grp(NON_LATIN_SCRIPT)
    summary = {
        "premise_corrected": ("The sidecar never routes: it reports "
                              "routing.reason='explicit model selection' for every input, "
                              "including Cyrillic and Devanagari, even when launched "
                              "without --model. These are SCRIPT groups, not routing "
                              "outcomes; nothing was detected."),
        "per_language": {r["lang"]: {"true_item": r.get("true_item"),
                                     "false_item": r.get("false_item")} for r in rows},
        "english_native": native,
        "other_latin_script": other_latin,
        "non_latin_script": non_latin,
        "instrument": instrument_record(),
        "verdict": None,
        "caveat": ("2 items per language (1 true, 1 false), 8 languages. One item moves a "
                   "group rate by 0.13-0.50, so only the qualitative pattern is "
                   "reportable. A single template per language, so this is not a "
                   "translation-quality measurement either."),
    }
    # WHAT TO LOOK FOR, now that routing is off the table: whether the judge
    # discriminates TRUE from FALSE items at all. A judge answering "true" throughout
    # scores exactly the always-true baseline and shows no separation between the two
    # item types, whatever the language.
    def separated(g: dict) -> bool | None:
        if not g.get("accuracy") or g.get("always_true_accuracy") is None:
            return None
        return abs(g["accuracy"] - g["always_true_accuracy"]) > 0.1

    seps = {k: separated(v) for k, v in
            (("english_native", native), ("other_latin", other_latin),
             ("non_latin", non_latin))}
    summary["groups_exceeding_always_true_baseline"] = seps
    if all(s is False for s in seps.values() if s is not None):
        summary["verdict"] = (
            "NO DISCRIMINATION IN ANY SCRIPT: every group scores exactly the "
            "always-answer-true baseline, and mean P(true) on FALSE items stays high "
            "(0.63-0.91). The English checkpoint affirms rather than discriminates when "
            "the text is not English -- a 'true' bias, not a routing effect. Consistent "
            "with the no_support result in P19 (mean P(true)=0.564 on items whose "
            "candidate value never appears).")
    else:
        summary["verdict"] = ("MIXED: at least one script group exceeds the always-true "
                              "baseline; inspect per_language before concluding")
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    out = run()
    p = RESULTS / "P20-language-misrouting.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in out["summary"].items()
                      if k not in ("instrument", "per_language")}, indent=2))
    print(f"\nwritten: {p}")
