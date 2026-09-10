from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.operator_mcp import (  # noqa: E402
    HostIdentity,
    OperatorHandoffError,
    OperatorProfileError,
    OperatorService,
    create_operator_server,
    load_operator_profile,
)


class _Inspector:
    def __init__(self, values: dict[str, list[int]] | None = None) -> None:
        self.values = values or {}

    def pids(self, process_name: str) -> list[int]:
        return list(self.values.get(process_name, []))


class _Process:
    def __init__(self, pid: int = 4242) -> None:
        self.pid = pid
        self.exit_code: int | None = None
        self.stdin: _Stdin | None = None

    def poll(self) -> int | None:
        return self.exit_code


class _Popen:
    def __init__(self, *, stdin: "_Stdin | None" = None) -> None:
        self.calls: list[tuple[list[str], dict[str, object]]] = []
        self.process = _Process()
        self.configured_stdin = stdin or _Stdin()

    def __call__(self, command: list[str], **kwargs: object) -> _Process:
        self.calls.append((command, kwargs))
        if kwargs.get("stdin") == subprocess.PIPE:
            self.process.stdin = self.configured_stdin
        return self.process


class _Stdin:
    def __init__(
        self, *, fail_on_write: bool = False, fail_on_flush: bool = False
    ) -> None:
        self.writes: list[bytes] = []
        self.flush_count = 0
        self.fail_on_write = fail_on_write
        self.fail_on_flush = fail_on_flush

    def write(self, payload: bytes) -> int:
        if self.fail_on_write:
            raise BrokenPipeError("fixture write failure")
        self.writes.append(payload)
        return len(payload)

    def flush(self) -> None:
        self.flush_count += 1
        if self.fail_on_flush:
            raise BrokenPipeError("fixture flush failure")


class OperatorMcpTests(unittest.TestCase):
    def _profile(self, root: Path, *, controls: dict[str, str] | None = None):
        executable = root / "python.exe"
        executable.write_bytes(b"exe")
        wrapper = root / "managed_replay.py"
        wrapper.write_bytes(b"print('fixture')\n")
        state = root / "operator-state"
        absent = root / "live-output"
        payload = {
            "schema_version": 1,
            "target": {
                "id": "operator-a",
                "display_name": "Operator A",
                "expected": {
                    "token_user": "DOMAIN\\operator",
                    "desktop": "WinSta0\\Default",
                    "machine": "TARGET-A",
                },
            },
            "endpoint": {
                "transport": "streamable-http",
                "host": "127.0.0.1",
                "port": 9876,
                "advertised_url": "http://127.0.0.1:9876/mcp",
            },
            "state_directory": str(state),
            "jobs": {
                "replay": {
                    "command": [str(executable), str(wrapper), "--launch"],
                    "working_directory": str(root),
                    "exclusive_process_names": ["ck3.exe"],
                    "required_paths": [
                        {
                            "path": str(wrapper),
                            "kind": "file",
                            "size": wrapper.stat().st_size,
                            "sha256": hashlib.sha256(wrapper.read_bytes())
                            .hexdigest()
                            .upper(),
                        }
                    ],
                    "absent_paths": [str(absent)],
                }
            },
        }
        if controls is not None:
            payload["jobs"]["replay"]["controls"] = controls
        profile_path = root / "operator.json"
        profile_path.write_text(json.dumps(payload), encoding="utf-8")
        return load_operator_profile(profile_path), state

    @staticmethod
    def _identity() -> HostIdentity:
        return HostIdentity(
            token_user="domain\\OPERATOR",
            desktop="winsta0\\default",
            machine="target-a",
            process_id=100,
        )

    def test_profile_is_target_configured_and_command_is_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile, _state = self._profile(Path(temporary))
        self.assertEqual(profile.target_id, "operator-a")
        self.assertEqual(profile.jobs["replay"].command[-1], "--launch")
        self.assertEqual(len(profile.source_sha256), 64)

    def test_profile_rejects_relative_executable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile, _state = self._profile(root)
            payload = json.loads(profile.source_path.read_text(encoding="utf-8"))
            payload["jobs"]["replay"]["command"][0] = "python.exe"
            profile.source_path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(OperatorProfileError, "must be an absolute"):
                load_operator_profile(profile.source_path)

    def test_preflight_is_green_only_on_exact_target_and_empty_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile, _state = self._profile(Path(temporary))
            service = OperatorService(
                profile,
                identity_probe=self._identity,
                process_inspector=_Inspector(),
            )
            result = service.preflight_job("operator-a", "replay")
            self.assertEqual(result["result"], "GREEN")
            self.assertEqual(result["observations"]["process_gates"]["ck3.exe"], [])
            self.assertEqual(len(result["evidence_sha256"]), 64)

            mismatch = OperatorService(
                profile,
                identity_probe=lambda: HostIdentity(
                    "sandbox", "WinSta0\\Private", "TARGET-A", 101
                ),
                process_inspector=_Inspector(),
            ).preflight_job("operator-a", "replay")
            self.assertEqual(mismatch["result"], "RED")
            self.assertIn("target_identity_exact", mismatch["failed_checks"])

            occupied = OperatorService(
                profile,
                identity_probe=self._identity,
                process_inspector=_Inspector({"ck3.exe": [777]}),
            ).preflight_job("operator-a", "replay")
            self.assertEqual(occupied["result"], "RED")
            self.assertIn("process_absent:ck3.exe", occupied["failed_checks"])

    def test_handoff_launches_only_profile_command_and_retry_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile, state = self._profile(Path(temporary))
            popen = _Popen()
            service = OperatorService(
                profile,
                identity_probe=self._identity,
                process_inspector=_Inspector(),
                popen_factory=popen,
                clock=lambda: 123.5,
            )
            first = service.handoff_job("operator-a", "replay", "request-1")
            second = service.handoff_job("operator-a", "replay", "request-1")
            self.assertEqual(first["result"], "ACCEPTED")
            self.assertFalse(first["idempotent_replay"])
            self.assertTrue(second["idempotent_replay"])
            self.assertEqual(first["job"]["job_id"], second["job"]["job_id"])
            self.assertEqual(first["job"]["pid"], 4242)
            self.assertEqual(len(popen.calls), 1)
            self.assertEqual(popen.calls[0][0], list(profile.jobs["replay"].command))
            self.assertEqual(
                popen.calls[0][1]["cwd"],
                str(profile.jobs["replay"].working_directory),
            )
            self.assertEqual(popen.calls[0][1]["stdin"], subprocess.DEVNULL)
            self.assertTrue(
                Path(first["job"]["stdout_path"]).is_relative_to(state)
            )
            self.assertTrue(
                Path(first["job"]["stderr_path"]).is_relative_to(state)
            )
            handoff = (
                Path(first["job"]["stdout_path"]).parent / "handoff.json"
            )
            self.assertTrue(handoff.is_file())

    def test_handoff_rejects_red_or_unconfigured_target_and_job(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile, _state = self._profile(Path(temporary))
            service = OperatorService(
                profile,
                identity_probe=self._identity,
                process_inspector=_Inspector({"ck3.exe": [9]}),
                popen_factory=_Popen(),
            )
            with self.assertRaisesRegex(OperatorHandoffError, "target mismatch"):
                service.handoff_job("operator-b", "replay", "request-1")
            with self.assertRaisesRegex(OperatorHandoffError, "not configured"):
                service.handoff_job("operator-a", "other", "request-1")
            with self.assertRaisesRegex(OperatorHandoffError, "preflight RED"):
                service.handoff_job("operator-a", "replay", "request-1")

    def test_named_control_uses_pipe_and_retry_writes_only_once(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile, _state = self._profile(
                Path(temporary), controls={"resume": "resume\n", "stop": "stop\n"}
            )
            popen = _Popen()
            service = OperatorService(
                profile,
                identity_probe=self._identity,
                process_inspector=_Inspector(),
                popen_factory=popen,
            )
            handed_off = service.handoff_job("operator-a", "replay", "launch-1")
            job_id = handed_off["job"]["job_id"]
            self.assertEqual(popen.calls[0][1]["stdin"], subprocess.PIPE)
            self.assertEqual(
                handed_off["job"]["available_controls"], ["resume", "stop"]
            )

            first = service.control_job(
                "operator-a", "replay", job_id, "resume", "control-1"
            )
            popen.process.exit_code = 0
            second = service.control_job(
                "operator-a", "replay", job_id, "resume", "control-1"
            )
            self.assertEqual(first["result"], "ACCEPTED")
            self.assertFalse(first["idempotent_replay"])
            self.assertTrue(second["idempotent_replay"])
            self.assertEqual(popen.configured_stdin.writes, [b"resume\n"])
            self.assertEqual(popen.configured_stdin.flush_count, 1)
            with self.assertRaisesRegex(OperatorHandoffError, "different job control"):
                service.control_job(
                    "operator-a", "replay", job_id, "stop", "control-1"
                )
            self.assertEqual(
                service.capabilities()["job_controls"],
                {"replay": ["resume", "stop"]},
            )
            self.assertEqual(
                service.status("operator-a")["jobs"][0]["available_controls"],
                ["resume", "stop"],
            )

    def test_control_rejects_unknown_exited_wrong_job_and_wrong_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile, _state = self._profile(
                Path(temporary), controls={"resume": "resume\n"}
            )
            popen = _Popen()
            service = OperatorService(
                profile,
                identity_probe=self._identity,
                process_inspector=_Inspector(),
                popen_factory=popen,
            )
            job_id = service.handoff_job(
                "operator-a", "replay", "launch-1"
            )["job"]["job_id"]
            with self.assertRaisesRegex(OperatorHandoffError, "target mismatch"):
                service.control_job(
                    "operator-b", "replay", job_id, "resume", "control-target"
                )
            with self.assertRaisesRegex(OperatorHandoffError, "not configured"):
                service.control_job(
                    "operator-a", "other", job_id, "resume", "control-job"
                )
            with self.assertRaisesRegex(OperatorHandoffError, "does not exist"):
                service.control_job(
                    "operator-a", "replay", "missing-job", "resume", "control-id"
                )
            with self.assertRaisesRegex(OperatorHandoffError, "not configured"):
                service.control_job(
                    "operator-a", "replay", job_id, "unknown", "control-name"
                )
            popen.process.exit_code = 9
            with self.assertRaisesRegex(OperatorHandoffError, "already exited"):
                service.control_job(
                    "operator-a", "replay", job_id, "resume", "control-exited"
                )
            self.assertEqual(popen.configured_stdin.writes, [])

    def test_control_write_or_flush_failure_is_red_and_not_retried(self) -> None:
        for failure in ("write", "flush"):
            with (
                self.subTest(failure=failure),
                tempfile.TemporaryDirectory() as temporary,
            ):
                profile, _state = self._profile(
                    Path(temporary), controls={"resume": "resume\n"}
                )
                stream = _Stdin(
                    fail_on_write=failure == "write",
                    fail_on_flush=failure == "flush",
                )
                popen = _Popen(stdin=stream)
                service = OperatorService(
                    profile,
                    identity_probe=self._identity,
                    process_inspector=_Inspector(),
                    popen_factory=popen,
                )
                job_id = service.handoff_job(
                    "operator-a", "replay", "launch-1"
                )["job"]["job_id"]
                first = service.control_job(
                    "operator-a", "replay", job_id, "resume", "control-red"
                )
                second = service.control_job(
                    "operator-a", "replay", job_id, "resume", "control-red"
                )
                self.assertEqual(first["result"], "RED")
                self.assertIn("BrokenPipeError", first["error"])
                self.assertTrue(second["idempotent_replay"])
                self.assertEqual(
                    stream.writes,
                    [] if failure == "write" else [b"resume\n"],
                )
                self.assertEqual(stream.flush_count, 0 if failure == "write" else 1)


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class OperatorMcpSdkTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_and_calls_operator_tools(self) -> None:
        from mcp import Client

        with tempfile.TemporaryDirectory() as temporary:
            fixture = OperatorMcpTests()
            profile, _state = fixture._profile(
                Path(temporary), controls={"resume": "resume\n"}
            )
            popen = _Popen()
            service = OperatorService(
                profile,
                identity_probe=fixture._identity,
                process_inspector=_Inspector(),
                popen_factory=popen,
            )
            server = create_operator_server(service)
            async with Client(server) as client:
                listed = await client.list_tools()
                self.assertEqual(
                    {tool.name for tool in listed.tools},
                    {
                        "operator_get_capabilities",
                        "operator_get_status",
                        "operator_preflight_job",
                        "operator_handoff_job",
                        "operator_control_job",
                    },
                )
                tools = {tool.name: tool for tool in listed.tools}
                self.assertTrue(
                    tools["operator_get_capabilities"].annotations.read_only_hint
                )
                self.assertTrue(
                    tools["operator_preflight_job"].annotations.read_only_hint
                )
                self.assertFalse(
                    tools["operator_handoff_job"].annotations.read_only_hint
                )
                self.assertTrue(
                    tools["operator_handoff_job"].annotations.idempotent_hint
                )
                self.assertFalse(
                    tools["operator_control_job"].annotations.read_only_hint
                )
                self.assertTrue(
                    tools["operator_control_job"].annotations.idempotent_hint
                )
                capabilities = await client.call_tool(
                    "operator_get_capabilities", {}
                )
                self.assertFalse(capabilities.is_error)
                self.assertEqual(
                    capabilities.structured_content["target_id"], "operator-a"
                )
                preflight = await client.call_tool(
                    "operator_preflight_job",
                    {"target_id": "operator-a", "job_name": "replay"},
                )
                self.assertFalse(preflight.is_error)
                self.assertEqual(preflight.structured_content["result"], "GREEN")
                handoff = await client.call_tool(
                    "operator_handoff_job",
                    {
                        "target_id": "operator-a",
                        "job_name": "replay",
                        "request_id": "launch-1",
                    },
                )
                self.assertFalse(handoff.is_error)
                control = await client.call_tool(
                    "operator_control_job",
                    {
                        "target_id": "operator-a",
                        "job_name": "replay",
                        "job_id": handoff.structured_content["job"]["job_id"],
                        "control_name": "resume",
                        "request_id": "control-1",
                    },
                )
                self.assertFalse(control.is_error)
                self.assertEqual(control.structured_content["result"], "ACCEPTED")
                self.assertEqual(popen.configured_stdin.writes, [b"resume\n"])


if __name__ == "__main__":
    unittest.main()
