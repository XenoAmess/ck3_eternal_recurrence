import copy
import sys
import unittest
from pathlib import Path

# Keep discovery from the repository root and discovery from this module
# equally valid (the module intentionally has no packaging dependency).
sys.path.insert(0, str(Path(__file__).parents[1]))
from tools.validate_domains import load_catalogue, validate_catalogue


class DomainCatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogue = load_catalogue()

    def test_phase0_catalogue_is_complete_but_schema_only(self):
        self.assertEqual(validate_catalogue(self.catalogue), [])
        self.assertEqual(self.catalogue["lifecycle_status"], "schema-and-validator-only")
        self.assertIn("No domain runtime is implemented", self.catalogue["completion_claim"])

    def test_all_38_domains_and_361_ids_are_covered(self):
        domains = self.catalogue["domains"]
        self.assertEqual(len(domains), 38)
        self.assertEqual({d["code"] for d in domains}, {chr(i) for i in range(65, 91)} | {f"A{chr(i)}" for i in range(65, 77)})
        ids = {i for d in domains for i in range(d["mechanism_ids"]["first"], d["mechanism_ids"]["last"] + 1)}
        self.assertEqual(ids, set(range(1, 362)))

    def test_gap_or_overlap_is_rejected(self):
        broken = copy.deepcopy(self.catalogue)
        broken["domains"][1]["mechanism_ids"]["first"] = 8
        errors = validate_catalogue(broken)
        self.assertTrue(any("overlapping" in error or "coverage" in error for error in errors))

    def test_terminal_outgoing_transition_is_rejected(self):
        broken = copy.deepcopy(self.catalogue)
        domain = broken["domains"][0]
        domain["transitions"].append({"from": domain["terminal_states"][0], "to": domain["initial_state"], "hook": "bad", "actor": "bad"})
        errors = validate_catalogue(broken)
        self.assertTrue(any("terminal state has outgoing" in error for error in errors))

    def test_religion_entry_and_weak_acl_are_rejected(self):
        broken = copy.deepcopy(self.catalogue)
        broken["domains"][0]["states"][0] = "faith_review"
        broken["permission_policies"]["celestial_manager_reviews_direct_vassal"]["player_manager"]["all_of"] = ["is_ai=no"]
        errors = validate_catalogue(broken)
        self.assertTrue(any("religion/faith" in error for error in errors))
        self.assertTrue(any("player manager ACL" in error for error in errors))

    def test_fervor_entry_is_rejected(self):
        broken = copy.deepcopy(self.catalogue)
        broken["domains"][0]["object_type"] = "fervor_case"
        errors = validate_catalogue(broken)
        self.assertTrue(any("religion/faith" in error for error in errors))

    def test_capacity_and_stale_guard_are_mandatory(self):
        broken = copy.deepcopy(self.catalogue)
        broken["domains"][0]["capacity"]["max_active_per_subject"] = 2
        broken["domains"][0]["cleanup"]["stale_deadline"] = "expire"
        errors = validate_catalogue(broken)
        self.assertTrue(any("bounded capacity" in error for error in errors))
        self.assertTrue(any("stale deadline" in error for error in errors))

    def test_malformed_object_fields_are_reported_not_raised(self):
        broken = copy.deepcopy(self.catalogue)
        broken["permission_policies"] = None
        broken["global_boundaries"] = None
        broken["domains"][0]["mechanism_ids"] = None
        broken["domains"][0]["capacity"] = None
        broken["domains"][0]["cleanup"] = None
        errors = validate_catalogue(broken)
        self.assertTrue(errors)
        self.assertTrue(any("mechanism id" in error for error in errors))
        self.assertTrue(any("bounded capacity" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
