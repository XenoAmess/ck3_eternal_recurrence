"""AUTHORED_NOTRUN: registered exact4 Crown consumer of new native whole wires.

Root first qualifies the coherent native producer and emits its four complete
command_result files. This one offline registered consumer replays those result
envelopes unchanged, adapting only top-level request correlation. Normalized
paused frames are fixtures; neither replay nor ACK grants live enactment credit.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from xar_autoplayer.bridge import realm_law_formal_private_transport as formal
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12003, CK3_12004


ACTOR = 29829
DATE = 53169072
LAW = "crown_authority_1"
ACTION_ID = "formal-crown-12004"
QUERY = "ck3_query_realm_law_crown_action_private_v1"
ENACT = "ck3_enact_realm_law_crown_private_v1"
RECEIPT = "ck3_query_realm_law_crown_receipt_private_v1"
BUDGETS = {"gold": 0, "prestige": 20000000, "piety": 0, "influence": 0, "merit": 0}
WIRE_FILES = {
    "query": "wire-law-crown-query.json",
    "submit": "wire-law-crown-submit-pending.json",
    "unchanged": "wire-law-crown-receipt-unchanged.json",
    "enacted": "wire-law-crown-receipt-enacted.json",
}


class FormalWholeWireDriver:
    # These are real production methods; no private transport/validator mirror.
    query_realm_law_crown_action_private_v1 = (
        NativeHeadlessGameplayDriver.query_realm_law_crown_action_private_v1
    )
    submit_realm_law_crown_private_v1 = (
        NativeHeadlessGameplayDriver.submit_realm_law_crown_private_v1
    )
    query_realm_law_crown_receipt_private_v1 = (
        NativeHeadlessGameplayDriver.query_realm_law_crown_receipt_private_v1
    )
    command_timeout_seconds = 1.0

    def __init__(self, wires, enabled=True):
        self.allow_private_realm_law_action = enabled
        self.wires = wires
        self.endpoint = self
        self.state = self
        self.sent = []
        self.receipt_case = "unchanged"
        query = wires["query"]["result"]
        self.observation = query["observation"]
        self.frame = {
            "snapshot_id": "compiled-fixture-native:40", "revision": 41,
            "native_revision": self.observation["snapshot_revision"],
            "date_raw": self.observation["date_raw"],
            "paused": True, "map_ready": True,
            "played_character": {
                "character_id": self.observation["player_character_id"], "alive": True,
            },
            "diagnostics": {"hello": {
                "expected_ck3_version": query["game_version"],
                "expected_ck3_sha256": query["executable_sha256"],
            }},
        }
        self.frame["revision"] = self.frame["native_revision"] + 1

    def take_snapshot(self):
        return deepcopy(self.frame)

    def take_snapshot_without_native_command_history(self):
        return self.take_snapshot()

    def select_receipt(self, name):
        self.receipt_case = name
        receipt = self.wires[name]["result"]["receipt"]
        native_revision = receipt["post_public_revision"]
        self.frame.update(snapshot_id=f"compiled-fixture-native:{native_revision}",
                          revision=native_revision + 1, native_revision=native_revision,
                          date_raw=receipt["post_date_raw"])

    def send(self, request):
        self.sent.append(deepcopy(request))

    def wait_for_command_result(self, request_id, _timeout):
        request = self.sent[-1]
        assert request["request_id"] == request_id
        name = {formal.QUERY_STEP: "query", formal.SUBMIT_STEP: "submit",
                formal.RECEIPT_STEP: self.receipt_case}[request["step"]]
        response = deepcopy(self.wires[name])
        assert response["type"] == "command_result"
        assert response["protocol_version"] == 1 and response["ok"] is True
        # Only correlation changes; the native result/DTO is never repaired.
        response["request_id"] = request_id
        return response


def test_actual4_registered_formal_guard_query_enact_independent_receipt():
    from mcp import Client

    directory = os.environ.get("CK3_M7_FORMAL_NATIVE_WIRE_DIR")
    if not directory:
        raise RuntimeError("Root FIRST requires CK3_M7_FORMAL_NATIVE_WIRE_DIR from the new native producer")
    wire_root = Path(directory)
    wires = {key: json.loads((wire_root / name).read_text(encoding="utf-8"))
             for key, name in WIRE_FILES.items()}
    originals = deepcopy(wires)

    async def call(client, name, arguments):
        result = await client.call_tool(name, arguments)
        assert result.is_error is False, result.content
        assert isinstance(result.structured_content, dict)
        return result.structured_content

    async def reject_before_send(client, driver, name, arguments):
        count = len(driver.sent)
        result = await client.call_tool(name, arguments)
        assert result.is_error is True
        assert len(driver.sent) == count

    async def exercise():
        disabled = FormalWholeWireDriver(wires, False)
        async with Client(create_server(disabled)) as client:
            names = {tool.name for tool in (await client.list_tools()).tools}
            assert not {QUERY, ENACT, RECEIPT} & names
        assert disabled.sent == []

        driver = FormalWholeWireDriver(wires)
        original_frame = deepcopy(driver.frame)
        public_revision = original_frame["revision"]
        native_revision = original_frame["native_revision"]
        assert native_revision == 40 and public_revision == 41
        assert original_frame["date_raw"] == DATE
        assert original_frame["played_character"]["character_id"] == ACTOR
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            assert {QUERY, ENACT, RECEIPT} <= tools.keys()
            for name in (QUERY, RECEIPT):
                assert tools[name].annotations.read_only_hint is True

            # Scoped accepted-tuple seam reproduces the old effective 2/3 set.
            # Shared exact parsing still returns actual4; no native binder alias.
            with patch.object(formal, "CK3_12004", CK3_12003):
                await reject_before_send(client, driver, QUERY,
                                         {"expected_revision": public_revision})

            driver.frame["diagnostics"]["hello"]["expected_ck3_sha256"] = "0" * 64
            await reject_before_send(client, driver, QUERY, {"expected_revision": public_revision})
            driver.frame = deepcopy(original_frame)
            driver.frame["paused"] = False
            await reject_before_send(client, driver, QUERY, {"expected_revision": public_revision})
            driver.frame = deepcopy(original_frame)
            await reject_before_send(client, driver, QUERY, {"expected_revision": public_revision + 1})

            # Ordinary registered snapshot uses the actual Service dispatcher.
            snapshot = await call(client, "ck3_take_snapshot",
                                  {"include_native_command_history": False})
            assert snapshot == original_frame
            readback = await call(client, QUERY, {"expected_revision": snapshot["revision"]})
            assert {key: readback[key] for key in driver.observation} == driver.observation
            assert readback["schema"] == formal.READ_SCHEMA
            assert readback["exact_ck3_build"] == CK3_12004.game_version
            assert readback["exe_sha256"] == CK3_12004.executable_sha256
            assert readback["queried_revision"] == public_revision
            assert readback["queried_native_revision"] == native_revision
            assert readback["queried_snapshot_id"] == original_frame["snapshot_id"]
            query_request = driver.sent[-1]
            assert query_request["step"] == formal.QUERY_STEP
            assert query_request["expected_revision"] == native_revision
            assert query_request["expected_player_character_id"] == ACTOR
            assert query_request["expected_date_raw"] == DATE

            submit_arguments = {"readback": readback, "law_key": LAW,
                                "budgets": deepcopy(BUDGETS), "action_id": ACTION_ID}
            untouched_readback = deepcopy(readback)
            driver.frame["played_character"]["character_id"] = ACTOR + 1
            await reject_before_send(client, driver, ENACT, submit_arguments)
            driver.frame = deepcopy(original_frame)
            driver.frame["native_revision"] = native_revision + 1
            await reject_before_send(client, driver, ENACT, submit_arguments)
            driver.frame = deepcopy(original_frame)

            pending = await call(client, ENACT, submit_arguments)
            native_ack = wires["submit"]["result"]["ack"]
            assert {key: pending[key] for key in native_ack} == native_ack
            assert readback == untouched_readback
            assert pending["schema"] == formal.ACTION_SCHEMA
            assert pending["status"] == "submitted_verification_pending"
            assert pending["verification_pending"] is True
            assert pending["material_result"] is False
            assert pending["submitted_request_id"] == ACTION_ID
            assert pending["exact_ck3_build"] == CK3_12004.game_version
            submit_request = driver.sent[-1]
            assert submit_request["step"] == formal.SUBMIT_STEP
            assert submit_request["expected_revision"] == native_revision
            assert submit_request["expected_native_revision"] == readback["native_snapshot_revision"]
            assert submit_request["expected_proof_epoch"] == readback["proof_epoch"]
            assert submit_request["submitted_request_id"] == ACTION_ID
            assert submit_request["group_key"] == "crown_authority"
            assert submit_request["law_key"] == LAW
            assert {key: submit_request[f"budget_{key}_raw"] for key in BUDGETS} == BUDGETS

            # Each independent receipt binds its own current public/native frame.
            driver.select_receipt("unchanged")
            failed = await call(client, RECEIPT, {
                "expected_revision": driver.frame["revision"], "submitted_request_id": ACTION_ID,
            })
            failed_receipt = wires["unchanged"]["result"]["receipt"]
            assert {key: failed[key] for key in failed_receipt} == failed_receipt
            assert failed["status"] == "failed" and failed["material_result"] is False
            assert driver.sent[-1]["expected_revision"] == 41

            driver.select_receipt("enacted")
            enacted = await call(client, RECEIPT, {
                "expected_revision": driver.frame["revision"], "submitted_request_id": ACTION_ID,
            })
            enacted_receipt = wires["enacted"]["result"]["receipt"]
            assert {key: enacted[key] for key in enacted_receipt} == enacted_receipt
            assert enacted["schema"] == formal.ACTION_SCHEMA
            assert enacted["status"] == "enacted" and enacted["material_result"] is True
            assert all(enacted[key] is True for key in (
                "effective_law_verified", "resources_verified", "succession_verified"))
            assert enacted["effective_law_key"] == LAW
            assert enacted["post_public_revision"] == 42
            assert enacted["post_date_raw"] == DATE
            assert enacted["exe_sha256"] == CK3_12004.executable_sha256
            receipt_request = driver.sent[-1]
            assert receipt_request["step"] == formal.RECEIPT_STEP
            assert receipt_request["expected_revision"] == 42
            assert receipt_request["submitted_request_id"] == ACTION_ID
            assert [row["step"] for row in driver.sent] == [
                formal.QUERY_STEP, formal.SUBMIT_STEP, formal.RECEIPT_STEP, formal.RECEIPT_STEP,
            ]

    asyncio.run(exercise())
    assert wires == originals
