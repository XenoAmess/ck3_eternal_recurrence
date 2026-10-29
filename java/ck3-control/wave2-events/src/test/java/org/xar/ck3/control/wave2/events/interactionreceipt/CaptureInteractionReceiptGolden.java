package org.xar.ck3.control.wave2.events.interactionreceipt;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Once-only actual shared Driver/Service/after-capture oracle with a synthetic native seam. */
public final class CaptureInteractionReceiptGolden {
    private CaptureInteractionReceiptGolden() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 4) { throw new IllegalArgumentException("repo-root python-exe new-scratch-root new-output required"); }
        Path repo = Path.of(args[0]).toAbsolutePath().normalize(); Path python = Path.of(args[1]).toAbsolutePath().normalize();
        Path scratch = Path.of(args[2]).toAbsolutePath().normalize(); Path output = Path.of(args[3]).toAbsolutePath().normalize();
        Path temporary = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize();
        if (!scratch.startsWith(temporary) || Files.exists(scratch) || !output.startsWith(temporary.getParent().resolve("logs")) || Files.exists(output)) {
            throw new IllegalArgumentException("fresh package paths required");
        }
        Files.createDirectories(scratch); ProcessBuilder builder = new ProcessBuilder(python.toString(), "-c", SCRIPT, repo.toString(), scratch.toString(), output.toString());
        builder.directory(repo.toFile()); builder.inheritIO(); builder.environment().put("TEMP", temporary.toString()); builder.environment().put("TMP", temporary.toString());
        Process process = builder.start();
        if (!process.waitFor(90, TimeUnit.SECONDS)) { process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); throw new IllegalStateException("receipt capture timeout"); }
        if (process.exitValue() != 0 || !Files.isRegularFile(output) || Files.size(output) > 65_536) { throw new IllegalStateException("original receipt capture failed"); }
    }
    private static final String SCRIPT = """
            from pathlib import Path
            import sys,json,copy,hashlib,datetime
            root,scratch,out=map(Path,sys.argv[1:]);sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'tools')]
            from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
            from xar_autoplayer.bridge.service import GameplayBridgeService
            from xar_autoplayer import pending_interaction_fallback as original
            from ck3_live_run_id import current_machine_id
            canonical=lambda value:json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
            sha=lambda data:hashlib.sha256(data).hexdigest()
            pending_id=301989889;calls=[]
            def native(step,identity=pending_id):
                notification=step.startswith('acknowledge-')
                before={'snapshot_id':'synthetic:7','revision':3,'paused':True,'pending_character_interaction':{'instance_id':identity,'sender_character_id':102,'auto_accept_notification':notification}}
                after={'snapshot_id':'synthetic:8','revision':4,'paused':True,'pending_character_interaction':None}
                driver=NativeHeadlessGameplayDriver.__new__(NativeHeadlessGameplayDriver);driver.command_timeout_seconds=1.0
                frames=[copy.deepcopy(before),copy.deepcopy(after)];driver.take_snapshot=lambda:frames.pop(0)
                driver._execute_primitive_step=lambda chosen,**kwargs:{'accepted':True,'step':chosen,'status':'ok','request_id':'synthetic-request','native_request_id':'synthetic-native-request'}
                driver._wait_for_snapshot=lambda snapshot,predicate,**kwargs:snapshot
                result=driver._execute_pending_character_interaction_reply(step,expected_revision=3);calls.append('native_driver_actual_method');return result
            steps=[action+'-pending-character-interaction' for action in ('accept','reject','acknowledge')]
            service=GameplayBridgeService.__new__(GameplayBridgeService)
            service.capabilities=lambda:{'action_steps':steps,'bridge_capabilities':[]}
            service.execute_step=lambda step,**kwargs:native(step)
            service.snapshot=lambda:{'revision':3,'pending_character_interaction':{'instance_id':pending_id,'sender_character_id':102,'auto_accept_notification':False}}
            bases={}
            for action in ('accept','reject','acknowledge'):bases['execute_'+action]=('execute_step',action,native(action+'-pending-character-interaction'))
            for accept in (True,False):
                action='accept' if accept else 'reject';result=service.reply_pending_character_interaction(accept=accept,interaction_instance_id=pending_id,expected_revision=3)
                calls.append('service_actual_reply_method');bases['service_'+action]=('reply_api',action,result)
            service.snapshot=lambda:{'revision':3,'pending_character_interaction':{'instance_id':pending_id,'sender_character_id':102,'auto_accept_notification':True}}
            bases['service_acknowledge']=('acknowledge_api','acknowledge',service.acknowledge_pending_character_interaction(interaction_instance_id=pending_id,expected_revision=3));calls.append('service_actual_acknowledge_method')
            specs=[(name,*data,None) for name,data in bases.items()]
            for name in ('ack_only','same_pending','wrong_original','wrong_status','unpaused','missing_remaining','remaining_other','accepted_false','accepted_missing','accepted_null','missing_step','wrong_step','error_with_response'):
                result=copy.deepcopy(bases['execute_reject'][2]);error=None
                if name=='ack_only':result={'accepted':True}
                elif name=='same_pending':result['remaining_pending_character_interaction']={'instance_id':pending_id}
                elif name=='wrong_original':result['interaction_result']['instance_id']=pending_id+1
                elif name=='wrong_status':result['interaction_result']['status']='accepted'
                elif name=='unpaused':result['paused']=False
                elif name=='missing_remaining':del result['remaining_pending_character_interaction']
                elif name=='remaining_other':result['remaining_pending_character_interaction']={'instance_id':pending_id+1}
                elif name=='accepted_false':result['accepted']=False
                elif name=='accepted_missing':del result['accepted']
                elif name=='accepted_null':result['accepted']=None
                elif name=='missing_step':del result['step']
                elif name=='wrong_step':result['step']='accept-pending-character-interaction'
                elif name=='error_with_response':error=RuntimeError('synthetic response followed by independent verification failure')
                specs.append((name,'execute_step','reject',result,error))
            specs.append(('error_only','execute_step','reject',None,RuntimeError('synthetic unknown outcome; never replay')))
            for name in ('reply_wrong_intent','reply_wrong_wrapper','ack_wrong_wrapper_flag'):
                origin,action,result=copy.deepcopy(bases['service_acknowledge' if name.startswith('ack_') else 'service_reject'])
                if name=='reply_wrong_intent':result['accepted']=True
                elif name=='reply_wrong_wrapper':result['interaction_instance_id']=pending_id+1
                else:result['acknowledged']=False
                specs.append((name,origin,action,result,None))
            cases=[]
            for index,(name,origin,action,result,error) in enumerate(specs):
                ticket={'incident_id':str(index)+'-'+name,'directory':str(scratch),'before':{'path':str(scratch/'synthetic-before-not-runtime-qualification.json'),'sha256':'0'*64},'pending_interaction_id':pending_id,'action':action}
                evidence=original.capture_pending_interaction_after_v1(ticket,outcome={'result':result} if result is not None else None,error=error)
                raw=canonical(result)
                cases.append({'name':name,'origin':origin,'action':action,'pending_interaction_id':pending_id,'response_utf8':raw.decode('utf-8'),'response_sha256':sha(raw),'legacy_command_acknowledged':evidence['command_acknowledged'],'legacy_original_pending_advanced_verified':evidence['original_pending_advanced_verified'],'error':None if error is None else {'type':type(error).__name__,'message':str(error)}})
            files=['ck3_autonomous_player/src/xar_autoplayer/pending_interaction_fallback.py','ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py']
            data={'schema':'xar.interaction-receipt-original-producer-golden/v1','machine_id':current_machine_id(),'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'notice':'Actual shared Native Driver method and Service reply/ACK wrappers; synthetic primitive/snapshot seam, no actual Native call. Every case executes original after-capture producer with a synthetic ticket; source response mutations are explicitly named. No before-ticket, Game or settlement qualification.',
                'source_refs':[{'path':name,'sha256':sha((root/name).read_bytes())} for name in files],'actual_method_calls':calls,'cases':cases}
            raw=canonical(data);assert len(raw)<=65536;assert sum(p.stat().st_size for p in scratch.rglob('*') if p.is_file())<=262144
            with out.open('xb') as stream:stream.write(raw)
            print(json.dumps({'machine_id':data['machine_id'],'output':str(out),'bytes':len(raw),'sha256':sha(raw),'cases':len(cases),'Game_MCP_ledger_calls':0}))
            """;
}
