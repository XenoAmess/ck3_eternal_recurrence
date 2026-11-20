package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PersonalGoldFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.PersonalGoldFramePublicCodec;

/** Actual C++ DATA tokens through the real receiver on an explicit software port; no Game or actual owner. */
final class NativePersonalGoldFrameV2ProducerTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final PersonalGoldFrame.Version VERSION=PersonalGoldFrame.Version.V2;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private record Input(String name,int bytes,String sha256,Long raw) { }
    private static final List<Input> INPUTS=List.of(
            new Input("personal-gold-v2-partial.json",1266,"e30ac0ef6e1bcf50e7d56597d661546700757ce126c3ee44d93856848e6ccadf",-12345L),
            new Input("personal-gold-v2-raw--1.json",1262,"7f3b213e5c238513b2a5f68267d6cbdb14ee9fb0c390700d7b31876ba0ee8a01",-1L),
            new Input("personal-gold-v2-raw--9223372036854775808.json",1280,"a95e473c44ab9aa87ff4566d392a582ec4f58dedf18397e8fe1022112cb33eb2",Long.MIN_VALUE),
            new Input("personal-gold-v2-raw-0.json",1261,"011321e6310f5082a902cdf66fa1288185def30bf6f08569b49ffc7962b15d70",0L),
            new Input("personal-gold-v2-raw-1.json",1261,"abae321994ed4c4e61765fd145a8539d58e3ccc328ffd7362ec7b894dd94b140",1L),
            new Input("personal-gold-v2-raw-9223372036854775807.json",1279,"ac05befbb8365d22281f22799be3982ecbf94dfe5b45475e992997d726ad830c",Long.MAX_VALUE),
            new Input("personal-gold-v2-unavailable.json",1302,"160b17627c72376e62451bbcb450749a29fecf640c93882449c0dbbbc2beb912",null));
    private static byte[] original(Input input)throws Exception {
        try(var stream=NativePersonalGoldFrameV2ProducerTest.class.getResourceAsStream("/newnative/personal-gold121003-v2/"+input.name())){
            if(stream==null)throw new IOException("actual C++ Gold V2 fixture missing");byte[] raw=stream.readNBytes(input.bytes()+1);
            assertEquals(input.bytes(),raw.length);assertEquals(input.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));return raw;
        }
    }
    private static ObjectNode hello(){
        var row=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",1)
                .put("bridge_version","software-gold-v2").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256())
                .put("game_adapter_id",VERSION.adapter()).put("game_adapter_status","ready").put("ck3_build_match",true);
        row.putArray("capabilities").add(VERSION.capability());return row;
    }
    private static NativePipeEndpoint.Config config(){return new NativePipeEndpoint.Config("\\\\.\\pipe\\software-gold-v2","software-gold-v2",GAME,
            "software-gold-v2-session","software-gold-v2",BUILD.executableSha256(),VERSION.adapter());}

    @Test void allSevenProductionCppTokensReachTheRealVersionedSenderReceiverAndCodecWithOriginalCustody()throws Exception {
        for(var input:INPUTS)try(var fixture=new Fixture(original(input),hello())){
            var received=assertInstanceOf(NativeGameTransport.PersonalGoldReceived.class,fixture.actual.readPersonalGoldFrameReceived(fixture.deadline));
            assertEquals(VERSION,received.frame().version());assertEquals(BUILD,received.frame().build());
            assertEquals(received.frame(),PersonalGoldFramePublicCodec.decodeOutcome(received.original()));
            assertEquals(received.frame(),PersonalGoldFrame.decodeV2(PersonalGoldFramePublicCodec.encode(received.frame())));
            received.requireOriginal(fixture.actual,received.validUntil());
            var ack=received.original();var custody=ack.custody().orElseThrow();custody.verify(ack);
            assertArrayEquals(fixture.source.token,ack.originalResultToken().orElseThrow().bytes());
            assertArrayEquals(fixture.source.request,ack.outbound().orElseThrow().originalPacket());
            assertEquals(VERSION.step(),NativeWire.decodeExecuteRequest(fixture.source.request).step());
            assertTrue(custody.writeEntered().order().compareTo(custody.writeCompleted().order())<0);
            assertTrue(custody.writeCompleted().order().compareTo(custody.responseReceived().order())<0);
            if(input.raw()!=null)assertEquals(input.raw().longValue(),assertInstanceOf(PersonalGoldFrame.Partial.class,received.frame()).personalGold().raw());
            else assertInstanceOf(PersonalGoldFrame.Unavailable.class,received.frame());
            assertEquals(1,fixture.source.writes);assertTrue(fixture.actual.latestObservedSnapshot().isEmpty());
            assertThrows(IOException.class,()->org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec.decodeOutcome(ack),
                    "a nested Core DTO cannot turn the personal-gold occurrence into a Core control receipt");
            fixture.actual.close();assertThrows(IOException.class,()->received.requireOriginal(fixture.actual,received.validUntil()));
        }
    }

    @Test void absentV2CapabilityWrongBuildAndWrongAdapterCannotSendOrFallBackToV1()throws Exception {
        for(String variant:List.of("missing-capability","only-v1-capability","wrong-version","old-sha","wrong-adapter")){
            var changed=hello();
            switch(variant){
                case "missing-capability"->changed.putArray("capabilities");
                case "only-v1-capability"->changed.putArray("capabilities").add(PersonalGoldFrame.CAPABILITY);
                case "wrong-version"->changed.put("expected_ck3_version","1.21.0");
                case "old-sha"->changed.put("expected_ck3_sha256",ExactCk3Build.CK3_1210.executableSha256());
                case "wrong-adapter"->changed.put("game_adapter_id",PersonalGoldFrame.ADAPTER);
                default->throw new AssertionError(variant);
            }
            try(var fixture=new Fixture(original(INPUTS.getFirst()),changed)){
                var unavailable=assertInstanceOf(NativeGameTransport.PersonalGoldReadUnavailable.class,fixture.actual.readPersonalGoldFrameReceived(fixture.deadline));
                assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,unavailable.original());assertEquals(0,fixture.source.writes,variant);
            }
        }
    }

    @Test void malformedReturnedAmountOrCoreContextPreservesTheOriginalAckAndNeverRetries()throws Exception {
        for(String variant:List.of("number-raw","unpaused","foreign-core","v1-step")){
            var envelope=NativeWire.object(NativeWire.parse(original(INPUTS.getFirst())));var row=NativeWire.object(envelope.get("result"));
            switch(variant){
                case "number-raw"->((ObjectNode)row.get("personal_gold")).put("raw",-12345);
                case "unpaused"->((ObjectNode)row.get("core_frame")).put("paused",false);
                case "foreign-core"->((ObjectNode)row.get("core_frame")).put("game_version","1.21.0");
                case "v1-step"->row.put("step",PersonalGoldFrame.STEP);
                default->throw new AssertionError(variant);
            }
            try(var fixture=new Fixture(StrictJson.canonical(envelope),hello())){
                var unavailable=assertInstanceOf(NativeGameTransport.PersonalGoldReadUnavailable.class,fixture.actual.readPersonalGoldFrameReceived(fixture.deadline));
                var ack=assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.original());assertTrue(ack.custody().isPresent());
                assertEquals(1,fixture.source.writes,variant);assertTrue(fixture.actual.latestObservedSnapshot().isEmpty());
            }
        }
    }
    private static final class Fixture implements AutoCloseable {
        final Replay source;final NativeGameTransport actual;final Instant deadline=Instant.now().plusSeconds(120);
        Fixture(byte[] cpp,ObjectNode hello)throws IOException {source=new Replay(cpp,hello);actual=new NativeGameTransport(source,config(),16,8,List.of());}
        @Override public void close()throws IOException {actual.close();}
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();final byte[] token;byte[] request;int writes;boolean closed;
        Replay(byte[] cpp,ObjectNode hello)throws IOException {
            var result=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(cpp)));token=result.result().token().orElseThrow().value();
            packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        @Override public void verify()throws IOException {if(closed)throw new IOException("software source closed");}
        @Override public void awaitConnection(Instant until)throws IOException {verify();}
        @Override public byte[] readPacket(Instant until)throws IOException {verify();if(packets.isEmpty())throw new IOException("no unsolicited software frame");return packets.removeFirst();}
        @Override public void writePacket(byte[] packet,Instant until)throws IOException {
            verify();var decoded=NativeWire.decodeExecuteRequest(packet);writes++;assertEquals(VERSION.step(),decoded.step());
            assertEquals(Optional.of(BigInteger.ZERO),decoded.expectedRevision());assertTrue(decoded.expectedSnapshotRevision().isEmpty());
            assertEquals(0,NativeWire.object(NativeWire.parse(decoded.normalizedAdditionalFields().value())).size());request=packet.clone();
            var output=new ByteArrayOutputStream();
            output.writeBytes(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+decoded.requestId()+"\",\"ok\":true,\"result\":").getBytes(StandardCharsets.UTF_8));
            // Software correlation only: preserve the genuine C++ result token byte for byte.
            output.writeBytes(token);output.write('}');packets.add(NativeWire.packet(output.toByteArray()));
        }
        @Override public void close(){closed=true;}
    }
}
