"""Pre-run certification: the five EnvOS gates, plus the load-bearing rule
that an unassessable obligation is NEVER a pass.

Check statuses: "pass", "violation", "unassessable".
Certification verdict: ADMIT iff every check passes. Any violation or any
unassessable check -> REJECT. An unassessable check is recorded as a
monitor-error, never silently converted to a pass.
"""
from .model import (serve_and_mutate, disclose, act, score, score_stale,
                    scorer_probes)

PASS, VIOLATION, UNASSESSABLE = "pass", "violation", "unassessable"


class Check:
    def __init__(self, name, status, detail):
        self.name = name
        self.status = status
        self.detail = detail

    def to_dict(self):
        return {"name": self.name, "status": self.status, "detail": self.detail}


def _require(ev, key):
    """Missing evidence -> the check cannot run -> unassessable, never pass."""
    if key not in ev:
        raise KeyError(key)
    return ev[key]


def check_intervention_validity(inst, ev):
    """Mutation fired exactly once, after prior serve, changing the target."""
    try:
        fired = _require(ev, "fired")
        count = _require(ev, "fire_count")
        after = _require(ev, "fired_after_serve")
        auth = _require(ev, "authoritative")
    except KeyError as e:
        return Check("intervention_validity", UNASSESSABLE,
                     "missing evidence: %s" % e)
    if not ev.get("served", False):
        return Check("intervention_validity", VIOLATION,
                     "mutation fired without prior serve")
    if not fired or count != 1 or not after:
        return Check("intervention_validity", VIOLATION,
                     "fired=%s count=%s after_serve=%s" % (fired, count, after))
    if auth != inst.v1 or inst.v1 == inst.v0:
        return Check("intervention_validity", VIOLATION,
                     "authoritative value does not equal mutated value")
    return Check("intervention_validity", PASS, "one-time post-serve mutation")


def check_observation_consistency(inst, ev):
    """Delivered disclosure matches authoritative state at delivery time."""
    try:
        auth_del = _require(ev, "authoritative_at_delivery")
    except KeyError as e:
        return Check("observation_consistency", UNASSESSABLE,
                     "missing evidence: %s" % e)
    for arm in ("OFF", "CUE", "LIVE"):
        d = disclose(inst, arm, ev)
        if d["kind"] == "live_value" and d["value"] != auth_del:
            return Check("observation_consistency", VIOLATION,
                         "LIVE disclosure %r != authoritative %r"
                         % (d["value"], auth_del))
        if d["kind"] == "reminder" and d["value"] is not None:
            return Check("observation_consistency", VIOLATION,
                         "reminder must not carry a value")
        if d["kind"] == "none" and d["value"] is not None:
            return Check("observation_consistency", VIOLATION,
                         "OFF arm must disclose nothing")
    return Check("observation_consistency", PASS,
                 "all arms disclose consistently")


def check_feasibility(inst, ev):
    """A scripted reference route (oracle) succeeds on the instance."""
    try:
        auth = _require(ev, "authoritative")
    except KeyError as e:
        return Check("feasibility", UNASSESSABLE, "missing evidence: %s" % e)
    oracle_action = act("oracle", "LIVE", inst, {"kind": "live_value",
                                                 "value": auth})
    if score(oracle_action, auth, inst.feasible):
        return Check("feasibility", PASS, "oracle route succeeds")
    return Check("feasibility", VIOLATION, "no scripted route succeeds")


def check_discrimination(inst, ev):
    """The deficient policy (never re-checks) fails while the oracle
    succeeds: the instance actually exposes the stale-information
    deficiency it claims to measure."""
    try:
        auth = _require(ev, "authoritative")
    except KeyError as e:
        return Check("discrimination", UNASSESSABLE,
                     "missing evidence: %s" % e)
    never_ok = score(act("never", "OFF", inst, {"kind": "none",
                                                "value": None}),
                     auth, inst.feasible)
    oracle_ok = score(act("oracle", "LIVE", inst, {"kind": "live_value",
                                                   "value": auth}),
                      auth, inst.feasible)
    if oracle_ok and not never_ok:
        return Check("discrimination", PASS,
                     "never-policy fails, oracle succeeds")
    return Check("discrimination", VIOLATION,
                 "never_ok=%s oracle_ok=%s" % (never_ok, oracle_ok))


def check_scorer_robustness(inst):
    """The scorer passes its probe battery (correct / stale / wrong /
    near-miss / valid controls). A corrupted scorer fails at least one."""
    fn = score_stale if inst.defect == "scorer_corrupt" else None
    for action, auth, feas, expected in scorer_probes(inst):
        if fn is not None:
            got = fn(action, inst, feas)
        else:
            got = score(action, auth, feas)
        if got != expected:
            return Check("scorer_robustness", VIOLATION,
                         "probe failed: action=%r auth=%r feas=%s "
                         "expected=%s got=%s"
                         % (action, auth, feas, expected, got))
    return Check("scorer_robustness", PASS, "all scorer probes pass")


def certify(inst):
    """Run all five gates on a candidate instance. Returns
    (verdict, [Check, ...], evidence). verdict is ADMIT or REJECT."""
    ev = serve_and_mutate(inst)
    checks = [
        check_intervention_validity(inst, ev),
        check_observation_consistency(inst, ev),
        check_feasibility(inst, ev),
        check_discrimination(inst, ev),
        check_scorer_robustness(inst),
    ]
    verdict = "ADMIT" if all(c.status == PASS for c in checks) else "REJECT"
    return verdict, checks, ev
