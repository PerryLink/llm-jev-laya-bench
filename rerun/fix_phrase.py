from pathlib import Path
p = Path("results/RERUN-REPORT.md")
t = p.read_text(encoding="utf-8")
old = "the P20 `0.912` claim (18 places, two\n  languages)"
new = ("the P20 `0.912` claim (the introduction, §6, §7 and\n"
       "  both generated manuscripts, in both languages)")
if old in t:
    p.write_text(t.replace(old, new, 1), encoding="utf-8")
    print("fixed")
else:
    print("anchor not present; checking variants")
    i = t.find("18 places")
    print(repr(t[i-120:i+80]) if i >= 0 else "no '18 places' anywhere")
