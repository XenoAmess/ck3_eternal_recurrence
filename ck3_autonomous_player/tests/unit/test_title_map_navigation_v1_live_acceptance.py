from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HARNESS_PATH = (
    PROJECT_ROOT
    / "native_bridge"
    / "research"
    / "run_title_map_navigation_v1_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_title_map_navigation_v1_live_acceptance",
    HARNESS_PATH,
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


PUBLIC_REVISION = 9
NATIVE_REVISION = 27
DATE_RAW = 53_182_016
SNAPSHOT_ID = "native:27"
EPISODE_RUN_ID = "native-1234-title-map-live-fixture"
CONNECTION_GENERATION = 4
PLAYER_CHARACTER_ID = 1_234


def _binding() -> dict[str, object]:
    return {
        "snapshot_id": SNAPSHOT_ID,
        "revision": PUBLIC_REVISION,
        "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "episode_run_id": EPISODE_RUN_ID,
        "connection_generation": CONNECTION_GENERATION,
    }


def _title(title_key: str) -> dict[str, object]:
    if title_key == HARNESS.DISPLACEMENT_TITLE_KEY:
        return {
            "key": title_key,
            "title_id": 50_000,
            "tier_raw": 2,
            "tier_key": "county",
            "anchor_kind": "title_bounds_center",
            "capital_province_id": 9_000,
            "bounds_extent": [80, 80, 120, 120],
            "map_x_adjustment": 0,
        }
    if title_key == HARNESS.COUNTY_TITLE_KEY:
        return {
            "key": title_key,
            "title_id": 50_001,
            "tier_raw": 2,
            "tier_key": "county",
            "anchor_kind": "title_bounds_center",
            "capital_province_id": 9_822,
            "bounds_extent": [1_600, -1_000, 1_674, -895],
            "map_x_adjustment": 5,
        }
    if title_key == HARNESS.BARONY_TITLE_KEY:
        return {
            "key": title_key,
            "title_id": 50_002,
            "tier_raw": 1,
            "tier_key": "barony",
            "anchor_kind": "title_bounds_center",
            "capital_province_id": 9_822,
            "bounds_extent": [1_632, -947, 1_632, -947],
            "map_x_adjustment": 0,
        }
    raise AssertionError(f"unexpected fixture title: {title_key}")


def _position(title_key: str) -> list[float]:
    if title_key == HARNESS.DISPLACEMENT_TITLE_KEY:
        return [100.0, 0.0, 100.0]
    # The static contract deliberately demonstrates that the county and its
    # capital barony can have the same final camera center.
    return [1_632.0, 0.0, -947.0]


def _camera(title_key: str, status: str) -> dict[str, object]:
    position = _position(title_key)
    state = [*position, 0.75, 0.0, 1.0]
    return {
        "status": status,
        "postcondition_verified": True,
        "expected_position_xyz": position,
        "current_state": state,
        "target_state": copy.deepcopy(state),
        "zoom_index": 3,
        "expected_zoom_value": 0.75,
        "settled": True,
        "target_write_blocked": False,
        "completion_predicate": (
            HARNESS.TITLE_MAP_NAVIGATION_V1_COMPLETION_PREDICATE
        ),
    }


def _result(
    title_key: str,
    status: str,
    *,
    dispatch_sequence: int,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "step": HARNESS.CENTER_MAP_ON_LANDED_TITLE_V1_STEP,
        "accepted": True,
        "status": status,
        "title": _title(title_key),
        "binding": _binding(),
        "native_action_ack": (
            {"sequence": dispatch_sequence, "status": "dispatched"}
            if status == "centered"
            else {"sequence": None, "status": "not_needed"}
        ),
        "camera_center": _camera(title_key, status),
        "source": {
            "game_version": HARNESS.TITLE_MAP_NAVIGATION_V1_GAME_VERSION,
            "executable_sha256": (
                HARNESS.TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256
            ),
            "backend_id": HARNESS.TITLE_MAP_NAVIGATION_V1_BACKEND_ID,
        },
    }


class _FakeService:
    def __init__(
        self,
        *,
        unknown_error: str = "title_key_not_found",
        mutate_on_unknown: bool = False,
        drift_after_commands: int | None = None,
    ) -> None:
        self.unknown_error = unknown_error
        self.mutate_on_unknown = mutate_on_unknown
        self.drift_after_commands = drift_after_commands
        self.current_title: str | None = None
        self.dispatch_sequence = 0
        self.command_title_keys: list[str] = []
        self.history: list[dict[str, object]] = []
        self.events: list[tuple[object, ...]] = []

    def _drifted(self) -> bool:
        return bool(
            self.drift_after_commands is not None
            and len(self.command_title_keys) >= self.drift_after_commands
        )

    def snapshot(self) -> dict[str, object]:
        self.events.append(("snapshot", len(self.command_title_keys)))
        binding = _binding()
        if self._drifted():
            binding["snapshot_id"] = "native:28"
            binding["native_revision"] = NATIVE_REVISION + 1
        return {
            **binding,
            "paused": True,
            "map_ready": True,
            "phase": "map_hud",
            "played_character": {
                "character_id": PLAYER_CHARACTER_ID,
                "alive": True,
            },
            "diagnostics": {
                "connection_generation": CONNECTION_GENERATION,
            },
            "native_command_history": copy.deepcopy(self.history),
        }

    def center_map_on_landed_title_v1(
        self,
        title_key: str,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        if expected_revision != PUBLIC_REVISION:
            raise AssertionError("runner did not reuse frozen public revision")
        self.events.append(("command", title_key, expected_revision))
        self.command_title_keys.append(title_key)
        if title_key == HARNESS.UNKNOWN_TITLE_KEY:
            if self.mutate_on_unknown:
                self.current_title = HARNESS.DISPLACEMENT_TITLE_KEY
            error = HARNESS.BridgeUnavailableError(
                f"native gameplay step failed: {self.unknown_error}"
            )
            error.native_error = self.unknown_error
            self.history.append(
                {
                    "index": len(self.history) + 1,
                    "command": HARNESS.CENTER_MAP_ON_LANDED_TITLE_V1_STEP,
                    "ok": False,
                    "error": f"BridgeUnavailableError: {error}",
                }
            )
            raise error
        status = (
            "already_centered"
            if self.current_title is not None
            and _position(self.current_title) == _position(title_key)
            else "centered"
        )
        if status == "centered":
            self.dispatch_sequence += 1
        result = _result(
            title_key,
            status,
            dispatch_sequence=self.dispatch_sequence,
        )
        self.current_title = title_key
        self.history.append(
            {
                "index": len(self.history) + 1,
                "command": HARNESS.CENTER_MAP_ON_LANDED_TITLE_V1_STEP,
                "ok": True,
                "result": copy.deepcopy(result),
            }
        )
        return result


def _capabilities(
    *,
    advertise: bool = True,
    generic_action: bool = False,
) -> dict[str, object]:
    bridge_capabilities = (
        [HARNESS.CENTER_MAP_ON_LANDED_TITLE_V1_CAPABILITY]
        if advertise
        else []
    )
    return {
        "backend_id": HARNESS.PURE_NATIVE_MODE,
        "bridge_capabilities": bridge_capabilities,
        "action_steps": (
            [HARNESS.CENTER_MAP_ON_LANDED_TITLE_V1_STEP]
            if generic_action
            else []
        ),
        "diagnostics": {
            "connected": True,
            "bridge_pid": 4_321,
            "connection_generation": CONNECTION_GENERATION,
            "hello": {
                "capabilities": bridge_capabilities,
                "expected_ck3_version": (
                    HARNESS.TITLE_MAP_NAVIGATION_V1_GAME_VERSION
                ),
                "expected_ck3_sha256": (
                    HARNESS.TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256
                ),
                "game_adapter_id": HARNESS.EXPECTED_ADAPTER_ID,
                "game_adapter_status": "ready",
                "ck3_build_match": True,
            },
        },
    }


class TitleMapNavigationV1LiveAcceptanceTests(unittest.TestCase):
    def test_one_session_matrix_has_displacements_repeat_and_typed_red(
        self,
    ) -> None:
        service = _FakeService()

        result = HARNESS._run_navigation_sequence(service)

        self.assertTrue(result["ok"])
        self.assertEqual(
            service.command_title_keys,
            list(HARNESS._EXPECTED_COMMAND_KEYS),
        )
        command_event_indexes = [
            index
            for index, event in enumerate(service.events)
            if event[0] == "command"
        ]
        self.assertEqual(len(command_event_indexes), 7)
        self.assertGreaterEqual(
            sum(event[0] == "snapshot" for event in service.events), 14
        )
        self.assertTrue(
            all(
                index > 0 and service.events[index - 1][0] == "snapshot"
                for index in command_event_indexes
            ),
            service.events,
        )
        self.assertEqual(
            [
                row["typed_service_payload"]["status"]
                for row in result["known_steps"]
            ],
            [
                "centered",
                "centered",
                "centered",
                "centered",
                "already_centered",
            ],
        )
        self.assertEqual(
            result["unknown_step"]["typed_error"]["native_error"],
            "title_key_not_found",
        )
        self.assertTrue(
            result["unknown_step"]["checks"]["camera_unchanged"]
        )
        self.assertEqual(
            len(result["raw_native_driver_history_delta"]), 7
        )

    def test_county_and_barony_may_share_center_but_are_distinct_titles(
        self,
    ) -> None:
        result = HARNESS._run_navigation_sequence(_FakeService())
        county = result["known_steps"][1]["typed_service_payload"]
        barony = result["known_steps"][3]["typed_service_payload"]

        self.assertEqual(
            county["camera_center"]["expected_position_xyz"],
            barony["camera_center"]["expected_position_xyz"],
        )
        self.assertNotEqual(county["title"]["title_id"], barony["title"]["title_id"])
        self.assertNotEqual(
            county["title"]["bounds_extent"],
            barony["title"]["bounds_extent"],
        )
        self.assertTrue(result["known_title_checks"]["distinct_title_bounds"])

    def test_wrong_unknown_code_is_not_a_typed_missing_title_red(self) -> None:
        result = HARNESS._run_navigation_sequence(
            _FakeService(unknown_error="internal_error")
        )

        self.assertFalse(result["ok"])
        self.assertFalse(result["unknown_step"]["checks"]["typed_red"])

    def test_unknown_camera_mutation_is_detected_by_already_centered_probe(
        self,
    ) -> None:
        result = HARNESS._run_navigation_sequence(
            _FakeService(mutate_on_unknown=True)
        )

        self.assertFalse(result["ok"])
        checks = result["unknown_step"]["checks"]
        self.assertFalse(checks["integrity_probe_already_centered"])
        self.assertFalse(checks["camera_unchanged"])

    def test_full_binding_drift_is_red(self) -> None:
        result = HARNESS._run_navigation_sequence(
            _FakeService(drift_after_commands=3)
        )

        self.assertFalse(result["ok"])
        self.assertFalse(result["checks"]["full_binding_stable"])

    def test_capability_is_advertised_but_never_a_generic_action(self) -> None:
        self.assertTrue(HARNESS._capability_proof(_capabilities())["ok"])
        self.assertFalse(
            HARNESS._capability_proof(
                _capabilities(generic_action=True)
            )["ok"]
        )
        self.assertFalse(
            HARNESS._capability_proof(
                _capabilities(advertise=False)
            )["ok"]
        )

    def test_binary_proof_binds_exe_dll_and_injector(self) -> None:
        expected_dll = "A" * 64
        expected_injector = "B" * 64
        proof = HARNESS._exact_binary_proof(
            _capabilities(),
            managed_executable_sha256=(
                HARNESS.TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256
            ),
            production_dll_sha256=expected_dll,
            expected_production_dll_sha256=expected_dll,
            injector_sha256=expected_injector,
            expected_injector_sha256=expected_injector,
        )
        wrong = HARNESS._exact_binary_proof(
            _capabilities(),
            managed_executable_sha256=(
                HARNESS.TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256
            ),
            production_dll_sha256=expected_dll,
            expected_production_dll_sha256=expected_dll,
            injector_sha256="C" * 64,
            expected_injector_sha256=expected_injector,
        )

        self.assertTrue(proof["ok"])
        self.assertFalse(wrong["ok"])
        self.assertFalse(wrong["checks"]["injector_sha256"])

    def test_source_save_is_hash_bound_and_contained(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            profile = root / "profile"
            save = profile / "save games" / "source.ck3"
            save.parent.mkdir(parents=True)
            save.write_bytes(b"immutable-title-map-source")
            digest = hashlib.sha256(save.read_bytes()).hexdigest().upper()

            resolved, identity = HARNESS._resolve_source_save(
                profile, Path("save games/source.ck3"), digest
            )

            self.assertEqual(resolved, save.resolve())
            self.assertEqual(identity["sha256"], digest)
            with self.assertRaisesRegex(HARNESS.AgentError, "escapes"):
                HARNESS._resolve_source_save(
                    profile, Path("../outside.ck3"), digest
                )
            with self.assertRaisesRegex(HARNESS.AgentError, "differs"):
                HARNESS._resolve_source_save(
                    profile, Path("save games/source.ck3"), "A" * 64
                )

    def test_cleanup_requires_nonce_and_managed_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            target = parent / "clone"
            target.mkdir()
            marker = target / HARNESS._DISPOSABLE_MARKER_NAME
            marker.write_text(
                json.dumps(
                    {"kind": HARNESS._DISPOSABLE_KIND, "nonce": "right"}
                ),
                encoding="utf-8",
            )
            blocked = HARNESS._cleanup_disposable_root(
                target,
                clone_nonce="right",
                retain_state=False,
                stage={
                    "session_started": True,
                    "cleanup": {"ok": False},
                },
            )
            self.assertFalse(blocked["ok"])
            self.assertTrue(target.exists())

            removed = HARNESS._cleanup_disposable_root(
                target,
                clone_nonce="right",
                retain_state=False,
                stage={
                    "session_started": True,
                    "cleanup": {"ok": True},
                },
            )
            self.assertTrue(removed["ok"])
            self.assertFalse(target.exists())

    def test_no_visual_input_import_and_inhibit_is_honestly_skipped(self) -> None:
        tree = ast.parse(HARNESS_PATH.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertTrue(
            imported.isdisjoint(
                {
                    "cv2",
                    "PIL",
                    "pyautogui",
                    "pyperclip",
                    "pytesseract",
                    "win32clipboard",
                    "win32gui",
                }
            )
        )
        interaction = HARNESS._interaction_audit()
        inhibit = HARNESS._inhibit_negative_report()
        self.assertTrue(interaction["all_zero"])
        self.assertEqual(inhibit["status"], "skipped")
        self.assertFalse(inhibit["executed"])
        self.assertFalse(inhibit["process_memory_modified"])
        self.assertTrue(inhibit["acceptable_for_gate"])

    def test_command_timeout_exceeds_native_settle_budget(self) -> None:
        self.assertGreater(HARNESS.NATIVE_COMMAND_TIMEOUT_SECONDS, 15.0)


if __name__ == "__main__":
    unittest.main()
