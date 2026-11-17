package org.xar.ck3.control.nativebridge.capabilities.registry;

import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.semantic.NativePlayedResources;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Standalone public query DATA; decoding never issues a private receiver, complete frame or action role. */
public final class PersonalGoldFramePublicCodec {
    public enum Request { INSTANCE }
    private PersonalGoldFramePublicCodec(){ }
    public static Request decodeArguments(PublicBindings.Arguments arguments) {
        Objects.requireNonNull(arguments);
        if(arguments instanceof PublicBindings.Value value)RegistryJson.keys(RegistryJson.object(value.original()),Set.of());
        return Request.INSTANCE;
    }
    public static PersonalGoldFrame decodeOutcome(NativeActionPort.DispatchOutcome original)throws IOException {
        Objects.requireNonNull(original);
        if(original instanceof NativeActionPort.RejectedBeforeDispatch rejected)
            throw new IOException("actual personal-gold source unavailable before dispatch: "+rejected.proof().reason());
        if(original instanceof NativeActionPort.Unknown unknown)
            throw new IOException("actual personal-gold result unknown; original request is never replayed: "+unknown.reason());
        var ack=(NativeActionPort.AckReceived)original;
        try {
            var outbound=ack.outbound().orElseThrow(()->new IOException("personal-gold original outbound is missing"));
            var request=NativeWire.decodeExecuteRequest(outbound.originalPacket());
            require(outbound.requestId().equals(ack.requestId())&&request.requestId().equals(ack.requestId())
                    &&PersonalGoldFrame.STEP.equals(request.step())&&request.expectedRevision().equals(java.util.Optional.of(BigInteger.ZERO))
                    &&request.expectedSnapshotRevision().isEmpty(),"original personal-gold request identity/step/revision differs");
            RegistryJson.keys(RegistryJson.object(new RawJson(request.normalizedAdditionalFields().value())),Set.of());
            var decoded=NativeWire.decode(ack.originalPacket());
            require(decoded instanceof NativeWire.CommandResult,"personal-gold requires the original command_result envelope");
            var result=(NativeWire.CommandResult)decoded;
            require(result.requestId().equals(ack.requestId())&&result.nativeOk()==ack.nativeOk()
                    &&Arrays.equals(result.payload().value(),ack.originalFrame().bytes()),"personal-gold retained envelope differs from its original packet");
            RegistryJson.keys(RegistryJson.object(ack.originalFrame()),Set.of("type","protocol_version","request_id","ok","result"));
            require(ack.nativeOk(),"native command_result rejected personal-gold query");
            require(result.result().presence()==NativeWire.Presence.VALUE,"personal-gold original result is missing or null");
            byte[] token=result.result().token().orElseThrow().value();
            require(ack.originalResultToken().isPresent()&&Arrays.equals(token,ack.originalResultToken().orElseThrow().bytes()),
                    "personal-gold retained result token differs from its original packet");
            return PersonalGoldFrame.decode(new RawJson(token));
        }catch(IllegalArgumentException invalid){throw new IOException("personal-gold original profile or partial result is invalid",invalid);}
    }
    public static RawJson encode(PersonalGoldFrame actual) {
        Objects.requireNonNull(actual);var row=JsonNodeFactory.instance.objectNode();
        row.put("step",PersonalGoldFrame.STEP);row.put("schema",PersonalGoldFrame.SCHEMA);
        row.put("game_version",actual.build().version());row.put("executable_sha256",actual.build().executableSha256().toUpperCase(Locale.ROOT));
        row.put("adapter_id",PersonalGoldFrame.ADAPTER);row.put("backend",PersonalGoldFrame.BACKEND);
        row.put("complete_snapshot",false);row.put("treasury_observed",false);row.put("monthly_flow_observed",false);
        row.put("application_main_observed",actual.applicationMainObserved());
        row.set("core_frame",RegistryJson.object(CoreFramePublicCodec.encode(actual.coreFrame())));
        if(actual instanceof PersonalGoldFrame.Partial partial) {
            row.put("status","partial");row.put("personal_gold_available",true);row.putNull("unavailable_reason");
            row.set("personal_gold",NativePlayedResources.encode(partial.personalGold()));
        }else {
            var unavailable=(PersonalGoldFrame.Unavailable)actual;
            row.put("status","unavailable");row.put("personal_gold_available",false);row.putNull("personal_gold");row.put("unavailable_reason",unavailable.reason());
        }
        var result=RegistryJson.encode(row);PersonalGoldFrame.decode(result);return result;
    }
    private static void require(boolean condition,String reason)throws IOException {if(!condition)throw new IOException(reason);}
}
