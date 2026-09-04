#!/usr/bin/env python3

from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from zg361_phase2_cross_cycle_endgame_action_cell import (  # noqa: E402
    EndgameResultBinding,
    PRODUCTION_SUBJECT_TRANSITION_MODE,
)
from zg361_phase2_cross_cycle_endgame_switch_ui import (  # noqa: E402
    ProductSwitchCharacterError,
    TITLE_NAVIGATION_CAPABILITY,
    _REQUIRED_UI_SOURCES,
    preflight_switch_character_ui_source,
    produce_product_subject_checkpoint_session,
)
from zg361_phase2_cross_cycle_endgame_switch_ui_desktop import (  # noqa: E402
    DesktopSwitchCharacterUiDriver,
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


class _Service:
    def __init__(self, checkpoint_path: Path) -> None:
        self.checkpoint_path = checkpoint_path
        self.player = 10
        self.active_event = {"instance_id": 361, "option_count": 3}
        self.revision = 7
        self.native_revision = 70
        self.pid = 4242
        self.generation = 5
        self.date_raw = 39000

    def snapshot(self):
        return {
            "snapshot_id": f"snap-{self.revision}-{self.player}",
            "revision": self.revision,
            "native_revision": self.native_revision,
            "date_raw": self.date_raw,
            "episode_run_id": "managed-product-episode",
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": self.player},
            "active_event": self.active_event,
            "diagnostics": {
                "bridge_pid": self.pid,
                "connection_generation": self.generation,
            },
        }

    def capabilities(self):
        return {"bridge_capabilities": [TITLE_NAVIGATION_CAPABILITY]}

    def query_current_event_window_context_v1(
        self, event_instance_id, *, expected_revision
    ):
        assert event_instance_id == 361
        assert expected_revision == self.revision
        return {
            "status": "available",
            "current_event_window_context": {
                "status": "available",
                "event_definition_key": "zg361we.361",
                "current_event_instance_id": 361,
                "snapshot_revision": self.native_revision,
                "date_raw": self.date_raw,
                "options": [
                    {
                        "native_option_index": index,
                        "shown": True,
                        "enabled": True,
                    }
                    for index in range(3)
                ],
            },
        }

    def center_map_on_landed_title_v1(self, title_key, *, expected_revision):
        assert expected_revision == self.revision
        return {
            "accepted": True,
            "status": "centered",
            "title": {
                "key": title_key,
                "anchor_kind": "title_bounds_center",
            },
            "binding": {
                "date_raw": self.date_raw,
                "episode_run_id": "managed-product-episode",
                "connection_generation": self.generation,
            },
            "camera_center": {
                "postcondition_verified": True,
                "settled": True,
            },
        }

    def select_event_option(
        self, option_number, *, event_instance_id=None, expected_revision=None
    ):
        assert option_number == 1
        assert event_instance_id == 361
        assert expected_revision == self.revision
        self.active_event = None
        self.revision += 1
        self.native_revision += 1
        return {"accepted": True, "status": "submitted"}

    def save_checkpoint(self, *, expected_revision=None):
        assert expected_revision == self.revision
        data = b"real product played-subject checkpoint"
        self.checkpoint_path.write_bytes(data)
        return {
            "accepted": True,
            "checkpoint": {
                "status": "saved",
                "path": str(self.checkpoint_path.resolve()),
                "size": len(data),
                "sha256": _sha(data),
            },
        }

    def query_zhongguo_workforce_collective_snapshot_v1(self, *args, **kwargs):
        raise AssertionError("the strict binder must not query providers")

    def query_zhongguo_ai_owned_case_snapshot_v1(self, *args, **kwargs):
        raise AssertionError("the strict binder must not query providers")


class _Ui:
    def __init__(self, service: _Service, *, generic: bool = False) -> None:
        self.service = service
        self.generic = generic

    def switch_to_centered_title(self, *, expected_ck3_pid, evidence_directory):
        self.service.player = 20
        self.service.revision += 1
        self.service.native_revision += 1
        return {
            "result": "GREEN",
            "transition_mode": PRODUCTION_SUBJECT_TRANSITION_MODE,
            "expected_ck3_pid": expected_ck3_pid,
            "official_ui_switch_submitted": True,
            "native_title_center_click": True,
            "caller_coordinate_used": False,
            "fixture_used": False,
            "console_used": False,
            "generic_character_rebind_used": self.generic,
            "business_postcondition_observed": False,
        }


class ProductSwitchCharacterTests(unittest.TestCase):
    def _result(self, sha: str) -> EndgameResultBinding:
        return EndgameResultBinding(
            owner_character_id=10,
            subject_character_id=20,
            result_event_instance_id=361,
            result_revision=7,
            result_native_revision=70,
            result_date_raw=39000,
            result_checkpoint_sha256=sha,
            save_lineage_id="seed-lineage-1",
        )

    def test_product_ui_switch_materializes_strict_child_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            owner_data = b"real owner-visible zg361we.361 checkpoint"
            owner_path = root / "owner-live.ck3"
            owner_path.write_bytes(owner_data)
            service = _Service(root / "service-current.ck3")
            session = produce_product_subject_checkpoint_session(
                service,
                result=self._result(_sha(owner_data)),
                owner_result_checkpoint={
                    "path": str(owner_path.resolve()),
                    "bytes": len(owner_data),
                    "sha256": _sha(owner_data),
                },
                subject_title_key="k_hedong",
                ui=_Ui(service),
                evidence_directory=root / "evidence",
                expected_ck3_pid=4242,
                timeout_seconds=0.2,
                poll_interval_seconds=0,
            )

            receipt = session.transition_receipt
            self.assertEqual(receipt["result"], "GREEN")
            self.assertEqual(
                receipt["transition_mode"], PRODUCTION_SUBJECT_TRANSITION_MODE
            )
            self.assertEqual(receipt["from_player_character_id"], 10)
            self.assertEqual(receipt["to_player_character_id"], 20)
            self.assertTrue(receipt["official_ui_switch_observed"])
            self.assertFalse(receipt["fixture_used"])
            self.assertFalse(receipt["console_used"])
            self.assertFalse(receipt["generic_character_rebind_used"])
            child = Path(receipt["subject_checkpoint"]["path"])
            self.assertTrue(child.is_file())
            self.assertEqual(_sha(child.read_bytes()), receipt["subject_checkpoint_sha256"])
            self.assertTrue(
                (root / "evidence" / "owner-result-zg361we-361.ck3").is_file()
            )
            self.assertTrue(
                (root / "evidence" / "product-subject-checkpoint-receipt.json").is_file()
            )

    def test_generic_rebind_ui_receipt_is_typed_red_before_child_save(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            owner_data = b"owner checkpoint"
            owner_path = root / "owner.ck3"
            owner_path.write_bytes(owner_data)
            service = _Service(root / "service-current.ck3")
            with self.assertRaises(ProductSwitchCharacterError) as raised:
                produce_product_subject_checkpoint_session(
                    service,
                    result=self._result(_sha(owner_data)),
                    owner_result_checkpoint={
                        "path": str(owner_path.resolve()),
                        "bytes": len(owner_data),
                        "sha256": _sha(owner_data),
                    },
                    subject_title_key="k_hedong",
                    ui=_Ui(service, generic=True),
                    evidence_directory=root / "evidence",
                    expected_ck3_pid=4242,
                    timeout_seconds=0.2,
                    poll_interval_seconds=0,
                )
            self.assertEqual(
                raised.exception.reason_code,
                "official_switch_ui_receipt_invalid",
            )
            self.assertFalse((root / "service-current.ck3").exists())

    def test_no_launch_preflight_reads_only_exact_ui_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative, snippets in _REQUIRED_UI_SOURCES.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("\n".join(snippets), encoding="utf-8")
            evidence = preflight_switch_character_ui_source(root)
            self.assertEqual(evidence["result"], "GREEN")
            self.assertEqual(
                evidence["readiness"], "static-ready-live-pending"
            )
            self.assertFalse(evidence["ck3_launched"])
            self.assertFalse(evidence["live_executed"])
            self.assertFalse(evidence["caller_coordinates_allowed"])

    def test_desktop_driver_uses_semantic_shortcuts_and_client_center(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)

            class Image:
                def save(self, path):
                    Path(path).write_bytes(b"screen")

            class Gui:
                @staticmethod
                def GetForegroundWindow():
                    return 99

                @staticmethod
                def GetWindowText(_hwnd):
                    return "Crusader Kings III"

                @staticmethod
                def GetClientRect(_hwnd):
                    return (0, 0, 1600, 900)

                @staticmethod
                def ClientToScreen(_hwnd, point):
                    return (point[0] + 50, point[1] + 25)

            class Process:
                @staticmethod
                def GetWindowThreadProcessId(_hwnd):
                    return (1, 4242)

            class PyAuto:
                def __init__(self, outer):
                    self.outer = outer

                def press(self, key):
                    self.outer.keys.append(key)
                    self.outer.stage = {
                        "escape": "pause",
                        "3": "any",
                        "tab": "map",
                        "enter": "complete",
                    }[key]

            class Desktop:
                def __init__(self):
                    self.stage = "gameplay"
                    self.keys = []
                    self.clicks = []
                    self.win32gui = Gui()
                    self.win32process = Process()
                    self.pyautogui = PyAuto(self)
                    self.ImageGrab = self

                @staticmethod
                def focus_ck3():
                    return True

                @staticmethod
                def grab():
                    return Image()

                def ocr_box_results(self, _image, _region):
                    text = {
                        "pause": "Switch Character",
                        "any": "Play as any Ruler in 1066",
                        "map": "Choose a Character on the Map.",
                    }.get(self.stage)
                    return [{"text": text}] if text is not None else []

                def deliberate_click(self, point, label):
                    self.clicks.append((point, label))
                    self.stage = "selected"

            desktop = Desktop()
            driver = DesktopSwitchCharacterUiDriver(
                desktop, timeout_seconds=0.2, poll_interval_seconds=0
            )
            receipt = driver.switch_to_centered_title(
                expected_ck3_pid=4242,
                evidence_directory=root,
            )
            self.assertEqual(desktop.keys, ["escape", "3", "tab", "enter"])
            self.assertEqual(desktop.clicks[0][0], (850, 475))
            self.assertEqual(receipt["result"], "GREEN")
            self.assertTrue(receipt["native_title_center_click"])
            self.assertTrue(receipt["action_ack_only"])
            self.assertFalse(receipt["business_postcondition_observed"])
            self.assertFalse(receipt["caller_coordinate_used"])


if __name__ == "__main__":
    unittest.main()
