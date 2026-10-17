"""Portable source-contract tests. No files, runtime state or Native calls."""
import ast
import copy
from pathlib import Path
import unittest
import json

from tools.g2_saved_campaign.campaign_root_paused_boundary_readonly import (
    classify_campaign_root_paused_boundary_readonly_v1 as qualify,
)


def rejection_row(sequence=1, native_revision=3, request_id="step-1-000000000000"):
    return {
        "request": {"sequence": sequence, "tool": "ck3_auto_turn", "arguments": {}},
        "result": {
            "is_error": True, "result_type": "complete",
            "structured_content": {
                "error_type": "_NativeCommandRejectedError",
                "diagnostics": {"native_command_rejection": {
                    "diagnostic_only": True,
                    "native_request_id": request_id,
                    "native_step": "query-campaign-root-context-v1",
                    "expected_native_revision": native_revision,
                    "native_error": "paused application-main boundary is not ready",
                }},
            },
            "content": [{"type": "text", "text": (
                "Error executing tool ck3_auto_turn: native gameplay step failed: "
                "paused application-main boundary is not ready"
            )}],
        },
    }


def diagnostic(row):
    return row["result"]["structured_content"]["diagnostics"]["native_command_rejection"]


class QualifierTests(unittest.TestCase):
    def test_completed_actual247_error_is_preserved(self):
        fixture = json.loads((Path(__file__).with_name('fixtures') /
                              'campaign_root_paused_boundary_actual247.json').read_bytes())
        row = fixture['row']
        before = copy.deepcopy(row)
        evidence = qualify(row)
        self.assertEqual(row, before)
        self.assertTrue(evidence['read_only_precondition'])
        self.assertIs(evidence['business_submission'], False)
        self.assertIs(evidence['original_action_replay_allowed'], False)
        self.assertEqual(evidence['native_request_id'], diagnostic(row)['native_request_id'])
        self.assertEqual(evidence['source_native_revision'], diagnostic(row)['expected_native_revision'])

    def test_exact_readonly_admission_failure(self):
        row = rejection_row()
        before = copy.deepcopy(row)
        evidence = qualify(row)
        self.assertEqual(row, before)
        self.assertEqual(evidence["classification"], "campaign_root_paused_boundary_not_ready_before_query")
        self.assertTrue(evidence["read_only_precondition"])
        for key in ("business_submission", "campaign_query_executor_submitted",
                    "campaign_root_read_attempted", "original_action_replay_allowed"):
            self.assertIs(evidence[key], False)
        self.assertEqual(evidence["source_native_revision"], 3)

    def test_identity_fields_are_not_fixed_to_one_runtime(self):
        for sequence, revision, identity in (
            (1, 1, "step-1-000000000000"),
            (27, 2**64-1, "step-987-abcdef012345"),
        ):
            with self.subTest(sequence=sequence, revision=revision):
                result = qualify(rejection_row(sequence, revision, identity))
                self.assertEqual(result["source_native_revision"], revision)
                self.assertEqual(result["native_request_id"], identity)

    def test_business_other_queries_and_unproven_errors_reject(self):
        cases = {
            "move": {"native_step": "move-army-1-to-2"},
            "pause": {"native_step": "pause-map"},
            "other_query": {"native_step": "query-loaded-feature-manifest-v1"},
            "busy": {"native_error": "application-main typed query executor is unavailable or busy"},
            "timeout": {"native_error": "application-main typed query timed out"},
            "not_diagnostic": {"diagnostic_only": False},
            "empty_id": {"native_request_id": ""},
            "wrong_id": {"native_request_id": "business-1"},
            "zero_native_revision": {"expected_native_revision": 0},
            "bool_native_revision": {"expected_native_revision": True},
            "overflow_native_revision": {"expected_native_revision": 2**64},
            "unknown_field": {"business_submission": True},
        }
        for name, changes in cases.items():
            with self.subTest(name=name):
                row = rejection_row()
                diagnostic(row).update(changes)
                self.assertIsNone(qualify(row))

    def test_incomplete_unknown_or_non_auto_response_rejects(self):
        def replace_error(row):
            row["result"]["structured_content"]["error_type"] = "BridgeUnavailableError"
        cases = {
            "client_error": lambda r: r.update(client_error="timeout"),
            "pending": lambda r: r["result"].update(result_type="pending"),
            "success": lambda r: r["result"].update(is_error=False),
            "arguments": lambda r: r["request"].update(arguments={"unsafe": True}),
            "wrong_tool": lambda r: r["request"].update(tool="ck3_execute_step"),
            "wrong_text": lambda r: r["result"]["content"][0].update(text="another error"),
            "missing_packet": lambda r: r["result"].update(structured_content=None),
            "malformed_diagnostics": lambda r: r["result"]["structured_content"].update(diagnostics=[]),
            "wrong_error_type": replace_error,
        }
        for name, change in cases.items():
            with self.subTest(name=name):
                row = rejection_row()
                change(row)
                self.assertIsNone(qualify(row))

    def test_formal_registry_ast_subset_needs_no_module_globals(self):
        path = Path(qualify.__code__.co_filename)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        selected = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "classify_campaign_root_paused_boundary_readonly_v1"]
        self.assertEqual(len(selected), 1)
        namespace = {}
        exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), namespace)
        self.assertEqual(namespace[selected[0].name](rejection_row()), qualify(rejection_row()))


if __name__ == "__main__":
    unittest.main()
