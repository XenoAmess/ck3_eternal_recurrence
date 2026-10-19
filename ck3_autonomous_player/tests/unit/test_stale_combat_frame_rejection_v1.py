"""Stale-frame rejection must not inspect obsolete combat payloads."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import threading
import unittest
from unittest import mock

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from xar_autoplayer.bridge import native_driver as native
from test_combat_simulation_inputs_contract import _combat_inputs, _snapshot
from test_combat_phase_inputs_v3_bridge import _fixture_result, _semantic_snapshot


def inputs(version):
    if version == 2:
        snapshot = {**_snapshot(), "paused": True, "snapshot_id": "local:41",
                    "revision": 42, "native_revision": 41,
                    "diagnostics": {"connection_generation": 2}}
        body = _combat_inputs()
        status = "available"
    else:
        packet = _semantic_snapshot()
        snapshot = {**packet["state"], "snapshot_id": packet["snapshot_id"],
                    "revision": packet["revision"], "native_revision": packet["revision"],
                    "diagnostics": {"connection_generation": 2}}
        result = _fixture_result()
        body, status = result["combat_simulation_inputs"], result["status"]
    base = body if version == 2 else body["base_inputs"]
    scenario = base["scenario"]
    binding = {key: snapshot.get(key) for key in ("native_revision", "snapshot_id", "revision")}
    binding.update(connection_generation=snapshot["diagnostics"]["connection_generation"],
                   episode_run_id="offline-episode", target_province_id=base["target_province_id"],
                   attacker_entry_province_id=scenario["attacker_entry_province_id"],
                   attacker_army_ids=scenario["attacker_army_ids"], defender_army_ids=scenario["defender_army_ids"])
    return snapshot, {"status": status, "combat_simulation_inputs": body,
                      "query_sequence": 1, "cache_binding": binding}


def names(version):
    suffix = "" if version == 2 else "_v3"
    return ("_combat_simulation_inputs" + suffix + "_query",
            "_combat_simulation_inputs" + suffix + "_cache_for_snapshot",
            "normalize_combat_simulation_inputs" + suffix)


def harness(version, cache):
    driver = object.__new__(native.NativeHeadlessGameplayDriver)
    driver._driver_state_lock = threading.RLock()
    setattr(driver, names(version)[0], copy.deepcopy(cache))
    return driver


class StaleCombatFrameRejectionV1Test(unittest.TestCase):
    def test_each_stale_binding_clears_without_normalizing_payload(self):
        for version in (2, 3):
            snapshot, cache = inputs(version)
            field, method, normalizer = names(version)
            for key in ("native_revision", "snapshot_id", "revision", "connection_generation", "episode_run_id"):
                with self.subTest(version=version, key=key):
                    changed = copy.deepcopy(cache)
                    changed["cache_binding"][key] = "foreign"
                    driver = harness(version, changed)
                    with mock.patch.object(native, normalizer, side_effect=AssertionError("obsolete payload inspected")):
                        self.assertIsNone(getattr(driver, method)(snapshot, episode_run_id="offline-episode"))
                    self.assertIsNone(getattr(driver, field))

    def test_current_frame_still_normalizes_and_returns_detached_data(self):
        for version in (2, 3):
            with self.subTest(version=version):
                snapshot, cache = inputs(version)
                field, method, normalizer = names(version)
                driver = harness(version, cache)
                with mock.patch.object(native, normalizer, wraps=getattr(native, normalizer)) as normalize:
                    result = getattr(driver, method)(snapshot, episode_run_id="offline-episode")
                self.assertEqual(normalize.call_count, 1)
                self.assertIsNotNone(result)
                result["combat_simulation_inputs"].clear()
                self.assertEqual(getattr(driver, field), cache)

    def test_current_malformed_payload_still_normalizes_and_clears(self):
        for version in (2, 3):
            with self.subTest(version=version):
                snapshot, cache = inputs(version)
                cache["combat_simulation_inputs"] = {}
                field, method, normalizer = names(version)
                driver = harness(version, cache)
                with mock.patch.object(native, normalizer, wraps=getattr(native, normalizer)) as normalize:
                    self.assertIsNone(getattr(driver, method)(snapshot, episode_run_id="offline-episode"))
                self.assertEqual(normalize.call_count, 1)
                self.assertIsNone(getattr(driver, field))

    def test_unpaused_retains_existing_cache_without_normalizing(self):
        for version in (2, 3):
            with self.subTest(version=version):
                snapshot, cache = inputs(version)
                snapshot["paused"] = False
                field, method, normalizer = names(version)
                driver = harness(version, cache)
                with mock.patch.object(native, normalizer, side_effect=AssertionError("unpaused payload inspected")):
                    self.assertIsNone(getattr(driver, method)(snapshot, episode_run_id="offline-episode"))
                self.assertEqual(getattr(driver, field), cache)


if __name__ == "__main__":
    unittest.main()
