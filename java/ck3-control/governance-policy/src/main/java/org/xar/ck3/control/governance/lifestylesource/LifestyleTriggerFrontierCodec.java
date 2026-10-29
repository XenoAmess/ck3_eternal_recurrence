package org.xar.ck3.control.governance.lifestylesource;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.lifestylesource.LifestyleSourceFacts.*;
import static org.xar.ck3.control.governance.lifestylesource.LifestyleSourceSupport.*;

/** Four independently qualified copied output planes. Raw addresses never become returned outputs. */
public final class LifestyleTriggerFrontierCodec {
    public static final String WIRE_KEY = "lifestyle_perk_trigger_frontier_12004";
    public static final String FACTS_KEY = "lifestyle_perk_trigger_frontier_facts_12004";
    public static final String SCHEMA = "lifestyle-perk-trigger-frontier-12004-v1";
    private static final List<String> OUTPUTS = List.of("returned_raw_u8", "returned_raw_u16", "returned_qword0", "returned_qword1");
    private static final Map<String, String> FRAME = spec("executable_sha256:s module_base:u64 frame_identity:?u64 snapshot_identity:s native_revision:u64 query_sequence:?u64 proof_epoch:u64 date_raw:?i32 caller_domain:s caller_snapshot_confirmed:b");
    private static final Map<String, String> TARGET = spec("slot_identity:?u64 target_identity:?u64 target_rva:?u64 copied:b unavailable_reason:s");
    private static final Map<String, String> INPUT = spec("read_frame:o module_image_size:?u32 module_time_date_stamp:?u32 public_revision:u64 mailbox_before_accepted:?b mailbox_after_accepted:?b target_key:s capture_scope:s command_identity:u64 selected_perk_identity:u64 requested_full_character_id:u32 selected_character_identity:?u64 selected_character_full_id:?u32 receiver_identity:?u64 vtable_identity:?u64 vtable_rva:?u64 slots:o source_context_root_word:?u16 source_context_full_id_payload:?u64 context_is_source_projection:b descriptor_provider:?o caller_before_after_confirmed:b repeated_raw_match:b native_before:?b native_after:?b unavailable_reason:s");
    private static final Map<String, String> DESCRIPTOR = spec("read_frame:o caller_root_kind_raw_u16:?u16 table_identity:?u64 initialization_guard_raw_i32:?i32 table_data_identity:?u64 capacity_raw_i32:?i32 count_raw_i32:?i32 selected_source_fallback:?b selected_descriptor_identity:?u64 descriptor_validator_pointer10:?u64 descriptor_selection_inputs_copied:b descriptor_validator_pointer_copied:b initializer_semantics_source_closed:b native_provider_return_observed:b unavailable_reason:s");
    private static final Map<String, String> LANE = spec("lane:s call_rva:u64 return_rva:u64 target:o raw_target_ready:b source_value_ready:b returned_raw_u8:?u8 returned_raw_u16:?u16 returned_qword0:?u64 returned_qword1:?u64 result_source:s closed_target_proof:?o natural_witness:?o unavailable_reason:s");
    private static final Map<String, String> PROOF = spec("target_rva:u64 exact_source_sha256:s producer_key:s complete_pure_readonly_body:b");
    private static final Map<String, String> EVENT = spec("clock_identity:u64 sequence:u64 thread_id:?u32");
    private static final Map<String, String> WITNESS = spec("read_frame:o query_cursor:o call_event:o return_event:o call_rva:u64 return_rva:u64 selected_perk_identity:u64 receiver_identity:u64 target_identity:u64 original_rcx:u64 original_rdx:u64 original_root_word:?u16 original_full_id_payload:?u64 returned_raw_u8:?u8 returned_raw_u16:?u16 returned_qword0:?u64 returned_qword1:?u64 original_matching_call_count:u32 original_call_observed:b original_return_observed:b");
    private static final Map<String, String> PACKET = spec("schema:s read_only:b copied_input_binding_ready:b inputs:o lanes:o");
    private static final Map<String, String> SLOTS = spec("slot58:o slot60:o slotc8:o");
    private static final Map<String, String> LANES = spec("descriptor_al:o root_kind_ax:o root_mask_qwords:o final_c8_al:o");
    private record Definition(String name, long call, long returned, Set<String> demanded, Optional<String> slot, long offset) { }
    private static final List<Definition> DEFINITIONS = List.of(
            new Definition("descriptor_al", 0x372E0AE, 0x372E0B0, Set.of("returned_raw_u8"), Optional.empty(), 0),
            new Definition("root_kind_ax", 0x372B4D3, 0x372B4D6, Set.of("returned_raw_u16"), Optional.of("slot58"), 0x58),
            new Definition("root_mask_qwords", 0x372B4EE, 0x372B4F1, Set.of("returned_qword0", "returned_qword1"), Optional.of("slot60"), 0x60),
            new Definition("final_c8_al", 0x372E34D, 0x372E353, Set.of("returned_raw_u8"), Optional.of("slotc8"), 0xC8));
    private LifestyleTriggerFrontierCodec() { }

    public static FrontierResult decode(JsonNode raw, Binding binding) {
        java.util.Objects.requireNonNull(binding);
        if (raw == null || raw.isMissingNode()) return new FrontierAbsent(Presence.MISSING);
        if (raw.isNull()) return new FrontierAbsent(Presence.NULL);
        try {
            JsonNode packet = object(raw, PACKET, "packet");
            require(text(packet, "schema").equals(SCHEMA) && yes(packet, "read_only"), "packet:frontier_schema_invalid");
            JsonNode inputs = object(packet.get("inputs"), INPUT, "inputs"), frame = frameNode(inputs.get("read_frame"), "inputs.read_frame");
            String target = text(inputs, "target_key"), scope = text(inputs, "capture_scope");
            require(TARGETS.contains(target), "inputs:target_not_admitted");
            require(Set.of("unavailable", "owned_memory_fixture", "actual_application_query").contains(scope), "inputs:capture_scope_not_admitted");
            bind(binding, frame, integer(inputs, "requested_full_character_id"), target, "inputs:", true);
            object(inputs.get("slots"), SLOTS, "inputs.slots");
            BigInteger vtableRva = nullableInteger(inputs, "vtable_rva"), vtable = nullableInteger(inputs, "vtable_identity");
            if (vtableRva != null) require(bounded(inputs, vtable, 1) && vtableRva.equals(vtable.subtract(integer(frame, "module_base"))), "inputs:bounded_vtable_rva_mismatch");
            JsonNode provider = inputs.get("descriptor_provider");
            if (!provider.isNull()) { object(provider, DESCRIPTOR, "inputs.descriptor_provider"); frameNode(provider.get("read_frame"), "inputs.descriptor_provider.read_frame"); }
            if (!yes(inputs, "context_is_source_projection"))
                require(isNull(inputs, "source_context_root_word") && isNull(inputs, "source_context_full_id_payload") && provider.isNull(), "inputs:undemanded_projected_context_filled");
            boolean bindingReady = yes(packet, "copied_input_binding_ready");
            require(!bindingReady || inputBound(inputs), "packet:copied_input_binding_unavailable");
            if (Boolean.FALSE.equals(bool(inputs, "mailbox_after_accepted")))
                require(!bindingReady && !yes(frame, "caller_snapshot_confirmed"), "packet:rejected_mailbox_admission_retained");
            JsonNode lanes = object(packet.get("lanes"), LANES, "lanes");
            BigInteger requested = integer(inputs, "requested_full_character_id");
            boolean actualBound = scope.equals("actual_application_query") && bindingReady && yes(inputs, "caller_before_after_confirmed")
                    && yes(inputs, "repeated_raw_match") && yes(inputs, "mailbox_before_accepted") && yes(inputs, "mailbox_after_accepted")
                    && nonzero(requested) && !requested.equals(new BigInteger("4294967295"))
                    && nonzero(integer(frame, "native_revision")) && nonzero(integer(frame, "proof_epoch")) && binding.completeFrame();
            var facts = DEFINITIONS.stream().map(definition -> laneFacts(definition, lanes.get(definition.name()), inputs, bindingReady, actualBound)).toList();
            return new FrontierDecoded(target, frame(frame, integer(inputs, "public_revision"), requested), CaptureScope.from(scope),
                    bindingReady, actualBound, new Lanes(facts.get(0), facts.get(1), facts.get(2), facts.get(3)), copy(packet));
        } catch (Invalid invalid) {
            var empty = emptyLane(); return new FrontierInvalid(invalid.getMessage(), new Lanes(empty, empty, empty, empty));
        }
    }
    private static JsonNode frameNode(JsonNode raw, String path) {
        JsonNode frame = object(raw, FRAME, path);
        require(text(frame, "executable_sha256").equals(EXE) && text(frame, "caller_domain").equals("stock_perk_legality_12004"), path + ":actual4_admission_invalid");
        require(!zero(nullableInteger(frame, "frame_identity")) && !zero(nullableInteger(frame, "query_sequence")), path + ":missing_numeric_carrier_must_be_null"); return frame;
    }
    private static boolean bounded(JsonNode inputs, BigInteger address, int width) {
        BigInteger size = nullableInteger(inputs, "module_image_size"), base = integer(inputs.get("read_frame"), "module_base");
        if (size == null || size.signum() <= 0 || address == null || address.compareTo(base) < 0) return false;
        BigInteger delta = address.subtract(base); return delta.compareTo(size) < 0 && BigInteger.valueOf(width).compareTo(size.subtract(delta)) <= 0;
    }
    private static boolean inputBound(JsonNode inputs) {
        JsonNode frame = inputs.get("read_frame"); BigInteger perk = integer(inputs, "selected_perk_identity");
        return nonzero(integer(frame, "module_base")) && yes(frame, "caller_snapshot_confirmed")
                && (!isNull(frame, "frame_identity") || !text(frame, "snapshot_identity").isEmpty())
                && !isNull(frame, "query_sequence") && !text(inputs, "target_key").isEmpty()
                && nonzero(integer(inputs, "command_identity")) && perk.signum() > 0 && perk.compareTo(U64_MAX.subtract(BigInteger.valueOf(0x80))) <= 0
                && equal(nullableInteger(inputs, "receiver_identity"), perk.add(BigInteger.valueOf(0x80)))
                && bounded(inputs, nullableInteger(inputs, "vtable_identity"), 0xD0);
    }
    private static JsonNode target(JsonNode raw, JsonNode inputs, String path) {
        JsonNode target = object(raw, TARGET, path);
        require(!yes(target, "copied") || !isNull(target, "target_identity"), path + ":copied_target_missing");
        BigInteger rva = nullableInteger(target, "target_rva"), address = nullableInteger(target, "target_identity");
        if (rva != null) require(bounded(inputs, address, 1) && rva.equals(address.subtract(integer(inputs.get("read_frame"), "module_base"))), path + ":bounded_target_rva_mismatch");
        return target;
    }
    private static JsonNode descriptorTarget(JsonNode inputs) {
        JsonNode descriptor = inputs.get("descriptor_provider");
        ObjectNode empty = StrictJson.object();
        empty.putNull("slot_identity"); empty.putNull("target_identity"); empty.putNull("target_rva"); empty.put("copied", false);
        empty.put("unavailable_reason", "lifestyle_descriptor_source_kind_association_unavailable");
        if (descriptor.isNull()) return empty;
        BigInteger selected = nullableInteger(descriptor, "selected_descriptor_identity");
        if (!same(descriptor.get("read_frame"), inputs.get("read_frame")) || isNull(inputs, "source_context_root_word")
                || !equal(nullableInteger(descriptor, "caller_root_kind_raw_u16"), nullableInteger(inputs, "source_context_root_word"))
                || selected == null || selected.compareTo(U64_MAX.subtract(BigInteger.valueOf(0x10))) > 0) {
            empty.put("unavailable_reason", "lifestyle_descriptor_same_query_selection_unavailable"); return empty;
        }
        BigInteger address = nullableInteger(descriptor, "descriptor_validator_pointer10"); empty.put("slot_identity", selected.add(BigInteger.valueOf(0x10)));
        if (address != null) empty.put("target_identity", address);
        if (bounded(inputs, address, 1)) empty.put("target_rva", address.subtract(integer(inputs.get("read_frame"), "module_base")));
        empty.put("copied", yes(descriptor, "descriptor_validator_pointer_copied")); empty.put("unavailable_reason", text(descriptor, "unavailable_reason")); return empty;
    }
    private static boolean orderedEvents(JsonNode left, JsonNode right) {
        BigInteger thread = nullableInteger(left, "thread_id");
        return nonzero(integer(left, "clock_identity")) && integer(left, "clock_identity").equals(integer(right, "clock_identity"))
                && nonzero(thread) && equal(thread, nullableInteger(right, "thread_id")) && integer(left, "sequence").signum() > 0
                && integer(left, "sequence").compareTo(integer(right, "sequence")) < 0;
    }
    private static LaneFacts laneFacts(Definition definition, JsonNode raw, JsonNode inputs, boolean bindingReady, boolean actualBound) {
        try {
            JsonNode lane = object(raw, LANE, "lanes." + definition.name());
            require(text(lane, "lane").equals(definition.name()) && integer(lane, "call_rva").equals(BigInteger.valueOf(definition.call()))
                    && integer(lane, "return_rva").equals(BigInteger.valueOf(definition.returned())), "lane:literal_call_return_mismatch");
            JsonNode target = target(lane.get("target"), inputs, "lane.target");
            JsonNode expected = definition.slot().isPresent() ? target(inputs.get("slots").get(definition.slot().orElseThrow()), inputs, "lane.input_target") : descriptorTarget(inputs);
            if (definition.slot().isPresent() && !isNull(expected, "slot_identity")) {
                BigInteger vtable = nullableInteger(inputs, "vtable_identity"), offset = BigInteger.valueOf(definition.offset());
                require(nonzero(vtable) && vtable.compareTo(U64_MAX.subtract(offset)) <= 0
                        && integer(expected, "slot_identity").equals(vtable.add(offset)), "lane:slot_storage_mismatch");
            }
            if (bindingReady) require(same(target, expected), "lane:current_input_target_mismatch");
            else if (definition.slot().isPresent()) require(same(target, expected), "lane:copied_slot_target_mismatch");
            boolean rawReady = yes(lane, "raw_target_ready");
            if (rawReady) require(bindingReady && inputBound(inputs) && yes(target, "copied")
                    && bounded(inputs, nullableInteger(target, "target_identity"), 1) && !isNull(target, "target_rva"), "lane:raw_target_binding_unavailable");
            JsonNode proof = lane.get("closed_target_proof"), witness = lane.get("natural_witness");
            if (!proof.isNull()) object(proof, PROOF, "lane.closed_target_proof");
            if (!witness.isNull()) {
                object(witness, WITNESS, "lane.natural_witness"); frameNode(witness.get("read_frame"), "lane.natural_witness.read_frame");
                for (String event : List.of("query_cursor", "call_event", "return_event")) object(witness.get(event), EVENT, "lane.natural_witness." + event);
            }
            String source = text(lane, "result_source");
            require(Set.of("unavailable", "closed_pure_target_source", "natural_original_once").contains(source), "lane:result_source_not_admitted");
            if (!yes(lane, "source_value_ready")) {
                for (String output : OUTPUTS) require(isNull(lane, output), "lane:unqualified_returned_output");
                require(source.equals("unavailable"), "lane:unqualified_returned_output");
                return new LaneFacts(Optional.of(Status.DECODED), rawReady, false, Outputs.unknown(), Optional.empty(),
                        Optional.of(text(lane, "unavailable_reason")), actualBound && rawReady, false);
            }
            require(rawReady && bindingReady, "lane:output_without_current_raw_binding");
            for (String output : OUTPUTS) require(definition.demanded().contains(output) != isNull(lane, output), "lane:returned_width_mismatch");
            if (source.equals("closed_pure_target_source")) {
                require(!proof.isNull() && yes(proof, "complete_pure_readonly_body") && equal(nullableInteger(proof, "target_rva"), nullableInteger(target, "target_rva"))
                        && !text(proof, "producer_key").isEmpty() && text(proof, "exact_source_sha256").matches("[0-9a-f]{64}"), "lane:exact_pure_target_proof_unavailable");
            } else {
                require(source.equals("natural_original_once") && !witness.isNull(), "lane:original_once_witness_unavailable");
                require(same(witness.get("read_frame"), inputs.get("read_frame"))
                        && integer(witness, "selected_perk_identity").equals(integer(inputs, "selected_perk_identity"))
                        && equal(nullableInteger(witness, "receiver_identity"), nullableInteger(inputs, "receiver_identity"))
                        && equal(nullableInteger(witness, "target_identity"), nullableInteger(target, "target_identity"))
                        && integer(witness, "call_rva").equals(BigInteger.valueOf(definition.call())) && integer(witness, "return_rva").equals(BigInteger.valueOf(definition.returned()))
                        && integer(witness, "original_matching_call_count").equals(BigInteger.ONE) && yes(witness, "original_call_observed") && yes(witness, "original_return_observed")
                        && orderedEvents(witness.get("query_cursor"), witness.get("call_event")) && orderedEvents(witness.get("call_event"), witness.get("return_event")),
                        "lane:original_once_frame_target_event_or_return_mismatch");
                for (String output : OUTPUTS) require(equal(nullableInteger(witness, output), nullableInteger(lane, output)), "lane:original_once_frame_target_event_or_return_mismatch");
                if (definition.slot().isPresent()) require(equal(nullableInteger(witness, "original_rcx"), nullableInteger(inputs, "receiver_identity")), "lane:original_receiver_mismatch");
                if (definition.name().equals("root_mask_qwords")) require(nonzero(integer(witness, "original_rdx")), "lane:original_mask_buffer_unavailable");
                if (definition.name().equals("descriptor_al")) {
                    JsonNode provider = inputs.get("descriptor_provider");
                    require(!provider.isNull() && nonzero(integer(witness, "original_rcx"))
                            && equal(nullableInteger(witness, "original_rdx"), nullableInteger(provider, "selected_descriptor_identity"))
                            && equal(nullableInteger(witness, "original_root_word"), nullableInteger(inputs, "source_context_root_word"))
                            && equal(nullableInteger(witness, "original_full_id_payload"), nullableInteger(inputs, "source_context_full_id_payload")), "lane:original_descriptor_scope_mismatch");
                }
                if (definition.name().equals("final_c8_al"))
                    require(nonzero(integer(witness, "original_rdx")) && equal(nullableInteger(witness, "original_root_word"), BigInteger.valueOf(4))
                            && equal(nullableInteger(witness, "original_full_id_payload"), nullableInteger(inputs, "selected_character_full_id")), "lane:original_c8_scope_unavailable");
            }
            return new LaneFacts(Optional.of(Status.DECODED), true, true, outputs(lane), Optional.of(ResultSource.from(source)),
                    Optional.of(text(lane, "unavailable_reason")), actualBound, actualBound);
        } catch (Invalid invalid) {
            return new LaneFacts(Optional.of(Status.INVALID), false, false, Outputs.unknown(), Optional.empty(), Optional.of(invalid.getMessage()), false, false);
        }
    }
    private static Outputs outputs(JsonNode lane) {
        BigInteger u8 = nullableInteger(lane, "returned_raw_u8"), u16 = nullableInteger(lane, "returned_raw_u16");
        return new Outputs(u8 == null ? Optional.empty() : Optional.of(u8.intValueExact()), u16 == null ? Optional.empty() : Optional.of(u16.intValueExact()),
                Optional.ofNullable(nullableInteger(lane, "returned_qword0")), Optional.ofNullable(nullableInteger(lane, "returned_qword1")));
    }
    private static LaneFacts emptyLane() { return new LaneFacts(Optional.empty(), false, false, Outputs.unknown(), Optional.empty(), Optional.empty(), false, false); }
    private static ObjectNode laneNode(LaneFacts lane) {
        ObjectNode result = StrictJson.object(); lane.status().ifPresent(status -> result.put("status", status.wire()));
        result.put("raw_target_ready", lane.rawTargetReady()); result.put("source_value_ready", lane.sourceValueReady()); putOutputs(result, lane.outputs());
        lane.resultSource().ifPresent(source -> result.put("result_source", source.wire())); lane.unavailableReason().ifPresent(reason -> result.put("unavailable_reason", reason));
        result.put("actual_target_source_claim_ready", lane.actualTargetSourceClaimReady()); result.put("actual_source_value_ready", lane.actualSourceValueReady()); return result;
    }
    public static ObjectNode factsNode(FrontierResult result) {
        java.util.Objects.requireNonNull(result);
        ObjectNode facts = result instanceof FrontierDecoded decoded ? decimalFacts(raw(decoded.original())) : StrictJson.object();
        if (result instanceof FrontierAbsent) { facts.put("status", "absent"); return facts; }
        Lanes lanes;
        if (result instanceof FrontierInvalid invalid) {
            facts.put("status", "invalid"); facts.put("unavailable_reason", invalid.reason()); facts.put("actual_application_response_bound", false); lanes = invalid.lanes();
        } else {
            FrontierDecoded decoded = (FrontierDecoded) result;
            facts.put("status", "decoded"); facts.put("actual_application_response_bound", decoded.actualApplicationResponseBound()); lanes = decoded.lanes();
        }
        facts.put("whole_parent_legality_decoded", false); ObjectNode encodedLanes = facts.putObject("lane_facts");
        encodedLanes.set("descriptor_al", laneNode(lanes.descriptorAl())); encodedLanes.set("root_kind_ax", laneNode(lanes.rootKindAx()));
        encodedLanes.set("root_mask_qwords", laneNode(lanes.rootMaskQwords())); encodedLanes.set("final_c8_al", laneNode(lanes.finalC8Al())); return facts;
    }
    /** Recompute every output plane from the exact retained original and the same caller bindings. */
    public static FrontierResult verifyFacts(JsonNode facts, JsonNode originalPacket, Binding binding) {
        FrontierResult decoded = decode(originalPacket, binding);
        require(facts != null && same(facts, factsNode(decoded)), "facts:frontier_original_projection_mismatch");
        return decoded;
    }
    public static byte[] encodeFacts(FrontierResult result) { return bytes(factsNode(result)); }
}
