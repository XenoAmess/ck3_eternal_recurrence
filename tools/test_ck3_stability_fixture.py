"""Synthetic fixture regressions; no CK3, Steam, desktop, SDK, or game assets."""
from __future__ import annotations

import copy
import ctypes
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

from PIL import Image, ImageDraw

from ck3_stability_fixture.chain import closed_save, verify_chain
from ck3_stability_fixture.evidence import NeedsOperator, sha256, write_new
from ck3_stability_fixture.pixels import PixelRouter, same_action, same_window
from ck3_stability_fixture.runner import assist
from ck3_stability_fixture.windows import HANDLE, OwnedWindowsBackend, abi


SIZE = (800, 600)


def glyphs(image, rect, seed=0, value=(230, 230, 230)):
    draw = ImageDraw.Draw(image)
    x, y, right, bottom = rect
    for index in range(8):
        left = x + 10 + index * 17
        draw.rectangle((left, y + 5, left + 3, y + 16), fill=value)
        draw.rectangle((left, y + 5 + (seed + index) % 3 * 4,
                        left + 9, y + 7 + (seed + index) % 3 * 4), fill=value)


def image(root, name, kind="STANDARD_EVENT", count=1, seed=0, disabled=False):
    value = Image.new("RGB", SIZE, (20, 35, 55))
    draw = ImageDraw.Draw(value)
    if kind != "MAP_WAIT":
        draw.rectangle((50, 50, 750, 555), fill=(35, 30, 25), outline=(180, 160, 100), width=4)
        if kind == "WAR_OUTCOME":
            draw.rectangle((50, 50, 750, 58), fill=(145, 100, 55))
        glyphs(value, [100, 80, 650, 110])
        glyphs(value, [100, 125, 650, 320], seed=seed)
        if kind == "STANDARD_EVENT":
            for index in range(5-count, 5):
                top = 340 + index * 42
                draw.rectangle((150, top, 650, top + 33), outline=(140, 120, 90), width=1)
                glyphs(value, [170, top + 4, 610, top + 30], value=(150, 150, 150)
                       if disabled and index == 5-count else (230, 230, 230))
        else:
            draw.rectangle((250, 475, 550, 510), outline=(200, 170, 80), width=3)
            glyphs(value, [270, 479, 530, 505])
    path = root / name
    value.save(path)
    return path


def reference(root, source, rect, name):
    path = root / (name + ".png")
    Image.open(source).crop(rect).save(path)
    return {"path": str(path), "sha256": sha256(path), "rect": rect, "max_delta": 0}


def profile(root):
    standard = image(root, "standard.png")
    war = image(root, "war.png", "WAR_OUTCOME")
    terrain = image(root, "map.png", "MAP_WAIT")
    slots = [{"top": 340 + i * 42, "bottom": 373 + i * 42, "line_x": [200, 600],
              "glyph_rect": [170, 344 + i * 42, 610, 370 + i * 42]} for i in range(5)]
    rois = {"title": {"rect": [100, 80, 650, 110]}, "body": {"rect": [100, 125, 650, 330]}}
    return {"owner": {"run_id": "synthetic-only--fixture--R0001"},
            "evidence_directory": str(root / "attempts"), "reviewed_max_actions": 3,
            "normal_save_due_utc": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "routing": {"frame_size": list(SIZE), "variants": [
                {"id": "event", "kind": "STANDARD_EVENT", "reviewed_as": "STANDARD_EVENT",
                 "patterns": [reference(root, standard, [60, 50, 740, 54], "event-top"),
                              reference(root, standard, [60, 552, 740, 556], "event-bottom")],
                 "identity_rois": rois, "option_slots": slots,
                 "excluded_slots": [{"top": 298, "bottom": 331, "line_x": [200, 600],
                                      "glyph_rect": [170, 302, 610, 328]}]},
                {"id": "war", "kind": "WAR_OUTCOME", "reviewed_as": "WAR_OUTCOME",
                 "patterns": [reference(root, war, [60, 50, 740, 54], "war-top"),
                              reference(root, war, [250, 475, 550, 478], "war-button")],
                 "identity_rois": rois, "action_rect": [270, 479, 530, 505],
                 "unique_close_button_reviewed": True},
                {"id": "map", "kind": "MAP_WAIT", "reviewed_as": "MAP_WAIT",
                 "patterns": [reference(root, terrain, [60, 50, 740, 54], "map-top"),
                              reference(root, terrain, [180, 180, 620, 320], "map-center")]},
            ]}}


class FakeBackend:
    def __init__(self, sources, fail_at_guard=None, ack=None):
        self.sources, self.index, self.keys, self.guards = sources, 0, [], 0
        self.fail_at_guard, self.ack = fail_at_guard, ack

    def guard(self, profile, initial=False):
        self.guards += 1
        if self.fail_at_guard == self.guards:
            raise NeedsOperator("synthetic stale lease/process/focus")
        return {"pid": 10, "hwnd": 11, "creation": 12}

    def capture(self, path):
        source = self.sources[min(self.index, len(self.sources)-1)]
        self.index += 1
        path.write_bytes(source.read_bytes())
        return {"size": list(SIZE), "sha256": sha256(path), "path": str(path)}

    def send_key(self, key, profile, step):
        self.keys.append(key)
        if isinstance(self.ack, Exception):
            raise self.ack
        return self.ack or {"accepted": True, "business_result": "NOT_VERIFIED"}


class RoutingTests(unittest.TestCase):
    def test_one_to_five_options_choose_physical_first_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            p = profile(root)
            router = PixelRouter(p["routing"])
            for count in range(1, 6):
                with self.subTest(count=count):
                    result = router.route(image(root, f"event-{count}.png", count=count))
                    self.assertEqual(result["option_count"], count)
                    self.assertEqual(result["action"], "Shift+1")
                    self.assertEqual(result["native_enabled"], "NOT_QUERIED")

    def test_dim_first_does_not_skip_to_bright_second(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(NeedsOperator, "first option dim"):
                PixelRouter(profile(root)["routing"]).route(image(root, "dim.png", count=3, disabled=True))

    def test_unknown_dimensions_and_unknown_window_refuse(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            router = PixelRouter(profile(root)["routing"])
            for size in ((801, 600), SIZE):
                path = root / (str(size[0]) + ".png")
                Image.new("RGB", size, "black").save(path)
                with self.assertRaises(NeedsOperator):
                    router.route(path)

    def test_sixth_option_is_not_five_option_event(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            p = profile(root)
            source = image(root, "six.png", count=5)
            raw = Image.open(source)
            ImageDraw.Draw(raw).rectangle((150, 298, 650, 331), outline=(140, 120, 90))
            raw.save(source)
            with self.assertRaisesRegex(NeedsOperator, "sixth option"):
                PixelRouter(p["routing"]).route(source)

    def test_stop_window_wins_over_matching_ordinary_shell(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            p = profile(root)
            stop = copy.deepcopy(p["routing"]["variants"][0])
            stop.update(id="succession", kind="STOP", reviewed_as="STOP")
            p["routing"]["variants"].append(stop)
            with self.assertRaisesRegex(NeedsOperator, "stop window"):
                PixelRouter(p["routing"]).route(root / "standard.png")

    def test_template_corruption_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            p = profile(root)
            Path(p["routing"]["variants"][0]["patterns"][0]["path"]).write_bytes(b"changed")
            with self.assertRaisesRegex(NeedsOperator, "pinned file changed"):
                PixelRouter(p["routing"])

    def test_war_result_identity_uses_body_not_just_victory_caption(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            router = PixelRouter(profile(root)["routing"])
            a = router.route(image(root, "war-a.png", "WAR_OUTCOME", seed=0))
            b = router.route(image(root, "war-b.png", "WAR_OUTCOME", seed=1))
            self.assertEqual(a["action"], "Escape")
            self.assertFalse(same_action(a, b))
            self.assertFalse(same_window(a, b))

    def test_normal_event_body_changes_do_not_release_same_action(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            router = PixelRouter(profile(root)["routing"])
            a = router.route(image(root, "event-a.png", seed=0))
            b = router.route(image(root, "event-b.png", seed=1))
            self.assertTrue(same_action(a, b))
            self.assertFalse(same_window(a, b))

    def test_war_close_button_is_found_at_actual_variable_height(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            p = profile(root)
            variant = p["routing"]["variants"][1]
            variant["patterns"][1] = reference(root, root / "war.png", [60, 552, 740, 556], "war-fixed-bottom")
            strips = []
            for name, relative in (("top", [0, 0, 301, 3]), ("bottom", [0, 33, 301, 36]),
                                   ("left", [0, 0, 3, 36]), ("right", [298, 0, 301, 36])):
                rect = [250 + relative[0], 475 + relative[1], 250 + relative[2], 475 + relative[3]]
                row = reference(root, root / "war.png", rect, "dynamic-" + name)
                row["relative_rect"] = relative
                strips.append(row)
            variant["button_geometry"] = {"search_rect": [200, 400, 600, 550],
                "width_range": [300, 302], "height_range": [35, 37],
                "strips": strips, "action_inset": [20, 4, 20, 6]}
            router = PixelRouter(p["routing"])
            original = router.route(root / "war.png")
            moved = root / "moved-war.png"
            raw = Image.open(root / "war.png")
            draw = ImageDraw.Draw(raw)
            draw.rectangle((250, 475, 550, 510), fill=(35, 30, 25))
            draw.rectangle((250, 425, 550, 460), outline=(200, 170, 80), width=3)
            glyphs(raw, [270, 429, 530, 455])
            raw.save(moved)
            current = router.route(moved)
            self.assertEqual(current["action"], "Escape")
            self.assertTrue(same_action(original, current))
            self.assertTrue(same_window(original, current))

    def test_neutral_borders_and_body_icons_keep_physical_first(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            p = profile(root)
            source = image(root, "neutral.png", count=3)
            raw = Image.open(source)
            draw = ImageDraw.Draw(raw)
            for index in range(2, 5):
                top = 340 + index*42
                draw.rectangle((150, top, 650, top+33), outline=(80, 82, 84), width=1)
            glyphs(raw, [170, 302, 610, 328])
            raw.save(source)
            router = PixelRouter(p["routing"])
            self.assertEqual(router.route(source)["option_count"], 3)
            # A dim physical first is still rejected rather than skipping it.
            draw.rectangle((170, 432, 610, 445), fill=(35, 30, 25))
            glyphs(raw, [170, 428, 610, 454], value=(150,150,150))
            raw.save(source)
            with self.assertRaisesRegex(NeedsOperator, "first option dim"):
                router.route(source)

    def test_absent_light_title_is_exact_and_body_does_not_release_action(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            router = PixelRouter(profile(root)["routing"])
            routes = []
            for seed in (0, 1):
                source = image(root, f"untitled-{seed}.png", seed=seed)
                raw = Image.open(source)
                ImageDraw.Draw(raw).rectangle((100, 80, 650, 110), fill=(35,30,25))
                raw.save(source)
                routes.append(router.route(source))
            self.assertEqual(routes[0]["shapes"]["title"]["pixels"], 0)
            self.assertTrue(same_window(routes[0], routes[0]))
            self.assertTrue(same_action(*routes))
            self.assertFalse(same_window(*routes))


class RunnerTests(unittest.TestCase):
    def test_default_analysis_sends_zero_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            p = profile(root)
            backend = FakeBackend([root / "standard.png"])
            result = assist(p, backend, sleep=lambda _: None)
            self.assertEqual(result["status"], "READY_FOR_OPERATOR_REVIEW")
            self.assertEqual(backend.keys, [])
            self.assertEqual(result["century_credit"], "NONE_FROM_UI_ASSIST")

    def test_war_escape_closure_only_records_ui_disappearance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            p = profile(root)
            backend = FakeBackend([root / "war.png"]*2 + [root / "map.png"]*2)
            result = assist(p, backend, execute=True, sleep=lambda _: None)
            self.assertEqual(backend.keys, ["Escape"])
            self.assertEqual(result["status"], "UI_DISAPPEARED_ROUTING_ONLY")
            self.assertEqual(result["business_result"], "NOT_VERIFIED")
            attempt = Path(result["attempt"])
            for name in ("intent.json", "before-a.png", "before-b.png", "after-a.png", "after-b.png"):
                self.assertTrue((attempt / "step-01" / name).is_file())
            self.assertTrue((attempt / "closed-operator-lock.json").is_file())

    def test_unchanged_after_ack_stops_without_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            p = profile(root)
            backend = FakeBackend([root / "standard.png"])
            result = assist(p, backend, execute=True, max_actions=3, sleep=lambda _: None)
            self.assertEqual(backend.keys, ["Shift+1"])
            self.assertEqual(result["status"], "NEEDS_OPERATOR")
            self.assertIn("no automatic retry", result["error"])

    def test_uncertain_input_reserved_across_attempts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            p = profile(root)
            first = FakeBackend([root / "standard.png"], ack=RuntimeError("synthetic transport uncertainty"))
            old = assist(p, first, execute=True, sleep=lambda _: None)
            next_backend = FakeBackend([root / "standard.png"])
            new = assist(p, next_backend, execute=True, sleep=lambda _: None)
            self.assertEqual(old["status"], "NEEDS_OPERATOR")
            self.assertEqual(new["status"], "NEEDS_OPERATOR")
            self.assertEqual(next_backend.keys, [])
            self.assertTrue((Path(old["attempt"]) / "result.json").exists())

    def test_guard_failure_and_deadline_send_zero_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            p = profile(root)
            for backend in (FakeBackend([root / "standard.png"], fail_at_guard=1),
                            FakeBackend([root / "standard.png"], fail_at_guard=6)):
                result = assist(p, backend, execute=True, sleep=lambda _: None)
                self.assertEqual(result["status"], "NEEDS_OPERATOR")
                self.assertEqual(backend.keys, [])
            p["normal_save_due_utc"] = datetime.now(timezone.utc).isoformat()
            backend = FakeBackend([root / "standard.png"])
            result = assist(p, backend, execute=True, sleep=lambda _: None)
            self.assertEqual(backend.keys, [])

    def test_existing_lock_is_preserved_and_no_input_occurs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            p = profile(root)
            Path(p["evidence_directory"]).mkdir()
            lock = Path(p["evidence_directory"]) / "operator.lock"
            lock.write_bytes(b"original-custodian")
            backend = FakeBackend([root / "standard.png"])
            result = assist(p, backend, execute=True, sleep=lambda _: None)
            self.assertEqual(result["status"], "NEEDS_OPERATOR")
            self.assertEqual(lock.read_bytes(), b"original-custodian")
            self.assertEqual(backend.keys, [])

    def test_mixed_post_restarts_independent_stable_preflight(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            p = profile(root)
            backend = FakeBackend([root/"war.png"]*2 + [root/"map.png",root/"standard.png"]
                                  + [root/"standard.png"]*2 + [root/"map.png"]*2)
            result = assist(p, backend, execute=True, max_actions=2, sleep=lambda _: None)
            self.assertEqual(backend.keys, ["Escape", "Shift+1"])
            self.assertEqual(result["steps"][0]["status"], "UNCONFIRMED_PENDING_NEXT_STABLE_ROUTE")
            self.assertTrue(result["steps"][0]["next_input_requires_independent_stable_route"])
            self.assertEqual(result["status"], "UI_DISAPPEARED_ROUTING_ONLY")
            self.assertEqual(result["business_result"], "NOT_VERIFIED")

    def test_unknown_post_stops_and_preserves_both_samples(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            p = profile(root)
            unknown = root / "unknown.png"
            Image.new("RGB", SIZE, "black").save(unknown)
            backend = FakeBackend([root/"war.png"]*2 + [root/"map.png",unknown])
            result = assist(p, backend, execute=True, max_actions=3, sleep=lambda _: None)
            self.assertEqual(backend.keys, ["Escape"])
            self.assertEqual(result["status"], "NEEDS_OPERATOR")
            self.assertTrue((Path(result["attempt"])/"step-01/after-a.png").is_file())
            self.assertTrue((Path(result["attempt"])/"step-01/after-b.png").is_file())

    def test_new_helper_directory_preserves_inherited_uncertain_action(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            p = profile(root)
            first = FakeBackend([root/"standard.png"], ack=RuntimeError("uncertain original input"))
            assist(p, first, execute=True, sleep=lambda _: None)
            old = Path(p["evidence_directory"])/"action-ledger.jsonl"
            p["inherited_ledgers"] = [{"path": str(old), "sha256": sha256(old)}]
            p["evidence_directory"] = str(root/"new-helper-attempts")
            second = FakeBackend([root/"standard.png"])
            result = assist(p, second, execute=True, sleep=lambda _: None)
            self.assertEqual(result["status"], "NEEDS_OPERATOR")
            self.assertEqual(second.keys, [])
            self.assertIn("already reserved", result["error"])

    def test_win32_input_abi_includes_mouse_union(self):
        self.assertEqual(abi(), {4: (28, 16, 4, 48), 8: (40, 24, 8, 72)}[ctypes.sizeof(HANDLE)])

    def test_production_guard_rejects_actual_custody_mismatches_without_ui(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            p = profile(root)
            cli = root / "bus.py"
            cli.write_bytes(b"synthetic pinned CLI")
            exe = root / "ck3.exe"
            exe.write_bytes(b"synthetic pinned EXE")
            control = root / "control.json"
            write_new(control, {"ck3_pid": 10, "executable": str(exe)})
            p["owner"].update(pid=10, process_create_time=12.0, repo=str(root), head="frozen-head",
                screen_task="original-screen", bus_dir=str(root), bus_cli={"path": str(cli), "sha256": sha256(cli)},
                executable={"path": str(exe), "sha256": sha256(exe)},
                control={"path": str(control), "sha256": sha256(control)})
            rows = [{"task_id": "original-screen", "state": "running", "resources": ["ck3-screen:acquired"],
                     "updated_at_utc": datetime.now(timezone.utc).isoformat()}]
            values = {"create": 12.0, "foreground_pid": 10, "head": "frozen-head", "dirty": b"", "inventory": [10]}
            fake = {
                "psutil": SimpleNamespace(Process=lambda pid: SimpleNamespace(create_time=lambda: values["create"], exe=lambda: str(exe)),
                    process_iter=lambda attrs: [SimpleNamespace(pid=pid, info={"name": "ck3.exe"}) for pid in values["inventory"]]),
                "pyautogui": SimpleNamespace(size=lambda: SIZE),
                "win32gui": SimpleNamespace(GetForegroundWindow=lambda: 11, IsWindowVisible=lambda hwnd: True,
                    IsIconic=lambda hwnd: False),
                "win32process": SimpleNamespace(GetWindowThreadProcessId=lambda hwnd: (13, values["foreground_pid"])),
            }
            def read(command, **kwargs):
                if command[-1] == "list":
                    return json.dumps({"tasks": rows}).encode()
                if command[-1] == "HEAD":
                    return (values["head"] + "\n").encode()
                return values["dirty"]
            backend = OwnedWindowsBackend.__new__(OwnedWindowsBackend)
            with patch.dict("sys.modules", fake), patch("subprocess.check_output", side_effect=read):
                self.assertEqual(backend.guard(p)["pid"], 10)
                for field, bad in (("create", 100.0), ("foreground_pid", 999), ("head", "different"),
                                   ("dirty", b" M owned.py"), ("inventory", [10, 20])):
                    with self.subTest(field=field):
                        old = values[field]
                        values[field] = bad
                        with self.assertRaises(NeedsOperator):
                            backend.guard(p)
                        values[field] = old
                old = rows[0]["updated_at_utc"]
                rows[0]["updated_at_utc"] = (datetime.now(timezone.utc)-timedelta(seconds=601)).isoformat()
                with self.assertRaisesRegex(NeedsOperator, "lease"):
                    backend.guard(p)
                rows[0]["updated_at_utc"] = old
                rows.append(copy.deepcopy(rows[0]))
                with self.assertRaisesRegex(NeedsOperator, "not unique"):
                    backend.guard(p)


def save(root, name, saved_date, actor=17):
    text = (f'meta_data={{\n\tversion="synthetic-game"\n\tmeta_date={saved_date}\n'
            '\tmeta_number_of_players=1\n}\n'
            f'played_character={{\n\tcharacter={actor}\n\tplayer=1\n}}\n'
            f'currently_played_characters={{ {actor} }}\n')
    path = root / name
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("gamestate", text)
    return {"path": str(path), "sha256": sha256(path)}


def chain(root, actor=17):
    before, after = save(root, "before.ck3", "1066.9.15"), save(root, "after.ck3", "1166.9.15", actor)
    evidence = root / "synthetic-evidence.json"
    write_new(evidence, {"synthetic_only": True})
    ref = {"path": str(evidence), "sha256": sha256(evidence)}
    retired = root / "retirement.json"
    write_new(retired, {"schema": "ck3.stability-normal-retirement.v1", "run_id": "synthetic-epoch",
                       "pid": 20, "exit_code": 0, "normal_save_then_exit": True,
                       "process_inventory_empty": True, "keeper_stopped": True, "screen_released": True,
                       "save_sha256": after["sha256"], "evidence": [ref]})
    return {"schema": "ck3.stability-save-chain.v1", "closed_only": True,
            "start_date": "1066.9.15", "target_years": 100, "game_version": "synthetic-game",
            "epochs": [{"run_id": "synthetic-epoch", "load": before, "end": after,
                        "retirement": {"path": str(retired), "sha256": sha256(retired)},
                        "natural_progress_evidence": [ref]}]}


class ChainTests(unittest.TestCase):
    def test_target_met_is_date_continuity_not_stability_green(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = verify_chain(chain(Path(temporary)))
            self.assertEqual(report["status"], "CLOSED_CHAIN_TARGET_REACHED")
            self.assertEqual(report["stability_result"], "NOT_GRADED")
            self.assertEqual(report["gameplay_evidence_review"], "REQUIRED")

    def test_incomplete_date_is_not_target_reached(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = chain(root)
            source["target_years"] = 101
            self.assertEqual(verify_chain(source)["status"], "CLOSED_CHAIN_INCOMPLETE")

    def test_actor_change_requires_natural_succession_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = chain(root, actor=18)
            with self.assertRaisesRegex(NeedsOperator, "natural succession"):
                verify_chain(source)
            source["epochs"][0]["natural_succession_evidence"] = source["epochs"][0]["natural_progress_evidence"]
            self.assertEqual(verify_chain(source)["status"], "CLOSED_CHAIN_TARGET_REACHED")

    def test_live_chain_and_hash_change_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = chain(root)
            source["closed_only"] = False
            with self.assertRaisesRegex(NeedsOperator, "closed attempts"):
                verify_chain(source)
            source["closed_only"] = True
            Path(source["epochs"][0]["end"]["path"]).write_bytes(b"changed-save")
            with self.assertRaisesRegex(NeedsOperator, "pinned file changed"):
                verify_chain(source)

    def test_duplicate_player_and_parent_date_do_not_credit_chain(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = chain(root)
            source["start_date"] = "1066.9.14"
            with self.assertRaisesRegex(NeedsOperator, "start date differs"):
                verify_chain(source)
            path = root / "duplicates.ck3"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("gamestate", 'meta_data={\n\tversion="v"\n\tmeta_date=1066.1.1\n'
                    '\tmeta_number_of_players=1\n}\nplayed_character={\n\tcharacter=1\n\tplayer=1\n}\n'
                    'currently_played_characters={ 1 2 }\n')
            with self.assertRaisesRegex(NeedsOperator, "binding differs"):
                closed_save({"path": str(path), "sha256": sha256(path)})


if __name__ == "__main__":
    unittest.main()
