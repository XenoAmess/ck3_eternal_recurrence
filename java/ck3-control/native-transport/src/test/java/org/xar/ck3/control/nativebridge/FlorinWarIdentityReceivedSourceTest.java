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
import org.xar.ck3.control.nativebridge.capabilities.registry.FlorinWarIdentityPublicCodec;
import org.xar.ck3.control.contracts.semantic.FlorinWarIdentityCodec;
import org.xar.ck3.control.contracts.semantic.FlorinWarIdentityData;
import org.xar.ck3.control.application.action.ActionCodec;
import com.fasterxml.jackson.databind.JsonNode;
import java.util.Map;
import java.util.TreeMap;

/** Real SDK state machine with original C++21 result tokens and an owned software port. Outer ACK correlation is software DATA, never a Native21 outbound/IPC claim. */
final class FlorinWarIdentityReceivedSourceTest {
    static final String BRIDGE="software-war-identity";
    static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private record Original(byte[] json,byte[] token,FlorinWarIdentityData.Observation decoded) { }
    @Test void allNineOriginalResultsPassThroughTheHeldReceiverWithoutBecomingFullOrControl() throws Exception {
        var originals=originals();assertEquals(9,originals.size());
        for(var entry:originals.entrySet())try(var fixture=new Fixture(entry.getValue().token(),true,false)) {
            var projected=assertInstanceOf(FlorinWarIdentityPublicCodec.PartialFullData.class,
                    fixture.actual.readActiveWarsIdentityProjection(fixture.deadline));
            assertEquals(entry.getValue().decoded(),projected.warData());
            assertArrayEquals(entry.getValue().token(),projected.original().originalResultToken().orElseThrow().bytes());
            assertArrayEquals(fixture.source.request,projected.original().outbound().orElseThrow().originalPacket());
            assertArrayEquals(fixture.source.response,projected.original().originalPacket());
            var chronology=projected.original().custody().orElseThrow();chronology.verify(projected.original());
            assertEquals(chronology,fixture.actual.originalRequestChronology(projected.original().requestId()).orElseThrow());
            assertFalse(projected.completeSnapshot());assertFalse(projected.completeActiveWarsQualified());
            assertTrue(fixture.actual.latestObservedSnapshot().isEmpty());assertEquals(1,fixture.source.writes);
            Object role=projected;assertFalse(role instanceof NativeGameTransport.CoreRead);assertFalse(role instanceof NativeFreshSnapshotPort.Result);
            if(projected.warData() instanceof FlorinWarIdentityData.Partial partial) {
                for(var war:partial.activeWars())assertEquals(6,war.richFields().size());
                if(entry.getKey().equals("war-attacker"))assertEquals(-2080374784,partial.activeWars().getFirst().warId().value());
                if(entry.getKey().equals("war-zero-duplicates"))assertEquals(0,partial.activeWars().getFirst().warId().value());
            } else assertTrue(StrictJson.parse(entry.getValue().json()).path("result").get("active_wars").isNull());
        }
    }
    @Test void missingCapabilityIsZeroDispatchAndLostAfterWriteReplyStaysUnknown() throws Exception {
        byte[] token=originals().get("war-attacker").token();
        try(var missing=new Fixture(token,false,false)) {
            var result=assertInstanceOf(FlorinWarIdentityPublicCodec.UnavailableRead.class,
                    missing.actual.readActiveWarsIdentityProjection(missing.deadline));
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,result.original());assertEquals(0,missing.source.writes);
        }
        try(var lost=new Fixture(token,true,true)) {
            var result=assertInstanceOf(FlorinWarIdentityPublicCodec.UnavailableRead.class,
                    lost.actual.readActiveWarsIdentityProjection(lost.deadline));
            var original=assertInstanceOf(NativeActionPort.Unknown.class,result.original());
            assertArrayEquals(lost.source.request,original.originalRequestPacket());
            assertEquals(1,lost.source.writes);assertTrue(lost.actual.latestObservedSnapshot().isEmpty());
        }
    }
    private static Map<String,Original> originals() throws Exception {
        String configured=System.getProperty("xar.florinWar.cppManifest"),sha=System.getProperty("xar.florinWar.cppManifestSha256");
        assertNotNull(configured,"required actual Native21 manifest");assertNotNull(sha,"required actual manifest SHA");
        Path path=Path.of(configured);assertTrue(path.isAbsolute());byte[] raw=small(path);
        assertEquals(sha,ActionCodec.sha256(raw));JsonNode manifest=StrictJson.parse(raw);assertEquals(0,manifest.path("exit").intValue());
        assertEquals(9,manifest.path("files").size());Map<String,Original> result=new TreeMap<>();
        for(JsonNode row:manifest.path("files")) {
            Path file=Path.of(row.path("path").textValue());assertTrue(file.isAbsolute());byte[] json=small(file);
            assertEquals(row.path("bytes").longValue(),json.length);assertEquals(row.path("sha256").textValue(),ActionCodec.sha256(json));
            var frame=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(json)));assertTrue(frame.nativeOk());
            String name=file.getFileName().toString().replace(".json","");assertEquals(name,frame.requestId());
            var data=FlorinWarIdentityPublicCodec.decodePacket(new org.xar.ck3.control.application.action.RawJson(json),name);
            assertNull(result.put(name,new Original(json,frame.result().token().orElseThrow().value(),data)));
        }
        return Map.copyOf(result);
    }
    private static byte[] small(Path path) throws IOException {
        long size=Files.size(path);if(size<1||size>65536)throw new IOException("bounded actual Native packet/manifest required");
        try(var in=Files.newInputStream(path)) {byte[] raw=in.readNBytes(65537);if(raw.length!=size||raw.length>65536)throw new IOException("captured Native original size changed");return raw;}
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
            var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"war-identity-software","war-identity-software",
                    GAME,"war-identity-session",BRIDGE,ExactCk3Build.CK3_1210.executableSha256(),FlorinWarIdentityCodec.ADAPTER);
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
                    .put("expected_ck3_sha256",ExactCk3Build.CK3_1210.executableSha256()).put("game_adapter_id",FlorinWarIdentityCodec.ADAPTER)
                    .put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=hello.putArray("capabilities");if(capability)caps.add(FlorinWarIdentityCodec.CAPABILITY);
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
            assertEquals(FlorinWarIdentityCodec.STEP,decoded.step());assertEquals(Optional.of(BigInteger.ZERO),decoded.expectedRevision());
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
