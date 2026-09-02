#!/usr/bin/env python3

from __future__ import annotations

import copy
import importlib.util
from importlib.machinery import ModuleSpec
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))


def _install_optional_desktop_import_stubs() -> None:
    attributes = {
        "pyautogui": (
            "FAILSAFE",
            "press",
            "hotkey",
            "moveTo",
            "click",
            "mouseDown",
            "mouseUp",
            "size",
        ),
        "numpy": (),
        "cv2": (),
        "win32api": ("GetKeyboardLayoutList",),
        "win32con": (),
        "win32gui": ("GetForegroundWindow", "GetWindowText"),
        "win32process": ("GetWindowThreadProcessId",),
    }
    for name, names in attributes.items():
        if name in sys.modules:
            module = sys.modules[name]
            if getattr(module, "__spec__", None) is None:
                module.__spec__ = ModuleSpec(name, loader=None)
            continue
        if importlib.util.find_spec(name) is None:
            module = types.ModuleType(name)
            module.__spec__ = ModuleSpec(name, loader=None)
            for attribute in names:
                setattr(module, attribute, None)
            sys.modules[name] = module


_install_optional_desktop_import_stubs()

import run_zhongguo_acceptance as phase2  # noqa: E402
import zg361_phase2_loaded_seed_live as live  # noqa: E402


def _ready_contract(root: Path) -> Path:
    contract = json.loads(
        phase2.PHASE2_SEED_CONTRACT_PATH.read_text(encoding="utf-8")
    )
    contract["status"] = "ready"
    contract["ready"] = True
    contract["blocker"] = ""
    contract["domain_query_matrix"].update(
        {
            "b2_pip_owner_character_id": 31001,
            "incident_owner_character_id": 31002,
            "workforce_owner_character_id": 31003,
            "ai_owned_case_owner_character_id": 31004,
            "ai_owned_case_subject_character_id": 31005,
        }
    )
    path = root / "canonical-seed.json"
    path.write_text(
        json.dumps(contract, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


def _snapshot(*, revision: int = 10) -> dict[str, object]:
    return {
        "snapshot_id": f"phase2-live:{revision}",
        "revision": revision,
        "native_revision": 110,
        "date_raw": 53147016,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": 29037, "alive": True},
        "diagnostics": {"bridge_pid": 4321, "connection_generation": 4},
    }


def _manifest(snapshot: dict[str, object]) -> dict[str, object]:
    return {
        "status": "available",
        "loaded_feature_manifest_ready": True,
        "binding": {
            "snapshot_id": snapshot["snapshot_id"],
            "revision": snapshot["revision"],
            "native_revision": snapshot["native_revision"],
            "date_raw": snapshot["date_raw"],
        },
        "effective_feature_flags": {
            "status": "available",
            "items": [
                {"key": "all_under_heaven", "enabled": True},
                {"key": "merit_admin", "enabled": True},
            ],
        },
        "script_dlc_keys": {
            "status": "available",
            "keys": ["All Under Heaven"],
        },
    }


class _ExistingService:
    def __init__(self, *, change_after_query: bool = False) -> None:
        self.calls: list[tuple[object, ...]] = []
        self.change_after_query = change_after_query
        self.queried = False

    def snapshot(self) -> dict[str, object]:
        revision = 11 if self.queried and self.change_after_query else 10
        value = _snapshot(revision=revision)
        self.calls.append(("snapshot", revision))
        return value

    def query_loaded_feature_manifest_v1(
        self, *, expected_revision: int
    ) -> dict[str, object]:
        self.calls.append(("manifest", expected_revision))
        value = _manifest(_snapshot())
        self.queried = True
        return value


class LoadedSeedLiveWrapperTests(unittest.TestCase):
    def test_plan_only_is_ready_but_waits_for_current_canonical_seed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "plan.json"
            exit_code = live.main(
                [
                    "--plan-only",
                    "--seed-contract",
                    str(phase2.PHASE2_SEED_CONTRACT_PATH),
                    "--output",
                    str(output),
                ]
            )
            plan = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 0)
        self.assertEqual(plan["result"], "GREEN")
        self.assertTrue(plan["ready_to_run"])
        self.assertFalse(plan["current_seed_ready"])
        self.assertEqual(plan["execution_state"], "WAITING_CANONICAL_SEED")
        self.assertTrue(plan["same_session_continuation"])
        self.assertFalse(plan["live_executed"])
        self.assertFalse(plan["provider_live_proof_claimed"])
        self.assertIn("launch CK3", plan["forbidden_operations"])
        self.assertIn("run any phase-two span handler", plan["forbidden_operations"])

    def test_existing_session_proves_eight_rows_without_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract_path = _ready_contract(root)
            service = _ExistingService()
            report = live.run_existing_session_loaded_seed_v2(
                service,
                seed_contract_path=contract_path,
                artifacts=root / "artifacts",
                tracked_ck3_pid=4321,
            )
        self.assertEqual(service.calls, [("snapshot", 10), ("manifest", 10), ("snapshot", 10)])
        self.assertEqual(report["result"], "GREEN")
        self.assertTrue(report["eight_row_loaded_proof_green"])
        self.assertEqual(report["span_actions_executed"], [])
        self.assertFalse(report["recorder_started"])
        self.assertFalse(report["provider_live_proof_claimed"])
        self.assertTrue(report["same_session_continuation_authorized"])
        rows = report["loaded_seed_proof"]["span_requirements"]
        self.assertEqual(len(rows), 8)
        self.assertTrue(all(row["provider_ready_claimed"] is False for row in rows))

    def test_changed_frame_is_typed_red_before_loaded_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract_path = _ready_contract(root)
            service = _ExistingService(change_after_query=True)
            with self.assertRaises(live.LoadedSeedLiveError) as raised:
                live.run_existing_session_loaded_seed_v2(
                    service,
                    seed_contract_path=contract_path,
                    artifacts=root / "artifacts",
                    tracked_ck3_pid=4321,
                )
            persisted = json.loads(
                (root / "artifacts" / live.REPORT_NAME).read_text(
                    encoding="utf-8"
                )
            )
        self.assertEqual(raised.exception.reason_code, "state_changed_after_manifest")
        self.assertEqual(persisted["result"], "RED")
        self.assertFalse(persisted["same_session_continuation_authorized"])
        self.assertEqual(persisted["span_actions_executed"], [])

    def test_blocked_seed_never_touches_existing_service(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = _ExistingService()
            with self.assertRaises(live.LoadedSeedLiveError) as raised:
                live.run_existing_session_loaded_seed_v2(
                    service,
                    seed_contract_path=phase2.PHASE2_SEED_CONTRACT_PATH,
                    artifacts=Path(temporary),
                    tracked_ck3_pid=4321,
                )
        self.assertEqual(raised.exception.reason_code, "canonical_seed_not_ready")
        self.assertEqual(service.calls, [])


if __name__ == "__main__":
    unittest.main()
