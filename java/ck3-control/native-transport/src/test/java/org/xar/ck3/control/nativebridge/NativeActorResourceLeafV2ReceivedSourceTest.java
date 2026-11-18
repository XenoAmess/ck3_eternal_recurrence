package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayDeque;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.ActorResourceLeafV2;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** Actual transport state machine with pinned C++ formatter tokens and software packet port; no Game/live role. */
final class NativeActorResourceLeafV2ReceivedSourceTest {
    static final String BRIDGE="software-resource-leaf-v2";
    static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    static byte[] originalToken()throws Exception {
        String file=System.getProperty("xar.resource.leaf.v2.partial.file"),sha=System.getProperty("xar.resource.leaf.v2.partial.sha256");
        assertNotNull(file,"NOT_RUN: actual C++ partial original path required");assertNotNull(sha,"actual original SHA required");
        assertTrue(Path.of(file).isAbsolute());assertTrue(sha.matches("[0-9A-Fa-f]{64}"));byte[] bytes=Files.readAllBytes(Path.of(file));
        assertEquals(sha.toLowerCase(Locale.ROOT),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        return assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(bytes))).result().token().orElseThrow().value();
    }
    @Test void realReceiverOccurrenceRetainsOriginalBytesIssuerWindowAndReadonlyRole()throws Exception {
        byte[] token=originalToken();
        try(var owner=new Fixture(token,true,false);var foreign=new Fixture(token,true,false)){
            var received=assertInstanceOf(NativeGameTransport.ActorResourceLeafReceivedV2.class,
                    owner.actual.readActorResourceLeafFrameReceivedV2(owner.deadline));
            var p=assertInstanceOf(ActorResourceLeafV2.Partial.class,received.frame());
            assertEquals(Long.MIN_VALUE,p.observedNonCash().orElseThrow().prestige().raw());
            assertArrayEquals(token,received.original().originalResultToken().orElseThrow().bytes());
            assertArrayEquals(owner.source.request,received.original().outbound().orElseThrow().originalPacket());
            assertArrayEquals(owner.source.response,received.original().originalPacket());
            assertEquals(1,owner.source.writes);assertEquals(0,foreign.source.writes);assertTrue(owner.actual.latestObservedSnapshot().isEmpty());
            received.requireOriginal(owner.actual,received.validUntil());
            assertThrows(IOException.class,()->received.requireOriginal(foreign.actual,received.validUntil()));
            assertThrows(IOException.class,()->received.requireOriginal(owner.actual,received.validUntil().plusNanos(1)));
            assertThrows(IOException.class,()->CoreFramePublicCodec.decodeOutcome(received.original()));
            Object role=received;assertFalse(role instanceof NativeGameTransport.CoreRead);assertFalse(role instanceof NativeFreshSnapshotPort.Result);
            owner.clock.now=received.validUntil();
            assertThrows(IOException.class,()->received.requireOriginal(owner.actual,received.validUntil()));
            assertEquals(1,owner.source.writes);
        }
    }
    @Test void capabilityZeroWriteAndAfterWriteUnknownKeepDistinctOriginalEvidence()throws Exception {
        byte[] token=originalToken();
        try(var missing=new Fixture(token,false,false)){
            var result=assertInstanceOf(NativeGameTransport.ActorResourceLeafReadUnavailableV2.class,
                    missing.actual.readActorResourceLeafFrameReceivedV2(missing.deadline));
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,result.original());assertEquals(0,missing.source.writes);
        }
        try(var lost=new Fixture(token,true,true)){
            var result=assertInstanceOf(NativeGameTransport.ActorResourceLeafReadUnavailableV2.class,
                    lost.actual.readActorResourceLeafFrameReceivedV2(lost.deadline));
            assertInstanceOf(NativeActionPort.Unknown.class,result.original());assertEquals(1,lost.source.writes);
            assertNotNull(lost.source.request);assertTrue(lost.actual.latestObservedSnapshot().isEmpty());
        }
    }
    static final class MutableClock extends Clock {
        Instant now=Instant.now();
        @Override public Instant instant(){return now;}
        @Override public ZoneId getZone(){return ZoneOffset.UTC;}
        @Override public Clock withZone(ZoneId zone){if(!zone.equals(ZoneOffset.UTC))throw new IllegalArgumentException("UTC fixture");return this;}
    }
    static final class Fixture implements AutoCloseable {
        final MutableClock clock=new MutableClock();final Instant deadline=clock.instant().plusSeconds(120);
        final Replay source;final NativeGameTransport actual;
        Fixture(byte[] token,boolean capability,boolean loseResponse)throws IOException {
            source=new Replay(token,capability,loseResponse,clock);
            String slash=Character.toString((char)92);
            var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"resource-leaf-software","resource-leaf-software",
                    GAME,"resource-leaf-session",BRIDGE,ExactCk3Build.CK3_1210.executableSha256(),ActorResourceLeafV2.ADAPTER);
            actual=new NativeGameTransport(source,config,16,8,List.of(),clock);
        }
        @Override public void close()throws IOException{actual.close();}
    }
    static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();final byte[] result;final boolean loseResponse;final MutableClock clock;
        int writes;boolean closed;byte[] request,response;
        Replay(byte[] token,boolean capability,boolean loseResponse,MutableClock clock)throws IOException {
            result=token.clone();this.loseResponse=loseResponse;this.clock=clock;
            ObjectNode hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid())
                    .put("connection_generation",1).put("bridge_version",BRIDGE).put("expected_ck3_version",ExactCk3Build.CK3_1210.version())
                    .put("expected_ck3_sha256",ExactCk3Build.CK3_1210.executableSha256()).put("game_adapter_id",ActorResourceLeafV2.ADAPTER)
                    .put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=hello.putArray("capabilities");if(capability)caps.add(ActorResourceLeafV2.CAPABILITY);
            packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        @Override public void verify()throws IOException{if(closed)throw new IOException("software source closed");}
        void check(Instant until)throws IOException{verify();if(!clock.instant().isBefore(until))throw new IOException("software deadline expired");}
        @Override public void awaitConnection(Instant until)throws IOException{check(until);}
        @Override public byte[] readPacket(Instant until)throws IOException{
            check(until);if(packets.isEmpty())throw new IOException("actual software response lost after write");return packets.removeFirst();
        }
        @Override public void writePacket(byte[] original,Instant until)throws IOException{
            check(until);var decoded=NativeWire.decodeExecuteRequest(original);writes++;request=original.clone();
            assertEquals(ActorResourceLeafV2.STEP,decoded.step());assertEquals(Optional.of(BigInteger.ZERO),decoded.expectedRevision());
            assertTrue(decoded.expectedSnapshotRevision().isEmpty());
            assertTrue(NativeWire.object(NativeWire.parse(decoded.normalizedAdditionalFields().value())).isEmpty());
            if(loseResponse)return;
            var bytes=new ByteArrayOutputStream();
            bytes.writeBytes(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+decoded.requestId()+
                    "\",\"ok\":true,\"result\":").getBytes(StandardCharsets.UTF_8));
            bytes.writeBytes(result);bytes.write('}');response=NativeWire.packet(bytes.toByteArray());packets.add(response.clone());
        }
        @Override public void close(){closed=true;}
    }
}
