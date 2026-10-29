package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Existing real Python budget/proposal/post producers are oracle inputs; no replacement Python business is written. */
final class OrdinaryMilitaryOriginalProducerTest {
    private static final String PROGRAM="""
            import copy,hashlib,json,pathlib,runpy,sys
            repo=pathlib.Path(sys.argv[1]); sys.path.insert(0,str(repo/'ck3_autonomous_player'/'src')); sys.path.insert(0,str(repo/'ck3_autonomous_player'/'tests'/'unit'))
            names=['ck3_autonomous_player/src/xar_autoplayer/war_active_retreat_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/ordinary_retreat_service_v1.py','ck3_autonomous_player/tests/unit/test_ordinary_active_retreat_v1.py']
            before={n:hashlib.sha256((repo/n).read_bytes()).hexdigest() for n in names}
            m=runpy.run_path(str(repo/names[2])); p=m['policy']; cases=[]
            def wire_scene():
                s,c,v=m['scene']()
                for army in s['player_armies']+[a for war in s['active_wars'] for a in war['enemy_armies']]:
                    if army.get('route_read_status')=='complete_empty':army.update(route_source_count=0,move_target_observable=False)
                    elif army.get('route_read_status')=='complete_nonempty':army.update(route_source_count=len(army['route_province_ids']),move_target_observable=True)
                return s,c,v
            for change in ('baseline','semantic_soldiers','score','attacker','no_targets','not_primary','unrelated_war','stronger','enemy_rally','enemy_route_unknown'):
                s,c,v=wire_scene(); w=s['active_wars'][0]
                if change=='semantic_soldiers':s['player_armies'][0]['soldiers']=999999
                elif change=='score':w['player_relative_war_score']=0
                elif change=='attacker':w['player_side']='attacker'
                elif change=='no_targets':w['targeted_title_ids']=[]
                elif change=='not_primary':w['player_is_primary_war_leader']=False
                elif change=='unrelated_war':w['enemy_armies'][0]['army_id']=999
                elif change=='stronger':c['attacker']['derived_current_fighting_raw']+=1
                elif change=='enemy_rally':w['enemy_armies'][0].update(route_read_status='complete_nonempty',route_source_count=1,move_target_observable=True,move_target_province_id=2579,route_province_ids=[2579])
                elif change=='enemy_route_unknown':w['enemy_armies'][0].update(route_read_status='not_attempted',route_source_count=None,move_target_observable=False,move_target_province_id=None,route_province_ids=[])
                cases.append({'change':change,'snapshot':s,'control':c,'budget':p.normal_retreat_loss_budget(s,c),'rallies':p._rallies(s,c['combat_province_id'])})
            s,c,v=wire_scene(); budget=p.normal_retreat_loss_budget(s,c)
            proposal=p.propose_retreat(s,c,m['CAPS'],maximum_next_tick_hard_loss_raw=budget['maximum_next_tick_hard_loss_raw'],preview=v)
            assert proposal['stage']=='order'
            keys=('source_binding','selected_owner_character_id','arguments','affected_public_cunit_ids_in_stored_order','unaffected_same_side_public_cunit_ids_in_stored_order','route_province_ids','assessment')
            order={k:proposal[k] for k in keys}; intent={**order,'episode_run_id':s['episode_run_id']}; service=m['TypedService'](pathlib.Path('unused-read-only')); service.current=s; service.control=c; m['post_scene'](service)
            posts=[]
            for change in ('valid','owner','combat','target','connection','same_frame'):
                post,transition=copy.deepcopy(service.current),copy.deepcopy(service.transition)
                if change=='owner':post['player_armies'][0]['owner_character_id']+=1
                elif change=='combat':transition['combat_id']+=1
                elif change=='target':post['player_armies'][0]['move_target_province_id']+=1
                elif change=='connection':post['diagnostics']['connection_generation']+=1
                elif change=='same_frame':post.update(revision=7,snapshot_id='fixture-current-retreat')
                posts.append({'change':change,'snapshot':post,'transition':transition,'expected':p.verify_independent_post(intent,post,transition)})
            after={n:hashlib.sha256((repo/n).read_bytes()).hexdigest() for n in names}; assert before==after
            print(json.dumps({'pins':before,'cases':cases,'order':order,'preview':v,'posts':posts},ensure_ascii=False,separators=(',',':')))
            """;
    @Test void actualBudgetAndRallyProducersMatchAllRealCounterpolicyGuards() throws Exception {
        Obj corpus=oracle();assertEquals(10,rows(corpus.get("cases")).size());
        for(Obj row:rows(corpus.get("cases"))) {
            Obj snapshot=OpportunityJson.object(row.get("snapshot"),"snapshot"),control=OpportunityJson.object(row.get("control"),"control");
            assertEquals(row.get("budget"),ActiveRetreatProposal.normalBudget(snapshot,control).json(),optionalText(row.get("change")));
            assertEquals(row.get("rallies"),numbers(ActiveRetreatProposal.rallies(snapshot,province(control.get("combat_province_id")))),optionalText(row.get("change")));
        }
    }
    @Test void actualProposalFlowsThroughSingleWriterReducerAndIndependentCurrentPost() throws Exception {
        Obj corpus=oracle();var order=ActiveRetreatState.order(OpportunityJson.object(corpus.get("order"),"actual proposed order"));
        var initial=ActiveRetreatState.State.initial();var started=ActiveRetreatState.reduce(initial,new ActiveRetreatState.StartOrder(order));
        var key=ActiveRetreatState.ClaimKey.of(order);
        var unknown=ActiveRetreatState.reduce(started,new ActiveRetreatState.UnknownOrder(key,"synthetic lost original ACK"));
        var restored=ActiveRetreatState.decode(OpportunityJson.object(OpportunityJson.parse(OpportunityJson.encode(ActiveRetreatState.encode(unknown))),"persisted domain"));
        assertEquals(unknown,restored);assertEquals(order,restored.pending().orElseThrow());
        assertThrows(IllegalArgumentException.class,()->ActiveRetreatState.reduce(restored,new ActiveRetreatState.StartOrder(order)));
        for(Obj row:rows(corpus.get("posts"))) {
            Obj snapshot=OpportunityJson.object(row.get("snapshot"),"independent snapshot"),transition=OpportunityJson.object(row.get("transition"),"independent transition");
            var actual=ActiveRetreatPost.transition(order,snapshot,transition);Obj expected=OpportunityJson.object(row.get("expected"),"original post");
            assertEquals(expected.get("operational_retreat_verified"),actual.json().get("operational_retreat_verified"),optionalText(row.get("change")));
            assertEquals(new Bool(false),actual.json().get("war_outcome_verified"));assertEquals(new Bool(false),actual.json().get("replay_allowed"));
            if(actual instanceof ActiveRetreatPost.Observed observed) {
                var observing=ActiveRetreatState.reduce(restored,new ActiveRetreatState.StartObserve(observed.after()));
                var done=ActiveRetreatState.reduce(observing,new ActiveRetreatState.FinishObserve(observed.after(),observed));
                assertTrue(done.pending().isEmpty());assertTrue(done.claimed(key));assertThrows(IllegalArgumentException.class,()->ActiveRetreatState.reduce(done,new ActiveRetreatState.StartOrder(order)));
                assertThrows(IllegalArgumentException.class,()->ActiveRetreatState.requireClaimsRetained(done,initial));
            }
        }
    }
    @Test void actualCurrentModelAndNormalizedPreviewProduceTheSameOriginalRetreatOrder() throws Exception {
        Obj corpus=oracle(),row=rows(corpus.get("cases")).getFirst();Obj snapshot=OpportunityJson.object(row.get("snapshot"),"snapshot"),control=OpportunityJson.object(row.get("control"),"actual normalized control");
        var request=GeneralBattleForecastIngressOriginalTest.request(obj(f("snapshot",snapshot),f("history",new Arr(List.of())),f("steps",new Arr(List.of())),f("capabilities",new Arr(List.of()))));
        var budget=assertInstanceOf(ActiveRetreatProposal.BudgetObserved.class,ActiveRetreatProposal.normalBudget(snapshot,control));
        var model=new CurrentBattleRetreatModel();
        assertInstanceOf(ActiveRetreatProposal.Preview.class,ActiveRetreatProposal.propose(request,control,budget,java.util.Optional.empty(),model));
        var order=assertInstanceOf(ActiveRetreatProposal.Order.class,ActiveRetreatProposal.propose(request,control,budget,java.util.Optional.of(OpportunityJson.object(corpus.get("preview"),"actual normalized preview")),model));
        assertEquals(corpus.get("order"),ActiveRetreatState.order(order));
        Obj missing=control.with("current_loss_inputs_v1",Nil.INSTANCE);
        assertInstanceOf(ActiveRetreatProposal.Keep.class,ActiveRetreatProposal.propose(request,missing,budget,java.util.Optional.empty(),model),"missing actual current loss operands cannot invent an order");
    }
    @Test void contractRejectsBooleanFloatMissingAndNullAndKeepsFullCombatAndUint64Identity() throws Exception {
        Obj corpus=oracle();var order=ActiveRetreatState.order(OpportunityJson.object(corpus.get("order"),"order"));Obj body=ActiveRetreatState.encode(ActiveRetreatState.reduce(ActiveRetreatState.State.initial(),new ActiveRetreatState.StartOrder(order)));
        Obj pending=OpportunityJson.object(body.get("pending"),"pending"),args=OpportunityJson.object(pending.get("arguments"),"args");
        for(Value invalid:List.of(new Bool(true),new DecimalValue("1.0"),Nil.INSTANCE,new Text("1")))
            assertThrows(IllegalArgumentException.class,()->ActiveRetreatState.decode(body.with("pending",pending.with("arguments",args.with("expected_combat_id",invalid)))));
        assertThrows(IllegalArgumentException.class,()->ActiveRetreatState.decode(body.with("claims",Nil.INSTANCE)));
        var signed=new org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.RetreatOrder(0,new java.math.BigInteger("9007199254740993"),Integer.MIN_VALUE,0,org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.Scope.FULL_SIDE,2579,"native-token");
        var frame=new ActiveRetreatProposal.SourceFrame("native:9007199254740993",signed.expectedRevision(),signed.expectedRevision(),java.math.BigInteger.valueOf(53219928),"exact-episode",signed.expectedRevision());
        var exact=new ActiveRetreatProposal.Order(frame,29829,signed,List.of(0),List.of(),List.of(2579),empty());
        var encoded=ActiveRetreatState.encode(ActiveRetreatState.reduce(ActiveRetreatState.State.initial(),new ActiveRetreatState.StartOrder(exact)));
        assertEquals(exact,ActiveRetreatState.decode(OpportunityJson.object(OpportunityJson.parse(OpportunityJson.encode(encoded)),"roundtrip")).pending().orElseThrow());
        assertFalse(MilitaryTimeline.isMutationFence("move-army-00-to-2"));assertTrue(MilitaryTimeline.isMutationFence("move-army-0-to-2"));
        assertTrue(MilitaryTimeline.isMutationFence("life-advance-one-day"));assertTrue(MilitaryTimeline.isMutationFence("battle-decision-epoch-advance-to-24"));
    }
    private static Obj oracle() throws Exception {return original(PROGRAM);}
    static Obj original(String program) throws Exception {
        String repository=required("xar.repository.root"),python=required("xar.python");ProcessBuilder builder=new ProcessBuilder(python,"-B","-X","utf8","-c",program,repository);
        builder.directory(Path.of(repository).toFile());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");Process process=builder.start();
        try(var readers=Executors.newVirtualThreadPerTaskExecutor()) {
            var out=readers.submit(()->read(process.getInputStream()));var err=readers.submit(()->read(process.getErrorStream()));
            try {process.getOutputStream().close();assertTrue(process.waitFor(45,TimeUnit.SECONDS),"original military producer timeout is RED");byte[] output=out.get(5,TimeUnit.SECONDS),error=err.get(5,TimeUnit.SECONDS);assertEquals(0,process.exitValue(),new String(error,StandardCharsets.UTF_8));return DriverJson.object(output,2*1024*1024);}
            finally{if(process.isAlive())process.destroyForcibly();}
        }
    }
    private static byte[] read(InputStream input)throws IOException{byte[] result=input.readNBytes(2*1024*1024+1);if(result.length>2*1024*1024)throw new IOException("bounded military original output exceeded");return result;}
    private static String required(String property){String result=System.getProperty(property);assertNotNull(result,"full step requires "+property);assertFalse(result.isBlank());return result;}
}
