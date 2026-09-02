from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[2]
RUNNER = (
    ROOT
    / "native_bridge"
    / "research"
    / "run_war_termination_terms_live_acceptance.py"
)
FIXTURE = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "g2_index7_evaluator_mcp_envelope_red_v1.json"
)


def _load_runner():
    spec = importlib.util.spec_from_file_location("war_terms_live", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load war-termination live runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _TextBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text

    def model_dump(self, *, mode: str, by_alias: bool):
        if mode != "json" or by_alias is not True:
            raise ValueError("unexpected dump mode")
        return {"type": self.type, "text": self.text}


class WarTerminationTermsLiveEnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = _load_runner()
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_fixture_preserves_exact_live_report_terminal_shape(self) -> None:
        observed = self.fixture["observed_report_shape"]
        self.assertEqual(
            self.fixture["source_report_sha256"],
            "4460C7E89A5F16BBE194A295D7C207788FCD38CE52D60359C8FEF5D746FBE383",
        )
        self.assertEqual(
            observed["error"],
            "RuntimeError: official MCP result lacks structured_content",
        )
        self.assertIsNone(observed["mcp_sequence"])
        self.assertTrue(observed["readiness_present"])
        self.assertTrue(observed["exact_build_proof_ok"])
        self.assertEqual(observed["session_exit_code"], 1)
        self.assertFalse(observed["private_jsonl_present"])

    def test_missing_structured_content_retains_official_error_envelope(self) -> None:
        envelope = self.fixture["deterministic_error_envelope"]
        result = SimpleNamespace(
            is_error=envelope["is_error"],
            structured_content=envelope["structured_content"],
            content=[_TextBlock(envelope["content"][0]["text"])],
        )
        with self.assertRaises(
            self.runner.OfficialMcpResultEnvelopeError
        ) as raised:
            self.runner._structured(
                result,
                tool_name="ck3_query_war_termination_terms:first",
            )
        diagnostic = raised.exception.diagnostic()
        expected = self.fixture["expected_diagnostic"]
        self.assertEqual(diagnostic["status"], expected["status"])
        self.assertFalse(diagnostic["ok"])
        self.assertEqual(diagnostic["failed_tool"], expected["failed_tool"])
        self.assertEqual(
            diagnostic["result"]["result_type"], "SimpleNamespace"
        )
        self.assertTrue(diagnostic["result"]["is_error"])
        self.assertIsNone(diagnostic["result"]["structured_content"])
        self.assertEqual(diagnostic["result"]["content"], envelope["content"])
        self.assertIn("content_count=1", str(raised.exception))

    def test_valid_structured_content_remains_strictly_object_typed(self) -> None:
        value = {"revision": 4, "paused": True}
        result = SimpleNamespace(
            is_error=False,
            structured_content=value,
            content=[],
        )
        actual = self.runner._structured(result, tool_name="ck3_take_snapshot")
        self.assertEqual(actual, value)
        self.assertIsNot(actual, value)
        with self.assertRaises(self.runner.OfficialMcpResultEnvelopeError):
            self.runner._structured(
                SimpleNamespace(
                    is_error=False,
                    structured_content=[value],
                    content=[],
                ),
                tool_name="ck3_take_snapshot",
            )

    def test_runner_preserves_typed_envelope_diagnostic_in_report_path(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("mcp_sequence = error.diagnostic()", source)
        self.assertIn(
            'tool_name="ck3_query_war_termination_terms:first"',
            source,
        )
        self.assertNotIn(
            'raise RuntimeError("official MCP result lacks structured_content")',
            source,
        )


if __name__ == "__main__":
    unittest.main()
