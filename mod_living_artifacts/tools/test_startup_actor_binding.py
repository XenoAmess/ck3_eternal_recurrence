"""Authored boundary regressions; no authored row is native qualification."""
from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest

from acceptance_contract import Frame, Object, field, json_value, mapping, pin, write_once
from startup_actor_binding import StartupActorBinding


def startup_fixture(root: Path, actor: int = 912345) -> tuple[Object, Object, Object]:
    preparation = write_once(root / "preparation.json", {"authored_test_data": True})
    policy: Object = {"schema": "ck3-frontend-fixture-start-policy-v1", "schema_version": 1,
        "preparation": {"path": preparation["path"], "sha256": preparation["sha256"]},
        "post_start": {"government_key": "feudal_government", "primary_title_tier_key": "duchy", "independent": True},
        "required_log_markers": ["XALW_FIXTURE_READY_V1"], "forbidden_log_markers": ["XALW_FIXTURE_INIT_ERROR_V1"]}
    source = write_once(root / "policy.json", policy)
    (root / "policy.snapshot.json").write_bytes(Path(source["path"]).read_bytes())
    frozen: Object = {"run_id": "unit-run", "argv": ["host", "--frontend-fixture-start-policy", source["path"]]}
    manifest: Object = {"machine_id": "unit-machine", "game": {"version": "unit-version", "exe_sha256": "a" * 64}}
    binding: Object = {"actor_character_id": actor, "primary_title_id": 7, "government_key": "feudal_government",
        "primary_title_tier_key": "duchy", "date_raw": 123456, "bridge_pid": 124, "connection_generation": 9,
        "pump_epoch": 13, "fixture_target_identity_proven": False}
    observations: list[Object] = []
    for epoch in (12, 13):
        frame: Object = {"paused": True, "map_ready": True, "source": "injected-dll-named-pipe", "backend_id": "native-headless",
            "episode_projection": "native_campaign", "snapshot_id": "native:2", "revision": 3, "native_revision": 2, "date_raw": 123456,
            "played_character": {"character_id": actor, "alive": True, "source": "native"},
            "managed_campaign_run_binding": {"run_id": "unit-run", "bridge_pipe": "unit-pipe"},
            "diagnostics": {"bridge_pid": 124, "connection_generation": 9, "pipe_name": "unit-pipe", "hello": {
                "pid": 124, "connection_generation": 9, "ck3_build_match": True,
                "expected_ck3_version": "unit-version", "expected_ck3_sha256": "a" * 64}}}
        row_binding = dict(binding)
        row_binding["pump_epoch"] = epoch
        observations.append({"snapshot": frame, "binding": row_binding, "campaign_root": {
            "campaign_root_context_ready": True, "backend_id": "native-headless", "player_character_id": actor,
            "player_character_alive": True, "government": {"key": "feudal_government"}, "independent": True,
            "immediate_liege_character_id": None, "top_liege_character_id": actor, "primary_title": {"title_id": 7, "tier_key": "duchy"},
            "queried_snapshot_id": "native:2", "queried_revision": 3, "queried_native_revision": 2, "date_raw": 123456,
            "provenance": {"game_version": "unit-version", "executable_sha256": "a" * 64}},
            "qualification": {"schema": "xar.ck3.engine-log-literals/v1", "exists": True, "read_only": True,
                "case_sensitive": True, "log_name": "debug.log", "matches": [
                    {"literal": "XALW_FIXTURE_READY_V1", "line_count": 1}, {"literal": "XALW_FIXTURE_INIT_ERROR_V1", "line_count": 0}]}})
    report: Object = {"frontend_fixture_start_policy_input": {"source_path": source["path"], "snapshot_path": str(root / "policy.snapshot.json"),
        "sha256": source["sha256"], "policy": policy},
        "frontend_fixture_start_submission": {"status": "SINGLE_START_ACKNOWLEDGED_POST_STATE_PENDING", "acknowledged": True,
            "retry_allowed": False, "result": {"schema": "ck3-frontend-fixture-robert-start-submission-v1", "schema_version": 1,
                "accepted": True, "pre_start_identity_proven": True, "fixture_target_identity_proven": False,
                "binding": {"bridge_pid": 124, "connection_generation": 9},
                "policy_binding": {"policy_sha256": source["sha256"], "preparation_sha256": preparation["sha256"]},
                "selected_candidate": {"schema": "ck3-frontend-selected-1066-feudal-candidate-v1", "schema_version": 1,
                    "accepted": True, "status": "ready", "route": "bookmarks", "selected_bookmark_group_key": "bm_group_1066",
                    "selected_bookmark_key": "bm_1066_rags_to_riches", "selected_character_name_key": "bookmark_rags_to_riches_duke_robert",
                    "selected_character_government_key": "feudal_government", "backend_id": "native-headless", "read_only": True,
                    "selected_bookmark_start_date_raw": 123456}}},
        "frontend_fixture_business_context": {"status": "ACTUAL_FIXTURE_QUALIFIED_BUSINESS_CONTEXT_BOUND", "actual_current_actor_bound": True,
            "qualification_observed": True, "fixture_target_identity_proven": False, "product_acceptance_proven": False,
            "start_resubmitted": False, "binding": binding, "observations": json_value(observations)}}
    return report, frozen, manifest


def parse(report: object, frozen: object, manifest: object) -> StartupActorBinding:
    return StartupActorBinding.parse(report, frozen=frozen, run_id="unit-run", machine_id="unit-machine", manifest=manifest)


class StartupActorBindingTests(unittest.TestCase):
    def test_runtime_actor_is_observed_and_roundtrips_without_historic_id(self) -> None:
        for actor in (912345, 812346):
            with self.subTest(actor=actor), tempfile.TemporaryDirectory() as directory:
                report, frozen, manifest = startup_fixture(Path(directory), actor)
                binding = parse(report, frozen, manifest)
                self.assertEqual(binding.player_id, actor)
                self.assertEqual(field(json_value(binding.to_json()), "runtime_actor_character_id"), actor)
                binding.validate_frame(Frame(7, 6, 123480, actor, 124, "9"))
                with self.assertRaisesRegex(ValueError, "differs"):
                    binding.validate_frame(Frame(7, 6, 123480, actor + 1, 124, "9"))

    def test_bare_native_actor_and_historic_id_are_insufficient(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report, frozen, manifest = startup_fixture(Path(directory))
            del report["frontend_fixture_start_submission"]
            with self.assertRaisesRegex(ValueError, "Missing"):
                parse(report, frozen, manifest)

    def test_selected_candidate_root_process_and_strict_types_are_guarded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original, frozen, manifest = startup_fixture(Path(directory))
            paths: tuple[tuple[tuple[str, ...], object], ...] = (
                (("frontend_fixture_start_submission", "result", "selected_candidate", "selected_character_name_key"), "another_bookmark"),
                (("frontend_fixture_business_context", "binding", "actor_character_id"), 912345.0),
                (("frontend_fixture_business_context", "binding", "bridge_pid"), True),
                (("frontend_fixture_business_context", "qualification_observed"), False),
                (("frontend_fixture_start_submission", "result", "binding", "connection_generation"), 2),
            )
            for keys, value in paths:
                report = copy.deepcopy(original)
                current: object = report
                for key in keys[:-1]:
                    current = field(current, key)
                target = mapping(current, "unit mutation")
                target[keys[-1]] = value
                # mapping deliberately copies at boundaries, so reconnect only
                # the authored test branch instead of mutating a parsed object.
                parent: object = report
                for key in keys[:-2]:
                    parent = field(parent, key)
                if not isinstance(parent, dict):
                    raise AssertionError("Authored object branch changed")
                parent[keys[-2]] = target
                with self.subTest(keys=keys), self.assertRaises(ValueError):
                    parse(report, frozen, manifest)

    def test_pinned_policy_or_preparation_changed_bytes_are_rejected(self) -> None:
        for name in ("policy.json", "policy.snapshot.json", "preparation.json"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                report, frozen, manifest = startup_fixture(Path(directory))
                path = Path(directory) / name
                old = pin(path)
                path.write_bytes(path.read_bytes() + b"\n")
                self.assertNotEqual(old["sha256"], pin(path)["sha256"])
                with self.assertRaisesRegex(ValueError, "bytes changed"):
                    parse(report, frozen, manifest)


if __name__ == "__main__":
    unittest.main()
