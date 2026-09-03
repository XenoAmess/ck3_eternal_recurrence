from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT.parent / "mod_zhongguo_style" / "common" / "activities" / "activity_types" / "zg361_jingcha.txt"
FIXTURE = ROOT / "native_bridge" / "research" / "fixtures" / "g2_activity_type_schema_boundary_v1.json"


def _strip_comment(line: str) -> str:
    """Remove CK3 comments while preserving # characters inside strings."""

    quoted = False
    escaped = False
    out: list[str] = []
    for char in line:
        if char == '"' and not escaped:
            quoted = not quoted
        if char == "#" and not quoted:
            break
        out.append(char)
        escaped = char == "\\" and not escaped
        if char != "\\":
            escaped = False
    return "".join(out)


def _brace_delta(line: str) -> int:
    quoted = False
    escaped = False
    delta = 0
    for char in line:
        if char == '"' and not escaped:
            quoted = not quoted
        elif not quoted:
            if char == "{":
                delta += 1
            elif char == "}":
                delta -= 1
        escaped = char == "\\" and not escaped
        if char != "\\":
            escaped = False
    return delta


def _top_level_keys(text: str) -> tuple[str, list[str], int]:
    """Return the root key, direct children, and final brace depth.

    This is intentionally a tiny inventory scanner, not a CK3 parser.  It
    records structure for the evidence fixture and never assigns semantics to
    an activity key.
    """

    root: str | None = None
    depth = 0
    keys: list[str] = []
    for raw in text.splitlines():
        line = _strip_comment(raw)
        if not line.strip():
            continue
        if root is None:
            match = re.match(r"^\s*([A-Za-z0-9_.]+)\s*=\s*\{", line)
            if match is None:
                continue
            root = match.group(1)
            depth += _brace_delta(line)
            continue
        if depth == 1:
            match = re.match(r"^\s*([A-Za-z0-9_.]+)\s*=", line)
            if match is not None:
                keys.append(match.group(1))
        depth += _brace_delta(line)
    if root is None:
        raise AssertionError("activity root was not found")
    return root, keys, depth


class G2ActivityTypeSchemaBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.source_bytes = SOURCE.read_bytes()
        cls.source_text = SOURCE.read_text(encoding="utf-8-sig")

    def test_source_hash_bom_and_top_level_inventory_are_frozen(self) -> None:
        source = self.fixture["source"]
        self.assertTrue(self.source_bytes.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(len(self.source_bytes), source["bytes"])
        self.assertEqual(
            hashlib.sha256(self.source_bytes).hexdigest().upper(),
            source["sha256"],
        )
        root, keys, depth = _top_level_keys(self.source_text)
        self.assertEqual(root, source["root_key"])
        self.assertEqual(keys, source["top_level_keys"])
        self.assertEqual(depth, 0)
        self.assertEqual(len(keys), len(set(keys)))

    def test_player_ui_intent_is_recorded_without_overclaiming_runtime_ai(self) -> None:
        source = self.fixture["source"]
        self.assertEqual(source["root_ai_will_do_value"], 0)
        root_block = self.source_text.split("activity_zg361_jingcha = {", 1)[1]
        self.assertRegex(root_block, r"(?ms)^\s*ai_will_do\s*=\s*\{\s*value\s*=\s*0\s*\}")
        self.assertFalse(self.fixture["open_kaishek_boundary"]["native_activity_capability"])

    def test_unknown_activity_surface_remains_fail_closed(self) -> None:
        boundary = self.fixture["open_kaishek_boundary"]
        self.assertEqual(boundary["parser_status"], "GREEN")
        self.assertEqual(boundary["validator_status"], "RED")
        self.assertEqual(boundary["diagnostic_class"], "UNKNOWN_OPCODE")
        self.assertFalse(boundary["activity_schema_bound"])
        self.assertFalse(boundary["allowlist_update_authorized"])
        self.assertFalse(boundary["runtime_certified"])

    def test_no_ck3_or_public_readiness_claim_is_recorded(self) -> None:
        boundaries = self.fixture["boundaries"]
        self.assertEqual(
            boundaries,
            {
                "ck3_started": False,
                "process_attached": False,
                "save_mutated": False,
                "mutation_sent": False,
                "public_abi_changed": False,
                "readiness_promoted": False,
                "activity_action_ready": False,
            },
        )


if __name__ == "__main__":
    unittest.main()
