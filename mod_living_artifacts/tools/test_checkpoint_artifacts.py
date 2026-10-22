"""Offline grammar and persistence-boundary tests, never a native PASS."""
from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
import tempfile
import unittest

from acceptance_contract import json_value
from checkpoint_artifacts import SavedArtifact, inspect_inputs, one, parse_block, variables
from living_artifacts_model import FEEDING_XP, Rarity


@dataclass(frozen=True)
class AuthoredArtifact:
    reference: str
    name: str
    rarity: str
    owner_id: str = "91"


AUTHORED_ARTIFACTS = (
    AuthoredArtifact("12", "★Living Artifact Under Test", "masterwork"),
    AuthoredArtifact("13", "Test Food: Common", "common"),
    AuthoredArtifact("14", "Test Food: Masterwork", "masterwork"),
    AuthoredArtifact("15", "Test Food: Famed", "famed"),
    AuthoredArtifact("16", "Test Food: Illustrious", "illustrious"),
)


def authored_checkpoint_text(artifacts: tuple[AuthoredArtifact, ...], *, nested_decoy: bool = False) -> str:
    """Render an authored grammar fixture; this is never an actual game save."""
    records = ""
    for item in artifacts:
        values = ""
        if item.reference == "12":
            for key, number in (("level", 1), ("xp_in_level", 92), ("pending_xp", 0),
                                ("growth_sequence", 0), ("last_settled_month", 12801), ("resonance", 20)):
                values += '{ flag="xalw_' + key + '" data={ type=value identity=' + str(number * 100000) + ' } } '
        records += (f'\t\t{item.reference}={{\n\t\t\tname="{item.name}"\n\t\t\ttype="sword"\n'
                    f'\t\t\trarity={item.rarity}\n\t\t\towner={item.owner_id}\n\t\t\tdurability=75\n'
                    f'\t\t\tvariables={{ data={{ {values} }} }}\n\t\t}}\n')
    decoy = 'other={\n\tartifacts={\n\t\t12={\n\t\t\tname="Wrong"\n\t\t}\n\t}\n}\n' if nested_decoy else ""
    return ('date=1066.9.15\nliving={\n\t91={\n\t\talive_data={\n'
            '\t\t\tvariables={ data={ { flag="xalw_fixture_target" data={ type=artifact identity=12 } } } }\n'
            '\t\t}\n\t}\n}\n' + decoy + 'artifacts={\n\tartifacts={\n' + records + '\t}\n}\n')


def authored_survivors(rarities: tuple[Rarity, ...]) -> tuple[AuthoredArtifact, ...]:
    return tuple(item for item in AUTHORED_ARTIFACTS if item.reference == "12" or item.rarity in rarities)


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
            path.write_text(authored_checkpoint_text(AUTHORED_ARTIFACTS, nested_decoy=True), encoding="utf-8")
            result = inspect_inputs(path, player_id=91)
            self.assertEqual(result.target_id, "12")
            self.assertEqual(result.date_literal, "1066.9.15")
            self.assertEqual(len(result.artifacts), 5)

    def test_explicit_remaining_roles_after_each_feed_and_json_roundtrip(self) -> None:
        rarities = tuple(FEEDING_XP)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "authored.ck3"
            for consumed_count in range(len(rarities) + 1):
                remaining = rarities[consumed_count:]
                artifacts = authored_survivors(remaining)
                with self.subTest(consumed_count=consumed_count):
                    path.write_text(authored_checkpoint_text(artifacts), encoding="utf-8")
                    result = inspect_inputs(path, player_id=91, expected_material_rarities=remaining)
                    self.assertEqual(result.target_id, "12")
                    self.assertEqual(tuple(item.artifact_id for item in result.artifacts), tuple(item.reference for item in artifacts))
                    self.assertEqual(len(result.artifacts), 5 - consumed_count)
                    self.assertEqual(json_value(json.loads(json.dumps(result.to_json(), ensure_ascii=False))), result.to_json())
                    if consumed_count:
                        with self.assertRaisesRegex(ValueError, "surviving material roles"):
                            inspect_inputs(path, player_id=91)

    def test_declared_consumption_requires_exact_saved_survivors_and_target(self) -> None:
        remaining: tuple[Rarity, ...] = ("masterwork", "famed", "illustrious")
        missing_wrong_material = tuple(item for item in AUTHORED_ARTIFACTS if item.reference != "14")
        absent_target = tuple(item for item in authored_survivors(remaining) if item.reference != "12")
        absent_survivor = tuple(item for item in authored_survivors(remaining) if item.reference != "15")
        cases = (("declared consumed common still exists", AUTHORED_ARTIFACTS),
                 ("masterwork consumed instead of common", missing_wrong_material),
                 ("target disappeared", absent_target), ("surviving famed missing", absent_survivor))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "authored.ck3"
            for label, artifacts in cases:
                with self.subTest(case=label):
                    path.write_text(authored_checkpoint_text(artifacts), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "surviving material roles"):
                        inspect_inputs(path, player_id=91, expected_material_rarities=remaining)

    def test_material_role_must_have_matching_rarity_and_unique_identity(self) -> None:
        wrong_rarity = tuple(replace(item, rarity="famed") if item.reference == "13" else item for item in AUTHORED_ARTIFACTS)
        duplicate_role = (*AUTHORED_ARTIFACTS, replace(AUTHORED_ARTIFACTS[1], reference="17"))
        duplicate_identity = (*AUTHORED_ARTIFACTS, AUTHORED_ARTIFACTS[1])
        cases = (("wrong rarity", wrong_rarity, "material rarity"),
                 ("duplicate role", duplicate_role, "surviving material roles"),
                 ("duplicate identity", duplicate_identity, "surviving material roles"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "authored.ck3"
            for label, artifacts, message in cases:
                with self.subTest(case=label):
                    path.write_text(authored_checkpoint_text(artifacts), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, message):
                        inspect_inputs(path, player_id=91)

    def test_remaining_roles_reject_non_tuple_false_equal_duplicate_and_unknown_values(self) -> None:
        malformed: tuple[object, ...] = (None, True, False, 1, 1.0, "common", ["common"],
            (True,), (False,), (1,), (1.0,), (["common"],), ("common", "common"), ("legendary",), ("Common",), (None,))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "authored.ck3"
            path.write_text(authored_checkpoint_text(AUTHORED_ARTIFACTS), encoding="utf-8")
            for value in malformed:
                with self.subTest(value=value):
                    # unittest's callable boundary intentionally supplies malformed
                    # runtime input without weakening the production signature.
                    self.assertRaisesRegex(ValueError, "Explicit unique native material rarities", inspect_inputs,
                        path, player_id=91, expected_material_rarities=value)


if __name__ == "__main__":
    unittest.main()
