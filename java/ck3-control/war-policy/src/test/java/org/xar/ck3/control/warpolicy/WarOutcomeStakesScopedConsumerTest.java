package org.xar.ck3.control.warpolicy;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.observation.ObservationReuse;

/** Exercises the actual production entrypoint; the old adapter shares that exact cache path. */
final class WarOutcomeStakesScopedConsumerTest {
    private record Bound(WarOutcomeStakesProjector projector,
            ObservationReuse<ObservationContext, WarObservationFrame, WarOutcomeStakesResult> owner,
            ObservationReuse.Token<ObservationContext, WarObservationFrame> token) { }

    private static Bound bound(ObjectNode request) {
        var owner = new ObservationReuse<ObservationContext, WarObservationFrame, WarOutcomeStakesResult>("original-writer", 8);
        var token = owner.bindFresh(new ObservationReuse.Scope<>(
            ObservationContext.fromJson(request.get("observation_context")),
            WarObservationFrame.fromSnapshot(request.get("snapshot")), version(240)));
        return new Bound(new WarOutcomeStakesProjector(ReviewedSourceRegistry.bundled()), owner, token);
    }

    private static ObservationReuse.WriterVersion version(int value) {
        return new ObservationReuse.WriterVersion("original-writer", BigInteger.valueOf(value));
    }

    @Test void directProductionAndConvenienceConsumerShareOneCompletedProjection() throws IOException {
        ObjectNode request = baseRequest(); var bound = bound(request); byte[] raw = StrictJson.canonical(request);
        var first = bound.projector().projectScoped(bound.owner(), bound.token(), raw);
        var adapter = new ScopedWarOutcomeStakesProjector(bound.projector(), bound.owner());
        var second = adapter.project(bound.token(), raw.clone());
        assertFalse(first.reused()); assertTrue(second.reused());
        assertSame(first.outcome().value(), second.outcome().value());
        assertArrayEquals(bound.projector().project(raw), second.outcome().value().toCanonicalBytes());
        assertEquals(1, bound.owner().retainedEntryCount());
    }

    @Test void malformedMissRevokesThePreviouslyCompletedLeaseThroughBothConsumers() throws IOException {
        for (boolean adapter : List.of(false, true)) {
            for (String variant : List.of("schema", "missing", "boolean_id", "snapshot", "extra")) {
                ObjectNode request = baseRequest(); var bound = bound(request);
                byte[] good = StrictJson.canonical(request);
                bound.projector().projectScoped(bound.owner(), bound.token(), good);
                switch (variant) {
                    case "schema" -> request.put("schema", "wrong-schema");
                    case "missing" -> request.remove("war_id");
                    case "boolean_id" -> request.put("war_id", true);
                    case "snapshot" -> request.putNull("snapshot");
                    case "extra" -> request.put("unrecognized", 1);
                    default -> throw new IllegalStateException("test variant");
                }
                byte[] malformed = StrictJson.canonical(request);
                var convenience = new ScopedWarOutcomeStakesProjector(bound.projector(), bound.owner());
                assertThrows(ContractViolationException.class, () -> {
                    if (adapter) { convenience.project(bound.token(), malformed); }
                    else { bound.projector().projectScoped(bound.owner(), bound.token(), malformed); }
                }, variant);
                assertEquals(ObservationReuse.Invalidation.INCOMPLETE_OBSERVATION, bound.owner().lastInvalidation());
                assertEquals(0, bound.owner().retainedEntryCount());
                assertThrows(IllegalStateException.class,
                    () -> bound.projector().projectScoped(bound.owner(), bound.token(), good));
                assertThrows(IllegalStateException.class, () -> bound.owner().bindFresh(bound.token().scope()));
            }
        }
    }

    @Test void malformedJsonMissAlsoRevokesWithoutReturningAnOlderCompleteValue() throws IOException {
        ObjectNode request = baseRequest(); var bound = bound(request);
        bound.projector().projectScoped(bound.owner(), bound.token(), StrictJson.canonical(request));
        assertThrows(ContractViolationException.class, () -> bound.projector().projectScoped(bound.owner(),
            bound.token(), new byte[] {'{'}));
        assertEquals(0, bound.owner().retainedEntryCount());
        assertThrows(IllegalStateException.class, () -> bound.owner().requireCurrent(bound.token()));
    }

    @Test void wholeInputSourceLeavesCannotAliasACompletedSameFrameRequest() throws IOException {
        ObjectNode request = baseRequest(); var bound = bound(request);
        bound.projector().projectScoped(bound.owner(), bound.token(), StrictJson.canonical(request));
        request.set("current_source_sha256", StrictJson.object());
        byte[] changed = StrictJson.canonical(request);
        var actual = bound.projector().projectScoped(bound.owner(), bound.token(), changed);
        assertFalse(actual.reused()); assertInstanceOf(ObservationReuse.Unknown.class, actual.outcome());
        assertArrayEquals(bound.projector().project(changed), actual.outcome().value().toCanonicalBytes());
        assertEquals(0, bound.owner().retainedEntryCount());
    }

    @Test void replacedGameOwnerCannotConsumeTheOldGamesCompletedLease() throws IOException {
        ObjectNode request = baseRequest(); var old = bound(request); var replacement = bound(request);
        byte[] raw = StrictJson.canonical(request);
        old.projector().projectScoped(old.owner(), old.token(), raw);
        old.owner().close();
        assertThrows(IllegalStateException.class,
            () -> replacement.projector().projectScoped(replacement.owner(), old.token(), raw));
        assertThrows(IllegalStateException.class,
            () -> old.projector().projectScoped(old.owner(), old.token(), raw));
        assertFalse(replacement.projector().projectScoped(replacement.owner(), replacement.token(), raw).reused());
    }

    @Test void unknownActionRemainsBlockedUntilOriginalOwnerSettlesAtANewerVersion() throws IOException {
        ObjectNode request = baseRequest(); var bound = bound(request); byte[] raw = StrictJson.canonical(request);
        bound.projector().projectScoped(bound.owner(), bound.token(), raw);
        bound.owner().beforeSubmit(version(240)); bound.owner().unknownOutcome(version(240));
        var source = bound.token().scope().source(); var frame = bound.token().scope().frame();
        assertThrows(IllegalStateException.class,
            () -> bound.owner().bindFresh(new ObservationReuse.Scope<>(source, frame, version(241))));
        assertThrows(IllegalStateException.class,
            () -> bound.projector().projectScoped(bound.owner(), bound.token(), raw));
        bound.owner().ownerSettledUnknown(version(241));
        var settled = bound.owner().bindFresh(new ObservationReuse.Scope<>(source, frame, version(241)));
        assertFalse(bound.projector().projectScoped(bound.owner(), settled, raw).reused());
    }

    @Test void sourceAndFullFrameDriftKeepTheirOriginalSpecificInvalidation() throws IOException {
        for (boolean source : List.of(false, true)) {
            ObjectNode request = baseRequest(); var bound = bound(request);
            bound.projector().projectScoped(bound.owner(), bound.token(), StrictJson.canonical(request));
            if (source) { ((ObjectNode) request.get("observation_context")).put("snapshot_sha256", "f".repeat(64)); }
            else { ((ObjectNode) request.get("snapshot").get("diagnostics")).put("connection_generation", 999); }
            byte[] drifted = StrictJson.canonical(request);
            assertThrows(ContractViolationException.class,
                () -> bound.projector().projectScoped(bound.owner(), bound.token(), drifted));
            assertEquals(source ? ObservationReuse.Invalidation.SOURCE_CHANGED : ObservationReuse.Invalidation.FRAME_CHANGED,
                bound.owner().lastInvalidation());
            assertEquals(0, bound.owner().retainedEntryCount());
        }
    }

    @Test void serializedBytesAndCallerBuffersCannotMutateACompletedResult() throws IOException {
        ObjectNode request = baseRequest(); var bound = bound(request); byte[] raw = StrictJson.canonical(request);
        byte[] sameRequest = raw.clone();
        var first = bound.projector().projectScoped(bound.owner(), bound.token(), raw);
        byte[] originalResult = first.outcome().value().toCanonicalBytes();
        byte[] exported = first.outcome().value().toCanonicalBytes(); exported[0] = 0; raw[0] = 0;
        var hit = bound.projector().projectScoped(bound.owner(), bound.token(), sameRequest);
        assertTrue(hit.reused()); assertArrayEquals(originalResult, hit.outcome().value().toCanonicalBytes());
        JsonNode wire = StrictJson.parse(originalResult);
        assertFalse(wire.path("actual_effects_verified").booleanValue());
        assertFalse(wire.path("automatic_surrender_qualified").booleanValue());
        assertTrue(wire.path("selected_action").isNull());
    }

    private static ObjectNode baseRequest() throws IOException {
        String resource = "/org/xar/ck3/control/warpolicy/war_outcome_stakes_golden_v1.jsonl";
        try (InputStream stream = WarOutcomeStakesScopedConsumerTest.class.getResourceAsStream(resource)) {
            if (stream == null) { throw new IllegalStateException("original producer corpus missing"); }
            byte[] raw = stream.readNBytes(2 * 1024 * 1024 + 1);
            if (raw.length > 2 * 1024 * 1024) { throw new IllegalStateException("original corpus budget exceeded"); }
            for (String line : new String(raw, StandardCharsets.UTF_8).split("\n")) {
                JsonNode row = StrictJson.parse(line.getBytes(StandardCharsets.UTF_8));
                if ("result".equals(row.path("expected_kind").textValue())
                        && "test_actual_normalizer_cache_and_json_roundtrip_claim_defender".equals(row.path("test_method").textValue())) {
                    JsonNode request = StrictJson.parse(StrictJson.text(row.get("input_json")).getBytes(StandardCharsets.UTF_8));
                    if (request instanceof ObjectNode object) { return object; }
                }
            }
            throw new IllegalStateException("original successful producer vector missing");
        }
    }
}
