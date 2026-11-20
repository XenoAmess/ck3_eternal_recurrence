package org.xar.ck3.control.nativebridge.capabilities.registry;

import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Strict current v2 DATA wire. Private transport receipts, not this codec, own actual dispatch authority. */
public final class GuiControlsFrameV2PublicCodec {
    private GuiControlsFrameV2PublicCodec(){}
    public record SelectionToken(BigInteger queryGeneration,BigInteger widgetId){public SelectionToken{GuiControlsFrameV2.positive64(queryGeneration);GuiControlsFrameV2.positive64(widgetId);}}
    public record Request(GuiControlsFrameV2.Operation operation,CoreFrame.Partial expectedCore,BigInteger deadlineUnixMs,
            GuiControlsFrameV2.Window window,OptionalLong expectedSourceRiteId,Optional<SelectionToken> selection){
        public Request{Objects.requireNonNull(operation);GuiControlsFrameV2.requireCore(expectedCore);GuiControlsFrameV2.positive64(deadlineUnixMs);Objects.requireNonNull(window);Objects.requireNonNull(expectedSourceRiteId);Objects.requireNonNull(selection);
            RegistryJson.require(expectedSourceRiteId.isPresent()==(window==GuiControlsFrameV2.Window.RITE),"only the Rite root has its required original source Rite");expectedSourceRiteId.ifPresent(RiteDraftCostsFrameV2::sourceRiteId);
            RegistryJson.require(selection.isPresent()==(operation==GuiControlsFrameV2.Operation.ACTIVATE)&&(!selection.isPresent()||window==GuiControlsFrameV2.Window.RITE),"only a Rite activation has its original query/widget selection");}
    }
    public static Request query(CoreFrame.Partial core,Instant until,GuiControlsFrameV2.Window window,OptionalLong source){return new Request(GuiControlsFrameV2.Operation.QUERY,core,BigInteger.valueOf(until.toEpochMilli()),window,source,Optional.empty());}
    public static Request activate(Request original,Instant until,SelectionToken selection){return new Request(GuiControlsFrameV2.Operation.ACTIVATE,original.expectedCore(),BigInteger.valueOf(until.toEpochMilli()),original.window(),original.expectedSourceRiteId(),Optional.of(selection));}
    public static RawJson additionalFields(Request request){
        var row=com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode();row.putObject("arguments");var claim=row.putObject("gui_control");var build=GuiControlsFrameV2.BUILD;
        claim.put("schema",GuiControlsFrameV2.REQUEST_SCHEMA).put("game_version",build.version()).put("executable_sha256",build.executableSha256().toUpperCase(java.util.Locale.ROOT)).put("adapter_id",build.coreFrameAdapterId()).put("backend",GuiControlsFrameV2.BACKEND).put("deadline_unix_ms",request.deadlineUnixMs()).put("window_name",request.window().wire());
        var p=request.expectedCore().prefix();claim.putObject("expected_core").put("date_raw",p.dateRaw()).put("speed",p.speed()).put("paused",p.paused()).put("local_player_id",p.localPlayerId()).put("map_ready",p.mapReady()).put("has_played_character",p.hasPlayedCharacter()).put("played_character_id",p.playedCharacterId()).put("played_character_alive",p.playedCharacterAlive());
        request.expectedSourceRiteId().ifPresent(value->claim.put("expected_source_rite_id",value));request.selection().ifPresent(value->claim.put("query_generation",value.queryGeneration().toString()).put("widget_id",value.widgetId().toString()));
        var result=RegistryJson.encode(row);RegistryJson.require(fields(request.operation(),result).equals(request),"current controls request roundtrip drift");return result;
    }
    public static Request decodeRequestPacket(byte[] packet)throws IOException{
        RegistryJson.require(packet!=null&&packet.length>=5&&packet.length<=16388,"bounded16KiB current request required");var decoded=NativeWire.decodeExecuteRequest(packet);boolean quoted=false;
        for(int i=4;i<packet.length;i++){int value=Byte.toUnsignedInt(packet[i]);RegistryJson.require(value<127&&value!='\\',"current request excludes non-ASCII/escapes");if(value=='"')quoted=!quoted;if(!quoted&&value=='-'&&i+1<packet.length&&packet[i+1]=='0'&&(i+2==packet.length||packet[i+2]<'0'||packet[i+2]>'9'))throw new IllegalArgumentException("canonical integer excludes negative zero");}
        var raw=RegistryJson.object(new RawJson(Arrays.copyOfRange(packet,4,packet.length)));RegistryJson.keys(raw,Set.of("type","protocol_version","request_id","step","expected_revision","arguments","gui_control"));
        RegistryJson.require(decoded.requestId().matches("[A-Za-z0-9_.-]{1,96}")&&decoded.expectedRevision().equals(Optional.of(BigInteger.ZERO))&&decoded.expectedSnapshotRevision().isEmpty(),"exact current controls outer request required");
        return fields(GuiControlsFrameV2.Operation.step(decoded.step()),new RawJson(decoded.normalizedAdditionalFields().value()));
    }
    private static Request fields(GuiControlsFrameV2.Operation operation,RawJson raw){
        var row=RegistryJson.object(raw);RegistryJson.keys(row,Set.of("arguments","gui_control"));RegistryJson.keys(RegistryJson.object(row.get("arguments")),Set.of());var claim=RegistryJson.object(row.get("gui_control"));
        var window=GuiControlsFrameV2.Window.wire(RegistryJson.text(claim.get("window_name")));var keys=new HashSet<>(Set.of("schema","game_version","executable_sha256","adapter_id","backend","deadline_unix_ms","expected_core","window_name"));if(window==GuiControlsFrameV2.Window.RITE)keys.add("expected_source_rite_id");if(operation==GuiControlsFrameV2.Operation.ACTIVATE){keys.add("query_generation");keys.add("widget_id");}RegistryJson.keys(claim,keys);
        var build=GuiControlsFrameV2.BUILD;RegistryJson.require(GuiControlsFrameV2.REQUEST_SCHEMA.equals(RegistryJson.text(claim.get("schema")))&&build.matches(RegistryJson.text(claim.get("game_version")),RegistryJson.text(claim.get("executable_sha256")))&&build.coreFrameAdapterId().equals(RegistryJson.text(claim.get("adapter_id")))&&GuiControlsFrameV2.BACKEND.equals(RegistryJson.text(claim.get("backend"))),"exact current controls request tuple required");
        var core=RegistryJson.object(claim.get("expected_core"));RegistryJson.keys(core,Set.of("date_raw","speed","paused","local_player_id","map_ready","has_played_character","played_character_id","played_character_alive"));
        var expected=new CoreFrame.Partial(build,new CoreFrame.Prefix(RegistryJson.int32(core.get("date_raw")),RegistryJson.int32(core.get("speed")),RegistryJson.bool(core.get("paused")),RegistryJson.int32(core.get("local_player_id")),RegistryJson.bool(core.get("map_ready")),RegistryJson.bool(core.get("has_played_character")),RegistryJson.int32(core.get("played_character_id")),RegistryJson.bool(core.get("played_character_alive"))));
        return new Request(operation,expected,RegistryJson.integer(claim.get("deadline_unix_ms"),BigInteger.ONE,RegistryJson.U64),window,window==GuiControlsFrameV2.Window.RITE?OptionalLong.of(RegistryJson.integer(claim.get("expected_source_rite_id"),BigInteger.ZERO,BigInteger.valueOf(0xffff_fffeL)).longValueExact()):OptionalLong.empty(),operation==GuiControlsFrameV2.Operation.ACTIVATE?Optional.of(new SelectionToken(GuiControlsFrameV2.uint64String(claim.get("query_generation")),GuiControlsFrameV2.uint64String(claim.get("widget_id")))):Optional.empty());
    }
    public static GuiControlsFrameV2 decodePacket(RawJson raw,String requestId)throws IOException{
        RegistryJson.require(raw.bytes().length<=GuiControlsFrameV2.MAXIMUM_BYTES+4096,"bounded controls ACK envelope required");var row=RegistryJson.object(raw);RegistryJson.keys(row,Set.of("type","protocol_version","request_id","ok","result"));RegistryJson.require("command_result".equals(RegistryJson.text(row.get("type")))&&RegistryJson.integer(row.get("protocol_version"),BigInteger.ONE,BigInteger.ONE).equals(BigInteger.ONE)&&requestId.equals(RegistryJson.text(row.get("request_id")))&&RegistryJson.bool(row.get("ok")),"original positive current controls envelope required");
        var decoded=NativeWire.decode(NativeWire.packet(raw.bytes()));if(!(decoded instanceof NativeWire.CommandResult result)||result.result().presence()!=NativeWire.Presence.VALUE)throw new IOException("original controls result token required");return GuiControlsFrameV2.decode(new RawJson(result.result().token().orElseThrow().value()));
    }
    public static GuiControlsFrameV2 decodeOutcome(NativeActionPort.DispatchOutcome actual)throws IOException{
        if(!(actual instanceof NativeActionPort.AckReceived ack))throw new IOException("actual controls ACK unavailable; original retained, no replay");var outbound=ack.outbound().orElseThrow(()->new IOException("original controls outbound absent"));var request=decodeRequestPacket(outbound.originalPacket());var outgoing=NativeWire.decodeExecuteRequest(outbound.originalPacket());
        if(!outbound.requestId().equals(ack.requestId())||!outgoing.requestId().equals(ack.requestId())||ack.originalPacket().length>GuiControlsFrameV2.MAXIMUM_BYTES+4100)throw new IOException("original controls request identity/size drift");
        var decoded=NativeWire.decode(ack.originalPacket());if(!(decoded instanceof NativeWire.CommandResult result)||!ack.nativeOk()||result.nativeOk()!=ack.nativeOk()||!result.requestId().equals(ack.requestId())||!Arrays.equals(result.payload().value(),ack.originalFrame().bytes())||result.result().presence()!=NativeWire.Presence.VALUE||ack.originalResultToken().isEmpty()||!Arrays.equals(result.result().token().orElseThrow().value(),ack.originalResultToken().orElseThrow().bytes()))throw new IOException("original controls result packet/token drift");
        var custody=ack.custody().orElseThrow(()->new IOException("actual controls custody absent"));custody.verify(ack);var frame=decodePacket(new RawJson(result.payload().value()),ack.requestId());
        if(frame.operation()!=request.operation()||frame.window()!=request.window()||frame.coreBeforeVerified()&&(!frame.coreFrame().equals(request.expectedCore())||!frame.ownerWitness().orElseThrow().connectionGeneration().equals(custody.session().connectionGeneration()))||frame.riteSourceVerified()&&(!request.expectedSourceRiteId().equals(frame.sourceRiteId()))||request.selection().isPresent()&&frame.queryGeneration().isPresent()&&!request.selection().orElseThrow().queryGeneration().equals(frame.queryGeneration().orElseThrow()))throw new IOException("controls result crossed original Core/source/window/generation/session");return frame;
    }
    public static RawJson encode(GuiControlsFrameV2 frame){
        var row=com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode();var build=GuiControlsFrameV2.BUILD;
        row.put("step",frame.operation().step()).put("schema",GuiControlsFrameV2.SCHEMA).put("game_version",build.version()).put("executable_sha256",build.executableSha256().toUpperCase(java.util.Locale.ROOT)).put("adapter_id",build.coreFrameAdapterId()).put("backend",GuiControlsFrameV2.BACKEND).put("status",frame.status().wire()).put("window_name",frame.window().wire());
        row.put("query_available",frame.queryAvailable()).put("application_main_observed",frame.coreFrame() instanceof CoreFrame.Partial||((CoreFrame.Unavailable)frame.coreFrame()).applicationMainObserved()).put("core_before_verified",frame.coreBeforeVerified()).put("source_abi_pins_verified",frame.sourceAbiPinsVerified()).put("rite_source_verified",frame.riteSourceVerified()).put("addresses_redacted",true);
        for(String key:Set.of("complete_snapshot","full_snapshot_before_verified","complete_gui_tree","effect_confirmed","physical_save_confirmed"))row.put(key,false);
        row.put("effect_attempted",frame.effectAttempted()).put("native_handled",frame.nativeHandled()).put("verification_pending",frame.verificationPending());row.set("core_frame",RegistryJson.object(CoreFramePublicCodec.encode(frame.coreFrame())));
        if(frame.sourceRiteId().isPresent())row.put("source_rite_id",frame.sourceRiteId().getAsLong());else row.putNull("source_rite_id");if(frame.queryGeneration().isPresent())row.put("query_generation",frame.queryGeneration().orElseThrow().toString());else row.putNull("query_generation");
        if(frame.ownerWitness().isPresent()){var w=frame.ownerWitness().orElseThrow();row.putObject("owner_witness").put("connection_generation",w.connectionGeneration().toString()).put("ticket_sequence",w.ticketSequence().toString()).put("pump_epoch",w.pumpEpoch().toString()).put("thread_id",w.threadId());}else row.putNull("owner_witness");
        if(frame.widgets().isPresent()){var rows=row.putArray("widgets");for(var w:frame.widgets().orElseThrow())rows.addObject().put("widget_id",w.widgetId().toString()).put("runtime_name",w.runtimeName()).put("child_path",w.childPath()).put("effective_visible",w.effectiveVisible()).put("enabled",w.enabled()).put("native_callback_admissible",w.nativeCallbackAdmissible());}else row.putNull("widgets");
        if(frame.unavailableReason().isPresent())row.put("unavailable_reason",frame.unavailableReason().orElseThrow());else row.putNull("unavailable_reason");var result=RegistryJson.encode(row);RegistryJson.require(GuiControlsFrameV2.decode(result).equals(frame),"controls v2 roundtrip drift");return result;
    }
}
