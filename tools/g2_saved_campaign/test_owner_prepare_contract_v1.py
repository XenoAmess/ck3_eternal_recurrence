"""Preparation type errors must not consume a create-only owner attempt."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import ast
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from typing import get_type_hints

import interactive_task_owner_v1 as owner
from owner_prepare_contract_v1 import OwnerPrepareInputsV1, validate_owner_prepare_inputs_v1


class OwnerPrepareContractTests(unittest.TestCase):
    def inputs(self) -> dict[str, object]:
        return dict(machine_id="synthetic-test-only", role="sdk_owner", stage_args=(),
                    pythonpath=None, enable_driver_state_wal=False)

    def test_tuple_and_list_keep_exact_argument_boundaries(self) -> None:
        for argv in ([], (), ["--qualify", "value with spaces"], ("--qualify", "value with spaces")):
            result = validate_owner_prepare_inputs_v1(**{**self.inputs(), "stage_args": argv})
            self.assertEqual(result.stage_args, tuple(argv))
            self.assertEqual(result.machine_id, "synthetic-test-only")
        with self.assertRaises(FrozenInstanceError):
            result.machine_id = "changed"

    def test_invalid_fields_are_rejected_before_os_or_create_only_writes(self) -> None:
        changes = [
            {"stage_args": "--qualify"}, {"stage_args": b"--qualify"},
            {"stage_args": [1]}, {"stage_args": ["bad\0arg"]},
            {"stage_args": ["x"] * 129}, {"machine_id": 123},
            {"machine_id": " "}, {"pythonpath": Path("unread")},
            {"pythonpath": "bad\0path"}, {"enable_driver_state_wal": 1},
            {"role": "feeder", "enable_driver_state_wal": True},
        ]
        preparation = dict(root="uncreated-owner-root", role="sdk_owner", stage="stage.py",
            stage_sha256="b" * 64, bootstrap_path="independent-bootstrap.py", cwd=".",
            machine_id="synthetic-test-only")
        with patch.object(owner, "Windows", side_effect=AssertionError("OS reached")), patch.object(
            owner, "sha", return_value="b" * 64
        ), patch.object(Path, "mkdir", side_effect=AssertionError("mkdir reached")), patch.object(
            owner, "once", side_effect=AssertionError("SPEC write reached")
        ):
            for changed in changes:
                with self.subTest(changed=changed), self.assertRaises(ValueError):
                    owner.prepare_spec(**{**preparation, **changed})

    def test_public_preparation_signature_resolves_without_helper_imports(self) -> None:
        hints = get_type_hints(owner.prepare_spec)
        self.assertIs(hints["return"], owner.PreparedOwnerReceiptV1)
        self.assertEqual(hints["role"], get_type_hints(OwnerPrepareInputsV1)["role"])
        self.assertEqual(set(get_type_hints(owner.PreparedOwnerReceiptV1)), {
            "machine_id", "utc", "spec", "spec_sha256", "task_name", "registered",
        })

    def test_arbitrary_file_loader_does_not_require_sibling_on_sys_path(self) -> None:
        source = str(Path(owner.__file__).resolve())
        program = "\n".join([
            "import importlib.util, sys, types",
            "from pathlib import Path",
            "from unittest.mock import patch",
            "source = Path(sys.argv[1]).resolve()",
            "sys.path[:] = [p for p in sys.path if Path(p or '.').resolve() != source.parent]",
            "sys.modules['owner_prepare_contract_v1'] = types.ModuleType('ambient_canary')",
            "spec = importlib.util.spec_from_file_location('arbitrary_production_owner_name', source)",
            "module = importlib.util.module_from_spec(spec)",
            "sys.modules[spec.name] = module",
            "spec.loader.exec_module(module)",
            "with patch.object(module, 'Windows', side_effect=AssertionError('OS reached')), patch.object(Path, 'mkdir', side_effect=AssertionError('mkdir reached')), patch.object(module, 'once', side_effect=AssertionError('write reached')):",
            "    try:",
            "        module.prepare_spec(root='uncreated', role='sdk_owner', stage='unread.py', stage_sha256='b'*64, bootstrap_path='unread-bootstrap.py', cwd='.', machine_id='synthetic-only', stage_args='--qualify')",
            "    except ValueError as error:",
            "        assert 'stage_args' in str(error), str(error)",
            "    else:",
            "        raise AssertionError('malformed argv was accepted')",
            "assert sys.modules['owner_prepare_contract_v1'].__name__ == 'ambient_canary'",
            "print('isolated source-bound parser passed')",
        ])
        result = subprocess.run([sys.executable, "-B", "-c", program, source],
                                capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("isolated source-bound parser passed", result.stdout)

    @unittest.skipUnless(importlib.util.find_spec("mypy"), "isolated checker is optional at runtime")
    def test_strict_checker_rejects_wrong_fields_and_value_types(self) -> None:
        from mypy import api
        repo = Path(__file__).resolve().parents[2]
        source = Path(owner.__file__).read_text(encoding="utf-8")
        receipt = next(node for node in ast.parse(source).body
                       if isinstance(node, ast.ClassDef) and node.name == "PreparedOwnerReceiptV1")
        # Check the actual self-contained bootstrap DTO, without pretending
        # that the legacy COM owner module is already in the strict lane.
        receipt_source = ast.get_source_segment(source, receipt)
        self.assertIsNotNone(receipt_source)
        code = "\n".join([
            "from typing import Literal, TypedDict",
            "from owner_prepare_contract_v1 import OwnerPrepareInputsV1",
            receipt_source or "",
            "value = OwnerPrepareInputsV1(machine_id=123, role='sdk_owner', stage_args='--qualify', pythonpath=None, enable_driver_state_wal=False)",
            "print(value.stage_arguments)",
            "receipt: PreparedOwnerReceiptV1 = {'machine_id': 'synthetic', 'utc': '', 'spec': '', 'spec_sha256': '', 'task_name': '', 'registered': False, 'spec_sha': ''}",
        ])
        # The checked-in config lists two file targets; command targets need
        # their own strict invocation instead of combining both target modes.
        with patch.dict(os.environ, {"MYPYPATH": str(repo / "tools/g2_saved_campaign")}):
            stdout, stderr, status = api.run([
                "--config-file=", "--strict", "--python-version=3.11",
                "--no-incremental", "--cache-dir", "nul", "-c", code,
            ])
        self.assertEqual(status, 1, (stdout, stderr))
        for error in ("[arg-type]", "[attr-defined]", "[typeddict-unknown-key]"):
            self.assertIn(error, stdout)


if __name__ == "__main__":
    unittest.main()
