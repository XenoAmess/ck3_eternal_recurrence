#!/usr/bin/env python3
"""Source-reviewed aging health manager-recovery interrupt contracts."""

from __future__ import annotations

from typing import Final


MANAGER_HEALTH_AGING_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "health.7000": {
        # Vanilla onset of infirmity.  Exact CK3 1.19.0.6 source and the R117
        # native event context both expose one unavoidable acknowledgement:
        # no saved scopes, one rendered/native option, and an infirm trait
        # indicator.  There is no alternate branch to optimize.
        "date_raw": 53152296,
        "root_character_id": 29037,
        "character_scopes": {},
        "boolean_scopes": (),
        "saved_scope_count": 0,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "health.7200": {
        # Vanilla yearly-health onset of withering mind.  The event has no
        # saved scopes and exposes one mandatory acknowledgement whose sole
        # scripted effect adds the indicated withering_mind trait.  There is
        # no alternative branch to prefer; bind the complete one-option frame
        # before acknowledging it.
        "date_raw": 53152296,
        "root_character_id": 29037,
        "character_scopes": {},
        "boolean_scopes": (),
        "saved_scope_count": 0,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "health.7400": {
        # Vanilla yearly-health onset of faltering heart. The event has no
        # saved scopes and one unavoidable acknowledgement whose sole effect
        # adds the indicated trait. Bind the complete R103 one-option frame.
        "date_raw": 53190360,
        "root_character_id": 29037,
        "character_scopes": {},
        "boolean_scopes": (),
        "saved_scope_count": 0,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "health.7500": {
        # Vanilla yearly-health onset of fragile bones. Like health.7200, the
        # event has no saved scopes and one unavoidable acknowledgement. Its
        # sole scripted effect adds fragile_bones, so there is no alternative
        # branch to optimize; bind the complete one-option frame first.
        "date_raw": 53152296,
        "root_character_id": 29037,
        "character_scopes": {},
        "boolean_scopes": (),
        "saved_scope_count": 0,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
}
