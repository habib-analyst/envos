"""Independent verdict reconstruction from archived evidence ONLY.

This module deliberately does NOT import the scorer, the certification
gates, or the runner. It re-derives the verdict and the failure
attribution from the archive's own fields, using separately written logic.
A term it cannot resolve is reported "unassessable" (monitor-error) --
never silently resolved in favour of a clean verdict.

Attribution classes: agent / mutation / disclosure / grader / clean /
unassessable.
"""
import json


def _need(archive, key):
    if key not in archive or archive[key] is None:
        raise KeyError(key)
    return archive[key]


def reconstruct(archive):
    """Returns dict with reconstructed_verdict (True/False/None),
    verdict_match (bool, False when unassessable), attribution, and notes.
    reconstructed_verdict None means unassessable."""
    notes = []
    # --- independent verdict: acted value vs authoritative value ---
    try:
        action = _need(archive, "agent_action_value")
        auth = _need(archive, "authoritative_at_decision")
        feasible = _need(archive, "feasible")
    except KeyError as e:
        return {"reconstructed_verdict": None, "verdict_match": False,
                "attribution": "unassessable",
                "notes": ["missing evidence for verdict: %s" % e]}
    recon = (action == auth) if feasible else False
    pipeline = archive.get("pipeline_verdict")
    match = (pipeline == recon) if pipeline is not None else False
    if pipeline is None:
        notes.append("pipeline verdict missing from archive")

    # --- validity re-derivation from the archive ---
    try:
        fired = _need(archive, "mutation_fired")
        count = _need(archive, "mutation_fire_count")
        after = _need(archive, "fired_after_serve")
        served = _need(archive, "served")
    except KeyError as e:
        return {"reconstructed_verdict": recon, "verdict_match": match,
                "attribution": "unassessable",
                "notes": ["missing evidence for mutation validity: %s" % e]}
    mutation_ok = (served is True and fired is True and count == 1
                   and after is True)
    try:
        kind = _need(archive, "disclosed_kind")
        dval = archive.get("disclosed_value")
        auth_del = _need(archive, "authoritative_at_delivery")
    except KeyError as e:
        return {"reconstructed_verdict": recon, "verdict_match": match,
                "attribution": "unassessable",
                "notes": ["missing evidence for disclosure validity: %s" % e]}
    if kind == "live_value":
        disclosure_ok = (dval == auth_del)
    elif kind in ("reminder", "none"):
        disclosure_ok = (dval is None)
    else:
        disclosure_ok = False

    # --- attribution. The recorded outcome is the pipeline verdict: a
    # mismatch between pipeline and independent reconstruction is itself
    # a grader failure, checked before the mutation/disclosure/agent
    # causes (in single-defect episodes these never co-occur with a
    # mismatch, but the order makes the grader check decisive).
    if not match:
        attribution = "grader"
    elif pipeline is True:
        attribution = "clean"
    elif not mutation_ok:
        attribution = "mutation"
    elif not disclosure_ok:
        attribution = "disclosure"
    else:
        attribution = "agent"
    return {"reconstructed_verdict": recon, "verdict_match": match,
            "attribution": attribution, "notes": notes}


def naive_baseline(archive):
    """Naive 'run agent, score terminal state' baseline: it sees only the
    pipeline verdict and attributes every failure to the agent. It cannot
    distinguish agent failure from mutation, disclosure, or grader failure."""
    verdict = archive.get("pipeline_verdict")
    if verdict is None:
        return {"verdict": None, "attribution": "unassessable"}
    return {"verdict": verdict,
            "attribution": "clean" if verdict else "agent"}


def archive_json(archive):
    return json.dumps(archive, sort_keys=True)
