from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
HEADER = ROOT / "native_bridge/include/xar_bridge/zhongguo_incident_snapshot_v1.hpp"
READER = ROOT / "native_bridge/src/zhongguo_incident_snapshot_v1.cpp"
SERIALIZER = ROOT / "native_bridge/src/zhongguo_incident_snapshot_v1_serializer.cpp"
MAILBOX = ROOT / "native_bridge/src/zhongguo_incident_snapshot_v1_mailbox.cpp"
MAILBOX_HEADER = ROOT / "native_bridge/include/xar_bridge/zhongguo_incident_snapshot_v1_mailbox.hpp"
ABI = ROOT / "native_bridge/research/zhongguo_incident_snapshot_v1_abi.json"
FIXTURE = ROOT / "native_bridge/research/fixtures/zhongguo_incident_snapshot_v1_source_contract.json"
SCHEMA = ROOT / "schemas/zhongguo-incident-snapshot-v1.schema.json"
EFFECTS = REPO / "mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_runtime_effects.txt"


def _allowlist(header: str, profile: str) -> list[str]:
    match = re.search(
        rf"kZhongguoIncidentSnapshotV1{profile.upper()}Allowlist\{{(.*?)\}};",
        header,
        re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"missing {profile} allowlist")
    return re.findall(r'"(zg361_ip_[^"]+)"', match.group(1))


class ZhongguoIncidentSnapshotScaffoldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.reader = READER.read_text(encoding="utf-8")
        cls.serializer = SERIALIZER.read_text(encoding="utf-8")
        cls.mailbox = MAILBOX.read_text(encoding="utf-8")
        cls.mailbox_header = MAILBOX_HEADER.read_text(encoding="utf-8")
        cls.effects = EFFECTS.read_text(encoding="utf-8-sig")
        cls.abi = json.loads(ABI.read_text(encoding="utf-8"))
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        json.loads(SCHEMA.read_text(encoding="utf-8"))

    def test_three_allowlists_are_fixed_exact_and_mod_backed(self) -> None:
        lists = {
            profile: _allowlist(self.header, profile)
            for profile in ("x", "y", "z")
        }
        for profile, keys in lists.items():
            with self.subTest(profile=profile):
                self.assertEqual(len(keys), 49)
                self.assertEqual(len(set(keys)), 49)
                self.assertEqual(
                    keys[:9],
                    [
                        "zg361_ip_probe_owner",
                        "zg361_ip_probe_subject",
                        "zg361_ip_probe_cycle",
                        "zg361_ip_probe_serial",
                        "zg361_ip_probe_result",
                        "zg361_ip_probe_source_kind",
                        "zg361_ip_probe_consequence_kind",
                        "zg361_ip_probe_subject_gold",
                        "zg361_ip_probe_capital_control",
                    ],
                )
                self.assertTrue(
                    all(
                        key in self.effects
                        for key in keys
                    )
                )
                self.assertTrue(
                    all(
                        key.startswith("zg361_ip_probe_")
                        or key.startswith(f"zg361_ip_{profile}_")
                        for key in keys
                    )
                )
        self.assertEqual(lists["x"][:9], lists["y"][:9])
        self.assertEqual(lists["x"][:9], lists["z"][:9])

    def test_manager_treasury_gap_is_explicit_not_a_hidden_allowlist_read(self) -> None:
        self.assertNotIn("zg361_ip_probe_manager_treasury", self.header)
        self.assertNotIn("zg361_ip_probe_manager_treasury", self.effects)
        for source in (self.reader, self.serializer):
            self.assertIn("not_recorded_by_mod", source)
        self.assertIsNone(self.abi["manager_treasury_gap"]["current_mod_producer"])
        self.assertTrue(
            self.abi["manager_treasury_gap"]["forbidden_inference"]
        )
        self.assertEqual(
            self.fixture["mod_producer_gap"]["typed_reason"],
            "not_recorded_by_mod",
        )

    def test_reader_is_same_frame_played_subject_only(self) -> None:
        for token in (
            "const ZhongguoEventTarget16V1 target{4, {}, character_id}",
            "Allowlist(request.profile)",
            "RawRows first{}",
            "RawRows second{}",
            "first != second",
            "before.played_character_id",
            "actual_owner != request.owner_character_id",
            "DecodeQ100000",
        ):
            self.assertIn(token, self.reader)
        self.assertNotIn("request.variable_name", self.reader)
        self.assertNotIn("request.subject_character_id", self.reader)

    def test_mailbox_request_is_exact_and_profile_is_enum(self) -> None:
        self.assertIn("std::array<std::string_view, 8> fields", self.mailbox)
        for key in (
            '"expected_revision"',
            '"owner_character_id"',
            '"profile"',
            '"request_nonce"',
        ):
            self.assertIn(key, self.mailbox)
        for forbidden in (
            "subject_character_id",
            "case_kind",
            "variable_name",
        ):
            self.assertIn(forbidden, self.mailbox)
        self.assertIn("ParseProfile(profile, output.profile)", self.mailbox)
        self.assertIn(
            "ExecuteZhongguoIncidentSnapshotMailboxQueryV1",
            self.mailbox_header,
        )

    def test_fixture_and_abi_remain_honest_about_integration(self) -> None:
        self.assertEqual(self.abi["allowlist"]["count_per_profile"], 49)
        self.assertEqual(self.fixture["allowlist_count_per_profile"], 49)
        self.assertEqual(
            self.fixture["integration_status"],
            "not_added_to_shared_build_or_protocol_surfaces",
        )
        self.assertIn("production_live_acceptance", self.abi["unsupported_claims"])


if __name__ == "__main__":
    unittest.main()
