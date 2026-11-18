package org.xar.ck3.control.nativebridge.capabilities.registry;

import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.semantic.NativePlayedResources;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Original actor query DATA codec. It constructs no ACK, private receipt, live receiver, complete observation or control permit. */
public final class ActorFoundationFramePublicCodec {
    public enum Request { INSTANCE }
    private ActorFoundationFramePublicCodec(){ }
    public static Request decodeArguments(PublicBindings.Arguments arguments){
        Objects.requireNonNull(arguments);
        if(arguments instanceof PublicBindings.Value value)RegistryJson.keys(RegistryJson.object(value.original()),Set.of());
        return Request.INSTANCE;
    }
    /** Pure archived original command_result JSON, not proof that an endpoint sent it. */
    public static ActorFoundationFrame decodePacket(RawJson original,String expectedRequestId)throws IOException {
        Objects.requireNonNull(original);Objects.requireNonNull(expectedRequestId);
        var envelope=RegistryJson.object(original);
        RegistryJson.keys(envelope,Set.of("type","protocol_version","request_id","ok","result"));
        RegistryJson.require("command_result".equals(RegistryJson.text(envelope.get("type")))
                &&RegistryJson.integer(envelope.get("protocol_version"),BigInteger.ONE,BigInteger.ONE).equals(BigInteger.ONE)
                &&expectedRequestId.equals(RegistryJson.text(envelope.get("request_id")))&&RegistryJson.bool(envelope.get("ok")),
                "actor foundation original envelope identity/status differs");
        var decoded=NativeWire.decode(NativeWire.packet(original.bytes()));
        RegistryJson.require(decoded instanceof NativeWire.CommandResult,"actor foundation requires its original command_result");
        var result=(NativeWire.CommandResult)decoded;
        RegistryJson.require(result.result().presence()==NativeWire.Presence.VALUE,"actor foundation original result is missing or null");
        return ActorFoundationFrame.decode(new RawJson(result.result().token().orElseThrow().value()));
    }
    /** Required tuple/capability DATA check for a future receiver; this alone attests no process, session or live source. */
    public static void requireHello(NativeWire.Hello original)throws IOException {
        Objects.requireNonNull(original);
        try {
            var decoded=NativeWire.decode(original.packet().value());
            require(decoded instanceof NativeWire.Hello,"actor foundation original HELLO packet missing");
            var actual=(NativeWire.Hello)decoded;
            require(actual.pid()==original.pid()&&actual.connectionGeneration().equals(original.connectionGeneration())
                    &&actual.bridgeVersion().equals(original.bridgeVersion())&&actual.gameSha256().equals(original.gameSha256())
                    &&actual.adapterId().equals(original.adapterId())&&actual.adapterStatus().equals(original.adapterStatus())
                    &&actual.buildMatch()==original.buildMatch()&&actual.capabilities().equals(original.capabilities()),
                    "actor foundation HELLO fields differ from the original packet");
            byte[] packet=original.packet().value();
            var raw=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(packet,4,packet.length)));
            require(ActorFoundationFrame.BUILD.matches(NativeWire.text(raw.get("expected_ck3_version")),actual.gameSha256())
                    &&ActorFoundationFrame.ADAPTER.equals(actual.adapterId())&&actual.buildMatch()&&actual.adapterStatus().equals("ready")
                    &&actual.capabilities().contains(ActorFoundationFrame.CAPABILITY),"actor foundation exact HELLO/capability unavailable");
        }catch(IllegalArgumentException invalid){throw new IOException("actor foundation HELLO original is invalid",invalid);}
    }
    public static ActorFoundationFrame decodeOutcome(NativeActionPort.DispatchOutcome original)throws IOException {
        Objects.requireNonNull(original);
        if(original instanceof NativeActionPort.RejectedBeforeDispatch rejected)
            throw new IOException("actual actor foundation source unavailable before dispatch: "+rejected.proof().reason());
        if(original instanceof NativeActionPort.Unknown unknown)
            throw new IOException("actual actor foundation result unknown; original request is never replayed: "+unknown.reason());
        var ack=(NativeActionPort.AckReceived)original;
        try {
            var outbound=ack.outbound().orElseThrow(()->new IOException("actor foundation original outbound missing"));
            var request=NativeWire.decodeExecuteRequest(outbound.originalPacket());
            require(outbound.requestId().equals(ack.requestId())&&request.requestId().equals(ack.requestId())
                    &&ActorFoundationFrame.STEP.equals(request.step())&&request.expectedRevision().equals(Optional.of(BigInteger.ZERO))
                    &&request.expectedSnapshotRevision().isEmpty(),"actor foundation request identity/step/revision differs");
            RegistryJson.keys(RegistryJson.object(new RawJson(request.normalizedAdditionalFields().value())),Set.of());
            var decoded=NativeWire.decode(ack.originalPacket());
            require(decoded instanceof NativeWire.CommandResult,"actor foundation original response is not command_result");
            var result=(NativeWire.CommandResult)decoded;
            require(result.requestId().equals(ack.requestId())&&result.nativeOk()==ack.nativeOk()
                    &&Arrays.equals(result.payload().value(),ack.originalFrame().bytes()),"actor foundation retained envelope differs");
            require(result.result().presence()==NativeWire.Presence.VALUE&&ack.originalResultToken().isPresent()
                    &&Arrays.equals(result.result().token().orElseThrow().value(),ack.originalResultToken().orElseThrow().bytes()),
                    "actor foundation retained result differs from the original response");
            return decodePacket(ack.originalFrame(),ack.requestId());
        }catch(IllegalArgumentException invalid){throw new IOException("actor foundation original profile or partial result is invalid",invalid);}
    }
    public static RawJson encode(ActorFoundationFrame actual){
        Objects.requireNonNull(actual);var row=JsonNodeFactory.instance.objectNode();
        row.put("step",ActorFoundationFrame.STEP);row.put("schema",ActorFoundationFrame.SCHEMA);
        row.put("game_version",actual.build().version());row.put("executable_sha256",actual.build().executableSha256().toUpperCase(Locale.ROOT));
        row.put("adapter_id",ActorFoundationFrame.ADAPTER);row.put("backend",ActorFoundationFrame.BACKEND);
        row.put("status",actual instanceof ActorFoundationFrame.Partial?"partial":"unavailable");
        row.put("foundation_available",actual instanceof ActorFoundationFrame.Partial);
        row.put("application_main_observed",actual.applicationMainObserved());
        row.put("complete_snapshot",false);row.put("treasury_observed",false);row.put("monthly_flow_observed",false);
        row.set("core_frame",RegistryJson.object(CoreFramePublicCodec.encode(actual.coreFrame())));
        if(actual.resources() instanceof ActorFoundationFrame.AvailableResources resources){
            row.put("resources_available",true);row.putNull("resources_unavailable_reason");var values=row.putObject("resources");
            values.set("gold",NativePlayedResources.encode(resources.gold()));values.set("prestige",NativePlayedResources.encode(resources.prestige()));
            values.set("piety",NativePlayedResources.encode(resources.piety()));values.put("stress_points",resources.stressPoints());
        }else{
            row.put("resources_available",false);row.putNull("resources");
            row.put("resources_unavailable_reason",((ActorFoundationFrame.UnavailableResources)actual.resources()).reason());
        }
        if(actual.relationships() instanceof ActorFoundationFrame.AvailableRelationships relationships){
            row.put("relationships_available",true);row.putNull("relationships_unavailable_reason");var values=row.putObject("relationships");
            values.put("betrothed_character_id",relationships.betrothedCharacterId());values.put("primary_spouse_character_id",relationships.primarySpouseCharacterId());
            var ids=values.putArray("spouse_character_ids");relationships.spouseCharacterIds().forEach(ids::add);
        }else{
            row.put("relationships_available",false);row.putNull("relationships");
            row.put("relationships_unavailable_reason",((ActorFoundationFrame.UnavailableRelationships)actual.relationships()).reason());
        }
        if(actual instanceof ActorFoundationFrame.Unavailable missing)row.put("unavailable_reason",missing.reason());else row.putNull("unavailable_reason");
        var result=RegistryJson.encode(row);ActorFoundationFrame.decode(result);return result;
    }
    private static void require(boolean condition,String reason)throws IOException {if(!condition)throw new IOException(reason);}
}
