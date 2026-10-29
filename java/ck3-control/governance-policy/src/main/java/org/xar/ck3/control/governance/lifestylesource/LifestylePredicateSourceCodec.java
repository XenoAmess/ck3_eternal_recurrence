package org.xar.ck3.control.governance.lifestylesource;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.lifestylesource.LifestyleSourceFacts.*;
import static org.xar.ck3.control.governance.lifestylesource.LifestyleSourceSupport.*;

/** Exact copied child288B1B0 normalizer; earlier SIL and native can_select remain separate observations. */
public final class LifestylePredicateSourceCodec {
    public static final String WIRE_KEY = "lifestyle_perk_predicate_source_12004";
    public static final String FACTS_KEY = "lifestyle_perk_predicate_source_facts_12004";
    public static final String SCHEMA = "lifestyle_perk_predicate_source_12004_v1";
    private static final Set<String> ERASED = Set.of("stock_perk_predicate_source_frame_changed", "stock_perk_predicate_source_changed");
    private static final Map<String, String> FRAME = spec("executable_sha256:s module_base:u64 snapshot_identity:s frame_identity:?u64 query_sequence:?u64 mailbox_before_accepted:?b mailbox_after_accepted:?b module_image_size:?u32 module_time_date_stamp:?u32 public_revision:u64 native_revision:u64 proof_epoch:u64 date_raw:i32 played_character_id:u32 caller_domain:s caller_snapshot_confirmed:b");
    private static final Map<String, String> INPUT = spec("command_identity:u64 registry_identity:?u64 requested_full_character_id_u32:?u32 registry_capacity_u32:?u32 indexed_character_identity:?u64 indexed_character_full_id_u32:?u32 used_fallback:?b selected_character_identity:?u64 selected_character_magic_u32:?u32 selected_character_full_id_u32:?u32 selected_character_field_1d0_u64:?u64 selected_perk_identity:?u64 selected_perk_magic_u32:?u32 prefix_admitted:?b unavailable_reason:s");
    private static final Map<String, String> TAIL = spec("value:?b unavailable_reason:s");
    private static final Map<String, String> TRACE = spec("selected_perk_identity:u64 compiled_trigger_receiver_identity:?u64 context_root_word:?u16 context_full_id_payload:?u64 evaluation_flag_raw_u8:?u8 trigger_vtable_raw:?u64 root_kind_getter_slot58_raw:?u64 root_mask_getter_slot60_raw:?u64 final_evaluator_slotc8_raw:?u64 source_projected_returned_raw_u8:?u8 value:?b context_projection_available:b copied_frame_ready:b input_leaf_ready:b child_source_value_ready:b native_callback_executed:b actual_trigger_evaluation_observed:b unavailable_reason:s");
    private static final Map<String, String> PACKET = spec("schema:s read_only:b target_key:s read_frame:o current_thread_tls_array_identity:?u64 inputs:o tail:?o truth_trace:?o value:?b unavailable_reason:s native_can_select_before:?b native_can_select_after:?b repeated_source_match:b");
    private LifestylePredicateSourceCodec() { }

    public static PredicateResult decode(JsonNode raw, Binding binding) {
        java.util.Objects.requireNonNull(binding);
        if (raw == null || raw.isMissingNode()) return new PredicateAbsent(Presence.MISSING);
        if (raw.isNull()) return new PredicateAbsent(Presence.NULL);
        try {
            JsonNode packet = object(raw, PACKET, "packet");
            require(text(packet, "schema").equals(SCHEMA) && yes(packet, "read_only"), "packet:source_schema_invalid");
            String target = text(packet, "target_key"); require(TARGETS.contains(target), "packet:target_not_admitted");
            JsonNode frame = object(packet.get("read_frame"), FRAME, "read_frame");
            require(text(frame, "executable_sha256").equals(EXE) && text(frame, "caller_domain").equals("stock_perk_legality_12004"), "read_frame:actual4_admission_invalid");
            bind(binding, frame, integer(frame, "played_character_id"), target, "read_frame:", false);
            JsonNode inputs = object(packet.get("inputs"), INPUT, "inputs"); validatePrefix(inputs, frame);
            JsonNode tail = packet.get("tail"), trace = packet.get("truth_trace");
            if (!tail.isNull()) object(tail, TAIL, "tail");
            if (!trace.isNull()) object(trace, TRACE, "truth_trace");
            String reason = text(packet, "unavailable_reason");
            boolean erased = ERASED.contains(reason), afterRejected = reason.equals("formal_mailbox_after_guard_rejected"), invalidated = erased || afterRejected;
            if (invalidated) {
                require(isNull(packet, "value") && Boolean.FALSE.equals(bool(frame, "caller_snapshot_confirmed")), "packet:source_invalidation_promoted");
                if (afterRejected) require(Boolean.FALSE.equals(bool(frame, "mailbox_after_accepted")), "read_frame:mailbox_rejection_flag_missing");
                else if (!tail.isNull()) require(isNull(tail, "value"), "tail:source_drift_value_retained");
            }
            Boolean prefix = bool(inputs, "prefix_admitted");
            if (!Boolean.TRUE.equals(prefix)) {
                require(tail.isNull() && trace.isNull(), "packet:tail_after_unadmitted_prefix");
                if (!invalidated) {
                    require(equal(bool(packet, "value"), prefix), "packet:prefix_value_mismatch");
                    require(reason.equals(text(inputs, "unavailable_reason")), "packet:prefix_reason_mismatch");
                }
            } else {
                require(!tail.isNull(), "packet:admitted_prefix_tail_missing");
                if (!invalidated) require(equal(bool(packet, "value"), bool(tail, "value")) && reason.equals(text(tail, "unavailable_reason")), "packet:tail_result_mismatch");
                if (isNull(tail, "value") && !erased) require(!text(tail, "unavailable_reason").isEmpty(), "tail:unknown_reason_missing");
                if (!trace.isNull()) {
                    validateTrace(trace, packet);
                    require(equal(bool(tail, "value"), bool(trace, "value")) || erased, "tail:truth_trace_result_mismatch");
                }
                if (yes(tail, "value")) require(!trace.isNull() && yes(trace, "value"), "tail:true_without_qualified_truth_trace");
            }
            if (isNull(packet, "value")) require(!reason.isEmpty(), "packet:unknown_reason_missing");
            if (yes(packet, "value")) require(yes(frame, "caller_snapshot_confirmed") && nonzero(integer(frame, "module_base"))
                    && (nonzero(nullableInteger(frame, "frame_identity")) || !text(frame, "snapshot_identity").isEmpty()), "packet:true_without_copied_frame_binding");
            return new PredicateDecoded(target, frame(frame, integer(frame, "public_revision"), integer(frame, "played_character_id")),
                    Truth.of(bool(packet, "value")), reason, Truth.of(prefix),
                    tail.isNull() ? Optional.empty() : Optional.of(Truth.of(bool(tail, "value"))), copy(packet));
        } catch (Invalid invalid) {
            String reason = invalid.getMessage();
            for (String bits : Set.of("8", "16", "32", "64")) reason = reason.replace("u" + bits + "_required", "uint" + bits + "_required");
            return new PredicateInvalid(reason.replace("i32_required", "int32_required"));
        }
    }
    private static final class PrefixStop extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final Boolean value;
        PrefixStop(Boolean value, String reason) { super(reason); this.value = value; }
    }
    private static BigInteger read(JsonNode inputs, Set<String> seen, String name, String reason) {
        seen.add(name); BigInteger value = nullableInteger(inputs, name);
        if (value == null) throw new PrefixStop(null, reason); return value;
    }
    private static void validatePrefix(JsonNode inputs, JsonNode frame) {
        var seen = new HashSet<>(Set.of("command_identity", "prefix_admitted", "unavailable_reason"));
        Boolean outcome = true; String reason = "";
        try {
            BigInteger registry = read(inputs, seen, "registry_identity", "lifestyle_perk_character_registry_unavailable");
            boolean fallback = zero(registry);
            if (!fallback) {
                require(nonzero(integer(inputs, "command_identity")) || isNull(inputs, "requested_full_character_id_u32"), "inputs:requested_id_after_null_command");
                BigInteger requested = read(inputs, seen, "requested_full_character_id_u32", "lifestyle_perk_requested_character_full_id_unavailable");
                require(requested.equals(integer(frame, "played_character_id")), "inputs:requested_full_id_frame_mismatch");
                BigInteger capacity = read(inputs, seen, "registry_capacity_u32", "lifestyle_perk_character_registry_capacity_unavailable");
                fallback = requested.and(BigInteger.valueOf(0xFFFFFF)).compareTo(capacity) >= 0;
                if (!fallback) {
                    BigInteger indexed = read(inputs, seen, "indexed_character_identity", "lifestyle_perk_character_registry_row_unavailable");
                    fallback = zero(indexed);
                    if (!fallback) fallback = !read(inputs, seen, "indexed_character_full_id_u32", "lifestyle_perk_indexed_character_full_id_unavailable").equals(requested);
                }
            }
            seen.add("used_fallback"); require(equal(bool(inputs, "used_fallback"), fallback), "inputs:full_generation_fallback_mismatch");
            BigInteger selected;
            if (fallback) selected = read(inputs, seen, "selected_character_identity", "lifestyle_perk_character_fallback_unavailable");
            else {
                seen.add("selected_character_identity"); selected = nullableInteger(inputs, "selected_character_identity");
                require(equal(selected, nullableInteger(inputs, "indexed_character_identity")), "inputs:indexed_selection_mismatch");
            }
            require(!zero(selected) || isNull(inputs, "selected_character_magic_u32"), "inputs:character_magic_after_null_selection");
            BigInteger magic = read(inputs, seen, "selected_character_magic_u32", "lifestyle_perk_character_magic_unavailable");
            if (!magic.equals(BigInteger.valueOf(0x43686172))) throw new PrefixStop(false, "");
            BigInteger full = read(inputs, seen, "selected_character_full_id_u32", "lifestyle_perk_selected_character_full_id_unavailable");
            if (full.equals(new BigInteger("4294967295"))) throw new PrefixStop(false, "");
            if (nonzero(read(inputs, seen, "selected_character_field_1d0_u64", "lifestyle_perk_character_field_1d0_unavailable"))) throw new PrefixStop(false, "");
            require(nonzero(integer(inputs, "command_identity")) || isNull(inputs, "selected_perk_identity"), "inputs:perk_after_null_command");
            BigInteger perk = read(inputs, seen, "selected_perk_identity", "lifestyle_perk_selected_definition_magic_unavailable");
            require(!zero(perk) || isNull(inputs, "selected_perk_magic_u32"), "inputs:perk_magic_after_null_definition");
            outcome = read(inputs, seen, "selected_perk_magic_u32", "lifestyle_perk_selected_definition_magic_unavailable").equals(BigInteger.valueOf(0x4744624F));
        } catch (PrefixStop stop) { outcome = stop.value; reason = stop.getMessage(); }
        require(equal(bool(inputs, "prefix_admitted"), outcome), "inputs:prefix_result_mismatch");
        require(text(inputs, "unavailable_reason").equals(reason), "inputs:prefix_reason_mismatch");
        for (String field : INPUT.keySet()) if (!seen.contains(field)) require(isNull(inputs, field), "inputs:unread_field_filled");
    }
    private static void validateTrace(JsonNode trace, JsonNode packet) {
        JsonNode inputs = packet.get("inputs");
        require(equal(nullableInteger(trace, "selected_perk_identity"), nullableInteger(inputs, "selected_perk_identity")), "truth_trace:perk_identity_mismatch");
        require(yes(trace, "context_projection_available"), "truth_trace:undemanded_context");
        require(Boolean.FALSE.equals(bool(trace, "native_callback_executed")) && Boolean.FALSE.equals(bool(trace, "actual_trigger_evaluation_observed")), "truth_trace:source_projection_promoted_to_native_evaluation");
        BigInteger receiver = nullableInteger(trace, "compiled_trigger_receiver_identity"), perk = integer(trace, "selected_perk_identity");
        if (receiver != null) require(perk.compareTo(U64_MAX.subtract(BigInteger.valueOf(0x80))) <= 0 && receiver.equals(perk.add(BigInteger.valueOf(0x80))), "truth_trace:receiver_binding_mismatch");
        boolean erased = ERASED.contains(text(packet, "unavailable_reason"));
        Set<String> virtual = Set.of("evaluation_flag_raw_u8", "trigger_vtable_raw", "root_kind_getter_slot58_raw", "root_mask_getter_slot60_raw", "final_evaluator_slotc8_raw", "source_projected_returned_raw_u8", "value");
        boolean contextMatches = equal(nullableInteger(trace, "context_root_word"), BigInteger.valueOf(4))
                && equal(nullableInteger(trace, "context_full_id_payload"), nullableInteger(inputs, "selected_character_full_id_u32"));
        if (!contextMatches || receiver == null) {
            require(receiver == null && !yes(trace, "copied_frame_ready"), "truth_trace:receiver_after_unavailable_context");
            for (String field : virtual) require(isNull(trace, field), "truth_trace:undemanded_virtual_field_filled");
        }
        if (!yes(trace, "copied_frame_ready") && !erased) for (String field : virtual) require(isNull(trace, field), "truth_trace:unread_frame_fields_filled");
        BigInteger returned = nullableInteger(trace, "source_projected_returned_raw_u8");
        if (returned == null) {
            require(isNull(trace, "value"), "truth_trace:value_without_returned_byte");
            require(!yes(trace, "child_source_value_ready") || erased, "truth_trace:ready_without_returned_byte");
            require(!text(trace, "unavailable_reason").isEmpty() || erased, "truth_trace:unknown_reason_missing");
        } else {
            require(equal(bool(trace, "value"), nonzero(returned)), "truth_trace:returned_byte_bool_mismatch");
            require(yes(trace, "copied_frame_ready") && yes(trace, "child_source_value_ready"), "truth_trace:returned_byte_not_qualified");
            require(contextMatches && receiver != null && !isNull(trace, "evaluation_flag_raw_u8"), "truth_trace:returned_byte_binding_unavailable");
            if (nonzero(returned)) {
                require(yes(trace, "input_leaf_ready"), "truth_trace:raw_slots_not_outputs");
                for (String field : Set.of("trigger_vtable_raw", "root_kind_getter_slot58_raw", "root_mask_getter_slot60_raw", "final_evaluator_slotc8_raw"))
                    require(nonzero(nullableInteger(trace, field)), "truth_trace:raw_slots_not_outputs");
            }
        }
    }
    public static ObjectNode factsNode(PredicateResult result) {
        java.util.Objects.requireNonNull(result);
        ObjectNode facts = result instanceof PredicateDecoded decoded ? decimalFacts(raw(decoded.original())) : StrictJson.object();
        if (result instanceof PredicateAbsent) { facts.put("status", "absent"); return facts; }
        facts.put("whole_parent_legality_decoded", false);
        if (result instanceof PredicateInvalid invalid) {
            facts.put("status", "invalid"); facts.putNull("value"); facts.put("unavailable_reason", invalid.reason()); return facts;
        }
        PredicateDecoded decoded = (PredicateDecoded) result;
        facts.put("status", "decoded");
        facts.put("source_value_status", switch (decoded.value()) { case UNKNOWN -> "unknown"; case KNOWN_FALSE -> "known_false"; case KNOWN_TRUE -> "known_true"; });
        return facts;
    }
    /** Recompute persisted facts from their retained original; encoded decimal strings are never accepted as native input. */
    public static PredicateResult verifyFacts(JsonNode facts, JsonNode originalPacket, Binding binding) {
        PredicateResult decoded = decode(originalPacket, binding);
        require(facts != null && same(facts, factsNode(decoded)), "facts:predicate_original_projection_mismatch");
        return decoded;
    }
    public static byte[] encodeFacts(PredicateResult result) { return bytes(factsNode(result)); }
}
