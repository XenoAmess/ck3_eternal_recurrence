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
                self.assertEqual(len(keys), 50)
                self.assertEqual(len(set(keys)), 50)
                self.assertEqual(
                    keys[:10],
                    [
                        f"zg361_ip_{profile}_probe_owner",
                        f"zg361_ip_{profile}_probe_subject",
                        f"zg361_ip_{profile}_probe_cycle",
                        f"zg361_ip_{profile}_probe_serial",
                        f"zg361_ip_{profile}_probe_result",
                        f"zg361_ip_{profile}_probe_source_kind",
                        f"zg361_ip_{profile}_probe_consequence_kind",
                        f"zg361_ip_{profile}_probe_subject_gold",
                        f"zg361_ip_{profile}_probe_manager_treasury",
                        f"zg361_ip_{profile}_probe_capital_control",
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
                        key.startswith(f"zg361_ip_{profile}_")
                        for key in keys
                    )
                )
        self.assertTrue(set(lists["x"][:10]).isdisjoint(lists["y"][:10]))
        self.assertTrue(set(lists["x"][:10]).isdisjoint(lists["z"][:10]))

    def test_manager_treasury_uses_exact_same_frame_mod_variable(self) -> None:
        for profile in ("x", "y", "z"):
            self.assertIn(
                f"zg361_ip_{profile}_probe_manager_treasury", self.header
            )
        self.assertIn(
            "DecodeQ100000(rows[probe_manager_treasury]", self.reader
        )
        self.assertNotIn("not_recorded_by_mod", self.reader)
        self.assertNotIn("not_recorded_by_mod", self.serializer)
        self.assertIn(
            "manager_treasury_source\\\":\\\"zg361_ip_probe_manager_treasury",
            self.serializer,
        )
        producer = self.abi["manager_treasury_binding"]
        self.assertEqual(
            producer["mod_variable_template"],
            "zg361_ip_{profile}_probe_manager_treasury",
        )
        self.assertEqual(
            producer["upstream_detector_variable"],
            "zg361_ip_probe_manager_treasury",
        )
        self.assertEqual(producer["value_source"], "root.treasury")
        self.assertEqual(
            producer["producer_capability_guard"],
            "government_has_flag = government_has_treasury",
        )
        self.assertTrue(
            producer["complete_cache_requires_variable"]
        )
        self.assertEqual(
            self.fixture["mod_producer_binding"]["missing_typed_reason"],
            "variable_absent",
        )
        self.assertEqual(
            self.fixture["mod_producer_binding"]["provider_key_template"],
            "zg361_ip_{profile}_probe_manager_treasury",
        )
        self.assertRegex(
            self.effects,
            r"set_variable\s*=\s*\{\s*name\s*=\s*"
            r"zg361_ip_probe_manager_treasury\s+value\s*=\s*root\.treasury\s*\}",
        )
        self.assertRegex(
            self.effects,
            r"has_variable\s*=\s*zg361_ip_probe_manager_treasury",
        )
        self.assertRegex(
            self.effects,
            r"government_has_flag\s*=\s*government_has_treasury",
        )
        for profile in ("x", "y", "z"):
            self.assertRegex(
                self.effects,
                rf"name\s*=\s*zg361_ip_{profile}_probe_manager_treasury\s+"
                r"value\s*=\s*var:zg361_ip_probe_manager_treasury",
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

    def test_fixture_and_abi_record_static_shared_integration(self) -> None:
        self.assertEqual(self.abi["allowlist"]["count_per_profile"], 50)
        self.assertEqual(self.fixture["allowlist_count_per_profile"], 50)
        self.assertEqual(
            self.fixture["integration_status"],
            "shared_protocol_static_ready",
        )
        self.assertEqual(
            self.fixture["mailbox_fixed_slot"],
            "permitted_executor_septendenary",
        )
        self.assertEqual(
            self.abi["mailbox_fixed_slot"],
            "permitted_executor_septendenary",
        )
        self.assertIn("production_live_acceptance", self.abi["unsupported_claims"])
        self.assertTrue(
            self.abi["profile_receipt_atomicity"][
                "mixed_na_incident_profiles_same_paused_frame"
            ]
        )


if __name__ == "__main__":
    unittest.main()
