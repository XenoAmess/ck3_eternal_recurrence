from __future__ import annotations

import asyncio
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))

from test_raiktor_war_bound_regiment_contract import (  # noqa: E402
    ATTACKER_ID,
    DEFENDER_ID,
    WAR_ID,
    _active,
)


SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "run_g2_postwar_cleanup_expiry_receipt.py"
)
MANIFEST = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "g2_postwar_cleanup_expiry_adapter_v1_manifest.json"
)
SPEC = importlib.util.spec_from_file_location(
    "run_g2_postwar_cleanup_expiry_receipt", SCRIPT
)
if SPEC is None or SPEC.loader is None:  # pragma: no cover
    raise RuntimeError(f"cannot import {SCRIPT}")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _snapshot(*, postwar: bool = False) -> dict[str, object]:
    return {
        "paused": True,
        "snapshot_id": "native:8" if postwar else "native:7",
        "revision": 96 if postwar else 91,
        "native_revision": 8 if postwar else 7,
        "date_raw": 53_175_816,
        "episode_run_id": "fixture-runtime-episode",
        "diagnostics": {"bridge_pid": 8765, "connection_generation": 3},
        "played_character": {"character_id": ATTACKER_ID},
        "active_wars": (
            []
            if postwar
            else [
                {
                    "war_id": WAR_ID,
                    "primary_opponent_character_id": DEFENDER_ID,
                }
            ]
        ),
    }


def _expiry(sequence: int, *, expiry: int = 53_219_616) -> dict[str, object]:
    step = f"query-raiktor-actual-truce-expiry-v1-{DEFENDER_ID}"
    payload = {
        "schema_version": 1,
        "backend_id": (
            "ck3-1.19.0.6-native-raiktor-actual-truce-expiry-v1"
        ),
        "status": "available",
        "snapshot_revision": 8,
        "current_date_raw": 53_175_816,
        "owner_character_id": ATTACKER_ID,
        "toward_character_id": DEFENDER_ID,
        "native_has_truce": True,
        "actual_expiry_observable": True,
        "expiry_date_raw": expiry,
        "same_frame_stable": True,
        "readiness": True,
        "temporal_semantics": "post_application_persisted_relation_state",
        "unavailable_reason": None,
    }
    return {
        "step": step,
        "accepted": True,
        "query_sequence": sequence,
        "snapshot_revision": 8,
        "raiktor_actual_truce_expiry": payload,
        "actual_truce_expiry_proof": copy.deepcopy(payload),
        "backend_id": "native-headless",
    }


def _inputs() -> dict[str, object]:
    active = _active()
    generations = RUNNER.retention._generation_vector(active)
    ticket_body = {
        "schema": "xar.ck3.g2_postwar_retention_ticket.v1",
        "exact_build_sha256": RUNNER.EXPECTED_EXE_SHA256,
        "source_report_sha256": "A" * 64,
        "war_id": WAR_ID,
        "character_id": ATTACKER_ID,
        "opponent_character_id": DEFENDER_ID,
        "source_snapshot_id": "native:7",
        "source_revision": 91,
        "source_native_revision": 7,
        "date_raw": 53_175_816,
        "source_connection_generation": 1,
        "source_episode_run_id": "historical-episode",
        "source_ck3_pid": 1234,
        "pre_termination_soldiers": 180,
        "evaluated_days": 1825,
        "frozen_generation_sha256": RUNNER._sha256_json(generations),
        "frozen_generations": generations,
    }
    ticket = copy.deepcopy(ticket_body)
    ticket.update(
        {
            "retention_ticket_id": RUNNER._sha256_json(ticket_body),
            "source_attribution_ready": False,
            "termination_action_bound": False,
            "actual_expiry_observable": False,
            "public_readiness_promoted": False,
            "gen034_closed": False,
            "pre_observation_backend_id": active["backend_id"],
        }
    )
    post = _snapshot(postwar=True)
    return {
        "ticket": ticket,
        "pre": {
            "snapshot": _snapshot(),
            "terms_query_sequence": 2,
            "receipt_sequence": 2,
            "war_bound_observation": active,
        },
        "termination_result": {
            "step": f"surrender-war-{WAR_ID}",
            "accepted": True,
            "status": "submitted",
            "backend_id": "native-headless",
        },
        "post_snapshots": [copy.deepcopy(post) for _ in range(3)],
        "cleanup_observation": RUNNER._destroyed_cleanup_fixture(active, post),
        "expiry_reads": [_expiry(3), _expiry(4)],
    }


class _FakeClient:
    def __init__(self, inputs: dict[str, object]) -> None:
        post = inputs["post_snapshots"]
        expiry = inputs["expiry_reads"]
        self.responses = [post[0], expiry[0], post[1], expiry[1], post[2]]
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def call_tool(self, name: str, arguments: dict[str, object]):
        self.calls.append((name, copy.deepcopy(arguments)))
        return SimpleNamespace(
            structured_content=copy.deepcopy(self.responses.pop(0)),
            is_error=False,
        )


class G2PostwarCleanupExpiryReceiptTests(unittest.TestCase):
    def test_builds_private_receipt_and_consumes_ticket(self) -> None:
        inputs = _inputs()
        receipt = RUNNER.build_postwar_receipt(**inputs)
        self.assertTrue(receipt["ticket_validation"]["ok"])
        self.assertEqual(
            receipt["post"]["truce_expiry"]["source"],
            "persisted_native_truce_row",
        )
        self.assertEqual(receipt["post"]["war_bound_cleanup"]["post_termination_soldiers"], 0)
        self.assertEqual(receipt["mutation_commands"], [f"surrender-war-{WAR_ID}"])
        self.assertFalse(receipt["boundaries"]["public_readiness_promoted"])
        self.assertFalse(receipt["boundaries"]["action_readiness_promoted"])
        self.assertFalse(receipt["boundaries"]["gen034_closed"])

    def test_rejects_cross_session_war_or_expiry_drift(self) -> None:
        for label, mutate in (
            (
                "pid",
                lambda value: value["post_snapshots"][1]["diagnostics"].update(
                    {"bridge_pid": 9999}
                ),
            ),
            (
                "war present",
                lambda value: value["post_snapshots"][0]["active_wars"].append(
                    {"war_id": WAR_ID}
                ),
            ),
            (
                "wrong defender",
                lambda value: value["expiry_reads"][0].update(
                    {"step": "query-raiktor-actual-truce-expiry-v1-999"}
                ),
            ),
            (
                "unstable expiry",
                lambda value: value["expiry_reads"][1][
                    "raiktor_actual_truce_expiry"
                ].update({"expiry_date_raw": 53_219_617}),
            ),
            (
                "extra mutation",
                lambda value: value["termination_result"].update(
                    {"step": "offer-white-peace-50331699"}
                ),
            ),
        ):
            with self.subTest(label=label):
                inputs = _inputs()
                mutate(inputs)
                with self.assertRaises(RUNNER.AdapterError):
                    RUNNER.build_postwar_receipt(**inputs)

    def test_rejects_surviving_cleanup_generation(self) -> None:
        inputs = _inputs()
        cleanup = inputs["cleanup_observation"]
        cleanup["cleanup"] = {"observable": True, "status": "still_alive"}
        regiment = cleanup["regiments"][0]
        regiment["postwar_persistent_state"] = "still_alive"
        row = regiment["composition_rows"][0]
        row["current_army_regiment_state"] = "still_alive"
        row["raised_carmy_state"] = "still_alive"
        row["frozen_carmy_roster_evidence"] = "still_attached"
        with self.assertRaises(RUNNER.AdapterError):
            RUNNER.build_postwar_receipt(**inputs)

    def test_async_collector_is_default_off_and_queries_retained_defender(self) -> None:
        inputs = _inputs()
        client = _FakeClient(inputs)
        with self.assertRaisesRegex(RUNNER.AdapterError, "default-OFF"):
            asyncio.run(
                RUNNER.collect_after_surrender(
                    client,
                    ticket=inputs["ticket"],
                    pre=inputs["pre"],
                    termination_result=inputs["termination_result"],
                    cleanup_observation=inputs["cleanup_observation"],
                )
            )
        self.assertEqual(client.calls, [])

        receipt = asyncio.run(
            RUNNER.collect_after_surrender(
                client,
                ticket=inputs["ticket"],
                pre=inputs["pre"],
                termination_result=inputs["termination_result"],
                cleanup_observation=inputs["cleanup_observation"],
                authorize_private_live=True,
            )
        )
        self.assertTrue(receipt["ticket_validation"]["ok"])
        self.assertEqual(
            client.calls,
            [
                ("ck3_take_snapshot", {}),
                (
                    "ck3_execute_step",
                    {
                        "step": f"query-raiktor-actual-truce-expiry-v1-{DEFENDER_ID}",
                        "expected_revision": 96,
                    },
                ),
                ("ck3_take_snapshot", {}),
                (
                    "ck3_execute_step",
                    {
                        "step": f"query-raiktor-actual-truce-expiry-v1-{DEFENDER_ID}",
                        "expected_revision": 96,
                    },
                ),
                ("ck3_take_snapshot", {}),
            ],
        )

    def test_committed_manifest_is_default_off_and_hash_pinned(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertTrue(manifest["default_off"])
        self.assertFalse(manifest["live_authorized"])
        self.assertFalse(manifest["public_readiness_promoted"])
        self.assertFalse(manifest["action_readiness_promoted"])
        self.assertFalse(manifest["gen034_closed"])
        self.assertFalse(
            manifest["runtime_seam"]["war_bound_cleanup_query_dispatch_present"]
        )
        for name in (
            "runner",
            "fixture",
            "retention_manifest",
            "retention_runner",
            "actual_expiry_contract",
            "actual_expiry_source_contract",
        ):
            path = Path(manifest["paths"][name])
            if not path.is_absolute():
                path = ROOT.parent / path
            self.assertEqual(_sha256(path), manifest["sha256"][name])


if __name__ == "__main__":
    unittest.main()
