# envos — open analog of EnvOS (arXiv 2610.40246)

Auditing computer-use agents when the world moves on: a framework for
building and **certifying** evaluation environments that change mid-task,
so a failure can be attributed to the agent rather than to broken
benchmark machinery. This is a scripted, CPU-only, $0 analog of the
paper's framework — not a reproduction of its frontier-model results.

## The idea (paper, §2–§3)

1. **Phenomenon–perturbation construction.** A seeded world plus a
   one-time, exposure-conditioned state mutation (fires only after the
   old value was served, at most once) plus a disclosure channel plus a
   once-only guard.
2. **Pre-run certification.** Five gates, all required: intervention
   validity, observation consistency, feasibility via a scripted route,
   behavioral discrimination, scorer robustness. An unassessable
   obligation does **not** count as a pass — a check that cannot run
   returns violation/monitor-error, never a pass.
3. **Frozen-rule execution** with archived evidence and **independent
   verdict reconstruction** from that archive (a separate code path
   that never imports the scorer, gates, or runner).

Principal study: **stale information** — a value the agent already saw
changes before it acts. Two synthetic workflow instances: clinic booking
(an appointment's location moves) and insurance approval (a policy cap
is lowered). Scripted agents with controlled re-check policies:
never / reminder-only / live-value, in OFF / CUE / LIVE disclosure arms.

## What was measured (scripted analog only)

- Certification: 240/240 valid instances admitted; 160/160 deliberately
  broken instances rejected across 8 defect classes (see
  `results/head_to_head.json`).
- Arm ordering (paired bootstrap 95% CIs exclude the null orderings):
  OFF < CUE < LIVE in both workflows.
- Attribution: the certification + reconstruction pipeline correctly
  attributes failures (agent vs mutation vs disclosure vs grader) where
  the naive "run agent, score terminal state" baseline cannot.
- Benign bound: reconstruction matches the pipeline verdict on clean
  episodes; valid-instance rejection within the locked bound.

The paper's frontier-model figures (clinic 0/16 → 15/16, insurance
1/10 → 9/10, corrupted episodes 0/26 accepted, external set 25/39 vs 4)
are **context only** and are never claimed as reproduced here.

## Layout

- `envos/model.py` — seeded worlds, perturbation, disclosure, policies, scorer
- `envos/certify.py` — the five pre-run gates (unassessable ≠ pass)
- `envos/runner.py` — frozen-rule execution + evidence archive (sha256)
- `envos/reconstruct.py` — independent reconstruction + attribution
- `envos/stats.py` — paired bootstrap CIs, Wilson intervals
- `experiments/pilot.py` — pilot gate (seed set A)
- `experiments/head_to_head.py` — preregistered head-to-head (seed set B)
- `KILLGATE.md` — gate verdicts incl. the G1 author-code recheck
- `PREREG.md` — locked bars (any bar fails → KILL, no bar-moving)

## Run

```bash
python3 -m unittest discover -s tests
python3 experiments/pilot.py
python3 experiments/head_to_head.py   # twice; results file byte-identical
```

Requirements: Python 3.10+ stdlib only. No network, no GPU, no cost.
