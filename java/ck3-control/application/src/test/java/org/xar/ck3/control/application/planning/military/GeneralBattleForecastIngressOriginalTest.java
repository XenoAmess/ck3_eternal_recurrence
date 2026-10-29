package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.military.combatwire.CombatSimulationInputsCodec;
import org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputsCodec;
import org.xar.ck3.control.wave2.military.combatwire.phaseevent.StockPhaseEventRuntime;
import org.xar.ck3.control.wave2.military.forecast.CombatObservationCache;

/** Replays the existing first-hop production regression through the real Java stage helper. */
final class GeneralBattleForecastIngressOriginalTest {
    static Obj corpus() throws Exception {return OrdinaryMilitaryOriginalProducerTest.original(PROGRAM);}
    private static final String PROGRAM="""
            import copy,hashlib,json,pathlib,runpy,sys
            repo=pathlib.Path(sys.argv[1]); sys.path.insert(0,str(repo/'ck3_autonomous_player'/'src')); sys.path.insert(0,str(repo/'ck3_autonomous_player'/'tests'/'unit'))
            path=repo/'ck3_autonomous_player/tests/unit/test_general_battle_first_hop_before_endpoint_12004.py'; pin=hashlib.sha256(path.read_bytes()).hexdigest(); m=runpy.run_path(str(path)); s=m['_snapshot']()
            # Explicit test-only completion of the old partial first-hop fixture, not new native observation evidence.
            for army in s['player_armies']:army.update(owner_character_id=29829,controllable=True)
            for war in s['active_wars']:
                for army in war['allied_armies']:army.update(owner_character_id=29829,controllable=True)
                for army in war['enemy_armies']:army.update(owner_character_id=30001,controllable=False)
            m['_call'].__globals__['_snapshot']=lambda:copy.deepcopy(s)
            def lease(row):
                if row['command'].startswith('preview-move-army-'):
                    row['result'].update(queried_snapshot_id=s['snapshot_id'],queried_revision=s['revision'],queried_native_revision=s['native_revision'],queried_episode_run_id=s['episode_run_id'],queried_connection_generation=s['diagnostics']['connection_generation'])
                return row
            base=[lease(m['_preview'](31,[30,40,31],1)),m['_horizon'](31,[40,31],2),lease(m['_preview'](40,[30,40],3)),m['_horizon'](40,[40],4)]
            stale=copy.deepcopy(base);stale[-1]['result']['queried_native_revision']=8
            cases=[]
            for name,commands,endpoint in [('safe',base,False),('missing_first_h1',base[:-1],False),('stale_h1',stale,False),('unsafe_first_hop',base[:-1]+[m['_horizon'](40,[40],4,conflict=True)],False),('endpoint', [lease(m['_preview'](31,[31],1)),m['_horizon'](31,[31],2,conflict=True)],True)]:
                expected=m['_call'](commands,endpoint_query=endpoint)
                steps=['preview-move-army-11-to-31','move-army-11-to-31','preview-move-army-11-to-40','move-army-11-to-40',m['query_route_contact_horizon_step'](11,31,(21,)),m['query_route_contact_horizon_step'](11,40,(21,))]
                cases.append({'name':name,'snapshot':s,'history':commands,'steps':steps,'capabilities':[m['QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY']] if endpoint else [],'expected':expected})
            assert hashlib.sha256(path.read_bytes()).hexdigest()==pin
            print(json.dumps({'source_sha256':pin,'cases':cases},ensure_ascii=False,separators=(',',':')))
            """;
    @Test void fullNativePreviewAndH1ConsumersReachSafeHopBeforeDemandingEndpointModel() throws Exception {
        Obj corpus=OrdinaryMilitaryOriginalProducerTest.original(PROGRAM);assertEquals(5,rows(corpus.get("cases")).size());
        for(Obj row:rows(corpus.get("cases"))) {
            PlanningRequest request=request(row);var base=new CombatSimulationInputsCodec();
            var cache=new CombatObservationCache(base,new CombatPhaseInputsCodec(base,new StockPhaseEventRuntime()));
            var policy=new GeneralBattleForecastPolicy(source(),cache,(r,b)->{throw new AssertionError("general helper cannot call a fake siege provider");},r->{throw new AssertionError("these participants are not in combat");},(r,b,d)->{throw new AssertionError("read-only planning test cannot submit");});
            Obj original=obj(f("policy",text("one-life-turn-v1")),f("phase",text("native_war_route")),f("selected_step",text("move-army-11-to-31")));
            assertEquals(row.get("expected"),policy.reviewGeneral(request,original),optionalText(row.get("name")));
        }
    }
    @Test void missingOrWrongTypedConnectionCanNeverLookLikeTheSameNativeReadLease() throws Exception {
        Obj row=rows(OrdinaryMilitaryOriginalProducerTest.original(PROGRAM).get("cases")).getFirst();PlanningRequest request=request(row);Obj snapshot=request.observations().snapshot();
        Obj result=obj(f("queried_snapshot_id",snapshot.get("snapshot_id")),f("queried_revision",snapshot.get("revision")),f("queried_native_revision",snapshot.get("native_revision")),f("queried_episode_run_id",snapshot.get("episode_run_id")),f("queried_connection_generation",number(3)));
        assertTrue(sameLease(request,result));
        for(Value invalid:List.of(Nil.INSTANCE,new Bool(true),new DecimalValue("3.0"),new Text("3"),number(0)))assertFalse(sameLease(request,result.with("queried_connection_generation",invalid)));
        Obj missingSnapshot=OpportunityJson.object(row.get("snapshot"),"snapshot").with("diagnostics",empty());PlanningRequest missing=request(row.with("snapshot",missingSnapshot));
        var noConnection=new java.util.LinkedHashMap<>(result.members());noConnection.remove("queried_connection_generation");assertFalse(sameLease(missing,new Obj(noConnection)),"two missing connection fields cannot authorize a fresh Native horizon");
        BigInteger exact=new BigInteger("9007199254740993");Obj largeSnapshot=OpportunityJson.object(row.get("snapshot"),"snapshot").with("revision",number(exact)).with("native_revision",number(exact)).with("diagnostics",obj(f("connection_generation",number(exact))));
        PlanningRequest large=request(row.with("snapshot",largeSnapshot));Obj largeResult=result.with("queried_revision",number(exact)).with("queried_native_revision",number(exact)).with("queried_connection_generation",number(exact));assertTrue(sameLease(large,largeResult));
        assertFalse(sameLease(large,largeResult.with("queried_connection_generation",number(new BigInteger("9007199254740992")))));
    }
    @Test void originalMilitaryOperandsSurviveOnlyDriverPublicationFieldsAndStillRejectArmyScopeChanges()throws Exception {
        var row=rows(corpus().get("cases")).getFirst();var request=request(row);Obj original=request.observations().snapshot();
        Obj published=original.with("native_command_history",new Arr(request.observations().history().stream().<Value>map(value->value).toList())).with("java_driver_facts_evidence",obj(f("path",text("derived-next-driver-facts")),f("bytes",number(1)),f("sha256",text("b".repeat(64)))));
        assertTrue(NativeMilitaryInputView.sameNativeOperands(original,published),"read-history publication is not a changed native military operand");
        var armies=rows(original.get("player_armies"));Obj moved=armies.getFirst().with("current_province_id",number(41));
        assertFalse(NativeMilitaryInputView.sameNativeOperands(original,published.with("player_armies",new Arr(List.of(moved)))),"source army movement must never be hidden by a cache hit");
        assertFalse(NativeMilitaryInputView.sameNativeOperands(original,published.with("declarable_wars",Nil.INSTANCE)),"missing and explicit null remain distinct");
        var diagnostics=OpportunityJson.object(original.get("diagnostics"),"actual diagnostics");
        assertFalse(NativeMilitaryInputView.sameNativeOperands(original,published.with("diagnostics",diagnostics.with("connection_generation",number(4)))));
    }
    private static ExactRef source(){return new ExactRef("synthetic-military-regression-source",1,"a".repeat(64));}
    static PlanningRequest request(Obj row) {
        Obj snapshot=OpportunityJson.object(row.get("snapshot"),"original snapshot").with("map_ready",new Bool(true));
        if(!(snapshot.get("played_character") instanceof Obj))snapshot=snapshot.with("played_character",obj(f("character_id",number(29829)),f("alive",new Bool(true))));
        BigInteger actor=OpportunityJson.integer(OpportunityJson.object(snapshot.get("played_character"),"actor").get("character_id"),"actor ID");
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(actor,OpportunityJson.integer(snapshot.get("native_revision"),"native revision"),OpportunityJson.integer(snapshot.get("date_raw"),"date")),OpportunityJson.text(snapshot.get("snapshot_id"),"snapshot id"),OpportunityJson.integer(snapshot.get("revision"),"revision"),OpportunityJson.text(snapshot.get("episode_run_id"),"episode"));
        var identity=new ObservationIdentity("synthetic-military-regression-machine",new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("134000000000000001"))),frame,1);
        Set<OperationKey> steps=OpportunityJson.array(row.get("steps"),"steps").stream().map(v->new OperationKey(OpportunityJson.text(v,"step"))).collect(Collectors.toSet());
        Set<String> capabilities=OpportunityJson.array(row.get("capabilities"),"capabilities").stream().map(v->OpportunityJson.text(v,"capability")).collect(Collectors.toSet());
        var observations=new PlanningObservation(snapshot,rows(row.get("history")),steps,capabilities,Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        Instant now=Instant.parse("2026-10-24T00:00:00Z");return new PlanningRequest(identity,new G2Source(identity.machineId(),now.toString(),"synthetic-regression",source()),"military-regression-session",now.plusSeconds(60),observations);
    }
}
