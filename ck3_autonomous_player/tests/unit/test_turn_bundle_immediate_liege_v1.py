"""Same-frame immediate liege identity in the ordinary turn bundle."""

from __future__ import annotations

import copy
import unittest

from test_turn_bundle_v1 import PLAYER_ID, _root, _snapshot
from xar_autoplayer.bridge.turn_bundle_contract import build_turn_bundle_v1


class TurnBundleImmediateLiegeV1Tests(unittest.TestCase):
    def test_distinct_immediate_and_top_lieges_keep_their_source_identities(self) -> None:
        source = _root()
        root = source["campaign_root_context"]
        immediate = (3 << 24) | 23_456
        top = (4 << 24) | 34_567
        root.update(
            immediate_liege_character_id=immediate,
            top_liege_character_id=top,
            independent=False,
        )
        root["related_character_contexts"][0]["top_liege_character_id"] = top
        # The root publishes these identities without publishing their contexts.
        self.assertNotIn(
            immediate, [row["character_id"] for row in root["related_character_contexts"]]
        )
        original = copy.deepcopy(source)

        bundle = build_turn_bundle_v1(_snapshot(), source)
        realm = bundle["realm_state"]["value"]

        self.assertEqual(realm["immediate_liege_character_id"], immediate)
        self.assertEqual(realm["top_liege_character_id"], top)
        self.assertFalse(realm["independent"])
        self.assertEqual(realm["direct_landed_vassal_character_ids"], [40])
        self.assertNotIn("immediate_liege_context", realm)
        self.assertEqual(bundle["binding"], source["binding"])
        self.assertEqual(bundle["source"]["query_sequence"], source["query_sequence"])
        self.assertEqual(source, original)

    def test_independent_null_is_not_replaced_by_the_top_liege(self) -> None:
        for explicit_null in (False, True):
            with self.subTest(explicit_null=explicit_null):
                source = _root()
                if explicit_null:
                    source["campaign_root_context"]["immediate_liege_character_id"] = None

                realm = build_turn_bundle_v1(_snapshot(), source)["realm_state"]["value"]

                self.assertIsNone(realm["immediate_liege_character_id"])
                self.assertEqual(realm["top_liege_character_id"], PLAYER_ID)
                self.assertTrue(realm["independent"])

    def test_nonnull_immediate_liege_requires_a_positive_full_int32(self) -> None:
        for invalid in (False, 0, -1, 2**31, "23456"):
            with self.subTest(invalid=invalid):
                source = _root()
                source["campaign_root_context"]["immediate_liege_character_id"] = invalid
                with self.assertRaisesRegex(ValueError, "immediate_liege_character_id"):
                    build_turn_bundle_v1(_snapshot(), source)

    def test_stale_or_unavailable_root_does_not_publish_a_liege_identity(self) -> None:
        stale = _root()
        stale["campaign_root_context"]["immediate_liege_character_id"] = 23_456
        stale["campaign_root_context"]["date_raw"] -= 1
        with self.assertRaisesRegex(ValueError, "date binding changed"):
            build_turn_bundle_v1(_snapshot(), stale)

        unavailable = build_turn_bundle_v1(_snapshot(), _root(available=False))
        self.assertEqual(unavailable["realm_state"]["status"], "unavailable")
        self.assertIsNone(unavailable["realm_state"]["value"])


if __name__ == "__main__":
    unittest.main()
