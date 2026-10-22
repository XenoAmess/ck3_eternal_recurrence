package org.xar.ck3.control.diagnostics;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.diagnostics.ClockFailureAssessment.*;
import org.xar.ck3.control.diagnostics.NativeClockFailureObservation.SourcePin;

class NativeClockFailureTest {
    private static final String ORIGINAL_SHA = "a29abe49623a8da965af385526b2b9a22ad0ed30d321d0ac340d4149fc74d9de";
    private static final SourcePin SOURCE = new SourcePin(ORIGINAL_SHA, 11558);

    private static byte[] fixture() throws IOException {
        try (InputStream stream = NativeClockFailureTest.class.getResourceAsStream("/native-clock-failure-n46-11558.normalized.json")) {
            assertNotNull(stream, "portable real-failure projection must be present");
            return stream.readAllBytes();
        }
    }

    private static ObjectNode golden() throws IOException {
        JsonNode parsed = StrictJson.parse(fixture());
        assertTrue(parsed instanceof ObjectNode);
        return (ObjectNode) parsed;
    }

    private static ObjectNode at(ObjectNode row, String pointer) {
        JsonNode value = row.at(pointer);
        assertTrue(value instanceof ObjectNode, pointer);
        return (ObjectNode) value;
    }

    private static byte[] raw(ObjectNode row) { return row.toString().getBytes(StandardCharsets.UTF_8); }
    private static NativeClockFailureObservation parse(ObjectNode row) { return NativeClockFailureCodec.parse(raw(row), SOURCE); }
    private static ClockFailureAssessment classify(ObjectNode row) { return NativeClockFailureClassifier.classify(parse(row), 5000); }
    private static void reject(ObjectNode row) { assertThrows(ContractViolationException.class, () -> parse(row)); }
    private static void rejectLiteralToken(ObjectNode row, String parentPointer, String key, String token) {
        // Preserve the wire token: a BigDecimal tree roundtrip can render 1.0 as integer text 1.
        String marker = "__native_clock_invalid_literal__";
        at(row, parentPointer).put(key, marker);
        String json = row.toString();
        String quotedMarker = "\"" + marker + "\"";
        assertEquals(json.indexOf(quotedMarker), json.lastIndexOf(quotedMarker), "unique test token marker");
        byte[] exactWire = json.replace(quotedMarker, token).getBytes(StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class, () -> NativeClockFailureCodec.parse(exactWire, SOURCE), token);
    }
    private static void noAuthority(ClockFailureAssessment value) {
        assertEquals(0, value.credit()); assertTrue(value.neverReplay()); assertFalse(value.resumeAuthorized());
        assertEquals(PermanentDeadlock.NOT_DETERMINABLE, value.permanentDeadlock());
    }

    @Test
    void realN46FailureRetainsTransportOwnerAckAndUnknownPauseAsDifferentFacts() throws IOException {
        NativeClockFailureObservation input = NativeClockFailureCodec.parse(fixture(), SOURCE);
        assertEquals("xenoamess-full-tower-eb9d2c1186", input.machineId());
        assertEquals(53279400, input.starting().dateRaw()); assertEquals(53279400, input.waitFinal().dateRaw());
        assertEquals(53279424, input.targetDateRaw()); assertTrue(input.starting().paused()); assertFalse(input.waitFinal().paused());
        assertEquals(122, input.progress().heartbeatEvents()); assertEquals("371768", input.progress().owner().last().decimal());
        assertEquals("371770", input.cleanupTail().owner().pumpEpochs().decimal());
        assertNull(input.cleanupTail().pausedAfterCleanup());
        ClockFailureAssessment result = NativeClockFailureClassifier.classify(input, 5000);
        assertEquals(TransportAlive.ALIVE_DURING_WAIT, result.transportAlive());
        assertEquals(OwnerProgress.STALLED_AT_WAIT_END_WITH_TAIL_PROGRESS, result.ownerProgress());
        assertEquals(PauseAcknowledgements.ALL_SUBMITTED, result.pauseAcknowledgements());
        assertEquals(PauseObserved.UNOBSERVED_AFTER_CLEANUP, result.pauseObserved());
        assertEquals(Long.valueOf(23523), result.trailingOwnerUnchangedMillis());
        assertFalse(result.observerReadingAtWaitEnd()); noAuthority(result);
    }

    @Test
    void newSchemaCanonicalRoundtripKeepsUint64UnicodeAndExplicitNull() throws IOException {
        ObjectNode row = golden(); row.put("machine_id", "机器😀");
        at(row, "/cleanup_tail/heartbeat").put("monotonic_ms", "18446744073709551615");
        NativeClockFailureObservation first = parse(row);
        byte[] encoded = NativeClockFailureCodec.encode(first);
        assertTrue(encoded.length <= NativeClockFailureCodec.MAX_BYTES);
        assertTrue(new String(encoded, StandardCharsets.UTF_8).contains("机器😀"));
        assertTrue(new String(encoded, StandardCharsets.UTF_8).contains("\"paused_after_cleanup\":null"));
        NativeClockFailureObservation second = NativeClockFailureCodec.parse(encoded, SOURCE);
        assertEquals(first, second); assertArrayEquals(encoded, NativeClockFailureCodec.encode(second));
    }

    @Test
    void numericIdentitiesRejectBoolFloatStringNullAndUnsafeIntegers() throws IOException {
        for (String invalid : new String[] {"true", "50688.0", "1e2", "\"50688\"", "null", "0", "-1", "4294967296"}) {
            rejectLiteralToken(golden(), "/wait_identity/bridge", "bridge_pid", invalid);
        }
        for (String invalid : new String[] {"true", "1.0", "\"1\"", "null", "9007199254740992"}) {
            rejectLiteralToken(golden(), "/starting/bridge", "connection_generation", invalid);
        }
    }

    @Test
    void uint64DomainRequiresCanonicalStringsAndDoesNotAddNumericAliases() throws IOException {
        for (String invalid : new String[] {"371768", "true", "371768.0", "null", "\"0371768\"", "\"-1\"", "\"18446744073709551616\""}) {
            rejectLiteralToken(golden(), "/progress/owner", "last", invalid);
        }
        for (String invalid : new String[] {"true", "6817.0", "\"6817\"", "-1"}) {
            rejectLiteralToken(golden(), "/progress/owner", "last_change_ms", invalid);
        }
    }

    @Test
    void requiredFieldsRejectMissingNullArraysAndUnknownKeys() throws IOException {
        for (String key : new String[] {"source", "wait_identity", "starting", "wait_final", "progress", "cleanup_tail"}) {
            ObjectNode missing = golden(); missing.remove(key); reject(missing);
            ObjectNode nullValue = golden(); nullValue.putNull(key); reject(nullValue);
            ObjectNode array = golden(); array.putArray(key); reject(array);
        }
        ObjectNode unknown = golden(); unknown.put("retry_allowed", true); reject(unknown);
        ObjectNode nested = golden(); at(nested, "/progress/owner").put("last_known", 1); reject(nested);
        ObjectNode missingTime = golden(); at(missingTime, "/progress/owner").remove("last_change_ms"); reject(missingTime);
    }

    @Test
    void parserRejectsDuplicateTrailingOversizedAndMalformedUtf8() throws IOException {
        String text = new String(fixture(), StandardCharsets.UTF_8);
        String duplicate = text.replace("\"target_date_raw\": 53279424", "\"target_date_raw\": 1, \"target_date_raw\": 53279424");
        assertThrows(ContractViolationException.class, () -> NativeClockFailureCodec.parse(duplicate.getBytes(StandardCharsets.UTF_8), SOURCE));
        assertThrows(ContractViolationException.class, () -> NativeClockFailureCodec.parse((text + " {}").getBytes(StandardCharsets.UTF_8), SOURCE));
        assertThrows(ContractViolationException.class, () -> NativeClockFailureCodec.parse(new byte[NativeClockFailureCodec.MAX_BYTES + 1], SOURCE));
        assertThrows(ContractViolationException.class, () -> NativeClockFailureCodec.parse(new byte[] {(byte) 0xc3, 0x28}, SOURCE));
    }

    @Test
    void sourcePinsSchemaAndConservativeAuthorityAreMandatory() throws IOException {
        byte[] fixture = fixture();
        assertThrows(ContractViolationException.class, () -> NativeClockFailureCodec.parse(fixture, new SourcePin("ab".repeat(32), 11558)));
        assertThrows(ContractViolationException.class, () -> NativeClockFailureCodec.parse(fixture, new SourcePin(ORIGINAL_SHA, 11559)));
        assertThrows(ContractViolationException.class, () -> NativeClockFailureCodec.parse(fixture, null));
        ObjectNode schema = golden(); schema.put("schema", "xar.exact-day-clock-failure.v2"); reject(schema);
        ObjectNode credit = golden(); credit.put("credit", 1); reject(credit);
        ObjectNode replay = golden(); replay.put("never_replay", false); reject(replay);
        ObjectNode original = golden(); at(original, "/source").put("projection_notice", "original"); reject(original);
    }

    @Test
    void pausePoststateNullFalseAndTrueRemainSeparateWithoutGrantingCredit() throws IOException {
        ClockFailureAssessment unobserved = classify(golden());
        assertEquals(PauseObserved.UNOBSERVED_AFTER_CLEANUP, unobserved.pauseObserved());
        for (boolean paused : new boolean[] {false, true}) {
            ObjectNode row = golden(); at(row, "/cleanup_tail").put("paused_after_cleanup", paused);
            ClockFailureAssessment result = classify(row);
            assertEquals(paused ? PauseObserved.OBSERVED_PAUSED_AFTER_CLEANUP : PauseObserved.OBSERVED_RUNNING_AFTER_CLEANUP,
                    result.pauseObserved()); noAuthority(result);
        }
        ObjectNode missing = golden(); at(missing, "/cleanup_tail").remove("paused_after_cleanup"); reject(missing);
        ObjectNode wrong = golden(); at(wrong, "/cleanup_tail").put("paused_after_cleanup", "false"); reject(wrong);
    }

    @Test
    void emptyCleanupAndUnknownAcknowledgementNeverImplyPause() throws IOException {
        ObjectNode empty = golden(); empty.putArray("cleanup_attempts");
        assertEquals(PauseAcknowledgements.NONE, classify(empty).pauseAcknowledgements());
        ObjectNode unknown = golden(); ((ObjectNode) unknown.get("cleanup_attempts").get(0)).putNull("accepted");
        assertEquals(PauseAcknowledgements.MIXED_OR_UNCONFIRMED, classify(unknown).pauseAcknowledgements());
        assertEquals(PauseObserved.UNOBSERVED_AFTER_CLEANUP, classify(unknown).pauseObserved());
        ObjectNode absent = golden(); absent.putNull("cleanup_attempts"); reject(absent);
        ObjectNode missingAck = golden(); ((ObjectNode) missingAck.get("cleanup_attempts").get(0)).remove("accepted"); reject(missingAck);
    }

    @Test
    void stallThresholdIsExplicitAndShortInterruptionsDoNotBecomePermanentDeadlocks() throws IOException {
        NativeClockFailureObservation observation = parse(golden());
        ClockFailureAssessment result = NativeClockFailureClassifier.classify(observation, 30000);
        assertEquals(OwnerProgress.PROGRESS_OBSERVED, result.ownerProgress()); noAuthority(result);
        assertThrows(ContractViolationException.class, () -> NativeClockFailureClassifier.classify(observation, 0));
        assertThrows(ContractViolationException.class, () -> NativeClockFailureClassifier.classify(observation, Long.MAX_VALUE));
    }

    @Test
    void flagsMissingAndResetsMakeOwnerEvidenceIndeterminate() throws IOException {
        for (String field : new String[] {"missing", "resets"}) {
            ObjectNode row = golden(); at(row, "/progress/owner").put(field, 1);
            ClockFailureAssessment result = classify(row); assertEquals(OwnerProgress.INDETERMINATE, result.ownerProgress());
            assertNull(result.trailingOwnerUnchangedMillis()); noAuthority(result);
        }
        ObjectNode flagged = golden(); at(flagged, "/progress").put("flags", "2");
        assertEquals(TransportAlive.INDETERMINATE, classify(flagged).transportAlive());
        assertEquals(OwnerProgress.INDETERMINATE, classify(flagged).ownerProgress());
    }

    @Test
    void asynchronousFramesAndObserverSamplesArePreservedWithoutInventedAtomicEquality() throws IOException {
        ObjectNode row = golden(); at(row, "/progress/owner").put("last", "371769").put("delta", "53");
        ClockFailureAssessment result = classify(row); assertEquals(OwnerProgress.INDETERMINATE, result.ownerProgress());
        assertNull(result.trailingOwnerUnchangedMillis()); noAuthority(result);
        ObjectNode observer = golden(); at(observer, "/wait_final/observer").put("read_in_progress", true);
        assertTrue(classify(observer).observerReadingAtWaitEnd()); noAuthority(classify(observer));
        assertEquals(parse(observer), NativeClockFailureCodec.parse(NativeClockFailureCodec.encode(parse(observer)), SOURCE));
    }

    @Test
    void identityRevisionAndCleanupCounterDriftCannotBecomeProgressProof() throws IOException {
        ObjectNode bridge = golden(); at(bridge, "/wait_final/bridge").put("connection_generation", 2);
        assertEquals(TransportAlive.INDETERMINATE, classify(bridge).transportAlive());
        assertEquals(OwnerProgress.INDETERMINATE, classify(bridge).ownerProgress());
        ObjectNode actor = golden(); at(actor, "/wait_final").put("episode_character_id", 40527);
        assertEquals(OwnerProgress.INDETERMINATE, classify(actor).ownerProgress());
        ObjectNode revision = golden(); at(revision, "/wait_final").put("revision", 1);
        assertEquals(OwnerProgress.INDETERMINATE, classify(revision).ownerProgress());
        ObjectNode tail = golden(); at(tail, "/cleanup_tail/owner").put("verified_pump_epochs", "1");
        assertEquals(OwnerProgress.INDETERMINATE, classify(tail).ownerProgress());
    }

    @Test
    void duplicateHeartbeatEventsAndAnEmptyWindowKeepTheirDifferentMeanings() throws IOException {
        ObjectNode duplicates = golden(); at(duplicates, "/progress").put("heartbeat_events", 130);
        assertEquals(TransportAlive.ALIVE_DURING_WAIT, classify(duplicates).transportAlive());
        ObjectNode empty = golden(); ObjectNode metric = at(empty, "/progress/heartbeat");
        metric.put("last", "11148").putNull("last_change_ms").put("changes", 0).put("delta", "0");
        at(empty, "/progress").put("heartbeat_events", 0).put("maximum_heartbeat_gap_ms", 30340);
        assertEquals(TransportAlive.NO_HEARTBEAT_PROGRESS, classify(empty).transportAlive());
        assertNull(parse(empty).progress().heartbeat().lastChangeMillis());
        assertEquals(parse(empty), NativeClockFailureCodec.parse(NativeClockFailureCodec.encode(parse(empty)), SOURCE));
    }

    @Test
    void impossibleMetricArithmeticAndOutOfWindowChangeTimesFailClosed() throws IOException {
        ObjectNode wrongDelta = golden(); at(wrongDelta, "/progress/owner").put("delta", "51"); reject(wrongDelta);
        ObjectNode late = golden(); at(late, "/progress/verified").put("last_change_ms", 30341); reject(late);
        ObjectNode unknownChange = golden(); at(unknownChange, "/progress/verified").putNull("last_change_ms"); reject(unknownChange);
        ObjectNode eventCount = golden(); at(eventCount, "/progress").put("heartbeat_events", 121); reject(eventCount);
        ObjectNode atomic = golden(); at(atomic, "/progress").put("atomic_observation", true); reject(atomic);
    }

    @Test
    void win32UnsignedPidDomainSurvivesEveryIdentityAndRoundtrip() throws IOException {
        ObjectNode row = golden();
        for (String pointer : new String[] {"/wait_identity/bridge", "/starting/bridge", "/wait_final/bridge"}) {
            at(row, pointer).put("bridge_pid", 4294967295L);
        }
        NativeClockFailureObservation input = parse(row);
        assertEquals(4294967295L, input.waitIdentity().bridge().bridgePid());
        assertEquals(input, NativeClockFailureCodec.parse(NativeClockFailureCodec.encode(input), SOURCE));
    }
}
