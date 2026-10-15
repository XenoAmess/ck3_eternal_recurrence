"""Focused offline tests. No desktop, Steam login, network or game is required."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "steam-ck3-versions" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import steam_ck3_versions as cli
import steam_versions_core as core
import steam_versions_uia as uia
import steam_versions_mouse as mouse


class Clock:
    def __init__(self):
        self.value = 0

    def now(self):
        return self.value

    def sleep(self, seconds):
        self.value += seconds


def snapshot(branch="1.20.0.4", state=4, version="1.20.0.4", build=100, target=0):
    return {"manifest_sha256": f"{branch}-{state}-{version}-{build}-{target}", "branch": branch,
            "numbers": {"StateFlags": state, "buildid": build, "TargetBuildID": target},
            "launcher": {"raw_version": version, "sha256": version},
            "executable": {"exists": True, "bytes": 20, "mtime_ns": build},
            "installed_depots": {"depot": {"manifest": str(build)}}}


class CoreTests(unittest.TestCase):
    def test_vdf_windows_backslashes_unicode_comments_and_nested(self):
        raw = r'''// comment
        "libraryfolders" { "0" { "path" "E:\\游戏\\Steam Library" "apps" { "1158310" "10" } } }
        '''
        data = core.parse_vdf(raw)
        self.assertEqual(data["libraryfolders"]["0"]["path"], "E:\\游戏\\Steam Library")
        self.assertEqual(data["libraryfolders"]["0"]["apps"]["1158310"], "10")

    def test_vdf_partial_and_duplicate_fail_explicitly(self):
        for raw in ['"AppState" { "appid"', '"a" "x" "a" "y"', '"a" "unterminated']:
            with self.subTest(raw=raw), self.assertRaises(core.VersionError):
                core.parse_vdf(raw)

    def test_exact_version_and_full_label(self):
        labels = ["None", "1.20.0.4 - Version 1.20.0.4", "1.19.0.6 - Old version"]
        self.assertEqual(core.resolve_target(labels, "1.20.0.4")["branch"], "1.20.0.4")
        self.assertEqual(core.resolve_target(labels, labels[2])["expected_version"], "1.19.0.6")
        self.assertEqual(core.resolve_target(labels, "public")["label"], "None")
        self.assertEqual(core.resolve_target(["无 - 不参与任何测试活动"], "stable")["branch"], "public")

    def test_short_prefix_and_multiple_version_labels_are_not_latest(self):
        labels = ["1.20.0.4 - previous", "1.20.1 - current", "beta - 1.20.0.4"]
        with self.assertRaises(core.VersionError):
            core.resolve_target(labels, "1.20")
        # A literal branch identity is stronger than incidental description.
        self.assertEqual(core.resolve_target(labels, "1.20.0.4")["label"], labels[0])
        with self.assertRaises(core.VersionError):
            core.resolve_target(["beta - 1.20.0.4", "old - 1.20.0.4"], "1.20.0.4")

    def test_actual_ck3_branch_key_and_advertised_patch_version_are_distinct(self):
        rows = [{"label": "1.20.0", "description_texts": ["Old Version 1.20.0.4 (Crozier)"],
                 "row_text": "1.20.0 Old Version 1.20.0.4 (Crozier) 2026年10月6日"},
                {"label": "1.19.0", "description_texts": ["Old Version 1.19.0.6 (Scribe)"],
                 "row_text": "1.19.0 Old Version 1.19.0.6 (Scribe) 2026年6月4日"}]
        labels = [row["label"] for row in rows]
        resolved = core.resolve_target(labels, "1.20.0.4", rows=rows)
        self.assertEqual(resolved["branch"], "1.20.0")
        self.assertEqual(resolved["expected_version"], "1.20.0.4")
        self.assertEqual(core.resolve_target(labels, "1.19.0.6", rows=rows)["branch"], "1.19.0")
        self.assertEqual(core.resolve_target(labels, "1.20.0", rows=rows)["expected_version"], "1.20.0.4")
        with self.assertRaises(core.VersionError):
            core.resolve_target(labels, "1.20.0.3", rows=rows)

    def test_selected_branch_is_not_installed(self):
        old = snapshot(version="1.20.1", build=101, target=100)
        problems = core.completion_problems(old, "1.20.0.4", "1.20.0.4")
        self.assertIn("target_build_not_installed", problems)
        self.assertIn("installed_launcher_version_mismatch", problems)
        self.assertTrue(core.completion_problems(snapshot(state=1026), "1.20.0.4"))

    def test_download_and_staging_counters_must_complete(self):
        observed = snapshot()
        observed["numbers"].update(BytesToDownload=100, BytesDownloaded=99,
                                   BytesToStage=120, BytesStaged=100)
        self.assertEqual(len(core.completion_problems(observed, "1.20.0.4")), 2)

    def test_wait_tracks_pending_then_verifies_stable_actual_file_hash(self):
        clock = Clock()
        pending, done = snapshot(state=1026), snapshot()
        events = []
        def observe(installation, hash_exe=False):
            result = copy.deepcopy(pending if clock.value < 2 else done)
            if hash_exe:
                result["executable"]["sha256"] = "actual-bytes-hash"
            return result
        result = core.wait_installed({}, "1.20.0.4", expected_version="1.20.0.4", timeout=10,
            poll_seconds=1, settle_seconds=2, observe=observe, clock=clock.now, sleep=clock.sleep,
            emit=lambda event, **fields: events.append((event, fields)))
        self.assertGreaterEqual(clock.value, 4)
        self.assertEqual(result["executable"]["sha256"], "actual-bytes-hash")
        self.assertEqual(events[-1][0], "installed_verified")

    def test_paused_or_unupdated_download_times_out(self):
        clock = Clock()
        with self.assertRaisesRegex(core.VersionError, "timed out"):
            core.wait_installed({}, "1.20.0.4", timeout=3, poll_seconds=1, settle_seconds=1,
                observe=lambda *args, **kwargs: snapshot(state=6), clock=clock.now, sleep=clock.sleep)

    def test_missing_expected_launcher_version_never_passes(self):
        observed = snapshot(version="")
        self.assertIn("installed_launcher_version_mismatch",
                      core.completion_problems(observed, "1.20.0.4", "1.20.0.4"))

    def test_manifest_discovery_and_actual_installed_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            steam = Path(directory) / "Steam"
            other = Path(directory) / "Other Library"
            (steam / "steamapps").mkdir(parents=True)
            (other / "steamapps").mkdir(parents=True)
            (steam / "steamapps" / "libraryfolders.vdf").write_text(
                '"libraryfolders" { "0" { "path" ' + json.dumps(str(other)) + ' } }', encoding="utf-8")
            manifest = other / "steamapps" / "appmanifest_1158310.acf"
            manifest.write_text('"AppState" { "appid" "1158310" "installdir" "CK3" '
                                '"StateFlags" "4" "buildid" "123" "UserConfig" { "BetaKey" "1.20.0.4" } }',
                                encoding="utf-8")
            game = other / "steamapps" / "common" / "CK3"
            (game / "binaries").mkdir(parents=True)
            (game / "launcher").mkdir()
            (game / "binaries" / "ck3.exe").write_bytes(b"not-a-running-game")
            (game / "launcher" / "launcher-settings.json").write_text('{"rawVersion":"1.20.0.4"}', encoding="utf-8")
            install = core.discover_installation(steam)
            result = core.observe_installation(install, hash_exe=True)
            self.assertEqual(result["numbers"]["buildid"], 123)
            self.assertEqual(result["branch"], "1.20.0.4")
            self.assertEqual(result["launcher"]["raw_version"], "1.20.0.4")
            self.assertEqual(len(result["executable"]["sha256"]), 64)
            # Merely finding two copies must not silently choose a machine path.
            (steam / "steamapps" / manifest.name).write_bytes(manifest.read_bytes())
            with self.assertRaisesRegex(core.VersionError, "not unique"):
                core.discover_installation(steam)
            self.assertEqual(Path(core.discover_installation(steam, other)["manifest_path"]), manifest)


class UITests(unittest.TestCase):
    def ui(self):
        instance = object.__new__(uia.SteamUI)
        instance.timeout = 0.5
        instance.emit = Mock()
        instance.combo = Mock(return_value=object())
        instance.expand = Mock()
        instance.act = Mock()
        instance.dump = Mock()
        instance.version_table = Mock(return_value=None)
        return instance

    def test_selection_ack_without_selected_readback_is_not_success(self):
        instance = self.ui()
        node = Mock()
        node.window_text.return_value = "1.20.0.4 - Previous"
        instance.option_nodes = Mock(return_value=[node])
        instance.selected = Mock(side_effect=["None", "None"])
        with patch.object(uia.time, "monotonic", side_effect=[0, 0, 1]), patch.object(uia.time, "sleep"):
            with self.assertRaisesRegex(core.VersionError, "ACK not confirmed"):
                instance.choose("1.20.0.4 - Previous")
        instance.act.assert_called_once_with(node)

    def test_successful_selection_explicitly_does_not_claim_installation(self):
        instance = self.ui()
        node = Mock()
        node.window_text.return_value = "1.20.0.4 - Previous"
        instance.option_nodes = Mock(return_value=[node])
        instance.selected = Mock(side_effect=["None", "1.20.0.4 - Previous"])
        result = instance.choose("1.20.0.4 - Previous")
        self.assertFalse(result["installed_verified"])
        self.assertTrue(result["changed"])

    def test_no_change_does_not_submit_selection(self):
        instance = self.ui()
        instance.selected = Mock(return_value="None")
        self.assertFalse(instance.choose("None")["changed"])
        instance.act.assert_not_called()

    def test_offline_mode_blocks_even_with_download_permission(self):
        arguments = Mock(allow_download=True, network_state="online")
        interface = Mock()
        interface.network_observation.return_value = {"state": "offline", "offline_labels": ["离线模式"]}
        with self.assertRaisesRegex(core.VersionError, "will not take it online"):
            cli.network_permission(arguments, interface, Mock())

    def test_unmanaged_screen_is_not_assumed_available(self):
        with self.assertRaisesRegex(core.VersionError, "lease"):
            cli.screen_guard(Mock(task_bus=None, exclusive_screen_confirmed=False))

    def test_options_are_scoped_to_ck3_properties_and_actual_visible_rows(self):
        instance = self.ui()
        def node(name, visible=True):
            result = Mock()
            result.element_info = SimpleNamespace(control_type="ListItem")
            result.window_text.return_value = name
            result.is_enabled.return_value = True
            result.is_visible.return_value = visible
            return result
        public = node("None")
        beta = node("1.20.0.4 - Previous")
        hidden = node("1.19.0.6 - Stale hidden", False)
        unrelated = node("Stellaris")
        instance.root = Mock()
        main = Mock()
        instance.selectors = {}
        instance.windows = Mock(return_value=[main, instance.root])
        instance.nodes = lambda root: [public, beta, hidden] if root is instance.root else [unrelated]
        self.assertEqual(instance.option_nodes(), [public, beta])

    def test_list_marks_offline_catalog_as_cached(self):
        instance = self.ui()
        instance.selected = Mock(return_value="None")
        instance.network_observation = Mock(return_value={"state": "offline", "offline_labels": ["离线模式"]})
        option = Mock()
        option.window_text.return_value = "None"
        instance.option_nodes = Mock(return_value=[option])
        result = instance.list_branches()
        self.assertEqual(result["availability"], "offline_cached_client_account_view")

    def test_actual_steam_duplicate_localized_betas_tab_uses_app_route(self):
        instance = self.ui()
        instance.root = Mock()
        instance.selectors = {}
        def tab(name, route):
            result = Mock()
            result.element_info = SimpleNamespace(control_type="TabItem", automation_id=route,
                                                 name=name, handle=None, process_id=100)
            result.window_text.return_value = name
            result.is_visible.return_value = True
            result.is_enabled.return_value = True
            return result
        outer = tab("游戏版本及测试版", "«rd»/app/1158310/properties/betas")
        inner = tab("游戏版本及测试版", "«rd»/app/1158310/properties/betas")
        foreign = tab("游戏版本及测试版", "«rd»/app/281990/properties/betas")
        instance.nodes = Mock(return_value=[outer, inner, foreign])
        self.assertIs(instance.betas_tab(), outer)
        instance.act.assert_not_called()

    def test_same_name_different_routes_are_not_deduplicated(self):
        one, two = Mock(), Mock()
        one.element_info.automation_id = "route-a"
        two.element_info.automation_id = "route-b"
        with self.assertRaisesRegex(core.VersionError, "distinct"):
            uia.SteamUI.same_route_actionable([one, two])

    def test_tab_action_prefers_invoke_but_branch_selection_prefers_select(self):
        instance = self.ui()
        # Call the real implementation, not the helper mock used in other
        # isolated selection tests. This mirrors Steam exposing both patterns.
        instance.guard = Mock()
        node = Mock()
        node.element_info = SimpleNamespace(name="游戏版本及测试版", control_type="TabItem",
                                           automation_id="route", handle=None, process_id=100)
        node.is_enabled.return_value = True
        node.is_visible.return_value = True
        uia.SteamUI.act(instance, node, prefer_invoke=True)
        node.iface_invoke.Invoke.assert_called_once()
        node.iface_selection_item.Select.assert_not_called()
        node.reset_mock()
        uia.SteamUI.act(instance, node)
        node.iface_selection_item.Select.assert_called_once()
        node.iface_invoke.Invoke.assert_not_called()

    def test_actual_new_steam_table_queries_offscreen_version_rows_and_checked_state(self):
        instance = self.ui()
        def row(label, description, selected, visible):
            radio = Mock()
            radio.element_info.control_type = "RadioButton"
            radio.is_enabled.return_value = True
            radio.is_visible.return_value = visible
            radio.iface_selection_item.CurrentIsSelected = selected
            texts = []
            for text in (label, description):
                node = Mock()
                node.element_info.control_type = "Text"
                node.window_text.return_value = text
                texts.append(node)
            result = Mock()
            result.element_info.control_type = "Custom"
            result.window_text.return_value = f"{label} {description} 2026年10月13日"
            result.descendants.return_value = [radio, *texts]
            return result
        public = row("默认公开版本", "游戏最常见版本", True, True)
        beta = row("1.20.0.4", "Old version 1.20.0.4", False, False)
        table = Mock()
        table.children.return_value = [public, beta]
        result = instance.list_table_branches(table, {"state": "offline"})
        self.assertEqual(result["labels"], ["默认公开版本", "1.20.0.4"])
        self.assertEqual(result["selected_label"], "默认公开版本")
        self.assertEqual(core.resolve_target(result["labels"], "public")["branch"], "public")
        self.assertEqual(core.resolve_target(result["labels"], "1.20.0.4")["expected_version"], "1.20.0.4")
        self.assertEqual(result["availability"], "offline_cached_client_account_view")

    def test_mapper_arguments_use_actual_independent_geometry_and_receipt(self):
        arguments = mouse.mapper_argv(Path("mapper.py"), Path("source.png"), Path("after.png"),
                                     1376, 768, 310.5, 220.0, 123456)
        pairs = dict(zip(arguments[5::2], arguments[6::2]))
        self.assertIn("--click", arguments)
        self.assertEqual(arguments[arguments.index("--preview-width") + 1], "1376")
        self.assertEqual(arguments[arguments.index("--preview-height") + 1], "768")
        self.assertEqual(arguments[arguments.index("--preview-left") + 1], "0")
        self.assertEqual(arguments[arguments.index("--preview-top") + 1], "0")
        self.assertEqual(arguments[arguments.index("--receipt") + 1], "after.png")
        self.assertEqual(arguments[arguments.index("--expected-foreground-hwnd") + 1], "123456")


if __name__ == "__main__":
    unittest.main(verbosity=2)
