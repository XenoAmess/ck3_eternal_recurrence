"""Offline planned DTO regression; this does not attest a live native provider."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from xar_autoplayer import player_child_default_formal_consumer as consumer
from xar_autoplayer.bridge import player_child_matrilineal_private_action_v1 as transport


FIXTURE = (Path(__file__).resolve().parents[1] / "fixtures"
           / "robert_guy_gone_unmaterialized_12003.json")


class _ExistingRootReadReached(RuntimeError):
    pass


class _Driver:
    def __init__(self, state_dir: Path, fixture: dict[str, object]) -> None:
        self.state_dir = state_dir
        self.frame = copy.deepcopy(fixture["snapshot"])
        self.native_result = copy.deepcopy(fixture["native_result"])
        self.allow_private_player_child_default_action = True
        self.endpoint = self
        self.state = self
        self.requests: list[dict[str, object]] = []
        self.subject_reads: list[dict[str, object]] = []
        self.root_reads: list[dict[str, object]] = []
        self.submissions = 0
        self.alliance_reads = 0

    def take_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.frame)

    def query_player_child_marriage_subject_private_v1(
        self, *, expected_native_revision: int, subject_character_id: int,
    ) -> dict[str, object]:
        self.subject_reads.append({
            "expected_native_revision": expected_native_revision,
            "subject_character_id": subject_character_id,
        })
        assert expected_native_revision == self.frame["native_revision"]
        assert subject_character_id == 38988
        return {"player_child_verified": True, "subject_character_id": 38988}

    def query_player_child_default_result_private_v1(
        self, *, pending: dict[str, object], cold: bool,
    ) -> dict[str, object]:
        return transport.query_player_child_matrilineal_result_private_v1(
            self, pending=pending, cold=cold, default_route=True)

    def send(self, frame: dict[str, object]) -> None:
        assert frame.get("step") == transport.DEFAULT_RESULT_STEP
        self.requests.append(copy.deepcopy(frame))

    def wait_for_command_result(
        self, request_id: str, timeout: float,
    ) -> dict[str, object]:
        assert request_id == self.requests[-1]["request_id"]
        assert timeout > 0
        return {"type": "command_result", "protocol_version": 1,
                "request_id": request_id, "ok": True,
                "result": copy.deepcopy(self.native_result)}

    def _execute_campaign_root_context_v1_query(
        self, *, expected_revision: int,
    ) -> dict[str, object]:
        self.root_reads.append({"expected_revision": expected_revision})
        # Stop at the existing native dependency without inventing another
        # legal candidate, value observation, or proposal submission.
        raise _ExistingRootReadReached("existing native split-successor read")

    def submit_player_child_default_private_v1(self, **_kwargs):
        self.submissions += 1
        raise AssertionError("the result fixture must not submit a proposal")

    def query_player_child_default_alliance_private_v1(self, **_kwargs):
        self.alliance_reads += 1
        raise AssertionError("unmaterialized retirement has no alliance credit")


class GoneUnmaterializedTest(unittest.TestCase):
    def test_normal_result_retires_original_pair_and_reaches_existing_retry(self) -> None:
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8-sig"))
        ledger = copy.deepcopy(fixture["input_ledger"])
        pending = copy.deepcopy(ledger["pending"])
        identity = fixture["bridge_identity"]
        with tempfile.TemporaryDirectory() as temp_dir:
            state_dir = Path(temp_dir)
            (state_dir / "player-child-default-formal-v1.json").write_text(
                json.dumps(ledger), encoding="utf-8")
            driver = _Driver(state_dir, fixture)
            with patch.object(consumer, "bridge_process_identity",
                              return_value=(identity["pid"], identity["creation_date"])):
                # The fake endpoint feeds the real transport _command; the
                # normal consumer retains its real atomic temporary _write.
                result = consumer.query_child_default_result_private(
                    driver, pending=pending, cold=True)
                after = consumer.read_child_default_ledger(state_dir)
                self.assertIsNone(after["pending"])
                resolved = after["resolved"]
                self.assertEqual(resolved["source_pending"], pending)
                self.assertEqual(resolved["status"], "gone_unmaterialized")
                self.assertEqual(resolved["attempted_candidate_ids"], [37909])
                self.assertNotIn("rejected_candidate_ids", resolved)
                self.assertNotIn("actual_alliance_result", resolved)
                self.assertFalse(resolved["material_result"])
                self.assertFalse(resolved["terminal_cause_available"])
                self.assertEqual(resolved["terminal_cause"], "not_observed")
                self.assertFalse(result["cold_absent_relation_unresolved"])
                with self.assertRaises(_ExistingRootReadReached):
                    consumer.plan_child_default_private(
                        driver, {"plan": {"selected_step": "life-advance",
                                          "phase": "life", "reason": "normal campaign"}},
                        fixture["snapshot"])
            self.assertEqual(len(driver.requests), 1)
            request = driver.requests[0]
            self.assertEqual(request["step"], transport.DEFAULT_RESULT_STEP)
            self.assertTrue(request["request_id"].startswith("family-child-action-"))
            self.assertEqual(request["expected_revision"], fixture["snapshot"]["native_revision"])
            self.assertEqual(request["cold_recovery"], 1)
            self.assertEqual((request["heir_character_id"], request["candidate_character_id"],
                              request["recipient_character_id"], request["source_date_raw"]),
                             (38988, 37909, 34332, 53219928))
            self.assertFalse(request["matrilineal_option_selected"])
            self.assertEqual(driver.subject_reads, [{
                "expected_native_revision": fixture["snapshot"]["native_revision"],
                "subject_character_id": 38988,
            }])
            self.assertEqual(driver.root_reads, [{"expected_revision": fixture["snapshot"]["revision"]}])
            self.assertEqual(driver.submissions, 0)
            self.assertEqual(driver.alliance_reads, 0)


if __name__ == "__main__":
    unittest.main()
