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

    def test_missing_ticking_rate_fails_for_each_de_jure_tier(self) -> None:
        for tier in ("duchy", "kingdom", "empire"):
            with self.subTest(tier=tier):
                cb = self.product / f"common/casus_belli_types/{tier}_de_jure_greatwar.txt"
                original = cb.read_bytes()
                rate = b"\tattacker_ticking_warscore = 0.055\n"
                self.assertEqual(original.count(rate), 1)
                cb.write_bytes(original.replace(rate, b""))
                result = self.command("validate_static.py", "--no-installed-game")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(f"{tier}.attacker_ticking_warscore must explicitly preserve 0.055 per day", result.stdout)
                cb.write_bytes(original)

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

    def physical_pin(self, path: Path) -> dict[str, object]:
        data, stat = path.read_bytes(), path.stat()
        return {"path": str(path.resolve()), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                "file_id": str(stat.st_ino), "mtime_ns": str(stat.st_mtime_ns)}

    def physical_atoms(self, *, captured: bool) -> dict[str, tuple[str, int]]:
        # Private synthetic saved data, not a game, Native oracle or live proof.
        balance = 9007199254740993
        atoms = self.standalone_atoms()
        atoms.update({key: ("value", value) for key, value in {
            "djcg_tier": 100000, "djcg_physical": 100000, "djcg_setup_gold": balance,
            "djcg_same_faith": 100000, "djcg_peace_of_god": 100000,
            "djcg_expected_extra_piety": 10000000}.items()})
        if captured:
            atoms.update({key: ("value", value) for key, value in {
                "djcg_physical_captured": 100000, "djcg_war_count": 100000,
                "djcg_after_gold": balance, "djcg_after_prestige": balance - 5000000,
                "djcg_after_piety": balance - 30000000}.items()})
            atoms.update(djcg_war=("war", 600), djcg_actual_goal=("lt", 500),
                         djcg_actual_attacker=("char", 200), djcg_actual_primary=("char", 300),
                         djcg_actual_secondary=("char", 400))
        return atoms

    def synthetic_physical_save(self, path: Path, *, captured: bool, changes: dict[str, tuple[str, int]] | None = None, omit: str | None = None) -> None:
        atoms = self.physical_atoms(captured=captured)
        atoms.update(changes or {})
        if omit is not None:atoms.pop(omit, None)
        entries = "\n".join('\t\t\t\t\t{\n\t\t\t\t\t\tflag="' + key + '"\n\t\t\t\t\t\tdata={\n\t\t\t\t\t\t\ttype=' + kind + '\n\t\t\t\t\t\t\tidentity=' + str(value) + '\n\t\t\t\t\t\t}\n\t\t\t\t\t}' for key, (kind, value) in atoms.items())
        text = 'SAV0100\nmeta_data={\n\tversion="1.21.0.3"\n}\ndate=1066.9.15\n\t200={\n\t\tfirst_name="SYNTHETIC_NOT_GAME"\n\t\talive_data={\n\t\t\tvariables={\n\t\t\t\tdata={\n' + entries + '\n\t\t\t\t}\n\t\t\t}\n\t\t}\n\t}\nplayed_character={\n\tcharacter=200\n\tplayer=1\n}\ncurrently_played_characters={\n\t200\n}\n'
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("gamestate", text)

    def physical_inputs(self) -> tuple[Path, Path, Path, Path]:
        fixture = self.root / "physical-observer"
        emitted = self.command("gen_acceptance_fixture.py", "--tier", "duchy", "--ordinary-gui-only", "--saved-entry-bridge", "--physical-only-observer", "--output", str(fixture))
        self.assertEqual(emitted.returncode, 0, emitted.stdout + emitted.stderr)
        s0, s1 = self.root / "SYNTHETIC-S0.ck3", self.root / "SYNTHETIC-S1.ck3"
        self.synthetic_physical_save(s0, captured=False)
        self.synthetic_physical_save(s1, captured=True)
        # Synthetic negative/consumer parser input only. This matches the known
        # wire shape but is never a C++ serializer oracle or live qualification.
        primary = SUPPORT.resolve().parent
        dispatch = {
            "schema": "ck3.djc_declaration_ui.current267_result.v1", "game_version": "1.21.0.3",
            "executable_sha256": "859F0D380098ADCB130EB9D453458222749FCDF6D46126AD0ED99D78F9A0AA28",
            "adapter_id": "ck3-1.21.0.3-26785313-msvc-x64", "backend": "ck3-1.21.0.3-native-application-main-djc-ui",
            "step": "send-current-djc-declaration-ui-v1", "action": "send_ui", "status": "send_dispatched",
            "source_available": True, "effect_attempted": True, "native_returned": True, "native_handled": True,
            "cleanup_known": True, "provider_generation": "1", "query_sequence": "1", "claim_sequence": "1",
            "facts_before": {"date_raw": 123456, "speed": 1, "paused": True, "local_player_id": 0,
                "map_ready": True, "has_played_character": True, "played_character_id": 200, "played_character_alive": True},
            "owner_witness": {"connection_generation": "1", "ticket_sequence": "1", "pump_epoch": "1", "thread_id": 1},
            "source": {"schema": "ck3.djc_declaration_ui.current267_source.v1", "target_character_id": 300,
                "cb_key": "duchy_de_jure_greatwar", "actor_id": 200, "recipient_id": 300,
                "selected": {"cb_key": "duchy_de_jure_greatwar", "claimant_character_id": -1,
                    "target_title_ids": [500], "extra_configuration_ids": [-16777215, -16777215], "source_row_enabled": True}},
            "addresses_redacted": True, "submitted": False, "war_created": False, "payment_confirmed": False,
            "physical_save_confirmed": False, "war_id": None, "total_debit": None, "unavailable_reason": None}
        core = json.loads((primary / "java/ck3-control/native-transport/src/test/resources/native26785313/core-producer-partial.json").read_bytes())
        core.update(date_raw=123456, played_character_id=200)
        lifecycle = {"schema": "djc.physical-load-lifecycle.v1", "process_ids": ["101", "202", "303"],
            "S0_sha256": hashlib.sha256(s0.read_bytes()).hexdigest(), "loaded_save_sha256": hashlib.sha256(s1.read_bytes()).hexdigest(),
            "physical_S0_confirmed": True, "physical_S1_confirmed": True, "cold_loaded": True}
        contents = {"native_dispatch": json.dumps(dispatch), "cold_core": json.dumps(core),
            "cold_log": "DJCG: PHYSICAL READBACK MATCH war_goal_participants_resources\n",
            "load_lifecycle": json.dumps(lifecycle), "setup_action": "DJCG: SETUP standalone_resources_before_business_observation\n",
            "observer_source": "SYNTHETIC source-adoption unit record only", "initial_source_save": "SYNTHETIC B0 Pin only"}
        contract = fixture / "gui-observer-contract.json"
        value: dict[str, object] = {"schema": "djc.physical-ordinary-evidence.v1", "machine_id": "desktop-3fevhd2-1c74096080",
            "game_version": "1.21.0.3", "game_build": 26785313,
            "exe_sha256": "859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28",
            "ordinary_native_ui": True, "cold_load_exact_s1": True, "process_ids": ["101", "202", "303"],
            "loaded_save_sha256": hashlib.sha256(s1.read_bytes()).hexdigest(),
            "observer_contract_sha256": hashlib.sha256(contract.read_bytes()).hexdigest()}
        for key, content in contents.items():
            path = self.root / ("SYNTHETIC-" + key + ".json")
            path.write_text(content, encoding="utf-8")
            value[key] = self.physical_pin(path)
        evidence = self.root / "SYNTHETIC-physical-evidence.json"
        evidence.write_text(json.dumps(value), encoding="utf-8")
        return s0, s1, evidence, contract

    def physical_command(self, inputs: tuple[Path, Path, Path, Path], report: str) -> subprocess.CompletedProcess[str]:
        return self.command("verify_fixture_log.py", "--physical-s0", str(inputs[0]), "--physical-s1", str(inputs[1]),
                            "--physical-evidence", str(inputs[2]), "--physical-contract", str(inputs[3]), "--report", str(self.root / report))

    def update_physical_artifact(self, inputs: tuple[Path, Path, Path, Path], key: str, changes: dict[str, object]) -> None:
        evidence = json.loads(inputs[2].read_bytes())
        path = Path(evidence[key]["path"])
        value = json.loads(path.read_bytes())
        value.update(changes)
        path.write_text(json.dumps(value), encoding="utf-8")
        evidence[key] = self.physical_pin(path)
        inputs[2].write_text(json.dumps(evidence), encoding="utf-8")

    def test_physical_only_passive_dynamic_states_have_real_war_and_once_guards(self) -> None:
        inputs = self.physical_inputs()
        fixture = inputs[3].parent
        self.assertFalse((fixture / "common/decisions").exists())
        events = parse_clausewitz((fixture / "events/djcg_observer_events.txt").read_text(encoding="utf-8-sig"))
        self.assertEqual({e.key for e in events.entries}, {"namespace", "djcg.1", "djcg.900"})
        setup = child(events, "djcg.1")
        self.assertEqual(scalar(setup, "hidden"), "yes")
        self.assertFalse({e.key for e in setup.entries} & {"option", "theme", "title", "desc"})
        scripted = parse_clausewitz((fixture / "common/scripted_guis/djcg_saved_entry_guis.txt").read_text(encoding="utf-8-sig"))
        capture = child(scripted, "djcg_saved_war_capture_gui")
        actual = child(child(capture, "effect"), "if")
        self.assertEqual(child(capture, "is_shown"), child(actual, "limit"))
        self.assertEqual([e.key for e in actual.entries], ["limit", "add_character_flag", "djcg_capture_physical_war_effect"])
        self.assertEqual(scalar(child(child(actual, "limit"), "any_character_war"), "djcg_physical_war_trigger"), "yes")
        bridge = parse_clausewitz((fixture / "gui/djcg_saved_entry_bridge.gui").read_text(encoding="utf-8-sig"))
        states = [b for b in walk(bridge) if any(e.key == "trigger_when" for e in b.entries)]
        self.assertEqual(len(states), 3)
        self.assertTrue(all(any(e.key == "on_start" for e in b.entries) for b in states))
        effect = (fixture / "common/scripted_effects/djcg_observer_effects.txt").read_text(encoding="utf-8-sig")
        readback = child(parse_clausewitz(effect), "djcg_physical_readback_effect")
        self.assertFalse({e.key for b in walk(readback) for e in b.entries} & {"set_variable", "add_character_flag", "trigger_event"})
        for path in fixture.rglob("*.txt"):
            keys = {e.key for b in walk(parse_clausewitz(path.read_text(encoding="utf-8-sig"))) for e in b.entries}
            self.assertFalse(keys & {"start_war", "end_war", "save_game", "load_game", "set_date", "change_title_holder"})
        self.assertNotIn("current_date = var:", effect)

    def test_physical_only_S0_S1_needs_no_phase2_phase3_and_preserves_large_integer_debit(self) -> None:
        inputs = self.physical_inputs()
        result = self.physical_command(inputs, "physical-good.json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads((self.root / "physical-good.json").read_bytes())
        self.assertEqual(report["actual_total_debit_saved_raw"], {"gold": "0", "prestige": "5000000", "piety": "30000000"})
        self.assertEqual(report["price_preview_comparison"], "NOT_RUN")
        self.assertIn("not an independent full War-table AST", report["boundary"])
        self.assertEqual(report["native_selected_tuple"]["extra_configuration_ids"], [-16777215, -16777215])

    def test_physical_only_missing_real_war_or_fake_phase_does_not_pass(self) -> None:
        inputs = self.physical_inputs()
        for i, omit in enumerate(("djcg_war", "djcg_actual_goal", "djcg_actual_secondary", "djcg_after_prestige")):
            self.synthetic_physical_save(inputs[1], captured=True, omit=omit, changes={"djcg_phase": ("value", 300000)})
            result = self.physical_command(inputs, f"physical-missing-{i}.json")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("phase alone is insufficient", result.stdout)

    def test_physical_only_wrong_actor_goal_resource_and_war_type_are_rejected(self) -> None:
        inputs = self.physical_inputs()
        cases = ({"djcg_actual_attacker": ("char", 999)}, {"djcg_actual_goal": ("lt", 501)},
                 {"djcg_actual_secondary": ("char", 300)}, {"djcg_war": ("value", 600)},
                 {"djcg_war_count": ("value", 200000)})
        for i, changes in enumerate(cases):
            self.synthetic_physical_save(inputs[1], captured=True, changes=changes)
            self.assertEqual(self.physical_command(inputs, f"physical-wrong-{i}.json").returncode, 1)

    def test_physical_only_cold_marker_or_Core_cannot_substitute_native_effect(self) -> None:
        cases: tuple[dict[str, object], ...] = ({"effect_attempted": False}, {"status": "available"}, {"war_id": 600}, {"total_debit": "300"})
        for i, change in enumerate(cases):
            inputs = self.physical_inputs()
            self.update_physical_artifact(inputs, "native_dispatch", change)
            self.assertEqual(self.physical_command(inputs, f"physical-bad-dispatch-{i}.json").returncode, 1)
            shutil.rmtree(inputs[3].parent)

    def test_physical_only_actual_cold_Core_and_exact_Load_are_required(self) -> None:
        cases: tuple[dict[str, object], ...] = ({"date_raw": 123457}, {"played_character_id": 999}, {"paused": False}, {"core_available": False})
        for i, change in enumerate(cases):
            inputs = self.physical_inputs()
            self.update_physical_artifact(inputs, "cold_core", change)
            self.assertEqual(self.physical_command(inputs, f"physical-bad-core-{i}.json").returncode, 1)
            shutil.rmtree(inputs[3].parent)
        inputs = self.physical_inputs()
        self.update_physical_artifact(inputs, "load_lifecycle", {"loaded_save_sha256": "0" * 64})
        self.assertEqual(self.physical_command(inputs, "physical-false-load.json").returncode, 1)

    def test_physical_only_rejects_changed_pin_hardlink_and_false_match_log(self) -> None:
        inputs = self.physical_inputs()
        evidence = json.loads(inputs[2].read_bytes())
        log = Path(evidence["cold_log"]["path"])
        log.write_text("DJCG: PHYSICAL READBACK FAIL current_war_or_resources\n")
        self.assertEqual(self.physical_command(inputs, "physical-pin-changed.json").returncode, 1)
        evidence["cold_log"] = self.physical_pin(log)
        inputs[2].write_text(json.dumps(evidence))
        self.assertEqual(self.physical_command(inputs, "physical-actual-fail.json").returncode, 1)
        alias = self.root / "S0-alias.ck3"
        os.link(inputs[0], alias)
        self.assertEqual(self.physical_command((inputs[0], alias, inputs[2], inputs[3]), "physical-hardlink.json").returncode, 1)

    def test_physical_only_rejects_cli_mix_and_keeps_default_standalone_contract(self) -> None:
        for i, args in enumerate((("--physical-only-observer",), ("--ordinary-gui-only", "--tier", "duchy", "--physical-only-observer"))):
            target = self.root / f"bad-physical-cli-{i}"
            self.assertEqual(self.command("gen_acceptance_fixture.py", *args, "--output", str(target)).returncode, 2)
            self.assertFalse(target.exists())
        fixture = self.root / "old-standalone"
        self.assertEqual(self.command("gen_acceptance_fixture.py", "--ordinary-gui-only", "--tier", "duchy", "--saved-entry-bridge", "--output", str(fixture)).returncode, 0)
        self.assertEqual(json.loads((fixture / "gui-observer-contract.json").read_bytes())["schema"], "djc.gui-ordinary-standalone-save.v2")

    def refresh_physical_s1(self, inputs: tuple[Path, Path, Path, Path]) -> None:
        evidence = json.loads(inputs[2].read_bytes())
        digest = hashlib.sha256(inputs[1].read_bytes()).hexdigest()
        evidence["loaded_save_sha256"] = digest
        path = Path(evidence["load_lifecycle"]["path"])
        record = json.loads(path.read_bytes())
        record["loaded_save_sha256"] = digest
        path.write_text(json.dumps(record))
        evidence["load_lifecycle"] = self.physical_pin(path)
        inputs[2].write_text(json.dumps(evidence))

    def test_physical_only_real_resource_delta_not_Core_or_phase_proves_charge(self) -> None:
        inputs = self.physical_inputs()
        cases = ({"djcg_after_gold": ("value", 9007199254740992)},
                 {"djcg_after_prestige": ("value", 9007199254740994)},
                 {"djcg_after_piety": ("value", 9007199254740993)})
        for i, changes in enumerate(cases):
            self.synthetic_physical_save(inputs[1], captured=True, changes=changes)
            self.refresh_physical_s1(inputs)
            result = self.physical_command(inputs, f"physical-money-{i}.json")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertNotIn("input-rejected", result.stdout)
            self.assertIn("debit", result.stdout)

    def test_physical_only_optional_real_preview_retains_exact_five_decimal_money(self) -> None:
        inputs = self.physical_inputs()
        evidence = json.loads(inputs[2].read_bytes())
        path = self.root / "SYNTHETIC-preview.txt"
        path.write_text("Synthetic preview unit evidence only")
        evidence["preview"] = {"artifact": self.physical_pin(path), "prestige": "50", "piety": "200"}
        inputs[2].write_text(json.dumps(evidence))
        good = self.physical_command(inputs, "physical-preview-good.json")
        self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
        self.assertIn('"price_preview_comparison": "OBSERVED"', good.stdout)
        evidence["preview"]["prestige"] = "50.00001"
        inputs[2].write_text(json.dumps(evidence))
        bad = self.physical_command(inputs, "physical-preview-bad.json")
        self.assertEqual(bad.returncode, 1, bad.stdout + bad.stderr)
        self.assertIn("differs from supplied genuine preview", bad.stdout)

    def test_physical_only_duplicate_native_JSON_and_false_Save_proof_are_rejected(self) -> None:
        inputs = self.physical_inputs()
        evidence = json.loads(inputs[2].read_bytes())
        path = Path(evidence["native_dispatch"]["path"])
        raw = path.read_text()
        path.write_text(raw[:-1] + ',"effect_attempted":true}')
        evidence["native_dispatch"] = self.physical_pin(path)
        inputs[2].write_text(json.dumps(evidence))
        duplicate = self.physical_command(inputs, "physical-duplicate.json")
        self.assertEqual(duplicate.returncode, 1)
        self.assertIn("duplicate JSON field", duplicate.stdout)
        shutil.rmtree(inputs[3].parent)
        inputs = self.physical_inputs()
        self.update_physical_artifact(inputs, "load_lifecycle", {"physical_S1_confirmed": False})
        self.assertEqual(self.physical_command(inputs, "physical-no-SAVE.json").returncode, 1)

    def test_physical_missing_and_partial_actor_values_have_true_branch_guards(self) -> None:
        inputs = self.physical_inputs()
        fixture = inputs[3].parent
        tree = parse_clausewitz((fixture / "common/scripted_triggers/djcg_observer_triggers.txt").read_text(encoding="utf-8-sig"))
        actor = child(tree, "djcg_physical_actor_trigger")
        self.assertEqual([e.key for e in actor.entries], ["trigger_if", "trigger_else"])
        guarded = child(actor, "trigger_if")
        limit = child(guarded, "limit")
        guarded_vars = {e.value for e in limit.entries if e.key == "exists"}
        self.assertTrue({"var:djcg_standalone", "var:djcg_tier", "var:djcg_physical",
            "var:djcg_setup_goal", "var:djcg_setup_primary", "var:djcg_setup_secondary"}.issubset(guarded_vars))
        self.assertTrue(all(e.key == "exists" for e in limit.entries))
        self.assertEqual(scalar(child(actor, "trigger_else"), "always"), "no")
        # The original actor expressions remain in the selected branch. Missing
        # OR partial setup cannot reach a naked value lookup via same-level AND.
        self.assertEqual(scalar(guarded, "var:djcg_standalone"), "1")
        self.assertEqual(scalar(guarded, "var:djcg_tier"), "1")
        self.assertEqual(scalar(guarded, "var:djcg_physical"), "1")
        self.assertEqual(scalar(guarded, "current_date"), "1066.9.15")

    def test_physical_pre_war_and_partial_capture_cannot_eagerly_read_absent_values(self) -> None:
        inputs = self.physical_inputs()
        fixture = inputs[3].parent
        tree = parse_clausewitz((fixture / "common/scripted_triggers/djcg_observer_triggers.txt").read_text(encoding="utf-8-sig"))
        war = child(tree, "djcg_physical_war_trigger")
        self.assertEqual([e.key for e in war.entries], ["trigger_if", "trigger_else"])
        guarded = child(war, "trigger_if")
        self.assertEqual({e.value for e in child(guarded, "limit").entries},
            {"root.var:djcg_setup_primary", "root.var:djcg_setup_secondary", "root.var:djcg_setup_goal", "var:djc_goal_title"})
        self.assertEqual(scalar(child(war, "trigger_else"), "always"), "no")
        self.assertEqual(scalar(guarded, "using_cb"), "duchy_de_jure_greatwar")
        self.assertEqual(scalar(guarded, "primary_attacker"), "root")
        ready = child(tree, "djcg_physical_readback_ready_trigger")
        self.assertEqual([e.key for e in ready.entries], ["trigger_if", "trigger_else"])
        body = child(ready, "trigger_if")
        protected = {e.value for e in child(body, "limit").entries}
        self.assertEqual(protected, {"var:" + key for key in (
            "djcg_physical_captured", "djcg_war_count", "djcg_after_gold", "djcg_after_prestige", "djcg_after_piety",
            "djcg_war", "djcg_actual_goal", "djcg_actual_attacker", "djcg_actual_primary", "djcg_actual_secondary")})
        self.assertEqual(scalar(body, "var:djcg_physical_captured"), "1")
        self.assertEqual(scalar(child(ready, "trigger_else"), "always"), "no")
        gui = parse_clausewitz((fixture / "common/scripted_guis/djcg_saved_entry_guis.txt").read_text(encoding="utf-8-sig"))
        shown = child(child(gui, "djcg_saved_war_readback_gui"), "is_shown")
        self.assertEqual([(e.key, e.value) for e in shown.entries], [("djcg_physical_readback_ready_trigger", "yes")])

    def test_physical_missing_guard_fix_has_no_seed_mutation_new_schema_or_new_mode(self) -> None:
        inputs = self.physical_inputs()
        contract = json.loads(inputs[3].read_bytes())
        self.assertEqual(contract["schema"], "djc.physical-ordinary-s0-s1.v1")
        self.assertFalse(contract["requires_phase_markers"])
        fixture = inputs[3].parent
        triggers = parse_clausewitz((fixture / "common/scripted_triggers/djcg_observer_triggers.txt").read_text(encoding="utf-8-sig"))
        self.assertFalse({e.key for b in walk(triggers) for e in b.entries} & {"set_variable", "add_character_flag", "trigger_event", "start_war", "add_prestige", "add_piety"})
        invalid = self.root / "unsupported-extra-guard-mode"
        self.assertEqual(self.command("gen_acceptance_fixture.py", "--safe-physical-guards", "--output", str(invalid)).returncode, 2)
        self.assertFalse(invalid.exists())

    def synthetic_flat_native(self, path: Path, *, captured: bool) -> None:
        self.synthetic_physical_save(path, captured=captured)
        with zipfile.ZipFile(path) as archive:
            content = archive.read("gamestate")
        self.assertTrue(content.startswith(b"SAV0100\n"))
        content = content.removeprefix(b"SAV0100\n")
        # Actual current native flat layout: root living table; numeric actor
        # keys are column zero. Once flags have empty data, not a value0 atom.
        content = content.replace(b"\t200={\n", b"living={\n200={\n", 1)
        content = content.replace(b"\t}\nplayed_character=", b"}\n}\nplayed_character=", 1)
        needle = b'\t\t\t\t\t{\n\t\t\t\t\t\tflag="djcg_standalone"'
        empty_flag = b'\t\t\t\t\t{\n\t\t\t\t\t\tflag="djcg_saved_entry_dispatched"\n\t\t\t\t\t\tdata={}\n\t\t\t\t\t}\n'
        self.assertIn(needle, content)
        content = content.replace(needle, empty_flag + needle, 1)
        content = re.sub(rb'flag="(djcg_[A-Za-z0-9_]+)"', rb'flag=\1', content)
        content = content.replace(b"\t\t\t\t\t{\n", b" {\n")
        path.write_bytes(b"SAV0100bf3a7e1200007f59\n" + content)

    def flat_native_inputs(self) -> tuple[Path, Path, Path, Path]:
        inputs = self.physical_inputs()
        self.synthetic_flat_native(inputs[0], captured=False)
        self.synthetic_flat_native(inputs[1], captured=True)
        evidence = json.loads(inputs[2].read_bytes())
        lifecycle = Path(evidence["load_lifecycle"]["path"])
        record = json.loads(lifecycle.read_bytes())
        record["S0_sha256"] = hashlib.sha256(inputs[0].read_bytes()).hexdigest()
        lifecycle.write_text(json.dumps(record))
        evidence["load_lifecycle"] = self.physical_pin(lifecycle)
        inputs[2].write_text(json.dumps(evidence))
        self.refresh_physical_s1(inputs)
        return inputs

    def test_physical_flat_native_header_actual_shape_and_ZIP_keep_same_business_contract(self) -> None:
        inputs = self.flat_native_inputs()
        result = self.physical_command(inputs, "flat-native-good.json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        value = json.loads((self.root / "flat-native-good.json").read_bytes())
        self.assertEqual(value["S0"]["format"], "plaintext")
        self.assertEqual(value["S1"]["format"], "plaintext")
        self.assertEqual(value["actual_total_debit_saved_raw"], {"gold": "0", "prestige": "5000000", "piety": "30000000"})
        self.assertEqual(json.loads(inputs[3].read_bytes())["schema"], "djc.physical-ordinary-s0-s1.v1")

    def test_physical_flat_rejects_decoded_surrogate_bad_header_NUL_and_late_invalid_UTF8(self) -> None:
        inputs = self.flat_native_inputs()
        original = inputs[0].read_bytes()
        bad = [original.removeprefix(b"SAV0100bf3a7e1200007f59\n"),
               original.replace(b"bf3a7e1200007f59", b"NOT_A_NATIVE_PIN", 1),
               original + b"\n\x00", original + b"\n#" + b"x" * 70000 + b"\xff"]
        for i, raw in enumerate(bad):
            inputs[0].write_bytes(raw)
            result = self.physical_command(inputs, f"flat-native-invalid-{i}.json")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn('"layer": "fixture-input-rejected"', result.stdout)

    def test_physical_flat_rejects_same_byte_identity_replacement_while_reading(self) -> None:
        path = self.root / "SYNTHETIC-flat-native.ck3"
        self.synthetic_flat_native(path, captured=False)
        module = runpy.run_path(str(self.product / "tools/verify_fixture_log.py"))
        reader = module["read_saved_point"]
        actual_identity = reader.__globals__["source_identity"]
        calls = 0
        original = path.read_bytes()
        def replace_on_recheck(actual_path: Path) -> tuple[int, int, int, int, int]:
            nonlocal calls
            calls += 1
            if calls == 2:
                replacement = self.root / "SYNTHETIC-same-bytes-replacement.ck3"
                replacement.write_bytes(original)
                actual_path.unlink()
                replacement.rename(actual_path)
            return actual_identity(actual_path)
        reader.__globals__["source_identity"] = replace_on_recheck
        try:
            with self.assertRaisesRegex(ValueError, "source changed"):
                reader(path, 0, 1, physical_stage="s0")
        finally:
            reader.__globals__["source_identity"] = actual_identity
        self.assertEqual(original, path.read_bytes())

    def test_physical_flat_requires_unique_qualified_living_actor_and_keeps_empty_flags_untyped(self) -> None:
        path = self.root / "SYNTHETIC-qualified-flat.ck3"
        self.synthetic_flat_native(path, captured=False)
        original = path.read_bytes()
        module = runpy.run_path(str(self.product / "tools/verify_fixture_log.py"))
        point = module["read_saved_point"](path, 0, 1, physical_stage="s0")
        self.assertNotIn("djcg_saved_entry_dispatched", point.atoms)
        for bad in (original.replace(b"living={", b"not_living={", 1),
                    original + b"\nliving={\n200={\nalive_data={}\n}\n}\n"):
            path.write_bytes(bad)
            with self.assertRaises(ValueError):module["read_saved_point"](path, 0, 1, physical_stage="s0")

    def test_legacy_v2_does_not_silently_accept_new_flat_native_mode(self) -> None:
        inputs = self.standalone_inputs()
        with zipfile.ZipFile(inputs[0]) as archive:
            text = archive.read("gamestate").removeprefix(b"SAV0100\n")
        inputs[0].write_bytes(b"SAV0100bf3a7e1200007f59\n" + text)
        result = self.gui_command(inputs, "legacy-flat-refused.json")
        self.assertEqual(result.returncode, 1)
        self.assertIn("ZIP/CRC invalid", result.stdout)

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


    def outcome_fixture(self, tier: str, outcome: str) -> Path:
        target = self.root / f"outcome-{tier}-{outcome}"
        result = self.command("gen_acceptance_fixture.py", "--tier", tier, "--outcome", outcome,
                              "--saved-entry-bridge", "--output", str(target))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return target

    def test_independent_outcomes_preserve_original_eight_and_entire_war_effects(self) -> None:
        original = self.event_definitions(self.fixture("all"))
        combined = []
        for ti, tier in enumerate(("duchy", "kingdom", "empire")):
            for oi, outcome in enumerate(("attacker", "white_peace", "defender")):
                fixture = self.outcome_fixture(tier, outcome)
                actual = self.event_definitions(fixture)
                stage = 10 + ti * 30 + oi * 10
                self.assertEqual(set(actual), {"djct.1", "djct.800", "djct.900", "djct.901", *(f"djct.{stage+n}" for n in range(4))})
                for offset in (0, 3, 1):
                    self.assertEqual(original[f"djct.{stage+offset}"], actual[f"djct.{stage+offset}"])
                before = child(child(original[f"djct.{stage+2}"], "immediate"), "if")
                after = child(child(actual[f"djct.{stage+2}"], "immediate"), "if")
                self.assertEqual(before.entries[:4], after.entries[:4])
                self.assertEqual(child(original[f"djct.{stage+2}"], "immediate").entries[-1], child(actual[f"djct.{stage+2}"], "immediate").entries[-1])
                contract = json.loads((fixture / "fixture-contract.json").read_bytes())
                self.assertEqual((contract["nominal_completion_natural_day"], contract["max_natural_days"]), (6, 18))
                self.assertEqual(len(contract["markers"]), 8)
                self.assertEqual(contract["successor_business_case"], "none")
                self.assertIn("same-process sequential reset/war stability", contract["claims_excluded"])
                self.assertNotIn("common/on_action/djct_on_actions.txt", [p.relative_to(fixture).as_posix() for p in fixture.rglob("*")])
                combined.extend(contract["markers"])
        expected = json.loads((self.root / "fixture-all/fixture-contract.json").read_bytes())["markers"]
        self.assertEqual(combined, expected)

    def test_independent_outcome_aggregate_requires_nine_exact_cells_and_same_source(self) -> None:
        args = ["--aggregate-outcomes"]
        contracts = []
        for tier in ("duchy", "kingdom", "empire"):
            for outcome in ("attacker", "white_peace", "defender"):
                fixture = self.outcome_fixture(tier, outcome)
                contract = fixture / "fixture-contract.json"
                contracts.append(contract)
                args.extend(("--log", str(self.synthetic_log(fixture)), "--contract", str(contract)))
        report = self.root / "independent72.json"
        result = self.command("verify_fixture_log.py", *args, "--report", str(report))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(report.read_bytes())["observed_pass_count"], 72)
        value = json.loads(contracts[-1].read_bytes())
        value["source_identity"]["producer_sha256"] = "0" * 64
        contracts[-1].write_text(json.dumps(value), encoding="utf-8")
        result = self.command("verify_fixture_log.py", *args, "--report", str(self.root / "mixed-source.json"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("identical producer", result.stdout)
        result = self.command("verify_fixture_log.py", *args[:-4], "--report", str(self.root / "missing-cell.json"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("exactly nine", result.stdout)

    def test_independent_outcome_invalid_modes_and_eight_masquerade_are_rejected(self) -> None:
        for i, flags in enumerate((("--outcome", "attacker"), ("--tier", "kingdom", "--outcome", "attacker", "--with-gui-observer"), ("--tier", "duchy", "--outcome", "white_peace", "--ordinary-gui-only"))):
            target = self.root / f"invalid-outcome-{i}"
            result = self.command("gen_acceptance_fixture.py", *flags, "--output", str(target))
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(target.exists())
        fixture = self.outcome_fixture("kingdom", "white_peace")
        contract = fixture / "fixture-contract.json"
        value = json.loads(contract.read_bytes())
        value["schema"] = "djc.external-acceptance.v2"
        contract.write_text(json.dumps(value), encoding="utf-8")
        result = self.command("verify_fixture_log.py", "--log", str(self.synthetic_log(fixture)), "--contract", str(contract), "--report", str(self.root / "legacy-eight.json"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("exact original ordered tier predicates", result.stdout)



if __name__ == "__main__":
    unittest.main()
