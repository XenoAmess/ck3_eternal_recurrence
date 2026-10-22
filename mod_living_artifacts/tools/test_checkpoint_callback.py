"""Strict saved-readback callback boundary regressions, no engine qualification."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from acceptance_contract import Frame, Object, Pin, json_value, pin, read, write_once
from checkpoint_callback import CheckpointSample, verify_readback
from living_artifacts_model import FEEDING_XP, Rarity
from test_checkpoint_artifacts import AUTHORED_ARTIFACTS, AuthoredArtifact, authored_checkpoint_text, authored_survivors


def callback_fixture(root: Path, *, artifacts: tuple[AuthoredArtifact, ...] = AUTHORED_ARTIFACTS) -> tuple[Object, Frame, Pin]:
    raw = root / "original.ck3"
    raw.write_bytes(b"authored-binary-not-game-evidence")
    melted = root / "melted.ck3"
    melted.write_text(authored_checkpoint_text(artifacts), encoding="utf-8")
    melter = root / "not-an-executable.txt"
    melter.write_text("Authored boundary fixture; never executed", encoding="utf-8")
    raw_pin, melted_pin, melter_pin = pin(raw), pin(melted), pin(melter)
    command = write_once(root / "command.json", {"argv": [melter_pin["path"], "melt", raw_pin["path"], "--format", "ck3", "--unknown-key", "error", "-o", melted_pin["path"]]})
    (root / "stdout.log").write_bytes(b"")
    (root / "stderr.log").write_bytes(b"")
    request = write_once(root / "request.json", {"run_id": "unit-run", "machine_id": "unit-machine", "operator_reviewer": "unit-root",
        "pid": 124, "connection_generation": "9", "actor_character_id": 91, "date_raw": 123456, "actual_source_save": raw_pin})
    spec = write_once(root / "spec.json", {"authored_test": True})
    storage = write_once(root / "storage.json", {"authored_test": True})
    receipt = write_once(root / "process.json", {"schema": "living-artifacts-checkpoint-melt-process-v2", "machine_id": "unit-machine", "run_id": "unit-run",
        "exit_code": 0, "status": "exited", "failure": None, "process_pid": 99, "raw": raw_pin, "melted": melted_pin, "melter": melter_pin, "command": command,
        "stdout": pin(root / "stdout.log"), "stderr": pin(root / "stderr.log"), "request": request, "spec": spec, "storage_check": storage,
        "source_file_identity": {"device_id_decimal": "1", "file_id_decimal": "2", "mtime_ns_decimal": "1800000000000000000", "size_bytes": raw_pin["bytes"]},
        "started_at_utc": "2000-01-01T00:00:00Z", "finished_at_utc": "2000-01-01T00:00:01Z", "game_commands_sent": False})
    response: Object = {"schema": "living-artifacts-checkpoint-readback-v1", "schema_version": 1, "status": "completed", "run_id": "unit-run",
        "machine_id": "unit-machine", "reviewer": "unit-root", "pid": 124, "connection_generation": "9", "actor_character_id": 91, "date_raw": 123456,
        "source_save": json_value(raw_pin), "melted_save": json_value(melted_pin), "melter": json_value(melter_pin),
        "command": json_value(command), "process_receipt": json_value(receipt)}
    return response, Frame(3, 2, 123456, 91, 124, "9"), raw_pin


class CheckpointCallbackTests(unittest.TestCase):
    def test_closed_callback_to_actual_file_parser_to_sample(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            response, frame, _ = callback_fixture(root)
            inputs, refs = verify_readback(response, run_id="unit-run", machine_id="unit-machine", reviewer="unit-root", frame=frame, source_save=pin(root / "original.ck3"))
            sample = CheckpointSample.from_saved(inputs.artifacts[0], inputs, native_equipped=True)
            self.assertEqual((sample.level, sample.xp, sample.pending, sample.growth_sequence, sample.month), (1, 92, 0, 0, 12801))
            self.assertTrue(sample.equipped)
            self.assertEqual(len(refs), 10)
            self.assertFalse(sample.to_json()["current_native_artifact_variable_query"])

    def test_surviving_rarities_cross_serialized_callback_and_strict_melt_evidence(self) -> None:
        rarities = tuple(FEEDING_XP)
        for consumed_count in range(len(rarities) + 1):
            remaining = rarities[consumed_count:]
            artifacts = authored_survivors(remaining)
            with self.subTest(consumed_count=consumed_count), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                response, frame, source_save = callback_fixture(root, artifacts=artifacts)
                response_pin = write_once(root / "serialized-root-response.json", response)
                decoded = read(Path(response_pin["path"]))
                inputs, refs = verify_readback(decoded, run_id="unit-run", machine_id="unit-machine", reviewer="unit-root",
                    frame=frame, source_save=source_save, expected_material_rarities=remaining)
                self.assertEqual(tuple(item.artifact_id for item in inputs.artifacts), tuple(item.reference for item in artifacts))
                self.assertEqual(len(refs), 10)
                self.assertEqual(refs[0], source_save)
                self.assertEqual(refs[1], pin(root / "melted.ck3"))
                command = read(root / "command.json")
                self.assertEqual(command["argv"], [str((root / "not-an-executable.txt").resolve()), "melt", source_save["path"],
                    "--format", "ck3", "--unknown-key", "error", "-o", refs[1]["path"]])
                sample = CheckpointSample.from_saved(inputs.artifacts[0], inputs, native_equipped=True)
                self.assertEqual((sample.artifact_id, sample.level, sample.xp), ("12", 1, 92))
                if consumed_count:
                    with self.assertRaisesRegex(ValueError, "surviving material roles"):
                        verify_readback(decoded, run_id="unit-run", machine_id="unit-machine", reviewer="unit-root",
                            frame=frame, source_save=source_save)

    def test_survivor_expectation_never_waives_wrong_consumption_or_missing_target(self) -> None:
        remaining: tuple[Rarity, ...] = ("masterwork", "famed", "illustrious")
        wrong_consumed = tuple(item for item in AUTHORED_ARTIFACTS if item.reference != "14")
        absent_target = tuple(item for item in authored_survivors(remaining) if item.reference != "12")
        for artifacts in (AUTHORED_ARTIFACTS, wrong_consumed, absent_target):
            with self.subTest(references=tuple(item.reference for item in artifacts)), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                response, frame, source_save = callback_fixture(root, artifacts=artifacts)
                with self.assertRaisesRegex(ValueError, "surviving material roles"):
                    verify_readback(response, run_id="unit-run", machine_id="unit-machine", reviewer="unit-root",
                        frame=frame, source_save=source_save, expected_material_rarities=remaining)

    def test_callback_propagates_invalid_survivor_contract_to_real_saved_parser(self) -> None:
        malformed: tuple[object, ...] = (None, True, False, 1, 1.0, "common", ["common"],
            (True,), (False,), (1,), (1.0,), (["common"],), ("common", "common"), ("legendary",), (None,))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            response, frame, source_save = callback_fixture(root)
            for value in malformed:
                with self.subTest(value=value):
                    # This deliberate malformed runtime call still traverses the
                    # callback's real pinned-file and strict argv checks first.
                    self.assertRaisesRegex(ValueError, "Explicit unique native material rarities", verify_readback,
                        response, run_id="unit-run", machine_id="unit-machine", reviewer="unit-root",
                        frame=frame, source_save=source_save, expected_material_rarities=value)

    def test_consumed_materials_do_not_waive_strict_melt_unknown_token_policy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            response, frame, source_save = callback_fixture(root, artifacts=authored_survivors(()))
            argv: list[str] = [str((root / "not-an-executable.txt").resolve()), "melt", source_save["path"],
                "--format", "ck3", "--unknown-key", "ignore", "-o", str((root / "melted.ck3").resolve())]
            # Re-pin a coherent authored receipt chain. A pin mismatch must not
            # hide the actual strict-policy rejection being exercised here.
            command = write_once(root / "nonstrict-command.json", {"argv": argv})
            process = read(root / "process.json")
            process["command"] = json_value(command)
            receipt = write_once(root / "nonstrict-process.json", process)
            response["command"] = json_value(command)
            response["process_receipt"] = json_value(receipt)
            with self.assertRaisesRegex(ValueError, "strict unknown-token policy"):
                verify_readback(response, run_id="unit-run", machine_id="unit-machine", reviewer="unit-root",
                    frame=frame, source_save=source_save, expected_material_rarities=())

    def test_false_equal_types_missing_extra_cross_identity_and_ack_rejected(self) -> None:
        mutations: tuple[tuple[str, object], ...] = (("schema_version", True), ("schema_version", 1.0), ("pid", 124.0),
            ("connection_generation", 9), ("date_raw", 123457), ("actor_character_id", 92), ("machine_id", "other"), ("status", "acknowledged"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original, frame, _ = callback_fixture(root)
            for key, value in mutations:
                response: dict[str, object] = dict(original)
                response[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    verify_readback(response, run_id="unit-run", machine_id="unit-machine", reviewer="unit-root", frame=frame, source_save=pin(root / "original.ck3"))
            for modified in ({key: item for key, item in original.items() if key != "melter"}, {**original, "PASS": True}):
                with self.assertRaises(ValueError):
                    verify_readback(modified, run_id="unit-run", machine_id="unit-machine", reviewer="unit-root", frame=frame, source_save=pin(root / "original.ck3"))

    def test_actual_raw_bytes_and_strict_melt_argv_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            response, frame, _ = callback_fixture(root)
            (root / "original.ck3").write_bytes(b"different actual checkpoint")
            with self.assertRaisesRegex(ValueError, "changed"):
                verify_readback(response, run_id="unit-run", machine_id="unit-machine", reviewer="unit-root", frame=frame, source_save=pin(root / "original.ck3"))


if __name__ == "__main__":
    unittest.main()
