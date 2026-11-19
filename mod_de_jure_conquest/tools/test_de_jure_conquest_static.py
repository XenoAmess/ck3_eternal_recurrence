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

    def synthetic_gui_save(self, path: Path, phase: int, *, changes: dict[str, tuple[str, int]] | None = None) -> None:
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
        variables = "\n".join('\t\t\t\t\t{\n\t\t\t\t\t\tflag="' + key + '"\n\t\t\t\t\t\tdata={\n\t\t\t\t\t\t\ttype=' + kind + '\n\t\t\t\t\t\t\tidentity=' + str(value) + '\n\t\t\t\t\t\t}\n\t\t\t\t\t}' for key, (kind, value) in atoms.items())
        text = 'SAV0100\nmeta_data={\n\tversion="1.21.0.3"\n}\n\t200={\n\t\tfirst_name="SYNTHETIC_NOT_GAME"\n\t\talive_data={\n\t\t\tvariables={\n\t\t\t\tdata={\n' + variables + '\n\t\t\t\t}\n\t\t\t}\n\t\t}\n\t}\nplayed_character={\n\tcharacter=200\n\tplayer=1\n}\ncurrently_played_characters={\n\t200\n}\n'
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


if __name__ == "__main__":
    unittest.main()
