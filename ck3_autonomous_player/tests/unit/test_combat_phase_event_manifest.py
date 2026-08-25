from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path
from typing import Any, Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = PROJECT_ROOT.parent
MANIFEST_PATH = (
    PROJECT_ROOT
    / "src"
    / "xar_autoplayer"
    / "simulation"
    / "data"
    / "ck3_1_19_0_6_stock_combat_phase_events.json"
)
GOLDEN_PATH = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "combat_phase_events"
    / "ck3_1_19_0_6_stock_golden.json"
)
GAME_ROOT = REPOSITORY_ROOT / "Crusader Kings III" / "game"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_manifest_hash(manifest: dict[str, Any]) -> str:
    payload = dict(manifest)
    payload.pop("canonical_manifest_sha256")
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def _walk(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _without_hash_comments(text: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def _named_brace_blocks(text: str) -> list[tuple[str, str]]:
    """Return source-order top-level `name = { ... }` blocks."""

    blocks: list[tuple[str, str]] = []
    i = 0
    depth = 0
    header = re.compile(r"([A-Za-z0-9_]+)\s*=\s*\{")
    while i < len(text):
        if depth == 0:
            match = header.match(text, i)
            if match:
                open_index = match.end() - 1
                cursor = open_index + 1
                nested = 1
                while cursor < len(text) and nested:
                    if text[cursor] == "{":
                        nested += 1
                    elif text[cursor] == "}":
                        nested -= 1
                    cursor += 1
                if nested:
                    raise AssertionError(f"unterminated source block {match.group(1)!r}")
                blocks.append((match.group(1), text[open_index + 1 : cursor - 1]))
                i = cursor
                continue
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return blocks


def _source_event_rows(path: Path) -> list[tuple[str, str, int]]:
    text = _without_hash_comments(path.read_text(encoding="utf-8-sig"))
    rows: list[tuple[str, str, int]] = []
    for key, body in _named_brace_blocks(text):
        event_type = re.search(r"\btype\s*=\s*(commander|knight)\b", body)
        if event_type is None:
            continue
        chance_blocks = [value for name, value in _named_brace_blocks(body) if name == "chance"]
        assert len(chance_blocks) == 1, key
        base = re.search(r"\bbase\s*=\s*(-?\d+)\b", chance_blocks[0])
        assert base is not None, key
        rows.append((key, event_type.group(1), int(base.group(1))))
    return rows


def _multiply_high_target(random31: int, weight_sum: int) -> int:
    return (random31 * weight_sum) >> 31


def test_manifest_identity_order_and_canonical_hash_are_independently_frozen() -> None:
    manifest = _load(MANIFEST_PATH)
    golden = _load(GOLDEN_PATH)

    assert list(manifest) == [
        "schema_version",
        "game_version",
        "executable_sha256",
        "rules_source",
        "files",
        "event_rows",
        "supported_transition_opcodes",
        "completeness",
        "canonical_manifest_sha256",
    ]
    assert manifest["schema_version"] == golden["schema_version"] == 1
    assert manifest["game_version"] == golden["game_version"] == "1.19.0.6"
    assert manifest["executable_sha256"] == golden["executable_sha256"]
    assert manifest["rules_source"] == "stock-installation-static-manifest"
    assert manifest["canonical_manifest_sha256"] == golden["manifest_canonical_sha256"]
    assert _canonical_manifest_hash(manifest) == golden["manifest_canonical_sha256"]

    frozen_columns = (
        "global_load_index",
        "type_load_index",
        "key",
        "type",
        "base_weight",
    )
    actual = [
        {name: row[name] for name in frozen_columns}
        for row in manifest["event_rows"]
    ]
    assert actual == golden["event_order"]
    assert [row["global_load_index"] for row in actual] == list(range(13))
    assert [row["type_load_index"] for row in actual if row["type"] == "commander"] == list(range(4))
    assert [row["type_load_index"] for row in actual if row["type"] == "knight"] == list(range(9))


def test_manifest_ast_shape_is_explicit_and_fail_closed() -> None:
    manifest = _load(MANIFEST_PATH)
    supported_transitions = set(manifest["supported_transition_opcodes"])
    row_keys = {
        "global_load_index",
        "type_load_index",
        "key",
        "type",
        "base_weight",
        "validity_ast",
        "chance_ast",
        "effect_ast",
        "transition_tags",
        "state_dependencies",
    }

    for row in manifest["event_rows"]:
        assert set(row) == row_keys
        assert row["validity_ast"]["op"]
        assert row["chance_ast"]["op"]
        assert row["effect_ast"]["op"]
        assert row["state_dependencies"] == sorted(set(row["state_dependencies"]))
        referenced_dependencies: set[str] = set()
        for node in _walk((row["validity_ast"], row["chance_ast"], row["effect_ast"])):
            if node.get("op") == "state_ref":
                referenced_dependencies.add(node["path"])
            if node.get("op") == "const_fixed":
                assert isinstance(node["raw"], int)
                assert node["scale"] == 100000
            if node.get("op") == "call_transition":
                assert node["key"] in supported_transitions
                assert isinstance(node["args"], dict)
                assert isinstance(node["dependencies"], list)
                referenced_dependencies.update(node["dependencies"])
            if node.get("op") == "select_side_knight":
                assert node["side"] in {"own", "enemy"}
                assert node["filter"]["op"]
                assert node["weight"]["op"]
                assert node["order_policy"]
                assert node["on_selected"]["op"]
            if node.get("op") == "random_list":
                assert node["source_order"] == "preserved"
                assert all(branch["op"] == "random_branch" for branch in node["branches"])
            assert node.get("value_type") != "normalized_ast_ref"
            assert not str(node.get("path", "")).startswith("chance_templates.")
        assert referenced_dependencies <= set(row["state_dependencies"])

    root_no_ops = [row["key"] for row in manifest["event_rows"] if row["effect_ast"]["op"] == "call_transition" and row["effect_ast"].get("key") == "no_op"]
    assert root_no_ops == ["commander_none", "knight_none"]
    completeness = manifest["completeness"]
    assert completeness["loaded_playset_verified"] is False
    assert completeness["ast_evaluator_ready"] is False
    assert completeness["original_trace_ready"] is False
    assert completeness["unsupported_opcodes"]


def test_stock_source_files_match_hashes_and_top_level_rows_when_installed() -> None:
    manifest = _load(MANIFEST_PATH)
    golden = _load(GOLDEN_PATH)
    if not GAME_ROOT.is_dir():
        return

    for source in manifest["files"]:
        path = GAME_ROOT / source["relative_path"]
        assert path.is_file(), source["relative_path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest().upper() == source["sha256"]

    commander_path = GAME_ROOT / "common/combat_phase_events/00_commander_phase_events.txt"
    knight_path = GAME_ROOT / "common/combat_phase_events/00_knight_phase_events.txt"
    source_rows = _source_event_rows(commander_path) + _source_event_rows(knight_path)
    expected_rows = [
        (row["key"], row["type"], row["base_weight"])
        for row in golden["event_order"]
    ]
    assert source_rows == expected_rows


def test_independent_selector_and_transition_vectors_are_self_consistent() -> None:
    golden = _load(GOLDEN_PATH)
    for vector in golden["selector_vectors"]:
        assert sum(vector["weights_in_source_order"]) == vector["weight_sum"]
        assert _multiply_high_target(vector["random31"], vector["weight_sum"]) == vector["target_via_multiply_high"]
        cumulative = 0
        selected = None
        for index, weight in enumerate(vector["weights_in_source_order"]):
            if weight <= 0:
                continue
            cumulative += weight
            if vector["target_via_multiply_high"] < cumulative:
                selected = index
                break
        assert selected == vector["selected_type_load_index"]

    maim = golden["transition_vectors"]["maim_random"]
    assert sum(maim["weights"]) == maim["weight_sum"]
    assert _multiply_high_target(maim["random31"], maim["weight_sum"]) == maim["target_via_multiply_high"]
    assert maim["selected_index"] == 0

    for vector in golden["transition_vectors"]["knight_increase_prowess"]:
        assert _multiply_high_target(vector["random31"], sum(vector["weights"])) == vector["target_via_multiply_high"]


def test_current_live_roster_golden_is_read_from_the_paused_v2_fixture() -> None:
    golden = _load(GOLDEN_PATH)["current_live_roster_observation"]
    fixture_path = PROJECT_ROOT / golden["source_fixture"]
    assert hashlib.sha256(fixture_path.read_bytes()).hexdigest().upper() == golden["source_fixture_sha256"]
    fixture = _load(fixture_path)
    assert fixture["capture"]["revision"] == golden["revision"]
    observation = fixture["combat_simulation_inputs"]
    scenario = observation["scenario"]
    assert scenario["kind"] == "explicit_hypothetical_contact"
    assert scenario["actual_route_dependency"] is False
    assert observation["target_province_id"] == golden["target_province_id"]
    assert scenario["attacker_entry_province_id"] == golden["attacker_entry_province_id"]
    assert [army["commander"]["character_id"] for army in observation["armies"]] == golden["commanders"]
    observed_knights = {
        str(army["army_id"]): [member["character_id"] for member in army["knights"]["members"]]
        for army in observation["armies"]
    }
    assert observed_knights == golden["knights_by_army"]
    all_character_ids = golden["commanders"] + [
        character_id
        for members in golden["knights_by_army"].values()
        for character_id in members
    ]
    assert len(all_character_ids) == 28
    assert len(set(all_character_ids)) == 28


class CombatPhaseEventManifestTests(unittest.TestCase):
    def test_manifest_identity_order_and_canonical_hash(self) -> None:
        test_manifest_identity_order_and_canonical_hash_are_independently_frozen()

    def test_manifest_ast_shape(self) -> None:
        test_manifest_ast_shape_is_explicit_and_fail_closed()

    def test_stock_source_files(self) -> None:
        test_stock_source_files_match_hashes_and_top_level_rows_when_installed()

    def test_independent_vectors(self) -> None:
        test_independent_selector_and_transition_vectors_are_self_consistent()

    def test_current_live_roster(self) -> None:
        test_current_live_roster_golden_is_read_from_the_paused_v2_fixture()
