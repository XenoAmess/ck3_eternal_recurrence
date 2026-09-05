#!/usr/bin/env python3
"""Exact live contracts for Phase-2 career/HC promotion interrupts."""

from __future__ import annotations


_PLAYER_CHARACTER_ID = 29037
_OBSERVED_M_ENTRY_DATE_RAW = 53156688

# Frozen by the authoritative career/HC generator.  Every business event has
# exactly the same four typed event scopes and three authored routes.  Only
# the listed dual-cost mechanisms conditionally hide routes 1 and 2.  The
# retained lineage already proved that shared treasury predicate false at D
# mechanisms 21 and 25, so later dual-cost windows must retain only native
# route 2 unless a live context proves the product state changed.
_DOMAIN_BUSINESS_IDS = {
    "m": tuple(range(92, 98)),
    "n": tuple(range(98, 106)),
    "o": tuple(range(106, 114)),
    "p": tuple(range(114, 121)),
    "q": tuple(range(121, 129)),
}
_DUAL_COST_IDS = frozenset({101, 104, 112, 114, 119})


def _business_contract(domain: str, mechanism_id: int) -> dict[str, object]:
    conditional_defer = mechanism_id in _DUAL_COST_IDS
    return {
        "date_raw": _OBSERVED_M_ENTRY_DATE_RAW,
        "date_policy": "product-observation-window",
        "root_character_id": _PLAYER_CHARACTER_ID,
        "character_scopes": {
            f"zg361_ch_{domain}_event_owner": _PLAYER_CHARACTER_ID,
        },
        "unique_character_scope_excludes": {
            f"zg361_ch_{domain}_event_subject": (_PLAYER_CHARACTER_ID,),
        },
        "scope_types": {
            f"zg361_ch_{domain}_event_cycle": "value",
            f"zg361_ch_{domain}_event_case": "value",
        },
        "boolean_scopes": (),
        "option_count": 1 if conditional_defer else 3,
        **({
            "snapshot_option_count": 3,
            "native_option_indices": (2,),
        } if conditional_defer else {}),
        "selected_option_number": 3 if conditional_defer else 1,
        "selected_native_option_index": 2 if conditional_defer else 0,
    }


CAREER_HC_TIMELINE_CONTRACTS: dict[str, dict[str, object]] = {
    "zg361ch.901": {
        # D completion receipt scheduled by the generated lifecycle effect.
        # Its sole option has no scripted mutation; the case is already
        # closed before this player-only acknowledgement is rendered.
        "date_raw": 53156664,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "scope_types": {},
        "boolean_scopes": (),
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361ch.25": {
        # Like .21, the retained D-lane manager does not satisfy the two
        # treasury-backed routes.  CK3 renders only the always-on defer route
        # in native slot 2; the active-event ABI retains all three slots.
        "date_raw": 53156640,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {"zg361_ch_d_event_owner": 29037},
        "unique_character_scope_excludes": {
            "zg361_ch_d_event_subject": (29037,),
        },
        "scope_types": {
            "zg361_ch_d_event_cycle": "value",
            "zg361_ch_d_event_case": "value",
        },
        "boolean_scopes": (),
        "option_count": 1,
        "snapshot_option_count": 3,
        "native_option_indices": (2,),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
}

for _domain, _mechanism_ids in _DOMAIN_BUSINESS_IDS.items():
    for _mechanism_id in _mechanism_ids:
        CAREER_HC_TIMELINE_CONTRACTS[f"zg361ch.{_mechanism_id}"] = (
            _business_contract(_domain, _mechanism_id)
        )

for _receipt_id in range(902, 907):
    CAREER_HC_TIMELINE_CONTRACTS[f"zg361ch.{_receipt_id}"] = {
        "date_raw": _OBSERVED_M_ENTRY_DATE_RAW,
        "date_policy": "product-observation-window",
        "root_character_id": _PLAYER_CHARACTER_ID,
        "character_scopes": {},
        "scope_types": {},
        "boolean_scopes": (),
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    }
