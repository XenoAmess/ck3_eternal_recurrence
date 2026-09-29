"""No-game exact target/userdir admission for the reviewed a04 GUI block."""

import argparse
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from capture_session import (
    A04_UI_SOURCE_ROOT, A04_UI_TARGETS, bind_a04_ui_target,
    checkpoint_source, gui_scale_disk_readback, prepare_a05_ui_settings,
    validate_a04_ui_gui_source_binding,
)


EVIDENCE = (A04_UI_SOURCE_ROOT /
            "episode02-e2-04-d05-screen-lease-20260928-a04")
UI_SOURCE = EVIDENCE / "native-ui-saved-settings-a01.pdx.txt"
UI_RECEIPT = EVIDENCE / "native-ui-saved-settings-a01.json"


def source_for(track: str) -> dict:
    spec = A04_UI_TARGETS[track]
    return {
        "save": {"path": str(A04_UI_SOURCE_ROOT / spec["save"][0]),
                 "bytes": spec["save"][1], "sha256": spec["save"][2]},
        "receipt": {"path": str(A04_UI_SOURCE_ROOT / spec["receipt"][0]),
                    "bytes": spec["receipt"][1], "sha256": spec["receipt"][2]},
        "actor": spec["actor"], "date_raw": spec["date_raw"],
        "source_episode_run_id": spec["source_episode_run_id"],
    }


def arguments(track: str, *, root: Path | None = None) -> argparse.Namespace:
    spec = A04_UI_TARGETS[track]
    attempt = root or (A04_UI_SOURCE_ROOT / (spec["attempt_prefix"] + "static-test"))
    return argparse.Namespace(
        import_a04_ui_gui_100=True, gui_scale="1.0", record_debug_desktop=False,
        checkpoint_save=A04_UI_SOURCE_ROOT / spec["save"][0],
        checkpoint_receipt=A04_UI_SOURCE_ROOT / spec["receipt"][0],
        a04_ui_settings_snapshot=UI_SOURCE,
        a04_ui_preservation_receipt=UI_RECEIPT,
        state_dir=attempt / "ck3-state", output_dir=attempt / "ck3-output",
    )


class A04UiTargetTest(unittest.TestCase):
    def test_four_frozen_tracks_bind_distinct_actual_userdirs(self) -> None:
        for track in A04_UI_TARGETS:
            with self.subTest(track=track):
                args = arguments(track)
                binding = bind_a04_ui_target(args, source_for(track))
                self.assertEqual(binding["track"], track)
                self.assertEqual(binding["userdir"], str(args.state_dir.resolve() / "profile"))
                self.assertEqual(binding["output_dir"], str(args.output_dir.resolve()))

    def test_d11_wrong_source_pair_actor_date_or_run_refuses(self) -> None:
        valid = source_for("e2-06-d11")
        mutations = (
            ("save", "sha256", "0" * 64),
            ("save", "bytes", valid["save"]["bytes"] + 1),
            ("receipt", "sha256", "0" * 64),
            ("receipt", "path", str(A04_UI_SOURCE_ROOT / "wrong-sidecar.json")),
            (None, "actor", 30097),
            (None, "date_raw", valid["date_raw"] + 24),
            (None, "source_episode_run_id", "another-run"),
        )
        for parent, field, value in mutations:
            with self.subTest(parent=parent, field=field):
                changed = deepcopy(valid)
                (changed[parent] if parent else changed)[field] = value
                with self.assertRaisesRegex(RuntimeError, "exact allowed track/source pair"):
                    bind_a04_ui_target(arguments("e2-06-d11"), changed)

    def test_d06_wrong_source_pair_actor_date_or_run_refuses(self) -> None:
        valid = source_for("e2-04-d06")
        mutations = (
            ("save", "path", str(A04_UI_SOURCE_ROOT / "other" / "d06-immutable.ck3")),
            ("save", "sha256", A04_UI_TARGETS["e2-04-d05"]["save"][2]),
            ("save", "bytes", valid["save"]["bytes"] + 1),
            ("receipt", "path", str(A04_UI_SOURCE_ROOT / "other" / "e2-04-d05-postframe-save.json")),
            ("receipt", "sha256", "0" * 64),
            ("receipt", "bytes", valid["receipt"]["bytes"] + 1),
            (None, "actor", 30097),
            (None, "date_raw", 53146344),
            (None, "source_episode_run_id", "native-29829-78c0d8f4b8a2"),
        )
        for parent, field, value in mutations:
            with self.subTest(parent=parent, field=field):
                changed = deepcopy(valid)
                (changed[parent] if parent else changed)[field] = value
                with self.assertRaisesRegex(RuntimeError, "exact allowed track/source pair"):
                    bind_a04_ui_target(arguments("e2-04-d06"), changed)

    def test_d06_source_cannot_enter_other_track_or_mixed_attempt(self) -> None:
        source = source_for("e2-04-d06")
        for other in ("e2-04-d05", "e2-05-d26", "e2-06-d11"):
            with self.subTest(other=other):
                with self.assertRaisesRegex(RuntimeError, "userdir/state/output"):
                    bind_a04_ui_target(arguments(other), source)
        args = arguments("e2-04-d06")
        args.output_dir = (A04_UI_SOURCE_ROOT /
                           "episode02-e2-04-d06-another-attempt" / "ck3-output")
        with self.assertRaisesRegex(RuntimeError, "userdir/state/output"):
            bind_a04_ui_target(args, source)

    @unittest.skipUnless((A04_UI_SOURCE_ROOT / A04_UI_TARGETS["e2-04-d06"]["save"][0]).is_file() and
                         (A04_UI_SOURCE_ROOT / A04_UI_TARGETS["e2-04-d06"]["receipt"][0]).is_file(),
                         "Frozen external d06 save and sidecar are unavailable")
    def test_real_d06_save_and_sidecar_bind_exactly(self) -> None:
        args = arguments("e2-04-d06")
        checkpoint = checkpoint_source(args.checkpoint_save, args.checkpoint_receipt)
        self.assertEqual(checkpoint["source_episode_run_id"], "native-29829-0a9929135691")
        self.assertEqual(checkpoint["date_raw"], 53146368)
        self.assertEqual(bind_a04_ui_target(args, checkpoint)["track"], "e2-04-d06")

    def test_d11_source_cannot_enter_d05_or_d26_userdir(self) -> None:
        source = source_for("e2-06-d11")
        for other in ("e2-04-d05", "e2-05-d26"):
            with self.subTest(other=other):
                with self.assertRaisesRegex(RuntimeError, "userdir/state/output"):
                    bind_a04_ui_target(arguments(other), source)

    def test_d11_state_output_must_be_one_isolated_attempt(self) -> None:
        source = source_for("e2-06-d11")
        for change in (
            {"state_dir": A04_UI_SOURCE_ROOT / "episode02-e2-06-d11-static-test" / "wrong-state"},
            {"output_dir": A04_UI_SOURCE_ROOT / "episode02-e2-06-d11-other" / "ck3-output"},
            {"state_dir": A04_UI_SOURCE_ROOT / "episode02-e2-04-d05-wrong" / "ck3-state"},
        ):
            with self.subTest(change=change):
                args = arguments("e2-06-d11")
                for key, value in change.items():
                    setattr(args, key, value)
                with self.assertRaisesRegex(RuntimeError, "userdir/state/output"):
                    bind_a04_ui_target(args, source)

    @unittest.skipUnless(UI_SOURCE.is_file() and UI_RECEIPT.is_file() and
                         (A04_UI_SOURCE_ROOT / A04_UI_TARGETS["e2-05-d26"]["save"][0]).is_file() and
                         (A04_UI_SOURCE_ROOT / A04_UI_TARGETS["e2-05-d26"]["receipt"][0]).is_file(),
                         "Frozen external d26 and a04 UI evidence is unavailable")
    def test_real_existing_d26_pair_remains_admitted(self) -> None:
        args = arguments("e2-05-d26")
        checkpoint = checkpoint_source(args.checkpoint_save, args.checkpoint_receipt)
        binding = validate_a04_ui_gui_source_binding(args, checkpoint)
        self.assertEqual(binding["target"]["track"], "e2-05-d26")
        self.assertEqual(binding["target"]["source_checkpoint"], checkpoint)

    @unittest.skipUnless(UI_SOURCE.is_file() and UI_RECEIPT.is_file() and
                         (A04_UI_SOURCE_ROOT / A04_UI_TARGETS["e2-06-d11"]["save"][0]).is_file() and
                         (A04_UI_SOURCE_ROOT / A04_UI_TARGETS["e2-06-d11"]["receipt"][0]).is_file(),
                         "Frozen external d11 and a04 UI evidence is unavailable")
    def test_real_d11_source_imports_only_gui_into_same_bound_profile(self) -> None:
        with tempfile.TemporaryDirectory(dir=A04_UI_SOURCE_ROOT,
                                         prefix="episode02-e2-06-d11-static-test-") as directory:
            root = Path(directory)
            args = arguments("e2-06-d11", root=root)
            output = args.output_dir
            profile = args.state_dir / "profile"
            output.mkdir()
            profile.mkdir(parents=True)
            checkpoint = checkpoint_source(args.checkpoint_save, args.checkpoint_receipt)
            binding = validate_a04_ui_gui_source_binding(args, checkpoint)
            self.assertEqual(binding["target"]["track"], "e2-06-d11")
            self.assertEqual(binding["target"]["source_checkpoint"], checkpoint)
            settings = profile / "pdx_settings.txt"
            template = '"Graphics"={}\n"Audio"={}\n'
            prepared = prepare_a05_ui_settings(settings, template, output, binding)
            expected = template.encode() + UI_SOURCE.read_bytes()[6642:6696]
            self.assertEqual(settings.read_bytes(), expected)
            self.assertEqual(prepared["target"]["userdir"], str(profile.resolve()))
            gate = gui_scale_disk_readback(
                settings, "1.0", "d11-static", allow_native_ui_one=True,
                require_native_a04_gui_block=True)
            self.assertTrue(gate["disk_gate_passed"])
            self.assertTrue(gate["native_a04_gui_block_passed"])
            self.assertFalse(gate["runtime_scale_proven"])
            with tempfile.TemporaryDirectory(dir=A04_UI_SOURCE_ROOT,
                                             prefix="episode02-e2-06-d11-other-") as other:
                wrong_profile = Path(other) / "ck3-state" / "profile"
                wrong_profile.mkdir(parents=True)
                wrong_output = Path(other) / "ck3-output"
                wrong_output.mkdir()
                with self.assertRaisesRegex(RuntimeError, "target userdir/output"):
                    prepare_a05_ui_settings(
                        wrong_profile / "pdx_settings.txt", template,
                        wrong_output, binding)


if __name__ == "__main__":
    unittest.main()
