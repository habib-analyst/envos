"""Frozen-rule execution: run one agent episode on one instance and
archive all evidence needed for independent verdict reconstruction."""
import hashlib
import json

from .model import serve_and_mutate, disclose, act, score, score_stale

ARM_POLICY = {"OFF": "never", "CUE": "reminder", "LIVE": "live"}


def run_episode(inst, arm):
    """Execute one episode under frozen rules. Returns the evidence
    archive (JSON-serializable dict). The archive carries its own sha256
    over its canonical form (excluding the hash field itself)."""
    ev = serve_and_mutate(inst)
    delivered = disclose(inst, arm, ev)
    policy = ARM_POLICY[arm]
    action = act(policy, arm, inst, delivered)
    auth = ev.get("authoritative")
    scorer = score_stale if inst.defect == "scorer_corrupt" else None
    if scorer is not None:
        verdict = scorer(action, inst, inst.feasible)
    else:
        verdict = score(action, auth, inst.feasible)
    archive = {
        "seed": inst.seed,
        "workflow": inst.workflow,
        "defect": inst.defect,
        "arm": arm,
        "policy": policy,
        "target": inst.target,
        "v0": inst.v0,
        "v1": inst.v1,
        "feasible": inst.feasible,
        "visible_in_summary": inst.visible_in_summary,
        "served": ev.get("served"),
        "mutation_fired": ev.get("fired"),
        "mutation_fire_count": ev.get("fire_count"),
        "fired_after_serve": ev.get("fired_after_serve"),
        "authoritative_at_delivery": ev.get("authoritative_at_delivery"),
        "authoritative_at_decision": auth,
        "disclosed_kind": delivered["kind"],
        "disclosed_value": delivered["value"],
        "agent_action_value": action,
        "pipeline_verdict": verdict,
    }
    archive["sha256"] = hashlib.sha256(
        json.dumps(archive, sort_keys=True).encode()).hexdigest()
    return archive


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, indent=1)
