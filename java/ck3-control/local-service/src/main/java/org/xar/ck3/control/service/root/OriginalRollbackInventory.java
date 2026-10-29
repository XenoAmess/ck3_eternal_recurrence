package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.service.root.OriginalRollbackSavedFrontier.*;

/** Exact on-disk original P37 inventory, successful tool postchecks and a proven pre-dispatch local refusal. */
public final class OriginalRollbackInventory {
    private static final String MESSAGE="retained terminal evidence forbids new RPC: ROOT-FIRST-QUEUE-EXCEPTION-P37C23.json";
    private OriginalRollbackInventory(){ }
    private record Refusal(long sequence,ExactRef request,ExactRef response,ObjectNode previousRequest,Path previousResponse) { }
    public static void verify(OriginalRollbackFiles.Scope files,OriginalRollbackProof proof,Saved saved,OriginalRollbackTail.Tail tail)throws IOException {
        ObjectNode inv=load(files,proof.sources().inventory(),1024*1024);
        exact(inv,Set.of("schema","machine_id","observed_at_utc","runtime_root","entries","other_request_entries","unknown_native_entries","new_save_entries","next_ref","plan_entries"));
        eq(inv,"schema","xar.current-saved-completed-unsaved-tail-inventory/v1");scope(inv,proof);
        for(String field:List.of("other_request_entries","unknown_native_entries","new_save_entries"))require(arr(inv.get(field),0).isEmpty(),"original inventory contains an omitted, UNKNOWN or newer SAVE entry");
        require(ref(inv,"next_ref").equals(proof.sources().actualNext()),"inventory NEXT source changed");
        yes(load(files,proof.sources().actualNext(),16384).get("failed_request_registered_without_readmission"));
        Refusal stop=refusal(files,proof,tail.nextSequence());
        files.requireAbsent(proof.runtimeRoot().resolve("p37-queue").resolve(String.format(java.util.Locale.ROOT,"INFLIGHT-%04d.json",stop.sequence())));
        files.requireAbsent(proof.runtimeRoot().resolve("p37-queue").resolve(String.format(java.util.Locale.ROOT,"%04d-before-action.json",stop.sequence())));
        List<JsonNode> entries=arr(inv.get("entries"),4096);require(!entries.isEmpty(),"finite nonempty original request inventory required");
        var full=new ArrayList<ExactRef>();var requests=new HashSet<Path>();var responses=new HashSet<Path>();var autos=new HashSet<Long>();
        long seen=saved.next()-1,turns=0;int refused=0;boolean previousSeen=false;
        for(JsonNode item:entries) {
            ObjectNode row=obj(item);exact(row,Set.of("sequence","request_ref","response_ref","after_ref"));long sequence=n(row,"sequence",1);
            require(sequence==Math.addExact(seen,1),"omitted, reordered or duplicate original request slot");seen=sequence;
            ExactRef request=ref(row,"request_ref"),response=ref(row,"response_ref");
            requirePath(request,proof.runtimeRoot().resolve("p37-requests").resolve(slot(sequence,"-1-result.json")));
            requirePath(response,proof.runtimeRoot().resolve("p37-responses").resolve(slot(sequence,"-1-result.json")));
            require(requests.add(Path.of(request.path()))&&responses.add(Path.of(response.path())),"duplicated physical original request source");
            ObjectNode req=load(files,request,16384),out=load(files,response,2*1024*1024);
            require(n(req,"sequence",1)==sequence&&same(out.get("request"),req),"original request and response source binding differs");
            if(sequence==stop.sequence()) {
                require(request.equals(stop.request())&&response.equals(stop.response()),"local refusal differs from unique original request slot");nil(row,"after_ref");refused++;continue;
            }
            require(sequence<stop.sequence()&&(!req.has("tool")||req.get("tool").isNull()||!"ck3_save_checkpoint".equals(text(req,"tool"))),"new SAVE or request exists after the local refusal");
            if(sequence==stop.sequence()-1) {
                require(same(req,stop.previousRequest())&&Path.of(response.path()).equals(stop.previousResponse()),"local refusal changed its actual already completed MET source");previousSeen=true;
            }
            if(req.hasNonNull("tool")&&"ck3_auto_turn".equals(text(req,"tool")))autos.add(sequence);
            if(req.hasNonNull("command")&&"full_loop".equals(text(req,"command"))) {
                require(!req.hasNonNull("tool")&&!out.has("client_error"),"original FULL completion must have its actual control contract");nil(row,"after_ref");
                ObjectNode body=successful(out,null);eq(body,"status","bounded_loop_finished");turns=Math.addExact(turns,n(body,"actual_turns",1));full.add(response);
            }else {
                String tool=text(req,"tool");successful(out,tool);ExactRef after=ref(row,"after_ref");
                requirePath(after,proof.runtimeRoot().resolve("p37-queue").resolve(slot(sequence,"-after-result.json")));
                ObjectNode post=load(files,after,16384);eq(post,"tool",tool);
                require(Path.of(text(post,"request")).equals(Path.of(request.path()))&&Path.of(text(post,"response")).equals(Path.of(response.path())),"actual successful postcheck belongs to a different request or result");
            }
        }
        require(seen==stop.sequence()&&refused==1&&previousSeen&&full.equals(proof.sources().successfulFullResponses()),"inventory omits a FULL or the unique final local refusal");
        var planSequences=new HashSet<Long>();ObjectNode review=load(files,proof.sources().currentDriverReview(),262144);
        long gamePid=n(obj(obj(review.get("Driver")).get("recorded_identity")),"bridge_pid",1);
        for(JsonNode item:arr(inv.get("plan_entries"),4096)) {
            ObjectNode row=obj(item);exact(row,Set.of("sequence","ref"));long sequence=n(row,"sequence",1);ExactRef reference=ref(row,"ref");
            require(autos.contains(sequence)&&planSequences.add(sequence),"before-submit decision plan must bind one actual AUTO slot");
            requirePath(reference,proof.runtimeRoot().resolve("p37-responses").resolve(slot(sequence,"-0-plan.json")));
            ObjectNode plan=load(files,reference,2*1024*1024),request=obj(plan.get("request"));plannedBody(plan);
            require(n(plan,"game_pid",1)==gamePid,"actual callback Game PID differs");
            eq(request,"tool","root_before_auto_turn_submit");eq(request,"callback_protocol","xar.ck3.decision-subdecision/v1");
            require(n(request,"parent_sequence",1)==sequence&&n(request,"callback_index",1)>=1,"actual decision callback parent/index differs");
            org.xar.ck3.control.continuity.writer.WriterContracts.requireDigest(text(request,"actual_observation_sha256"));
            require(responses.add(Path.of(reference.path())),"duplicate actual before-submit plan path");
        }
        require(new HashSet<>(files.jsonFiles(proof.runtimeRoot().resolve("p37-requests"),4096)).equals(requests)
                &&new HashSet<>(files.jsonFiles(proof.runtimeRoot().resolve("p37-responses"),4096)).equals(responses),"physical request/response inventory has undeclared or omitted files");
        require(tail.cycles()==Math.addExact(saved.cycles(),turns),"all completed tail cycles must be explained by actual inventoried FULLs");
    }
    /** The actual before-submit producer has its own result envelope and does not emit SDK result_type. */
    static ObjectNode plannedBody(ObjectNode plan) {
        eq(plan,"source","actual GameplayBridgeService.before_submit callback");
        ObjectNode result=obj(plan.get("result"));no(result.get("is_error"));ObjectNode body=obj(result.get("structured_content"));
        eq(body,"status","planned");require(!obj(body.get("plan")).isEmpty(),"actual finite before-submit decision plan required");return body;
    }
    private static Refusal refusal(OriginalRollbackFiles.Scope files,OriginalRollbackProof proof,long actualNext)throws IOException {
        ObjectNode stop=load(files,proof.sources().interruption(),65536);
        exact(stop,Set.of("schema","machine_id","observed_at_utc","runtime_root","sequence","request_ref","response_ref","inflight_ref","before_ref","first_exception_ref","halt_ref","rejection_stage","sdk_rpc_started","native_submission_started"));
        eq(stop,"schema","xar.current-saved-local-recording-paused-refusal/v1");scope(stop,proof);long failed=n(stop,"sequence",1);
        require(Math.addExact(failed,1)==actualNext,"local refusal must preserve the actual next unused sequence");
        eq(stop,"rejection_stage","terminal_evidence_before_request_dispatch");no(stop.get("sdk_rpc_started"));no(stop.get("native_submission_started"));nil(stop,"inflight_ref");nil(stop,"before_ref");
        ExactRef request=ref(stop,"request_ref"),response=ref(stop,"response_ref"),firstRef=ref(stop,"first_exception_ref"),haltRef=ref(stop,"halt_ref");
        requirePath(firstRef,proof.runtimeRoot().resolve("ROOT-FIRST-QUEUE-EXCEPTION-P37C23.json"));
        requirePath(haltRef,proof.runtimeRoot().resolve("p37-queue").resolve("ROOT-REQUEST-HALTED-"+failed+".json"));
        ObjectNode req=load(files,request,16384),out=load(files,response,1024*1024),first=load(files,firstRef,65536),halt=load(files,haltRef,65536);
        require(n(req,"sequence",1)==failed&&same(out.get("request"),req)&&!out.has("result"),"local refusal must have no invented successful SDK result");
        eq(req,"tool","ck3_take_semantic_snapshot_private_v1");require(obj(req.get("arguments")).isEmpty(),"actual refused SEM arguments differ");
        eq(out,"client_error",MESSAGE);no(out.get("replay_allowed"));
        ObjectNode guard=obj(first.get("guard_observation")),flags=obj(guard.get("terminal_flags"));
        eq(first,"stage","guard");no(first.get("replay_allowed"));eq(obj(first.get("exception_tree")),"type","RecordingPaused");
        eq(guard,"checking","recording_terminal_flags");no(guard.get("reserve_reply"));eq(guard,"error_type","RecordingPaused");
        require(n(guard,"next_sequence",1)==failed,"recording guard sequence changed");exact(flags,Set.of("failed.json","completed.json","closed-file-probe.json"));
        boolean any=false;for(JsonNode flag:flags){any|=bool(flag);}require(any,"actual recording terminal flag required");
        ObjectNode previous=obj(halt.get("original_request"));Path previousResponse=Path.of(text(halt,"original_response"));
        eq(halt,"message",MESSAGE);eq(halt,"error_type","ValueError");no(halt.get("replay_allowed"));
        require(n(halt,"next_sequence",1)==actualNext&&Path.of(text(halt,"first_exception_receipt")).equals(Path.of(firstRef.path()))
                &&n(previous,"sequence",1)==failed-1&&obj(previous.get("arguments")).isEmpty(),"halt must retain the exact completed previous MET source");
        eq(previous,"tool","root_current_runtime_metrics");
        require(previousResponse.equals(proof.runtimeRoot().resolve("p37-responses").resolve(slot(failed-1,"-1-result.json")))
                &&Path.of(text(out,"original_response")).equals(previousResponse),"local refusal changed original completed MET response");
        return new Refusal(failed,request,response,previous,previousResponse);
    }
    static void scope(ObjectNode row,OriginalRollbackProof proof) {
        eq(row,"machine_id",proof.machineId());utc(row,"observed_at_utc");require(Path.of(text(row,"runtime_root")).equals(proof.runtimeRoot()),"original runtime scope differs");
    }
    private static String slot(long sequence,String suffix){return String.format(java.util.Locale.ROOT,"%04d",sequence)+suffix;}
    private static void requirePath(ExactRef reference,Path expected){require(Path.of(reference.path()).equals(expected),"original source is not its canonical request slot path");}
}
