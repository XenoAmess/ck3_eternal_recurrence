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

/** Exact wire DATA, byte-checked against the C++ formatter by the Native CI fixture; real Java transport/custody, no live Game credit. */
final class NativeCoreFrame26785313ProducerTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final String ADAPTER="ck3-1.21.0.3-26785313-msvc-x64",BRIDGE="software-core26785313";
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));

    private static byte[] payload(String name,int bytes,String sha)throws Exception {
        String root=System.getProperty("xar.native.core26785313.fixtures");
        byte[] original;
        if(root==null||root.isBlank()) {
            try(var input=NativeCoreFrame26785313ProducerTest.class.getResourceAsStream("/native26785313/"+name)) {
                if(input==null)throw new IOException("exact C++ producer test resource missing: "+name);
                original=input.readNBytes(bytes+1);
            }
        } else {
            if(!Path.of(root).isAbsolute())throw new IOException("exact absolute xar.native.core26785313.fixtures required");
            original=Files.readAllBytes(Path.of(root).resolve(name));
        }
        assertEquals(bytes,original.length);assertEquals(sha,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        return original;
    }
    private static byte[] partial()throws Exception {
        return payload("core-producer-partial.json",614,"e1b7c3837652dd8e619d5d58dc94d6775bf803715d926362906e4b2cf92d879d");
    }
    private static byte[] unavailable()throws Exception {
        return payload("core-producer-unavailable.json",635,"907b2075af91baa2b5e44684f90fe8244d1cf2b91256c9111130b179e004e0f1");
    }
    private static Instant deadline(){return Instant.now().plusSeconds(20);}
    private static NativePipeEndpoint.Config config(){
        return new NativePipeEndpoint.Config("\\\\.\\pipe\\core26785313-software","core26785313-software",GAME,"core26785313-session",BRIDGE,BUILD.executableSha256(),ADAPTER);
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

    @Test void coreOnlySourceCannotBuyFullClockSaveExitGuiOrFinancialQualification()throws Exception {
        assertTrue(ExactCk3Build.florinCoreFrameBuild(BUILD.version(),BUILD.executableSha256()).isPresent());
        assertTrue(ExactCk3Build.florinCoreFullBuild(BUILD.version(),BUILD.executableSha256()).isEmpty());
        assertThrows(IllegalStateException.class,BUILD::coreFullAdapterId);
        assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.Build.require(BUILD.version(),BUILD.executableSha256()));
        var advertised=hello();
        advertised.withArray("capabilities").add("game.state.snapshot").add(NativeFreshSnapshotPort.CAPABILITY)
                .add(CoreApplicationExit.CAPABILITY).add("game.query.personal-gold.v1");
        for(var step:CoreClockControl.Step.values())advertised.withArray("capabilities").add(step.requiredCapability());
        var source=new Replay(partial(),advertised);
        try(var actual=transport(source)) {
            var first=received(actual);var frame=assertInstanceOf(CoreFrame.Partial.class,first.frame());
            for(var step:CoreClockControl.Step.values()) {
                assertThrows(IllegalArgumentException.class,()->CoreClockControl.request(step,frame));
                assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,actual.submitCoreClockControl(first,step,first.validUntil()));
            }
            assertThrows(IllegalArgumentException.class,()->CoreApplicationExit.request(frame));
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,actual.submitCoreNormalExit(first,first.validUntil()));
            var full=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,actual.readFreshFullState(deadline()));
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,full.dispatch());
            assertTrue(actual.latestObservedSnapshot().isEmpty());assertEquals(1,source.writes);assertEquals(0,source.fullStateWrites);
            first.requireOriginal(actual,first.validUntil());
        }
    }

    @Test void legacyFlorinAndBb3PacketsCannotBorrowNewHelloAndNoPositiveAckIsRewritten()throws Exception {
        var prefix=assertInstanceOf(CoreFrame.Partial.class,CoreFrame.decode(new RawJson(partial()))).prefix();
        for(var old:java.util.List.of(ExactCk3Build.CK3_1210,ExactCk3Build.CK3_1210_STEAM_26757580)) {
            byte[] bytes=CoreFramePublicCodec.encode(new CoreFrame.Partial(old,prefix)).bytes();
            var source=new Replay(bytes,hello());
            try(var actual=transport(source)) {
                var refused=assertInstanceOf(NativeGameTransport.CoreReadUnavailable.class,actual.readCoreFrameReceived(deadline()));
                var ack=assertInstanceOf(NativeActionPort.AckReceived.class,refused.original());
                assertTrue(ack.nativeOk());assertArrayEquals(bytes,ack.originalResultToken().orElseThrow().bytes());
                assertEquals(1,source.writes);assertEquals(0,source.fullStateWrites);
            }
        }
    }

    @Test void actualPublicRegistryConsumesOnlyTheSameReceivedCoreAndPreservesCrossTupleAck()throws Exception {
        for(var sourceBuild:java.util.List.of(BUILD,ExactCk3Build.CK3_1210,ExactCk3Build.CK3_1210_STEAM_26757580)) {
            var prefix=assertInstanceOf(CoreFrame.Partial.class,CoreFrame.decode(new RawJson(partial()))).prefix();
            byte[] payload=sourceBuild==BUILD?partial():CoreFramePublicCodec.encode(new CoreFrame.Partial(sourceBuild,prefix)).bytes();
            var source=new Replay(payload,hello());
            try(var actual=transport(source)) {
                var registry=new org.xar.ck3.control.nativebridge.capabilities.registry.RegistryCore(actual,
                        new org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes());
                var read=registry.query_core_frame_v1(new org.xar.ck3.control.nativebridge.capabilities.registry.RegistryCore.CoreRequest(deadline()));
                NativeActionPort.AckReceived ack;
                if(sourceBuild==BUILD) {
                    var known=assertInstanceOf(org.xar.ck3.control.nativebridge.capabilities.registry.RegistryCore.CoreKnown.class,read);
                    assertEquals(BUILD,known.frame().build());ack=known.original();
                } else {
                    var refused=assertInstanceOf(org.xar.ck3.control.nativebridge.capabilities.registry.RegistryCore.CoreUnavailable.class,read);
                    ack=assertInstanceOf(NativeActionPort.AckReceived.class,refused.original());
                }
                assertTrue(ack.nativeOk());assertArrayEquals(payload,ack.originalResultToken().orElseThrow().bytes());
                ack.custody().orElseThrow().verify(ack);assertEquals(1,source.writes);assertEquals(0,source.fullStateWrites);
            }
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
