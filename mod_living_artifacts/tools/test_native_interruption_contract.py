"""Real producer -> public file checkpoint -> product consumer, without CK3."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from typing import Protocol, runtime_checkable

from acceptance_contract import Object, json_value, object_value, pin, write_once
from ck3_mod_acceptance import MANIFEST_SCHEMA, PRODUCTS_SCHEMA, RUNTIME_SCHEMA, Selection
from ck3_mod_acceptance_client import CaseClient
from native_interruption_contract import NativeInterruptionRequest, completed_interruption_response, parse_completed_interruption


@runtime_checkable
class RootCheckpointConsumer(Protocol):
    """Narrow typed boundary to the existing untyped shared public method."""
    def root_checkpoint(self, name: str, request: Object, reserve: int = 90) -> object: ...


class PublicCheckpointPort(CaseClient):
    """Only the time/native guard is authored; use the real checkpoint method."""
    def __init__(self, output: Path) -> None:
        # Use the real selector with authored static inputs; no host/game executes.
        output.mkdir(parents=True, exist_ok=True)
        fixture = Path(tempfile.mkdtemp(prefix="checkpoint-selection-", dir=output))
        authored = fixture / "never-executed-static-input.json"
        reference = write_once(authored, {"authored_offline_input_only": True})
        row: Object = {"path_key": "authored", "bytes": reference["bytes"], "sha256": reference["sha256"]}
        manifest = fixture / "manifest.json"
        write_once(manifest, {"schema": MANIFEST_SCHEMA, "source_root": {"path_key": "source_root"},
            "host": row, "source_index": row, "native_source_index": row,
            "native": {"dll": row, "injector": row}})
        runtime = fixture / "runtime.json"
        write_once(runtime, {"schema": RUNTIME_SCHEMA, "manifest": pin(manifest), "python": sys.executable,
            "repo_root": str(fixture), "game_dir": str(fixture), "userdir_root": str(fixture),
            "artifacts_root": str(fixture), "paths": {"source_root": str(fixture), "authored": str(authored)}})
        products = fixture / "products.json"
        case: Object = {"id": "native-interruption-contract",
            "startup": {"mode": "ordinary_gui_campaign", "state_dir": str(fixture / "state")},
            "initial_plan": str(authored), "required_mcp_tools": [],
            "budgets": {"command_timeout": 300, "readiness_timeout": 1800, "timeout": 4800,
                "poll_interval": 0.05, "hold_seconds": 1800},
            "normal_close": {"owner": "shared entry/CaseClient", "reserve_seconds": 180,
                "actual_retained_OS0_and_original_native0_required": True}}
        write_once(products, {"schema": PRODUCTS_SCHEMA, "products": {"living-artifacts": {"cases": [case]}}})
        self.selection = Selection(runtime, products, "living-artifacts", "native-interruption-contract")
        self.output = output
        self.frozen = {"run_id": "unit-run"}
        self.operator_reviewer = "unit-root"
        self._hold = 9999999999.0

    def remaining(self) -> float:
        return 1000.0

    def guard(self, reserve: int = 90, *, failure_shutdown: bool = False,
              normal_exit_steps: list[Object] | None = None) -> dict[str, object]:
        return {"authored_offline_transport": True}


def request_fixture(directory: Path) -> NativeInterruptionRequest:
    source = directory / 'authored-native-frame.json'
    source.write_text('{"authored_test":true}', encoding='utf-8')
    return {"schema": "living-artifacts-native-interruption-request-v1", "run_id": "unit-run", "machine_id": "unit-machine",
            "kind": "interaction", "instance_id": 67108864, "date_raw": 53144928,
            "original_native_frame_record": pin(source), "existing_specialist_policy_priority": True,
            "unknown_event_first_displayed_or_interaction_legal_left": True, "no_replay_of_unknown": True}


class InterruptionResponseTests(unittest.TestCase):
    def test_actual_encoder_file_public_checkpoint_product_parser_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "not-created" / "checkpoint"
            self.assertFalse(output.exists())
            port = PublicCheckpointPort(output)
            self.assertIsInstance(port.selection, Selection)
            request = request_fixture(output)
            generated = completed_interruption_response(request, reviewer="unit-root")
            encoded = json_value(generated)
            write_once(output / 'review-root-result.json', object_value(encoded))
            public: RootCheckpointConsumer = port
            self.assertIsInstance(public, RootCheckpointConsumer)
            actual = public.root_checkpoint('review', object_value(request))
            parsed = parse_completed_interruption(actual, request=request, reviewer='unit-root')
            self.assertEqual(parsed, generated)
            awaiting = object_value(json.loads((output / 'review-awaiting.json').read_bytes()))
            self.assertEqual(awaiting['run_id'], parsed['run_id'])
            self.assertEqual(awaiting['reserve_seconds'], 180)

    def test_original_r7_missing_envelope_is_rejected_by_actual_public_consumer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            request = request_fixture(output)
            write_once(output / 'review-root-result.json', {"native_interruption_continued": True, "original_instance_independently_absent": True})
            with self.assertRaisesRegex(ValueError, 'Root checkpoint crossed scene'):
                public: RootCheckpointConsumer = PublicCheckpointPort(output)
                public.root_checkpoint('review', object_value(request), reserve=180)

    def test_missing_extra_wrong_identity_false_equal_numbers_and_flags_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            request = request_fixture(Path(temporary))
            generated: Object = object_value(completed_interruption_response(request, reviewer='unit-root'))
            wrong: tuple[tuple[str, object], ...] = (("instance_id", True), ("instance_id", 67108864.0),
                ("date_raw", 53144928.0), ("date_raw", True), ("run_id", "other-run"), ("machine_id", "other-machine"),
                ("reviewer", "other-root"), ("kind", "event"), ("schema", "other"),
                ("native_interruption_continued", 1), ("original_instance_independently_absent", False))
            for key, replacement in wrong:
                with self.subTest(key=key, replacement=replacement), self.assertRaises(ValueError):
                    parse_completed_interruption({**generated, key: replacement}, request=request, reviewer='unit-root')
            for key in generated:
                with self.subTest(missing=key), self.assertRaises(ValueError):
                    parse_completed_interruption({name: value for name, value in generated.items() if name != key}, request=request, reviewer='unit-root')
            with self.assertRaises(ValueError):
                parse_completed_interruption({**generated, 'extra': True}, request=request, reviewer='unit-root')


if __name__ == '__main__':
    unittest.main()
