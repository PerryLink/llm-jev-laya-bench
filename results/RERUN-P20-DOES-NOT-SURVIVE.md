P20: the 0.912 figure does not survive re-measurement, and the reason is a fixed rubric

THE CLAIM THE PAPER MAKES

That on non-Latin scripts the judge gives FALSE items a mean P(true) as high as 0.912 -- reading
"not stated" as support, most strongly in the languages it was never trained on. It appears in the
introduction's evidence table, in section 6, in section 7, in both languages and in the built
manuscript. It is one of the paper's sharpest illustrations of the absence-collapse.

WHAT THE RE-RUN SAYS

    non-Latin false-item mean P(true)     0.9121  ->  0.4795
    non-Latin accuracy                    0.500   ->  1.000
    english-native false-item P(true)     0.4068  ->  0.1323

THE HALF-SPLIT THAT SETTLES IT

This is not noise and it is not a flaky battery. The same artifact contains two arms, and they
behave in exactly the way item-construction drift predicts:

    TRUE-item arm    rubric correct in BOTH script versions
                     48 of 48 fields reproduce identically, across all 8 languages
    FALSE-item arm   rubric named the WRONG value in the published version
                     22 fields differ

An arm whose instructions were right reproduces perfectly. An arm whose instructions were wrong
does not. That is a controlled comparison inside one artifact, and it rules out sampling noise,
network jitter, a bad run, and interpreter problems. **The two runs asked the judge different
questions.**

THE MECHANISM, FROM FROZEN EVIDENCE

`src/items/p20_language_misrouting.py:104-115` carries the comment

    AUDIT FIX (finding: mismatched criteria on the false item)

and writes `criteria_used`, which is `null` in the published artifact and populated in the re-run.
So the criteria were corrected AFTER the artifact was produced. The re-run therefore measures the
CORRECTED protocol; the published artifact measures the defective one.

WHAT THIS MEANS, STATED PLAINLY

**The paper prints a number that its own code no longer produces, and the code was changed
because the number was measuring a bug.** The 0.912 is real in the sense that it was measured --
but what it measured is a judge being asked a malformed question, not a judge failing to notice
an absence.

The direction matters and should not be softened: the corrected figure **0.4795** is less
dramatic than 0.912. The paper's sharpest illustration of absence-collapse is weakened by fixing
a defect in the paper's own instrument. That is the honest outcome and it is the same shape as
every other correction this project has made -- they all moved the claims DOWN.

WHAT MUST HAPPEN, AND IT IS NOT A RERUN

The condition has to be assigned, not re-measured again:

  (a) If the paper's claim is about a judge given CORRECT criteria, then 0.912 is withdrawn and
      replaced by 0.4795, and the absence-collapse is illustrated by a smaller number. The
      qualitative finding may still hold -- 0.4795 is still far above a calibrated judge's
      behaviour on items with no support -- but it must be re-stated.
  (b) If the claim is about what happens when the judge is asked a MALFORMED question, then 0.912
      stands, but the paper must say so, because that is a different and weaker claim: it would
      be about protocol sensitivity, not about the judge's own failure mode.

(a) is almost certainly right, since the paper's argument is about the judge, not about the
prompt. But it is the author's call, and it is a substantive change to a headline result, not an
edit.

The same defect class explains P5, where frozen evidence settles it too: `items/evidence-brief-
pilot.json`, written four minutes AFTER the P5 artifact, records `true_pos=4` where the artifact
has 5. Today's generator matches the frozen snapshot, not the artifact -- so P5's re-run measured
a different item set, and its headline numbers move with it (with-carrier accuracy 0.25 -> 0.3125,
without-carrier 0.0 -> 0.25, certified-live 16/16 -> 12/16). Its verdict branch is unchanged.
