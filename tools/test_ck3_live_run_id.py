#!/usr/bin/env python3
"""Tests for machine- and mod-scoped CK3 live-run identifiers."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import ck3_live_run_id as live_ids


class LiveRunIdTests(unittest.TestCase):
    def test_sequences_are_scoped_by_machine_and_mod(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = live_ids.allocate_live_run_id(
                "auto-upgrade-buildings", state_root=root, machine_id="machine-a"
            )
            second = live_ids.allocate_live_run_id(
                "auto-upgrade-buildings", state_root=root, machine_id="machine-a"
            )
            other_mod = live_ids.allocate_live_run_id(
                "remove-mandala", state_root=root, machine_id="machine-a"
            )
            other_machine = live_ids.allocate_live_run_id(
                "auto-upgrade-buildings", state_root=root, machine_id="machine-b"
            )

        self.assertEqual(first.run_id, "machine-a--auto-upgrade-buildings--R0001")
        self.assertEqual(second.run_id, "machine-a--auto-upgrade-buildings--R0002")
        self.assertEqual(other_mod.run_id, "machine-a--remove-mandala--R0001")
        self.assertEqual(
            other_machine.run_id, "machine-b--auto-upgrade-buildings--R0001"
        )

    def test_batch_allocations_share_execution_but_keep_mod_counters(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            rows = live_ids.allocate_live_run_ids(
                ("eternal-recurrence", "vivhite-courtier"),
                state_root=Path(temporary),
                machine_id="matrix-host",
            )
        self.assertEqual(len({row.execution_id for row in rows}), 1)
        self.assertEqual([row.sequence for row in rows], [1, 1])
        self.assertNotEqual(rows[0].run_id, rows[1].run_id)

    def test_legacy_alias_is_metadata_not_the_new_counter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            identity = live_ids.allocate_live_run_id(
                "auto-upgrade-buildings",
                state_root=Path(temporary),
                machine_id="machine-a",
                legacy_alias="R410",
            )
        self.assertEqual(identity.sequence, 1)
        self.assertEqual(identity.legacy_alias, "R410")
        self.assertTrue(identity.run_id.endswith("--R0001"))

    def test_receipt_binds_all_mods_in_one_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rows = live_ids.allocate_live_run_ids(
                ("eternal-recurrence", "vivhite-courtier"),
                state_root=root / "state",
                machine_id="matrix-host",
            )
            artifacts = root / "artifacts"
            artifacts.mkdir()
            receipt = live_ids.write_identity_receipt(artifacts, rows)
            payload = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(payload["execution_id"], rows[0].execution_id)
        self.assertEqual(
            [item["mod_key"] for item in payload["identities"]],
            ["eternal-recurrence", "vivhite-courtier"],
        )

    def test_status_is_append_only_and_bound_to_allocation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            identity = live_ids.allocate_live_run_id(
                "auto-upgrade-buildings", state_root=root, machine_id="machine-a"
            )
            live_ids.record_live_run_status(
                identity,
                "launch-started",
                reason="test process launch",
                state_root=root,
            )
            live_ids.record_live_run_status(
                identity,
                "completed-red",
                reason="fixture assertion",
                state_root=root,
            )
            status_path = root / "machine-a" / "auto-upgrade-buildings" / "statuses.jsonl"
            rows = [json.loads(line) for line in status_path.read_text().splitlines()]
        self.assertEqual([row["status"] for row in rows], ["launch-started", "completed-red"])
        self.assertTrue(all(row["run_id"] == identity.run_id for row in rows))

    def test_machine_token_is_opaque_and_distinguishes_hosts(self) -> None:
        first = live_ids.derive_machine_id("Gaming Rig", "secret-guid-a")
        second = live_ids.derive_machine_id("Gaming Rig", "secret-guid-b")
        self.assertRegex(first, r"^gaming-rig-[0-9a-f]{10}$")
        self.assertNotEqual(first, second)
        self.assertNotIn("secret", first)

    def test_unknown_mod_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(live_ids.LiveRunIdError):
                live_ids.allocate_live_run_id(
                    "typo-mod", state_root=Path(temporary), machine_id="machine-a"
                )


if __name__ == "__main__":
    unittest.main()
