"""Self-contained optional-episode regression; source pins are provenance, never CI file inputs."""
from __future__ import annotations

from copy import deepcopy
import unittest
from ck3_mod_acceptance_cases import faith_e02_pilgrimage_observations as O

# No referenced source path is opened here. Raw absence is retained in this
# minimal projection; all fields below were copied from the pinned actual R22 frame.
SOURCE_REFERENCE: dict[str, object] = {'kind': 'DERIVED_MINIMAL_GUARD_PROJECTION_OF_REAL_R22_FRAME',
 'machine_id': '4-8e1c2f1861',
 'observed_at_utc': '2026-10-20T23:11:19.383687+00:00',
 'full_source_pin': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\capture-b35-p3-a01\\live\\4-8e1c2f1861--faith-engine--R0022\\case-output\\faith-e02-journey-001-event-13-key-window-refresh.json',
                     'bytes': 41020,
                     'sha256': 'e86bbf37e16bc74d11dce41adf9cfa88aefa3e8f4658eef2bed1068b6de56580'},
 'json_pointer': '/query_after_frame',
 'diagnosis_sha256': 'fd185e14d0e4824bf002a2a78d3784cbe0bf02768e3612af7df0d09768e6ee14',
 'old_frame_predicate_result': None,
 'fixture_is_live_observation': False}

R22_FRAME: O.JSONObject = {'date_raw': 53148024,
 'revision': 482,
 'native_revision': 481,
 'paused': True,
 'map_ready': True,
 'backend_id': 'native-headless',
 'source': 'injected-dll-named-pipe',
 'played_character': {'character_id': 31254, 'alive': True, 'source': 'native'},
 'diagnostics': {'bridge_pid': 21144,
                 'connection_generation': 1,
                 'hello': {'pid': 21144,
                           'connection_generation': 1,
                           'ck3_build_match': True,
                           'game_adapter_id': 'ck3-1.20.0.4-msvc-x64'}}}

R22_BINDING: O.MilestoneBinding = {'run_id': '4-8e1c2f1861--faith-engine--R0022',
 'machine_id': '4-8e1c2f1861',
 'actor_character_id': 31254,
 'bridge_pid': 21144,
 'connection_generation': 1,
 'episode_run_id': None}


class OptionalEpisodeTests(unittest.TestCase):
    def test_retained_r22_missing_episode_none_admits_without_raw_backfill(self) -> None:
        frame = deepcopy(R22_FRAME)
        self.assertNotIn("episode_run_id", frame)
        observed = O._frame(frame, O.parse_binding(R22_BINDING))
        self.assertIsNotNone(observed)
        if observed is None:
            self.fail("The real R22 optional-field counterexample must bind")
        self.assertEqual((observed.date_raw, observed.revision, observed.native_revision),
                         (53148024, 482, 481))
        self.assertNotIn("episode_run_id", observed.raw)
        self.assertEqual(frame, R22_FRAME)

    def test_explicit_null_and_declared_episode_preserve_provided_value(self) -> None:
        frame = deepcopy(R22_FRAME)
        frame["episode_run_id"] = None
        observed = O._frame(frame, O.parse_binding(R22_BINDING))
        self.assertIsNotNone(observed)
        if observed is None:
            self.fail("Explicit null matches a declared null episode")
        self.assertIn("episode_run_id", observed.raw)
        self.assertIsNone(observed.raw["episode_run_id"])
        declared = deepcopy(R22_BINDING)
        declared["episode_run_id"] = "authored-episode-a"
        frame["episode_run_id"] = "authored-episode-a"
        self.assertIsNotNone(O._frame(frame, O.parse_binding(declared)))
        self.assertEqual(frame["episode_run_id"], "authored-episode-a")

    def test_nonnull_missing_or_wrong_provided_value_and_type_reject(self) -> None:
        declared = deepcopy(R22_BINDING)
        declared["episode_run_id"] = "authored-episode-a"
        self.assertIsNone(O._frame(deepcopy(R22_FRAME), O.parse_binding(declared)))
        bad_values: tuple[O.JSONValue, ...] = (None, "authored-episode-b", False, 0, 1.0, [], {})
        for value in bad_values:
            frame = deepcopy(R22_FRAME)
            frame["episode_run_id"] = value
            with self.subTest(declared="nonnull", supplied=value):
                self.assertIsNone(O._frame(frame, O.parse_binding(declared)))
        for value in bad_values[1:]:
            frame = deepcopy(R22_FRAME)
            frame["episode_run_id"] = value
            with self.subTest(declared=None, supplied=value):
                self.assertIsNone(O._frame(frame, O.parse_binding(R22_BINDING)))
        malformed = O._object(R22_BINDING)
        malformed["episode_run_id"] = False
        with self.assertRaises(ValueError):
            O.parse_binding(malformed)

    def test_other_owner_build_pause_and_integer_guards_still_reject(self) -> None:
        mutations: tuple[tuple[tuple[str, ...], O.JSONValue], ...] = (
            (("played_character", "character_id"), 31255),
            (("played_character", "alive"), False),
            (("played_character", "source"), "authored-other-source"),
            (("diagnostics", "bridge_pid"), 21145),
            (("diagnostics", "hello", "pid"), 21145),
            (("diagnostics", "connection_generation"), 2),
            (("diagnostics", "hello", "connection_generation"), 2),
            (("paused",), False), (("map_ready",), False),
            (("backend_id",), "authored-other-backend"),
            (("source",), "authored-other-source"),
            (("diagnostics", "hello", "ck3_build_match"), False),
            (("diagnostics", "hello", "game_adapter_id"), "ck3-other-build"),
            (("date_raw",), True), (("revision",), False), (("native_revision",), None),
            (("played_character", "character_id"), True),
        )
        for path, value in mutations:
            frame = deepcopy(R22_FRAME)
            selected = frame
            for key in path[:-1]:
                item = selected[key]
                if not isinstance(item, dict):
                    self.fail("Fixture path is not an object")
                selected = item
            selected[path[-1]] = value
            with self.subTest(path=path):
                self.assertIsNone(O._frame(frame, O.parse_binding(R22_BINDING)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
