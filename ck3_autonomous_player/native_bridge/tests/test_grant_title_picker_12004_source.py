"""Finite source/pin projection checks; never native or gameplay acceptance.

These checks run on copied source bytes, including under Python -O. The
optional frozen capture receipt validates the exact native body projection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CAPTURE_ROOT: Path | None = None


def pin_arrays(text: str, prefix: str) -> dict[int, bytes]:
    pattern = rf"std::array<unsigned char,(\d+)> {prefix}(\d+)\{{([^}}]+)\}};"
    result: dict[int, bytes] = {}
    for length, index, literal in re.findall(pattern, text):
        data = bytes(int(token.strip(), 16) for token in literal.split(","))
        if len(data) != int(length):
            raise ValueError("declared native body size differs from literal")
        result[int(index)] = data
    return result


class GrantTitlePicker12004Source(unittest.TestCase):
    def test_actual4_profile_has_individual_entries_and_primary_types(self) -> None:
        source = (ROOT / "include/xar_bridge/ck3_12004_grant_title_picker_profile.hpp").read_text()
        initializer = source.split("kGrantTitlePickerImageProfile12004V1{", 1)[1].split("};", 1)[0]
        values = [int(x, 16) for x in re.findall(r"0x[0-9A-Fa-f]+", initializer)]
        self.assertEqual(values, [
            0x44D6058, 0x55072C0, 0x44BC418, 0x5514460,
            0x44BA8A0, 0x5694B20, 0x452DBE8, 0x5742F58,
            0x45250E8, 0x5731D88, 0x4712A28,
            0x10EC1F0, 0x10EC2F0, 0x10EC4B0, 0x10EC0E0,
            0x117C520, 0x117BAD0, 0x10E6FE0, 0xAF34A0,
            0x10E7800, 0x2160380,
        ])
        self.assertIn("GuiAbiRevisionV1::crozier12004", initializer)

    def test_complete_actual4_native_bodies_cover_dispatch_and_moved_guard(self) -> None:
        source = (ROOT / "src/grant_title_picker_pins_12004_v1.inc").read_text()
        arrays = pin_arrays(source, "kGrant12004Pin")
        rows = [(int(rva, 16), int(index)) for rva, index in re.findall(
            r"\{(0x[0-9a-fA-F]+),kGrant12004Pin(\d+)\}", source)]
        self.assertEqual([rva for rva, _ in rows], [
            0x10E5CD0, 0x10EC1F0, 0x10EC2F0, 0x10EC4B0,
            0x10EC0E0, 0x117C520, 0x117BAD0, 0x10E6FE0,
            0xAF34A0, 0x117EFE0, 0x10E7800, 0x2160380, 0x10E7A80,
        ])
        self.assertEqual(len(arrays), 13)
        self.assertEqual(max(map(len, arrays.values())), 1358)
        # Actual .4 moved the definition-kind guard into the called updater.
        update = arrays[12]
        # Inspect exact documented operands rather than equating changed bodies.
        self.assertIn(bytes.fromhex("4489b1dc110000"), update)
        self.assertIn(bytes.fromhex("80bbfa260000010f85fd000000"), update)
        if CAPTURE_ROOT is not None:
            report = json.loads((CAPTURE_ROOT / "PROJECT-ACTUAL4-PINS-001.actual.json").read_text())
            self.assertEqual(report["grant_include_sha256"], hashlib.sha256(source.encode()).hexdigest())
            self.assertEqual(report["future_pass"], None)
            self.assertEqual(report["whole_status"], "NOT_GREEN")
            for (_, index), body in zip(rows, report["grant_complete_bodies"], strict=True):
                self.assertEqual(len(arrays[index]), body["bytes"])
                self.assertEqual(hashlib.sha256(arrays[index]).hexdigest(), body["sha256"])

    def test_actual4_context_and_command_dependencies_are_not_legacy_binders(self) -> None:
        source = (ROOT / "src/ordinary_character_interaction_v1.cpp").read_text()
        binder = source.split("Bindings BindOrdinaryInteractionImage12004(", 1)[1].split(
            "bool ReadOrdinaryInteractionContextV1", 1)[0]
        self.assertIn("sha != ck3_12004::kExecutableSha256", binder)
        self.assertIn("ck3_12004::BindInteractionContext12004", binder)
        self.assertIn("ck3_12004::BindCommandImage12004", binder)
        self.assertNotIn("BindOrdinaryInteractionImage12003", binder)
        self.assertNotIn("BindCoreImage12003", binder)
        self.assertIn("0x307C340", binder)
        self.assertIn("0x3079690", binder)
        self.assertIn("0x3078860", binder)

    def test_version_selected_prefixes_preserve_twenty_actual4_pins(self) -> None:
        source = (ROOT / "src/ordinary_interaction_code_pins_12004_v1.inc").read_text()
        rows = re.findall(r"\{(0x[0-9A-Fa-f]+), \{\{([^}]+)\}\}\}", source)
        self.assertEqual(len(rows), 20)
        self.assertEqual([int(rva, 16) for rva, _ in rows], [
            0x89DA60, 0x3F7E220, 0xA055E0, 0x3076C70, 0x3079690,
            0x30788C0, 0x3078860, 0x307BC60, 0x3076E30, 0x3078A40,
            0x3078C70, 0x307C020, 0x3077380, 0x2968150, 0x37F06D0,
            0x3148DC0, 0x310CEC0, 0x372DF10, 0x307C440, 0x307C340,
        ])
        for _, literal in rows:
            self.assertEqual(len(literal.split(",")), 32)
        mailbox = (ROOT / "src/ordinary_interaction_mailbox_v1.cpp").read_text()
        self.assertIn("executable_sha256 == ck3_12004::kExecutableSha256", mailbox)
        self.assertIn("if (pins == nullptr) return false", mailbox)
        self.assertIn("game::IsCk3_12004Descriptor(envelope->game->descriptor())", mailbox)

    def test_full_id_frame_selection_warning_and_transfer_checks_remain(self) -> None:
        source = (ROOT / "src/grant_title_picker_v1.cpp").read_text()
        for required in [
            "observed!=id", "returned_id!=id", "recipient!=c.recipient_character_full_id",
            "env.gui_abi_revision!=profile->gui_revision", "!OrdinaryPins(env.module_base,profile->actual4)",
            "before!=c.expected_snapshot", "dispatch!=before", "first!=second", "after!=stable",
            "SameIds(first.observation.selected_title_full_ids,c.expected_selected_title_full_ids)",
            "stock_grant_warning_confirmation_required", "selected_title_holder_changed",
            "h.holder_character_full_id==c.recipient_character_full_id&&out.transfer_verified",
            "business_full_credit\\\":false", "kImageProfile12003", "GrantPins(env.module_base)",
        ]:
            self.assertIn(required, source)
        self.assertIn("game::IsCk3_12004Descriptor(d)", source)
        self.assertIn("return nullptr", source.split("const ImageProfile *Profile", 1)[1].split("bool Bytes", 1)[0])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-root", type=Path)
    args, remaining = parser.parse_known_args()
    CAPTURE_ROOT = args.capture_root
    unittest.main(argv=[__file__, *remaining])
