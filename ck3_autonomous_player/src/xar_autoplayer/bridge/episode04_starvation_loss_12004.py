"""Read-only R05 evidence predicate; retained observations are never a loss forecast.

The current native journals have independent sequences and no common invocation
key. This predicate exposes the two useful primitives, but cannot upgrade their
same-day coincidence into strict stock-at-writer causal attribution.
"""
from __future__ import annotations

from collections.abc import Mapping

SCALE = 100_000
EXE_SHA256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"
_SUPPLY_RETURN = 0x24E35FF
_DISPATCH_RETURN = 0x2A9AB4B


def _integer(value: object, bits: int = 64, unsigned: bool = False) -> bool:
    return (type(value) is int
            and (0 if unsigned else -(1 << (bits - 1))) <= value
            <= ((1 << bits) - 1 if unsigned else (1 << (bits - 1)) - 1))


def stock_state_12004(raw: object, scale: object, levels: object,
                      fractions: object) -> dict:
    """Exact scalar selection: signed Q64 /100000 trunc0, then signed32 cast.

    Loaded arrays are operands, not assumed stock constants. The strict raw
    threshold and native state selection are deliberately separate outputs.
    """
    if type(scale) is not int or scale != SCALE:
        raise ValueError("supply scale must be exactly 100000")
    if not _integer(raw):
        raise ValueError("supply raw must be signed int64, not bool/float")
    if (not isinstance(levels, list) or any(not _integer(v, 32) for v in levels)
            or not isinstance(fractions, list) or any(not _integer(v) for v in fractions)):
        raise ValueError("loaded supply arrays must be typed integer lists")
    integer = (abs(raw) // SCALE) * (-1 if raw < 0 else 1)
    bits = integer & 0xFFFFFFFF
    integer = bits - 0x100000000 if bits & 0x80000000 else bits
    index = next((i for i, threshold in enumerate(levels) if integer >= threshold), len(levels)-1)
    base = fractions[index] if 0 <= index < len(fractions) else 0
    return {"scale": SCALE, "stock_integer": integer, "state_index": index,
            "base_fraction_raw": base, "strict_raw_below_ten": raw < 10*SCALE,
            "nonnegative_strict_below_ten": 0 <= raw < 10*SCALE,
            "negative_raw": raw < 0,
            "loaded_arrays_are_stock_60_10_0": levels == [60, 10, 0] and fractions == [0, 0, 5000]}


def _physical_debit(event: Mapping) -> int | None:
    """Recompute unique owned slots; never use request or cached raised deltas."""
    if (event.get("same_instance_after") is not True
            or event.get("physical_capture_complete") is not True
            or event.get("physical_debit_observed") is not True
            or event.get("capture_failure_flags") != 0):
        return None
    slots = event.get("physical_slots")
    aliases = event.get("data_aliases")
    count = event.get("native_data_record_count")
    if (not isinstance(slots, list) or not isinstance(aliases, list)
            or type(count) is not int or count < 0
            or event.get("captured_data_record_count") != count
            or len(aliases) != count or event.get("physical_slot_count") != len(slots)):
        return None
    covered = set()
    for ordinal, alias in enumerate(aliases):
        if not isinstance(alias, Mapping) or alias.get("data_record_index") != ordinal:
            return None
        index = alias.get("physical_slot_index")
        if (type(index) is not int or not 0 <= index < len(slots)
                or not _integer(alias.get("persistent_regiment_id"), 32)
                or not _integer(alias.get("data_chunk_ordinal"), 32)):
            return None
        covered.add(index)
    if covered != set(range(len(slots))):
        return None
    total = 0
    for index, slot in enumerate(slots):
        if (not isinstance(slot, Mapping) or slot.get("physical_slot_index") != index
                or slot.get("same_instance_after") is not True):
            return None
        before, after = slot.get("before"), slot.get("after")
        if not isinstance(before, Mapping) or not isinstance(after, Mapping):
            return None
        for key in ("current_soldiers", "maximum_soldiers", "state_raw"):
            if not _integer(before.get(key), 32) or not _integer(after.get(key), 32):
                return None
        total += before["current_soldiers"] - after["current_soldiers"]
    return total if event.get("actual_physical_soldier_debit") == total else None


def assess_episode04_starvation_loss_12004(
    army: Mapping, *, window: Mapping, loss_after_sequence: int,
    callback_after_sequence: int,
) -> dict:
    """Consume normalized current journals plus explicit observed endpoint facts.

    `window` is the caller's evidence extract, not a trusted synthesized scene.
    Its references must be preserved by the outer artifact owner. There is no
    action, observer installation, replay, native call or input mutation here.
    """
    if not _integer(loss_after_sequence, unsigned=True) or not _integer(callback_after_sequence, unsigned=True):
        raise ValueError("each journal requires its own nonnegative uint64 fence")
    reasons = []
    result = {"schema": "episode04-starvation-loss-12004-v1", "evidence_scope": "retained-native-observations-predicate",
              "status": "unknown", "strict_starvation_causal_attribution": "unknown",
              "actual_supply_preferred_physical_debit_soldiers": None,
              "callback_after_nonnegative_stock_below_ten_observed": False,
              "source_endpoint_candidate": False, "candidate_callback_sequences": [],
              "supply_preferred_writer_sequences": [], "rejected_writer_sequences": [],
              "unknown_reasons": reasons, "new_live_evidence": False,
              "future_loss_projected": False, "native_calls_executed": 0}
    exe_sha256 = window.get("executable_sha256")
    if (window.get("game_version") != "1.20.0.4"
            or not isinstance(exe_sha256, str) or exe_sha256.lower() != EXE_SHA256):
        reasons.append("exact_build_binding_missing_or_mismatched")
    if not isinstance(window.get("machine_id"), str) or not window.get("machine_id"):
        reasons.append("machine_id_missing")
    for key in ("endpoint_references", "roster_before", "roster_after"):
        if not isinstance(window.get(key), list) or not window[key]:
            reasons.append(key + "_missing")
    if window.get("roster_before") != window.get("roster_after"):
        reasons.append("regiment_membership_or_order_changed")
    for key in ("same_session", "same_army_full_ids", "exact_day", "stationary_window",
                "no_county_arrival", "no_reorganization", "no_combat", "no_gathering"):
        if window.get(key) is not True:
            reasons.append(key + "_not_observed")
    before, after = window.get("date_before_raw"), window.get("date_after_raw")
    if not _integer(before, 32) or not _integer(after, 32) or after-before != 24:
        reasons.append("window_is_not_observed_exact_plus24")
    inputs = army.get("monthly_loss_budget_inputs_v1")
    inputs = inputs if isinstance(inputs, Mapping) else {}
    losses = army.get("actual_loss_writer_observations_v1")
    callbacks = army.get("actual_supply_callback_observations_v1")
    if not isinstance(losses, Mapping) or not isinstance(callbacks, Mapping):
        reasons.append("required_actual_journal_absent")
        return result
    if losses.get("membership_basis") != "membership_at_query":
        reasons.append("writer_membership_basis_unrecognized")
    if losses.get("source") != "native_natural_writer_entry_return":
        reasons.append("writer_source_unrecognized")
    if callbacks.get("identity_basis") != "public_unit_and_native_carmy_full_ids_at_invocation":
        reasons.append("callback_identity_basis_unrecognized")
    if callbacks.get("source") != "native_natural_supply_callback_entry_return":
        reasons.append("callback_source_unrecognized")
    selected = {}
    for label, family, fence in (("loss", losses, loss_after_sequence), ("callback", callbacks, callback_after_sequence)):
        events = family.get("events")
        if (family.get("status") != "available" or family.get("observer_installed") is not True
                or not isinstance(events, list) or family.get("event_count") != len(events)):
            reasons.append(label + "_journal_unavailable")
            return result
        oldest, latest = family.get("oldest_available_sequence"), family.get("latest_sequence")
        if (not _integer(oldest, unsigned=True) or not _integer(latest, unsigned=True)
                or latest < fence or (oldest > fence+1 and latest > fence)):
            reasons.append(label + "_journal_fence_gap_or_reset")
        if family.get("unattributed_capture_failures") != 0:
            reasons.append(label + "_unattributed_capture_failures")
        seqs = [e.get("sequence") for e in events if isinstance(e, Mapping)]
        if len(seqs) != len(events) or any(not _integer(s, unsigned=True) for s in seqs) or seqs != sorted(set(seqs)):
            reasons.append(label + "_event_sequences_malformed")
            return result
        selected[label] = [event for event in events if event["sequence"] > fence]
    candidates = []
    for event in selected["callback"]:
        if (event.get("caller_return_rva") != _DISPATCH_RETURN
                or event.get("same_instance_after") is not True or event.get("capture_failure_flags") != 0
                or event.get("army_id") != window.get("army_id")
                or event.get("native_carmy_id") != window.get("native_carmy_id")):
            reasons.append("callback_route_identity_or_capture_incomplete")
            continue
        date = event.get("passed_date_raw64")
        if not _integer(date, unsigned=True) or (date & 0xFFFFFFFF) != after:
            reasons.append("callback_date_outside_window")
            continue
        try:
            state = stock_state_12004(event["after"]["supply_raw"], SCALE,
                inputs.get("loaded_supply_state_levels"), inputs.get("loaded_supply_state_fractions_raw"))
        except (ValueError, KeyError, TypeError):
            reasons.append("callback_poststock_or_loaded_state_unavailable")
            continue
        if state["negative_raw"]:
            reasons.append("negative_poststock_outside_successful_updater_domain")
        if state["nonnegative_strict_below_ten"]:
            candidates.append(event["sequence"])
        if not state["loaded_arrays_are_stock_60_10_0"]:
            reasons.append("loaded_state_table_is_not_stock_ten_threshold")
    result["candidate_callback_sequences"] = candidates
    result["callback_after_nonnegative_stock_below_ten_observed"] = bool(candidates)
    debits = []
    for event in selected["loss"]:
        sequence = event["sequence"]
        if event.get("army_regiment_id") not in window.get("roster_after", []):
            reasons.append("writer_outside_stable_full_roster")
            continue
        debit = _physical_debit(event)
        source_supply = (event.get("caller_kind") == "supply_preferred"
                         and event.get("caller_return_rva") == _SUPPLY_RETURN
                         and event.get("request_scale") == SCALE
                         and type(event.get("request_scale")) is int)
        if event.get("observed_date_raw") != after or not source_supply or debit is None:
            result["rejected_writer_sequences"].append(sequence)
            reasons.append("writer_not_complete_source_matched_supply_preferred")
            continue
        result["supply_preferred_writer_sequences"].append(sequence)
        debits.append(debit)
    if debits:
        result["actual_supply_preferred_physical_debit_soldiers"] = sum(debits)
    if len(selected["callback"]) != 1:
        reasons.append("callback_not_unique_in_window")
    result["source_endpoint_candidate"] = (not reasons and bool(candidates) and sum(debits) > 0)
    # No ordinal comparison between two unrelated sequence domains is valid.
    reasons.append("no_shared_callback_writer_invocation_key_or_stock_at_writer_capture")
    if not selected["loss"]:
        reasons.append("empty_retained_writer_history_does_not_prove_zero_loss")
    result["unknown_reasons"] = list(dict.fromkeys(reasons))
    return result
