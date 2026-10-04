import copy
import unittest
from xar_autoplayer.bridge.white_rendered_text_contract import (
    normalize_white_rendered_text, TEXT_NAMES, SCHEMA, STEP, PROOFS,
)

class WhiteRenderedTextContractTests(unittest.TestCase):
    def setUp(self):
        self.binding = dict(game_pid=19376, native_revision=2, connection_generation=1,
                            played_character_id=31254, date_raw=53144328, episode_run_id="synthetic-text")
        self.raw = dict(schema=SCHEMA, step=STEP, read_only=True, available=True,
                        rendered_text_available=True, selected_down_available=False,
                        **{name: True for name in PROOFS},
                        **{k: v for k, v in self.binding.items() if k != "episode_run_id"},
                        widget_count=506, text_source="actual_CPdxGuiTextbox_GetText_390", unavailable_reason="",
                        fields={name: dict(child_path=f"0/1/{n}", text_utf8='中文\\n"#gold 20#!',
                                           effective_visible=True, enabled=True) for n, name in enumerate(TEXT_NAMES)})

    def test_actual_utf8_markup_preserved(self):
        result = normalize_white_rendered_text(self.raw, self.binding)
        self.assertEqual(result["fields"], self.raw["fields"])
        self.assertIsNot(result["fields"], self.raw["fields"])

    def test_owner_frame_inner_census_and_down_guards(self):
        for key, value in (("date_raw", 53144329), ("tree_complete", False),
                           ("inner_modal_visible", False), ("selected_down_available", True),
                           ("source_abi_pins_verified", False), ("stable_two_pass_text", False)):
            with self.subTest(key=key):
                raw = copy.deepcopy(self.raw); raw[key] = value
                with self.assertRaises(ValueError): normalize_white_rendered_text(raw, self.binding)

    def test_fixed_visible_identity_path_and_utf8_bounds(self):
        for update in ({"child_path": "0/1/1"}, {"effective_visible": False},
                       {"text_utf8": "中" * 683}, {"text_utf8": "\ud800"}, {"text_utf8": "\0"}):
            with self.subTest(update=repr(update)):
                raw = copy.deepcopy(self.raw); raw["fields"][TEXT_NAMES[0]].update(update)
                with self.assertRaises(ValueError): normalize_white_rendered_text(raw, self.binding)

    def test_unknown_controls_refused(self):
        raw = copy.deepcopy(self.raw); raw["fields"]["caller_widget"] = {"text_utf8": "30"}
        with self.assertRaises(ValueError): normalize_white_rendered_text(raw, self.binding)

    def test_unavailable_preserves_null_and_refuses_leaked_values(self):
        raw = copy.deepcopy(self.raw)
        raw.update(available=False, rendered_text_available=False, unavailable_reason="actual_hidden",
                   fields={name: None for name in TEXT_NAMES})
        self.assertFalse(normalize_white_rendered_text(raw, self.binding)["available"])
        raw["fields"][TEXT_NAMES[0]] = self.raw["fields"][TEXT_NAMES[0]]
        with self.assertRaises(ValueError): normalize_white_rendered_text(raw, self.binding)

if __name__ == "__main__":
    unittest.main()
