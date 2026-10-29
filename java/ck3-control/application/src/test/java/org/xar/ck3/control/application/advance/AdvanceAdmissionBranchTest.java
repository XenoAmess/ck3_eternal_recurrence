package org.xar.ck3.control.application.advance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.governance.CrownRetryDueTest;
import org.xar.ck3.control.application.planning.military.BattleReaderWatch;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

/** Synthetic original-input regressions. No test authorizes a Native process, actual writer or game day. */
final class AdvanceAdmissionBranchTest {
    private static final Instant NOW=Instant.parse("2026-10-23T19:00:00Z");
    private static final BigInteger DATE=BigInteger.valueOf(53288256);
    private static final ExactRef DEFINITION=new ExactRef("fixture/watch-native-definition",1,"a".repeat(64));
    private static final G2Source SOURCE=new G2Source("xenoamess-full-tower-eb9d2c1186",NOW.toString(),"1.20.0.4",DEFINITION);
    private static final Set<String> CAPS=Set.of(ClockStatusRead.ARM_CAP,ClockStatusRead.STATUS_CAP,ClockStatusRead.CANCEL_CAP,"game.state.pending-character-interaction");
    private static final Set<OperationKey> STEPS=Set.of(new OperationKey("life-advance-one-day"),new OperationKey("set-speed-2"),new OperationKey("set-speed-5"),new OperationKey("resume-map"),new OperationKey("pause-map"));
    private static Obj json(String value) { return DriverJson.object(value.getBytes(StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES); }
    private static IntegerValue n(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static AdvanceObservationPort.Frame frame(Obj semantic) {
        var observed=new ObservationIdentity(SOURCE.machineId(),new GameGeneration(4242,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),integer(semantic.get("native_revision"),"native_revision"),integer(semantic.get("date_raw"),"date_raw")),
                        text(semantic.get("snapshot_id"),"snapshot_id"),integer(semantic.get("revision"),"revision"),"fixture-episode"),1);
        byte[] raw=DriverJson.encode(semantic); ExactRef packet=new ExactRef("fixture/SEM-"+DriverJson.sha256(raw),raw.length,DriverJson.sha256(raw));
        return new AdvanceObservationPort.Frame(observed,SOURCE,"fixture-session",semantic,new ObservationProvenance.Push(observed.frame().snapshotId(),observed.frame().identity().nativeRevision(),packet),NOW,packet);
    }
    private static Obj army(int id,int owner,int province,boolean controlled,boolean combat) {
        return new Obj(Map.of("army_id",n(id),"owner_character_id",n(owner),"current_province_id",n(province),"move_target_province_id",Nil.INSTANCE,
                "controllable",new Bool(controlled),"in_combat",new Bool(combat),"retreating",new Bool(false),"army_state",new Text(combat ? "combat" : "regular"),
                "army_state_code",n(combat ? 2 : 1),"route_province_ids",new Arr(List.of())));
    }
    private static Obj snapshot(boolean combat) {
        Obj own=army(11,29829,2510,true,combat), enemy=army(33,50000,combat ? 2510 : 3011,false,combat);
        return json("""
                {"snapshot_id":"native:1","revision":1,"native_revision":1,"date_raw":53288256,"speed":1,"paused":true,"map_ready":true,
                 "episode_run_id":"fixture-episode","episode_character_id":29829,"local_player_id":0,"played_character":{"character_id":29829,"alive":true},
                 "one_life_terminal":false,"one_life_terminal_reason":null,"active_event":null,"pending_character_interaction":null,
                 "war_objective_assault_supported":true,"top_exclusive_modal_choice_hint":{"status":"absent","owner_verified":true},
                 "diagnostics":{"connected":true,"bridge_pid":4242,"connection_generation":1,"hello":{"ck3_build_match":true}}}
                """).with("player_armies",new Arr(List.of(own))).with("active_wars",new Arr(List.of(new Obj(Map.of("war_id",n(1),"player_relative_war_score",n(0),"allied_armies",new Arr(List.of(own)),"enemy_armies",new Arr(List.of(enemy)))))))
                .with("diagnostics",json("{\"connected\":true,\"bridge_pid\":4242,\"connection_generation\":1}").with("hello",new Obj(Map.of("ck3_build_match",new Bool(true),
                        "expected_ck3_version",new Text(ExactCk3Build.CK3_12004.version()),"expected_ck3_sha256",new Text(ExactCk3Build.CK3_12004.executableSha256())))));
    }
    @Test void warWatchIsDefaultOffAndRejectsIncompleteOrTrimmedRosterInputs() {
        var actual=frame(snapshot(false));
        assertTrue(WarDailyWatch.select(actual,false,true,"life-advance-one-day",Optional.empty(),CAPS,STEPS,false).isEmpty());
        var context=WarDailyWatch.select(actual,true,true,"life-advance-one-day",Optional.empty(),CAPS,STEPS,false).orElseThrow();
        assertEquals(List.of(11,33),context.watchArmyIds()); assertEquals(context,WarDailyWatch.decode(WarDailyWatch.encode(context)));
        assertTrue(context.readyToArm(frame(actual.semantic().with("speed",n(2)))));
        assertThrows(IllegalArgumentException.class,() -> frame(actual.semantic().with("speed",new DecimalValue("2.0"))));
        Obj war=object(array(actual.semantic().get("active_wars"),"wars").getFirst(),"war");
        Obj missing=actual.semantic().with("active_wars",new Arr(List.of(war.with("enemy_armies",Nil.INSTANCE))));
        assertTrue(WarDailyWatch.select(frame(missing),true,true,"life-advance-one-day",Optional.empty(),CAPS,STEPS,false).isEmpty());
        Obj enemy=object(array(war.get("enemy_armies"),"enemies").getFirst(),"enemy");
        for (Value invalid:List.of(new Bool(true),new DecimalValue("33.0"),n(-1),n(0))) {
            Obj altered=actual.semantic().with("active_wars",new Arr(List.of(war.with("enemy_armies",new Arr(List.of(enemy.with("army_id",invalid)))))));
            assertTrue(WarDailyWatch.select(frame(altered),true,true,"life-advance-one-day",Optional.empty(),CAPS,STEPS,false).isEmpty());
        }
        assertTrue(WarDailyWatch.select(actual,true,true,"life-advance-one-day",Optional.of("contact_free"),CAPS,STEPS,false).isEmpty());
        assertTrue(WarDailyWatch.select(actual,true,true,"life-advance-one-day",Optional.empty(),CAPS,STEPS,true).isEmpty());
    }
    private static Obj unavailable(Obj frame) {
        Obj source=new Obj(Map.of("snapshot_id",frame.get("snapshot_id"),"revision",frame.get("revision"),"native_revision",frame.get("native_revision"),"date_raw",frame.get("date_raw"),
                "actor_character_id",n(29829),"episode_run_id",frame.get("episode_run_id"),"bridge_pid",n(4242),"connection_generation",n(1),"paused",new Bool(true),"map_ready",new Bool(true)));
        String step="query-battle-control-snapshot-v1-11";
        Obj request=new Obj(Map.of("type",new Text("execute_step"),"protocol_version",n(1),"request_id",new Text("actual-failed-read"),"step",new Text(step),"expected_revision",n(1)));
        Obj failure=json("""
                {"executor_enter":true,"executor_exception":{"code":0,"image":"none","rva":null},"executor_finish":true,"executor_typed_result":false,
                 "final_equal":null,"final_read":null,"frame_stable":true,"query_type":"battle_control","stage":"typed_result","typed_result":false,"wait_completed":true,"wait_result":"completed"}
                """);
        Obj response=new Obj(Map.of("type",new Text("command_result"),"protocol_version",n(1),"request_id",new Text("actual-failed-read"),"ok",new Bool(false),
                "error",new Text("application-main typed query failed or its snapshot changed"),"typed_query_failure_v1",failure));
        Obj scope=new Obj(Map.of("subject_army_id",n(11),"province_id",n(2510),"actor_character_id",n(29829),"episode_run_id",frame.get("episode_run_id"),"bridge_pid",n(4242),"connection_generation",n(1),
                "active_war_ids",new Arr(List.of(n(1))),"observed_combat_army_ids",new Arr(List.of(n(11),n(33)))));
        return new Obj(Map.ofEntries(Map.entry("schema",new Text(BattleReaderWatch.SCHEMA)),Map.entry("step",new Text(step)),Map.entry("accepted",new Bool(false)),Map.entry("status",new Text("unavailable")),
                Map.entry("read_only",new Bool(true)),Map.entry("business_submission",new Bool(false)),Map.entry("replay_allowed",new Bool(false)),Map.entry("backend_id",new Text("native-headless")),
                Map.entry("battle_control_snapshot",Nil.INSTANCE),Map.entry("diagnostic_reason",new Text("native_battle_control_typed_read_failed")),Map.entry("prediction_ready",new Bool(false)),Map.entry("retreat_authorized",new Bool(false)),
                Map.entry("scope_key",scope),Map.entry("source_frame",source),Map.entry("same_frame_readback",source),Map.entry("native_request",request),Map.entry("native_command_result",response)));
    }
    @Test void realFailedReaderWatchFeedsTheSelectedNativeExactDaySpeedFiveOnly() {
        Obj semantic=snapshot(true), failure=unavailable(semantic); BattleReaderWatch.validateUnavailable(failure);
        Obj row=new Obj(Map.of("index",n(1),"command",failure.get("step"),"ok",new Bool(false),"result",failure)); List<Obj> history=List.of(row);
        var actual=frame(semantic); var request=new PlanningRequest(actual.identity(),SOURCE,actual.sessionId(),NOW.plusSeconds(30),new PlanningObservation(semantic,history,STEPS,CAPS,Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        var original=original(request,"life-advance-one-day");
        var facts=AdvanceHistory.verifiedFacts(original,actual,history,STEPS,CAPS,45,false,actual.originalEvidence());
        assertTrue(facts.readerUnavailableSpeedFiveReady()); assertTrue(facts.dailyWatch().isEmpty());
        AdvancePlan plan=AdvancePlan.decode(AdvanceRewrite.rewriteBound(request,original,"life-advance-one-day",Optional.empty(),facts));
        assertEquals(5,plan.speed()); assertEquals(ReaderUnavailableSpeed.POLICY,plan.policy()); assertEquals(AdvancePlan.ClockMode.EXACT_SENTINEL,plan.clockMode());
        assertEquals(DATE.add(AdvancePlan.DAY),plan.targetDateRaw()); assertTrue(plan.watchArmyIds().isEmpty());
        Obj wrong=failure.with("native_command_result",object(failure.get("native_command_result"),"response").with("request_id",new Text("other-request")));
        assertFalse(ReaderUnavailableSpeed.ready(semantic,List.of(row.with("result",wrong)),true,"life-advance-one-day",Optional.empty(),CAPS,STEPS,false));
        assertFalse(ReaderUnavailableSpeed.ready(semantic,history,true,"life-advance-one-day",Optional.empty(),CAPS,STEPS,true));
    }
    @Test void actualCrownPublisherPrivateDueClipsRealOrdinaryAdvanceHorizonAndNoProofPreservesThirtyDays() throws Exception {
        var captured=CrownRetryDueTest.publishedDueFixture(); var identity=captured.observed();
        Obj semantic=captured.semantic().with("speed",n(1)).with("episode_character_id",new IntegerValue(identity.frame().identity().player()))
                .with("active_event",Nil.INSTANCE).with("pending_character_interaction",Nil.INSTANCE).with("one_life_terminal_reason",Nil.INSTANCE)
                .with("player_armies",new Arr(List.of())).with("active_wars",new Arr(List.of()));
        byte[] raw=DriverJson.encode(semantic); ExactRef ref=new ExactRef("fixture/crown-semantic",raw.length,DriverJson.sha256(raw));
        var frame=new AdvanceObservationPort.Frame(identity,captured.source(),"actual-crown-fixture",semantic,new ObservationProvenance.Push(identity.frame().snapshotId(),identity.frame().identity().nativeRevision(),ref),NOW,ref);
        var stamp=new DriverSnapshotFacts.Stamp(1,0,identity.game(),identity.frame().episodeRunId(),ref.sha256());
        Set<OperationKey> steps=Set.of(new OperationKey("set-speed-5"),new OperationKey("resume-map"),new OperationKey("pause-map"));
        var runtime=new ProductionAdvanceReadiness.RuntimeFacts(identity,captured.source(),frame.sessionId(),stamp,steps,CAPS,Optional.of(captured.due()),true,true,false,ref);
        int bound=ProductionAdvanceReadiness.verifiedCrownMaximum(runtime,frame,captured.producer(),captured.borrowed(), NOW.plusSeconds(30)); assertEquals(10,bound);
        var request=new PlanningRequest(identity,captured.source(),frame.sessionId(),NOW.plusSeconds(30),new PlanningObservation(semantic,List.of(),steps,CAPS,Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        var original=original(request,"life-advance");
        var actual=AdvanceHistory.verifiedFacts(original,frame,List.of(),steps,CAPS,bound,false,ref);
        AdvancePlan clipped=AdvancePlan.decode(AdvanceRewrite.rewriteBound(request,original,"life-advance",Optional.empty(),actual));
        assertEquals(10,clipped.horizonDays()); assertEquals(identity.frame().identity().dateRaw().add(AdvancePlan.DAY.multiply(BigInteger.TEN)),clipped.targetDateRaw());
        var absent=new ProductionAdvanceReadiness.RuntimeFacts(identity,captured.source(),frame.sessionId(),stamp,steps,CAPS,Optional.empty(),true,true,false,ref);
        assertEquals(45,ProductionAdvanceReadiness.verifiedCrownMaximum(absent,frame,captured.producer(),captured.borrowed(), NOW.plusSeconds(30)));
        var uncut=AdvanceHistory.verifiedFacts(original,frame,List.of(),steps,CAPS,45,false,ref);
        assertEquals(30,AdvancePlan.decode(AdvanceRewrite.rewriteBound(request,original,"life-advance",Optional.empty(),uncut)).horizonDays());
        assertFalse(captured.due().authorizesAction()); assertEquals(0,captured.due().savedDayCredit());
    }
    private static ActionCommand original(PlanningRequest request,String step) {
        return new ActionCommand("admission-fixture",request.before(),request.source(),request.sessionId(),new OperationKey(step),new Obj(Map.of()),
                new ExpectedPostcondition(1,request.before(),request.source(),"fixture/skeleton",List.of(new ExpectedBoolean(new FieldKey("paused"),true))),
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),request.deadline());
    }
}
