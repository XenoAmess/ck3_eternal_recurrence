"""Producer/consumer, strict wire negatives and real local CDP socket tests."""
from __future__ import annotations

import base64
from dataclasses import replace
import hashlib
import json
import socket
import struct
import threading
import time
import unittest
from unittest.mock import patch

from steam_offline_state_contract import (
    EndpointIdentity, NativeEvidence, ProbeResult, ProcessIdentity, SourceIdentity,
    exact_int, parse_getter, parse_result,
)
from steam_offline_state_probe import (
    ProbeError, _descendants, cdp_evaluate, getter_expression, target_candidates,
)

_NONCE = "0123456789abcdef0123456789abcdef"


def sample() -> ProbeResult:
    return ProbeResult(
        "test-machine-0123456789", "2026-10-20T15:00:00Z", _NONCE,
        "offline", "observed",
        ProcessIdentity(41, "134369704160368681", "C:/Steam/steam.exe", "10.96.30.42"),
        SourceIdentity("C:/Steam/steamui/chunk.js", 14382868, "a" * 64,
                       "1407374883818107", "1788653822000000000"),
        EndpointIdentity(42, "134369704160368683", 9999,
                         "Shared", "about:blank"),
        ("source_and_process_bound",), "cef_app_getters",
    )


class ContractTests(unittest.TestCase):
    def test_both_getters_produce_each_state(self) -> None:
        for value, state in ((True, "offline"), (False, "online")):
            with self.subTest(value=value):
                self.assertEqual(parse_getter(
                    {"nonce": _NONCE, "direct": value, "method": value}, _NONCE), state)

    def test_malformed_getters_never_mean_online(self) -> None:
        getters: tuple[object, ...] = (None, [], {}, {"nonce": _NONCE},
                    {"nonce": _NONCE, "direct": 1, "method": True},
                    {"nonce": _NONCE, "direct": False, "method": 0},
                    {"nonce": _NONCE, "direct": "false", "method": False},
                    {"nonce": _NONCE, "direct": None, "method": None},
                    {"nonce": _NONCE, "direct": True, "method": False},
                    {"nonce": "stale", "direct": True, "method": True},
                    {"nonce": _NONCE, "direct": True, "method": True, "other": 0})
        for raw in getters:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_getter(raw, _NONCE)

    def test_full_json_round_trip_preserves_large_identities(self) -> None:
        original = sample()
        value: object = json.loads(json.dumps(original.to_wire()))
        restored = parse_result(value)
        self.assertEqual(original, restored)
        self.assertEqual(restored.steam, original.steam)

    def test_unavailable_omits_boolean_and_round_trips(self) -> None:
        original = ProbeResult("test-machine", "2026-10-20T15:00:00Z",
                               _NONCE, "unavailable", "cdp_not_enabled",
                               None, None, None)
        wire = original.to_wire()
        self.assertNotIn("offline_mode", wire)
        self.assertEqual(parse_result(json.loads(json.dumps(wire))), original)

    def test_integer_ids_reject_equal_but_wrong_types(self) -> None:
        for value in (True, False, 41.0, "41", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                exact_int(value, 1, 65535)
        for bad in (True, 41.0, "41"):
            wire = json.loads(json.dumps(sample().to_wire()))
            wire["steam"]["pid"] = bad
            with self.subTest(value=bad), self.assertRaises(ValueError):
                parse_result(wire)

    def test_decimal_wire_ids_reject_lossy_or_noncanonical_forms(self) -> None:
        for bad in (134369704160368681, 1.3436970416036868e17,
                    "0134369704160368681", "+134369704160368681", "1e17", str(2**64)):
            wire = json.loads(json.dumps(sample().to_wire()))
            wire["steam"]["birth_filetime"] = bad
            with self.subTest(value=bad), self.assertRaises(ValueError):
                parse_result(wire)

    def test_missing_null_empty_and_wrong_fields_stay_distinct(self) -> None:
        for mutate in ("missing_source", "null_source", "null_diagnostics",
                       "tuple_diagnostics", "bad_boolean", "extra_alias",
                       "unavailable_with_boolean", "invalid_reason"):
            wire = json.loads(json.dumps(sample().to_wire()))
            if mutate == "missing_source": del wire["source"]
            elif mutate == "null_source": wire["source"] = None
            elif mutate == "null_diagnostics": wire["diagnostics"] = None
            elif mutate == "tuple_diagnostics": wire["diagnostics"] = ()
            elif mutate == "bad_boolean": wire["offline_mode"] = 1
            elif mutate == "extra_alias": wire["offline"] = True
            elif mutate == "unavailable_with_boolean": wire["status"] = "unavailable"
            else: wire["reason"] = []
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                parse_result(wire)

    def test_owned_descendants_do_not_include_other_client(self) -> None:
        rows = {1: (0, "steam.exe"), 2: (1, "helper.exe"),
                3: (2, "steamwebhelper.exe"), 4: (0, "steamwebhelper.exe")}
        self.assertEqual(_descendants(rows, 1), frozenset((1, 2, 3)))

    def test_foreign_or_malformed_endpoints_reject_before_network(self) -> None:
        for url in ("ws://example.com:9/devtools/page/a",
                    "ws://127.0.0.1:10/devtools/page/a",
                    "ws://user@127.0.0.1:9/devtools/page/a",
                    "http://127.0.0.1:9/devtools/page/a",
                    "ws://127.0.0.1:9/devtools/page/a?secret=x"):
            with self.subTest(url=url), self.assertRaises(ProbeError):
                cdp_evaluate(url, 9, _NONCE, 0.1)


    def test_discovery_binds_target_id_and_rejects_auth_urls(self) -> None:
        good = {"type": "page", "id": "good", "title": "SharedJSContext",
                "url": "about:blank",
                "webSocketDebuggerUrl": "ws://127.0.0.1:9/devtools/page/good"}
        wrong = {**good, "id": "other"}
        auth = {**good, "url": "https://steamloopback.host/index?auth=secret"}
        foreign = {**good, "url": "https://steamloopback.host.invalid/"}
        with patch("steam_offline_state_probe.http_json", side_effect=[
            {"Browser": "Chrome/128.0", "Protocol-Version": "1.3"},
            [good, wrong, auth, foreign],
        ]):
            self.assertEqual(target_candidates(9, 0.1),
                             (("good", "about:blank", good["webSocketDebuggerUrl"]),))

    def test_expression_is_fixed_readonly_getters(self) -> None:
        expression = getter_expression(_NONCE)
        self.assertIn("app.GetCurrentUser()", expression)
        self.assertIn("user.bIsOfflineMode", expression)
        self.assertIn("app.BIsOfflineMode()", expression)
        for forbidden in ("SetOffline", "GoOnline", "SteamAPI_Init", "fetch(", "eval("):
            self.assertNotIn(forbidden, expression)



def native_sample() -> ProbeResult:
    common = sample()
    if common.steam is None:
        raise AssertionError("fixture needs a Steam identity")
    source = SourceIdentity("C:/Steam/SteamUI.dll", 18962584, "b" * 64,
                            "1407374883818110", "1788653822000000000")
    base, rva = 9007199254740993, 17970727
    anchor = "440fb60513c9b000488d157d3b7400488bcbe81d9e3b00"
    evidence = NativeEvidence(
        common.machine_id, common.observed_at_utc, common.nonce, str(base),
        20000000, str(rva), str(base + rva), "6384908", anchor,
        hashlib.sha256(bytes.fromhex(anchor)).hexdigest(), (1, 1),
        common.steam, common.steam, source, source,
        "17963680", "1400000012345", "340", (4, 4),
    )
    return ProbeResult(common.machine_id, common.observed_at_utc, common.nonce,
                       "offline", "observed", common.steam, source, None, (),
                       "native_current_user_byte", evidence)


class NativeContractTests(unittest.TestCase):
    def test_native_json_round_trip_has_distinct_provenance(self) -> None:
        original = native_sample()
        wire = json.loads(json.dumps(original.to_wire()))
        self.assertEqual(wire["observation_method"], "native_current_user_byte")
        self.assertIsNone(wire["endpoint"])
        self.assertEqual(wire["native_evidence"]["raw_samples"], [1, 1])
        self.assertEqual(parse_result(wire), original)


    def test_native_zero_and_voice_tray_state_do_not_qualify_online(self) -> None:
        offline = native_sample()
        if offline.native_evidence is None:
            self.fail("fixture needs native evidence")
        evidence = replace(offline.native_evidence, raw_samples=(0, 0),
                           tray_state_samples=(5, 5))
        online = replace(offline, status="online", native_evidence=evidence)
        wire = json.loads(json.dumps(online.to_wire()))
        self.assertIs(wire["offline_mode"], False)
        self.assertEqual(wire["native_evidence"]["raw_samples"], [0, 0])
        with self.assertRaises(ValueError):
            parse_result(wire)

    def test_v1_persisted_receipt_migrates_explicitly(self) -> None:
        original = sample()
        wire = json.loads(json.dumps(original.to_wire()))
        wire["schema"] = "xar.steam-offline-state-probe/v1"
        del wire["native_evidence"]
        del wire["observation_method"]
        self.assertEqual(parse_result(wire), original)

    def test_native_provenance_rejects_cross_identity_and_wrong_types(self) -> None:
        for mutation in ("numeric_address", "wrong_address", "range", "bool_sample",
                         "float_sample", "changed_sample", "changed_process",
                         "changed_source", "wrong_nonce", "wrong_anchor", "wrong_method",
                         "missing_method", "false_mode", "tray_mismatch", "tray_wrong_type",
                         "manager_null", "unexpected_field"):
            wire = json.loads(json.dumps(native_sample().to_wire()))
            evidence = wire["native_evidence"]
            if mutation == "numeric_address": evidence["module_base"] = 9007199254740993
            elif mutation == "wrong_address": evidence["value_address"] = "1"
            elif mutation == "range": evidence["module_size"] = 100
            elif mutation == "bool_sample": evidence["raw_samples"] = [True, True]
            elif mutation == "float_sample": evidence["raw_samples"] = [1.0, 1.0]
            elif mutation == "changed_sample": evidence["raw_samples"] = [1, 0]
            elif mutation == "changed_process": evidence["steam_after"]["birth_filetime"] = "1"
            elif mutation == "changed_source": evidence["source_after"]["file_id"] = "1"
            elif mutation == "wrong_nonce": evidence["nonce"] = "stale"
            elif mutation == "wrong_anchor": evidence["producer_anchor_hex"] = "00"
            elif mutation == "wrong_method": wire["observation_method"] = "cef_app_getters"
            elif mutation == "missing_method": wire["observation_method"] = None
            elif mutation == "false_mode": wire["offline_mode"] = False
            elif mutation == "tray_mismatch": evidence["tray_state_samples"] = [5, 5]
            elif mutation == "tray_wrong_type": evidence["tray_state_samples"] = [4.0, 4.0]
            elif mutation == "manager_null": evidence["tray_manager_address"] = "0"
            else: evidence["alias"] = "wrong"
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                parse_result(wire)


def receive(stream: socket.socket, count: int) -> bytes:
    value = bytearray()
    while len(value) < count:
        part = stream.recv(count - len(value))
        if not part: raise RuntimeError("fixture disconnected")
        value.extend(part)
    return bytes(value)


class CdpSocketTests(unittest.TestCase):
    def test_real_socket_producer_consumer_and_exact_request(self) -> None:
        errors: list[BaseException] = []
        requests: list[object] = []
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            listener.settimeout(3)
            port = listener.getsockname()[1]
            def serve() -> None:
                try:
                    with listener.accept()[0] as stream:
                        stream.settimeout(3)
                        header = bytearray()
                        while not header.endswith(b"\r\n\r\n"):
                            header.extend(receive(stream, 1))
                        lines = bytes(header).decode("ascii").split("\r\n")
                        key = next(line.split(": ", 1)[1] for line in lines
                                   if line.startswith("Sec-WebSocket-Key:"))
                        accept = base64.b64encode(hashlib.sha1(
                            (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11")
                            .encode("ascii")).digest()).decode("ascii")
                        stream.sendall(("HTTP/1.1 101 Switching Protocols\r\n"
                            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
                            f"Sec-WebSocket-Accept: {accept}\r\n\r\n").encode("ascii"))
                        first, second = receive(stream, 2)
                        if first != 0x81 or not second & 128:
                            raise RuntimeError("client frame must be masked text")
                        length = second & 127
                        if length == 126: length = struct.unpack("!H", receive(stream, 2))[0]
                        elif length == 127: length = struct.unpack("!Q", receive(stream, 8))[0]
                        mask = receive(stream, 4)
                        raw = receive(stream, length)
                        decoded = bytes(value ^ mask[i % 4] for i, value in enumerate(raw))
                        requests.append(json.loads(decoded))
                        payload = json.dumps({"id": 1, "result": {"result": {
                            "type": "object", "value": {
                                "nonce": _NONCE, "direct": True, "method": True,
                            }}}}).encode("utf-8")
                        header_bytes = (bytes((0x81, len(payload))) if len(payload) < 126
                            else bytes((0x81, 126)) + struct.pack("!H", len(payload)))
                        stream.sendall(header_bytes + payload)
                except BaseException as error:
                    errors.append(error)
            worker = threading.Thread(target=serve)
            worker.start()
            try:
                raw = cdp_evaluate(f"ws://127.0.0.1:{port}/devtools/page/Shared",
                                   port, _NONCE, 2)
                self.assertEqual(parse_getter(raw, _NONCE), "offline")
            finally:
                worker.join(4)
            self.assertFalse(worker.is_alive())
            if errors: raise errors[0]
        self.assertEqual(len(requests), 1)
        request = requests[0]
        if not isinstance(request, dict): self.fail("request must be JSON object")
        self.assertEqual(request["method"], "Runtime.evaluate")
        self.assertEqual(request["id"], 1)
        self.assertEqual(request["params"]["expression"], getter_expression(_NONCE))
        self.assertIs(request["params"]["throwOnSideEffect"], True)
        self.assertIs(request["params"]["returnByValue"], True)


if __name__ == "__main__":
    unittest.main()
