#!/usr/bin/env python3
"""Deterministic tests for the phase-two append-only loader-stage gate."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import zg361_phase2_loader_stage as loader


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class FakeTime:
    def __init__(self, on_sleep=None) -> None:
        self.value = 0.0
        self.sleep_count = 0
        self.on_sleep = on_sleep

    def clock(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.sleep_count += 1
        self.value += seconds
        if self.on_sleep is not None:
            self.on_sleep(self.sleep_count)


def rows(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)

        # Database dependency progress is observational only.  It must expose
        # the last native node without changing the stage classification or
        # authorizing the event waiter.
        dependency_snapshot = loader.inspect_loader_logs(
            (
                b"[00:00:01][D][database_dependencies.cpp:433]: "
                b"Database Node Init Time: CGameConceptTypeDatabase - 3 ms - 3 ms including dependencies\n"
                b"[00:00:02][D][database_dependencies.cpp:433]: "
                b"Database Node Init Time: CJominiLoadScreenDatabase - 4 ms - 4 ms including dependencies\n"
                b"[00:00:03][D][database_dependencies.cpp:433]: "
                b"PostInit - CJominiLoadScreenDatabase\n"
            ),
            b"",
        )
        require(
            dependency_snapshot["database_node_count"] == 2,
            "database dependency node count was not observed",
        )
        require(
            dependency_snapshot["last_database_node"]
            == "CJominiLoadScreenDatabase",
            "last database dependency node was not observed",
        )
        require(
            dependency_snapshot["database_nodes"]
            == [
                {
                    "timestamp": "00:00:01",
                    "source_line": "database_dependencies.cpp:433",
                    "node": "CGameConceptTypeDatabase",
                    "init_ms": 3,
                    "inclusive_ms": 3,
                },
                {
                    "timestamp": "00:00:02",
                    "source_line": "database_dependencies.cpp:433",
                    "node": "CJominiLoadScreenDatabase",
                    "init_ms": 4,
                    "inclusive_ms": 4,
                },
            ],
            "database dependency node context was not typed",
        )
        require(
            dependency_snapshot["last_database_node_detail"]
            == dependency_snapshot["database_nodes"][-1],
            "last database dependency detail did not preserve node context",
        )
        require(
            dependency_snapshot["stage"] == "engine_start"
            and dependency_snapshot["event_wait_authorized"] is False,
            "database dependency observation changed loader authorization",
        )
        require(
            dependency_snapshot["database_callback_count"] == 2
            and dependency_snapshot["last_database_callback"]
            == dependency_snapshot["database_nodes"][-1],
            "database callback completion telemetry was not preserved",
        )
        require(
            dependency_snapshot["database_post_init_count"] == 1
            and dependency_snapshot["database_post_init"] == [
                {
                    "timestamp": "00:00:03",
                    "source_line": "database_dependencies.cpp:433",
                    "value": "CJominiLoadScreenDatabase",
                }
            ],
            "PostInit telemetry was not captured as opaque text",
        )

        # attempt07's concrete product errors stop a stagnant database load.
        fatal_logs = root / "fatal" / "logs"
        fatal_logs.mkdir(parents=True)
        (fatal_logs / "debug.log").write_text(
            "[00:00:01][D][jomini_eventmanager.cpp:594]: Loaded events\n",
            encoding="utf-8",
        )
        (fatal_logs / "error.log").write_text(
            "\n".join(
                (
                    "[00:00:02][E][event.cpp:368]: Theme missing in event 'zga_phase2_seed.1'",
                    "[00:00:03][E][jomini_script_system.cpp:303]: Script system error!",
                    "  Error: revoke_court_position effect [ Expected opening bracket ]",
                    "  Script location: file: common/scripted_effects/zg361_workforce_exit_fact_effects.txt line: 421",
                    "[00:00:04][E][jomini_script_system.cpp:303]: Script system error!",
                    "  Error: revoke_court_position effect [ Expected opening bracket ]",
                    "  Script location: file: common/scripted_effects/zg361_workforce_exit_fact_effects.txt line: 421",
                    "[00:00:05][E][pdx_persistent_reader.cpp:216]: Error: Unknown trigger: value in file: common/script_values/zg361_manager_governance_runtime_values.txt",
                    "[00:00:06][E][jomini_script_argument.cpp:192]: Compiling source for zg361_career_hc_accept_cl_transfer_effect failed for unknown arguments: TICKET_SUBJECT. At file: common/scripted_effects/zg361_career_hc_runtime_effects.txt line: 390",
                    "[00:00:07][E][jomini_script_argument.cpp:192]: Compiling source for zg361_career_hc_accept_cl_transfer_effect failed for unknown arguments: TICKET_SUBJECT. At file: common/scripted_effects/zg361_career_hc_runtime_effects.txt line: 390",
                    "[00:00:08][E][jomini_eventmanager.cpp:428]: Duplicated event ID 'zg361we.52640' found. New Location: 'file: events/zg361_workforce_endgame_runtime_events.txt line: 3223'",
                    "[00:00:09][E][jomini_eventmanager.cpp:428]: Duplicated event ID 'vanilla.52640' found. New Location: 'file: events/vanilla_events.txt line: 99'",
                    "[00:00:10][E][jomini_eventmanager.cpp:142]: '52750' is not a valid event ID, has to be < 10000",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        fatal_progress = root / "fatal" / "loader-progress.jsonl"
        fatal_time = FakeTime()
        try:
            loader.wait_for_phase2_seed_loader_stage(
                fatal_logs,
                fatal_progress,
                timeout_seconds=10.0,
                fatal_stall_seconds=2.0,
                poll_interval_seconds=1.0,
                clock=fatal_time.clock,
                sleeper=fatal_time.sleep,
            )
            raise AssertionError("fatal loader logs did not fail")
        except loader.LoaderParseRed as error:
            require(
                error.evidence["state"] == "loader_parse_red",
                "fatal loader state was not typed loader_parse_red",
            )
            require(
                error.evidence["fatal_error_count"] == 4,
                "fatal signatures were not deduplicated/scoped to product paths",
            )
            require(
                error.evidence["reason_code"]
                == "known_parser_errors_stalled_database",
                "parser RED did not expose its bounded reason code",
            )
            require(
                error.evidence["theme_warning_count"] == 1,
                "theme warning was not counted separately",
            )
            require(
                len(error.evidence["fatal_errors"]) == 4,
                "fatal evidence list does not match its count",
            )
        fatal_rows = rows(fatal_progress)
        require(
            fatal_rows[-1]["state"] == "loader_parse_red",
            "append-only evidence lacks the final parser RED",
        )
        require(
            len(fatal_rows[-1]["fatal_errors"]) == 4,
            "append-only parser RED lacks deduplicated findings",
        )

        # A managed native session that has already reported a non-zero
        # process exit must terminate the loader gate immediately.  This is
        # the concrete C0000005 boundary from the bounded CK3 attempt; it
        # must not be rewritten as the generic 300-second timeout.
        exit_logs = root / "process-exit" / "logs"
        exit_logs.mkdir(parents=True)
        (exit_logs / "debug.log").write_bytes(b"")
        (exit_logs / "error.log").write_bytes(b"")
        exit_progress = root / "process-exit" / "loader-progress.jsonl"
        exit_time = FakeTime()
        session_report = {
            "kind": "ck3_native_headless_session",
            "exit_reason": "process_exit",
            "process_exit_code": 1,
            "pid": 79880,
            "ok": False,
        }

        def process_exit_probe() -> dict[str, object] | None:
            if exit_time.sleep_count < 1:
                return None
            return {
                "terminal": True,
                "session_thread_alive": False,
                "session_report": session_report,
                "session_error": None,
            }

        try:
            loader.wait_for_phase2_seed_loader_stage(
                exit_logs,
                exit_progress,
                timeout_seconds=300.0,
                fatal_stall_seconds=45.0,
                poll_interval_seconds=1.0,
                native_session_probe=process_exit_probe,
                clock=exit_time.clock,
                sleeper=exit_time.sleep,
            )
            raise AssertionError("native process exit did not fail early")
        except loader.LoaderNativeSessionExitRed as error:
            require(
                error.evidence["state"] == "native_session_process_exit",
                "native process exit received the wrong terminal",
            )
            require(
                error.evidence["process_exit_code"] == 1
                and error.evidence["process_exit_nonzero"] is True,
                "non-zero native process exit was not preserved",
            )
            require(
                error.evidence["native_session"]["session_report"]
                == session_report,
                "native session report was not preserved in loader evidence",
            )
        require(
            exit_time.value < 45.0,
            "native process exit waited for the generic loader timeout",
        )
        require(
            rows(exit_progress)[-1]["state"] == "native_session_process_exit",
            "append-only evidence lacks the native process-exit terminal",
        )

        # A terminal supervisor result must win even when the log already
        # contains a marker that would otherwise authorize the event waiter.
        # This guards the ordering boundary: a stale Load Save/In Game marker
        # cannot be promoted to GREEN after CK3 has exited non-zero.
        precedence_logs = root / "authorized-probe-precedence" / "logs"
        precedence_logs.mkdir(parents=True)
        (precedence_logs / "debug.log").write_text(
            "[00:00:01][D][gameapplication.cpp:558]: "
            "Setting idler 'Load Save' with init options\n",
            encoding="utf-8",
        )
        (precedence_logs / "error.log").write_text("", encoding="utf-8")
        precedence_progress = (
            root / "authorized-probe-precedence" / "loader-progress.jsonl"
        )
        precedence_probe_calls: list[int] = []

        def authorized_process_exit_probe() -> dict[str, object] | None:
            precedence_probe_calls.append(1)
            return {
                "terminal": True,
                "session_report": {
                    "exit_reason": "process_exit",
                    "process_exit_code": 1,
                },
            }

        try:
            loader.wait_for_phase2_seed_loader_stage(
                precedence_logs,
                precedence_progress,
                timeout_seconds=10.0,
                fatal_stall_seconds=3.0,
                poll_interval_seconds=0.0,
                native_session_probe=authorized_process_exit_probe,
            )
            raise AssertionError(
                "terminal native session was incorrectly promoted to GREEN"
            )
        except loader.LoaderNativeSessionExitRed as error:
            require(
                error.evidence["state"] == "native_session_process_exit",
                "authorized marker did not preserve typed process-exit RED",
            )
            require(
                error.evidence["event_wait_authorized"] is True,
                "precedence regression did not exercise an authorized marker",
            )
            require(
                error.evidence["process_exit_nonzero"] is True,
                "authorized-marker process exit lost its non-zero evidence",
            )
        require(
            precedence_probe_calls == [1],
            "native session probe was not called before authorized GREEN",
        )
        require(
            all(
                row["state"] != "loader_stage_ready"
                for row in rows(precedence_progress)
            ),
            "authorized marker emitted a false loader_stage_ready terminal",
        )

        # A theme warning is actionable static debt, but cannot impersonate a
        # parser/compiler stall and trigger the typed early-RED boundary.
        theme_logs = root / "theme" / "logs"
        theme_logs.mkdir(parents=True)
        (theme_logs / "debug.log").write_text(
            "[00:00:01][D][jomini_eventmanager.cpp:594]: Loaded events\n",
            encoding="utf-8",
        )
        (theme_logs / "error.log").write_text(
            "[00:00:02][E][event.cpp:368]: Theme missing in event 'zga_phase2_seed.1'\n",
            encoding="utf-8",
        )
        theme_progress = root / "theme" / "loader-progress.jsonl"
        theme_time = FakeTime()
        try:
            loader.wait_for_phase2_seed_loader_stage(
                theme_logs,
                theme_progress,
                timeout_seconds=4.0,
                fatal_stall_seconds=2.0,
                poll_interval_seconds=1.0,
                clock=theme_time.clock,
                sleeper=theme_time.sleep,
            )
            raise AssertionError("theme-only load did not reach its bound")
        except loader.LoaderStageTimeout as error:
            require(
                error.evidence["state"] == "loader_stage_timeout",
                "theme-only stall received the wrong terminal",
            )
            require(
                error.evidence["fatal_error_count"] == 0,
                "theme-only warning was misclassified as fatal",
            )
            require(
                error.evidence["theme_warning_count"] == 1,
                "theme-only warning was not observed",
            )
            require(
                error.evidence["reason_code"]
                == "database_init_without_callback_completion",
                "theme-only timeout did not expose its database boundary",
            )
        require(
            all(
                row["state"] != "loader_parse_red"
                for row in rows(theme_progress)
            ),
            "theme-only warning emitted a false parser RED",
        )

        # A database node timing line proves one callback completed, but
        # unrelated event-manager chatter must not hide that the loader never
        # reached a terminal.  Exact-build evidence now proves the observed
        # callback vector returned and exhausted, so this must not be called a
        # callback stall.
        callback_logs = root / "callback-stall" / "logs"
        callback_logs.mkdir(parents=True)
        callback_debug = callback_logs / "debug.log"
        callback_debug.write_text(
            "[00:00:01][D][database_dependencies.cpp:433]: "
            "Database Node Init Time: CGameConceptTypeDatabase - 4 ms - 4 ms including dependencies\n"
            "[00:00:01][D][database_dependencies.cpp:433]: "
            "Database Node Init Time: CJominiLoadScreenDatabase - 4 ms - 4 ms including dependencies\n"
            "[00:00:02][D][jomini_eventmanager.cpp:594]: Loaded events\n",
            encoding="utf-8",
        )
        (callback_logs / "error.log").write_text("", encoding="utf-8")
        callback_progress = root / "callback-stall" / "loader-progress.jsonl"
        callback_time = FakeTime()
        try:
            loader.wait_for_phase2_seed_loader_stage(
                callback_logs,
                callback_progress,
                timeout_seconds=4.0,
                fatal_stall_seconds=2.0,
                poll_interval_seconds=1.0,
                clock=callback_time.clock,
                sleeper=callback_time.sleep,
            )
            raise AssertionError("callback stall did not reach its bound")
        except loader.LoaderStageTimeout as error:
            require(
                error.evidence["reason_code"]
                == "loader_terminal_missing_after_database_completion_publish",
                "post-callback timeout retained its disproven attribution",
            )
            require(
                error.evidence["deprecated_reason_code"]
                == "database_callback_stall",
                "post-callback timeout lost its compatibility reason",
            )
            require(
                error.evidence["database_callback_count"] == 2,
                "callback stall evidence lost completed callback count",
            )
            require(
                error.evidence[
                    "database_completion_publish_sequence_observed"
                ]
                is True,
                "proven completion-publish node sequence was not classified",
            )
            require(
                error.evidence["database_completion_publish_contract"]
                == "phase2-outer-completion-edge-v1"
                and error.evidence["database_completion_publish_rva"]
                == "0x3B9CFD7",
                "completion-publish classification lost its exact contract",
            )
            require(
                error.evidence["database_callback_quiet_seconds"] >= 3.0,
                "callback-specific quiet clock did not advance",
            )
            require(
                error.evidence[
                    "database_callback_completion_quiet_seconds"
                ]
                == error.evidence["database_callback_quiet_seconds"],
                "completion quiet clock and compatibility alias diverged",
            )
        require(
            rows(callback_progress)[-1]["reason_code"]
            == "loader_terminal_missing_after_database_completion_publish",
            "append-only post-callback timeout lacked its corrected reason",
        )

        # Even a known historical parser error cannot steal the terminal once
        # CK3 has demonstrably reached Frontend.  That is a save-resume failure,
        # not the attempt07 database-init stall.
        frontend_logs = root / "frontend" / "logs"
        frontend_logs.mkdir(parents=True)
        (frontend_logs / "debug.log").write_text(
            "[00:00:01][D][jomini_eventmanager.cpp:594]: Loaded events\n"
            "[00:00:02][D][gameapplication.cpp:558]: "
            "Setting idler 'Frontend' with NO init options\n",
            encoding="utf-8",
        )
        (frontend_logs / "error.log").write_text(
            "[00:00:01][E][jomini_eventmanager.cpp:428]: "
            "Duplicated event ID 'zg361we.52640' found. "
            "New Location: 'file: events/zg361_workforce_endgame_runtime_events.txt "
            "line: 3223'\n",
            encoding="utf-8",
        )
        frontend_progress = root / "frontend" / "loader-progress.jsonl"
        frontend_time = FakeTime()
        try:
            loader.wait_for_phase2_seed_loader_stage(
                frontend_logs,
                frontend_progress,
                timeout_seconds=4.0,
                fatal_stall_seconds=2.0,
                poll_interval_seconds=1.0,
                clock=frontend_time.clock,
                sleeper=frontend_time.sleep,
            )
            raise AssertionError("frontend-only load did not reach its bound")
        except loader.LoaderResumeRed as error:
            require(
                error.evidence["state"] == "save_resume_red",
                "frontend-only load was misclassified as parser RED",
            )
        require(
            all(
                row["state"] != "loader_parse_red"
                for row in rows(frontend_progress)
            ),
            "historical parser error stole the Frontend terminal",
        )

        # Ordinary append progress reaches Load Save and authorizes the event
        # waiter; no screenshot, coordinate, or fixture decision is involved.
        normal_logs = root / "normal" / "logs"
        normal_logs.mkdir(parents=True)
        debug_path = normal_logs / "debug.log"
        debug_path.write_text(
            "[00:00:01][D][jomini_eventmanager.cpp:594]: Loaded events\n",
            encoding="utf-8",
        )
        (normal_logs / "error.log").write_text("", encoding="utf-8")

        def advance_loader(sleep_count: int) -> None:
            if sleep_count == 1:
                with debug_path.open("a", encoding="utf-8") as stream:
                    stream.write(
                        "[00:00:02][D][gameapplication.cpp:558]: "
                        "Setting idler 'Frontend' with NO init options\n"
                    )
            elif sleep_count == 2:
                with debug_path.open("a", encoding="utf-8") as stream:
                    stream.write(
                        "[00:00:03][D][gameapplication.cpp:558]: "
                        "Setting idler 'Load Save' with init options\n"
                    )

        normal_progress = root / "normal" / "loader-progress.jsonl"
        normal_time = FakeTime(advance_loader)
        ready = loader.wait_for_phase2_seed_loader_stage(
            normal_logs,
            normal_progress,
            timeout_seconds=10.0,
            fatal_stall_seconds=3.0,
            poll_interval_seconds=1.0,
            clock=normal_time.clock,
            sleeper=normal_time.sleep,
        )
        require(ready["result"] == "GREEN", "normal loader did not pass")
        require(
            ready["state"] == "loader_stage_ready",
            "normal loader returned the wrong terminal",
        )
        require(
            ready["stage"] == "load_save",
            "frontend alone incorrectly authorized event wait",
        )
        require(
            ready["event_wait_authorized"] is True,
            "Load Save did not authorize event wait",
        )
        require(
            rows(normal_progress)[-1]["state"] == "loader_stage_ready",
            "append-only evidence lacks the ready terminal",
        )

    print("GREEN: phase-two loader gate classifies parse RED without visual input")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
