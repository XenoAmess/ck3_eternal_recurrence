from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "analyze_phase2_producer_histogram_live.py"
)
SPEC = importlib.util.spec_from_file_location("phase2_producer_histogram_v2", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

MANIFEST_SHA = "A" * 64
GIT_SHA = "b" * 40
SOURCE_ZIP_SHA = "c" * 64
SOURCE_TREE_SHA = "d" * 64
EXE_SHA = "e" * 64
DLL_SHA = "f" * 64
INJECTOR_SHA = "1" * 64
PIPE = r"\\.\pipe\phase2_histogram_test"


def identity(**changes: int) -> dict[str, int]:
    value = {
        "task_pointer": 0x1000,
        "task_state": 1,
        "callback_pointer": 0x2000,
        "vptr": 0x3000,
        "slot2_target": 0x14088B480,
        "slot2_rva": MODULE.SELECTED_SLOT2_RVA,
        "owner_pointer": 0x4000,
        "thread_id": 7,
        "timestamp_qpc": 90,
    }
    value.update(changes)
    return value


def observer(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "private_build": True,
        "installed": True,
        "failure": 0,
        "producer_0x3B9CFD2_entry_count": 2,
        "producer_0x3B9CFD7_entry_count": 2,
        "histogram_capacity": MODULE.HISTOGRAM_CAPACITY,
        "histogram_bin_count": 1,
        "histogram_overflow_count": 0,
        "histogram_read_failure_count": 0,
        "callback_slot2_rva_histogram": [
            {"slot2_rva": 0x817C20, "count": 2}
        ],
        "selected_slot2_rva": MODULE.SELECTED_SLOT2_RVA,
        "selected_count": 0,
        "selected_first": None,
        "selected_last": None,
        "read_failure_count": 0,
    }
    value.update(changes)
    return value


def manifest() -> dict[str, object]:
    return {
        "schema_version": 1,
        "kind": "zg361_phase2_native_observer_seam",
        "result": "GREEN",
        "source_git_commit": GIT_SHA,
        "exact_build": {
            "game_version": "1.19.0.6",
            "game_executable_sha256": EXE_SHA,
        },
        "build": {
            "bridge_dll_sha256": DLL_SHA,
            "bridge_injector_sha256": INJECTOR_SHA,
        },
        "session_binding": {
            "source_zip_sha256": SOURCE_ZIP_SHA,
            "clean_source_tree_sha256": SOURCE_TREE_SHA,
            "pipe_name": PIPE,
        },
        "seam": {"heartbeat_object": MODULE.OBSERVER_KEY},
        "report_contract": {"schema": MODULE.REPORT_SCHEMA},
    }


def runner(*samples: dict[str, object]) -> dict[str, object]:
    return {
        "frozen_git_commit": GIT_SHA,
        "list_domain_observer_gate": {
            "result": "GREEN",
            "observer_manifest": {"sha256": MANIFEST_SHA},
        },
        "source_identity": {
            "source_zip": {"sha256": SOURCE_ZIP_SHA},
            "clean_source_tree": {"tree_sha256": SOURCE_TREE_SHA},
        },
        "external_dependencies": {
            "sha256_before": {
                "game_executable": EXE_SHA,
                "bridge_dll": DLL_SHA,
                "bridge_injector": INJECTOR_SHA,
            }
        },
        "bridge": {"pipe": PIPE},
        "binding": {"bridge_pid": 42},
        "native_session": {
            "heartbeats": [
                {
                    "type": "heartbeat",
                    "pid": 42,
                    "sequence": index + 1,
                    MODULE.OBSERVER_KEY: sample,
                }
                for index, sample in enumerate(samples)
            ]
        },
    }


def analyze(*samples: dict[str, object]) -> dict[str, object]:
    return MODULE.analyze(
        runner(*samples), manifest(), observer_manifest_sha256=MANIFEST_SHA
    )


class Phase2ProducerHistogramLivePostprocessTests(unittest.TestCase):
    def test_checked_in_contract_matches_parser_constants(self) -> None:
        contract = json.loads(
            (
                ROOT
                / "native_bridge"
                / "research"
                / "phase2_producer_histogram_live_postprocess_v2_contract.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(contract["observer"]["heartbeat_object"], MODULE.OBSERVER_KEY)
        self.assertEqual(contract["observer"]["report_schema"], MODULE.REPORT_SCHEMA)
        self.assertEqual(
            contract["observer"]["histogram_capacity"], MODULE.HISTOGRAM_CAPACITY
        )
        self.assertEqual(
            int(contract["observer"]["selected_slot2_rva"], 16),
            MODULE.SELECTED_SLOT2_RVA,
        )

    def test_zero_selected_is_no_go(self) -> None:
        result = analyze(observer())
        self.assertEqual(
            (result["status"], result["decision"], result["next_gate_allowed"]),
            ("NO-GO", "selected-not-observed", False),
        )

    def test_consistent_selected_identity_allows_only_next_gate(self) -> None:
        selected = identity()
        result = analyze(
            observer(
                callback_slot2_rva_histogram=[
                    {"slot2_rva": MODULE.SELECTED_SLOT2_RVA, "count": 2}
                ],
                selected_count=2,
                selected_first=selected,
                selected_last={**selected, "timestamp_qpc": 100},
            )
        )
        self.assertEqual(
            (result["status"], result["decision"], result["next_gate_allowed"]),
            ("GREEN", "selected-consistent-next-gate", True),
        )

    def test_selected_first_last_state_or_identity_mismatch_is_no_go(self) -> None:
        result = analyze(
            observer(
                callback_slot2_rva_histogram=[
                    {"slot2_rva": MODULE.SELECTED_SLOT2_RVA, "count": 2}
                ],
                selected_count=2,
                selected_first=identity(),
                selected_last=identity(task_state=2, timestamp_qpc=100),
            )
        )
        self.assertEqual(
            (result["status"], result["decision"], result["next_gate_allowed"]),
            ("NO-GO", "selected-state-or-identity-inconsistent", False),
        )

    def test_overflow_or_read_failure_is_no_go(self) -> None:
        selected = identity()
        overflow = analyze(
            observer(
                callback_slot2_rva_histogram=[
                    {"slot2_rva": MODULE.SELECTED_SLOT2_RVA, "count": 2}
                ],
                histogram_overflow_count=1,
                producer_0x3B9CFD2_entry_count=3,
                producer_0x3B9CFD7_entry_count=3,
                selected_count=2,
                selected_first=selected,
                selected_last={**selected, "timestamp_qpc": 100},
            )
        )
        self.assertEqual(
            (overflow["status"], overflow["decision"]),
            ("NO-GO", "histogram-incomplete"),
        )
        read_failure = analyze(
            observer(
                callback_slot2_rva_histogram=[
                    {"slot2_rva": MODULE.SELECTED_SLOT2_RVA, "count": 1}
                ],
                histogram_read_failure_count=1,
                selected_count=1,
                selected_first=selected,
                selected_last={**selected, "timestamp_qpc": 100},
            )
        )
        self.assertEqual(
            (read_failure["status"], read_failure["decision"]),
            ("NO-GO", "histogram-incomplete"),
        )
        general_read_failure = analyze(
            observer(
                read_failure_count=1,
            )
        )
        self.assertEqual(
            (general_read_failure["status"], general_read_failure["decision"]),
            ("NO-GO", "histogram-incomplete"),
        )

    def test_histogram_bound_and_relations_are_strict(self) -> None:
        rows = [
            {"slot2_rva": 0x1000 + index, "count": 1}
            for index in range(MODULE.HISTOGRAM_CAPACITY + 1)
        ]
        result = analyze(
            observer(
                producer_0x3B9CFD2_entry_count=len(rows),
                producer_0x3B9CFD7_entry_count=len(rows),
                histogram_bin_count=len(rows),
                callback_slot2_rva_histogram=rows,
            )
        )
        self.assertEqual(
            (result["status"], result["decision"]),
            ("RED", "observer-counter-or-histogram-invalid"),
        )

    def test_manifest_source_session_or_pid_mismatch_is_red(self) -> None:
        changed_runner = runner(observer())
        changed_runner["bridge"] = {"pipe": r"\\.\pipe\other"}
        result = MODULE.analyze(
            changed_runner, manifest(), observer_manifest_sha256=MANIFEST_SHA
        )
        self.assertEqual(
            (result["status"], result["decision"]),
            ("RED", "evidence-identity-mismatch"),
        )
        self.assertIn("pipe-identity-mismatch", result["identity"]["issues"])

    def test_counter_and_histogram_regression_is_red(self) -> None:
        result = analyze(
            observer(
                producer_0x3B9CFD2_entry_count=3,
                producer_0x3B9CFD7_entry_count=3,
                callback_slot2_rva_histogram=[
                    {"slot2_rva": 0x817C20, "count": 3}
                ],
            ),
            observer(),
        )
        self.assertEqual(
            (result["status"], result["decision"]),
            ("RED", "observer-counter-or-histogram-invalid"),
        )

    def test_exact_schema_rejects_extra_and_result_serializes(self) -> None:
        result = analyze(observer(future_field=1))
        self.assertEqual(
            (result["status"], result["decision"]),
            ("RED", "observer-schema-missing-or-invalid"),
        )
        self.assertIsInstance(json.dumps(result), str)


if __name__ == "__main__":
    unittest.main()
