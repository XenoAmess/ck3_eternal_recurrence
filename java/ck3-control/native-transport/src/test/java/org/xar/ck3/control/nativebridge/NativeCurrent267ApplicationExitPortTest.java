package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** Dedicated current quit ABI DATA/real transport custody only. No requested ACK is a natural process exit. */
final class NativeCurrent267ApplicationExitPortTest {
    private static final String ROOT="/newnative/application-exit26785313-v1/";
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(999)));
    private static byte[] resource(String name)throws Exception {
        byte[] content;
        try(var input=NativeCurrent267ApplicationExitPortTest.class.getResourceAsStream(ROOT+name)) {
            if(input==null)throw new IOException("actual C++ current267 producer resource required: "+name);
            content=input.readNBytes(16385);assertTrue(content.length<=16384);
        }
        JsonNode pins;
        try(var input=NativeCurrent267ApplicationExitPortTest.class.getResourceAsStream(ROOT+"producer-pins.json")) {
            if(input==null)throw new IOException("current267 actual producer pins required");pins=StrictJson.parse(input.readNBytes(16384));
        }
        var expected=pins.get(name);assertNotNull(expected);assertEquals(expected.get("bytes").intValue(),content.length);
        assertEquals(expected.get("sha256").textValue(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(content)));return content;
    }
    private static CoreFrame.Partial partial()throws Exception {
        var request=NativeWire.decodeExecuteRequest(NativeWire.packet(resource("request-current267.json")));
        assertEquals(CoreApplicationExit.STEP,request.step());var row=NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));
        var claim=NativeWire.object(row.get("core_application_exit"));
        return new CoreFrame.Partial(BUILD,new CoreFrame.Prefix(integer(claim,"date_raw"),integer(claim,"speed"),bool(claim,"paused"),
                integer(claim,"local_player_id"),bool(claim,"map_ready"),bool(claim,"has_played_character"),integer(claim,"played_character_id"),bool(claim,"played_character_alive")));
    }
    private static int integer(JsonNode row,String key){return Math.toIntExact(StrictJson.integer(row.get(key),Integer.MIN_VALUE,Integer.MAX_VALUE));}
    private static boolean bool(JsonNode row,String key){var value=row.get(key);StrictJson.require(value!=null&&value.isBoolean(),"boolean required: "+key);return value.booleanValue();}
    private static ObjectNode reply(String name)throws Exception {
        var envelope=NativeWire.object(NativeWire.parse(resource(name)));return (ObjectNode)envelope.get("result");
    }
    private static NativePipeEndpoint.Config config(){return new NativePipeEndpoint.Config("\\\\.\\pipe\\current-quit-DATA","current-quit-data",GAME,"current-quit-session","current-quit-bridge",BUILD.executableSha256(),BUILD.coreFrameAdapterId());}
    private static NativeGameTransport transport(Port source){return new NativeGameTransport(source,config(),16,4);}
    @Test void requestMatchesActualCppCurrentClaimWithoutWideningAnyClockOrSaveClaim()throws Exception {
        var frame=partial();var request=CoreApplicationExit.request(frame);var fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));
        assertEquals(Set.of("core_application_exit"),fields.properties().stream().map(java.util.Map.Entry::getKey).collect(java.util.stream.Collectors.toSet()));
        var claim=NativeWire.object(fields.get("core_application_exit"));
        assertEquals(13,claim.size());assertEquals(CoreApplicationExit.SCHEMA,claim.path("schema").textValue());
        assertTrue(BUILD.matches(claim.path("game_version").textValue(),claim.path("executable_sha256").textValue()));
        assertEquals(BUILD.coreFrameAdapterId(),claim.path("adapter_id").textValue());assertEquals("ck3-1.21.0.3-native-headless-main-thread",claim.path("backend").textValue());
        var cpp=NativeWire.object(NativeWire.parse(NativeWire.decodeExecuteRequest(NativeWire.packet(resource("request-current267.json"))).normalizedAdditionalFields().value()));
        var expected=NativeWire.object(cpp.get("core_application_exit"));expected.put("executable_sha256",claim.path("executable_sha256").textValue());assertEquals(expected,claim);
        for(var step:CoreClockControl.Step.values())assertThrows(IllegalArgumentException.class,()->CoreClockControl.request(step,frame));
        assertThrows(IllegalStateException.class,BUILD::coreFullAdapterId);
        var legacy=CoreApplicationExit.request(new CoreFrame.Partial(ExactCk3Build.CK3_1210,frame.prefix()));
        assertEquals("ck3-1.21.0-native-headless-main-thread",StrictJson.parse(legacy.additionalFields().bytes()).path("core_application_exit").path("backend").textValue());
    }
    @Test void originalPrivateCurrentCoreAllowsOneExitWriteButNoExitEffectOrSaveClaim()throws Exception {
        var source=new Port(partial(),true,reply("requested-SYNTHETIC-DATA.json"));
        try(var actual=transport(source)) {
            var before=assertInstanceOf(NativeGameTransport.CoreReceived.class,actual.readCoreFrameReceived(Instant.now().plusSeconds(30)));
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,actual.submitCoreNormalExit(before,before.validUntil()));
            assertEquals(1,source.exitWrites);ack.custody().orElseThrow().verify(ack);assertArrayEquals(source.exitPacket,ack.outbound().orElseThrow().originalPacket());
            var body=StrictJson.parse(ack.originalResultToken().orElseThrow().bytes());assertEquals("requested",body.path("dispatch_status").textValue());
            assertFalse(body.path("normal_exit_confirmed").booleanValue());assertFalse(body.path("physical_save_confirmed").booleanValue());assertFalse(body.path("complete_snapshot").booleanValue());
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,actual.submitCoreNormalExit(before,before.validUntil()));assertEquals(1,source.exitWrites);
            assertTrue(actual.latestObservedSnapshot().isEmpty());
        }
    }
    @Test void missingCapabilityForeignIssuerBadPausedCoreAndDeadlineExtensionNeverWriteExit()throws Exception {
        var source=new Port(partial(),false,reply("requested-SYNTHETIC-DATA.json"));
        try(var actual=transport(source)) {
            var before=assertInstanceOf(NativeGameTransport.CoreReceived.class,actual.readCoreFrameReceived(Instant.now().plusSeconds(30)));
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,actual.submitCoreNormalExit(before,before.validUntil()));assertEquals(0,source.exitWrites);
        }
        var ownerPort=new Port(partial(),true,reply("requested-SYNTHETIC-DATA.json"));var foreignPort=new Port(partial(),true,reply("requested-SYNTHETIC-DATA.json"));
        try(var owner=transport(ownerPort);var foreign=transport(foreignPort)) {
            var before=assertInstanceOf(NativeGameTransport.CoreReceived.class,owner.readCoreFrameReceived(Instant.now().plusSeconds(30)));
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,foreign.submitCoreNormalExit(before,before.validUntil()));assertEquals(0,foreignPort.exitWrites);
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,owner.submitCoreNormalExit(before,before.validUntil().plusNanos(1)));assertEquals(0,ownerPort.exitWrites);
        }
        var prefix=partial().prefix();assertThrows(IllegalArgumentException.class,()->CoreApplicationExit.request(new CoreFrame.Partial(BUILD,
                new CoreFrame.Prefix(prefix.dateRaw(),prefix.speed(),false,prefix.localPlayerId(),true,true,prefix.playedCharacterId(),true))));
    }
    @Test void actualCppIndeterminateAckAndMissingReplyKeepOriginalUnknownWithoutReplay()throws Exception {
        for(boolean missing:List.of(false,true)) {
            var source=new Port(partial(),true,reply("indeterminate-SYNTHETIC-DATA.json"));source.dropReply=missing;
            try(var actual=transport(source)) {
                var before=assertInstanceOf(NativeGameTransport.CoreReceived.class,actual.readCoreFrameReceived(Instant.now().plusSeconds(30)));
                var unknown=assertInstanceOf(NativeActionPort.Unknown.class,actual.submitCoreNormalExit(before,before.validUntil()));
                assertArrayEquals(source.exitPacket,unknown.originalRequestPacket());assertEquals(1,source.exitWrites);
                if(!missing){var ack=actual.originalIndeterminateCoreAcknowledgement(unknown.requestId()).orElseThrow();assertFalse(ack.nativeOk());ack.custody().orElseThrow().verify(ack);}
                assertSame(unknown,actual.submitCoreNormalExit(before,before.validUntil()));
                assertSame(unknown,actual.submitCoreClockControl(before,CoreClockControl.Step.PAUSE_MAP,before.validUntil()));assertEquals(1,source.exitWrites);
            }
        }
    }
    @Test void actualCppNoGameRefusalRemainsOriginalNegativeAckAndNeverAnExitReceipt()throws Exception {
        var source=new Port(partial(),true,reply("unavailable-NoGame.json"));
        try(var actual=transport(source)) {
            var before=assertInstanceOf(NativeGameTransport.CoreReceived.class,actual.readCoreFrameReceived(Instant.now().plusSeconds(30)));
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,actual.submitCoreNormalExit(before,before.validUntil()));
            assertFalse(ack.nativeOk());ack.custody().orElseThrow().verify(ack);
            var body=StrictJson.parse(ack.originalResultToken().orElseThrow().bytes());
            assertEquals("unavailable",body.path("dispatch_status").textValue());assertFalse(body.path("accepted").booleanValue());
            assertFalse(body.path("effect_attempted").booleanValue());assertFalse(body.path("normal_exit_confirmed").booleanValue());
            assertEquals(1,source.exitWrites);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,actual.submitCoreNormalExit(before,before.validUntil()));
            assertEquals(1,source.exitWrites);assertTrue(actual.latestObservedSnapshot().isEmpty());
        }
    }
    private static final class Port implements NativePacketPort {
        final ArrayDeque<byte[]> incoming=new ArrayDeque<>();final CoreFrame.Partial core;final ObjectNode result;
        boolean closed,dropReply;int exitWrites;byte[] exitPacket;
        Port(CoreFrame.Partial core,boolean capability,ObjectNode result)throws IOException {
            this.core=core;this.result=result;
            var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",7)
                    .put("bridge_version","current-quit-bridge").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256())
                    .put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=hello.putArray("capabilities").add(CoreFrame.CAPABILITY);if(capability)caps.add(CoreApplicationExit.CAPABILITY);
            incoming.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("authored source closed");}
        public void verifyCoreControlWindowPolicy(){ /* Authored source: no real window claim. */ }
        public void awaitConnection(Instant deadline)throws IOException{verify();}
        public byte[] readPacket(Instant deadline)throws IOException{verify();if(incoming.isEmpty())throw new IOException("authored missing reply");return incoming.removeFirst();}
        public void writePacket(byte[] packet,Instant deadline)throws IOException {
            verify();var request=NativeWire.decodeExecuteRequest(packet);ObjectNode response;
            if(request.step().equals(CoreFrame.STEP))response=NativeWire.object(NativeWire.parse(CoreFramePublicCodec.encode(core).bytes()));
            else {
                assertEquals(CoreApplicationExit.STEP,request.step());assertEquals(Optional.of(BigInteger.ZERO),request.expectedRevision());
                assertTrue(request.expectedSnapshotRevision().isEmpty());var fields=NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));
                assertEquals(2,fields.size());assertTrue(fields.get("core_control_deadline_unix_ms").isIntegralNumber());assertEquals(deadline.toEpochMilli(),fields.get("core_control_deadline_unix_ms").longValue());
                assertEquals(StrictJson.parse(CoreApplicationExit.request(core).additionalFields().bytes()).get("core_application_exit"),fields.get("core_application_exit"));
                exitWrites++;exitPacket=packet.clone();if(dropReply)return;response=result;
            }
            boolean accepted=!response.has("accepted")||response.get("accepted").booleanValue();
            var envelope=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",accepted);envelope.set("result",response);
            incoming.add(NativeWire.packet(StrictJson.canonical(envelope)));
        }
        public void close(){closed=true;}
    }
}
