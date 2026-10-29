package org.xar.ck3.control.wave3.planning.peacetimescope;

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
import org.xar.ck3.control.wave3.planning.peacetimescope.PeacetimeScope.Failure;
import org.xar.ck3.control.wave3.planning.peacetimescope.PeacetimeScope.Presence;

final class PeacetimeScopeTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @Test void actualThreeOriginalHelpersAgreeAcrossClosedObservationsAndFailures() throws IOException {
        JsonNode rows = fixture().get("cases"); assertTrue(rows.size() >= 35);
        for (JsonNode row : rows) {
            byte[] request = JSON.writeValueAsBytes(row.get("input")); String name = row.get("name").textValue();
            if (row.get("original_accepted").booleanValue()) {
                assertEquals(row.get("expected"), JSON.readTree(PeacetimeScopeCodec.verifyAndEncode(request)), name);
            } else {
                assertThrows(IllegalArgumentException.class, () -> PeacetimeScopeCodec.verify(request), name);
            }
        }
    }

    @Test void publicAndNativeRevisionRemainIndependentWhileAllSixFieldsBind() throws IOException {
        PeacetimeScopeCodec.Request request = PeacetimeScopeCodec.decode(bytes(input("stable-two-observations")));
        assertNotEquals(request.before().frame().revision(), request.before().frame().nativeRevision());
        for (String name : List.of("current-drift-date_raw", "current-drift-episode_run_id", "current-actor-drift", "current-native-stamp-drift")) {
            PeacetimeScope.Unavailable rejected = assertThrows(PeacetimeScope.Unavailable.class,
                    () -> PeacetimeScopeCodec.verify(bytes(input(name))));
            assertEquals(Failure.crossed_paused_frame, rejected.failure(), name);
        }
        assertEquals(Failure.peaceful_paused_actor_frame_required, assertThrows(PeacetimeScope.Unavailable.class,
                () -> PeacetimeScopeCodec.verify(bytes(input("current-drift-revision")))).failure());
    }

    @Test void missingOrNullActivityIsClearButMissingOrNullCollectionsAreNotEmpty() throws IOException {
        PeacetimeScopeCodec.Request missing = PeacetimeScopeCodec.decode(bytes(input("missing-clear-active_event")));
        PeacetimeScopeCodec.Request explicitNull = PeacetimeScopeCodec.decode(bytes(input("stable-two-observations")));
        assertEquals(Presence.MISSING, missing.before().activeEvent()); assertEquals(Presence.NULL, explicitNull.before().activeEvent());
        PeacetimeScope.verify(missing.before(), missing.expectedRevision(), missing.readback());
        ObjectNode request = input("stable-two-observations"); before(request).putNull("active_wars");
        assertThrows(PeacetimeScope.Unavailable.class, () -> PeacetimeScopeCodec.verify(bytes(request)));
        before(request).remove("active_wars");
        assertThrows(PeacetimeScope.Unavailable.class, () -> PeacetimeScopeCodec.verify(bytes(request)));
    }

    @Test void independentWalletReadbackCannotBeReplacedByFrameEquality() throws IOException {
        assertEquals(Failure.player_gold_changed, assertThrows(PeacetimeScope.Unavailable.class,
                () -> PeacetimeScopeCodec.verify(bytes(input("same-frame-wallet-changed")))).failure());
        ObjectNode request = input("zero-observed-wallet");
        assertEquals(BigInteger.ZERO, PeacetimeScopeCodec.verify(bytes(request)).observedGoldRaw());
    }

    @Test void actualFloatAndBooleanAliasesAcceptedByOldEqualityAreRejectedAtJavaBoundary() throws IOException {
        JsonNode corrections = fixture().get("contract_corrections"); assertEquals(3, corrections.size());
        for (JsonNode row : corrections) {
            assertTrue(row.get("original_accepted").booleanValue(), row.get("name").textValue());
            assertFalse(row.get("java_expected_accepted").booleanValue());
            assertThrows(IllegalArgumentException.class, () -> PeacetimeScopeCodec.verify(bytes(row.get("input"))));
        }
        for (String field : List.of("native_revision", "revision", "date_raw", "played_character_id")) {
            for (JsonNode bad : List.of(JSON.getNodeFactory().booleanNode(true), JSON.getNodeFactory().numberNode(17.0), JSON.getNodeFactory().textNode("17"))) {
                ObjectNode request = input("stable-two-observations"); before(request).set(field, bad);
                assertThrows(IllegalArgumentException.class, () -> PeacetimeScopeCodec.verify(bytes(request)), field);
            }
        }
    }

    @Test void readerPortIsCalledOnceAndNotCalledAfterInitialFailure() throws IOException {
        PeacetimeScopeCodec.Request request = PeacetimeScopeCodec.decode(bytes(input("stable-two-observations")));
        AtomicInteger calls = new AtomicInteger();
        PeacetimeScope.StableObservation checked = PeacetimeScope.verifyFromReader(request.before(), request.expectedRevision(),
                Optional.of(() -> { calls.incrementAndGet(); return request.readback(); }));
        assertEquals(1, calls.get()); assertFalse(checked.formalActionReady());
        assertThrows(PeacetimeScope.Unavailable.class, () -> PeacetimeScope.verifyFromReader(request.before(), BigInteger.ZERO,
                Optional.of(() -> { calls.incrementAndGet(); return request.readback(); })));
        assertEquals(1, calls.get());
        assertEquals(Failure.internal_snapshot_reader_unavailable, assertThrows(PeacetimeScope.Unavailable.class,
                () -> PeacetimeScope.verifyFromReader(request.before(), request.expectedRevision(), Optional.empty())).failure());
        assertEquals(Failure.internal_snapshot_malformed, assertThrows(PeacetimeScope.Unavailable.class,
                () -> PeacetimeScope.verifyFromReader(request.before(), request.expectedRevision(), Optional.of(() -> null))).failure());
    }

    @Test void exactLargeIntegersAndClosedResultSurviveJsonPersistenceRoundTrip() throws IOException {
        for (JsonNode row : fixture().get("cases")) {
            if (!row.get("original_accepted").booleanValue()) { continue; }
            byte[] originalRequest = bytes(row.get("input")); byte[] persistedRequest = OpportunityJson.encode(OpportunityJson.parse(originalRequest));
            byte[] result = PeacetimeScopeCodec.verifyAndEncode(originalRequest);
            assertEquals(JSON.readTree(result), JSON.readTree(PeacetimeScopeCodec.verifyAndEncode(persistedRequest)));
            assertEquals(JSON.readTree(result), JSON.readTree(OpportunityJson.encode(OpportunityJson.parse(result))));
        }
        PeacetimeScope.StableObservation large = PeacetimeScopeCodec.verify(bytes(input("large-exact-frame-integers")));
        assertEquals(new BigInteger("9007199254740997"), large.frame().nativeRevision());
    }

    @Test void strictWrapperAndReaderUnionRejectUnknownMissingDuplicateAndMalformedInput() throws IOException {
        ObjectNode unknown = input("stable-two-observations"); unknown.put("qualified", true);
        assertThrows(IllegalArgumentException.class, () -> PeacetimeScopeCodec.verify(bytes(unknown)));
        ObjectNode missing = input("stable-two-observations"); missing.remove("expected_revision");
        assertThrows(IllegalArgumentException.class, () -> PeacetimeScopeCodec.verify(bytes(missing)));
        ObjectNode readerGreen = input("stable-two-observations"); ((ObjectNode) readerGreen.get("reader")).put("qualified", true);
        assertThrows(IllegalArgumentException.class, () -> PeacetimeScopeCodec.verify(bytes(readerGreen)));
        byte[] valid = bytes(input("stable-two-observations"));
        String duplicate = new String(valid, StandardCharsets.UTF_8).replaceFirst("\\{", "{\"schema\":\"" + PeacetimeScopeCodec.SCHEMA + "\",");
        assertThrows(IllegalArgumentException.class, () -> PeacetimeScopeCodec.verify(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> PeacetimeScopeCodec.verify(new byte[] {(byte) 0xc3, (byte) 0x28}));
        assertThrows(IllegalArgumentException.class, () -> PeacetimeScopeCodec.verify(new byte[PeacetimeScopeCodec.MAXIMUM_WRAPPER_BYTES + 1]));
    }

    private static ObjectNode before(ObjectNode request) { return (ObjectNode) request.get("before"); }
    private static byte[] bytes(JsonNode value) throws IOException { return JSON.writeValueAsBytes(value); }
    private static ObjectNode input(String name) throws IOException {
        for (JsonNode row : fixture().get("cases")) {
            if (row.get("name").textValue().equals(name)) { return (ObjectNode) row.get("input").deepCopy(); }
        }
        throw new IOException("missing actual original producer scenario " + name);
    }
    private static JsonNode fixture() throws IOException {
        try (InputStream stream = PeacetimeScopeTest.class.getResourceAsStream("/peacetimescope/original-producer-golden.json")) {
            if (stream == null) { throw new IOException("actual original helper golden required; not skipped"); }
            return JSON.readTree(stream);
        }
    }
}
