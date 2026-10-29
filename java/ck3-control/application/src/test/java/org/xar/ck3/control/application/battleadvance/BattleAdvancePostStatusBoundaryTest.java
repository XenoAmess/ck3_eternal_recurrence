package org.xar.ck3.control.application.battleadvance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.battleadvance.BattleAdvanceFixture.*;

import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Executes the production composite over the existing scripted DATA fixture; no live qualification. */
final class BattleAdvancePostStatusBoundaryTest {
    @Test void eventFirstSeenAfterFinalStatusIsRetainedAndCannotGrantCheckpoint() throws Exception {
        BattleAdvanceFixture fixture = beforeFinalStatus();
        fixture.frames.add(frame(5, 124, true, true));
        fixture.statusReads.addAll(List.of(armed(), stopped()));

        ActionPorts.EffectObserved result = assertInstanceOf(ActionPorts.EffectObserved.class,
                fixture.composite().run(parent(), fixture));

        assertBoundaryMatchesOriginalEnding(fixture, BattleAdvanceFrame.Kind.ACTIVE_EVENT);
        assertTrue(result.observation().actual().contains(new ExpectedBoolean(
                new FieldKey("timeline.checkpoint_eligible"), false)));
        assertEquals(List.of(BattleAdvancePlan.ARM_PREFIX + "100-to-124-speed-3-mode-decision-a-1-0",
                "resume-map"), fixture.steps);
        assertFalse(fixture.completed.canceled());
        assertNull(fixture.failed);
    }

    @Test void activeWarSetFirstSeenAfterFinalStatusReachesTheSameRecordedBoundaryConsumer() throws Exception {
        BattleAdvanceFixture fixture = beforeFinalStatus();
        Frame original = frame(5, 124, true, false);
        OpportunityJson.Obj war = new OpportunityJson.Obj(Map.of(
                "war_id", new OpportunityJson.IntegerValue(BigInteger.valueOf(42))));
        fixture.frames.add(withSemantic(original, original.semantic().with(
                "active_wars", new OpportunityJson.Arr(List.of(war)))));
        fixture.statusReads.addAll(List.of(armed(), stopped()));

        ActionPorts.EffectObserved result = assertInstanceOf(ActionPorts.EffectObserved.class,
                fixture.composite().run(parent(), fixture));

        assertBoundaryMatchesOriginalEnding(fixture, BattleAdvanceFrame.Kind.ACTIVE_WAR_SET_CHANGED);
        assertEquals(List.of(42), fixture.completed.decisionBoundary().orElseThrow().afterWarIds());
        assertTrue(result.observation().actual().contains(new ExpectedBoolean(
                new FieldKey("timeline.checkpoint_eligible"), false)));
        assertEquals(2, fixture.steps.size());
        assertFalse(fixture.completed.canceled());
        assertNull(fixture.failed);
    }

    @Test void newlyObservedBoundaryCannotTurnArmedStatusIntoAnInventedCancelOrCompletedStop() throws Exception {
        BattleAdvanceFixture fixture = beforeFinalStatus();
        fixture.frames.addAll(List.of(frame(5, 124, true, true), frame(6, 124, true, true)));
        fixture.statusReads.addAll(List.of(armed(), armed()));

        assertInstanceOf(ActionPorts.Pending.class, fixture.composite().run(parent(), fixture));

        assertNull(fixture.completed);
        assertNotNull(fixture.failed);
        assertEquals(List.of(BattleAdvancePlan.ARM_PREFIX + "100-to-124-speed-3-mode-decision-a-1-0",
                "resume-map"), fixture.steps);
        assertTrue(fixture.failed.reason().contains("sentinel decision boundary generation/date/status"));
    }

    private static BattleAdvanceFixture beforeFinalStatus() {
        BattleAdvanceFixture fixture = new BattleAdvanceFixture();
        fixture.frames.addAll(List.of(frame(1, 100, true, false), frame(2, 100, true, false),
                frame(3, 100, true, false), frame(4, 124, true, false)));
        return fixture;
    }

    private static Frame withSemantic(Frame original, OpportunityJson.Obj semantic) {
        return new Frame(original.identity(), original.source(), original.sessionId(), semantic,
                original.provenance(), original.observedAt(), original.originalEvidence());
    }

    private static void assertBoundaryMatchesOriginalEnding(BattleAdvanceFixture fixture, BattleAdvanceFrame.Kind kind) {
        BattleAdvanceComposite.Outcome outcome = fixture.completed;
        BattleAdvanceFrame.Boundary boundary = outcome.decisionBoundary().orElseThrow();
        assertEquals(kind, boundary.kind());
        Optional<BattleAdvanceFrame.Boundary> actual = BattleAdvanceFrame.boundary(
                BattleAdvanceFrame.decode(outcome.starting()), BattleAdvanceFrame.decode(outcome.ending()));
        assertEquals(actual, outcome.decisionBoundary());
        var decoded = BattleAdvanceResultCodec.decode(BattleAdvanceResultCodec.completed(outcome),
                BattleAdvanceResultCodec.Profile.JAVA_V1);
        assertEquals(actual, BattleAdvanceResultCodec.decodeBoundary(decoded));
        assertEquals(1, outcome.elapsedDays());
    }
}

