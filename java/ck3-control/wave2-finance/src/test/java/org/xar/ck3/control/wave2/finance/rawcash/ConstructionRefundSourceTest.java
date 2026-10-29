package org.xar.ck3.control.wave2.finance.rawcash;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.HashSet;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanCodec;
import org.xar.ck3.control.wave2.finance.holyloan.LoanFinancingCodec.PlanningFrame;
import org.xar.ck3.control.wave2.finance.rawcash.ConstructionRefundSource.Candidate;
import org.xar.ck3.control.wave2.finance.rawcash.ConstructionRefundSource.Refused;
import org.xar.ck3.control.wave2.finance.rawcash.ConstructionRefundSource.Refusal;
import org.xar.ck3.control.wave2.finance.rawcash.ConstructionRefundSource.Unavailable;

class ConstructionRefundSourceTest {
    private static final BigInteger EPOCH = new BigInteger("18446744073709551614");
    private static final PlanningFrame FRAME = frame(17);
    private static PlanningFrame frame(int actor) {
        return new PlanningFrame("synthetic-public:19", BigInteger.valueOf(19), BigInteger.valueOf(7),
                BigInteger.valueOf(53288496), BigInteger.valueOf(actor), "synthetic-producer-episode",
                BigInteger.valueOf(500), BigInteger.valueOf(2));
    }

    /** Actual C++ Read+Serialize output is mandatory. Missing native environment must fail, never skip or synthesize a golden. */
    @Test void actualNativeProducerToJavaAndPersistenceForAllThirteenCases() throws Exception {
        ObjectNode golden = actualNativeProducerGolden();
        assertEquals("xar.construction-refund-native-producer-golden.v1", StrictJson.text(golden.get("schema")));
        assertTrue(golden.get("rows").isArray()); assertEquals(13, golden.get("rows").size()); Set<Integer> seen = new HashSet<>();
        for (JsonNode raw : golden.get("rows")) {
            ObjectNode row = StrictJson.object(raw, Set.of("scenario", "receipt", "result"));
            int scenario = (int) StrictJson.integer(row.get("scenario"), 0, 12); assertTrue(seen.add(scenario));
            assertEquals(row.get("receipt"), row.get("result").get("construction_refund_source_v1"));
            assertEquals("7", row.get("result").get("snapshot_revision").textValue());
            PlanningFrame expected = scenario == 10 ? frame(0) : FRAME;
            ConstructionRefundSource.Result decoded = ConstructionRefundSource.projectNative(StrictJson.canonical(row.get("receipt")), expected, EPOCH, 2);
            if (Set.of(0, 1, 2, 3, 10, 11).contains(scenario)) {
                Candidate copy = assertInstanceOf(Candidate.class, decoded);
                assertEquals(copy.receiver(), assertInstanceOf(Candidate.class,
                        ConstructionRefundSource.decode(copy.toJson(), expected, EPOCH, 2)).receiver());
                assertFalse(copy.finalCancelGateObserved()); assertFalse(copy.submissionQualified());
                assertFalse(copy.receivedFundsVerified()); assertEquals(0, copy.fundingCreditRaw());
                var assessment = copy.refundAssessment();
                assertEquals(copy.frame(), assessment.frame()); assertEquals(EPOCH, assessment.captureEpoch());
                assertEquals(copy.receiver(), assessment.receiver());
                assertEquals(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(copy.toJson())),
                        assessment.sourceCopySha256());
                assertSame(assessment, ConstructionRefundSource.decodeRefundAssessment(assessment.toJson(), copy));
                assertArrayEquals(assessment.toJson(), ConstructionRefundSource.decodeRefundAssessment(
                        assessment.toJson(), assertInstanceOf(Candidate.class,
                                ConstructionRefundSource.decode(copy.toJson(), expected, EPOCH, 2))).toJson());
                assertFalse(assessment.completeNetRefundQuote()); assertTrue(assessment.refundQuoteRaw().isEmpty());
                assertFalse(assessment.receivedFundsVerified()); assertFalse(assessment.submissionQualified());
                assertEquals(0, assessment.fundingCreditRaw());
                assertEquals(ConstructionRefundSource.FollowupContract.DEFINITION_EFFECT_AND_EVENT_MANAGER_HANDOFF_PATHS,
                        assessment.followupContract());
                assertEquals(scenario == 2 ? 0 : 10, assessment.storedInputs().size());
                if (scenario != 2) {
                    assertEquals(91, assessment.recordedBuilderCharacterId().orElseThrow());
                    assertEquals(15000000, assessment.storedInputs().get(0).storedRaw());
                    assertEquals(ConstructionRefundSource.ResourceDestination.CURRENT_COMMAND_ACTOR_GOLD,
                            assessment.storedInputs().get(0).destination());
                    assertEquals(ConstructionRefundSource.ResourceDestination.NO_HANDLER_IN_THIS_DISPATCH,
                            assessment.storedInputs().get(3).destination());
                    assertEquals(Long.MIN_VALUE, assessment.storedInputs().get(9).storedRaw());
                    for (int slot = 0; slot < 10; ++slot)
                        assertEquals(slot, assessment.storedInputs().get(slot).slot().nativeIndex());
                } else assertTrue(assessment.recordedBuilderCharacterId().isEmpty());
                assertEquals(scenario == 1 ? ConstructionRefundSource.RefundKnowledge.CURRENT_RECEIVER_COMPONENT_UNAVAILABLE
                        : scenario == 2 ? ConstructionRefundSource.RefundKnowledge.NO_ACTIVE_RECORD
                        : scenario == 3 ? ConstructionRefundSource.RefundKnowledge.COPIED_NATIVE_GATE_REFUSED
                        : ConstructionRefundSource.RefundKnowledge.DIRECT_VECTOR_COPIED_FULL_NET_REFUND_UNQUALIFIED,
                        assessment.knowledge());
                if (scenario == 1) { assertTrue(copy.receiver().componentPointer().isEmpty()); assertTrue(copy.receiver().currentGoldRaw().isEmpty()); }
                if (scenario == 2) { assertTrue(copy.activeRecord().isEmpty()); assertFalse(copy.copiedCancelGateAllows()); }
                if (scenario == 3) { assertFalse(copy.copiedCancelGateAllows()); }
                if (scenario == 10) { assertEquals(0, copy.receiver().characterId()); }
                if (scenario == 11) { assertEquals(0, copy.receiver().currentGoldRaw().orElseThrow()); }
                if (scenario != 2) {
                    var record = copy.activeRecord().orElseThrow();
                    assertEquals(91, record.recordedBuilderCharacterId()); assertNotEquals(record.recordedBuilderCharacterId(), copy.receiver().characterId());
                    assertEquals(Long.MIN_VALUE, record.recordedCostRawNative().get(9));
                    assertEquals("9007199254750752", record.recordPointer().decimal());
                    assertEquals(EPOCH, record.startWord());
                }
            } else {
                Unavailable unavailable = assertInstanceOf(Unavailable.class, decoded);
                assertEquals(unavailable.reason(), assertInstanceOf(Unavailable.class,
                        ConstructionRefundSource.decode(unavailable.toJson(), expected, EPOCH, 2)).reason());
            }
        }
        assertEquals(13, seen.size());
    }

    @Test void derivedRefundKnowledgeRejectsFundingConsumerAndSourceForgery() {
        Candidate copiedSource = assertInstanceOf(Candidate.class, project(nativeInput()));
        var assessment = copiedSource.refundAssessment();
        for (String field : Set.of("copied_receiver", "stored_resource_inputs", "planning_frame", "source_copy_sha256")) {
            ObjectNode omitted = (ObjectNode) StrictJson.parse(assessment.toJson()); omitted.remove(field);
            assertThrows(IllegalArgumentException.class, () -> ConstructionRefundSource.decodeRefundAssessment(StrictJson.canonical(omitted), copiedSource));
        }
        for (String field : Set.of("complete_net_refund_quote", "received_funds_verified", "submission_qualified")) {
            ObjectNode credited = (ObjectNode) StrictJson.parse(assessment.toJson()); credited.put(field, true);
            assertThrows(IllegalArgumentException.class, () -> ConstructionRefundSource.decodeRefundAssessment(StrictJson.canonical(credited), copiedSource));
        }
        ObjectNode claimed = (ObjectNode) StrictJson.parse(assessment.toJson());
        claimed.put("refund_quote_raw", 15000000).put("funding_credit_raw", 15000000);
        assertThrows(IllegalArgumentException.class, () -> ConstructionRefundSource.decodeRefundAssessment(StrictJson.canonical(claimed), copiedSource));
        ObjectNode wrongReceiver = (ObjectNode) StrictJson.parse(assessment.toJson());
        ((ObjectNode) wrongReceiver.get("copied_receiver")).put("character_id", 91);
        assertThrows(IllegalArgumentException.class, () -> ConstructionRefundSource.decodeRefundAssessment(StrictJson.canonical(wrongReceiver), copiedSource));
        ObjectNode wrongConsumer = (ObjectNode) StrictJson.parse(assessment.toJson());
        ((ObjectNode) wrongConsumer.get("stored_resource_inputs").get(0)).put("destination", "ACTOR_PRIMARY_TITLE_INDIRECT");
        assertThrows(IllegalArgumentException.class, () -> ConstructionRefundSource.decodeRefundAssessment(StrictJson.canonical(wrongConsumer), copiedSource));
        ObjectNode stringAmount = (ObjectNode) StrictJson.parse(assessment.toJson());
        ((ObjectNode) stringAmount.get("stored_resource_inputs").get(0)).put("stored_raw", "15000000");
        assertThrows(IllegalArgumentException.class, () -> ConstructionRefundSource.decodeRefundAssessment(StrictJson.canonical(stringAmount), copiedSource));
        ObjectNode differentWallet = nativeInput(); ((ObjectNode) differentWallet.get("receiver")).put("current_gold_raw", 999999);
        Candidate newCopy = assertInstanceOf(Candidate.class, project(differentWallet));
        assertThrows(IllegalArgumentException.class, () -> ConstructionRefundSource.decodeRefundAssessment(assessment.toJson(), newCopy));
    }

    @Test void strictTokenAndFieldFailuresNeverBecomeAQuoteOrFunds() {
        for (String key : new String[] {"read_only", "scope", "native_revision", "capture_epoch", "receiver", "active_record"}) {
            ObjectNode missing = nativeInput(); missing.remove(key);
            assertThrows(IllegalArgumentException.class, () -> project(missing));
        }
        for (String replacement : new String[] {"true", "1.0", "7", "\"07\"", "\"18446744073709551616\""}) {
            ObjectNode wrong = nativeInput(); wrong.set("native_revision", StrictJson.parse(replacement.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> project(wrong));
        }
        for (String key : new String[] {"final_action_gate_observed", "submission_qualified", "received_funds_verified"}) {
            ObjectNode forged = nativeInput(); forged.put(key, true); assertThrows(IllegalArgumentException.class, () -> project(forged));
        }
        ObjectNode extra = nativeInput(); extra.put("native_entry_rva", 0x310DB20L);
        assertThrows(IllegalArgumentException.class, () -> project(extra));
        ObjectNode funded = nativeInput(); funded.put("funding_credit_raw", 1);
        assertThrows(IllegalArgumentException.class, () -> project(funded));
    }

    @Test void actorNativeEpochProvinceAndPlanningFrameRemainDistinct() {
        ObjectNode revision = nativeInput(); revision.put("native_revision", "19");
        assertEquals(new Refused(Refusal.FRAME_DRIFT), project(revision));
        ObjectNode actor = nativeInput(); actor.put("actor_character_id", 91);
        assertEquals(new Refused(Refusal.FRAME_DRIFT), project(actor));
        assertEquals(new Refused(Refusal.FRAME_DRIFT), ConstructionRefundSource.projectNative(StrictJson.canonical(nativeInput()), FRAME, BigInteger.ONE, 2));
        assertEquals(new Refused(Refusal.FRAME_DRIFT), ConstructionRefundSource.projectNative(StrictJson.canonical(nativeInput()), FRAME, EPOCH, 3));
        Candidate candidate = assertInstanceOf(Candidate.class, project(nativeInput()));
        ObjectNode stored = (ObjectNode) StrictJson.parse(candidate.toJson()); ((ObjectNode) stored.get("planning_frame")).put("connection_generation", "3");
        assertEquals(new Refused(Refusal.FRAME_DRIFT), ConstructionRefundSource.decode(StrictJson.canonical(stored), FRAME, EPOCH, 2));
        ObjectNode receiver = nativeInput(); ((ObjectNode) receiver.get("receiver")).put("character_id", 91);
        assertThrows(IllegalArgumentException.class, () -> project(receiver));
    }

    @Test void noActiveProjectMissingWalletAndObservedZeroRetainDifferentSemantics() {
        ObjectNode absent = nativeInput(); absent.putNull("active_record"); absent.put("copied_cancel_gate_allows", false);
        assertTrue(assertInstanceOf(Candidate.class, project(absent)).activeRecord().isEmpty());
        absent.put("copied_cancel_gate_allows", true); assertThrows(IllegalArgumentException.class, () -> project(absent));
        ObjectNode wallet = nativeInput(); ((ObjectNode) wallet.get("receiver")).putNull("component_pointer").putNull("current_gold_raw");
        assertTrue(assertInstanceOf(Candidate.class, project(wallet)).receiver().currentGoldRaw().isEmpty());
        ((ObjectNode) wallet.get("receiver")).put("current_gold_raw", 0);
        assertThrows(IllegalArgumentException.class, () -> project(wallet));
        ObjectNode zero = nativeInput(); ((ObjectNode) zero.get("receiver")).put("current_gold_raw", 0);
        assertEquals(0, assertInstanceOf(Candidate.class, project(zero)).receiver().currentGoldRaw().orElseThrow());
    }

    @Test void tenSignedResourcesAndDecimalPointersRejectLossyOrMalformedCopies() {
        for (String replacement : new String[] {"true", "1.0", "\"1\"", "9223372036854775808"}) {
            ObjectNode node = nativeInput(); ((ObjectNode) node.get("active_record")).set("recorded_cost_raw_native",
                    StrictJson.parse(("[" + replacement + ",0,0,0,0,0,0,0,0,0]").getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> project(node));
        }
        ObjectNode rounded = nativeInput(); ((ObjectNode) rounded.get("active_record")).put("definition_pointer", 9007199254741008L);
        assertThrows(IllegalArgumentException.class, () -> project(rounded));
        ObjectNode missing = nativeInput(); ((ObjectNode) missing.get("active_record")).remove("recorded_builder_character_id");
        assertThrows(IllegalArgumentException.class, () -> project(missing));
        ObjectNode shortVector = nativeInput(); ((ObjectNode) shortVector.get("active_record")).putArray("recorded_cost_raw_native").add(0);
        assertThrows(IllegalArgumentException.class, () -> project(shortVector));
    }

    @Test void knownMutatorsRemainClassifiedAndOldSourceSchemaCannotMasqueradeAsNativeV1() {
        for (long rva : new long[] {0x2982630L, 0x310DB20L, 0x24677B0L, 0x285EE40L, 0x12A38C0L, 0x246CE30L, 0x310D5B0L,
                0x3728020L, 0x373C320L, 0x3728590L, 0x3727EC0L}) {
            assertEquals(ConstructionRefundSource.NativeEffect.MUTATION,
                    ConstructionRefundSource.nativeEffect(HolyLoanCodec.VERSION, HolyLoanCodec.SHA256, rva));
        }
        ObjectNode old = nativeInput(); old.put("schema", "xar.ck3.copied-construction-refund-source.v1");
        assertThrows(IllegalArgumentException.class, () -> project(old));
        ObjectNode wrongBuild = nativeInput(); wrongBuild.put("game_version", "1.19.0.6");
        assertEquals(new Refused(Refusal.WRONG_EXACT_BUILD), project(wrongBuild));
    }


    /** Real original whole RF bytes, kept once by the admitted collector; no generated substitute. */
    @Test void actualContextWholeBodiesFeedTheExistingMutationClassifierWithoutCreatingFunds() throws Exception {
        String configured = System.getProperty("xar.m4.context.capture.manifest");
        String configuredSha = System.getProperty("xar.m4.context.capture.manifest.sha256");
        assertNotNull(configured, "actual M4 phaseB capture manifest is mandatory");
        assertEquals("12ceccad77c20a24f6b3a9f7309ff0a51918d12a8c1f30c796e7b672c6cd3178",
                configuredSha, "use the retained actual source role, not a replacement capture");
        Path manifest = Path.of(configured);
        assertEquals(6988L, Files.size(manifest));
        byte[] original = Files.readAllBytes(manifest);
        assertEquals(configuredSha, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        JsonNode capture = StrictJson.parse(original);
        assertEquals("xar.native-raw-window-capture/v1", capture.get("schema").textValue());
        assertEquals("COMPLETE", capture.get("status").textValue());
        assertEquals(HolyLoanCodec.SHA256.toLowerCase(java.util.Locale.ROOT), capture.get("inherited_image_sha256").textValue());
        assertEquals(capture.get("before_held").get("value"), capture.get("before_path").get("value"));
        assertEquals(capture.get("before_held").get("value"), capture.get("after_held").get("value"));
        assertEquals(capture.get("before_held").get("value"), capture.get("after_path").get("value"));
        assertEquals(0, capture.get("counts").get("unknown_read_outcomes").intValue());
        long[] entries = {0x3728020L, 0x373C320L, 0x3728590L};
        int[] sizes = {646, 382, 596};
        String[] expected = {
            "1d742fdacc90fddf499d04f5f4d6efdacc92752918e34af9883a2326e2d41eb4",
            "5fa489215832705e0f8fcc1ed4685158b85ccb4be64920105d4197b8320a75c5",
            "ccf4dc9246ba2ea8bb3ceed94128b2b0f54920608b3e9d6fd5c3641f90ea5401"};
        for (int index = 0; index < entries.length; index++) {
            JsonNode row = capture.get("windows").get(index + 1);
            assertEquals("CODE", row.get("window").get("kind").textValue());
            assertEquals("COMPLETE", row.get("status").textValue());
            assertEquals(entries[index] - 0xc00L, row.get("window").get("file_offset").longValue());
            assertEquals(sizes[index], row.get("window").get("length").intValue());
            String filename = "window-%03d.raw".formatted(index + 1);
            assertEquals(filename, row.get("raw_artifact").get("filename").textValue());
            Path raw = manifest.getParent().resolve(filename);
            assertEquals((long) sizes[index], Files.size(raw));
            byte[] body = Files.readAllBytes(raw);
            assertEquals(expected[index], HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body)));
            assertEquals(expected[index], row.get("raw_artifact").get("sha256").textValue());
            // Actual source and destination writes from the complete body, not just a caller name.
            if (index == 0) {
                assertArrayEquals(HexFormat.of().parseHex("49890649890f"),
                        java.util.Arrays.copyOfRange(body, 0x50, 0x56));
            } else if (index == 1) {
                assertArrayEquals(HexFormat.of().parseHex("4c8927"), java.util.Arrays.copyOfRange(body, 0x40, 0x43));
                assertArrayEquals(HexFormat.of().parseHex("4c8966084c8926"),
                        java.util.Arrays.copyOfRange(body, 0x150, 0x157));
            } else {
                assertArrayEquals(HexFormat.of().parseHex("49890649890f"),
                        java.util.Arrays.copyOfRange(body, 0x52, 0x58));
            }
            assertEquals(ConstructionRefundSource.NativeEffect.MUTATION,
                    ConstructionRefundSource.nativeEffect(HolyLoanCodec.VERSION, HolyLoanCodec.SHA256, entries[index]));
            assertEquals(ConstructionRefundSource.NativeEffect.UNKNOWN,
                    ConstructionRefundSource.nativeEffect("1.20.0.2", HolyLoanCodec.SHA256, entries[index]));
        }
        // The original C++ Read+Serialize producer joins the actual Java source/assessment codec.
        // These software fixture inputs still grant no Game or funding qualification.
        ObjectNode golden = actualNativeProducerGolden();
        assertEquals("xar.construction-refund-native-producer-golden.v1", StrictJson.text(golden.get("schema")));
        JsonNode producer = null;
        for (JsonNode row : golden.get("rows"))
            if (StrictJson.integer(row.get("scenario"), 0, 12) == 0) producer = row.get("receipt");
        assertNotNull(producer, "actual native producer scenario0 must be retained");
        Candidate source = assertInstanceOf(Candidate.class,
                ConstructionRefundSource.projectNative(StrictJson.canonical(producer), FRAME, EPOCH, 2));
        byte[] persisted = source.refundAssessment().toJson();
        var restored = ConstructionRefundSource.decodeRefundAssessment(persisted, source);
        assertArrayEquals(persisted, restored.toJson());
        assertFalse(restored.completeNetRefundQuote());
        assertTrue(restored.refundQuoteRaw().isEmpty());
        assertFalse(restored.receivedFundsVerified());
        assertFalse(restored.submissionQualified());
        assertEquals(0, restored.fundingCreditRaw());
    }

    private static ObjectNode actualNativeProducerGolden() throws Exception {
        String configured = System.getProperty("xar.construction.refund.producer.golden");
        String expectedSha = System.getProperty("xar.construction.refund.producer.golden.sha256");
        assertNotNull(configured, "Root must build/run construction_refund_source_12004_fixture emit and pass the actual output path");
        assertNotNull(expectedSha, "the typed native producer role must supply its exact SHA256");
        assertTrue(expectedSha.matches("[0-9a-f]{64}"), "canonical producer role SHA256 required");
        byte[] producerBytes = Files.readAllBytes(Path.of(configured));
        assertEquals(expectedSha, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(producerBytes)));
        return StrictJson.object(StrictJson.parse(producerBytes), Set.of("schema", "rows"));
    }

    private static ConstructionRefundSource.Result project(ObjectNode node) { return ConstructionRefundSource.projectNative(StrictJson.canonical(node), FRAME, EPOCH, 2); }
    private static ObjectNode nativeInput() {
        ObjectNode node = StrictJson.object(); node.put("schema", ConstructionRefundSource.NATIVE_SCHEMA);
        node.put("game_version", HolyLoanCodec.VERSION); node.put("executable_sha256", HolyLoanCodec.SHA256);
        node.put("read_only", true); node.put("scope", "copied_province_construction_source"); node.put("available", true); node.putNull("unavailable_reason");
        node.put("native_revision", "7"); node.put("capture_epoch", EPOCH.toString()); node.put("date_raw", 53288496); node.put("actor_character_id", 17);
        node.put("province_id", 2); node.put("copied_cancel_gate_allows", true);
        ObjectNode active = node.putObject("active_record"); active.put("record_pointer", "9007199254750752"); active.put("definition_pointer", "9007199254872064");
        active.put("slot_index", 3); active.put("start_word", EPOCH.toString()); active.put("recorded_builder_character_id", 91);
        var vector = active.putArray("recorded_cost_raw_native"); vector.add(15000000); for (int index = 1; index < 9; index++) { vector.add(0); } vector.add(Long.MIN_VALUE);
        ObjectNode receiver = node.putObject("receiver"); receiver.put("character_id", 17); receiver.put("component_pointer", "9007199254806528"); receiver.put("current_gold_raw", 8300000);
        node.put("final_action_gate_observed", false); node.put("submission_qualified", false); node.put("received_funds_verified", false); node.put("funding_credit_raw", 0); return node;
    }
}
