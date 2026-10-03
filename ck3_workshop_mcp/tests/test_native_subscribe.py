from __future__ import annotations

import ctypes
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ck3_workshop_mcp import steam_subscribe as subscribe
from ck3_workshop_mcp.steam_native import SteamNativeError

APP = 1158310
ITEM = 123456789


class FakeClient:
    ugc = 123

    def __init__(self, *, result=1, callback_item=ITEM, handle=999, state=1, error=None):
        self.result, self.callback_item = result, callback_item
        self.handle, self.state, self.error = handle, state, error
        self.starts, self.waits, self.observes = [], [], []
        self.library = SimpleNamespace(SteamAPI_ISteamUGC_SubscribeItem=self.start,
                                      SteamAPI_ISteamUGC_GetItemState=self.observe)

    def app_id(self):
        return APP

    def start(self, ugc, item):
        self.starts.append((ugc, item))
        return self.handle

    def observe(self, ugc, item):
        self.observes.append((ugc, item))
        return self.state

    def _wait_for_result(self, handle, result_type, callback_id, *, timeout_seconds):
        self.waits.append((handle, result_type, callback_id, timeout_seconds))
        if self.error:
            raise self.error
        return result_type(self.result, self.callback_item)


class NativeSubscribeTests(unittest.TestCase):
    def run_client(self, **kwargs):
        client = FakeClient(**kwargs)
        with patch.object(subscribe, "_bind", side_effect=lambda library, name, *_: getattr(library, name)):
            result = subscribe._run_subscribe(client, ITEM, 0.001)
        return result, client

    def test_win64_exact_call_result_abi(self):
        self.assertEqual(16, ctypes.sizeof(subscribe.SubscribeItemResult))
        self.assertEqual(0, subscribe.SubscribeItemResult.result.offset)
        self.assertEqual(8, subscribe.SubscribeItemResult.item_id.offset)
        self.assertEqual(1313, subscribe.SUBSCRIBE_CALLBACK_ID)

    def test_exact_callback_and_subscribed_state_complete(self):
        result, client = self.run_client(state=5)
        self.assertTrue(result["ok"])
        self.assertEqual("complete", result["status"])
        self.assertEqual({"callback_id": 1313, "item_id": str(ITEM), "result": 1}, result["callback"])
        self.assertEqual([(123, ITEM)], client.starts)
        self.assertEqual([(999, subscribe.SubscribeItemResult, 1313, 0.001)], client.waits)
        self.assertEqual([(123, ITEM)], client.observes)
        self.assertFalse(result["installation_verified"])
        self.assertFalse(result["content_verified"])

    def test_start_handle_without_callback_remains_unknown_and_is_not_retried(self):
        result, client = self.run_client(error=SteamNativeError("API_CALL_RESULT_UNKNOWN", "timeout"))
        self.assertFalse(result["ok"])
        self.assertTrue(result["started"])
        self.assertEqual("unknown", result["status"])
        self.assertIsNone(result["callback"])
        self.assertEqual(1, len(client.starts))
        self.assertEqual([], client.observes)

    def test_foreign_callback_cannot_prove_subscription(self):
        result, client = self.run_client(callback_item=9)
        self.assertFalse(result["ok"])
        self.assertEqual("unknown", result["status"])
        self.assertEqual("SUBSCRIBE_CALLBACK_ITEM_MISMATCH", result["error"]["code"])
        self.assertEqual([], client.observes)
        self.assertEqual(1, len(client.starts))

    def test_failed_callback_and_invalid_call_are_known_failures(self):
        result, client = self.run_client(result=2)
        self.assertFalse(result["ok"])
        self.assertEqual("failed", result["status"])
        self.assertEqual(2, result["callback"]["result"])
        self.assertEqual([], client.observes)
        result, client = self.run_client(handle=0)
        self.assertEqual("failed", result["status"])
        self.assertFalse(result["started"])
        self.assertEqual([], client.waits)

    def test_successful_callback_without_subscribed_bit_is_partial(self):
        result, client = self.run_client(state=4)
        self.assertFalse(result["ok"])
        self.assertEqual("partial", result["status"])
        self.assertFalse(result["subscribed"])
        self.assertEqual("SUBSCRIPTION_STATE_UNVERIFIED", result["error"]["code"])
        self.assertEqual(1, len(client.starts))

    def test_invalid_arguments_fail_before_symbols_or_dll(self):
        cases = [("0", APP, 180), ("-1", APP, 180), ("１２３", APP, 180),
                 (str(2**64), APP, 180), (str(ITEM), 0, 180),
                 (str(ITEM), 2**32, 180), (str(ITEM), True, 180),
                 (str(ITEM), APP, float("nan")), (str(ITEM), APP, 0),
                 (str(ITEM), APP, 3601)]
        for item, app, timeout in cases:
            with self.subTest(item=item, app=app, timeout=timeout), patch.object(subscribe, "symbols") as inspect:
                with self.assertRaises(SteamNativeError):
                    subscribe.subscribe("unused.dll", item, app, timeout)
                inspect.assert_not_called()

    def test_missing_optional_exports_are_a_capability_gap_without_dll_load(self):
        metadata = {"subscription_missing": ["SteamAPI_ISteamUGC_SubscribeItem"]}
        with patch.object(subscribe, "symbols", return_value=metadata), patch.object(subscribe, "_open_client") as open_client:
            with self.assertRaisesRegex(SteamNativeError, "subscription exports"):
                subscribe.subscribe("unused.dll", str(ITEM))
            open_client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
