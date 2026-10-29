package org.xar.ck3.control.nativebridge.capabilities.registry;

import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.NativeWire;

/** The original standalone core query has no arguments and never yields a complete gameplay observation. */
public final class CoreFramePublicCodec {
    public enum Request { INSTANCE }
    private CoreFramePublicCodec() { }
    public static Request decodeArguments(PublicBindings.Arguments arguments) {
        Objects.requireNonNull(arguments);
        if(arguments instanceof PublicBindings.Value value) RegistryJson.keys(RegistryJson.object(value.original()),Set.of());
        return Request.INSTANCE;
    }
    /** Checks the exact retained outbound and command_result before the existing strict native result decoder. */
    public static CoreFrame decodeOutcome(NativeActionPort.DispatchOutcome actual) throws IOException {
        Objects.requireNonNull(actual);
        if(actual instanceof NativeActionPort.RejectedBeforeDispatch rejected)
            throw new IOException("actual core-frame source unavailable before dispatch: "+rejected.proof().reason());
        if(actual instanceof NativeActionPort.Unknown unknown)
            throw new IOException("actual core-frame result unknown; original request is never replayed: "+unknown.reason());
        var ack=(NativeActionPort.AckReceived)actual;
        var outbound=ack.outbound().orElseThrow(()->new IOException("actual core-frame outbound packet is missing"));
        var request=NativeWire.decodeExecuteRequest(outbound.originalPacket());
        require(outbound.requestId().equals(ack.requestId())&&request.requestId().equals(ack.requestId())
                &&request.step().equals(CoreFrame.STEP)&&request.expectedRevision().equals(java.util.Optional.of(BigInteger.ZERO))
                &&request.expectedSnapshotRevision().isEmpty(),"original standalone core request identity/step/revision differs");
        require(RegistryJson.object(new RawJson(request.normalizedAdditionalFields().value())).isEmpty(),"standalone core request has unexpected arguments");
        var decoded=NativeWire.decode(ack.originalPacket());
        require(decoded instanceof NativeWire.CommandResult,"core result must be an original command_result packet");
        var result=(NativeWire.CommandResult)decoded;
        require(result.requestId().equals(ack.requestId())&&result.nativeOk()==ack.nativeOk()
                &&Arrays.equals(result.payload().value(),ack.originalFrame().bytes()),"original core command_result envelope differs from retained outcome");
        require(ack.nativeOk(),"native core-frame command_result rejected the query");
        require(result.result().presence()==NativeWire.Presence.VALUE,"native core-frame result is missing or null");
        byte[] token=result.result().token().orElseThrow().value();
        require(ack.originalResultToken().isPresent()&&Arrays.equals(token,ack.originalResultToken().orElseThrow().bytes()),
                "core-frame retained result token differs from original packet");
        try {return CoreFrame.decode(new RawJson(token));}
        catch(IllegalArgumentException invalid) {throw new IOException("actual core-frame profile or partial result is unavailable",invalid);}
    }
    /** Sole public normalization, matching the original .4 producer after exact native source validation. */
    public static RawJson encode(CoreFrame actual) {
        Objects.requireNonNull(actual);ObjectNode row=JsonNodeFactory.instance.objectNode();
        row.put("schema","ck3_12004_core_frame_v1");row.put("game_version","1.20.0.4");row.put("executable_sha256",RegistryJson.EXE);
        row.put("adapter_id","ck3-1.20.0.4-msvc-x64");row.put("backend","ck3-1.20.0.4-native-headless-main-thread");
        row.put("complete_snapshot",false);var excluded=row.putArray("excluded_snapshot_families");CoreFrame.EXCLUDED.forEach(excluded::add);
        if(actual instanceof CoreFrame.Partial partial) {
            var prefix=partial.prefix();row.put("status","partial");row.put("core_available",true);row.put("application_main_observed",true);row.putNull("unavailable_reason");
            row.put("date_raw",prefix.dateRaw());row.put("speed",prefix.speed());row.put("paused",prefix.paused());
            row.put("local_player_id",prefix.localPlayerId());row.put("map_ready",prefix.mapReady());row.put("has_played_character",prefix.hasPlayedCharacter());
            row.put("played_character_id",prefix.playedCharacterId());row.put("played_character_alive",prefix.playedCharacterAlive());
        } else {
            var unavailable=(CoreFrame.Unavailable)actual;row.put("status","unavailable");row.put("core_available",false);
            row.put("application_main_observed",unavailable.applicationMainObserved());row.put("unavailable_reason",unavailable.reason());
            for(String field:java.util.List.of("date_raw","speed","paused","local_player_id","map_ready","has_played_character","played_character_id","played_character_alive"))row.putNull(field);
        }
        RawJson result=RegistryJson.encode(row);CoreFrame.decode(result);return result;
    }
    private static void require(boolean condition,String reason)throws IOException {if(!condition)throw new IOException(reason);}
}
