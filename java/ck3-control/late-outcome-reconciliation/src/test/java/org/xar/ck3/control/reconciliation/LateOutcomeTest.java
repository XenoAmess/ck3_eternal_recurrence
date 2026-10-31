package org.xar.ck3.control.reconciliation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.*;
import static org.junit.jupiter.api.Assertions.*;

class LateOutcomeTest {
    private static final String REAL_SHA = "a29abe49623a8da965af385526b2b9a22ad0ed30d321d0ac340d4149fc74d9de";
    private static final Instant NOW = Instant.parse("2026-10-22T13:30:00Z");
    private static final String SHA = "1".repeat(64);
    private static CrossJsDecimalUInt64 u(long value) { return new CrossJsDecimalUInt64(Long.toString(value)); }
    private static byte[] resource(String name) throws IOException {
        try (var input = LateOutcomeTest.class.getResourceAsStream("/" + name)) {
            assertNotNull(input); return input.readAllBytes();
        }
    }
    private static ObjectNode statusRow() throws IOException { return (ObjectNode) StrictJson.parse(resource("synthetic-late-status.json")); }
    private static ObjectNode frameRow() throws IOException { return (ObjectNode) StrictJson.parse(resource("synthetic-late-semantic.json")); }
    private static ObjectNode at(ObjectNode row, String pointer) { return (ObjectNode) row.at(pointer); }
    private static byte[] wire(ObjectNode row) { return row.toString().getBytes(StandardCharsets.UTF_8); }
    private static Scope scope() {
        return new Scope("synthetic-machine-not-runtime", new ProcessIdentity(12345, u(1000)),
                new ProcessIdentity(23456, u(2000)), new ProcessIdentity(34567, u(3000)), "synthetic-session",
                new SourceBinding(SHA, SHA, SHA, SHA, SHA), 1, 40526, "synthetic-episode", new WorldIdentity(u(111), u(222)));
    }
    private static ContentEvidenceRef ref(String key) { return new ContentEvidenceRef(SHA, 1, key); }
    private static Attempt attempt() {
        return new Attempt(scope(), new OriginalFailure(ref("original-error"), 11543, 11558, false, false),
                new Arm(u(1), 53279400, 53279424, 3, Mode.TERMINAL_OR_SENTINEL, List.of(), 0),
                ref("original-writer-head"), 3, u(101), u(201));
    }
    private static Budget budget() { return new Budget(30_000, 8, 2000, 100, NOW.plusSeconds(30)); }
    private static Context context(int count) { return new Context(GameLife.SAME_PROCESS_ALIVE, 1000, NOW, count); }
    private static Evidence evidence(long sequence, long elapsed) {
        return new Evidence(scope(), scope(), sequence, ref("synthetic-read-" + sequence), elapsed,
                NOW.minusMillis(1000 - elapsed), u(900100));
    }
    private static Status status(ObjectNode row) { return SentinelCodec.decode(wire(row)); }
    private static Semantic semantic(ObjectNode row) { return NativeSemanticCodec.decode(wire(row), 16_384); }
    private static List<Read> lateReads() throws IOException {
        return List.of(new StatusRead(evidence(11559, 100), status(statusRow())),
                new SemanticRead(evidence(11560, 200), semantic(frameRow())),
                new StatusRead(evidence(11561, 300), status(statusRow())));
    }
    private static Assessment plan(List<Read> reads) { return LateOutcomePlanner.assess(attempt(), budget(), context(reads.size()), reads); }
    private static Assessment withFrame(Consumer<ObjectNode> edit) throws IOException {
        ObjectNode frame = frameRow(); edit.accept(frame);
        return plan(List.of(new StatusRead(evidence(11559, 100), status(statusRow())),
                new SemanticRead(evidence(11560, 200), semantic(frame)),
                new StatusRead(evidence(11561, 300), status(statusRow()))));
    }
    private static Scope changedScope(String field) {
        Scope s = scope();
        return new Scope(field.equals("machine") ? "other-machine" : s.machineId(),
                field.equals("game") ? new ProcessIdentity(s.game().pid(), u(1001)) : s.game(),
                field.equals("queue") ? new ProcessIdentity(s.queue().pid(), u(2001)) : s.queue(),
                field.equals("application") ? new ProcessIdentity(s.application().pid(), u(3001)) : s.application(),
                field.equals("session") ? "other-session" : s.sessionId(),
                field.equals("source") ? new SourceBinding("2".repeat(64), SHA, SHA, SHA, SHA) : s.source(),
                field.equals("connection") ? 2 : s.connectionGeneration(),
                field.equals("actor") ? 40527 : s.actorId(), field.equals("episode") ? "other-episode" : s.episodeId(),
                field.equals("world") ? new WorldIdentity(u(112), u(222)) : s.world());
    }

    @Test void original11558ProjectionCannotSupplyMissingCurrentProof() throws IOException {
        OriginalFailureProjection original = OriginalFailureProjection.decode(resource("original-n46-11558.projection.json"), REAL_SHA);
        assertEquals(11558, original.autoSequence()); assertFalse(original.normalStatusQueryAttempted());
        assertFalse(original.stopValidationAttempted()); assertEquals(State.ARMED, original.historicalArm().state());
        assertEquals(Outcome.UNRESOLVED, original.assessIncomplete().outcome());
        assertEquals(0, original.assessIncomplete().originalCredit()); assertTrue(original.assessIncomplete().neverReplay());
        JsonNode root = StrictJson.parse(resource("original-n46-11558.projection.json"));
        assertThrows(ContractViolationException.class, () -> SentinelCodec.decode(root.at("/payload/armed_reply").toString().getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> OriginalFailureProjection.decode(resource("original-n46-11558.projection.json"), SHA));
    }
    @Test void syntheticCompleteLateStopOnlyProposesWriterRevalidation() throws IOException {
        Assessment result = plan(lateReads());
        assertEquals(Outcome.PROPOSED, result.outcome()); assertEquals(Reason.LATE_STOP_REQUIRES_WRITER_REDUCER, result.reason());
        assertNull(result.nextRead()); assertEquals(0, result.originalCredit()); assertTrue(result.neverReplay());
        assertEquals(List.of(11559L, 11560L, 11561L), result.observedSequences());
        assertFalse(attempt().original().normalStatusQueryAttempted()); assertFalse(attempt().original().stopValidationAttempted());
    }
    @Test void armedGuardRemainsAndNoSemanticOrCancelIsProposed() throws IOException {
        ObjectNode row = statusRow(); row.put("state", "armed"); row.put("trigger_flags", 0); row.putArray("trigger_reasons");
        row.put("pause_observed", false); row.put("trigger_date_raw", 0); row.put("overshoot_days", -1);
        Assessment result = plan(List.of(new StatusRead(evidence(11559, 100), status(row))));
        assertEquals(Outcome.WAIT, result.outcome()); assertEquals(Reason.ARMED_GUARD_RETAINED, result.reason());
        assertEquals(ReadKind.CURRENT_SENTINEL_STATUS, result.nextRead());
    }
    @Test void emptyAndTwoReadPlansHaveSpecificNextReads() throws IOException {
        assertEquals(ReadKind.CURRENT_SENTINEL_STATUS, plan(List.of()).nextRead());
        List<Read> reads = lateReads();
        assertEquals(ReadKind.CURRENT_SEMANTIC_FRAME, plan(reads.subList(0, 1)).nextRead());
        assertEquals(ReadKind.CURRENT_SENTINEL_STATUS, plan(reads.subList(0, 2)).nextRead());
    }
    @Test void closedOrUnknownGameCannotBeReconciledFromOldVisuals() throws IOException {
        assertEquals(Outcome.REJECTED, LateOutcomePlanner.assess(attempt(), budget(), new Context(GameLife.CLOSED, 1000, NOW, 3), lateReads()).outcome());
        assertEquals(Outcome.UNRESOLVED, LateOutcomePlanner.assess(attempt(), budget(), new Context(GameLife.UNKNOWN, 1000, NOW, 3), lateReads()).outcome());
    }
    @Test void pauseAckShapeAndUnpausedSemanticDoNotProvePause() throws IOException {
        assertThrows(ContractViolationException.class, () -> SentinelCodec.decode("{\"accepted\":true,\"status\":\"submitted\"}".getBytes(StandardCharsets.UTF_8)));
        ObjectNode frame = frameRow(); frame.put("paused", false); at(frame, "/diagnostics/last_heartbeat/main_thread_query_mailbox_v1").put("paused", false);
        Assessment result = plan(List.of(new StatusRead(evidence(11559, 100), status(statusRow())), new SemanticRead(evidence(11560, 200), semantic(frame))));
        assertEquals(Outcome.WAIT, result.outcome()); assertEquals(Reason.SEMANTIC_NOT_PAUSED, result.reason());
    }
    @Test void allTransportIdentityChangesRejectBeforeAndAfterRead() throws IOException {
        for (String field : List.of("machine", "game", "queue", "application", "session", "source", "connection", "actor", "episode", "world")) {
            for (boolean before : List.of(true, false)) {
                Evidence original = evidence(11559, 100);
                Evidence changed = new Evidence(before ? changedScope(field) : scope(), before ? scope() : changedScope(field),
                        original.sequence(), original.reply(), original.receivedElapsedMillis(), original.observedAt(), original.readerWin32UptimeMillis());
                assertEquals(Outcome.REJECTED, plan(List.of(new StatusRead(changed, status(statusRow())))).outcome(), field);
            }
        }
    }
    @Test void duplicateReorderedAndOriginalSequencesRemainRejectedFacts() throws IOException {
        List<Read> reads = lateReads();
        Assessment duplicate = plan(List.of(reads.get(0), new SemanticRead(evidence(11559, 200), semantic(frameRow()))));
        assertEquals(Reason.READ_SEQUENCE_INVALID, duplicate.reason()); assertEquals(List.of(11559L, 11559L), duplicate.observedSequences());
        assertEquals(Outcome.REJECTED, plan(List.of(new StatusRead(evidence(11558, 100), status(statusRow())))).outcome());
        assertEquals(Outcome.REJECTED, plan(List.of(reads.get(1), reads.get(0))).outcome());
    }
    @Test void terminalSlotChangeAndArmedRollbackReject() throws IOException {
        for (String key : List.of("generation", "target_date_raw", "speed", "army_count", "combat_count")) {
            ObjectNode row = statusRow(); row.put(key, row.get(key).longValue() + 1);
            List<Read> reads = new ArrayList<>(lateReads()); reads.set(2, new StatusRead(evidence(11561, 300), status(row)));
            assertEquals(Outcome.REJECTED, plan(reads).outcome(), key);
        }
        ObjectNode row = statusRow(); row.put("state", "armed");
        List<Read> reads = new ArrayList<>(lateReads()); reads.set(2, new StatusRead(evidence(11561, 300), status(row)));
        assertEquals(Reason.SLOT_CHANGED, plan(reads).reason());
    }
    @Test void nativePauseOwnershipIsAcceptedOnlyInItsActualBranch() throws IOException {
        ObjectNode row = statusRow(); row.put("trigger_flags", 8193); row.putArray("trigger_reasons").add("date_deadline").add("native_pause");
        row.put("intermediate_pause_count", 1); row.put("pause_wrapper_called", false);
        Status stop = status(row);
        List<Read> reads = List.of(new StatusRead(evidence(11559, 100), stop), new SemanticRead(evidence(11560, 200), semantic(frameRow())), new StatusRead(evidence(11561, 300), stop));
        assertEquals(Outcome.PROPOSED, plan(reads).outcome());
        row.put("pause_wrapper_called", true);
        assertEquals(Reason.STOP_NOT_VALID, plan(List.of(new StatusRead(evidence(11559, 100), status(row)))).reason());
    }
    @Test void wrongStopDateTickDeltaAndOvershootCannotBeProposed() throws IOException {
        for (String key : List.of("last_observed_date_raw", "trigger_date_raw", "completed_daily_ticks", "signed_date_delta_from_target_raw", "overshoot_days", "intermediate_pause_count")) {
            ObjectNode row = statusRow(); row.put(key, row.get(key).longValue() + 1);
            assertEquals(Outcome.REJECTED, plan(List.of(new StatusRead(evidence(11559, 100), status(row)))).outcome(), key);
        }
        ObjectNode row = statusRow(); row.put("pause_observed", false);
        assertEquals(Reason.STOP_NOT_VALID, plan(List.of(new StatusRead(evidence(11559, 100), status(row)))).reason());
    }
    @Test void playedActorDeathSuccessionAndPendingEpisodeCannotBeProposed() throws IOException {
        assertEquals(Outcome.REJECTED, withFrame(row -> at(row, "/played_character").put("character_id", 40527)).outcome());
        assertEquals(Outcome.REJECTED, withFrame(row -> at(row, "/played_character").put("alive", false)).outcome());
        assertEquals(Outcome.REJECTED, withFrame(row -> row.put("one_life_terminal", true)).outcome());
        assertEquals(Outcome.REJECTED, withFrame(row -> row.put("episode_identity_pending", true)).outcome());
        assertEquals(Outcome.REJECTED, withFrame(row -> row.put("snapshot_id", "native:2")).outcome());
    }
    @Test void actualSemanticIdentityAndWorldChangeReject() throws IOException {
        assertEquals(Outcome.REJECTED, withFrame(row -> at(row, "/diagnostics").put("bridge_pid", 999)).outcome());
        assertEquals(Outcome.REJECTED, withFrame(row -> at(row, "/diagnostics/last_heartbeat").put("pid", 999)).outcome());
        assertEquals(Outcome.REJECTED, withFrame(row -> at(row, "/diagnostics/last_heartbeat/main_thread_query_mailbox_v1").put("game_state", 112)).outcome());
        assertEquals(Outcome.REJECTED, withFrame(row -> row.put("episode_run_id", "other-episode")).outcome());
    }
    @Test void eachNativeFreshnessFloorIsIndependent() throws IOException {
        assertEquals(Reason.FRAME_REGRESSED, withFrame(row -> { row.put("native_revision", 2); row.put("snapshot_id", "native:2"); }).reason());
        assertEquals(Reason.FRAME_REGRESSED, withFrame(row -> at(row, "/diagnostics/last_heartbeat").put("sequence", 200)).reason());
        assertEquals(Reason.FRAME_REGRESSED, withFrame(row -> at(row, "/diagnostics/last_heartbeat/main_thread_query_mailbox_v1").put("owner_verified_pump_epochs", 100)).reason());
    }
    @Test void staleNativeAndStaleJavaReceiptUseSeparateClockDomains() throws IOException {
        ObjectNode row = frameRow(); at(row, "/diagnostics/last_heartbeat").put("monotonic_ms", 890000);
        Assessment stale = plan(List.of(new StatusRead(evidence(11559, 100), status(statusRow())), new SemanticRead(evidence(11560, 200), semantic(row))));
        assertEquals(Reason.SEMANTIC_NOT_FRESH, stale.reason());
        Assessment oldReceipt = LateOutcomePlanner.assess(attempt(), budget(), new Context(GameLife.SAME_PROCESS_ALIVE, 4000, NOW, 3), lateReads());
        assertEquals(Outcome.UNRESOLVED, oldReceipt.outcome()); assertEquals(Reason.SEMANTIC_NOT_FRESH, oldReceipt.reason());
        at(row, "/diagnostics/last_heartbeat").put("monotonic_ms", 900101);
        assertEquals(Outcome.WAIT, plan(List.of(new StatusRead(evidence(11559, 100), status(statusRow())), new SemanticRead(evidence(11560, 200), semantic(row)))).outcome());
    }
    @Test void freshHeartbeatCannotReplaceOwnerStampOrMatchingOwnerFrame() throws IOException {
        for (String field : List.of("stamp_read_success", "stop", "failure", "current_tid", "owner_tid")) {
            ObjectNode row = frameRow(); ObjectNode owner = at(row, "/diagnostics/last_heartbeat/main_thread_query_mailbox_v1");
            if (field.equals("stamp_read_success")) { owner.put(field, false); }
            else if (field.equals("stop")) { owner.put(field, true); }
            else { owner.put(field, 0); if (field.equals("failure")) { owner.put(field, 1); } }
            Assessment result = plan(List.of(new StatusRead(evidence(11559, 100), status(statusRow())), new SemanticRead(evidence(11560, 200), semantic(row))));
            assertEquals(Outcome.WAIT, result.outcome(), field);
        }
        assertEquals(Outcome.REJECTED, withFrame(row -> at(row, "/diagnostics/last_heartbeat/main_thread_query_mailbox_v1").put("date_raw", 53279400)).outcome());
    }
    @Test void fullHistoryConsumesReadBudgetAndHardDeadline() throws IOException {
        Budget twoReads = new Budget(30000, 2, 2000, 100, NOW.plusSeconds(30));
        assertEquals(Outcome.UNRESOLVED, LateOutcomePlanner.assess(attempt(), twoReads, context(2), lateReads().subList(0, 2)).outcome());
        assertEquals(Reason.BUDGET_EXHAUSTED, LateOutcomePlanner.assess(attempt(), twoReads, context(3), lateReads()).reason());
        assertEquals(Reason.DEADLINE_EXPIRED, LateOutcomePlanner.assess(attempt(), budget(), new Context(GameLife.SAME_PROCESS_ALIVE, 1000, NOW.plusSeconds(30), 3), lateReads()).reason());
        assertEquals(Reason.BUDGET_EXHAUSTED, LateOutcomePlanner.assess(attempt(), budget(), new Context(GameLife.SAME_PROCESS_ALIVE, 30000, NOW, 0), List.of()).reason());
        Assessment reset = LateOutcomePlanner.assess(attempt(), twoReads, context(3), List.of());
        assertEquals(Reason.HISTORY_INCOMPLETE, reset.reason()); assertEquals(3, reset.consumedReads());
    }
    @Test void unavailableAndWrongReadOrderAreExplicit() throws IOException {
        assertEquals(Reason.READ_UNAVAILABLE, plan(List.of(new UnavailableRead(evidence(11559, 100), ReadKind.CURRENT_SENTINEL_STATUS, "reader not wired"))).reason());
        assertEquals(Reason.WRONG_READ_ORDER, plan(List.of(new SemanticRead(evidence(11559, 100), semantic(frameRow())))).reason());
    }
    @Test void receiveTimesCannotRunBackwardsOrIntoFuture() throws IOException {
        Evidence future = new Evidence(scope(), scope(), 11559, ref("future"), 1001, NOW, u(900100));
        assertEquals(Reason.READ_TIME_INVALID, plan(List.of(new StatusRead(future, status(statusRow())))).reason());
        Evidence back = new Evidence(scope(), scope(), 11560, ref("back"), 90, NOW.minusSeconds(2), u(900100));
        assertEquals(Reason.READ_TIME_INVALID, plan(List.of(new StatusRead(evidence(11559, 100), status(statusRow())), new SemanticRead(back, semantic(frameRow())))).reason());
    }
    private static void rejectRawStatus(String key, String token) throws IOException {
        ObjectNode row = statusRow(); row.put(key, "__raw_token__");
        byte[] raw = row.toString().replace("\"__raw_token__\"", token).getBytes(StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class, () -> SentinelCodec.decode(raw), key + "=" + token);
    }
    @Test void statusStrictTypesMissingNullAndExtraFieldsAreRejected() throws IOException {
        for (String token : List.of("true", "1.0", "1e0", "\"1\"", "null", "-1", "18446744073709551616")) { rejectRawStatus("generation", token); }
        for (String key : List.of("starting_date_raw", "target_date_raw", "last_observed_date_raw", "trigger_date_raw")) { rejectRawStatus(key, "-1"); }
        rejectRawStatus("overshoot_days", "-2"); rejectRawStatus("army_count", "4294967296"); rejectRawStatus("pause_observed", "1");
        ObjectNode row = statusRow(); row.remove("trigger_reasons"); assertThrows(ContractViolationException.class, () -> SentinelCodec.decode(wire(row)));
        ObjectNode extra = statusRow(); extra.put("accepted", true); assertThrows(ContractViolationException.class, () -> SentinelCodec.decode(wire(extra)));
    }
    @Test void triggerReasonsRejectDuplicatesWrongOrderAndUnknownBits() throws IOException {
        ObjectNode row = statusRow(); row.putArray("trigger_reasons").add("date_deadline").add("date_deadline");
        assertThrows(ContractViolationException.class, () -> SentinelCodec.decode(wire(row)));
        ObjectNode wrong = statusRow(); wrong.put("trigger_flags", 8193); wrong.putArray("trigger_reasons").add("native_pause").add("date_deadline");
        assertThrows(ContractViolationException.class, () -> SentinelCodec.decode(wire(wrong)));
        rejectRawStatus("trigger_flags", "131072");
    }
    @Test void semanticCriticalTokensCannotCoerceAndUnknownBusinessFloatIsNotCanonicalized() throws IOException {
        for (String token : List.of("true", "3.0", "3e0", "\"3\"", "null", "9007199254740992")) {
            ObjectNode row = frameRow(); row.put("native_revision", "__raw_token__");
            byte[] raw = row.toString().replace("\"__raw_token__\"", token).getBytes(StandardCharsets.UTF_8);
            assertThrows(ContractViolationException.class, () -> NativeSemanticCodec.decode(raw, 16384));
        }
        ObjectNode row = frameRow(); row.put("unrelated_business_fraction", 0.5);
        assertEquals(3, semantic(row).nativeRevision());
        ObjectNode absent = frameRow(); at(absent, "/diagnostics/last_heartbeat/main_thread_query_mailbox_v1").remove("game_state");
        assertThrows(ContractViolationException.class, () -> semantic(absent));
        ObjectNode nullValue = frameRow(); at(nullValue, "/played_character").putNull("alive");
        assertThrows(ContractViolationException.class, () -> semantic(nullValue));
        assertThrows(ContractViolationException.class, () -> NativeSemanticCodec.decode(resource("synthetic-late-semantic.json"), 8));
    }
    @Test void nativeUInt64ConversionAndIndependentCrossJsDomainAreExact() throws IOException {
        ObjectNode row = statusRow(); row.put("generation", new java.math.BigInteger("18446744073709551615"));
        assertEquals("18446744073709551615", status(row).generation().decimal());
        assertThrows(ContractViolationException.class, () -> new CrossJsDecimalUInt64("01"));
        assertThrows(ContractViolationException.class, () -> new Arm(u(1), -1, 23, 3, Mode.TERMINAL_OR_SENTINEL, List.of(), 0));
        assertDoesNotThrow(() -> new Arm(u(1), 0, 24, 3, Mode.TERMINAL_OR_SENTINEL, List.of(0, Integer.MAX_VALUE), 0));
        assertThrows(ContractViolationException.class, () -> new Arm(u(1), 0, 24, 3, Mode.TERMINAL_OR_SENTINEL, List.of(1, 1), 0));
    }
    @Test void originalCompletedErrorFactsStayDistinctAndZeroCredit() throws IOException {
        Attempt original = attempt();
        Attempt completedError = new Attempt(original.scope(), new OriginalFailure(original.original().receipt(), 11543, 11558, true, true),
                original.arm(), original.expectedHead(), original.minNativeRevision(), original.minVerifiedPumpEpoch(), original.minHeartbeatSequence());
        assertEquals(Outcome.PROPOSED, LateOutcomePlanner.assess(completedError, budget(), context(3), lateReads()).outcome());
        assertTrue(completedError.original().normalStatusQueryAttempted()); assertTrue(completedError.original().stopValidationAttempted());
        assertEquals(0, completedError.original().originalCredit()); assertTrue(completedError.original().neverReplay());
        assertFalse(original.original().normalStatusQueryAttempted());
    }
    @Test void assessmentRoundTripKeepsOriginalBindingAndNoExecutionCapability() throws IOException {
        for (Assessment result : List.of(plan(List.of()), plan(lateReads()),
                OriginalFailureProjection.decode(resource("original-n46-11558.projection.json"), REAL_SHA).assessIncomplete())) {
            byte[] encoded = AssessmentCodec.encode(attempt(), result);
            assertEquals(result, AssessmentCodec.decode(encoded, attempt()));
            ObjectNode row = (ObjectNode) StrictJson.parse(encoded); row.put("original_auto_sequence", 11557);
            assertThrows(ContractViolationException.class, () -> AssessmentCodec.decode(wire(row), attempt()));
        }
        ObjectNode row = (ObjectNode) StrictJson.parse(AssessmentCodec.encode(attempt(), plan(lateReads())));
        assertFalse(row.has("resumeAuthorized")); assertFalse(row.has("cancel")); assertFalse(row.has("resume_ticket"));
        row.put("original_credit", 1); assertThrows(ContractViolationException.class, () -> AssessmentCodec.decode(wire(row), attempt()));
        ObjectNode extra = (ObjectNode) StrictJson.parse(AssessmentCodec.encode(attempt(), plan(List.of())));
        extra.put("resumeAuthorized", true); assertThrows(ContractViolationException.class, () -> AssessmentCodec.decode(wire(extra), attempt()));
    }
    @Test void assessmentCannotReplayAcrossScopeArmOrFreshnessBoundsWithSameThreeOldPins() throws IOException {
        Attempt original = attempt(); byte[] encoded = AssessmentCodec.encode(original, plan(lateReads()));
        for (String field : List.of("machine", "game", "queue", "application", "session", "source", "connection", "actor", "episode", "world")) {
            Attempt other = new Attempt(changedScope(field), original.original(), original.arm(), original.expectedHead(),
                    original.minNativeRevision(), original.minVerifiedPumpEpoch(), original.minHeartbeatSequence());
            assertThrows(ContractViolationException.class, () -> AssessmentCodec.decode(encoded, other), field);
        }
        Attempt otherArm = new Attempt(original.scope(), original.original(),
                new Arm(u(2), 53279400, 53279424, 3, Mode.TERMINAL_OR_SENTINEL, List.of(), 0), original.expectedHead(),
                original.minNativeRevision(), original.minVerifiedPumpEpoch(), original.minHeartbeatSequence());
        assertThrows(ContractViolationException.class, () -> AssessmentCodec.decode(encoded, otherArm));
        for (int index = 0; index < 3; index++) {
            Attempt other = new Attempt(original.scope(), original.original(), original.arm(), original.expectedHead(),
                    original.minNativeRevision() + (index == 0 ? 1 : 0), index == 1 ? u(102) : original.minVerifiedPumpEpoch(),
                    index == 2 ? u(202) : original.minHeartbeatSequence());
            assertThrows(ContractViolationException.class, () -> AssessmentCodec.decode(encoded, other));
        }
    }
    @Test void farFutureUtcDeadlineCannotOverflowBoundedLocalBudget() {
        Budget far = new Budget(30_000, 8, 2000, 100, Instant.MAX);
        Assessment result = LateOutcomePlanner.assess(attempt(), far, context(0), List.of());
        assertEquals(Outcome.WAIT, result.outcome()); assertEquals(100, result.waitMillis());
        Budget shortLocal = new Budget(1001, 8, 2000, 100, Instant.MAX);
        assertEquals(1, LateOutcomePlanner.assess(attempt(), shortLocal, context(0), List.of()).waitMillis());
    }

    @Test void idleStatusAdmitsZeroSpeedAndPreservesResetFacts() throws IOException {
        // Source-derived software fixture: simulates Native63 reset/cancel idle state (speed 0..5 legal for IDLE)
        // This is NOT an actual live ACK or game observation.
        ObjectNode row = statusRow();
        row.put("state", "idle");
        row.put("generation", 0);
        row.put("starting_date_raw", 0);
        row.put("target_date_raw", 0);
        row.put("last_observed_date_raw", 0);
        row.put("trigger_date_raw", 0);
        row.put("speed", 0);
        row.put("mode", "decision_epoch");
        row.put("army_count", 0);
        row.put("combat_count", 0);
        row.put("completed_daily_ticks", 0);
        row.put("intermediate_pause_count", 0);
        row.put("trigger_flags", 0);
        row.putArray("trigger_reasons");
        row.put("signed_date_delta_from_target_raw", 0);
        row.put("overshoot_days", -1);
        row.put("pause_wrapper_called", false);
        row.put("pause_observed", false);
        row.put("terminal_observed", false);
        row.put("abnormal", false);

        Status idle0 = status(row);
        assertEquals(State.IDLE, idle0.state());
        assertEquals(0, idle0.speed());
        assertEquals("0", idle0.generation().decimal());
        assertEquals(0, idle0.startingDateRaw());
        assertEquals(0, idle0.targetDateRaw());
        assertEquals(0, idle0.lastObservedDateRaw());
        assertEquals(0, idle0.triggerDateRaw());
        assertEquals(Mode.DECISION_EPOCH, idle0.mode());
        assertEquals(0, idle0.armyCount());
        assertEquals(0, idle0.combatCount());
        assertEquals(0, idle0.completedDailyTicks());
        assertEquals(0, idle0.intermediatePauseCount());
        assertEquals(0, idle0.triggerFlags());
        assertEquals(List.of(), idle0.triggerReasons());
        assertEquals(0, idle0.signedDateDeltaFromTargetRaw());
        assertEquals(-1, idle0.overshootDays());
        assertFalse(idle0.pauseWrapperCalled());
        assertFalse(idle0.pauseObserved());
        assertFalse(idle0.terminalObserved());
        assertFalse(idle0.abnormal());

        // Canceled idle with speed 1..5 remains accepted
        for (int s = 1; s <= 5; s++) {
            ObjectNode cancelRow = statusRow();
            cancelRow.put("state", "idle");
            cancelRow.put("speed", s);
            cancelRow.put("generation", 1);
            cancelRow.put("starting_date_raw", 53279400);
            cancelRow.put("target_date_raw", 53279424);
            cancelRow.put("last_observed_date_raw", 53279400);
            cancelRow.put("trigger_date_raw", 0);
            cancelRow.put("mode", "terminal_or_sentinel");
            cancelRow.put("army_count", 0);
            cancelRow.put("combat_count", 0);
            cancelRow.put("completed_daily_ticks", 0);
            cancelRow.put("intermediate_pause_count", 0);
            cancelRow.put("trigger_flags", 0);
            cancelRow.putArray("trigger_reasons");
            cancelRow.put("signed_date_delta_from_target_raw", 0);
            cancelRow.put("overshoot_days", -1);
            cancelRow.put("pause_wrapper_called", false);
            cancelRow.put("pause_observed", false);
            cancelRow.put("terminal_observed", false);
            cancelRow.put("abnormal", false);
            Status canceled = status(cancelRow);
            assertEquals(State.IDLE, canceled.state());
            assertEquals(s, canceled.speed());
        }
    }

    @Test void nonIdleSpeedZeroAndMalformedTokensAreRejected() throws IOException {
        // Negative boundaries: speed 0 must be rejected for all non-IDLE states
        for (String state : List.of("armed", "triggered", "failed", "unavailable")) {
            ObjectNode row = statusRow();
            row.put("state", state);
            row.put("speed", 0);
            // Ensure other fields are consistent with the state to isolate speed rejection
            if (state.equals("armed")) {
                row.put("generation", 1);
                row.put("starting_date_raw", 53279400);
                row.put("target_date_raw", 53279424);
                row.put("last_observed_date_raw", 53279400);
                row.put("trigger_date_raw", 0);
                row.put("mode", "terminal_or_sentinel");
                row.put("army_count", 0);
                row.put("combat_count", 0);
                row.put("completed_daily_ticks", 0);
                row.put("intermediate_pause_count", 0);
                row.put("trigger_flags", 0);
                row.putArray("trigger_reasons");
                row.put("signed_date_delta_from_target_raw", 0);
                row.put("overshoot_days", -1);
                row.put("pause_wrapper_called", false);
                row.put("pause_observed", false);
                row.put("terminal_observed", false);
                row.put("abnormal", false);
            } else if (state.equals("triggered")) {
                row.put("generation", 1);
                row.put("starting_date_raw", 53279400);
                row.put("target_date_raw", 53279424);
                row.put("last_observed_date_raw", 53279424);
                row.put("trigger_date_raw", 53279424);
                row.put("mode", "terminal_or_sentinel");
                row.put("army_count", 0);
                row.put("combat_count", 0);
                row.put("completed_daily_ticks", 1);
                row.put("intermediate_pause_count", 0);
                row.put("trigger_flags", 1);
                row.putArray("trigger_reasons").add("date_deadline");
                row.put("signed_date_delta_from_target_raw", 0);
                row.put("overshoot_days", 0);
                row.put("pause_wrapper_called", true);
                row.put("pause_observed", true);
                row.put("terminal_observed", false);
                row.put("abnormal", false);
            } else if (state.equals("failed")) {
                row.put("generation", 1);
                row.put("starting_date_raw", 53279400);
                row.put("target_date_raw", 53279424);
                row.put("last_observed_date_raw", 53279424);
                row.put("trigger_date_raw", 53279424);
                row.put("mode", "terminal_or_sentinel");
                row.put("army_count", 0);
                row.put("combat_count", 0);
                row.put("completed_daily_ticks", 1);
                row.put("intermediate_pause_count", 0);
                row.put("trigger_flags", 1);
                row.putArray("trigger_reasons").add("date_deadline");
                row.put("signed_date_delta_from_target_raw", 0);
                row.put("overshoot_days", 0);
                row.put("pause_wrapper_called", true);
                row.put("pause_observed", true);
                row.put("terminal_observed", false);
                row.put("abnormal", true);
            } else if (state.equals("unavailable")) {
                row.put("generation", 0);
                row.put("starting_date_raw", 0);
                row.put("target_date_raw", 0);
                row.put("last_observed_date_raw", 0);
                row.put("trigger_date_raw", 0);
                row.put("mode", "decision_epoch");
                row.put("army_count", 0);
                row.put("combat_count", 0);
                row.put("completed_daily_ticks", 0);
                row.put("intermediate_pause_count", 0);
                row.put("trigger_flags", 0);
                row.putArray("trigger_reasons");
                row.put("signed_date_delta_from_target_raw", 0);
                row.put("overshoot_days", -1);
                row.put("pause_wrapper_called", false);
                row.put("pause_observed", false);
                row.put("terminal_observed", false);
                row.put("abnormal", false);
            }
            assertThrows(ContractViolationException.class, () -> status(row), "speed 0 rejected for " + state);
        }

        // Negative/out-of-range speeds for any state
        for (int badSpeed : List.of(-1, 6, 100)) {
            ObjectNode row = statusRow();
            row.put("speed", badSpeed);
            assertThrows(ContractViolationException.class, () -> status(row), "speed " + badSpeed + " rejected");
        }

        // Strict malformed numeric tokens for speed field
        for (String token : List.of("true", "1.0", "1e0", "\"1\"", "null", "-1", "18446744073709551616")) {
            ObjectNode row = statusRow();
            row.put("speed", "__raw_token__");
            byte[] raw = row.toString().replace("\"__raw_token__\"", token).getBytes(StandardCharsets.UTF_8);
            assertThrows(ContractViolationException.class, () -> SentinelCodec.decode(raw), "malformed speed token: " + token);
        }

        // Arm speed 0 rejection (unchanged contract)
        assertThrows(ContractViolationException.class, () -> new Arm(u(1), 53279400, 53279424, 0, Mode.TERMINAL_OR_SENTINEL, List.of(), 0), "Arm speed 0 rejected");

        // Direct typed Status construction with speed 0 for non-IDLE
        assertThrows(ContractViolationException.class, () -> new Status(State.ARMED, u(1), 53279400, 53279424, 53279400, 0, 0, Mode.TERMINAL_OR_SENTINEL, 0, 0, 0, 0, 0, List.of(), 0, -1, false, false, false, false), "Status speed 0 rejected for ARMED");
        assertThrows(ContractViolationException.class, () -> new Status(State.TRIGGERED, u(1), 53279400, 53279424, 53279424, 53279424, 0, Mode.TERMINAL_OR_SENTINEL, 0, 0, 1, 0, 1, List.of("date_deadline"), 0, 0, true, true, false, false), "Status speed 0 rejected for TRIGGERED");
        assertThrows(ContractViolationException.class, () -> new Status(State.FAILED, u(1), 53279400, 53279424, 53279424, 53279424, 0, Mode.TERMINAL_OR_SENTINEL, 0, 0, 1, 0, 1, List.of("date_deadline"), 0, 0, true, true, false, true), "Status speed 0 rejected for FAILED");
        assertThrows(ContractViolationException.class, () -> new Status(State.UNAVAILABLE, u(0), 0, 0, 0, 0, 0, Mode.DECISION_EPOCH, 0, 0, 0, 0, 0, List.of(), 0, -1, false, false, false, false), "Status speed 0 rejected for UNAVAILABLE");
    }
}
