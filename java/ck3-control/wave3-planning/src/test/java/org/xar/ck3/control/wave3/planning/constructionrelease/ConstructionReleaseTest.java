package org.xar.ck3.control.wave3.planning.constructionrelease;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave3.planning.constructionrelease.ConstructionRelease.Reason;

final class ConstructionReleaseTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @Test void actualOriginalReleaseHelperMatchesEveryNormalGoldenCase() throws IOException {
        JsonNode cases = fixture().get("cases"); assertTrue(cases.size() >= 24);
        for (JsonNode row : cases) {
            ConstructionRelease.Decision decision = ConstructionReleaseCodec.assess(bytes(row.get("input")));
            assertEquals(row.get("expected_blocks_candidate").booleanValue(), decision.blocksCandidate(), row.get("name").textValue());
            assertFalse(decision.formalActionReady());
        }
    }

    @Test void wholeOriginalQueryConsumerDefersOnlyTheBuildingDomain() throws IOException {
        JsonNode cases = fixture().get("consumer_cases"); assertEquals(4, cases.size());
        for (JsonNode row : cases) {
            ConstructionRelease.Decision decision = ConstructionReleaseCodec.assess(bytes(row.get("input")));
            JsonNode consumer = row.get("expected_consumer"); boolean queried = consumer.get("construction_query_calls").intValue() == 1;
            assertEquals(queried, !decision.blocksCandidate(), row.get("name").textValue());
            boolean hasBuilding = false; boolean hasDiplomacy = false;
            for (JsonNode domain : consumer.get("domains")) {
                hasBuilding |= domain.textValue().equals("building"); hasDiplomacy |= domain.textValue().equals("diplomacy");
            }
            assertEquals(queried, hasBuilding); assertTrue(hasDiplomacy, "unreleased construction cannot stop independent gifts");
            assertEquals(queried ? "selected" : "prior_receipt_not_released", consumer.get("construction_status").textValue());
            assertTrue(row.get("projection_not_original").booleanValue());
            assertEquals(64, consumer.get("original_full_result_sha256").textValue().length());
        }
    }

    @Test void bothNativeFrameAndDateMustStrictlyAdvanceWithVerifiedSameActorAndProcess() throws IOException {
        assertFalse(assess("later-native-and-date-release").blocksCandidate());
        assertEquals(Reason.native_frame_not_later, assess("hold-post_native_revision-17").reason());
        assertEquals(Reason.date_not_later, assess("hold-post_date_raw-53202168").reason());
        assertEquals(Reason.postcondition_unverified, assess("hold-postcondition_verified-False").reason());
        assertEquals(Reason.process_mismatch, assess("different-process-pid-holds").reason());
        assertEquals(Reason.process_observation_unavailable, assess("process-reader-unavailable-holds").reason());
    }

    @Test void uniqueBirthParserComparesOriginalSpellingsWithoutReplacingEvidence() throws IOException {
        ObjectNode input = input("different-spelling-same-process-instant");
        ConstructionReleaseCodec.Request decoded = ConstructionReleaseCodec.decode(bytes(input));
        ConstructionRelease.Receipt receipt = (ConstructionRelease.Receipt) decoded.applied();
        String prior = receipt.details().orElseThrow().originalPostCreationDate().orElseThrow();
        String observed = ((ConstructionRelease.ObservedIdentity) decoded.processObservation()).identity().originalCreationDate();
        assertNotEquals(prior, observed); assertFalse(ConstructionReleaseCodec.assess(bytes(input)).blocksCandidate());
        assertTrue(assess("unrepresentable-100ns-is-not-normalized-away").blocksCandidate());
        assertFalse(assess("later-native-and-date-release").blocksCandidate(), "original exact opaque fixture spelling equality remains ABI");
    }

    @Test void foreignEpisodeDoesNotReadProcessAndCurrentEpisodeReadsBeforeReceiptChecks() throws IOException {
        ConstructionReleaseCodec.Request foreign = ConstructionReleaseCodec.decode(bytes(input("foreign-episode-does-not-read-process")));
        AtomicInteger calls = new AtomicInteger();
        ConstructionRelease.Decision ignored = ConstructionRelease.assessFromReader(foreign.frame(), foreign.applied(),
                Optional.of(() -> { calls.incrementAndGet(); throw new IllegalStateException("unused reader must not run"); }));
        assertFalse(ignored.blocksCandidate()); assertEquals(0, calls.get());
        ConstructionReleaseCodec.Request malformed = ConstructionReleaseCodec.decode(bytes(input("missing-status-holds")));
        ConstructionRelease.Decision held = ConstructionRelease.assessFromReader(malformed.frame(), malformed.applied(),
                Optional.of(() -> { calls.incrementAndGet(); return malformed.processObservation(); }));
        assertTrue(held.blocksCandidate()); assertEquals(Reason.status_not_applied, held.reason()); assertEquals(1, calls.get());
        assertEquals(Reason.process_observation_unavailable, ConstructionRelease.assessFromReader(malformed.frame(), malformed.applied(), Optional.empty()).reason());
    }

    @Test void actualOldIdentityAliasesAndWrongIdentityTokensAreRejected() throws IOException {
        JsonNode corrections = fixture().get("contract_corrections"); assertEquals(2, corrections.size());
        for (JsonNode row : corrections) {
            assertFalse(row.get("expected_blocks_candidate").booleanValue(), "old equality alias was actually accepted");
            assertThrows(IllegalArgumentException.class, () -> ConstructionReleaseCodec.assess(bytes(row.get("input"))));
        }
        for (String key : List.of("actor_character_id", "post_bridge_pid", "post_native_revision", "post_date_raw")) {
            ObjectNode request = input("later-native-and-date-release"); ((ObjectNode) request.get("applied")).put(key, 1.0);
            assertThrows(IllegalArgumentException.class, () -> ConstructionReleaseCodec.assess(bytes(request)), key);
        }
        ObjectNode unavailable = input("process-reader-unavailable-holds");
        assertTrue(ConstructionReleaseCodec.assess(bytes(unavailable)).blocksCandidate());
    }

    @Test void receiptAndDecisionPersistenceKeepExactJsonIntegerDomain() throws IOException {
        for (JsonNode row : fixture().get("cases")) {
            byte[] raw = bytes(row.get("input")); byte[] persisted = OpportunityJson.encode(OpportunityJson.parse(raw));
            assertEquals(ConstructionReleaseCodec.assess(raw), ConstructionReleaseCodec.assess(persisted));
            byte[] result = ConstructionReleaseCodec.assessAndEncode(raw);
            assertEquals(JSON.readTree(result), JSON.readTree(OpportunityJson.encode(OpportunityJson.parse(result))));
        }
        ObjectNode request = input("later-native-and-date-release"); BigInteger large = new BigInteger("9007199254740997");
        ((ObjectNode) request.get("frame")).put("played_character_id", large); ((ObjectNode) request.get("applied")).put("actor_character_id", large);
        assertFalse(ConstructionReleaseCodec.assess(bytes(request)).blocksCandidate());
    }

    @Test void strictWrapperAndObservedIdentityUnionRejectGreenLabelsAndMalformedJson() throws IOException {
        ObjectNode unknown = input("later-native-and-date-release"); unknown.put("released", true);
        assertThrows(IllegalArgumentException.class, () -> ConstructionReleaseCodec.assess(bytes(unknown)));
        ObjectNode missing = input("later-native-and-date-release"); missing.remove("frame");
        assertThrows(IllegalArgumentException.class, () -> ConstructionReleaseCodec.assess(bytes(missing)));
        ObjectNode process = input("later-native-and-date-release"); ((ObjectNode) process.get("process_observation")).put("same_process", true);
        assertThrows(IllegalArgumentException.class, () -> ConstructionReleaseCodec.assess(bytes(process)));
        String raw = JSON.writeValueAsString(input("later-native-and-date-release"));
        String duplicate = raw.replaceFirst("\\{", "{\"schema\":\"" + ConstructionReleaseCodec.SCHEMA + "\",");
        assertThrows(IllegalArgumentException.class, () -> ConstructionReleaseCodec.assess(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> ConstructionReleaseCodec.assess(new byte[] {(byte) 0xc3, (byte) 0x28}));
    }

    private static ConstructionRelease.Decision assess(String name) throws IOException { return ConstructionReleaseCodec.assess(bytes(input(name))); }
    private static byte[] bytes(JsonNode value) throws IOException { return JSON.writeValueAsBytes(value); }
    private static ObjectNode input(String name) throws IOException {
        for (JsonNode row : fixture().get("cases")) { if (row.get("name").textValue().equals(name)) { return (ObjectNode) row.get("input").deepCopy(); } }
        throw new IOException("missing actual original release scenario " + name);
    }
    private static JsonNode fixture() throws IOException {
        try (InputStream stream = ConstructionReleaseTest.class.getResourceAsStream("/constructionrelease/original-producer-golden.json")) {
            if (stream == null) { throw new IOException("actual original helper and whole query golden required; not skipped"); }
            return JSON.readTree(stream);
        }
    }
}
