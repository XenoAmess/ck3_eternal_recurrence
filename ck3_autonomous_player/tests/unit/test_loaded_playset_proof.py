from __future__ import annotations

import copy
from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.environment import (
    OUTER_DESCRIPTOR_REF,
    PROFILE_MANIFEST_NAME,
    _contract_digest,
    sha256_file,
    snapshot_digest,
    tree_snapshot,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.simulation.loaded_playset_proof import (
    LOADED_PLAYSET_PROOF_SCHEMA_VERSION,
    LOADED_PLAYSET_PROOF_SCOPE,
    LoadedPlaysetProofError,
    build_loaded_playset_proof,
    validate_loaded_playset_proof,
)
from xar_autoplayer.simulation.phase_event_manifest import (
    FrozenPhaseEventSource,
    load_stock_phase_event_manifest,
)


_SOURCE_PATHS = (
    "common/combat_phase_events/_combat_phase_events.info",
    "common/combat_phase_events/00_commander_phase_events.txt",
    "common/combat_phase_events/00_knight_phase_events.txt",
    "common/scripted_effects/00_commander_effects.txt",
    "common/scripted_effects/00_death_management_effects.txt",
    "common/scripted_effects/00_lifestyle_focus_effects.txt",
    "common/scripted_effects/20_health_effects.txt",
    "common/script_values/00_basic_values.txt",
    "common/script_values/00_combat_values.txt",
    "common/script_values/00_court_position_values.txt",
    "common/script_values/04_ep2_accolade_values.txt",
)
_ACTIVE_REASON = (
    "suspended launch active; removed only after authenticated tree shutdown"
)
_RECIPE_PATH = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "combat_phase_events"
    / "v3_loaded_playset_proof_recipe.json"
)


class _ManagedPlaysetFixture:
    def __init__(self, root: Path) -> None:
        self.state_dir = (root / "state").resolve()
        self.profile = self.state_dir / "profile"
        self.production = self.profile / "mod-content" / "xar-production"
        self.game_dir = (root / "game-install").resolve()
        self.executable = self.game_dir / "binaries" / "ck3.exe"
        self.episode_run_id = "native-707-loaded-playset"
        self.snapshot_binding = {
            "snapshot_id": "native-snapshot-41",
            "revision": 41,
            "native_revision": 17,
        }
        self.hello = {
            "pid": 4343,
            "session_generation": 0,
            "game_version": "1.19.0.6",
            "executable_sha256": "",
        }
        self.environment_path = self.profile / PROFILE_MANIFEST_NAME
        self.dlc_load_path = self.profile / "dlc_load.json"
        self.outer_path = self.profile / "mod" / "xar_autoplayer.mod"
        self.inner_path = self.production / "descriptor.mod"
        self._write_fixture()

    def _write_fixture(self) -> None:
        self.executable.parent.mkdir(parents=True)
        self.executable.write_bytes(b"pinned ck3 executable fixture\n")
        executable_sha = sha256_file(self.executable).upper()
        self.hello["executable_sha256"] = executable_sha

        sources: list[FrozenPhaseEventSource] = []
        for index, relative in enumerate(_SOURCE_PATHS):
            path = self.game_dir / "game" / Path(relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"stock-source-{index}\n".encode("ascii"))
            sources.append(
                FrozenPhaseEventSource(
                    relative_path=relative,
                    sha256=sha256_file(path).upper(),
                    load_order=index,
                )
            )
        self.manifest = replace(
            load_stock_phase_event_manifest(),
            executable_sha256=executable_sha,
            files=tuple(sources),
        )

        self.production.mkdir(parents=True)
        self.inner_path.write_text(
            'name="fixture"\nversion="1"\n', encoding="utf-8"
        )
        self.outer_path.parent.mkdir(parents=True)
        self.outer_path.write_text(
            self.inner_path.read_text(encoding="utf-8")
            + f'path="{self.production.as_posix()}"\n',
            encoding="utf-8-sig",
        )
        self._write_json(
            self.dlc_load_path,
            {"enabled_mods": [OUTER_DESCRIPTOR_REF], "disabled_dlcs": []},
        )
        control = self.state_dir / "control"
        control.mkdir(parents=True)
        self._write_json(
            control / "ck3.json",
            {
                "format_version": 1,
                "nonce": "a" * 32,
                "ck3_pid": 4343,
                "parent_pid": 3131,
                "executable": str(self.executable),
                "creation_date": "20260825123456.123456+000",
            },
        )
        self._write_json(
            control / "unsafe-cleanup.json",
            {"nonce": "a" * 32, "ck3_pid": 4343, "reason": _ACTIVE_REASON},
        )
        self.environment = {
            "format_version": 1,
            "state_dir": str(self.state_dir),
            "profile_dir": str(self.profile),
            "game": {
                "raw_version": "1.19.0.6",
                "executable": str(self.executable),
                "executable_sha256": executable_sha.lower(),
            },
            "mod": {
                "production_path": str(self.production),
                "production_tree_sha256": "",
                "production_file_count": 0,
            },
            "load_profile": {
                "enabled_mods": [OUTER_DESCRIPTOR_REF],
                "disabled_dlcs": [],
                "outer_descriptor": str(self.outer_path),
                "outer_descriptor_sha256": sha256_file(self.outer_path),
                "dlc_load_sha256": sha256_file(self.dlc_load_path),
            },
        }
        self.refresh_environment_binding()

    def refresh_environment_binding(self) -> None:
        snapshot = tree_snapshot(self.production)
        self.environment["mod"]["production_tree_sha256"] = snapshot_digest(
            snapshot
        )
        self.environment["mod"]["production_file_count"] = len(snapshot)
        self.environment["load_profile"]["outer_descriptor_sha256"] = sha256_file(
            self.outer_path
        )
        self.environment["load_profile"]["dlc_load_sha256"] = sha256_file(
            self.dlc_load_path
        )
        self.environment["environment_sha256"] = _contract_digest(
            self.environment
        )
        self._write_json(self.environment_path, self.environment)

    def build(self) -> dict[str, object]:
        return build_loaded_playset_proof(
            self.state_dir,
            episode_run_id=self.episode_run_id,
            snapshot_binding=self.snapshot_binding,
            native_hello=self.hello,
            _manifest=self.manifest,
        )

    def validate(
        self,
        proof: object,
        *,
        episode_run_id: str | None = None,
        snapshot_binding: dict[str, object] | None = None,
        hello: dict[str, object] | None = None,
    ) -> dict[str, object]:
        return validate_loaded_playset_proof(
            proof,
            self.state_dir,
            episode_run_id=episode_run_id or self.episode_run_id,
            snapshot_binding=snapshot_binding or self.snapshot_binding,
            native_hello=hello or self.hello,
            _manifest=self.manifest,
        )

    @staticmethod
    def _write_json(path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


class _ProofSnapshotDriver:
    def __init__(
        self,
        state_dir: Path,
        snapshot: dict[str, object],
        *,
        drift_on_read: bool = False,
    ) -> None:
        self.state_dir = state_dir
        self.snapshot = copy.deepcopy(snapshot)
        self.drift_on_read = drift_on_read

    def take_snapshot(self) -> dict[str, object]:
        row = copy.deepcopy(self.snapshot)
        if self.drift_on_read:
            row["snapshot_id"] = "native-snapshot-42"
            row["revision"] = 42
            row["native_revision"] = 18
        return row


class LoadedPlaysetProofTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.fixture = _ManagedPlaysetFixture(Path(self.temporary.name))

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_verified_proof_is_deterministic_and_covers_all_eleven_sources(self) -> None:
        first = self.fixture.build()
        second = self.fixture.build()

        self.assertEqual(first, second)
        self.assertEqual(first["status"], "verified")
        self.assertEqual(first["episode_run_id"], self.fixture.episode_run_id)
        self.assertEqual(first["snapshot_binding"], self.fixture.snapshot_binding)
        self.assertEqual(first["stock_sources"]["count"], 11)
        self.assertEqual(
            [row["relative_path"] for row in first["stock_sources"]["files"]],
            list(_SOURCE_PATHS),
        )
        self.assertTrue(first["claims"]["loaded_playset_verified"])
        self.assertEqual(self.fixture.validate(first), first)

    def test_proof_recipe_freezes_bindings_without_closing_other_gates(self) -> None:
        recipe = json.loads(_RECIPE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            recipe["schema_version"], LOADED_PLAYSET_PROOF_SCHEMA_VERSION
        )
        self.assertEqual(recipe["proof_scope"], LOADED_PLAYSET_PROOF_SCOPE)
        self.assertEqual(recipe["source_count"], 11)
        self.assertEqual(
            recipe["source_paths_in_load_order"], list(_SOURCE_PATHS)
        )
        self.assertEqual(
            recipe["enabled_mods_exact"], [OUTER_DESCRIPTOR_REF]
        )
        gates = recipe["independent_fidelity_gates"]
        self.assertFalse(gates["ast_evaluator_ready"])
        self.assertFalse(gates["original_trace_ready"])
        self.assertFalse(gates["transition_fidelity_gate"])
        self.assertFalse(gates["planner_usable"])
        self.assertFalse(gates["active_attack_allowed"])

    def test_service_binds_verified_proof_to_the_exact_same_snapshot(self) -> None:
        snapshot = {
            **self.fixture.snapshot_binding,
            "paused": True,
            "episode_run_id": self.fixture.episode_run_id,
            "diagnostics": {"hello": copy.deepcopy(self.fixture.hello)},
        }
        service = GameplayBridgeService(
            _ProofSnapshotDriver(self.fixture.state_dir, snapshot)
        )

        def build_with_fixture_manifest(*args, **kwargs):
            return build_loaded_playset_proof(
                *args, **kwargs, _manifest=self.fixture.manifest
            )

        with mock.patch(
            "xar_autoplayer.bridge.service.build_loaded_playset_proof",
            side_effect=build_with_fixture_manifest,
        ):
            proof = service._loaded_playset_proof_for_snapshot(snapshot)

        self.assertEqual(proof["status"], "verified")
        self.assertEqual(
            proof["snapshot_binding"], self.fixture.snapshot_binding
        )
        self.assertTrue(proof["claims"]["loaded_playset_verified"])

    def test_service_rejects_proof_when_snapshot_changes_during_hashing(self) -> None:
        snapshot = {
            **self.fixture.snapshot_binding,
            "paused": True,
            "episode_run_id": self.fixture.episode_run_id,
            "diagnostics": {"hello": copy.deepcopy(self.fixture.hello)},
        }
        service = GameplayBridgeService(
            _ProofSnapshotDriver(
                self.fixture.state_dir,
                snapshot,
                drift_on_read=True,
            )
        )

        def build_with_fixture_manifest(*args, **kwargs):
            return build_loaded_playset_proof(
                *args, **kwargs, _manifest=self.fixture.manifest
            )

        with mock.patch(
            "xar_autoplayer.bridge.service.build_loaded_playset_proof",
            side_effect=build_with_fixture_manifest,
        ):
            proof = service._loaded_playset_proof_for_snapshot(snapshot)

        self.assertEqual(proof["status"], "unavailable")
        self.assertFalse(proof["claims"]["loaded_playset_verified"])
        self.assertEqual(
            proof["unavailable_reason"],
            "snapshot_changed_during_loaded_playset_proof",
        )

    def test_enabled_mods_must_be_the_exact_autoplayer_singleton(self) -> None:
        self.fixture._write_json(
            self.fixture.dlc_load_path,
            {
                "enabled_mods": [OUTER_DESCRIPTOR_REF, "mod/forbidden.mod"],
                "disabled_dlcs": [],
            },
        )
        self.fixture.refresh_environment_binding()

        with self.assertRaisesRegex(
            LoadedPlaysetProofError, "exact xar_autoplayer singleton"
        ):
            self.fixture.build()

    def test_production_exact_path_overlay_is_rejected(self) -> None:
        overlay = self.fixture.production / Path(_SOURCE_PATHS[0])
        overlay.parent.mkdir(parents=True)
        overlay.write_text("override\n", encoding="utf-8")
        self.fixture.refresh_environment_binding()

        with self.assertRaisesRegex(LoadedPlaysetProofError, "overlays"):
            self.fixture.build()

    def test_production_replace_path_covering_a_source_is_rejected(self) -> None:
        self.fixture.inner_path.write_text(
            'name="fixture"\nreplace_path="common/combat_phase_events"\n',
            encoding="utf-8",
        )
        self.fixture.refresh_environment_binding()

        with self.assertRaisesRegex(LoadedPlaysetProofError, "replace_path covers"):
            self.fixture.build()

    def test_each_stock_source_is_rehashed(self) -> None:
        stock = self.fixture.game_dir / "game" / Path(_SOURCE_PATHS[7])
        stock.write_text("drifted\n", encoding="utf-8")

        with self.assertRaisesRegex(LoadedPlaysetProofError, "source hash differs"):
            self.fixture.build()

    def test_proof_rejects_episode_and_snapshot_drift(self) -> None:
        proof = self.fixture.build()
        with self.assertRaisesRegex(
            LoadedPlaysetProofError, "current episode/environment"
        ):
            self.fixture.validate(proof, episode_run_id="native-other-episode")

        changed = dict(self.fixture.snapshot_binding)
        changed["revision"] = 42
        with self.assertRaisesRegex(
            LoadedPlaysetProofError, "current episode/environment"
        ):
            self.fixture.validate(proof, snapshot_binding=changed)

    def test_proof_rejects_environment_fingerprint_change(self) -> None:
        proof = self.fixture.build()
        self.fixture.environment["proof_epoch"] = 2
        self.fixture.refresh_environment_binding()

        with self.assertRaisesRegex(
            LoadedPlaysetProofError, "current episode/environment"
        ):
            self.fixture.validate(proof)

    def test_native_pid_must_match_the_managed_launch(self) -> None:
        changed = dict(self.fixture.hello)
        changed["pid"] = 4344
        with self.assertRaisesRegex(LoadedPlaysetProofError, "PID differs"):
            self.fixture.validate(self.fixture.build(), hello=changed)

    def test_proof_hash_tampering_is_rejected_before_rebuild(self) -> None:
        proof = self.fixture.build()
        proof["claims"]["loaded_playset_verified"] = False
        with self.assertRaisesRegex(LoadedPlaysetProofError, "proof hash differs"):
            self.fixture.validate(proof)


if __name__ == "__main__":
    unittest.main()
