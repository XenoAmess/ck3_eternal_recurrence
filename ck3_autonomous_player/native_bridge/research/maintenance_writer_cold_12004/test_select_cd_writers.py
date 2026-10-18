"""New narrow tests only; fixtures are consumer projections, never CK3 evidence."""
import copy
import unittest
from select_cd_writers import select


def result(slots):
    rows = [{"slot": slot, "offset": (0x2C0, 0x2C8, 0x28, 0x30)[slot],
             "RIP_after": 0x140001001 + slot, "RIP_after_rva": 0x1001 + slot,
             "physical_write_qualified": True, "unavailable_reasons": [],
             "known_producer": False, "maintenance_attribution": "unclosed",
             "actual_writer_game_date": None, "writer_instruction_start": None}
            for slot in slots]
    return {"origin": "original_files_bound_to_Root_admission", "Root_binding": {},
            "input_pins": {}, "evidence_machine_id": "synthetic-projection-test-only",
            "qualified_writers": rows, "unknown_traps": [], "issues": [],
            "missing_or_unproved_live_restores": [], "cleanup_proved": True,
            "status": "ACTUAL_WRITERS_SOURCE_UNKNOWN", "qualified_slot_count": len(rows),
            "unknown_slot_count": 0, "finite_window_reason": "timeout",
            "known_producer": False, "maintenance_attribution": "unclosed",
            "actual_writer_game_date": None, "full_window_all_writes_covered": False}


class Selection(unittest.TestCase):
    def test_ab_does_not_supply_cd_and_same_value_cd_retained(self):
        original = result([0, 1])
        output = select(original)
        self.assertFalse(output["source_decode_candidate_available"])
        self.assertEqual(output["status"], "NO_QUALIFIED_C_D_TRAP_RETAINED")
        original = result([0, 2, 3])
        original["qualified_writers"][1]["same_value_write"] = True
        saved = copy.deepcopy(original)
        output = select(original)
        self.assertEqual(original, saved)
        self.assertTrue(output["source_decode_candidate_available"])
        self.assertEqual([x["record"]["slot"] for x in output["selected_c_d_writers"]], [2, 3])
        self.assertTrue(output["selected_c_d_writers"][0]["record"]["same_value_write"])
        self.assertIsNone(output["paid_maintenance_raw"])
        self.assertFalse(output["same_net_invocation_proved"])

    def test_cleanup_partial_foreign_and_slot_alias_never_source_ready(self):
        partial = result([2])
        partial.update(cleanup_proved=False, issues=["cleanup_not_proved"],
                       status="PARTIAL_ACTUAL_WRITERS_SOURCE_UNKNOWN")
        output = select(partial)
        self.assertEqual(len(output["selected_c_d_writers"]), 1)
        self.assertFalse(output["source_decode_candidate_available"])
        foreign = result([3])
        foreign["qualified_writers"][0]["RIP_after_rva"] = None
        self.assertFalse(select(foreign)["source_decode_candidate_available"])
        for key, value in (("slot", True), ("offset", 0x2C0),
                           ("known_producer", True), ("actual_writer_game_date", 123)):
            bad = result([2])
            bad["qualified_writers"][0][key] = value
            with self.assertRaises(ValueError):
                select(bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
