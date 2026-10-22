"""Authored producer/file/consumer regression; no local CK3 paths or AI credit."""
from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
import tempfile
import unittest

from acceptance_contract import Object, array, field, object_value, read, write_once
from checkpoint_artifacts import SavedVariable
from npc_saved_observer import HEALTHY_ROLES, INPUTS, InputKind, NpcInitialBaseline, NpcSavedObservation, SavedInventory, observe_npc_saved, parse_saved_inventory
from prepare_npc_fixture import NpcFixtureSpec, Role


@dataclass(frozen=True)
class AuthoredItem:
    role: Role
    kind: InputKind
    identity: str
    owner: str


OWNERS: dict[Role, str] = {"landed": "100", "baron": "101", "courtier": "102"}
ITEMS = tuple(AuthoredItem(role, kind, str(1000 + role_index * 10 + kind_index), OWNERS[role])
    for role_index, role in enumerate(HEALTHY_ROLES) for kind_index, kind in enumerate(INPUTS))


def variable(name: str, kind: str, identity: str | None = None, *, flag: str | None = None) -> str:
    data = "type=" + kind + (" identity=" + identity if identity is not None else "")
    if flag is not None:
        data += ' flag="' + flag + '"'
    return '{ flag="' + name + '" data={ ' + data + ' } }'


def input_name(kind: InputKind) -> str:
    return "xalw_npc_fixture_target" if kind == "target" else "xalw_npc_fixture_material_" + kind


def authored_save(*, items: tuple[AuthoredItem, ...] = ITEMS, missing_owner: tuple[Role, ...] = (),
                  missing_marker: tuple[Role, ...] = (), missing_actor: tuple[Role, ...] = (),
                  missing_inventory: tuple[Role, ...] = (), missing_reference: tuple[tuple[Role, InputKind], ...] = (),
                  unresolved_reference: tuple[tuple[Role, InputKind], ...] = (), equipped: bool = False,
                  date: str = "1066.9.15") -> str:
    """Fixture input refs remain fixed even when a post-state item is absent."""
    player_values = [variable("xalw_npc_fixture_owner_" + role, "character", OWNERS[role])
        for role in HEALTHY_ROLES if role not in missing_owner]
    player_values.extend(variable("xalw_npc_fixture_missing_" + role, "boolean", "1") for role in missing_marker)
    living = '\t91={\n\t\talive_data={\n\t\t\tvariables={ data={ ' + " ".join(player_values) + ' } }\n\t\t}\n\t}\n'
    for role in HEALTHY_ROLES:
        if role in missing_actor:
            continue
        values: list[str] = []
        for item in ITEMS:
            if item.role != role or (role, item.kind) in missing_reference:
                continue
            values.append(variable(input_name(item.kind), "artifact", None if (role, item.kind) in unresolved_reference else item.identity))
        # A private flag is deliberately unrelated to actual native equipped slots.
        values.append(variable("xalw_imaginary_equipped_flag", "boolean", "1"))
        native_inventory = ""
        if role not in missing_inventory:
            owned = [item.identity for item in items if item.owner == OWNERS[role]]
            slots = f' equipped={{ weapon={next(item.identity for item in items if item.role == role and item.kind == "target")} }}' if equipped else ""
            native_inventory = '\t\t\tinventory={ owner=' + OWNERS[role] + slots + ' artifacts={ ' + " ".join(owned) + ' } }\n'
        living += '\t' + OWNERS[role] + '={\n\t\talive_data={\n\t\t\tvariables={ data={ ' + " ".join(values) + ' } }\n' + native_inventory + '\t\t}\n\t}\n'
    artifact_records = ""
    for item in items:
        rarity = "illustrious" if item.kind == "target" else item.kind
        artifact_records += '\t\t' + item.identity + '={\n\t\t\tname="Authored ' + item.role + " " + item.kind + '"\n'
        artifact_records += '\t\t\ttype="sword"\n\t\t\trarity=' + rarity + '\n\t\t\towner=' + item.owner + '\n\t\t\tdurability=75\n'
        artifact_records += '\t\t\tvariables={ data={ ' + variable("xalw_level", "value", "100000") + ' } }\n\t\t}\n'
    return "date=" + date + "\nliving={\n" + living + "}\nartifacts={\n\tartifacts={\n" + artifact_records + "\t}\n}\n"


def observe(directory: Path, name: str, content: str, *, baseline: NpcInitialBaseline | None = None) -> NpcSavedObservation:
    path = directory / name
    path.write_text(content, encoding="utf-8")
    return observe_npc_saved(path, player_id="91", machine_id="authored-unit-machine", spec=NpcFixtureSpec(0),
        phase="initial" if baseline is None else "post", baseline=baseline)


class NativeSavedInventoryTests(unittest.TestCase):
    def test_absent_empty_present_and_missing_are_distinct_and_ignore_private_flags(self) -> None:
        examples = (
            ('{ alive_data={ variables={ data={ ' + variable("xalw_is_equipped", "boolean", "1") + ' } } inventory={ owner=100 artifacts={ 1000 } } } }', "equipped_absent", ()),
            ('{ alive_data={ inventory={ owner=100 artifacts={ 1000 } equipped={ } } } }', "equipped_empty", ()),
            ('{ alive_data={ inventory={ owner=100 artifacts={ 1000 } equipped={ weapon=1000 } } } }', "equipped_present", ("weapon",)),
            ('{ alive_data={ } }', "missing", None),
        )
        for source, status, slots in examples:
            with self.subTest(status=status):
                actual = parse_saved_inventory("100", source)
                self.assertEqual(actual.status, status)
                self.assertEqual(actual.slots_for("1000"), slots)
                self.assertEqual(SavedInventory.parse(json.loads(json.dumps(actual.to_json()))), actual)

    def test_inventory_requires_owner_list_unique_keys_and_bidirectional_slot_membership(self) -> None:
        invalid = (
            '{ alive_data={ inventory={ artifacts={ 1000 } } } }',
            '{ alive_data={ inventory={ owner=100 } } }',
            '{ alive_data={ inventory={ owner=101 artifacts={ 1000 } } } }',
            '{ alive_data={ inventory={ owner=100 artifacts={ 1000 1000 } } } }',
            '{ alive_data={ inventory={ owner=100 artifacts={ 1000 } equipped={ weapon=1001 } } } }',
            '{ alive_data={ inventory={ owner=100 artifacts={ 1000 } equipped={ weapon=1000 weapon=1000 } } } }',
            '{ alive_data={ inventory={ owner=100 artifacts={ 1000 } equipped={ weapon=1000 armor=1000 } } } }',
            '{ alive_data={ inventory={ owner=100 artifacts={ 1000 } equipped={ 1000 } } } }',
            '{ alive_data={ inventory={ owner=100 artifacts={ 1000 } equipped={ } equipped={ } } } }',
            '{ inventory={ owner=100 artifacts={ 1000 } } }',
        )
        for source in invalid:
            with self.subTest(source=source), self.assertRaises(ValueError):
                parse_saved_inventory("100", source)

    def test_inventory_json_rejects_missing_extra_false_equal_numbers_and_invalid_branches(self) -> None:
        original = parse_saved_inventory("100", '{ alive_data={ inventory={ owner=100 artifacts={ 1000 } } } }').to_json()
        for key in original:
            with self.subTest(missing=key), self.assertRaises(ValueError):
                SavedInventory.parse({name: value for name, value in original.items() if name != key})
        for key, value in (("character_id", 100), ("owner_id", True), ("owned_ids", [1000]),
                ("owned_ids", [1000.0]), ("status", "missing"), ("equipped_slots", [["weapon", "1000"]]), ("extra", True)):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                SavedInventory.parse({**original, key: value})


class NpcSavedObserverTests(unittest.TestCase):
    def test_actual_producer_json_file_consumer_and_baseline_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            produced = observe(root, "initial.ck3", authored_save())
            write_once(root / "saved-observation.json", produced.to_json())
            consumed = NpcSavedObservation.parse(read(root / "saved-observation.json"))
            self.assertEqual(consumed, produced)
            self.assertTrue(consumed.initial_inputs_complete)
            self.assertEqual(tuple(role.role for role in consumed.roles), HEALTHY_ROLES)
            self.assertEqual(tuple(item.kind for item in consumed.roles[0].items), INPUTS)
            self.assertEqual(consumed.roles[0].raw_owner_reference, SavedVariable("character", "100", None))
            self.assertEqual(consumed.roles[0].items[0].raw_reference, SavedVariable("artifact", "1000", None))
            self.assertEqual(consumed.roles[0].items[0].equipped_slots, ())
            self.assertIs(consumed.to_json()["ai_business_pass"], False)
            baseline = NpcInitialBaseline(consumed)
            self.assertEqual(NpcInitialBaseline.parse(json.loads(json.dumps(baseline.to_json()))), baseline)

    def test_post_states_preserve_gone_owner_change_and_missing_or_unresolved_references(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            baseline = NpcInitialBaseline(observe(root, "initial.ck3", authored_save()))
            current_items = tuple(replace(item, owner="999") if item.identity == "1002" else item for item in ITEMS if item.identity != "1001")
            post = observe(root, "post.ck3", authored_save(items=current_items, equipped=True,
                missing_reference=(("landed", "common"),), unresolved_reference=(("landed", "masterwork"),), date="1066.10.1"), baseline=baseline)
            target, gone, changed, _, _ = post.roles[0].items
            self.assertEqual((target.status, target.equipped_slots), ("owned", ("weapon",)))
            self.assertEqual((gone.status, gone.reference_status, gone.artifact_id, gone.artifact), ("gone", "missing", "1001", None))
            self.assertEqual((changed.status, changed.reference_status, changed.artifact_id), ("owner_changed", "unresolved", "1002"))
            self.assertIsNotNone(changed.artifact)
            if changed.artifact is None:
                self.fail("Existing changed-owner artifact was not retained")
            self.assertEqual(changed.artifact.owner_id, "999")
            self.assertIsNone(changed.equipped_slots)
            self.assertFalse(post.initial_inputs_complete)
            self.assertEqual(NpcSavedObservation.parse(json.loads(json.dumps(post.to_json()))), post)
            with self.assertRaises(ValueError):
                NpcInitialBaseline(post)

    def test_candidate_missing_owner_reference_missing_character_missing_and_inventory_missing_differ(self) -> None:
        cases = (
            (authored_save(missing_owner=("landed",), missing_marker=("landed",)), "candidate_missing"),
            (authored_save(missing_owner=("landed",)), "owner_reference_missing"),
            (authored_save(missing_actor=("landed",)), "character_missing"),
            (authored_save(missing_inventory=("landed",)), "inventory_missing"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index, (content, status) in enumerate(cases):
                with self.subTest(status=status):
                    actual = observe(root, f"missing-{index}.ck3", content)
                    self.assertEqual(actual.roles[0].status, status)
                    self.assertFalse(actual.initial_inputs_complete)
                    self.assertEqual(NpcSavedObservation.parse(actual.to_json()), actual)
                    with self.assertRaises(ValueError):
                        NpcInitialBaseline(actual)
            missing_inventory = observe(root, "inventory-again.ck3", authored_save(missing_inventory=("landed",)))
            self.assertTrue(all(item.status == "inventory_missing" and item.equipped_slots is None for item in missing_inventory.roles[0].items))

    def test_initial_inputs_must_all_have_references_records_and_matching_rarity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index, content in enumerate((authored_save(missing_reference=(("landed", "common"),)),
                    authored_save(unresolved_reference=(("landed", "common"),)),
                    authored_save(items=tuple(item for item in ITEMS if item.identity != "1001")))):
                with self.subTest(case=index):
                    observation = observe(root, f"incomplete-{index}.ck3", content)
                    self.assertFalse(observation.initial_inputs_complete)
                    with self.assertRaises(ValueError):
                        NpcInitialBaseline(observation)
            wrong = authored_save().replace("\t\t\trarity=common", "\t\t\trarity=famed", 1)
            with self.assertRaisesRegex(ValueError, "type/rarity"):
                observe(root, "wrong-rarity.ck3", wrong)

    def test_saved_inventory_and_actual_artifact_ownership_require_both_directions(self) -> None:
        base = authored_save()
        bad = (
            base.replace("owner=100 artifacts={ 1000 1001 1002 1003 1004 }", "owner=100 artifacts={ 1000 1002 1003 1004 }", 1),
            base.replace("\t\t\towner=100\n", "\t\t\towner=999\n", 1),
            base.replace("owner=100 artifacts={ 1000 1001 1002 1003 1004 }", "owner=100 artifacts={ 1000 1001 1002 1003 1004 9999 }", 1),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index, content in enumerate(bad):
                with self.subTest(case=index), self.assertRaisesRegex(ValueError, "bidirectionally"):
                    observe(root, f"bad-owner-{index}.ck3", content)

    def test_binding_type_duplicates_changed_post_identity_and_missing_marker_conflicts_are_rejected(self) -> None:
        base = authored_save()
        invalid = (
            base.replace('flag="xalw_npc_fixture_owner_landed" data={ type=character identity=100 }', 'flag="xalw_npc_fixture_owner_landed" data={ type=value identity=100 }'),
            base.replace('flag="xalw_npc_fixture_owner_landed" data={ type=character identity=100 }', 'flag="xalw_npc_fixture_owner_landed" data={ type=character identity=100.0 }'),
            base.replace('flag="xalw_npc_fixture_owner_baron" data={ type=character identity=101 }', 'flag="xalw_npc_fixture_owner_baron" data={ type=character identity=100 }'),
            authored_save(missing_marker=("landed",)),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index, content in enumerate(invalid):
                with self.subTest(case=index), self.assertRaises(ValueError):
                    observe(root, f"bad-binding-{index}.ck3", content)
            baseline = NpcInitialBaseline(observe(root, "initial.ck3", base))
            with self.assertRaisesRegex(ValueError, "binding changed"):
                observe(root, "changed-owner.ck3", base.replace('type=character identity=100', 'type=character identity=999', 1), baseline=baseline)
            with self.assertRaisesRegex(ValueError, "reference changed"):
                observe(root, "changed-item.ck3", base.replace('type=artifact identity=1000', 'type=artifact identity=1001', 1), baseline=baseline)

    def test_decimal_64_bit_item_identity_and_raw_encoding_round_trip_losslessly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = authored_save().replace("1000", "18446744073709551614")
            produced = observe(Path(temporary), "large-id.ck3", source)
            actual = NpcSavedObservation.parse(json.loads(json.dumps(produced.to_json())))
            self.assertEqual(actual.roles[0].items[0].artifact_id, "18446744073709551614")
            self.assertEqual(actual.roles[0].items[0].raw_reference, SavedVariable("artifact", "18446744073709551614", None))

    def test_roles_phase_spec_player_and_source_pin_guards_survive_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initial = observe(root, "initial.ck3", authored_save())
            baseline = NpcInitialBaseline(initial)
            path = root / "other.ck3"
            path.write_text(authored_save(), encoding="utf-8")
            for role in ("fragile", "queue"):
                with self.subTest(role=role):
                    self.assertRaisesRegex(ValueError, "healthy", observe_npc_saved, path,
                        player_id="91", machine_id="authored-unit-machine", spec=NpcFixtureSpec(0), roles=(role,))
            for kwargs in ({"phase": "post"}, {"phase": "initial", "baseline": baseline},
                    {"roles": ["landed"]}, {"roles": ("landed", "landed")}, {"player_id": True}, {"player_id": 91.0}):
                arguments: dict[str, object] = {"player_id": "91", "machine_id": "authored-unit-machine", "spec": NpcFixtureSpec(0), **kwargs}
                with self.subTest(kwargs=kwargs):
                    self.assertRaises(ValueError, observe_npc_saved, path, **arguments)
            with self.assertRaisesRegex(ValueError, "crossed"):
                observe_npc_saved(path, player_id="91", machine_id="other-machine", spec=NpcFixtureSpec(0), phase="post", baseline=baseline)
            path.write_text(authored_save(date="1066.9.14"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "predates"):
                observe_npc_saved(path, player_id="91", machine_id="authored-unit-machine", spec=NpcFixtureSpec(0), phase="post", baseline=baseline)
            (root / "initial.ck3").write_text("changed input", encoding="utf-8")
            with self.assertRaises(ValueError):
                NpcSavedObservation.parse(initial.to_json())

    def test_observation_json_missing_wrong_fields_types_and_forged_credit_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            original = observe(Path(temporary), "initial.ck3", authored_save()).to_json()
            for key in original:
                with self.subTest(missing=key), self.assertRaises(ValueError):
                    NpcSavedObservation.parse({name: value for name, value in original.items() if name != key})
            for key, value in (("schema_version", True), ("schema_version", 1.0), ("player_id", 91),
                    ("initial_inputs_complete", 1), ("initial_inputs_complete", False), ("ai_business_pass", True),
                    ("current_native_observed", 0), ("role_eligibility_independently_observed", True),
                    ("phase", "post"), ("saved_date", "1066.09.15"), ("observed_at_utc", "2026-10-22T11:00:00"), ("extra", True)):
                with self.subTest(key=key), self.assertRaises(ValueError):
                    NpcSavedObservation.parse({**original, key: value})
            changed = object_value(json.loads(json.dumps(original)))
            roles = field(changed, "roles")
            self.assertIsInstance(roles, list)
            if not isinstance(roles, list):
                self.fail("Serialized roles must be list")
            first = object_value(roles[0])
            first["owner_id"] = "999"
            roles[0] = first
            with self.assertRaises(ValueError):
                NpcSavedObservation.parse(changed)

    def test_deep_json_reference_artifact_slot_and_state_contracts_are_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            original = observe(Path(temporary), "initial.ck3", authored_save()).to_json()
            first = object_value(array(field(original, "roles"), "roles")[0])
            first_item = object_value(array(field(first, "items"), "items")[0])
            raw_reference = object_value(field(first_item, "raw_reference"))
            artifact = object_value(field(first_item, "artifact"))
            changes: tuple[tuple[str, object], ...] = (
                ("reference_status", "missing"), ("reference_status", "unknown"),
                ("artifact_id", 1000), ("artifact_id", 1000.0), ("status", "gone"),
                ("status", "consumed_by_ai"), ("equipped_slots", ["weapon"]),
                ("raw_reference", {**raw_reference, "raw_identity_decimal": True}),
                ("raw_reference", {**raw_reference, "raw_identity_decimal": 1000.0}),
                ("raw_reference", {"type": "artifact", "identity": "1000", "flag": None}),
                ("artifact", {**artifact, "owner_id": 100}),
                ("artifact", {**artifact, "durability_decimal": 75.0}),
                ("artifact", {**artifact, "durability_decimal": "75"}),
                ("extra", True),
            )
            variants = [{**first_item, key: value} for key, value in changes]
            variants.extend({key: value for key, value in first_item.items() if key != missing} for missing in first_item)
            for index, replacement in enumerate(variants):
                roles = array(field(original, "roles"), "roles")
                items = array(field(first, "items"), "items")
                items[0] = replacement
                roles[0] = {**first, "items": items}
                with self.subTest(case=index), self.assertRaises(ValueError):
                    NpcSavedObservation.parse({**original, "roles": roles})


if __name__ == "__main__":
    unittest.main()
