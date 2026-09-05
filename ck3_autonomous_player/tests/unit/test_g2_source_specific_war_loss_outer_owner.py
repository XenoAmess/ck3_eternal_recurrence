from __future__ import annotations

import asyncio
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "run_g2_source_specific_war_loss_outer_owner.py"
)
MANIFEST = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "g2_source_specific_war_loss_outer_owner_v1_manifest.json"
)
SPEC = importlib.util.spec_from_file_location("g2_source_loss_outer_owner", SCRIPT)
if SPEC is None or SPEC.loader is None:  # pragma: no cover
    raise RuntimeError(f"cannot load {SCRIPT}")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


PID = 17_292
WAR_ID = 50_331_699
CHARACTER_ID = 29_829
DATE_RAW = 53_223_936


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _source_capture() -> dict[str, object]:
    executions: list[dict[str, object]] = []
    for index in range(6):
        current_id = 20_000 + index
        persistent_id = 30_000 + index
        soldiers = 100 + index
        executions.append(
            {
                "sequence": index + 1,
                "thread_id": 700 + index,
                "loaded_node": f"0x{0x1000 + index * 0x100:X}",
                "created_army": f"0x{0x9000 + index * 0x100:X}",
                "army_generation_id": 10_000 + index,
                "war_id": WAR_ID,
                "initial_soldiers": soldiers,
                "evaluated_name": "norman_highwaymen",
                "current_regiments": [
                    {"generation_id": current_id, "current_soldiers": soldiers}
                ],
                "persistent_regiments": [
                    {
                        "generation_id": persistent_id,
                        "war_id": WAR_ID,
                        "current_regiment_ids": [current_id],
                    }
                ],
            }
        )
    return {
        "schema": "raiktor-war-bound-private-capture-v1",
        "status": "private_test_only",
        "result": "GREEN",
        "reason": "six-action-bound-source-executions-captured",
        "read_only": True,
        "public_bridge_abi_changed": False,
        "production_detour_installed": False,
        "readiness_promotion": False,
        "pid": PID,
        "image_base": "0x140000000",
        "observation_stop_rva": "0x2E7F951",
        "observation_window_end_rva_exclusive": "0x2E7F9A6",
        "exe_sha256": RUNNER.EXPECTED_EXE_SHA256,
        "arm_proof_sha256": (
            "B7DC28B0B9EDB0F8A03E5DB2F03AD6CA1E3B649648BAE161B6A487063735B9B8"
        ),
        "event_definition_key": "bookmark.1071",
        "option_key": "bookmark.1071.a",
        "option_index": 0,
        "exact_raiktor_war_id": WAR_ID,
        "source_execution_count": 6,
        "breakpoint_installed": True,
        "original_breakpoint_byte_restored": True,
        "process_terminated": False,
        "attach_mode": True,
        "debugger_detached": True,
        "executions": executions,
    }


def _lifecycle_result() -> dict[str, object]:
    return {
        "status": "green",
        "source_normalization": {"capture_pid": PID},
        "handoff": {"capture_pid": PID},
        "source_specific_loss_join": {"identity": {"ck3_pid": PID}},
        "ok": True,
    }


class FakeOperations:
    def __init__(self, capture: dict[str, object] | None = None) -> None:
        self.capture = capture or _source_capture()
        self.driver = object()
        self.events: list[object] = []
        self.bridge_pid = PID
        self.alive = True

    async def acquire_exclusive_launch(self) -> object:
        token = object()
        self.events.append("acquire")
        return token

    async def launch_normal_event_process(self, token: object) -> dict[str, object]:
        self.events.append(("launch", token))
        return {
            "pid": PID,
            "startup_mode": "normal-event",
            "event_target": "bookmark.1071.a",
            "exclusive_slot": True,
            "cleanup_owner": "outer-owner",
        }

    async def capture_natural_source_event(
        self, launch: dict[str, object], pid: int
    ) -> dict[str, object]:
        self.events.append(("observe", launch, pid))
        return {"pid": pid, "capture": self.capture, "capture_sha256": "A" * 64}

    async def is_owned_process_alive(
        self, launch: dict[str, object], pid: int
    ) -> bool:
        self.events.append(("alive", launch, pid))
        return self.alive

    async def pause_owned_process(
        self, launch: dict[str, object], pid: int
    ) -> dict[str, object]:
        self.events.append(("pause", launch, pid))
        return {"pid": pid, "paused": True, "after_observer_detach": True}

    async def attach_bridge_to_pid(
        self, launch: dict[str, object], pid: int
    ) -> object:
        self.events.append(("attach", launch, pid))
        return self.driver

    async def read_bridge_binding(self, driver: object) -> dict[str, object]:
        self.events.append(("binding", driver))
        return {
            "bridge_pid": self.bridge_pid,
            "explicit_target_pid": PID,
            "attached": True,
        }

    async def final_cleanup(
        self, launch: dict[str, object], driver: object | None, pid: int
    ) -> None:
        self.events.append(("cleanup", launch, driver, pid))

    async def release_exclusive_launch(self, token: object) -> None:
        self.events.append(("release", token))


class G2SourceSpecificWarLossOuterOwnerTests(unittest.TestCase):
    def _run(
        self,
        operations: FakeOperations,
        continuation: object,
    ) -> dict[str, object]:
        return asyncio.run(
            RUNNER.run_exclusive_outer_owner(
                operations,
                expected_character_id=CHARACTER_ID,
                expected_date_raw=DATE_RAW,
                postwar_timeout=1.0,
                continuation=continuation,
            )
        )

    def test_same_pid_same_driver_and_unique_cleanup_are_ordered(self) -> None:
        operations = FakeOperations()
        seen_driver: list[object] = []

        async def continuation(driver: object, **_kwargs: object) -> dict[str, object]:
            operations.events.append(("continuation", driver))
            seen_driver.append(driver)
            return _lifecycle_result()

        result = self._run(operations, continuation)
        event_names = [event if isinstance(event, str) else event[0] for event in operations.events]
        self.assertEqual(
            event_names,
            [
                "acquire",
                "launch",
                "observe",
                "alive",
                "pause",
                "attach",
                "binding",
                "continuation",
                "cleanup",
                "release",
            ],
        )
        self.assertIs(seen_driver[0], operations.driver)
        cleanup = [event for event in operations.events if not isinstance(event, str) and event[0] == "cleanup"]
        self.assertEqual(len(cleanup), 1)
        self.assertIs(cleanup[0][2], operations.driver)
        self.assertEqual(cleanup[0][3], PID)
        self.assertEqual(set(result["process_identity"].values()), {PID})
        self.assertEqual(result["ownership"]["final_cleanup_calls"], 1)
        self.assertTrue(result["observer_handoff"]["breakpoint_restored"])
        self.assertFalse(result["observer_handoff"]["process_terminated"])

    def test_unsafe_observer_handoff_is_no_go_before_bridge_and_cleans_once(self) -> None:
        capture = _source_capture()
        capture["process_terminated"] = True
        operations = FakeOperations(capture)

        async def continuation(*_args: object, **_kwargs: object) -> dict[str, object]:
            self.fail("continuation must not run")

        with self.assertRaisesRegex(
            RUNNER.OuterOwnerContractError, "detach-without-kill contract is NO-GO"
        ):
            self._run(operations, continuation)
        event_names = [event if isinstance(event, str) else event[0] for event in operations.events]
        self.assertNotIn("attach", event_names)
        self.assertNotIn("continuation", event_names)
        self.assertEqual(event_names.count("cleanup"), 1)
        self.assertEqual(event_names[-1], "release")

    def test_process_death_or_bridge_pid_drift_stops_before_continuation(self) -> None:
        async def continuation(*_args: object, **_kwargs: object) -> dict[str, object]:
            self.fail("continuation must not run")

        dead = FakeOperations()
        dead.alive = False
        with self.assertRaisesRegex(
            RUNNER.OuterOwnerContractError, "did not survive observer detachment"
        ):
            self._run(dead, continuation)
        self.assertEqual(
            len([event for event in dead.events if not isinstance(event, str) and event[0] == "cleanup"]),
            1,
        )

        drifted = FakeOperations()
        drifted.bridge_pid = PID + 1
        with self.assertRaisesRegex(
            RUNNER.OuterOwnerContractError, "bridge is not explicitly attached"
        ):
            self._run(drifted, continuation)
        names = [event if isinstance(event, str) else event[0] for event in drifted.events]
        self.assertNotIn("continuation", names)
        self.assertEqual(names.count("cleanup"), 1)

    def test_continuation_failure_still_has_one_outer_cleanup(self) -> None:
        operations = FakeOperations()

        async def continuation(*_args: object, **_kwargs: object) -> dict[str, object]:
            operations.events.append("continuation")
            raise RuntimeError("deterministic continuation failure")

        with self.assertRaisesRegex(RuntimeError, "deterministic continuation failure"):
            self._run(operations, continuation)
        names = [event if isinstance(event, str) else event[0] for event in operations.events]
        self.assertEqual(names.count("cleanup"), 1)
        self.assertEqual(names[-1], "release")

    def test_returned_process_lease_is_cleaned_even_if_launch_receipt_is_red(self) -> None:
        class InvalidLaunchOperations(FakeOperations):
            async def launch_normal_event_process(
                self, token: object
            ) -> dict[str, object]:
                self.events.append(("launch", token))
                return {
                    "pid": PID,
                    "startup_mode": "debugger-launch",
                    "event_target": "bookmark.1071.a",
                    "exclusive_slot": True,
                    "cleanup_owner": "outer-owner",
                }

        operations = InvalidLaunchOperations()

        async def continuation(*_args: object, **_kwargs: object) -> dict[str, object]:
            self.fail("continuation must not run")

        with self.assertRaisesRegex(
            RUNNER.OuterOwnerContractError, "launch ownership drifted"
        ):
            self._run(operations, continuation)
        names = [event if isinstance(event, str) else event[0] for event in operations.events]
        self.assertEqual(names, ["acquire", "launch", "cleanup", "release"])

    def test_no_launch_manifest_and_observer_source_preflight_are_honest(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "static-ready-no-launch")
        self.assertFalse(manifest["live_authorized"])
        self.assertFalse(manifest["composition"]["live_adapter_implemented"])
        self.assertFalse(
            manifest["composition"]["standalone_capture_runner_used_as_inner_phase"]
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths: dict[str, str] = {}
            hashes: dict[str, str] = {}
            for name in manifest["paths"]:
                path = root / f"{name}.input"
                if name == "source_observer":
                    path.write_text(
                        "\n".join(
                            (
                                "DebugActiveProcess(options.attach_pid)",
                                "DebugSetProcessKillOnExit(FALSE)",
                                "capture.original_breakpoint_byte_restored = WriteRemoteByte(",
                                "if (!process_exited && capture.attach_mode)",
                                "DebugActiveProcessStop(process_info.dwProcessId)",
                                "} else if (!process_exited) {",
                                "capture.process_terminated = TerminateProcess(",
                            )
                        ),
                        encoding="utf-8",
                    )
                else:
                    path.write_bytes(f"fixture:{name}\n".encode("ascii"))
                paths[name] = str(path)
                hashes[name] = _sha256(path)
            fixture_manifest = {
                "schema": RUNNER.MANIFEST_SCHEMA,
                "status": "static-ready-no-launch",
                "default_off": True,
                "live_authorized": False,
                "paths": paths,
                "sha256": hashes,
                "composition": {
                    "live_adapter_implemented": False,
                    "standalone_capture_runner_used_as_inner_phase": False,
                    "final_cleanup_owner": "outer-owner",
                },
                "boundaries": {
                    "live_executed": False,
                    "source_specific_loss_ready": False,
                    "comparison_input_ready": False,
                    "decision_ready": False,
                    "automatic_surrender_ready": False,
                    "gen034_closed": False,
                },
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(fixture_manifest), encoding="utf-8")
            output = root / "preflight.json"
            with mock.patch.object(
                RUNNER, "EXPECTED_EXE_SHA256", hashes["game_executable"]
            ):
                report = RUNNER.run_no_launch_preflight(
                    manifest_path,
                    output,
                    repo_root=root,
                    process_inventory=lambda: {"counts": {"ck3.exe": 0}},
                )
        self.assertEqual(report["status"], RUNNER.EXPECTED_STATUS)
        self.assertFalse(report["no_go"]["live_command_available"])
        self.assertTrue(report["observer_source_proof"]["attach_branch_detaches"])
        self.assertFalse(report["boundaries"]["ck3_started_or_attached"])
        for name, value in manifest["paths"].items():
            path = Path(value)
            if not path.is_absolute():
                path = ROOT.parent / path
                self.assertEqual(_sha256(path), manifest["sha256"][name])
            else:
                self.assertRegex(manifest["sha256"][name], r"^[0-9A-F]{64}$")

    def test_observer_source_branch_proof_rejects_attach_termination(self) -> None:
        source = "\n".join(
            (
                "DebugActiveProcess(options.attach_pid)",
                "DebugSetProcessKillOnExit(FALSE)",
                "capture.original_breakpoint_byte_restored = WriteRemoteByte(",
                "if (!process_exited && capture.attach_mode)",
                "capture.process_terminated = TerminateProcess(",
                "DebugActiveProcessStop(process_info.dwProcessId)",
                "} else if (!process_exited) {",
            )
        )
        with self.assertRaises(RUNNER.OuterOwnerContractError):
            RUNNER._validate_observer_source(source)


if __name__ == "__main__":
    unittest.main()
