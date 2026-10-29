package org.xar.ck3.control.application.planning.sway;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.vanilla.schemesway.OrdinarySwaySchedule.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService;

/** Application controls are explicit synthetic proposals, never actual native receipts or success goldens. */
public final class OrdinarySwayPolicyTest {
    private static final long ACTOR = 29829, TARGET = 34333;
    private static final BigInteger DATE = BigInteger.valueOf(53280000);
    private static final ExactRef POLICY_SOURCE = new ExactRef("fixture:declared-policy-source", 1, "1".repeat(64));

    @Test void earlierSelectedActionIsPreservedWithoutCollectingAnything() {
        var request = request(true, "1"); AtomicInteger calls = new AtomicInteger();
        var policy = new OrdinarySwayPolicy(POLICY_SOURCE, ignored -> {
            calls.incrementAndGet(); throw new AssertionError("earlier action must not collect Sway");
        }, OrdinarySwayPolicyTest::expected);
        var earlier = previous(request, "query-prisoner-receipt");
        assertInstanceOf(OrdinaryPolicy.Keep.class, policy.evaluate(request, earlier)); assertEquals(0, calls.get());
    }

    @Test void capturedFrameDriftPrecedesEveryLazyPersistentInputRead() {
        var request = request(true, "1"); AtomicInteger reads = new AtomicInteger();
        ObservationIdentity foreign = new ObservationIdentity(request.before().machineId(), request.before().game(),
                new ProposalFrame(request.before().frame().identity(), "foreign-snapshot", BigInteger.valueOf(18), "episode:fixture"), 1);
        var policy = new OrdinarySwayPolicy(POLICY_SOURCE, ignored -> new OrdinarySwayPolicy.CapturedView(
                foreign, Optional.of(root(List.of(TARGET))), all(), () -> { reads.incrementAndGet(); return Optional.empty(); }),
                OrdinarySwayPolicyTest::expected);
        assertInstanceOf(OrdinaryPolicy.Keep.class, policy.evaluate(request, previous(request, "life-advance")));
        assertEquals(0, reads.get());
    }

    @Test void actualCollectorProjectionDistinguishesKnownEmptyFrontierFromUnread() {
        var request = request(true, "1"); ObjectNode value = StrictJson.object();
        ObjectNode root = value.putObject("campaign_root_context");
        root.put("status", "available"); root.put("player_character_id", ACTOR); root.put("player_character_alive", true);
        root.put("snapshot_revision", 5); root.put("date_raw", DATE); root.putArray("direct_landed_vassal_character_ids");
        var known = OrdinarySwayPolicy.project(request.before(), OpportunityJson.parse(StrictJson.canonical(value)), all(),
                () -> Optional.of(new OrdinarySwayService.Inputs(Ledger.empty(), Optional.empty())));
        assertTrue(known.root().orElseThrow().frontier().orElseThrow().isEmpty());
        root.putNull("direct_landed_vassal_character_ids");
        var unread = OrdinarySwayPolicy.project(request.before(), OpportunityJson.parse(StrictJson.canonical(value)), all(),
                () -> Optional.empty());
        assertTrue(unread.root().orElseThrow().frontier().isEmpty());
        assertTrue(OrdinarySwayPolicy.project(request.before(), OpportunityJson.Nil.INSTANCE, all(), () -> Optional.empty()).root().isEmpty());
    }

    @Test void fourOriginalJobsReachTheExistingStageAndRestoreTheSameTypedDecision() {
        var request = request(true, "1");
        var pending = new Pending("sway-original-unknown", ACTOR, TARGET);
        var identity = new Identity("sway-original-applied", ACTOR, TARGET, 134217986, 8);
        var applied = new Resolved(identity, true, true, false, Optional.empty());
        List<Ledger> ledgers = List.of(Ledger.empty(), new Ledger(Optional.of(pending), Optional.empty()),
                new Ledger(Optional.empty(), Optional.of(applied)), Ledger.empty());
        List<Job> jobs = List.of(Job.QUERY_SELECTED_TARGET, Job.RECONCILE_PENDING, Job.OBSERVE_APPLIED, Job.COMPLETE_NO_RELATION);
        for (int index = 0; index < jobs.size(); index++) {
            Ledger ledger = ledgers.get(index); Root root = root(index == 3 ? List.of() : List.of(TARGET));
            var command = selected(policy(root, ledger, all(), new AtomicInteger()), request);
            var staged = OrdinarySwayPolicy.restoreStaged(command);
            assertEquals(jobs.get(index), staged.decision().job().orElseThrow());
            assertEquals(request.before().frame().revision(), staged.frame().publicRevision());
            assertEquals(request.before().frame().identity().nativeRevision(), staged.frame().nativeRevision());
            assertFalse(staged.decision().submitAllowed());
            if (index == 1) assertEquals(Optional.of(pending.actionId()), staged.decision().actionId());
            if (index == 2) assertEquals(Optional.of(identity.actionId()), staged.decision().actionId());
        }
    }

    @Test void disabledOriginalReadersCauseZeroLazyInputReads() {
        var request = request(true, "1"); AtomicInteger reads = new AtomicInteger();
        var policy = policy(root(List.of(TARGET)), Ledger.empty(), new OrdinarySwayService.Capabilities(false, false, false), reads);
        assertInstanceOf(OrdinaryPolicy.Keep.class, policy.evaluate(request, previous(request, "life-advance")));
        assertEquals(0, reads.get());
    }

    @Test void optionalInputFailurePreservesTheExistingOrdinaryContinuation() {
        var request = request(true, "1");
        var policy = new OrdinarySwayPolicy(POLICY_SOURCE, value -> new OrdinarySwayPolicy.CapturedView(
                value.before(), Optional.of(root(List.of(TARGET))), all(), () -> { throw new OrdinarySwayService.Unavailable("declared fixture unavailable"); }),
                OrdinarySwayPolicyTest::expected);
        assertInstanceOf(OrdinaryPolicy.Keep.class, policy.evaluate(request, previous(request, "life-advance")));
    }

    @Test void wrongRootNativeFrameCannotSupplyATargetOrACommand() {
        var request = request(true, "1");
        Root stale = new Root(true, ACTOR, true, BigInteger.valueOf(4), DATE, Optional.of(List.of(TARGET)));
        assertInstanceOf(OrdinaryPolicy.Keep.class, policy(stale, Ledger.empty(), all(), new AtomicInteger())
                .evaluate(request, previous(request, "life-advance")));
    }

    @Test void absentCompositeRegistrationPreservesThePlanAndDoesNotInventANativeOperation() {
        var request = request(false, "1");
        assertInstanceOf(OrdinaryPolicy.Keep.class, policy(root(List.of(TARGET)), Ledger.empty(), all(), new AtomicInteger())
                .evaluate(request, previous(request, "life-advance")));
    }

    @Test void unboundOrForeignPostconditionCannotProduceASelectedCommand() {
        var request = request(true, "1"); var collector = collector(root(List.of(TARGET)), Ledger.empty(), all(), new AtomicInteger());
        var absent = new OrdinarySwayPolicy(POLICY_SOURCE, collector, (ignored, staged) -> null);
        assertInstanceOf(OrdinaryPolicy.Stop.class, absent.evaluate(request, previous(request, "life-advance")));
        var foreign = new OrdinarySwayPolicy(POLICY_SOURCE, collector, (ignored, staged) -> expected(request(true, "2"), staged));
        assertInstanceOf(OrdinaryPolicy.Stop.class, foreign.evaluate(request, previous(request, "life-advance")));
    }

    @Test void oneImmutableCommandKeepsFrameClaimsOriginalSourceAndConservativeWorldPurpose() {
        var request = request(true, "1"); var policy = policy(root(List.of(TARGET)), Ledger.empty(), all(), new AtomicInteger());
        var result = assertInstanceOf(OrdinaryPolicy.Replace.class, policy.evaluate(request, previous(request, "life-advance")));
        var command = result.draft().command().orElseThrow();
        assertEquals(OrdinaryPolicy.Purpose.WORLD_ACTION, result.draft().purpose());
        assertEquals(request.before(), command.before()); assertEquals(request.source(), command.source());
        assertEquals(request.deadline(), command.deadline()); assertEquals(OrdinarySwayPolicy.OPERATION, command.operation());
        assertEquals(Set.of(BigInteger.valueOf(ACTOR), BigInteger.valueOf(TARGET)), command.claims().characterIds());
        JsonNode arguments = StrictJson.parse(OpportunityJson.encode(command.arguments()));
        assertFalse(arguments.at("/decision/submit_allowed").booleanValue());
        assertFalse(arguments.at("/decision/native_ai_rank_claimed").booleanValue());
        assertEquals(1, command.arguments().members().keySet().stream().filter("decision"::equals).count());
    }

    @Test void strictCompositeDecoderRejectsWrongTypesAndUndeclaredFields() {
        var request = request(true, "1"); var command = selected(policy(root(List.of(TARGET)), Ledger.empty(), all(), new AtomicInteger()), request);
        ObjectNode args = (ObjectNode)StrictJson.parse(OpportunityJson.encode(command.arguments()));
        ((ObjectNode)args.get("decision")).put("target_character_id", 34333.0);
        ObjectNode malformed = args;
        assertThrows(IllegalArgumentException.class, () -> OrdinarySwayPolicy.restoreStaged(withArguments(command, malformed)));
        args = (ObjectNode)StrictJson.parse(OpportunityJson.encode(command.arguments()));
        ((ObjectNode)args.get("frame_flags")).put("invented", true); ObjectNode unknown = args;
        assertThrows(IllegalArgumentException.class, () -> OrdinarySwayPolicy.restoreStaged(withArguments(command, unknown)));
    }

    @Test void commandIdentityIsStableForTheSameSourceAndChangesForADifferentAdmittedSource() {
        var one = request(true, "1"); var two = request(true, "2");
        var policy = policy(root(List.of(TARGET)), Ledger.empty(), all(), new AtomicInteger());
        assertEquals(selected(policy, one).actionId(), selected(policy, one).actionId());
        assertNotEquals(selected(policy, one).actionId(), selected(policy, two).actionId());
        var staged = OrdinarySwayPolicy.restoreStaged(selected(policy, one));
        assertEquals(new BigInteger("17"), staged.frame().publicRevision());
        assertEquals(new BigInteger("5"), staged.frame().nativeRevision());
    }

    private static OrdinarySwayPolicy policy(Root root, Ledger ledger, OrdinarySwayService.Capabilities capabilities, AtomicInteger reads) {
        return new OrdinarySwayPolicy(POLICY_SOURCE, collector(root, ledger, capabilities, reads), OrdinarySwayPolicyTest::expected);
    }
    private static OrdinarySwayPolicy.CopiedSource collector(Root root, Ledger ledger, OrdinarySwayService.Capabilities capabilities, AtomicInteger reads) {
        return request -> new OrdinarySwayPolicy.CapturedView(request.before(), Optional.of(root), capabilities, () -> {
            reads.incrementAndGet(); return Optional.of(new OrdinarySwayService.Inputs(ledger, Optional.empty()));
        });
    }
    private static Root root(List<Long> ids) { return new Root(true, ACTOR, true, BigInteger.valueOf(5), DATE, Optional.of(ids)); }
    private static OrdinarySwayService.Capabilities all() { return new OrdinarySwayService.Capabilities(true, true, true); }
    private static ActionCommand selected(OrdinarySwayPolicy policy, PlanningRequest request) {
        return assertInstanceOf(OrdinaryPolicy.Replace.class, policy.evaluate(request, previous(request, "life-advance")))
                .draft().command().orElseThrow();
    }
    private static ExpectedPostcondition expected(PlanningRequest request, OrdinarySwayService.Staged staged) {
        // Explicit test-only contract. Production observer schema/facts belong to the sole coordinator.
        return new ExpectedPostcondition(1, request.before(), request.source(), "fixture:declared-native-post/v1",
                List.of(new ExpectedBoolean(new FieldKey("fixture.observed"), true)));
    }
    private static OrdinaryPolicy.Draft previous(PlanningRequest request, String operation) {
        ActionCommand command = new ActionCommand("fixture-selected-before-sway", request.before(), request.source(), request.sessionId(),
                new OperationKey(operation), new OpportunityJson.Obj(java.util.Map.of()), expected(request, null),
                new Claims(Set.of(), Set.of(), Set.of(), Set.of()), request.deadline());
        return new OrdinaryPolicy.Draft("fixture-earlier-policy", "life-advance", "explicit synthetic earlier selection",
                OrdinaryPolicy.Kind.ORDINARY, Optional.of(command), OrdinaryPolicy.Purpose.DATE_ADVANCE,
                Optional.empty(), new OpportunityJson.Obj(java.util.Map.of()));
    }
    private static PlanningRequest request(boolean registered, String digestDigit) {
        var identity = new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(BigInteger.valueOf(ACTOR), BigInteger.valueOf(5), DATE);
        var frame = new ProposalFrame(identity, "fixture-native:5", BigInteger.valueOf(17), "episode:fixture");
        var before = new ObservationIdentity("xenoamess-full-tower-eb9d2c1186",
                new GameGeneration(73, new PythonOnlyUInt64(new BigInteger("134370000000000001"))), frame, 1);
        var source = new G2Source(before.machineId(), "2026-10-23T15:40:00Z", "1.20.0.4",
                new ExactRef("fixture:explicit-synthetic-observation", 1, digestDigit.repeat(64)));
        ObjectNode snapshot = StrictJson.object(); snapshot.put("snapshot_id", frame.snapshotId()); snapshot.put("episode_run_id", frame.episodeRunId());
        snapshot.put("revision", frame.revision()); snapshot.put("native_revision", identity.nativeRevision()); snapshot.put("date_raw", DATE);
        snapshot.put("paused", true); snapshot.put("map_ready", true); snapshot.putArray("active_wars"); snapshot.putArray("player_armies");
        snapshot.putNull("active_event"); snapshot.putNull("pending_character_interaction");
        snapshot.putObject("played_character").put("character_id", ACTOR).put("alive", true);
        var observations = new PlanningObservation(OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(snapshot)), "snapshot"),
                List.of(), registered ? Set.of(OrdinarySwayPolicy.OPERATION) : Set.of(), Set.of(), Optional.empty(),
                List.of(), Optional.empty(), Optional.empty(), false);
        return new PlanningRequest(before, source, "fixture:session", Instant.parse("2030-01-01T00:00:00Z"), observations);
    }
    private static ActionCommand withArguments(ActionCommand command, ObjectNode args) {
        return new ActionCommand(command.actionId(), command.before(), command.source(), command.sessionId(), command.operation(),
                OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(args)), "mutated arguments"), command.expected(), command.claims(), command.deadline());
    }
}
