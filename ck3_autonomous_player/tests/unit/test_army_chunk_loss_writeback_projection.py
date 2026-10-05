"""One focused source-derived current-DATA replay case; no native/game access."""
from __future__ import annotations

import copy
import unittest

from xar_autoplayer.bridge.army_replenishment_records_contract import normalize_regiment_replenishment_records_v1
from xar_autoplayer.bridge.army_chunk_loss_writeback_projection import project_observed_writer_chunk_changes


def record(index, persistent, current, maximum, state=0):
    return {"record_index": index, "persistent_regiment_id": persistent,
            "chunk_index": 0, "status": "available", "unavailable_reason": None,
            "current_soldiers": current, "maximum_soldiers": maximum,
            "effective_current_soldiers": maximum if state == 3 and current == 0 else current,
            "state_raw": state, "chunk_army_regiment_id": 117440517,
            "native_can_replenish": False, "native_chunk_can_replenish": False,
            "persistent_monthly_replenishment_fraction_raw": 0,
            "persistent_prepared_replenishment_fraction_raw": 0,
            "persistent_monthly_replenishment_fraction_scale": 100000,
            "persistent_prepared_replenishment_fraction_scale": 100000}


class ChunkLossWritebackTest(unittest.TestCase):
    def test_queried_admission_and_complete_DATA_replay(self):
        data = {"army_regiment_id": 117440517, "source": "native_all_data_records",
                "status": "available", "ready": True, "native_data_record_count": 3,
                "unavailable_reason": None, "native_loss_writer_skipped": False,
                "loss_writer_admission_unavailable_reason": None,
                "records": [record(0, 301989889, 0, 4, 3),
                            record(1, 570425346, 20, 25),
                            record(2, 570425346, 20, 25)]}
        normalized = normalize_regiment_replenishment_records_v1([data])
        army = {"regiment_strengths": [{"army_regiment_id": 117440517, "current_soldiers": 20}],
                "regiment_replenishment_records_v1": normalized}
        request = {"army_regiment_id": 117440517, "writer_quantity_raw": 300000,
                   "writer_quantity_scale": 100000}
        result = project_observed_writer_chunk_changes(army, request)
        #2634374 stores−3 for the state3 physicalzero, then2634467 with
        #negativecap restores0 and transfers its recoveredraw to nextrecord.
        self.assertEqual([(w["pass"], w["record_index"], w["current_after"], w["selected_quantity_raw"])
                          for w in result["writes"]],
                         [(1, 0, -3, 300000), (2, 0, 0, -300000), (2, 1, 17, 300000)])
        self.assertEqual([c["current_soldiers"] for c in result["physical_chunks_after"]], [0, 17])
        self.assertEqual(result["physical_current_delta"], -3)
        self.assertTrue(result["chunk_writeback_ready"])
        self.assertFalse(result["actual_loss"])
        self.assertIsNone(result["raised_regiment_current_after"])
        self.assertEqual(army["regiment_replenishment_records_v1"][0]["records"][1]["current_soldiers"], 20)

        fractional = copy.deepcopy(army)
        fractional["regiment_replenishment_records_v1"][0]["records"] = [record(0, 570425346, 20, 25)]
        fractional["regiment_replenishment_records_v1"][0]["native_data_record_count"] = 1
        fraction = project_observed_writer_chunk_changes(fractional, {**request, "writer_quantity_raw": 50000})
        self.assertEqual(fraction["physical_current_delta"], 0)
        self.assertEqual(fraction["remaining_writer_quantity_raw"], 0)
        self.assertEqual([w["pass"] for w in fraction["writes"]], [1, 2])

        ordinary = copy.deepcopy(army)
        ordinary["regiment_replenishment_records_v1"][0]["records"] = [record(0, 570425346, 20, 25), record(1, 570425346, 20, 25)]
        ordinary["regiment_replenishment_records_v1"][0]["native_data_record_count"] = 2
        exhausted = project_observed_writer_chunk_changes(ordinary, {**request, "writer_quantity_raw": 2300000})
        self.assertEqual(exhausted["physical_current_delta"], -20)
        self.assertEqual(exhausted["remaining_writer_quantity_raw"], 300000)

        skipped = copy.deepcopy(army)
        skipped["regiment_replenishment_records_v1"][0]["native_loss_writer_skipped"] = True
        skip = project_observed_writer_chunk_changes(skipped, request)
        self.assertTrue(skip["writer_skipped"])
        self.assertFalse(skip["refresh_requested"])
        self.assertEqual(skip["writes"], [])
        zero = copy.deepcopy(army)
        zero["regiment_strengths"][0]["current_soldiers"] = 0
        refresh = project_observed_writer_chunk_changes(zero, request)
        self.assertTrue(refresh["refresh_requested"])
        self.assertEqual(refresh["physical_current_delta"], 0)
        self.assertEqual(refresh["writes"], [])

        legacy = copy.deepcopy(data)
        del legacy["native_loss_writer_skipped"]
        del legacy["loss_writer_admission_unavailable_reason"]
        for row in legacy["records"]:
            del row["chunk_army_regiment_id"]
        legacy_rows = normalize_regiment_replenishment_records_v1([legacy])
        missing = project_observed_writer_chunk_changes({**army, "regiment_replenishment_records_v1": legacy_rows}, request)
        self.assertFalse(missing["chunk_writeback_ready"])
        self.assertEqual(missing["missing_inputs"], ["native_loss_writer_skipped"])


if __name__ == "__main__":
    unittest.main()
