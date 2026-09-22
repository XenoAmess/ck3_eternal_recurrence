from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.vanilla_events import policy  # noqa: E402


def _scope(name: str, type_key: str, character_id: int | None = None) -> dict:
    identity = (
        {"status": "available", "kind": "character", "character_id": character_id}
        if character_id is not None
        else {"status": "unavailable", "reason": "generic_scope_payload_identity_not_closed"}
    )
    return {
        "name": name,
        "scope": {"status": "available", "type_key": type_key, "typed_identity": identity},
    }


def _r0136_context(flag: str = "had_nick_the_drunkard") -> dict:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": "lifestyle_nicknames.1000",
        "current_event_instance_id": 32,
        "date_raw": 53503128,
        "root_scope": _scope("root", "character", 36403)["scope"],
        "saved_scopes": [
            _scope("possible_conqueror", "character", 36403),
            _scope("toggle_null_result", "boolean"),
            _scope("nickname_root_scope", "character", 36403),
            _scope(flag, "boolean"),
            _scope("nickname_getter", "character", 36403),
            _scope("informer", "character", 36567),
        ],
        "options": [{
            "rendered_index": 0,
            "native_option_index": 1,
            "shown": True,
            "enabled": True,
            "fallback": False,
            "cancel": False,
        }],
    }


class LifestyleNicknameConsumerTests(unittest.TestCase):
    def test_r0136_and_legacy_source_generated_flags_select_sole_option(self) -> None:
        for flag in ("had_nick_the_drunkard", "had_nick_the_mad"):
            with self.subTest(flag=flag):
                result = policy.recommend_registered_vanilla_event_option_v1(
                    _r0136_context(flag),
                    played_character_id=36403,
                    snapshot_option_count=6,
                )
                self.assertEqual(result["status"], "recommended", result)
                self.assertEqual(result["selected_option_number"], 2)
                self.assertEqual(result["selected_native_option_index"], 1)
                self.assertEqual(result["failed_checks"], [])

    def test_r0136_material_scope_or_option_drift_blocks(self) -> None:
        variants = []
        wrong_informer = _r0136_context()
        wrong_informer["saved_scopes"][-1] = _scope("informer", "character", 36403)
        variants.append(wrong_informer)
        wrong_boolean = _r0136_context()
        wrong_boolean["saved_scopes"][3] = _scope("had_nick_the_drunkard", "character", 36567)
        variants.append(wrong_boolean)
        extra_scope = _r0136_context()
        extra_scope["saved_scopes"].append(_scope("unexpected", "boolean"))
        variants.append(extra_scope)
        wrong_flag = _r0136_context("other_boolean")
        variants.append(wrong_flag)
        wrong_option = _r0136_context()
        wrong_option["options"][0]["native_option_index"] = 0
        variants.append(wrong_option)
        for context in variants:
            with self.subTest(context=context):
                result = policy.recommend_registered_vanilla_event_option_v1(
                    context, played_character_id=36403, snapshot_option_count=6
                )
                self.assertEqual(result["status"], "blocked", result)

    def test_exact_source_hash_drift_blocks(self) -> None:
        real_query = policy.query_vanilla_event_knowledge_v1

        def changed_source(key: str) -> dict:
            knowledge = copy.deepcopy(real_query(key))
            knowledge["analysis"]["source_sha256"][
                "events/nickname_events/nickname_events.txt"
            ] = "0" * 64
            return knowledge

        with patch.object(policy, "query_vanilla_event_knowledge_v1", changed_source):
            result = policy.recommend_registered_vanilla_event_option_v1(
                _r0136_context(), played_character_id=36403, snapshot_option_count=6
            )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(
            result["unavailable_reason"],
            "registered_nickname_exact_source_or_contract_drift",
        )


if __name__ == "__main__":
    unittest.main()
