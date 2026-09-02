#!/usr/bin/env python3
"""Focused tests for the non-media phase-two authoring ledger validator."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parents[1]
LEDGER_PATH = REPO_ROOT / "mod_zhongguo_style" / "promo" / "phase2-authoring-claims.json"
VALIDATOR_PATH = TOOLS_DIR / "validate_phase2_authoring_claims.py"
sys.path.insert(0, str(TOOLS_DIR))

from validate_phase2_authoring_claims import (  # noqa: E402
    project_cue_input,
    validate_ledger,
)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Phase2AuthoringClaimsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))

    def _validate_mutation(self, payload: dict[str, object]) -> list[str]:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ledger.json"
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            return validate_ledger(path)

    def test_checked_in_ledger_is_green_and_read_only(self) -> None:
        tracked = [
            LEDGER_PATH,
            REPO_ROOT / "mod_zhongguo_style" / "promo" / "phase2-promo-project.json",
            REPO_ROOT / "mod_zhongguo_style" / "promo" / "phase2-brief.md",
            REPO_ROOT / "mod_zhongguo_style" / "promo" / "promo-manifest.json",
            REPO_ROOT
            / "mod_zhongguo_style"
            / "promo"
            / "phase2-readiness-2026-09-02.md",
            REPO_ROOT
            / "docs"
            / "ck3-native-ai"
            / "phase2-producer-identity-live-2026-09-02.md",
        ]
        before = {path: _hash(path) for path in tracked}
        result = subprocess.run(
            [sys.executable, str(VALIDATOR_PATH), "--validate-only"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("VALIDATION: GREEN", result.stdout)
        self.assertIn("media generated: no", result.stdout)
        self.assertEqual(before, {path: _hash(path) for path in tracked})

    def test_rejects_release_overclaim(self) -> None:
        payload = copy.deepcopy(self.ledger)
        payload["chapters"][1]["claim"]["release_status"] = "production-live"
        errors = self._validate_mutation(payload)
        self.assertTrue(any("release status must remain pending" in row for row in errors))

    def test_rejects_source_hash_drift(self) -> None:
        payload = copy.deepcopy(self.ledger)
        payload["source_project"]["sha256"] = "0" * 64
        errors = self._validate_mutation(payload)
        self.assertTrue(any("source project hash drifted" in row for row in errors))

    def test_rejects_noncanonical_span_binding(self) -> None:
        payload = copy.deepcopy(self.ledger)
        payload["chapters"][4]["footage_binding"]["producer_key"] = "fake-span"
        errors = self._validate_mutation(payload)
        self.assertTrue(any("canonical real span" in row for row in errors))

    def test_rejects_subtitle_outside_editorial_safe_width(self) -> None:
        payload = copy.deepcopy(self.ledger)
        payload["chapters"][0]["cue"]["subtitle_zh_cn_lines"] = ["长" * 25]
        payload["chapters"][0]["cue"]["narration_zh_cn"] = "长" * 25
        errors = self._validate_mutation(payload)
        self.assertTrue(any("editorial safe width" in row for row in errors))

    def test_rejects_language_policy_drift(self) -> None:
        payload = copy.deepcopy(self.ledger)
        payload["language_policy"]["primary_narration"] = "en"
        errors = self._validate_mutation(payload)
        self.assertTrue(any("language policy" in row for row in errors))

    def test_project_cue_projection_preserves_semantic_newlines(self) -> None:
        cue = self.ledger["chapters"][1]["cue"]
        projected = project_cue_input(cue)
        self.assertEqual(set(projected), {"id", "narration", "subtitles"})
        self.assertEqual(projected["id"], "p2-zh-02-fact-quota")
        self.assertEqual(projected["narration"], {"zh-CN": cue["narration_zh_cn"]})
        self.assertEqual(
            projected["subtitles"]["zh-CN"],
            "\n".join(cue["subtitle_zh_cn_lines"]),
        )
        self.assertEqual(
            projected["subtitles"]["en"],
            "\n".join(cue["subtitle_en_lines"]),
        )

    def test_rejects_missing_visible_claim_observations(self) -> None:
        payload = copy.deepcopy(self.ledger)
        del payload["chapters"][2]["claim"]["required_visible_observations"]
        errors = self._validate_mutation(payload)
        self.assertTrue(any("explicit visible observations" in row for row in errors))

    def test_rejects_nonsemantic_editorial_break(self) -> None:
        payload = copy.deepcopy(self.ledger)
        cue = payload["chapters"][0]["cue"]
        cue["subtitle_en_lines"] = ["This line has no boundary", "Second line."]
        errors = self._validate_mutation(payload)
        self.assertTrue(any("sentence or clause boundary" in row for row in errors))

    def test_rejects_readiness_overclaim(self) -> None:
        payload = copy.deepcopy(self.ledger)
        payload["readiness_review"][
            "lineage_bound_phase2_clean_spans_verified"
        ] = 8
        errors = self._validate_mutation(payload)
        self.assertTrue(any("zero-footage RED terminal" in row for row in errors))

    def test_rejects_generated_finale_completion_overclaim(self) -> None:
        payload = copy.deepcopy(self.ledger)
        payload["chapters"][-1]["generated_card_title"]["en"] = (
            "ORGANIZATIONAL CAPABILITY COMPLETE"
        )
        errors = self._validate_mutation(payload)
        self.assertTrue(any("overclaims completion" in row for row in errors))


if __name__ == "__main__":
    unittest.main()
