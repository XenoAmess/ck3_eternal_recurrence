package org.xar.ck3.control.warpolicy;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.observation.ObservationReuse;

final class ScopedWarOutcomeStakesProjectorTest {
    private record Bound(ObservationReuse<ObservationContext, WarObservationFrame, WarOutcomeStakesResult> owner,
            ObservationReuse.Token<ObservationContext, WarObservationFrame> token,
            ScopedWarOutcomeStakesProjector consumer, WarOutcomeStakesProjector original) { }

    private static Bound bound(ObjectNode input) {
        var source = ObservationContext.fromJson(input.get("observation_context"));
        var frame = WarObservationFrame.fromSnapshot(input.get("snapshot"));
        var owner = new ObservationReuse<ObservationContext, WarObservationFrame, WarOutcomeStakesResult>("original-writer", 8);
        var token = owner.bindFresh(new ObservationReuse.Scope<>(source, frame,
            new ObservationReuse.WriterVersion("original-writer", BigInteger.valueOf(240))));
        var projector = new WarOutcomeStakesProjector(ReviewedSourceRegistry.bundled());
        return new Bound(owner, token, new ScopedWarOutcomeStakesProjector(projector, owner), projector);
    }

    @Test void actualProjectionAndWholeWireMatchOriginalWithDifferentPublicAndNativeRevisions() throws IOException {
        ObjectNode input = baseRequest(); var bound = bound(input); byte[] raw = StrictJson.canonical(input);
        assertNotEquals(bound.token().scope().frame().revision(), bound.token().scope().frame().nativeRevision());
        var first = bound.consumer().project(bound.token(), raw);
        var second = bound.consumer().project(bound.token(), raw);
        assertFalse(first.reused()); assertTrue(second.reused());
        assertArrayEquals(bound.original().project(raw), first.outcome().value().toCanonicalBytes());
        assertArrayEquals(first.outcome().value().toCanonicalBytes(), second.outcome().value().toCanonicalBytes());
        JsonNode result = first.outcome().value().toJson();
        assertFalse(result.path("actual_effects_verified").booleanValue());
        assertFalse(result.path("automatic_surrender_qualified").booleanValue());
        assertTrue(result.path("selected_action").isNull());
        assertThrows(UnsupportedOperationException.class, () -> first.outcome().value().consultedSources().clear());
    }

    @Test void identicalFrameLabelsCannotAliasDifferentCompleteInputBytes() throws IOException {
        ObjectNode input = baseRequest(); var bound = bound(input);
        var first = bound.consumer().project(bound.token(), StrictJson.canonical(input));
        object(input, "snapshot").put("legacy_extension_not_used_for_selection", true);
        var changed = bound.consumer().project(bound.token(), StrictJson.canonical(input));
        assertFalse(first.reused()); assertFalse(changed.reused());
        assertArrayEquals(bound.original().project(StrictJson.canonical(input)), changed.outcome().value().toCanonicalBytes());
        assertEquals(2, bound.owner().retainedEntryCount());
    }

    @Test void sourceDriftAndCrossFrameInputRevokeTheRealLeaseBeforeReturningAnyPriorValue() throws IOException {
        for (boolean sourceChanged : new boolean[] {true, false}) {
            ObjectNode input = baseRequest(); var bound = bound(input);
            bound.consumer().project(bound.token(), StrictJson.canonical(input));
            if (sourceChanged) object(input, "observation_context").put("snapshot_sha256", "f".repeat(64));
            else object(input, "snapshot").put("revision", bound.token().scope().frame().revision().add(BigInteger.ONE));
            assertThrows(ContractViolationException.class,
                () -> bound.consumer().project(bound.token(), StrictJson.canonical(input)));
            assertThrows(IllegalStateException.class, () -> bound.owner().requireCurrent(bound.token()));
            assertEquals(0, bound.owner().retainedEntryCount());
            assertEquals(sourceChanged ? ObservationReuse.Invalidation.SOURCE_CHANGED : ObservationReuse.Invalidation.FRAME_CHANGED,
                bound.owner().lastInvalidation());
        }
    }

    @Test void realUnknownResultIsPreservedButNotRetainedOrAutomaticallyRetried() throws IOException {
        ObjectNode input = baseRequest(); input.set("campaign_root", StrictJson.object().put("status", "unavailable"));
        var bound = bound(input); byte[] raw = StrictJson.canonical(input);
        var actual = bound.consumer().project(bound.token(), raw);
        assertInstanceOf(ObservationReuse.Unknown.class, actual.outcome());
        assertEquals(WarOutcomeStakesResult.Status.UNKNOWN, actual.outcome().value().status());
        assertArrayEquals(bound.original().project(raw), actual.outcome().value().toCanonicalBytes());
        assertEquals(0, bound.owner().retainedEntryCount());
        assertThrows(IllegalStateException.class, () -> bound.consumer().project(bound.token(), raw));
    }

    @Test void originalTypedFrameSeparatesActorEpisodeBridgeConnectionAndNativeRevision() throws IOException {
        for (String change : java.util.List.of("actor", "episode", "bridge", "connection", "native")) {
            ObjectNode input = baseRequest(); var bound = bound(input); ObjectNode snapshot = object(input, "snapshot");
            switch (change) {
                case "actor" -> object(snapshot, "played_character").put("character_id", bound.token().scope().frame().playedCharacterId() + 1);
                case "episode" -> snapshot.put("episode_run_id", "a-different-episode");
                case "bridge" -> object(snapshot, "diagnostics").put("bridge_pid", bound.token().scope().frame().bridgePid() + 1);
                case "connection" -> object(snapshot, "diagnostics").put("connection_generation", bound.token().scope().frame().connectionGeneration().add(BigInteger.ONE));
                case "native" -> {
                    BigInteger next = bound.token().scope().frame().nativeRevision().add(BigInteger.ONE);
                    snapshot.put("native_revision", next); snapshot.put("snapshot_id", "native:" + next);
                }
                default -> throw new IllegalArgumentException("test variant");
            }
            assertThrows(ContractViolationException.class,
                () -> bound.consumer().project(bound.token(), StrictJson.canonical(input)), change);
            assertThrows(IllegalStateException.class, () -> bound.owner().requireCurrent(bound.token()), change);
        }
    }

    @Test void originalWriterSubmissionAndActualPoststateVersionInvalidateProductionConsumer() throws IOException {
        ObjectNode input = baseRequest(); var bound = bound(input); byte[] raw = StrictJson.canonical(input);
        bound.consumer().project(bound.token(), raw);
        var oldVersion = bound.token().scope().writerVersion(); bound.owner().beforeSubmit(oldVersion);
        assertThrows(IllegalStateException.class, () -> bound.consumer().project(bound.token(), raw));
        var poststate = new ObservationReuse.WriterVersion(oldVersion.authorityId(), oldVersion.version().add(BigInteger.ONE));
        bound.owner().afterPoststateVersionChange(oldVersion, poststate);
        var freshToken = bound.owner().bindFresh(new ObservationReuse.Scope<>(bound.token().scope().source(),
            bound.token().scope().frame(), poststate));
        assertFalse(bound.consumer().project(freshToken, raw).reused());
    }

    @Test void completeOriginalProducerCorpusRetainsEveryResultAndInvalidContract() throws IOException {
        String resource = "/org/xar/ck3/control/warpolicy/war_outcome_stakes_golden_v1.jsonl";
        int rows = 0;
        try (InputStream stream = ScopedWarOutcomeStakesProjectorTest.class.getResourceAsStream(resource)) {
            if (stream == null) throw new IllegalStateException("original committed corpus missing");
            byte[] raw = stream.readNBytes(2 * 1024 * 1024 + 1);
            if (raw.length > 2 * 1024 * 1024) throw new IllegalStateException("original corpus budget exceeded");
            for (String line : new String(raw, StandardCharsets.UTF_8).split("\n")) {
                JsonNode vector = StrictJson.parse(line.getBytes(StandardCharsets.UTF_8));
                if (!vector.has("input_json")) continue;
                rows++;
                byte[] inputBytes = StrictJson.text(vector.get("input_json")).getBytes(StandardCharsets.UTF_8);
                if ("invalid_contract".equals(vector.path("expected_kind").textValue())) {
                    assertThrows(ContractViolationException.class, () -> {
                        ObjectNode input = StrictJson.object(StrictJson.parse(inputBytes), java.util.Set.of("schema", "war_id", "snapshot",
                            "campaign_root", "current_source_sha256", "observation_context"));
                        var binding = bound(input); binding.consumer().project(binding.token(), inputBytes);
                    }, "original vector " + rows);
                } else {
                    JsonNode parsed = StrictJson.parse(inputBytes);
                    if (!(parsed instanceof ObjectNode input)) throw new IllegalStateException("original request is not object");
                    var binding = bound(input);
                    var value = binding.consumer().project(binding.token(), inputBytes).outcome().value();
                    assertArrayEquals(StrictJson.canonical(vector.get("expected")), value.toCanonicalBytes(), "original vector " + rows);
                    assertArrayEquals(binding.original().project(inputBytes), value.toCanonicalBytes(), "original production vector " + rows);
                }
            }
        }
        assertTrue(rows > 0, "corpus cannot silently skip");
    }

    private static ObjectNode object(ObjectNode parent, String key) {
        if (parent.get(key) instanceof ObjectNode object) return object;
        throw new IllegalArgumentException("object absent: " + key);
    }
    private static ObjectNode baseRequest() throws IOException {
        String resource = "/org/xar/ck3/control/warpolicy/war_outcome_stakes_golden_v1.jsonl";
        try (InputStream stream = ScopedWarOutcomeStakesProjectorTest.class.getResourceAsStream(resource)) {
            if (stream == null) throw new IllegalStateException("original committed producer/oracle resource missing");
            byte[] raw = stream.readNBytes(2 * 1024 * 1024 + 1);
            if (raw.length > 2 * 1024 * 1024) throw new IllegalStateException("original corpus budget exceeded");
            for (String line : new String(raw, StandardCharsets.UTF_8).split("\n")) {
                JsonNode row = StrictJson.parse(line.getBytes(StandardCharsets.UTF_8));
                if ("result".equals(row.path("expected_kind").textValue())
                        && "test_actual_normalizer_cache_and_json_roundtrip_claim_defender".equals(row.path("test_method").textValue())) {
                    JsonNode input = StrictJson.parse(StrictJson.text(row.get("input_json")).getBytes(StandardCharsets.UTF_8));
                    if (input instanceof ObjectNode object) return object;
                    throw new IllegalStateException("original input object missing");
                }
            }
            throw new IllegalStateException("original successful producer vector missing");
        }
    }
}
