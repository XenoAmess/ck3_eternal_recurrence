from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
HARNESS_PATH = (
    PROJECT_ROOT
    / "native_bridge"
    / "research"
    / "run_loaded_feature_manifest_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_loaded_feature_manifest_live_acceptance",
    HARNESS_PATH,
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


PUBLIC_REVISION = 7
NATIVE_REVISION = 31
DATE_RAW = 53_182_016
SNAPSHOT_ID = "native:31"
PIPE_NAME = r"\\.\pipe\xar_loaded_feature_live_fixture"


def _feature_items() -> list[dict[str, object]]:
    return [
        {
            "native_index": index,
            "cstring_id": cstring_id,
            "key": key,
            "enabled": index in HARNESS._ALWAYS_ON_FEATURE_INDICES
            or index % 4 == 0,
        }
        for index, (cstring_id, key) in enumerate(
            HARNESS.loaded_feature_contract._FEATURE_DEFINITIONS
        )
    ]


def _frame() -> dict[str, object]:
    return {
        "schema": "loaded-feature-manifest-v1",
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "unavailable_reason": None,
        "build": {
            "version": HARNESS.LOADED_FEATURE_MANIFEST_V1_GAME_VERSION,
            "exe_sha256": (
                HARNESS.LOADED_FEATURE_MANIFEST_V1_EXECUTABLE_SHA256
            ),
        },
        "effective_feature_flags": {
            "status": "available",
            "unavailable_reason": None,
            "native_count": 44,
            "items": _feature_items(),
        },
        "script_dlc_keys": {
            "status": "available",
            "unavailable_reason": None,
            "enumerated_count": 3,
            "keys": ["DLC A", "Zeta", "éclair"],
        },
        "entitlements": {
            "status": "unavailable",
            "unavailable_reason": "store_verdict_provenance_unclosed",
            "items": None,
        },
        "readiness": {
            "effective_feature_flags_ready": True,
            "script_dlc_keys_ready": True,
            "entitlements_ready": False,
            "same_frame_ready": True,
            "actionable_ready": True,
        },
        "provenance": {
            "feature_root_slot_rva": "0x576CC68",
            "feature_bitset_rva": "root+0x2B0",
            "feature_enum_table_rva": "0x42F7850..0x42F7900",
            "script_dlc_set_rva": "0x5762590",
            "backend_id": (
                HARNESS.loaded_feature_contract
                .LOADED_FEATURE_MANIFEST_V1_BACKEND_ID
            ),
        },
    }


def _query_result(
    query_sequence: int,
    *,
    frame: dict[str, object] | None = None,
) -> dict[str, object]:
    manifest = copy.deepcopy(frame if frame is not None else _frame())
    return {
        "step": HARNESS.QUERY_LOADED_FEATURE_MANIFEST_V1_STEP,
        "accepted": True,
        "status": manifest["status"],
        "query_sequence": query_sequence,
        "snapshot_revision": NATIVE_REVISION,
        "loaded_feature_manifest": manifest,
        "backend_id": "native-headless",
        "loaded_feature_manifest_ready": True,
        "scope": "exact-loaded-feature-manifest",
        "source": {
            "game_version": (
                HARNESS.LOADED_FEATURE_MANIFEST_V1_GAME_VERSION
            ),
            "executable_sha256": (
                HARNESS.LOADED_FEATURE_MANIFEST_V1_EXECUTABLE_SHA256
            ),
            "snapshot_id": SNAPSHOT_ID,
            "revision": PUBLIC_REVISION,
            "native_revision": NATIVE_REVISION,
            "date_raw": DATE_RAW,
            "paused": True,
            "backend_id": "native-headless",
        },
        "binding": {
            "snapshot_id": SNAPSHOT_ID,
            "revision": PUBLIC_REVISION,
            "native_revision": NATIVE_REVISION,
            "date_raw": DATE_RAW,
            "expected_revision": PUBLIC_REVISION,
        },
    }


def _snapshot(*, map_ready: bool = True) -> dict[str, object]:
    return {
        "snapshot_id": SNAPSHOT_ID,
        "revision": PUBLIC_REVISION,
        "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "episode_run_id": "loaded-feature-live-fixture",
        "paused": True,
        "map_ready": map_ready,
        "phase": "map_hud",
    }


class _FakeService:
    def __init__(
        self,
        *,
        second_frame: dict[str, object] | None = None,
        envelope_drift: bool = False,
        snapshot_drift: bool = False,
        map_ready: bool = True,
    ) -> None:
        self.second_frame = second_frame
        self.envelope_drift = envelope_drift
        self.snapshot_drift = snapshot_drift
        self.map_ready = map_ready
        self.query_count = 0
        self.calls: list[tuple[str, int]] = []

    def snapshot(self) -> dict[str, object]:
        result = _snapshot(map_ready=self.map_ready)
        if self.snapshot_drift and self.query_count >= 1:
            result["native_revision"] = NATIVE_REVISION + 1
            result["snapshot_id"] = "native:32"
        return result

    def query_loaded_feature_manifest_v1(
        self, *, expected_revision: int
    ) -> dict[str, object]:
        if expected_revision != PUBLIC_REVISION:
            raise AssertionError("query did not use frozen public revision")
        self.calls.append(
            (HARNESS.QUERY_LOADED_FEATURE_MANIFEST_V1_STEP, expected_revision)
        )
        self.query_count += 1
        frame = self.second_frame if self.query_count == 2 else None
        result = _query_result(self.query_count, frame=frame)
        if self.envelope_drift and self.query_count == 2:
            result["backend_id"] = "drifted"
        return result


def _capabilities(*, include_query: bool = True) -> dict[str, object]:
    bridge_capabilities = (
        [HARNESS.QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY]
        if include_query
        else []
    )
    return {
        "bridge_capabilities": bridge_capabilities,
        "action_steps": (
            [HARNESS.QUERY_LOADED_FEATURE_MANIFEST_V1_STEP]
            if include_query
            else []
        ),
        "loaded_feature_manifest_v1_query_supported": include_query,
        "diagnostics": {
            "connected": True,
            "bridge_pid": 1234,
            "connection_generation": 5,
            "hello": {
                "capabilities": bridge_capabilities,
                "expected_ck3_version": (
                    HARNESS.LOADED_FEATURE_MANIFEST_V1_GAME_VERSION
                ),
                "expected_ck3_sha256": (
                    HARNESS.LOADED_FEATURE_MANIFEST_V1_EXECUTABLE_SHA256
                ),
                "game_adapter_id": HARNESS.EXPECTED_ADAPTER_ID,
                "game_adapter_status": "ready",
                "ck3_build_match": True,
            },
        },
    }


class LoadedFeatureManifestLiveAcceptanceTests(unittest.TestCase):
    def test_manifest_proof_requires_all_exact_rows_and_baseline_bits(
        self,
    ) -> None:
        proof = HARNESS._manifest_proof(
            _query_result(1),
            expected_native_revision=NATIVE_REVISION,
            expected_date_raw=DATE_RAW,
        )

        self.assertTrue(proof["ok"])
        self.assertEqual(proof["native_row_count"], 44)
        self.assertGreaterEqual(
            proof["computed_enabled_popcount"],
            len(HARNESS._ALWAYS_ON_FEATURE_INDICES),
        )
        self.assertTrue(proof["checks"]["always_on_feature_baseline"])

    def test_manifest_proof_rejects_registry_identity_drift(self) -> None:
        changed = _query_result(1)
        changed["loaded_feature_manifest"]["effective_feature_flags"][
            "items"
        ][12]["cstring_id"] += 1

        proof = HARNESS._manifest_proof(
            changed,
            expected_native_revision=NATIVE_REVISION,
            expected_date_raw=DATE_RAW,
        )

        self.assertFalse(proof["ok"])
        self.assertFalse(proof["checks"]["exact_44_native_rows"])

    def test_manifest_proof_rejects_missing_always_on_feature(self) -> None:
        changed = _query_result(1)
        items = changed["loaded_feature_manifest"][
            "effective_feature_flags"
        ]["items"]
        for item in items:
            item["enabled"] = False

        proof = HARNESS._manifest_proof(
            changed,
            expected_native_revision=NATIVE_REVISION,
            expected_date_raw=DATE_RAW,
        )

        self.assertFalse(proof["ok"])
        self.assertEqual(proof["computed_enabled_popcount"], 0)
        self.assertFalse(proof["checks"]["enabled_popcount_reasonable"])
        self.assertFalse(proof["checks"]["always_on_feature_baseline"])

    def test_manifest_proof_rejects_noncanonical_script_key_order(self) -> None:
        changed = _query_result(1)
        changed["loaded_feature_manifest"]["script_dlc_keys"]["keys"] = [
            "éclair",
            "DLC A",
            "Zeta",
        ]

        proof = HARNESS._manifest_proof(
            changed,
            expected_native_revision=NATIVE_REVISION,
            expected_date_raw=DATE_RAW,
        )

        self.assertFalse(proof["ok"])
        self.assertFalse(
            proof["checks"]["script_dlc_keys_unsigned_bytewise_sorted"]
        )

    def test_manifest_proof_rejects_entitlement_inference(self) -> None:
        changed = _query_result(1)
        changed["loaded_feature_manifest"]["entitlements"] = {
            "status": "available",
            "unavailable_reason": None,
            "items": [],
        }

        proof = HARNESS._manifest_proof(
            changed,
            expected_native_revision=NATIVE_REVISION,
            expected_date_raw=DATE_RAW,
        )

        self.assertFalse(proof["ok"])
        self.assertFalse(
            proof["checks"]["entitlements_typed_unavailable"]
        )

    def test_manifest_proof_requires_actionable_not_entitlement_ready(
        self,
    ) -> None:
        changed = _query_result(1)
        changed["loaded_feature_manifest"]["readiness"][
            "entitlements_ready"
        ] = True

        proof = HARNESS._manifest_proof(
            changed,
            expected_native_revision=NATIVE_REVISION,
            expected_date_raw=DATE_RAW,
        )

        self.assertFalse(proof["ok"])
        self.assertFalse(proof["checks"]["readiness_exact"])

    def test_adjacent_queries_are_strictly_equal_except_sequence(self) -> None:
        service = _FakeService()

        result = HARNESS._run_double_query_sequence(service)

        self.assertTrue(result["ok"])
        self.assertTrue(
            result["checks"]["adjacent_manifest_frames_strictly_equal"]
        )
        self.assertTrue(result["checks"]["only_query_sequence_changed"])
        self.assertEqual(
            service.calls,
            [
                (
                    HARNESS.QUERY_LOADED_FEATURE_MANIFEST_V1_STEP,
                    PUBLIC_REVISION,
                ),
                (
                    HARNESS.QUERY_LOADED_FEATURE_MANIFEST_V1_STEP,
                    PUBLIC_REVISION,
                ),
            ],
        )

    def test_adjacent_query_rejects_frame_and_envelope_drift(self) -> None:
        changed = _frame()
        changed["effective_feature_flags"]["items"][0]["enabled"] = False
        frame_result = HARNESS._run_double_query_sequence(
            _FakeService(second_frame=changed)
        )
        envelope_result = HARNESS._run_double_query_sequence(
            _FakeService(envelope_drift=True)
        )

        self.assertFalse(frame_result["ok"])
        self.assertFalse(
            frame_result["checks"][
                "adjacent_manifest_frames_strictly_equal"
            ]
        )
        self.assertFalse(envelope_result["ok"])
        self.assertFalse(
            envelope_result["checks"]["only_query_sequence_changed"]
        )

    def test_snapshot_drift_and_non_map_snapshot_are_rejected(self) -> None:
        drifted = HARNESS._run_double_query_sequence(
            _FakeService(snapshot_drift=True)
        )
        self.assertFalse(drifted["ok"])
        self.assertFalse(
            drifted["checks"]["between_same_paused_binding"]
        )
        with self.assertRaisesRegex(RuntimeError, "map-ready"):
            HARNESS._run_double_query_sequence(
                _FakeService(map_ready=False)
            )

    def test_capability_and_same_process_proofs_are_explicit(self) -> None:
        capabilities = _capabilities()
        capability = HARNESS._capability_proof(capabilities)
        same_process = HARNESS._same_process_proof(
            capabilities, copy.deepcopy(capabilities)
        )

        self.assertTrue(capability["ok"])
        self.assertTrue(same_process["ok"])
        self.assertFalse(HARNESS._capability_proof(_capabilities(
            include_query=False
        ))["ok"])

    def test_exact_binary_proof_binds_both_exe_and_dll_hashes(self) -> None:
        expected_dll = "A" * 64
        proof = HARNESS._exact_binary_proof(
            _capabilities(),
            managed_executable_sha256=(
                HARNESS.LOADED_FEATURE_MANIFEST_V1_EXECUTABLE_SHA256
            ),
            production_dll_sha256=expected_dll,
            expected_production_dll_sha256=expected_dll,
        )
        wrong = HARNESS._exact_binary_proof(
            _capabilities(),
            managed_executable_sha256=(
                HARNESS.LOADED_FEATURE_MANIFEST_V1_EXECUTABLE_SHA256
            ),
            production_dll_sha256="B" * 64,
            expected_production_dll_sha256=expected_dll,
        )

        self.assertTrue(proof["ok"])
        self.assertFalse(wrong["ok"])
        self.assertFalse(wrong["checks"]["production_dll_sha256"])

    def test_source_save_resolution_is_hash_bound_and_contained(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            profile = root / "profile"
            save = profile / "save games" / "source.ck3"
            save.parent.mkdir(parents=True)
            save.write_bytes(b"immutable-loaded-feature-source")
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

    def test_cleanup_requires_matching_nonce_and_managed_cleanup(self) -> None:
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

    def test_sha_parser_rejects_noncanonical_length(self) -> None:
        self.assertEqual(
            HARNESS._canonical_sha256("a" * 64, "fixture"), "A" * 64
        )
        with self.assertRaisesRegex(ValueError, "64 hex digits"):
            HARNESS._canonical_sha256("not-a-hash", "fixture")


if __name__ == "__main__":
    unittest.main()
