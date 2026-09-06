#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 contracts for the generated 361 readiness ledger."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest import mock
import unittest

from gen_361_mechanisms import BOM, MOD_ROOT, main, outputs
from zg361_mechanism_data import load_mechanisms
from zg361_readiness_data import (
    CLAIMS,
    CUMULATIVE_COUNTS,
    EXPECTED_CUMULATIVE_COUNTS,
    EXPECTED_CUMULATIVE_RANGES,
    EXPECTED_EXCLUSIVE_COUNTS,
    EXPECTED_EXCLUSIVE_RANGES,
    EXCLUSIVE_COUNTS,
    LATEST_PRODUCT_ACCEPTANCE,
    LEVELS,
    READINESS_BY_ID,
    RECENT_PRODUCT_ACCEPTANCE_ATTEMPTS,
    ReadinessLevel,
    format_ranges,
    ids_at_least,
    ids_at_level,
)


class ReadinessDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mechanisms = load_mechanisms(MOD_ROOT)
        cls.rendered = outputs(cls.mechanisms)
        cls.ledger_path = MOD_ROOT / "docs" / "361-phase2-coverage-ledger.md"
        cls.manifest_path = MOD_ROOT / "docs" / "361-mechanism-manifest.json"
        cls.mapping_path = (
            MOD_ROOT / "docs" / "361-mechanism-implementation-manifest.md"
        )

    def test_all_361_ids_are_claimed_exactly_once(self) -> None:
        flattened = [mechanism_id for claim in CLAIMS for mechanism_id in claim.ids]
        self.assertEqual(len(flattened), 361)
        self.assertEqual(len(set(flattened)), 361)
        self.assertEqual(sorted(flattened), list(range(1, 362)))
        self.assertEqual(tuple(READINESS_BY_ID), tuple(range(1, 362)))
        for mechanism_id, record in READINESS_BY_ID.items():
            self.assertEqual(record.mechanism_id, mechanism_id)

    def test_levels_are_ordered_exclusive_and_cumulative(self) -> None:
        self.assertEqual(tuple(int(level) for level in LEVELS), (0, 1, 2, 3, 4))
        exclusive_sets = [set(ids_at_level(level)) for level in LEVELS]
        for index, left in enumerate(exclusive_sets):
            for right in exclusive_sets[index + 1 :]:
                self.assertTrue(left.isdisjoint(right))
        self.assertEqual(set().union(*exclusive_sets), set(range(1, 362)))
        for lower, higher in zip(LEVELS, LEVELS[1:]):
            self.assertGreaterEqual(
                set(ids_at_least(lower)),
                set(ids_at_least(higher)),
            )

    def test_frozen_counts_match_current_master_evidence(self) -> None:
        self.assertEqual(dict(EXCLUSIVE_COUNTS), dict(EXPECTED_EXCLUSIVE_COUNTS))
        self.assertEqual(
            dict(EXCLUSIVE_COUNTS),
            {
                "design-only": 0,
                "python-l0": 0,
                "ck3-static-ready": 0,
                "central-wired": 357,
                "ck3-live": 4,
            },
        )
        self.assertEqual(dict(CUMULATIVE_COUNTS), dict(EXPECTED_CUMULATIVE_COUNTS))
        self.assertEqual(
            dict(CUMULATIVE_COUNTS),
            {
                "design-only": 361,
                "python-l0": 361,
                "ck3-static-ready": 361,
                "central-wired": 361,
                "ck3-live": 4,
            },
        )

    def test_frozen_exclusive_and_cumulative_range_snapshots(self) -> None:
        actual_exclusive = {
            level.key: format_ranges(ids_at_level(level)) for level in LEVELS
        }
        actual_cumulative = {
            level.key: format_ranges(ids_at_least(level)) for level in LEVELS
        }
        self.assertEqual(actual_exclusive, dict(EXPECTED_EXCLUSIVE_RANGES))
        self.assertEqual(actual_cumulative, dict(EXPECTED_CUMULATIVE_RANGES))
        self.assertEqual(
            actual_exclusive["ck3-static-ready"],
            "",
        )
        self.assertEqual(
            actual_exclusive["central-wired"],
            "002-017, 019-068, 070-356, 358-361",
        )

    def test_product_snapshots_record_r107_baseline_and_recent_reds_without_promoting_ids(self) -> None:
        snapshot = LATEST_PRODUCT_ACCEPTANCE
        self.assertEqual(snapshot.run_id, "R107")
        self.assertEqual(snapshot.result, "RED")
        self.assertEqual(snapshot.product_commit, "275ee65")
        self.assertEqual(snapshot.verified_file_count, 937)
        self.assertEqual(snapshot.speed, 5)
        self.assertEqual(snapshot.observation_days, 918)
        self.assertEqual(snapshot.native_observations, 221)
        self.assertEqual(len(snapshot.drained_event_keys), 68)
        self.assertIn("zg361b2.40", snapshot.drained_event_keys)
        self.assertIn("zg361ch.128", snapshot.drained_event_keys)
        self.assertIn("zg361ch.102", snapshot.drained_event_keys)
        self.assertIn("zg361comp.1", snapshot.drained_event_keys)
        self.assertIn("four replacement clients", snapshot.boundary)
        self.assertIn("copy audit remains RED", snapshot.boundary)
        self.assertIn("PID 32972", snapshot.boundary)
        self.assertIn("canonical registry remains 0/4", snapshot.boundary)
        self.assertIn("0/3", snapshot.boundary)
        self.assertEqual(EXCLUSIVE_COUNTS["ck3-live"], 4)

        ledger = self.rendered[self.ledger_path].decode("utf-8-sig")
        self.assertIn("R111–R118 增量全量候选验收记录", ledger)
        self.assertEqual(
            tuple(attempt.run_id for attempt in RECENT_PRODUCT_ACCEPTANCE_ATTEMPTS),
            ("R111", "R112", "R113", "R114", "R115", "R116", "R117", "R118"),
        )
        self.assertTrue(
            all(attempt.verified_file_count == 1031 for attempt in RECENT_PRODUCT_ACCEPTANCE_ATTEMPTS)
        )
        self.assertIn("R107 基线完整产品验收快照", ledger)
        self.assertIn("`R107`", ledger)
        self.assertIn("`R114`", ledger)
        self.assertIn("`R115`", ledger)
        self.assertIn("`R116`", ledger)
        self.assertIn("`R117`", ledger)
        self.assertIn("`R118`", ledger)
        self.assertIn("d54d3beb0dcf26a3831b6b0441e92dbba28a56aca8e77fae770c01416f208aa5", ledger)
        self.assertIn("d4616282305cdc6761aaf624b771731f93d221fe3cce4ab5a324acfe87d2ae10", ledger)
        self.assertIn("318d60a217065ffaaa51dd92ad9cf3b9db349d9a673ef86ee604b507553a5a44", ledger)
        self.assertIn("resume1 复用 PID 54484", ledger)
        self.assertIn("36/36 interrupts 全部 GREEN", ledger)
        self.assertIn("22 个 Career desc 上产生 154 条", ledger)
        self.assertIn("全同签名扫描为 2,601 处", ledger)
        self.assertIn("R113、R114、R115 旧签名均为 0", ledger)
        self.assertIn("550 日观察边界不是唯一故障", ledger)
        self.assertIn("R117 必须 fresh 启动后验收", ledger)
        self.assertIn("6512d2150e901678a10fbbc70814760a7e968ddd", ledger)
        self.assertIn("同一 PID 45944", ledger)
        self.assertIn("续跑最终捕获 561 条产品 runtime diagnostics", ledger)
        self.assertIn("zg361b1.91 -> zg361_b1_open_cycle_effect", ledger)
        self.assertIn("weak Character 45030", ledger)
        self.assertIn("Character 45031", ledger)
        self.assertIn("清空并按当前合法 roster 重建 candidates", ledger)
        self.assertIn("player-only 与 eligibility gate", ledger)
        self.assertIn("R117 不是完整迁移树 GREEN", ledger)
        self.assertIn("380af02c8ccaace03144c6ea2beb4dda32454a33", ledger)
        self.assertIn("原生 MCP-only", ledger)
        self.assertIn("同一 PID 184992", ledger)
        self.assertIn("restart_count=0", ledger)
        self.assertIn("产品 runtime blocking diagnostics 均为 0", ledger)
        self.assertIn("ep3_interactions_events.0630", ledger)
        self.assertIn("manager roster", ledger)
        self.assertIn("年度 B1 按预期记录 empty roster 并关闭", ledger)
        self.assertIn("`zg361pp.147` 未到达", ledger)
        self.assertIn("scenario/seed RED", ledger)
        self.assertIn("R118 不提升任何逐号 readiness", ledger)
        self.assertIn("b3r116_resume1", ledger)
        self.assertIn("b3r117_resume1", ledger)
        self.assertIn("b3r118_resume1", ledger)
        self.assertIn("b3r118_resume2", ledger)
        self.assertIn("937 files", ledger)
        self.assertIn("918 游戏日", ledger)
        self.assertIn("221 次 native/MCP 观测", ledger)

    def test_workforce_endgame_40_are_central_wired_with_terminal_external_wait(self) -> None:
        workforce_ids = set(range(242, 278)) | {355, 356, 360, 361}
        self.assertEqual(len(workforce_ids), 40)
        for mechanism_id in sorted(workforce_ids):
            record = READINESS_BY_ID[mechanism_id]
            self.assertEqual(record.level, ReadinessLevel.CENTRAL_WIRED)
            self.assertEqual(
                record.package,
                "workforce-endgame-conditional-external-wait"
                if mechanism_id in {360, 361}
                else "workforce-endgame-ck3-runtime",
            )
            self.assertEqual(
                record.evidence[:3],
                (
                    "tools/gen_361_workforce_endgame_runtime.py",
                    "tools/test_zg361_workforce_endgame_runtime.py",
                    "docs/361-workforce-endgame-ck3-runtime-spec.md",
                ),
            )
            self.assertEqual(
                record.evidence[3:],
                (
                    "tools/gen_361_phase2_central_runtime.py",
                    "tools/test_zg361_phase2_central_runtime.py",
                    "docs/361-phase2-central-runtime-spec.md",
                    "common/scripted_effects/zg361_core_review_cycle_effects.txt",
                    "common/scripted_effects/zg361_core_result_delivery_effects.txt",
                    "common/scripted_effects/zg361_core_appeal_scoreboard_effects.txt",
                    "common/scripted_effects/zg361_core_elimination_effects.txt",
                ),
            )
            if mechanism_id in {360, 361}:
                self.assertIn("conditional", record.note)
                self.assertIn("not central-completable", record.note)
        self.assertEqual(set(ids_at_least(ReadinessLevel.CK3_STATIC_READY)), set(range(1, 362)))
        self.assertEqual(set(ids_at_least(ReadinessLevel.CENTRAL_WIRED)), set(range(1, 362)))

    def test_manifest_embeds_current_summary_and_every_per_id_record(self) -> None:
        manifest = json.loads(self.rendered[self.manifest_path].decode("utf-8"))
        self.assertEqual(manifest["schema"], 5)
        self.assertEqual(
            manifest["readiness"]["authority"],
            "tools/zg361_readiness_data.py",
        )
        self.assertEqual(
            manifest["readiness"]["exclusive_counts"],
            dict(EXCLUSIVE_COUNTS),
        )
        self.assertEqual(
            manifest["readiness"]["cumulative_counts"],
            dict(CUMULATIVE_COUNTS),
        )
        self.assertEqual(
            [item["id"] for item in manifest["items"]],
            list(range(1, 362)),
        )
        for item in manifest["items"]:
            self.assertEqual(
                item["readiness"],
                READINESS_BY_ID[item["id"]].manifest_payload(),
            )
        item_018 = manifest["items"][17]
        self.assertEqual(item_018["readiness"]["highest_level"], "ck3-live")
        self.assertIn("zg361.53 remains CK3 static-ready", item_018["readiness"]["note"])
        self.assertIn(
            "does not prove complete per-ID semantics",
            manifest["readiness"]["central_wiring_boundary"],
        )

    def test_checked_in_manifest_and_ledgers_are_not_stale(self) -> None:
        for path in (self.ledger_path, self.manifest_path, self.mapping_path):
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file())
                self.assertEqual(path.read_bytes(), self.rendered[path])

    def test_generated_ledger_has_bom_and_no_whitespace_damage(self) -> None:
        self.assertTrue(self.rendered[self.ledger_path].startswith(BOM))
        for path in (self.ledger_path, self.manifest_path, self.mapping_path):
            payload = self.rendered[path]
            text = payload.decode("utf-8-sig")
            with self.subTest(path=path.name):
                self.assertNotIn("\r", text)
                self.assertTrue(text.endswith("\n"))
                self.assertFalse(
                    any(line.endswith((" ", "\t")) for line in text.splitlines())
                )

    def test_generator_check_mode_is_green(self) -> None:
        output = io.StringIO()
        with mock.patch("sys.stdout", output):
            result = main(["--check"])
        self.assertEqual(result, 0, output.getvalue())
        self.assertIn("GREEN: checked 361 mechanisms", output.getvalue())


if __name__ == "__main__":
    unittest.main()
