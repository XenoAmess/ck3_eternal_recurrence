from __future__ import annotations

import json
import unittest

from xar_autoplayer.bridge.bounded_json_chunks_v1 import (
    MAX_FAST_CHUNK_BYTES, iter_bounded_json_chunks_v1,
)


class BoundedJsonChunksV1Test(unittest.TestCase):
    def test_compact_bytes_preserve_order_scalars_and_nested_aliases(self):
        nested = {"中文": "引号\"与换行\n", "zero": -0.0, "min": -(2**63)}
        cases = [None, [], {}, [None, False, True, 2**64 - 1, 1.25, "🦁"],
                 {"z": [nested, nested], "a": list(range(8193))},
                 {1: "integer key", None: [2, 3]}, (1, {"tuple": (False, 7)}),
                 {"one": [float("inf"), float("nan"), float("-inf")]},
                 {"long": "abc" * 100000}]
        for ascii_only in (False, True):
            for sort in (False, True):
                for value in cases:
                    with self.subTest(ascii=ascii_only, sort=sort, kind=type(value).__name__):
                        encoder = json.JSONEncoder(ensure_ascii=ascii_only, sort_keys=sort, separators=(",", ":"))
                        try:
                            expected = "".join(encoder.iterencode(value))
                        except (TypeError, ValueError) as error:
                            with self.assertRaises(type(error)):
                                "".join(iter_bounded_json_chunks_v1(value, encoder))
                        else:
                            self.assertEqual("".join(iter_bounded_json_chunks_v1(value, encoder)), expected)

    def test_disallowed_float_circular_and_invalid_key_keep_rejection(self):
        circular = []
        circular.append(circular)
        cases = [circular, {("invalid",): 4}, [float("nan")], {"f": float("inf")}]
        encoder = json.JSONEncoder(allow_nan=False, separators=(",", ":"))
        for value in cases:
            with self.subTest(kind=type(value).__name__):
                try:
                    "".join(encoder.iterencode(value))
                except (TypeError, ValueError) as expected:
                    with self.assertRaises(type(expected)) as actual:
                        "".join(iter_bounded_json_chunks_v1(value, encoder))
                    self.assertEqual(str(actual.exception), str(expected))
                else:
                    self.fail("negative fixture unexpectedly encoded")

    def test_fast_group_text_is_bounded_for_flat_scalar_inputs(self):
        for value in (list(range(50000)), ["🦁\n" * 1000] * 500,
                      [{"entry": i, "health": 1.25, "name": "角色"} for i in range(1000)]):
            encoder = json.JSONEncoder(ensure_ascii=False, separators=(",", ":"))
            chunks = list(iter_bounded_json_chunks_v1(value, encoder))
            self.assertLessEqual(max(len(text.encode("utf-8")) for text in chunks), MAX_FAST_CHUNK_BYTES)
            self.assertEqual("".join(chunks), "".join(encoder.iterencode(value)))

    def test_indented_and_custom_separator_paths_keep_original_encoder(self):
        value = {"z": [1, {"a": "中文"}], "n": None}
        for encoder in (json.JSONEncoder(indent=2), json.JSONEncoder(separators=(", ", ": "))):
            self.assertEqual(list(iter_bounded_json_chunks_v1(value, encoder)), list(encoder.iterencode(value)))
