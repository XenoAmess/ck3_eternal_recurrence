"""Reject malformed JSON anchors before they can authorize loading a save."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from typing import NotRequired, TypedDict, get_type_hints

from xar_autoplayer.cold_checkpoint_validator import (
    ColdCheckpointAnchorV1,
    validate_cold_start_checkpoint_payload_for_pipe,
)
from xar_autoplayer.bridge.succession_transition_contract import (
    legacy_rogue_one_life_binding_v1,
    normalize_succession_lifecycle_binding_v1,
)
from xar_autoplayer.errors import AgentError


PIPE = "synthetic-cold-type-contract"
DIGEST = "0" * 64


class HistoryRowFixture(TypedDict):
    index: object
    command: str
    ok: bool
    result: dict[str, dict[str, object]]


class PayloadFixture(TypedDict):
    format_version: object
    pipe_name: str
    episode_character_id: object
    episode_run_id: str
    last_checkpoint: dict[str, object]
    command_history: list[HistoryRowFixture]
    succession_lifecycle: NotRequired[object]


def payload() -> PayloadFixture:
    checkpoint = {
        "name": "xar_checkpoint.ck3", "size": 1, "sha256": DIGEST,
        "date_raw": 1, "history_index": 1,
        "episode_character_id": 1, "episode_run_id": "synthetic-actor-1",
    }
    return {
        "format_version": 2, "pipe_name": PIPE,
        "episode_character_id": 1, "episode_run_id": "synthetic-actor-1",
        "last_checkpoint": deepcopy(checkpoint),
        "command_history": [{"index": 1, "command": "save-checkpoint", "ok": True,
                             "result": {"checkpoint": deepcopy(checkpoint)}}],
    }


class ColdCheckpointTypeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        # These paths are never created, read, or launched.
        self.spec = SimpleNamespace(profile_dir=Path("synthetic-unopened-profile"))

    def validate(self, value: object) -> ColdCheckpointAnchorV1:
        with patch.object(Path, "stat", return_value=SimpleNamespace(st_size=1)), patch(
            "xar_autoplayer.native_session._sha256_file", return_value=DIGEST
        ):
            return validate_cold_start_checkpoint_payload_for_pipe(self.spec, PIPE, value)

    def rejected_before_save_io(self, value: object) -> None:
        with patch.object(Path, "stat", side_effect=AssertionError("save stat reached")), patch(
            "xar_autoplayer.native_session._sha256_file",
            side_effect=AssertionError("save hash reached"),
        ), self.assertRaises(AgentError):
            validate_cold_start_checkpoint_payload_for_pipe(self.spec, PIPE, value)

    def test_valid_legacy_anchor_is_preserved_without_mutation(self) -> None:
        value = payload()
        before = deepcopy(value)
        result = self.validate(value)
        self.assertEqual(result["history_index"], 1)
        self.assertIsNone(result["succession_lifecycle"])
        self.assertEqual(value, before)

    def test_native_session_return_annotations_resolve_at_runtime(self) -> None:
        from xar_autoplayer import native_session
        for function in (native_session._validate_cold_start_checkpoint,
                         native_session.validate_cold_start_checkpoint_for_pipe):
            self.assertIs(get_type_hints(function)["return"], ColdCheckpointAnchorV1)

    def test_missing_lifecycle_migrates_but_explicit_top_level_null_is_rejected(self) -> None:
        for mask in range(8):
            with self.subTest(null_slots=mask):
                value = payload()
                slots = [value, value["last_checkpoint"],
                         value["command_history"][0]["result"]["checkpoint"]]
                for index, slot in enumerate(slots):
                    if mask & (1 << index):
                        slot["succession_lifecycle"] = None
                before = deepcopy(value)
                if mask & 1:
                    self.rejected_before_save_io(value)
                else:
                    self.assertIsNone(self.validate(value)["succession_lifecycle"])
                self.assertEqual(value, before)

    def test_numeric_lookalikes_do_not_bind_integer_anchors(self) -> None:
        cases = [
            ("format_version", 2.0), ("actor", True), ("actor", 1.0),
            ("history_index", True), ("history_index", 1.0),
            ("saved_size", True), ("saved_size", 1.0), ("saved_date", True),
            ("saved_date", 1.0), ("checkpoint_actor", True),
            ("checkpoint_actor", 1.0),
        ]
        for field, bad in cases:
            with self.subTest(field=field, bad=bad):
                value = payload()
                checkpoint = value["last_checkpoint"]
                row = value["command_history"][0]
                saved = row["result"]["checkpoint"]
                if field == "actor":
                    value["episode_character_id"] = bad
                elif field == "checkpoint_actor":
                    checkpoint["episode_character_id"] = bad
                elif field == "history_index":
                    row["index"] = bad
                elif field == "saved_size":
                    saved["size"] = bad
                elif field == "saved_date":
                    saved["date_raw"] = bad
                else:
                    value["format_version"] = bad
                self.rejected_before_save_io(value)

    def test_lifecycle_uses_the_resume_consumer_contract_in_all_three_slots(self) -> None:
        binding = legacy_rogue_one_life_binding_v1()
        value = payload()
        slots = [value, value["last_checkpoint"],
                 value["command_history"][0]["result"]["checkpoint"]]
        for slot in slots:
            slot["succession_lifecycle"] = deepcopy(binding)
        before = deepcopy(value)
        self.assertEqual(self.validate(value)["succession_lifecycle"], binding)
        self.assertEqual(value, before)
        for slot_index in range(3):
            for bad in (None, {}, [], {**binding, "lifecycle": []}):
                with self.subTest(slot=slot_index, bad=bad):
                    changed = deepcopy(value)
                    changed_slots = [changed, changed["last_checkpoint"],
                                     changed["command_history"][0]["result"]["checkpoint"]]
                    changed_slots[slot_index]["succession_lifecycle"] = bad
                    self.rejected_before_save_io(changed)
        for slot in slots:
            slot["succession_lifecycle"] = {}
        self.rejected_before_save_io(value)

    def test_lifecycle_non_string_enum_raises_contract_value_error(self) -> None:
        for bad in ([], {}, 1, True):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, "lifecycle"):
                normalize_succession_lifecycle_binding_v1({
                    **legacy_rogue_one_life_binding_v1(), "lifecycle": bad,
                })


if __name__ == "__main__":
    unittest.main()
