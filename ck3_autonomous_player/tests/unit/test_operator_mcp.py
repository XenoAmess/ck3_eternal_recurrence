from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
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

    def poll(self) -> int | None:
        return self.exit_code


class _Popen:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], dict[str, object]]] = []
        self.process = _Process()

    def __call__(self, command: list[str], **kwargs: object) -> _Process:
        self.calls.append((command, kwargs))
        return self.process


class OperatorMcpTests(unittest.TestCase):
    def _profile(self, root: Path):
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


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class OperatorMcpSdkTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_and_calls_operator_tools(self) -> None:
        from mcp import Client

        with tempfile.TemporaryDirectory() as temporary:
            fixture = OperatorMcpTests()
            profile, _state = fixture._profile(Path(temporary))
            service = OperatorService(
                profile,
                identity_probe=fixture._identity,
                process_inspector=_Inspector(),
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


if __name__ == "__main__":
    unittest.main()
