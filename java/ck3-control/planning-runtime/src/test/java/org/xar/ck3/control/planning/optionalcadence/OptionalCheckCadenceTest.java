package org.xar.ck3.control.planning.optionalcadence;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.EnumMap;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.optionalcadence.CadenceModels.*;

final class OptionalCheckCadenceTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String EPISODE = "cadence-java-test";
    private static final Frame ZERO = frame(0, 0);

    @Test
    void stateProducerCanonicalizesEveryRowAndRetainsTheOriginalIntegerAndOptionalTypes() throws IOException {
        BigInteger huge=BigInteger.ONE.shiftLeft(100);
        Frame frame=new Frame(EPISODE,huge,huge.add(BigInteger.ONE));
        State state=OptionalCheckCadence.record(State.empty(EPISODE),Domain.FEAST,frame,true);
        state=OptionalCheckCadence.deferCouncilTechnicalRead(state,frame,"D:/actual-read-unavailable.json");
        byte[] encoded=CadenceJson.writeState(state);
        assertArrayEquals(org.xar.ck3.control.contracts.StrictJson.canonical(JSON.readTree(encoded),65_536),encoded);
        assertEquals(state,CadenceJson.readState(encoded,EPISODE));
        assertTrue(new String(encoded,StandardCharsets.UTF_8).contains(huge.toString()));
        ObjectNode legacy=JSON.createObjectNode().put("schema",SCHEMA).put("episode_run_id",EPISODE);
        legacy.set("domains",JSON.readTree(encoded).get("domains"));
        byte[] originalOrder=JSON.writeValueAsBytes(legacy);
        assertFalse(java.util.Arrays.equals(originalOrder,encoded),"the original cadence encoder order reproduces worker19");
        assertEquals(state,CadenceJson.readState(originalOrder,EPISODE));
        assertArrayEquals(encoded,CadenceJson.writeState(CadenceJson.readState(originalOrder,EPISODE)));
    }

    @Test
    void unchangedProducerGoldenReplaysEveryTransitionAndSnapshot() throws IOException {
        JsonNode golden;
        try (InputStream stream = getClass().getResourceAsStream("/optionalcadence/golden.json")) {
            if (stream == null) { throw new IllegalStateException("real producer golden missing; capture was not executed"); }
            golden = JSON.readTree(stream);
        }
        assertEquals("xar.optional-check-cadence.golden.v1", golden.path("schema").textValue());
        assertEquals(0, golden.path("producer_exit_code").intValue());
        assertTrue(golden.path("producer").path("sha256").textValue().matches("[0-9a-f]{64}"));
        assertFalse(golden.path("machine_id").textValue().isBlank());
        int transitions = 0;
        for (JsonNode scenario : golden.path("cases")) {
            String episode = scenario.path("episode").textValue();
            State state = State.empty(episode);
            for (JsonNode step : scenario.path("steps")) {
                String currentEpisode = step.has("episode") ? step.get("episode").textValue() : episode;
                Frame current = new Frame(currentEpisode, step.get("date_raw").bigIntegerValue(),
                        step.get("native_revision").bigIntegerValue());
                state = OptionalCheckCadence.forEpisode(state, currentEpisode);
                switch (step.get("operation").textValue()) {
                    case "record" -> state = OptionalCheckCadence.record(state,
                            Domain.fromWire(step.get("domain").textValue()), current, step.get("actual_action").booleanValue());
                    case "defer_council" -> state = OptionalCheckCadence.deferCouncilTechnicalRead(state,
                            current, step.get("evidence_path").textValue());
                    case "requalify" -> {
                        Requalification result = OptionalCheckCadence.requalifyLifestyleFrontierOnce(state,
                                current, step.get("native_catalogue").textValue());
                        assertEquals(step.get("expected_changed").booleanValue(), result.changed());
                        state = result.state();
                    }
                    case "deferred" -> assertEquals(step.get("expected_deferred"), JSON.readTree(
                            CadenceJson.writeDeferred(OptionalCheckCadence.deferred(state,
                                    Domain.fromWire(step.get("domain").textValue()), current))));
                    case "action_recorded" -> assertEquals(step.get("expected_action_recorded").booleanValue(),
                            OptionalCheckCadence.actionRecorded(state,
                                    Domain.fromWire(step.get("domain").textValue()), current));
                    default -> fail("unknown golden operation");
                }
                assertEquals(step.get("expected_state"), JSON.readTree(CadenceJson.writeState(state)),
                        scenario.get("name").textValue() + " transition " + transitions);
                assertEquals(state, CadenceJson.readState(CadenceJson.writeState(state), currentEpisode));
                transitions++;
            }
        }
        assertTrue(transitions >= 40, "the actual producer capture must cover all four scenarios");
        for (JsonNode example : golden.path("snapshot_cases")) {
            Optional<Frame> result = CadenceJson.readFrame(JSON.writeValueAsBytes(example.get("snapshot")));
            JsonNode expected = example.get("expected_frame");
            if (expected.isNull()) { assertTrue(result.isEmpty()); }
            else {
                Frame value = result.orElseThrow();
                assertEquals(expected.get(0).textValue(), value.episodeRunId());
                assertEquals(expected.get(1).bigIntegerValue(), value.dateRaw());
                assertEquals(expected.get(2).bigIntegerValue(), value.nativeRevision());
            }
        }
    }

    @Test
    void exactThirdMissTriggersThirtyDaysAndIndependentDomains() {
        State state = threeMisses(Domain.COUNCIL);
        Row council = state.row(Domain.COUNCIL);
        assertEquals(0, council.consecutiveNoAction());
        assertEquals(BigInteger.valueOf(768), council.nextDueDateRaw().orElseThrow());
        assertEquals(BigInteger.valueOf(29), OptionalCheckCadence.deferred(state, Domain.COUNCIL, frame(72, 3))
                .orElseThrow().remainingGameDays());
        assertEquals(BigInteger.ONE, OptionalCheckCadence.deferred(state, Domain.COUNCIL, frame(767, 4))
                .orElseThrow().remainingGameDays());
        assertTrue(OptionalCheckCadence.deferred(state, Domain.COUNCIL, frame(768, 4)).isEmpty());
        for (Domain domain : Domain.values()) {
            if (domain != Domain.COUNCIL) { assertEquals(Row.empty(), state.row(domain)); }
        }
    }

    @Test
    void sameFrameDeduplicatesButDifferentNativeRevisionCounts() {
        State once = OptionalCheckCadence.record(State.empty(EPISODE), Domain.CROWN, ZERO, false);
        assertEquals(once, OptionalCheckCadence.record(once, Domain.CROWN, ZERO, false));
        State next = OptionalCheckCadence.record(once, Domain.CROWN, frame(0, 1), false);
        assertEquals(2, next.row(Domain.CROWN).consecutiveNoAction());
    }

    @Test
    void actualActionResetsCooldownAndObserverDoesNotCountSameFrameAgain() {
        State prior = threeMisses(Domain.CONSTRUCTION);
        Frame current = frame(72, 4);
        State action = OptionalCheckCadence.record(prior, Domain.CONSTRUCTION, current, true);
        assertTrue(action.row(Domain.CONSTRUCTION).nextDueDateRaw().isEmpty());
        assertTrue(OptionalCheckCadence.actionRecorded(action, Domain.CONSTRUCTION, current));
        assertFalse(OptionalCheckCadence.actionRecorded(action, Domain.CONSTRUCTION, frame(72, 5)));
        assertEquals(action, OptionalCheckCadence.record(action, Domain.CONSTRUCTION, current, true));
        assertEquals(action, OptionalCheckCadence.observeRead(action, Domain.CONSTRUCTION, current,
                ReadCompletion.COMPLETE_NO_ACTION));
    }

    @Test
    void unknownReadsNeverIncrementAndUnknownOrPendingReceiptsNeverDefer() {
        State state = threeMisses(Domain.LIFESTYLE);
        Frame current = frame(72, 4);
        assertEquals(state, OptionalCheckCadence.observeRead(state, Domain.LIFESTYLE, current,
                ReadCompletion.INCOMPLETE_OR_UNKNOWN));
        assertInstanceOf(CheckDeferred.class,
                OptionalCheckCadence.gate(state, Domain.LIFESTYLE, Optional.of(current), PendingState.ABSENT));
        assertEquals(new CheckRequired(CheckReason.PENDING_RECEIPT),
                OptionalCheckCadence.gate(state, Domain.LIFESTYLE, Optional.of(current), PendingState.PENDING));
        assertEquals(new CheckRequired(CheckReason.UNKNOWN_RECEIPT),
                OptionalCheckCadence.gate(state, Domain.LIFESTYLE, Optional.of(current), PendingState.UNKNOWN));
        assertEquals(new CheckRequired(CheckReason.FRAME_UNAVAILABLE),
                OptionalCheckCadence.gate(state, Domain.LIFESTYLE, Optional.empty(), PendingState.ABSENT));
    }

    @Test
    void technicalDeferPreservesCountersAndEvidenceSameFrameUntilDue() {
        State state = OptionalCheckCadence.record(State.empty(EPISODE), Domain.COUNCIL, ZERO, false);
        Frame current = frame(24, 1);
        State deferred = OptionalCheckCadence.deferCouncilTechnicalRead(state, current, "evidence/原生.json");
        assertEquals(1, deferred.row(Domain.COUNCIL).consecutiveNoAction());
        assertTrue(deferred.row(Domain.COUNCIL).lastActualActionFrame().isEmpty());
        assertEquals(deferred, OptionalCheckCadence.deferCouncilTechnicalRead(deferred, current, "changed.json"));
        assertEquals(deferred, OptionalCheckCadence.record(deferred, Domain.COUNCIL, current, false));
        assertEquals(DeferStatus.TECHNICAL_READ_UNAVAILABLE,
                OptionalCheckCadence.deferred(deferred, Domain.COUNCIL, frame(48, 2)).orElseThrow().status());
        State action = OptionalCheckCadence.record(deferred, Domain.COUNCIL, current, true);
        assertTrue(action.row(Domain.COUNCIL).technicalDefer().isEmpty());
        assertTrue(action.row(Domain.COUNCIL).nextDueDateRaw().isEmpty());
    }

    @Test
    void catalogueRequalificationIsScopedAndRetainsActualActionMarker() {
        State state = threeMisses(Domain.LIFESTYLE);
        for (int index = 0; index < 3; index++) {
            state = OptionalCheckCadence.record(state, Domain.COUNCIL, frame(index * 24L, index), false);
        }
        Frame current = frame(72, 4);
        Requalification first = OptionalCheckCadence.requalifyLifestyleFrontierOnce(state, current, "catalogue-v2");
        assertTrue(first.changed());
        assertEquals(state.row(Domain.COUNCIL), first.state().row(Domain.COUNCIL));
        assertTrue(first.state().row(Domain.LIFESTYLE).lastCheckFrame().isEmpty());
        assertTrue(first.state().row(Domain.LIFESTYLE).lastActualActionFrame().isEmpty());
        State acted = OptionalCheckCadence.record(first.state(), Domain.LIFESTYLE, current, true);
        Requalification unchanged = OptionalCheckCadence.requalifyLifestyleFrontierOnce(acted, current, "catalogue-v2");
        assertFalse(unchanged.changed());
        Requalification upgraded = OptionalCheckCadence.requalifyLifestyleFrontierOnce(acted, current, "catalogue-v3");
        assertTrue(upgraded.changed());
        assertEquals(Optional.of(current.marker()), upgraded.state().row(Domain.LIFESTYLE).lastActualActionFrame());
    }

    @Test
    void episodeResetAndArbitraryPrecisionNeverReuseAnotherEpisodeCooldown() {
        State prior = threeMisses(Domain.FEAST);
        Frame fresh = new Frame("fresh", BigInteger.ZERO, BigInteger.ZERO);
        assertTrue(OptionalCheckCadence.deferred(prior, Domain.FEAST, fresh).isEmpty());
        State reset = OptionalCheckCadence.record(prior, Domain.FEAST, fresh, false);
        assertEquals("fresh", reset.episodeRunId());
        assertEquals(1, reset.row(Domain.FEAST).consecutiveNoAction());
        BigInteger huge = BigInteger.ONE.shiftLeft(100);
        State state = State.empty(EPISODE);
        for (int i = 0; i < 3; i++) {
            state = OptionalCheckCadence.record(state, Domain.FEAST,
                    new Frame(EPISODE, huge.add(BigInteger.valueOf(i)), huge), false);
        }
        assertEquals(huge.add(BigInteger.valueOf(722)), state.row(Domain.FEAST).nextDueDateRaw().orElseThrow());
        assertEquals(state, CadenceJson.readState(CadenceJson.writeState(state), EPISODE));
    }

    @Test
    void cooldownRejectsEarlyRecordingButPermitsTheExactDueDate() {
        State state = threeMisses(Domain.RANSOM);
        assertThrows(IllegalArgumentException.class,
                () -> OptionalCheckCadence.record(state, Domain.RANSOM, frame(767, 4), false));
        State next = OptionalCheckCadence.record(state, Domain.RANSOM, frame(768, 4), false);
        assertEquals(1, next.row(Domain.RANSOM).consecutiveNoAction());
        assertTrue(next.row(Domain.RANSOM).nextDueDateRaw().isEmpty());
    }

    @Test
    void typedModelsRejectNullsNegativeMarkersInvalidCountsAndMutableMaps() {
        assertThrows(IllegalArgumentException.class, () -> new Frame("", BigInteger.ZERO, BigInteger.ZERO));
        assertThrows(IllegalArgumentException.class, () -> frame(-1, 0));
        assertThrows(IllegalArgumentException.class, () -> frame(0, -1));
        assertThrows(IllegalArgumentException.class,
                () -> new Frame(String.valueOf((char) 0xd800), BigInteger.ZERO, BigInteger.ZERO));
        assertThrows(IllegalArgumentException.class, () -> new Row(3, Optional.empty(), Optional.empty(),
                Optional.empty(), Optional.empty(), Optional.empty()));
        assertThrows(IllegalArgumentException.class, () -> Domain.fromWire("unknown"));
        assertThrows(IllegalArgumentException.class, () -> new State(EPISODE, new EnumMap<>(Domain.class)));
        State state = State.empty(EPISODE);
        assertThrows(UnsupportedOperationException.class, () -> state.domains().put(Domain.FEAST, Row.empty()));
    }

    @Test
    void strictStateCodecRejectsEveryMissingRequiredFieldAndUnknownFields() throws IOException {
        ObjectNode valid = stateNode();
        for (String field : new String[]{"schema", "episode_run_id", "domains"}) {
            ObjectNode broken = valid.deepCopy();
            broken.remove(field);
            reject(broken);
        }
        for (String field : new String[]{"consecutive_no_action", "next_due_date_raw", "last_check_frame", "last_actual_action_frame"}) {
            ObjectNode broken = valid.deepCopy();
            ((ObjectNode) broken.path("domains").path("council")).remove(field);
            reject(broken);
        }
        ObjectNode rootExtra = valid.deepCopy(); rootExtra.put("typo", 1); reject(rootExtra);
        ObjectNode rowExtra = valid.deepCopy(); ((ObjectNode) rowExtra.path("domains").path("council")).put("typo", 1); reject(rowExtra);
        ObjectNode missingDomain = valid.deepCopy(); ((ObjectNode) missingDomain.path("domains")).remove("crown"); reject(missingDomain);
        ObjectNode extraDomain = valid.deepCopy(); ((ObjectNode) extraDomain.path("domains")).set("unknown", JSON.createObjectNode()); reject(extraDomain);
    }

    @Test
    void integerTokensRejectBooleansFloatsStringsOverflowCountsAndWrongMarkerShapes() throws IOException {
        for (String token : new String[]{"true", "false", "0.0", "1e0", "\"0\"", "null", "-1", "3", "18446744073709551616"}) {
            ObjectNode node = stateNode();
            ((ObjectNode) node.path("domains").path("council")).set("consecutive_no_action", JSON.readTree(token));
            reject(node);
        }
        for (String token : new String[]{"true", "0.0", "\"0\"", "[]", "{}"}) {
            ObjectNode node = stateNode();
            ((ObjectNode) node.path("domains").path("council")).set("next_due_date_raw", JSON.readTree(token));
            reject(node);
        }
        for (String marker : new String[]{"[]", "[0]", "[0,0,0]", "[true,0]", "[0,0.0]", "[-1,0]", "{}"}) {
            ObjectNode node = stateNode();
            ((ObjectNode) node.path("domains").path("council")).set("last_check_frame", JSON.readTree(marker));
            reject(node);
        }
    }

    @Test
    void optionalAbsentIsDistinctFromNullAndTechnicalBranchCannotInventActionCredit() throws IOException {
        ObjectNode valid = stateNode();
        assertEquals(State.empty(EPISODE), CadenceJson.readState(JSON.writeValueAsBytes(valid), EPISODE));
        for (String field : new String[]{"native_catalogue", "technical_defer"}) {
            ObjectNode bad = valid.deepCopy(); ((ObjectNode) bad.path("domains").path("council")).putNull(field); reject(bad);
        }
        State deferred = OptionalCheckCadence.deferCouncilTechnicalRead(State.empty(EPISODE), ZERO, "evidence.json");
        for (String field : new String[]{"business_submission", "no_action_counter_incremented"}) {
            ObjectNode bad = (ObjectNode) JSON.readTree(CadenceJson.writeState(deferred));
            ((ObjectNode) bad.path("domains").path("council").path("technical_defer")).put(field, true); reject(bad);
        }
        ObjectNode missingDue = (ObjectNode) JSON.readTree(CadenceJson.writeState(deferred));
        ((ObjectNode) missingDue.path("domains").path("council")).putNull("next_due_date_raw"); reject(missingDue);
        ObjectNode wrongFrame = (ObjectNode) JSON.readTree(CadenceJson.writeState(deferred));
        ((ObjectNode) wrongFrame.path("domains").path("council")).set("last_check_frame", JSON.readTree("[0,1]"));
        reject(wrongFrame);
    }

    @Test
    void strictInputRejectsDuplicatesTrailingJsonInvalidUtf8AndOversizedData() {
        assertThrows(IllegalArgumentException.class,
                () -> CadenceJson.readState(bytes("{\"schema\":\"a\",\"schema\":\"b\"}"), EPISODE));
        assertThrows(IllegalArgumentException.class,
                () -> CadenceJson.readState(bytes(new String(CadenceJson.writeState(State.empty(EPISODE)), StandardCharsets.UTF_8) + " {}"), EPISODE));
        assertThrows(IllegalArgumentException.class, () -> CadenceJson.readState(new byte[]{(byte) 0xc3, 0x28}, EPISODE));
        assertThrows(IllegalArgumentException.class, () -> CadenceJson.readState(new byte[65_537], EPISODE));
    }

    @Test
    void outputByteBudgetRejectsCombinedTextAndCountsUtf8BytesBeforePublication() {
        String longEpisode = "e".repeat(32_768);
        Frame frame = new Frame(longEpisode, BigInteger.ZERO, BigInteger.ZERO);
        State combined = OptionalCheckCadence.deferCouncilTechnicalRead(State.empty(longEpisode), frame,
                "p".repeat(32_768));
        assertThrows(IllegalArgumentException.class, () -> CadenceJson.writeState(combined));

        State utf8 = OptionalCheckCadence.deferCouncilTechnicalRead(State.empty(EPISODE), ZERO,
                "汉".repeat(25_000));
        assertThrows(IllegalArgumentException.class, () -> CadenceJson.writeState(utf8));
        Optional<Deferred> utf8Deferred = OptionalCheckCadence.deferred(utf8, Domain.COUNCIL, frame(1, 1));
        assertThrows(IllegalArgumentException.class, () -> CadenceJson.writeDeferred(utf8Deferred));

        State bounded = OptionalCheckCadence.deferCouncilTechnicalRead(State.empty(EPISODE), ZERO,
                "汉".repeat(16_000));
        byte[] encoded = CadenceJson.writeState(bounded);
        assertTrue(encoded.length < 65_536);
        assertEquals(bounded, CadenceJson.readState(encoded, EPISODE));
    }

    @Test
    void extensibleSnapshotsRequirePausedExactIntegersAndDoNotGrantSourceQualification() {
        assertEquals(Optional.of(ZERO), CadenceJson.readFrame(bytes("{\"episode_run_id\":\"cadence-java-test\",\"date_raw\":0,\"native_revision\":0,\"paused\":true,\"other\":[]}")));
        for (String snapshot : new String[]{"{}", "[]", "null",
                "{\"episode_run_id\":\"e\",\"date_raw\":true,\"native_revision\":0,\"paused\":true}",
                "{\"episode_run_id\":\"e\",\"date_raw\":0,\"native_revision\":0.0,\"paused\":true}",
                "{\"episode_run_id\":\"e\",\"date_raw\":0,\"native_revision\":0,\"paused\":1}",
                "{\"episode_run_id\":\"e\",\"date_raw\":-1,\"native_revision\":0,\"paused\":true}"}) {
            assertTrue(CadenceJson.readFrame(bytes(snapshot)).isEmpty());
        }
        assertEquals(State.empty("new-episode"), CadenceJson.readState(
                bytes("{\"schema\":\"xar.optional-check-cadence.v1\",\"episode_run_id\":\"old\",\"domains\":null}"), "new-episode"));
    }

    private static Frame frame(long date, long revision) {
        return new Frame(EPISODE, BigInteger.valueOf(date), BigInteger.valueOf(revision));
    }
    private static State threeMisses(Domain domain) {
        State state = State.empty(EPISODE);
        for (int i = 0; i < 3; i++) { state = OptionalCheckCadence.record(state, domain, frame(i * 24L, i), false); }
        return state;
    }
    private static ObjectNode stateNode() throws IOException {
        return (ObjectNode) JSON.readTree(CadenceJson.writeState(State.empty(EPISODE)));
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static void reject(JsonNode value) throws IOException {
        byte[] bytes = JSON.writeValueAsBytes(value);
        assertThrows(IllegalArgumentException.class, () -> CadenceJson.readState(bytes, EPISODE));
    }
}
