"""Strict saved-readback callback boundary regressions, no engine qualification."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from acceptance_contract import Frame, Object, Pin, json_value, pin, write_once
from checkpoint_callback import CheckpointSample, verify_readback


def callback_fixture(root: Path) -> tuple[Object, Frame, Pin]:
    raw = root / "original.ck3"
    raw.write_bytes(b"authored-binary-not-game-evidence")
    melted = root / "melted.ck3"
    artifact_records = ""
    for reference, name, rarity in ((12, "Living Artifact Under Test", "masterwork"), (13, "Test Food: Common", "common"),
                                  (14, "Test Food: Masterwork", "masterwork"), (15, "Test Food: Famed", "famed"), (16, "Test Food: Illustrious", "illustrious")):
        values = ""
        if reference == 12:
            for key, number in (("level", 1), ("xp_in_level", 92), ("pending_xp", 0), ("growth_sequence", 0), ("last_settled_month", 12801), ("resonance", 20)):
                values += '{ flag="xalw_' + key + '" data={ type=value identity=' + str(number * 100000) + ' } } '
        artifact_records += f'\t\t{reference}={{\n\t\t\tname="{name}"\n\t\t\ttype="sword"\n\t\t\trarity={rarity}\n\t\t\towner=91\n\t\t\tdurability=75\n\t\t\tvariables={{ data={{ {values} }} }}\n\t\t}}\n'
    melted.write_text('date=1066.9.15\nliving={\n\t91={\n\t\talive_data={\n\t\t\tvariables={ data={ { flag="xalw_fixture_target" data={ type=artifact identity=12 } } } }\n\t\t}\n\t}\n}\nartifacts={\n\tartifacts={\n' + artifact_records + '\t}\n}\n', encoding="utf-8")
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
