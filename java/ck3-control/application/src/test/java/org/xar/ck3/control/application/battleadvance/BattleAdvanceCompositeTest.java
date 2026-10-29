package org.xar.ck3.control.application.battleadvance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.battleadvance.BattleAdvanceFixture.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Mode;
import org.xar.ck3.control.reconciliation.LateOutcome.State;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;

/** Runs the migrated production composite against scripted real-shape Native frames and durable child receipts. */
final class BattleAdvanceCompositeTest {
    @Test void actualCompositeUsesConfirmedArmAndOneResumeWithoutNoopSpeedMutation() throws Exception {
        var fixture = new BattleAdvanceFixture();
        fixture.frames.addAll(List.of(frame(1, 100, true, false), frame(2, 100, true, false), frame(3, 100, true, false), frame(4, 124, true, false), frame(5, 124, true, false)));
        fixture.statusReads.addAll(List.of(armed(), stopped()));
        var result = fixture.composite().run(parent(), fixture);
        assertInstanceOf(ActionPorts.EffectObserved.class, result);
        assertEquals(List.of(BattleAdvancePlan.ARM_PREFIX + "100-to-124-speed-3-mode-decision-a-1-0", "resume-map"), fixture.steps);
        assertEquals(1, fixture.completed.elapsedDays()); assertEquals(2, fixture.completed.actions().size());
        assertEquals(0, fixture.steps.stream().filter("pause-map"::equals).count()); assertFalse(fixture.completed.canceled());
        assertTrue(fixture.completed.queryEvidence().size() >= 2); assertNull(fixture.failed);
        assertEquals(new BigInteger("281474976710657"), BattleAdvanceFrame.decode(fixture.completed.starting()).armies().getFirst().combatId().orElseThrow());
        var material = BattleAdvanceResultCodec.completed(fixture.completed);
        var decoded = BattleAdvanceResultCodec.decode(material, BattleAdvanceResultCodec.Profile.JAVA_V1);
        assertEquals(fixture.completed.plan(), decoded.plan().orElseThrow()); assertEquals(stopped(), decoded.sentinel().orElseThrow());
        assertEquals(new OpportunityJson.Text("1"), decoded.envelope().get("sentinel_generation"));
        assertThrows(IllegalArgumentException.class, () -> BattleAdvanceResultCodec.decode(material, BattleAdvanceResultCodec.Profile.LEGACY_NATIVE_V1));
    }
    @Test void unknownResumeNeverReplaysOrSubmitsEvenCleanupPause() throws Exception {
        var fixture = new BattleAdvanceFixture(); fixture.unknownStep = "resume-map";
        fixture.frames.addAll(List.of(frame(1, 100, true, false), frame(2, 100, true, false), frame(3, 100, true, false)));
        fixture.statusReads.add(armed());
        var result = fixture.composite().run(parent(), fixture);
        assertInstanceOf(ActionPorts.Pending.class, result); assertEquals(2, fixture.steps.size()); assertEquals(3, fixture.frameReads);
        assertEquals(1, fixture.steps.stream().filter("resume-map"::equals).count()); assertFalse(fixture.steps.contains("pause-map"));
        assertNotNull(fixture.failed); assertFalse(fixture.failed.actions().getLast().settled()); assertNull(fixture.completed);
        assertEquals(new OpportunityJson.Text("postcondition_failed"), BattleAdvanceResultCodec.decode(BattleAdvanceResultCodec.failed(fixture.failed), BattleAdvanceResultCodec.Profile.JAVA_V1).envelope().get("progress_status"));
        ActionCommand command = parent();
        var guard = new GuardEvidence(command.before(), SOURCE, command.sessionId(), BigInteger.ONE, command.operation(), REF, REF, "fixture-authority", NOW, NOW.plusSeconds(3600));
        var retained = new CompositeExecution(BattleAdvanceComposite.HANDLER, NOW, guard, fixture.children.stream()
                .map(row -> new CompositeExecution.Child(row.command().actionId(), row.bodySha256())).toList());
        assertInstanceOf(ActionPorts.Pending.class, fixture.composite().observe(command, retained));
        assertEquals(2, fixture.steps.size()); assertEquals(3, fixture.frameReads);
    }
    @Test void exhaustedNativeStopWaitHasOneSeparatelyDurableCleanupPauseAndNoDayCredit() throws Exception {
        var fixture = new BattleAdvanceFixture();
        fixture.frames.add(frame(1, 100, true, false)); fixture.frames.add(frame(2, 100, true, false)); fixture.frames.add(frame(3, 100, true, false));
        for (int revision = 4; revision <= 9; revision++) fixture.frames.add(frame(revision, 124, false, false));
        fixture.frames.add(frame(10, 124, true, false)); fixture.statusReads.add(armed());
        assertInstanceOf(ActionPorts.Pending.class, fixture.composite().run(parent(), fixture));
        assertEquals(1, fixture.steps.stream().filter("pause-map"::equals).count()); assertEquals(1, fixture.steps.stream().filter("resume-map"::equals).count());
        assertEquals(3, fixture.failed.actions().size()); assertNull(fixture.completed);
    }
    @Test void cleanupPauseAckWithoutActualPauseRemainsUnknownAndDoesNotRetryPause() throws Exception {
        var fixture = new BattleAdvanceFixture(); fixture.unknownStep = "pause-map";
        fixture.frames.add(frame(1, 100, true, false)); fixture.frames.add(frame(2, 100, true, false)); fixture.frames.add(frame(3, 100, true, false));
        for (int revision = 4; revision <= 9; revision++) fixture.frames.add(frame(revision, 100, false, false));
        fixture.statusReads.add(armed());
        assertInstanceOf(ActionPorts.Pending.class, fixture.composite().run(parent(), fixture));
        assertEquals(1, fixture.steps.stream().filter("pause-map"::equals).count()); assertEquals(1, fixture.steps.stream().filter("resume-map"::equals).count());
        assertFalse(fixture.failed.actions().getLast().settled()); assertTrue(fixture.failed.cleanupError().isPresent()); assertNull(fixture.completed);
    }
    @Test void modalSelfPauseBeforeFirstDailyTickCancelsExactGenerationAndAcceptsZeroDayBoundary() throws Exception {
        var fixture = new BattleAdvanceFixture();
        fixture.frames.addAll(List.of(frame(1, 100, true, false), frame(2, 100, true, false), frame(3, 100, true, false),
                frame(4, 100, false, true), frame(5, 100, true, true), frame(6, 100, true, true), frame(7, 100, true, true)));
        fixture.statusReads.addAll(List.of(armed(), armed(), idle()));
        var result = fixture.composite().run(parent(), fixture);
        assertInstanceOf(ActionPorts.EffectObserved.class, result); assertEquals(0, fixture.completed.elapsedDays());
        assertTrue(fixture.completed.canceled()); assertFalse(fixture.steps.contains("pause-map"));
        assertEquals(BattleAdvancePlan.CANCEL_PREFIX + "1", fixture.steps.getLast());
        assertEquals(BattleAdvanceFrame.Kind.ACTIVE_EVENT, fixture.completed.decisionBoundary().orElseThrow().kind());
    }
    @Test void modalAtNativeDeadlineKeepsTriggeredStopAndNeverCancelsIt() throws Exception {
        var fixture = new BattleAdvanceFixture();
        fixture.frames.addAll(List.of(frame(1, 100, true, false), frame(2, 100, true, false), frame(3, 100, true, false), frame(4, 124, true, true), frame(5, 124, true, true)));
        fixture.statusReads.addAll(List.of(armed(), stopped()));
        assertInstanceOf(ActionPorts.EffectObserved.class, fixture.composite().run(parent(), fixture));
        assertFalse(fixture.completed.canceled()); assertEquals(2, fixture.steps.size());
    }
    @Test void modalAfterArmAtSameNativeRevisionCancelsBeforeAnyResumeAndReportsControlOnly() throws Exception {
        var fixture = new BattleAdvanceFixture();
        fixture.frames.addAll(List.of(sameNativeFrame(1, false), sameNativeFrame(2, false), sameNativeFrame(3, true), sameNativeFrame(4, true)));
        fixture.statusReads.addAll(List.of(armed(), armed(), idle()));
        var result = assertInstanceOf(ActionPorts.CompositeControlObserved.class, fixture.composite().run(parent(), fixture));
        assertEquals(List.of(BattleAdvancePlan.ARM_PREFIX + "100-to-124-speed-3-mode-decision-a-1-0", BattleAdvancePlan.CANCEL_PREFIX + "1"), fixture.steps);
        assertEquals(0, fixture.completed.elapsedDays()); assertTrue(fixture.completed.canceled());
        assertEquals(idle(), fixture.completed.nativeStopRead().status());
        assertEquals(1, result.observation().supportingReads().size());
        assertEquals(new BigInteger("1"), result.observation().semantic().after().frame().identity().nativeRevision());
        assertTrue(result.observation().semantic().actual().containsAll(List.of(
                new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("native.gameplay_verified"), false),
                new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("timeline.advance_verified"), false),
                new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("timeline.checkpoint_eligible"), false))));
        assertFalse(fixture.steps.contains("resume-map"));
    }
    @Test void directPausedSameDayModalAfterResumeIsRecognizedWithoutExhaustingWait() throws Exception {
        var fixture = new BattleAdvanceFixture();
        fixture.frames.addAll(List.of(frame(1, 100, true, false), frame(2, 100, true, false), frame(3, 100, true, false),
                frame(4, 100, true, true), frame(5, 100, true, true)));
        fixture.statusReads.addAll(List.of(armed(), armed(), idle()));
        assertInstanceOf(ActionPorts.EffectObserved.class, fixture.composite().run(parent(), fixture));
        assertEquals(1, fixture.steps.stream().filter("resume-map"::equals).count());
        assertEquals(0, fixture.completed.elapsedDays()); assertTrue(fixture.completed.canceled()); assertNull(fixture.failed);
    }
    @Test void unknownGenerationCancelCannotBecomeAControlTerminalOrBeRetried() throws Exception {
        var fixture = new BattleAdvanceFixture(); fixture.unknownStep = BattleAdvancePlan.CANCEL_PREFIX + "1";
        fixture.frames.addAll(List.of(sameNativeFrame(1, false), sameNativeFrame(2, false), sameNativeFrame(3, true)));
        fixture.statusReads.addAll(List.of(armed(), armed()));
        assertInstanceOf(ActionPorts.Pending.class, fixture.composite().run(parent(), fixture));
        assertEquals(2, fixture.steps.size()); assertFalse(fixture.steps.contains("resume-map"));
        assertFalse(fixture.failed.actions().getLast().settled()); assertNull(fixture.completed);
    }
    private static Frame sameNativeFrame(int revision, boolean modal) {
        Frame original = frame(revision, 100, true, modal);
        var semantic = original.semantic().with("native_revision", new OpportunityJson.IntegerValue(BigInteger.ONE));
        var old = original.identity();
        var identity = new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(old.machineId(), old.game(),
                new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(
                        new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(old.frame().identity().player(), BigInteger.ONE, old.frame().identity().dateRaw()),
                        old.frame().snapshotId(), old.frame().revision(), old.frame().episodeRunId()), old.observationVersion());
        return new Frame(identity, original.source(), original.sessionId(), semantic,
                new ObservationProvenance.Push(identity.frame().snapshotId(), identity.frame().identity().nativeRevision(), original.originalEvidence()), original.observedAt(), original.originalEvidence());
    }
    @Test void statusFromDifferentGenerationCannotClaimDayCredit() throws Exception {
        var fixture = new BattleAdvanceFixture();
        fixture.frames.addAll(List.of(frame(1, 100, true, false), frame(2, 100, true, false), frame(3, 100, true, false), frame(4, 124, true, false), frame(5, 124, true, false), frame(6, 124, true, false)));
        Status wrong = new Status(State.TRIGGERED, new CrossJsDecimalUInt64("2"), 100, 124, 124, 124, 3, Mode.DECISION_EPOCH, 1, 1, 1, 0, 1, List.of("date_deadline"), 0, 0, true, true, false, false);
        fixture.statusReads.addAll(List.of(armed(), wrong));
        assertInstanceOf(ActionPorts.Pending.class, fixture.composite().run(parent(), fixture));
        assertNull(fixture.completed); assertNotNull(fixture.failed); assertFalse(fixture.steps.contains("pause-map"));
    }
    @Test void exactStepSpellingsPreserveZeroArmyAndRefuseAliasesOverflowAndExplicitSpeedThree() {
        assertTrue(BattleAdvanceStep.parse("committed-route-sentinel-advance-army-0-to-7-until-124").isPresent());
        for (String invalid : List.of("battle-decision-epoch-advance-to-0124", "battle-decision-epoch-advance-to-9223372036854775808",
                "committed-route-sentinel-advance-army-00-to-7-until-124", "committed-route-sentinel-advance-army-0-to-7-until-124-speed-3",
                "war-objective-hold-sentinel-advance-war-0-army-0-at-7-until-124", "battle-decision-epoch-advance-to-１２４"))
            assertTrue(BattleAdvanceStep.parse(invalid).isEmpty(), invalid);
    }
    @Test void strongPlanRoundtripRejectsWrongTypeMissingFieldsAndTypedTargetDeadlineMismatch() {
        ActionCommand original = parent(); assertEquals(original, ActionCodec.decodeCommand(ActionCodec.encodeCommand(original)));
        var valid = BattleAdvancePlan.decode(original);
        var wrong = valid.json().with("speed", new OpportunityJson.Bool(true));
        ActionCommand malformed = new ActionCommand(original.actionId(), original.before(), original.source(), original.sessionId(), original.operation(),
                new OpportunityJson.Obj(Map.of(BattleAdvancePlan.KEY, wrong)), original.expected(), original.claims(), original.deadline());
        assertThrows(IllegalArgumentException.class, () -> BattleAdvancePlan.decode(malformed));
        var fields = new java.util.LinkedHashMap<>(valid.json().members()); fields.remove("campaign_deadline");
        var missing = new ActionCommand(original.actionId(), original.before(), original.source(), original.sessionId(), original.operation(),
                new OpportunityJson.Obj(Map.of(BattleAdvancePlan.KEY, new OpportunityJson.Obj(fields))), original.expected(), original.claims(), original.deadline());
        assertThrows(IllegalArgumentException.class, () -> BattleAdvancePlan.decode(missing));
        assertEquals(0, valid.watchArmyIds().getFirst());
        var cap = new CampaignDeadline.Configuration(new CampaignDeadline.Founding("episode-1", "1000.1.1", BigInteger.valueOf(100), 1),
                CampaignDeadline.CALENDAR_PROFILE, BigInteger.valueOf(124), List.of(BigInteger.valueOf(100), BigInteger.valueOf(124)));
        var config = BattleAdvancePlan.Configuration.production(Optional.of(cap));
        var typed = BattleAdvanceStep.parse("battle-decision-epoch-advance-to-148").orElseThrow();
        assertThrows(IllegalArgumentException.class, () -> BattleAdvancePlan.create(typed, BattleAdvanceFrame.decode(frame(1, 100, true, false)), config));
        var generic = BattleAdvanceStep.parse("battle-decision-epoch-advance").orElseThrow();
        assertEquals(124, BattleAdvancePlan.create(generic, BattleAdvanceFrame.decode(frame(1, 100, true, false)), config).targetDateRaw());
    }
    @Test void startingModalAndWrongCommittedRouteAreRejectedBeforeClockMutation() {
        var battle = BattleAdvanceStep.parse("battle-decision-epoch-advance-to-124").orElseThrow();
        assertThrows(IllegalArgumentException.class, () -> BattleAdvancePlan.create(battle, BattleAdvanceFrame.decode(frame(1, 100, true, true)), BattleAdvancePlan.Configuration.production(Optional.empty())));
        var route = BattleAdvanceStep.parse("committed-route-sentinel-advance-army-0-to-7-until-124").orElseThrow();
        assertThrows(IllegalArgumentException.class, () -> BattleAdvancePlan.create(route, BattleAdvanceFrame.decode(frame(1, 100, true, false)), BattleAdvancePlan.Configuration.production(Optional.empty())));
    }
    @Test void holdRechecksPublishedWarAndAllArmiesRatherThanCallingNativeWatchExactWarTerminal() {
        Frame base = frame(1, 100, true, false);
        String text = new String(OpportunityJson.encode(base.semantic()), StandardCharsets.UTF_8)
                .replace("\"army_state\":\"combat\"", "\"army_state\":\"regular\"").replace("\"army_state_code\":2", "\"army_state_code\":1")
                .replace("\"in_combat\":true", "\"in_combat\":false").replace("\"combat_id\":281474976710657", "\"combat_id\":-1")
                .replace("\"active_wars\":[]", "\"active_wars\":[{\"war_id\":16777231,\"war_objective_province_ids\":[7]}]");
        var semantic = OpportunityJson.object(OpportunityJson.parse(text.getBytes(StandardCharsets.UTF_8)), "fixture");
        Frame holdFrame = new Frame(base.identity(), base.source(), base.sessionId(), semantic, base.provenance(), base.observedAt(), base.originalEvidence());
        var hold = (BattleAdvanceStep.Hold) BattleAdvanceStep.parse("war-objective-hold-sentinel-advance-war-16777231-army-0-at-7-until-124").orElseThrow();
        var snapshot = BattleAdvanceFrame.decode(holdFrame);
        assertEquals(BattleAdvanceFrame.HoldStatus.MATCHED, snapshot.hold(List.of(0), hold).status());
        assertEquals(24, BattleAdvancePlan.create(hold, snapshot, BattleAdvancePlan.Configuration.production(Optional.empty())).targetDateRaw() - 100);
        var lostWar = new Frame(base.identity(), base.source(), base.sessionId(), semantic.with("active_wars", new OpportunityJson.Arr(List.of())), base.provenance(), base.observedAt(), base.originalEvidence());
        assertEquals(BattleAdvanceFrame.HoldStatus.INVALIDATED, BattleAdvanceFrame.decode(lostWar).hold(List.of(0), hold).status());
        var armyGone = new Frame(base.identity(), base.source(), base.sessionId(), semantic.with("player_armies", new OpportunityJson.Arr(List.of())), base.provenance(), base.observedAt(), base.originalEvidence());
        assertEquals(BattleAdvanceFrame.HoldStatus.INVALIDATED, BattleAdvanceFrame.decode(armyGone).hold(List.of(0), hold).status());
    }
    @Test void thrownResumeWithNoReturnedReceiptNeverSubmitsCleanupOrAnotherResume() throws Exception {
        for (boolean beforeReceipt : List.of(false, true)) {
            var fixture = new BattleAdvanceFixture(); fixture.throwingStep = "resume-map"; fixture.throwBeforeReceipt = beforeReceipt;
            fixture.frames.addAll(List.of(frame(1, 100, true, false), frame(2, 100, true, false), frame(3, 100, true, false)));
            fixture.statusReads.add(armed());
            assertInstanceOf(ActionPorts.Pending.class, fixture.composite().run(parent(), fixture));
            assertEquals(1, fixture.steps.stream().filter("resume-map"::equals).count());
            assertFalse(fixture.steps.contains("pause-map")); assertEquals(3, fixture.frameReads);
            assertNotNull(fixture.failed); assertNull(fixture.completed);
        }
    }
    @Test void sharedClockObservesLastPreResumeEventAndOnlyCancelsOriginalGeneration() {
        var fixture = new BattleAdvanceFixture();
        var start = frame(1, 100, true, false);
        var arm = new Status(State.ARMED, new CrossJsDecimalUInt64("1"), 100, 124, 100, 0, 3, Mode.TERMINAL_OR_SENTINEL,
                0, 0, 0, 0, 0, List.of(), 0, -1, false, false, false, false);
        var idle = new Status(State.IDLE, arm.generation(), 100, 124, 100, 0, 3, arm.mode(), 0, 0, 0, 0, 0, List.of(), 0, -1, false, false, false, false);
        fixture.frames.addAll(List.of(frame(2, 100, true, false), frame(3, 100, true, true), frame(4, 100, true, true)));
        fixture.statusReads.addAll(List.of(arm, idle));
        var status = new org.xar.ck3.control.application.advance.ClockStatusRead(fixture, REF, fixture.archiveForTest());
        var clock = new org.xar.ck3.control.application.advance.AdvanceClock(fixture, status,
                (parent, current) -> new org.xar.ck3.control.application.advance.AdvanceReadiness.Facts(current.identity(), AVAILABLE,
                        java.util.Set.of(org.xar.ck3.control.application.advance.ClockStatusRead.ARM_CAP, org.xar.ck3.control.application.advance.ClockStatusRead.STATUS_CAP,
                                org.xar.ck3.control.application.advance.ClockStatusRead.CANCEL_CAP), false, false, false, 45, REF),
                java.time.Clock.fixed(NOW, java.time.ZoneOffset.UTC), 4, java.time.Duration.ofSeconds(30), java.time.Duration.ofSeconds(120));
        var plan = new org.xar.ck3.control.application.advance.AdvancePlan(BigInteger.valueOf(100), BigInteger.valueOf(124), 1, 3,
                "exact_one_day_unavoidable_contact", true, org.xar.ck3.control.application.advance.AdvancePlan.ClockMode.EXACT_SENTINEL, Optional.empty());
        var result = clock.execute(parent(), fixture, start, plan);
        assertEquals(List.of(plan.armStep(), org.xar.ck3.control.application.advance.ClockStatusRead.CANCEL_PREFIX + "1"), fixture.steps);
        assertEquals(0, result.diagnostics().elapsedDays()); assertTrue(result.diagnostics().canceled());
        assertEquals(org.xar.ck3.control.application.advance.AdvanceClock.ProgressStatus.BOUNDARY_INTERRUPTED, result.diagnostics().progressStatus());
    }
    @Test void retainedCanonicalChildBindingsRejectDuplicatesReorderingAndUnknownBeforeAnyRead() throws Exception {
        var fixture = new BattleAdvanceFixture();
        fixture.frames.addAll(List.of(frame(1, 100, true, false), frame(2, 100, true, false), frame(3, 100, true, false), frame(4, 124, true, false), frame(5, 124, true, false)));
        fixture.statusReads.addAll(List.of(armed(), stopped())); fixture.composite().run(parent(), fixture);
        var children = fixture.completed.actions();
        assertDoesNotThrow(() -> org.xar.ck3.control.application.advance.AdvanceClockArchivedReplay.verifyChildBindings(parent(), children));
        assertThrows(IllegalArgumentException.class, () -> org.xar.ck3.control.application.advance.AdvanceClockArchivedReplay.verifyChildBindings(parent(), List.of(children.getFirst(), children.getFirst())));
        assertThrows(IllegalArgumentException.class, () -> org.xar.ck3.control.application.advance.AdvanceClockArchivedReplay.verifyChildBindings(parent(), List.of(children.getLast(), children.getFirst())));
        var unknown = new BattleAdvanceFixture(); unknown.unknownStep = "resume-map";
        unknown.frames.addAll(List.of(frame(1, 100, true, false), frame(2, 100, true, false), frame(3, 100, true, false))); unknown.statusReads.add(armed());
        unknown.composite().run(parent(), unknown);
        assertThrows(IllegalArgumentException.class, () -> org.xar.ck3.control.application.advance.AdvanceClockArchivedReplay.verifyChildBindings(parent(), unknown.children));
        assertEquals(3, unknown.frameReads); assertEquals(2, unknown.steps.size());
    }
    @Test void normalSharedClockReturnsActualFreshEndpointAfterTerminalStatus() {
        var fixture = new BattleAdvanceFixture(); var start = frame(1, 100, true, false);
        var arm = new Status(State.ARMED, new CrossJsDecimalUInt64("1"), 100, 124, 100, 0, 3, Mode.TERMINAL_OR_SENTINEL,
                0, 0, 0, 0, 0, List.of(), 0, -1, false, false, false, false);
        var stop = new Status(State.TRIGGERED, arm.generation(), 100, 124, 124, 124, 3, arm.mode(),
                0, 0, 1, 0, 1, List.of("date_deadline"), 0, 0, true, true, false, false);
        var actualEndpoint = frame(5, 124, true, false);
        fixture.frames.addAll(List.of(frame(2, 100, true, false), frame(3, 100, true, false), frame(4, 124, true, false), actualEndpoint));
        fixture.statusReads.add(stop);
        var status = new org.xar.ck3.control.application.advance.ClockStatusRead(fixture, REF, fixture.archiveForTest());
        var clock = new org.xar.ck3.control.application.advance.AdvanceClock(fixture, status,
                (parent, current) -> new org.xar.ck3.control.application.advance.AdvanceReadiness.Facts(current.identity(), AVAILABLE,
                        java.util.Set.of(org.xar.ck3.control.application.advance.ClockStatusRead.ARM_CAP, org.xar.ck3.control.application.advance.ClockStatusRead.STATUS_CAP,
                                org.xar.ck3.control.application.advance.ClockStatusRead.CANCEL_CAP), false, false, false, 45, REF),
                java.time.Clock.fixed(NOW, java.time.ZoneOffset.UTC), 4, java.time.Duration.ofSeconds(30), java.time.Duration.ofSeconds(120));
        var plan = new org.xar.ck3.control.application.advance.AdvancePlan(BigInteger.valueOf(100), BigInteger.valueOf(124), 1, 3,
                "exact_one_day_unavoidable_contact", true, org.xar.ck3.control.application.advance.AdvancePlan.ClockMode.EXACT_SENTINEL, Optional.empty());
        var result = clock.execute(parent(), fixture, start, plan);
        assertEquals(actualEndpoint, result.endingFrame()); assertEquals(1, result.diagnostics().elapsedDays());
        assertDoesNotThrow(() -> org.xar.ck3.control.application.advance.AdvanceClockArchivedReplay.verifySequence(plan, start, result.endingFrame(),
                result.diagnostics().progressStatus(), result.diagnostics().nativeStopRead(), fixture.completed()));
    }
}
