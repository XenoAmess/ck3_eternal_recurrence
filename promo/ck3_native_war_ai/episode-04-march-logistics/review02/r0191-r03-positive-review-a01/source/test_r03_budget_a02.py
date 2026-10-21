"""Only the amended budget domains; prior13 unrelated guards reused unchanged."""
import unittest
from r03_pipeline_a02 import Usage
from r03_budget_a02 import CONTACT_CAP,AGGREGATE_CAP

class BudgetDelta(unittest.TestCase):
    def test_amended_contact_bound_and_prior7M_are_distinct(self) -> None:
        self.assertEqual(CONTACT_CAP,12582912)
        self.assertEqual(AGGREGATE_CAP,14680064)
        Usage(contacts=11*1048576).check()
        Usage(contacts=CONTACT_CAP,endpoints=524288,metadata=786432,sources=524288).check()
        with self.assertRaisesRegex(ValueError,"12MiB"):
            Usage(contacts=CONTACT_CAP+1).check()
    def test_other_component_caps_stay_fixed(self) -> None:
        for usage,category in [(Usage(endpoints=524288),"endpoints"),
                               (Usage(metadata=786432),"metadata"),
                               (Usage(sources=524288),"sources")]:
            with self.assertRaises(ValueError):
                usage.check(category,1)
if __name__=="__main__":
    unittest.main(verbosity=2)
