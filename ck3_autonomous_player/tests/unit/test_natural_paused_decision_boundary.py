"""Portable focused guard test for CK3 self-pause during a submitted sentinel.

The paused frame is a projection of actual completed SEM1732. The preceding
running/start frames are synthetic counterfactuals, not claims about AUTO1731.
No Native command is issued by this test.
"""
from __future__ import annotations

import copy
import gzip
import json
from pathlib import Path
from unittest import TestCase

from xar_autoplayer.bridge import native_driver as driver


FIXTURE = Path(__file__).parent / "fixtures" / "actual_sem1732_paused_interaction.json.gz"


def _frames():
    with gzip.open(FIXTURE, "rt", encoding="utf-8") as stream:
        record = json.load(stream)
    assert record["schema"] == "xar.p41.paused-interaction-semantic-projection/v1"
    after = record["paused_semantic"]
    assert after["paused"] is True and after["map_ready"] is True
    assert after["date_raw"] == 53220840
    assert after["pending_character_interaction"]["instance_id"] == 1610612749
    before = copy.deepcopy(after)
    before["paused"] = False
    before["revision"] -= 1
    before["native_revision"] -= 1
    before["snapshot_id"] = "native:" + str(before["native_revision"])
    starting = copy.deepcopy(before)
    starting["date_raw"] = 53220696
    starting["revision"] -= 1
    starting["pending_character_interaction"] = None
    return starting, before, after


def _qualified(starting, before, after, actions=(), expected=None):
    boundary = driver._battle_sentinel_player_decision_boundary(after)
    if expected is None:
        expected = driver._battle_sentinel_player_decision_boundary(before)
    return driver._verified_battle_sentinel_paused_decision_boundary(
        starting=starting, before_pause=before, after_pause=after,
        pause_actions=list(actions), inspected_boundary=boundary,
        expected_boundary=expected,
    )


class NaturalPausedDecisionBoundaryTest(TestCase):
    def test_submitted_sentinel_zero_pause_only_on_fresh_same_decision(self):
        starting, before, after = _frames()
        self.assertTrue(_qualified(starting, before, after, actions=()))
        self.assertTrue(_qualified(starting, before, after, actions=[{"step": "pause-map"}]))
        self.assertFalse(_qualified(starting, before, after, actions=[{}, {}]))

    def test_zero_pause_rejects_missing_or_changed_identity_and_stale_frames(self):
        starting, before, after = _frames()
        cases = []
        item = copy.deepcopy(after); item["pending_character_interaction"]["instance_id"] += 1
        cases.append(("other_interaction", starting, before, item, ()))
        item = copy.deepcopy(after); item["diagnostics"]["bridge_pid"] += 1
        cases.append(("other_game", starting, before, item, ()))
        item = copy.deepcopy(after); item["date_raw"] += 24
        cases.append(("later_day", starting, before, item, ()))
        item = copy.deepcopy(after); item["revision"] = before["revision"]
        cases.append(("no_fresh_public_frame", starting, before, item, ()))
        item = copy.deepcopy(after); item["paused"] = False
        cases.append(("not_paused", starting, before, item, ()))
        item = copy.deepcopy(before); item["paused"] = True
        cases.append(("already_paused_before_observation", starting, item, after, ()))
        item = copy.deepcopy(before); item["pending_character_interaction"] = None
        cases.append(("no_running_boundary", starting, item, after, ()))
        item = copy.deepcopy(starting)
        item["date_raw"] = after["date_raw"]
        item["pending_character_interaction"] = copy.deepcopy(after["pending_character_interaction"])
        cases.append(("decision_not_new", item, before, after, ()))
        item = copy.deepcopy(after); item["pending_character_interaction"] = None
        cases.append(("decision_disappeared", starting, before, item, ()))
        for name, start, running, paused, actions in cases:
            with self.subTest(name=name):
                self.assertFalse(_qualified(start, running, paused, actions=actions))
