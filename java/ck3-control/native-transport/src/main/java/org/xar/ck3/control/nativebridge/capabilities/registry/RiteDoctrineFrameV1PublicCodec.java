package org.xar.ck3.control.nativebridge.capabilities.registry;

import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.NativeWire;

/** DATA codec only. An actual transport's private query, Core and draft supply effect authority. */
public final class RiteDoctrineFrameV1PublicCodec {
    private RiteDoctrineFrameV1PublicCodec(){}
    public record Lease(BigInteger providerGeneration,BigInteger querySequence){
        public Lease{GuiControlsFrameV2.positive64(providerGeneration);GuiControlsFrameV2.positive64(querySequence);}
    }
    public record Request(RiteDoctrineFrameV1.Action action,CoreFrame.Partial expectedCore,BigInteger deadlineUnixMs,long sourceRiteId,Optional<Lease> lease){
        public Request{
            Objects.requireNonNull(action);GuiControlsFrameV2.requireCore(expectedCore);GuiControlsFrameV2.positive64(deadlineUnixMs);
            RiteDraftCostsFrameV2.sourceRiteId(sourceRiteId);Objects.requireNonNull(lease);
            RegistryJson.require(expectedCore.prefix().playedCharacterId()!=0&&lease.isPresent()==(action!=RiteDoctrineFrameV1.Action.QUERY),"fixed current Rite action and original nonzero effect lease required");
        }
    }
    public static Request query(CoreFrame.Partial core,Instant until,long sourceRiteId){return new Request(RiteDoctrineFrameV1.Action.QUERY,core,BigInteger.valueOf(until.toEpochMilli()),sourceRiteId,Optional.empty());}
    public static Request action(Request original,RiteDoctrineFrameV1.Action action,Instant until,Lease lease){
        RegistryJson.require(original.action()==RiteDoctrineFrameV1.Action.QUERY&&action!=RiteDoctrineFrameV1.Action.QUERY&&!action.finalConfirmation(),"effect must derive its original query DATA");
        return new Request(action,original.expectedCore(),BigInteger.valueOf(until.toEpochMilli()),original.sourceRiteId(),Optional.of(lease));
    }
    /** DATA transform only; only a held receiver can issue a Stage1-bound private final token. */
    public static Request finalQuery(Request stageOne){return finalStage(stageOne,RiteDoctrineFrameV1.Action.QUERY_FINAL_CONFIRMATION);}
    public static Request acceptFinal(Request stageOne){return finalStage(stageOne,RiteDoctrineFrameV1.Action.ACCEPT_FINAL_CONFIRMATION);}
    private static Request finalStage(Request original,RiteDoctrineFrameV1.Action action){
        Objects.requireNonNull(original);RegistryJson.require(original.action()==RiteDoctrineFrameV1.Action.CONFIRM_EDIT&&original.lease().isPresent(),"final confirmation DATA must retain original Stage1 action/lease");
        return new Request(action,original.expectedCore(),original.deadlineUnixMs(),original.sourceRiteId(),original.lease());
    }
    public static RawJson additionalFields(Request request){
        var row=com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode();row.putObject("arguments");var claim=row.putObject("rite_doctrine");var build=GuiControlsFrameV2.BUILD;
        claim.put("schema",RiteDoctrineFrameV1.REQUEST_SCHEMA).put("game_version",build.version()).put("executable_sha256",build.executableSha256().toUpperCase(java.util.Locale.ROOT)).put("adapter_id",build.coreFrameAdapterId()).put("backend",GuiControlsFrameV2.BACKEND).put("action",request.action().wire()).put("deadline_unix_ms",request.deadlineUnixMs()).put("expected_source_rite_id",request.sourceRiteId());
        var p=request.expectedCore().prefix();claim.putObject("expected_core").put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused()).put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter()).put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());
        claim.put("provider_generation",request.lease().map(value->value.providerGeneration().toString()).orElse("0")).put("query_sequence",request.lease().map(value->value.querySequence().toString()).orElse("0"));
        var encoded=RegistryJson.encode(row);RegistryJson.require(fields(encoded).equals(request),"current Rite complete request roundtrip drift");return encoded;
    }
    public static Request decodeRequestPacket(byte[] packet)throws IOException{
        RegistryJson.require(packet!=null&&packet.length>=5&&packet.length<=16388,"bounded16KiB current Rite request required");var decoded=NativeWire.decodeExecuteRequest(packet);boolean quoted=false;
        for(int i=4;i<packet.length;i++){int value=Byte.toUnsignedInt(packet[i]);RegistryJson.require(value<127&&value!='\\',"current Rite request excludes escapes/non-ASCII");if(value=='"')quoted=!quoted;if(!quoted&&value=='-'&&i+1<packet.length&&packet[i+1]=='0'&&(i+2==packet.length||packet[i+2]<'0'||packet[i+2]>'9'))throw new IllegalArgumentException("canonical integer excludes negative zero");}
        var row=RegistryJson.object(new RawJson(Arrays.copyOfRange(packet,4,packet.length)));RegistryJson.keys(row,Set.of("type","protocol_version","request_id","step","expected_revision","arguments","rite_doctrine"));
        RegistryJson.require(decoded.requestId().matches("[A-Za-z0-9_.-]{1,96}")&&decoded.expectedRevision().equals(Optional.of(BigInteger.ZERO))&&decoded.expectedSnapshotRevision().isEmpty(),"exact current Rite outer request required");
        var request=fields(new RawJson(decoded.normalizedAdditionalFields().value()));
        RegistryJson.require(request.action().step().equals(decoded.step()),"fixed Rite action must use its explicit initial/final step");return request;
    }
    private static Request fields(RawJson raw){
        var row=RegistryJson.object(raw);RegistryJson.keys(row,Set.of("arguments","rite_doctrine"));RegistryJson.keys(RegistryJson.object(row.get("arguments")),Set.of());var claim=RegistryJson.object(row.get("rite_doctrine"));
        RegistryJson.keys(claim,Set.of("schema","game_version","executable_sha256","adapter_id","backend","action","deadline_unix_ms","expected_core","expected_source_rite_id","provider_generation","query_sequence"));var build=GuiControlsFrameV2.BUILD;
        RegistryJson.require(RiteDoctrineFrameV1.REQUEST_SCHEMA.equals(RegistryJson.text(claim.get("schema")))&&build.matches(RegistryJson.text(claim.get("game_version")),RegistryJson.text(claim.get("executable_sha256")))&&build.coreFrameAdapterId().equals(RegistryJson.text(claim.get("adapter_id")))&&GuiControlsFrameV2.BACKEND.equals(RegistryJson.text(claim.get("backend"))),"exact current Rite request tuple required");
        var p=RegistryJson.object(claim.get("expected_core"));RegistryJson.keys(p,Set.of("date_raw","speed","paused","local_player_id","map_ready","has_played_character","played_character_id","played_character_alive"));
        var core=new CoreFrame.Partial(build,new CoreFrame.Prefix(RegistryJson.int32(p.get("date_raw")),RegistryJson.int32(p.get("speed")),RegistryJson.bool(p.get("paused")),RegistryJson.int32(p.get("local_player_id")),RegistryJson.bool(p.get("map_ready")),RegistryJson.bool(p.get("has_played_character")),RegistryJson.int32(p.get("played_character_id")),RegistryJson.bool(p.get("played_character_alive"))));
        var action=RiteDoctrineFrameV1.Action.wire(RegistryJson.text(claim.get("action")));var generation=RiteDoctrineFrameV1.uint64(claim.get("provider_generation"));var sequence=RiteDoctrineFrameV1.uint64(claim.get("query_sequence"));
        if(action==RiteDoctrineFrameV1.Action.QUERY)RegistryJson.require(generation.signum()==0&&sequence.signum()==0,"query cannot import an effect lease");
        return new Request(action,core,RegistryJson.integer(claim.get("deadline_unix_ms"),BigInteger.ONE,RegistryJson.U64),RegistryJson.integer(claim.get("expected_source_rite_id"),BigInteger.ZERO,BigInteger.valueOf(0xffff_fffeL)).longValueExact(),action==RiteDoctrineFrameV1.Action.QUERY?Optional.empty():Optional.of(new Lease(generation,sequence)));
    }
    public static RiteDoctrineFrameV1 decodePacket(RawJson raw,String requestId)throws IOException{
        RegistryJson.require(raw.bytes().length<=RiteDoctrineFrameV1.MAXIMUM_BYTES+4096,"bounded current Rite ACK envelope required");var row=RegistryJson.object(raw);RegistryJson.keys(row,Set.of("type","protocol_version","request_id","ok","result"));
        RegistryJson.require("command_result".equals(RegistryJson.text(row.get("type")))&&RegistryJson.integer(row.get("protocol_version"),BigInteger.ONE,BigInteger.ONE).equals(BigInteger.ONE)&&requestId.equals(RegistryJson.text(row.get("request_id"))),"original current Rite envelope required");
        var frame=RiteDoctrineFrameV1.decode(RegistryJson.encode(row.get("result")));RegistryJson.require(RegistryJson.bool(row.get("ok"))==frame.nativeOk(),"current Rite outer/inner result coherence required");return frame;
    }
    public static RiteDoctrineFrameV1 decodeOutcome(NativeActionPort.DispatchOutcome actual)throws IOException{
        if(!(actual instanceof NativeActionPort.AckReceived ack))throw new IOException("actual Rite ACK unavailable; original retained, no replay");var outbound=ack.outbound().orElseThrow(()->new IOException("original Rite outbound absent"));var request=decodeRequestPacket(outbound.originalPacket());var outgoing=NativeWire.decodeExecuteRequest(outbound.originalPacket());
        if(!outbound.requestId().equals(ack.requestId())||!outgoing.requestId().equals(ack.requestId())||ack.originalPacket().length>RiteDoctrineFrameV1.MAXIMUM_BYTES+4100)throw new IOException("original Rite identity/size drift");
        var decoded=NativeWire.decode(ack.originalPacket());if(!(decoded instanceof NativeWire.CommandResult result)||result.nativeOk()!=ack.nativeOk()||!result.requestId().equals(ack.requestId())||!Arrays.equals(result.payload().value(),ack.originalFrame().bytes())||result.result().presence()!=NativeWire.Presence.VALUE||ack.originalResultToken().isEmpty()||!Arrays.equals(result.result().token().orElseThrow().value(),ack.originalResultToken().orElseThrow().bytes()))throw new IOException("original Rite packet/token drift");
        var custody=ack.custody().orElseThrow(()->new IOException("actual Rite custody absent"));custody.verify(ack);var frame=decodePacket(new RawJson(result.payload().value()),ack.requestId());
        if(frame.action()!=request.action()||frame.nativeOk()!=ack.nativeOk())throw new IOException("Rite result action/outer outcome differs from original");
        if(frame.facts().isPresent()&&(!frame.coreFrame().equals(request.expectedCore())||frame.facts().orElseThrow().sourceRiteId()!=request.sourceRiteId()||!frame.ownerWitness().orElseThrow().connectionGeneration().equals(custody.session().connectionGeneration())))throw new IOException("Rite result crossed original Core/source/session");
        if(request.lease().isPresent()&&(!request.lease().orElseThrow().providerGeneration().equals(frame.providerGeneration())||!request.lease().orElseThrow().querySequence().equals(frame.querySequence())))throw new IOException("Rite effect result crossed original private provider/query lease");return frame;
    }
    public static RawJson encode(RiteDoctrineFrameV1 frame){
        var row=com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode();var build=GuiControlsFrameV2.BUILD;
        row.put("schema",RiteDoctrineFrameV1.SCHEMA).put("game_version",build.version()).put("executable_sha256",build.executableSha256().toUpperCase(java.util.Locale.ROOT)).put("adapter_id",build.coreFrameAdapterId()).put("backend",GuiControlsFrameV2.BACKEND).put("step",frame.action().step()).put("action",frame.action().wire()).put("status",frame.status().wire());
        row.put("facts_available",frame.facts().isPresent()).put("effect_attempted",frame.effectAttempted()).put("native_returned",frame.nativeReturned()).put("native_handled",frame.nativeHandled()).put("post_selected_evaluated",frame.postSelectedEvaluated()).put("post_selected",frame.postSelected()).put("addresses_redacted",true);
        for(String key:Set.of("complete_snapshot","complete_gui_tree","physical_save_confirmed","rite_edit_confirmed"))row.put(key,false);
        row.put("group_key",RiteDoctrineFrameV1.GROUP_KEY).put("target_key",RiteDoctrineFrameV1.TARGET_KEY).put("provider_generation",frame.providerGeneration().toString()).put("query_sequence",frame.querySequence().toString()).put("claim_sequence",frame.claimSequence().toString());row.set("core_frame",RegistryJson.object(CoreFramePublicCodec.encode(frame.coreFrame())));
        if(frame.facts().isPresent()){
            var f=frame.facts().orElseThrow();row.putObject("facts").put("source_rite_id",f.sourceRiteId()).put("category_available",f.categoryAvailable()).put("target_available",f.targetAvailable()).put("should_display_evaluated",f.shouldDisplayEvaluated()).put("should_display",f.shouldDisplay()).put("can_pick_evaluated",f.canPickEvaluated()).put("can_pick",f.canPick()).put("knowledge_evaluated",f.knowledgeEvaluated()).put("known_doctrine",f.knownDoctrine()).put("pam_gate_available",f.pamGateAvailable()).put("pam_gate_true",f.pamGateAvailable()).put("selected_evaluated",f.selectedEvaluated()).put("selected",f.selected()).put("can_edit_evaluated",f.canEditEvaluated()).put("can_edit",f.canEdit()).put("piety_cost_raw",Long.toString(f.pietyCostRaw())).put("piety_missing_signed_raw",Long.toString(f.pietyMissingSignedRaw())).put("raw_scale",100000);
            var w=frame.ownerWitness().orElseThrow();row.putObject("owner_witness").put("connection_generation",w.connectionGeneration().toString()).put("ticket_sequence",w.ticketSequence().toString()).put("pump_epoch",w.pumpEpoch().toString()).put("thread_id",w.threadId());
        }else{row.putNull("facts");row.putNull("owner_witness");}
        if(frame.unavailableReason().isPresent())row.put("unavailable_reason",frame.unavailableReason().orElseThrow());else row.putNull("unavailable_reason");var encoded=RegistryJson.encode(row);RegistryJson.require(RiteDoctrineFrameV1.decode(encoded).equals(frame),"current Rite result roundtrip drift");return encoded;
    }
}
