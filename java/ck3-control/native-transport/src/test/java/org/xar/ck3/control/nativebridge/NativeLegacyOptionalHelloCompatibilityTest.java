package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/** Optional legacy protocol metadata only. The real receiver handles software snapshots;
 * no Complete, Ready, Driver, Game or private Full role is constructed by this test. */
final class NativeLegacyOptionalHelloCompatibilityTest {
    private static final String BRIDGE="legacy-optional-software";
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final ExactCk3Build LEGACY=ExactCk3Build.CK3_12004;
    private static final String OLD_ADAPTER="ck3-1.20.0.4-msvc-x64";

    @Test void absentLegacyVersionPreservesInitialAndAutomaticSnapshotReceiverInputs() throws Exception {
        var hello=hello(LEGACY,OLD_ADAPTER,Optional.empty());assertFalse(hello.has("expected_ck3_version"));
        var initial=legacySnapshot("fixture-snapshot-1",1,53144328);
        try(var source=new Replay(hello,initial,true);var actual=transport(source,LEGACY,OLD_ADAPTER)) {
            Instant until=Instant.now().plusSeconds(30);var first=actual.observe(until);
            assertArrayEquals(initial,first.originalPacket());
            var semantic=DriverObservationAssembler.canonicalNativeState(first).semantic();
            var tree=DriverJson.toNode(semantic);assertTrue(tree.path("paused").booleanValue());assertTrue(tree.path("map_ready").booleanValue());
            assertEquals(73,tree.path("played_character").path("character_id").intValue());
            actual.acceptedSnapshotRevision(first).requireOriginal(first);
            var second=actual.observe(until);assertEquals("fixture-snapshot-2",second.snapshotId());assertEquals(BigInteger.TWO,second.nativeRevision());
            assertEquals(1,source.autoProduced);assertArrayEquals(initial,source.initial);assertArrayEquals(initial,first.originalPacket());
            assertEquals(BigInteger.valueOf(2),actual.diagnostics().production().orElseThrow().receivedSnapshotCount());
            assertEquals(BigInteger.ZERO,actual.diagnostics().production().orElseThrow().rejectedSnapshotCount());
            assertSame(second,actual.latestObservedSnapshot().orElseThrow());
            assertEquals(NativeGameTransport.ReceivedState.HELLO_VERIFIED,actual.diagnostics().receivedState());
            strictFullUnavailable(actual,until);assertEquals(0,source.writes);
        }
    }
    @Test void realFlorinCppMarkerCannotBorrowAVersionlessHelloEvenWithMatchingHashAndAdapter() throws Exception {
        var build=ExactCk3Build.CK3_1210;String adapter="ck3-1.21.0-msvc-x64";
        var hello=hello(build,adapter,Optional.empty());assertFalse(hello.has("expected_ck3_version"));
        byte[] original=fullCpp();
        try(var source=new Replay(hello,original,false);var actual=transport(source,build,adapter)) {
            Instant until=Instant.now().plusSeconds(30);assertThrows(UncheckedIOException.class,()->actual.observe(until));
            rejected(actual,source.initial);strictFullUnavailable(actual,until);assertEquals(0,source.writes);
        }
    }
    @Test void presentWrongTypeOptionalVersionRejectsAndRetainsTheOriginalLegacySnapshot() throws Exception {
        for(String kind:List.of("null","boolean","integer","object")) {
            var hello=hello(LEGACY,OLD_ADAPTER,Optional.empty());
            switch(kind) {
                case "null" -> hello.putNull("expected_ck3_version");
                case "boolean" -> hello.put("expected_ck3_version",true);
                case "integer" -> hello.put("expected_ck3_version",12004);
                case "object" -> hello.putObject("expected_ck3_version");
                default -> throw new AssertionError(kind);
            }
            try(var source=new Replay(hello,legacySnapshot("fixture-snapshot-1",1,53144328),false);var actual=transport(source,LEGACY,OLD_ADAPTER)) {
                assertThrows(UncheckedIOException.class,()->actual.observe(Instant.now().plusSeconds(30)));
                rejected(actual,source.initial);assertEquals(0,source.writes);
            }
        }
    }

    private static void rejected(NativeGameTransport actual,byte[] original) throws Exception {
        var production=actual.diagnostics().production().orElseThrow();assertEquals(BigInteger.ONE,production.receivedSnapshotCount());
        assertEquals(BigInteger.ONE,production.rejectedSnapshotCount());
        assertArrayEquals(original,production.lastRejectedSnapshot().orElseThrow().original().originalPacket().value());
        assertTrue(actual.latestAcceptedSnapshotRevision().isEmpty());assertTrue(actual.latestObservedSnapshot().isEmpty());
    }
    private static void strictFullUnavailable(NativeGameTransport actual,Instant until) throws Exception {
        var absent=assertInstanceOf(NativeGameTransport.FullClockReadUnavailable.class,actual.readFullClockFrameReceived(until));
        var read=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,absent.original());
        assertEquals(0,assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,read.dispatch()).proof().requestBytesWritten());
    }
    private static ObjectNode hello(ExactCk3Build build,String adapter,Optional<String> version) {
        var row=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",5)
                .put("bridge_version",BRIDGE).put("expected_ck3_sha256",build.executableSha256()).put("game_adapter_id",adapter)
                .put("game_adapter_status","ready").put("ck3_build_match",true);
        version.ifPresent(value->row.put("expected_ck3_version",value));row.putArray("capabilities").add("game.state.snapshot").add(NativeFreshSnapshotPort.CAPABILITY);return row;
    }
    /** Same legacy software initial-state field shape as ActionWriterIntegrationFixture, with no new schema marker. */
    private static byte[] legacySnapshot(String id,int revision,int date) throws IOException {
        var state=StrictJson.object().put("paused",true).put("map_ready",true).put("speed",3).put("date_raw",date);
        state.putObject("played_character").put("character_id",73).put("alive",true);
        state.putNull("active_event").putNull("pending_character_interaction").put("one_life_terminal",false).putNull("one_life_terminal_reason").put("episode_identity_pending",false);
        state.putArray("active_wars");state.putArray("player_armies");state.putObject("diagnostics").put("bridge_pid",42).put("connection_generation",5);
        var frame=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id",id).put("revision",revision);frame.set("state",state);
        return NativeWire.packet(StrictJson.canonical(frame));
    }
    private static NativeGameTransport transport(Replay source,ExactCk3Build build,String adapter) {
        String slash=Character.toString(92);
        var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"legacy-optional-software","legacy-optional-software",GAME,"legacy-optional-session",BRIDGE,build.executableSha256(),adapter);
        return new NativeGameTransport(source,config,16,8,List.of(),Clock.systemUTC());
    }
    private static byte[] fullCpp() throws Exception {
        String override=System.getProperty("xar.native.legacyHello.full.path");byte[] body;
        if(override!=null) {
            if(override.isBlank()||!Path.of(override).isAbsolute())throw new IOException("explicit absolute C++ Full source required");
            try(var input=Files.newInputStream(Path.of(override))){body=input.readNBytes(1172);}
        } else try(var input=NativeLegacyOptionalHelloCompatibilityTest.class.getResourceAsStream("/newnative/full1210/full-snapshot-producer-002.json")) {
            if(input==null)throw new IOException("exact C++ Full002 resource missing");body=input.readNBytes(1172);
        }
        assertEquals(1171,body.length);assertEquals("5eca02fea7c3f5095d675238f59b69b8d166ed17a0bd4c208b0e133700d7e550",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body)));
        return NativeWire.packet(body);
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();final byte[] initial;final boolean automatic;
        int autoProduced,writes;boolean closed;
        Replay(ObjectNode hello,byte[] initial,boolean automatic) throws IOException {
            this.initial=initial.clone();this.automatic=automatic;packets.add(NativeWire.packet(StrictJson.canonical(hello)));packets.add(initial.clone());
        }
        @Override public void verify() throws IOException {if(closed)throw new IOException("software source closed");}
        @Override public void awaitConnection(Instant until) throws IOException {verify();}
        @Override public byte[] readPacket(Instant until) throws IOException {
            verify();if(packets.isEmpty()&&automatic&&autoProduced==0){autoProduced++;packets.add(legacySnapshot("fixture-snapshot-2",2,53144352));}
            if(packets.isEmpty())throw new IOException("software snapshot source exhausted");return packets.removeFirst();
        }
        @Override public void writePacket(byte[] packet,Instant until) {writes++;throw new AssertionError("passive optional HELLO test must never write a query/action");}
        @Override public void close(){closed=true;}
    }
}
