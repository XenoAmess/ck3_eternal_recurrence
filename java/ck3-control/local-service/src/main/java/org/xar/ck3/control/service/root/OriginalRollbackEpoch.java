package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.Native;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.platform.win32.WinBase.FILETIME;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.service.root.OriginalRollbackSavedFrontier.*;

/** Actual original abnormal Game/SDK exits, independent task closure, screen lease release and full Driver review. */
public final class OriginalRollbackEpoch {
    private OriginalRollbackEpoch(){ }
    public record Closed(ExactRef driver,FileStatIdentity driverIdentity,ExactRef save,FileStatIdentity saveIdentity,
            long historyRows,String pipeName,long gamePid,BigInteger gameBirth,ObjectNode review) {
        public Closed { review=review.deepCopy(); }
        @Override public ObjectNode review(){return review.deepCopy();}
    }
    private record Process(String role,long pid,BigInteger birth,long exitCode,String executable) { }
    public static Closed verify(OriginalRollbackFiles.Scope files,OriginalRollbackProof proof,Saved saved,OriginalRollbackTail.Tail tail)throws IOException {
        ObjectNode epoch=load(files,proof.sources().abnormalClosedEpoch(),65536);
        exact(epoch,Set.of("schema","machine_id","observed_at_utc","runtime_root","refs","tasks","sdk_normal"));
        eq(epoch,"schema","xar.current-saved-observed-abnormal-epoch/v1");OriginalRollbackInventory.scope(epoch,proof);no(epoch.get("sdk_normal"));
        ObjectNode refs=obj(epoch.get("refs"));exact(refs,Set.of("sdk_closed","supervisor_closed","game_exit","screen_release"));
        ObjectNode sdk=load(files,ref(refs,"sdk_closed"),16384),supervisor=load(files,ref(refs,"supervisor_closed"),16384),gameExit=load(files,ref(refs,"game_exit"),16384);
        eq(sdk,"machine_id",proof.machineId());eq(sdk,"status","ACTUAL_BOTH_SDK_EXITS_OBSERVED");no(sdk.get("normal"));
        List<Process> processes=sdkProcesses(sdk.get("processes"));
        eq(supervisor,"machine_id",proof.machineId());eq(gameExit,"machine_id",proof.machineId());
        ObjectNode owned=obj(supervisor.get("owned_cleanup")),phase=obj(supervisor.get("known_preload_phase"));
        ObjectNode before=obj(phase.get("before")),after=obj(phase.get("after"));
        long gamePid=n(gameExit,"pid",1),gameCode=n(gameExit,"exit_code",0);BigInteger birth=birth(gameExit.get("creation_filetime"));
        StrictJson.text(owned.get("ck3_creation_date"));yes(gameExit.get("kernel_signaled"));yes(gameExit.get("forced_owned_job_cleanup"));no(gameExit.get("normal_wm_close_qualified"));
        zero(owned,"job_active_processes_final");for(String field:List.of("tree_gone","cleanup_proven","ok"))yes(owned.get(field));
        require(arr(owned.get("contract_errors"),0).isEmpty()&&n(owned,"ck3_pid",1)==gamePid&&n(owned,"ck3_exit_code",0)==gameCode
                &&n(before,"pid",1)==gamePid&&n(after,"pid",1)==gamePid&&birth(before.get("creation_filetime")).equals(birth)
                &&birth(after.get("creation_filetime")).equals(birth),"actual owned Game cleanup, process birth and empty Job differ");
        ObjectNode again=obj(supervisor.get("sdk_actual_exit"));eq(again,"status","ACTUAL_BOTH_SDK_EXITS_OBSERVED");
        require(sdkProcesses(again.get("processes")).equals(processes),"supervisor and original SDK receipts identify different generations");
        for(Process process:processes)requireExited(process.pid(),process.birth(),process.exitCode());requireExited(gamePid,birth,gameCode);
        var roles=new HashSet<String>();var specs=new HashSet<String>();var closures=new HashSet<String>();var absent=new HashSet<String>();var nonces=new HashSet<String>();
        List<JsonNode> tasks=arr(epoch.get("tasks"),3);
        for(JsonNode item:tasks) {
            ObjectNode task=obj(item);exact(task,Set.of("role","spec","closed","unregistered"));String role=text(task,"role");
            require(Set.of("supervisor","display","feeder").contains(role)&&roles.add(role),"duplicate or unknown original Task role");
            ExactRef spec=ref(task,"spec"),closed=ref(task,"closed"),unregistered=ref(task,"unregistered");
            require(specs.add(spec.path())&&closures.add(closed.path())&&absent.add(unregistered.path())&&nonces.add(task(files,proof.machineId(),spec,closed,unregistered)),"Task evidence generations must be independent");
        }
        require(tasks.size()>=2&&roles.containsAll(Set.of("supervisor","display")),"actual supervisor and display Tasks must both have closed");
        screenRelease(load(files,ref(refs,"screen_release"),16384),proof.machineId(),supervisor);
        ObjectNode review=load(files,proof.sources().currentDriverReview(),262144);
        exact(review,Set.of("schema","machine_id","observed_at_utc","runtime_root","Driver","SAVE","raw_state_ref","raw_governance_ref","actual_next_ref","canonical_qualification_performed"));
        eq(review,"schema","xar.current-saved-unsaved-tail-driver-review/v1");OriginalRollbackInventory.scope(review,proof);no(review.get("canonical_qualification_performed"));
        require(ref(review,"raw_state_ref").equals(proof.sources().rawState())&&ref(review,"raw_governance_ref").equals(proof.sources().rawGovernance())
                &&ref(review,"actual_next_ref").equals(proof.sources().actualNext()),"closed Driver review changed original state sources");
        ObjectNode driver=obj(review.get("Driver")),save=obj(review.get("SAVE"));
        exact(driver,Set.of("ref","identity","format_version","command_history_count","last_checkpoint","recorded_identity","history_scope","history_truncated","history_rewritten"));exact(save,Set.of("ref","identity"));
        ExactRef driverRef=ref(driver,"ref"),saveRef=ref(save,"ref");FileStatIdentity driverId=FileStatIdentity.fromJson(driver.get("identity"),FileStatIdentity.SCHEMA),saveId=FileStatIdentity.fromJson(save.get("identity"),FileStatIdentity.SCHEMA);
        require(Path.of(driverRef.path()).equals(Path.of(saved.driver().path()))&&driverId.bytes().equals(BigInteger.valueOf(driverRef.bytes()))
                &&saveRef.equals(saved.save())&&saveId.equals(saved.saveIdentity())&&n(driver,"format_version",2)==2&&same(driver.get("last_checkpoint"),saved.rawCheckpoint()),"unaltered current Driver must retain the exact prior SAVE");
        eq(driver,"history_scope","complete_current_file");no(driver.get("history_truncated"));no(driver.get("history_rewritten"));
        long historyRows=n(driver,"command_history_count",1);require(historyRows>=saved.previousHistoryRows(),"current Driver lost previously observed history");
        ObjectNode recorded=obj(driver.get("recorded_identity"));String pipe=text(recorded,"pipe_name");
        require(n(recorded,"bridge_pid",1)==gamePid&&n(recorded,"episode_character_id",1)==tail.frame().actorCharacterId()
                &&text(recorded,"episode_run_id").equals(tail.frame().episodeRunId()),"closed Driver identity differs from actual unsaved frame and Game");
        ObjectNode binding=obj(recorded.get("session_binding_observation"));exact(binding,Set.of("present","value"));
        if(!bool(binding.get("present")))nil(binding,"value");else {
            ObjectNode value=obj(binding.get("value"));exact(value,Set.of("pipe_name","bridge_pid","episode_character_id","episode_run_id"));eq(value,"pipe_name",pipe);
            require(n(value,"bridge_pid",1)==gamePid&&n(value,"episode_character_id",1)==tail.frame().actorCharacterId()&&text(value,"episode_run_id").equals(tail.frame().episodeRunId()),"actual optional session binding differs");
        }
        return new Closed(driverRef,driverId,saveRef,saveId,historyRows,pipe,gamePid,birth,review);
    }
    /** Historical Python-only numeric FILETIME is decoded losslessly here; it is never emitted as a JavaScript number. */
    private static BigInteger birth(JsonNode value) {
        require(value!=null&&(value.isIntegralNumber()||value.isTextual()),"exact original FILETIME integer or canonical decimal string required");
        String decimal=value.isTextual()?value.textValue():value.bigIntegerValue().toString();
        require(decimal.matches("[1-9][0-9]*"),"canonical positive original FILETIME required");BigInteger result=new BigInteger(decimal);
        require(result.compareTo(StrictJson.UINT64_MAX)<=0,"original FILETIME exceeds uint64");return result;
    }
    private static List<Process> sdkProcesses(JsonNode rows) {
        var result=new ArrayList<Process>();var roles=new HashSet<String>();var generations=new HashSet<String>();
        for(JsonNode item:arr(rows,2)) {
            ObjectNode row=obj(item);String role=text(row,"role");require(Set.of("sdk_queue","sdk_application").contains(role)&&roles.add(role),"exact two original SDK roles required");
            long expected=role.equals("sdk_queue")?1:0;yes(row.get("kernel_exit_observed"));nil(row,"observation_error");zero(row,"wait_result");
            require(n(row,"exit_code",0)==expected,"actual abnormal SDK exit code differs");long pid=n(row,"pid",1);require(pid<=0xffff_ffffL,"uint32 SDK PID required");
            BigInteger originalBirth=birth(row.get("creation_filetime"));require(generations.add(pid+":"+originalBirth),"two distinct actual SDK generations required");
            result.add(new Process(role,pid,originalBirth,expected,text(row,"executable")));
        }
        require(result.size()==2,"both actual SDK processes must have closed");return result.stream().sorted(java.util.Comparator.comparing(Process::role)).toList();
    }
    private static String task(OriginalRollbackFiles.Scope files,String machine,ExactRef specRef,ExactRef closedRef,ExactRef unregisteredRef)throws IOException {
        ObjectNode spec=load(files,specRef,16384),closed=load(files,closedRef,16384);String nonce=text(spec,"nonce");
        eq(spec,"machine_id",machine);eq(closed,"machine_id",machine);eq(closed,"nonce",nonce);eq(closed,"spec_sha256",specRef.sha256());eq(spec,"task_name","XARG2ManagedOwner-"+nonce);
        zero(closed,"job_active_after_stage");no(closed.get("forced_remaining_cleanup"));
        require(n(closed,"bootstrap_exit_code",0)==n(closed,"child_exit_code",0),"Task bootstrap ACK differs from actual child exit");
        ObjectNode absence=load(files,unregisteredRef,16384),original;
        if(absence.has("stdout")) { zero(absence,"returncode");original=parseText(text(absence,"stdout")); }
        else {
            exact(absence,Set.of("machine_id","utc","task_name","operation","actual"));utc(absence,"utc");eq(absence,"operation","unregister");
            ObjectNode actual=obj(absence.get("actual"));zero(actual,"instances");String[] arguments=text(actual,"arguments").split("\\s+");int count=0;
            for(int i=0;i<arguments.length;i++)if(arguments[i].equals("--spec-sha")){require(i+1<arguments.length&&arguments[i+1].equals(specRef.sha256()),"Task action binds another SPEC");count++;}
            require(count==1,"actual Task action must bind the exact sole SPEC SHA");original=absence;
        }
        eq(original,"machine_id",machine);yes(obj(original.get("actual")).get("absent_after"));
        if(original.has("task_name"))eq(original,"task_name","XARG2ManagedOwner-"+nonce);if(original.has("operation"))eq(original,"operation","unregister");if(original.has("utc"))utc(original,"utc");
        return nonce;
    }
    private static void screenRelease(ObjectNode release,String machine,ObjectNode supervisor) {
        eq(release,"machine_id",machine);zero(release,"returncode");ObjectNode result=parseText(text(release,"stdout")),task=obj(result.get("task")),keeper=obj(supervisor.get("keeper"));
        yes(result.get("ok"));eq(task,"state","done");require(arr(task.get("resources"),0).isEmpty(),"screen lease remains held");
        eq(task,"task_id",text(keeper,"task_id"));yes(keeper.get("thread_exited"));nil(keeper,"failure");long last=n(keeper,"last_sequence",1);
        if(release.has("release_expected_sequence")||release.has("release_actual_sequence")) {
            long actual=n(release,"release_actual_sequence",1);require(n(release,"release_expected_sequence",1)==last&&actual>last,"screen lease CAS predecessor differs");
            ObjectNode event=obj(result.get("event"));for(ObjectNode row:List.of(result,task,event))eq(row,"schema","codex.task_bus.v1");
            eq(event,"task_id",text(keeper,"task_id"));eq(event,"state","done");eq(event,"kind","completed");require(arr(event.get("resources"),0).isEmpty(),"screen completion event retains a resource");
            require(n(task,"last_sequence",1)==actual&&n(event,"sequence",1)==actual,"screen lease CAS sequence differs");utc(event,"timestamp_utc");StrictJson.text(event.get("event_id"));
        }else require(n(task,"last_sequence",1)==Math.addExact(last,1),"legacy screen release must be the adjacent actual task sequence");
    }
    private static ObjectNode parseText(String json){return obj(StrictJson.parse(json.getBytes(StandardCharsets.UTF_8),16384));}
    private static void requireExited(long pid,BigInteger expectedBirth,long exitCode)throws IOException {
        if(!com.sun.jna.Platform.isWindows()||pid<=0||pid>0xffff_ffffL)throw new IOException("actual Windows original process generation required");
        HANDLE handle=Kernel32.INSTANCE.OpenProcess(0x00100000|0x1000,false,(int)pid);
        if(handle==null||WinBase.INVALID_HANDLE_VALUE.equals(handle)) {
            if(Native.getLastError()==87)return; // ERROR_INVALID_PARAMETER: this exact PID no longer exists.
            throw new IOException("original process exit unavailable Win32="+Native.getLastError());
        }
        try {
            FILETIME created=new FILETIME(),exited=new FILETIME(),kernel=new FILETIME(),user=new FILETIME();
            if(!Kernel32.INSTANCE.GetProcessTimes(handle,created,exited,kernel,user))throw new IOException("original process birth unavailable Win32="+Native.getLastError());
            BigInteger actual=new BigInteger(Long.toUnsignedString(created.toDWordLong().longValue()));
            if(!actual.equals(expectedBirth))return; // PID reuse never grants ownership of the replacement generation.
            if(Kernel32.INSTANCE.WaitForSingleObject(handle,0)!=0)throw new IOException("original completed-tail process is still running");
            var code=new com.sun.jna.ptr.IntByReference();if(!Kernel32.INSTANCE.GetExitCodeProcess(handle,code)||Integer.toUnsignedLong(code.getValue())!=exitCode)
                throw new IOException("actual original process exit differs from retained kernel result");
        }finally {Kernel32.INSTANCE.CloseHandle(handle);}
    }
}
