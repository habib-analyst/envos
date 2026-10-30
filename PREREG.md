# PREREG — project #102 `envos` (LOCKED before head-to-head)

Locked: 2026-10-30, after the pilot (seed set A) and before any
head-to-head run. Head-to-head uses FRESH seeds (sets B) never used in
the pilot or unit tests. Decision rule (standing, no exceptions):
ANY locked bar fails -> KILL. No post-hoc bar changes, no bar-shrinking.

## What is gated

The certification + evidence pipeline (pre-run gates + post-run
independent reconstruction from archived evidence) vs the naive
"run agent, score terminal state" baseline, on the scripted analog of
the paper's stale-information phenomenon (clinic booking, insurance
approval). Appendix S1 families are excluded from all bars.

## G2 — disease (certification quality + arm ordering)

- G2a certification: on fresh seeds (valid: seeds 5000-5119 per
  workflow, n=240; broken: 10 per defect class per workflow, n=160
  across 8 classes):
  - valid-instance acceptance >= 95% per workflow;
  - broken-instance rejection >= 90% overall AND >= 80% per defect
    class (pooled across workflows).
- G2b arm ordering: on fresh certified instances (seeds 6000-6199 per
  workflow, n=200/workflow, same instance across all three arms):
  - paired bootstrap 95% CI (10,000 resamples, seed 12345) for
    (CUE - OFF) has lower bound > 0, AND for (LIVE - CUE) has lower
    bound > 0, per workflow and pooled. (OFF = 0 by admission is
    acknowledged: the discrimination gate requires the never-policy to
    fail, so the informative comparisons are the interior CUE rate and
    LIVE - CUE; the CI rule still applies to both differences.)

## G3 — load-bearing mechanism (attribution + benign bound)

- Attribution: on failure episodes (50 per class, fresh seeds 7000+):
  classes = mutation (double_fire + LIVE arm), disclosure
  (disclosure_mismatch + LIVE arm), grader (scorer_corrupt + LIVE arm),
  agent (valid instance + OFF arm). True cause is the constructed
  defect (agent class: no defect, never-policy failure).
  - pipeline correct-attribution rate >= 90% pooled across classes,
    AND >= 80% per class;
  - naive baseline (attributes every failure to the agent) <= 50%
    pooled — i.e. the naive baseline cannot do this task.
- Benign/utility bound:
  - valid-instance rejection <= 5% (same numbers as G2a);
  - independent reconstruction matches the pipeline verdict on >= 98%
    of clean episodes (live-policy episodes on certified valid
    instances, seeds 7100-7249, n=150).

## Analysis rules

- Determinism: head-to-head run twice; results file byte-identical
  (sha256 recorded). Any nondeterminism voids the run.
- Tests green before the run; any test failure voids the run.
- Numbers reported are measured only. The paper's frontier-model
  figures are context, never results.
