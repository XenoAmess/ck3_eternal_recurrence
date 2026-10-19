"""Owned partition avoids an intermediate copy while retaining public isolation.

Portable repository-only tests use the existing two-title valid fixture. The
paired baseline is the former build function, reconstructed at its one changed
call; a frozen source fingerprint prevents mirroring a changed implementation.
"""
from copy import deepcopy
import ast
import hashlib
import inspect
import json
from pathlib import Path
import sys
import textwrap
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from xar_autoplayer.bridge import turn_bundle_contract as contract
from test_turn_bundle_v1 import _root, _snapshot

BASELINE_SOURCE_SHA256 = "f8a0fdb73208fc5fecbba3bb05bdebbb5248e3e3d0a1e0c6fbd8d75375492acd"


def original_builder():
    source = textwrap.dedent(inspect.getsource(contract.build_turn_bundle_v1))
    new = 'partition = _owned_partition_component(\n            {'
    old = 'partition = _component(\n            "available",\n            {'
    if source.count(new) != 1:
        raise ValueError("owned partition call boundary changed")
    source = source.replace(new, old, 1)
    if hashlib.sha256(source.encode()).hexdigest() != BASELINE_SOURCE_SHA256:
        raise ValueError("original turn-bundle baseline changed")
    tree = ast.parse(source)
    namespace = dict(vars(contract))
    exec(compile(tree, "<former-turn-bundle-builder>", "exec"), namespace)
    return namespace["build_turn_bundle_v1"]


def counted_build(build, snapshot, root):
    # Only call count is evidence; no time or recursive-size benchmark.
    with patch.object(contract.copy, "deepcopy", wraps=deepcopy) as counter:
        result = build(snapshot, root)
        count = counter.call_count
    return result, count


class OwnedPartitionTests(unittest.TestCase):
    def test_public_dto_equal_with_exactly_one_less_copy_on_existing_fixture(self):
        snapshot, root = _snapshot(), _root()
        untouched = deepcopy((snapshot, root))
        old, old_calls = counted_build(original_builder(), snapshot, root)
        new, new_calls = counted_build(contract.build_turn_bundle_v1, snapshot, root)
        self.assertEqual(new, old)
        self.assertEqual(json.dumps(new, ensure_ascii=False, separators=(",", ":")),
                         json.dumps(old, ensure_ascii=False, separators=(",", ":")))
        self.assertEqual(old_calls - new_calls, 1)
        self.assertEqual((snapshot, root), untouched)

    def test_input_output_and_partition_branches_remain_independently_mutable(self):
        for build in (original_builder(), contract.build_turn_bundle_v1):
            with self.subTest(builder=build.__code__.co_filename):
                snapshot, root = _snapshot(), _root()
                result = build(snapshot, root)
                partition = result["succession_state"]["value"]["partition"]["value"]
                source_row = root["campaign_root_context"]["held_title_partition"][1]
                title_row = partition["title_heirs"][1]
                other_row = partition["titles_to_other_heirs"][0]
                self.assertIsNot(title_row, source_row)
                self.assertIsNot(other_row, source_row)
                self.assertIsNot(title_row, other_row)
                self.assertIsNot(title_row["title"], other_row["title"])
                title_row["title"]["title_id"] = 8001
                self.assertEqual(other_row["title"]["title_id"], 91)
                self.assertEqual(source_row["title"]["title_id"], 91)
                source_row["title"]["title_id"] = 8002
                self.assertEqual(other_row["title"]["title_id"], 91)
                self.assertEqual(title_row["title"]["title_id"], 8001)
                other_row["first_heir_character_id"] = 8003
                self.assertEqual(source_row["first_heir_character_id"], 77)
                self.assertEqual(title_row["first_heir_character_id"], 77)
                # Primary title is also exposed by two independent public domains.
                ruler = result["ruler_state"]["value"]["primary_title"]["value"]
                succession = result["succession_state"]["value"]["primary_title"]["value"]
                self.assertIsNot(ruler, succession)
                ruler["title_id"] = 8004
                self.assertEqual(succession["title_id"], 90)
                self.assertEqual(root["campaign_root_context"]["primary_title"]["title_id"], 90)
                # The no-heir mutable branch retains its own title clone too.
                root = _root()
                root["campaign_root_context"]["held_title_partition"][1]["first_heir_character_id"] = None
                bundle = build(_snapshot(), root)
                value = bundle["succession_state"]["value"]["partition"]["value"]
                missing = value["titles_without_heir"][0]
                self.assertIsNot(missing, value["title_heirs"][1]["title"])
                missing["title_id"] = 8005
                self.assertEqual(value["title_heirs"][1]["title"]["title_id"], 91)
                self.assertEqual(root["campaign_root_context"]["held_title_partition"][1]["title"]["title_id"], 91)

    def test_missing_stale_binding_and_unavailable_keep_original_contract(self):
        old = original_builder()
        for change in ("missing", "stale"):
            root = _root()
            if change == "missing":
                root.pop("binding")
            else:
                root["binding"]["native_revision"] += 1
            errors = []
            for build in (old, contract.build_turn_bundle_v1):
                with self.assertRaises(ValueError) as caught:
                    build(_snapshot(), root)
                errors.append((type(caught.exception), str(caught.exception)))
            self.assertEqual(errors[0], errors[1])
        root = _root(available=False)
        previous, old_calls = counted_build(old, _snapshot(), root)
        current, new_calls = counted_build(contract.build_turn_bundle_v1, _snapshot(), root)
        self.assertEqual(current, previous)
        self.assertEqual(old_calls, new_calls)
        self.assertEqual(current["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
