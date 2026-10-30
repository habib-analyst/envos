# KILLGATE — project #102 `envos` (kill-gate first)

Source paper: arXiv 2610.40246, "EnvOS: Auditing Computer-Use Agents When
the World Moves On" (Kadu et al., QpiAI, submitted 29 Oct 2026).
Build: open analog — certification framework + evidence archive +
independent reconstruction, with scripted agents on two seeded synthetic
workflows (clinic booking, insurance approval). Pure stdlib Python,
deterministic, CPU-only, $0, no LLMs/APIs/GPUs.

## Gate verdicts

- **G0 harness: PASS.** Deterministic, CPU-only, $0, no LLMs/APIs/GPUs.
  13/13 unit tests green. Archive re-run byte-identical (sha256 stable).
- **G1 author-code recheck: PASS, with a documented caveat.**
  Checked fresh 2026-10-30:
  - Abs page (arxiv.org/abs/2610.40246): NO author code link. The "Code,
    Data and Media" section holds only third-party finder toggles
    (alphaXiv, CatalyzeX, DagsHub, Hugging Face, etc.).
  - Full-text HTML (arxiv.org/html/2610.40246v1, 15,212 lines): ZERO
    zenodo, ZERO 4open, ZERO "replication package" matches. GitHub
    matches are only LaTeXML/arXiv feedback links and reference titles.
  - Web search ("EnvOS Kadu code github"): noise only, no author repo.
  - Caveat, stated plainly: the paper repeatedly refers to an
    *anonymous supplement* (a 24,399-file / 94.6 MB package of raw
    archives, scorer outputs, validity re-derivations, a no-model
    reproduction target, and at least one task module) and to "released
    scorer source" (digest a113a2a8). HOWEVER: the paper gives NO public
    location for that supplement — no URL, DOI, repo link, or reference
    entry — and its described contents are review-evidence archives plus
    a reproduction target, not a released implementation of the
    certification framework itself. Unlike #100 (replication package
    cited by host, anonymous.4open.science) and PORTAL (4open link in a
    footnote), there is no retrievable author artifact to duplicate.
    This build therefore does not duplicate any author-released
    instrument. If the orchestrator reads the supplement references as a
    G1 kill under the #100 precedent, that veto is recorded here as an
    open challenge to this verdict — the evidence is quoted above so the
    decision can be re-litigated without re-fetching.
- **Pilot gate: PASS (all three prongs, seed set A).**
  - (a) Certification: 48/48 valid instances ADMITTED (24/workflow);
    64/64 deliberately broken instances REJECTED (8 defect classes x 4
    x 2 workflows: never_fires, double_fire, no_prior_serve,
    disclosure_mismatch, unsolvable, scorer_corrupt,
    irrelevant_mutation, missing_mutation_record).
  - (b) Stale-information ordering on certified instances: clinic
    OFF 0/24 < CUE 10/24 (0.417) < LIVE 24/24 (1.0); insurance OFF 0/24
    < CUE 9/24 (0.375) < LIVE 24/24 (1.0).
  - (c) Unassessable != pass, literally: missing-mutation-record
    instance REJECTED with intervention_validity status
    "unassessable" (not pass); reconstruction of an archive with a
    deleted mutation record attributes "unassessable", never clean/agent.
- **G2 disease: PASS (fresh seeds, PREREG-locked bars).**
  Valid acceptance 120/120 per workflow (bar >=95%); broken rejection
  160/160 overall and 20/20 per defect class (bars >=90% / >=80%).
  Arm ordering with paired bootstrap 95% CIs excluding null orderings:
  clinic CUE-OFF +0.355 [0.290, 0.420], LIVE-CUE +0.645 [0.580, 0.710];
  insurance CUE-OFF +0.335 [0.270, 0.400], LIVE-CUE +0.665 [0.600, 0.730];
  pooled CUE-OFF +0.345 [0.297, 0.393], LIVE-CUE +0.655 [0.608, 0.703].
- **G3 load-bearing mechanism: PASS.** Pipeline attribution 200/200
  across mutation/disclosure/grader/agent classes (bar >=90%);
  naive baseline 25% pooled (bar <=50%) — correct only on agent
  episodes. Benign bound: reconstruction matched on 150/150 clean
  episodes (bar >=98%); valid rejection 0/240 (bar <=5%).
- **Tests / determinism: PASS.** 13/13 tests green; head-to-head run
  twice, results file byte-identical, sha256
  040af03df395ba4a210ab271f02c4f2ec89bd8fc5a83739e55fa2227b2f70b9d.
- **Overall verdict: PASS.** Staged payload in ~/workspace/build/envos/;
  PAPER.md at hidden_files/papers/envos/PAPER.md; LinkedIn draft DRAFT
  ONLY at hidden_files/linkedin_drafts/envos.md (not queued anywhere).
  **REPO NEEDED: habib-analyst/envos.** No repo created, nothing pushed.

## Scope honesty (mandatory)

- All numbers are SCRIPTED-ANALOG numbers. The paper's frontier-model
  figures (clinic 0/16 -> 15/16, insurance 1/10 -> 9/10, corrupted
  episodes 0/26 accepted, external set 25/39 vs 4) are CONTEXT ONLY and
  are never presented as reproduced.
- OFF = 0 on certified instances is a consequence of the discrimination
  gate (admission requires the never-policy to fail); the measured
  effects are the interior CUE rate (reminder recovers only when the
  change is visible in the summary view) and LIVE = 1.0.
- Appendix S1 phenomenon families are OUT of preregistered bars (the
  brief's rule); only the principal stale-information phenomenon is gated.
