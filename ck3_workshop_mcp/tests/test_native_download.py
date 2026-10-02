from __future__ import annotations

import ctypes
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ck3_workshop_mcp import steam_download as download
from ck3_workshop_mcp import steam_native


APP = 1158310
ITEM = "3182367229"


class FakeApi:
    def __init__(self, cache: Path, *, callbacks=None, started=True, state=4,
                 install=True, actual_path=None):
        self.cache, self.started, self.state = cache, started, state
        self.events = callbacks if callbacks is not None else [
            {"callback_id": 3406, "app_id": APP, "item_id": ITEM, "result": 1}]
        self.install = install
        self.actual_path = actual_path or cache
        self.start_calls = 0
        self.install_calls = 0
        self.got_exact_callback = False

    def start(self, item):
        self.start_calls += 1
        if self.started:
            self.cache.mkdir(exist_ok=True)
        return self.started

    def callbacks(self):
        events, self.events = self.events, []
        for event in events:
            if event and event["app_id"] == APP and event["item_id"] == ITEM:
                self.got_exact_callback = True
            yield event

    def observe(self, item):
        flags = {"raw": self.state, **{name: bool(self.state & bit)
                                     for name, bit in download._STATE_BITS.items()}}
        return flags, {"available": True, "downloaded_bytes": 42, "total_bytes": 42}

    def installation(self, item):
        if not self.got_exact_callback:
            raise AssertionError("GetItemInstallInfo called before exact callback")
        self.install_calls += 1
        return {"path": str(self.actual_path), "size_on_disk": 42, "timestamp": 7} if self.install else None


class NativeDownloadTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.cache = self.root / ITEM
        self.arguments = download._arguments("unused.dll", ITEM, APP, 0.002, self.cache)

    def tearDown(self):
        self.temporary.cleanup()

    def run_api(self, **kwargs):
        api = FakeApi(self.cache, **kwargs)
        return download._run_download(api, self.arguments), api

    def test_win64_callback_abi(self):
        self.assertEqual(24, ctypes.sizeof(download.CallbackMsg))
        self.assertEqual(24, ctypes.sizeof(download.DownloadItemResult))
        self.assertEqual(8, download.CallbackMsg.parameter.offset)
        self.assertEqual(16, download.CallbackMsg.parameter_size.offset)
        self.assertEqual(8, download.DownloadItemResult.item_id.offset)
        self.assertEqual(16, download.DownloadItemResult.result.offset)

    def test_exact_callback_installed_flags_and_actual_path_complete(self):
        result, api = self.run_api(callbacks=[None,
            {"app_id": 99, "item_id": ITEM, "result": 1},
            {"app_id": APP, "item_id": "9", "result": 1},
            {"callback_id": 3406, "app_id": APP, "item_id": ITEM, "result": 1}])
        self.assertTrue(result["ok"])
        self.assertEqual("complete", result["status"])
        self.assertEqual(3, result["ignored_callbacks"])
        self.assertEqual(str(self.cache), result["install_info"]["path"])
        self.assertEqual(1, api.start_calls)
        self.assertEqual(1, api.install_calls)
        self.assertTrue(result["expected_cache_absent_before_start"])

    def test_start_ack_is_not_completion_and_timeout_does_not_retry(self):
        result, api = self.run_api(callbacks=[])
        self.assertFalse(result["ok"])
        self.assertTrue(result["started"])
        self.assertEqual("unknown", result["status"])
        self.assertEqual("DOWNLOAD_TIMEOUT", result["error"]["code"])
        self.assertIsNone(result["install_info"])
        self.assertEqual(1, api.start_calls)
        self.assertEqual(0, api.install_calls)

    def test_rejected_start_and_failed_callback_are_known_failures(self):
        result, api = self.run_api(started=False)
        self.assertEqual("failed", result["status"])
        self.assertEqual("DOWNLOAD_NOT_STARTED", result["error"]["code"])
        self.assertEqual(0, api.install_calls)
        result, api = self.run_api(callbacks=[{"app_id": APP, "item_id": ITEM, "result": 2}])
        self.assertFalse(result["ok"])
        self.assertEqual("failed", result["status"])
        self.assertEqual(2, result["callback"]["result"])
        self.assertEqual(0, api.install_calls)

    def test_installed_bit_does_not_hide_update_or_pending_flags(self):
        for state in (0, 4 | 8, 4 | 16, 4 | 32):
            with self.subTest(state=state):
                if self.cache.exists():
                    self.cache.rmdir()
                result, _ = self.run_api(state=state)
                self.assertFalse(result["ok"])
                self.assertEqual("partial", result["status"])
                self.assertEqual(state, result["state_flags"]["raw"])

    def test_successful_callback_without_install_info_remains_partial(self):
        result, _ = self.run_api(install=False)
        self.assertFalse(result["ok"])
        self.assertEqual("partial", result["status"])
        self.assertIsNone(result["install_info"])

    def test_actual_install_path_must_match_exact_expected_cache(self):
        result, _ = self.run_api(actual_path=self.root / "other")
        self.assertFalse(result["ok"])
        self.assertEqual("partial", result["status"])
        self.assertEqual("INSTALL_PATH_MISMATCH", result["error"]["code"])

    def test_old_cache_refused_without_any_download_or_deletion(self):
        self.cache.mkdir()
        old = self.cache / "old.txt"
        old.write_text("preserve", encoding="utf-8")
        result, api = self.run_api()
        self.assertFalse(result["ok"])
        self.assertEqual("CACHE_ALREADY_EXISTS", result["error"]["code"])
        self.assertEqual(0, api.start_calls)
        self.assertEqual("preserve", old.read_text(encoding="utf-8"))

    def test_manual_dispatch_frees_every_callback_and_copies_before_free(self):
        payload = download.DownloadItemResult(APP, int(ITEM), 1)
        queue = [(123, None), (3406, payload)]
        freed = []

        def next_callback(pipe, message_pointer):
            if not queue:
                return False
            callback_id, data = queue.pop(0)
            message = ctypes.cast(message_pointer, ctypes.POINTER(download.CallbackMsg)).contents
            message.callback_id = callback_id
            message.parameter = ctypes.addressof(data) if data is not None else None
            message.parameter_size = ctypes.sizeof(data) if data is not None else 0
            return True

        def free(pipe):
            freed.append(pipe)
            if len(freed) == 2:
                payload.result = 99

        library = SimpleNamespace(
            SteamAPI_ManualDispatch_Init=lambda: None,
            SteamAPI_GetHSteamPipe=lambda: 7,
            SteamAPI_ManualDispatch_RunFrame=lambda pipe: None,
            SteamAPI_ManualDispatch_GetNextCallback=next_callback,
            SteamAPI_ManualDispatch_FreeLastCallback=free,
            SteamAPI_ISteamUGC_DownloadItem=lambda ugc, item, priority: not priority,
            SteamAPI_ISteamUGC_GetItemState=lambda *a: 4,
            SteamAPI_ISteamUGC_GetItemDownloadInfo=lambda *a: False,
            SteamAPI_ISteamUGC_GetItemInstallInfo=lambda *a: False)
        client = SimpleNamespace(library=library, ugc=123)
        with patch.object(download, "_bind", side_effect=lambda lib, name, *a: getattr(lib, name)):
            api = download._NativeDownloadApi(client)
        events = api.callbacks()
        self.assertIsNone(next(events))
        self.assertEqual([7], freed)
        payload.result = 1
        event = next(events)
        self.assertEqual(1, event["result"])
        self.assertEqual(str(payload.item_id), event["item_id"])
        with self.assertRaises(StopIteration):
            next(events)
        self.assertEqual([7, 7], freed)
        self.assertEqual(1, event["result"])
        self.assertTrue(api.start(int(ITEM)))

    def test_malformed_download_callback_is_freed_and_not_accepted(self):
        api = download._NativeDownloadApi.__new__(download._NativeDownloadApi)
        api.pipe, api._frame = 7, lambda pipe: None
        freed = []
        def next_callback(pipe, pointer):
            message = ctypes.cast(pointer, ctypes.POINTER(download.CallbackMsg)).contents
            message.callback_id = 3406
            message.parameter_size = 1
            message.parameter = None
            return True
        api._next, api._free = next_callback, lambda pipe: freed.append(pipe)
        with self.assertRaises(steam_native.SteamNativeError):
            list(api.callbacks())
        self.assertEqual([7], freed)

    def test_mcp_entry_spawns_fresh_worker_without_loading_caller_dll(self):
        frozen = {**download._base(self.arguments), "status": "complete", "ok": True}
        process = subprocess.CompletedProcess([], 0, json.dumps(frozen), "")
        with patch.object(download.subprocess, "run", return_value=process) as run, \
             patch.object(download, "_open_client", side_effect=AssertionError("caller loaded Steam")):
            result = download.download("unused.dll", ITEM, APP, 0.002, str(self.cache))
        self.assertTrue(result["ok"])
        command = run.call_args.args[0]
        self.assertEqual([download.sys.executable, "-m", "ck3_workshop_mcp.steam_download", "--worker"], command[:4])
        self.assertNotIn("shell", run.call_args.kwargs)
        self.assertNotIn("SubscribeItem", str(command))
        self.assertNotIn("CreateItem", str(command))

    def test_missing_or_wrong_worker_result_is_unknown_without_retry(self):
        for outcome in (subprocess.TimeoutExpired("worker", 15),
                        subprocess.CompletedProcess([], 0, "garbled", ""),
                        subprocess.CompletedProcess([], 0, json.dumps({"schema": download.SCHEMA, "item_id": "9", "app_id": APP}), "")):
            with self.subTest(outcome=outcome), patch.object(download.subprocess, "run") as run:
                if isinstance(outcome, Exception):
                    run.side_effect = outcome
                else:
                    run.return_value = outcome
                result = download.download("unused.dll", ITEM, APP, 0.002, str(self.cache))
                self.assertFalse(result["ok"])
                self.assertEqual("unknown", result["status"])
                self.assertIsNone(result["started"])
                self.assertEqual(1, run.call_count)

    def test_invalid_target_timeout_and_cache_are_rejected_before_process(self):
        for item, timeout, cache in (("0", 300, None), ("-1", 300, None),
                                     (ITEM, float("nan"), None), (ITEM, 0, None),
                                     (ITEM, 300, "relative/" + ITEM),
                                     (ITEM, 300, str(self.root / "9"))):
            with self.subTest(item=item, timeout=timeout, cache=cache), patch.object(download.subprocess, "run") as run:
                with self.assertRaises(steam_native.SteamNativeError):
                    download.download("unused.dll", item, APP, timeout, cache)
                run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
