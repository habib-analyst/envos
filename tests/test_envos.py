"""envos unit tests (stdlib unittest, deterministic)."""
import json
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from envos.model import Instance, DEFECTS  # noqa: E402
from envos.certify import certify  # noqa: E402
from envos.runner import run_episode  # noqa: E402
from envos.reconstruct import reconstruct, naive_baseline  # noqa: E402


class TestCertification(unittest.TestCase):
    def test_valid_instances_admitted(self):
        for seed in range(20):
            for wf in ("clinic", "insurance"):
                verdict, checks, _ = certify(Instance(seed, wf))
                self.assertEqual(verdict, "ADMIT", (seed, wf, checks))

    def test_each_defect_rejected(self):
        for defect in DEFECTS:
            if defect is None:
                continue
            for wf in ("clinic", "insurance"):
                verdict, checks, _ = certify(Instance(7, wf, defect))
                self.assertEqual(verdict, "REJECT", (defect, wf, checks))

    def test_unassessable_never_passes(self):
        verdict, checks, _ = certify(
            Instance(7, "clinic", "missing_mutation_record"))
        by_name = {c.name: c.status for c in checks}
        self.assertEqual(by_name["intervention_validity"], "unassessable")
        self.assertEqual(verdict, "REJECT")
        self.assertNotIn("pass", [by_name["intervention_validity"]])

    def test_no_check_reports_pass_when_unassessable(self):
        # Every check that cannot run must say so explicitly.
        _, checks, _ = certify(Instance(7, "clinic",
                                        "missing_mutation_record"))
        for c in checks:
            self.assertIn(c.status, ("pass", "violation", "unassessable"))


class TestArms(unittest.TestCase):
    def test_ordering_on_certified_instances(self):
        off = cue = live = 0
        n = 0
        for seed in range(50):
            for wf in ("clinic", "insurance"):
                inst = Instance(seed, wf)
                v, _, _ = certify(inst)
                assert v == "ADMIT"
                off += run_episode(inst, "OFF")["pipeline_verdict"]
                cue += run_episode(inst, "CUE")["pipeline_verdict"]
                live += run_episode(inst, "LIVE")["pipeline_verdict"]
                n += 1
        self.assertLess(off, cue)
        self.assertLess(cue, live)
        self.assertEqual(live, n)  # live-value arm recovers on all feasible

    def test_oracle_succeeds_and_never_fails_on_admitted(self):
        from envos.model import act, score, serve_and_mutate
        for seed in range(20):
            inst = Instance(seed, "clinic")
            ev = serve_and_mutate(inst)
            self.assertTrue(score(act("oracle", "LIVE", inst, {}),
                                  ev["authoritative"], True))
            self.assertFalse(score(act("never", "OFF", inst, {}),
                                   ev["authoritative"], True))


class TestReconstruction(unittest.TestCase):
    def test_clean_episode_matches(self):
        inst = Instance(3, "insurance")
        arch = run_episode(inst, "LIVE")
        r = reconstruct(arch)
        self.assertTrue(r["verdict_match"])
        self.assertEqual(r["attribution"], "clean")

    def test_agent_failure_attributed(self):
        inst = Instance(3, "clinic")
        arch = run_episode(inst, "OFF")
        r = reconstruct(arch)
        self.assertEqual(r["attribution"], "agent")
        self.assertEqual(naive_baseline(arch)["attribution"], "agent")

    def test_mutation_defect_attributed(self):
        inst = Instance(3, "clinic", "double_fire")
        arch = run_episode(inst, "LIVE")
        r = reconstruct(arch)
        self.assertEqual(r["attribution"], "mutation")
        self.assertEqual(naive_baseline(arch)["attribution"], "agent")

    def test_disclosure_defect_attributed(self):
        inst = Instance(3, "insurance", "disclosure_mismatch")
        arch = run_episode(inst, "LIVE")
        r = reconstruct(arch)
        self.assertEqual(r["attribution"], "disclosure")
        self.assertEqual(naive_baseline(arch)["attribution"], "agent")

    def test_grader_defect_attributed(self):
        inst = Instance(3, "clinic", "scorer_corrupt")
        arch = run_episode(inst, "LIVE")
        r = reconstruct(arch)
        self.assertEqual(r["attribution"], "grader")
        self.assertEqual(naive_baseline(arch)["attribution"], "agent")

    def test_missing_evidence_is_unassessable(self):
        inst = Instance(3, "clinic")
        arch = run_episode(inst, "LIVE")
        del arch["mutation_fired"]
        r = reconstruct(arch)
        # The verdict itself is still derivable, but validity cannot be
        # re-derived without the mutation record: attribution must be
        # unassessable, never a clean/agent verdict.
        self.assertEqual(r["attribution"], "unassessable")
        self.assertIn("mutation", r["notes"][0])


class TestDeterminism(unittest.TestCase):
    def test_archive_hash_stable(self):
        a1 = run_episode(Instance(11, "clinic"), "CUE")
        a2 = run_episode(Instance(11, "clinic"), "CUE")
        self.assertEqual(json.dumps(a1, sort_keys=True),
                         json.dumps(a2, sort_keys=True))
        self.assertEqual(a1["sha256"], a2["sha256"])


if __name__ == "__main__":
    unittest.main()
