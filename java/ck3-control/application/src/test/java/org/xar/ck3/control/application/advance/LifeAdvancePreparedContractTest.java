package org.xar.ck3.control.application.advance;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** The actual rewrite producer feeds the strict Life-to-planner enrichment consumer.
 * Runtime readiness, canonical writer custody and gameplay are outside this pure contract test.
 */
final class LifeAdvancePreparedContractTest {
    private static final OperationKey OP=new OperationKey("life-advance-one-day");
    private static final Obj ARGS=new Obj(Map.of("caller_evidence",new Text("retained-original-selection")));
    private static final Obj DETAIL=new Obj(Map.of("selected_step",new Text(OP.value()),"reason",new Text("actual-selected-detail")));
    private static PlanningRequest request() {
        Instant now=Instant.parse("2026-10-24T00:00:00Z");
        var source=new G2Source("software-fixture-no-game",now.toString(),"1.20.0.4",new ExactRef("fixture/source",1,"a".repeat(64)));
        var frame=new ProposalFrame(new Frame(BigInteger.valueOf(29829),BigInteger.ONE,BigInteger.valueOf(53288256)),"native:1",BigInteger.ONE,"fixture-episode");
        var identity=new ObservationIdentity(source.machineId(),new GameGeneration(4242,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),frame,1);
        Obj semantic=DriverJson.object("{\"paused\":true,\"map_ready\":true,\"speed\":1,\"player_armies\":[],\"active_wars\":[],\"active_event\":null,\"pending_character_interaction\":null,\"one_life_terminal_reason\":null,\"top_exclusive_modal_choice_hint\":{\"status\":\"absent\"}}".getBytes(java.nio.charset.StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES);
        return new PlanningRequest(identity,source,"fixture-session",now.plusSeconds(30),
                new PlanningObservation(semantic,List.of(),Set.of(OP),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static ActionCommand actual(PlanningRequest request) {
        Obj ancestor=ARGS.with("plan",DETAIL);
        String decision=OP.value()+":"+ActionCodec.sha256(DriverJson.encode(ancestor));
        var seed=new ActionCommand(ActionIds.forDecision(request.sessionId(),request.before(),decision),request.before(),request.source(),request.sessionId(),OP,ancestor,
                new ExpectedPostcondition(1,request.before(),request.source(),AdvancePlan.OBSERVER,List.of(new ExpectedBoolean(new FieldKey("paused"),true))),
                new Claims(Set.of(),Set.of(),Set.of(),Set.of()),request.deadline());
        return AdvanceRewrite.exactDay(request,seed);
    }
    private static ActionCommand with(ActionCommand original,String id,Obj arguments) {
        return new ActionCommand(id,original.before(),original.source(),original.sessionId(),original.operation(),arguments,original.expected(),original.claims(),original.deadline());
    }
    @Test void realRewriteEnrichmentPreservesAncestorAndRejectsChangedCallerArgumentsIdAndDetail() {
        PlanningRequest request=request();ActionCommand actual=actual(request);
        assertDoesNotThrow(()->LifeAdvanceCommands.requirePrepared(request,OP,ARGS,DETAIL,actual));
        assertThrows(IllegalArgumentException.class,()->LifeAdvanceCommands.requirePrepared(request,OP,ARGS,DETAIL,
                with(actual,actual.actionId(),actual.arguments().with("caller_evidence",new Text("changed")))));
        assertThrows(IllegalArgumentException.class,()->LifeAdvanceCommands.requirePrepared(request,OP,ARGS,DETAIL,
                with(actual,"foreign-action-id",actual.arguments())));
        assertThrows(IllegalArgumentException.class,()->LifeAdvanceCommands.requirePrepared(request,OP,ARGS,
                DETAIL.with("reason",new Text("changed")),actual));
        assertThrows(IllegalArgumentException.class,()->LifeAdvanceCommands.requirePrepared(request,OP,
                ARGS.with("plan",DETAIL),DETAIL,actual));
    }
    @Test void strictCanonicalPlanDoesNotAcceptLegacyOrWrongTypedFieldsAsProducerEnrichment() {
        PlanningRequest request=request();ActionCommand actual=actual(request);AdvancePlan plan=AdvancePlan.decode(actual);
        Obj wrong=plan.json().with("horizon_days",new Bool(true));
        assertThrows(IllegalArgumentException.class,()->LifeAdvanceCommands.requirePrepared(request,OP,ARGS,DETAIL,
                with(actual,actual.actionId(),actual.arguments().with(AdvancePlan.KEY,wrong))));
        var legacy=new java.util.LinkedHashMap<>(plan.json().members());legacy.remove("war_daily_watch");legacy.put("schema",new Text(AdvancePlan.LEGACY_SCHEMA));
        assertThrows(IllegalArgumentException.class,()->LifeAdvanceCommands.requirePrepared(request,OP,ARGS,DETAIL,
                with(actual,actual.actionId(),actual.arguments().with(AdvancePlan.KEY,new Obj(legacy)))));
    }
}
