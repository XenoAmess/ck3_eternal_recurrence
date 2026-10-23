"""Negative static-contract checks; actual gameplay requires native acceptance."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch

from product import RUNTIME_FILES, SOURCE, spec
import gen_runtime
import prepare_live_fixture
import validate_static


@dataclass
class NaturalCharacter:
    """Small test state; this is not an emulation of CK3's pregnancy engine."""

    faith: str
    age: int = 18
    alive: bool = True
    consorts: tuple[str, ...] = ()
    concubinist: str | None = None
    pregnant: bool = False
    fertile: bool = True
    variables: dict[str, int] = field(default_factory=dict)
    partner_lists: dict[str, list[str]] = field(default_factory=dict)


class NaturalScriptHarness:
    """Execute the generated simulation's actual AST in its declared subset.

    Unknown effects/triggers raise instead of silently succeeding. This checks
    source ordering and persistent pair state, without claiming native scope or
    engine acceptance. The real experience helper is an observed call boundary.
    """

    def __init__(self, characters: dict[str, NaturalCharacter], year: int = 1066, month: int = 9) -> None:
        self.characters = characters
        self.year = year
        self.month = month
        self.scopes: dict[str, str] = {}
        self.recorded: list[tuple[str, str]] = []
        template_root = SOURCE / "tools/runtime_templates"
        self.definitions: dict[str, tuple[validate_static.EffectAssignment, ...]] = {}
        for name in ("effects", "events", "values"):
            source = (template_root / f"sxad_natural_{name}.txt").read_text(encoding="utf-8-sig")
            for node in validate_static.effect_assignments(source):
                if isinstance(node.value, tuple):
                    self.definitions[node.key] = node.value

    @staticmethod
    def block(node: validate_static.EffectAssignment) -> tuple[validate_static.EffectAssignment, ...]:
        if not isinstance(node.value, tuple):
            raise ValueError(f"Expected block: {node.key}")
        return node.value

    @staticmethod
    def scalar(node: validate_static.EffectAssignment) -> str:
        if not isinstance(node.value, str):
            raise ValueError(f"Expected scalar: {node.key}")
        return node.value

    @staticmethod
    def child(nodes: tuple[validate_static.EffectAssignment, ...], key: str) -> validate_static.EffectAssignment:
        return next(node for node in nodes if node.key == key)

    def resolve(self, reference: str, current: str, partner: str | None) -> str:
        if reference == "this":
            return current
        if reference == "$PARTNER$":
            if partner is None:
                raise ValueError("Missing partner macro")
            return partner
        if reference == "this.concubinist":
            owner = self.characters[current].concubinist
            if owner is None:
                raise ValueError("Character has no concubinist")
            return owner
        if reference.startswith("scope:"):
            return self.scopes[reference[6:]]
        raise ValueError(f"Unsupported scope: {reference}")

    def numeric(self, name: str) -> int:
        if name == "current_year":
            return self.year
        if name == "current_month":
            return self.month
        if name not in self.definitions:
            return int(name)
        result = 0
        for node in self.definitions[name]:
            value = self.numeric(self.scalar(node))
            if node.key == "value":
                result = value
            elif node.key == "multiply":
                result *= value
            elif node.key == "add":
                result += value
            else:
                raise ValueError(f"Unsupported script-value statement: {node.key}")
        return result

    def condition(self, nodes: tuple[validate_static.EffectAssignment, ...], current: str, partner: str | None) -> bool:
        results: list[bool] = []
        character = self.characters[current]
        for node in nodes:
            key = node.key
            if key == "NOT":
                results.append(not self.condition(self.block(node), current, partner))
            elif key.startswith("scope:") or key == "$PARTNER$":
                results.append(self.condition(self.block(node), self.resolve(key, current, partner), partner))
            elif key == "is_alive":
                results.append(character.alive == (self.scalar(node) == "yes"))
            elif key == "age":
                if node.operator != ">=":
                    raise ValueError("Unsupported age operator")
                results.append(character.age >= int(self.scalar(node)))
            elif key == "exists":
                results.append(self.resolve(self.scalar(node), current, partner) in self.characters)
            elif key == "this":
                results.append(current == self.resolve(self.scalar(node), current, partner))
            elif key == "is_concubine":
                results.append(character.concubinist is not None)
            elif key == "has_variable":
                results.append(self.scalar(node) in character.variables)
            elif key.startswith("var:"):
                results.append(character.variables[key[4:]] == self.numeric(self.scalar(node)))
            elif key == "is_target_in_variable_list":
                children = self.block(node)
                name = self.scalar(self.child(children, "name"))
                target = self.resolve(self.scalar(self.child(children, "target")), current, partner)
                results.append(target in character.partner_lists.get(name, []))
            else:
                raise ValueError(f"Unsupported simulation trigger: {key}")
        return all(results)

    def execute(self, nodes: tuple[validate_static.EffectAssignment, ...], current: str, partner: str | None = None) -> None:
        previous_condition = False
        for node in nodes:
            key = node.key
            if key == "if":
                children = self.block(node)
                previous_condition = self.condition(self.block(self.child(children, "limit")), current, partner)
                if previous_condition:
                    self.execute(tuple(child for child in children if child.key != "limit"), current, partner)
            elif key == "else":
                if not previous_condition:
                    self.execute(self.block(node), current, partner)
            elif key in {"save_scope_as", "save_temporary_scope_as"}:
                self.scopes[self.scalar(node)] = current
            elif key.startswith("scope:") or key in {"$PARTNER$", "this.concubinist"}:
                self.execute(self.block(node), self.resolve(key, current, partner), partner)
            elif key in {"every_faith_character", "every_consort"}:
                children = self.block(node)
                candidates = (tuple(identity for identity, character in self.characters.items() if character.faith == current)
                              if key == "every_faith_character" else self.characters[current].consorts)
                predicate = self.block(self.child(children, "limit"))
                for identity in candidates:
                    if self.condition(predicate, identity, partner):
                        self.execute(tuple(child for child in children if child.key != "limit"), identity, partner)
            elif key == "clear_variable_list":
                self.characters[current].partner_lists.pop(self.scalar(node), None)
            elif key == "set_variable":
                children = self.block(node)
                name = self.scalar(self.child(children, "name"))
                self.characters[current].variables[name] = self.numeric(self.scalar(self.child(children, "value")))
            elif key == "add_to_variable_list":
                children = self.block(node)
                name = self.scalar(self.child(children, "name"))
                target = self.resolve(self.scalar(self.child(children, "target")), current, partner)
                self.characters[current].partner_lists.setdefault(name, []).append(target)
            elif key.startswith("sxad_"):
                helper_partner: str | None = partner
                if isinstance(node.value, tuple):
                    helper_partner = self.resolve(self.scalar(self.child(node.value, "PARTNER")), current, partner)
                if key == "sxad_record_pair_effect":
                    if helper_partner is None:
                        raise ValueError("Experience helper is missing its partner")
                    self.recorded.append((current, helper_partner))
                else:
                    self.execute(self.definitions[key], current, helper_partner)
            else:
                raise ValueError(f"Unsupported simulation effect: {key}")

    def pulse(self, faith: str) -> None:
        # A native on_action starts a fresh event context, but retains character
        # variables/lists. No state is carried by an accumulating event list.
        self.scopes.clear()
        immediate = self.block(self.child(self.definitions["sxad_natural.1"], "immediate"))
        self.execute(immediate, faith)


class SupermanNaturalFixtureTests(unittest.TestCase):
    """Verify the real fixture producer and contract, without running CK3."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="sxad-natural-fixture-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.templates = self.source / "tools/natural_fixture"
        shutil.copytree(SOURCE / "tools/natural_fixture", self.templates)

    def prepare(self, output: Path) -> prepare_live_fixture.NaturalFixtureReport:
        with patch.object(prepare_live_fixture, "SOURCE", self.source):
            return prepare_live_fixture.prepare_natural_fixture(output)

    def test_real_emitter_preserves_templates_hashes_and_unrun_receipt(self) -> None:
        output = self.root / "fixture"
        report = self.prepare(output)
        self.assertEqual(report["case_count"], 6)
        self.assertEqual(len(report["expected_pass_markers"]), 7)
        self.assertEqual(len(report["readback_character_references"]), 12)
        self.assertEqual(report["candidate_results"], "not_run")
        self.assertIs(report["ck3_started"], False)
        self.assertEqual(report["maximum_natural_days"], 35)
        self.assertTrue(report["machine_id"])
        self.assertTrue(report["observed_at_utc"])
        self.assertEqual(json.loads((self.root / "fixture.fixture.json").read_text(encoding="utf-8")), report)
        self.assertEqual(len(report["files"]), 8)
        for entry in report["files"]:
            raw = (output / entry["path"]).read_bytes()
            self.assertEqual(entry["size"], len(raw))
            self.assertEqual(entry["sha256"], hashlib.sha256(raw).hexdigest())
            template = self.templates / ("cases.json" if entry["path"] == "_natural_simulation_cells.json" else entry["path"])
            self.assertEqual(raw, template.read_bytes())
            if entry["path"].endswith(".yml"):
                self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))

    def test_real_calendar_and_native_observer_have_distinct_source_paths(self) -> None:
        output = self.root / "fixture"
        report = self.prepare(output)
        event = (output / "events/sxanf_events.txt").read_text(encoding="utf-8-sig")
        on_action = (output / "common/on_action/sxanf_on_actions.txt").read_text(encoding="utf-8-sig")
        effects = (output / "common/scripted_effects/sxanf_effects.txt").read_text(encoding="utf-8-sig")
        self.assertRegex(event, r"id\s*=\s*sxanf\.7\s+months\s*=\s*1")
        self.assertRegex(event, r"id\s*=\s*sxanf\.8\s+days\s*=\s*2")
        self.assertRegex(on_action, r"on_faith_monthly\s*=\s*\{\s*on_actions\s*=\s*\{\s*sxanf_observe_native_monthly")
        self.assertIn('debug_log = "SXANF: NATIVE_FAITH_MONTHLY_OBSERVED"', on_action)
        self.assertNotRegex(validate_static.masked(event + effects), r"\bon_action\s*=\s*on_faith_monthly")
        self.assertIn("id = sxad_natural.1", effects)
        self.assertIn("sxad_simulate_natural_character_effect = yes", event)
        self.assertIn("sxad_simulate_natural_pair_effect = { PARTNER = scope:sxanf_dead_b }", event)
        self.assertRegex(event, r"age\s*=\s*16[^\n]+save_scope_as\s*=\s*sxanf_minor_b")
        self.assertEqual(len(re.findall(r"scope:sxanf_minor_b\s*=\s*\{[^{}]*age\s*<\s*18", event)), 3)
        for marker_value in report["expected_pass_markers"]:
            self.assertIn(f'debug_log = "{marker_value}"', event)
        for reference in report["readback_character_references"]:
            self.assertIn("name = " + reference, event)
        for source in (event, on_action, effects):
            validate_static.effect_assignments(source)

    def test_integer_and_unrun_fields_are_validated_before_writing(self) -> None:
        contract = self.templates / "cases.json"
        original = contract.read_text(encoding="utf-8")
        invalid: tuple[tuple[str, str, str], ...] = (
            ('"case_count": 6', '"case_count": 6.0', "expected six"),
            ('"case_index": 1', '"case_index": true', "invalid natural simulation cell index"),
            ('"case_index": 1', '"case_index": 1.0', "invalid natural simulation cell index"),
            ('"maximum_natural_days": 35', '"maximum_natural_days": 35.0', "calendar bound"),
            ('"result": "not_run"', '"result": "passed"', "may not claim"),
        )
        for index, (before, after, message) in enumerate(invalid):
            with self.subTest(after=after):
                self.assertIn(before, original)
                contract.write_text(original.replace(before, after, 1), encoding="utf-8")
                target = self.root / f"invalid-{index}"
                with self.assertRaisesRegex(ValueError, message):
                    self.prepare(target)
                self.assertFalse(target.exists())
                self.assertFalse((self.root / f"invalid-{index}.fixture.json").exists())

    def test_attempt_protection_and_missing_template_never_overwrite(self) -> None:
        output = self.root / "existing"
        output.mkdir()
        sentinel = output / "evidence.txt"
        sentinel.write_bytes(b"retained evidence")
        with self.assertRaisesRegex(ValueError, "new directory outside product source"):
            self.prepare(output)
        self.assertEqual(sentinel.read_bytes(), b"retained evidence")
        with self.assertRaisesRegex(ValueError, "new directory outside product source"):
            self.prepare(self.source / "generated")
        receipt = self.root / "receipt-only.fixture.json"
        receipt.write_bytes(b"retained receipt")
        with self.assertRaisesRegex(ValueError, "new directory outside product source"):
            self.prepare(self.root / "receipt-only")
        self.assertEqual(receipt.read_bytes(), b"retained receipt")
        (self.templates / "events/sxanf_events.txt").unlink()
        with self.assertRaises(FileNotFoundError):
            self.prepare(self.root / "incomplete")
        self.assertFalse((self.root / "incomplete").exists())


class SupermanNaturalSimulationTests(unittest.TestCase):
    def test_additive_native_monthly_event_has_no_scheduler(self) -> None:
        root = SOURCE / "tools/runtime_templates"
        on_actions = (root / "sxad_natural_on_actions.txt").read_text(encoding="utf-8-sig")
        event = (root / "sxad_natural_events.txt").read_text(encoding="utf-8-sig")
        cleaned_on_actions = validate_static.masked(on_actions)
        self.assertRegex(cleaned_on_actions, r"on_faith_monthly\s*=\s*\{\s*on_actions\s*=\s*\{\s*sxad_natural_monthly_on_action\s*\}\s*\}")
        self.assertRegex(cleaned_on_actions, r"sxad_natural_monthly_on_action\s*=\s*\{\s*events\s*=\s*\{\s*sxad_natural\.1\s*\}\s*\}")
        self.assertRegex(event, r"scope\s*=\s*faith")
        self.assertRegex(event, r"hidden\s*=\s*yes")
        self.assertNotRegex(validate_static.masked(on_actions + event), r"\b(?:trigger_event|on_game_start|on_game_load|cooldown)\b")

    def test_cross_faith_both_directions_reload_and_duplicate_links_count_once(self) -> None:
        first = NaturalCharacter("faith_a", consorts=("second", "second"))
        second = NaturalCharacter("faith_b", consorts=("first",))
        world = NaturalScriptHarness({"first": first, "second": second})
        world.pulse("faith_a")
        world.pulse("faith_b")
        world.pulse("faith_a")
        self.assertEqual(world.recorded, [("first", "second")])
        # Persist only JSON-representable character state, then start a fresh
        # harness as a reload would. Neither reverse faith may add a second act.
        restored: object = json.loads(json.dumps({identity: {"variables": character.variables, "lists": character.partner_lists}
                                                 for identity, character in world.characters.items()}))
        if not isinstance(restored, dict):
            raise ValueError("Saved simulation state must be a JSON object")
        reload_world = NaturalScriptHarness({"first": NaturalCharacter("faith_a", consorts=("second",)),
                                            "second": NaturalCharacter("faith_b", consorts=("first",))})
        for identity, character in reload_world.characters.items():
            # This is a test-only JSON boundary; validate every field instead of
            # relying on json.loads' dynamic return type.
            state = restored[identity]
            if not isinstance(state, dict) or set(state) != {"variables", "lists"}:
                raise ValueError("Saved character fields differ")
            if not isinstance(state["variables"], dict) or not isinstance(state["lists"], dict):
                raise ValueError("Saved variables and lists must be JSON objects")
            for key, value in state["variables"].items():
                if not isinstance(key, str) or type(value) is not int:
                    raise ValueError("Saved variable key/value types differ")
                character.variables[key] = value
            for key, values in state["lists"].items():
                if not isinstance(key, str) or not isinstance(values, list):
                    raise ValueError("Saved partner list types differ")
                for value in values:
                    if not isinstance(value, str):
                        raise ValueError("Saved partner identity must be a string")
                    character.partner_lists.setdefault(key, []).append(value)
        reload_world.pulse("faith_b")
        reload_world.pulse("faith_a")
        self.assertEqual(reload_world.recorded, [])

    def test_month_rollover_resets_both_sides_lazily(self) -> None:
        world = NaturalScriptHarness({"first": NaturalCharacter("a", consorts=("second",)),
                                      "second": NaturalCharacter("b", consorts=("first",))}, year=1066, month=12)
        world.pulse("a")
        world.year, world.month = 1067, 1
        world.pulse("b")
        world.pulse("a")
        self.assertEqual(world.recorded, [("first", "second"), ("second", "first")])
        for character in world.characters.values():
            self.assertEqual(character.variables["sxad_natural_month"], 1067 * 12 + 1)
            self.assertEqual(len(character.partner_lists["sxad_natural_partners"]), 1)

    def test_polygamy_concubinist_same_gender_and_infertility_are_not_excluded(self) -> None:
        # The formal consort graph intentionally carries no sex filter. Both
        # same-gender and mixed-gender graphs take this exact source path.
        world = NaturalScriptHarness({"ruler": NaturalCharacter("a", consorts=("spouse", "concubine"), fertile=False),
                                      "spouse": NaturalCharacter("a", consorts=("ruler",), pregnant=True),
                                      "concubine": NaturalCharacter("b", concubinist="ruler")})
        world.pulse("b")  # Reverse concubine link works without every_consort symmetry.
        world.pulse("a")
        self.assertEqual({frozenset(pair) for pair in world.recorded},
                         {frozenset(("ruler", "spouse")), frozenset(("ruler", "concubine"))})
        self.assertEqual(len(world.recorded), 2)

    def test_both_participants_must_be_alive_and_at_least_eighteen(self) -> None:
        for age, alive in ((17, True), (18, False)):
            for owner_ineligible in (True, False):
                with self.subTest(age=age, alive=alive, owner_ineligible=owner_ineligible):
                    owner = NaturalCharacter("a", consorts=("partner",))
                    partner = NaturalCharacter("b", consorts=("owner",))
                    target = owner if owner_ineligible else partner
                    target.age, target.alive = age, alive
                    world = NaturalScriptHarness({"owner": owner, "partner": partner})
                    world.pulse("a")
                    world.pulse("b")
                    self.assertEqual(world.recorded, [])

    def test_simulation_never_replays_pregnancy_or_vanilla_sex_effects(self) -> None:
        root = SOURCE / "tools/runtime_templates"
        source = "\n".join(path.read_text(encoding="utf-8-sig") for path in root.glob("sxad_natural_*.txt"))
        cleaned = validate_static.masked(source)
        self.assertNotRegex(cleaned, r"\b(?:make_pregnant|had_sex_with_effect|had_sex_with_unknown_effect|fertility|is_female|is_pregnant)\b")
        self.assertEqual(len(re.findall(r"\bsxad_record_pair_effect\s*=", cleaned)), 1)
        for path in root.glob("sxad_natural_*.txt"):
            validate_static.blocks(path.read_text(encoding="utf-8-sig"))


@dataclass
class EncounterState:
    """Observed interception calls in the explicit deterministic script subset."""

    pairs: list[tuple[str, str]] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    scopes: dict[str, str] = field(default_factory=dict)
    pair_calls: int = 0
    unknown_calls: int = 0
    pregnancies: int = 0


class EncounterScriptHarness:
    """Interpret real generated fragments, not CK3's reproductive engine.

    Fixture participants are living adults. The real experience helper's outer
    eligibility/suppression guard is parsed; skill transfer and internal native
    pregnancy effects remain observed boundaries. Unrecognised effects raise.
    """

    def __init__(self) -> None:
        self.state = EncounterState()
        self.helpers = {node.key: NaturalScriptHarness.block(node)
                        for node in validate_static.effect_assignments(gen_runtime.experience_effects())}

    def allowed(self, helper: str) -> bool:
        outer = NaturalScriptHarness.block(NaturalScriptHarness.child(self.helpers[helper], "if"))
        limit = NaturalScriptHarness.block(NaturalScriptHarness.child(outer, "limit"))
        return self.condition(limit)

    def condition(self, nodes: tuple[validate_static.EffectAssignment, ...]) -> bool:
        results: list[bool] = []
        for node in nodes:
            if node.key == "NOT":
                results.append(not self.condition(NaturalScriptHarness.block(node)))
            elif node.key == "exists":
                reference = NaturalScriptHarness.scalar(node)
                if not reference.startswith("scope:"):
                    raise ValueError("Suppression fixture expected named scope")
                results.append(reference[6:] in self.state.scopes)
            elif node.key == "is_alive":
                results.append(NaturalScriptHarness.scalar(node) == "yes")
            elif node.key == "age":
                if node.operator != ">=":
                    raise ValueError("Unsupported eligibility operator")
                results.append(18 >= int(NaturalScriptHarness.scalar(node)))
            else:
                raise ValueError(f"Unsupported encounter condition: {node.key}")
        return all(results)

    def execute(self, source: str, current: str = "root", *, roll_success: bool = True,
                branch_index: int = 0) -> None:
        self.run(validate_static.effect_assignments(source), current,
                 roll_success=roll_success, branch_index=branch_index)

    def run(self, nodes: tuple[validate_static.EffectAssignment, ...], current: str, *,
            roll_success: bool, branch_index: int) -> None:
        for node in nodes:
            key = node.key
            if key == "save_temporary_scope_as":
                self.state.scopes[NaturalScriptHarness.scalar(node)] = current
            elif key == "clear_saved_scope":
                self.state.scopes.pop(NaturalScriptHarness.scalar(node), None)
            elif key == "sxad_record_unknown_effect":
                if self.allowed(key):
                    self.state.unknowns.append(current)
            elif isinstance(node.value, tuple):
                children = node.value
                if key in {"sxad_record_pair_effect", "had_sex_with_effect"}:
                    field_name = "PARTNER" if key == "sxad_record_pair_effect" else "CHARACTER"
                    partner = NaturalScriptHarness.scalar(NaturalScriptHarness.child(children, field_name))
                    if key == "had_sex_with_effect":
                        self.state.pair_calls += 1
                    if self.allowed("sxad_record_pair_effect"):
                        self.state.pairs.append((current, partner))
                elif key == "had_sex_with_unknown_effect":
                    self.state.unknown_calls += 1
                    if self.allowed("sxad_record_unknown_effect"):
                        self.state.unknowns.append(current)
                elif key == "make_pregnant":
                    self.state.pregnancies += 1
                elif key == "random":
                    chance = NaturalScriptHarness.scalar(NaturalScriptHarness.child(children, "chance"))
                    if chance == "100" or (chance != "0" and roll_success):
                        self.run(tuple(child for child in children if child.key != "chance"), current,
                                 roll_success=roll_success, branch_index=branch_index)
                elif key == "random_list":
                    branches = [child for child in children if child.key.isdigit()]
                    self.run(NaturalScriptHarness.block(branches[branch_index]), current,
                             roll_success=roll_success, branch_index=branch_index)
                elif key == "hidden_effect" or key.startswith("scope:"):
                    self.run(children, key if key.startswith("scope:") else current,
                             roll_success=roll_success, branch_index=branch_index)
                elif key in {"show_as_tooltip", "trigger", "limit"}:
                    continue
                else:
                    raise ValueError(f"Unsupported encounter fixture effect: {key}")
            else:
                raise ValueError(f"Unsupported encounter fixture scalar: {key}")


class SupermanEncounterProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.projections = gen_runtime.load_encounter_projections()
        self.by_name = {projection.name: projection for projection in self.projections}
        self.outputs = gen_runtime.encounter_hook_outputs()

    def fragment(self, name: str, anchor_contains: str) -> str:
        projection = self.by_name[name]
        anchor = next(insertion.anchor for insertion in projection.insertions
                      if anchor_contains in insertion.anchor)
        source = self.outputs[projection.output].decode("utf-8-sig")
        start = source.index(anchor)
        end = start + len(anchor)
        if any(insertion.anchor == anchor and insertion.position == "before"
               for insertion in projection.insertions):
            start = source.rindex(gen_runtime.INSERT_BEGIN, 0, start)
        if any(insertion.anchor == anchor and insertion.position == "after"
               for insertion in projection.insertions):
            end = source.index(gen_runtime.INSERT_END, end) + len(gen_runtime.INSERT_END)
        return source[start:end]

    def test_actual_renderer_preserves_all_source_hashes_and_roundtrips(self) -> None:
        raw: object = json.loads((SOURCE / "docs/2026-10-23-script-coverage.json").read_text(encoding="utf-8"))
        audit = SupermanEncounterSchemaTests.object_value(raw)
        hashes = SupermanEncounterSchemaTests.object_value(audit["source_sha256"])
        self.assertEqual(len(self.projections), 9)
        for projection in self.projections:
            with self.subTest(name=projection.name):
                pinned = (gen_runtime.PINNED_ROOT / projection.pinned_file).read_bytes()
                self.assertEqual(hashlib.sha256(pinned).hexdigest(), projection.pinned_sha256)
                self.assertEqual(hashes[projection.source_path], projection.source_sha256)
                rendered = self.outputs[projection.output].decode("utf-8-sig")
                recovered = re.sub(r"(?ms)^\t# SXAD_HOOK_BEGIN\n.*?^\t# SXAD_HOOK_END\n", "", rendered)
                original = gen_runtime.extract_effect(recovered, projection.name)
                self.assertEqual(original.encode("utf-8-sig"), pinned)
                owned = gen_runtime.encounter_owned_code(projection.output, rendered)
                self.assertEqual(owned.count("sxad_record_pair_effect") + owned.count("sxad_record_unknown_effect"),
                                 sum(insertion.text.count("sxad_record_pair_effect") + insertion.text.count("sxad_record_unknown_effect")
                                     for insertion in projection.insertions))

    def test_zero_percent_roll_records_pair_before_failed_draw(self) -> None:
        fragment = self.fragment("learning_medicine.2023", "chance = 50").replace("chance = 50", "chance = 0")
        harness = EncounterScriptHarness()
        harness.execute(fragment)
        self.assertEqual(harness.state.pairs, [("scope:woman", "scope:man")])
        self.assertEqual(harness.state.pair_calls, 0)
        self.assertEqual(harness.state.scopes, {})

    def test_success_draw_keeps_native_sex_without_second_mod_record(self) -> None:
        fragment = self.fragment("learning_medicine.2023", "chance = 50").replace("chance = 50", "chance = 100")
        harness = EncounterScriptHarness()
        harness.execute(fragment)
        self.assertEqual(harness.state.pairs, [("scope:woman", "scope:man")])
        self.assertEqual(harness.state.pair_calls, 1)
        self.assertEqual(harness.state.scopes, {})

    def test_independent_repeated_rolls_and_later_explicit_sex_are_not_throttled(self) -> None:
        fragment = self.fragment("learning_medicine.2023", "chance = 50")
        harness = EncounterScriptHarness()
        harness.execute(fragment + fragment)
        harness.execute("scope:woman = { had_sex_with_effect = { CHARACTER = scope:man PREGNANCY_CHANCE = 0 } }")
        self.assertEqual(harness.state.pairs, [("scope:woman", "scope:man")] * 3)
        self.assertEqual(harness.state.pair_calls, 3)
        self.assertEqual(harness.state.scopes, {})

    def test_pilgrimage_std_effect_runs_and_later_unknown_sex_is_restored(self) -> None:
        fragment = self.fragment("pilgrimage.2101", "had_sex_with_unknown_effect")
        for branch in (0, 1):
            with self.subTest(branch=branch):
                harness = EncounterScriptHarness()
                harness.execute("had_sex_with_effect = { CHARACTER = scope:naked_tempter PREGNANCY_CHANCE = 0 }")
                harness.execute(fragment, branch_index=branch)
                self.assertEqual(harness.state.pairs, [("root", "scope:naked_tempter")])
                self.assertEqual(harness.state.unknowns, [])
                self.assertEqual(harness.state.unknown_calls, 1)
                self.assertEqual(harness.state.scopes, {})
                harness.execute("had_sex_with_unknown_effect = { GENDER = female }")
                self.assertEqual(harness.state.unknowns, ["root"])

    def test_previews_never_record_or_leave_temporary_markers(self) -> None:
        harness = EncounterScriptHarness()
        harness.execute("show_as_tooltip = {\n" + self.fragment("learning_medicine.2023", "chance = 50") + "}")
        self.assertEqual(harness.state, EncounterState())

    def test_selected_twins_branch_records_one_encounter(self) -> None:
        harness = EncounterScriptHarness()
        harness.execute(self.fragment("learning_medicine.2023", "number_of_children = 2"), current="scope:woman")
        self.assertEqual(harness.state.pairs, [("scope:woman", "scope:man")])
        self.assertEqual(harness.state.pregnancies, 1)

    def test_adventurer_all_lover_branches_share_one_ungated_pair_record(self) -> None:
        projection = self.by_name["fund_inspiration.6513"]
        rendered = self.outputs[projection.output].decode("utf-8-sig")
        definition = NaturalScriptHarness.block(validate_static.effect_assignments(
            gen_runtime.extract_effect(rendered, projection.name))[0])
        immediate = NaturalScriptHarness.block(NaturalScriptHarness.child(definition, "immediate"))
        candidates = [node for node in immediate if node.key == "scope:inspiration_owner"
                      and isinstance(node.value, tuple)
                      and any(child.key == "set_random_lover_reason" for child in node.value)]
        self.assertEqual(len(candidates), 1)
        common = NaturalScriptHarness.block(candidates[0])
        relation_index = next(index for index, node in enumerate(common)
                              if node.key == "set_random_lover_reason")
        # The actual generated record is a direct child of the common actor
        # block, after the pregnancy/other-lover branches have converged. No
        # sex, fertility or pregnancy predicate gates this encounter capture.
        preceding = common[relation_index - 1]
        self.assertEqual(preceding.key, "hidden_effect")
        self.assertEqual(NaturalScriptHarness.block(preceding)[0].key, "sxad_record_pair_effect")
        owned = gen_runtime.encounter_owned_code(projection.output, rendered)
        self.assertEqual(owned.count("sxad_record_pair_effect"), 1)
        self.assertNotIn("make_pregnant", owned)
        self.assertNotIn("is_female", owned)
        self.assertNotIn("can_have_children", owned)
        # Pregnancy and nonpregnancy paths both reach that same single record;
        # an independently repeated episode still records a second encounter.
        for pregnant in (False, True):
            with self.subTest(pregnant=pregnant):
                harness = EncounterScriptHarness()
                if pregnant:
                    harness.execute("make_pregnant = { father = scope:inspiration_owner }",
                                    current="scope:adventurer_lover")
                harness.execute(owned, current="scope:inspiration_owner")
                self.assertEqual(harness.state.pairs,
                                 [("scope:inspiration_owner", "scope:adventurer_lover")])
                self.assertEqual(harness.state.pregnancies, int(pregnant))
                harness.execute(owned, current="scope:inspiration_owner")
                self.assertEqual(len(harness.state.pairs), 2)

    def test_outer_brothel_record_is_before_internal_random(self) -> None:
        projection = self.by_name["rakish_brothel_night_effect"]
        rendered = self.outputs[projection.output].decode("utf-8-sig")
        self.assertLess(rendered.index("sxad_record_unknown_effect = yes"), rendered.index("random_list = {"))
        harness = EncounterScriptHarness()
        harness.execute(gen_runtime.encounter_owned_code(projection.output, rendered), roll_success=False)
        self.assertEqual(harness.state.unknowns, ["root"])

    def test_existing_encounter_results_have_no_second_projection(self) -> None:
        self.assertNotIn("ep3_wedding.0003", self.by_name)
        self.assertNotIn("lover.8102", self.by_name)

    def test_owned_code_rejects_stock_tampering_and_missing_boundary(self) -> None:
        projection = self.by_name["mpo_events_tova.0035"]
        rendered = self.outputs[projection.output].decode("utf-8-sig")
        self.assertIn("add_piety", rendered)
        self.assertNotIn("add_piety", gen_runtime.encounter_owned_code(projection.output, rendered))
        for changed in (rendered.replace("type = character_event", "type = activity_event", 1),
                        rendered.replace(gen_runtime.INSERT_BEGIN, "", 1)):
            with self.subTest(changed=changed[:100]):
                with self.assertRaises(ValueError):
                    gen_runtime.encounter_owned_code(projection.output, changed)

    def test_ledger_guard_still_sees_new_mod_base_attribute_writes(self) -> None:
        projection = self.by_name["mpo_events_tova.0035"]
        source = self.outputs[projection.output].decode("utf-8-sig")
        changed = source.replace(gen_runtime.INSERT_BEGIN, gen_runtime.INSERT_BEGIN + "add_health = 1\n", 1)
        owned = gen_runtime.encounter_owned_code(projection.output, changed)
        self.assertIn("add_health = 1", owned)
        texts = {relative: body.decode("utf-8-sig") for relative, body in gen_runtime.render_outputs().items()
                 if relative.endswith((".txt", ".gui", ".mod"))}
        texts[projection.output] = changed
        self.assertIn(f"base attribute mutation forbidden by ledger contract: {projection.output}",
                      validate_static.ledger_contract(texts)["errors"])


class SupermanEncounterSchemaTests(unittest.TestCase):
    @staticmethod
    def object_value(value: object) -> dict[str, object]:
        if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
            raise ValueError("Test fixture must be a JSON object with string keys")
        return {key: item for key, item in value.items()}

    @staticmethod
    def array_value(value: object) -> list[object]:
        if not isinstance(value, list):
            raise ValueError("Test fixture must be a JSON array")
        return [item for item in value]

    def document(self) -> dict[str, object]:
        raw: object = json.loads(gen_runtime.ENCOUNTER_SOURCES.read_text(encoding="utf-8"))
        return self.object_value(raw)

    def entry(self, document: dict[str, object], index: int = 0) -> dict[str, object]:
        rows = self.array_value(document["projections"])
        row = self.object_value(rows[index])
        rows[index] = row
        document["projections"] = rows
        return row

    def insertion(self, document: dict[str, object]) -> dict[str, object]:
        entry = self.entry(document)
        rows = self.array_value(entry["insertions"])
        row = self.object_value(rows[0])
        rows[0] = row
        entry["insertions"] = rows
        return row

    def reject(self, document: dict[str, object]) -> None:
        with tempfile.TemporaryDirectory(prefix="sxad-encounter-schema-") as temporary:
            path = Path(temporary) / "manifest.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(ValueError):
                gen_runtime.load_encounter_projections(path)

    def test_unknown_and_missing_fields_at_every_json_boundary_are_rejected(self) -> None:
        for level in ("document", "entry", "insertion"):
            baseline = self.document()
            row = baseline if level == "document" else (self.entry(baseline) if level == "entry" else self.insertion(baseline))
            keys = tuple(row)
            for key in (*keys, "unexpected"):
                with self.subTest(level=level, key=key):
                    document = self.document()
                    row = document if level == "document" else (self.entry(document) if level == "entry" else self.insertion(document))
                    if key == "unexpected":
                        row[key] = "unexpected"
                    else:
                        row.pop(key)
                    self.reject(document)

    def test_counts_reject_booleans_floats_strings_and_other_ordinals(self) -> None:
        for value in (True, False, 1.0, 0, 2, "1", None):
            with self.subTest(value=value, kind=type(value).__name__):
                document = self.document()
                self.insertion(document)["expected_count"] = value
                self.reject(document)

    def test_wrong_types_and_empty_required_values_are_rejected(self) -> None:
        root_cases: tuple[tuple[str, object], ...] = (("projections", {}), ("projections", None),
            ("machine_id", None), ("machine_id", ""), ("source_buildid", 25734779),
            ("source_buildid", True), ("source_buildid", "025734779"), ("source_buildid", "1.0"),
            ("schema", "other"), ("game_version", "1.20.0.3"), ("exe_sha256", "0" * 64))
        for key, value in root_cases:
            with self.subTest(level="document", field=key, value=value):
                document = self.document()
                document[key] = value
                self.reject(document)
        for key, value in (("name", ""), ("name", "illegal\nname"), ("kind", "effect"),
                           ("source_sha256", "F" * 64), ("source_sha256", None),
                           ("pinned_sha256", "abc"), ("insertions", []), ("insertions", {}),
                           ("namespace", "unexpected")):
            with self.subTest(level="entry", field=key, value=value):
                document = self.document()
                self.entry(document)[key] = value
                self.reject(document)
        for key, value in (("position", "replace"), ("anchor", ""), ("text", ""),
                           ("text", "# SXAD_HOOK_BEGIN\n")):
            with self.subTest(level="insertion", field=key, value=value):
                document = self.document()
                self.insertion(document)[key] = value
                self.reject(document)

    def test_event_namespace_must_match_the_event_identifier(self) -> None:
        for value in (None, "other_namespace", 1, "bad.namespace"):
            with self.subTest(namespace=value):
                document = self.document()
                self.entry(document, 2)["namespace"] = value
                self.reject(document)

    def test_noncontained_and_noncanonical_paths_are_rejected(self) -> None:
        cases = (("output", "/events/x.txt"), ("output", "C:/events/x.txt"),
                 ("output", "common/scripted_effects/../x.txt"),
                 ("output", "common//scripted_effects/x.txt"),
                 ("output", "common/scripted_effects/./x.txt"),
                 ("output", "events/x.txt"), ("source_path", "../events/x.txt"),
                 ("source_path", "common\\scripted_effects\\x.txt"),
                 ("pinned_file", "nested/x.txt"), ("pinned_file", "../x.txt"))
        for key, value in cases:
            with self.subTest(field=key, value=value):
                document = self.document()
                self.entry(document)[key] = value
                self.reject(document)

    def test_duplicate_definition_output_or_pinned_source_is_rejected(self) -> None:
        for key in ("name", "output", "pinned_file"):
            with self.subTest(field=key):
                document = self.document()
                first = self.entry(document)
                self.entry(document, 1)[key] = first[key]
                self.reject(document)

    def test_real_renderer_rejects_changed_snapshot_and_definition(self) -> None:
        projection = gen_runtime.load_encounter_projections()[0]
        original = (gen_runtime.PINNED_ROOT / projection.pinned_file).read_bytes()
        with tempfile.TemporaryDirectory(prefix="sxad-encounter-pin-") as temporary:
            pinned_root = Path(temporary)
            target = pinned_root / projection.pinned_file
            target.write_bytes(original + b"\n")
            with patch.object(gen_runtime, "PINNED_ROOT", pinned_root), \
                 patch.object(gen_runtime, "load_encounter_projections", return_value=(projection,)):
                with self.assertRaises(ValueError):
                    gen_runtime.encounter_hook_outputs()
            changed = original + b"\nsecond_definition = {}\n"
            target.write_bytes(changed)
            updated = replace(projection, pinned_sha256=hashlib.sha256(changed).hexdigest())
            with patch.object(gen_runtime, "PINNED_ROOT", pinned_root), \
                 patch.object(gen_runtime, "load_encounter_projections", return_value=(updated,)):
                with self.assertRaises(ValueError):
                    gen_runtime.encounter_hook_outputs()

    def test_real_renderer_rejects_missing_ambiguous_and_overlapping_anchors(self) -> None:
        projection = gen_runtime.load_encounter_projections()[0]
        insertion = projection.insertions[0]
        variants = ((replace(insertion, anchor="nonexistent anchor"),),
                    (replace(insertion, anchor="{"),), (insertion, insertion))
        for insertions in variants:
            with self.subTest(insertions=insertions):
                changed = replace(projection, insertions=insertions)
                with patch.object(gen_runtime, "load_encounter_projections", return_value=(changed,)):
                    with self.assertRaises(ValueError):
                        gen_runtime.encounter_hook_outputs()


class SupermanStaticContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="sxad-static-contract-")
        self.addCleanup(self.temporary.cleanup)
        self.source = Path(self.temporary.name) / "source"
        shutil.copytree(SOURCE, self.source)
        self.product = replace(spec(), source=self.source)

    def validate(self):
        with patch.object(validate_static, "SOURCE", self.source), patch.object(validate_static, "spec", return_value=self.product):
            return validate_static.validate()

    def append(self, relative: str, content: str) -> None:
        path = self.source / relative
        source = path.read_text(encoding="utf-8-sig")
        path.write_text(source + content, encoding="utf-8-sig", newline="\n")

    def test_reviewed_source_is_green(self) -> None:
        report = self.validate()
        self.assertEqual(report["errors"], [])
        self.assertFalse(report["ck3_started"])

    def test_changed_generated_runtime_is_red(self) -> None:
        relative = "common/scripted_effects/sxad_experience_effects.txt"
        self.append(relative, "\n# manually changed generated output\n")
        self.assertIn(f"generated byte parity mismatch: {relative}", self.validate()["errors"])

    def test_acceptance_marker_leak_is_red(self) -> None:
        relative = "common/scripted_effects/sxad_experience_effects.txt"
        path = self.source / relative
        original = path.read_bytes()
        for marker in ("sxadt_injected_effect", "sxat_injected_effect"):
            with self.subTest(marker=marker):
                path.write_bytes(original + f"\n{marker} = {{}}\n".encode("utf-8"))
                self.assertIn(f"acceptance marker leaked into runtime: {relative}", self.validate()["errors"])

    def test_scripted_effect_count_over_twenty_is_red(self) -> None:
        relative = "common/scripted_effects/sxad_experience_effects.txt"
        self.append(relative, "\n" + "\n".join(f"sxad_unreviewed_{i}_effect = {{}}" for i in range(21)))
        self.assertTrue(any("scripted-effect definition count exceeds 20" in error for error in self.validate()["errors"]))

    def test_duplicate_and_missing_localization_references_are_red(self) -> None:
        relative = "localization/english/sxad_l_english.yml"
        self.append(relative, '\n sxad_unresolved_reference:0 "$sxad_missing_reference$"\n')
        self.assertTrue(any("missing localization reference english" in error for error in self.validate()["errors"]))
        self.append(relative, ' sxad_unresolved_reference:0 "Duplicate"\n')
        self.assertTrue(any("duplicate localization key" in error for error in self.validate()["errors"]))

    def test_malformed_brace_returns_red_report(self) -> None:
        self.append("common/scripted_effects/sxad_experience_effects.txt", "\n}\n")
        report = self.validate()
        self.assertEqual(report["status"], "RED")
        self.assertTrue(any("unmatched closing brace" in error for error in report["errors"]))

    def test_strings_and_comments_do_not_inflate_top_level_count(self) -> None:
        blocks = validate_static.top_level_blocks('sxad_one = { log = "{quoted}" # {comment}\n nested = {} }\n sxad_two = {}\n')
        self.assertEqual([block.key for block in blocks], ["sxad_one", "sxad_two"])

    def test_ledger_contract_mutations_are_red(self) -> None:
        texts = {relative: (self.source / relative).read_text(encoding="utf-8-sig")
                 for relative in RUNTIME_FILES if Path(relative).suffix in {".txt", ".gui", ".mod"}}
        self.assertEqual(validate_static.ledger_contract(texts)["errors"], [])

        def change_block(relative, key, pattern, replacement):
            source = texts[relative]
            block = next(block for block in validate_static.top_level_blocks(source) if block.key == key)
            body, count = re.subn(pattern, replacement, source[block.start:block.end], count=1)
            self.assertEqual(count, 1, (relative, key, pattern))
            return source[:block.start] + body + source[block.end:]

        cases: list[tuple[str, str, str]] = []
        for skill in validate_static.LEDGER_SKILLS:
            balance = f"sxad_{skill}_balance"
            transfer = f"sxad_transfer_{skill}_effect"
            probe = f"sxad_probe_{skill}_effect"
            cases.extend((
                (skill + "/nonconserved-increment", validate_static.TRANSFER_FILE,
                 change_block(validate_static.TRANSFER_FILE, transfer, r"\badd\s*=\s*1\b", "add = 2")),
                (skill + "/nonconserved-initialization", validate_static.TRANSFER_FILE,
                 change_block(validate_static.TRANSFER_FILE, transfer, r"\bvalue\s*=\s*-1\b", "value = 1")),
                (skill + "/wrong-modifier-point", validate_static.MODIFIER_FILE,
                 change_block(validate_static.MODIFIER_FILE, f"sxad_{skill}_gain_modifier", rf"\b{skill}\s*=\s*1\b", f"{skill} = 2")),
                (skill + "/wrong-loss-scale-sign", validate_static.VALUES_FILE,
                 change_block(validate_static.VALUES_FILE, f"sxad_{skill}_loss_scale", r"\bmultiply\s*=\s*-1\b", "multiply = 1")),
                (skill + "/zero-receiver-excluded", validate_static.PROBE_FILE,
                 change_block(validate_static.PROBE_FILE, probe, r"\blimit\s*=\s*\{", f"limit = {{ {skill} > 0")),
                (skill + "/zero-donor-allowed", validate_static.PROBE_FILE,
                 change_block(validate_static.PROBE_FILE, probe, rf"\b{skill}\s*>\s*0\b", f"{skill} >= 0")),
                (skill + "/receiver-saturation-bypassed", validate_static.PROBE_FILE,
                 change_block(validate_static.PROBE_FILE, probe, rf"var:{balance}\s*<\s*1000000\b", f"var:{balance} <= 1000000")),
                (skill + "/donor-saturation-bypassed", validate_static.PROBE_FILE,
                 change_block(validate_static.PROBE_FILE, probe, rf"var:{balance}\s*>\s*-1000000\b", f"var:{balance} >= -1000000")),
            ))
        health_balance = "sxad_health_balance"
        health_transfer = "sxad_transfer_health_effect"
        health_probe = "sxad_probe_health_effect"
        cases.extend((
            ("health/nonconserved-increment", validate_static.TRANSFER_FILE,
             change_block(validate_static.TRANSFER_FILE, health_transfer, r"\badd\s*=\s*0\.00075\b", "add = 0.00076")),
            ("health/nonconserved-initialization", validate_static.TRANSFER_FILE,
             change_block(validate_static.TRANSFER_FILE, health_transfer, r"\bvalue\s*=\s*-0\.00075\b", "value = 0.00075")),
            ("health/wrong-modifier-point", validate_static.MODIFIER_FILE,
             change_block(validate_static.MODIFIER_FILE, "sxad_health_gain_modifier", r"\bhealth\s*=\s*1\b", "health = 2")),
            ("health/wrong-loss-scale-sign", validate_static.VALUES_FILE,
             change_block(validate_static.VALUES_FILE, "sxad_health_loss_scale", r"\bmultiply\s*=\s*-1\b", "multiply = 1")),
            ("health/wrong-total-getter", validate_static.VALUES_FILE,
             change_block(validate_static.VALUES_FILE, "sxad_health_value", r"\bvalue\s*=\s*health\b", "value = 3")),
            ("health/zero-receiver-excluded", validate_static.PROBE_FILE,
             change_block(validate_static.PROBE_FILE, health_probe, r"\blimit\s*=\s*\{", "limit = { health > 0")),
            ("health/donor-floor-lowered", validate_static.PROBE_FILE,
             change_block(validate_static.PROBE_FILE, health_probe, r"\bhealth\s*>=\s*3\.00075\b", "health >= 3.00074")),
            ("health/exact-donor-floor-excluded", validate_static.PROBE_FILE,
             change_block(validate_static.PROBE_FILE, health_probe, r"\bhealth\s*>=\s*3\.00075\b", "health > 3.00075")),
            ("health/receiver-capacity-overflows-by-precision-unit", validate_static.PROBE_FILE,
             change_block(validate_static.PROBE_FILE, health_probe, rf"var:{health_balance}\s*<=\s*999999\.99925\b", f"var:{health_balance} <= 999999.99926")),
            ("health/donor-capacity-overflows-by-precision-unit", validate_static.PROBE_FILE,
             change_block(validate_static.PROBE_FILE, health_probe, rf"var:{health_balance}\s*>=\s*-999999\.99925\b", f"var:{health_balance} >= -999999.99926")),
            ("health/missing-donor-rebuild", validate_static.TRANSFER_FILE,
             change_block(validate_static.TRANSFER_FILE, health_transfer, r"scope:sxad_donor\s*=\s*\{\s*sxad_rebuild_health_modifier_effect\s*=\s*yes\s*\}", "")),
            ("toast/wrong-recipient-icon", "common/character_interactions/sxad_interactions.txt",
             change_block("common/character_interactions/sxad_interactions.txt", "sxad_view_experience_interaction",
                          r"\bleft_icon\s*=\s*scope:recipient\b", "left_icon = scope:actor")),
            ("toast/sent-to-recipient-instead-of-actor", "common/character_interactions/sxad_interactions.txt",
             change_block("common/character_interactions/sxad_interactions.txt", "sxad_view_experience_interaction",
                          r"scope:actor\s*=\s*\{\s*send_interface_toast", "scope:recipient = { send_interface_toast")),
            ("toast/retired-event-dispatch", "common/character_interactions/sxad_interactions.txt",
             change_block("common/character_interactions/sxad_interactions.txt", "sxad_view_experience_interaction",
                          r"\bsend_interface_toast\s*=\s*\{", "trigger_event = sxad.1 send_interface_toast = {")),
            ("toast/native-confirmation-default-restored", "common/character_interactions/sxad_interactions.txt",
             change_block("common/character_interactions/sxad_interactions.txt", "sxad_view_experience_interaction",
                          r"\bneeds_confirmation\s*=\s*\{\s*always\s*=\s*no\s*\}", "")),
            ("toast/native-confirmation-enabled", "common/character_interactions/sxad_interactions.txt",
             change_block("common/character_interactions/sxad_interactions.txt", "sxad_view_experience_interaction",
                          r"\bneeds_confirmation\s*=\s*\{\s*always\s*=\s*no\s*\}", "needs_confirmation = { always = yes }")),
        ))
        for effect in ("add_health", "set_health", "change_health"):
            cases.append(("health/base-write/" + effect, validate_static.PROBE_FILE,
                          texts[validate_static.PROBE_FILE] + f"\n{effect} = 0.00075\n"))
        cases.extend((
            ("base-skill-write", validate_static.PROBE_FILE, texts[validate_static.PROBE_FILE] + "\nadd_diplomacy_skill = 1\n"),
            ("missing-receiver-rebuild", validate_static.TRANSFER_FILE,
             change_block(validate_static.TRANSFER_FILE, "sxad_transfer_diplomacy_effect", r"\bsxad_rebuild_diplomacy_modifier_effect\s*=\s*yes\b", "")),
            ("missing-rebuild-refresh", validate_static.PROBE_FILE,
             change_block(validate_static.PROBE_FILE, "sxad_rebuild_diplomacy_modifier_effect", r"\bforce_character_skill_recalculation\s*=\s*yes\b", "")),
            ("unequal-random-weight", validate_static.TRANSFER_FILE,
             change_block(validate_static.TRANSFER_FILE, "sxad_select_transfer_effect", r"\b1\s*=\s*\{", "2 = {")),
            ("query-ledger-write", "events/sxad_events.txt", texts["events/sxad_events.txt"] + "\nset_variable = { name = sxad_diplomacy_balance value = 1 }\n"),
            ("experience-ceiling-reduced", "common/scripted_effects/sxad_experience_effects.txt",
             texts["common/scripted_effects/sxad_experience_effects.txt"].replace("92233720368547", "100")),
        ))
        for name, relative, changed in cases:
            with self.subTest(contract=name):
                # The independent ledger contract receives the mutated source;
                # generator byte-parity cannot make this negative check pass.
                self.assertTrue(validate_static.ledger_contract({**texts, relative: changed})["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
