package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** Original .3 stock controller flow. Selection and ACK never establish control. */
public final class PlayerControlCodec {
    private PlayerControlCodec() { }
    public static RawJson request(Context c,ControlRequest r,String actualRequestId) {
        need(c.build()==Build.CROZIER3,"stock player-control producer is qualified only for exact .3");
        need(actualRequestId!=null && !actualRequestId.isEmpty(),"actual coordinator request ID required for native nonce");
        ObjectNode n=common(c).put("action",r.action().wire())
                .put("expected_process_creation_filetime_100ns",r.source().creationFiletime().integer())
                .put("source_inventory_sha256",r.source().inventorySha256().value()).put("request_nonce",actualRequestId);
        if(r.action()!=ControlAction.QUERY_CONTEXT) {
            n.put("expected_control_context_signature",r.contextSignature().orElseThrow().value());
            if(r.candidate().isPresent()) n.put("candidate_character_id",r.candidate().orElseThrow().value()); else n.putNull("candidate_character_id");
        }
        return encode(n);
    }
    public static ControlObservation decode(RawJson original,Context c,ControlRequest r) {
        need(c.build()==Build.CROZIER3,"stock controller observation source only qualifies exact .3");
        JsonNode n=parse(original);
        closed(n,"schema","step","action","status","native_revision","connection_generation","game_pid","played_character_id","process_creation_filetime_100ns","pump_epoch",
            "exact_build_verified","owner_verified","process_identity_verified","source_abi_pins_verified","stock_files_verified","loaded_source_binding_verified","frame_verified",
            "context_signature_verified","control_context_signature","phase","flow_id","flow_source_character_id","flow_target_character_id","flow_local_player_id","flow_complete",
            "local_player_id","controlled_character_id","selected_character_id","controlled_character_is_ai","ironman","multiple_players","controller_records_complete","controller_records",
            "candidates_complete","candidates","targets","dispatches","stage_consumed","control_postcondition_verified","reason");
        eq(n,"schema","ck3-player-control-v1"); eq(n,"step","player-control-v1"); eq(n,"action",r.action().wire());
        eq(n,"native_revision",c.revision()); eq(n,"connection_generation",c.connectionGeneration()); eq(n,"game_pid",BigInteger.valueOf(c.before().game().pid())); eq(n,"played_character_id",c.actor());
        eq(n,"process_creation_filetime_100ns",r.source().creationFiletime().integer());
        ControlStatus status=enumeration(n,"status",ControlStatus.class); ControlPhase phase=enumeration(n,"phase",ControlPhase.class);
        ControlProofs proofs=new ControlProofs(bool(n,"exact_build_verified"),bool(n,"owner_verified"),bool(n,"process_identity_verified"),bool(n,"source_abi_pins_verified"),bool(n,"stock_files_verified"),bool(n,"loaded_source_binding_verified"),bool(n,"frame_verified"));
        BigInteger epoch=u64(n,"pump_epoch"); String signature=text(n,"control_context_signature"), flow=nullableText(n,"flow_id");
        if(flow!=null) new Signature(flow);
        if(status!=ControlStatus.UNAVAILABLE) { new Signature(signature); need(proofs.complete() && epoch.signum()>0 && flow!=null,"available control context lacks real source/owner/process/frame proof"); }
        else if(!signature.isEmpty()) new Signature(signature);
        List<Controller> controllers=list(n,"controller_records",16384,row->{
            closed(row,"player_id","character_id","is_current_controller","is_ai");
            return new Controller(nullablePlayer(row,"player_id"),nullableId(row,"character_id"),nullableBool(row,"is_current_controller"),nullableBool(row,"is_ai"));
        });
        List<String> controllerIds=controllers.stream().filter(x->x.character()!=null).map(x->x.player()+":"+x.character()).toList(); unique(controllerIds,16384);
        List<ControlCandidate> candidates=list(n,"candidates",16384,row->{
            closed(row,"character_id","playable_id","is_ruler","can_control","selection_visible","selection_enabled","source_verified");
            return new ControlCandidate(nullableId(row,"character_id"),nullableNumber(row,"playable_id",BigInteger.ONE,U64),nullableBool(row,"is_ruler"),nullableBool(row,"can_control"),
                    nullableBool(row,"selection_visible"),nullableBool(row,"selection_enabled"),nullableBool(row,"source_verified"));
        }); unique(candidates.stream().filter(x->x.character()!=null).map(ControlCandidate::character).toList(),16384);
        List<ControlTarget> targets=list(n,"targets",4,row->{
            closed(row,"read_complete","root_exists","root_visible","target_exists","target_visible","target_enabled","unique_target","dispatch_admitted","target_vtable_rva");
            return new ControlTarget(bool(row,"read_complete"),bool(row,"root_exists"),bool(row,"root_visible"),bool(row,"target_exists"),bool(row,"target_visible"),bool(row,"target_enabled"),bool(row,"unique_target"),bool(row,"dispatch_admitted"),u64(row,"target_vtable_rva"));
        });
        List<ControlDispatch> dispatches=list(n,"dispatches",4,row->{
            closed(row,"claim_latched","dispatch_invoked","native_handled","post_read_complete","postcondition_observed");
            return new ControlDispatch(bool(row,"claim_latched"),bool(row,"dispatch_invoked"),bool(row,"native_handled"),bool(row,"post_read_complete"),bool(row,"postcondition_observed"));
        });
        List<Boolean> consumed=list(n,"stage_consumed",4,row->{ need(row.isBoolean(),"four actual consumed boolean stages required"); return row.booleanValue(); });
        need(targets.size()==4 && dispatches.size()==4 && consumed.size()==4,"exact four native controller stages required");
        boolean signatureVerified=bool(n,"context_signature_verified");
        for(int i=0;i<4;i++) {
            ControlDispatch d=dispatches.get(i);
            if(r.action()==ControlAction.QUERY_CONTEXT || i!=r.action().ordinal()-1) need(!d.claimLatched() && !d.invoked(),"one typed control request consumed/dispatched another stage");
            if(r.action()!=ControlAction.QUERY_CONTEXT && d.claimLatched()) need(consumed.get(i),"claimed native stage became unconsumed");
        }
        if(r.action()!=ControlAction.QUERY_CONTEXT && status!=ControlStatus.UNAVAILABLE) need(signatureVerified,"native mutation lacks latest backend signature proof");
        ControlObservation out=new ControlObservation(r.action(),status,phase,proofs,epoch,signature,flow,nullableId(n,"flow_source_character_id"),nullableId(n,"flow_target_character_id"),nullablePlayer(n,"flow_local_player_id"),
            bool(n,"flow_complete"),nullablePlayer(n,"local_player_id"),nullableId(n,"controlled_character_id"),nullableId(n,"selected_character_id"),nullableBool(n,"controlled_character_is_ai"),
            nullableBool(n,"ironman"),nullableBool(n,"multiple_players"),bool(n,"controller_records_complete"),controllers,bool(n,"candidates_complete"),candidates,targets,dispatches,consumed,
            signatureVerified,bool(n,"control_postcondition_verified"),text(n,"reason"));
        need(out.controlVerified()==actualControlObserved(out),"control summary differs from real manager and AI observations");
        need(status!=ControlStatus.CONTROL_OBSERVED || out.controlVerified(),"selected character is not actual control");
        return out;
    }
    public static boolean actualControlObserved(ControlObservation n) {
        if(!n.proofs().complete() || n.pumpEpoch().signum()<=0 || n.flowId()==null || !n.flowId().matches("[0-9a-f]{64}") || !n.signature().matches("[0-9a-f]{64}")
                || !n.controllersComplete() || !n.flowComplete() || n.phase()!=ControlPhase.CONTROL_CONFIRMED || n.stageConsumed().size()!=4 || !n.stageConsumed().get(3)
                || !Boolean.FALSE.equals(n.controlledAi()) || n.flowLocalPlayer()==null || !Objects.equals(n.localPlayer(),n.flowLocalPlayer())
                || n.controlledCharacter()==null || !Objects.equals(n.controlledCharacter(),n.targetCharacter()) || Objects.equals(n.sourceCharacter(),n.targetCharacter())) return false;
        for(Controller row:n.controllers()) if(row.player()==null || row.character()==null || row.current()==null) return false;
        List<Controller> current=n.controllers().stream().filter(row->Boolean.TRUE.equals(row.current()) && Objects.equals(row.player(),n.localPlayer())).toList();
        return current.size()==1 && Objects.equals(current.get(0).character(),n.controlledCharacter()) && Boolean.FALSE.equals(current.get(0).ai())
                && n.controllers().stream().noneMatch(row->Boolean.TRUE.equals(row.current()) && Objects.equals(row.player(),n.localPlayer()) && Objects.equals(row.character(),n.sourceCharacter()));
    }
    /** Latest eligible context only. Durable consumed stages survive query/revision/reconnect. */
    public static boolean stageReady(ControlObservation n,ControlAction action,CharacterId candidate) {
        if(n.status()!=ControlStatus.CONTEXT_OBSERVED || !n.proofs().complete() || n.pumpEpoch().signum()<=0 || n.flowId()==null || !n.controllersComplete()
                || !Boolean.FALSE.equals(n.controlledAi()) || !Boolean.FALSE.equals(n.ironman()) || !Boolean.FALSE.equals(n.multiplePlayers())
                || n.sourceCharacter()==null || !Objects.equals(n.sourceCharacter(),n.controlledCharacter()) || !Objects.equals(n.flowLocalPlayer(),n.localPlayer())) return false;
        int index=action.ordinal()-1; if(index<0 || !n.targets().get(index).dispatchAdmitted()) return false;
        List<Controller> current=n.controllers().stream().filter(row->Boolean.TRUE.equals(row.current()) && Objects.equals(row.player(),n.localPlayer())).toList();
        if(current.size()!=1 || !Objects.equals(current.get(0).character(),n.sourceCharacter()) || !Boolean.FALSE.equals(current.get(0).ai())) return false;
        if(action==ControlAction.OPEN_PAUSE_MENU) return n.phase()==ControlPhase.MAP && n.stageConsumed().stream().noneMatch(Boolean::booleanValue);
        if(action==ControlAction.OPEN_SWITCH) return n.phase()==ControlPhase.PAUSE_MENU && n.stageConsumed().subList(1,4).stream().noneMatch(Boolean::booleanValue);
        if(n.phase()!=ControlPhase.SWITCH_CHOOSER || !n.stageConsumed().get(1) || !n.candidatesComplete() || candidate==null) return false;
        List<ControlCandidate> selected=n.candidates().stream().filter(row->Objects.equals(row.character(),candidate.value())).toList();
        if(selected.size()!=1) return false; ControlCandidate row=selected.get(0);
        if(!Boolean.TRUE.equals(row.canControl()) || !Boolean.TRUE.equals(row.ruler()) || !Boolean.TRUE.equals(row.sourceVerified())
                || row.playableId()==null || !Boolean.TRUE.equals(row.visible()) || !Boolean.TRUE.equals(row.enabled()) || Objects.equals(n.sourceCharacter(),candidate.value())) return false;
        if(action==ControlAction.CHOOSE_CHARACTER) return !n.stageConsumed().get(2) && !n.stageConsumed().get(3);
        return n.stageConsumed().get(2) && !n.stageConsumed().get(3) && Objects.equals(n.selectedCharacter(),candidate.value()) && Objects.equals(n.targetCharacter(),candidate.value());
    }
    /** Must receive an independent actual snapshot projection, never the command_result token. */
    public static boolean verifyIndependentControl(Context before,Context after,ControlObservation original) {
        return actualControlObserved(original) && before.before().machineId().equals(after.before().machineId())
            && before.before().game().equals(after.before().game()) && before.sessionId().equals(after.sessionId())
            && before.connectionGeneration().equals(after.connectionGeneration()) && before.build()==after.build()
            && before.controls().episodeRunId().equals(after.controls().episodeRunId()) && before.date().equals(after.date())
            && after.controls().paused() && after.controls().mapReady() && after.controls().alive()
            && after.actor().equals(BigInteger.valueOf(original.controlledCharacter())) && after.revision().compareTo(before.revision())>=0;
    }
}
