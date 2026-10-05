"""One source-derived refresh case, including its independent writer seam."""
import copy
import unittest

from xar_autoplayer.bridge.army_regiment_refresh_projection import project_observed_raised_regiment_refresh
from xar_autoplayer.bridge.army_chunk_loss_writeback_projection import project_observed_writer_chunk_changes


class RaisedRefreshProjectionTest(unittest.TestCase):
    def test_aliases_special_current_and_character_refresh(self):
        def chunk(index, persistent, current, maximum, state):
            return {"record_index": index, "persistent_regiment_id": persistent,
                    "chunk_index": 0, "current_soldiers": current,
                    "maximum_soldiers": maximum, "state_raw": state,
                    "chunk_army_regiment_id": 117440517}
        data = {"army_regiment_id": 117440517, "status": "available",
                "native_loss_writer_skipped": False,
                "records": [chunk(0, 301989889, 0, 4, 3),
                            chunk(1, 570425346, 20, 25, 0),
                            chunk(2, 570425346, 20, 25, 0)]}
        direct = project_observed_raised_regiment_refresh(data)
        self.assertEqual((direct["current_soldiers"], direct["maximum_soldiers"]), (44, 54))
        self.assertEqual([x["effective_current_contribution"] for x in direct["record_contributions"]], [4, 20, 20])
        army = {"regiment_strengths": [{"army_regiment_id": 117440517, "current_soldiers": 44}],
                "regiment_replenishment_records_v1": [data]}
        request = {"army_regiment_id": 117440517, "writer_quantity_raw": 300000,
                   "writer_quantity_scale": 100000}
        replay = project_observed_writer_chunk_changes(army, request)
        refreshed = replay["conditional_raised_regiment_refresh"]
        #One physical ordinarychunk loses3, but its two DATA occurrences
        #each contribute17. State3 physical0 contributes its maximum4.
        self.assertEqual(replay["physical_current_delta"], -3)
        self.assertEqual((refreshed["current_soldiers"], refreshed["maximum_soldiers"]), (38, 54))
        self.assertTrue(refreshed["current_maximum_ready"])
        self.assertFalse(refreshed["actual_refresh"])
        self.assertIsNone(replay["raised_regiment_current_after"])
        self.assertEqual(refreshed["input_basis"], "conditional_chunk_writeback")

        zero = copy.deepcopy(army)
        zero["regiment_strengths"][0]["current_soldiers"] = 0
        only = project_observed_writer_chunk_changes(zero, request)
        self.assertEqual(only["writes"], [])
        self.assertEqual(only["conditional_raised_regiment_refresh"]["current_soldiers"], 44)
        self.assertTrue(only["refresh_requested"])

        character = {**data, "native_loss_writer_skipped": True}
        independent = project_observed_raised_regiment_refresh(character)
        self.assertEqual((independent["current_soldiers"], independent["maximum_soldiers"]), (1, 1))
        self.assertTrue(independent["character_override"])
        skip = project_observed_writer_chunk_changes({**army, "regiment_replenishment_records_v1": [character]}, request)
        self.assertEqual(skip["conditional_raised_regiment_refresh"]["status"], "not_called")
        self.assertFalse(skip["refresh_requested"])

        empty = project_observed_raised_regiment_refresh({**data, "records": []})
        self.assertEqual((empty["current_soldiers"], empty["maximum_soldiers"]), (0, 0))
        missing = project_observed_raised_regiment_refresh({**data, "native_loss_writer_skipped": None})
        self.assertFalse(missing["current_maximum_ready"])
        self.assertIsNone(missing["current_soldiers"])
        #Native32 ADD wraps, including an ordinary value belowphysical0;
        #neither physical/current contributions nor sums are zero-clamped.
        wrapped = project_observed_raised_regiment_refresh({**data, "records": [
            chunk(0, 301989889, 2147483647, 2147483647, 0),
            chunk(1, 570425346, -1, 1, 0),
            chunk(2, 838860803, 2, 2, 0)]})
        self.assertEqual((wrapped["current_soldiers"], wrapped["maximum_soldiers"]), (-2147483648, -2147483646))


if __name__ == "__main__":
    unittest.main()
