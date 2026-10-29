package org.xar.ck3.control.application.planning.military;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Existing CompiledOriginalCapture-compatible test entry. Executes original helpers; creates no Python production source. */
public final class WarCoreBoundaryOriginalCapture {
    private WarCoreBoundaryOriginalCapture() { }
    public static void main(String[] args)throws IOException,InterruptedException {
        if(args.length!=3)throw new IllegalArgumentException("repo python fresh-output required");
        Path repo=Path.of(args[0]).toAbsolutePath(),output=Path.of(args[2]).toAbsolutePath();
        if(Files.exists(output))throw new IllegalArgumentException("fresh original capture required");
        Process child=new ProcessBuilder(List.of(args[1],"-B","-c",SCRIPT,repo.toString(),output.toString())).directory(repo.toFile()).inheritIO().start();
        if(!child.waitFor(90,TimeUnit.SECONDS)){child.destroyForcibly();throw new IllegalStateException("original boundary capture timed out; Root Job owns remaining cleanup");}
        if(child.exitValue()!=0)throw new IllegalStateException("actual original boundary producer exited "+child.exitValue());
        if(!Files.isRegularFile(output)||Files.size(output)==0||Files.size(output)>1_048_576)throw new IllegalStateException("capture requires bounded nonempty output");
    }
    private static final String SCRIPT="""
            import sys,json,copy,hashlib,datetime
            from pathlib import Path
            repo=Path(sys.argv[1]);output=Path(sys.argv[2]);sys.path.insert(0,str(repo/'ck3_autonomous_player/src'));sys.path.insert(0,str(repo/'tools'))
            from ck3_live_run_id import current_machine_id
            from xar_autoplayer import strategy
            from xar_autoplayer.bridge import native_driver
            from xar_autoplayer.current_native_war_end_conditions_v1 import assess_current_native_war_end_conditions_v1
            checkpoint={'sha256':'a'*64,'size':17,'date_raw':24000,'history_index':1}
            restored={'date_raw':24000,'player_armies':[{'army_id':304,'current_province_id':48}],'active_wars':[{'war_id':25,'allied_armies':[{'army_id':304,'controllable':True}]}]}
            def row(i,c,r):return {'index':i,'command':c,'ok':True,'result':r}
            base=[row(2,'preview-move-army-304-to-52',{'route_preview':{'status':'available','army_id':304,'origin_province_id':48,'target_province_id':52,'route_province_ids':[50,53,52],'previewed_date_raw':24000}}),row(3,'move-army-304-to-52',{'war_action':{'status':'moving','army_id':304,'target_province_id':52,'submitted_date_raw':24000},'player_armies':[{'army_id':304,'move_target_province_id':52,'route_province_ids':[53,52]}]})]
            event=row(4,'query-current-event-window-context-v1',{'accepted':True,'status':'available','current_event_instance_id':3,'current_event_window_context':{'status':'available','window_match_count':1,'current_event_instance_id':3,'event_definition_key':'death_management.1000'}})
            rollback=[]
            for name,history in [('moving_discarded_branch',base),('unresolved_player_event',[*base,event]),('event_was_chosen',[*base,row(4,'select-event-option-2',{'status':'postcondition_verified'}),dict(event,index=5)])]:
                before=copy.deepcopy(history)
                expected=native_driver._derive_rollback_war_failure_from_epoch(history,checkpoint=checkpoint,restored_snapshot=restored,episode_run_id='native-31853-r849')
                if history!=before:raise AssertionError('original mutated '+name)
                rollback.append({'name':name,'history':history,'checkpoint':checkpoint,'restored_snapshot':restored,'episode_run_id':'native-31853-r849','expected':expected})
            start=row(1,'start-assault-9',{'assault_action':{'status':'assault_started','siege_id':9,'war_id':88,'province_id':2585}})
            war={'war_id':88,'player_side':'attacker','player_is_primary_war_leader':True,'player_relative_war_score':24,'allied_armies':[],'objective_province_states':[]}
            snapshot={'paused':True,'war_objective_assault_supported':True,'active_wars':[war],'played_character':{'character_id':29829,'alive':True},'date_raw':24000,'snapshot_id':'snapshot-1','revision':1,'native_revision':1,'episode_run_id':'episode-1','diagnostics':{'connection_generation':1}}
            assault=[]
            for name,history,states in [('missing_rich_row',[start],[]),('explicit_null_closes',[start],[{'province_id':2585,'siege_observable':True,'active_siege':None}]),('missing_does_not_close',[start],[{'province_id':2585,'siege_observable':True}]),('proven_stop_closes',[start,row(2,'stop-assault-9',{'assault_action':{'status':'assault_stopped','siege_id':9,'war_id':88,'province_id':2585}})],[])]:
                sem=copy.deepcopy(snapshot);sem['active_wars'][0]['objective_province_states']=states
                expected=strategy._unobservable_started_assaults(sem,active_wars=sem['active_wars'],commands=history)
                assault.append({'name':name,'snapshot':sem,'history':history,'expected':expected})
            option={'outcome':'white_peace','context_constructed':True,'native_validator_passed':True,'available':True,'ai_acceptance':100,'auto_accept':False,'recipient_response':{'status':'unavailable','would_accept_now':True}}
            end=[]
            for name,value in [('no_current_options',None),('answer_is_unavailable',{'options':{'surrender':option,'white_peace':option,'victory':dict(option,available=False)}})]:
                end.append({'name':name,'war':war,'options':value,'expected':assess_current_native_war_end_conditions_v1(war,value)})
            sources=['tools/ck3_live_run_id.py','ck3_autonomous_player/src/xar_autoplayer/strategy.py','ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py','ck3_autonomous_player/src/xar_autoplayer/current_native_war_end_conditions_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/assault_holding_observation_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py']
            data={'schema':'xar.warcore-boundary-original-golden.v1','machine_id':current_machine_id(),'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'new_live_evidence':False,'origin':'Existing original producer functions called directly with regression shapes from native driver and gameplay bridge tests; no original business implementation is reconstructed.','source_bindings':[{'path':p,'bytes':(repo/p).stat().st_size,'sha256':hashlib.sha256((repo/p).read_bytes()).hexdigest()} for p in sources],'rollback':rollback,'assault':assault,'end_conditions':end}
            raw=(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'))+chr(10)).encode()
            if len(raw)>1048576:raise ValueError('capture bound exceeded')
            output.parent.mkdir(parents=True,exist_ok=True)
            with output.open('xb') as stream:stream.write(raw)
            print(json.dumps({'machine_id':data['machine_id'],'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'cases':len(rollback)+len(assault)+len(end)}))
            """;
}
