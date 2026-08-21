from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest import mock


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.environment import (  # noqa: E402
    OUTER_DESCRIPTOR_REF,
    REPO_ROOT,
    AgentError,
    EnvironmentSpec,
    ck3_process_inventory,
    ensure_state_path_safe,
    prepare_profile,
    sha256_file,
    verify_profile,
)
from xar_autoplayer.locking import exclusive_state_lock  # noqa: E402
from xar_autoplayer.process_watchdog import (  # noqa: E402
    _fallback_children,
    _matches,
    _parent_matches,
    _terminate_authenticated,
    _unlink_if_owned,
)
from xar_autoplayer.rules import MOD_RULES, rule_contract  # noqa: E402
from xar_autoplayer.runtime import (  # noqa: E402
    SessionHandle,
    _assign_process_to_job,
    _authenticated_watchdog_state,
    _close_job,
    _create_kill_on_close_job,
    _create_suspended_process,
    _job_active_processes,
    _process_identity,
    _start_process_watchdog,
    _stop_authenticated_watchdog,
    append_event,
    _terminate_job,
    parse_runtime_attestation,
    stop_tracked,
    unique_exact_ocr_match,
    validate_event_chain,
    validate_final_report_payload,
    wait_for_main_menu,
    wait_for_runtime_attestation,
)
from xar_autoplayer.integrity import steam_userdata_snapshot  # noqa: E402


GAME_DIR = REPO_ROOT / "Crusader Kings III"


class RuleContractTests(unittest.TestCase):
    def test_contract_is_vanilla_defaults_plus_exact_mod_track(self) -> None:
        path = GAME_DIR / "game" / "common" / "game_rules" / "00_game_rules.txt"
        contract = rule_contract(path)
        self.assertEqual(contract["declared_vanilla_rule_count"], 81)
        self.assertEqual(
            [
                (entry["rule"], entry["setting"])
                for entry in contract["profile"][-3:]
            ],
            list(MOD_RULES),
        )
        self.assertFalse(contract["ironman"])


class PathSafetyTests(unittest.TestCase):
    def test_rejects_parent_or_child_overlap(self) -> None:
        protected = Path("C:/protected/root")
        cases = (protected, protected / "child", protected.parent)
        for candidate in cases:
            with self.subTest(candidate=candidate):
                with self.assertRaises(AgentError):
                    ensure_state_path_safe(candidate, [("fixture", protected)])

    def test_accepts_disjoint_path(self) -> None:
        ensure_state_path_safe(
            Path("C:/agent-state"), [("fixture", Path("D:/protected"))]
        )


class PreparedProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.process_patch = mock.patch(
            "xar_autoplayer.environment.ck3_processes", return_value=[]
        )
        self.process_patch.start()
        self.addCleanup(self.process_patch.stop)

    def test_prepare_is_single_mod_and_preserves_tutorial(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-agent-test-") as temporary:
            spec = EnvironmentSpec(Path(temporary).resolve(), GAME_DIR.resolve())
            first = prepare_profile(spec)
            self.assertEqual(
                first["load_profile"]["enabled_mods"], [OUTER_DESCRIPTOR_REF]
            )
            tutorial = spec.profile_dir / "tutorial.txt"
            sentinel = tutorial.read_bytes() + b"# persistent-fixture\n"
            tutorial.write_bytes(sentinel)
            second = prepare_profile(spec)
            self.assertEqual(tutorial.read_bytes(), sentinel)
            self.assertFalse(
                second["persistent_tutorial_state"]["initialized_this_prepare"]
            )
            verify_profile(spec)

    def test_verify_rejects_a_second_mod(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-agent-test-") as temporary:
            spec = EnvironmentSpec(Path(temporary).resolve(), GAME_DIR.resolve())
            prepare_profile(spec)
            path = spec.profile_dir / "dlc_load.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["enabled_mods"].append("mod/forbidden.mod")
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(AgentError, "exact singleton"):
                verify_profile(spec)

    def test_verify_rejects_settings_and_outer_descriptor_drift(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-agent-test-") as temporary:
            spec = EnvironmentSpec(Path(temporary).resolve(), GAME_DIR.resolve())
            prepare_profile(spec)
            settings = spec.profile_dir / "pdx_settings.txt"
            settings.write_text(
                settings.read_text(encoding="utf-8").replace(
                    'value="2560x1440"', 'value="1920x1080"'
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(AgentError, "pdx_settings contract differs"):
                verify_profile(spec)
            prepare_profile(spec)
            outer = spec.profile_dir / "mod" / "xar_autoplayer.mod"
            outer.write_bytes(outer.read_bytes() + b"# drift\n")
            with self.assertRaisesRegex(AgentError, "outer descriptor fingerprint"):
                verify_profile(spec)

    def test_verify_rechecks_ck3_executable_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-agent-test-") as temporary:
            spec = EnvironmentSpec(Path(temporary).resolve(), GAME_DIR.resolve())
            prepare_profile(spec)
            original = sha256_file

            def changed(path: Path) -> str:
                if Path(path).resolve() == spec.game_exe.resolve():
                    return "0" * 64
                return original(Path(path))

            with mock.patch(
                "xar_autoplayer.environment.sha256_file", side_effect=changed
            ):
                with self.assertRaisesRegex(AgentError, "executable fingerprint"):
                    verify_profile(spec)

    def test_development_projection_does_not_invent_a_git_tag(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-agent-test-") as temporary:
            spec = EnvironmentSpec(Path(temporary).resolve(), GAME_DIR.resolve())
            manifest = prepare_profile(spec)
            provenance = manifest["mod"]["source_provenance"]
            tag = manifest["mod"]["release_identity"]["git_tag"]
            self.assertIn(tag, (None, f"v{manifest['mod']['release_identity']['mod_version']}"))
            if tag is not None:
                self.assertIn(tag, provenance["git_tags_at_revision"])


class RuntimeAttestationTests(unittest.TestCase):
    def test_final_report_is_bound_to_the_hash_chain_tail(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-agent-report-") as temporary:
            events = Path(temporary) / "events.jsonl"
            append_event(events, {"kind": "smoke_started"})
            tail = append_event(events, {"kind": "smoke_finished", "ok": True})
            chain = validate_event_chain(events)
            report = {
                "finalized": True,
                "ok": True,
                "final_event_sha256": tail,
            }
            validate_final_report_payload(report, chain)
            lines = events.read_text(encoding="utf-8").splitlines()
            tampered = json.loads(lines[0])
            tampered["kind"] = "changed"
            lines[0] = json.dumps(tampered)
            events.write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(AgentError, "digest differs"):
                validate_event_chain(events)

    def test_fresh_session_and_exact_mount_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-agent-test-") as temporary:
            profile = Path(temporary).resolve() / "profile"
            production = profile / "mod-content" / "xar-production"
            text = "\n".join(
                [
                    "Log system initialized current",
                    "琉焰卿的永恒轮回|mod/xar_autoplayer.mod|Enabled",
                    f"Mounted Data: {production}",
                ]
            )
            result = parse_runtime_attestation(text, profile, production)
            self.assertEqual(
                result["enabled_mods"][0]["descriptor"], OUTER_DESCRIPTOR_REF
            )
            self.assertEqual(
                result["isolated_mod_mounts"], [str(production.resolve())]
            )

    def test_rejects_a_persistent_log_with_an_old_session(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-agent-test-") as temporary:
            profile = Path(temporary).resolve() / "profile"
            production = profile / "mod-content" / "xar-production"
            text = "\n".join(
                [
                    "Log system initialized old",
                    "Other|mod/other.mod|Enabled",
                    "Log system initialized current",
                    "琉焰卿的永恒轮回|mod/xar_autoplayer.mod|Enabled",
                    f"Mounted Data: {production}",
                ]
            )
            with self.assertRaisesRegex(AgentError, "exactly one"):
                parse_runtime_attestation(text, profile, production)

    def test_rejects_runtime_extra_mod(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-agent-test-") as temporary:
            profile = Path(temporary).resolve() / "profile"
            production = profile / "mod-content" / "xar-production"
            text = "\n".join(
                [
                    "Log system initialized current",
                    "琉焰卿的永恒轮回|mod/xar_autoplayer.mod|Enabled",
                    "Other|mod/other.mod|Enabled",
                    f"Mounted Data: {production}",
                ]
            )
            with self.assertRaisesRegex(AgentError, "exact singleton"):
                parse_runtime_attestation(text, profile, production)

    def test_rejects_an_external_unclassified_mount(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-agent-test-") as temporary:
            root = Path(temporary).resolve()
            profile = root / "profile"
            production = profile / "mod-content" / "xar-production"
            game = root / "game"
            text = "\n".join(
                [
                    "Log system initialized current",
                    "琉焰卿的永恒轮回|mod/xar_autoplayer.mod|Enabled",
                    f"Mounted Data: {production}",
                    f"Mounted Data: {root / 'external-mod'}",
                ]
            )
            with self.assertRaisesRegex(AgentError, "unclassified"):
                parse_runtime_attestation(text, profile, production, game)

    def test_wait_rejects_a_log_older_than_the_launch_epoch(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-agent-log-") as temporary:
            root = Path(temporary).resolve()
            spec = EnvironmentSpec(root, root / "game")
            path = spec.profile_dir / "logs" / "debug.log"
            path.parent.mkdir(parents=True)
            path.write_text("Log system initialized stale\n", encoding="utf-8")
            old = time.time_ns() - 10_000_000_000
            os.utime(path, ns=(old, old))
            handle = SimpleNamespace(log_epoch_ns=time.time_ns(), cleared_logs=[])
            with self.assertRaisesRegex(AgentError, "stale"):
                wait_for_runtime_attestation(spec, handle, timeout_seconds=0.01)


class VisibleMainMenuAttestationTests(unittest.TestCase):
    def test_unique_exact_match_nfkc_whitespace_and_ambiguity(self) -> None:
        normalized = {"text": "Ａ\u3000Ｂ\tＣ", "score": 0.9}
        self.assertIs(
            unique_exact_ocr_match([normalized], "ABC"),
            normalized,
        )
        self.assertIsNone(
            unique_exact_ocr_match([{"text": "新游戏教程"}], "新游戏")
        )
        self.assertIsNone(
            unique_exact_ocr_match(
                [{"text": "新游戏"}, {"text": " 新 游 戏 "}], "新游戏"
            )
        )
        self.assertIsNone(unique_exact_ocr_match([], "新游戏"))

    def test_wait_requires_two_consecutive_unique_frames_and_archives_both(
        self,
    ) -> None:
        class FakeImage:
            size = (2560, 1440)

            def __init__(self, payload: bytes) -> None:
                self.payload = payload

            def save(self, path: Path) -> None:
                Path(path).write_bytes(self.payload)

            def crop(self, _bbox: object) -> "FakeImage":
                return FakeImage(self.payload + b"-crop")

        images = [FakeImage(f"frame-{index}".encode("ascii")) for index in range(1, 5)]
        ocr_frames = [
            [{"text": " 新\u3000游 戏 ", "score": 0.9}],
            [
                {"text": "新游戏", "score": 0.9},
                {"text": " 新 游 戏 ", "score": 0.8},
            ],
            [{"text": "新游戏", "score": 0.91}],
            [{"text": " 新 游 戏 ", "score": 0.92}],
        ]
        process = SimpleNamespace(pid=321, returncode=None, poll=lambda: None)
        handle = SimpleNamespace(process=process)
        rect = (10, 20, 2570, 1460)

        with tempfile.TemporaryDirectory(prefix="xar-main-menu-") as temporary:
            artifacts = Path(temporary).resolve()
            with mock.patch(
                "PIL.ImageGrab.grab", side_effect=images
            ) as grab, mock.patch(
                "xar_autoplayer.runtime._window_for_pid",
                return_value=(99, rect),
            ), mock.patch(
                "xar_autoplayer.runtime._focus_window"
            ), mock.patch(
                "xar_autoplayer.runtime._ocr_items", side_effect=ocr_frames
            ), mock.patch(
                "xar_autoplayer.runtime.time.sleep"
            ):
                result = wait_for_main_menu(handle, artifacts, timeout_seconds=1)

            self.assertEqual(grab.call_count, 4)
            self.assertEqual(result["stable_frames"], 2)
            evidence = result["stable_frame_evidence"]
            self.assertEqual([entry["frame"] for entry in evidence], [1, 2])
            self.assertEqual(result["screenshot"], evidence[1]["screenshot"])
            self.assertEqual(result["ocr"], evidence[1]["ocr"])
            self.assertEqual(Path(evidence[0]["screenshot"]).read_bytes(), b"frame-3")
            self.assertEqual(Path(evidence[1]["screenshot"]).read_bytes(), b"frame-4")
            for entry in evidence:
                screenshot = Path(entry["screenshot"])
                ocr_path = Path(entry["ocr"])
                self.assertTrue(screenshot.is_file())
                self.assertTrue(ocr_path.is_file())
                self.assertEqual(sha256_file(screenshot), entry["screenshot_sha256"])
                self.assertEqual(sha256_file(ocr_path), entry["ocr_sha256"])
                items = json.loads(ocr_path.read_text(encoding="utf-8"))
                self.assertIsNotNone(unique_exact_ocr_match(items, "新游戏"))


class StateLockTests(unittest.TestCase):
    def test_second_thread_cannot_take_the_same_state_lock(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-agent-lock-") as temporary:
            state = Path(temporary).resolve()
            entered = threading.Event()
            release = threading.Event()

            def holder() -> None:
                with exclusive_state_lock(state, "holder"):
                    entered.set()
                    release.wait(timeout=10)

            thread = threading.Thread(target=holder)
            thread.start()
            self.assertTrue(entered.wait(timeout=5))
            try:
                with self.assertRaisesRegex(AgentError, "already locked"):
                    with exclusive_state_lock(state, "contender"):
                        self.fail("contender unexpectedly acquired the state lock")
            finally:
                release.set()
                thread.join(timeout=5)
            self.assertFalse(thread.is_alive())

    def test_second_process_cannot_take_the_same_state_lock(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-agent-lock-") as temporary:
            state = Path(temporary).resolve()
            ready = state / "child.ready"
            release = state / "child.release"
            code = (
                "import pathlib,sys,time;"
                "sys.path.insert(0,sys.argv[1]);"
                "from xar_autoplayer.locking import exclusive_state_lock;"
                "state=pathlib.Path(sys.argv[2]);"
                "ready=pathlib.Path(sys.argv[3]);"
                "release=pathlib.Path(sys.argv[4]);"
                "ctx=exclusive_state_lock(state,'child');ctx.__enter__();"
                "ready.write_text('ready');"
                "\nwhile not release.exists(): time.sleep(0.05)\n"
                "ctx.__exit__(None,None,None)"
            )
            child = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    code,
                    str(PACKAGE_ROOT),
                    str(state),
                    str(ready),
                    str(release),
                ]
            )
            deadline = time.monotonic() + 5
            while not ready.is_file() and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertTrue(ready.is_file())
            try:
                with self.assertRaisesRegex(AgentError, "already locked"):
                    with exclusive_state_lock(state, "parent"):
                        self.fail("parent unexpectedly acquired the child lock")
            finally:
                release.write_text("release", encoding="ascii")
                child.wait(timeout=5)
            self.assertEqual(child.returncode, 0)


class TrackedShutdownTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows tracked shutdown contract")
    def test_stop_tracked_freezes_proof_before_closing_real_process_handle(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-real-stop-") as temporary:
            root = Path(temporary)
            executable = Path(sys.executable)
            job = _create_kill_on_close_job()
            process = _create_suspended_process(
                [str(executable), "-c", "import time;time.sleep(60)"],
                executable.parent,
            )
            _assign_process_to_job(job, process)
            process.resume()
            nonce = "real-stop"
            creation = "fixture-creation"
            pid_file = root / "ck3.json"
            pid_file.write_text(
                json.dumps(
                    {
                        "format_version": 1,
                        "nonce": nonce,
                        "ck3_pid": process.pid,
                        "parent_pid": os.getpid(),
                        "executable": str(executable),
                        "creation_date": creation,
                    }
                ),
                encoding="utf-8",
            )
            marker = root / "unsafe-cleanup.json"
            marker.write_text(json.dumps({"nonce": nonce}), encoding="utf-8")
            ready = root / "watchdog.ready.json"
            ready.write_text("{}\n", encoding="ascii")
            handle = SessionHandle(
                process=process,
                pid_file=pid_file,
                watchdog_pid=54321,
                command=[str(executable)],
                log_epoch_ns=0,
                cleared_logs=[],
                nonce=nonce,
                record_file=pid_file,
                ready_file=ready,
                unsafe_marker=marker,
                ck3_creation_date=creation,
                watchdog_creation_date="watchdog-created",
                job_handle=job,
            )
            with mock.patch(
                "xar_autoplayer.runtime._authenticated_watchdog_state",
                side_effect=["running", "absent"],
            ), mock.patch(
                "xar_autoplayer.runtime._stop_authenticated_watchdog",
                return_value=True,
            ), mock.patch(
                "xar_autoplayer.runtime.ck3_process_inventory",
                return_value={
                    "tasklist_returncode": 0,
                    "tasklist_pids": [],
                    "wmi_pids": [],
                    "processes": [],
                },
            ):
                result = stop_tracked(handle, require_running=True)
            self.assertTrue(result["cleanup_proven"])
            self.assertEqual(result["job_active_processes_final"], 0)
            self.assertIsNone(process._process_handle)

    @unittest.skipUnless(
        os.environ.get("XAR_RUN_DESKTOP_INTEGRATION") == "1",
        "explicit desktop integration test",
    )
    def test_watchdog_ready_authenticates_the_parent_object(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-watchdog-ready-") as temporary:
            root = Path(temporary)
            parent = _process_identity(os.getpid())
            self.assertIsNotNone(parent)
            nonce = "integration-parent-identity"
            ready = root / "watchdog.ready.json"
            record = root / "ck3.json"
            marker = root / "unsafe-cleanup.json"
            watchdog_pid = 0
            creation_date = ""
            try:
                watchdog_pid, creation_date = _start_process_watchdog(
                    os.getpid(),
                    Path(str(parent["executable"])),
                    str(parent["creation_date"]),
                    nonce,
                    ready,
                    record,
                    marker,
                    GAME_DIR / "binaries" / "ck3.exe",
                )
                payload = json.loads(ready.read_text(encoding="ascii"))
                self.assertEqual(payload["parent_pid"], os.getpid())
                self.assertEqual(
                    payload["parent_creation_date"], parent["creation_date"]
                )
            finally:
                if watchdog_pid:
                    _stop_authenticated_watchdog(
                        watchdog_pid,
                        creation_date,
                        os.getpid(),
                        nonce,
                    )

    @unittest.skipUnless(os.name == "nt", "Windows Job Object contract")
    def test_suspended_process_is_assigned_before_resume(self) -> None:
        executable = Path(os.environ.get("ComSpec", "C:/Windows/System32/cmd.exe"))
        job = _create_kill_on_close_job()
        process = _create_suspended_process(
            [str(executable), "/d", "/c", "exit", "0"], executable.parent
        )
        try:
            self.assertIsNone(process.poll())
            self.assertFalse(process.resumed)
            self.assertEqual(process.image_path(), executable.resolve())
            _assign_process_to_job(job, process)
            self.assertEqual(_job_active_processes(job), 1)
            process.resume()
            self.assertEqual(process.wait(timeout=5), 0)
            self.assertEqual(_job_active_processes(job), 0)
        finally:
            process.terminate_exact()
            _close_job(job)
            process.close()

    @unittest.skipUnless(os.name == "nt", "Windows Job Object contract")
    def test_terminate_job_kills_the_spawned_process_tree(self) -> None:
        code = (
            "import subprocess,sys,time;"
            "subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);"
            "time.sleep(60)"
        )
        executable = Path(sys.executable)
        job = _create_kill_on_close_job()
        process = _create_suspended_process(
            [str(executable), "-c", code], executable.parent
        )
        try:
            _assign_process_to_job(job, process)
            process.resume()
            deadline = time.monotonic() + 5
            while _job_active_processes(job) < 2 and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertGreaterEqual(_job_active_processes(job), 2)
            _terminate_job(job)
            process.wait(timeout=5)
            deadline = time.monotonic() + 5
            while _job_active_processes(job) and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertEqual(_job_active_processes(job), 0)
        finally:
            if _job_active_processes(job):
                _terminate_job(job)
            _close_job(job)
            process.close()

    def test_corrupt_pid_file_does_not_prevent_held_process_cleanup(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-agent-stop-") as temporary:
            root = Path(temporary)
            pid_file = root / "ck3.json"
            pid_file.write_text("corrupt\n", encoding="ascii")
            process = mock.MagicMock()
            process.pid = 12345
            process.poll.side_effect = [None, 0, 0]
            job_handle = object()
            handle = SessionHandle(
                process=process,
                pid_file=pid_file,
                watchdog_pid=54321,
                command=["C:/game/ck3.exe"],
                log_epoch_ns=0,
                cleared_logs=[],
                nonce="test-nonce",
                record_file=pid_file,
                ready_file=root / "watchdog.ready.json",
                unsafe_marker=root / "unsafe-cleanup.json",
                ck3_creation_date="ck3-created",
                watchdog_creation_date="watchdog-created",
                job_handle=job_handle,
            )
            with mock.patch(
                "xar_autoplayer.runtime._authenticated_watchdog_state",
                side_effect=["running", "absent"],
            ), mock.patch(
                "xar_autoplayer.runtime._stop_authenticated_watchdog",
                return_value=True,
            ), mock.patch(
                "xar_autoplayer.runtime._terminate_job"
            ) as terminate_job, mock.patch(
                "xar_autoplayer.runtime._job_active_processes", side_effect=[1, 0]
            ), mock.patch(
                "xar_autoplayer.runtime._close_job"
            ), mock.patch(
                "xar_autoplayer.runtime.ck3_process_inventory",
                return_value={
                    "tasklist_returncode": 0,
                    "tasklist_pids": [],
                    "wmi_pids": [],
                    "processes": [],
                },
            ):
                result = stop_tracked(handle)
            self.assertFalse(result["ok"])
            self.assertIn("PID file is unavailable", result["contract_errors"][0])
            self.assertTrue(result["tree_gone"])
            self.assertTrue(result["cleanup_proven"])
            terminate_job.assert_called_once_with(job_handle)
            process.wait.assert_called_once()
            self.assertFalse(pid_file.exists())

    def test_watchdog_identity_rejects_a_reused_numeric_pid(self) -> None:
        process = SimpleNamespace(
            ProcessId=123,
            ParentProcessId=456,
            Name="notepad.exe",
            ExecutablePath="C:/Windows/notepad.exe",
            CreationDate="newer",
        )
        self.assertFalse(
            _matches(
                process,
                expected_pid=123,
                parent_pid=456,
                executable="C:/game/ck3.exe",
                creation_date="older",
            )
        )

    def test_watchdog_parent_identity_rejects_reused_pid(self) -> None:
        process = SimpleNamespace(
            ProcessId=456,
            ExecutablePath="C:/Python/python.exe",
            CreationDate="newer",
        )
        self.assertFalse(
            _parent_matches(
                process,
                expected_pid=456,
                executable="C:/Python/python.exe",
                creation_date="older",
            )
        )

    def test_watchdog_same_object_with_unverifiable_command_is_unknown(self) -> None:
        identity = {
            "pid": 123,
            "parent_pid": 456,
            "name": "pythonw.exe",
            "executable": "C:/Python/pythonw.exe",
            "creation_date": "same-object",
            "command_line": "",
        }
        with mock.patch(
            "xar_autoplayer.runtime._process_identity", return_value=identity
        ):
            self.assertEqual(
                _authenticated_watchdog_state(
                    123, "same-object", 456, "expected-nonce"
                ),
                "unknown",
            )

    def test_tasklist_access_denied_is_not_an_empty_inventory(self) -> None:
        denied = subprocess.CompletedProcess(
            args=["tasklist"],
            returncode=1,
            stdout="",
            stderr="ERROR: Access denied",
        )
        with mock.patch(
            "xar_autoplayer.environment.subprocess.run", return_value=denied
        ):
            with self.assertRaisesRegex(AgentError, "tasklist inventory failed"):
                ck3_process_inventory()

    def test_process_inventory_disagreement_is_not_accepted(self) -> None:
        tasklist = subprocess.CompletedProcess(
            args=["tasklist"],
            returncode=0,
            stdout='"ck3.exe","123","Console","1","1 K"\n',
            stderr="",
        )
        wmi = subprocess.CompletedProcess(
            args=["powershell"], returncode=0, stdout="[]\n", stderr=""
        )
        with mock.patch(
            "xar_autoplayer.environment.subprocess.run",
            side_effect=[tasklist, wmi],
        ):
            with self.assertRaisesRegex(AgentError, "inventories disagree"):
                ck3_process_inventory()

    def test_wmi_failure_is_not_an_empty_inventory(self) -> None:
        tasklist = subprocess.CompletedProcess(
            args=["tasklist"],
            returncode=0,
            stdout="INFO: No tasks are running which match the specified criteria.\n",
            stderr="",
        )
        wmi = subprocess.CompletedProcess(
            args=["powershell"], returncode=1, stdout="", stderr="Access denied"
        )
        with mock.patch(
            "xar_autoplayer.environment.subprocess.run",
            side_effect=[tasklist, wmi],
        ):
            with self.assertRaisesRegex(AgentError, "WMI inventory failed"):
                ck3_process_inventory()

    def test_watchdog_accepts_empty_wmi_path_for_handle_authentication(self) -> None:
        row = SimpleNamespace(
            ProcessId=123,
            ParentProcessId=456,
            Name="ck3.exe",
            ExecutablePath=None,
            CreationDate="created",
        )
        service = mock.Mock()
        service.ExecQuery.return_value = [row]
        self.assertEqual(
            _fallback_children(service, 456, "C:/game/ck3.exe"),
            [(123, "created")],
        )

    def test_watchdog_rejects_same_parent_ck3_with_different_path(self) -> None:
        row = SimpleNamespace(
            ProcessId=123,
            ParentProcessId=456,
            Name="ck3.exe",
            ExecutablePath="C:/other/ck3.exe",
            CreationDate="created",
        )
        service = mock.Mock()
        service.ExecQuery.return_value = [row]
        with self.assertRaisesRegex(RuntimeError, "identity is ambiguous"):
            _fallback_children(service, 456, "C:/game/ck3.exe")

    def test_watchdog_unlinks_only_its_own_nonce(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-agent-nonce-") as temporary:
            path = Path(temporary) / "unsafe-cleanup.json"
            path.write_text('{"nonce":"new-generation"}\n', encoding="utf-8")
            self.assertFalse(_unlink_if_owned(path, "old-generation"))
            self.assertTrue(path.is_file())
            self.assertTrue(_unlink_if_owned(path, "new-generation"))
            self.assertFalse(path.exists())

    @unittest.skipUnless(os.name == "nt", "Windows pinned-process wait contract")
    def test_watchdog_accepts_job_winning_terminate_race(self) -> None:
        import pywintypes
        import win32event

        row = SimpleNamespace(
            ProcessId=123,
            ParentProcessId=456,
            Name="ck3.exe",
            ExecutablePath="C:/game/ck3.exe",
            CreationDate="created",
        )
        service = mock.Mock()
        service.ExecQuery.return_value = [row]
        handle = object()
        with mock.patch(
            "xar_autoplayer.process_watchdog.win32api.OpenProcess",
            return_value=handle,
        ), mock.patch(
            "xar_autoplayer.process_watchdog.win32event.WaitForSingleObject",
            side_effect=[win32event.WAIT_TIMEOUT, win32event.WAIT_OBJECT_0],
        ) as wait, mock.patch(
            "xar_autoplayer.process_watchdog.win32process.GetModuleFileNameEx",
            return_value="C:/game/ck3.exe",
        ), mock.patch(
            "xar_autoplayer.process_watchdog.win32api.TerminateProcess",
            side_effect=pywintypes.error(
                5, "TerminateProcess", "Access is denied"
            ),
        ), mock.patch(
            "xar_autoplayer.process_watchdog.win32api.CloseHandle"
        ) as close:
            self.assertIsNone(
                _terminate_authenticated(
                    service, 123, 456, "C:/game/ck3.exe", "created"
                )
            )
        wait.assert_has_calls([mock.call(handle, 0), mock.call(handle, 20_000)])
        close.assert_called_once_with(handle)

    @unittest.skipUnless(os.name == "nt", "Windows pinned-process wait contract")
    def test_watchdog_normal_termination_uses_full_exact_handle_drain(self) -> None:
        import win32event

        row = SimpleNamespace(
            ProcessId=123,
            ParentProcessId=456,
            Name="ck3.exe",
            ExecutablePath="C:/game/ck3.exe",
            CreationDate="created",
        )
        service = mock.Mock()
        service.ExecQuery.return_value = [row]
        handle = object()
        with mock.patch(
            "xar_autoplayer.process_watchdog.win32api.OpenProcess",
            return_value=handle,
        ), mock.patch(
            "xar_autoplayer.process_watchdog.win32event.WaitForSingleObject",
            side_effect=[win32event.WAIT_TIMEOUT, win32event.WAIT_OBJECT_0],
        ) as wait, mock.patch(
            "xar_autoplayer.process_watchdog.win32process.GetModuleFileNameEx",
            return_value="C:/game/ck3.exe",
        ), mock.patch(
            "xar_autoplayer.process_watchdog.win32api.TerminateProcess"
        ) as terminate, mock.patch(
            "xar_autoplayer.process_watchdog.win32api.CloseHandle"
        ) as close:
            self.assertIsNone(
                _terminate_authenticated(
                    service, 123, 456, "C:/game/ck3.exe", "created"
                )
            )
        terminate.assert_called_once_with(handle, 1)
        wait.assert_has_calls([mock.call(handle, 0), mock.call(handle, 20_000)])
        close.assert_called_once_with(handle)

    @unittest.skipUnless(os.name == "nt", "Windows pinned-process wait contract")
    def test_watchdog_wmi_disappearance_waits_for_exact_handle(self) -> None:
        import win32event

        service = mock.Mock()
        service.ExecQuery.return_value = []
        handle = object()
        with mock.patch(
            "xar_autoplayer.process_watchdog.win32api.OpenProcess",
            return_value=handle,
        ), mock.patch(
            "xar_autoplayer.process_watchdog.win32event.WaitForSingleObject",
            side_effect=[win32event.WAIT_TIMEOUT, win32event.WAIT_OBJECT_0],
        ) as wait, mock.patch(
            "xar_autoplayer.process_watchdog.win32api.TerminateProcess"
        ) as terminate, mock.patch(
            "xar_autoplayer.process_watchdog.win32api.CloseHandle"
        ) as close:
            self.assertIsNone(
                _terminate_authenticated(
                    service, 123, 456, "C:/game/ck3.exe", "created"
                )
            )
        terminate.assert_not_called()
        wait.assert_has_calls([mock.call(handle, 0), mock.call(handle, 20_000)])
        close.assert_called_once_with(handle)

    @unittest.skipUnless(os.name == "nt", "Windows pinned-process wait contract")
    def test_watchdog_fails_closed_when_terminate_race_never_signals(self) -> None:
        import pywintypes
        import win32event

        row = SimpleNamespace(
            ProcessId=123,
            ParentProcessId=456,
            Name="ck3.exe",
            ExecutablePath="C:/game/ck3.exe",
            CreationDate="created",
        )
        service = mock.Mock()
        service.ExecQuery.return_value = [row]
        handle = object()
        with mock.patch(
            "xar_autoplayer.process_watchdog.win32api.OpenProcess",
            return_value=handle,
        ), mock.patch(
            "xar_autoplayer.process_watchdog.win32event.WaitForSingleObject",
            side_effect=[win32event.WAIT_TIMEOUT, win32event.WAIT_TIMEOUT],
        ) as wait, mock.patch(
            "xar_autoplayer.process_watchdog.win32process.GetModuleFileNameEx",
            return_value="C:/game/ck3.exe",
        ), mock.patch(
            "xar_autoplayer.process_watchdog.win32api.TerminateProcess",
            side_effect=pywintypes.error(
                5, "TerminateProcess", "Access is denied"
            ),
        ), mock.patch(
            "xar_autoplayer.process_watchdog.win32api.CloseHandle"
        ) as close:
            failure = _terminate_authenticated(
                service, 123, 456, "C:/game/ck3.exe", "created"
            )
        self.assertIn("terminate:123", str(failure))
        wait.assert_has_calls([mock.call(handle, 0), mock.call(handle, 20_000)])
        close.assert_called_once_with(handle)

    @unittest.skipUnless(os.name == "nt", "Windows pinned-process wait contract")
    def test_watchdog_fails_closed_when_terminate_race_wait_errors(self) -> None:
        import pywintypes
        import win32event

        row = SimpleNamespace(
            ProcessId=123,
            ParentProcessId=456,
            Name="ck3.exe",
            ExecutablePath="C:/game/ck3.exe",
            CreationDate="created",
        )
        service = mock.Mock()
        service.ExecQuery.return_value = [row]
        handle = object()
        with mock.patch(
            "xar_autoplayer.process_watchdog.win32api.OpenProcess",
            return_value=handle,
        ), mock.patch(
            "xar_autoplayer.process_watchdog.win32event.WaitForSingleObject",
            side_effect=[
                win32event.WAIT_TIMEOUT,
                OSError("wait failed while process state is unknown"),
            ],
        ), mock.patch(
            "xar_autoplayer.process_watchdog.win32process.GetModuleFileNameEx",
            return_value="C:/game/ck3.exe",
        ), mock.patch(
            "xar_autoplayer.process_watchdog.win32api.TerminateProcess",
            side_effect=pywintypes.error(
                5, "TerminateProcess", "Access is denied"
            ),
        ), mock.patch(
            "xar_autoplayer.process_watchdog.win32api.CloseHandle"
        ) as close:
            failure = _terminate_authenticated(
                service, 123, 456, "C:/game/ck3.exe", "created"
            )
        self.assertIn("wait failed", str(failure))
        close.assert_called_once_with(handle)


class SteamSemanticSnapshotTests(unittest.TestCase):
    def test_only_change_number_and_mtime_are_volatile(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-agent-steam-") as temporary:
            steam = Path(temporary).resolve() / "Steam"
            cache = steam / "userdata" / "1" / "1158310" / "remotecache.vdf"
            cache.parent.mkdir(parents=True)
            template = (
                '"1158310"\n{{\n\t"ChangeNumber"\t\t"{change}"\n'
                '\t"save games/example.ck3"\n\t{{\n\t\t"sha"\t\t"{sha}"\n\t}}\n}}\n'
            )
            with mock.patch("xar_autoplayer.integrity._steam_path", return_value=steam):
                cache.write_text(template.format(change=12, sha="abc"), encoding="utf-8")
                first = steam_userdata_snapshot()
                cache.write_text(template.format(change=13, sha="abc"), encoding="utf-8")
                second = steam_userdata_snapshot()
                self.assertEqual(first, second)
                cache.write_text(template.format(change=13, sha="def"), encoding="utf-8")
                third = steam_userdata_snapshot()
                self.assertNotEqual(second, third)


if __name__ == "__main__":
    unittest.main()
