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
| `categories.json` | 2039 | `AA9816A222577ECE5399307478787A732BFCBEF5411A1079836C093559EC254A` |
| `train.csv` | 839076 | `430F67959418D85742B7B8D18D3D10A3DC507A922F7D150E37BB6FB5CB52D20A` |
| `test.csv` | 239964 | `06DF876211F53776F7B9DD743F914E91900682A9D99E1B7C2BA24685FCF72D4D` |

## Note

`categories.json` carries a **UTF-8 BOM**. Read it with `encoding="utf-8-sig"` or `json.loads` raises on the first character.

## Contamination

Banking77 is in the judge's prior training set, and the paper records that the *generator's* exposure is stronger still -- so contamination runs **with** the negative result rather than against it. No accuracy claim in this repository should be read without that caveat.
