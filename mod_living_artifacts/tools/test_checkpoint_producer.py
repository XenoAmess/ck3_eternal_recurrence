"""Offline producer boundaries and real benign subprocesses; no game qualification."""
from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass, replace
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from acceptance_contract import Frame, Object, integer, json_value, pin, read, write_once
from checkpoint_callback import checked_pin, verify_readback
from checkpoint_producer import (Identity, ProducerSpec, StoragePins, blocked_response, execute_melter, preserve_source, raw_object, storage_admission, validate_request)


def subject_python() -> str:
    # A Windows venv executable is a redirector and is not the retained subject
    # of its descendant. These process-only tests use the actual base executable
    # so timeout/wait refer to the same process that owns stdout/stderr handles.
    candidate: object = getattr(sys, "_base_executable", None)
    if type(candidate) is not str or not Path(candidate).is_file():
        raise AssertionError("An actual base Python executable is required")
    return candidate


def fixture_spec(root: Path) -> ProducerSpec:
    identity = Identity("unit-run", "unit-machine", "unit-root", 124, "9", 91, 123456)
    manifest = write_once(root / "manifest.json", {"machine_id": identity.machine_id, "game": {"version": "unit-version", "exe_sha256": "a" * 64}})
    frame: Object = {"paused": True, "map_ready": True, "source": "injected-dll-named-pipe", "backend_id": "native-headless",
        "episode_projection": "native_campaign", "revision": 3, "native_revision": 2, "date_raw": identity.date_raw,
        "played_character": {"character_id": identity.actor, "alive": True, "source": "native"},
        "managed_campaign_run_binding": {"run_id": identity.run_id, "bridge_pipe": "unit-pipe"},
        "diagnostics": {"bridge_pid": identity.pid, "connection_generation": 9, "pipe_name": "unit-pipe", "hello": {
            "pid": identity.pid, "connection_generation": 9, "ck3_build_match": True, "expected_ck3_version": "unit-version", "expected_ck3_sha256": "a" * 64}}}
    snapshot = write_once(root / "snapshot.json", {"rows": [{"ok": True, "plan": {"tool": "ck3_take_snapshot"}, "result": frame}]})
    source = root / "source.ck3"
    source.write_bytes(b"authored save boundary input, never SDK evidence")
    request = write_once(root / "checkpoint-readback-01-awaiting.json", {"schema": "living-artifacts-checkpoint-readback-request-v1",
        **{key: value for key, value in identity.to_json().items() if key != "reviewer"}, "operator_reviewer": identity.reviewer,
        "actual_source_save": pin(source), "expected_target_id": None, "required_response_schema": "living-artifacts-checkpoint-readback-v1",
        "required_unknown_token_policy": "error", "original_native_frame_record": snapshot, "observation_number": 1,
        "storage_policy": "docs/storage-retention-policy.json", "business_pass": False,
        "original_hold_deadline": 4102444800.0, "reserve_seconds": 180})
    harmless = write_once(root / "not-official.json", {"authored_data": True})
    storage: StoragePins = {"policy": harmless, "machine_profile": harmless, "asset_ledger": harmless, "reservation": harmless, "inspection": harmless}
    return ProducerSpec(identity, request, manifest, harmless, harmless, harmless, storage, root / "unique-output", 1024 * 1024, 65536, 2)


@dataclass(frozen=True)
class AuthoredDisk:
    total: int = 1000 * 1024**3
    used: int = 500 * 1024**3
    free: int = 500 * 1024**3


def storage_fixture(root: Path, *, wrong_budget: tuple[str, object] | None = None) -> ProducerSpec:
    spec = fixture_spec(root)
    policy = pin(Path(__file__).resolve().parents[2] / "docs/storage-retention-policy.json")
    volume = root.anchor
    budget: dict[str, object] = {"system_growth_reserve_bytes": 1024**3, "other_unspent_reservations_bytes": 0,
        "current_project_usage_bytes": 1000, "effective_project_quota_bytes": 100 * 1024**3}
    if wrong_budget is not None:
        budget[wrong_budget[0]] = wrong_budget[1]
    profile = write_once(root / "profile.json", {"machine_id": "unit-machine", "policy_version": "1.0.0", "observed_at_utc": "2026-01-01T00:00:00Z",
        "project_root_map": {"unit": str(root)}, "usage_basis": {"bounded_project_roots_complete": True}, "volume_map": {volume: budget}})
    ledger = write_once(root / "ledger.json", {"machine_id": "unit-machine", "policy_version": "1.0.0",
        "asset_groups": [{"machine_id": "unit-machine", "asset_id": "unit", "root_id": "unit", "owner_task": "unit-work"}]})
    reservation = write_once(root / "reservation.json", {"machine_id": "unit-machine", "review_at_utc": "2027-01-01T00:00:00Z",
        "coordinator": "unit-root", "owner_task": "unit-work", "state": "reserved_for_python_native_runtime",
        "reservation_bytes": {volume: 2 * 1024**3}, "other_unspent_reservations_bytes": {volume: 0}})
    inspection = write_once(root / "inspection.json", {"schema": "xar.storage-retention-inspection.v1", "machine_id": "unit-machine", "policy_version": "1.0.0",
        "trigger": "before-heavy-write", "observed_at_utc": "2026-01-01T01:00:00Z", "outcomes": [{"state": "current_use"}],
        "input_pins": {entry["path"]: entry["sha256"] for entry in (policy, profile, ledger)}})
    return replace(spec, storage=StoragePins(policy=policy, machine_profile=profile, asset_ledger=ledger, reservation=reservation, inspection=inspection))


class ProducerTests(unittest.TestCase):
    def test_spec_producer_to_parser_json_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original = fixture_spec(Path(directory))
            encoded = json.loads(json.dumps(original.to_json()))
            restored = ProducerSpec.parse(encoded)
            self.assertEqual(restored, original)
            self.assertEqual(restored.identity.to_json(), original.identity.to_json())

    def test_spec_rejects_bool_float_missing_extra_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original = fixture_spec(Path(directory)).to_json()
            for key, value in (("schema_version", True), ("schema_version", 1.0), ("maximum_log_bytes", False),
                               ("timeout_seconds", 2.0), ("maximum_melted_bytes", None)):
                changed: dict[str, object] = dict(original)
                changed[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    ProducerSpec.parse(changed)
            for alternate in ({key: value for key, value in original.items() if key != "storage"}, {**original, "legacy_alias": True}):
                with self.assertRaises(ValueError):
                    ProducerSpec.parse(alternate)

    def test_actual_request_native_source_identity_and_machine_are_joined(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            spec = fixture_spec(Path(directory))
            request, source, response = validate_request(spec, machine_id="unit-machine", now=datetime(2026, 1, 1, tzinfo=timezone.utc))
            self.assertEqual(source, pin(Path(directory) / "source.ck3"))
            self.assertEqual(response.name, "checkpoint-readback-01-root-result.json")
            self.assertIsNone(request["expected_target_id"])
            with self.assertRaisesRegex(ValueError, "another machine"):
                validate_request(spec, machine_id="another-machine", now=datetime(2026, 1, 1, tzinfo=timezone.utc))

    def test_identity_rejects_float_bool_noncanonical_64_bit_strings(self) -> None:
        original = Identity("unit-run", "unit-machine", "unit-root", 124, "9", 91, 123456).to_json()
        for key, value in (("pid", True), ("actor_character_id", 91.0), ("date_raw", False), ("connection_generation", 9), ("connection_generation", "09")):
            changed: dict[str, object] = dict(original)
            changed[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                Identity.parse(changed)

    def test_raw_native_boundary_keeps_64_bits_but_rejects_duplicate_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "raw.json"
            path.write_text('{"opaque_native_q64":18446744073709551614}', encoding="utf-8")
            self.assertEqual(raw_object(path)["opaque_native_q64"], 18446744073709551614)
            path.write_text('{"schema":1,"schema":2}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                raw_object(path)

    def test_exact_source_preservation_and_same_size_changed_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.ck3"
            source.write_bytes(b"abc")
            expected = pin(source)
            copied, identity = preserve_source(expected, root / "copy.ck3")
            self.assertEqual(copied["sha256"], expected["sha256"])
            self.assertIsInstance(identity["mtime_ns_decimal"], str)
            self.assertEqual(identity["size_bytes"], 3)
            source.write_bytes(b"abd")
            with self.assertRaisesRegex(ValueError, "differ"):
                preserve_source(expected, root / "mismatch.ck3")

    def test_real_benign_child_exit_and_empty_stream_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            actual = execute_melter((subject_python(), "-c", "import sys; print('actual child'); sys.exit(7)"),
                                   output=output, timeout=3, maximum_melted=1024, maximum_log=1024)
            self.assertEqual((actual.status, actual.exit_code), ("exited", 7))
            self.assertIsNotNone(actual.pid)
            self.assertIn(b"actual child", (output / "stdout.log").read_bytes())
            self.assertEqual((output / "stderr.log").read_bytes(), b"")

    def test_launch_failure_never_invents_pid_or_exit_zero(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            actual = execute_melter((str(output / "absent-tool.exe"),), output=output, timeout=1, maximum_melted=1024, maximum_log=1024)
            self.assertEqual(actual.status, "launch_failed")
            self.assertIsNone(actual.pid)
            self.assertIsNone(actual.exit_code)
            self.assertIsNotNone(actual.failure)

    def test_actual_empty_child_streams_reach_consumer_without_a_sentinel(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            actual = execute_melter((subject_python(), "-c", "pass"), output=output, timeout=3, maximum_melted=1024, maximum_log=1024)
            self.assertEqual((actual.status, actual.exit_code), ("exited", 0))
            for name in ("stdout.log", "stderr.log"):
                reference = pin(output / name)
                self.assertEqual(reference["bytes"], 0)
                self.assertEqual(checked_pin(reference, "actual empty log", allow_empty=True), reference)
                with self.assertRaises(ValueError):
                    checked_pin(reference, "non-log artifacts stay nonempty")

    def test_real_failed_empty_child_streams_preserve_blocked_reason_in_consumer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            actual = execute_melter((subject_python(), "-c", "import sys; sys.exit(7)"), output=output, timeout=3, maximum_melted=1024, maximum_log=1024)
            self.assertEqual(actual.exit_code, 7)
            evidence = [pin(output / "stdout.log"), pin(output / "stderr.log")]
            self.assertEqual([item["bytes"] for item in evidence], [0, 0])
            identity = Identity("unit-run", "unit-machine", "unit-root", 124, "9", 91, 123456)
            response = blocked_response(identity, reason=f"Actual strict melt exit={actual.exit_code}", evidence=evidence)
            retained = write_once(output / "blocked.json", response)
            source = output / "source.ck3"
            source.write_bytes(b"authored boundary input")
            with self.assertRaisesRegex(ValueError, "BLOCKED: Actual strict melt exit=7"):
                verify_readback(read(Path(retained["path"])), run_id="unit-run", machine_id="unit-machine", reviewer="unit-root",
                    frame=Frame(3, 2, 123456, 91, 124, "9"), source_save=pin(source))

    def test_real_child_timeout_and_output_limit_cannot_complete(self) -> None:
        for expression, timeout, maximum, expected in (("import time; time.sleep(5)", 1, 1024, "timeout"),
                                                       ("print('X'*4096)", 3, 1024, "output_limit")):
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as directory:
                actual = execute_melter((subject_python(), "-c", expression), output=Path(directory), timeout=timeout,
                                       maximum_melted=1024, maximum_log=maximum)
                self.assertEqual(actual.status, expected)
                self.assertIsNotNone(actual.exit_code)

    def test_common_storage_formula_counts_full_existing_holds_conservatively(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            spec = storage_fixture(Path(directory))
            with patch("checkpoint_producer.shutil.disk_usage", return_value=AuthoredDisk()):
                result = storage_admission(spec, source_bytes=100, now=datetime(2026, 1, 2, tzinfo=timezone.utc))
            self.assertEqual(result["status"], "ADMITTED_FOR_THIS_COPY_MELT_ONLY")
            self.assertFalse(result["new_reservation_created"])
            self.assertEqual(result["projected_usage_upper_bound_bytes"], 1000 + 2 * 1024**3 + integer(result["this_write_peak_bytes"], "observed peak"))

    def test_missing_bool_float_storage_inputs_never_become_zero(self) -> None:
        for name, value in (("current_project_usage_bytes", None), ("current_project_usage_bytes", 1000.0),
                            ("system_growth_reserve_bytes", True), ("other_unspent_reservations_bytes", None)):
            with self.subTest(name=name, value=value), tempfile.TemporaryDirectory() as directory:
                spec = storage_fixture(Path(directory), wrong_budget=(name, value))
                with patch("checkpoint_producer.shutil.disk_usage", return_value=AuthoredDisk()), self.assertRaises(ValueError):
                    storage_admission(spec, source_bytes=100, now=datetime(2026, 1, 2, tzinfo=timezone.utc))

    def test_expired_storage_and_insufficient_fresh_space_block(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            spec = storage_fixture(Path(directory))
            with self.assertRaisesRegex(ValueError, "unexpired"):
                storage_admission(spec, source_bytes=100, now=datetime(2028, 1, 1, tzinfo=timezone.utc))
            with patch("checkpoint_producer.shutil.disk_usage", return_value=AuthoredDisk(free=1)), self.assertRaisesRegex(ValueError, "capacity"):
                storage_admission(spec, source_bytes=100, now=datetime(2026, 1, 2, tzinfo=timezone.utc))


if __name__ == "__main__":
    unittest.main()
