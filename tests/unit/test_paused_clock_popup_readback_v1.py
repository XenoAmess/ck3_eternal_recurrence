import copy
import unittest
from tools.g2_saved_campaign.paused_clock_popup_readback_v1 import paused_clock_popup_readback_v1


class PausedClockPopupTests(unittest.TestCase):
    def setUp(self):
        # The relevant fields of the actual paused Native event readback.
        # Request identities, process identities and filesystem paths are absent.
        self.event = {"paused": True, "ordinary_events": [],
            "active_event": {"source": "native", "instance_id": 110,
                "option_count": 3, "options": [
                    {"index": index, "option_number": index + 1, "enabled": True}
                    for index in range(3)]},
            "pending_character_interaction": None,
            "final_screen": None, "event_resolution": "typed_query_required"}

    def test_actual_event_projection_is_retained(self):
        before = copy.deepcopy(self.event)
        self.assertTrue(paused_clock_popup_readback_v1(self.event))
        self.assertEqual(before, self.event)

    def test_legacy_map_shape(self):
        value = dict(self.event, active_event=None, final_screen="map_hud", event_resolution="none")
        self.assertTrue(paused_clock_popup_readback_v1(value))

    def test_unresolved_interaction_shape(self):
        value = dict(self.event, active_event=None, event_resolution="none",
                     pending_character_interaction={"instance_id": "synthetic-pending"})
        self.assertTrue(paused_clock_popup_readback_v1(value))

    def test_malformed_event_and_resolution_are_rejected(self):
        for mutation in ({"instance_id": True}, {"instance_id": 0},
                         {"option_count": False}, {"option_count": 0}):
            with self.subTest(mutation=mutation):
                value = copy.deepcopy(self.event)
                value["active_event"].update(mutation)
                self.assertFalse(paused_clock_popup_readback_v1(value))
        for mutation in ({"paused": False}, {"final_screen": "map_hud"},
                         {"event_resolution": "selected"}, {"event_resolution": "none"},
                         {"ordinary_events": [{"selected": True}]},
                         {"pending_character_interaction": {}}):
            with self.subTest(mutation=mutation):
                self.assertFalse(paused_clock_popup_readback_v1(dict(self.event, **mutation)))


if __name__ == "__main__":
    unittest.main()
