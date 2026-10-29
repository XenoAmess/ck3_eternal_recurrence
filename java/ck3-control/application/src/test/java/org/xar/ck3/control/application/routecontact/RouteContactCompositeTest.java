package org.xar.ck3.control.application.routecontact;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.routecontact.RouteContactModel.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.AdvanceObservationPort;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.action.ObservationProvenance;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Runs the real route handler's exact-day/refresh/UNKNOWN/strict-followup branches, without a native connection. */
final class RouteContactCompositeTest {
    static final Instant NOW = Instant.parse("2026-10-23T15:30:00Z");
    static final ExactRef EVIDENCE = new ExactRef("D:/fixture/route-contact.json", 1, "a".repeat(64));
    static final G2Source SOURCE = new G2Source("xenoamess-full-tower-eb9d2c1186", NOW.toString(), "1.20.0.4", EVIDENCE);
    static final JointBudgetSelector.Claims CLAIMS = new JointBudgetSelector.Claims(RouteContactProofsTest.starting().controlledIds().stream().map(BigInteger::valueOf).collect(java.util.stream.Collectors.toSet()), Set.of(), Set.of(), Set.of());
    static final Frame START = RouteContactProofsTest.starting();
    static AdvanceObservationPort.Frame raw(Frame frame) {
        var fields = new LinkedHashMap<String, Value>();
        fields.put("snapshot_id", new Text(frame.snapshotId())); fields.put("revision", new IntegerValue(frame.revision())); fields.put("native_revision", new IntegerValue(frame.nativeRevision()));
        fields.put("date_raw", n(frame.dateRaw())); fields.put("episode_run_id", new Text(frame.owner().episodeRunId()));
        fields.put("episode_character_id", n(frame.owner().episodeCharacterId())); fields.put("local_player_id", n(frame.owner().localPlayerId()));
        fields.put("played_character", new Obj(Map.of("character_id", n(frame.owner().episodeCharacterId()))));
        fields.put("map_ready", new Bool(frame.mapReady())); fields.put("paused", new Bool(frame.paused())); fields.put("speed", n(frame.speed()));
        fields.put("one_life_terminal", new Bool(frame.oneLifeTerminal())); fields.put("played_character_alive", new Bool(frame.playedCharacterAlive()));
        fields.put("one_life_terminal_reason", Nil.INSTANCE); fields.put("active_event", frame.activeEvent()); fields.put("pending_character_interaction", frame.pendingInteraction());
        fields.put("top_exclusive_modal_choice_hint", frame.modal());
        fields.put("diagnostics", new Obj(Map.of("bridge_pid", n(frame.owner().bridgePid()), "connection_generation", new IntegerValue(frame.owner().connectionGeneration()))));
        fields.put("player_armies", new Arr(frame.ownArmies().stream().map(RouteContactCompositeTest::armyJson).map(Value.class::cast).toList()));
        fields.put("active_wars", new Arr(List.of(new Obj(Map.of("war_id", n(1), "enemy_armies", new Arr(frame.hostileArmies().stream().map(RouteContactCompositeTest::armyJson).map(Value.class::cast).toList()))))));
        var identity = new ObservationIdentity(frame.owner().machineId(), frame.owner().game(),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(frame.owner().episodeCharacterId()), frame.nativeRevision(), BigInteger.valueOf(frame.dateRaw())),
                        frame.snapshotId(), frame.revision(), frame.owner().episodeRunId()), 1);
        return new AdvanceObservationPort.Frame(identity, SOURCE, frame.owner().sessionId(), new Obj(fields),
                new ObservationProvenance.Push(frame.snapshotId(), frame.nativeRevision(), EVIDENCE), NOW.plusSeconds(1), EVIDENCE);
    }
    static Obj armyJson(Army army) {
        return new Obj(Map.of("army_id", n(army.armyId()), "current_province_id", n(army.currentProvinceId()),
                "move_target_province_id", army.targetProvinceId().<Value>map(RouteContactCompositeTest::n).orElse(Nil.INSTANCE),
                "route_province_ids", new Arr(army.remainingRoute().stream().map(RouteContactCompositeTest::n).map(Value.class::cast).toList()),
                "controllable", new Bool(army.controllable()), "army_state", army.state().<Value>map(Text::new).orElse(Nil.INSTANCE),
                "army_state_code", army.stateCode().<Value>map(RouteContactCompositeTest::n).orElse(Nil.INSTANCE),
                "in_combat", new Bool(army.inCombat()), "retreating", new Bool(army.retreating())));
    }
    static IntegerValue n(int value) { return new IntegerValue(BigInteger.valueOf(value)); }
    static IntegerValue n(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    static ActionCommand command(boolean window) {
        var before = raw(START).identity();
        var provisional = new ActionCommand("route-a", before, SOURCE, "session-1", new OperationKey(window ? "advance-route-contact-window-v1-0-to-20-days-3-h-1-8" : "advance-route-contact-horizon-v1-0-to-20-h-1-8"),
                new Obj(Map.of()), new ExpectedPostcondition(1, before, SOURCE, RouteContactComposite.OBSERVER, List.of()), CLAIMS, NOW.plusSeconds(30));
        var actual = new Fixture(); actual.endpoint = !window; Proof proof = actual.handler().project(provisional);
        return new ActionCommand(provisional.actionId(), before, SOURCE, provisional.sessionId(), provisional.operation(), provisional.arguments(),
                new ExpectedPostcondition(1, before, SOURCE, RouteContactComposite.OBSERVER, RouteContactComposite.expected(proof)), CLAIMS, provisional.deadline());
    }
    static final class TestChildren implements CompositeActionPort.Children {
        final List<ActionReceipt> rows = new ArrayList<>(); int submissions;
        @Override public String nextActionId() { return "route-a.child-" + (submissions + 1); }
        @Override public List<ActionReceipt> completed() { return List.copyOf(rows); }
        @Override public ActionReceipt submit(ActionCommand child) { throw new AssertionError("clock fixture must explicitly preserve its original child receipt"); }
    }
    /** Typed controller DATA only; no receive custody, native source, writer or dispatch qualification is claimed. */
    static ActionReceipt pauseReceipt(ActionCommand parent, AdvanceObservationPort.Frame ending, boolean unknown) {
        ActionCommand child = AdvancePrimitives.child(parent, ending, "route-a.refresh", "pause-map", parent.deadline());
        if (unknown) return new ActionReceipt(1, 1, child, ActionCodec.bodySha256(child), new ActionState.Unknown(Optional.empty(), Optional.empty(), "lost ACK", List.of(EVIDENCE)));
        GuardEvidence guard = new GuardEvidence(ending.identity(), SOURCE, "session-1", BigInteger.ONE, child.operation(), EVIDENCE, EVIDENCE, "authority-1", NOW, NOW.plusSeconds(30));
        NativeRequest request = new NativeRequest("pause-map", "game.command.pause-map", new RawJson("{}".getBytes(StandardCharsets.UTF_8)));
        ActionState.Attempt attempt = new ActionState.Attempt("refresh-request", NOW, guard, request);
        var ack = new NativeActionPort.AckReceived("refresh-request", true, Optional.of(new RawJson("{\"step\":\"pause-map\",\"accepted\":true,\"status\":\"already_paused\"}".getBytes(StandardCharsets.UTF_8))), new RawJson("{}".getBytes(StandardCharsets.UTF_8)), new byte[]{1});
        var effect = new ActionState.EffectObservation(ending.identity(), SOURCE, "session-1", AdvancePrimitives.TIMELINE_OBSERVER,
                PauseConfirmation.actualValues(), "refresh-effect-read", NOW.plusSeconds(1), EVIDENCE);
        return new ActionReceipt(1, 1, child, ActionCodec.bodySha256(child), new ActionState.Settled(attempt, ack, new ActionState.PauseConfirmed(effect)));
    }
    static final class Fixture implements AdvanceObservationPort, RouteContactComposite.History, RouteContactComposite.Clocks, RouteContactComposite.EvidenceArchive {
        AdvanceObservationPort.Frame start = raw(START);
        AdvanceObservationPort.Frame end = raw(RouteContactProofsTest.frame(2, 124, START.ownArmies(), START.hostileArmies()));
        AdvanceObservationPort.Frame refreshed = raw(RouteContactProofsTest.frame(3, 124, START.ownArmies(), START.hostileArmies()));
        boolean endpoint = true, unknown, unknownRefresh, readbackUnavailable, missingQuery, legacyPause; int exactCalls, windowCalls, refreshCalls, nextCalls, failures, completions;
        RouteContactComposite.ContactFailure lastFailure;
        String refreshStatus = "already_paused"; List<TimelineEntry> prior = List.of(); List<ExactRef> clockFailureEvidence = List.of();
        RouteContactComposite handler() { return new RouteContactComposite(this, this, this, new RouteContactComposite.Settings(3, false), Clock.fixed(NOW, ZoneOffset.UTC), this); }
        @Override public AdvanceObservationPort.Frame current(ActionCommand parent, Instant deadline) { return start; }
        @Override public AdvanceObservationPort.Frame next(ActionCommand parent, ObservationIdentity after, Instant deadline) { nextCalls++; if (readbackUnavailable) throw new IllegalStateException("source-bound refresh frame unavailable"); return refreshed; }
        @Override public List<RouteContactProofs.QueryEntry> survivingQueries(ActionCommand parent) {
            if (missingQuery) return List.of();
            RouteQuery query = endpoint ? RouteContactProofsTest.endpointQuery(START) : RouteContactProofsTest.query(START);
            return List.of(new RouteContactProofs.QueryEntry(new RouteContactProofs.Scope(0, 20, List.of(8)), Optional.of(query)));
        }
        @Override public List<TimelineEntry> survivingTimeline(ActionCommand parent) { return prior; }
        @Override public RouteContactComposite.ClockResult window(ActionCommand parent, CompositeActionPort.Children children, AdvanceObservationPort.Frame starting, Proof proof, int speed) {
            windowCalls++;
            if (unknown) return SharedRouteContactClocks.unresolved(starting, "unknown window", clockFailureEvidence, speed, "bounded_frozen_route_window");
            return new RouteContactComposite.ClockResult(end, true, false, "verified window");
        }
        @Override public RouteContactComposite.ClockResult exactDay(ActionCommand parent, CompositeActionPort.Children children, AdvanceObservationPort.Frame starting, Proof proof, int speed) {
            exactCalls++; assertEquals(endpoint ? 1 : 3, speed);
            return unknown ? SharedRouteContactClocks.unresolved(starting, "unknown exact day", List.of(), speed, "exact_one_day_unresolved")
                    : RouteContactEvidenceTest.reportedExact(parent, starting, end, speed);
        }
        @Override public RouteContactComposite.PauseRefresh refreshPaused(ActionCommand parent, CompositeActionPort.Children children, AdvanceObservationPort.Frame ending, Instant deadline) {
            refreshCalls++; var receipt = pauseReceipt(parent, ending, unknownRefresh);
            if (legacyPause && receipt.state() instanceof ActionState.Settled settled) receipt = new ActionReceipt(receipt.version(), receipt.sequence(), receipt.command(), receipt.bodySha256(),
                    new ActionState.Settled(settled.attempt(), settled.dispatch(), new ActionState.Applied(((ActionState.PauseConfirmed)settled.settlement()).observation())));
            ((TestChildren)children).rows.add(receipt); return new RouteContactComposite.PauseRefresh(receipt, refreshStatus);
        }
        @Override public ExactRef completed(ActionCommand parent, RouteContactComposite.Completion completion) { completions++; return EVIDENCE; }
        @Override public ExactRef failed(ActionCommand parent, RouteContactComposite.ContactFailure failure) { failures++; lastFailure = failure; return EVIDENCE; }
    }
    @Test void originalUnavoidableBranchUsesOneSameDateRefreshAndPreservesPrediction() throws InterruptedException {
        Fixture fixture = new Fixture(); var result = fixture.handler().run(command(false), new TestChildren());
        assertInstanceOf(ActionPorts.EffectObserved.class, result); assertEquals(1, fixture.exactCalls); assertEquals(1, fixture.refreshCalls); assertEquals(1, fixture.nextCalls);
        var actual = ((ActionPorts.EffectObserved) result).observation().actual();
        assertTrue(actual.contains(new ExpectedBoolean(new FieldKey("contact_transition.contact_observed"), false))); assertEquals(1, fixture.completions);
    }
    @Test void unknownClockCannotSubmitRefreshOrRunAnotherDay() throws InterruptedException {
        Fixture fixture = new Fixture(); fixture.unknown = true;
        assertInstanceOf(ActionPorts.Pending.class, fixture.handler().run(command(false), new TestChildren()));
        assertEquals(1, fixture.exactCalls); assertEquals(0, fixture.refreshCalls); assertEquals(0, fixture.nextCalls); assertEquals(1, fixture.failures);
    }
    @Test void actualClockFailureOriginalRefsSurviveTheParentPendingWithoutAProgressClaim() throws InterruptedException {
        Fixture fixture = new Fixture(); fixture.endpoint = false; fixture.unknown = true;
        ExactRef basis = new ExactRef("D:/fixture/actual-clock-failure-basis", 71, "c".repeat(64));
        ExactRef status = new ExactRef("D:/fixture/actual-clock-status-packet", 79, "d".repeat(64));
        fixture.clockFailureEvidence = List.of(basis, status); TestChildren children = new TestChildren();
        var pending = assertInstanceOf(ActionPorts.Pending.class, fixture.handler().run(command(true), children));
        assertEquals(List.of(EVIDENCE, fixture.start.originalEvidence(), basis, status), pending.evidence());
        assertEquals(List.of(basis, status), fixture.lastFailure.failureEvidence()); assertEquals(fixture.start, fixture.lastFailure.ending());
        assertEquals(1, fixture.windowCalls); assertEquals(0, fixture.exactCalls); assertEquals(0, fixture.refreshCalls); assertEquals(0, fixture.nextCalls); assertEquals(0, fixture.completions);
        assertThrows(UnsupportedOperationException.class, () -> fixture.lastFailure.failureEvidence().clear());
    }
    @Test void unresolvedClockCopiesTheCompleteOriginalListAndCannotBecomeVerifiedCompletion() {
        List<ExactRef> originals = new ArrayList<>(); originals.add(EVIDENCE);
        var unresolved = SharedRouteContactClocks.unresolved(raw(START), "actual original failure", originals, 3, "bounded_frozen_route_window"); originals.clear();
        assertEquals(List.of(EVIDENCE), unresolved.failureEvidence()); assertTrue(unresolved.unknown()); assertFalse(unresolved.nativeClockVerified()); assertFalse(unresolved.checkpointEligible());
        assertThrows(UnsupportedOperationException.class, () -> unresolved.failureEvidence().clear());
        assertThrows(IllegalArgumentException.class, () -> new RouteContactComposite.ClockResult(raw(START), true, false, "invalid verified failure",
                RouteContactComposite.ClockProgress.POSTCONDITION, 3, "bounded_frozen_route_window", true, Optional.empty(), List.of(EVIDENCE)));
    }
    @Test void lostRefreshAckCannotCauseAnotherRefresh() throws InterruptedException {
        Fixture fixture = new Fixture(); fixture.unknownRefresh = true;
        assertInstanceOf(ActionPorts.Pending.class, fixture.handler().run(command(false), new TestChildren()));
        assertEquals(1, fixture.refreshCalls); assertEquals(0, fixture.nextCalls); assertEquals(0, fixture.completions);
    }
    @Test void wrongRefreshAckCannotPretendTheSamePausedWindowWasRefreshed() throws InterruptedException {
        Fixture fixture = new Fixture(); fixture.refreshStatus = "paused";
        assertInstanceOf(ActionPorts.Pending.class, fixture.handler().run(command(false), new TestChildren())); assertEquals(0, fixture.nextCalls);
    }
    @Test void strictFollowupFailsAfterItsSingleRefreshWithoutAnotherGeometryCredit() throws InterruptedException {
        Fixture fixture = new Fixture(); var boundary = new Transition(TransitionKind.PREDICTED_CONTACT_BOUNDARY_REACHED, false, "episode-1", 0, 10, 76, 100, List.of(8));
        fixture.prior = List.of(new AdvanceHistory(true, 0, "episode-1", 100, Optional.of(boundary), false));
        var result = assertInstanceOf(ActionPorts.Pending.class, fixture.handler().run(command(false), new TestChildren()));
        assertEquals(fixture.lastFailure.originalErrorMessage().orElseThrow(), result.reason()); assertEquals("exhausted_without_strong_transition", fixture.lastFailure.status());
        assertEquals(1, fixture.refreshCalls); assertEquals(1, fixture.failures); assertEquals(0, fixture.completions);
    }
    @Test void unavailableRefreshReadbackKeepsTheStrictFollowupFailureMarker() throws InterruptedException {
        Fixture fixture = new Fixture(); fixture.readbackUnavailable = true;
        var boundary = new Transition(TransitionKind.PREDICTED_CONTACT_BOUNDARY_REACHED, false, "episode-1", 0, 10, 76, 100, List.of(8));
        fixture.prior = List.of(new AdvanceHistory(true, 0, "episode-1", 100, Optional.of(boundary), false));
        assertInstanceOf(ActionPorts.Pending.class, fixture.handler().run(command(false), new TestChildren()));
        assertEquals(1, fixture.refreshCalls); assertEquals(1, fixture.nextCalls); assertTrue(fixture.lastFailure.strictFollowupUnresolved());
    }
    @Test void boundedWindowUsesSharedBattleClockAndNeverOneDayRefresh() throws InterruptedException {
        Fixture fixture = new Fixture(); fixture.endpoint = false; fixture.end = raw(RouteContactProofsTest.frame(2, 172, START.ownArmies(), START.hostileArmies()));
        assertInstanceOf(ActionPorts.EffectObserved.class, fixture.handler().run(command(true), new TestChildren()));
        assertEquals(1, fixture.windowCalls); assertEquals(0, fixture.exactCalls); assertEquals(0, fixture.refreshCalls);
    }
    @Test void staleStartingRevisionFailsBeforeEitherClockExecutes() {
        Fixture fixture = new Fixture(); fixture.start = raw(RouteContactProofsTest.frame(2, 100, START.ownArmies(), START.hostileArmies()));
        assertThrows(IllegalArgumentException.class, () -> fixture.handler().validate(command(false))); assertEquals(0, fixture.exactCalls); assertEquals(0, fixture.windowCalls);
    }
    @Test void forcedRefreshMustStayOnTheSameDateAndConnection() throws InterruptedException {
        Fixture fixture = new Fixture(); fixture.refreshed = raw(RouteContactProofsTest.frame(3, 148, START.ownArmies(), START.hostileArmies()));
        assertInstanceOf(ActionPorts.Pending.class, fixture.handler().run(command(false), new TestChildren())); assertEquals(0, fixture.completions);
    }
    @Test void strictIntegerDomainSurvivesJsonRoundtripAndRejectsBooleanRevision() {
        AdvanceObservationPort.Frame raw = raw(START);
        Obj roundtrip = OpportunityJson.object(OpportunityJson.parse(OpportunityJson.encode(raw.semantic())), "roundtrip");
        assertEquals(START, RouteContactCodec.frame(new AdvanceObservationPort.Frame(raw.identity(), raw.source(), raw.sessionId(), roundtrip, raw.provenance(), raw.observedAt(), raw.originalEvidence())));
        assertThrows(IllegalArgumentException.class, () -> new AdvanceObservationPort.Frame(raw.identity(), raw.source(), raw.sessionId(), roundtrip.with("native_revision", new Bool(true)), raw.provenance(), raw.observedAt(), raw.originalEvidence()));
    }
    @Test void detachedCapabilityFrameUsesTheSameIdentityBoundParser() {
        var raw = raw(START);
        assertEquals(START, RouteContactCodec.frame(raw.identity(), raw.source(), raw.sessionId(), raw.semantic()));
        assertThrows(IllegalArgumentException.class, () -> RouteContactCodec.frame(raw.identity(), raw.source(), raw.sessionId(), raw.semantic().with("revision", n(999))));
        assertThrows(IllegalArgumentException.class, () -> RouteContactCodec.frame(raw.identity(), raw.source(), raw.sessionId(), raw.semantic().with("native_revision", new Bool(true))));
        var missing = new LinkedHashMap<String, Value>(raw.semantic().members()); missing.remove("active_event");
        assertThrows(IllegalArgumentException.class, () -> RouteContactCodec.frame(raw.identity(), raw.source(), raw.sessionId(), new Obj(missing)));
    }
    @Test void projectedProofIsPureAndSubmissionRequiresItsExactExpectationAndOwnedClaims() {
        Fixture fixture = new Fixture(); ActionCommand actual = command(false);
        assertEquals(fixture.handler().project(actual), fixture.handler().project(actual));
        assertEquals(0, fixture.exactCalls + fixture.windowCalls + fixture.refreshCalls + fixture.nextCalls + fixture.failures + fixture.completions);
        var wrongExpected = new ActionCommand(actual.actionId(), actual.before(), actual.source(), actual.sessionId(), actual.operation(), actual.arguments(),
                new ExpectedPostcondition(1, actual.before(), actual.source(), RouteContactComposite.OBSERVER, List.of()), actual.claims(), actual.deadline());
        assertThrows(IllegalArgumentException.class, () -> fixture.handler().validate(wrongExpected));
        for (Set<BigInteger> armies : List.of(Set.<BigInteger>of(), Set.of(BigInteger.ZERO, BigInteger.valueOf(8)))) {
            var bad = new ActionCommand(actual.actionId(), actual.before(), actual.source(), actual.sessionId(), actual.operation(), actual.arguments(), actual.expected(),
                    new JointBudgetSelector.Claims(armies, Set.of(), Set.of(), Set.of()), actual.deadline());
            assertThrows(IllegalArgumentException.class, () -> fixture.handler().validate(bad));
        }
        fixture.handler().validate(actual);
        assertEquals(0, fixture.exactCalls + fixture.windowCalls + fixture.refreshCalls);
    }
    @Test void onlyMissingProofGetsTheTypedPublicUnavailableFailure() {
        Fixture fixture = new Fixture(); fixture.missingQuery = true;
        assertThrows(RouteContactComposite.ProofUnavailable.class, () -> fixture.handler().project(command(false)));
        fixture.missingQuery = false; fixture.start = raw(RouteContactProofsTest.frame(2, 100, START.ownArmies(), START.hostileArmies()));
        var sourceError = assertThrows(IllegalArgumentException.class, () -> fixture.handler().project(command(false)));
        assertFalse(sourceError instanceof RouteContactComposite.ProofUnavailable);
        assertEquals(0, fixture.exactCalls + fixture.windowCalls + fixture.refreshCalls);
    }
    @Test void historicalAppliedPauseCannotAuthorizeANewRefreshReadback() throws InterruptedException {
        Fixture fixture = new Fixture(); fixture.legacyPause = true; TestChildren children = new TestChildren();
        assertInstanceOf(ActionPorts.Pending.class, fixture.handler().run(command(false), children));
        assertEquals(1, fixture.refreshCalls); assertEquals(0, fixture.nextCalls); assertEquals(0, fixture.completions);
        assertFalse(RouteContactComposite.currentPauseConfirmed(children.completed().getLast()));
        assertTrue(fixture.lastFailure.clockResult().orElseThrow().originalReport().isPresent());
        assertTrue(fixture.lastFailure.refresh().orElseThrow().ackStatus().isEmpty());
    }
    @Test void retainedUnknownResumeNeverReadsOrSubmitsAgainAfterTheOriginalDeadline() {
        var parent = command(false); var fixture = new Fixture();
        var guard = new GuardEvidence(parent.before(), parent.source(), parent.sessionId(), BigInteger.ONE, parent.operation(),
                EVIDENCE, EVIDENCE, "route-retained-guard", NOW, parent.deadline());
        var retained = new CompositeExecution(RouteContactComposite.HANDLER, NOW, guard,
                List.of(new CompositeExecution.Child("route-a.unknown-resume", "b".repeat(64))));
        AdvanceObservationPort readsForbidden = new AdvanceObservationPort() {
            @Override public AdvanceObservationPort.Frame current(ActionCommand ignored, Instant deadline) { throw new AssertionError("expired UNKNOWN cannot request a new frame"); }
            @Override public AdvanceObservationPort.Frame next(ActionCommand ignored, ObservationIdentity after, Instant deadline) { throw new AssertionError("expired UNKNOWN cannot request a later frame"); }
        };
        var handler = new RouteContactComposite(readsForbidden, fixture, fixture, new RouteContactComposite.Settings(3, false),
                Clock.fixed(parent.deadline().plusSeconds(60), ZoneOffset.UTC), fixture);
        for (int index = 0; index < 2; index++) {
            var pending = assertInstanceOf(ActionPorts.Pending.class, handler.observe(parent, retained));
            assertEquals(List.of(EVIDENCE), pending.evidence());
        }
        assertEquals(0, fixture.exactCalls + fixture.windowCalls + fixture.refreshCalls + fixture.nextCalls + fixture.completions);
    }
}
