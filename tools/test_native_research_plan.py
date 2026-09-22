"""Offline acceptance for new research records; fixtures make no CK3 claims."""

from __future__ import annotations

from copy import deepcopy
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import native_research_plan as research


def sample_plan() -> dict:
    plan = research.template("synthetic-fixture", "synthetic-build")
    plan.update(question="When does this synthetic producer create a candidate?", purpose="npc-choice")
    plan["build"]["exe_sha256"] = "a" * 64
    plan["observation"].update(
        mode="paused-snapshot", actor_kind="ai", owner_scope="Synthetic AI owner",
        identity_kind="generation-id", identity_lifetime="Bound only within the recorded session",
        producer_trigger="paused-query", producer="Synthetic cached row producer",
        caller="Synthetic paused query", consumer="Synthetic candidate reader",
        cache_lifetime="Until synthetic owner invalidation", expected_signal="One matching row",
        zero_sample_meaning="No row observed in this slice; not proof of an empty world",
        stop_condition="One read only",
    )
    return plan


class ResearchPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.plan = sample_plan()

    def add_evidence(self, layer: str) -> None:
        path = self.base / "evidence.txt"
        path.write_text("synthetic evidence bytes only", encoding="utf-8")
        self.plan["evidence"] = [{
            "id": "proof", "path": path.name, "sha256": research.fingerprint(path)["sha256"],
            "exe_sha256": self.plan["build"]["exe_sha256"], "layer": layer,
            "supports": "Synthetic reader test; no claim about CK3", "session": "fixture-session",
            "frame": "fixture-frame", "identity": "fixture-object",
        }]
        self.plan["edges"][0]["evidence"] = ["proof"]

    def test_new_draft_cannot_be_mistaken_for_completed_plan(self) -> None:
        with self.assertRaisesRegex(ValueError, "question"):
            research.check(research.template("new-topic", "test-build"), self.base)

    def test_paused_wait_does_not_observe_daily_or_action_producer(self) -> None:
        for trigger in ("daily-tick", "on-action", "unknown"):
            with self.subTest(trigger=trigger):
                self.plan["observation"]["producer_trigger"] = trigger
                self.assertTrue(research.check(self.plan, self.base)["observation_plan_issues"])
                with self.assertRaises(ValueError):
                    research.check(self.plan, self.base, for_observation=True)

    def test_npc_question_rejects_human_but_player_legality_can_use_human(self) -> None:
        self.plan["observation"]["actor_kind"] = "human"
        with self.assertRaisesRegex(ValueError, "NPC choice"):
            research.check(self.plan, self.base, for_observation=True)
        self.plan["purpose"] = "player-legality"
        self.assertEqual(research.check(self.plan, self.base, for_observation=True)["result"], "plan-consistent")

    def test_passive_window_is_explicit_and_no_runtime_is_performed(self) -> None:
        self.plan["observation"].update(mode="passive-runtime", producer_trigger="daily-tick")
        with self.assertRaisesRegex(ValueError, "separately authorized"):
            research.check(self.plan, self.base, for_observation=True)
        self.plan["observation"]["runtime_window_ref"] = "existing-approved-run-contract.md#window"
        result = research.check(self.plan, self.base, for_observation=True)
        self.assertFalse(result["live_execution_performed"])
        self.assertFalse(result["semantic_correctness_verified"])

    def test_unknown_graph_is_dashed_and_own_policy_excluded_from_native_count(self) -> None:
        own = deepcopy(self.plan["edges"][0])
        own.update(id="policy", status="counter-policy")
        self.plan["edges"].append(own)
        self.plan["nodes"][0]["label"] = 'Quoted "node" | ` text'
        result = research.check(self.plan, self.base)
        rendered = research.render(self.plan, result)
        self.assertEqual(result["enumerated_native_edges"], 1)
        self.assertIn('-. "decision [unknown]', rendered)
        self.assertIn("&quot;node&quot;", rendered)
        self.assertIn("&#124;", rendered)
        self.assertEqual(rendered, research.render(self.plan, result))

    def test_bytes_or_offline_tests_cannot_establish_semantics_or_live(self) -> None:
        for layer, status in (("locator", "static-confirmed"), ("exact-build", "static-confirmed"),
                              ("offline-fixture", "live-confirmed")):
            with self.subTest(layer=layer, status=status):
                self.add_evidence(layer)
                self.plan["edges"][0]["status"] = status
                with self.assertRaises(ValueError):
                    research.check(self.plan, self.base)
        self.add_evidence("source-contract")
        self.plan["edges"][0]["status"] = "static-confirmed"
        self.assertFalse(research.check(self.plan, self.base)["semantic_correctness_verified"])

    def test_live_declaration_needs_identity_and_cases_do_not_follow_edge_counts(self) -> None:
        self.add_evidence("live-observation")
        self.plan["edges"][0]["status"] = "live-confirmed"
        self.plan["cases"] = [{"id": "boundary", "question": "Other side of threshold?", "status": "pending", "evidence": []}]
        result = research.check(self.plan, self.base)
        self.assertEqual(result["declared_cases_by_status"]["observed"], 0)
        self.plan["evidence"][0].pop("identity")
        with self.assertRaisesRegex(ValueError, "identity"):
            research.check(self.plan, self.base)

    def test_evidence_hash_and_version_drift_reject(self) -> None:
        self.add_evidence("source-contract")
        self.plan["evidence"][0]["exe_sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "build hash"):
            research.check(self.plan, self.base)
        self.plan["evidence"][0]["exe_sha256"] = self.plan["build"]["exe_sha256"]
        (self.base / "evidence.txt").write_text("changed bytes", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "file hash mismatch"):
            research.check(self.plan, self.base)

    def test_dangling_duplicate_and_missing_unknown_question_reject(self) -> None:
        variants = []
        p = deepcopy(self.plan)
        p["edges"][0]["to"] = "absent"
        variants.append(p)
        p = deepcopy(self.plan)
        p["nodes"].append(p["nodes"][0])
        variants.append(p)
        p = deepcopy(self.plan)
        p["edges"][0]["evidence"] = ["absent"]
        variants.append(p)
        p = deepcopy(self.plan)
        p["edges"][0]["open_question"] = ""
        variants.append(p)
        for plan in variants:
            with self.subTest(plan=plan), self.assertRaises(ValueError):
                research.check(plan, self.base)

    def test_cli_rejects_bad_plan_under_normal_and_optimized_python(self) -> None:
        path = self.base / "plan.json"
        self.plan["observation"]["producer_trigger"] = "daily-tick"
        path.write_text(json.dumps(self.plan), encoding="utf-8")
        for flags in ([], ["-O"]):
            result = subprocess.run([sys.executable, *flags, str(Path(research.__file__)), "check", str(path), "--for-observation"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("paused capture", result.stderr)

    def test_cli_renders_from_relative_evidence_and_will_not_replace_artifact(self) -> None:
        self.add_evidence("source-contract")
        self.plan["edges"][0]["status"] = "static-confirmed"
        path, output = self.base / "plan.json", self.base / "graph.md"
        path.write_text(json.dumps(self.plan), encoding="utf-8")
        command = [sys.executable, str(Path(research.__file__)), "render", str(path), "--output", str(output)]
        result = subprocess.run(command, capture_output=True, text=True, cwd=Path(research.__file__).parent)
        self.assertEqual(result.returncode, 0, result.stderr)
        original = output.read_bytes()
        self.assertIn(research.fingerprint(path)["sha256"].encode(), original)
        self.assertIn(b"| proof | source-contract | evidence.txt |", original)
        self.assertIn(b"| producer_trigger | paused-query |", original)
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(output.read_bytes(), original)

    def test_duplicate_json_keys_rejected(self) -> None:
        path = self.base / "duplicate.json"
        path.write_text('{"schema": "a", "schema": "b"}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            research.load_plan(path)

    def test_confirmed_edge_accepts_null_question_but_rejects_other_types(self) -> None:
        self.add_evidence("source-contract")
        self.plan["edges"][0].update(status="static-confirmed", open_question=None)
        result = research.check(self.plan, self.base)
        self.assertIn("| decision | static-confirmed | proof |  |", research.render(self.plan, result))
        self.plan["edges"][0]["open_question"] = []
        with self.assertRaisesRegex(ValueError, "open_question"):
            research.check(self.plan, self.base)

    def test_plan_hash_binds_the_bytes_parsed_even_if_editor_saves_during_check(self) -> None:
        path = self.base / "plan.json"
        initial = json.dumps(self.plan).encode("utf-8")
        changed_plan = deepcopy(self.plan)
        changed_plan["question"] = "A later revision of the question"
        changed = json.dumps(changed_plan).encode("utf-8")
        path.write_bytes(initial)
        original_read = Path.read_bytes

        def read_and_edit(read_path: Path) -> bytes:
            raw = original_read(read_path)
            if read_path == path:
                path.write_bytes(changed)
            return raw

        output = io.StringIO()
        with mock.patch.object(Path, "read_bytes", read_and_edit), contextlib.redirect_stdout(output):
            self.assertEqual(research.main(["check", str(path)]), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["plan_sha256"], hashlib.sha256(initial).hexdigest())
        self.assertEqual(path.read_bytes(), changed)


if __name__ == "__main__":
    unittest.main()
