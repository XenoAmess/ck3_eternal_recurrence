from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ck3_workshop_mcp import steam_native


class FakeSteamClient:
    def __init__(
        self,
        *,
        create_result: steam_native._CreateResult | None = None,
        submit_result: steam_native._SubmitResult | None = None,
        create_error: steam_native.SteamNativeError | None = None,
        submit_error: steam_native.SteamNativeError | None = None,
    ) -> None:
        self.create_result = create_result or steam_native._CreateResult(1, 9_000_000_001, False)
        self.submit_result = submit_result or steam_native._SubmitResult(1, False)
        self.create_error = create_error
        self.submit_error = submit_error
        self.create_calls = 0
        self.submit_calls = 0
        self.fields: list[tuple[str, object]] = []

    def __enter__(self) -> "FakeSteamClient":
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def logged_on(self) -> bool:
        return True

    def create_item(self, app_id: int) -> steam_native._CreateResult:
        self.create_calls += 1
        self.fields.append(("app_id", app_id))
        if self.create_error:
            raise self.create_error
        return self.create_result

    def start_item_update(self, app_id: int, item_id: int) -> int:
        self.fields.extend((("update_app_id", app_id), ("item_id", item_id)))
        return 123

    def set_title(self, handle: int, value: str) -> bool:
        self.fields.append(("title", value))
        return handle == 123

    def set_description(self, handle: int, value: str) -> bool:
        self.fields.append(("description", value))
        return handle == 123

    def set_content(self, handle: int, value: Path) -> bool:
        self.fields.append(("content", value))
        return handle == 123

    def set_preview(self, handle: int, value: Path) -> bool:
        self.fields.append(("preview", value))
        return handle == 123

    def set_visibility(self, handle: int, value: int) -> bool:
        self.fields.append(("visibility", value))
        return handle == 123

    def set_tags(self, handle: int, value: tuple[str, ...]) -> bool:
        self.fields.append(("tags", value))
        return handle == 123

    def submit_item_update(self, handle: int, change_note: str | None) -> steam_native._SubmitResult:
        self.submit_calls += 1
        self.fields.append(("change_note", change_note))
        if self.submit_error:
            raise self.submit_error
        return self.submit_result


class SteamNativeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.content = self.root / "staging"
        self.content.mkdir()
        (self.content / "descriptor.mod").write_text(
            'name="Fixture"\nsupported_version="1.20.0.3"\n', encoding="utf-8"
        )
        self.preview = self.content / "thumbnail.png"
        self.preview.write_bytes(b"fake-png")
        self.description = self.root / "description.bbcode"
        self.description.write_text("[h1]Fixture[/h1]\n", encoding="utf-8")
        self.plan_file = self.root / "plan.json"
        self.receipt_file = self.root / "receipt.json"
        self.plan = {
            "operation_id": "fixture-create-01",
            "operation": "create",
            "app_id": 1_158_310,
            "target_item_id": None,
            "title": "Fixture maintained edition",
            "description_path": str(self.description),
            "content_path": str(self.content),
            "preview_path": str(self.preview),
            "visibility": "public",
            "tags": ["Balance"],
            "change_note": "Initial release",
            "workshop_legal_agreement_accepted": False,
        }
        self._write_plan()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_plan(self) -> None:
        self.plan_file.write_text(
            json.dumps(self.plan, ensure_ascii=False), encoding="utf-8"
        )

    def _publish(self, client: FakeSteamClient) -> dict[str, object]:
        with patch.object(steam_native, "_open_client", return_value=client):
            return steam_native.publish("unused.dll", self.plan_file, self.receipt_file)

    def test_callback_abi_and_accessor_selection(self) -> None:
        self.assertEqual(24, steam_native.ctypes.sizeof(steam_native.CreateItemResult))
        self.assertEqual(8, steam_native.ctypes.sizeof(steam_native.SubmitItemUpdateResult))
        self.assertEqual(
            {
                "ugc": "SteamAPI_SteamUGC_v016",
                "utils": "SteamAPI_SteamUtils_v010",
                "user": "SteamAPI_SteamUser_v021",
            },
            steam_native._select_accessors(
                [
                    "SteamAPI_SteamUGC_v015",
                    "SteamAPI_SteamUGC_v016",
                    "SteamAPI_SteamUtils_v010",
                    "SteamAPI_SteamUser_v021",
                ]
            ),
        )

    def test_create_records_item_and_completed_receipt_prevents_duplicate(self) -> None:
        client = FakeSteamClient()
        result = self._publish(client)
        self.assertTrue(result["ok"])
        self.assertEqual("9000000001", result["item_id"])
        self.assertEqual(1, client.create_calls)
        self.assertEqual(1, client.submit_calls)
        receipt = json.loads(self.receipt_file.read_text(encoding="utf-8"))
        self.assertEqual("complete", receipt["stage"])
        self.assertEqual("9000000001", receipt["item_id"])

        never_opened = FakeSteamClient()
        replay = self._publish(never_opened)
        self.assertTrue(replay["replayed_receipt"])
        self.assertEqual(0, never_opened.create_calls)
        self.assertEqual(0, never_opened.submit_calls)

    def test_unknown_create_is_not_retried(self) -> None:
        first = FakeSteamClient(
            create_error=steam_native.SteamNativeError(
                "API_CALL_RESULT_UNKNOWN", "lost callback"
            )
        )
        with self.assertRaisesRegex(steam_native.SteamNativeError, "lost callback"):
            self._publish(first)
        self.assertEqual("create_intent", json.loads(self.receipt_file.read_text())["stage"])

        second = FakeSteamClient()
        with self.assertRaises(steam_native.SteamNativeError) as raised:
            self._publish(second)
        self.assertEqual("UNKNOWN_CREATE_RESULT", raised.exception.code)
        self.assertEqual(0, second.create_calls)

    def test_create_eula_pause_resumes_without_second_create(self) -> None:
        first = FakeSteamClient(
            create_result=steam_native._CreateResult(1, 9_000_000_002, True)
        )
        paused = self._publish(first)
        self.assertEqual("eula_required", paused["status"])
        self.assertFalse(paused["submitted"])
        self.assertEqual(1, first.create_calls)
        self.assertEqual(0, first.submit_calls)

        self.plan["workshop_legal_agreement_accepted"] = True
        self._write_plan()
        second = FakeSteamClient()
        resumed = self._publish(second)
        self.assertTrue(resumed["ok"])
        self.assertEqual("9000000002", resumed["item_id"])
        self.assertEqual(0, second.create_calls)
        self.assertEqual(1, second.submit_calls)

    def test_unknown_submit_is_not_retried(self) -> None:
        first = FakeSteamClient(
            submit_error=steam_native.SteamNativeError(
                "API_CALL_RESULT_UNKNOWN", "lost submit callback"
            )
        )
        with self.assertRaisesRegex(steam_native.SteamNativeError, "lost submit callback"):
            self._publish(first)
        receipt = json.loads(self.receipt_file.read_text(encoding="utf-8"))
        self.assertEqual("submit_intent", receipt["stage"])
        self.assertEqual("9000000001", receipt["item_id"])

        second = FakeSteamClient()
        with self.assertRaises(steam_native.SteamNativeError) as raised:
            self._publish(second)
        self.assertEqual("UNKNOWN_SUBMIT_RESULT", raised.exception.code)
        self.assertEqual(0, second.create_calls)
        self.assertEqual(0, second.submit_calls)

    def test_update_target_change_is_rejected_by_receipt_binding(self) -> None:
        self.plan.update(
            operation_id="fixture-update-01",
            operation="update",
            target_item_id="9000000010",
        )
        self._write_plan()
        self._publish(FakeSteamClient())

        self.plan["target_item_id"] = "9000000011"
        self._write_plan()
        with self.assertRaises(steam_native.SteamNativeError) as raised:
            self._publish(FakeSteamClient())
        self.assertEqual("RECEIPT_PLAN_MISMATCH", raised.exception.code)

    def test_default_update_keeps_content_metadata_and_notes_with_derived_tag(self) -> None:
        self.plan.update(operation="update", target_item_id="9000000010")
        self._write_plan()
        client = FakeSteamClient()
        result = self._publish(client)
        self.assertTrue(result["ok"])
        self.assertEqual(0, client.create_calls)
        self.assertEqual(1, client.submit_calls)
        self.assertEqual(
            ["update_app_id", "item_id", "title", "description", "content", "preview", "visibility", "tags", "change_note"],
            [name for name, value in client.fields],
        )
        self.assertIn(("tags", ("Balance", "1.20 'Crozier'")), client.fields)
        self.assertIn(("change_note", "Initial release"), client.fields)
        self.assertFalse(json.loads(self.receipt_file.read_text())["tags_only"])

    def test_tags_only_updates_complete_tag_list_without_content_or_new_notes(self) -> None:
        self.plan.update(operation="update", target_item_id="9000000010", tags_only=True,
                         tags=["Gameplay", "1.19 'Old fixture'", "Balance"])
        self._write_plan()
        client = FakeSteamClient()
        result = self._publish(client)
        self.assertTrue(result["ok"])
        self.assertEqual(0, client.create_calls)
        self.assertEqual(1, client.submit_calls)
        self.assertEqual(
            [("update_app_id", 1_158_310), ("item_id", 9_000_000_010),
             ("tags", ("Gameplay", "Balance", "1.20 'Crozier'")), ("change_note", None)],
            client.fields,
        )
        receipt = json.loads(self.receipt_file.read_text())
        self.assertTrue(receipt["tags_only"])
        self.assertEqual("compatibility_tags_only", receipt["update_scope"])
        self.assertEqual(["Gameplay", "Balance", "1.20 'Crozier'"], receipt["tags"])

    def test_tags_only_flag_and_final_tag_list_are_bound_in_payload_hash(self) -> None:
        self.plan.update(operation="update", target_item_id="9000000010")
        normal = steam_native._prepare_plan(self.plan)
        self.plan["tags_only"] = True
        tags_only = steam_native._prepare_plan(self.plan)
        self.assertNotEqual(normal.payload_sha256, tags_only.payload_sha256)
        self.plan["tags"] = ["Balance", "Events"]
        other_tags = steam_native._prepare_plan(self.plan)
        self.assertNotEqual(tags_only.payload_sha256, other_tags.payload_sha256)
        self.assertEqual(("Balance", "Events", "1.20 'Crozier'"), other_tags.tags)

    def test_tags_only_rejects_create_or_preview_changes_before_client_open(self) -> None:
        self.plan["tags_only"] = True
        with patch.object(steam_native, "_open_client") as opened:
            self._write_plan()
            with self.assertRaisesRegex(steam_native.SteamNativeError, "requires an update"):
                steam_native.publish("unused.dll", self.plan_file, self.receipt_file)
            self.plan.update(operation="update", target_item_id="9000000010")
            for field in ("additional_preview_files", "update_preview_files", "remove_preview_indices"):
                self.plan[field] = [0]
                self._write_plan()
                with self.assertRaisesRegex(steam_native.SteamNativeError, "cannot change additional previews"):
                    steam_native.publish("unused.dll", self.plan_file, self.receipt_file)
                del self.plan[field]
            opened.assert_not_called()

    def test_unknown_staging_minor_rejected_before_any_SDK_client(self) -> None:
        (self.content / "descriptor.mod").write_text('supported_version="1.21.0"\n', encoding="utf-8")
        with patch.object(steam_native, "_open_client") as opened:
            with self.assertRaisesRegex(steam_native.SteamNativeError, "no confirmed"):
                steam_native.publish("unused.dll", self.plan_file, self.receipt_file)
            opened.assert_not_called()
        self.assertFalse(self.receipt_file.exists())

    def test_legacy_119_actual_provider_keeps_original_tags_content_and_notes(self) -> None:
        (self.content / "descriptor.mod").write_text('supported_version="1.19.0.6"\n', encoding="utf-8")
        self.plan.update(operation="update", target_item_id="9000000010",
                         tags=["Balance", "1.19 'Prior fixture'"])
        self._write_plan()
        client = FakeSteamClient()
        self.assertTrue(self._publish(client)["ok"])
        self.assertIn(("tags", ("Balance", "1.19 'Prior fixture'")), client.fields)
        self.assertIn(("content", self.content), client.fields)
        self.assertIn(("change_note", "Initial release"), client.fields)
        self.assertEqual(1, client.submit_calls)
        self.assertFalse(json.loads(self.receipt_file.read_text())["tags_only"])

    def test_submit_nullable_change_note_passes_c_char_p_NULL(self) -> None:
        observed = []
        client = object.__new__(steam_native._NativeClient)
        client.ugc = steam_native.ctypes.c_void_p(1)
        signature = steam_native.ctypes.CFUNCTYPE(
            steam_native.ctypes.c_uint64, steam_native.ctypes.c_void_p,
            steam_native.ctypes.c_uint64, steam_native.ctypes.c_char_p,
        )

        def submit(_ugc, _handle, note):
            observed.append(note)
            return 123

        client._submit = signature(submit)
        client._wait_for_result = lambda *_args: steam_native.SubmitItemUpdateResult(1, False)
        self.assertEqual(1, client.submit_item_update(123, None).result)
        self.assertEqual(1, client.submit_item_update(123, "Original note").result)
        self.assertEqual([None, b"Original note"], observed)


if __name__ == "__main__":
    unittest.main()
