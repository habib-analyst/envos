"""envos core model: seeded synthetic worlds, phenomenon perturbation,
disclosure channels, scripted agent policies, and the terminal scorer.

Scripted-analog scope (stated everywhere): no LLMs, no APIs, no GPUs.
Two workflow instances of the paper's stale-information phenomenon:
  - clinic:    an appointment's location moves after the agent saw it.
  - insurance: a policy coverage cap is lowered after the agent read it.
The paper's frontier-model figures are context only and are never claimed here.
"""
import random

DOCTORS = ["Dr. Alvarez", "Dr. Chen", "Dr. Okafor", "Dr. Patel", "Dr. Novak"]
DATES = ["2026-11-09", "2026-11-10", "2026-11-11", "2026-11-12"]
TIMES = ["09:00", "10:30", "13:00", "15:30"]
LOCATIONS = ["Room 101", "Room 204", "Wing B", "Annex 3", "Suite 12"]
PROCEDURES = ["MRI brain", "CT chest", "knee arthroscopy", "colonoscopy", "echocardiogram"]

# Defect flags a candidate instance may carry (None = valid instance).
DEFECTS = (None, "never_fires", "double_fire", "no_prior_serve",
           "disclosure_mismatch", "unsolvable", "scorer_corrupt",
           "irrelevant_mutation", "missing_mutation_record")


class Instance:
    """One seeded candidate evaluation instance."""

    def __init__(self, seed, workflow, defect=None):
        assert workflow in ("clinic", "insurance")
        assert defect in DEFECTS
        rng = random.Random(seed)
        self.seed = seed
        self.workflow = workflow
        self.defect = defect
        if workflow == "clinic":
            self.target = "%s %s %s" % (rng.choice(DOCTORS), rng.choice(DATES),
                                        rng.choice(TIMES))
            self.v0 = rng.choice(LOCATIONS)
            rest = [loc for loc in LOCATIONS if loc != self.v0]
            self.v1 = rng.choice(rest)
        else:
            self.target = rng.choice(PROCEDURES)
            self.v0 = rng.choice([5000, 8000, 12000, 20000])
            self.v1 = self.v0 // 2
        # Whether the change is visible in the summary/list view the
        # reminder policy re-reads (a property of the disclosure design,
        # not a coin flip at run time: fixed per instance by its seed).
        self.visible_in_summary = rng.random() < 0.4
        # Feasibility: unsolvable defect makes even the oracle fail.
        self.feasible = defect != "unsolvable"

    def to_dict(self):
        return {"seed": self.seed, "workflow": self.workflow,
                "defect": self.defect, "target": self.target,
                "v0": self.v0, "v1": self.v1,
                "visible_in_summary": self.visible_in_summary,
                "feasible": self.feasible}


def serve_and_mutate(inst):
    """Simulate the exposure-conditioned one-time perturbation.

    Returns an evidence dict. The mutation fires only after the old value
    was served (prior-serve anchor) and at most once (once-only guard),
    unless the instance carries a defect that breaks exactly one of these.
    """
    ev = {}
    if inst.defect == "no_prior_serve":
        ev["served"] = False
        ev["fired"] = True
        ev["fire_count"] = 1
        ev["fired_after_serve"] = False
        ev["authoritative"] = inst.v1
        return ev
    ev["served"] = True
    ev["fired_after_serve"] = True
    if inst.defect == "never_fires":
        ev["fired"] = False
        ev["fire_count"] = 0
        ev["authoritative"] = inst.v0
    elif inst.defect == "double_fire":
        ev["fired"] = True
        ev["fire_count"] = 2
        # Second fire moves the value again, after disclosure.
        ev["authoritative"] = "MOVED-AGAIN"
        ev["authoritative_at_delivery"] = inst.v1
    elif inst.defect == "irrelevant_mutation":
        ev["fired"] = True
        ev["fire_count"] = 1
        # Mutation touches an unrelated field; the target value is unchanged.
        ev["authoritative"] = inst.v0
    else:
        ev["fired"] = True
        ev["fire_count"] = 1
        ev["authoritative"] = inst.v1
    ev.setdefault("authoritative_at_delivery", ev["authoritative"])
    if inst.defect == "missing_mutation_record":
        # Evidence needed by the intervention-validity check is absent.
        ev.pop("fired", None)
        ev.pop("fire_count", None)
    return ev


def disclose(inst, arm, ev):
    """Disclosure channel for one arm. Returns delivered content.

    OFF:  nothing extra. CUE: reminder to re-check, no value.
    LIVE: the current authoritative value, as of delivery time.
    The disclosure_mismatch defect delivers the stale value as current.
    """
    assert arm in ("OFF", "CUE", "LIVE")
    if arm == "OFF":
        return {"kind": "none", "value": None}
    if arm == "CUE":
        return {"kind": "reminder", "value": None}
    delivered = ev.get("authoritative_at_delivery", ev.get("authoritative"))
    if inst.defect == "disclosure_mismatch":
        delivered = inst.v0
    return {"kind": "live_value", "value": delivered}


def act(policy, arm, inst, delivered):
    """Scripted agent policies (controlled re-check behaviour)."""
    assert policy in ("never", "reminder", "live", "oracle")
    if policy == "oracle":
        # Reference route: always re-reads authoritative state.
        return inst.v1 if inst.defect != "double_fire" else "MOVED-AGAIN"
    if policy == "never":
        return inst.v0
    if policy == "reminder":
        if arm == "CUE" and inst.visible_in_summary:
            return inst.v1
        return inst.v0
    if policy == "live":
        if arm == "LIVE" and delivered["kind"] == "live_value":
            return delivered["value"]
        return inst.v0
    raise AssertionError(policy)


def score(action_value, authoritative_value, feasible):
    """Terminal scorer: acted value must equal authoritative value."""
    if not feasible:
        return False
    return action_value == authoritative_value


def score_stale(action_value, inst, feasible):
    """Corrupted scorer (scorer_corrupt defect): compares against the
    stale value instead of the authoritative value."""
    if not feasible:
        return False
    return action_value == inst.v0


def scorer_probes(inst):
    """Probe battery for scorer robustness: (action, authoritative,
    feasible, expected). A sound scorer passes all; a corrupted scorer
    (stale comparison, always-pass, always-fail) fails at least one."""
    return [
        (inst.v1, inst.v1, True, True),    # correct action, valid control
        (inst.v0, inst.v1, True, False),   # stale action must fail
        ("WRONG-VALUE", inst.v1, True, False),  # wrong value must fail
        (inst.v1, inst.v1, False, False),  # infeasible instance must fail
        (inst.v0, inst.v0, True, True),    # no-change control passes
        (inst.v1, inst.v0, True, False),   # near-miss: new value, old truth
    ]
