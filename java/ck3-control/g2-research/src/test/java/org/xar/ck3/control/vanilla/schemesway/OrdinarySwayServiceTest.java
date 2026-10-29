package org.xar.ck3.control.vanilla.schemesway;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.vanilla.schemesway.OrdinarySwaySchedule.*;
import static org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService.*;

/** Persistent producer -> strict projection -> Java Service -> formal/lifecycle/following consumer regressions. */
public final class OrdinarySwayServiceTest {
    @TempDir Path temporary;
    private final OrdinarySwayService service = new OrdinarySwayService();

    @Test void originalProducer34Plans9StatesAnd210AssertionsRemainInDefaultJunit() throws Exception {
        Path vector = temporary.resolve("original-producer.json");
        try (InputStream stream = getClass().getResourceAsStream("/schemesway/producer-golden-v1.json")) {
            assertNotNull(stream, "the exact committed original producer fixture is required");
            Files.copy(stream, vector);
        }
        SwayScheduleVerification.main(new String[] {vector.toString()});
    }

    @Test void unchangedOriginalServiceProducerFeedsAllExecutionBranches() throws Exception {
        try (InputStream stream = getClass().getResourceAsStream("/schemesway/service-producer-golden-v1.json")) {
            assertNotNull(stream, "actual original adapter capture must be committed; missing environment is not a skipped pass");
            JsonNode vectors = StrictJson.parse(stream.readAllBytes(), 262144);
            assertEquals("xar.java-ordinary-sway-service-original-golden/v1", vectors.path("schema").textValue());
            assertEquals(19, vectors.path("cases").size());
            for (JsonNode vector : vectors.path("cases")) {
                String id = vector.path("id").textValue();
                Request request = SwayScheduleWire.decode(StrictJson.canonical(vector.get("request")));
                Port port = new Port(); port.failQuery = vector.get("query_failure").booleanValue();
                Optional<Pending> pending = Optional.empty();
                JsonNode originalPending = vector.get("current_pending");
                if (!originalPending.isNull()) {
                    pending = Optional.of(new Pending(originalPending.get("action_id").textValue(),
                            originalPending.get("actor_character_id").longValue(), originalPending.get("target_character_id").longValue()));
                }
                port.inputs = Optional.of(new Inputs(new Ledger(pending, request.ledger().resolved()), request.state()));
                Job job = plan(request).job().orElseThrow();
                if (job == Job.OBSERVE_APPLIED) {
                    port.lifecycle = OrdinarySwayExecutionWire.lifecycle(StrictJson.canonical(vector.get("formal_result")));
                } else if (vector.get("formal_result").has("status")) {
                    port.formal = OrdinarySwayExecutionWire.formal(StrictJson.canonical(vector.get("formal_result")));
                }
                Execution actual = service.execute(staged(request), port);
                Receipt receipt = actual instanceof Started started ? started.receipt() : ((Continued) actual).receipt().orElseThrow();
                JsonNode expected = vector.get("expected");
                assertEquals(expected.get("turn_owned").booleanValue(), actual instanceof Started, id);
                assertEquals(expected.get("outcome").textValue(), receipt.outcome().name().toLowerCase(java.util.Locale.ROOT), id);
                assertEquals(expected.get("scheduler_state"), StrictJson.parse(SwayScheduleWire.encodeState(receipt.schedulerState())), id);
                long queryCalls = port.calls.stream().filter("query-formal"::equals).count();
                assertEquals(expected.path("counts").path("query").longValue(), queryCalls, id);
                assertEquals(expected.path("counts").path("consume").longValue(), port.failQuery ? 0 : queryCalls, id);
                assertEquals(expected.path("counts").path("lifecycle").longValue(), port.calls.stream().filter("lifecycle"::equals).count(), id);
                assertEquals(expected.path("counts").path("fresh_plan").longValue(), port.calls.stream().filter("fresh-ordinary"::equals).count(), id);
                assertEquals(expected.path("counts").path("fresh_execute").longValue(), port.calls.stream().filter("fresh-ordinary"::equals).count(), id);
            }
        }
    }

    @Test void familyRetryDriftAndNonordinaryPriorityReadNoInputs() {
        Request request = base();
        Captured captured = captured(request);
        InputPort forbidden = () -> { fail("drift/mandatory work must not read state or ledger"); return Optional.empty(); };
        Captured retry = new Captured(captured.source(), new Wrapper(captured.wrapper().snapshotId(),
                captured.wrapper().publicRevision().add(BigInteger.ONE)), captured.selectedStep(), captured.frame(), captured.root(), captured.capabilities());
        assertEquals(StageReason.CAPTURED_FRAME_CHANGED, service.stage(retry, forbidden).reason());
        assertEquals(StageReason.PRESERVE_SELECTED_STEP, service.stage(new Captured(captured.source(), captured.wrapper(),
                Step.OTHER, captured.frame(), captured.root(), captured.capabilities()), forbidden).reason());
        assertEquals(StageReason.READERS_DISABLED, service.stage(new Captured(captured.source(), captured.wrapper(),
                captured.selectedStep(), captured.frame(), captured.root(), new Capabilities(true, false, false)), forbidden).reason());
    }

    @Test void actualNewStartOwnsTurnOnlyAfterIndependentFormalPostcondition() {
        Port port = new Port(); port.formal = formal("applied", true);
        Execution result = service.execute(staged(base()), port);
        Started started = assertInstanceOf(Started.class, result);
        assertEquals(Outcome.APPLIED, started.receipt().outcome());
        assertEquals(List.of("inputs", "query-formal", "state"), port.calls);
        assertEquals(base().frame().orElseThrow(), port.queriedFrame);
        assertEquals(BigInteger.valueOf(4), port.queriedFrame.publicRevision());
        assertEquals(BigInteger.valueOf(3), port.queriedFrame.nativeRevision());
        assertEquals(900L, port.target);
        assertEquals(0, started.receipt().schedulerState().noOperationCount());
        assertFalse(started.receipt().samePidOrRuntimeClaim());
        JsonNode encoded = StrictJson.parse(OrdinarySwayExecutionWire.encode(result));
        assertEquals("executed", encoded.path("status").textValue());
        assertTrue(encoded.path("result").path("postcondition_verified").booleanValue());
        assertTrue(encoded.path("following_plan").isNull());
    }

    @Test void ackPendingUnknownAndUnverifiedAppliedNeverOwnTurnOrReplay() {
        for (String status : List.of("receipt_pending", "postcondition_pending", "submission_unresolved", "pending_recovery", "applied", "future_status")) {
            Port port = new Port(); port.formal = formal(status, false);
            Continued result = assertInstanceOf(Continued.class, service.execute(staged(base()), port));
            assertEquals(List.of("inputs", "query-formal", "state", "fresh-ordinary"), port.calls, status);
            Outcome expected = List.of("applied", "future_status").contains(status) ? Outcome.OBSERVED : Outcome.PENDING;
            assertEquals(expected, result.receipt().orElseThrow().outcome(), status);
            assertEquals(0, result.receipt().orElseThrow().schedulerState().noOperationCount());
            assertEquals("fresh-current-plan", StrictJson.parse(OrdinarySwayExecutionWire.encode(result)).path("following_plan").path("id").textValue());
        }
    }

    @Test void executorRereadsOriginalPendingAndNeverSubmitsNewOpportunityAcrossIt() {
        Port port = new Port();
        port.inputs = Optional.of(new Inputs(new Ledger(Optional.of(new Pending("original", 7, 900)), Optional.empty()), Optional.empty()));
        Continued result = assertInstanceOf(Continued.class, service.execute(staged(base()), port));
        assertEquals(Outcome.PENDING, result.receipt().orElseThrow().outcome());
        assertEquals(LocalStatus.ORIGINAL_PENDING_PRESERVED, ((LocalResult) result.receipt().orElseThrow().result()).status());
        assertEquals(List.of("inputs", "state", "fresh-ordinary"), port.calls);

        Request pending = withLedger(base(), new Ledger(Optional.of(new Pending("original", 7, 900)), Optional.empty()));
        Port changed = new Port();
        changed.inputs = Optional.of(new Inputs(new Ledger(Optional.of(new Pending("other", 7, 900)), Optional.empty()), Optional.empty()));
        Continued mismatch = assertInstanceOf(Continued.class, service.execute(staged(pending), changed));
        assertEquals(LocalStatus.PENDING_IDENTITY_CHANGED, ((LocalResult) mismatch.receipt().orElseThrow().result()).status());
        assertEquals(List.of("inputs", "state", "fresh-ordinary"), changed.calls);

        Port recovery = new Port(); recovery.inputs = Optional.of(new Inputs(pending.ledger(), Optional.empty())); recovery.formal = formal("applied", true);
        Continued recovered = assertInstanceOf(Continued.class, service.execute(staged(pending), recovery));
        assertEquals(Outcome.OBSERVED, recovered.receipt().orElseThrow().outcome(), "recovery is not a new Start");
        assertEquals(List.of("inputs", "query-formal", "state", "fresh-ordinary"), recovery.calls);
    }

    @Test void unavailableInputOrQueryKeepsOrdinaryProgressAndUnknownIntent() {
        Port absent = new Port(); absent.inputs = Optional.empty();
        Continued unavailable = assertInstanceOf(Continued.class, service.execute(staged(base()), absent));
        assertTrue(unavailable.receipt().isEmpty());
        assertEquals(LocalStatus.INPUTS_ABSENT, unavailable.unavailable().orElseThrow().status());
        assertEquals(List.of("inputs", "fresh-ordinary"), absent.calls);
        Port failed = new Port(); failed.failQuery = true;
        Continued queried = assertInstanceOf(Continued.class, service.execute(staged(base()), failed));
        assertEquals(Outcome.UNAVAILABLE, queried.receipt().orElseThrow().outcome());
        assertEquals(0, queried.receipt().orElseThrow().schedulerState().noOperationCount());
        assertEquals(List.of("inputs", "query-formal", "state", "fresh-ordinary"), failed.calls);
    }

    @Test void stateWriteFailureAfterActualStartCannotCauseSecondStart() {
        Port port = new Port(); port.formal = formal("applied", true); port.failSave = true;
        Started result = assertInstanceOf(Started.class, service.execute(staged(base()), port));
        assertEquals(Optional.of("state disk unavailable"), result.receipt().stateWriteError());
        assertEquals(List.of("inputs", "query-formal", "state"), port.calls);
    }

    @Test void observedEmptyFrontierCompletesWithoutNativeQueryAndTrueNoopsKeepCooldown() {
        Request request = base(); Root root = request.root().orElseThrow();
        Root empty = new Root(root.available(), root.actorCharacterId(), root.alive(), root.nativeRevision(), root.dateRaw(), Optional.of(List.of()));
        Request emptyRequest = new Request(request.source(), request.frame(), request.selectedStep(), Optional.of(empty), request.ledger(), request.state(), false);
        Port port = new Port();
        Continued result = assertInstanceOf(Continued.class, service.execute(staged(emptyRequest), port));
        State first = result.receipt().orElseThrow().schedulerState();
        assertEquals(1, first.noOperationCount()); assertEquals(Optional.of(BigInteger.valueOf(1024)), first.nextCheckDateRaw());
        assertEquals(List.of("inputs", "state", "fresh-ordinary"), port.calls);
        Frame frame = request.frame().orElseThrow();
        Frame tomorrow = new Frame(frame.snapshotId(), frame.publicRevision(), frame.nativeRevision(), BigInteger.valueOf(1024),
                frame.actorCharacterId(), frame.paused(), frame.mapReady(), frame.alive(), frame.context());
        Root laterRoot = new Root(true, 7, true, tomorrow.nativeRevision(), tomorrow.dateRaw(), Optional.of(List.of()));
        Request second = new Request(request.source(), Optional.of(tomorrow), Step.LIFE_ADVANCE, Optional.of(laterRoot), Ledger.empty(), Optional.of(first), false);
        Continued secondResult = assertInstanceOf(Continued.class, service.execute(staged(second), new Port()));
        assertEquals(2, secondResult.receipt().orElseThrow().schedulerState().noOperationCount());
        assertEquals(Optional.of(BigInteger.valueOf(1744)), secondResult.receipt().orElseThrow().schedulerState().nextCheckDateRaw());
    }

    @Test void lifecycleObservationRemainsIndependentFromNamedGainTerminalAndContinuation() {
        Identity identity = new Identity("original", 7, 900, 16777233, 1);
        Ledger ledger = new Ledger(Optional.empty(), Optional.of(new Resolved(identity, true, true, false, Optional.empty())));
        for (String status : List.of("observed", "query_failed")) {
            Port port = new Port(); port.inputs = Optional.of(new Inputs(ledger, Optional.empty()));
            port.lifecycle = OrdinarySwayExecutionWire.lifecycle(bytes("{\"status\":\"" + status + "\",\"native_status_raw\":0,\"named_gain_observed\":false}"));
            Continued result = assertInstanceOf(Continued.class, service.execute(staged(withLedger(base(), ledger)), port));
            Receipt receipt = result.receipt().orElseThrow();
            assertEquals(status.equals("observed") ? Outcome.OBSERVED : Outcome.UNAVAILABLE, receipt.outcome());
            assertEquals(Optional.of("original"), receipt.schedulerState().lastObservationAttemptActionId());
            assertEquals(Optional.empty(), receipt.schedulerState().lastTerminalActionId());
            assertEquals(List.of("inputs", "lifecycle", "state", "fresh-ordinary"), port.calls);
        }
    }

    @Test void existingRelationFollowupKeepsThreeNoopReasonsDistinct() {
        for (String following : List.of("finish_selected_relation", "return_to_opportunity_selection", "native_start_unavailable", "unknown")) {
            Port port = new Port();
            port.formal = OrdinarySwayExecutionWire.formal(bytes("{\"status\":\"already_applied\",\"followup\":{\"decision\":\"" + following + "\"}}"));
            Continued result = assertInstanceOf(Continued.class, service.execute(staged(base()), port));
            assertEquals(following.equals("unknown") ? Outcome.OBSERVED : Outcome.NO_OPERATION, result.receipt().orElseThrow().outcome());
            assertEquals(following, StrictJson.parse(OrdinarySwayExecutionWire.encode(result)).path("ordinary_sway_optional").path("result").path("followup").path("decision").textValue());
        }
    }

    @Test void strictHostConsumerAndSerializerUseSingleValidatedContracts() {
        ObjectNode row = stageJson();
        JsonNode actual = StrictJson.parse(OrdinarySwayServiceWire.stage(StrictJson.canonical(row)));
        assertEquals("staged", actual.path("status").textValue());
        assertEquals(STEP, actual.path("selected_step").textValue());
        assertEquals("query_selected_target", actual.path("decision").path("job").textValue());
        assertFalse(actual.path("submit_allowed").booleanValue());
        ObjectNode bad = row.deepCopy(); bad.put("wrapper_revision", true);
        assertThrows(IllegalArgumentException.class, () -> OrdinarySwayServiceWire.stage(StrictJson.canonical(bad)));
        ObjectNode drift = row.deepCopy(); drift.put("wrapper_revision", 5);
        assertEquals("captured_frame_changed", StrictJson.parse(OrdinarySwayServiceWire.stage(StrictJson.canonical(drift))).path("reason").textValue());
        assertThrows(IllegalArgumentException.class, () -> OrdinarySwayExecutionWire.formal(bytes("{\"status\":\"applied\",\"postcondition_verified\":1}")));
        assertThrows(IllegalArgumentException.class, () -> OrdinarySwayExecutionWire.formal(bytes("{\"status\":\"applied\",\"status\":\"receipt_pending\"}")));
        Port port = new Port(); port.formal = OrdinarySwayExecutionWire.formal(bytes("{\"status\":\"future_status\",\"cost\":0.125,\"long_id\":\"18446744073709551615\"}"));
        JsonNode encoded = StrictJson.parse(OrdinarySwayExecutionWire.encode(service.execute(staged(base()), port)));
        assertEquals("18446744073709551615", encoded.path("ordinary_sway_optional").path("result").path("long_id").textValue());
        assertEquals(new java.math.BigDecimal("0.125"), encoded.path("ordinary_sway_optional").path("result").path("cost").decimalValue());
        byte[] fullEvidence = bytes("{\"status\":\"receipt_pending\",\"opaque\":\"" + "x".repeat(StrictJson.EXPLICIT_MAX_BYTES + 16) + "\"}");
        FormalResult large = OrdinarySwayExecutionWire.formal(fullEvidence);
        assertEquals(fullEvidence.length, large.evidence().size(), "opaque evidence uses its actual projection role budget");
    }

    @Test void exactSourcePhaseEndStrategyReferencesNeverBecomeOutcomeFacts() {
        G2Source source = new G2Source(base().source().machineId(), base().source().observedAtUtc(), "1.20.0.4",
                new ExactRef("stock/00_scheme_scripted_effects.txt", StockSwayPhaseEndProfile.SOURCE_BYTES, StockSwayPhaseEndProfile.SOURCE_SHA256));
        var profile = StockSwayPhaseEndProfile.sourceBound(source);
        assertEquals(List.of(10, 10, 30, 50, 100), profile.orderedAiBranches().stream().map(StockSwayPhaseEndProfile.EndReference::percent).toList());
        assertTrue(profile.phaseSuccessCanContinueSameInstance()); assertFalse(profile.namedGainOrTerminalClaimed());
        assertFalse(profile.evaluatesNativeCanContinue()); assertFalse(profile.changesOrdinaryPolicy());
        assertThrows(IllegalArgumentException.class, () -> StockSwayPhaseEndProfile.sourceBound(new G2Source(source.machineId(), source.observedAtUtc(), "1.19.0.6", source.sourceRef())));
        var lifecycle = StockSwayLifecycleProfile.sourceBound(new G2Source(source.machineId(), source.observedAtUtc(), "1.20.0.4",
                new ExactRef("stock/sway_scheme.txt", StockSwayLifecycleProfile.SOURCE_BYTES, StockSwayLifecycleProfile.SOURCE_SHA256)));
        assertEquals(List.of(StockSwayLifecycleProfile.TriggerGroup.DEAD_ELSE_WAR,
                StockSwayLifecycleProfile.TriggerGroup.DEAD_ELSE_WAR,
                StockSwayLifecycleProfile.TriggerGroup.INDEPENDENT_DIPLOMATIC_RANGE), lifecycle.invalidationNotifications().stream().map(StockSwayLifecycleProfile.NotificationReference::group).toList());
        assertTrue(lifecycle.invalidationRangeBranchIsIndependent());
        assertEquals(List.of("sway_success", "sway_failure"), lifecycle.phaseOutcomeActions());
        assertFalse(lifecycle.notificationProvesNativeEndCause()); assertFalse(lifecycle.phaseSuccessIsFinalTerminal());
        assertFalse(lifecycle.evaluatesCurrentValidityOrRoll());
    }

    private Staged staged(Request request) {
        return service.stage(captured(request), () -> Optional.of(new Inputs(request.ledger(), request.state()))).staged().orElseThrow();
    }
    private static Captured captured(Request request) {
        Frame frame = request.frame().orElseThrow();
        return new Captured(request.source(), new Wrapper(frame.snapshotId(), frame.publicRevision()), request.selectedStep(), request.frame(), request.root(), new Capabilities(true, true, true));
    }
    private static Request base() {
        try (InputStream stream = OrdinarySwayServiceTest.class.getResourceAsStream("/schemesway/producer-golden-v1.json")) {
            if (stream == null) { throw new IllegalStateException("required committed golden missing"); }
            return SwayScheduleWire.decode(StrictJson.canonical(StrictJson.parse(stream.readAllBytes(), 262144).path("plan_cases").get(0).get("input")));
        } catch (java.io.IOException failure) { throw new IllegalStateException(failure); }
    }
    private static ObjectNode stageJson() {
        try (InputStream stream = OrdinarySwayServiceTest.class.getResourceAsStream("/schemesway/producer-golden-v1.json")) {
            if (stream == null) { throw new IllegalStateException("required committed golden missing"); }
            ObjectNode row = StrictJson.object(); row.put("schema", OrdinarySwayServiceWire.REQUEST_SCHEMA);
            row.put("wrapper_snapshot_id", base().frame().orElseThrow().snapshotId()); row.put("wrapper_revision", 4);
            row.put("formal_query_enabled", true); row.put("formal_action_enabled", true); row.put("lifecycle_reader_enabled", true);
            row.set("request", StrictJson.parse(stream.readAllBytes(), 262144).path("plan_cases").get(0).get("input")); return row;
        } catch (java.io.IOException failure) { throw new IllegalStateException(failure); }
    }
    private static Request withLedger(Request request, Ledger ledger) {
        return new Request(request.source(), request.frame(), request.selectedStep(), request.root(), ledger, request.state(), request.activeObservationOnly());
    }
    private static FormalResult formal(String status, boolean post) {
        return OrdinarySwayExecutionWire.formal(bytes("{\"status\":\"" + status + "\",\"postcondition_verified\":" + post + ",\"action_id\":\"actual-consumer-action\"}"));
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static ProjectionJson projection(String value) { return ProjectionJson.object(bytes(value), ProjectionJson.MAX_BYTES); }

    private static final class Port implements ExecutionPort {
        private final List<String> calls = new ArrayList<>();
        private Optional<Inputs> inputs = Optional.of(new Inputs(Ledger.empty(), Optional.empty()));
        private FormalResult formal = formal("no_positive_opportunity", false);
        private LifecycleResult lifecycle = OrdinarySwayExecutionWire.lifecycle(bytes("{\"status\":\"observed\"}"));
        private boolean failQuery;
        private boolean failSave;
        private Frame queriedFrame;
        private long target;
        @Override public Optional<Inputs> loadInputs() { calls.add("inputs"); return inputs; }
        @Override public FormalResult queryAndConsume(Frame frame, long targetCharacterId) {
            calls.add("query-formal"); queriedFrame = frame; target = targetCharacterId;
            if (failQuery) { throw new Unavailable("original writer retains unresolved durable intent"); } return formal;
        }
        @Override public LifecycleResult observeLifecycle(Frame frame) { calls.add("lifecycle"); return lifecycle; }
        @Override public Optional<String> saveScheduler(State state) {
            calls.add("state"); if (failSave) { throw new Unavailable("state disk unavailable"); } return Optional.empty();
        }
        @Override public OrdinaryContinuation executeFreshOrdinary() {
            calls.add("fresh-ordinary"); return new OrdinaryContinuation(projection("{\"status\":\"executed\"}"), projection("{\"id\":\"fresh-current-plan\"}"));
        }
    }
}
