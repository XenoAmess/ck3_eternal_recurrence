from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import xar_autoplayer.codex_mcp_setup as setup


class _RecordingRunner:
    def __init__(self, results: list[setup.CommandResult]) -> None:
        self.results = list(results)
        self.commands: list[list[str]] = []

    def __call__(self, command: object) -> setup.CommandResult:
        self.commands.append(list(command))
        if not self.results:
            raise AssertionError(f"unexpected command: {command}")
        return self.results.pop(0)


def _codex_payload(layout: setup.PortableMcpLayout) -> str:
    command = setup.mcp_server_arguments(layout)
    return json.dumps(
        {
            "name": layout.server_name,
            "enabled": True,
            "transport": {
                "type": "stdio",
                "command": command[0],
                "args": command[1:],
                "env": None,
                "env_vars": [],
                "cwd": None,
            },
        }
    )


def _offline_knowledge_payload(
    *,
    tool_listed: bool = True,
    contract_count: int | None = None,
    analysis_count: int | None = None,
) -> str:
    manifest = setup.current_vanilla_event_knowledge_manifest()
    return json.dumps({
        "tool_listed": tool_listed,
        "all_offline_tools_listed": True,
        "contract_count": (
            manifest["current_contract_count"]
            if contract_count is None
            else contract_count
        ),
        "analysis_count": (
            manifest["current_analysis_count"]
            if analysis_count is None
            else analysis_count
        ),
        "analysis_keyset_matches_contracts": True,
        "query_is_error": False,
        "query_event_definition_key": (
            setup.VANILLA_EVENT_KNOWLEDGE_PROBE_KEY
        ),
        "query_status": "available",
        "query_contract_non_null": True,
        "query_analysis_non_null": True,
        "knowledge_list_is_error": False,
        "knowledge_list_status": "available",
        "knowledge_dataset_sha256": manifest["knowledge_dataset_sha256"],
        "evidence_list_is_error": False,
        "evidence_list_status": "available",
        "evidence_count": manifest["portable_evidence_count"],
        "evidence_dataset_sha256": manifest[
            "portable_evidence_dataset_sha256"
        ],
        "evidence_read_is_error": False,
        "evidence_read_status": "available",
        "evidence_read_id_matches": True,
        "source_is_error": False,
        "source_status": "available",
        "source_dataset_sha256": manifest[
            "source_provenance_dataset_sha256"
        ],
        "source_candidates_lexical_only": True,
        "requires_ck3": False,
    })


class PortableCodexMcpSetupTests(unittest.TestCase):
    def _layout(self, root: Path, *, account: str | None = None) -> setup.PortableMcpLayout:
        selected = account or setup.current_windows_account()
        return setup.build_layout(
            account=selected,
            local_app_data=root / "local",
            codex_command=root / "bin" / "codex.CMD",
            bootstrap_python=sys.executable,
            game_dir=root / "game",
            bridge_dll=root / "native" / "xar_ck3_bridge.dll",
            bridge_injector=root / "native" / "xar_ck3_bridge_injector.exe",
        )

    def _materialize_runtime_files(self, layout: setup.PortableMcpLayout) -> None:
        layout.venv_python.parent.mkdir(parents=True)
        layout.venv_python.write_bytes(b"python")
        assert layout.codex_command is not None
        layout.codex_command.parent.mkdir(parents=True)
        layout.codex_command.write_bytes(b"codex")

    def test_account_slug_is_stable_and_rejects_empty(self) -> None:
        self.assertEqual(setup.safe_account_slug("Codex Sandbox Offline"), "codex-sandbox-offline")
        self.assertEqual(setup.safe_account_slug("XENOA"), "xenoa")
        with self.assertRaises(setup.PortableMcpSetupError):
            setup.safe_account_slug("  中文  ")

    def test_xenoa_and_offline_defaults_are_disjoint(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            xenoa = self._layout(root, account="xenoa")
            offline = self._layout(root, account="CodexSandboxOffline")
        self.assertNotEqual(xenoa.server_name, offline.server_name)
        self.assertNotEqual(xenoa.pipe_name, offline.pipe_name)
        self.assertNotEqual(xenoa.state_dir, offline.state_dir)
        self.assertNotEqual(xenoa.userdir, offline.userdir)
        self.assertTrue(str(xenoa.userdir).startswith(str(xenoa.state_dir)))
        self.assertTrue(str(offline.userdir).startswith(str(offline.state_dir)))

    def test_shared_or_non_account_pipe_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaisesRegex(
                setup.PortableMcpSetupError, "account slug"
            ):
                setup.build_layout(
                    account="xenoa",
                    local_app_data=raw,
                    pipe_name=r"\\.\pipe\xar_ck3_bridge_mcp_shared",
                )

    def test_mcp_registration_reuses_repository_server_and_native_driver(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            layout = self._layout(Path(raw))
        arguments = setup.mcp_server_arguments(layout)
        self.assertEqual(arguments[0], str(layout.venv_python))
        self.assertEqual(arguments[1], str(setup.REPOSITORY_MCP_SERVER))
        self.assertEqual(arguments[2:4], ["--driver", "native-headless"])
        self.assertIn(str(layout.state_dir), arguments)
        self.assertIn(str(layout.userdir), arguments)
        self.assertIn(layout.pipe_name, arguments)
        self.assertNotIn("native-session", arguments)

    def test_plan_exposes_existing_generic_rebind_and_never_launches_ck3(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            plan = setup.render_plan(self._layout(Path(raw)))
        self.assertFalse(plan["launches_ck3"])
        self.assertEqual(
            plan["generic_rebind"]["tool"], setup.SET_PLAYED_CHARACTER_TOOL
        )
        self.assertEqual(
            plan["generic_rebind"]["capability"],
            setup.SET_PLAYED_CHARACTER_CAPABILITY,
        )
        self.assertTrue(plan["generic_rebind"]["provider_reused"])
        self.assertEqual(
            plan["install_command"][-2:], ["mcp==2.0.0", "pywin32==312"]
        )
        self.assertNotIn("onnxruntime", " ".join(plan["install_command"]))
        knowledge = plan["offline_vanilla_event_knowledge"]
        self.assertEqual(
            knowledge["tool"], setup.VANILLA_EVENT_KNOWLEDGE_TOOL
        )
        self.assertEqual(
            set(knowledge["tools"]),
            set(setup.VANILLA_EVENT_OFFLINE_TOOLS),
        )
        self.assertEqual(
            knowledge["schema"], "xar.ck3.vanilla-event-knowledge"
        )
        self.assertEqual(knowledge["schema_version"], 1)
        self.assertEqual(knowledge["current_contract_count"], 169)
        self.assertEqual(knowledge["current_analysis_count"], 169)
        self.assertEqual(len(knowledge["knowledge_dataset_sha256"]), 64)
        self.assertGreater(knowledge["portable_evidence_count"], 0)
        self.assertEqual(
            len(knowledge["portable_evidence_dataset_sha256"]), 64
        )
        self.assertEqual(
            len(knowledge["source_provenance_dataset_sha256"]), 64
        )
        self.assertEqual(
            knowledge["count_semantics"],
            "current-revision-data-fact-not-abi",
        )
        self.assertFalse(knowledge["requires_ck3"])

    def test_native_session_command_is_only_rendered_with_explicit_assets(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            layout = self._layout(root)
            command = setup.native_session_command(layout)
        assert command is not None
        self.assertIn("native-session", command)
        self.assertIn(str(layout.bridge_dll), command)
        self.assertIn(str(layout.bridge_injector), command)
        self.assertIn(layout.pipe_name, command)

    def test_codex_config_match_accepts_real_cli_json_shape(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            layout = self._layout(Path(raw))
        payload = json.loads(_codex_payload(layout))
        self.assertTrue(setup.codex_config_matches(layout, payload))
        payload["transport"]["args"][-1] = "streamable-http"
        self.assertFalse(setup.codex_config_matches(layout, payload))

    def test_register_is_idempotent_for_exact_existing_entry(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            layout = self._layout(Path(raw))
            self._materialize_runtime_files(layout)
            runner = _RecordingRunner(
                [setup.CommandResult(0, _codex_payload(layout))]
            )
            result = setup.register_codex_mcp(layout, runner=runner)
            self.assertEqual(result["result"], "already_registered")
            self.assertTrue(layout.marker_path.is_file())
        self.assertEqual(len(runner.commands), 1)
        self.assertEqual(runner.commands[0][-2:], [layout.server_name, "--json"])

    def test_register_adds_and_reads_back_without_starting_server(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            layout = self._layout(Path(raw))
            self._materialize_runtime_files(layout)
            runner = _RecordingRunner(
                [
                    setup.CommandResult(1, stderr="not configured"),
                    setup.CommandResult(0, "Added"),
                    setup.CommandResult(0, _codex_payload(layout)),
                ]
            )
            result = setup.register_codex_mcp(layout, runner=runner)
        self.assertEqual(result["result"], "registered")
        self.assertEqual(runner.commands[1], setup.codex_add_command(layout))
        self.assertNotIn("native-session", runner.commands[1])

    def test_register_does_not_overwrite_different_entry_without_replace(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            layout = self._layout(Path(raw))
            self._materialize_runtime_files(layout)
            different = json.loads(_codex_payload(layout))
            different["transport"]["command"] = r"C:\wrong\python.exe"
            runner = _RecordingRunner(
                [setup.CommandResult(0, json.dumps(different))]
            )
            with self.assertRaisesRegex(
                setup.PortableMcpSetupError, "different command"
            ):
                setup.register_codex_mcp(layout, runner=runner)
        self.assertEqual(len(runner.commands), 1)

    def test_register_replace_is_explicit_and_read_back(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            layout = self._layout(Path(raw))
            self._materialize_runtime_files(layout)
            different = json.loads(_codex_payload(layout))
            different["transport"]["args"] = ["wrong"]
            runner = _RecordingRunner(
                [
                    setup.CommandResult(0, json.dumps(different)),
                    setup.CommandResult(0, "Removed"),
                    setup.CommandResult(0, "Added"),
                    setup.CommandResult(0, _codex_payload(layout)),
                ]
            )
            result = setup.register_codex_mcp(
                layout, replace=True, runner=runner
            )
        self.assertEqual(result["result"], "registered")
        self.assertEqual(runner.commands[1][-3:], ["mcp", "remove", layout.server_name])

    def test_apply_refuses_to_write_another_accounts_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            layout = self._layout(Path(raw), account="definitely-not-current")
            with self.assertRaisesRegex(
                setup.PortableMcpSetupError, "must run as"
            ):
                setup.register_codex_mcp(layout, runner=_RecordingRunner([]))

    def test_doctor_green_requires_exact_registration_and_exact_game_build(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            layout = self._layout(Path(raw))
            self._materialize_runtime_files(layout)
            game_exe = layout.game_dir / "binaries" / "ck3.exe"
            game_exe.parent.mkdir(parents=True)
            game_exe.write_bytes(b"exact-fixture")
            assert layout.bridge_dll is not None
            assert layout.bridge_injector is not None
            layout.bridge_dll.parent.mkdir(parents=True)
            layout.bridge_dll.write_bytes(b"dll")
            layout.bridge_injector.write_bytes(b"injector")
            setup._write_layout_marker(layout)
            runner = _RecordingRunner(
                [
                    setup.CommandResult(0),
                    setup.CommandResult(0, "usage"),
                    setup.CommandResult(0, _offline_knowledge_payload()),
                    setup.CommandResult(0, _codex_payload(layout)),
                ]
            )
            with mock.patch.object(
                setup, "_sha256", return_value=setup.EXACT_CK3_SHA256
            ):
                report = setup.doctor(
                    layout,
                    require_native_assets=True,
                    runner=runner,
                )
        self.assertEqual(report["result"], "GREEN")
        self.assertTrue(report["registered_exact"])
        self.assertTrue(report["native_session_assets_ready"])
        self.assertEqual(
            report["offline_vanilla_event_knowledge"]["contract_count"],
            169,
        )
        self.assertEqual(
            report["offline_vanilla_event_knowledge"]["analysis_count"],
            169,
        )
        self.assertFalse(report["launches_ck3"])
        self.assertEqual(len(runner.commands), 4)

    def test_doctor_reports_unregistered_without_starting_ck3(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            layout = self._layout(Path(raw))
            self._materialize_runtime_files(layout)
            setup._write_layout_marker(layout)
            runner = _RecordingRunner(
                [
                    setup.CommandResult(0),
                    setup.CommandResult(0, "usage"),
                    setup.CommandResult(0, _offline_knowledge_payload()),
                    setup.CommandResult(1, stderr="not configured"),
                ]
            )
            report = setup.doctor(layout, runner=runner)
        self.assertEqual(report["result"], "RED")
        self.assertEqual(report["failed_checks"], ["codex_registration"])
        self.assertFalse(report["registered_exact"])
        self.assertTrue(all("native-session" not in row for row in runner.commands))

    def test_doctor_rejects_stale_offline_knowledge_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            layout = self._layout(Path(raw))
            self._materialize_runtime_files(layout)
            setup._write_layout_marker(layout)
            runner = _RecordingRunner(
                [
                    setup.CommandResult(0),
                    setup.CommandResult(0, "usage"),
                    setup.CommandResult(
                        0,
                        _offline_knowledge_payload(analysis_count=156),
                    ),
                    setup.CommandResult(0, _codex_payload(layout)),
                ]
            )
            report = setup.doctor(layout, runner=runner)
        self.assertEqual(report["result"], "RED")
        self.assertEqual(
            report["failed_checks"],
            ["offline_vanilla_event_knowledge"],
        )
        self.assertEqual(
            report["offline_vanilla_event_knowledge"]["analysis_count"],
            156,
        )
        self.assertEqual(
            report["offline_vanilla_event_knowledge"][
                "expected_current_analysis_count"
            ],
            169,
        )

    @unittest.skipUnless(
        os.name == "nt" and importlib.util.find_spec("mcp") is not None,
        "installed-runtime MCP smoke requires Windows and the optional SDK",
    )
    def test_installed_runtime_lists_and_calls_offline_knowledge_tool(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            layout = setup.build_layout(
                account=setup.current_windows_account(),
                local_app_data=root / "local",
                venv_dir=Path(sys.executable).resolve().parents[1],
                state_dir=root / "state",
                userdir=root / "state" / "profile",
                codex_command=root / "bin" / "codex.CMD",
                bootstrap_python=sys.executable,
                game_dir=root / "game",
            )
            passed, detail, payload = (
                setup._check_offline_vanilla_event_knowledge(
                    layout,
                    setup._run_command,
                )
            )
        self.assertTrue(passed, detail)
        self.assertTrue(payload["tool_listed"])
        self.assertTrue(payload["all_offline_tools_listed"])
        self.assertEqual(payload["contract_count"], 169)
        self.assertEqual(payload["analysis_count"], 169)
        self.assertEqual(payload["query_status"], "available")
        self.assertTrue(payload["query_analysis_non_null"])
        self.assertEqual(payload["knowledge_list_status"], "available")
        self.assertEqual(payload["evidence_list_status"], "available")
        self.assertEqual(payload["evidence_read_status"], "available")
        self.assertEqual(payload["source_status"], "available")
        self.assertTrue(payload["source_candidates_lexical_only"])
        self.assertFalse(payload["requires_ck3"])


if __name__ == "__main__":
    unittest.main()
