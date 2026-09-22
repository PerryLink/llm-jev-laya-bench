import json

for n in ["P19-calibration", "P15b-rep-r1", "P15-complementarity-strong-regime",
          "P23-llm-logprobs", "P25-truncation-harm", "P20-language-misrouting",
          "P2-mock-pipeline-rehearsal", "P10-plausibility-pruning-paired",
          "P1-rank-vs-choice", "P5-certificate-verification",
          "P26-truncation-harm-valid", "P22-chain-audit"]:
    d = json.load(open("results/" + n + ".json", encoding="utf-8"))
    print("=" * 70)
    print(n, "->", list(d.keys())[:14])
    r = d.get("rows") or []
    if r:
        print("   n_rows", len(r), "row0 keys:", list(r[0].keys())[:22])
    for k in ("summary", "cost", "_spend_usd", "_provenance"):
        if k in d:
            v = d[k]
            print("  ", k, "=", json.dumps(v, ensure_ascii=False)[:400])
