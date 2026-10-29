package org.xar.ck3.control.application.planning.campaign;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.application.planning.OrdinaryCorePolicy;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningWire;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** The shared actual-terminal producer, strict persisted codec and ordinary focus reader form one chain. */
final class ScoredCrossRunPlanningTest {
    private static final Instant AT=Instant.parse("2026-10-24T00:00:00Z");
    @Test void sharedProducerRetainsOuterWrapperStepsAndConsumesConfirmedInnerResultsOnly() {
        var terminal=json("{\"terminal\":true,\"terminal_reason\":\"played_character_dead\",\"settlement_status\":\"complete\",\"score\":123.5}");
        var rows=List.of(json("{\"command\":\"auto-run 2\",\"ok\":true,\"result\":{\"turns\":["
                +"{\"command\":\"auto-turn\",\"ok\":true,\"result\":{\"auto_turn\":{\"selected_step\":\"enforce-demands-9\"},\"war_victory\":{\"status\":\"victory_enforced\"}}},"
                +"{\"command\":\"auto-turn\",\"ok\":true,\"result\":{\"auto_turn\":{\"selected_step\":\"arrange-marriage-707-809\"},\"marriage_result\":{\"status\":\"send_confirmed\"}}}]}}"));
        var state=CrossRunPlanning.recordScoredTerminal(CrossRunPlanning.empty(),"life",rows,terminal,AT);
        var persisted=CrossRunPlanning.decodeState(CrossRunPlanning.encodeState(state));
        assertEquals(state,persisted);assertEquals(List.of("auto-run 2","death-terminal"),persisted.episodes().getFirst().successfulSteps());
        assertTrue(persisted.episodes().getFirst().achievements().palermoHolyWarWon());
        assertFalse(persisted.episodes().getFirst().achievements().danishBetrothalAccepted());
        assertEquals(Optional.of("war"),CrossRunPlanning.focus(persisted.nextRunPlan()));
        assertEquals(CrossRunPlanning.focus(persisted.nextRunPlan()),CrossRunPlanning.focus(Optional.of(CrossRunPlanning.planJson(persisted.nextRunPlan()))));
        var request=ordinaryRequest(persisted.nextRunPlan());var wire=PlanningWire.encodeRequest(request);
        var restored=PlanningWire.decodeRequest(wire);assertEquals(request,restored);
        assertEquals(Optional.of("war"),OrdinaryCorePolicy.focus(restored));
        assertTrue(new String(wire,StandardCharsets.UTF_8).contains("\"creation_filetime\":\"18446744073709551615\""));
        var encoded=object(OpportunityJson.parse(CrossRunPlanning.encodeState(state)),"canonical state");
        var actual=terminal.with("cross_run_strategy",encoded.with("recorded_episode",CrossRunPlanning.episodeJson(state.episodes().getFirst())));
        assertEquals(state,CrossRunStrategySource.terminal(CrossRunPlanning.empty(),"life",rows,actual,AT));
        assertThrows(IllegalArgumentException.class,()->CrossRunStrategySource.terminal(CrossRunPlanning.empty(),"life",List.of(),actual,AT));
    }
    private static PlanningRequest ordinaryRequest(CrossRunPlanning.Plan plan){
        var source=new G2Source("cross-run-software-machine",AT.toString(),"software-only",
                new ExactRef("D:/software-fixtures/source.java",1,"a".repeat(64)));
        var identity=new ObservationIdentity(source.machineId(),new GameGeneration(123,
                new PythonOnlyUInt64(new BigInteger("18446744073709551615"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE,BigInteger.ONE,BigInteger.valueOf(240)),
                        "original-snapshot",BigInteger.ONE,"life"),1);
        var snapshot=json("{\"snapshot_id\":\"original-snapshot\",\"episode_run_id\":\"life\",\"revision\":1,\"native_revision\":1,\"date_raw\":240,\"paused\":true,\"map_ready\":true,\"played_character\":{\"character_id\":1,\"alive\":true},\"active_wars\":[],\"player_armies\":[]}");
        return new PlanningRequest(identity,source,"software-session",AT.plusSeconds(30),new PlanningObservation(snapshot,
                List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.of(CrossRunPlanning.planJson(plan)),false));
    }
    @Test void terminalStatusScoreTokensDuplicateTerminalAndWrongHistoryCannotMintAnotherLife() {
        var terminal=json("{\"terminal\":true,\"settlement_status\":\"complete\",\"score\":1}");
        assertThrows(IllegalArgumentException.class,()->CrossRunPlanning.recordScoredTerminal(CrossRunPlanning.empty(),"life",List.of(),terminal.with("score",Nil.INSTANCE),AT));
        assertThrows(IllegalArgumentException.class,()->CrossRunPlanning.recordScoredTerminal(CrossRunPlanning.empty(),"life",List.of(),terminal.with("score",new Bool(true)),AT));
        assertThrows(IllegalArgumentException.class,()->CrossRunPlanning.recordScoredTerminal(CrossRunPlanning.empty(),"life",List.of(),terminal.with("settlement_status",new Bool(true)),AT));
        assertThrows(IllegalArgumentException.class,()->CrossRunPlanning.recordScoredTerminal(CrossRunPlanning.empty(),"life",List.of(),terminal.with("settlement_status",new Text("settlement_unavailable")),AT));
        assertThrows(IllegalArgumentException.class,()->CrossRunPlanning.recordScoredTerminal(CrossRunPlanning.empty(),"life",List.of(json("{\"command\":\"death-terminal\",\"ok\":true,\"result\":{}}")),terminal,AT));
        assertThrows(IllegalArgumentException.class,()->CrossRunPlanning.recordScoredTerminal(CrossRunPlanning.empty(),"life",List.of(json("{\"command\":\"query\",\"ok\":1}")),terminal,AT));
        assertThrows(IllegalArgumentException.class,()->CrossRunPlanning.decodeState(OpportunityJson.encode(
                object(OpportunityJson.parse(CrossRunPlanning.encodeState(CrossRunPlanning.empty())),"state")
                .with("format_version",new DecimalValue("1.0")))));
    }
    private static Obj json(String raw){return object(OpportunityJson.parse(raw.getBytes(StandardCharsets.UTF_8)),"software original");}
}
