"""Actual shared restore functions with authored inputs; no live qualification."""
from __future__ import annotations

import argparse
import ast
import asyncio
import copy
import hashlib
from pathlib import Path
import re
import sys
import tempfile
import threading
import time
from typing import Awaitable, Callable, Protocol, runtime_checkable
import unittest

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parents[1]
for directory in (REPO / "tools", REPO / "ck3_autonomous_player/src"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import acceptance_adapter as core
from acceptance_contract import Frame, Object, Pin, field, json_value, mapping, pin
from ck3_mod_acceptance_saved_profile_v2 import materialize_saved_profile_v2
from saved_campaign_actor_binding import SavedCampaignActorBinding
from test_saved_campaign_profile_inventory_v2 import ProfileSpec, actual_host_preparer

EXE_SHA = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"


def cold_frame(*, epoch: int, run_id: str = "cold-unit", actor: int = 91) -> Object:
    return {"paused": True, "map_ready": True, "source": "injected-dll-named-pipe", "backend_id": "native-headless",
        "episode_projection": "native_campaign", "snapshot_id": "native:1", "revision": 2, "native_revision": 1,
        "date_raw": 123456, "local_player_id": 1, "active_event": None,
        "played_character": {"character_id": actor, "alive": True, "source": "native"},
        "managed_campaign_run_binding": {"run_id": run_id, "bridge_pipe": "unit-pipe"},
        "diagnostics": {"bridge_pid": 124, "connection_generation": 9, "pipe_name": "unit-pipe", "protocol_version": 1,
            "connected": True, "semantic_state_available": True, "transport_fatal_error": None, "last_error": None,
            "rejected_state_snapshot_count": 0,
            "hello": {"pid": 124, "connection_generation": 9, "ck3_build_match": True, "game_adapter_id": "ck3-1.20.0.4-msvc-x64",
                "expected_ck3_version": "1.20.0.4", "expected_ck3_sha256": EXE_SHA, "capabilities": ["game.state.snapshot"]},
            "last_heartbeat": {"pid": 124,
                "main_thread_query_mailbox_v1": {"ready": True, "stamp_read_success": True, "pump_epochs": epoch,
                    "owner_verified_pump_epochs": epoch, "owner_tid": 200, "current_tid": 200},
                "snapshot_observer_12002": {"read_in_progress": False, "started_ms": epoch * 10, "completed_ms": epoch * 10 + 1}}}}


class RestoreClient:
    def __init__(self, run_id: str = "cold-unit") -> None:
        self.epochs = iter((1, 2, 3))
        self.run_id = run_id

    async def fresh(self) -> Object:
        return cold_frame(epoch=next(self.epochs), run_id=self.run_id)

    async def call(self, name: str, arguments: object = None) -> Object:
        if name == "ck3_migration_pipe_diagnostics":
            return {"pipe": "unit-pipe", "transport_error": None, "diagnostics": json_value(field(cold_frame(epoch=1), "diagnostics"))}
        if name != "ck3_query_campaign_root_context_v1":
            raise AssertionError("Authored test must not submit another tool")
        return {"campaign_root_context_ready": True, "backend_id": "native-headless", "player_character_id": 91,
            "player_character_alive": True, "queried_snapshot_id": "native:1", "queried_revision": 2,
            "queried_native_revision": 1, "date_raw": 123456,
            "provenance": {"game_version": "1.20.0.4", "executable_sha256": EXE_SHA}}


@runtime_checkable
class ActualRestore(Protocol):
    def __call__(self, client: RestoreClient, expected: object, *, report: dict[str, object], write: Callable[[], None],
                 timeout: float, managed_done: threading.Event | None, poll_interval: float) -> Awaitable[object]: ...


def actual_restore() -> ActualRestore:
    source = REPO / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"
    names = {"saved_campaign_admission_frame", "saved_campaign_root_binding", "saved_campaign_initial_snapshot_state",
             "saved_campaign_cancelled_wait_receipt", "wait_for_saved_campaign"}
    tree = ast.parse(source.read_bytes())
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names]
    if {node.name for node in nodes} != names:
        raise AssertionError("Actual shared restore implementation missing")
    scope: dict[str, object] = {"asyncio": asyncio, "copy": copy, "time": time, "threading": threading,
        "now": lambda: "2000-01-01T00:00:00Z", "json": __import__("json"), "re": re}
    exec(compile(ast.Module(body=list(nodes), type_ignores=[]), str(source), "exec"), scope)
    value = scope["wait_for_saved_campaign"]
    if not isinstance(value, ActualRestore):
        raise AssertionError("Actual shared restore function unavailable")
    return value


def restore_fixture(root: Path) -> tuple[dict[str, object], Object, Object]:
    product = root / "formal"
    product.mkdir()
    (product / "descriptor.mod").write_text('name="AUTHORED TEST PRODUCT"\n', encoding="utf-8")
    config: dict[str, Pin] = {}
    for index, name in enumerate(("pdx_settings.txt", "tutorial.txt", "presets.txt", "player/game_rules/presets.txt")):
        path = root / "input" / str(index)
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(b"authored configuration; no game")
        config[name] = pin(path)
    prepared = materialize_saved_profile_v2({"state_dir": str(root / "state"), "output": str(root / "prepare")}, product, config,
        source_role="formal_product")
    source = root / "authored-input.ck3"
    source.write_bytes(b"AUTHORED PREFLIGHT; NEVER LOADED IN CK3")
    args = argparse.Namespace(saved_campaign_save=source, saved_campaign_save_bytes=source.stat().st_size,
        saved_campaign_save_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), saved_campaign_player_id=91,
        saved_campaign_date_raw=123456, saved_campaign_product_inventory=Path(prepared["product_inventory"]["path"]))
    copied = mapping(actual_host_preparer()(args, ProfileSpec(Path(prepared["profile"]), Path(prepared["state_dir"]))), "actual prepared copy")
    expected = {key: copied[key] for key in ("source_path", "bytes", "sha256", "actor_character_id", "date_raw")}
    report: dict[str, object] = {"pipe": "unit-pipe", "saved_campaign_input": copied,
        "saved_campaign_launch": {"status": "ACTUAL_SINGLE_CLI_RESTORE_LAUNCHED", "argv_admitted": True,
            "continue_last_save": False, "load_save_name": "restored_campaign", "ck3_pid": 124,
            "command": ["AUTHORED-TEST-NO-PROCESS", "-loadsave=restored_campaign"]}}

    def write() -> None:
        return None

    async def run() -> object:
        return await actual_restore()(RestoreClient(), expected, report=report, write=write, timeout=3.0,
                                      managed_done=None, poll_interval=0.001)

    asyncio.run(run())
    frozen: Object = {"run_id": "cold-unit", "argv": ["host", "--state-dir", prepared["state_dir"],
        "--saved-campaign-save", str(source), "--saved-campaign-save-bytes", str(source.stat().st_size),
        "--saved-campaign-save-sha256", hashlib.sha256(source.read_bytes()).hexdigest(), "--saved-campaign-player-id", "91",
        "--saved-campaign-date-raw", "123456", "--saved-campaign-product-inventory", prepared["product_inventory"]["path"]]}
    manifest: Object = {"machine_id": "unit-machine", "game": {"version": "1.20.0.4", "exe_sha256": EXE_SHA}}
    return report, frozen, manifest


def parse(report: object, frozen: object, manifest: object) -> SavedCampaignActorBinding:
    return SavedCampaignActorBinding.parse(report, frozen=frozen, run_id="cold-unit", machine_id="unit-machine", manifest=manifest)


def change(root: object, path: tuple[str, ...], value: object) -> None:
    current = root
    for key in path[:-1]:
        if not isinstance(current, dict):
            raise AssertionError("Authored mutation path is not an object")
        current = current[key]
    if not isinstance(current, dict):
        raise AssertionError("Authored mutation target is not an object")
    current[path[-1]] = value


class SavedCampaignActorBindingTests(unittest.TestCase):
    def test_actual_host_prepare_restore_native_root_to_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report, frozen, manifest = restore_fixture(Path(temporary))
            bound = parse(report, frozen, manifest)
            self.assertEqual((bound.player_id, bound.pid, bound.generation_decimal, bound.pump_epoch_decimal), (91, 124, "9", "3"))
            self.assertFalse(bound.to_json()["product_acceptance_proven"])
            bound.validate_frame(Frame(2, 1, 123456, 91, 124, "9"))
            with self.assertRaises(ValueError):
                bound.validate_frame(Frame(2, 1, 123456, 92, 124, "9"))

    def test_ack_false_equal_types_root_and_restore_identity_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            original, frozen, manifest = restore_fixture(Path(temporary))
            changes: tuple[tuple[tuple[str, ...], object], ...] = (
                (("saved_campaign_launch", "argv_admitted"), False),
                (("saved_campaign_launch", "ck3_pid"), True),
                (("saved_campaign_input", "actor_character_id"), 91.0),
                (("saved_campaign_restore", "status"), "WAITING_FOR_ACTUAL_SAVED_CAMPAIGN_OWNER_FRAMES"),
                (("saved_campaign_restore", "binding", "connection_generation"), True),
                (("saved_campaign_restore", "binding", "date_raw"), 123457),
                (("saved_campaign_restore", "observations"), []))
            for path, value in changes:
                changed = copy.deepcopy(original)
                change(changed, path, value)
                with self.subTest(path=path), self.assertRaises(ValueError):
                    parse(changed, frozen, manifest)

    def test_shared_root_and_advancing_pumps_are_reconsumed_not_just_status(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            original, frozen, manifest = restore_fixture(Path(temporary))
            for kind in ("root", "pump", "binding"):
                changed = copy.deepcopy(original)
                rows = field(field(changed, "saved_campaign_restore"), "observations")
                if not isinstance(rows, list):
                    raise AssertionError("Actual shared observations missing")
                if kind == "root":
                    change(rows[-1], ("campaign_root", "player_character_id"), 92)
                elif kind == "pump":
                    change(rows[-1], ("snapshot", "diagnostics", "last_heartbeat", "main_thread_query_mailbox_v1", "owner_verified_pump_epochs"), True)
                else:
                    change(rows[-1], ("binding",), None)
                with self.subTest(kind=kind), self.assertRaises(ValueError):
                    parse(changed, frozen, manifest)

    def test_copied_save_and_frozen_source_identity_cannot_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report, frozen, manifest = restore_fixture(Path(temporary))
            copied = Path(text_path(field(field(report, "saved_campaign_input"), "copied_save_path")))
            copied.write_bytes(b"changed actual copy")
            with self.assertRaisesRegex(ValueError, "copy differs"):
                parse(report, frozen, manifest)


def text_path(value: object) -> str:
    if not isinstance(value, str):
        raise AssertionError("Authored test path is not text")
    return value


if __name__ == "__main__":
    unittest.main()
