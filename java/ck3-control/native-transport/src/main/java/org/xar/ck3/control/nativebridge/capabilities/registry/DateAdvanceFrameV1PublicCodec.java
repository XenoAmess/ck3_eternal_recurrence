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

/** Explicit current-date wire. Query changes its outer request identity, never the original action body/deadline. */
public final class DateAdvanceFrameV1PublicCodec {
    private DateAdvanceFrameV1PublicCodec(){}
    public record Request(DateAdvanceFrameV1.Step step,CoreFrame.Partial expectedCore,BigInteger deadlineUnixMs,String operationId){
        public Request{Objects.requireNonNull(step);Objects.requireNonNull(expectedCore);RegistryJson.require(expectedCore.build()==GuiControlsFrameV2.BUILD,"exact current date Core build required");DateAdvanceFrameV1.requireExpectedCore(expectedCore.prefix());GuiControlsFrameV2.positive64(deadlineUnixMs);DateAdvanceFrameV1.safeId(operationId);}
    }
    public static Request action(CoreFrame.Partial core,Instant originalDeadline,String operationId){return new Request(DateAdvanceFrameV1.Step.ADVANCE,core,BigInteger.valueOf(originalDeadline.toEpochMilli()),operationId);}
    /** No fresh deadline parameter exists. An expired exact original body is only a readonly status lookup. */
    public static Request query(Request original){return new Request(DateAdvanceFrameV1.Step.QUERY,original.expectedCore(),original.deadlineUnixMs(),original.operationId());}
    public static RawJson additionalFields(Request request){
        var row=com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode();row.putObject("arguments");var claim=row.putObject("date_advance");var build=GuiControlsFrameV2.BUILD;
        claim.put("schema",DateAdvanceFrameV1.REQUEST_SCHEMA).put("game_version",build.version()).put("executable_sha256",build.executableSha256().toUpperCase(java.util.Locale.ROOT)).put("adapter_id",build.coreFrameAdapterId()).put("backend",GuiControlsFrameV2.BACKEND).put("deadline_unix_ms",request.deadlineUnixMs()).put("operation_id",request.operationId());
        putPrefix(claim.putObject("expected_core"),request.expectedCore().prefix());var encoded=RegistryJson.encode(row);RegistryJson.require(fields(request.step(),encoded).equals(request),"exact current date request roundtrip required");return encoded;
    }
    public static Request decodeRequestPacket(byte[] packet)throws IOException{
        RegistryJson.require(packet!=null&&packet.length>=5&&packet.length<=16388,"bounded16KiB current date request required");var decoded=NativeWire.decodeExecuteRequest(packet);boolean quoted=false;
        for(int i=4;i<packet.length;i++){int value=Byte.toUnsignedInt(packet[i]);RegistryJson.require(value<127&&value!='\\',"current date request excludes non-ASCII/escapes");if(value=='"')quoted=!quoted;if(!quoted&&value=='-'&&i+1<packet.length&&packet[i+1]=='0'&&(i+2==packet.length||packet[i+2]<'0'||packet[i+2]>'9'))throw new IllegalArgumentException("canonical integer excludes negative zero");}
        var row=RegistryJson.object(new RawJson(Arrays.copyOfRange(packet,4,packet.length)));RegistryJson.keys(row,Set.of("type","protocol_version","request_id","step","expected_revision","arguments","date_advance"));
        DateAdvanceFrameV1.safeId(decoded.requestId());RegistryJson.require(decoded.expectedRevision().equals(Optional.of(BigInteger.ZERO))&&decoded.expectedSnapshotRevision().isEmpty(),"exact zero revision current date envelope required");
        return fields(DateAdvanceFrameV1.Step.wire(decoded.step()),new RawJson(decoded.normalizedAdditionalFields().value()));
    }
    private static Request fields(DateAdvanceFrameV1.Step step,RawJson raw){
        var row=RegistryJson.object(raw);RegistryJson.keys(row,Set.of("arguments","date_advance"));RegistryJson.keys(RegistryJson.object(row.get("arguments")),Set.of());var claim=RegistryJson.object(row.get("date_advance"));RegistryJson.keys(claim,Set.of("schema","game_version","executable_sha256","adapter_id","backend","deadline_unix_ms","expected_core","operation_id"));var build=GuiControlsFrameV2.BUILD;
        RegistryJson.require(DateAdvanceFrameV1.REQUEST_SCHEMA.equals(RegistryJson.text(claim.get("schema")))&&build.matches(RegistryJson.text(claim.get("game_version")),RegistryJson.text(claim.get("executable_sha256")))&&build.coreFrameAdapterId().equals(RegistryJson.text(claim.get("adapter_id")))&&GuiControlsFrameV2.BACKEND.equals(RegistryJson.text(claim.get("backend"))),"exact current date request tuple required");
        return new Request(step,new CoreFrame.Partial(build,DateAdvanceFrameV1.prefix(claim.get("expected_core"))),RegistryJson.integer(claim.get("deadline_unix_ms"),BigInteger.ONE,RegistryJson.U64),RegistryJson.text(claim.get("operation_id")));
    }
    public static DateAdvanceFrameV1 decodePacket(RawJson raw,String requestId)throws IOException{
        RegistryJson.require(raw.bytes().length<=DateAdvanceFrameV1.MAXIMUM_BYTES+4096,"bounded current date ACK required");var row=RegistryJson.object(raw);RegistryJson.keys(row,Set.of("type","protocol_version","request_id","ok","result"));
        RegistryJson.require("command_result".equals(RegistryJson.text(row.get("type")))&&RegistryJson.integer(row.get("protocol_version"),BigInteger.ONE,BigInteger.ONE).equals(BigInteger.ONE)&&requestId.equals(RegistryJson.text(row.get("request_id"))),"exact original date envelope required");
        var frame=DateAdvanceFrameV1.decode(RegistryJson.encode(row.get("result")));RegistryJson.require(RegistryJson.bool(row.get("ok"))==frame.nativeOk(),"date outer ok must distinguish action accepted from query claim-found");return frame;
    }
    public static DateAdvanceFrameV1 decodeOutcome(NativeActionPort.DispatchOutcome actual)throws IOException{
        if(!(actual instanceof NativeActionPort.AckReceived ack))throw new IOException("actual date ACK absent; preserve original without replay");var outbound=ack.outbound().orElseThrow(()->new IOException("original date outbound absent"));var request=decodeRequestPacket(outbound.originalPacket());var outgoing=NativeWire.decodeExecuteRequest(outbound.originalPacket());
        if(!outbound.requestId().equals(ack.requestId())||!outgoing.requestId().equals(ack.requestId())||ack.originalPacket().length>DateAdvanceFrameV1.MAXIMUM_BYTES+4100)throw new IOException("date original request identity/size drift");
        var decoded=NativeWire.decode(ack.originalPacket());if(!(decoded instanceof NativeWire.CommandResult result)||result.nativeOk()!=ack.nativeOk()||!result.requestId().equals(ack.requestId())||!Arrays.equals(result.payload().value(),ack.originalFrame().bytes())||result.result().presence()!=NativeWire.Presence.VALUE||ack.originalResultToken().isEmpty()||!Arrays.equals(result.result().token().orElseThrow().value(),ack.originalResultToken().orElseThrow().bytes()))throw new IOException("date original packet/token drift");
        var custody=ack.custody().orElseThrow(()->new IOException("actual date ACK custody absent"));custody.verify(ack);var frame=decodePacket(new RawJson(result.payload().value()),ack.requestId());
        if(frame.step()!=request.step()||!frame.operationId().equals(request.operationId())||frame.nativeOk()!=ack.nativeOk()||frame.coreBefore().isPresent()&&!frame.coreBefore().orElseThrow().equals(request.expectedCore().prefix())||frame.ownerWitness().isPresent()&&!frame.ownerWitness().orElseThrow().connectionGeneration().equals(custody.session().connectionGeneration()))throw new IOException("date result crossed its original operation/Core/owner/session");return frame;
    }
    private static void putPrefix(com.fasterxml.jackson.databind.node.ObjectNode row,CoreFrame.Prefix p){row.put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused()).put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter()).put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());}
    public static RawJson encode(DateAdvanceFrameV1 frame){
        var row=com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode();var build=GuiControlsFrameV2.BUILD;
        row.put("schema",DateAdvanceFrameV1.SCHEMA).put("game_version",build.version()).put("executable_sha256",build.executableSha256().toUpperCase(java.util.Locale.ROOT)).put("adapter_id",build.coreFrameAdapterId()).put("backend",GuiControlsFrameV2.BACKEND).put("step",frame.step().wire()).put("status",frame.status().wire()).put("operation_id",frame.operationId());
        row.put("accepted",frame.accepted()).put("claim_found",frame.claimFound()).put("owner_before_verified",frame.ownerBeforeVerified()).put("arm_attempted",frame.armAttempted()).put("resume_attempted",frame.resumeAttempted()).put("resume_submitted",frame.resumeSubmitted()).put("exact_day_confirmed",frame.exactDayConfirmed()).put("shutdown_safe",frame.shutdownSafe()).put("armed",frame.armed()).put("access_cleanup_unknown",frame.accessCleanupUnknown()).put("complete_snapshot",false).put("physical_save_confirmed",false).put("failure_flags",frame.failureFlags());
        if(frame.claimSequence().isPresent())row.put("claim_sequence",frame.claimSequence().orElseThrow().toString());else row.putNull("claim_sequence");if(frame.generation().isPresent())row.put("generation",frame.generation().orElseThrow().toString());else row.putNull("generation");
        if(frame.coreBefore().isPresent())putPrefix(row.putObject("core_before"),frame.coreBefore().orElseThrow());else row.putNull("core_before");row.putNull("core_after");
        if(frame.ownerWitness().isPresent()){var w=frame.ownerWitness().orElseThrow();row.putObject("owner_witness").put("connection_generation",w.connectionGeneration().toString()).put("ticket_sequence",w.ticketSequence().toString()).put("pump_epoch",w.pumpEpoch().toString()).put("thread_id",w.threadId());}else row.putNull("owner_witness");
        if(frame.sentinel().isPresent()){
            var s=frame.sentinel().orElseThrow();var node=row.putObject("sentinel").put("state",s.state().wire()).put("mode",s.mode().wire()).put("army_count",s.armyCount()).put("combat_count",s.combatCount()).put("starting_date_raw",s.startingDateRaw()).put("target_date_raw",s.targetDateRaw()).put("last_observed_date_raw",s.lastObservedDateRaw()).put("trigger_date_raw",s.triggerDateRaw()).put("speed",s.speed()).put("completed_daily_ticks",s.completedDailyTicks()).put("trigger_flags",s.triggerFlags()).put("signed_date_delta_from_target_raw",s.signedDateDeltaFromTargetRaw()).put("overshoot_days",s.overshootDays()).put("pause_wrapper_called",s.pauseWrapperCalled()).put("pause_observed",s.pauseObserved()).put("combat_terminal_observed",s.combatTerminalObserved()).put("abnormal",s.abnormal());if(s.generation().isPresent())node.put("generation",s.generation().orElseThrow().toString());else node.putNull("generation");
        }else row.putNull("sentinel");var encoded=RegistryJson.encode(row);RegistryJson.require(DateAdvanceFrameV1.decode(encoded).equals(frame),"current date result roundtrip drift");return encoded;
    }
}
