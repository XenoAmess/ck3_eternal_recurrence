from __future__ import annotations

import ctypes
import hashlib
import json
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from ck3_workshop_mcp import steam_native as native
from tests.test_steam_native import FakeSteamClient


def snapshot(count: int = 4) -> dict[str, object]:
    return {
        "item_id": "3182367229", "app_id": 1158310,
        "previews": [
            {"index": index, "type": 0, "url": f"https://example.test/{index}.jpg",
             "original_filename": f"old-{index}.jpg"}
            for index in range(count)
        ],
    }


class PreviewClient(FakeSteamClient):
    def __init__(self, *, current: dict[str, object] | None = None, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.current = current or snapshot()
        self.query_calls = 0
        self.fail_setter: str | None = None

    def additional_previews(self, item_id: int) -> list[dict[str, object]]:
        self.query_calls += 1
        self.fields.append(("query_item_id", item_id))
        return self.current["previews"]

    def update_preview_file(self, handle: int, index: int, value: Path) -> bool:
        self.fields.append(("update_preview", (index, value.name)))
        return self.fail_setter != "update"

    def remove_preview(self, handle: int, index: int) -> bool:
        self.fields.append(("remove_preview", index))
        return self.fail_setter != "remove"

    def add_preview_file(self, handle: int, value: Path) -> bool:
        self.fields.append(("add_preview", value.name))
        return self.fail_setter != "add"


class NativePreviewPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.stage = self.root / "staging"
        self.stage.mkdir()
        (self.stage / "descriptor.mod").write_text('name="Fixture"\n', encoding="utf-8")
        self.files = []
        for index in range(3):
            path = self.root / f"new-{index}.png"
            path.write_bytes(b"\x89PNG\r\n\x1a\n" + bytes([index]) * 64)
            self.files.append({"path": str(path), "size": path.stat().st_size,
                               "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        self.plan = {
            "operation_id": "fixture-media-update", "operation": "update", "app_id": 1158310,
            "target_item_id": "3182367229", "title": "Fixture", "description": "Fixture",
            "content_path": str(self.stage), "visibility": "public", "change_note": "New images",
            "expected_additional_previews": snapshot(),
            "update_preview_files": [dict(self.files[0], index=0)],
            "remove_preview_indices": [1, 3], "additional_preview_files": self.files[1:],
        }
        self.plan_file = self.root / "plan.json"
        self.receipt = self.root / "receipt.json"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def publish(self, client: PreviewClient) -> dict[str, object]:
        self.plan_file.write_text(json.dumps(self.plan), encoding="utf-8")
        with patch.object(native, "_open_client", return_value=client):
            return native.publish("unused.dll", self.plan_file, self.receipt)

    def test_update_replaces_then_removes_descending_then_appends_without_create(self) -> None:
        client = PreviewClient()
        result = self.publish(client)
        self.assertTrue(result["ok"])
        self.assertEqual("3182367229", result["item_id"])
        self.assertEqual(0, client.create_calls)
        changes = [entry for entry in client.fields if entry[0] in {"update_preview", "remove_preview", "add_preview"}]
        self.assertEqual([
            ("update_preview", (0, "new-0.png")), ("remove_preview", 3),
            ("remove_preview", 1), ("add_preview", "new-1.png"), ("add_preview", "new-2.png"),
        ], changes)
        self.assertEqual(("query_item_id", 3182367229), client.fields[0])
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertEqual(snapshot(), receipt["additional_previews_before"])
        self.assertEqual([3, 1], receipt["additional_preview_changes"]["remove_indices"])

    def test_public_preview_drift_stops_before_start_or_submit(self) -> None:
        changed = snapshot()
        changed["previews"][0]["url"] = "https://example.test/concurrent.jpg"
        client = PreviewClient(current=changed)
        with self.assertRaises(native.SteamNativeError) as raised:
            self.publish(client)
        self.assertEqual("PREVIEW_SNAPSHOT_MISMATCH", raised.exception.code)
        self.assertFalse(any(name == "item_id" for name, _ in client.fields))
        self.assertEqual(0, client.submit_calls)

    def test_rejected_media_setter_never_submits(self) -> None:
        for field in ("update", "remove", "add"):
            with self.subTest(field=field):
                client = PreviewClient()
                client.fail_setter = field
                with self.assertRaises(native.SteamNativeError) as raised:
                    self.publish(client)
                self.assertEqual("SET_ITEM_FIELD_FAILED", raised.exception.code)
                self.assertEqual(0, client.submit_calls)

    def test_unknown_media_submit_is_not_retried_or_requeried(self) -> None:
        first = PreviewClient(submit_error=native.SteamNativeError("API_CALL_RESULT_UNKNOWN", "lost callback"))
        with self.assertRaisesRegex(native.SteamNativeError, "lost callback"):
            self.publish(first)
        second = PreviewClient()
        with self.assertRaises(native.SteamNativeError) as raised:
            self.publish(second)
        self.assertEqual("UNKNOWN_SUBMIT_RESULT", raised.exception.code)
        self.assertEqual(0, second.query_calls)
        self.assertEqual(0, second.create_calls)
        self.assertEqual(0, second.submit_calls)

    def test_changed_file_is_rejected_before_loading_steam(self) -> None:
        Path(self.files[1]["path"]).write_bytes(b"\x89PNG\r\n\x1a\n" + b"different" * 8)
        self.plan_file.write_text(json.dumps(self.plan), encoding="utf-8")
        with patch.object(native, "_open_client") as opened:
            with self.assertRaises(native.SteamNativeError) as raised:
                native.publish("unused.dll", self.plan_file, self.receipt)
            self.assertEqual("PREVIEW_FILE_MISMATCH", raised.exception.code)
            opened.assert_not_called()

    def test_new_frozen_media_payload_cannot_reuse_completed_receipt(self) -> None:
        self.publish(PreviewClient())
        self.plan["additional_preview_files"] = list(reversed(self.files[1:]))
        with self.assertRaises(native.SteamNativeError) as raised:
            self.publish(PreviewClient())
        self.assertEqual("RECEIPT_PLAN_MISMATCH", raised.exception.code)

    def test_invalid_target_indices_or_create_are_rejected(self) -> None:
        changes = [
            {"target_item_id": "3182367230"},
            {"expected_additional_previews": None},
            {"remove_preview_indices": [True]},
            {"remove_preview_indices": [-1]},
            {"remove_preview_indices": [4]},
            {"remove_preview_indices": [1, 1]},
            {"remove_preview_indices": [0]},
            {"operation": "create", "target_item_id": None},
        ]
        for change in changes:
            with self.subTest(change=change):
                with self.assertRaises(native.SteamNativeError):
                    native._prepare_plan(dict(self.plan, **change))

    def test_native_image_limit_and_frozen_hash_are_required(self) -> None:
        for change in [{"size": 1048576}, {"size": 0}, {"sha256": "missing"}, {"path": "relative.png"}]:
            with self.subTest(change=change):
                with self.assertRaises(native.SteamNativeError):
                    native._prepare_plan(dict(self.plan, additional_preview_files=[dict(self.files[1], **change)]))
        wrong_format = self.root / "fake.jpg"
        wrong_format.write_bytes(b"Not an image" * 8)
        wrong = {"path": str(wrong_format), "size": wrong_format.stat().st_size,
                 "sha256": hashlib.sha256(wrong_format.read_bytes()).hexdigest()}
        with self.assertRaisesRegex(native.SteamNativeError, "PNG, JPEG or GIF"):
            native._prepare_plan(dict(self.plan, additional_preview_files=[wrong]))

    def test_existing_video_cannot_be_replaced_as_image(self) -> None:
        current = snapshot()
        current["previews"][0]["type"] = 1
        with self.assertRaisesRegex(native.SteamNativeError, "existing image"):
            native._prepare_plan(dict(self.plan, expected_additional_previews=current))

    def test_empty_optional_arrays_preserve_legacy_payload_hash(self) -> None:
        old = {key: value for key, value in self.plan.items() if key not in {
            "expected_additional_previews", "additional_preview_files", "update_preview_files", "remove_preview_indices"
        }}
        self.assertEqual(native._prepare_plan(old).payload_sha256, native._prepare_plan(dict(
            old, additional_preview_files=[], update_preview_files=[], remove_preview_indices=[]
        )).payload_sha256)


class NativePreviewQueryTests(unittest.TestCase):
    def client(self, **changes: object) -> native._NativeClient:
        result = native.UGCQueryCompletedResult(handle=77, result=1, num_results_returned=1,
                                                total_matching_results=1, cached_data=False)
        for key, value in changes.items():
            setattr(result, key, value)
        client = native._NativeClient.__new__(native._NativeClient)
        client.ugc = ctypes.c_void_p(55)
        client._wait_for_result = Mock(return_value=result)
        functions = {
            "CreateQueryUGCDetailsRequest": Mock(return_value=77),
            "SetReturnAdditionalPreviews": Mock(return_value=True),
            "SetAllowCachedResponse": Mock(return_value=True),
            "SendQueryUGCRequest": Mock(return_value=999),
            "GetQueryUGCNumAdditionalPreviews": Mock(return_value=1),
            "ReleaseQueryUGCRequest": Mock(return_value=True),
        }

        def get(_ugc: object, _handle: object, _item_index: object, _preview_index: object,
                url: object, _url_size: object, filename: object, _filename_size: object,
                kind: object) -> bool:
            raw_url = b"https://example.test/old.jpg\0"
            ctypes.memmove(url, raw_url, len(raw_url))
            ctypes.memmove(filename, b"old.jpg\0", 8)
            ctypes.cast(kind, ctypes.POINTER(ctypes.c_int32)).contents.value = 0
            return True

        functions["GetQueryUGCAdditionalPreview"] = Mock(side_effect=get)
        client.library = types.SimpleNamespace(**{"SteamAPI_ISteamUGC_" + name: fn for name, fn in functions.items()})
        return client

    def test_query_abi_one_target_ordered_metadata_and_handle_release(self) -> None:
        self.assertEqual(280, ctypes.sizeof(native.UGCQueryCompletedResult))
        self.assertEqual(20, native.UGCQueryCompletedResult.cached_data.offset)
        self.assertEqual(21, native.UGCQueryCompletedResult.next_cursor.offset)
        client = self.client()
        self.assertEqual([{"index": 0, "type": 0, "url": "https://example.test/old.jpg",
                           "original_filename": "old.jpg"}], client.additional_previews(3182367229))
        create_args = client.library.SteamAPI_ISteamUGC_CreateQueryUGCDetailsRequest.call_args.args
        self.assertEqual(3182367229, create_args[1][0])
        self.assertEqual(1, create_args[2])
        client.library.SteamAPI_ISteamUGC_SetAllowCachedResponse.assert_called_once_with(client.ugc, 77, 0)
        client._wait_for_result.assert_called_once_with(999, native.UGCQueryCompletedResult, 3401)
        client.library.SteamAPI_ISteamUGC_ReleaseQueryUGCRequest.assert_called_once_with(client.ugc, 77)

    def test_query_failure_mismatch_cached_data_or_zero_results_always_release(self) -> None:
        for changes in [{"result": 2}, {"handle": 78}, {"num_results_returned": 0}, {"cached_data": True}]:
            with self.subTest(changes=changes):
                client = self.client(**changes)
                with self.assertRaises(native.SteamNativeError) as raised:
                    client.additional_previews(3182367229)
                self.assertEqual("PREVIEW_QUERY_FAILED", raised.exception.code)
                client.library.SteamAPI_ISteamUGC_ReleaseQueryUGCRequest.assert_called_once()

    def test_query_callback_loss_always_releases(self) -> None:
        client = self.client()
        client._wait_for_result.side_effect = native.SteamNativeError("API_CALL_RESULT_UNKNOWN", "timeout")
        with self.assertRaisesRegex(native.SteamNativeError, "timeout"):
            client.additional_previews(3182367229)
        client.library.SteamAPI_ISteamUGC_ReleaseQueryUGCRequest.assert_called_once()


if __name__ == "__main__":
    unittest.main()
