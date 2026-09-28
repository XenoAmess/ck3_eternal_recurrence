"""Fail-closed checks for the H2743 read-only runner's external gates."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SCRIPT = (Path(__file__).resolve().parents[2] / "native_bridge" / "research"
          / "run_h2743_dejure_readonly_v3.py")
spec = importlib.util.spec_from_file_location("run_h2743_dejure_readonly_v3", SCRIPT)
assert spec is not None and spec.loader is not None
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def clean_receipt() -> dict[str, object]:
    return {
        "returncode": 0,
        "ck3_pids_after": [],
        "stdout_reader_alive_after": False,
        "source_sha256_after": runner.SOURCE_HASHES.copy(),
        "candidate_dll_sha256_after": runner.DLL_SHA,
        "injector_sha256_after": runner.INJECTOR_SHA,
        "exe_sha256_after": runner.EXE_SHA,
        "binary_audit_live_sha256": "A" * 64,
        "prepared_save_sha256_after": runner.SOURCE_HASHES["xar_checkpoint.ck3"],
        "prepared_sidecar_sha256_after": runner.SOURCE_HASHES["first-heir-marriage-formal-v1.json"],
    }


class H2743RunnerGateTests(unittest.TestCase):
    def test_final_result_requires_clean_managed_exit_and_unchanged_inputs(self) -> None:
        runner.require_clean_session_exit(clean_receipt())
        failures = (
            ("returncode", 1),
            ("ck3_pids_after", [1234]),
            ("stdout_reader_alive_after", True),
            ("candidate_dll_sha256_after", "0" * 64),
            ("exe_sha256_after", "0" * 64),
            ("binary_audit_live_sha256", None),
            ("prepared_save_sha256_after", "0" * 64),
            ("prepared_sidecar_sha256_after", "0" * 64),
        )
        for field, bad_value in failures:
            with self.subTest(field=field):
                receipt = clean_receipt()
                receipt[field] = bad_value
                with self.assertRaises(RuntimeError):
                    runner.require_clean_session_exit(receipt)
        receipt = clean_receipt()
        receipt["source_sha256_after"]["driver-state.json"] = "0" * 64
        with self.assertRaises(RuntimeError):
            runner.require_clean_session_exit(receipt)

    def test_renewed_lease_rechecks_owner_after_heartbeat(self) -> None:
        heartbeat = SimpleNamespace(stdout=(
            b'{"ok":true,"task":{"task_id":"h2743-review","state":"running",'
            b'"resources":["ck3-screen:acquired"]}}'
        ))
        with (patch.object(runner, "screen_lease") as check,
              patch.object(runner.subprocess, "run", return_value=heartbeat) as call):
            runner.renew_screen_lease("h2743-review")
        self.assertEqual(check.call_count, 2)
        self.assertEqual(call.call_args.args[0][-3:], ["heartbeat", "--task", "h2743-review"])

    def test_rejected_heartbeat_cannot_validate_exclusive_screen(self) -> None:
        heartbeat = SimpleNamespace(stdout=(
            b'{"ok":true,"task":{"task_id":"h2743-review","state":"done",'
            b'"resources":[]}}'
        ))
        with (patch.object(runner, "screen_lease") as check,
              patch.object(runner.subprocess, "run", return_value=heartbeat)):
            with self.assertRaises(RuntimeError):
                runner.renew_screen_lease("h2743-review")
        self.assertEqual(check.call_count, 1)

    def test_screen_lease_routes_through_legacy_non_utf8_summary(self) -> None:
        listed = SimpleNamespace(stdout=(
            b'{"ok":true,"tasks":[{"task_id":"h2743-review","state":"running",'
            b'"stale":false,"resources":["ck3-screen:acquired"],'
            b'"summary":"legacy-\xff"}]}'
        ))
        with patch.object(runner.subprocess, "run", return_value=listed):
            runner.screen_lease("h2743-review")

    def test_war_options_rejects_any_of_six_frame_drifts_or_wrong_war(self) -> None:
        snapshot = {"snapshot_id": "native:3", "revision": 4, "native_revision": 3,
                    "date_raw": 53217264, "episode_run_id": runner.EPISODE,
                    "diagnostics": {"connection_generation": 1, "bridge_pid": 1234}}
        frame = runner.frame_signature(snapshot)
        runner.require_snapshot_bridge_pid(snapshot, 1234)
        with self.assertRaises(RuntimeError):
            runner.require_snapshot_bridge_pid(snapshot, 4321)
        missing_pid = copy.deepcopy(snapshot)
        missing_pid["diagnostics"].pop("bridge_pid")
        with self.assertRaises(RuntimeError):
            runner.require_snapshot_bridge_pid(missing_pid, 1234)
        war = {"war_id": 16777231, "player_side": "defender",
               "player_is_primary_war_leader": True,
               "primary_opponent_character_id": 30097,
               "player_relative_war_score": -12, "targeted_title_ids": [2128]}
        other_war = {"war_id": 16777230, "player_side": "attacker",
                     "player_is_primary_war_leader": False,
                     "primary_opponent_character_id": 31000,
                     "player_relative_war_score": 5, "targeted_title_ids": [2200]}
        snapshot["active_wars"] = [war, other_war]
        expected_wars = runner.full_war_signature(snapshot)
        self.assertEqual([row["war_id"] for row in expected_wars], [16777230, 16777231])
        result = {"step": runner.OPTIONS_QUERY, "accepted": True,
                  "status": "available", "query_sequence": 2,
                  "queried_snapshot_id": "native:3", "queried_revision": 4,
                  "queried_native_revision": 3,
                  "queried_episode_run_id": runner.EPISODE,
                  "queried_connection_generation": 1,
                  "termination_query_context": {
                      "queried_date_raw": 53217264,
                      "queried_connection_generation": 1,
                      "queried_episode_run_id": runner.EPISODE,
                      "queried_character_id": 29829,
                      "active_war_signature": copy.deepcopy(expected_wars)},
                  "war_termination_options": {
                      "war_id": 16777231, "player_side": "defender",
                      "player_is_primary_war_leader": True,
                      "active_casus_belli_identity": {
                          "database_index": 17,
                          "canonical_key": "individual_county_de_jure_cb"},
                      "options": {"surrender": {
                          "outcome": "attacker_victory",
                          "native_validator_passed": True, "available": True,
                          "recipient_response": {"would_accept_now": True}},
                          "white_peace": {}, "victory": {}}}}
        runner.require_options_query(result, frame, war, expected_wars)
        mutations = (
            ("queried_snapshot_id", "native:4"),
            ("queried_revision", 5),
            ("queried_native_revision", 4),
            ("queried_episode_run_id", "other-episode"),
            ("queried_connection_generation", 2),
            ("termination_query_context.queried_date_raw", 53217265),
            ("war_termination_options.war_id", 123),
            ("termination_query_context.active_war_signature", []),
            ("query_sequence", 0),
            ("war_termination_options.options.surrender.available", False),
            ("war_termination_options.options.surrender.recipient_response.would_accept_now", False),
        )
        for dotted, bad in mutations:
            with self.subTest(field=dotted):
                changed = copy.deepcopy(result)
                current = changed
                parts = dotted.split(".")
                for part in parts[:-1]:
                    current = current[part]
                current[parts[-1]] = bad
                with self.assertRaises(RuntimeError):
                    runner.require_options_query(changed, frame, war, expected_wars)

        for changed_wars in ([copy.deepcopy(war)],
                             [copy.deepcopy(other_war), copy.deepcopy(war), copy.deepcopy(war)],
                             [{**other_war, "player_relative_war_score": 6}, copy.deepcopy(war)]):
            with self.subTest(active_wars=changed_wars):
                changed = copy.deepcopy(result)
                changed["termination_query_context"]["active_war_signature"] = changed_wars
                with self.assertRaises(RuntimeError):
                    runner.require_options_query(changed, frame, war, expected_wars)

        duplicate_before = copy.deepcopy(snapshot)
        duplicate_before["active_wars"].append(copy.deepcopy(war))
        with self.assertRaises(RuntimeError):
            runner.full_war_signature(duplicate_before)

        for field in (*runner.FRAME_FIELDS, "connection_generation"):
            with self.subTest(snapshot_field=field):
                changed = copy.deepcopy(snapshot)
                target = changed["diagnostics"] if field == "connection_generation" else changed
                target[field] = "other" if isinstance(target[field], str) else target[field] + 1
                if field == "episode_run_id":
                    with self.assertRaises(RuntimeError):
                        runner.frame_signature(changed)
                else:
                    self.assertNotEqual(runner.frame_signature(changed), frame)

        for diagnostics in (None, {}, {"connection_generation": None},
                            {"connection_generation": True}):
            with self.subTest(diagnostics=diagnostics):
                missing = dict(snapshot)
                missing["diagnostics"] = diagnostics
                missing["connection_generation"] = 1  # Top-level value is not authoritative.
                with self.assertRaises(RuntimeError):
                    runner.frame_signature(missing)

    def test_new_candidate_requires_target_holder_prestate_without_delta_claim(self) -> None:
        baseline = {"target_title_ids": [2128], "target_title_holder_prestate": [
            {"title_id": 2128, "holder_character_id": 33435,
             "holder_immediate_liege_character_id": 29829}]}
        runner.require_target_holder_prestate(baseline)
        for bad_rows in (
            None, [],
            [{"title_id": 2128, "holder_character_id": 33435,
              "holder_immediate_liege_character_id": 29829}] * 2,
            [{"title_id": 2129, "holder_character_id": 33435,
              "holder_immediate_liege_character_id": 29829}],
            [{"title_id": 2128, "holder_character_id": True,
              "holder_immediate_liege_character_id": 29829}],
            [{"title_id": 2128, "holder_character_id": 33435,
              "holder_immediate_liege_character_id": 33435}],
        ):
            with self.subTest(rows=bad_rows):
                changed = copy.deepcopy(baseline)
                changed["target_title_holder_prestate"] = bad_rows
                with self.assertRaises(RuntimeError):
                    runner.require_target_holder_prestate(changed)
        no_liege = copy.deepcopy(baseline)
        no_liege["target_title_holder_prestate"][0]["holder_immediate_liege_character_id"] = None
        runner.require_target_holder_prestate(no_liege)

    def test_loaded_binary_audit_rejects_wrong_process_module(self) -> None:
        process = SimpleNamespace(exe=lambda: str(runner.EXE),
                                  memory_maps=lambda grouped=False: [
                                      SimpleNamespace(path=str(runner.DLL))],
                                  create_time=lambda: 123.0)
        def hashed(path: Path) -> str:
            if path.resolve() == runner.EXE.resolve():
                return runner.EXE_SHA
            if path.resolve() == runner.DLL.resolve():
                return runner.DLL_SHA
            return "B" * 64
        with (patch("psutil.Process", return_value=process),
              patch.object(runner, "sha256", side_effect=hashed)):
            audit = runner.audit_loaded_binaries(1234, Path("D:/synthetic-state"))
            self.assertTrue(audit["loaded_module_path_and_disk_sha_verified"])
            self.assertIsNone(audit["loaded_in_memory_image_sha256"])
            process.memory_maps = lambda grouped=False: [
                SimpleNamespace(path="D:/wrong/xar_ck3_bridge.dll")]
            with self.assertRaises(RuntimeError):
                runner.audit_loaded_binaries(1234, Path("D:/synthetic-state"))
            process.memory_maps = lambda grouped=False: [SimpleNamespace(path=str(runner.DLL))]
            process.exe = lambda: "D:/wrong/ck3.exe"
            with self.assertRaises(RuntimeError):
                runner.audit_loaded_binaries(1234, Path("D:/synthetic-state"))


if __name__ == "__main__":
    unittest.main()
