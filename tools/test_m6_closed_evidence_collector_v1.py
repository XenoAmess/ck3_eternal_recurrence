"""One bounded synthetic IO compound; never imports or contacts the game."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from g2_saved_campaign.m6_closed_evidence_collector_v1 import LIMIT, collect


def pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "closed": True}


def episode(full_id=17, generation=0):
    identity = {"action_id": "synthetic-original", "actor_character_id": 7, "target_character_id": 9,
                "scheme_instance_id": full_id, "scheme_instance_generation": generation}
    measurement = {**identity, "source_date_raw": 2000, "source_native_revision": 20,
                   "baseline_source_date_raw": 1000, "baseline_source_native_revision": 10,
                   "incremental_named_gain_observed": True, "tracked_instance_active": True,
                   "scheme_sway_opinion": {"observed": True, "present": True, "value": 25},
                   "next_turn_consumed": False}
    return {**{key: identity[key] for key in ("action_id", "actor_character_id", "target_character_id")},
            "status": "applied", "postcondition_verified": True,
            "native_receipt": identity, "first_named_gain_intervention": measurement,
            "material_intervention": {**measurement, "incremental_named_gain_observed": False,
                                      "source_date_raw": 4000, "source_native_revision": 60},
            "terminal_intervention": {**identity, "source_date_raw": 3000, "source_native_revision": 40,
                                      "instance_terminal_outcome_observed": True,
                                      "terminal_cause_observed": False, "terminal_cause": "unknown",
                                      "next_turn_consumed": False}}


class ClosedM6CollectorIO(unittest.TestCase):
    def test_closed_pins_archive_dedup_changes_oversized_and_generation_separation(self):
        with tempfile.TemporaryDirectory(prefix="m6-closed-pointer-") as temporary:
            root = Path(temporary)
            first, second = root / "closed-ledger.json", root / "closed-auto.json"
            original = episode()
            first.write_text(json.dumps({"resolved": original}), encoding="utf-8")
            consumed = deepcopy(original)
            for kind in ("first_named_gain_intervention", "terminal_intervention"):
                consumed[kind].update(next_turn_consumed=True, following_native_revision=61, following_date_raw=4000)
            current = episode(16777233, 1)  # The same low slot, different complete ID/generation.
            current["previous_interventions"] = [consumed]
            second.write_text(json.dumps({"result": {"structured_content": {
                "status": "executed", "selected_step": "life-advance", "sway_following_turn": current}}}), encoding="utf-8")
            manifest = {"schema": "g2.m6.closed-evidence-manifest/v1", "machine_id": "synthetic-source-machine",
                        "campaign_id": "synthetic-campaign", "batch_id": "synthetic-closed-batch",
                        "closed_at_utc": "2026-10-19T02:00:00Z", "sources": [pin(first), pin(second)],
                        "selections": [{"source": 0, "pointer": "/resolved", "kind": "ledger_episode"},
                                       {"source": 1, "pointer": "/result/structured_content", "kind": "ordinary_auto"}]}
            report = collect(manifest, collector_machine_id="synthetic-collector-machine")
            self.assertEqual(len(report["groups"]), 2)
            old = next(group for group in report["groups"] if group["identity"]["scheme_instance_generation"] == 0)
            gain = next(row for row in old["observations"] if row["kind"] == "first_named_gain_intervention")
            self.assertEqual((gain["measurement"]["source_date_raw"], gain["measurement"]["baseline_source_date_raw"]), (2000, 1000))
            self.assertEqual(len(gain["occurrences"]), 2)
            self.assertFalse(gain["occurrences"][0]["consumption"]["next_turn_consumed"])
            following = gain["occurrences"][1]
            self.assertTrue(following["consumption"]["next_turn_consumed"])
            self.assertEqual(following["source"], 1)
            self.assertTrue(following["pointer"].endswith("/previous_interventions/0/first_named_gain_intervention"))
            self.assertEqual(following["ordinary_auto"]["selected_step"], "life-advance")
            self.assertFalse(report["G2_M6_credit_awarded"])
            self.assertEqual(report["evidence_packet_ready"], "not_evaluated")
            self.assertEqual(report["Game_MCP_SDK_calls"], 0)
            self.assertEqual(report["source_machine_id"], "synthetic-source-machine")
            self.assertEqual(report["collector_machine_id"], "synthetic-collector-machine")

            # A same-size rewrite must fail SHA binding, with no substituted evidence.
            first.write_bytes(first.read_bytes().replace(b"25", b"26"))
            with self.assertRaisesRegex(ValueError, "content changed"):
                collect(manifest, collector_machine_id="synthetic-collector-machine")

            huge = root / "oversized-closed-auto.json"
            huge.write_bytes(b" " * (LIMIT + 1))
            oversize = {**manifest, "sources": [pin(huge)], "selections": [manifest["selections"][0]]}
            with patch.object(Path, "read_bytes", side_effect=AssertionError("oversized body must not be read")):
                skipped = collect(oversize, collector_machine_id="synthetic-collector-machine")
            self.assertEqual(skipped["groups"], [])
            self.assertEqual(skipped["sources"][0]["state"], "oversized_source/not_observed")

            # A mismatched generation cannot be merged into the original episode.
            invalid = root / "invalid-generation.json"
            invalid.write_text(json.dumps({"resolved": episode(17, 1)}), encoding="utf-8")
            rejected = collect({**oversize, "sources": [pin(invalid)]}, collector_machine_id="synthetic-collector-machine")
            self.assertEqual(rejected["groups"], [])
            self.assertEqual(rejected["issues"][0]["state"], "identity_not_observed")


if __name__ == "__main__":
    unittest.main()
