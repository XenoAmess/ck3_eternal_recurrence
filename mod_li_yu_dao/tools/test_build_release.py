"""Offline regression checks for packaging and static gate failure cases."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import build_release as release
import validate_static as static


def write(path: Path, text: str, *, bom: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8-sig" if bom else "utf-8", newline="\n")


def fixture(source: Path) -> None:
    scripts = {
        "descriptor.mod": 'version="0.1.0"\nname="Li Yu Dao test"\nsupported_version="1.20.*"\n',
        "common/religion/faith_types/lyd_faiths.txt": "lyd_faith = { faith_details = { religion = confucianism_religion } main_rite = lyd_rite }\n",
        "common/religion/rite_types/lyd_rites.txt": "lyd_rite = { name = lyd_rite desc = lyd_rite_desc faith = lyd_faith tenets = { lyd_tenet lyd_tenet_second lyd_tenet_third } }\n",
        "common/religion/tenet_types/lyd_tenets.txt": "lyd_tenet = { }\nlyd_tenet_second = { }\nlyd_tenet_third = { }\n",
        "history/faiths/lyd_faith_history.txt": "lyd_faith = { 867.1.1 = { main_rite = lyd_rite } }\n",
        "common/scripted_triggers/lyd_actor_triggers.txt": "lyd_actor = { is_ai = no }\n",
        "common/scripted_effects/lyd_notice_effects.txt": "lyd_notify = { add_stress = -5 remove_short_term_gold = 10 add_gold = 5 trigger_event = lyd.1 }\n",
        "common/decisions/lyd_decisions.txt": 'lyd_open = { picture = { reference = "gfx/interface/illustrations/decisions/decision_dynasty_house.dds" } ai_check_interval = 0 is_shown = { lyd_actor = yes } effect = { if = { limit = { lyd_actor = yes } lyd_notify = yes } } }\n',
        "common/character_interactions/lyd_interactions.txt": "lyd_request = { is_shown = { scope:actor = { lyd_actor = yes } } on_accept = { scope:actor = { lyd_notify = yes } } }\n",
        "events/lyd_events.txt": "namespace = lyd\nlyd.1 = { type = character_event title = lyd.1.t desc = lyd.1.d option = { name = lyd.1.a } }\n",
    }
    for relative, text in scripts.items():
        write(source / relative, text, bom=True)
    # Keep the fixture minimal while covering every fixed production path.
    for relative in release.REQUIRED_RUNTIME_FILES:
        path = source / relative
        if path.suffix == ".txt" and not path.exists():
            write(path, "# Empty consent fixture\n", bom=True)
    for language in ("english", "simp_chinese"):
        write(source / f"localization/{language}/lyd_content_l_{language}.yml", f'l_{language}:\n lyd_rite:0 "School"\n lyd_rite_desc:0 "A tradition"\n lyd_tenet_name:0 "Learning"\n lyd_tenet_desc:0 "Learning practice"\n lyd_tenet_second_name:0 "Rites"\n lyd_tenet_second_desc:0 "Ritual practice"\n lyd_tenet_third_name:0 "Virtue"\n lyd_tenet_third_desc:0 "Virtue practice"\n', bom=True)
        write(source / f"localization/{language}/lyd_runtime_l_{language}.yml", f'l_{language}:\n lyd_open:0 "Open"\n lyd_request:0 "Request"\n lyd.1.t:0 "Discussion"\n lyd.1.d:0 "$lyd_open$ [ROOT.Char.GetName]"\n lyd.1.a:0 "Agree"\n', bom=True)
        write(source / f"localization/{language}/lyd_c2_consent_l_{language}.yml", f'l_{language}:\n', bom=True)


class BuildTests(unittest.TestCase):
    def test_parameterized_guard_proves_only_current_actor(self) -> None:
        parse = static.parse_clausewitz
        helper = parse("is_ai = no faith = $TARGET$")
        target_only = parse("$ACTOR$ = { is_ai = no }")
        recipient_only = parse("scope:recipient = { is_ai = no }")
        triggers = {"lyd_direct": helper, "lyd_indirect": target_only, "lyd_recipient": recipient_only}
        self.assertTrue(static.player_guard(parse("lyd_direct = { TARGET = scope:recipient.faith }"), triggers))
        self.assertFalse(static.player_guard(parse("lyd_indirect = { ACTOR = scope:recipient }"), triggers))
        self.assertFalse(static.player_guard(parse("lyd_recipient = { ACTOR = root }"), triggers))
        self.assertFalse(static.player_guard(parse("NOT = { lyd_direct = { TARGET = faith } }"), triggers))

    def test_variable_names_are_internal_but_option_names_are_localized(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lyd-variable-loc-") as directory:
            source = Path(directory)
            fixture(source)
            effects = source / "common/scripted_effects/lyd_notice_effects.txt"
            write(effects, effects.read_text(encoding="utf-8-sig").replace(
                "add_stress = -5", "set_variable = { name = lyd_internal_only value = 1 } add_stress = -5"), bom=True)
            self.assertEqual(static.validate(source)["result"], "GREEN")
            events = source / "events/lyd_events.txt"
            write(events, events.read_text(encoding="utf-8-sig").replace("name = lyd.1.a", "name = lyd_missing_option"), bom=True)
            report = static.validate(source)
            self.assertEqual(report["result"], "RED")
            self.assertTrue(any("unlocalized field" in item and "lyd_missing_option" in item for item in report["errors"]))

    def test_reproducible_archive_and_fixture_exclusion(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lyd-build-test-") as directory:
            base = Path(directory)
            source = base / "source"
            fixture(source)
            for relative in ("tools/test_fixture.txt", "docs/design.md", "debug/probe.txt", "fixtures/events/lyd_debug.txt", "common/decisions/tests/lyd_probe.txt"):
                write(source / relative, "NEVER_SHIP_FIXTURE\n")
            first = release.build_release(source, base / "a" / release.PRODUCT_ID, revision="0" * 40)
            second = release.build_release(source, base / "b" / release.PRODUCT_ID, revision="0" * 40)
            self.assertEqual(Path(first["manifest"]).read_bytes(), Path(second["manifest"]).read_bytes())
            self.assertEqual(Path(first["archive"]).read_bytes(), Path(second["archive"]).read_bytes())
            manifest = json.loads(Path(first["manifest"]).read_text(encoding="utf-8"))
            expected = set(release.REQUIRED_RUNTIME_FILES) | {
                "common/scripted_triggers/lyd_actor_triggers.txt",
                "common/scripted_effects/lyd_notice_effects.txt",
            }
            self.assertEqual({entry["path"] for entry in manifest["files"]}, expected)
            with zipfile.ZipFile(first["archive"]) as archive:
                self.assertEqual(set(archive.namelist()), {f"{release.PRODUCT_ID}/{relative}" for relative in expected})
                self.assertTrue(all(b"NEVER_SHIP_FIXTURE" not in archive.read(name) for name in archive.namelist()))
            self.assertEqual(release.verify_manifest(Path(first["staging"]), Path(first["manifest"])), len(expected))
            write(Path(first["staging"]) / "docs/leaked.md", "leak")
            with self.assertRaisesRegex(ValueError, "missing or extra"):
                release.verify_manifest(Path(first["staging"]), Path(first["manifest"]))

    def test_runtime_family_rejects_test_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lyd-family-test-") as directory:
            source = Path(directory)
            fixture(source)
            write(source / "common/scripted_effects/lyd_fixture_effects.txt", "lyd_fixture = { }\n")
            with self.assertRaisesRegex(ValueError, "test/debug"):
                release.collect_runtime_files(source)

    def test_static_gate_and_meaningful_negative_cases(self) -> None:
        mutants = (
            ("common/decisions/lyd_decisions.txt", "lyd_actor = yes", "always = yes", "decision"),
            ("common/scripted_effects/lyd_notice_effects.txt", "trigger_event = lyd.1", "lyd_missing_helper = yes", "unresolved LYD"),
            ("common/scripted_effects/lyd_notice_effects.txt", "lyd_notify = {", "lyd_notify = { {", "unexpected opening"),
            ("localization/simp_chinese/lyd_runtime_l_simp_chinese.yml", "[ROOT.Char.GetName]", "[ROOT.Char.GetTitleAsName]", "placeholder mismatch"),
            ("common/character_interactions/lyd_interactions.txt", "scope:actor = { lyd_actor = yes }", "scope:recipient = { lyd_actor = yes }", "actor player gate"),
        )
        with tempfile.TemporaryDirectory(prefix="lyd-static-test-") as directory:
            source = Path(directory)
            fixture(source)
            self.assertEqual(static.validate(source)["result"], "GREEN")
            for relative, original, replacement, expected in mutants:
                with self.subTest(relative=relative, expected=expected):
                    path = source / relative
                    initial = path.read_bytes()
                    text = path.read_text(encoding="utf-8-sig")
                    write(path, text.replace(original, replacement), bom=True)
                    report = static.validate(source)
                    self.assertEqual(report["result"], "RED")
                    self.assertTrue(any(expected in error for error in report["errors"]), report["errors"])
                    path.write_bytes(initial)

    def test_r0001_boot_regressions_and_native_tier_interval(self) -> None:
        decisions = "common/decisions/lyd_decisions.txt"
        effects = "common/scripted_effects/lyd_notice_effects.txt"
        picture = 'picture = { reference = "gfx/interface/illustrations/decisions/decision_dynasty_house.dds" }'
        mutants = (
            (effects, "add_stress = -5", "change_stress = -5", "unknown native effect change_stress"),
            (effects, "add_gold = 5", "add_gold = -5", "negative add_gold"),
            (decisions, picture, "", "decision picture"),
            (decisions, picture, 'picture = "gfx/interface/illustrations/decisions/decision_dynasty_house.dds"', "decision picture"),
            (decisions, picture, "picture = { }", "decision picture"),
            (decisions, "ai_check_interval = 0", "", "AI check interval"),
            (decisions, "ai_check_interval = 0", "ai_check_interval = -1", "AI check interval"),
            (decisions, "ai_check_interval = 0", "ai_check_interval_by_tier = { county = 0 }", "AI check interval"),
            (decisions, "ai_check_interval = 0", "ai_check_interval_by_tier = { barony = 0 county = 0 duchy = 0 kingdom = -1 empire = 0 hegemony = 0 }", "AI check interval"),
        )
        with tempfile.TemporaryDirectory(prefix="lyd-boot-regression-") as directory:
            source = Path(directory)
            fixture(source)
            self.assertEqual(static.validate(source)["result"], "GREEN")
            # Every shipped native script and descriptor is covered by the BOM
            # rule; missing encoding cannot hide behind a passing fixture.
            for relative in release.collect_runtime_files(source):
                if Path(relative).suffix not in {".txt", ".mod"}:
                    continue
                with self.subTest(missing_bom=relative):
                    path = source / relative
                    initial = path.read_bytes()
                    self.assertTrue(initial.startswith(b"\xef\xbb\xbf"))
                    path.write_bytes(initial[3:])
                    report = static.validate(source)
                    self.assertEqual(report["result"], "RED")
                    self.assertTrue(any("runtime script needs UTF-8 BOM" in error and relative in error for error in report["errors"]), report["errors"])
                    path.write_bytes(initial)
            for relative, original, replacement, expected in mutants:
                with self.subTest(replacement=replacement):
                    path = source / relative
                    initial = path.read_bytes()
                    write(path, path.read_text(encoding="utf-8-sig").replace(original, replacement), bom=True)
                    report = static.validate(source)
                    self.assertEqual(report["result"], "RED")
                    self.assertTrue(any(expected in error for error in report["errors"]), report["errors"])
                    path.write_bytes(initial)
            path = source / decisions
            text = path.read_text(encoding="utf-8-sig")
            write(path, text.replace("ai_check_interval = 0", "ai_check_interval_by_tier = { barony = 0 county = 12 duchy = 6 kingdom = 1 empire = 1 hegemony = 1 }"), bom=True)
            self.assertEqual(static.validate(source)["result"], "GREEN")


if __name__ == "__main__":
    unittest.main()
