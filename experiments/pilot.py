"""Pilot gate (seed set A): small-sample checks before PREREG lock.
(a) certification rejects broken instances, accepts valid ones;
(b) stale-information arm ordering never < reminder < live-value;
(c) unassessable != pass, literally.
Writes results/pilot.json (no timestamps, deterministic)."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from envos.model import Instance, DEFECTS  # noqa: E402
from envos.certify import certify  # noqa: E402
from envos.runner import run_episode  # noqa: E402
from envos.reconstruct import reconstruct  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "results", "pilot.json")

VALID_SEEDS = range(1000, 1024)          # 24 per workflow
BROKEN_PER_CLASS = 4                     # per workflow


def main():
    res = {"valid": {}, "broken": {}, "arms": {}, "unassessable": {}}
    # (a) valid acceptance
    for wf in ("clinic", "insurance"):
        admitted = rejected = 0
        for s in VALID_SEEDS:
            v, _, _ = certify(Instance(s, wf))
            if v == "ADMIT":
                admitted += 1
            else:
                rejected += 1
        res["valid"][wf] = {"admitted": admitted, "rejected": rejected}
    # (a) broken rejection, per defect class
    for defect in DEFECTS:
        if defect is None:
            continue
        res["broken"][defect] = {}
        for wf in ("clinic", "insurance"):
            rejected = admitted = 0
            for i in range(BROKEN_PER_CLASS):
                v, _, _ = certify(Instance(2000 + i, wf, defect))
                if v == "REJECT":
                    rejected += 1
                else:
                    admitted += 1
            res["broken"][defect][wf] = {"rejected": rejected,
                                         "admitted": admitted}
    # (b) arm ordering on certified valid instances
    for wf in ("clinic", "insurance"):
        counts = {"OFF": 0, "CUE": 0, "LIVE": 0}
        n = 0
        for s in VALID_SEEDS:
            inst = Instance(s, wf)
            v, _, _ = certify(inst)
            assert v == "ADMIT"
            for arm in counts:
                counts[arm] += int(run_episode(inst, arm)["pipeline_verdict"])
            n += 1
        res["arms"][wf] = {"n": n, "successes": counts,
                           "rates": {a: counts[a] / n for a in counts}}
    # (c) unassessable: missing-record instances must REJECT with an
    # explicitly unassessable check, and reconstruction of an archive with
    # a deleted mutation record must attribute "unassessable".
    inst = Instance(2000, "clinic", "missing_mutation_record")
    v, checks, _ = certify(inst)
    res["unassessable"]["certify_verdict"] = v
    res["unassessable"]["check_statuses"] = {c.name: c.status
                                             for c in checks}
    arch = run_episode(Instance(2000, "clinic"), "LIVE")
    del arch["mutation_fired"]
    res["unassessable"]["reconstruct_attribution"] = \
        reconstruct(arch)["attribution"]
    with open(OUT, "w") as f:
        f.write(json.dumps(res, sort_keys=True, indent=1))
    print(json.dumps(res, sort_keys=True, indent=1))


if __name__ == "__main__":
    main()
