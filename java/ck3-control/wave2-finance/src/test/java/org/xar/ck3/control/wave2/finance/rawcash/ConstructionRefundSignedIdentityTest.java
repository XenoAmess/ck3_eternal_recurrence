package org.xar.ck3.control.wave2.finance.rawcash;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.holyloan.LoanFinancingCodec.PlanningFrame;

/** Actual C++ producer artifact plus separately identified malformed copies; no Game or cancellation action. */
final class ConstructionRefundSignedIdentityTest {
    private static final BigInteger EPOCH = new BigInteger("18446744073709551614");

    private static ObjectNode artifact() throws Exception {
        String file = System.getProperty("xar.construction.refund.signed.golden");
        String sha = System.getProperty("xar.construction.refund.signed.golden.sha256");
        assertNotNull(file, "actual signed native producer artifact required");
        assertNotNull(sha, "actual signed native producer artifact SHA required");
        byte[] bytes = Files.readAllBytes(Path.of(file));
        assertEquals(sha, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        return StrictJson.object(StrictJson.parse(bytes), Set.of("cases"));
    }
    private static ObjectNode source(String name) throws Exception {
        for (JsonNode row : artifact().get("cases")) if (name.equals(StrictJson.text(row.get("case")))) {
            assertEquals(name.equals("negative-two-typed-data") ? "typed-serialize-data" : "native-read",
                    StrictJson.text(row.get("source_kind")));
            return (ObjectNode) row.get("receipt").deepCopy();
        }
        throw new AssertionError("missing actual producer case " + name);
    }
    private static PlanningFrame frame(long actor) {
        return new PlanningFrame("signed-refund:19", BigInteger.valueOf(19), BigInteger.valueOf(7),
                BigInteger.valueOf(53288496), BigInteger.valueOf(actor), "signed-refund-software-episode",
                BigInteger.valueOf(123), BigInteger.ONE);
    }
    private static ConstructionRefundSource.Result project(ObjectNode source, long actor) {
        return ConstructionRefundSource.projectNative(StrictJson.canonical(source), frame(actor), EPOCH, 2);
    }
    private static void noFunds(ConstructionRefundSource.Candidate candidate) {
        assertFalse(candidate.finalCancelGateObserved()); assertFalse(candidate.submissionQualified());
        assertFalse(candidate.receivedFundsVerified()); assertEquals(0, candidate.fundingCreditRaw());
        var assessment = candidate.refundAssessment();
        assertFalse(assessment.completeNetRefundQuote()); assertTrue(assessment.refundQuoteRaw().isEmpty());
        assertFalse(assessment.submissionQualified()); assertFalse(assessment.receivedFundsVerified());
        assertEquals(0, assessment.fundingCreditRaw());
        assertArrayEquals(assessment.toJson(), ConstructionRefundSource.decodeRefundAssessment(assessment.toJson(), candidate).toJson());
    }

    @Test void actualSignedProducerNativeReadsAndTypedDataRoundTripWithoutFunding() throws Exception {
        for (var pair : java.util.Map.of("int-min-owned-read", (long) Integer.MIN_VALUE,
                "zero-owned-read", 0L, "negative-two-typed-data", -2L).entrySet()) {
            ObjectNode nativeSource = source(pair.getKey());
            var candidate = assertInstanceOf(ConstructionRefundSource.Candidate.class, project(nativeSource, pair.getValue()));
            assertEquals(pair.getValue().longValue(), candidate.receiver().characterId());
            assertEquals(BigInteger.valueOf(pair.getValue()), candidate.frame().actorCharacterId());
            var persisted = StrictJson.parse(candidate.toJson());
            assertEquals(nativeSource, persisted.get("native_observation"));
            var restored = assertInstanceOf(ConstructionRefundSource.Candidate.class,
                    ConstructionRefundSource.decode(candidate.toJson(), frame(pair.getValue()), EPOCH, 2));
            assertArrayEquals(candidate.toJson(), restored.toJson());
            assertEquals(nativeSource.get("active_record").get("recorded_builder_character_id").longValue(),
                    restored.activeRecord().orElseThrow().recordedBuilderCharacterId());
            if (!pair.getKey().equals("zero-owned-read"))
                assertEquals(4294967294L, restored.activeRecord().orElseThrow().recordedBuilderCharacterId());
            noFunds(candidate); noFunds(restored);
        }
    }

    @Test void actualMinusOneReadRemainsUnavailableWithNullActorAndReceiver() throws Exception {
        ObjectNode absent = source("minus-one-unavailable-read");
        assertTrue(absent.get("actor_character_id").isNull()); assertTrue(absent.get("receiver").isNull());
        var unavailable = assertInstanceOf(ConstructionRefundSource.Unavailable.class, project(absent, 17));
        assertArrayEquals(unavailable.toJson(), assertInstanceOf(ConstructionRefundSource.Unavailable.class,
                ConstructionRefundSource.decode(unavailable.toJson(), frame(17), EPOCH, 2)).toJson());
    }

    @Test void actorAndReceiverRejectUnsignedAliasesFloatsBooleanAndAbsentValue() throws Exception {
        ObjectNode seed = source("int-min-owned-read");
        for (String token : java.util.List.of("2147483648", "4294967294", "-2147483649", "-1", "true", "-2147483648.0")) {
            ObjectNode actor = seed.deepCopy(); actor.set("actor_character_id", StrictJson.parse(token.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> project(actor, Integer.MIN_VALUE), "actor " + token);
            ObjectNode receiver = seed.deepCopy(); ((ObjectNode) receiver.get("receiver")).set("character_id",
                    StrictJson.parse(token.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> project(receiver, Integer.MIN_VALUE), "receiver " + token);
        }
    }

    @Test void signedFrameAndReceiverBindingsRemainExact() throws Exception {
        ObjectNode minimum = source("int-min-owned-read");
        assertEquals(new ConstructionRefundSource.Refused(ConstructionRefundSource.Refusal.FRAME_DRIFT),
                project(minimum, Integer.MIN_VALUE + 1L));
        ObjectNode crossed = minimum.deepCopy(); ((ObjectNode) crossed.get("receiver")).put("character_id", -2);
        assertThrows(IllegalArgumentException.class, () -> project(crossed, Integer.MIN_VALUE));
        assertThrows(IllegalArgumentException.class, () -> project(minimum, -1));
        assertThrows(IllegalArgumentException.class, () -> project(minimum, 2147483648L));
        var candidate = assertInstanceOf(ConstructionRefundSource.Candidate.class, project(minimum, Integer.MIN_VALUE));
        for (long actor : new long[] {-1, 2147483648L, -2147483649L}) {
            ObjectNode saved = (ObjectNode) StrictJson.parse(candidate.toJson());
            ((ObjectNode) saved.get("planning_frame")).put("actor_character_id", actor);
            assertThrows(IllegalArgumentException.class,
                    () -> ConstructionRefundSource.decode(StrictJson.canonical(saved), frame(Integer.MIN_VALUE), EPOCH, 2));
        }
    }

    @Test void builderRemainsRawUint32AndDoesNotAuthorizeFunding() throws Exception {
        ObjectNode seed = source("int-min-owned-read");
        for (long bits : new long[] {0, 2147483648L, 4294967294L, 4294967295L}) {
            ObjectNode changed = seed.deepCopy(); ((ObjectNode) changed.get("active_record")).put("recorded_builder_character_id", bits);
            var candidate = assertInstanceOf(ConstructionRefundSource.Candidate.class, project(changed, Integer.MIN_VALUE));
            assertEquals(bits, candidate.activeRecord().orElseThrow().recordedBuilderCharacterId()); noFunds(candidate);
        }
        for (long invalid : new long[] {-1, 4294967296L}) {
            ObjectNode changed = seed.deepCopy(); ((ObjectNode) changed.get("active_record")).put("recorded_builder_character_id", invalid);
            assertThrows(IllegalArgumentException.class, () -> project(changed, Integer.MIN_VALUE));
        }
    }

    @Test void receiverValueObjectUsesSignedInt32RatherThanUnsignedBits() {
        for (long actor : new long[] {Integer.MIN_VALUE, -2, 0, Integer.MAX_VALUE})
            assertEquals(actor, new ConstructionRefundSource.Receiver(actor, Optional.empty(), OptionalLong.empty()).characterId());
        for (long actor : new long[] {Integer.MIN_VALUE - 1L, -1, Integer.MAX_VALUE + 1L, 4294967294L})
            assertThrows(IllegalArgumentException.class,
                    () -> new ConstructionRefundSource.Receiver(actor, Optional.empty(), OptionalLong.empty()));
    }
}
