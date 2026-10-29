package org.xar.ck3.control.g2.m6;

import java.nio.charset.StandardCharsets;
import java.io.IOException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.g2.m6.SwayHistoricalImport.*;

final class SwayHistoricalImportTest {
    private static final String EXE = M6SourceProducer.EXE;
    private static final String TUPLE = "\"actor_character_id\":10,\"target_character_id\":20,"
            + "\"scheme_instance_id\":16777217,\"scheme_instance_generation\":1";

    private static String original(String action, String extra) {
        return "{\"status\":\"applied\",\"postcondition_verified\":true,\"action_id\":\"" + action
                + "\",\"actor_character_id\":10,\"target_character_id\":20,\"native_receipt\":{"
                + "\"schema\":\"active-scheme-sway-formal-private-v1\",\"stage\":\"applied\","
                + "\"postcondition_verified\":true,\"action_id\":\"" + action + "\","
                + "\"scheme_instance_id\":16777217,\"scheme_instance_generation\":1,"
                + "\"exact_ck3_build\":\"1.20.0.4\",\"exe_sha256\":\"" + EXE + "\"}" + extra + "}";
    }

    private static ProjectionJson json(String raw) {
        return ProjectionJson.object(raw.getBytes(StandardCharsets.UTF_8), MAX_BYTES);
    }

    @Test void retainsNonemptyOriginalHistoryAndConsumptionWithoutInventingCurrentIdentity() {
        String first = "{" + TUPLE + ",\"next_turn_consumed\":true,"
                + "\"source_native_revision\":9007199254740993,\"source_date_raw\":100,"
                + "\"following_native_revision\":9007199254740994,\"following_date_raw\":124,"
                + "\"incremental_named_gain_observed\":true,\"tracked_instance_active\":true,"
                + "\"scheme_sway_opinion\":{\"observed\":true,\"present\":true,\"value\":5},"
                + "\"previous_scheme_sway_opinion\":{\"observed\":true,\"present\":false,\"value\":null}}";
        String raw = original("a", ",\"next_turn_consumed\":true,\"first_named_gain_intervention\":"
                + first + ",\"terminal_intervention\":null,\"previous_interventions\":["
                + original("b", ",\"next_turn_consumed\":false") + "]");
        History history = parse(json(raw));
        assertArrayEquals(raw.getBytes(StandardCharsets.UTF_8), history.originalResolved().bytes());
        assertTrue(history.startConsumption().markedConsumed());
        Retained retained = assertInstanceOf(Retained.class, history.plane(Plane.FIRST_GAIN));
        assertTrue(retained.consumption().markedConsumed());
        assertEquals("9007199254740993", retained.originalSource().orElseThrow().nativeRevision().toString());
        assertEquals("9007199254740994", retained.consumption().following().orElseThrow().nativeRevision().toString());
        assertInstanceOf(Missing.class, history.plane(Plane.PHASE));
        assertInstanceOf(ExplicitNull.class, history.plane(Plane.TERMINAL));
        assertEquals(2, flatten(history).size());
        var episode = identityOnlyEpisode(history);
        assertEquals(history.identity(), episode.identity());
        assertTrue(episode.start().isEmpty());
        assertTrue(episode.firstNamedGain().isEmpty());
        assertTrue(episode.terminal().isEmpty());
    }

    @Test void distinguishesAbsentPreviousFromPresentEmptyAndRejectsNullOrRepeatedActions() {
        assertTrue(parse(json(original("a", ""))).previous().isEmpty());
        assertTrue(parse(json(original("a", ",\"previous_interventions\":[]")))
                .previous().orElseThrow().isEmpty());
        assertThrows(IllegalArgumentException.class, () -> parse(json(original("a",
                ",\"previous_interventions\":null"))));
        assertThrows(IllegalArgumentException.class, () -> parse(json(original("a",
                ",\"previous_interventions\":[" + original("a", "") + "]"))));
    }

    @Test void rejectsBooleanAndIntegerTypeConfusionAndCrossInstancePlane() {
        assertThrows(IllegalArgumentException.class, () -> parse(json(original("a",
                ",\"next_turn_consumed\":1"))));
        assertThrows(IllegalArgumentException.class, () -> parse(json(original("a",
                ",\"phase_intervention\":{" + TUPLE + ",\"source_native_revision\":true,\"source_date_raw\":1}"))));
        assertThrows(IllegalArgumentException.class, () -> parse(json(original("a",
                ",\"material_intervention\":{" + TUPLE.replace("character_id\":20", "character_id\":21") + "}"))));
        assertThrows(IllegalArgumentException.class, () -> parse(json(original("a",
                ",\"following_native_revision\":10"))));
    }

    @Test void retainedAttributedLabelStaysHistoricalAndNeverBecomesTerminalProof() {
        History history = parse(json(original("a", ",\"terminal_intervention\":{" + TUPLE
                + ",\"next_turn_consumed\":true,\"instance_terminal_outcome_observed\":true,"
                + "\"terminal_cause_observed\":true,\"terminal_cause\":\"authored_sway_complete_100_source\"}")));
        assertInstanceOf(Retained.class, history.plane(Plane.TERMINAL));
        assertTrue(identityOnlyEpisode(history).terminal().isEmpty());
    }

    @Test void stopRetainsIndependentSubmissionAndRequiresOriginalActionAndFullInstance() {
        String stop = "{\"action_id\":\"stop-sway-0123456789abcdef0123456789abcdef\","
                + "\"original_action_id\":\"a\"," + TUPLE
                + ",\"postcondition_verified\":false,\"status\":\"stop_submission_unresolved\"}";
        History history = parse(json(original("a", ",\"stop_intervention\":" + stop)));
        Retained retained = assertInstanceOf(Retained.class, history.plane(Plane.STOP));
        assertArrayEquals(stop.getBytes(StandardCharsets.UTF_8), retained.original().bytes());
        assertTrue(identityOnlyEpisode(history).terminal().isEmpty());
        for (String accepted : new String[] {"stop-sway-Scoped_09-X", "stop-sway-" + "a".repeat(54)}) {
            History imported = parse(json(original("a", ",\"stop_intervention\":"
                    + stop.replace("stop-sway-0123456789abcdef0123456789abcdef", accepted))));
            assertInstanceOf(Retained.class, imported.plane(Plane.STOP));
            assertTrue(identityOnlyEpisode(imported).terminal().isEmpty());
        }
        for (String wrong : new String[] {
                stop.replace("\"original_action_id\":\"a\"", "\"original_action_id\":\"b\""),
                stop.replace("stop-sway-0123456789abcdef0123456789abcdef", "a"),
                stop.replace("stop-sway-0123456789abcdef0123456789abcdef", "stop-sway-" + "a".repeat(55)),
                stop.replace("stop-sway-0123456789abcdef0123456789abcdef", "stop-sway-非法"),
                stop.replace("stop-sway-0123456789abcdef0123456789abcdef", "stop-sway-invalid.id"),
                stop.replace("\"scheme_instance_id\":16777217", "\"scheme_instance_id\":16777218")}) {
            assertThrows(IllegalArgumentException.class, () -> parse(json(original("a",
                    ",\"stop_intervention\":" + wrong))));
        }
        assertThrows(IllegalArgumentException.class, () -> parse(json(original("a",
                ",\"phase_intervention\":{" + TUPLE + ",\"action_id\":\"b\"}"))));
    }

    @Test void realMixedBuildHistoryAndMissingCaptureEpochRemainHistoricalOnly()
            throws IOException, NoSuchAlgorithmException {
        byte[] original;
        try (var stream = getClass().getResourceAsStream("/m6native/legacy-sway-source05.json")) {
            assertNotNull(stream, "required source-bound real historical fixture");
            original = stream.readAllBytes();
        }
        assertEquals("6f1da9ee2c0e00839497a650cbcfaba527807342e85cce29d8a357344f55aad9",
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        var root = StrictJson.parse(original, MAX_BYTES);
        var resolved = root.get("resolved");
        assertEquals("1.20.0.3", resolved.get("native_receipt").get("exact_ck3_build").textValue());
        assertEquals("1.20.0.4", resolved.get("latest_instance_observation")
                .get("exact_ck3_build").textValue());
        History history = parse(json(resolved.toString()));
        assertEquals(134217986L, history.identity().schemeInstanceId());
        assertTrue(history.startConsumption().markedConsumed());
        assertTrue(identityOnlyEpisode(history).start().isEmpty());
        assertTrue(identityOnlyEpisode(history).terminal().isEmpty());
        var noEpoch = resolved.deepCopy();
        ((com.fasterxml.jackson.databind.node.ObjectNode) noEpoch).remove("pre_capture_epoch");
        assertEquals(history.identity(), parse(json(noEpoch.toString())).identity());
    }

    @Test void recoveredAppliedObservationUsesTheSameOriginalValidatorAndAllowsZeroInstance() {
        String raw = "{\"status\":\"applied\",\"postcondition_verified\":true,\"action_id\":\"a\","
                + "\"actor_character_id\":10,\"target_character_id\":20,\"native_receipt\":null,"
                + "\"applied_instance_observation\":{\"scheme_instance_id\":0,"
                + "\"scheme_instance_generation\":0,\"source_read\":{\"exact_ck3_build\":\"1.20.0.4\","
                + "\"exe_sha256\":\"" + EXE + "\"}}}";
        History history = parse(json(raw));
        assertEquals(0L, history.identity().schemeInstanceId());
        assertTrue(identityOnlyEpisode(history).start().isEmpty());
        assertThrows(IllegalArgumentException.class,
                () -> parse(json(raw.replace("1.20.0.4", "1.20.0.3"))));
    }
}
