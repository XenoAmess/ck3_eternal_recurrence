package org.xar.ck3.control.application.presentation;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pure display DATA and actual canonical receipt vectors; no Root, Game or screen-draw fixture. */
public final class DecisionDisplayTest {
    public static final Instant NOW = Instant.parse("2026-10-26T19:00:00Z");
    public static ActionCommand command(String id, String operation) {
        var ref = new ExactRef("D:/display-software-vector/source.json", 1, "a".repeat(64));
        var source = new G2Source("display-software-vector", NOW.toString(), "1.20.0.4", ref);
        var game = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var before = new ProposalLifecycle.ObservationIdentity(source.machineId(), game,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),
                        StrictJson.UINT64_MAX.subtract(BigInteger.ONE), BigInteger.valueOf(24000)),
                        "display-vector", StrictJson.UINT64_MAX, "episode-display"), 1);
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, before, source, "display-vector/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true)));
        return new ActionCommand(id, before, source, "display-session", new OperationKey(operation),
                new OpportunityJson.Obj(Map.of()), expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()),
                NOW.plusSeconds(30));
    }
    public static ActionReceipt unknown(ActionCommand original, String request, long sequence) {
        var evidence = original.source().sourceRef();
        var guard = new GuardEvidence(original.before(), original.source(), original.sessionId(), BigInteger.ONE,
                original.operation(), evidence, evidence, "display-vector", NOW, original.deadline());
        var attempt = new ActionState.Attempt(request, NOW, guard, new NativeRequest(original.operation().value(),
                Optional.empty(), new RawJson(new byte[]{'{','}'})));
        return new ActionReceipt(1, sequence, original, ActionCodec.bodySha256(original),
                new ActionState.Unknown(Optional.of(attempt), Optional.empty(), "software transport completion unknown", List.of(evidence)));
    }
    @Test void exactWholePlanFeedsTheSameChildParentAndUnknownAttemptWithoutClaimingDraw() {
        var snapshots = new ArrayList<DecisionDisplay.Snapshot>();
        var feed = new DecisionDisplay(Clock.fixed(NOW, ZoneOffset.UTC), snapshots::add, failure -> fail(failure.reason()));
        ActionCommand parent = command("parent", "life-advance-one-day");
        var draft = new OrdinaryPolicy.Draft("ordinary", "advance", "当前局势允许短步推进，随后复查军情。",
                OrdinaryPolicy.Kind.ORDINARY, Optional.of(parent), OrdinaryPolicy.Purpose.DATE_ADVANCE,
                Optional.empty(), new OpportunityJson.Obj(Map.of()));
        var trace = new PlanTrace(parent.before(), List.of(), Optional.of(draft));
        var frame = parent.before().frame();
        var fields = new java.util.LinkedHashMap<String, OpportunityJson.Value>();
        fields.put("snapshot_id", new OpportunityJson.Text(frame.snapshotId()));
        fields.put("revision", new OpportunityJson.IntegerValue(frame.revision()));
        fields.put("native_revision", new OpportunityJson.IntegerValue(frame.identity().nativeRevision()));
        fields.put("date_raw", new OpportunityJson.IntegerValue(frame.identity().dateRaw()));
        fields.put("episode_run_id", new OpportunityJson.Text(frame.episodeRunId()));
        fields.put("played_character", new OpportunityJson.Obj(Map.of("character_id", new OpportunityJson.IntegerValue(frame.identity().player()))));
        fields.put("paused", new OpportunityJson.Bool(true)); fields.put("map_ready", new OpportunityJson.Bool(true));
        fields.put("active_wars", new OpportunityJson.Arr(List.of())); fields.put("player_armies", new OpportunityJson.Arr(List.of()));
        var request = new PlanningRequest(parent.before(), parent.source(), parent.sessionId(), parent.deadline(),
                new PlanningObservation(new OpportunityJson.Obj(fields), List.of(), Set.of(parent.operation()), Set.of(),
                        Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false));
        feed.planned(request, new PlanningResult.ActionSelected(parent, trace));
        feed.preparing(parent, List::of, false);
        ActionCommand child = command("parent-child", "pause-map");
        feed.preparing(child, () -> List.of(parent), false);
        var before = feed.snapshot().current().orElseThrow();
        assertEquals(List.of(DecisionDisplay.Identity.from(parent)), before.parents());
        assertTrue(before.rationale().contains(draft.reason()));
        var receipt = unknown(child, "actual-original-request", 7);
        feed.returned(receipt);
        var after = feed.snapshot().current().orElseThrow();
        assertEquals(DecisionDisplay.Status.UNRESOLVED, after.status());
        assertEquals(Optional.of("actual-original-request"), after.attemptRequestId());
        assertEquals(7, after.receiptSequence().orElseThrow());
        assertEquals(child.origin(), after.context().origin());
        assertEquals("134000000000000001", after.context().origin().game().creationFiletime().value().toString());
        assertEquals(StrictJson.UINT64_MAX, after.context().origin().requireGameplay().frame().revision());
        assertEquals(List.of(DecisionDisplay.Identity.from(parent)), after.parents());
        assertEquals(DecisionDisplay.Delivery.RENDERER_UPDATED, feed.snapshot().delivery());
        assertTrue(DecisionDisplayText.render(feed.snapshot()).contains("不能重复提交"));
        long publication = feed.snapshot().publication();
        feed.returned(receipt);
        assertEquals(publication, feed.snapshot().publication());
        feed.planned(request, new PlanningResult.Stopped(parent.before(), PlanningResult.StopReason.DEADLINE,
                "actual original planning deadline expired", trace));
        assertTrue(feed.snapshot().current().orElseThrow().action().isEmpty());
        assertEquals("actual original planning deadline expired", feed.snapshot().current().orElseThrow().rationale());
        feed.planned(request, new PlanningResult.IncompleteMigration(parent.before(), List.of(PlanningStage.ORDINARY_CORE),
                new PlanTrace(parent.before(), List.of(), Optional.empty())));
        assertEquals(DecisionDisplay.Status.PLANNING_STOPPED, feed.snapshot().current().orElseThrow().status());
        assertTrue(feed.snapshot().current().orElseThrow().action().isEmpty());
    }
    @Test void actualAckAndIndependentEffectRemainDifferentAudienceStates() {
        ActionCommand command = command("ack", "pause-map");
        var pending = unknown(command, "one-request", 2);
        var attempt = ActionTransitions.attempt(pending.state()).orElseThrow();
        var ack = new NativeActionPort.AckReceived(attempt.requestId(), true, Optional.empty(),
                new RawJson(new byte[]{'{','}'}), new byte[]{1});
        var feed = new DecisionDisplay(Clock.fixed(NOW, ZoneOffset.UTC), snapshot -> { }, failure -> { });
        feed.preparing(command, List::of, false);
        feed.returned(new ActionReceipt(1, 3, command, pending.bodySha256(), new ActionState.AckReceived(attempt, ack)));
        assertEquals(DecisionDisplay.Status.ACK_RECEIVED, feed.snapshot().current().orElseThrow().status());
        assertTrue(DecisionDisplayText.render(feed.snapshot()).contains("不能据此推断业务完成"));
        feed.returned(pending); // An older canonical event must never replace the displayed attempt.
        assertEquals(DecisionDisplay.Delivery.UNAVAILABLE, feed.snapshot().delivery());
        assertEquals(3, feed.snapshot().current().orElseThrow().receiptSequence().orElseThrow());
    }
    @Test void changedAttemptOrForeignParentCannotBorrowTheOriginalDisplayIdentity() {
        var failures = new AtomicInteger();
        var feed = new DecisionDisplay(Clock.fixed(NOW, ZoneOffset.UTC), snapshot -> { }, failure -> failures.incrementAndGet());
        ActionCommand original = command("unknown", "pause-map");
        feed.preparing(original, List::of, false);
        feed.returned(unknown(original, "original-attempt", 3));
        feed.returned(unknown(original, "replacement-attempt", 4));
        assertEquals(1, failures.get());
        assertEquals(Optional.of("original-attempt"), feed.snapshot().current().orElseThrow().attemptRequestId());
        ActionCommand parent = command("foreign-parent", "pause-map");
        var foreign = new ActionCommand(parent.actionId(), parent.origin(), parent.source(), "different-session",
                parent.operation(), parent.arguments(), parent.expectation(), parent.claims(), parent.deadline());
        feed.preparing(original, () -> List.of(foreign), false);
        assertEquals(2, failures.get());
        assertEquals("unknown", feed.snapshot().current().orElseThrow().action().orElseThrow().actionId());
    }
    @Test void boundedHistoryAndOptionalRendererFailureCannotProduceBusinessCreditOrRetireTheAttempt() {
        var failures = new AtomicInteger();
        var feed = new DecisionDisplay(Clock.fixed(NOW, ZoneOffset.UTC),
                snapshot -> { throw new IOException("no graphical renderer"); }, failure -> failures.incrementAndGet());
        for (int index = 0; index < DecisionDisplay.MAX_IDENTITIES + 5; index++) {
            var command = command("bounded-" + index, "query-current-state");
            feed.preparing(command, List::of, false);
            feed.returned(unknown(command, "request-" + index, index + 1));
        }
        assertEquals(DecisionDisplay.MAX_HISTORY, feed.snapshot().history().size());
        assertEquals(DecisionDisplay.Delivery.UNAVAILABLE, feed.snapshot().delivery());
        assertTrue(failures.get() > 0);
        assertEquals(DecisionDisplay.Status.UNRESOLVED, feed.snapshot().current().orElseThrow().status());
        assertFalse(DecisionDisplayText.render(feed.snapshot()).contains("罗贝尔的30年"));
    }
}

