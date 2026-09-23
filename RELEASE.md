# Release instructions

**Everything is prepared and verified. The commands below are the ones only you can run**,
because they need your GitHub, Zenodo and arXiv credentials — which I do not have and should
not have.

Final state at the release commit:

```
python paper/verify_all.py   ->   62 passed, 0 warnings, 0 failures  (62 checks)
git status                   ->   clean
credentials in the tree      ->   0
```

---

## Step 0 — rotate the keys first

`protocol/INCIDENT-credential-echo.md` records that `DEEPSEEK_API_KEY` once reached a session
log. Rotate both before publishing anything:

- `DEEPSEEK_API_KEY`
- `OPENROUTER_API_KEY`

The artifact tree contains no credential value (verified), but a key that has been in a log is
a key that should be replaced, and the cost of doing it before publication is zero.

---

## Step 1 — create the GitHub repository and push

There is **no remote configured** in this checkout. Create the repository first, then:

```bash
cd D:\Projects\llm-jev-laya-bench
git remote add origin https://github.com/PerryLink/llm-jev-laya-bench.git
git push -u origin master
```

`CITATION.cff` already points at `https://github.com/PerryLink/llm-jev-laya-bench`, so the
repository name must match that or the citation will be wrong.

---

## Step 2 — tag the release

The tag is what Zenodo archives, and what the DOI will point at.

```bash
git tag -a v1.0.0 -m "First release: measurements, artifacts and audit trail"
git push origin v1.0.0
```

**Do this only after the tree is final.** A tag is immutable in practice; if the paper changes
afterwards the DOI will point at a version that no longer matches the text.

---

## Step 3 — connect Zenodo and get the DOI

1. Sign in to <https://zenodo.org> with GitHub.
2. Go to **Settings → GitHub** and flip the switch for `llm-jev-laya-bench` to **ON**.
3. Zenodo archives each release automatically. The `v1.0.0` release created in step 2 may need
   a nudge — if the repository was only just enabled, edit and re-save the release on GitHub.
4. Copy the **DOI** Zenodo assigns (it looks like `10.5281/zenodo.XXXXXXX`).

---

## Step 4 — write the DOI back into the paper, then rebuild

The DOI is a sentence in the paper, so the paper has to be rebuilt after it exists. **This
order is not cosmetic**: a paper that claims a citable DOI before the DOI exists is making a
claim it cannot support, in a paper about claims that cannot be supported.

Two places to update:

- `CITATION.cff` — the commented `# doi:` line near the bottom
- `README.md` line ~149 — the Zenodo DOI reference
- The paper's data-availability sentence, in `paper/09-10-11-discussion-limits-repro-draft.md`
  and its English mirror `paper/en/09-10-11-discussion-limits-repro.md`

Then:

```bash
python paper/_assemble.py
python paper/en/_assemble.py
python paper/verify_all.py      # must stay at 0 failures
git add -A && git commit -m "Add the Zenodo DOI"
git tag -a v1.0.1 -m "Release with DOI"
git push origin master --tags
```

---

## Step 5 — request arXiv endorsement

**Start this first**, because it depends on another person replying and you do not control the
timing. arXiv does not require an academic affiliation; it requires an endorsement.

1. Pick a paper you cite whose author is likely to be reachable — something close in topic.
2. Open that paper's arXiv abstract page.
3. Click **"Which authors of this paper are endorsers?"** at the bottom right.
4. That gives you an endorsement code and a link to request one.
5. Send a short, specific request. Suggested text:

> Subject: arXiv endorsement request — cs.CL
>
> Dear Dr. [Name],
>
> I am an independent researcher and would like to submit a measurement study to arXiv
> (cs.CL). I am asking you for an endorsement because your work on [specific paper] is
> directly related to what I am submitting.
>
> The paper measures the cost, latency and failure boundaries of three judgment layers on a
> common item set — a local non-autoregressive typed-decision model, a remote typed-decision
> service, and a frontier LLM. Its central contribution is negative: it reports that the
> judges' own self-reported fields are unreliable, that capability collapses exactly where
> the task requires noticing an ABSENCE, and that a heterogeneous judge provided no
> incremental coverage in any of three task regimes.
>
> The artifact and its audit trail are public: [GitHub URL], archived at [DOI]. The paper
> records four of its own earlier conclusions as RETRACTED IN THE TEXT, and includes 59
> automated checks that a reader can re-run.
>
> Endorsement code: [code from the arXiv page]
>
> Thank you for considering it.

---

## Step 6 — submit

**English → arXiv.** Use the built `paper/en/MANUSCRIPT.md`. Category: **cs.CL** primary;
**cs.AI** secondary if offered. The AI-assistance disclosure is already in the manuscript;
arXiv requires it to be reported, and it is.

**Chinese → ChinaXiv** (<https://chinaxiv.org>). Use `paper/MANUSCRIPT.md`.

---

## What is already done and needs no action

- Author block in `CITATION.cff` (**PerryLink**, Independent Researcher, no ORCID claimed)
- AI-assistance disclosure, Option B, both languages, in the manuscripts — arXiv's three
  requirements (report the use, take responsibility, no AI authorship) are all satisfied
- Licence split: artifact **Apache-2.0**, paper **CC-BY-4.0**
- Conflict of interest disclosed in README, THIRD-PARTY, the paper and the disclosure
  (**the author maintains `laya-mcp`**, one of the systems evaluated, reported at 0.225)
- 48 references, every one opened against a fetched primary source
- Full English translation, 7 of 7 sections, assembled and checked
- Both manuscripts rebuilt and `verify_all.py` green at 62 checks

## What to look at before you run step 1

Two passages are worth your eyes because they are claims you will be signing:

1. **§7.6.1's before/after disclosure** — that putting the ignore-SUPERSEDED value among the
   options more than halves Δ_catch, so the regime-3 effect is substantially a function of how
   the options are built. It is the paper's own thesis applied to the paper's own measurement,
   and it is stated plainly rather than buried.
2. **The reinstated P26 ruling** — the only correction in this project that moves a claim UP.
   It is reinstated because the evidence was produced, not because it was re-read.
