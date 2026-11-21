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

/** Strict current frontend DATA codec. Only the receiver may bind it to a live original menu occurrence. */
public final class FrontendMenuFrameV1PublicCodec {
    private FrontendMenuFrameV1PublicCodec() { }
    public record Lease(BigInteger providerGeneration,BigInteger querySequence) {
        public Lease {FrontendMenuFrameV1.uint64(providerGeneration,false);FrontendMenuFrameV1.uint64(querySequence,false);
            RegistryJson.require((providerGeneration.signum()==0)==(querySequence.signum()==0),"frontend lease must be all zero or all nonzero");}
        public boolean empty(){return providerGeneration.signum()==0;}
    }
    public record Request(FrontendMenuFrameV1.Action action,BigInteger deadlineUnixMs,Lease lease) {
        public Request {Objects.requireNonNull(action);Objects.requireNonNull(lease);FrontendMenuFrameV1.uint64(deadlineUnixMs,true);
            RegistryJson.require(action.readOnly()==lease.empty(),"query requires zero lease; effect requires its original nonzero menu lease");}
        public Instant deadline(){return Instant.ofEpochMilli(deadlineUnixMs.longValueExact());}
    }
    public static Request query(Instant deadline){return new Request(FrontendMenuFrameV1.Action.QUERY_MENU,BigInteger.valueOf(Objects.requireNonNull(deadline).toEpochMilli()),new Lease(BigInteger.ZERO,BigInteger.ZERO));}
    public static Request action(FrontendMenuFrameV1.Action action,Request originalQuery,Lease lease) {
        Objects.requireNonNull(originalQuery);RegistryJson.require(originalQuery.action().readOnly()&&!action.readOnly(),"fixed menu effect requires its original query deadline");
        return new Request(action,originalQuery.deadlineUnixMs(),lease);
    }
    public static RawJson additionalFields(Request request) {
        Objects.requireNonNull(request);var row=com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode();row.putObject("arguments");var c=row.putObject("frontend_menu");var b=FrontendMenuFrameV1.BUILD;
        c.put("schema",FrontendMenuFrameV1.REQUEST_SCHEMA).put("game_version",b.version()).put("executable_sha256",b.executableSha256().toUpperCase(java.util.Locale.ROOT))
                .put("adapter_id",b.coreFrameAdapterId()).put("backend",FrontendMenuFrameV1.BACKEND).put("action",request.action().wire()).put("deadline_unix_ms",request.deadlineUnixMs())
                .put("provider_generation",request.lease().providerGeneration().toString()).put("query_sequence",request.lease().querySequence().toString());
        RawJson result=RegistryJson.encode(row);RegistryJson.require(decodeFields(result).equals(request),"frontend request roundtrip drift");return result;
    }
    public static Request decodeRequestPacket(byte[] packet)throws IOException {
        RegistryJson.require(packet!=null&&packet.length>=5&&packet.length-4<=16384,"bounded16KiB frontend request required");
        var request=NativeWire.decodeExecuteRequest(packet);var row=RegistryJson.object(new RawJson(Arrays.copyOfRange(packet,4,packet.length)));
        RegistryJson.keys(row,Set.of("type","protocol_version","request_id","step","expected_revision","arguments","frontend_menu"));
        RegistryJson.require(request.requestId().matches("[A-Za-z0-9_.-]{1,96}")&&request.expectedRevision().equals(Optional.of(BigInteger.ZERO))&&request.expectedSnapshotRevision().isEmpty(),"exact frontend request envelope required");
        Request result=decodeFields(new RawJson(request.normalizedAdditionalFields().value()));RegistryJson.require(request.step().equals(result.action().step()),"frontend request action/step mismatch");return result;
    }
    private static Request decodeFields(RawJson original) {
        var row=RegistryJson.object(original);RegistryJson.keys(row,Set.of("arguments","frontend_menu"));RegistryJson.keys(RegistryJson.object(row.get("arguments")),Set.of());
        var c=RegistryJson.object(row.get("frontend_menu"));RegistryJson.keys(c,Set.of("schema","game_version","executable_sha256","adapter_id","backend","action","deadline_unix_ms","provider_generation","query_sequence"));
        FrontendMenuFrameV1.requireTuple(c,FrontendMenuFrameV1.REQUEST_SCHEMA);
        return new Request(FrontendMenuFrameV1.Action.wire(RegistryJson.text(c.get("action"))),RegistryJson.integer(c.get("deadline_unix_ms"),BigInteger.ONE,RegistryJson.U64),new Lease(FrontendMenuFrameV1.decimal(c.get("provider_generation"),false),FrontendMenuFrameV1.decimal(c.get("query_sequence"),false)));
    }
    public static FrontendMenuFrameV1 decodePacket(RawJson original,String expectedRequestId)throws IOException {
        var row=RegistryJson.object(original);RegistryJson.keys(row,Set.of("type","protocol_version","request_id","ok","result"));
        RegistryJson.require("command_result".equals(RegistryJson.text(row.get("type")))&&RegistryJson.integer(row.get("protocol_version"),BigInteger.ONE,BigInteger.ONE).equals(BigInteger.ONE)
                &&Objects.requireNonNull(expectedRequestId).equals(RegistryJson.text(row.get("request_id"))),"exact frontend result envelope required");
        var frame=FrontendMenuFrameV1.decode(new RawJson(RegistryJson.encode(RegistryJson.object(row.get("result"))).bytes()));
        RegistryJson.require(RegistryJson.bool(row.get("ok"))==frame.nativeOk(),"frontend ok/status coherence mismatch");return frame;
    }
    public static FrontendMenuFrameV1 decodeOutcome(NativeActionPort.DispatchOutcome outcome)throws IOException {
        Objects.requireNonNull(outcome);if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("actual original frontend ACK unavailable; preserve outcome without replay");
        var outbound=ack.outbound().orElseThrow(()->new IOException("frontend original outbound missing"));Request request=decodeRequestPacket(outbound.originalPacket());var parsed=NativeWire.decodeExecuteRequest(outbound.originalPacket());
        if(!outbound.requestId().equals(ack.requestId())||!parsed.requestId().equals(ack.requestId()))throw new IOException("frontend request identity drift");
        var decoded=NativeWire.decode(ack.originalPacket());
        if(!(decoded instanceof NativeWire.CommandResult result)||result.nativeOk()!=ack.nativeOk()||!result.requestId().equals(ack.requestId())||!Arrays.equals(result.payload().value(),ack.originalFrame().bytes())
                ||result.result().presence()!=NativeWire.Presence.VALUE||ack.originalResultToken().isEmpty()||!Arrays.equals(result.result().token().orElseThrow().value(),ack.originalResultToken().orElseThrow().bytes()))throw new IOException("frontend original result token/envelope drift");
        var frame=decodePacket(new RawJson(result.payload().value()),ack.requestId());if(frame.action()!=request.action())throw new IOException("frontend response crossed its actual original action");
        if(!request.action().readOnly()&&(!frame.providerGeneration().equals(request.lease().providerGeneration())||!frame.querySequence().equals(request.lease().querySequence())))throw new IOException("frontend response changed original private lease");
        var custody=ack.custody().orElseThrow(()->new IOException("frontend actual ACK custody missing"));custody.verify(ack);
        if(frame.ownerWitness().isPresent()&&!frame.ownerWitness().orElseThrow().connectionGeneration().equals(custody.session().connectionGeneration()))throw new IOException("frontend source crossed actual connection owner");
        return frame;
    }
    public static RawJson encode(FrontendMenuFrameV1 frame) {
        Objects.requireNonNull(frame);var row=com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode();var b=FrontendMenuFrameV1.BUILD;
        row.put("schema",FrontendMenuFrameV1.SCHEMA).put("game_version",b.version()).put("executable_sha256",b.executableSha256().toUpperCase(java.util.Locale.ROOT)).put("adapter_id",b.coreFrameAdapterId()).put("backend",FrontendMenuFrameV1.BACKEND)
                .put("step",frame.action().step()).put("action",frame.action().wire()).put("status",frame.status().wire()).put("facts_available",frame.source().isPresent()).put("effect_attempted",frame.effectAttempted()).put("native_returned",frame.nativeReturned()).put("post_selection_verified",frame.postSelectionVerified())
                .put("addresses_redacted",true).put("world_core_fabricated",false).put("application_exit_confirmed",false).put("game_started_confirmed",false).put("physical_save_confirmed",false)
                .put("provider_generation",frame.providerGeneration().toString()).put("query_sequence",frame.querySequence().toString()).put("claim_sequence",frame.claimSequence().toString());
        if(frame.source().isPresent()) {
            var s=frame.source().orElseThrow();var source=row.putObject("source");source.put("route",s.route().wire()).put("application_verified",true).put("gui_context_verified",true).put("global_root_verified",true).put("route_root_visible",true).put("no_world",true)
                    .put("robert_source_verified",s.robertSourceVerified()).put("start_admissible",s.startAdmissible());
            if(s.selectedBookmarkKey().isPresent())source.put("selected_bookmark_key",s.selectedBookmarkKey().orElseThrow());else source.putNull("selected_bookmark_key");
            if(s.selectedCharacterKey().isPresent())source.put("selected_character_key",s.selectedCharacterKey().orElseThrow());else source.putNull("selected_character_key");
            var w=frame.ownerWitness().orElseThrow();row.putObject("owner_witness").put("connection_generation",w.connectionGeneration().toString()).put("ticket_sequence",w.ticketSequence().toString()).put("pump_epoch",w.pumpEpoch().toString()).put("thread_id",w.threadId());
        } else {row.putNull("source");row.putNull("owner_witness");}
        if(frame.unavailableReason().isPresent())row.put("unavailable_reason",frame.unavailableReason().orElseThrow());else row.putNull("unavailable_reason");
        RawJson encoded=RegistryJson.encode(row);RegistryJson.require(FrontendMenuFrameV1.decode(encoded).equals(frame),"frontend result roundtrip drift");return encoded;
    }
}
