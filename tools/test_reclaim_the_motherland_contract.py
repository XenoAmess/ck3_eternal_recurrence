"""Deterministic source contracts for the Reclaim the Motherland CK3 mod.

This suite deliberately does not launch CK3.  It parses the small Clausewitz-script
surface needed by the feature and checks the approved gameplay invariants.  The
upstream SHA-256 pins are for CK3 1.19.0.6 (Scribe).
"""

from __future__ import annotations

import codecs
import hashlib
import json
import os
import re
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "mod_reclaim_the_motherland"

RULES = MOD / "common/game_rules/rmtm_game_rules.txt"
RESTORATION_DECISIONS = MOD / "common/decisions/rmtm_restoration_decisions.txt"
MANDATE_OVERRIDE = (
    MOD / "common/decisions/dlc_decisions/tgp/zz_rmtm_mandate_override.txt"
)
CUSTOM_EFFECTS = MOD / "common/scripted_effects/rmtm_dynastic_cycle_effects.txt"
LOYALTY_EFFECTS = MOD / "common/scripted_effects/rmtm_loyalty_resolution_effects.txt"
LOYALTY_TRIGGERS = MOD / "common/scripted_triggers/rmtm_loyalty_triggers.txt"
LOYALTY_VALUES = MOD / "common/script_values/rmtm_loyalty_values.txt"
LOYALTY_EVENTS = MOD / "events/rmtm_loyalty_events.txt"
GENERATED_TITLE_NAMES = (
    MOD / "common/scripted_effects/rmtm_generated_title_name_effects.txt"
)
SCRIPTED_EFFECTS_DIR = MOD / "common/scripted_effects"
RESTORATION_TRIGGERS = MOD / "common/scripted_triggers/rmtm_restoration_triggers.txt"
FIXTURE_EFFECTS = (
    ROOT
    / "tools/fixtures/reclaim_the_motherland_acceptance/common/scripted_effects/rqa_effects.txt"
)

RULE = "rmtm_hegemon_fate"
RECLAIM_SETTING = "rmtm_reclaim_the_motherland"
VANILLA_SETTING = "rmtm_vanilla_shattering"
LOYALTY_RULE = "rmtm_pro_hegemon_choice"
DYNAMIC_LOYALTY_SETTING = "rmtm_divided_hearts"
LEGACY_LOYALTY_SETTING = "rmtm_unwavering_loyalty"
DISPATCH_EFFECT = "tgp_chaos_shattering_effect"
RECLAIM_EFFECT = "rmtm_chaos_shattering_effect"
VANILLA_EFFECT = "rmtm_vanilla_chaos_shattering_effect"
RESTORATION_TRIGGER = "rmtm_holds_restoration_hegemony_trigger"
MARKER = "rmtm_restoration_hegemony"
VANILLA_DECISION = "situation_dynastic_cycle_claim_mandate_decision"
RESTORATION_DECISION = "rmtm_claim_restoration_decision"
MANDATE_PERCENT_VALUE = "claim_mandate_china_county_percentage_value"

VANILLA_DECISION_FILE_SHA256 = (
    "FFC1CE8BC35DDCAFA29956E4DC4159EB295E10E17FD0881CE5DD558671206651"
)
VANILLA_VALUES_FILE_SHA256 = (
    "D91DCDBF7038FAE3D8D71B9C4156B2B23744DE6F718A34DA26D1656BC48B7706"
)
VANILLA_EFFECTS_FILE_SHA256 = (
    "86574FB7CE246EF6D1B2741B211785D282AD39659E8771E0E5C714ACDC001782"
)
# Parsed body digest of tgp_chaos_shattering_effect in the pinned file.
VANILLA_CHAOS_EFFECT_BODY_SHA256 = (
    "98B4ACA0F3E8844D0222C70674F639AF47BF4542A2EC58CCC1F911A84AD6E026"
)
VANILLA_MANDATE_DECISION_BODY_SHA256 = (
    "1D628EBEA1DA3C1217BBFF73CE10CDAAD5E9EACCAAFF0B00DC6FEB23814E819F"
)

VANILLA_RELATIVE_PATHS = {
    "decision": Path("common/decisions/dlc_decisions/tgp/tgp_dynastic_cycle_decisions.txt"),
    "values": Path("common/script_values/10_tgp_dynastic_cycle_values.txt"),
    "effects": Path("common/scripted_effects/10_dlc_tgp_dynastic_cycle_scripted_effects.txt"),
}


@dataclass(frozen=True)
class Entry:
    key: str
    operator: str | None = None
    value: str | "Block" | None = None


@dataclass(frozen=True)
class Block:
    entries: tuple[Entry, ...]


def tokenize_clausewitz(text: str) -> list[str]:
    """Tokenize comments, quoted values, operators and braces without rewriting text."""

    tokens: list[str] = []
    index = 0
    operators = ("?=", ">=", "<=", "!=", "==", "=", ">", "<")
    while index < len(text):
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if char == "#":
            newline = text.find("\n", index)
            index = len(text) if newline == -1 else newline + 1
            continue
        if char in "{}":
            tokens.append(char)
            index += 1
            continue
        if char == '"':
            end = index + 1
            escaped = False
            while end < len(text):
                current = text[end]
                if current == '"' and not escaped:
                    end += 1
                    break
                if current == "\\" and not escaped:
                    escaped = True
                else:
                    escaped = False
                end += 1
            else:
                raise ValueError("unterminated quoted string")
            tokens.append(text[index:end])
            index = end
            continue
        operator = next((candidate for candidate in operators if text.startswith(candidate, index)), None)
        if operator is not None:
            tokens.append(operator)
            index += len(operator)
            continue

        end = index
        while end < len(text):
            if text[end].isspace() or text[end] in '{}#"=<>!':
                break
            if text.startswith("?=", end):
                break
            end += 1
        if end == index:
            raise ValueError(f"unsupported character {text[index]!r} at offset {index}")
        tokens.append(text[index:end])
        index = end
    return tokens


def parse_clausewitz(text: str) -> Block:
    tokens = tokenize_clausewitz(text)
    index = 0
    operators = {"?=", ">=", "<=", "!=", "==", "=", ">", "<"}

    def parse_entries(stop_at_brace: bool) -> Block:
        nonlocal index
        entries: list[Entry] = []
        while index < len(tokens):
            if tokens[index] == "}":
                if not stop_at_brace:
                    raise ValueError("unexpected closing brace")
                index += 1
                return Block(tuple(entries))

            key = tokens[index]
            if key == "{":
                raise ValueError("unexpected opening brace without an assignment")
            index += 1
            if index >= len(tokens) or tokens[index] not in operators:
                entries.append(Entry(key))
                continue

            operator = tokens[index]
            index += 1
            if index >= len(tokens):
                raise ValueError(f"missing value after {key} {operator}")
            if tokens[index] == "{":
                index += 1
                value: str | Block = parse_entries(stop_at_brace=True)
            else:
                if tokens[index] == "}":
                    raise ValueError(f"missing value after {key} {operator}")
                value = tokens[index]
                index += 1
            entries.append(Entry(key, operator, value))

        if stop_at_brace:
            raise ValueError("unterminated block")
        return Block(tuple(entries))

    parsed = parse_entries(stop_at_brace=False)
    if index != len(tokens):
        raise ValueError("parser did not consume all tokens")
    return parsed


def read_script(path: Path) -> tuple[str, Block]:
    if not path.is_file():
        raise AssertionError(f"required script is missing: {path.relative_to(ROOT)}")
    raw = path.read_bytes()
    if not raw.startswith(codecs.BOM_UTF8):
        raise AssertionError(f"CK3 script must use UTF-8 BOM: {path.relative_to(ROOT)}")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise AssertionError(f"invalid UTF-8 in {path.relative_to(ROOT)}: {error}") from error
    return text, parse_clausewitz(text)


def read_script_directory(path: Path) -> list[tuple[Path, str, Block]]:
    files = sorted(path.glob("*.txt"))
    if not files:
        raise AssertionError(f"required script directory is empty: {path.relative_to(ROOT)}")
    return [(file, *read_script(file)) for file in files]


def collection_block(collection: list[tuple[Path, str, Block]], key: str) -> Block:
    matches: list[tuple[Path, Block]] = []
    for path, _, parsed in collection:
        for entry in direct_entries(parsed, key):
            if isinstance(entry.value, Block):
                matches.append((path, entry.value))
    if len(matches) != 1:
        locations = ", ".join(str(path.relative_to(ROOT)) for path, _ in matches)
        raise AssertionError(f"expected exactly one top-level {key!r}; found {len(matches)} in {locations}")
    return matches[0][1]


def direct_entries(block: Block, key: str) -> list[Entry]:
    return [entry for entry in block.entries if entry.key == key]


def direct_block(block: Block, key: str) -> Block:
    matches = [entry.value for entry in direct_entries(block, key) if isinstance(entry.value, Block)]
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one direct block {key!r}, found {len(matches)}")
    return matches[0]


def descendants(block: Block) -> Iterator[Entry]:
    for entry in block.entries:
        yield entry
        if isinstance(entry.value, Block):
            yield from descendants(entry.value)


def descendant_blocks(block: Block, key: str) -> list[Block]:
    return [entry.value for entry in descendants(block) if entry.key == key and isinstance(entry.value, Block)]


def scalar_values(block: Block, key: str, *, recursive: bool = True) -> list[str]:
    entries = descendants(block) if recursive else iter(block.entries)
    return [entry.value for entry in entries if entry.key == key and isinstance(entry.value, str)]


def flattened_tokens(block: Block) -> list[str]:
    result: list[str] = []
    for entry in descendants(block):
        result.append(entry.key)
        if entry.operator is not None:
            result.append(entry.operator)
        if isinstance(entry.value, str):
            result.append(entry.value)
    return result


def contains_fragment(block: Block, fragment: str) -> bool:
    return any(fragment in token for token in flattened_tokens(block))


def has_assignment(
    block: Block,
    key: str,
    value: str | None = None,
    *,
    operators: set[str] | None = None,
    recursive: bool = True,
) -> bool:
    entries = descendants(block) if recursive else iter(block.entries)
    return any(
        entry.key == key
        and isinstance(entry.value, str)
        and (value is None or entry.value == value)
        and (operators is None or entry.operator in operators)
        for entry in entries
    )


def has_key(block: Block, key: str, *, recursive: bool = True) -> bool:
    entries = descendants(block) if recursive else iter(block.entries)
    return any(entry.key == key for entry in entries)


def denies_trigger(block: Block, trigger: str) -> bool:
    if has_assignment(block, trigger, "no"):
        return True
    return any(
        has_assignment(negated, trigger, "yes")
        for negated in descendant_blocks(block, "NOT")
    )


def excludes_old_emperor(block: Block) -> bool:
    for entry in descendants(block):
        if (
            entry.key == "top_liege"
            and entry.operator == "!="
            and isinstance(entry.value, str)
            and "old_emperor" in entry.value
        ):
            return True
    return any(
        any(
            entry.key == "top_liege"
            and isinstance(entry.value, str)
            and "old_emperor" in entry.value
            for entry in descendants(negated)
        )
        for negated in descendant_blocks(block, "NOT")
    )


def without_approved_restoration_guards(block: Block) -> Block:
    kept: list[Entry] = []
    for entry in block.entries:
        if isinstance(entry.value, Block) and (
            (
                entry.key == "trigger_if"
                and has_assignment(entry.value, "has_game_rule", RECLAIM_SETTING)
                and denies_trigger(entry.value, RESTORATION_TRIGGER)
            )
            or (
                entry.key == "NOT"
                and has_assignment(entry.value, RESTORATION_TRIGGER, "yes")
            )
        ):
            continue
        value = (
            without_approved_restoration_guards(entry.value)
            if isinstance(entry.value, Block)
            else entry.value
        )
        kept.append(Entry(entry.key, entry.operator, value))
    return Block(tuple(kept))


def entry_contains(entry: Entry, *needles: str) -> bool:
    if not isinstance(entry.value, Block):
        return False
    tokens = set(flattened_tokens(entry.value))
    return all(needle in tokens for needle in needles)


def body_digest(block: Block) -> str:
    def serialize(value: str | Block | None) -> object:
        if isinstance(value, Block):
            return [[entry.key, entry.operator, serialize(entry.value)] for entry in value.entries]
        return value

    canonical = json.dumps(serialize(block), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def find_vanilla_game_root() -> Path | None:
    candidates: list[Path] = []
    configured = os.environ.get("RMTM_CK3_GAME_ROOT")
    if configured:
        candidates.append(Path(configured))
    candidates.extend(
        [
            ROOT / "Crusader Kings III/game",
            Path(r"D:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game"),
        ]
    )
    for candidate in candidates:
        if all((candidate / relative).is_file() for relative in VANILLA_RELATIVE_PATHS.values()):
            return candidate
    return None


def block_statement_index(block: Block, predicate) -> int:
    for index, entry in enumerate(block.entries):
        if predicate(entry):
            return index
    raise AssertionError("required ordered statement was not found")


class TestReclaimTheMotherlandContract(unittest.TestCase):
    maxDiff = None

    def test_game_rule_has_exactly_the_two_approved_paths(self) -> None:
        _, parsed = read_script(RULES)
        rule = direct_block(parsed, RULE)
        self.assertEqual(scalar_values(rule, "default", recursive=False), [RECLAIM_SETTING])

        option_blocks = {
            entry.key
            for entry in rule.entries
            if isinstance(entry.value, Block) and entry.key != "categories"
        }
        self.assertEqual(option_blocks, {RECLAIM_SETTING, VANILLA_SETTING})
        self.assertEqual(len(direct_entries(rule, RECLAIM_SETTING)), 1)
        self.assertEqual(len(direct_entries(rule, VANILLA_SETTING)), 1)

        loyalty_rule = direct_block(parsed, LOYALTY_RULE)
        self.assertEqual(
            scalar_values(loyalty_rule, "default", recursive=False),
            [DYNAMIC_LOYALTY_SETTING],
        )
        loyalty_options = {
            entry.key
            for entry in loyalty_rule.entries
            if isinstance(entry.value, Block) and entry.key != "categories"
        }
        self.assertEqual(
            loyalty_options,
            {DYNAMIC_LOYALTY_SETTING, LEGACY_LOYALTY_SETTING},
        )

    def test_live_fixture_samples_only_county_or_higher_direct_vassals(self) -> None:
        text = FIXTURE_EFFECTS.read_text(encoding="utf-8-sig")
        initialization = text.split("rqa_enter_chaos_effect", 1)[0]
        self.assertGreaterEqual(
            initialization.count("highest_held_title_tier >= tier_county"),
            4,
            "fixture actors must match the product's county-or-higher vassal contract",
        )
        chaos_verification = text.split("rqa_verify_chaos_effect", 1)[1].split(
            "rqa_transfer_county_to_control_effect", 1
        )[0]
        self.assertIn(
            "var:rqa_personal_county = { holder = root }",
            chaos_verification,
            "live acceptance must prove the exact pre-Chaos personal county holder",
        )
        self.assertNotIn(
            "holder.top_liege = root",
            chaos_verification,
            "remaining somewhere in the realm is weaker than retaining personal land",
        )

    def test_shattering_dispatcher_routes_custom_and_vanilla_effects(self) -> None:
        effects = read_script_directory(SCRIPTED_EFFECTS_DIR)
        dispatcher = collection_block(effects, DISPATCH_EFFECT)

        reclaim_branches = [
            branch
            for key in ("if", "else_if")
            for branch in descendant_blocks(dispatcher, key)
            if has_assignment(branch, "has_game_rule", RECLAIM_SETTING)
        ]
        self.assertEqual(len(reclaim_branches), 1, "custom setting needs one explicit dispatcher branch")
        self.assertTrue(has_assignment(reclaim_branches[0], RECLAIM_EFFECT, "yes"))

        explicit_vanilla = [
            branch
            for key in ("if", "else_if")
            for branch in descendant_blocks(dispatcher, key)
            if has_assignment(branch, "has_game_rule", VANILLA_SETTING)
            and has_assignment(branch, VANILLA_EFFECT, "yes")
        ]
        fallback_vanilla = [
            branch
            for branch in descendant_blocks(dispatcher, "else")
            if has_assignment(branch, VANILLA_EFFECT, "yes")
        ]
        self.assertEqual(
            len(explicit_vanilla) + len(fallback_vanilla),
            1,
            "vanilla setting must route to the pinned vanilla helper (explicitly or as the only fallback)",
        )

    def test_vanilla_source_files_and_copied_effect_are_pinned(self) -> None:
        mandate_text, _ = read_script(MANDATE_OVERRIDE)
        effects = read_script_directory(SCRIPTED_EFFECTS_DIR)
        effects_text = "\n".join(text for _, text, _ in effects)
        self.assertIn(VANILLA_DECISION_FILE_SHA256, mandate_text.upper())
        self.assertIn(VANILLA_VALUES_FILE_SHA256, mandate_text.upper())
        self.assertIn(VANILLA_EFFECTS_FILE_SHA256, effects_text.upper())

        vanilla_copy = collection_block(effects, VANILLA_EFFECT)
        self.assertEqual(
            body_digest(vanilla_copy),
            VANILLA_CHAOS_EFFECT_BODY_SHA256,
            "the vanilla rule path must remain an exact parsed copy of the pinned upstream effect body",
        )

        mandate = direct_block(parse_clausewitz(mandate_text), VANILLA_DECISION)
        self.assertEqual(
            body_digest(without_approved_restoration_guards(mandate)),
            VANILLA_MANDATE_DECISION_BODY_SHA256,
            "apart from conditional restoration guards, the override must match the pinned vanilla decision",
        )
        mandate_effect = direct_block(mandate, "effect")
        flag_index = block_statement_index(
            mandate_effect,
            lambda entry: entry.key == "add_character_flag"
            and entry_contains(entry, "claimed_the_mandate_of_heaven", "days", "3"),
        )
        gok_index = block_statement_index(
            mandate_effect,
            lambda entry: entry.key == "gok_government_change_story_end_effect"
            and entry.value == "yes",
        )
        situation_index = block_statement_index(
            mandate_effect,
            lambda entry: entry.key == "situation:dynastic_cycle"
            and entry_contains(entry, "save_scope_as", "situation"),
        )
        mandate_index = block_statement_index(
            mandate_effect,
            lambda entry: entry.key == "tgp_claim_mandate_of_heaven_effect"
            and entry.value == "yes",
        )
        self.assertTrue(flag_index < gok_index < situation_index < mandate_index)

    def test_installed_vanilla_matches_pins_when_available(self) -> None:
        game_root = find_vanilla_game_root()
        if game_root is None:
            self.skipTest("CK3 files unavailable; committed source/body pins still apply")

        expected = {
            "decision": VANILLA_DECISION_FILE_SHA256,
            "values": VANILLA_VALUES_FILE_SHA256,
            "effects": VANILLA_EFFECTS_FILE_SHA256,
        }
        for name, relative in VANILLA_RELATIVE_PATHS.items():
            self.assertEqual(file_sha256(game_root / relative), expected[name])

        vanilla_effects = parse_clausewitz(
            (game_root / VANILLA_RELATIVE_PATHS["effects"]).read_text(encoding="utf-8-sig")
        )
        self.assertEqual(
            body_digest(direct_block(vanilla_effects, DISPATCH_EFFECT)),
            VANILLA_CHAOS_EFFECT_BODY_SHA256,
        )

    def test_restoration_uses_the_original_51_percent_expression(self) -> None:
        text, parsed = read_script(RESTORATION_DECISIONS)
        decision = direct_block(parsed, RESTORATION_DECISION)
        valid = direct_block(decision, "is_valid")
        china_blocks = descendant_blocks(valid, "title:h_china")
        self.assertTrue(china_blocks, "validity must scope the calculation to title:h_china")
        county_blocks = [
            county
            for china in china_blocks
            for county in descendant_blocks(china, "any_de_jure_county")
        ]
        self.assertTrue(county_blocks, "validity must count h_china de-jure counties")
        self.assertTrue(
            any(
                has_assignment(
                    county,
                    "percent",
                    MANDATE_PERCENT_VALUE,
                    operators={">="},
                )
                for county in county_blocks
            ),
            "reference the upstream script value; do not duplicate 0.51",
        )
        self.assertNotRegex(text, r"(?<![\d.])0\.51(?![\d.])")
        self.assertTrue(
            any(
                has_assignment(county, "this", "root")
                and has_assignment(county, "is_tributary_of_suzerain_or_above", "root")
                for county in county_blocks
            ),
            "county ownership must keep vanilla's ruler-or-tributary accounting",
        )

    def test_marker_trigger_is_shared_by_both_decisions(self) -> None:
        _, trigger_file = read_script(RESTORATION_TRIGGERS)
        trigger = direct_block(trigger_file, RESTORATION_TRIGGER)
        held_title_blocks = descendant_blocks(trigger, "any_held_title")
        self.assertTrue(
            any(has_assignment(block, "has_variable", MARKER) for block in held_title_blocks),
            "the durable title variable is the sole identity of a restoration hegemony",
        )

        _, restoration_file = read_script(RESTORATION_DECISIONS)
        restoration = direct_block(restoration_file, RESTORATION_DECISION)
        self.assertTrue(has_assignment(direct_block(restoration, "is_shown"), RESTORATION_TRIGGER, "yes"))
        self.assertTrue(has_assignment(direct_block(restoration, "is_valid"), RESTORATION_TRIGGER, "yes"))

        _, mandate_file = read_script(MANDATE_OVERRIDE)
        mandate = direct_block(mandate_file, VANILLA_DECISION)
        for section_name in ("is_shown", "is_valid"):
            section = direct_block(mandate, section_name)
            direct_guards = [
                guard
                for guard in descendant_blocks(section, "NOT")
                if has_assignment(guard, RESTORATION_TRIGGER, "yes")
            ]
            self.assertEqual(
                len(direct_guards),
                1,
                f"{section_name} must unconditionally hard-block marked rulers",
            )

    def test_custom_shattering_marks_title_and_never_forces_step_down(self) -> None:
        _, custom_file = read_script(CUSTOM_EFFECTS)
        custom = direct_block(custom_file, RECLAIM_EFFECT)
        self.assertFalse(
            has_key(custom, "force_step_down_landed_titles"),
            "custom shattering must preserve the old emperor's personal lands and titles",
        )
        creators = [
            entry
            for entry in custom_file.entries
            if isinstance(entry.value, Block)
            and has_key(entry.value, "create_dynamic_title")
            and has_assignment(entry.value, "tier", "hegemony")
        ]
        self.assertEqual(len(creators), 1, "one helper must create the restoration hegemony")
        creator = creators[0]
        assert isinstance(creator.value, Block)
        self.assertTrue(
            has_assignment(custom, creator.key, "yes"),
            "custom shattering must invoke the marked-title creator",
        )
        marker_setters = [
            block
            for block in descendant_blocks(creator.value, "set_variable")
            if has_assignment(block, "name", MARKER)
            and has_assignment(block, "value", "yes")
        ]
        self.assertEqual(len(marker_setters), 1)
        grant_resolved_index = block_statement_index(
            creator.value,
            lambda entry: entry.key == "resolve_title_and_vassal_change",
        )
        name_helper_index = block_statement_index(
            creator.value,
            lambda entry: entry.key
            == "rmtm_freeze_restoration_hegemony_name_effect"
            and entry.value == "yes",
        )
        self.assertLess(
            grant_resolved_index,
            name_helper_index,
            "apply the frozen dynasty name only after the title-gain on-action",
        )
        generated_text, generated_file = read_script(GENERATED_TITLE_NAMES)
        name_helper = direct_block(
            generated_file, "rmtm_freeze_restoration_hegemony_name_effect"
        )
        self.assertEqual(generated_text.count("is_title_localization_key_used ="), 89)
        self.assertIn("is_title_localization_key_used = dynn_title_song", generated_text)
        self.assertIn("is_title_localization_key_used = dynn_title_tang", generated_text)
        self.assertIn("set_title_name = rmtm_later_dynn_title_song", generated_text)
        self.assertIn("set_title_name = rmtm_later_dynn_title_tang", generated_text)
        self.assertTrue(
            has_assignment(
                name_helper,
                "move_title_name_to",
                "scope:rmtm_restoration_hegemony_title",
            ),
            "unlisted literal player-authored names need a move-title-name fallback",
        )
        self.assertTrue(
            has_assignment(
                name_helper, "set_title_prefix", "rmtm_restoration_title_prefix"
            )
        )
        for language in (
            "english", "french", "german", "japanese", "korean",
            "polish", "russian", "simp_chinese", "spanish",
        ):
            localization = (
                MOD
                / "localization"
                / language
                / f"rmtm_generated_title_names_l_{language}.yml"
            ).read_text(encoding="utf-8-sig")
            self.assertIn(
                'rmtm_later_dynn_title_song:0 '
                '"$rmtm_restoration_title_prefix$$dynn_title_song$"',
                localization,
            )

        effects = read_script_directory(SCRIPTED_EFFECTS_DIR)
        vanilla = collection_block(effects, VANILLA_EFFECT)
        self.assertTrue(has_assignment(vanilla, "force_step_down_landed_titles", "yes"))

        weak_title_pruning_loops = [
            loop
            for loop in descendant_blocks(custom, "every_in_list")
            if has_key(loop, "tgp_fire_china_realm_name_event_for_vassals_effect")
            and has_key(loop, "destroy_title")
        ]
        self.assertEqual(len(weak_title_pruning_loops), 1)
        pruning_limit = direct_block(weak_title_pruning_loops[0], "limit")
        self.assertTrue(
            has_assignment(
                pruning_limit,
                "this",
                "scope:old_emperor_temp",
                operators={"!="},
            ),
            "the weak-ruler pruning pass must not destroy the former hegemon's other titles",
        )
        self.assertTrue(
            contains_fragment(pruning_limit, "rmtm_final_loyal_direct_vassals"),
            "final loyalists must retain weak kingdom/empire titles and their existing names",
        )

    def test_phase_two_loyalty_resolution_is_one_shot_and_priority_ordered(self) -> None:
        trigger_text, trigger_file = read_script(LOYALTY_TRIGGERS)
        hard_defect = direct_block(trigger_file, "rmtm_pro_hegemon_hard_defect_trigger")
        hard_stay = direct_block(trigger_file, "rmtm_pro_hegemon_hard_stay_trigger")
        for fragment in (
            "is_at_war_with",
            "has_relation_rival",
            "has_relation_nemesis",
            "house_has_feud_relation_with_trigger",
            "disloyal",
            "value <= -75",
            "independence_faction",
            "claimant_faction",
        ):
            self.assertIn(fragment, trigger_text)
        for fragment in (
            "has_relation_best_friend",
            "has_relation_soulmate",
            "former_movement_leader",
            "dynasty",
            "has_trait = loyal",
            "has_strong_hook",
        ):
            self.assertIn(fragment, trigger_text)
        self.assertTrue(has_key(hard_defect, "any_targeting_faction"))
        self.assertTrue(has_key(hard_stay, "has_strong_hook"))

        value_text, value_file = read_script(LOYALTY_VALUES)
        score = direct_block(value_file, "rmtm_pro_hegemon_loyalty_score_value")
        self.assertEqual(scalar_values(score, "value", recursive=False), ["65"])
        self.assertEqual(scalar_values(score, "min", recursive=False), ["5"])
        self.assertEqual(scalar_values(score, "max", recursive=False), ["95"])
        for fragment in (
            "value >= 75", "value >= 50", "value >= 25", "value >= 0",
            "value >= -24", "value >= -49", "add = -50",
            "has_relation_friend", "has_relation_lover", "has_relation_elder",
            "has_relation_disciple", "content", "ambitious",
            "is_powerful_vassal_of", "tier_kingdom", "tier_empire",
            "RATIO = 0.35", "RATIO = 0.6", "legitimacy_level <= 1",
            "legitimacy_level >= 4", "level >= 1", "level >= 2",
        ):
            self.assertIn(fragment, value_text)

        effect_text, effect_file = read_script(LOYALTY_EFFECTS)
        resolver = direct_block(effect_file, "rmtm_resolve_pro_hegemon_loyalty_effect")
        self.assertTrue(has_assignment(resolver, "chance", "var:rmtm_loyalty_score"))
        self.assertIn("is_ai = no", effect_text)
        self.assertIn("var:rmtm_loyalty_score >= 50", effect_text)
        self.assertGreaterEqual(effect_text.count("name = rmtm_loyalty_outcome"), 6)
        self.assertIn("rmtm_final_loyal_direct_vassals", effect_text)
        self.assertIn("rmtm_defecting_direct_vassals", effect_text)

        custom_text, _ = read_script(CUSTOM_EFFECTS)
        self.assertIn("remove_variable = rmtm_loyalty_outcome", custom_text)
        self.assertIn("has_game_rule = rmtm_unwavering_loyalty", custom_text)
        self.assertIn("rmtm_resolve_pro_hegemon_loyalty_effect = yes", custom_text)
        self.assertIn("NOT = { is_in_list = rmtm_final_loyal_direct_vassals }", custom_text)

        event_text, event_file = read_script(LOYALTY_EVENTS)
        summary = direct_block(event_file, "rmtm.1001")
        self.assertTrue(has_assignment(summary, "title", "rmtm_loyalty_summary_title"))
        self.assertIn("rmtm_loyalty_summary_both", event_text)
        self.assertIn("rmtm_loyalty_summary_loyal_only", event_text)
        self.assertIn("rmtm_loyalty_summary_defector_only", event_text)

    def test_loyalists_are_frozen_from_direct_vassals_historical_movement(self) -> None:
        _, custom_file = read_script(CUSTOM_EFFECTS)
        custom = direct_block(custom_file, RECLAIM_EFFECT)
        loyalist_loops = [
            loop
            for loop in descendant_blocks(custom, "every_vassal")
            if any(
                contains_fragment(limit, "former_movement_member")
                and contains_fragment(limit, "pro_hegemon_movement")
                for limit in descendant_blocks(loop, "limit")
            )
            and has_assignment(loop, "add_to_list")
        ]
        self.assertEqual(
            len(loyalist_loops),
            1,
            "freeze loyalists once from the old emperor's direct every_vassal set",
        )
        self.assertTrue(
            descendant_blocks(loyalist_loops[0], "limit"),
            "historical movement identity must be a selection condition",
        )
        self.assertFalse(
            any(
                contains_fragment(loop, "former_movement_member")
                for loop in descendant_blocks(custom, "every_vassal_or_below")
            ),
            "indirect vassals must remain inside their existing loyalist realm trees",
        )

    def test_reassignment_loop_excludes_the_preserved_old_emperor_realm(self) -> None:
        _, custom_file = read_script(CUSTOM_EFFECTS)
        custom = direct_block(custom_file, RECLAIM_EFFECT)
        candidates = [
            loop
            for loop in descendant_blocks(custom, "every_in_list")
            if (
                has_key(loop, "change_liege")
                or has_key(loop, "start_tributary_interaction_effect")
            )
            and descendant_blocks(loop, "limit")
        ]
        protected = [
            loop
            for loop in candidates
            if any(excludes_old_emperor(limit) for limit in descendant_blocks(loop, "limit"))
        ]
        self.assertTrue(
            protected,
            "the vanilla re-affiliation loop must exclude characters whose top liege is still the old emperor",
        )

    def test_restoration_effect_keeps_vanilla_effect_order_then_destroys_frozen_titles(self) -> None:
        _, parsed = read_script(RESTORATION_DECISIONS)
        decision = direct_block(parsed, RESTORATION_DECISION)
        effect = direct_block(decision, "effect")

        freeze_index = block_statement_index(
            effect,
            lambda entry: entry.key == "every_held_title"
            and entry_contains(entry, MARKER, "add_to_list"),
        )
        freeze_entry = effect.entries[freeze_index]
        assert isinstance(freeze_entry.value, Block)
        frozen_lists = scalar_values(freeze_entry.value, "add_to_list")
        self.assertEqual(len(frozen_lists), 1, "freeze into one local list before changing the mandate")
        frozen_list = frozen_lists[0]

        flag_index = block_statement_index(
            effect,
            lambda entry: entry.key == "add_character_flag"
            and entry_contains(entry, "claimed_the_mandate_of_heaven", "days", "3"),
        )
        gok_index = block_statement_index(
            effect,
            lambda entry: entry.key == "gok_government_change_story_end_effect"
            and entry.value == "yes",
        )
        situation_index = block_statement_index(
            effect,
            lambda entry: entry.key == "situation:dynastic_cycle"
            and entry_contains(entry, "save_scope_as", "situation"),
        )
        mandate_index = block_statement_index(
            effect,
            lambda entry: entry.key == "tgp_claim_mandate_of_heaven_effect" and entry.value == "yes",
        )
        destroy_index = block_statement_index(
            effect,
            lambda entry: entry.key == "every_in_list"
            and entry_contains(entry, "list", frozen_list, "destroy_title"),
        )
        self.assertEqual(
            sorted([freeze_index, flag_index, gok_index, situation_index, mandate_index, destroy_index]),
            [freeze_index, flag_index, gok_index, situation_index, mandate_index, destroy_index],
            "freeze -> flag -> GoK cleanup -> situation scope -> vanilla claim -> destroy",
        )
        destroy_entry = effect.entries[destroy_index]
        assert isinstance(destroy_entry.value, Block)
        self.assertTrue(
            has_assignment(destroy_entry.value, "exists"),
            "destroy only frozen restoration titles that still exist after the vanilla claim effect",
        )

    def test_daily_localization_is_bom_utf8_and_key_symmetric(self) -> None:
        language_specs = {
            "english": ("l_english:", re.compile(r"[A-Za-z]")),
            "simp_chinese": ("l_simp_chinese:", re.compile(r"[\u3400-\u9fff]")),
        }
        parsed_keys: dict[str, set[str]] = {}
        required = {
            f"rule_{RULE}",
            f"setting_{RECLAIM_SETTING}",
            f"setting_{RECLAIM_SETTING}_desc",
            f"setting_{VANILLA_SETTING}",
            f"setting_{VANILLA_SETTING}_desc",
            RESTORATION_DECISION,
            f"{RESTORATION_DECISION}_desc",
            f"{RESTORATION_DECISION}_tooltip",
            f"{RESTORATION_DECISION}_confirm",
        }
        loc_line = re.compile(r'^\s+([A-Za-z0-9_.-]+):(?:\d+)?\s+"(.*)"\s*$')

        for language, (expected_header, content_pattern) in language_specs.items():
            files = sorted((MOD / "localization" / language).glob("rmtm_*.yml"))
            self.assertTrue(files, f"missing {language} RMTM localization")
            keys: set[str] = set()
            values: dict[str, str] = {}
            for path in files:
                raw = path.read_bytes()
                self.assertTrue(raw.startswith(codecs.BOM_UTF8), f"missing UTF-8 BOM: {path}")
                text = raw.decode("utf-8-sig")
                lines = [line for line in text.splitlines() if line.strip()]
                self.assertTrue(lines and lines[0] == expected_header, f"wrong locale header: {path}")
                for line_number, line in enumerate(lines[1:], start=2):
                    match = loc_line.fullmatch(line)
                    self.assertIsNotNone(match, f"invalid loc row {path}:{line_number}: {line!r}")
                    assert match is not None
                    key, value = match.groups()
                    self.assertNotIn(key, keys, f"duplicate localization key: {key}")
                    keys.add(key)
                    values[key] = value
            self.assertTrue(required <= keys, f"missing {language} keys: {sorted(required - keys)}")
            for key in required:
                self.assertRegex(values[key], content_pattern, f"empty/wrong-language value for {key}")
            parsed_keys[language] = keys

        self.assertEqual(
            parsed_keys["english"],
            parsed_keys["simp_chinese"],
            "daily-development English and Simplified Chinese key sets must stay symmetric",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
