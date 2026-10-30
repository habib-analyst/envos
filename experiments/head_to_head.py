"""Head-to-head (fresh seed set B) vs PREREG.md bars. Deterministic:
no timestamps; run twice and compare sha256 of the results file."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from envos.model import Instance, DEFECTS  # noqa: E402
from envos.certify import certify  # noqa: E402
from envos.runner import run_episode  # noqa: E402
from envos.reconstruct import reconstruct, naive_baseline  # noqa: E402
from envos.stats import paired_bootstrap_ci, wilson_interval  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "results",
                    "head_to_head.json")


def main():
    res = {}

    # ---- G2a: certification on fresh seeds ----
    valid = {}
    for wf in ("clinic", "insurance"):
        adm = rej = 0
        for s in range(5000, 5120):
            v, _, _ = certify(Instance(s, wf))
            if v == "ADMIT":
                adm += 1
            else:
                rej += 1
        valid[wf] = {"admitted": adm, "rejected": rej,
                     "accept_rate": adm / (adm + rej)}
    broken = {}
    tot_rej = tot = 0
    for defect in DEFECTS:
        if defect is None:
            continue
        rej = adm = 0
        for wf in ("clinic", "insurance"):
            for i in range(10):
                v, _, _ = certify(Instance(5200 + i, wf, defect))
                if v == "REJECT":
                    rej += 1
                else:
                    adm += 1
        broken[defect] = {"rejected": rej, "admitted": adm,
                          "reject_rate": rej / (rej + adm)}
        tot_rej += rej
        tot += rej + adm
    res["G2a_certification"] = {
        "valid": valid, "broken": broken,
        "broken_reject_rate_overall": tot_rej / tot}

    # ---- G2b: arm ordering, paired bootstrap ----
    arms = {}
    pooled = {"OFF": [], "CUE": [], "LIVE": []}
    for wf in ("clinic", "insurance"):
        per = {"OFF": [], "CUE": [], "LIVE": []}
        for s in range(6000, 6200):
            inst = Instance(s, wf)
            v, _, _ = certify(inst)
            assert v == "ADMIT", (s, wf)
            for arm in per:
                r = int(run_episode(inst, arm)["pipeline_verdict"])
                per[arm].append(r)
                pooled[arm].append(r)
        arms[wf] = {
            "n": len(per["OFF"]),
            "rates": {a: sum(per[a]) / len(per[a]) for a in per},
            "ci_cue_minus_off": paired_bootstrap_ci(per["OFF"], per["CUE"]),
            "ci_live_minus_cue": paired_bootstrap_ci(per["CUE"], per["LIVE"]),
        }
    arms["pooled"] = {
        "n": len(pooled["OFF"]),
        "rates": {a: sum(pooled[a]) / len(pooled[a]) for a in pooled},
        "ci_cue_minus_off": paired_bootstrap_ci(pooled["OFF"], pooled["CUE"]),
        "ci_live_minus_cue": paired_bootstrap_ci(pooled["CUE"],
                                                 pooled["LIVE"]),
    }
    res["G2b_arm_ordering"] = arms

    # ---- G3: attribution on constructed failure episodes ----
    classes = [
        ("mutation", "double_fire", "LIVE"),
        ("disclosure", "disclosure_mismatch", "LIVE"),
        ("grader", "scorer_corrupt", "LIVE"),
        ("agent", None, "OFF"),
    ]
    attrib = {}
    pipe_ok = naive_ok = tot_f = 0
    for name, defect, arm in classes:
        p_ok = n_ok = 0
        for i in range(50):
            inst = Instance(7000 + i, "clinic" if i % 2 == 0 else "insurance",
                            defect)
            arch = run_episode(inst, arm)
            assert arch["pipeline_verdict"] is False, (name, i)
            r = reconstruct(arch)
            if r["attribution"] == name:
                p_ok += 1
            if naive_baseline(arch)["attribution"] == name:
                n_ok += 1
        attrib[name] = {"n": 50, "pipeline_correct": p_ok,
                        "pipeline_rate": p_ok / 50,
                        "naive_correct": n_ok, "naive_rate": n_ok / 50}
        pipe_ok += p_ok
        naive_ok += n_ok
        tot_f += 50
    attrib["pooled"] = {"n": tot_f, "pipeline_rate": pipe_ok / tot_f,
                        "naive_rate": naive_ok / tot_f}
    res["G3_attribution"] = attrib

    # ---- G3 benign bound: reconstruction match on clean episodes ----
    match = 0
    n_clean = 0
    for s in range(7100, 7250):
        inst = Instance(s, "clinic" if s % 2 == 0 else "insurance")
        v, _, _ = certify(inst)
        assert v == "ADMIT"
        arch = run_episode(inst, "LIVE")
        assert arch["pipeline_verdict"] is True
        r = reconstruct(arch)
        match += int(r["verdict_match"] and r["attribution"] == "clean")
        n_clean += 1
    res["G3_benign"] = {
        "clean_episodes": n_clean, "reconstruction_match": match,
        "match_rate": match / n_clean,
        "valid_reject_rate_pooled":
            1 - sum(valid[w]["admitted"] for w in valid) / 240.0}

    # ---- PREREG bar evaluation (no bar-moving: bars from PREREG.md) ----
    bars = {}
    bars["G2a_valid_accept_ge_95"] = all(
        valid[w]["accept_rate"] >= 0.95 for w in valid)
    bars["G2a_broken_reject_ge_90"] = \
        res["G2a_certification"]["broken_reject_rate_overall"] >= 0.90
    bars["G2a_broken_per_class_ge_80"] = all(
        broken[d]["reject_rate"] >= 0.80 for d in broken)
    bars["G2b_ci_cue_minus_off_gt_0"] = all(
        arms[k]["ci_cue_minus_off"][1] > 0 for k in arms)
    bars["G2b_ci_live_minus_cue_gt_0"] = all(
        arms[k]["ci_live_minus_cue"][1] > 0 for k in arms)
    bars["G3_pipeline_attrib_ge_90"] = attrib["pooled"]["pipeline_rate"] >= 0.90
    bars["G3_pipeline_per_class_ge_80"] = all(
        attrib[c]["pipeline_rate"] >= 0.80 for c in
        ("mutation", "disclosure", "grader", "agent"))
    bars["G3_naive_le_50"] = attrib["pooled"]["naive_rate"] <= 0.50
    bars["G3_reconstruction_match_ge_98"] = \
        res["G3_benign"]["match_rate"] >= 0.98
    bars["G3_valid_reject_le_5"] = \
        res["G3_benign"]["valid_reject_rate_pooled"] <= 0.05
    bars["ALL_PASS"] = all(bars.values())
    res["prereg_bars"] = bars

    with open(OUT, "w") as f:
        f.write(json.dumps(res, sort_keys=True, indent=1))
    print(json.dumps(res, sort_keys=True, indent=1))


if __name__ == "__main__":
    main()
