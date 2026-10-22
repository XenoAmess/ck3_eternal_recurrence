"""Authored producer/file/consumer regression; no local CK3 paths or AI credit."""
from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
import tempfile
import unittest

from acceptance_contract import Object, array, field, object_value, pin, read, text, write_once
from checkpoint_artifacts import SavedVariable
from npc_saved_observer import HEALTHY_ROLES, INPUTS, InputKind, NpcInitialBaseline, NpcSavedObservation, SavedInventory, initial_owner_lifecycle_issues, observe_npc_saved, parse_saved_inventory, saved_character_reference
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


def r9_excerpt_text() -> str:
    """Retained actual R9 leaf records with explicitly authored outer wrappers."""
    value = read(Path(__file__).with_name("fixtures") / "r9_npc_saved_reference_excerpts.json")
    if value["schema"] != "living-artifacts-r9-saved-reference-excerpts-v1" or value["projection_wrapper_authored"] is not True or value["source_leaf_text_verbatim"] is not True:
        raise ValueError("Actual R9 excerpt provenance differs")
    return text(value["saved_text"], "actual saved R9 reference projection")


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
                  date: str = "1066.9.15", unscheduled_roles: tuple[Role, ...] = ()) -> str:
    """Fixture input refs remain fixed even when a post-state item is absent."""
    player_values = [variable("xalw_npc_fixture_owner_" + role, "char", OWNERS[role])
        for role in HEALTHY_ROLES if role not in missing_owner]
    player_values.extend(variable("xalw_npc_fixture_missing_" + role, "boolean", "1") for role in missing_marker)
    living = '\t91={\n\t\talive_data={\n\t\t\tvariables={ data={ ' + " ".join(player_values) + ' } }\n\t\t}\n\t}\n'
    for role in HEALTHY_ROLES:
        if role in missing_actor:
            continue
        values: list[str] = []
        if role not in unscheduled_roles:
            year, month, _ = (int(part) for part in date.split("."))
            values.extend((variable("xalw_monthly_chain", "boolean", "1"), variable("xalw_last_owner_month", "value", str((year * 12 + month) * 100000))))
            if date == "1066.9.15":
                values.append(variable("xalw_ai_review_queued", "boolean", "1"))
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
    def test_actual_r10_saved_observation_missing_lifecycle_reaches_real_json_consumer(self) -> None:
        fixture = read(Path(__file__).with_name("fixtures") / "r10_npc_initial_lifecycle_observation.json")
        self.assertEqual(fixture["schema"], "living-artifacts-r10-initial-lifecycle-observation-excerpt-v1")
        self.assertIs(fixture["projection_payload_verbatim"], True)
        original = object_value(fixture["observation"])
        with tempfile.TemporaryDirectory() as temporary:
            # The original historical payload/source pin remains in the fixture.
            # Only its file-identity provider is authored for this JSON parser
            # regression; this does not authenticate a raw CK3 save in CI.
            placeholder = Path(temporary) / "authored-file-pin-provider.txt"
            placeholder.write_text("Authored parser boundary; no game-state or native evidence", encoding="utf-8")
            parsed = NpcSavedObservation.parse({**original, "melted_source": pin(placeholder)})
            self.assertEqual(tuple(role.owner_id for role in parsed.roles), ("36893", "45602", "37986"))
            self.assertTrue(parsed.initial_inputs_complete)
            self.assertFalse(parsed.initial_lifecycle_ready)
            self.assertFalse(parsed.to_json()["ai_business_pass"])
            for role in parsed.roles:
                self.assertIn("xalw_npc_fixture_initial_inputs_created", dict(role.saved_variables))
                issues = initial_owner_lifecycle_issues(role, parsed.saved_date)
                self.assertEqual(tuple(issue.split(":", 1)[0] for issue in issues), tuple(text(item, "actual missing field") for item in array(fixture["missing_fields"], "actual missing fields")))
            consumed = NpcSavedObservation.parse(json.loads(json.dumps(parsed.to_json())))
            self.assertEqual(consumed, parsed)
            self.assertFalse(consumed.initial_lifecycle_ready)

    def test_actual_r9_char_reference_records_reach_observer_and_json_consumer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "r9-selected-actual-records.ck3"
            source.write_text(r9_excerpt_text(), encoding="utf-8")
            observed = observe_npc_saved(source, player_id="31254", machine_id="pc-20260924rtuf-f11af23c08", spec=NpcFixtureSpec(0))
            self.assertTrue(observed.initial_inputs_complete)
            self.assertFalse(observed.initial_lifecycle_ready)
            self.assertTrue(all(len(initial_owner_lifecycle_issues(role, observed.saved_date)) == 3 for role in observed.roles))
            self.assertEqual(tuple(role.owner_id for role in observed.roles), ("37243", "46974", "38570"))
            self.assertTrue(all(role.raw_owner_reference is not None and role.raw_owner_reference.kind == "char" for role in observed.roles))
            consumed = NpcSavedObservation.parse(json.loads(json.dumps(observed.to_json())))
            self.assertEqual(consumed, observed)
            self.assertEqual(NpcInitialBaseline(consumed).observation, observed)
            altered = object_value(json.loads(json.dumps(observed.to_json())))
            role = object_value(array(altered["roles"], "roles")[0])
            owner = object_value(role["raw_owner_reference"])
            owner["type"] = "character"
            role["raw_owner_reference"] = owner
            rows = array(altered["roles"], "roles"); rows[0] = role
            altered["roles"] = object_value({"rows": rows})["rows"]
            with self.assertRaisesRegex(ValueError, "Exact saved char"):
                NpcSavedObservation.parse(altered)

    def test_character_decoder_rejects_authored_alias_and_unresolved_or_wrong_type(self) -> None:
        self.assertEqual(saved_character_reference(SavedVariable("char", "37243", None), "R9 landed"), "37243")
        for value in (SavedVariable("character", "37243", None), SavedVariable("artifact", "37243", None),
                SavedVariable("value", "37243", None), SavedVariable("char", None, None), SavedVariable("char", "0", None),
                SavedVariable("char", "37243.0", None), SavedVariable("char", "37243", "unexpected")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                saved_character_reference(value, "actual saved owner")

    def test_initial_lifecycle_is_separate_from_inventory_and_survives_json_without_ai_credit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ready = observe(root, "ready.ck3", authored_save())
            missing = observe(root, "not-started.ck3", authored_save(unscheduled_roles=("landed",)))
            self.assertTrue(ready.initial_inputs_complete and ready.initial_lifecycle_ready)
            self.assertTrue(missing.initial_inputs_complete)
            self.assertFalse(missing.initial_lifecycle_ready)
            self.assertEqual(initial_owner_lifecycle_issues(ready.roles[0], ready.saved_date), ())
            self.assertEqual(len(initial_owner_lifecycle_issues(missing.roles[0], missing.saved_date)), 3)
            for role in missing.roles[1:]:
                self.assertEqual(initial_owner_lifecycle_issues(role, missing.saved_date), ())
            parsed = NpcSavedObservation.parse(json.loads(json.dumps(missing.to_json())))
            self.assertEqual(parsed, missing)
            self.assertFalse(parsed.initial_lifecycle_ready)
            self.assertFalse(parsed.to_json()["ai_business_pass"])
            # This remains an inventory reference baseline, not AI qualification.
            self.assertEqual(NpcInitialBaseline(parsed).observation, missing)

    def test_lifecycle_fields_require_exact_boolean_value_month_and_raw_json_types(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            initial = observe(Path(temporary), "initial.ck3", authored_save())
            role = initial.roles[0]
            for name, value in (("xalw_monthly_chain", SavedVariable("value", "100000", None)),
                    ("xalw_monthly_chain", SavedVariable("boolean", None, None)),
                    ("xalw_ai_review_queued", SavedVariable("boolean", "0", None)),
                    ("xalw_ai_review_queued", SavedVariable("boolean", "1", "unexpected")),
                    ("xalw_last_owner_month", SavedVariable("value", "1280000000", None)),
                    ("xalw_last_owner_month", SavedVariable("value", "1280100001", None)),
                    ("xalw_last_owner_month", SavedVariable("flag", "1280100000", None))):
                altered = dict(role.saved_variables)
                altered[name] = value
                with self.subTest(name=name, value=value):
                    changed = replace(role, saved_variables=tuple(altered.items()))
                    self.assertTrue(any(name in issue for issue in initial_owner_lifecycle_issues(changed, initial.saved_date)))
            original = initial.to_json()
            for raw in (True, 1280100000.0, 1280100000):
                mutated = object_value(json.loads(json.dumps(original)))
                roles = array(mutated["roles"], "roles")
                selected = object_value(roles[0]); values = object_value(selected["saved_variables"])
                values["xalw_last_owner_month"] = {"type": "value", "raw_identity_decimal": raw, "flag": None}
                selected["saved_variables"] = values; roles[0] = selected
                mutated["roles"] = object_value({"roles": roles})["roles"]
                with self.subTest(raw=raw), self.assertRaises(ValueError):
                    NpcSavedObservation.parse(mutated)

    def test_selected_artifact_without_character_owner_is_present_unsupported_not_gone(self) -> None:
        content = authored_save().replace("\t\t\towner=100\n", "\t\t\tholy_site_owner=191\n", 1)
        with tempfile.TemporaryDirectory() as temporary, self.assertRaisesRegex(ValueError, "exists without owner.*not gone"):
            observe(Path(temporary), "selected-ownerless.ck3", content)

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
            self.assertEqual(consumed.roles[0].raw_owner_reference, SavedVariable("char", "100", None))
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
            base.replace('flag="xalw_npc_fixture_owner_landed" data={ type=char identity=100 }', 'flag="xalw_npc_fixture_owner_landed" data={ type=value identity=100 }'),
            base.replace('flag="xalw_npc_fixture_owner_landed" data={ type=char identity=100 }', 'flag="xalw_npc_fixture_owner_landed" data={ type=char identity=100.0 }'),
            base.replace('flag="xalw_npc_fixture_owner_baron" data={ type=char identity=101 }', 'flag="xalw_npc_fixture_owner_baron" data={ type=char identity=100 }'),
            authored_save(missing_marker=("landed",)),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index, content in enumerate(invalid):
                with self.subTest(case=index), self.assertRaises(ValueError):
                    observe(root, f"bad-binding-{index}.ck3", content)
            baseline = NpcInitialBaseline(observe(root, "initial.ck3", base))
            with self.assertRaisesRegex(ValueError, "binding changed"):
                observe(root, "changed-owner.ck3", base.replace('type=char identity=100', 'type=char identity=999', 1), baseline=baseline)
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
