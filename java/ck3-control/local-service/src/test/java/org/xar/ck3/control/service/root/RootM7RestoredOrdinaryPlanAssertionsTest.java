package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.campaigncadence.CampaignCalendar;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * Default-CI component software evidence: real Goal/Driver codecs and campaign policy output
 * reach the new assertion consumer. No Managed Root, actual SAVE/LOAD, or full planner is created.
 */
public final class RootM7RestoredOrdinaryPlanAssertionsTest {
    private static final ExactRef SOURCE = new ExactRef("D:/software-fixtures/m7-source", 1, "a".repeat(64));
    private static final ExactRef EXE = new ExactRef("D:/software-fixtures/m7-ck3.exe", 128, "b".repeat(64));
    private static final String EPOCH = "c".repeat(64);
    private static final String MACHINE = "m7-restored-plan-component-software";
    private static final String EPISODE = "actual-component-successor-episode";
    private static final BigInteger PUBLIC = new BigInteger("18446744073709551615");
    private static final BigInteger NATIVE = PUBLIC.subtract(BigInteger.ONE);
    private static final int RAW = CampaignCalendar.dateToRaw("1066.9.15");

    private record Produced(DriverStateSnapshot.Value originalGoal, G2Source source,
            PlanningRequest request, OrdinaryPolicy.Draft draft) { }

    @Test void persistedMatchedGoalAndActualCampaignPolicyReachTheAssertionConsumer() throws Exception {
        Produced actual = produce();
        var consumed = RootM7RestoredOrdinaryPlanAssertions.requireConsumption(actual.originalGoal(), actual.source(),
                EPOCH, EXE, actual.request(), actual.draft());
        assertEquals(73, consumed.observation().goal().originCharacterId());
        assertEquals(74, consumed.observation().goal().currentCharacterId());
        assertEquals(1, consumed.observation().goal().progress().reconciledSuccessions());
        assertEquals(PUBLIC, consumed.observation().revision());
        assertEquals(NATIVE, consumed.observation().nativeRevision());
        assertNotEquals(consumed.observation().revision(), consumed.observation().nativeRevision());
        assertEquals(EPISODE, consumed.observation().episodeRunId());
        assertEquals("18446744073709551615", consumed.observation().game().creationFiletime());
        assertEquals(0, consumed.savedDayCredit());
        assertFalse(consumed.gameActionsSubmitted()); assertFalse(consumed.coldAuthorityGranted());
    }

    @Test void emptyMetadataPublicationPassesCanonicalOptionalCheck() throws Exception {
        Produced actual = produce(Optional.empty(), Optional.empty());
        var consumed = RootM7RestoredOrdinaryPlanAssertions.requireConsumption(actual.originalGoal(), actual.source(),
                Optional.empty(), Optional.empty(), actual.request(), actual.draft());
        assertEquals(73, consumed.observation().goal().originCharacterId());
        assertEquals(74, consumed.observation().goal().currentCharacterId());
        assertEquals(1, consumed.observation().goal().progress().reconciledSuccessions());
        assertEquals(PUBLIC, consumed.observation().revision());
        assertEquals(NATIVE, consumed.observation().nativeRevision());
        assertNotEquals(consumed.observation().revision(), consumed.observation().nativeRevision());
        assertEquals(EPISODE, consumed.observation().episodeRunId());
        assertEquals("18446744073709551615", consumed.observation().game().creationFiletime());
        assertTrue(consumed.observation().sourceEpoch().isEmpty());
        assertTrue(consumed.observation().executable().isEmpty());
        assertFalse(consumed.replayAuthorized());
        assertEquals(0, consumed.savedDayCredit());
        assertFalse(consumed.gameActionsSubmitted()); assertFalse(consumed.coldAuthorityGranted());
    }

    @Test void missingAndNullSavedGoalsAndAbsentCurrentGoalCannotQualify() throws Exception {
        Produced actual = produce();
        for (DriverStateSnapshot.Slot absent : List.<DriverStateSnapshot.Slot>of(
                new DriverStateSnapshot.Missing(), new DriverStateSnapshot.NullValue())) {
            assertThrows(IOException.class, () -> RootM7RestoredOrdinaryPlanAssertions.requireConsumption(absent,
                    actual.source(), EPOCH, EXE, actual.request(), actual.draft()));
        }
        PlanningObservation old = actual.request().observations();
        var absent = new PlanningRequest(actual.request().before(), actual.source(), actual.request().sessionId(),
                actual.request().deadline(), new PlanningObservation(old.snapshot(), old.history(),
                old.actionSteps(), old.bridgeCapabilities(), old.battleSpeedReadiness(), old.actionFacts(),
                Optional.empty(), old.crossRunPlan(), old.initialLifestyleFocusRequired()));
        assertThrows(IOException.class, () -> RootM7RestoredOrdinaryPlanAssertions.requireConsumption(actual.originalGoal(),
                actual.source(), EPOCH, EXE, absent, actual.draft()));
    }

    @Test void absentForeignEpochAndExecutableSourcesCannotBorrowAValidGoalPublication() throws Exception {
        Produced actual = produce();
        assertThrows(IOException.class, () -> RootM7RestoredOrdinaryPlanAssertions.requireConsumption(actual.originalGoal(),
                null, EPOCH, EXE, actual.request(), actual.draft()));
        var foreign = new G2Source(MACHINE, actual.source().observedAtUtc(), actual.source().exactBuild(),
                new ExactRef("D:/software-fixtures/foreign-source", 1, "d".repeat(64)));
        assertThrows(IOException.class, () -> RootM7RestoredOrdinaryPlanAssertions.requireConsumption(actual.originalGoal(),
                foreign, EPOCH, EXE, actual.request(), actual.draft()));
        assertThrows(IOException.class, () -> RootM7RestoredOrdinaryPlanAssertions.requireConsumption(actual.originalGoal(),
                actual.source(), "d".repeat(64), EXE, actual.request(), actual.draft()));
        assertThrows(IOException.class, () -> RootM7RestoredOrdinaryPlanAssertions.requireConsumption(actual.originalGoal(),
                actual.source(), EPOCH, SOURCE, actual.request(), actual.draft()));
    }

    @Test void anotherCompleteGoalOrAnOmittedConsumptionCannotBecomeRestoredIntent() throws Exception {
        Produced actual = produce();
        var foreignGoal = new DriverStateSnapshot.Value(GoalCodec.encodeGoal(
                OrdinaryCampaignGoal.newGoal("foreign-component-campaign", 74)));
        assertThrows(IOException.class, () -> RootM7RestoredOrdinaryPlanAssertions.requireConsumption(foreignGoal,
                actual.source(), EPOCH, EXE, actual.request(), actual.draft()));
        OrdinaryPolicy.Draft old = actual.draft();
        var stripped = new OrdinaryPolicy.Draft(old.policy(), old.phase(), old.reason(), old.kind(), old.command(),
                old.purpose(), old.domain(), new OpportunityJson.Obj(Map.of()));
        assertThrows(IOException.class, () -> RootM7RestoredOrdinaryPlanAssertions.requireConsumption(actual.originalGoal(),
                actual.source(), EPOCH, EXE, actual.request(), stripped));
    }

    @Test void aDifferentDateInAnOtherwiseValidKernelPublicationCannotBorrowTheCurrentFrame() throws Exception {
        Produced actual = produce(); OrdinaryPolicy.Draft old = actual.draft();
        var kernel = OpportunityJson.object(old.detail().get("m7_kernel_plan_consumption"), "actual kernel publication");
        var observation = OpportunityJson.object(kernel.get("observation"), "actual kernel observation")
                .with("date_raw", new OpportunityJson.IntegerValue(BigInteger.valueOf(RAW + 24L)));
        var changed = new OrdinaryPolicy.Draft(old.policy(), old.phase(), old.reason(), old.kind(), old.command(),
                old.purpose(), old.domain(), old.detail().with("m7_kernel_plan_consumption", kernel.with("observation", observation)));
        assertThrows(IOException.class, () -> RootM7RestoredOrdinaryPlanAssertions.requireConsumption(actual.originalGoal(),
                actual.source(), EPOCH, EXE, actual.request(), changed));
    }

    private static Produced produce() {
        return produce(Optional.of(EPOCH), Optional.of(EXE));
    }

    private static Produced produce(Optional<String> epoch, Optional<ExactRef> executable) {
        var continued = OrdinaryCampaignGoal.continueGoal(OrdinaryCampaignGoal.newGoal("component-ordinary-campaign", 73),
                new OrdinaryCampaignGoal.Reconciliation(OrdinaryCampaignGoal.Verdict.MATCHED, 73, 74,
                        List.of(1L, 2L), List.of(3L), List.of()));
        var slot = new DriverStateSnapshot.Value(GoalCodec.encodeGoal(continued));
        var driver = new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("software-pipe", 42,
                BigInteger.valueOf(74), EPISODE), List.of(), new DriverStateSnapshot.NullValue(),
                new DriverStateSnapshot.NullValue(), new DriverStateSnapshot.NullValue(), new DriverStateSnapshot.NullValue(),
                new DriverStateSnapshot.NullValue(), slot, new DriverStateSnapshot.Value("[]".getBytes(StandardCharsets.UTF_8)));
        var originalGoal = (DriverStateSnapshot.Value) DriverStateSnapshot.decodeComplete(driver.encode()).campaignGoal();
        var goal = GoalCodec.decodeGoal(originalGoal.json());
        var source = new G2Source(MACHINE, "2026-10-26T00:00:00Z", "component-software", SOURCE);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(74),
                NATIVE, BigInteger.valueOf(RAW)), "m7-component-native-frame", PUBLIC, EPISODE);
        var before = new ProposalLifecycle.ObservationIdentity(MACHINE,
                new GameGeneration(42, new PythonOnlyUInt64(PUBLIC)), frame, 1);
        var snapshot = OpportunityJson.object(OpportunityJson.parse(("""
                {"snapshot_id":"m7-component-native-frame","episode_run_id":"%s",
                "revision":%s,"native_revision":%s,"date_raw":%d,"paused":true,"map_ready":true,
                "played_character":{"character_id":74,"alive":true},"active_wars":[],"player_armies":[],
                "diagnostics":{"bridge_pid":42,"connection_generation":1}}
                """).formatted(EPISODE, PUBLIC, NATIVE, RAW).getBytes(StandardCharsets.UTF_8)), "component software frame")
                .with("campaign_goal", OpportunityJson.parse(originalGoal.json()));
        var request = new PlanningRequest(before, source, "m7-component-session", Instant.parse("2099-01-01T00:00:00Z"),
                new PlanningObservation(snapshot, List.of(), Set.of(), Set.of(), Optional.empty(), List.of(),
                        Optional.of(goal), Optional.empty(), false));
        var projected = M7CampaignPolicies.projectGoal(request, epoch, executable, Optional.empty()).orElseThrow();
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, before, source, "component-software/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true)));
        var command = new ActionCommand("m7-component-plan", before, source, request.sessionId(),
                new OperationKey("query-component-read-v1"), new OpportunityJson.Obj(Map.of()), expected,
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), request.deadline());
        var draft = new OrdinaryPolicy.Draft("one-life-turn-v1", "component-read", "component software producer input",
                OrdinaryPolicy.Kind.ORDINARY, Optional.of(command), OrdinaryPolicy.Purpose.READ_ONLY, Optional.empty(),
                new OpportunityJson.Obj(Map.of()));
        var policy = new M7CampaignPolicies.CampaignAdvancePolicy(SOURCE, ignored -> Optional.empty(),
                (current, old, step, cap) -> { throw new AssertionError("read selection cannot rewrite a clock"); },
                current -> { assertSame(request, current); return Optional.of(projected); });
        var published = assertInstanceOf(OrdinaryPolicy.Replace.class, policy.evaluate(request, draft)).draft();
        return new Produced(originalGoal, source, request, published);
    }
}
