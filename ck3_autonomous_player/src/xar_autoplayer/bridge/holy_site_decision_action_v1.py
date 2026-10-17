"""Finite original HolySite decision identities shared by typed read/action paths."""
from __future__ import annotations

from types import MappingProxyType
from typing import Literal, cast

HolySiteDecisionActionV1 = Literal["adopt", "promote", "demote", "abandon"]

HOLY_SITE_DECISION_KEYS_V1 = MappingProxyType({
    "adopt": "adopt_holy_site_decision",
    "promote": "elevate_holy_site_decision",
    "demote": "demote_holy_site_decision",
    "abandon": "abandon_holy_site_decision",
})


def normalize_holy_site_decision_action_v1(value: object) -> HolySiteDecisionActionV1:
    """Reject arbitrary keys, coercions and unknown actions before native I/O."""
    if type(value) is not str or value not in HOLY_SITE_DECISION_KEYS_V1:
        raise ValueError("HolySite decision action must be adopt, promote, demote or abandon")
    return cast(HolySiteDecisionActionV1, value)


def holy_site_decision_key_v1(value: object) -> str:
    return HOLY_SITE_DECISION_KEYS_V1[normalize_holy_site_decision_action_v1(value)]
