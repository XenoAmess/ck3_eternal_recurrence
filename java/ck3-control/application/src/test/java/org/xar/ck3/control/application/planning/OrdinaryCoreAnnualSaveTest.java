package org.xar.ck3.control.application.planning;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real core policy public evaluate boundary; ordinary SAVE cadence is owned by Controller's confirmed pair/date. */
final class OrdinaryCoreAnnualSaveTest {
    private static final ExactRef REF = new ExactRef("D:/annual-policy/implementation.java", 1, "a".repeat(64));
    private static final Instant BASE = Instant.parse("2026-11-04T00:00:00Z");

    @Test void postwarCleanupDoesNotScheduleAnExtraAutomaticSave() {
        List<String> history = new ArrayList<>(milestones());
        history.addFirst("save-checkpoint"); history.add("disband-army-7");
        assertLife(history);
    }
    @Test void completedWarAndMarriageMilestonesDoNotScheduleAnExtraAutomaticSave() {
        List<String> history = new ArrayList<>(milestones()); history.addFirst("save-checkpoint");
        assertLife(history);
    }
    @Test void threeOrMoreLifeCyclesCannotSubstituteForAGameYear() {
        List<String> history = new ArrayList<>(milestones()); history.add("save-checkpoint");
        history.addAll(List.of("life-advance", "life-advance", "life-advance", "economic-event-cycle"));
        assertLife(history);
    }
    private static List<String> milestones() {
        return List.of("dynasty-review", "succession-review", "marriage-confirm-response", "war-enforce-demands", "war-disband-armies");
    }
    private static void assertLife(List<String> operations) {
        var calls = new ArrayList<String>();
        var leaves = new ArrayList<WarCorePlanner.Leaf>();
        for (var boundary : List.of(WarCorePlanner.Boundary.TERMINATION_SCORE_PRELUDE,
                WarCorePlanner.Boundary.PENDING_WAR_INTERACTION_PRELUDE, WarCorePlanner.Boundary.BATTLE_CONTROL_PRELUDE))
            leaves.add(new WarCorePlanner.Leaf(boundary, REF,
                    (request, draft) -> new MilitaryPlanningDecision.Keep(new OpportunityJson.Obj(Map.of()))));
        PlanningReadPort reads = new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
                throw new AssertionError("peaceful annual policy fixture cannot perform a native read");
            }
        };
        var war = new WarCorePlanner(leaves, request -> { throw unused(); }, (request, selection) -> { throw unused(); }, reads,
                (input, selection) -> { throw unused(); }, (request, previous) -> { throw unused(); });
        OrdinaryCorePolicy.CoreProducer events = (request, previous) -> { calls.add("events"); return new OrdinaryPolicy.Keep("none"); };
        OrdinaryCorePolicy.CoreProducer council = (request, previous) -> { calls.add("council"); return new OrdinaryPolicy.Keep("none"); };
        OrdinaryCorePolicy.CoreProducer marriage = (request, previous) -> { calls.add("marriage"); return new OrdinaryPolicy.Keep("none"); };
        OrdinaryCorePolicy.CoreProducer entry = (request, previous) -> { calls.add("war-entry"); return new OrdinaryPolicy.Keep("none"); };
        var core = new OrdinaryCorePolicy(REF, war, events, council, marriage, entry,
                (request, operation, arguments, plan, purpose, domain) -> {
                    calls.add(operation.value());
                    return new OrdinaryCorePolicy.Prepared(new ActionCommand("annual-policy-action", request.before(), request.source(),
                            request.sessionId(), operation, arguments,
                            new ExpectedPostcondition(1, request.before(), request.source(), "annual-policy/v1",
                            List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true))),
                            new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), request.deadline()));
                }, step -> step.equals("life-advance"));
        PlanningRequest request = request(operations);
        var replacement = assertInstanceOf(OrdinaryPolicy.Replace.class, core.evaluate(request, OrdinaryPolicy.Draft.empty()));
        assertEquals("life-advance", replacement.draft().command().orElseThrow().operation().value());
        assertEquals(List.of("events", "council", "marriage", "war-entry", "life-advance"), calls);
        assertEquals(request.before(), replacement.draft().command().orElseThrow().before());
        assertEquals("current_life_loop", ((OpportunityJson.Text) replacement.draft().detail().get("phase")).value());
    }
    private static PlanningRequest request(List<String> operations) {
        var game = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var before = new ObservationIdentity("annual-policy", game,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.ONE,
                BigInteger.valueOf(53_154_768)), "annual-frame", BigInteger.ONE, "annual-episode"), 1);
        var source = new G2Source("annual-policy", BASE.toString(), "annual-fixture", REF);
        var snapshot = OpportunityJson.object(OpportunityJson.parse(("{\"paused\":true,\"map_ready\":true,\"revision\":1,"
                + "\"native_revision\":1,\"date_raw\":53154768,\"snapshot_id\":\"annual-frame\",\"episode_run_id\":\"annual-episode\","
                + "\"played_character\":{\"character_id\":29829},\"active_wars\":[],\"player_armies\":[]}").getBytes(StandardCharsets.UTF_8)), "annual policy");
        var rows = new ArrayList<OpportunityJson.Obj>();
        for (String operation : operations) rows.add(new OpportunityJson.Obj(Map.of(
                "index", new OpportunityJson.IntegerValue(BigInteger.valueOf(rows.size() + 1)),
                "command", new OpportunityJson.Text(operation), "ok", new OpportunityJson.Bool(true))));
        var observation = new PlanningObservation(snapshot, rows,
                Set.of(new OperationKey("life-advance"), new OperationKey("save-checkpoint")), Set.of(),
                Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false);
        return new PlanningRequest(before, source, "annual-session", BASE.plusSeconds(30), observation);
    }
    private static AssertionError unused() { return new AssertionError("no active-war or physical side effect in annual policy fixture"); }
}
