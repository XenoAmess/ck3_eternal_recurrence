"""Real product CLI regressions; no installed game or live acceptance is claimed."""
from __future__ import annotations

import json
import hashlib
import os
import re
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from typing import Iterator

SOURCE = Path(__file__).resolve().parents[1]
SUPPORT = SOURCE.parent / "tools"
sys.path.insert(0, str(SUPPORT))
from extract_auto_upgrade_buildings import Block, parse_clausewitz


def walk(block: Block) -> Iterator[Block]:
    yield block
    for entry in block.entries:
        if isinstance(entry.value, Block):
            yield from walk(entry.value)


def child(block: Block, key: str) -> Block:
    values = [entry.value for entry in block.entries if entry.key == key]
    if len(values) != 1 or not isinstance(values[0], Block):
        raise AssertionError(f"expected one block {key}")
    return values[0]


def scalar(block: Block, key: str) -> str:
    values = [entry.value for entry in block.entries if entry.key == key]
    if len(values) != 1 or not isinstance(values[0], str):
        raise AssertionError(f"expected one scalar {key}")
    return values[0]


class DeJureConquestStaticContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="djc-product-cli-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.product = self.root / "mod_de_jure_conquest"
        metadata = runpy.run_path(str(SOURCE / "tools/product.py"))
        runtime = metadata.get("RUNTIME_FILES")
        if not isinstance(runtime, frozenset) or not all(isinstance(x, str) for x in runtime):
            raise TypeError("actual product runtime inventory is not a string frozenset")
        for relative in runtime:
            source = SOURCE / relative
            target = self.product / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        for name in ("product.py", "validate_static.py", "build_release.py", "gen_acceptance_fixture.py", "verify_fixture_log.py"):
            target = self.product / "tools" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / "tools" / name, target)

    def command(self, tool: str, *args: str) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(SUPPORT)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run([sys.executable, "-B", "-X", "utf8", str(self.product / "tools" / tool), *args],
                              cwd=self.root, env=environment, capture_output=True, text=True, encoding="utf-8", check=False)

    def test_full_runtime_and_nine_language_release_validation(self) -> None:
        result = self.command("validate_static.py", "--no-installed-game", "--release-localization")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertIsInstance(report, dict)
        self.assertEqual(report["runtime_allowlist_count"], 16)
        self.assertEqual(report["checked_runtime_file_count"], 16)
        self.assertEqual(report["live"], "NOT_RUN")
        self.assertEqual(report["errors"], [])

    def test_real_cb_source_rejects_AI_fee_and_war_identity_regressions(self) -> None:
        cb = self.product / "common/casus_belli_types/duchy_de_jure_greatwar.txt"
        original = cb.read_bytes()
        for before, after, expected in (
            (b"\tai = no", b"\tai = yes", "ai must equal no"),
            (b"\t\t\tvalue = 200", b"\t\t\tvalue = 201", "value must equal 200"),
            (b"djc_join_de_jure_defenders = { WAR = root.war }", b"djc_join_de_jure_defenders = { WAR = scope:attacker }", "WAR must equal root.war"),
        ):
            with self.subTest(expected=expected):
                self.assertEqual(original.count(before), 1)
                cb.write_bytes(original.replace(before, after, 1))
                result = self.command("validate_static.py", "--no-installed-game", "--release-localization")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(expected, result.stdout)
                cb.write_bytes(original)
        self.assertEqual(self.command("validate_static.py", "--no-installed-game", "--release-localization").returncode, 0)

    def test_upstream_and_foreign_Workshop_ids_reject_before_git_or_output(self) -> None:
        for item in ("3600021457", "3809999999", "0", "true"):
            with self.subTest(item=item):
                target = self.root / ("forbidden-" + item)
                result = self.command("build_release.py", "--output", str(target), "--workshop-item-id", item)
                self.assertEqual(result.returncode, 1)
                self.assertIn("maintained Workshop item must be 3812510217", result.stderr)
                self.assertFalse(target.exists())
                self.assertNotIn("not a git repository", result.stderr)

    def test_wrong_entry_shapes_fail_closed_without_traceback(self) -> None:
        cb = self.product / "common/casus_belli_types/duchy_de_jure_greatwar.txt"
        original = cb.read_bytes()
        cb.write_bytes(original.replace(b"allowed_for_character = {", b"allowed_for_character = no\n unused_original_allowed_block = {", 1))
        result = self.command("validate_static.py", "--no-installed-game")
        self.assertEqual(result.returncode, 1)
        self.assertIn("allowed_for_character must be a block", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_original_matrix_emitter_keeps_72_unique_markers_and_121_fixture(self) -> None:
        target = self.root / "actual-emitted-fixture"
        result = self.command("gen_acceptance_fixture.py", "--output", str(target))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('supported_version="1.21.*"', (target / "descriptor.mod").read_text())
        contract = json.loads((target / "fixture-contract.json").read_text())
        self.assertEqual(len(contract["markers"]), 72)
        self.assertEqual(len(set(contract["markers"])), 72)
        self.assertEqual(contract["player_history_id"], 1128)
        self.assertTrue(contract["claims_excluded"])

    def fixture(self, tier: str) -> Path:
        target = self.root / ("fixture-" + tier)
        if not target.exists():
            result = self.command("gen_acceptance_fixture.py", "--tier", tier, "--output", str(target))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return target

    def event_definitions(self, fixture: Path) -> dict[str, Block]:
        result: dict[str, Block] = {}
        for path in (fixture / "events").glob("*.txt"):
            for entry in parse_clausewitz(path.read_text(encoding="utf-8-sig")).entries:
                if entry.key.startswith("djct.") and isinstance(entry.value, Block):
                    self.assertNotIn(entry.key, result)
                    result[entry.key] = entry.value
        return result

    def synthetic_log(self, fixture: Path, suffix: str = "") -> Path:
        contract = json.loads((fixture / "fixture-contract.json").read_text())
        path = self.root / (fixture.name + suffix + ".SYNTHETIC-UNIT-NOT-GAME.log")
        path.write_text("SYNTHETIC UNIT INPUT; NOT GAME EVIDENCE\nDJCT: TEST BEGIN scripted-war-1128\n" + "\n".join("DJCT: TEST PASS " + marker for marker in contract["markers"]) + "\nDJCT: TEST DONE scripted-war-1128\n", encoding="utf-8")
        return path

    def test_tiers_partition_exact_original_72_and_refuse_invalid_tier(self) -> None:
        all_contract = json.loads((self.fixture("all") / "fixture-contract.json").read_text())
        combined = []
        for tier in ("duchy", "kingdom", "empire"):
            contract = json.loads((self.fixture(tier) / "fixture-contract.json").read_text())
            self.assertEqual(len(contract["markers"]), 24)
            self.assertTrue(all(marker.startswith(tier + "_") for marker in contract["markers"]))
            self.assertEqual(contract["nominal_completion_natural_day"], 16)
            self.assertEqual(contract["max_natural_days"], 18)
            self.assertLess(contract["max_natural_days"], 35)
            combined.extend(contract["markers"])
        self.assertEqual(combined, all_contract["markers"])
        self.assertEqual(len(set(combined)), 72)
        self.assertEqual(all_contract["max_natural_days"], 48)
        result = self.command("gen_acceptance_fixture.py", "--tier", "invalid", "--output", str(self.root / "invalid-tier"))
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / "invalid-tier").exists())

    def test_actual_event_graph_has_two_day_reset_and_bounded_terminal_windows(self) -> None:
        for tier in ("all", "duchy", "kingdom", "empire"):
            fixture = self.fixture(tier)
            events = self.event_definitions(fixture)
            day, event = 1, "djct.1"
            visited: set[str] = set()
            while event != "djct.800":
                self.assertNotIn(event, visited)
                visited.add(event)
                links = []
                for block in walk(events[event]):
                    for entry in block.entries:
                        if entry.key == "trigger_event":
                            if isinstance(entry.value, Block):
                                links.append((scalar(entry.value, "id"), int(scalar(entry.value, "days"))))
                            elif isinstance(entry.value, str):
                                links.append((entry.value, 0))
                self.assertEqual(len(links), 1, (tier, event, links))
                target, delay = links[0]
                if event != "djct.1" and int(event.split(".")[1]) % 10 == 0:
                    self.assertEqual(delay, 2)
                    self.assertEqual(int(target.split(".")[1]), int(event.split(".")[1]) + 3)
                day += delay
                event = target
            self.assertEqual(day, 46 if tier == "all" else 16)
            on_action = parse_clausewitz((fixture / "common/on_action/djct_on_actions.txt").read_text(encoding="utf-8-sig"))
            watchdog = [block for block in walk(on_action) if any(entry.key == "id" and entry.value == "djct.901" for entry in block.entries)]
            self.assertEqual(len(watchdog), 1)
            self.assertEqual(int(scalar(watchdog[0], "days")), 48 if tier == "all" else 18)
            for terminal in ("djct.800", "djct.900"):
                self.assertEqual(scalar(events[terminal], "type"), "character_event")
                self.assertEqual(scalar(events[terminal], "theme"), "realm")
                self.assertFalse(any(entry.key == "hidden" for entry in events[terminal].entries))
                self.assertEqual(scalar(child(events[terminal], "option"), "name"), "djct_keep_paused")

    def test_actual_preparation_is_delayed_readback_and_only_restores_Naples(self) -> None:
        for tier in ("duchy", "kingdom", "empire"):
            fixture = self.fixture(tier)
            events = self.event_definitions(fixture)
            first = {"duchy": 10, "kingdom": 40, "empire": 70}[tier]
            for stage in (first, first + 10, first + 20):
                prepare = events[f"djct.{stage}"]
                self.assertFalse(any(entry.key == "start_war" for block in walk(prepare) for entry in block.entries))
                timers = [entry.value for block in walk(prepare) for entry in block.entries if entry.key == "add_character_flag"]
                self.assertEqual(len(timers), 1)
                self.assertIsInstance(timers[0], Block)
                timer = next(value for value in timers if isinstance(value, Block))
                self.assertEqual(scalar(timer, "flag"), "djct_reset_wait")
                self.assertEqual(scalar(timer, "days"), "2")
                self.assertTrue(any(entry.key == "add_stress" and entry.value == "-1000" for block in walk(prepare) for entry in block.entries))
                ready = events[f"djct.{stage+3}"]
                actual = child(child(child(ready, "immediate"), "if"), "limit")
                self.assertEqual(scalar(actual, "stress"), "0")
                wait_guards = [entry.value for entry in actual.entries if entry.key == "NOT" and isinstance(entry.value, Block) and any(item.key == "has_character_flag" and item.value == "djct_reset_wait" for item in entry.value.entries)]
                self.assertEqual(len(wait_guards), 1)
                independent_changes = [block for block in walk(prepare) if any(entry.key == "type" and entry.value == "independency" for entry in block.entries)]
                self.assertEqual(len(independent_changes), 0 if tier == "empire" else 1)
                if tier != "empire":
                    restored = [entry.key for block in walk(prepare) for entry in block.entries if isinstance(entry.value, Block) and any(item.key == "becomes_independent" for item in entry.value.entries)]
                    self.assertEqual(restored, ["var:djct_napoli_holder"])
                    self.assertTrue(any(entry.key == "djct_napoli_originally_independent" or entry.key == "var:djct_napoli_originally_independent" for block in walk(prepare) for entry in block.entries))

    def test_all_original_72_pass_predicates_remain_exact(self) -> None:
        events = self.event_definitions(self.fixture("all"))
        actual: dict[str, Block] = {}
        for event in events.values():
            for block in walk(event):
                logs = [entry.value for entry in block.entries if entry.key == "debug_log" and isinstance(entry.value, str) and entry.value.startswith('"DJCT: TEST PASS ')]
                if logs:
                    self.assertEqual(len(logs), 1)
                    message = logs[0]
                    self.assertIsInstance(message, str)
                    if not isinstance(message, str):
                        raise AssertionError("PASS must have a string literal")
                    marker = message.removeprefix('"DJCT: TEST PASS ').removesuffix('"')
                    self.assertNotIn(marker, actual)
                    actual[marker] = child(block, "limit")
        expected = {}
        for tier, goal, county_a, county_b, holder_a, holder_b in (
            ("duchy", "d_capua", "c_capua", "c_napoli", "djct_capua_holder", "djct_napoli_holder"),
            ("kingdom", "k_sicily", "c_capua", "c_napoli", "djct_capua_holder", "djct_napoli_holder"),
            ("empire", "e_italy", "c_roma", "c_firenze", "djct_roma_holder", "djct_firenze_holder"),
        ):
            cb = tier + "_de_jure_greatwar"
            for outcome in ("attacker", "white_peace", "defender"):
                label = tier + "_" + outcome + "_"
                conditions = {
                    "ai_unavailable": f"var:djct_case_primary = {{ NOT = {{ can_declare_war = {{ defender = root casus_belli = {cb} target_titles = {{ title:{goal} }} }} }} }}",
                    "distinct_realms": "var:djct_case_primary.top_liege != var:djct_case_secondary.top_liege",
                    "native_eligibility": f"can_declare_war = {{ defender = var:djct_case_primary.top_liege casus_belli = {cb} target_titles = {{ title:{goal} }} }}",
                    "native_participants": f"var:djct_current_war = {{ using_cb = {cb} is_attacker = root is_defender = root.var:djct_case_primary.top_liege is_defender = root.var:djct_case_secondary.top_liege }}",
                    "native_goal": f"var:djct_current_war = {{ trigger_if = {{ limit = {{ has_variable = djc_goal_title }} var:djc_goal_title = title:{goal} }} trigger_else = {{ always = no }} }}",
                    "county_ownership": f"title:{county_a}.holder = root title:{county_b}.holder = root" if outcome == "attacker" else f"title:{county_a}.holder = var:{holder_a} title:{county_b}.holder = var:{holder_b}",
                    "war_ended": f"NOT = {{ any_character_war = {{ using_cb = {cb} is_attacker = root }} }}",
                    "outside_and_owned_unchanged": "title:c_vannes.holder = var:djct_capua_holder title:c_apulia.holder = var:djct_owned_holder",
                }
                expected.update({label + suffix: parse_clausewitz(condition) for suffix, condition in conditions.items()})
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 72)

    def test_real_three_log_consumer_accepts_union_and_rejects_corruption(self) -> None:
        fixtures = [self.fixture(tier) for tier in ("duchy", "kingdom", "empire")]
        logs = [self.synthetic_log(fixture) for fixture in fixtures]
        args = ["--aggregate"]
        for fixture, log in zip(fixtures, logs, strict=True):
            args += ["--log", str(log), "--contract", str(fixture / "fixture-contract.json")]
        report = self.root / "aggregate-software.json"
        result = self.command("verify_fixture_log.py", *args, "--report", str(report))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(report.read_text())
        self.assertEqual(payload["expected_pass_count"], 72)
        self.assertEqual(payload["observed_pass_count"], 72)
        self.assertEqual(len(payload["source_runs"]), 3)
        self.assertTrue(all(count == 1 for count in payload["observed_marker_counts"].values()))
        original = logs[0].read_text()
        first_marker = json.loads((fixtures[0] / "fixture-contract.json").read_text())["markers"][0]
        for index, corrupted in enumerate((original + "DJCT: TEST PASS " + first_marker + "\n", original.replace("DJCT: TEST PASS " + first_marker + "\n", ""), original + "DJCT: TEST PASS unknown_business_marker\n", original + "DJCT: TEST FAIL prepared_readback\n", original + "DJCT: TEST STOP failed_no_successor\n")):
            logs[0].write_text(corrupted)
            result = self.command("verify_fixture_log.py", *args, "--report", str(self.root / f"corrupt-{index}.json"))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)
        logs[0].write_text(original)
        duplicate = args.copy()
        duplicate[duplicate.index(str(logs[1]))] = str(logs[0])
        result = self.command("verify_fixture_log.py", *duplicate, "--report", str(self.root / "duplicate-log.json"))
        self.assertEqual(result.returncode, 1)

    def test_log_contract_types_and_legacy_single_log_remain_explicit(self) -> None:
        fixture = self.fixture("all")
        contract = fixture / "fixture-contract.json"
        value = json.loads(contract.read_text())
        log = self.synthetic_log(fixture)
        legacy = {key: value[key] for key in ("schema", "player_history_id", "layer", "markers", "claims_excluded", "requires_done_marker")}
        legacy["schema"] = "djc.external-acceptance.v1"
        contract.write_text(json.dumps(legacy))
        result = self.command("verify_fixture_log.py", "--log", str(log), "--contract", str(contract), "--report", str(self.root / "legacy-single.json"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for index, wrong in enumerate((dict(value, player_history_id=True), dict(value, max_natural_days=True), dict(value, tier=["all"]), dict(value, markers=value["markers"][:-1]), dict(value, claims_excluded=[]), dict(value, latest_date="1066.12.31"), dict(value, completion_event="unknown.1"))):
            contract.write_text(json.dumps(wrong))
            result = self.command("verify_fixture_log.py", "--log", str(log), "--contract", str(contract), "--report", str(self.root / f"wrong-contract-{index}.json"))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_release_localization_rejects_missing_original_foreign_key(self) -> None:
        localization = self.product / "localization/french/greatwar_l_french.yml"
        rows = localization.read_text(encoding="utf-8-sig").splitlines(keepends=True)
        localization.write_text("".join(rows[:-1]), encoding="utf-8-sig")
        result = self.command("validate_static.py", "--no-installed-game", "--release-localization")
        self.assertEqual(result.returncode, 1)
        self.assertIn("release localization keys differ: french", result.stdout)

    def gui_inputs(self) -> tuple[Path, Path, Path, Path]:
        fixture = self.root / "gui-companion"
        result = self.command("gen_acceptance_fixture.py", "--tier", "duchy", "--with-gui-observer", "--output", str(fixture))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        before, after = self.root / "SYNTHETIC-S1.ck3", self.root / "SYNTHETIC-S2.ck3"
        self.synthetic_gui_save(before, 2)
        self.synthetic_gui_save(after, 3)
        artifacts = []
        for kind in ("preview", "declare_action", "load_action", "reloaded_state"):
            path = self.root / ("SYNTHETIC-NOT-GAME-" + kind + ".txt")
            path.write_text("Synthetic unit artifact only: " + kind, encoding="utf-8")
            artifacts.append({"kind": kind, "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        evidence = self.root / "SYNTHETIC-GUI-evidence.json"
        evidence.write_text(json.dumps({"schema": "djc.gui-physical-save-evidence.v1", "machine_id": "desktop-3fevhd2-1c74096080", "game_version": "1.21.0.3", "game_build": 26785313, "exe_sha256": "859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28", "tier": "duchy", "ordinary_gui_declaration": True, "same_completed_matrix_world": True, "paused_same_date": True, "load_method": "gui_load_same_process", "process_before": "101", "process_after": "101", "loaded_save_sha256": hashlib.sha256(before.read_bytes()).hexdigest(), "preview_prestige": "50", "preview_piety": "200", "artifacts": artifacts}), encoding="utf-8")
        return before, after, evidence, fixture / "gui-observer-contract.json"

    def synthetic_gui_save(self, path: Path, phase: int, *, changes: dict[str, tuple[str, int]] | None = None, standalone: bool = False, physical_date: str = "1066.9.15") -> None:
        # Deliberately beyond JS Number's safe integer domain. These are private
        # synthetic saved-value parser tests, never engine/resource qualification.
        balance = 9007199254740993
        atoms = {key: ("value", value) for key, value in {
            "djcg_phase": phase * 100000, "djcg_tier": 100000, "djcg_date": 12345600000,
            "djcg_before_gold": balance, "djcg_before_prestige": balance, "djcg_before_piety": balance,
            "djcg_after_gold": balance, "djcg_after_prestige": balance - 5000000, "djcg_after_piety": balance - 30000000,
            "djcg_same_faith": 100000, "djcg_peace_of_god": 100000, "djcg_expected_extra_piety": 10000000,
        }.items()}
        atoms.update(djcg_primary=("char", 300), djcg_secondary=("char", 400), djcg_goal=("lt", 500), djcg_war=("war", 600))
        if phase == 3:
            atoms.update(djcg_reload_date=("value", 12345600000), djcg_reload_gold=("value", balance), djcg_reload_prestige=("value", balance - 5000000), djcg_reload_piety=("value", balance - 30000000))
        atoms.update(changes or {})
        if standalone:
            for name in ("djcg_setup_date", "djcg_date", "djcg_reload_date"):
                atoms.pop(name, None)
        variables = "\n".join('\t\t\t\t\t{\n\t\t\t\t\t\tflag="' + key + '"\n\t\t\t\t\t\tdata={\n\t\t\t\t\t\t\ttype=' + kind + '\n\t\t\t\t\t\t\tidentity=' + str(value) + '\n\t\t\t\t\t\t}\n\t\t\t\t\t}' for key, (kind, value) in atoms.items())
        text = 'SAV0100\nmeta_data={\n\tversion="1.21.0.3"\n}\n' + ('date=' + physical_date + '\n' if standalone else '') + '\t200={\n\t\tfirst_name="SYNTHETIC_NOT_GAME"\n\t\talive_data={\n\t\t\tvariables={\n\t\t\t\tdata={\n' + variables + '\n\t\t\t\t}\n\t\t\t}\n\t\t}\n\t}\nplayed_character={\n\tcharacter=200\n\tplayer=1\n}\ncurrently_played_characters={\n\t200\n}\n'
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("gamestate", text.encode())

    def gui_command(self, inputs: tuple[Path, Path, Path, Path], report: str) -> subprocess.CompletedProcess[str]:
        before, after, evidence, contract = inputs
        return self.command("verify_fixture_log.py", "--gui-save-before", str(before), "--gui-save-after", str(after), "--gui-evidence", str(evidence), "--gui-contract", str(contract), "--report", str(self.root / report))

    def test_optional_gui_observer_keeps_default_matrix_and_cannot_create_actions(self) -> None:
        plain = self.fixture("duchy")
        inputs = self.gui_inputs()
        companion = inputs[3].parent
        for path in plain.rglob("*"):
            if path.is_file() and path.relative_to(plain).as_posix() != "common/on_action/djct_on_actions.txt":
                self.assertEqual(path.read_bytes(), (companion / path.relative_to(plain)).read_bytes())
        for path in companion.rglob("*.txt"):
            if "djcg" not in path.name:
                continue
            block = parse_clausewitz(path.read_text(encoding="utf-8-sig"))
            forbidden = {"start_war", "end_war", "add_gold", "add_prestige", "add_piety", "save_game", "load_game", "set_player_character", "set_date", "change_title_holder", "remove_character_flag"}
            self.assertFalse({entry.key for nested in walk(block) for entry in nested.entries} & forbidden)
        hook = parse_clausewitz((companion / "common/on_action/djct_on_actions.txt").read_text(encoding="utf-8-sig"))
        player = child(child(child(hook, "djct_initialize"), "effect"), "every_player")
        replay_guard = child(player, "if")
        self.assertEqual(scalar(child(replay_guard, "limit"), "has_variable"), "djct_started")
        self.assertEqual({entry.key for entry in replay_guard.entries}, {"limit", "debug_log"})
        result = self.command("gen_acceptance_fixture.py", "--with-gui-observer", "--output", str(self.root / "invalid-all-gui"))
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / "invalid-all-gui").exists())

    def test_actual_physical_ZIP_GUI_consumer_keeps_exact_money_and_persistent_war(self) -> None:
        inputs = self.gui_inputs()
        result = self.gui_command(inputs, "gui-save-software.json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        value = json.loads((self.root / "gui-save-software.json").read_text())
        money = value["money_raw_decimal_strings"]
        self.assertEqual(money["before_prestige"], "9007199254740993")
        self.assertEqual(money["actual_total_prestige_debit"], "5000000")
        self.assertEqual(money["actual_total_piety_debit"], "30000000")
        self.assertEqual(money["piety_preview"], "20000000")
        self.assertEqual(money["conditional_extra_piety"], "10000000")
        self.assertEqual(value["persisted_references"]["djcg_war"]["raw_identity"], "600")
        self.assertEqual(value["before_save"]["member"]["name"], "gamestate")
        self.assertIn("not a Native", value["fixed_point_codec"])

    def test_GUI_consumer_rejects_preview_forgery_wrong_Load_and_contract_types(self) -> None:
        inputs = self.gui_inputs()
        before, after, evidence, contract = inputs
        original = json.loads(evidence.read_text())
        corruptions: tuple[dict[str, object], ...] = ({"preview_piety": "300"}, {"preview_prestige": 50}, {"preview_piety": True}, {"game_build": True}, {"loaded_save_sha256": "0" * 64}, {"ordinary_gui_declaration": False}, {"load_method": "cold_process_load"}, {"process_after": "202"})
        for index, changes in enumerate(corruptions):
            evidence.write_text(json.dumps(dict(original, **changes)))
            result = self.gui_command(inputs, f"bad-gui-{index}.json")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)
        evidence.write_text(json.dumps(original))
        definition = json.loads(contract.read_text())
        contract.write_text(json.dumps(dict(definition, tier_value=True)))
        result = self.gui_command(inputs, "bad-gui-contract.json")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)

    def test_GUI_consumer_rejects_wrong_physical_phase_money_references_and_ZIP(self) -> None:
        inputs = self.gui_inputs()
        for index, changes in enumerate(({"djcg_phase": ("value", 200000)}, {"djcg_reload_piety": ("value", 1)}, {"djcg_war": ("war", 601)}, {"djcg_date": ("value", 12345600001)}, {"djcg_primary": ("char", 200)}, {"djcg_phase": ("char", 300000)})):
            self.synthetic_gui_save(inputs[1], 3, changes=changes)
            result = self.gui_command(inputs, f"bad-save-{index}.json")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)
        inputs[1].write_bytes(b"not a physical CK3 ZIP")
        result = self.gui_command(inputs, "bad-physical-zip.json")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_single_tier_initializes_only_consumed_matrix_holder_and_clock_state(self) -> None:
        expected_holders = {
            "all": {"djct_capua_holder", "djct_napoli_holder", "djct_roma_holder", "djct_firenze_holder", "djct_owned_holder"},
            "duchy": {"djct_capua_holder", "djct_napoli_holder", "djct_owned_holder"},
            "kingdom": {"djct_capua_holder", "djct_napoli_holder", "djct_owned_holder"},
            "empire": {"djct_capua_holder", "djct_roma_holder", "djct_firenze_holder", "djct_owned_holder"},
        }
        for tier, expected in expected_holders.items():
            fixture = self.fixture(tier)
            declarations: set[str] = set()
            variable_reads: set[str] = set()
            for path in fixture.rglob("*.txt"):
                text = path.read_text(encoding="utf-8-sig")
                # Native var references and has/remove_variable are actual loaded
                # script consumers. Do not add dummy reads to silence the linter.
                variable_reads.update(re.findall(r"var:(djct_[A-Za-z0-9_]+)", text))
                for block in walk(parse_clausewitz(text)):
                    for entry in block.entries:
                        if entry.key == "set_variable" and isinstance(entry.value, Block):
                            name = scalar(entry.value, "name")
                            if name.startswith("djct_"):
                                declarations.add(name)
                        if entry.key in ("has_variable", "remove_variable") and isinstance(entry.value, str):
                            variable_reads.add(entry.value)
            self.assertEqual({name for name in declarations if name.endswith("_holder")}, expected)
            self.assertNotIn("djct_reset_date", declarations)
            self.assertNotIn("djct_ready_date", declarations)
            self.assertTrue(declarations <= variable_reads, (tier, declarations - variable_reads))
        _, _, _, contract = self.gui_inputs()
        definition = json.loads(contract.read_text())
        self.assertIn("djcg_date", definition["base_value_variables"])
        self.assertIn("djcg_reload_date", definition["reload_value_variables"])
        companion = contract.parent
        gui_effects = (companion / "common/scripted_effects/djcg_observer_effects.txt").read_text(encoding="utf-8-sig")
        self.assertIn("name = djcg_date value = current_date", gui_effects)
        self.assertIn("name = djcg_reload_date value = current_date", gui_effects)

    def test_eligibility_diagnostics_are_read_only_and_keep_all_original_tier_predicates(self) -> None:
        plain = self.fixture("kingdom")
        diagnosed = self.root / "diagnosed-kingdom"
        result = self.command("gen_acceptance_fixture.py", "--tier", "kingdom", "--diagnose-eligibility", "--output", str(diagnosed))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        matrices: list[dict[str, Block]] = []
        for fixture in (plain, diagnosed):
            limits: dict[str, Block] = {}
            for event in self.event_definitions(fixture).values():
                for block in walk(event):
                    for entry in block.entries:
                        if entry.key == "debug_log" and isinstance(entry.value, str) and entry.value.startswith('"DJCT: TEST PASS '):
                            limits[entry.value] = child(block, "limit")
            matrices.append(limits)
        self.assertEqual(matrices[0], matrices[1])
        self.assertEqual(len(matrices[1]), 24)
        before = json.loads((plain / "fixture-contract.json").read_text())
        after = json.loads((diagnosed / "fixture-contract.json").read_text())
        self.assertEqual(after.pop("eligibility_failure_probe"), "READONLY-STATE-AND-ON-FAILURE")
        self.assertEqual(before, after)
        helper = diagnosed / "common/scripted_effects/djct_eligibility_probes.txt"
        text = helper.read_text(encoding="utf-8-sig")
        forbidden = {"set_variable", "change_variable", "remove_variable", "add_character_flag", "remove_character_flag", "start_war", "end_war", "change_government", "change_title_holder", "cancel_truce_one_way", "add_stress", "add_gold", "add_piety", "add_prestige", "trigger_event", "save_game", "load_game", "set_date"}
        self.assertFalse({entry.key for block in walk(parse_clausewitz(text)) for entry in block.entries} & forbidden)
        self.assertNotIn("DJCT: TEST PASS", text)
        self.assertNotRegex(text, r"save_(?:temporary_)?scope_as\s*=\s*adventurer")
        for role in ("primary_original", "primary_top", "secondary_original", "secondary_top"):
            self.assertIn(role + "_government_landless_adventurer_government", text)
            self.assertIn(role + "_government_merchant_government", text)
        for predicate in ("root_raised_armies", "root_in_range_primary", "root_owns_goal", "ambient_adventurer_exists", "context_incoming_target_exists", "context_incoming_target_matches_goal", "context_native_before_clear", "control_duchy_native_pre_alias"):
            self.assertIn(predicate, text)
        self.assertIn("stock_UI_group_helpers_omitted_unbound_reserved_scopes", text)
        self.assertNotRegex(text, r"save_(?:temporary_)?scope_as\s*=\s*(?:target|attacker|defender|recipient)(?:\s|})")
        self.assertEqual(3, text.count("debug_log_scopes = yes"))

    def test_probe_only_follows_real_native_failure_and_never_rearms_or_advances(self) -> None:
        target = self.root / "diagnostic-failure-order"
        result = self.command("gen_acceptance_fixture.py", "--tier", "kingdom", "--diagnose-eligibility", "--output", str(target))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        events = self.event_definitions(target)
        for stage, outcome in ((43, "attacker"), (53, "white_peace"), (63, "defender")):
            marker = '"DJCT: TEST PASS kingdom_' + outcome + '_native_eligibility"'
            guards = [block for block in walk(events[f"djct.{stage}"]) if any(entry.key == "debug_log" and entry.value == marker for entry in block.entries)]
            self.assertEqual(len(guards), 1)
            parents = [block for block in walk(events[f"djct.{stage}"]) if any(entry.key == "if" and entry.value == guards[0] for entry in block.entries)]
            self.assertEqual(len(parents), 1)
            failure = child(parents[0], "else")
            keys = [entry.key for entry in failure.entries]
            self.assertEqual(keys, [f"djct_probe_kingdom_{outcome}_failure_effect", "debug_log", "djct_stop_effect"])
            self.assertFalse(any(entry.key == "trigger_event" for block in walk(failure) for entry in block.entries))

    def test_probe_consumer_preserves_failed_native_gate_without_awarding_diagnostic_credit(self) -> None:
        fixture = self.fixture("kingdom")
        log = self.synthetic_log(fixture)
        log.write_text(log.read_text() + 'DJCT: PROBE kingdom_white_peace_root_raised_armies TRUE\nDJCT: PROBE kingdom_white_peace_control_duchy_native_pre_alias FALSE\nDJCT: TEST FAIL kingdom_white_peace_native_eligibility\nDJCT: TEST STOP failed_no_successor\n')
        report = self.root / "probe-is-not-credit.json"
        result = self.command("verify_fixture_log.py", "--log", str(log), "--contract", str(fixture / "fixture-contract.json"), "--report", str(report))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        value = json.loads(report.read_text())
        self.assertEqual(value["result"], "RED")
        self.assertEqual(value["observed_pass_count"], 24)
        self.assertEqual(value["diagnostic_readbacks"]["kingdom_white_peace_root_raised_armies"], [True])
        self.assertEqual(value["diagnostic_readbacks"]["kingdom_white_peace_control_duchy_native_pre_alias"], [False])
        self.assertTrue(any("failure markers" in error for error in value["errors"]))


    def test_target_context_hygiene_is_explicit_and_preserves_all_72_limits(self) -> None:
        plain = self.fixture("all")
        target = self.root / "all-context-hygiene"
        result = self.command("gen_acceptance_fixture.py", "--diagnose-eligibility",
                              "--clear-inherited-target", "--output", str(target))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        matrices: list[dict[str, Block]] = []
        for fixture in (plain, target):
            limits: dict[str, Block] = {}
            for event in self.event_definitions(fixture).values():
                for block in walk(event):
                    for entry in block.entries:
                        if entry.key == "debug_log" and isinstance(entry.value, str) and entry.value.startswith('"DJCT: TEST PASS '):
                            limits[entry.value] = child(block, "limit")
            matrices.append(limits)
        self.assertEqual(matrices[0], matrices[1])
        self.assertEqual(72, len(matrices[1]))
        contract = json.loads((target / "fixture-contract.json").read_text())
        self.assertEqual("CLEAR-INHERITED-TARGET-BEFORE-NATIVE", contract["event_target_context"])
        helper = (target / "common/scripted_effects/djct_eligibility_probes.txt").read_text(encoding="utf-8-sig")
        self.assertEqual(9, helper.count("clear_saved_scope = target"))
        aliases = re.findall(r"save_temporary_scope_as\s*=\s*(\w+)", helper)
        self.assertTrue(aliases)
        self.assertTrue(all(alias.startswith("djct_probe_frame_") for alias in aliases))
        self.assertNotIn("save_scope_as =", helper)
        self.assertNotRegex(helper, r"clear_saved_scope\s*=\s*(?!target\b)\w+")
        for suffix in ("context_identity_before_clear", "context_identity_after_clear",
                       "context_native_before_clear", "context_native_after_clear",
                       "context_identity_after_native_query", "context_target_exists_after_clear"):
            self.assertIn("kingdom_white_peace_" + suffix, helper)

    def test_context_clear_requires_diagnosis_before_any_output(self) -> None:
        target = self.root / "not-admitted-context-clear"
        result = self.command("gen_acceptance_fixture.py", "--tier", "kingdom",
                              "--clear-inherited-target", "--output", str(target))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("requires --diagnose-eligibility", result.stderr)
        self.assertFalse(target.exists())

    def test_hygiene_consumer_requires_real_paired_readbacks_without_extra_pass_credit(self) -> None:
        target = self.root / "context-consumer"
        result = self.command("gen_acceptance_fixture.py", "--tier", "kingdom", "--diagnose-eligibility",
                              "--clear-inherited-target", "--output", str(target))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        log = self.synthetic_log(target)
        report = self.root / "context-report.json"
        args = ("--log", str(log), "--contract", str(target / "fixture-contract.json"))
        self.assertEqual(1, self.command("verify_fixture_log.py", *args, "--report", str(self.root / "missing-context-report.json")).returncode)
        original = log.read_text()
        readbacks = []
        for outcome in ("attacker", "white_peace", "defender"):
            label = "kingdom_" + outcome
            for suffix, truth in (("context_identity_before_clear", True),
                ("context_identity_after_clear", True), ("context_target_exists_after_clear", False),
                ("context_native_after_clear", True), ("context_identity_after_native_query", True),
                ("context_native_before_clear", outcome == "attacker")):
                readbacks.append(f"DJCT: PROBE {label}_{suffix} {str(truth).upper()}\n")
        log.write_text(original + "".join(readbacks))
        checked = self.command("verify_fixture_log.py", *args, "--report", str(report))
        self.assertEqual(0, checked.returncode, checked.stdout + checked.stderr)
        value = json.loads(report.read_text())
        self.assertTrue(value["target_context_hygiene"])
        self.assertEqual(24, value["observed_pass_count"])
        self.assertEqual([False], value["diagnostic_readbacks"]["kingdom_white_peace_context_native_before_clear"])
        log.write_text(log.read_text().replace("kingdom_white_peace_context_target_exists_after_clear FALSE",
                                              "kingdom_white_peace_context_target_exists_after_clear TRUE"))
        self.assertEqual(1, self.command("verify_fixture_log.py", *args, "--report", str(self.root / "bad-context-report.json")).returncode)

    def standalone_atoms(self) -> dict[str, tuple[str, int]]:
        return {"djcg_standalone": ("value", 100000),
                "djcg_setup_prestige": ("value", 9007199254740993), "djcg_setup_piety": ("value", 9007199254740993),
                "djcg_setup_goal": ("lt", 500), "djcg_setup_capua_title": ("lt", 501), "djcg_setup_napoli_title": ("lt", 502),
                "djcg_setup_primary": ("char", 300), "djcg_setup_secondary": ("char", 400)}

    def standalone_inputs(self) -> tuple[Path, Path, Path, Path]:
        before, after, evidence, _ = self.gui_inputs()
        fixture = self.root / "standalone-ordinary"
        result = self.command("gen_acceptance_fixture.py", "--tier", "duchy", "--ordinary-gui-only", "--saved-entry-bridge", "--output", str(fixture))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        fields = self.standalone_atoms()
        self.synthetic_gui_save(before, 2, changes=fields, standalone=True)
        self.synthetic_gui_save(after, 3, changes=fields, standalone=True)
        initial = self.root / "SYNTHETIC-INITIAL-SOURCE.ck3"
        initial.write_bytes(b"Synthetic source-pin unit input; never an actual Game or decoded-world proof.")
        stat = initial.stat()
        value = json.loads(evidence.read_bytes())
        value.update(schema="djc.gui-standalone-physical-save-evidence.v2", same_completed_matrix_world=False,
                     fresh_source_setup_world=True, setup_action_actual=True,
                     load_method="cold_process_load", process_after="202",
                     loaded_save_sha256=hashlib.sha256(before.read_bytes()).hexdigest(),
                     initial_source_save={"path": str(initial), "bytes": stat.st_size, "sha256": hashlib.sha256(initial.read_bytes()).hexdigest(), "file_id": str(stat.st_ino), "mtime_ns": str(stat.st_mtime_ns)})
        for kind in ("setup_action", "process_lifecycle"):
            path = self.root / ("SYNTHETIC-NOT-GAME-" + kind + ".txt")
            path.write_text("Synthetic software artifact only: " + kind)
            value["artifacts"].append({"kind": kind, "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        evidence.write_text(json.dumps(value), encoding="utf-8")
        return before, after, evidence, fixture / "gui-observer-contract.json"

    def test_standalone_setup_has_no_matrix_war_truce_or_calendar_actions(self) -> None:
        _, _, _, contract = self.standalone_inputs()
        fixture = contract.parent
        self.assertFalse((fixture / "fixture-contract.json").exists())
        self.assertFalse((fixture / "common/on_action").exists())
        all_text = "\n".join(p.read_text(encoding="utf-8-sig") for p in fixture.rglob("*.txt"))
        self.assertNotIn("djct_", all_text)
        self.assertNotIn("DJCT: TEST PASS", all_text)
        for path in fixture.rglob("*.yml"):
            self.assertNotIn("After this tier really finishes", path.read_text(encoding="utf-8-sig"))
            self.assertNotIn("cancel only its directed fixture truce", path.read_text(encoding="utf-8-sig"))
        forbidden = {"start_war", "end_war", "cancel_truce_one_way", "change_title_holder", "change_government", "save_game", "load_game", "set_player_character", "set_date", "add_gold", "days", "hours"}
        nodes = [block for path in fixture.rglob("*.txt") for block in walk(parse_clausewitz(path.read_text(encoding="utf-8-sig")))]
        self.assertFalse({e.key for block in nodes for e in block.entries} & forbidden)
        events = parse_clausewitz((fixture / "events/djcg_observer_events.txt").read_text(encoding="utf-8-sig"))
        setup = child(child(events, "djcg.1"), "immediate")
        guarded = child(setup, "if")
        limit = child(guarded, "limit")
        self.assertEqual(scalar(limit, "this"), "character:1128")
        self.assertEqual(scalar(limit, "current_date"), "1066.9.15")
        not_blocks = [e.value for e in limit.entries if e.key == "NOT" and isinstance(e.value, Block)]
        self.assertTrue(any(any(e.key == "has_variable" and e.value == "djcg_standalone" for e in block.entries) for block in not_blocks))
        self.assertEqual(scalar(guarded, "add_prestige"), "100000")
        self.assertEqual(scalar(guarded, "add_piety"), "100000")
        self.assertEqual(scalar(guarded, "add_prestige_level"), "5")
        resources = [(block, e.key) for block in nodes for e in block.entries if e.key in {"add_prestige", "add_piety", "add_prestige_level"}]
        self.assertEqual(len(resources), 3)
        self.assertTrue(all(block == guarded for block, _ in resources))
        self.assertEqual(all_text.count("clear_saved_scope = target"), 1)
        metadata = json.loads(contract.read_bytes())
        self.assertIs(metadata["same_completed_matrix_world_required"], False)
        self.assertIs(metadata["matrix_pass_credit"], False)

    def test_standalone_cli_rejects_mixed_or_other_tier_modes_before_output(self) -> None:
        variants = (("--ordinary-gui-only",), ("--ordinary-gui-only", "--tier", "kingdom"),
                    ("--ordinary-gui-only", "--tier", "duchy", "--with-gui-observer"),
                    ("--ordinary-gui-only", "--tier", "duchy", "--diagnose-eligibility"),
                    ("--ordinary-gui-only", "--tier", "duchy", "--clear-inherited-target"))
        for i, args in enumerate(variants):
            target = self.root / f"invalid-standalone-{i}"
            result = self.command("gen_acceptance_fixture.py", *args, "--output", str(target))
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertFalse(target.exists())

    def test_standalone_physical_consumer_records_actual_mode_setup_and_coldload(self) -> None:
        inputs = self.standalone_inputs()
        result = self.gui_command(inputs, "standalone-good.json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads((self.root / "standalone-good.json").read_bytes())
        self.assertEqual(report["source_mode"], "standalone-ordinary-only")
        self.assertEqual(report["load_method"], "cold_process_load")
        self.assertEqual(report["money_raw_decimal_strings"]["actual_total_piety_debit"], "30000000")
        self.assertEqual(report["money_raw_decimal_strings"]["actual_total_gold_debit"], "0")
        self.assertEqual(report["persisted_references"]["djcg_goal"]["raw_identity"], "500")
        self.assertIn("no completed-matrix credit", report["boundary"])

    def test_standalone_consumer_rejects_v1_masquerade_and_false_setup_contracts(self) -> None:
        inputs = self.standalone_inputs()
        original = json.loads(inputs[3].read_bytes())
        corruptions: tuple[dict[str, object], ...] = (
            {"schema": "djc.gui-ordinary-save.v1"}, {"same_completed_matrix_world_required": True},
            {"standalone_setup_required": False}, {"matrix_pass_credit": True}, {"fresh_start_date": "1066.9.16"},
            {"standalone_value_variables": []}, {"setup_resources": {"prestige": True, "piety": 100000, "prestige_level": 5}})
        for i, replacement in enumerate(corruptions):
            inputs[3].write_text(json.dumps(dict(original, **replacement)))
            result = self.gui_command(inputs, f"standalone-bad-contract-{i}.json")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_standalone_consumer_rejects_missing_real_setup_and_changed_initial_pin(self) -> None:
        inputs = self.standalone_inputs()
        original = json.loads(inputs[2].read_bytes())
        variants: tuple[dict[str, object], ...] = ({"same_completed_matrix_world": True}, {"fresh_source_setup_world": False},
            {"setup_action_actual": False}, {"initial_source_save": {}}, {"schema": "djc.gui-physical-save-evidence.v1"})
        for i, replacement in enumerate(variants):
            inputs[2].write_text(json.dumps(dict(original, **replacement)))
            result = self.gui_command(inputs, f"standalone-bad-source-{i}.json")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        inputs[2].write_text(json.dumps(original))
        initial = Path(original["initial_source_save"]["path"])
        initial.write_bytes(initial.read_bytes() + b" changed")
        self.assertEqual(self.gui_command(inputs, "standalone-mutated-initial.json").returncode, 1)

    def test_standalone_consumer_rejects_old_mode_wrong_war_type_and_changed_setup_money(self) -> None:
        inputs = self.standalone_inputs()
        fields = self.standalone_atoms()
        for i, wrong in enumerate(({"djcg_standalone": ("value", 0)}, {"djcg_setup_piety": ("value", 1)},
                                   {"djcg_war": ("char", 600)}, {"djcg_goal": ("char", 500)}, {"djcg_setup_goal": ("lt", 501)}, {"djcg_setup_primary": ("char", 401)})):
            self.synthetic_gui_save(inputs[1], 3, changes=dict(fields, **wrong), standalone=True)
            result = self.gui_command(inputs, f"standalone-bad-point-{i}.json")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_standalone_consumer_reports_unexpected_gold_debit_without_rounding(self) -> None:
        inputs = self.standalone_inputs()
        fields = dict(self.standalone_atoms(), djcg_after_gold=("value", 9007199254740992), djcg_reload_gold=("value", 9007199254740992))
        self.synthetic_gui_save(inputs[0], 2, changes=fields, standalone=True)
        self.synthetic_gui_save(inputs[1], 3, changes=fields, standalone=True)
        evidence = json.loads(inputs[2].read_bytes())
        evidence["loaded_save_sha256"] = hashlib.sha256(inputs[0].read_bytes()).hexdigest()
        inputs[2].write_text(json.dumps(evidence))
        result = self.gui_command(inputs, "standalone-gold-debit.json")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        report = json.loads((self.root / "standalone-gold-debit.json").read_bytes())
        self.assertEqual(report["money_raw_decimal_strings"]["actual_total_gold_debit"], "1")
        self.assertIn("gold changed", report["errors"][0])

    def test_standalone_consumer_rejects_same_file_hardlink_save_pair(self) -> None:
        inputs = self.standalone_inputs()
        alias = self.root / "SYNTHETIC-S1-hardlink.ck3"
        os.link(inputs[0], alias)
        result = self.gui_command((inputs[0], alias, inputs[2], inputs[3]), "standalone-hardlink.json")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("same file/hardlink", (self.root / "standalone-hardlink.json").read_text())

    def test_saved_entry_bridge_is_explicit_guarded_once_and_skips_captured_S0(self) -> None:
        inputs = self.standalone_inputs()
        fixture = inputs[3].parent
        scripted = parse_clausewitz((fixture / "common/scripted_guis/djcg_saved_entry_guis.txt").read_text(encoding="utf-8-sig"))
        gui = child(scripted, "djcg_saved_entry_gui")
        shown = child(gui, "is_shown")
        dispatched = child(child(gui, "effect"), "if")
        limit = child(dispatched, "limit")
        self.assertEqual(shown, limit)
        self.assertEqual(scalar(limit, "this"), "character:1128")
        self.assertEqual(scalar(limit, "current_date"), "1066.9.15")
        self.assertEqual(scalar(limit, "is_ai"), "no")
        self.assertEqual(scalar(limit, "is_alive"), "yes")
        blocked = {e.value for b in walk(limit) for e in b.entries if e.key in {"has_character_flag", "has_variable"}}
        self.assertEqual(blocked, {"djcg_saved_entry_dispatched", "djcg_standalone"})
        keys = [e.key for e in dispatched.entries]
        self.assertEqual(keys, ["limit", "add_character_flag", "trigger_event"])
        self.assertEqual(scalar(dispatched, "trigger_event"), "djcg.1")
        widget = (fixture / "gui/scripted_widgets/djcg_saved_entry_widgets.txt").read_text(encoding="utf-8-sig")
        self.assertEqual(widget.strip(), "gui/djcg_saved_entry_bridge.gui = djcg_saved_entry_bridge_window")
        bridge = (fixture / "gui/djcg_saved_entry_bridge.gui").read_text(encoding="utf-8-sig")
        self.assertIn("GuiScope.SetRoot( GetPlayer.MakeScope ).End", bridge)
        self.assertIn("GetScriptedGui('djcg_saved_entry_gui').Execute", bridge)
        invalid = self.root / "invalid-bridge-only"
        self.assertEqual(self.command("gen_acceptance_fixture.py", "--saved-entry-bridge", "--output", str(invalid)).returncode, 2)
        self.assertFalse(invalid.exists())

    def test_standalone_date_operands_are_literals_and_saved_date_variables_are_absent(self) -> None:
        inputs = self.standalone_inputs()
        fixture = inputs[3].parent
        for path in fixture.rglob("*.txt"):
            for block in walk(parse_clausewitz(path.read_text(encoding="utf-8-sig"))):
                for entry in block.entries:
                    if entry.key == "current_date":self.assertEqual(entry.value, "1066.9.15")
                    if entry.key == "set_variable" and isinstance(entry.value, Block):
                        self.assertNotIn(scalar(entry.value, "name"), {"djcg_date", "djcg_setup_date", "djcg_reload_date"})
        definition = json.loads(inputs[3].read_bytes())
        self.assertEqual(definition["schema"], "djc.gui-ordinary-standalone-save.v2")
        self.assertTrue(definition["saved_entry_bridge"])
        self.assertNotIn("djcg_date", definition["base_value_variables"])

    def test_standalone_physical_date_mismatch_or_nested_fake_does_not_pass(self) -> None:
        inputs = self.standalone_inputs()
        for i, date in enumerate(("1066.9.16", "1066.9.15\ndate=1066.9.15", '"1066.9.15"\nnoise={ date=1066.9.16 }\ndate=1066.9.16')):
            self.synthetic_gui_save(inputs[1], 3, changes=self.standalone_atoms(), standalone=True, physical_date=date)
            result = self.gui_command(inputs, f"invalid-physical-date-{i}.json")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("physical root date", (self.root / f"invalid-physical-date-{i}.json").read_text())

    def test_hygiene_contract_rejects_false_or_unpaired_mode(self) -> None:
        fixture = self.fixture("kingdom")
        path = fixture / "fixture-contract.json"
        raw = json.loads(path.read_text())
        log = self.synthetic_log(fixture)
        for index, replacement in enumerate((True, False, None, "CLEAR", "CLEAR-INHERITED-TARGET-BEFORE-NATIVE")):
            with self.subTest(value=replacement):
                path.write_text(json.dumps({**raw, "event_target_context": replacement}))
                report = self.root / f"bad-contract-{index}.json"
                result = self.command("verify_fixture_log.py", "--log", str(log), "--contract", str(path), "--report", str(report))
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                value = json.loads(report.read_text())
                self.assertEqual("fixture-input-rejected", value["layer"])
                self.assertIn("event_target_context", value["errors"][0])


if __name__ == "__main__":
    unittest.main()
