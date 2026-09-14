"""Focused no-launch tests for the DEV14 R691 construction candidate tools."""

from __future__ import annotations

import importlib.util
import pathlib
import unittest


HERE = pathlib.Path(__file__).resolve().parent


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generator = load_module(
    "domain_construction_candidate_generator",
    "generate_domain_construction_one_day_candidate.py",
)
runner = load_module(
    "domain_construction_candidate_runner",
    "run_domain_construction_one_day_candidate.py",
)


class DomainConstructionCandidateTests(unittest.TestCase):
    def test_named_pipe_is_canonical_and_legacy_shape_is_rejected(self) -> None:
        self.assertEqual(runner.validate_named_pipe(generator.PIPE), generator.PIPE)
        with self.assertRaises(runner.CandidateError):
            runner.validate_named_pipe(r"\.\pipe\legacy")

    def test_date_only_step_and_counter_classification(self) -> None:
        target, command = runner.build_date_only_arm_step(17_000)
        self.assertEqual(target, 17_024)
        self.assertIn("17000-to-17024", command)
        self.assertEqual(
            runner.classify_counter_deltas(
                {"producer_calls": 0, "accepted_captures": 0}
            ),
            "BOUNDED_NO_GO",
        )
        self.assertEqual(
            runner.classify_counter_deltas(
                {"producer_calls": 1, "accepted_captures": 1}
            ),
            "GREEN",
        )
        with self.assertRaises(runner.CandidateError):
            runner.classify_counter_deltas(
                {"producer_calls": 1, "accepted_captures": 0}
            )

    def test_live_runner_rebind_is_exact_and_single_resume(self) -> None:
        source = '''from preflight_r690 import run_preflight
ROUND = "R690"
OLD_ROUND = "R689"
PIPE = r"\\\\.\\pipe\\xar_ck3_bridge_g2_m4_r690_construction_one_day_e08f4a1"
STATE = ART / "state-r690"
LIVE = ART / "live-r690"
previous = "R689"
probe = "DEV13"
first = "set-speed-3"
second = "resume-map"
'''
        rebound = generator.rebind_live_runner(source)
        compile(rebound, "run_r691.py", "exec")
        self.assertIn("from preflight_r691 import", rebound)
        self.assertIn('ROUND = "R691"', rebound)
        self.assertIn('OLD_ROUND = "R690"', rebound)
        self.assertIn('previous = "R690"', rebound)
        self.assertIn(generator.PIPE, rebound)
        self.assertIn("DEV14", rebound)
        self.assertNotIn("state-r690", rebound)
        self.assertEqual(rebound.count('"set-speed-3"'), 1)
        self.assertEqual(rebound.count('"resume-map"'), 1)

    def test_rendered_preflight_compiles_and_binds_r691(self) -> None:
        source = generator.render_preflight()
        compile(source, "preflight_r691.py", "exec")
        folded = source.casefold()
        self.assertNotIn(generator.FORBIDDEN_WINDOWS_SHELL, folded)
        self.assertNotIn(generator.FORBIDDEN_WINDOWS_SHELL_SHORT, folded)
        self.assertIn('STATE = ART / "state-r691"', source)
        self.assertIn('value.get("new_round") == "R691"', source)
        self.assertIn('value.get("old_round") == "R690"', source)
        self.assertIn(repr(generator.PIPE), source)

    def test_outer_runner_has_explicit_execution_gate(self) -> None:
        source = (HERE / "run_domain_construction_one_day_candidate.py").read_text(
            encoding="utf-8-sig"
        )
        compile(source, "run_domain_construction_one_day_candidate.py", "exec")
        folded = source.casefold()
        self.assertNotIn(generator.FORBIDDEN_WINDOWS_SHELL, folded)
        self.assertNotIn(generator.FORBIDDEN_WINDOWS_SHELL_SHORT, folded)
        self.assertIn('parser.add_argument("--execute", action="store_true")', source)
        self.assertIn("if not args.execute:", source)
        self.assertIn('"status": "GREEN_NO_LAUNCH"', source)


if __name__ == "__main__":
    unittest.main()
