package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.military.OrdinaryAutomaticSurrenderPolicy;
import org.xar.ck3.control.application.planning.military.OrdinaryWhitePeacePolicy;
import org.xar.ck3.control.application.planning.military.WarDeclarationContinuity;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Complete pure formatter inputs are software DATA; they grant no actual Root, action or observation authority. */
final class RootWarActionExecutionResultTest {
    private static final String EXE="2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
    private static final ArmyCalls.Revision REV=new ArmyCalls.Revision(new Present<>(BigInteger.valueOf(20)));
    private static Obj json(String value){return DriverJson.object(value.getBytes(StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES);}
    private static Obj change(Obj row,String key,Value value){var fields=new LinkedHashMap<>(row.members());fields.put(key,value);return new Obj(fields);}
    private static Obj raw(String step,String status){return json("{\"step\":\""+step+"\",\"accepted\":true,\"status\":\""+status+"\",\"backend_id\":\"native-headless\"}");}
    private static Obj before(){return json("""
            {"snapshot_id":"native:10","revision":20,"native_revision":10,"date_raw":1000,
             "episode_run_id":"software-episode","paused":true,"map_ready":true,"army_routes_supported":true,
             "war_objective_assault_supported":true,"played_character":{"character_id":73,"alive":true},
             "diagnostics":{"bridge_pid":42,"connection_generation":5,"hello":{"pid":42,"expected_ck3_version":"1.20.0.4",
              "expected_ck3_sha256":"EXE"}},
             "played_character_gold":{"raw":1000000,"scale":100000},"played_character_prestige":{"raw":500000,"scale":100000},
             "played_character_piety":{"raw":800000,"scale":100000},
             "active_wars":[{"war_id":7,"player_side":"attacker","player_is_primary_war_leader":true,
              "primary_opponent_character_id":24,"targeted_title_ids":[91],"player_relative_war_score":-100,
              "objective_province_states":[{"province_id":9,"siege_observable":true,"active_siege":{
               "siege_id":5,"assault_observable":true,"assault_in_progress":false,"can_start_assault":true,
               "can_stop_assault":false,"player_army_besieging":true,"opaque_siege":{"ordered":[3,1],"null":null}}}]}],
             "player_armies":[{"army_id":0,"controllable":true,"owner_character_id":73,"current_province_id":3,
              "move_target_observable":true,"move_target_province_id":null,"route_province_ids":[],
              "army_state":"regular","army_state_code":1,"in_combat":false,"retreating":false}]}
            """.replace("EXE",EXE));}
    private static Obj after(){return change(change(change(before(),"snapshot_id",new Text("native:11")),
            "revision",new IntegerValue(BigInteger.valueOf(21))),"native_revision",new IntegerValue(BigInteger.valueOf(11)));}
    private static Obj noWar(){return change(after(),"active_wars",new Arr(List.of()));}
    private static Obj activeWar(){return (Obj)((Arr)before().get("active_wars")).items().getFirst();}
    private static Obj options(){return json("""
            {"war_id":7,"player_side":"attacker","player_is_primary_war_leader":true,"player_relative_war_score":-100,
             "war_duration_days":800,"absolute_war_scores_observable":true,"attacker_war_score":-100,"defender_war_score":100,
             "active_casus_belli_identity":{"canonical_key":"raiktor_claim_cb","database_index":71}}
            """);}
    private static Obj response(){return json("{\"status\":\"available\",\"decision_status_raw\":2,\"would_accept_now\":true}");}
    private static Obj surrenderOption(){return new Obj(Map.of("recipient_response",response(),"auto_accept",new Bool(true)));}
    private static Obj whiteOption(){return new Obj(Map.of("recipient_response",response(),"ai_acceptance",json("{\"raw\":100000}")));}
    private static Obj moveAfter(){return change(after(),"player_armies",json("""
            {"rows":[{"army_id":0,"controllable":true,"owner_character_id":73,"current_province_id":3,
             "move_target_observable":true,"move_target_province_id":9,"route_province_ids":[4,9],
             "opaque_army":{"literal":"001","null":null}}]}
            """).get("rows"));}
    private static Obj rejectedMoveAfter() {
        Obj army=(Obj)((Arr)moveAfter().get("player_armies")).items().getFirst();
        army=change(change(change(army,"route_read_status",new Text("complete_nonempty")),"in_combat",new Bool(false)),"retreating",new Bool(false));
        return change(moveAfter(),"player_armies",new Arr(List.of(army)));
    }
    private static Obj negativeRequest(){return json("{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"negative-original\",\"step\":\"move-army-0-to-9\",\"expected_revision\":10}");}
    private static Obj negativeResponse(String error){return json("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"negative-original\",\"ok\":false,\"error\":\""+error+"\"}");}
    private static Obj assaultAfter(boolean active) {
        Obj last=after(),war=(Obj)((Arr)last.get("active_wars")).items().getFirst();
        Obj province=(Obj)((Arr)war.get("objective_province_states")).items().getFirst();
        Obj siege=(Obj)province.get("active_siege");
        siege=change(change(change(siege,"assault_in_progress",new Bool(active)),"can_start_assault",new Bool(!active)),"can_stop_assault",new Bool(active));
        return change(last,"active_wars",new Arr(List.of(change(war,"objective_province_states",new Arr(List.of(change(province,"active_siege",siege)))))));
    }
    private static Obj siegeObject(Obj frame) {
        Obj war=(Obj)((Arr)frame.get("active_wars")).items().getFirst();
        Obj province=(Obj)((Arr)war.get("objective_province_states")).items().getFirst();
        return (Obj)province.get("active_siege");
    }
    private static Context context() {
        var source=new G2Source("software-test-machine","2026-10-24T10:00:00Z","1.20.0.4",new ExactRef("shape-only-source",1,"a".repeat(64)));
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(73),BigInteger.TEN,BigInteger.valueOf(1000)),
                "native:10",BigInteger.valueOf(20),"software-episode");
        return new Context(new ObservationIdentity(source.machineId(),new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),frame,1),
                source,"software-session",Instant.parse("2026-10-24T10:01:00Z"));
    }
    @Test void fullMoveArmyAndAssaultObjectsReachTheSolePublicSerdeWithoutInventingQueryMetadata() {
        Obj primitive=change(raw("move-army-0-to-9","submitted"),"opaque_ack",json("{\"ordered\":[3,1],\"null\":null}"));
        Obj move=RootWarActionExecutionResult.move(new ArmyCalls.Move(REV,new PublicUnitId(0),new PositiveId(9)),primitive,before(),moveAfter());
        assertEquals(primitive.get("opaque_ack"),move.get("opaque_ack"));assertEquals(moveAfter().get("player_armies"),move.get("player_armies"));
        assertEquals("moving",((Text)((Obj)move.get("war_action")).get("status")).value());
        Obj assault=RootWarActionExecutionResult.assault(new ArmyCalls.Siege(PublicMethod.START_ASSAULT,REV,new PositiveId(5)),
                raw("start-assault-5","start_submitted"),before(),assaultAfter(true),List.of(),List.of());
        assertEquals(siegeObject(assaultAfter(true)).get("opaque_siege"),((Obj)assault.get("active_siege")).get("opaque_siege"));
        assertEquals(assault.get("war_action"),assault.get("assault_action"));
        assertFalse(((Obj)assault.get("war_action")).members().containsKey("postcondition_verified"));
        for(Obj result:List.of(move,assault)) {
            RawJson encoded=ArmyPublicWire.encodeExactSourceBound(result,context());
            assertEquals(result,ArmyPublicWire.decodeExactSourceBound(encoded,context()));
            assertEquals(encoded,ArmyPublicWire.encodeExactSourceBound(ArmyPublicWire.decodeExactSourceBound(encoded,context()),context()));
            assertFalse(RootWarActionExecutionResult.json(encoded).members().containsKey("queried_snapshot_id"));
            assertTrue(((Text)RootWarActionExecutionResult.json(encoded).get("revision")).value().equals("21"));
        }
    }
    @Test void movementArrivalUsesIndependentRevisionAndRouteAndDoesNotTreatMissingArmyAsAnAck() {
        var call=new ArmyCalls.Move(REV,new PublicUnitId(0),new PositiveId(9));
        Obj army=(Obj)((Arr)before().get("player_armies")).items().getFirst();
        Obj here=change(before(),"player_armies",new Arr(List.of(change(army,"current_province_id",new IntegerValue(BigInteger.valueOf(9))))));
        Obj later=change(change(change(here,"revision",new IntegerValue(BigInteger.valueOf(21))),"native_revision",new IntegerValue(BigInteger.valueOf(11))),"snapshot_id",new Text("native:11"));
        assertEquals("arrived",RootWarActionExecutionResult.movePostcondition(here,later,0,9,true));
        assertNull(RootWarActionExecutionResult.movePostcondition(here,here,0,9,true));
        assertNull(RootWarActionExecutionResult.movePostcondition(before(),change(moveAfter(),"player_armies",new Arr(List.of(
                change((Obj)((Arr)moveAfter().get("player_armies")).items().getFirst(),"route_province_ids",new Arr(List.of()))))),0,9,true));
        Obj absent=change(after(),"player_armies",new Arr(List.of()));
        assertEquals("army_no_longer_present",RootWarActionExecutionResult.movePostcondition(before(),absent,0,9,true));
        Obj result=RootWarActionExecutionResult.move(call,raw("move-army-0-to-9","submitted"),before(),absent);
        assertEquals(new Arr(List.of()),result.get("player_armies"));
    }
    @Test void negativeAckRecoveryRetainsFalseAckAndOriginalPacketsAndRequiresTheIndependentNewRoute()throws Exception {
        var call=new ArmyCalls.Move(REV,new PublicUnitId(0),new PositiveId(9));
        Obj response=negativeResponse("CK3 move-army state is unavailable");
        Obj result=RootWarActionExecutionResult.negativeMove(call,before(),rejectedMoveAfter(),negativeRequest(),response,"negative-original");
        assertEquals(new Bool(false),result.get("accepted"));assertEquals(new Bool(false),result.get("native_ack_verified"));
        assertEquals(new Text("observed_after_native_error"),result.get("status"));
        Obj original=(Obj)result.get("native_error_evidence");assertEquals(negativeRequest(),original.get("native_request"));assertEquals(response,original.get("native_command_result"));
        assertThrows(IllegalArgumentException.class,()->RootWarActionExecutionResult.negativeMove(call,before(),
                change(rejectedMoveAfter(),"native_revision",new IntegerValue(BigInteger.TEN)),negativeRequest(),response,"negative-original"));
        assertThrows(IllegalArgumentException.class,()->RootWarActionExecutionResult.negativeMove(call,before(),rejectedMoveAfter(),
                change(negativeRequest(),"expected_revision",new Bool(true)),response,"negative-original"));
        assertThrows(IOException.class,()->RootWarActionExecutionResult.negativeMove(call,before(),rejectedMoveAfter(),negativeRequest(),negativeResponse("unrelated native failure"),"negative-original"));
        for(String error:List.of("CK3 army cannot move to the destination","CK3 army has no move mode for the destination","CK3 army state rejects movement")) {
            Obj deferred=RootWarActionExecutionResult.negativeMove(call,before(),after(),negativeRequest(),negativeResponse(error),"negative-original");
            assertEquals(new Text("deferred"),deferred.get("status"));assertEquals(new Bool(false),deferred.get("accepted"));
            assertFalse(deferred.members().containsKey("business_submission_may_have_applied"));
        }
    }
    @Test void assaultRequiresTheSameSiegeAndARealFlagTransitionAndRetainsTheCompleteActiveSiege() {
        var call=new ArmyCalls.Siege(PublicMethod.START_ASSAULT,REV,new PositiveId(5));
        assertThrows(IllegalArgumentException.class,()->RootWarActionExecutionResult.assault(call,raw("start-assault-5","start_submitted"),
                before(),after(),List.of(),List.of()));
        assertThrows(IllegalArgumentException.class,()->RootWarActionExecutionResult.assault(call,raw("start-assault-5","submitted"),
                before(),assaultAfter(true),List.of(),List.of()));
        Obj malformed=change(before(),"war_objective_assault_supported",new Bool(false));
        assertThrows(IllegalArgumentException.class,()->RootWarActionExecutionResult.assault(call,raw("start-assault-5","start_submitted"),
                malformed,assaultAfter(true),List.of(),List.of()));
        Obj war=activeWar();Obj duplicate=change(assaultAfter(true),"active_wars",new Arr(List.of(war,war)));
        assertThrows(IllegalArgumentException.class,()->RootWarActionExecutionResult.assault(call,raw("start-assault-5","start_submitted"),
                before(),duplicate,List.of(),List.of()));
    }
    @Test void genericTerminationVariantFieldsAndOptionalNullsFollowTheOriginalWrapper() {
        var surrenderCall=new ArmyCalls.War(PublicMethod.SURRENDER_WAR,REV,BigInteger.valueOf(7));
        for(var variant:OrdinaryAutomaticSurrenderPolicy.Variant.values()) {
            var evidence=new OrdinaryAutomaticSurrenderPolicy.Ready(variant,activeWar(),options(),surrenderOption());
            Obj result=RootWarActionExecutionResult.surrender(surrenderCall,raw("surrender-war-7","submitted"),before(),noWar(),evidence);
            Obj action=(Obj)result.get("war_termination_result");
            boolean rich=variant!=OrdinaryAutomaticSurrenderPolicy.Variant.DE_JURE_NO_SAFE_ROUTE;
            assertEquals(rich,action.members().containsKey("surrender_variant"));
            assertEquals(rich,action.members().containsKey("absolute_war_scores_observable"));
            assertFalse(action.members().containsKey("one_shot_authorization"));assertFalse(action.members().containsKey("explicit_player_request"));
            assertSame(Nil.INSTANCE,action.get("remaining_active_war"));
        }
        for(var variant:OrdinaryWhitePeacePolicy.Variant.values()) {
            var evidence=new OrdinaryWhitePeacePolicy.Ready(variant,activeWar(),options(),Optional.empty(),whiteOption());
            Obj result=RootWarActionExecutionResult.white(new ArmyCalls.War(PublicMethod.OFFER_WHITE_PEACE,REV,BigInteger.valueOf(7)),
                    raw("offer-white-peace-7","submitted"),before(),noWar(),evidence);
            Obj action=(Obj)result.get("war_termination_result");
            assertSame(Nil.INSTANCE,action.get("claimant_character_id"));assertEquals(activeWar().get("targeted_title_ids"),action.get("target_title_ids"));
            assertEquals(variant!=OrdinaryWhitePeacePolicy.Variant.CLAIM_CB,action.members().containsKey("recipient_ai_acceptance_raw"));
        }
        var enforce=RootWarActionExecutionResult.enforce(new ArmyCalls.War(PublicMethod.ENFORCE_DEMANDS,REV,BigInteger.valueOf(7)),
                raw("enforce-demands-7","submitted"),before(),noWar());
        assertEquals(enforce.get("war_action"),enforce.get("war_victory"));
        Obj observation=(Obj)enforce.get("ordinary_war_exit_observation_v1");
        assertEquals(new Text("not_observed"),((Obj)observation.get("truce")).get("status"));
        assertEquals(new Text("not_observed"),((Obj)observation.get("claims")).get("status"));
        Obj zeroBefore=change(before(),"active_wars",new Arr(List.of(change(activeWar(),"war_id",new IntegerValue(BigInteger.ZERO)))));
        assertSame(Nil.INSTANCE,RootWarActionExecutionResult.enforce(new ArmyCalls.War(PublicMethod.ENFORCE_DEMANDS,REV,BigInteger.ZERO),
                raw("enforce-demands-0","submitted"),zeroBefore,noWar()).get("ordinary_war_exit_observation_v1"));
    }
    @Test void wrongAckFieldsBoolIntegersCrossDateAndUnknownNeverBecomeAFullAppliedResult() {
        var call=new ArmyCalls.War(PublicMethod.SURRENDER_WAR,REV,BigInteger.valueOf(7));
        var evidence=new OrdinaryAutomaticSurrenderPolicy.Ready(OrdinaryAutomaticSurrenderPolicy.Variant.DE_JURE_NO_SAFE_ROUTE,
                activeWar(),options(),surrenderOption());
        for(Obj malformed:List.of(change(raw("surrender-war-7","submitted"),"accepted",new IntegerValue(BigInteger.ONE)),
                change(raw("surrender-war-7","submitted"),"extra",Nil.INSTANCE),
                raw("surrender-war-8","submitted"),raw("surrender-war-7","accepted")))
            assertThrows(IllegalArgumentException.class,()->RootWarActionExecutionResult.surrender(call,malformed,before(),noWar(),evidence));
        assertThrows(IllegalArgumentException.class,()->RootWarActionExecutionResult.surrender(call,raw("surrender-war-7","submitted"),before(),
                change(noWar(),"date_raw",new Bool(true)),evidence));
        assertThrows(IllegalArgumentException.class,()->RootWarActionExecutionResult.surrender(call,raw("surrender-war-7","submitted"),before(),
                change(noWar(),"date_raw",new IntegerValue(BigInteger.valueOf(1001))),evidence));
        var unknown=new ActionState.Unknown(Optional.empty(),Optional.empty(),"actual source missing",List.of());
        assertThrows(IOException.class,()->RootWarActionExecutionResult.requireObservedState(unknown));
        assertThrows(IOException.class,()->RootWarActionExecutionResult.requireObservedState(new ActionState.IntentDurable()));
        assertTrue(ActionTransitions.attempt(unknown).isEmpty());assertTrue(ActionTransitions.dispatch(unknown).isEmpty());
    }
    @Test void fullDriverOriginalsUseTheSharedTypedComposerAndKeepTheOldSmallByteLaneExplicit() {
        Obj large=change(before(),"ignored_opaque_original",new Text("x".repeat(StrictJson.EXPLICIT_MAX_BYTES+1024)));
        Obj primitive=raw("enforce-demands-7","submitted");
        Obj envelope=new Obj(Map.of("before_snapshot",large,"post_snapshot",noWar(),"action_result",primitive,
                "claims_result",Nil.INSTANCE,"title_holder_results",Nil.INSTANCE,"truce_result",Nil.INSTANCE));
        assertTrue(DriverJson.encode(envelope).length>StrictJson.EXPLICIT_MAX_BYTES);
        assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservationCodec
                .decodeAndCompose(DriverJson.encode(envelope)),"the generic legacy byte lane remains finite and must not parse full Driver originals");
        Obj result=RootWarActionExecutionResult.enforce(new ArmyCalls.War(PublicMethod.ENFORCE_DEMANDS,REV,BigInteger.valueOf(7)),primitive,large,noWar());
        Obj small=RootWarActionExecutionResult.enforce(new ArmyCalls.War(PublicMethod.ENFORCE_DEMANDS,REV,BigInteger.valueOf(7)),primitive,before(),noWar());
        assertEquals(small,result,"sole typed algorithm ignores unrelated retained original fields without truncating the input");
        RawJson wire=ArmyPublicWire.encodeExactSourceBound(result,context());
        assertEquals(result,ArmyPublicWire.decodeExactSourceBound(wire,context()));
    }

    @Test void actualOriginalDriverFormatterAstFeedsEveryBranchAndTheSharedPublicConsumer()throws Exception {
        var cases=new ArrayList<Value>();var results=new ArrayList<Obj>();
        var moveCall=new ArmyCalls.Move(REV,new PublicUnitId(0),new PositiveId(9));
        add(cases,results,"move",raw("move-army-0-to-9","submitted"),before(),moveAfter(),new Obj(Map.of()),
                RootWarActionExecutionResult.move(moveCall,raw("move-army-0-to-9","submitted"),before(),moveAfter()));
        for(boolean recovered:List.of(true,false)) {
            Obj response=negativeResponse(recovered?"CK3 move-army state is unavailable":"CK3 army state rejects movement");
            Obj last=recovered?rejectedMoveAfter():after();
            add(cases,results,recovered?"negative_move":"deferred_move",raw("move-army-0-to-9","submitted"),before(),last,
                    new Obj(Map.of("request",negativeRequest(),"response",response)),
                    RootWarActionExecutionResult.negativeMove(moveCall,before(),last,negativeRequest(),response,"negative-original"));
        }
        for(boolean start:List.of(true,false)) {
            Obj first=start?before():assaultAfter(true),last=start?assaultAfter(true):after();
            String step=(start?"start":"stop")+"-assault-5",status=(start?"start":"stop")+"_submitted";
            var call=new ArmyCalls.Siege(start?PublicMethod.START_ASSAULT:PublicMethod.STOP_ASSAULT,REV,new PositiveId(5));
            add(cases,results,"assault",raw(step,status),first,last,new Obj(Map.of("start",new Bool(start))),
                    RootWarActionExecutionResult.assault(call,raw(step,status),first,last,List.of(),List.of()));
        }
        add(cases,results,"enforce",raw("enforce-demands-7","submitted"),before(),noWar(),new Obj(Map.of()),
                RootWarActionExecutionResult.enforce(new ArmyCalls.War(PublicMethod.ENFORCE_DEMANDS,REV,BigInteger.valueOf(7)),
                        raw("enforce-demands-7","submitted"),before(),noWar()));
        for(var variant:OrdinaryAutomaticSurrenderPolicy.Variant.values()) {
            var evidence=new OrdinaryAutomaticSurrenderPolicy.Ready(variant,activeWar(),options(),surrenderOption());
            add(cases,results,"surrender",raw("surrender-war-7","submitted"),before(),noWar(),evidence.evidence(),
                    RootWarActionExecutionResult.surrender(new ArmyCalls.War(PublicMethod.SURRENDER_WAR,REV,BigInteger.valueOf(7)),
                            raw("surrender-war-7","submitted"),before(),noWar(),evidence));
        }
        for(var variant:OrdinaryWhitePeacePolicy.Variant.values()) {
            Optional<Obj> terms=variant==OrdinaryWhitePeacePolicy.Variant.CLAIM_CB?Optional.of(json("{\"claimant_character_id\":73,\"target_title_ids\":[91]}")):Optional.empty();
            var evidence=new OrdinaryWhitePeacePolicy.Ready(variant,activeWar(),options(),terms,whiteOption());
            add(cases,results,"white",raw("offer-white-peace-7","submitted"),before(),noWar(),evidence.evidence(),
                    RootWarActionExecutionResult.white(new ArmyCalls.War(PublicMethod.OFFER_WHITE_PEACE,REV,BigInteger.valueOf(7)),
                            raw("offer-white-peace-7","submitted"),before(),noWar(),evidence));
        }
        var choice=new DeclarationContract.Choice("24-2--1",BigInteger.valueOf(24),BigInteger.TWO,"claim_cb",
                BigInteger.valueOf(-1),BigInteger.valueOf(73),List.of(BigInteger.valueOf(91)));
        var origin=WarDeclarationContinuity.arm(before(),choice,Optional.of(new WarDeclarationContinuity.Roles(73,24)),"original-request-1");
        var pending=new WarDeclarationContinuity.Record(origin,WarDeclarationContinuity.Status.SUBMISSION_UNKNOWN,
                WarDeclarationContinuity.NativeResponse.UNKNOWN,true,OptionalInt.empty(),false,Optional.empty(),
                WarDeclarationContinuity.Reason.ORIGINAL_REQUEST_NOT_YET_OBSERVED);
        Obj declarationAfter=change(after(),"active_wars",new Arr(List.of(activeWar(),change(activeWar(),"war_id",new IntegerValue(BigInteger.valueOf(8))))));
        var continuity=WarDeclarationContinuity.observe(WarDeclarationContinuity.mark(pending,true),declarationAfter);
        add(cases,results,"declare",raw("declare-war-24-2--1","submitted"),before(),declarationAfter,WarDeclarationContinuity.json(continuity),
                RootWarActionExecutionResult.declaration(new ArmyCalls.Declaration(PublicMethod.DECLARE_WAR,REV,"24-2--1"),
                        raw("declare-war-24-2--1","submitted"),declarationAfter,continuity));
        Obj original=oracle(new Obj(Map.of("cases",new Arr(cases))));
        var records=OpportunityJson.array(original.get("results"),"original complete Driver results");
        assertEquals(results.size(),records.size());
        for(int i=0;i<records.size();i++) {
            assertEquals(records.get(i),results.get(i),"actual original formatter branch "+i);
            RawJson publicResult=ArmyPublicWire.encodeExactSourceBound(results.get(i),context());
            assertEquals(records.get(i),ArmyPublicWire.decodeExactSourceBound(publicResult,context()));
        }
    }
    private static void add(List<Value> cases,List<Obj> results,String mode,Obj raw,Obj before,Obj after,Obj evidence,Obj result) {
        cases.add(new Obj(Map.of("mode",new Text(mode),"raw",raw,"before",before,"after",after,"evidence",evidence)));results.add(result);
    }
    private static Obj oracle(Obj input)throws Exception {
        String python=System.getProperty("xar.python"),configured=System.getProperty("xar.repository.root");
        if(python==null||configured==null)throw new IOException("MISSING/NOT_RUN: original Python producer properties xar.python and xar.repository.root");
        Path root=Path.of(configured).toRealPath();
        String[][] pins={
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py","eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603"},
            {"ck3_autonomous_player/src/xar_autoplayer/ordinary_war_exit_observation_v1.py","593deae4c4c0c33eca17a3aaf3f810b6ec98462bed1ac7cb5161e431d03670dd"},
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/player_claims_contract.py","08fc5c228f16491d9faf3b065d5599662d73bbf854e380c5258e7f759ad863fc"},
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/player_truce_expiry_contract.py","318828fd2b221ff1564f160c7d1b03a01e8eaa7bc97262837bd50a2be6d7b3de"},
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/title_holder_contract.py","cbd762eb4944837baa7a4caf5500c4e088e72759bc9eb1f7506b0972b4466f81"}};
        for(String[] pin:pins) {
            Path original=root.resolve(pin[0]).toRealPath();assertTrue(original.startsWith(root));
            assertEquals(pin[1],HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(original))),"actual original source drift");
        }
        String script="""
                import ast,copy,json,pathlib,sys,types
                root=pathlib.Path(sys.argv[1]);src=root/'ck3_autonomous_player'/'src'
                sys.path.insert(0,str(src))
                from xar_autoplayer.ordinary_war_exit_observation_v1 import compose_ordinary_war_exit_observation_v1
                path=src/'xar_autoplayer'/'bridge'/'native_driver.py'
                tree=ast.parse(path.read_text(encoding='utf-8'))
                functions={node.name:node for node in ast.walk(tree) if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))}
                env={'copy':copy,'BridgeUnavailableError':ValueError,
                     'compose_ordinary_war_exit_observation_v1':compose_ordinary_war_exit_observation_v1}
                for name in ('_army_by_id','_army_move_postcondition','_army_is_known_stationary','_army_in_combat_or_retreat',
                             '_war_siege_province_states','_assault_siege_observation','_positive_native_id','_war_by_id'):
                    node=copy.deepcopy(functions[name]);node.decorator_list=[]
                    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(path),'exec'),env)
                def keys(node):
                    return {key.value for key in node.value.keys if isinstance(key,ast.Constant)} if isinstance(node,ast.Return) and isinstance(node.value,ast.Dict) else set()
                war=functions['_execute_native_war_step'];termination=functions['_execute_war_termination_step']
                returns=[node for node in ast.walk(war) if isinstance(node,ast.Return)]
                picks={'enforce':next(node for node in returns if 'war_victory' in keys(node)),
                       'assault':next(node for node in returns if 'assault_action' in keys(node)),
                       'negative_move':next(node for node in returns if 'native_error_evidence' in keys(node))}
                picks['deferred_move']=next(node for node in returns if 'war_action' in keys(node) and isinstance(node.value,ast.Dict)
                    and any(isinstance(k,ast.Constant) and k.value=='status' and isinstance(v,ast.Constant) and v.value=='deferred'
                            for k,v in zip(node.value.keys,node.value.values)))
                for node in returns:
                    if keys(node)=={'step','accepted','status','backend_id','war_action','player_armies','snapshot_id','revision'}:
                        continue
                    if 'war_action' in keys(node) and 'player_armies' in keys(node) and isinstance(node.value,ast.Dict):
                        for key,value in zip(node.value.keys,node.value.values):
                            if isinstance(key,ast.Constant) and key.value=='war_action' and isinstance(value,ast.Dict):
                                if any(isinstance(k,ast.Constant) and k.value=='status' and isinstance(v,ast.Name) and v.id=='status'
                                       for k,v in zip(value.keys,value.values)):
                                    picks['move']=node
                picks['declare']=next(node for node in ast.walk(functions['_execute_declarable_war_step']) if 'declaration' in keys(node))
                for node in ast.walk(termination):
                    if 'war_termination_result' not in keys(node):continue
                    action=next(value for key,value in zip(node.value.keys,node.value.values) if isinstance(key,ast.Constant) and key.value=='war_termination_result')
                    outcome=next(value for key,value in zip(action.keys,action.values) if isinstance(key,ast.Constant) and key.value=='outcome')
                    picks['white' if isinstance(outcome,ast.Constant) and outcome.value=='white_peace' else 'surrender']=node
                results=[]
                for case in json.load(sys.stdin)['cases']:
                    mode=case['mode'];before=case['before'];after=case['after'];raw=case['raw'];evidence=case['evidence']
                    local=dict(env,result=raw,starting=before,changed=after,current=after,step=raw['step'],
                               army_id=0,province_id=9,submitted_date_raw=before['date_raw'],war_id=7,
                               evidence=evidence,options=evidence.get('options'),terms=evidence.get('terms'),
                               war=evidence.get('war'),white_peace=evidence.get('white_peace'),surrender=evidence.get('surrender'),
                               war31_one_shot=False,reservation=None,explicit_surrender=False,explicit_once=None)
                    local['remaining_war']=env['_war_by_id'](after,7)
                    local['status']='applied' if local['remaining_war'] is None else 'submitted_pending'
                    if mode=='move':
                        local['status']=env['_army_move_postcondition'](after,0,9,require_route=True,starting_snapshot=before)
                    if mode in ('negative_move','deferred_move'):
                        starting_army=env['_army_by_id'](before,0);observed_army=env['_army_by_id'](after,0)
                        request=evidence['request'];response=evidence['response']
                        local.update(error=types.SimpleNamespace(native_error=response['error']),request=request,response=response,rid='negative-original',
                                     old_actor=before['played_character'],new_actor=after['played_character'],old_diag=before['diagnostics'],new_diag=after['diagnostics'],
                                     old_route=starting_army.get('route_province_ids'),route=observed_army.get('route_province_ids'),starting_army=starting_army)
                    if mode=='assault':
                        start=evidence['start']
                        observation=env['_assault_siege_observation'](before,siege_id=5)
                        applied=env['_assault_siege_observation'](after,siege_id=5,war_id=7,province_id=9)
                        local.update(observation=observation,applied=applied,starting_siege_id=5,is_start=start,
                                     expected_active=start,expected_submission_status='start_submitted' if start else 'stop_submitted',
                                     action_status='assault_started' if start else 'assault_stopped')
                        # Use the actual source assignment for assault_action, retaining every original field and conditional.
                        assignment=next(node for node in ast.walk(war) if isinstance(node,ast.Assign)
                                        and any(isinstance(target,ast.Name) and target.id=='assault_action' for target in node.targets))
                        exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(assignment)],type_ignores=[])),str(path),'exec'),local)
                    if mode=='declare':
                        local.update(declaration=evidence['declaration'],continuity=evidence,declaration_id=evidence['declaration']['declaration_id'],
                                     request_id=evidence['request_id'],war_started=evidence['status']=='war_started',active_wars=after['active_wars'])
                    if mode in ('surrender','white'):
                        local['response']=evidence['surrender' if mode=='surrender' else 'white_peace']['recipient_response']
                    node=copy.deepcopy(picks[mode])
                    fn=ast.FunctionDef(name='actual_result',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),
                                       body=[node],decorator_list=[])
                    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(path),'exec'),local)
                    results.append(local['actual_result']())
                print(json.dumps({'results':results},ensure_ascii=False,allow_nan=False,separators=(',',':')))
                """;
        var builder=new ProcessBuilder(python,"-B","-c",script,root.toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.environment().put("PYTHONIOENCODING","utf-8");
        Process process=builder.start();
        try {
            process.getOutputStream().write(DriverJson.encode(input));process.getOutputStream().close();
            var output=java.util.concurrent.CompletableFuture.supplyAsync(()->readBounded(process.getInputStream()));
            var errors=java.util.concurrent.CompletableFuture.supplyAsync(()->readBounded(process.getErrorStream()));
            if(!process.waitFor(30,TimeUnit.SECONDS)){process.destroyForcibly();throw new IOException("original war formatter oracle timed out");}
            byte[] bytes=output.get(5,TimeUnit.SECONDS),stderr=errors.get(5,TimeUnit.SECONDS);
            assertEquals(0,process.exitValue(),new String(stderr,StandardCharsets.UTF_8));return DriverJson.object(bytes,1024*1024);
        } finally {if(process.isAlive())process.destroyForcibly();}
    }
    private static byte[] readBounded(java.io.InputStream input) {
        try {byte[] result=input.readNBytes(1024*1024+1);if(result.length>1024*1024)throw new IOException("bounded original oracle output exceeded");return result;}
        catch(IOException error){throw new java.io.UncheckedIOException(error);}
    }
}

