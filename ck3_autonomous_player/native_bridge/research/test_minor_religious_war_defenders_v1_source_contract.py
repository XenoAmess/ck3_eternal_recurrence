"""Exact-build and default-OFF source contract for slot49."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import unittest

import pefile


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
CONTRACT = json.loads(
    (ROOT / "research" / "minor_religious_war_defenders_v1_contract.json")
    .read_text(encoding="utf-8")
)


class MinorReligiousWarDefendersSourceContractTest(unittest.TestCase):
    def test_exact_executable_and_native_spans(self) -> None:
        configured = os.environ.get("XAR_CK3_EXECUTABLE_PATH")
        executable = (
            Path(configured)
            if configured
            else REPO / "Crusader Kings III" / "binaries" / "ck3.exe"
        )
        if not executable.is_file():
            self.skipTest("exact CK3 executable is unavailable")
        self.assertEqual(
            hashlib.sha256(executable.read_bytes()).hexdigest().upper(),
            CONTRACT["ck3_exe_sha256"],
        )
        pe = pefile.PE(str(executable), fast_load=True)
        for prefix in ("collector", "real_war_caller", "append_helper"):
            rva = int(CONTRACT["native"][prefix + "_rva"], 16)
            size = CONTRACT["native"][prefix + "_span_size"]
            self.assertEqual(
                hashlib.sha256(pe.get_data(rva, size)).hexdigest().upper(),
                CONTRACT["native"][prefix + "_span_sha256"],
            )

    def test_default_off_slot49_and_private_wire(self) -> None:
        cmake = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
        option = CONTRACT["private_wire"]["cmake_option"]
        self.assertIn(f"  {option}\n", cmake)
        option_tail = cmake.split(f"  {option}\n", 1)[1].split(")", 1)[0]
        self.assertIn("\n  OFF\n", option_tail)
        self.assertIn("src/minor_religious_war_defenders_v1.cpp", cmake)
        self.assertIn(
            "src/minor_religious_war_defenders_private_wire_v1.cpp", cmake
        )
        mailbox = (
            ROOT / "include" / "xar_bridge" / "main_thread_query_mailbox_v1.hpp"
        ).read_text(encoding="utf-8")
        bridge = (ROOT / "src" / "bridge.cpp").read_text(encoding="utf-8")
        wire_header = (
            ROOT / "include" / "xar_bridge"
            / "minor_religious_war_defenders_private_wire_v1.hpp"
        ).read_text(encoding="utf-8")
        self.assertIn("slot 49", mailbox)
        self.assertIn("permitted_executor_novemquadragintary", mailbox)
        self.assertIn(
            "ExecuteMinorReligiousWarDefendersPrivateQueryV1", bridge
        )
        self.assertIn(
            CONTRACT["private_wire"]["step"].split("<", 1)[0], wire_header
        )

    def test_full_generation_and_power_roundtrip_are_mandatory(self) -> None:
        source = (
            ROOT / "src" / "minor_religious_war_defenders_v1.cpp"
        ).read_text(encoding="utf-8")
        wire = (
            ROOT / "src" / "minor_religious_war_defenders_private_wire_v1.cpp"
        ).read_text(encoding="utf-8")
        self.assertIn("identity != full_id", source)
        self.assertIn("ResolveCharacter(env, access, id) != candidate", source)
        self.assertIn("kPowerContainerOffset", source)
        self.assertIn("same_frame_power_leaf_mismatch", wire)
        self.assertGreaterEqual(wire.count("SameFrame(access)"), 2)
        self.assertNotIn("SubmitDeclareWar", wire)

    def test_python_route_is_opt_in_and_not_a_public_mcp_tool(self) -> None:
        driver = (
            REPO / "ck3_autonomous_player" / "src" / "xar_autoplayer"
            / "bridge" / "native_driver.py"
        ).read_text(encoding="utf-8")
        mcp = (
            REPO / "ck3_autonomous_player" / "src" / "xar_autoplayer"
            / "bridge" / "mcp_server.py"
        ).read_text(encoding="utf-8")
        service = (
            REPO / "ck3_autonomous_player" / "src" / "xar_autoplayer"
            / "bridge" / "service.py"
        ).read_text(encoding="utf-8")
        flag = CONTRACT["private_wire"]["native_driver_opt_in"]
        self.assertIn(f"{flag}: bool = False", driver)
        self.assertIn("query_minor_religious_war_defenders_private_v1", driver)
        self.assertEqual(
            mcp.count("def _ck3_query_minor_religious_war_defenders_private_v1"),
            1,
        )
        self.assertNotIn("@server.tool()\n    def ck3_query_minor_religious", mcp)
        self.assertNotIn("minor_religious_war_defenders", service)


if __name__ == "__main__":
    unittest.main()
