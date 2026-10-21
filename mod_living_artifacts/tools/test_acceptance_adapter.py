"""Offline producer/consumer and once-only control tests; no live qualification."""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest

import acceptance_adapter as adapter
from acceptance_contract import ArtifactSample, Object, exact_getter_integer, json_value, pin, read, write_once
import prepare_fixture
from living_artifacts_core import render_core_localization
from test_core_generation import Script


def sample_line(*, equipped: bool = True) -> str:
    template = prepare_fixture._sample_log(equipped)
    match = re.fullmatch(r'debug_log = "(.*)"', template)
    if match is None:
        raise AssertionError("Actual logger producer changed its literal form")
    values = {
        "xalw_fixture_item.GetOwner.GetID": "29829",
        "xalw_fixture_item.GetID": "16777217",
        "xalw_fixture_item.GetDurability|5": "100.00000",
        "xalw_fixture_owner.MakeScope.Var('xalw_fixture_observer_sequence').GetValue|5": "2.00000",
        "xalw_fixture_owner.MakeScope.Var('xalw_fixture_observed_day').GetValue|5": "1000.00000",
        "xalw_fixture_owner.MakeScope.ScriptValue('xalw_current_month_value')|5": "12800.00000",
    }
    for name, value in (("level", "2"), ("xp_in_level", "0"), ("pending_xp", "0"), ("growth_sequence", "1"),
                        ("last_settled_month", "12800"), ("resonance", "25")):
        values[f"xalw_fixture_item.MakeScope.Var('xalw_{name}').GetValue|5"] = value + ".00000"
    def resolve(found: re.Match[str]) -> str:
        key = found.group(1)
        if key not in values:
            raise AssertionError("Unit getter fixture must explicitly bind new producer field: " + key)
        return values[key]
    return re.sub(r"\[([^\]]+)\]", resolve, match.group(1))


class UnitPort:
    """Authored public-boundary rows to exercise control logic, never SDK evidence."""

    def __init__(self, output: Path) -> None:
        self.output = output
        self.state = output / "state"
        self.manifest: object = {"machine_id": "unit-machine", "game": {"version": "1.20.0.4", "exe_sha256": "a" * 64}}
        self.frozen: object = {"run_id": "unit-run"}
        self.calls: list[str] = []
        self.frame: Object = {
            "paused": True, "map_ready": True, "source": "injected-dll-named-pipe", "backend_id": "native-headless",
            "episode_projection": "native_campaign", "revision": 1, "native_revision": 1, "date_raw": 24000,
            "played_character": {"character_id": 29829, "alive": True, "source": "native"},
            "active_event": None, "pending_character_interaction": None,
            "diagnostics": {"bridge_pid": 123, "connection_generation": 1, "pipe_name": "unit-pipe",
                            "hello": {"pid": 123, "connection_generation": 1, "ck3_build_match": True,
                                      "expected_ck3_version": "1.20.0.4", "expected_ck3_sha256": "a" * 64}},
            "managed_campaign_run_binding": {"run_id": "unit-run", "bridge_pipe": "unit-pipe"},
        }

    def snapshot(self, allow_actor_change: bool = False, require_event_free: bool = True) -> object:
        raise AssertionError("Not part of this unit's action-only seam")

    def execute_plan(self, steps: list[Object], name: str, timeout: int | float | None = None, reserve: int = 90) -> object:
        tool = steps[0]["tool"]
        if not isinstance(tool, str):
            raise AssertionError("Tool must be explicit")
        self.calls.append(tool)
        result: Object
        if tool == adapter.WINDOW:
            result = {"available": True, "current": {"available": True, "native_visible": True, "effective_visible": True}}
        elif tool == adapter.ITEM:
            result = {"available": True, "read_only": True, "loaded_source_pins_verified": True, "personally_owned": True,
                      "inventory_artifact": True, "requested_artifact_id": 16777217, "played_character_id": 29829,
                      "date_raw": 24000, "native_equipped_observed": True, "equipped": False, "equipped_slot_index": None,
                      "effective_slot_index": 0, "replacing_artifact_id": None, "can_equip_in_effective_slot": True, "can_unequip": False}
        elif tool == adapter.EQUIP:
            result = {"once_intent_consumed": True, "intent_sequence": 1,
                      "desired_inventory_state_observed": True}  # Deliberately dishonest ACK flag is never credited.
        elif tool == adapter.EQUIP_POST:
            result = {"desired_inventory_state_observed": False}
        else:
            raise AssertionError("Unexpected unit request: " + tool)
        row: Object = {"ok": True, "result": result, "after_snapshot": self.frame}
        write_once(self.output / (name + ".actual-results.json"), {"rows": [row], "unit_test_data": True})
        return [row]

    def advance_day(self, days: int = 1, timeout: float = 300, allow_event_boundary: bool = False,
                    allow_actor_change: bool = False) -> object:
        raise AssertionError("No simulated days in this unit test")

    def guard(self, reserve: int = 90) -> object:
        return {"unit_test": True}

    def log_bytes(self, name: str = "debug.log", maximum: int = 64 * 1024 * 1024) -> bytes:
        raise AssertionError("No authored log can stand in for a live logger in this unit")

    def checkpoint(self, name: str, value: object) -> object:
        return write_once(self.output / (name + ".json"), value)

    def root_checkpoint(self, name: str, request: Object, reserve: int = 90) -> object:
        raise AssertionError("No reviewer in this unit")


class AcceptanceContractTests(unittest.TestCase):
    def test_localization_rejects_script_scope_prefix_and_keeps_named_object_methods(self) -> None:
        for language in ("simp_chinese", "english"):
            entries = render_core_localization("simp_chinese" if language == "simp_chinese" else "english")
            self.assertFalse(any("[scope:" in body for body in entries.values()))
            self.assertIn("xalw_artifact.MakeScope.Var('xalw_level')", entries["xalw.10.desc"])
        self.assertNotIn("[scope:", prepare_fixture.render_observer_effects())

    def test_actual_logger_template_reaches_consumer(self) -> None:
        sample = ArtifactSample.parse(sample_line())
        self.assertEqual((sample.owner_id, sample.artifact_id, sample.level, sample.xp, sample.growth_sequence), ("29829", "16777217", 2, 0, 1))
        self.assertEqual(ArtifactSample.parse(sample_line(equipped=False)).equipped, False)

    def test_getter_fraction_cannot_be_rounded_into_a_passing_integer(self) -> None:
        with self.assertRaisesRegex(ValueError, "noninteger"):
            ArtifactSample.parse(sample_line().replace("level=2.00000", "level=2.00001"))
        self.assertEqual(exact_getter_integer("1,280.00000", "grouped native integer"), 1280)
        with self.assertRaises(ValueError):
            exact_getter_integer("12,80.00000", "malformed grouping")

    def test_missing_wrong_duplicate_or_unexpanded_fields_are_rejected(self) -> None:
        for changed in (sample_line().replace("pending=0.00000;", ""), sample_line().replace("growth=", "growth_sequence="),
                        sample_line() + ";level=2.00000", sample_line().replace("owner=29829", "owner=[scope:owner.GetID]")):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                ArtifactSample.parse(changed)

    def test_identity_keeps_decimal_strings_across_json_roundtrip(self) -> None:
        sample = ArtifactSample.parse(sample_line().replace("artifact=16777217", "artifact=18446744073709551614"))
        payload = sample.to_json()
        self.assertEqual(json.loads(json.dumps(payload))["artifact_id"], "18446744073709551614")
        self.assertEqual(json_value(("first", "second")), ["first", "second"])
        with self.assertRaisesRegex(ValueError, "safe range"):
            json_value(2**53)

    def test_read_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "wrong.json"
            path.write_text('{"schema_version":1,"schema_version":2}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                read(path)

    def test_actual_input_rarities_and_references_are_not_inferred_from_role(self) -> None:
        rows = [f"XALW_INPUT_V1;role={role};owner=29829;artifact={number};rarity={rarity}"
                for number, role, rarity in ((1, "target", "masterwork"), (2, "common", "common"), (3, "masterwork", "masterwork"),
                                             (4, "famed", "famed"), (5, "illustrious", "illustrious"))]
        self.assertEqual(adapter._inputs("\n".join(rows).encode())["illustrious"], ("29829", "5"))
        with self.assertRaisesRegex(ValueError, "rarity"):
            adapter._inputs("\n".join(rows).replace("artifact=5;rarity=illustrious", "artifact=5;rarity=famed").encode())
        with self.assertRaisesRegex(ValueError, "distinct"):
            adapter._inputs("\n".join(rows).replace("artifact=5", "artifact=4").encode())

    def test_observer_after_initialization_only_writes_own_metadata(self) -> None:
        script = Script(prepare_fixture.render_observer_effects())
        observer = script.named("xalw_fixture_observe_effect")
        names = [script.scalar(block, "name").value for block in script.descendants(observer, "set_variable")]
        self.assertTrue(names)
        self.assertTrue(all(name.startswith("xalw_fixture_") for name in names))
        self.assertFalse(script.descendants(observer, "change_variable"))
        self.assertFalse(any(scalar.key in {"xalw_feed_material_effect", "xalw_settle_xp_effect", "destroy_artifact", "equip_artifact_to_owner_replace"}
                             for block in (observer, *script.blocks) for scalar in script.scalars(block)
                             if observer.opening < scalar.start < observer.end))

    def test_unknown_original_equipment_ack_is_not_replayed_or_credited(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            port = UnitPort(Path(temporary))
            session = adapter.Session({"run_id": "unit-run"}, port, adapter.Contract(72, 420, 60, (), (), 29829))
            with self.assertRaisesRegex(adapter.CaseBlocked, "unknown"):
                session.equip("16777217", True)
            self.assertEqual(port.calls.count(adapter.EQUIP), 1)
            self.assertEqual(port.calls.count(adapter.EQUIP_POST), 3)
            self.assertTrue(session.original_action_unknown)

    def test_every_declared_optional_action_is_explicit(self) -> None:
        config = read(Path(__file__).with_name("core_continuous.contract.json"))
        spec: Object = {"required_mcp_tools": list(adapter.REQUIRED_TOOLS), "opt_in_read_only_mcp_tools": [adapter.ITEM],
                        **adapter.REQUIRED_OPT_INS}
        context: Object = {"product": "living-artifacts", "case": "core_continuous", "case_contract": config, "case_spec": spec}
        self.assertEqual(adapter.validate_contract(context).maximum_days, 72)
        spec["opt_in_player_artifact_personal_use_actions"] = False
        with self.assertRaisesRegex(ValueError, "opt-in"):
            adapter.validate_contract(context)

    def test_frozen_emitter_reaches_runtime_copy_and_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = root / "emitted"
            fixture = prepare_fixture.emit_fixture(original)
            context: Object = {"state_dir": str(root / "allocated"),
                "case_contract": read(Path(__file__).with_name("core_continuous.contract.json")),
                "case_inputs": {"post_start": {"government_key": "feudal_government", "primary_title_tier_key": "duchy", "independent": True}}}
            adapter._write_fixture_contract(original, adapter._bound_config(context), fixture)
            copied = root / "allocated/profile/mod-content/fixture"
            shutil.copytree(original, copied)
            self.assertTrue(adapter._prepared_sources(context, root / "allocated"))
            script = copied / "common/scripted_effects/xalw_fixture_observer.txt"
            script.write_bytes(script.read_bytes() + b"\n# changed after preparation\n")
            with self.assertRaisesRegex(ValueError, "runtime fixture differs"):
                adapter._prepared_sources(context, root / "allocated")

    def test_pins_reject_equal_but_wrong_json_types(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "one-byte.txt"
            source.write_bytes(b"a")
            reference = pin(source)
            for value in (True, 1.0):
                wrong: dict[str, object] = dict(reference)
                wrong["bytes"] = value
                with self.subTest(value=value), self.assertRaisesRegex(ValueError, "bool/float"):
                    adapter._checked_pin(wrong, "unit source", source)


if __name__ == "__main__":
    unittest.main()
