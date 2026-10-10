"""Copied source inputs beside the existing selected quote, with separate outputs."""
from __future__ import annotations

SHA = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"
_TOP = {"schema", "schema_version", "source_ordinal", "quote_kind", "selected_query_completed",
        "unavailable_reason", "read_only", "native_callbacks_added", "samples"}
_FRAME = {"executable_sha256", "module_base", "native_revision", "query_sequence", "proof_epoch",
          "date_raw", "jailer_full_id", "prisoner_full_id", "recipient_full_id", "definition_identity",
          "interaction_context_identity", "original_scope_identity", "roles_verified_in_owned_context",
          "same_frame_confirmed"}
_SAMPLE = {"sample_index", "frame", "copied_at_existing_query_call", "source_answer_raw_u8",
           "native_answer_raw_u8", "answer_source_ready", "answer_effects_source_ready",
           "source_auto_accept", "native_auto_accept", "recipient_score", "actor_on_send_costs"}
_SCORE = {"producer_rva", "score_block_identity", "base_q64", "modifiers_data_identity",
          "modifier_count_raw_i32", "raw_inputs_complete", "numeric_source_ready", "projected_q64",
          "native_getter_called", "native_getter_returned_output_pointer", "native_final_output_q64",
          "projected_value_matches_native_final", "unavailable_reason", "ordered_modifier_occurrences"}
_ROW = {"native_occurrence_index", "stored_receiver_identity", "vtable_identity", "slot30_target_identity", "raw_receiver_ready"}
_COST = {"cost_block_identity", "numeric_source_ready", "native_getter_called", "clamp_nonnegative_raw_u8",
         "round_raw_u8", "projected_q64", "native_final_q64", "original_output_copied", "original_output_q64",
         "unavailable_reason", "lanes"}
_LANE = {"lane_index", "lane_identity", "mode_c0_i32", "raw_temp_q64", "branch", "unavailable_reason"}

def _check(value: bool, reason: str) -> None:
    if not value:
        raise ValueError("selected prisoner source: " + reason)

def _int(v: object, lo: int, hi: int, *, nullable: bool = False) -> bool:
    return (nullable and v is None) or (type(v) is int and lo <= v <= hi)

def _bool(v: object, *, nullable: bool = False) -> bool:
    return type(v) is bool or (nullable and v is None)

def _reason(v: object) -> bool:
    return v is None or (isinstance(v, str) and bool(v))

def _shape(v: object, keys: set[str]) -> bool:
    return isinstance(v, dict) and set(v) == keys

def _q64(v: object, *, nullable: bool = True) -> bool:
    return _int(v, -(1 << 63), (1 << 63) - 1, nullable=nullable)

def _array(v: object) -> bool:
    return v is None or (isinstance(v, list) and len(v) == 10 and all(_q64(x, nullable=False) for x in v))

def _wrap(v: int) -> int:
    return ((v + (1 << 63)) % (1 << 64)) - (1 << 63)

def _round(v: int) -> int:
    # Exact signed IMUL-high/SAR14 correction, then MOVSXD EDX.
    biased = _wrap(v + (-50000 if v < 0 else 50000))
    shifted = ((biased * 0x29F16B11C6D1E109) >> 64) >> 14
    quotient = shifted + (1 if shifted < 0 else 0)
    narrowed = ((quotient + (1 << 31)) % (1 << 32)) - (1 << 31)
    return narrowed * 100000

def normalize_prisoner_selected_quote_source_12004(
    value: object, *, native_revision: int, query_sequence: int, proof_epoch: int,
    date_raw: int, jailer_full_id: int, prisoner_full_id: int, source_ordinal: int,
    quote_kind: str, existing_quote: dict[str, object] | None = None,
) -> dict[str, object]:
    _check(_shape(value, _TOP), "payload shape")
    v = value
    _check(v["schema"] == "prisoner-selected-quote-source-12004" and v["schema_version"] == 1,
           "schema")
    _check(type(v["source_ordinal"]) is int and v["source_ordinal"] == source_ordinal and
           v["quote_kind"] == quote_kind and quote_kind in ("ordinary_ransom", "negotiated_preview"), "selected route")
    _check(_bool(v["selected_query_completed"]) and _reason(v["unavailable_reason"]) and
           v["read_only"] is True and type(v["native_callbacks_added"]) is int and v["native_callbacks_added"] == 0, "query facts")
    samples = v["samples"]
    _check(isinstance(samples, list) and len(samples) <= 4, "sample bound")
    for index, s in enumerate(samples):
        _check(_shape(s, _SAMPLE) and type(s["sample_index"]) is int and s["sample_index"] == index, "sample order")
        f = s["frame"]
        _check(_shape(f, _FRAME) and f["executable_sha256"] == SHA, "actual build")
        _check(all(type(f[key]) is int and f[key] == expected for key, expected in (
            ("native_revision", native_revision), ("query_sequence", query_sequence), ("proof_epoch", proof_epoch),
            ("jailer_full_id", jailer_full_id), ("prisoner_full_id", prisoner_full_id))), "frame binding")
        _check(f["date_raw"] is None or (type(f["date_raw"]) is int and f["date_raw"] == date_raw
               and -(1 << 31) <= f["date_raw"] < (1 << 31)), "copied date binding")
        _check(all(_int(f[k], 0, (1 << 64)-1) for k in ("module_base", "definition_identity", "interaction_context_identity", "original_scope_identity")), "pointer facts")
        _check(_int(f["recipient_full_id"], 0, (1 << 32)-1, nullable=True) and
               _bool(f["roles_verified_in_owned_context"]) and _bool(f["same_frame_confirmed"]), "role facts")
        ready = f["date_raw"] is not None and f["roles_verified_in_owned_context"] and f["same_frame_confirmed"] and all(f[k] > 0 for k in (
            "module_base", "definition_identity", "interaction_context_identity", "original_scope_identity"))
        if f["roles_verified_in_owned_context"]:
            _check(_int(f["recipient_full_id"], 1, (1 << 32)-2) and f["original_scope_identity"] == f["interaction_context_identity"] + 8, "owned scope")
            if quote_kind == "negotiated_preview":
                _check(f["recipient_full_id"] == prisoner_full_id, "two-role recipient")
        _check(_bool(s["copied_at_existing_query_call"]) and s["copied_at_existing_query_call"] is True, "capture boundary")
        _check(all(_int(s[k], 0, 255, nullable=True) for k in ("source_answer_raw_u8", "native_answer_raw_u8")) and
               all(_bool(s[k]) for k in ("answer_source_ready", "answer_effects_source_ready")) and
               all(_bool(s[k], nullable=True) for k in ("source_auto_accept", "native_auto_accept")), "answer types")
        _check(s["answer_source_ready"] == (s["source_answer_raw_u8"] is not None) and
               (not s["answer_source_ready"] or ready) and
               (not s["answer_effects_source_ready"] or s["answer_source_ready"]), "answer qualification")
        _check(s["source_auto_accept"] is None or ready, "auto-accept frame")
        score = s["recipient_score"]
        if score is not None:
            _check(_shape(score, _SCORE) and score["producer_rva"] == 0x3761780, "score producer")
            _check(_int(score["score_block_identity"], 0, (1 << 64)-1) and
                   (not f["definition_identity"] or score["score_block_identity"] == f["definition_identity"] + 0x1918), "recipient score block")
            _check(all(_q64(score[k]) for k in ("base_q64", "projected_q64", "native_final_output_q64")) and
                   _int(score["modifiers_data_identity"], 0, (1 << 64)-1, nullable=True) and
                   _int(score["modifier_count_raw_i32"], -(1 << 31), (1 << 31)-1, nullable=True), "score raw types")
            _check(all(_bool(score[k]) for k in ("raw_inputs_complete", "numeric_source_ready", "native_getter_called", "native_getter_returned_output_pointer")) and
                   _bool(score["projected_value_matches_native_final"], nullable=True) and _reason(score["unavailable_reason"]), "score facts")
            rows = score["ordered_modifier_occurrences"]
            _check(isinstance(rows, list) and len(rows) <= 4096, "modifier bound")
            for n, row in enumerate(rows):
                _check(_shape(row, _ROW) and type(row["native_occurrence_index"]) is int and row["native_occurrence_index"] == n,
                       "modifier occurrence order")
                _check(all(_int(row[k], 0, (1 << 64)-1, nullable=True) for k in (
                    "stored_receiver_identity", "vtable_identity", "slot30_target_identity")) and _bool(row["raw_receiver_ready"]), "modifier identities")
                if row["raw_receiver_ready"]:
                    _check(all(row[k] is not None and row[k] > 0 for k in (
                        "stored_receiver_identity", "vtable_identity", "slot30_target_identity")), "modifier receiver")
            if score["raw_inputs_complete"]:
                _check(score["base_q64"] is not None and score["modifiers_data_identity"] is not None and
                       _int(score["modifier_count_raw_i32"], 0, 4096) and len(rows) == score["modifier_count_raw_i32"] and
                       all(r["raw_receiver_ready"] for r in rows), "complete modifier input")
            _check(score["numeric_source_ready"] == (score["projected_q64"] is not None), "projected score null")
            if score["numeric_source_ready"]:
                # The live capture currently has no per-modifier returned
                # witness. Only a genuinely copied count0 is complete here.
                _check(ready and score["raw_inputs_complete"] and score["modifier_count_raw_i32"] == 0 and
                       score["projected_q64"] == score["base_q64"] and score["unavailable_reason"] is None, "source score qualification")
            _check(not score["native_getter_returned_output_pointer"] or score["native_getter_called"], "getter call")
            _check(score["native_final_output_q64"] is None or (score["native_getter_called"] and score["native_getter_returned_output_pointer"]), "getter output")
            match = None if score["projected_q64"] is None or score["native_final_output_q64"] is None else score["projected_q64"] == score["native_final_output_q64"]
            _check(score["projected_value_matches_native_final"] is match, "separate score comparison")
        cost = s["actor_on_send_costs"]
        if cost is not None:
            _check(quote_kind == "negotiated_preview" and _shape(cost, _COST), "actor on-send cost route")
            _check(_int(cost["cost_block_identity"], 0, (1 << 64)-1) and
                   (not f["roles_verified_in_owned_context"] or cost["cost_block_identity"] == f["definition_identity"] + 0x40) and
                   all(_bool(cost[k]) for k in ("numeric_source_ready", "native_getter_called", "original_output_copied")) and
                   all(_int(cost[k], 0, 255, nullable=True) for k in ("clamp_nonnegative_raw_u8", "round_raw_u8")) and
                   all(_array(cost[k]) for k in ("projected_q64", "native_final_q64", "original_output_q64")) and
                   _reason(cost["unavailable_reason"]), "cost raw facts")
            _check(cost["original_output_copied"] == (cost["original_output_q64"] is not None), "initial output null")
            lanes = cost["lanes"]
            _check(isinstance(lanes, list) and len(lanes) == 10, "cost lanes")
            for n, lane in enumerate(lanes):
                _check(_shape(lane, _LANE) and lane["lane_index"] == n and
                       lane["lane_identity"] == cost["cost_block_identity"] + 0x40 + n * 0xF0 and
                       _int(lane["mode_c0_i32"], -(1 << 31), (1 << 31)-1, nullable=True) and _q64(lane["raw_temp_q64"]) and
                       isinstance(lane["branch"], str) and bool(lane["branch"]) and _reason(lane["unavailable_reason"]), "ordered cost lane")
            _check(cost["numeric_source_ready"] == (cost["projected_q64"] is not None), "cost projection null")
            if cost["numeric_source_ready"]:
                _check(ready and cost["original_output_copied"] and cost["clamp_nonnegative_raw_u8"] is not None and
                       cost["round_raw_u8"] is not None and all(l["raw_temp_q64"] is not None for l in lanes), "cost source qualification")
                expected = [_wrap(a+l["raw_temp_q64"]) for a,l in zip(cost["original_output_q64"], lanes)]
                if cost["clamp_nonnegative_raw_u8"] != 0:
                    expected = [max(x, 0) for x in expected]
                if cost["round_raw_u8"] != 0:
                    expected = [_round(x) for x in expected]
                _check(cost["projected_q64"] == expected and cost["unavailable_reason"] is None, "cost parent arithmetic")
    if existing_quote and existing_quote.get("status") == "available" and quote_kind == "ordinary_ransom":
        _check(v["selected_query_completed"] is True, "existing quote capture")
        if samples:
            last = samples[-1]
            _check(last["frame"]["recipient_full_id"] is None or last["frame"]["recipient_full_id"] == existing_quote.get("payer_character_id"), "existing recipient join")
            _check(last["native_answer_raw_u8"] is None or last["native_answer_raw_u8"] == existing_quote.get("recipient_answer_status_raw"), "existing answer join")
            if last["recipient_score"] is not None:
                observed = last["recipient_score"]["native_final_output_q64"]
                _check(observed is None or observed == existing_quote.get("recipient_acceptance_raw"), "existing getter join")
    return dict(v)
