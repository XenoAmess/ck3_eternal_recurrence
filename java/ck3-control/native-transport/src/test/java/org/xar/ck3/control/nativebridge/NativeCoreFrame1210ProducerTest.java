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
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.HexFormat;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** Actual C++ payload bytes through the Java receiver over software packets. No Game/Native-process oracle or control admission. */
final class NativeCoreFrame1210ProducerTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_1210;
    private static final String ADAPTER="ck3-1.21.0-msvc-x64",BRIDGE="software-core1210";
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));

    private static byte[] payload(String name,int bytes,String sha)throws Exception {
        String root=System.getProperty("xar.native.core1210.fixtures");
        byte[] original;
        if(root==null||root.isBlank()) {
            try(var input=NativeCoreFrame1210ProducerTest.class.getResourceAsStream("/native1210/"+name)) {
                if(input==null)throw new IOException("exact C++ producer test resource missing: "+name);
                original=input.readNBytes(bytes+1);
            }
        } else {
            if(!Path.of(root).isAbsolute())throw new IOException("exact absolute xar.native.core1210.fixtures required");
            original=Files.readAllBytes(Path.of(root).resolve(name));
        }
        assertEquals(bytes,original.length);assertEquals(sha,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        return original;
    }
    private static byte[] partial()throws Exception {
        return payload("core-producer-partial.json",599,"1d7df534e64680a88b4a40665b175c15b1928c47f0cdd0c5058ef381063d9ec6");
    }
    private static byte[] unavailable()throws Exception {
        return payload("core-producer-unavailable.json",620,"4a1c50df66540be46f59d210ae53eaf318ae0f7089b3663a6eed0cd4bdf2c38d");
    }
    private static Instant deadline(){return Instant.now().plusSeconds(20);}
    private static NativePipeEndpoint.Config config(){
        return new NativePipeEndpoint.Config("\\\\.\\pipe\\core1210-software","core1210-software",GAME,"core1210-session",BRIDGE,BUILD.executableSha256(),ADAPTER);
    }
    private static ObjectNode hello(){
        var row=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",1)
                .put("bridge_version",BRIDGE).put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256())
                .put("game_adapter_id",ADAPTER).put("game_adapter_status","ready").put("ck3_build_match",true);
        row.putArray("capabilities").add(CoreFrame.CAPABILITY);return row;
    }
    private static NativeGameTransport transport(Replay source){return new NativeGameTransport(source,config(),16,2);}
    private static NativeGameTransport.CoreReceived received(NativeGameTransport transport)throws InterruptedException {
        return assertInstanceOf(NativeGameTransport.CoreReceived.class,transport.readCoreFrameReceived(deadline()));
    }
    private static void original(NativeGameTransport.CoreReceived received,NativeGameTransport transport,Replay source)throws Exception {
        assertEquals(1,source.writes);assertEquals(1,source.helloReads);assertEquals(0,source.fullStateWrites);
        var ack=received.original();assertTrue(ack.nativeOk());assertEquals(source.requestId,ack.requestId());
        assertArrayEquals(source.result,ack.originalResultToken().orElseThrow().bytes());
        assertArrayEquals(source.response,ack.originalPacket());assertArrayEquals(source.request,ack.outbound().orElseThrow().originalPacket());
        var custody=ack.custody().orElseThrow();custody.verify(ack);
        assertEquals(transport.awaitHello(received.validUntil()),custody.session());
        assertTrue(custody.writeEntered().order().compareTo(custody.responseReceived().order())<0);
        assertFalse(custody.responseReceived().observedAt().isAfter(received.validUntil()));
        received.requireOriginal(transport,received.validUntil());assertTrue(transport.latestObservedSnapshot().isEmpty());
    }

    @Test void originalCppPartialReachesTypedReceiverWithOneCoreReadAndNoFullSnapshot()throws Exception {
        byte[] original=partial();var source=new Replay(original,hello());
        try(var actual=transport(source)){
            var received=received(actual);var partial=assertInstanceOf(CoreFrame.Partial.class,received.frame());
            assertEquals(BUILD,partial.build());assertEquals(123456,partial.prefix().dateRaw());assertEquals(5,partial.prefix().speed());
            assertTrue(partial.prefix().paused());assertEquals(7,partial.prefix().localPlayerId());assertTrue(partial.prefix().mapReady());
            assertTrue(partial.prefix().hasPlayedCharacter());assertEquals(16777217,partial.prefix().playedCharacterId());assertTrue(partial.prefix().playedCharacterAlive());
            original(received,actual,source);assertArrayEquals(original,source.result);
        }
    }

    @Test void originalCppUnavailableRemainsTypedUnavailableDataWithItsActualPositiveAck()throws Exception {
        byte[] original=unavailable();var source=new Replay(original,hello());
        try(var actual=transport(source)){
            var received=received(actual);var unavailable=assertInstanceOf(CoreFrame.Unavailable.class,received.frame());
            assertEquals(BUILD,unavailable.build());assertTrue(unavailable.applicationMainObserved());assertEquals("core_frame_changed",unavailable.reason());
            original(received,actual,source);assertArrayEquals(original,source.result);
        }
    }

    @Test void missingCapabilityAndEveryMixedExactTupleRefuseBeforeAnyRequestWrite()throws Exception {
        for(String changed:new String[]{"capability","version","hash","adapter"}){
            var advertised=hello();
            switch(changed){
                case "capability"->advertised.putArray("capabilities");
                case "version"->advertised.put("expected_ck3_version",ExactCk3Build.CK3_12004.version());
                case "hash"->advertised.put("expected_ck3_sha256",ExactCk3Build.CK3_12004.executableSha256());
                case "adapter"->advertised.put("game_adapter_id","ck3-1.20.0.4-msvc-x64");
                default->throw new AssertionError(changed);
            }
            var source=new Replay(partial(),advertised);
            try(var actual=transport(source)){
                var refused=assertInstanceOf(NativeGameTransport.CoreReadUnavailable.class,actual.readCoreFrameReceived(deadline()),changed);
                assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,refused.original());
                assertFalse(refused.reason().isBlank());assertEquals(0,source.writes,changed);assertEquals(0,source.fullStateWrites);
            }
        }
    }

    @Test void completeOldFourPayloadCannotBorrowTheFlorinHelloAndItsAckIsNeverRelabelledZero()throws Exception {
        var nativePrefix=assertInstanceOf(CoreFrame.Partial.class,CoreFrame.decode(new RawJson(partial()))).prefix();
        // Deliberate negative from the genuine old Java codec, not a claim of a new C++ producer observation.
        byte[] old=CoreFramePublicCodec.encode(new CoreFrame.Partial(ExactCk3Build.CK3_12004,nativePrefix)).bytes();
        assertEquals(ExactCk3Build.CK3_12004,CoreFrame.decode(new RawJson(old)).build());
        var source=new Replay(old,hello());
        try(var actual=transport(source)){
            var unavailable=assertInstanceOf(NativeGameTransport.CoreReadUnavailable.class,actual.readCoreFrameReceived(deadline()));
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.original());
            assertTrue(ack.nativeOk());ack.custody().orElseThrow().verify(ack);assertArrayEquals(old,ack.originalResultToken().orElseThrow().bytes());
            assertFalse(unavailable.reason().isBlank());assertEquals(1,source.writes);assertEquals(0,source.fullStateWrites);
        }
    }

    @Test void sameSessionForeignIssuerAndDeadlineExtensionCannotUseThePrivateReceivedRole()throws Exception {
        var first=new Replay(partial(),hello());var second=new Replay(partial(),hello());
        try(var actual=transport(first);var foreign=transport(second)){
            var received=received(actual);assertEquals(actual.awaitHello(received.validUntil()),foreign.awaitHello(received.validUntil()));
            assertThrows(IOException.class,()->received.requireOriginal(foreign,received.validUntil()));
            assertThrows(IOException.class,()->received.requireOriginal(actual,received.validUntil().plusNanos(1)));
            original(received,actual,first);assertEquals(0,second.writes);
        }
    }

    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();final byte[] result;int writes,helloReads,fullStateWrites;
        boolean closed;String requestId;byte[] request,response;
        Replay(byte[] actualCppPayload,ObjectNode hello)throws IOException {
            result=actualCppPayload.clone();packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        public void verify()throws IOException {if(closed)throw new IOException("software source closed");}
        public void awaitConnection(Instant until)throws IOException {check(until);}
        private void check(Instant until)throws IOException {verify();if(!Instant.now().isBefore(until))throw new IOException("actual software operation deadline expired");}
        public byte[] readPacket(Instant until)throws IOException {
            check(until);if(packets.isEmpty())throw new IOException("software source has no packet; no unsolicited full snapshot");
            byte[] packet=packets.removeFirst();if(NativeWire.decode(packet) instanceof NativeWire.Hello)helloReads++;return packet;
        }
        public void writePacket(byte[] original,Instant until)throws IOException {
            check(until);var decoded=NativeWire.decodeExecuteRequest(original);
            if(decoded.step().equals(NativeFreshSnapshotPort.STEP))fullStateWrites++;
            assertEquals(CoreFrame.STEP,decoded.step());assertEquals(Optional.of(BigInteger.ZERO),decoded.expectedRevision());
            assertTrue(decoded.expectedSnapshotRevision().isEmpty());assertEquals(0,NativeWire.object(NativeWire.parse(decoded.normalizedAdditionalFields().value())).size());
            assertTrue(decoded.requestId().matches("[A-Za-z0-9_-]+"));writes++;requestId=decoded.requestId();request=original.clone();
            var output=new ByteArrayOutputStream();
            output.writeBytes(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+requestId+"\",\"ok\":true,\"result\":").getBytes(StandardCharsets.UTF_8));
            output.writeBytes(result);output.write('}');response=NativeWire.packet(output.toByteArray());packets.add(response.clone());
        }
        public void close(){closed=true;}
    }
}
