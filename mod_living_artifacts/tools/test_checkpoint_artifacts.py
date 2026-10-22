"""Offline grammar and persistence-boundary tests, never a native PASS."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from acceptance_contract import json_value
from checkpoint_artifacts import SavedArtifact, inspect_inputs, one, parse_block, variables


class CheckpointArtifactsTests(unittest.TestCase):
    def test_real_saved_variable_encoding_preserves_zero_absence_and_64_bits(self) -> None:
        # The typed-zero form is present in actual R2 saved growth_sequence and
        # pending_xp. Identity strings remain strings, including future64 refs.
        scope = parse_block('{ variables={ data={ { flag="xalw_growth_sequence" data={ type=value } } '
            '{ flag="xalw_fixture_target" data={ type=artifact identity=18446744073709551614 } } } } }')
        result = variables(scope)
        self.assertEqual(result["xalw_growth_sequence"].integer_value("growth"), 0)
        self.assertIsNone(result["xalw_growth_sequence"].raw_identity)
        self.assertNotIn("xalw_pending_xp", result)
        self.assertEqual(result["xalw_fixture_target"].artifact_reference("target"), "18446744073709551614")
        self.assertEqual(json_value(result["xalw_fixture_target"].to_json()), {
            "type": "artifact", "raw_identity_decimal": "18446744073709551614", "flag": None})

    def test_duplicate_wrong_type_fraction_and_malformed_blocks_rejected(self) -> None:
        for value in ('{ x={ }', '{ x={ } } trailing', '{ x= }', '{ x="unterminated }'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_block(value)
        with self.assertRaisesRegex(ValueError, "Nonunique"):
            one(parse_block('{ owner=1 owner=2 }'), "owner")
        for identity in ("true", "1.0", "01"):
            with self.subTest(identity=identity), self.assertRaises(ValueError):
                variables(parse_block('{ variables={ data={ { flag="xalw_xp_in_level" data={ type=value identity=' + identity + ' } } } } }'))
        selected = variables(parse_block('{ variables={ data={ { flag="xalw_level" data={ type=value identity=100001 } } } } }'))
        with self.assertRaisesRegex(ValueError, "Fractional"):
            selected["xalw_level"].integer_value("level")
        with self.assertRaisesRegex(ValueError, "artifact reference"):
            selected["xalw_level"].artifact_reference("level")

    def test_artifact_record_does_not_borrow_nested_owner_or_name(self) -> None:
        raw = '12={ name="Test" type="sword" rarity=common owner=91 durability=74.50000 history={ owner=78 name="Other" } }'
        item = SavedArtifact.parse("12", raw)
        self.assertEqual((item.owner_id, item.name, item.durability_decimal), ("91", "Test", "74.50000"))
        with self.assertRaisesRegex(ValueError, "owner"):
            SavedArtifact.parse("12", raw.replace("owner=91", ""))

    def test_section_path_guards_identically_numbered_non_artifact_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "authored.ck3"
            records = "".join(f'\t\t{index}={{\n\t\t\tname="{name}"\n\t\t\ttype="sword"\n\t\t\trarity={rarity}\n\t\t\towner=91\n\t\t\tdurability=75\n\t\t}}\n'
                for index, name, rarity in ((12, "★Living Artifact Under Test", "masterwork"), (13, "Test Food: Common", "common"),
                    (14, "Test Food: Masterwork", "masterwork"), (15, "Test Food: Famed", "famed"), (16, "Test Food: Illustrious", "illustrious")))
            path.write_text('date=1066.9.15\nliving={\n\t91={\n\t\talive_data={\n\t\t\tvariables={ data={ { flag="xalw_fixture_target" data={ type=artifact identity=12 } } } }\n\t\t}\n\t}\n}\n'
                'other={\n\tartifacts={\n\t\t12={\n\t\t\tname="Wrong"\n\t\t}\n\t}\n}\nartifacts={\n\tartifacts={\n' + records + '\t}\n}\n', encoding="utf-8")
            result = inspect_inputs(path, player_id=91)
            self.assertEqual(result.target_id, "12")
            self.assertEqual(result.date_literal, "1066.9.15")
            self.assertEqual(len(result.artifacts), 5)


if __name__ == "__main__":
    unittest.main()
