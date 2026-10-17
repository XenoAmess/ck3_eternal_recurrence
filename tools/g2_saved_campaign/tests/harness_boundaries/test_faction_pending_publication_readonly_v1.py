from copy import deepcopy
import json
from pathlib import Path
import unittest
from tools.g2_saved_campaign.faction_pending_publication_readonly_v1 import classify_faction_pending_publication_readonly_v1 as qualify

PACK = Path(__file__).resolve().parent
ROW = json.loads((PACK / "actual517-projection.json").read_bytes())


class ExactFactionPublicationWait(unittest.TestCase):
    def test_actual517_and_other_same_source_planning_literal(self):
        row = deepcopy(ROW)
        for message in ["private faction pending same-date paused revision did not arrive",
                        "private faction pending frame changed before receipt"]:
            row["result"]["content"][0]["text"] = "Error executing tool ck3_auto_turn: " + message
            result = qualify(row)
            self.assertTrue(result["read_only_precondition"])
            self.assertFalse(result["business_submission"])
            self.assertTrue(result["prior_faction_business_may_be_pending"])
            self.assertTrue(result["faction_pending_ledger_must_be_preserved"])
            self.assertFalse(result["prior_gift_result_verified"])

    def test_submit_receipt_cold_wait_unknown_or_malformed_reject(self):
        messages = ["private faction pending frame has no bounded native wait",
                    "private-submit-faction-gift-member-v1 command_result timed out",
                    "private-query-faction-gift-receipt-v1 command_result timed out",
                    "private-query-faction-gift-cold-recovery-v1 command_result timed out",
                    "private faction pending same-date paused revision did not arrive extra",
                    "unknown", "private faction pending receipt has a newer same-date paused frame"]
        for message in messages:
            row=deepcopy(ROW);row["result"]["content"][0]["text"]="Error executing tool ck3_auto_turn: "+message
            self.assertIsNone(qualify(row))
        for key,value in [("client_error","timeout"),("request",{"tool":"ck3_execute_step","sequence":517,"arguments":{}})]:
            row=deepcopy(ROW);row[key]=value;self.assertIsNone(qualify(row))
        row=deepcopy(ROW);row["result"]["structured_content"]={"status":"submitted"};self.assertIsNone(qualify(row))


if __name__=="__main__":unittest.main()
