"""Source-specific component labels for existing normalized actual4 writer rows.

This does not join callbacks, infer stock, compute a soldier debit or establish
history completeness. Use the existing keyed join and physical capture for those.
"""
from __future__ import annotations
from collections.abc import Mapping


def classify_actual_loss_component_12004(writer: Mapping[str, object]) -> dict:
    result = dict(source="exact_actual4_callback_and_allocator_callsites",
        component="unknown", phase="unknown", source_ready=False,
        reason="unrecognized_writer_caller", physical_loss_inferred=False)
    pc, kind = writer.get("caller_return_rva"), writer.get("caller_kind")
    direct = {
        (0x24E35FF,"supply_preferred"): ("supply","preferred"),
        (0x24E377C,"siege_or_raid_preferred"): ("siege_or_raid","preferred"),
    }
    if type(pc) is int and isinstance(kind,str) and (pc,kind) in direct:
        component,phase=direct[(pc,kind)]
        return {**result,"component":component,"phase":phase,"source_ready":True,"reason":None}
    if pc!=0x2A958E8 or kind!="residual_allocator":
        return result
    context=writer.get("residual_parent_context_v1")
    if not isinstance(context,Mapping):
        return {**result,"reason":"residual_parent_context_absent"}
    if (context.get("source_complete") is not True
            or type(context.get("capture_failure_flags")) is not int
            or context["capture_failure_flags"]!=0
            or context.get("parent_kind")!=4
            or context.get("allocator_entry_rva")!=0x2A957E0
            or context.get("observed_continuation_rva")!=0x2A957E8
            or any(context.get(key) is not True for key in (
                "receiver_identity_matches","array_header_matches","writer_full_id_in_actual_array"))):
        return {**result,"reason":"residual_source_capture_incomplete"}
    outer,flags=context.get("allocator_caller_return_rva"),context.get("flags_raw")
    if type(outer) is not int or type(flags) is not int:
        return {**result,"reason":"residual_callsite_or_flags_unavailable"}
    source=context.get("request_source")
    if source=="county_entry":
        if outer==0x24E2630 and flags==0:
            return {**result,"component":"county_entry","phase":"residual",
                "source_ready":True,"reason":None}
        return {**result,"reason":"county_callsite_flags_conflict"}
    if source!="periodic_callback" or context.get("enclosing_parent_kind")!=1:
        return {**result,"reason":"periodic_callback_parent_unproven"}
    supply=writer.get("supply_parent_context_v1")
    invocation=supply.get("invocation") if isinstance(supply,Mapping) else None
    if (not isinstance(invocation,Mapping)
            or context.get("parent_invocation_token")!=invocation.get("invocation_token")
            or context.get("native_thread_id")!=invocation.get("native_thread_id")
            or context.get("army_id")!=supply.get("army_id")
            or context.get("native_carmy_id")!=supply.get("native_carmy_id")
            or supply.get("receiver_identity_matches") is not True
            or supply.get("capture_failure_flags")!=0):
        return {**result,"reason":"residual_and_periodic_copied_identity_mismatch"}
    if (outer,flags)==(0x24E3638,2):
        return {**result,"component":"supply","phase":"residual","source_ready":True,"reason":None}
    if (outer,flags)==(0x24E37B3,0):
        return {**result,"component":"siege_or_raid","phase":"residual","source_ready":True,"reason":None}
    return {**result,"reason":"periodic_callsite_flags_conflict"}
