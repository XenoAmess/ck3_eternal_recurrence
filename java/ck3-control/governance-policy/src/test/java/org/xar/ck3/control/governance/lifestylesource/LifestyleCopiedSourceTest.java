package org.xar.ck3.control.governance.lifestylesource;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.lifestylesource.LifestyleSourceFacts.*;

/** Labeled software copied packets exercise the full normalizers. No native query or game qualification. */
final class LifestyleCopiedSourceTest {
    private static final BigInteger BASE = new BigInteger("9223372036854780000"), PLAYER = BigInteger.valueOf(29829);
    private static final Binding BINDING = Binding.exact("native:23", BigInteger.valueOf(23), 100, PLAYER, Optional.of("cutting_corners_perk"));
    private static ObjectNode object() { return StrictJson.object(); }
    private static ObjectNode child(ObjectNode parent, String name) { return (ObjectNode) parent.get(name); }
    private static ObjectNode predicate() {
        ObjectNode packet = object(); packet.put("schema", LifestylePredicateSourceCodec.SCHEMA); packet.put("read_only", true);
        packet.put("target_key", "cutting_corners_perk"); ObjectNode frame = packet.putObject("read_frame");
        frame.put("executable_sha256", LifestyleSourceSupport.EXE); frame.put("module_base", BASE); frame.put("snapshot_identity", "native:23");
        frame.putNull("frame_identity"); frame.put("query_sequence", 71); frame.put("mailbox_before_accepted", true); frame.put("mailbox_after_accepted", true);
        frame.put("module_image_size", 65536); frame.put("module_time_date_stamp", 123); frame.put("public_revision", 11); frame.put("native_revision", 23);
        frame.put("proof_epoch", 37); frame.put("date_raw", 100); frame.put("played_character_id", PLAYER);
        frame.put("caller_domain", "stock_perk_legality_12004"); frame.put("caller_snapshot_confirmed", true);
        packet.putNull("current_thread_tls_array_identity"); ObjectNode inputs = packet.putObject("inputs");
        for (String field : List.of("registry_identity", "requested_full_character_id_u32", "registry_capacity_u32", "indexed_character_identity",
                "indexed_character_full_id_u32", "used_fallback", "selected_character_identity", "selected_character_magic_u32",
                "selected_character_full_id_u32", "selected_character_field_1d0_u64", "selected_perk_identity", "selected_perk_magic_u32", "prefix_admitted")) inputs.putNull(field);
        inputs.put("command_identity", BASE.add(BigInteger.ONE)); inputs.put("registry_identity", 0); inputs.put("used_fallback", true);
        inputs.put("selected_character_identity", BASE.add(BigInteger.TWO)); inputs.put("selected_character_magic_u32", 0);
        inputs.put("prefix_admitted", false); inputs.put("unavailable_reason", "");
        packet.putNull("tail"); packet.putNull("truth_trace"); packet.put("value", false); packet.put("unavailable_reason", "");
        packet.put("native_can_select_before", false); packet.put("native_can_select_after", false); packet.put("repeated_source_match", true); return packet;
    }
    private static ObjectNode admittedPredicate(boolean value) {
        ObjectNode packet = predicate(), inputs = child(packet, "inputs");
        inputs.put("selected_character_magic_u32", 0x43686172); inputs.put("selected_character_full_id_u32", PLAYER);
        inputs.put("selected_character_field_1d0_u64", 0); inputs.put("selected_perk_identity", BASE.add(BigInteger.valueOf(0x7000)));
        inputs.put("selected_perk_magic_u32", 0x4744624F); inputs.put("prefix_admitted", true);
        ObjectNode tail = packet.putObject("tail"); tail.put("value", value); tail.put("unavailable_reason", "");
        ObjectNode trace = packet.putObject("truth_trace"); trace.put("selected_perk_identity", BASE.add(BigInteger.valueOf(0x7000)));
        trace.put("compiled_trigger_receiver_identity", BASE.add(BigInteger.valueOf(0x7080))); trace.put("context_root_word", 4); trace.put("context_full_id_payload", PLAYER);
        trace.put("evaluation_flag_raw_u8", 0); trace.put("source_projected_returned_raw_u8", value ? 1 : 0);
        for (String field : List.of("trigger_vtable_raw", "root_kind_getter_slot58_raw", "root_mask_getter_slot60_raw", "final_evaluator_slotc8_raw")) {
            if (value) trace.put(field, BASE.add(BigInteger.valueOf(0x1000))); else trace.putNull(field);
        }
        trace.put("value", value); trace.put("context_projection_available", true); trace.put("copied_frame_ready", true);
        trace.put("input_leaf_ready", value); trace.put("child_source_value_ready", true); trace.put("native_callback_executed", false);
        trace.put("actual_trigger_evaluation_observed", false); trace.put("unavailable_reason", ""); packet.put("value", value); return packet;
    }
    private static ObjectNode frontier() {
        ObjectNode packet = object(); packet.put("schema", LifestyleTriggerFrontierCodec.SCHEMA); packet.put("read_only", true); packet.put("copied_input_binding_ready", true);
        ObjectNode inputs = packet.putObject("inputs"), frame = inputs.putObject("read_frame");
        frame.put("executable_sha256", LifestyleSourceSupport.EXE); frame.put("module_base", BASE); frame.putNull("frame_identity"); frame.put("snapshot_identity", "native:23");
        frame.put("native_revision", 23); frame.put("query_sequence", 71); frame.put("proof_epoch", 37); frame.put("date_raw", 100);
        frame.put("caller_domain", "stock_perk_legality_12004"); frame.put("caller_snapshot_confirmed", true);
        inputs.put("module_image_size", 65536); inputs.put("module_time_date_stamp", 123); inputs.put("public_revision", 11);
        inputs.put("mailbox_before_accepted", true); inputs.put("mailbox_after_accepted", true); inputs.put("target_key", "cutting_corners_perk");
        inputs.put("capture_scope", "owned_memory_fixture"); inputs.put("command_identity", BASE.add(BigInteger.ONE)); inputs.put("selected_perk_identity", BASE.add(BigInteger.valueOf(0x7000)));
        inputs.put("requested_full_character_id", PLAYER); inputs.put("selected_character_identity", BASE.add(BigInteger.valueOf(0x8000)));
        inputs.put("selected_character_full_id", PLAYER); inputs.put("receiver_identity", BASE.add(BigInteger.valueOf(0x7080)));
        inputs.put("vtable_identity", BASE.add(BigInteger.valueOf(0x5000))); inputs.put("vtable_rva", 0x5000);
        ObjectNode slots = inputs.putObject("slots"); slots.set("slot58", target(0x58, 0x1000)); slots.set("slot60", target(0x60, 0x2000)); slots.set("slotc8", target(0xC8, 0x3000));
        inputs.putNull("source_context_root_word"); inputs.putNull("source_context_full_id_payload"); inputs.put("context_is_source_projection", false); inputs.putNull("descriptor_provider");
        inputs.put("caller_before_after_confirmed", true); inputs.put("repeated_raw_match", true); inputs.put("native_before", false); inputs.put("native_after", false); inputs.put("unavailable_reason", "");
        ObjectNode lanes = packet.putObject("lanes");
        ObjectNode emptyTarget = object(); emptyTarget.putNull("slot_identity"); emptyTarget.putNull("target_identity"); emptyTarget.putNull("target_rva");
        emptyTarget.put("copied", false); emptyTarget.put("unavailable_reason", "lifestyle_descriptor_source_kind_association_unavailable");
        lanes.set("descriptor_al", lane("descriptor_al", 0x372E0AE, 0x372E0B0, emptyTarget, false));
        lanes.set("root_kind_ax", lane("root_kind_ax", 0x372B4D3, 0x372B4D6, slots.get("slot58"), true));
        lanes.set("root_mask_qwords", lane("root_mask_qwords", 0x372B4EE, 0x372B4F1, slots.get("slot60"), true));
        lanes.set("final_c8_al", lane("final_c8_al", 0x372E34D, 0x372E353, slots.get("slotc8"), true)); return packet;
    }
    private static ObjectNode target(long slot, long rva) {
        ObjectNode target = object(); target.put("slot_identity", BASE.add(BigInteger.valueOf(0x5000 + slot)));
        target.put("target_identity", BASE.add(BigInteger.valueOf(rva))); target.put("target_rva", rva); target.put("copied", true); target.put("unavailable_reason", ""); return target;
    }
    private static ObjectNode lane(String name, long call, long returned, JsonNode target, boolean rawReady) {
        ObjectNode lane = object(); lane.put("lane", name); lane.put("call_rva", call); lane.put("return_rva", returned); lane.set("target", target.deepCopy());
        lane.put("raw_target_ready", rawReady); lane.put("source_value_ready", false);
        for (String field : List.of("returned_raw_u8", "returned_raw_u16", "returned_qword0", "returned_qword1")) lane.putNull(field);
        lane.put("result_source", "unavailable"); lane.putNull("closed_target_proof"); lane.putNull("natural_witness"); lane.put("unavailable_reason", "copied_source_output_unknown"); return lane;
    }
    private static ObjectNode event(int sequence) {
        ObjectNode event = object(); event.put("clock_identity", BASE); event.put("sequence", sequence); event.put("thread_id", 7); return event;
    }
    private static ObjectNode naturalRootKind(ObjectNode packet) {
        ObjectNode inputs = child(packet, "inputs"), lane = child(child(packet, "lanes"), "root_kind_ax");
        lane.put("source_value_ready", true); lane.put("returned_raw_u16", 0); lane.put("result_source", "natural_original_once");
        ObjectNode witness = lane.putObject("natural_witness"); witness.set("read_frame", inputs.get("read_frame").deepCopy());
        witness.set("query_cursor", event(1)); witness.set("call_event", event(2)); witness.set("return_event", event(3));
        witness.put("call_rva", 0x372B4D3); witness.put("return_rva", 0x372B4D6);
        witness.set("selected_perk_identity", inputs.get("selected_perk_identity").deepCopy()); witness.set("receiver_identity", inputs.get("receiver_identity").deepCopy());
        witness.put("target_identity", BASE.add(BigInteger.valueOf(0x1000))); witness.set("original_rcx", inputs.get("receiver_identity").deepCopy());
        witness.put("original_rdx", 0); witness.putNull("original_root_word"); witness.putNull("original_full_id_payload");
        witness.putNull("returned_raw_u8"); witness.put("returned_raw_u16", 0); witness.putNull("returned_qword0"); witness.putNull("returned_qword1");
        witness.put("original_matching_call_count", 1); witness.put("original_call_observed", true); witness.put("original_return_observed", true); return lane;
    }
    private static FrontierDecoded decoded(ObjectNode packet) { return assertInstanceOf(FrontierDecoded.class, LifestyleTriggerFrontierCodec.decode(packet, BINDING)); }
    @Test void absentAndExplicitNullHaveDistinctTypedPresenceAndNeitherProducesParentCredit() {
        assertEquals(Presence.MISSING, assertInstanceOf(PredicateAbsent.class, LifestylePredicateSourceCodec.decode(null, BINDING)).presence());
        assertEquals(Presence.NULL, assertInstanceOf(PredicateAbsent.class, LifestylePredicateSourceCodec.decode(com.fasterxml.jackson.databind.node.NullNode.getInstance(), BINDING)).presence());
        assertEquals(Presence.MISSING, assertInstanceOf(FrontierAbsent.class, LifestyleTriggerFrontierCodec.decode(null, BINDING)).presence());
        assertEquals(Presence.NULL, assertInstanceOf(FrontierAbsent.class, LifestyleTriggerFrontierCodec.decode(com.fasterxml.jackson.databind.node.NullNode.getInstance(), BINDING)).presence());
        assertEquals("absent", LifestyleTriggerFrontierCodec.factsNode(new FrontierAbsent(Presence.NULL)).get("status").textValue());
    }
    @Test void prefixPartialUnknownFalseAndMailboxInvalidationKeepTheirIndependentRawPlanes() {
        ObjectNode packet = predicate(); PredicateDecoded known = assertInstanceOf(PredicateDecoded.class, LifestylePredicateSourceCodec.decode(packet, BINDING));
        assertEquals(Truth.KNOWN_FALSE, known.value()); assertFalse(known.wholeParentLegalityDecoded());
        ObjectNode inputs = child(packet, "inputs");
        inputs.fieldNames().forEachRemaining(name -> { if (!name.equals("command_identity") && !name.equals("unavailable_reason")) inputs.putNull(name); });
        inputs.put("unavailable_reason", "lifestyle_perk_character_registry_unavailable"); packet.putNull("value"); packet.put("unavailable_reason", "lifestyle_perk_character_registry_unavailable");
        assertEquals(Truth.UNKNOWN, assertInstanceOf(PredicateDecoded.class, LifestylePredicateSourceCodec.decode(packet, BINDING)).value());
        inputs.put("selected_character_full_id_u32", PLAYER);
        assertInstanceOf(PredicateInvalid.class, LifestylePredicateSourceCodec.decode(packet, BINDING));
        packet = predicate(); child(packet, "read_frame").put("mailbox_after_accepted", false); child(packet, "read_frame").put("caller_snapshot_confirmed", false);
        packet.putNull("value"); packet.put("unavailable_reason", "formal_mailbox_after_guard_rejected");
        PredicateDecoded rejected = assertInstanceOf(PredicateDecoded.class, LifestylePredicateSourceCodec.decode(packet, BINDING));
        assertEquals(Truth.UNKNOWN, rejected.value()); assertEquals(Truth.KNOWN_FALSE, rejected.prefixValue());
        assertFalse(LifestylePredicateSourceCodec.factsNode(rejected).get("native_can_select_after").booleanValue());
    }
    @Test void traceReturnedByteAndCompleteReachedPathAreRequiredWithoutNativeCallbackPromotion() {
        assertEquals(Truth.KNOWN_FALSE, assertInstanceOf(PredicateDecoded.class, LifestylePredicateSourceCodec.decode(admittedPredicate(false), BINDING)).value());
        ObjectNode packet = admittedPredicate(true);
        assertEquals(Truth.KNOWN_TRUE, assertInstanceOf(PredicateDecoded.class, LifestylePredicateSourceCodec.decode(packet, BINDING)).value());
        child(packet, "truth_trace").putNull("final_evaluator_slotc8_raw"); assertInstanceOf(PredicateInvalid.class, LifestylePredicateSourceCodec.decode(packet, BINDING));
        packet = admittedPredicate(false); child(packet, "truth_trace").put("actual_trigger_evaluation_observed", true);
        assertInstanceOf(PredicateInvalid.class, LifestylePredicateSourceCodec.decode(packet, BINDING));
    }
    @Test void exactSchemaSourceNativeFrameGenerationAndStrictNumericTypesAreComparedWithoutRepair() {
        ObjectNode packet = predicate(); child(packet, "read_frame").put("executable_sha256", "f".repeat(64));
        assertInstanceOf(PredicateInvalid.class, LifestylePredicateSourceCodec.decode(packet, BINDING));
        packet = predicate(); child(packet, "read_frame").put("native_revision", true); assertInstanceOf(PredicateInvalid.class, LifestylePredicateSourceCodec.decode(packet, BINDING));
        packet = predicate(); child(packet, "inputs").put("command_identity", 1.5); assertInstanceOf(PredicateInvalid.class, LifestylePredicateSourceCodec.decode(packet, BINDING));
        packet = predicate(); child(packet, "read_frame").remove("frame_identity"); assertInstanceOf(PredicateInvalid.class, LifestylePredicateSourceCodec.decode(packet, BINDING));
        assertInstanceOf(PredicateInvalid.class, LifestylePredicateSourceCodec.decode(predicate(), Binding.exact("public:11", BigInteger.valueOf(23), 100, PLAYER, Optional.empty())));
        assertInstanceOf(FrontierInvalid.class, LifestyleTriggerFrontierCodec.decode(frontier(), Binding.exact("native:23", BigInteger.valueOf(23), 100, PLAYER.add(BigInteger.ONE.shiftLeft(24)), Optional.empty())));
    }
    @Test void copiedSlotsAndFourOutputPlanesRemainIndependentAndOwnedFixtureIsNotActualResponse() {
        FrontierDecoded result = decoded(frontier());
        assertEquals(CaptureScope.OWNED_MEMORY_FIXTURE, result.captureScope()); assertFalse(result.actualApplicationResponseBound());
        assertFalse(result.wholeParentLegalityDecoded()); assertEquals(3, result.lanes().all().stream().filter(LaneFacts::rawTargetReady).count());
        assertTrue(result.lanes().all().stream().allMatch(lane -> lane.status().orElseThrow() == Status.DECODED && !lane.sourceValueReady() && lane.outputs().empty() && !lane.actualSourceValueReady()));
        ObjectNode packet = frontier(); child(child(child(packet, "inputs"), "slots"), "slot60").put("target_rva", 8193);
        result = decoded(packet); assertEquals(Status.INVALID, result.lanes().rootMaskQwords().status().orElseThrow());
        assertEquals(Status.DECODED, result.lanes().rootKindAx().status().orElseThrow()); assertEquals(Status.DECODED, result.lanes().finalC8Al().status().orElseThrow());
    }
    @Test void rawSlotsUnqualifiedZeroWrongWidthsAndCallsitesNeverBecomeReturnedValues() {
        for (String mutation : List.of("zero", "bool", "float", "width", "call")) {
            ObjectNode packet = frontier(), lane = child(child(packet, "lanes"), "root_kind_ax");
            switch (mutation) {
                case "zero" -> lane.put("returned_raw_u16", 0);
                case "bool" -> lane.put("returned_raw_u16", false);
                case "float" -> lane.put("returned_raw_u16", 0.5);
                case "width" -> lane.put("returned_raw_u16", 65536);
                case "call" -> lane.put("call_rva", 0x372B4D4);
                default -> fail("unreachable fixture mutation");
            }
            FrontierDecoded result = decoded(packet);
            assertEquals(Status.INVALID, result.lanes().rootKindAx().status().orElseThrow(), mutation);
            assertTrue(result.lanes().rootKindAx().outputs().empty()); assertFalse(result.lanes().rootKindAx().sourceValueReady());
            assertEquals(Status.DECODED, result.lanes().rootMaskQwords().status().orElseThrow());
            assertDoesNotThrow(() -> LifestyleTriggerFrontierCodec.encodeFacts(result));
        }
    }
    @Test void exactClosedBodyProofAndNaturalOnceWitnessQualifyOnlyTheirOwnReturnedWidth() {
        ObjectNode packet = frontier(), lane = child(child(packet, "lanes"), "root_kind_ax");
        lane.put("source_value_ready", true); lane.put("returned_raw_u16", 0); lane.put("result_source", "closed_pure_target_source");
        assertEquals(Status.INVALID, decoded(packet).lanes().rootKindAx().status().orElseThrow());
        ObjectNode proof = lane.putObject("closed_target_proof"); proof.put("target_rva", 0x1000); proof.put("exact_source_sha256", "f".repeat(64));
        proof.put("producer_key", "labeled-software-proof"); proof.put("complete_pure_readonly_body", true);
        FrontierDecoded result = decoded(packet); assertTrue(result.lanes().rootKindAx().sourceValueReady());
        assertEquals(Optional.of(0), result.lanes().rootKindAx().outputs().rawU16()); assertFalse(result.lanes().rootKindAx().actualSourceValueReady());
        packet = frontier(); naturalRootKind(packet); result = decoded(packet); assertTrue(result.lanes().rootKindAx().sourceValueReady());
        child(child(child(packet, "lanes"), "root_kind_ax"), "natural_witness").put("original_matching_call_count", 2);
        assertEquals(Status.INVALID, decoded(packet).lanes().rootKindAx().status().orElseThrow());
        packet = frontier(); lane = naturalRootKind(packet); child(child(lane, "natural_witness"), "return_event").put("sequence", 2);
        assertEquals(Status.INVALID, decoded(packet).lanes().rootKindAx().status().orElseThrow());
    }
    @Test void mailboxRejectionRemovesAllReadinessCreditWithoutErasingCopiedTargets() {
        ObjectNode packet = frontier(); packet.put("copied_input_binding_ready", false); ObjectNode inputs = child(packet, "inputs");
        child(inputs, "read_frame").put("caller_snapshot_confirmed", false); inputs.put("mailbox_after_accepted", false);
        for (JsonNode lane : packet.get("lanes")) { ((ObjectNode) lane).put("raw_target_ready", false); ((ObjectNode) lane).put("source_value_ready", false); }
        FrontierDecoded result = decoded(packet); assertTrue(result.lanes().all().stream().noneMatch(LaneFacts::rawTargetReady));
        assertEquals(BASE.add(BigInteger.valueOf(0x2000)), LifestyleSourceSupport.integer(child(child(inputs, "slots"), "slot60"), "target_identity"));
        inputs.put("capture_scope", "actual_application_query"); result = decoded(packet); assertFalse(result.actualApplicationResponseBound());
    }
    @Test void actualResponseCreditNeedsAllExistingCallerBindingsAndCannotPromoteAnotherLane() {
        ObjectNode packet = frontier(); child(packet, "inputs").put("capture_scope", "actual_application_query"); naturalRootKind(packet);
        FrontierDecoded result = decoded(packet); assertTrue(result.actualApplicationResponseBound()); assertTrue(result.lanes().rootKindAx().actualSourceValueReady());
        assertFalse(result.lanes().rootMaskQwords().actualSourceValueReady()); assertFalse(result.wholeParentLegalityDecoded());
        result = assertInstanceOf(FrontierDecoded.class, LifestyleTriggerFrontierCodec.decode(packet, Binding.unbound()));
        assertFalse(result.actualApplicationResponseBound()); assertFalse(result.lanes().rootKindAx().actualSourceValueReady());
    }
    @Test void descriptorProviderRequiresTheSameCopiedFrameKindSelectionAndOriginalCallScope() {
        ObjectNode packet = frontier(), inputs = child(packet, "inputs"), lane = child(child(packet, "lanes"), "descriptor_al");
        inputs.put("context_is_source_projection", true); inputs.put("source_context_root_word", 4); inputs.put("source_context_full_id_payload", PLAYER);
        ObjectNode provider = inputs.putObject("descriptor_provider"); provider.set("read_frame", inputs.get("read_frame").deepCopy());
        provider.put("caller_root_kind_raw_u16", 4); provider.put("table_identity", BASE.add(BigInteger.valueOf(0x9000)));
        provider.put("initialization_guard_raw_i32", 1); provider.put("table_data_identity", BASE.add(BigInteger.valueOf(0x9100)));
        provider.put("capacity_raw_i32", 8); provider.put("count_raw_i32", 5); provider.put("selected_source_fallback", false);
        provider.put("selected_descriptor_identity", BASE.add(BigInteger.valueOf(0x9200))); provider.put("descriptor_validator_pointer10", BASE.add(BigInteger.valueOf(0x4000)));
        provider.put("descriptor_selection_inputs_copied", true); provider.put("descriptor_validator_pointer_copied", true);
        provider.put("initializer_semantics_source_closed", true); provider.put("native_provider_return_observed", false); provider.put("unavailable_reason", "");
        ObjectNode target = child(lane, "target"); target.put("slot_identity", BASE.add(BigInteger.valueOf(0x9210)));
        target.put("target_identity", BASE.add(BigInteger.valueOf(0x4000))); target.put("target_rva", 0x4000); target.put("copied", true); target.put("unavailable_reason", "");
        lane.put("raw_target_ready", true); lane.put("source_value_ready", true); lane.put("returned_raw_u8", 0); lane.put("result_source", "natural_original_once");
        ObjectNode original = frontier(); ObjectNode rootKind = naturalRootKind(original);
        ObjectNode witness = child(rootKind, "natural_witness").deepCopy(); witness.set("read_frame", inputs.get("read_frame").deepCopy());
        witness.put("call_rva", 0x372E0AE); witness.put("return_rva", 0x372E0B0); witness.put("target_identity", BASE.add(BigInteger.valueOf(0x4000)));
        witness.put("original_rcx", BASE.add(BigInteger.valueOf(0x6000))); witness.put("original_rdx", BASE.add(BigInteger.valueOf(0x9200)));
        witness.put("original_root_word", 4); witness.put("original_full_id_payload", PLAYER); witness.putNull("returned_raw_u16"); witness.put("returned_raw_u8", 0);
        lane.set("natural_witness", witness);
        FrontierDecoded result = decoded(packet); assertTrue(result.lanes().descriptorAl().sourceValueReady()); assertEquals(Optional.of(0), result.lanes().descriptorAl().outputs().rawU8());
        witness.put("original_full_id_payload", PLAYER.add(BigInteger.ONE));
        result = decoded(packet); assertEquals(Status.INVALID, result.lanes().descriptorAl().status().orElseThrow());
        assertEquals(Status.DECODED, result.lanes().rootKindAx().status().orElseThrow());
        witness.put("original_full_id_payload", PLAYER); child(provider, "read_frame").put("snapshot_identity", "other-query");
        assertEquals(Status.INVALID, decoded(packet).lanes().descriptorAl().status().orElseThrow());
    }
    @Test void maskQwordsAndFinalAlKeepTheirOwnWidthsAndOriginalReceiverScope() {
        ObjectNode packet = frontier(), lane = child(child(packet, "lanes"), "root_mask_qwords");
        lane.put("source_value_ready", true); lane.put("returned_qword0", 0); lane.put("returned_qword1", LifestyleSourceSupport.U64_MAX);
        lane.put("result_source", "closed_pure_target_source"); ObjectNode proof = lane.putObject("closed_target_proof");
        proof.put("target_rva", 0x2000); proof.put("exact_source_sha256", "a".repeat(64)); proof.put("producer_key", "software-mask-proof"); proof.put("complete_pure_readonly_body", true);
        FrontierDecoded result = decoded(packet); assertTrue(result.lanes().rootMaskQwords().sourceValueReady());
        JsonNode facts = LifestyleTriggerFrontierCodec.factsNode(result); assertEquals("0", facts.get("lane_facts").get("root_mask_qwords").get("returned_qword0").textValue());
        assertEquals(LifestyleSourceSupport.U64_MAX.toString(), facts.get("lane_facts").get("root_mask_qwords").get("returned_qword1").textValue());
        lane.put("returned_raw_u16", 0); assertEquals(Status.INVALID, decoded(packet).lanes().rootMaskQwords().status().orElseThrow());
        packet = frontier(); ObjectNode original = frontier(), rootKind = naturalRootKind(original);
        lane = child(child(packet, "lanes"), "final_c8_al"); lane.put("source_value_ready", true); lane.put("returned_raw_u8", 1); lane.put("result_source", "natural_original_once");
        ObjectNode witness = child(rootKind, "natural_witness").deepCopy(); witness.put("call_rva", 0x372E34D); witness.put("return_rva", 0x372E353);
        witness.put("target_identity", BASE.add(BigInteger.valueOf(0x3000))); witness.put("original_rdx", BASE.add(BigInteger.valueOf(0x6000)));
        witness.put("original_root_word", 4); witness.put("original_full_id_payload", PLAYER); witness.putNull("returned_raw_u16"); witness.put("returned_raw_u8", 1);
        lane.set("natural_witness", witness); assertTrue(decoded(packet).lanes().finalC8Al().sourceValueReady());
        witness.put("original_rdx", 0); result = decoded(packet); assertEquals(Status.INVALID, result.lanes().finalC8Al().status().orElseThrow());
        assertEquals(Status.DECODED, result.lanes().rootMaskQwords().status().orElseThrow());
    }
    @Test void immutableCopiedPacketsRoundTripWithoutChangingNativeIntegersAndFactsUseDecimalU64Strings() {
        ObjectNode rawPredicate = admittedPredicate(false); PredicateDecoded predicate = assertInstanceOf(PredicateDecoded.class, LifestylePredicateSourceCodec.decode(rawPredicate, BINDING));
        byte[] before = predicate.original().canonicalNativeJson(); rawPredicate.put("value", true);
        assertArrayEquals(before, predicate.original().canonicalNativeJson());
        assertEquals(predicate, LifestylePredicateSourceCodec.decode(StrictJson.parse(before), BINDING));
        JsonNode encodedPredicate = StrictJson.parse(LifestylePredicateSourceCodec.encodeFacts(predicate));
        assertEquals(BASE.toString(), encodedPredicate.get("read_frame").get("module_base").textValue());
        assertEquals(predicate, LifestylePredicateSourceCodec.verifyFacts(encodedPredicate, StrictJson.parse(before), BINDING));
        assertTrue(StrictJson.parse(before).get("read_frame").get("module_base").isIntegralNumber());
        FrontierDecoded frontier = decoded(frontier()); JsonNode facts = StrictJson.parse(LifestyleTriggerFrontierCodec.encodeFacts(frontier));
        assertEquals(frontier, LifestyleTriggerFrontierCodec.decode(StrictJson.parse(frontier.original().canonicalNativeJson()), BINDING));
        assertEquals("23", facts.get("inputs").get("read_frame").get("native_revision").textValue());
        assertEquals("11", facts.get("inputs").get("public_revision").textValue());
        assertEquals(frontier, LifestyleTriggerFrontierCodec.verifyFacts(facts, StrictJson.parse(frontier.original().canonicalNativeJson()), BINDING));
        ObjectNode changedFacts = facts.deepCopy(); child(child(changedFacts, "inputs"), "read_frame").put("native_revision", 23);
        assertThrows(IllegalArgumentException.class, () -> LifestyleTriggerFrontierCodec.verifyFacts(changedFacts,
                StrictJson.parse(frontier.original().canonicalNativeJson()), BINDING));
        assertEquals(100, facts.get("inputs").get("read_frame").get("date_raw").intValue());
        assertFalse(facts.get("whole_parent_legality_decoded").booleanValue());
        byte[] exposed = frontier.original().canonicalNativeJson(); exposed[0] = 0; assertNotEquals(0, frontier.original().canonicalNativeJson()[0]);
    }
}
