"""Four source-closed zero-request branches of government/first-Land312A950."""
from __future__ import annotations

KNOWN_ZERO_STAGES_FOLLOWING_312A950_12003 = (
    "government_bit29_false", "character_1b0_absent", "first_land_invalid", "first_land_nonnegative",
)


def following312a950_stage_selection_12003(leaf):
    government = leaf["government_source"]
    if not government["ready"]:
        return None
    if not government["flags_raw_u32"] & 0x20000000:
        return "government_bit29_false"
    state = leaf["character_state_present"]
    if state is False:
        return "character_1b0_absent"
    first = leaf["first_land_source"]
    land = leaf["land_resolution"]
    if state is not True or first is None or not first["ready"] or land is None or not land["ready"]:
        return None
    if land["admitted"] is False:
        return "first_land_invalid"
    balance = land["balance_raw_q64"]
    if land["admitted"] is True and balance is not None:
        return "first_land_nonnegative" if balance >= 0 else "negative_land_mode3_income_unobserved"
    return None


def emit_following_312a950_requests_12003(leaf):
    if not leaf["ready"] or leaf["stage_selection"] not in KNOWN_ZERO_STAGES_FOLLOWING_312A950_12003:
        raise ValueError("Required native input unavailable: following_government_land_312a950")
    return ()
