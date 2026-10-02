#!/usr/bin/env python3
"""Tests for machine- and mod-scoped CK3 live-run identifiers."""

from __future__ import annotations

import json
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

import ck3_live_run_id as live_ids


class LiveRunIdTests(unittest.TestCase):
    def cli_json(self, args: list[str]) -> dict:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(live_ids.main(args), 0)
        return json.loads(output.getvalue())

    def test_external_cli_counters_are_scoped_without_changing_builtin_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            common = ["--state-root", str(root), "--machine-id", "machine-a"]
            first = self.cli_json(["allocate", "--external-mod", "example-overhaul", *common])
            second = self.cli_json(["allocate", "--external-mod", "example-overhaul", *common])
            other_mod = self.cli_json(["allocate", "--external-mod", "another-overhaul", *common])
            other_machine = self.cli_json(["allocate", "--external-mod", "example-overhaul",
                                           "--state-root", str(root), "--machine-id", "machine-b"])
            builtin = self.cli_json(["allocate", "--mod", "vanilla", *common])
            self.assertEqual(first["run_id"], "machine-a--example-overhaul--R0001")
            self.assertEqual(second["sequence"], 2)
            self.assertEqual(other_mod["sequence"], 1)
            self.assertEqual(other_machine["sequence"], 1)
            self.assertEqual(builtin["run_id"], "machine-a--vanilla--R0001")
            counter = json.loads((root / "machine-a/example-overhaul/counter.json").read_text())
            self.assertEqual(counter["schema"], live_ids.COUNTER_SCHEMA)
            self.assertEqual(counter["last_sequence"], 2)

    def test_external_cli_status_and_identity_keep_v1_and_legacy_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            common = ["--state-root", str(root), "--machine-id", "machine-a"]
            allocated = self.cli_json(["allocate", "--external-mod", "example-overhaul",
                                       "--legacy-alias", "R12a", *common])
            self.assertEqual(allocated["schema"], live_ids.IDENTITY_SCHEMA)
            self.assertEqual(allocated["legacy_alias"], "R12A")
            identity = live_ids.load_live_run_identity(allocated["run_id"], "example-overhaul",
                                                       state_root=root, machine_id="machine-a", external_mod=True)
            self.assertEqual(identity.to_dict(), allocated)
            self.assertEqual(live_ids.format_run_id("machine-a", "example-overhaul", 1, external_mod=True), identity.run_id)
            for status in ("launch-started", "completed-red"):
                row = self.cli_json(["status", "--external-mod", "example-overhaul", "--run-id", identity.run_id,
                                     "--status", status, "--reason", "synthetic offline test", *common])
                self.assertEqual(row["execution_id"], identity.execution_id)
            rows = [json.loads(line) for line in (root / "machine-a/example-overhaul/statuses.jsonl").read_text().splitlines()]
            self.assertEqual([row["status"] for row in rows], ["launch-started", "completed-red"])
            with self.assertRaises(live_ids.LiveRunIdError):
                live_ids.load_live_run_identity(identity.run_id, "another-overhaul", state_root=root,
                                                machine_id="machine-a", external_mod=True)

    def test_external_invalid_slugs_refuse_before_state_write(self) -> None:
        invalid = ("Example-mod", " example-mod", "example-mod ", "", "bad--key", "-bad", "bad-",
                   "../bad", "bad/key", "C:mod", "é", "a" * 65, "nul", "com1", "vanilla")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for slug in invalid:
                with self.subTest(slug=slug), self.assertRaises(live_ids.LiveRunIdError):
                    live_ids.allocate_live_run_id(slug, external_mod=True, state_root=root, machine_id="machine-a")
                self.assertEqual(list(root.iterdir()), [])

    def test_mod_modes_are_mutually_exclusive_and_builtin_listing_is_unchanged(self) -> None:
        for command in ("allocate", "status"):
            suffix = [] if command == "allocate" else ["--run-id", "irrelevant", "--status", "voided", "--reason", "test"]
            for mode_args in ([], ["--mod", "vanilla", "--external-mod", "example-overhaul"]):
                with self.subTest(command=command, modes=mode_args), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    live_ids._parse_args([command, *mode_args, *suffix])
                self.assertEqual(error.exception.code, 2)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(live_ids.main(["list-mods"]), 0)
        self.assertEqual(set(output.getvalue().splitlines()), live_ids.CANONICAL_MOD_KEYS)
        self.assertNotIn("example-overhaul", live_ids.CANONICAL_MOD_KEYS)

    def test_expansion_products_receive_separate_counters(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            rows = live_ids.allocate_live_run_ids(
                ("celestial-commerce-corruption", "tributary-expansion-directives"),
                state_root=Path(temporary),
                machine_id="upgrade-host",
            )
            again = live_ids.allocate_live_run_id(
                "celestial-commerce-corruption",
                state_root=Path(temporary),
                machine_id="upgrade-host",
            )
        self.assertEqual([row.sequence for row in rows], [1, 1])
        self.assertEqual(again.sequence, 2)
        self.assertNotEqual(rows[0].run_id, rows[1].run_id)

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
