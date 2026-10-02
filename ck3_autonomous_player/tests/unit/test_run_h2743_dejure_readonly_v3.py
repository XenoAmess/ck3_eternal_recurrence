"""Fail-closed checks for the H2743 read-only runner's external gates."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
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
    def test_cli_modes_reject_live_conflict_before_any_side_effect(self) -> None:
        for conflicting_mode in ("--check-static", "--prepare-no-launch"):
            with self.subTest(conflicting_mode=conflicting_mode):
                argv = ["runner", "--candidate", runner.EXISTING_TRUCE_CANDIDATE,
                        conflicting_mode, "--run", "--prepared-attempt", "D:/synthetic-attempt",
                        "--steam-gate", "D:/synthetic-steam-gate", "--task-id", "synthetic"]
                with (patch.object(sys, "argv", argv),
                      patch.object(runner, "select_candidate") as select,
                      patch.object(runner, "check_static") as static,
                      patch.object(runner, "prepare_no_launch") as prepare,
                      patch.object(runner, "live_gate") as steam,
                      patch.object(runner, "run") as live,
                      patch.object(runner.subprocess, "Popen") as launch):
                    with self.assertRaises(SystemExit) as error:
                        runner.main()
                self.assertEqual(error.exception.code, 2)
                for guard in (select, static, prepare, steam, live, launch):
                    guard.assert_not_called()

    def test_existing_truce_candidate_uses_new_pair_and_only_readonly_step(self) -> None:
        try:
            runner.select_candidate(runner.EXISTING_TRUCE_CANDIDATE)
            self.assertEqual(runner.ROOT, runner.EXISTING_TRUCE_ROOT)
            self.assertEqual(runner.DLL, runner.EXISTING_TRUCE_BUILD / "xar_ck3_bridge.dll")
            self.assertEqual(runner.DLL_SHA, runner.EXISTING_TRUCE_DLL_SHA)
            self.assertEqual(runner.INJECTOR_SHA, runner.EXISTING_TRUCE_INJECTOR_SHA)
            self.assertEqual(runner.QUERY, "query-h2743-preaction-existing-truce-v1")
            self.assertEqual(runner.LIVE_OUTPUT, "live-preaction-existing-truce-v1")
        finally:
            runner.select_candidate(runner.DEFAULT_CANDIDATE)
        self.assertEqual(runner.ROOT, runner.BASE_ROOT)
        self.assertEqual(runner.QUERY, runner.BASE_QUERY)

    def test_storage_candidate_requires_new_pin_and_keeps_stock_condition_unknown(self) -> None:
        try:
            runner.select_candidate(runner.STORAGE_CANDIDATE)
            self.assertEqual(runner.DLL, runner.STORAGE_DLL)
            self.assertEqual(runner.DLL_SHA, runner.STORAGE_DLL_SHA)
            self.assertEqual(runner.LIVE_OUTPUT, "live-dejure-war-storage-v5")
        finally:
            runner.select_candidate(runner.DEFAULT_CANDIDATE)
        baseline = {
            "border_raid_storage_candidate_v1": {
                "schema": "xar.ck3.h2743-border-raid-storage-candidate.v1",
                "status": "structural_candidate_only", "candidate": False,
                "storage_capacity": 17, "active_war_count": 2,
                "matching_war_count": 0, "unavailable_reason": None,
                "native_condition_observed": False,
            },
            "truce_inputs_v1": {"border_raid_pair": {
                "status": "unavailable", "value": None,
                "unavailable_reason": "stock_condition_reader_unavailable"}},
        }
        runner.require_storage_candidate(baseline)
        for path, value in (
            (("border_raid_storage_candidate_v1", "native_condition_observed"), True),
            (("border_raid_storage_candidate_v1", "status"), "observed"),
            (("border_raid_storage_candidate_v1", "matching_war_count"), 1),
            (("truce_inputs_v1", "border_raid_pair", "status"), "observed"),
        ):
            with self.subTest(path=path):
                changed = copy.deepcopy(baseline)
                node = changed
                for segment in path[:-1]:
                    node = node[segment]
                node[path[-1]] = value
                with self.assertRaises(RuntimeError):
                    runner.require_storage_candidate(changed)

    def test_partial_truce_candidate_is_exact_and_cannot_reuse_old_ready(self) -> None:
        try:
            runner.select_candidate(runner.TRUCE_CANDIDATE)
            self.assertEqual(runner.DLL, runner.TRUCE_DLL)
            self.assertEqual(runner.DLL_SHA, runner.TRUCE_DLL_SHA)
            self.assertEqual(runner.LIVE_OUTPUT, "live-dejure-partial-truce-v4")
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                attempt = root / "attempt-12-dejure-baseline-no-launch"
                attempt.mkdir()
                legacy_ready = {
                    "status": "no_launch_preflight_ready",
                    "source_hashes": runner.SOURCE_HASHES,
                    "candidate_dll_sha256": runner.TRUCE_DLL_SHA,
                    "injector_sha256": runner.INJECTOR_SHA,
                    "ck3_launch_attempted": False,
                    "gameplay_action_submitted": False,
                    "prepare": {"exit_code": 0},
                    "rebind": {"exit_code": 0},
                    "preflight": {"exit_code": 0},
                }
                (attempt / "ready-summary.json").write_text(json.dumps(legacy_ready), encoding="utf-8")
                with patch.object(runner, "ROOT", root):
                    with self.assertRaisesRegex(RuntimeError, "no-launch preflight READY absent"):
                        runner.prepared_state(attempt)
                    legacy_ready["candidate_kind"] = runner.TRUCE_CANDIDATE
                    (attempt / "ready-summary.json").write_text(json.dumps(legacy_ready), encoding="utf-8")
                    old_pair = {
                        "candidate_kind": runner.DEFAULT_CANDIDATE,
                        "candidate_dll": str(runner.DLL),
                        "candidate_dll_sha256": runner.TRUCE_DLL_SHA,
                        "source_hashes": runner.SOURCE_HASHES,
                        "ck3_launch_attempted": False,
                        "gameplay_action_submitted": False,
                    }
                    (attempt / "source-pair.json").write_text(json.dumps(old_pair), encoding="utf-8")
                    with self.assertRaisesRegex(RuntimeError, "belongs to another candidate"):
                        runner.prepared_state(attempt)
            with self.assertRaises(ValueError):
                runner.select_candidate("unreviewed-dll")
        finally:
            runner.select_candidate(runner.DEFAULT_CANDIDATE)

    def test_partial_truce_wire_never_becomes_surrender_terms(self) -> None:
        observed = lambda value: {"status": "observed", "value": value,
                                  "unavailable_reason": None}
        unavailable = lambda reason: {"status": "unavailable", "value": None,
                                      "unavailable_reason": reason}
        inputs = {
            "schema": "xar.ck3.defender-de-jure-truce-inputs.v1",
            "attacker_flexible_truces_perk": observed(False),
            "attacker_government_is_nomadic": observed(True),
            "defender_government_is_nomadic": observed(False),
            "nomad_both": observed(False),
            "short": unavailable("stock_condition_reader_unavailable"),
            "long": unavailable("stock_condition_reader_unavailable"),
            "border_raid_pair": unavailable("stock_condition_reader_unavailable"),
            "evaluated_days": None,
            "persisted_expiry_date_raw": None,
        }
        baseline = {"truce_inputs_v1": inputs, "material_complete": False,
                    "directed_truce": None, "action_literal": None}
        runner.require_partial_truce_inputs(baseline)
        for mutation in (
            lambda row: row.pop("truce_inputs_v1"),
            lambda row: row["truce_inputs_v1"].update(evaluated_days=730),
            lambda row: row["truce_inputs_v1"]["short"].update(
                status="observed", value=False, unavailable_reason=None),
            lambda row: row.update(directed_truce={"days": 730}),
            lambda row: row.update(action_literal="surrender-war-16777231"),
        ):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(baseline)
                mutation(changed)
                with self.assertRaises(RuntimeError):
                    runner.require_partial_truce_inputs(changed)

    def test_cold_map_wait_and_independent_lease_failure_gate(self) -> None:
        # R0004 first command took 23m37s; the old 300s frame gate was RED.
        self.assertGreaterEqual(runner.FRAME_SECONDS, 1800)
        self.assertLessEqual(runner.FRAME_SECONDS, runner.SESSION_SECONDS)
        # attempt-13 returned a successful transport frame while map loading.
        # This must remain a readiness poll, never the before-payload or a query.
        loading = {"date_raw": 53217264, "paused": True, "map_ready": False,
                   "local_player_id": 0, "played_character": None, "active_wars": []}
        self.assertTrue(runner.cold_map_snapshot_pending(loading))
        with patch.object(runner, "require_snapshot") as identity:
            self.assertIsNone(runner.admit_ready_snapshot(loading))
            identity.assert_not_called()
        with self.assertRaisesRegex(RuntimeError, "snapshot identity differs"):
            runner.require_snapshot(loading)
        ready = dict(loading, map_ready=True)
        # attempt-14 reached map_ready=true before episode, actor and wars bound.
        ready["local_player_id"] = 1
        self.assertTrue(runner.cold_map_snapshot_pending(ready))
        with patch.object(runner, "require_snapshot") as identity:
            self.assertIsNone(runner.admit_ready_snapshot(ready))
            identity.assert_not_called()
        for changed in (dict(ready, paused=False), dict(ready, date_raw=53217265)):
            with self.subTest(early_contradiction=changed):
                self.assertFalse(runner.cold_map_snapshot_pending(changed))
                with self.assertRaisesRegex(RuntimeError, "snapshot identity differs"):
                    runner.admit_ready_snapshot(changed)
        for changed in (dict(ready, paused=0), dict(ready, date_raw=53217264.0)):
            with self.subTest(malformed_clock=changed), self.assertRaisesRegex(
                    RuntimeError, "type is malformed"):
                runner.cold_map_snapshot_pending(changed)
        wrong_episode = dict(ready, episode_run_id="other-campaign")
        self.assertFalse(runner.cold_map_snapshot_pending(wrong_episode))
        with self.assertRaisesRegex(RuntimeError, "snapshot identity differs"):
            runner.admit_ready_snapshot(wrong_episode)
        wrong_actor = dict(ready, played_character={"character_id": 12345})
        self.assertFalse(runner.cold_map_snapshot_pending(wrong_actor))
        with self.assertRaisesRegex(RuntimeError, "snapshot identity differs"):
            runner.admit_ready_snapshot(wrong_actor)
        complete_war = {"war_id": 16777231, "player_side": "defender",
                        "player_is_primary_war_leader": True,
                        "primary_opponent_character_id": 30097,
                        "player_relative_war_score": -12,
                        "targeted_title_ids": [2128]}
        float_actor = dict(ready, episode_run_id=runner.EPISODE,
                           played_character={"character_id": 29829.0},
                           active_wars=[complete_war])
        with self.assertRaisesRegex(RuntimeError, "played-character ID type"):
            runner.admit_ready_snapshot(float_actor)
        with self.assertRaisesRegex(RuntimeError, "snapshot identity differs"):
            runner.require_snapshot(float_actor)
        partially_bound = dict(ready, episode_run_id=runner.EPISODE,
                               played_character={"character_id": 29829})
        self.assertTrue(runner.cold_map_snapshot_pending(partially_bound))
        for malformed in ("unknown", 29829):
            with self.subTest(played_character=malformed), self.assertRaisesRegex(
                    RuntimeError, "played-character shape"):
                runner.cold_map_snapshot_pending(dict(ready, played_character=malformed))
        for malformed in (None, {}, "none"):
            with self.subTest(active_wars=malformed), self.assertRaisesRegex(
                    RuntimeError, "active-war shape"):
                runner.cold_map_snapshot_pending(dict(ready, active_wars=malformed))
        for malformed in (None, 0, 1, "false"):
            with self.subTest(malformed=malformed), self.assertRaisesRegex(
                    RuntimeError, "map readiness field"):
                runner.cold_map_snapshot_pending(dict(loading, map_ready=malformed))
        runner.require_lease_watchdog_healthy([])
        with self.assertRaisesRegex(RuntimeError, "screen lease watchdog failed"):
            runner.require_lease_watchdog_healthy(["lease owner changed"])

    def test_after_frame_cannot_reuse_identity_with_map_not_ready(self) -> None:
        war = {"war_id": 16777231, "player_side": "defender",
               "player_is_primary_war_leader": True,
               "primary_opponent_character_id": 30097,
               "player_relative_war_score": -12, "targeted_title_ids": [2128]}
        snapshot = {"episode_run_id": runner.EPISODE, "date_raw": 53217264,
                    "played_character": {"character_id": 29829}, "paused": True,
                    "map_ready": True, "active_wars": [war], "snapshot_id": "native:3",
                    "revision": 4, "native_revision": 3,
                    "diagnostics": {"connection_generation": 1}}
        admitted = runner.admit_ready_snapshot(snapshot)
        self.assertIsNotNone(admitted)
        current_war, frame, wars = admitted
        runner.require_same_ready_frame(snapshot, current_war, frame, wars)
        for bad_ready in (False, None, 0, "true"):
            with self.subTest(map_ready=bad_ready):
                changed = dict(snapshot, map_ready=bad_ready)
                with self.assertRaises(RuntimeError):
                    runner.require_same_ready_frame(changed, current_war, frame, wars)
        transitional = dict(snapshot, episode_run_id=None, played_character=None,
                            active_wars=[])
        with self.assertRaisesRegex(RuntimeError, "baseline changed"):
            runner.require_same_ready_frame(transitional, current_war, frame, wars)
        missing_ready = dict(snapshot)
        missing_ready.pop("map_ready")
        with self.assertRaises(RuntimeError):
            runner.require_same_ready_frame(missing_ready, current_war, frame, wars)
        changed = dict(snapshot, active_wars=[dict(war, player_relative_war_score=-13)])
        with self.assertRaises(RuntimeError):
            runner.require_same_ready_frame(changed, current_war, frame, wars)

    def test_r0110_native_four_explicit_query_claim_and_drift_denial(self) -> None:
        war = {"war_id": 16777231, "player_side": "defender",
               "player_is_primary_war_leader": True,
               "primary_opponent_character_id": 30097,
               "player_relative_war_score": -12, "targeted_title_ids": [2128]}
        before = {"episode_run_id": runner.EPISODE, "date_raw": 53217264,
                  "played_character": {"character_id": 29829, "alive": True},
                  "paused": True, "map_ready": True, "active_wars": [war],
                  "snapshot_id": "native:4", "revision": 5, "native_revision": 4,
                  "diagnostics": {"connection_generation": 1}}
        frame = runner.frame_signature(before)
        arguments = runner.existing_truce_query_arguments(before, frame)
        self.assertEqual(arguments["step"], runner.QUERY)
        self.assertEqual(arguments["expected_revision"], 5)
        self.assertEqual(arguments["expected_h2743_frame"]["snapshot_id"], "native:4")
        independent_public = dict(before, revision=7)
        independent_frame = runner.frame_signature(independent_public)
        independent_arguments = runner.existing_truce_query_arguments(
            independent_public, independent_frame,
        )
        self.assertEqual(independent_arguments["expected_revision"], 7)
        self.assertEqual(independent_arguments["expected_h2743_frame"]["native_revision"], 4)
        for key, value in (("snapshot_id", "native:3"), ("revision", 6),
                           ("native_revision", 5), ("connection_generation", 2)):
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                runner.existing_truce_query_arguments(before, dict(frame, **{key: value}))

    def test_failed_read_can_prove_cleanup_without_publishing_success(self) -> None:
        receipt = clean_receipt()
        receipt["binary_audit_live_sha256"] = None
        runner.require_clean_session_exit(receipt, require_read_audit=False)
        with self.assertRaises(RuntimeError):
            runner.require_clean_session_exit(receipt)
        receipt["ck3_pids_after"] = [1234]
        with self.assertRaises(RuntimeError):
            runner.require_clean_session_exit(receipt, require_read_audit=False)

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
