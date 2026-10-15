"""Join copied invocation identities, never unrelated journal sequences or dates."""
from __future__ import annotations

from collections.abc import Mapping
from .episode04_starvation_loss_12004 import _physical_debit, EXE_SHA256


def join_actual_supply_parent_writer_observations_v1(
    army: Mapping, *, game_version: str, executable_sha256: str,
    callback_after_sequence: int, loss_after_sequence: int,
) -> dict:
    if (type(callback_after_sequence) is not int or callback_after_sequence < 0
            or type(loss_after_sequence) is not int or loss_after_sequence < 0):
        raise ValueError("separate journal fences must be nonnegative integers")
    result = dict(source="copied_natural_callback_context_at_actual_writer_entry",
        status="unavailable", events=[], joined_writer_count=0,
        strict_below_ten_supply_physical_debit_soldiers=None,
        source_supply_writer_at_exact_ten_count=0,
        physical_debit_sum_scope="only_complete_keyed_source_supply_preferred_invocations",
        complete_selected_writer_history_joined=False,
        unknown_reasons=[], new_live_evidence=False, native_calls_executed=0,
        callback_sequence_order_used=False, callback_entry_stock_used=False,
        callback_return_stock_used=False)
    why=result["unknown_reasons"]
    if (game_version!="1.20.0.4" or not isinstance(executable_sha256,str)
            or executable_sha256.lower()!=EXE_SHA256):
        why.append("exact_build_binding_missing_or_mismatched");return result
    callbacks=army.get("actual_supply_callback_observations_v1")
    writers=army.get("actual_loss_writer_observations_v1")
    if not isinstance(callbacks,Mapping) or not isinstance(writers,Mapping):
        why.append("required_actual_journal_absent");return result
    for label,family,fence in [("callback",callbacks,callback_after_sequence),("writer",writers,loss_after_sequence)]:
        oldest,latest=family.get("oldest_available_sequence"),family.get("latest_sequence")
        if (type(oldest) is not int or type(latest) is not int or latest<fence
                or (oldest>fence+1 and latest>fence)):
            why.append(label+"_fence_gap_or_reset")
        if family.get("unattributed_capture_failures")!=0:
            why.append(label+"_unattributed_capture_failures")
        sequences=[event["sequence"] for event in family.get("events",[])]
        if sequences!=sorted(set(sequences)):
            why.append(label+"_event_sequences_repeated_or_unordered")
    events=callbacks.get("events",[])
    index={};duplicates=set()
    for callback in events:
        if callback["sequence"]<=callback_after_sequence:continue
        meta=callback.get("supply_parent_invocation_v1")
        if not isinstance(meta,Mapping):continue
        token=meta["invocation_token"]
        if token in index:duplicates.add(token)
        index[token]=callback
    if duplicates:why.append("duplicate_callback_invocation_token")
    debit_total=0;positive=False
    for writer in writers.get("events",[]):
        if writer["sequence"]<=loss_after_sequence:continue
        row=dict(writer_sequence=writer["sequence"],status="unknown",reason=None,
            invocation_token=None,callback_sequence=None,stock_at_writer_entry_raw=None,
            physical_debit_soldiers=_physical_debit(writer),source_supply_preferred=False,
            source_siege_or_raid_preferred=False,strict_below_ten=False,exact_ten=False)
        result["events"].append(row)
        context=writer.get("supply_parent_context_v1")
        if not isinstance(context,Mapping):row["reason"]="parent_context_absent";continue
        invocation=context["invocation"];token=invocation["invocation_token"]
        row["invocation_token"]=token
        callback=index.get(token)
        if callback is None or token in duplicates:row["reason"]="unique_retained_callback_token_missing";continue
        row["callback_sequence"]=callback["sequence"]
        if invocation!=callback["supply_parent_invocation_v1"]:
            row["reason"]="invocation_thread_depth_route_mismatch";continue
        if (context["capture_failure_flags"]!=0 or context["receiver_identity_matches"] is not True
                or not callback["same_instance_after"] or callback["capture_failure_flags"]!=0
                or context["army_id"]!=callback["army_id"]
                or context["native_carmy_id"]!=callback["native_carmy_id"]
                or context["passed_date_raw64"]!=callback["passed_date_raw64"]
                or context["army_id"]!=army.get("army_id")
                or context["native_carmy_id"]!=army.get("native_carmy_id")):
            row["reason"]="parent_receiver_identity_or_capture_incomplete";continue
        stock=context["stock_at_writer_entry_raw"]
        if stock is None:row["reason"]="stock_at_writer_entry_unavailable";continue
        if context["stock_scale"]!=100000:
            row["reason"]="stock_at_writer_scale_mismatch";continue
        date=context["passed_date_raw64"]
        if date is None or (date & 0xFFFFFFFF)!=(writer["observed_date_raw"] & 0xFFFFFFFF if type(writer["observed_date_raw"]) is int else None):
            row["reason"]="writer_clock_and_actual_callback_date_differ";continue
        row.update(status="joined",stock_at_writer_entry_raw=stock,
            source_supply_preferred=(writer["caller_kind"]=="supply_preferred" and writer["caller_return_rva"]==0x24E35FF),
            source_siege_or_raid_preferred=(writer["caller_kind"]=="siege_or_raid_preferred" and writer["caller_return_rva"]==0x24E377C),
            strict_below_ten=0<=stock<1000000,exact_ten=stock==1000000)
        result["joined_writer_count"]+=1
        if row["source_supply_preferred"] and row["exact_ten"]:
            result["source_supply_writer_at_exact_ten_count"]+=1
        if (row["source_supply_preferred"] and row["strict_below_ten"]
                and row["physical_debit_soldiers"] is not None
                and row["physical_debit_soldiers"]>0):
            positive=True;debit_total+=row["physical_debit_soldiers"]
    if positive and not why:
        result["strict_below_ten_supply_physical_debit_soldiers"]=debit_total
    result["complete_selected_writer_history_joined"]=(
        not why and bool(result["events"]) and all(e["status"]=="joined" for e in result["events"]))
    result["status"]="available" if not why and result["events"] and all(e["status"]=="joined" for e in result["events"]) else "partial"
    return result
