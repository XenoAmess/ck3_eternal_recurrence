package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.xar.ck3.control.application.action.FullSnapshotClockControl;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/** Software packets and a file-only artifact witness. No Native call/Managed owner/Game/Host exists.
 * Nonempty rows are explicit synthetic DATA, not observations of Native126 or the user's session.
 * CI without the independent candidate artifact does not claim to run this opt-in packet fixture. */
@EnabledIfSystemProperty(named="xar.army126.dll",matches=".+")
final class Current126ArmyIdentityTransportTest {
    private static final ExactCk3Build FULL=ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final String BRIDGE="army126-software";
    private static ExactRef source(){return new ExactRef(Path.of(System.getProperty("xar.army126.dll")).toAbsolutePath().toString(),
            12395520L,"30c21218df7b9ca567b30f5a02fe31731c790db1397e0ecc45b89aa502e617ea");}

    @Test void explicitArtifactModeReachesTheSoleReceiveNormalizerWithoutLosingGenerationBits()throws Exception {
        try(var f=new Fixture(full(),true)) {
            var observed=f.transport.readFreshArmyIdentity126(f.deadline);var actual=assertInstanceOf(NativeGameTransport.ArmyIdentityReceived.class,observed,observed::toString);
            assertEquals(source(),actual.source());
            var state=DriverJson.toNode(actual.semantic());var rows=state.path("player_armies");
            assertEquals(2,rows.size());assertEquals(-2080374784,rows.get(0).path("army_id").intValue());
            assertEquals(0,rows.get(1).path("army_id").intValue());
            for(var row:rows){assertEquals(-2130706431,row.path("owner_character_id").intValue());assertTrue(row.path("controllable").booleanValue());assertEquals(3,row.size());}
            assertArrayEquals(f.port.lastSnapshot,actual.frame().originalPacket());
            f.transport.acceptedSnapshotRevision(actual.frame()).requireOriginal(actual.frame());
            assertEquals(1,f.port.reads);assertEquals(0,f.port.actions);
        }
    }
    @Test void theDefaultFullAndOrdinaryObservationApisCannotBorrowTheIdentityMode()throws Exception {
        try(var f=new Fixture(full(),true)) {
            var result=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,f.transport.readFreshFullState(f.deadline));
            var rejected=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,result.dispatch());
            assertEquals(0,rejected.proof().requestBytesWritten());assertTrue(result.reason().contains("identity-only"));
            assertThrows(java.io.UncheckedIOException.class,()->f.transport.observe(f.deadline));
            assertEquals(0,f.port.reads);assertEquals(0,f.port.actions);
        }
    }
    @Test void wrongArtifactOrForeignEndpointNeverCreatesAReadonlyBinding()throws Exception {
        try(var f=new Fixture(full(),false);var other=new Fixture(full(),false)) {
            assertThrows(IOException.class,()->f.transport.bindArmyIdentity126SoftwareSource(other.port,source()));
            var bad=new ExactRef(source().path(),source().bytes()-1,source().sha256());
            assertThrows(IOException.class,()->f.transport.bindArmyIdentity126SoftwareSource(f.port,bad));
            var result=assertInstanceOf(NativeGameTransport.ArmyIdentityUnavailable.class,f.transport.readFreshArmyIdentity126(f.deadline));
            var original=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,result.original());
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,original.dispatch());
            assertEquals(0,f.port.reads);assertTrue(f.transport.latestAcceptedSnapshotRevision().isEmpty());
        }
    }
    @Test void unavailableMalformedAndContradictoryRowsNeverBecomeAnObservedEmptyCollection()throws Exception {
        for(String fault:List.of("absent-array","null-array","unit-sentinel","owner-sentinel","other-owner","extra-route","false-owned")) {
            var state=full();var army=(ObjectNode)state.path("player_armies").get(0);
            switch(fault) {
                case "absent-array"->state.remove("player_armies");
                case "null-array"->state.putNull("player_armies");
                case "unit-sentinel"->army.put("army_id",-1);
                case "owner-sentinel"->army.put("owner_character_id",-1);
                case "other-owner"->army.put("owner_character_id",31254);
                case "extra-route"->army.putArray("route_province_ids");
                case "false-owned"->army.put("controllable",false);
                default->throw new AssertionError();
            }
            try(var f=new Fixture(state,true)) {
                var absent=assertInstanceOf(NativeGameTransport.ArmyIdentityUnavailable.class,f.transport.readFreshArmyIdentity126(f.deadline),fault);
                assertInstanceOf(NativeActionPort.AckReceived.class,assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,absent.original()).dispatch(),absent::toString);
                assertTrue(f.transport.latestAcceptedSnapshotRevision().isEmpty(),fault);assertEquals(1,f.port.reads);
            }
        }
    }
    @Test void currentTupleEventAndWarScopeRemainStrictInTheNewReadMode()throws Exception {
        for(String fault:List.of("war","event","tuple","actor-tuple")) {
            var state=full();
            switch(fault) {
                case "war"->state.putArray("active_wars").addObject().put("war_id",1);
                case "event"->state.putObject("active_event").put("instance_id",1);
                case "tuple"->state.put("adapter_id","wrong");
                case "actor-tuple"->((ObjectNode)state.get("played_character")).put("game_version","wrong");
                default->throw new AssertionError();
            }
            try(var f=new Fixture(state,true)) {
                var absent=assertInstanceOf(NativeGameTransport.ArmyIdentityUnavailable.class,f.transport.readFreshArmyIdentity126(f.deadline),fault);
                assertInstanceOf(NativeActionPort.AckReceived.class,assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,absent.original()).dispatch(),absent::toString);
                assertTrue(f.transport.latestAcceptedSnapshotRevision().isEmpty(),fault);assertEquals(0,f.port.actions);
            }
        }
    }
    @Test void identityObservationDoesNotGrantClockSaveOrDifferentSpeed()throws Exception {
        assertFalse(FullSnapshotClockControl.isMappedSave112Bridge(source()));
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.requestMappedSave112(source(),"native:7",BigInteger.valueOf(7),Instant.now().plusSeconds(30)));
        try(var f=new Fixture(full(),true)) {
            var observed=f.transport.readFreshArmyIdentity126(f.deadline);assertInstanceOf(NativeGameTransport.ArmyIdentityReceived.class,observed,observed::toString);
            assertInstanceOf(NativeGameTransport.FullClockReadUnavailable.class,f.transport.readFullClockFrameReceived(f.deadline));
            assertEquals(1,f.port.reads);assertEquals(0,f.port.actions);
        }
    }

    private static ObjectNode identity(String schema) {
        return StrictJson.object().put("schema",schema).put("game_version",FULL.version()).put("executable_sha256",FULL.executableSha256())
                .put("adapter_id",FULL.coreFullAdapterId()).put("backend",FULL.coreFullBackend());
    }
    private static ObjectNode full() {
        var root=identity("ck3_1210_full_state_v1").put("date_raw",53179344).put("speed",5).put("paused",true).put("map_ready",true).put("local_player_id",1);
        var actor=identity("ck3_1210_played_character_v1").put("character_id",-2130706431).put("alive",true).put("stress_points",0);
        actor.putNull("betrothed_id");actor.putNull("primary_spouse_id");actor.putArray("spouse_ids");root.set("played_character",actor);
        for(String resource:List.of("gold","prestige","piety"))root.putObject("played_character_"+resource).put("raw",0).put("scale",100000);
        root.putNull("active_event");root.putNull("pending_character_interaction");root.putNull("one_life_settlement");root.putArray("active_wars");root.putArray("history");
        var rows=root.putArray("player_armies");
        for(int unit:new int[]{-2080374784,0})rows.addObject().put("army_id",unit).put("owner_character_id",-2130706431).put("controllable",true);
        return root;
    }
    private static final class Fixture implements AutoCloseable {
        final Instant deadline=Instant.now().plusSeconds(30);final Replay port;final NativeGameTransport transport;
        Fixture(ObjectNode state,boolean bind)throws Exception {
            port=new Replay(state);String s=Character.toString(92);
            var cfg=new NativePipeEndpoint.Config(s+s+"."+s+"pipe"+s+"army126-software","army126-software",GAME,"army126-session",BRIDGE,FULL.executableSha256(),FULL.coreFullAdapterId());
            transport=new NativeGameTransport(port,cfg,32,32,List.of(),Clock.systemUTC());
            if(bind)transport.bindArmyIdentity126SoftwareSource(port,source());
        }
        @Override public void close()throws IOException {transport.close();}
    }
    private static final class Replay implements NativePacketPort {
        final ObjectNode state;final ArrayDeque<byte[]> packets=new ArrayDeque<>();int reads,actions;boolean closed;byte[] lastSnapshot;
        Replay(ObjectNode state)throws IOException {
            this.state=state.deepCopy();var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",1)
                    .put("bridge_version",BRIDGE).put("expected_ck3_version",FULL.version()).put("expected_ck3_sha256",FULL.executableSha256())
                    .put("game_adapter_id",FULL.coreFullAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            hello.putArray("capabilities").add(NativeFreshSnapshotPort.CAPABILITY).add("game.state.snapshot");packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        @Override public void verify()throws IOException {if(closed)throw new IOException("software endpoint closed");}
        @Override public void verifyCoreControlWindowPolicy()throws IOException {verify();}
        @Override public void awaitConnection(Instant deadline)throws IOException {verify();}
        @Override public byte[] readPacket(Instant deadline)throws IOException {verify();if(packets.isEmpty())throw new IOException("software response absent");return packets.removeFirst();}
        @Override public void writePacket(byte[] raw,Instant deadline)throws IOException {
            verify();var request=NativeWire.decodeExecuteRequest(raw);
            if(!request.step().equals(NativeFreshSnapshotPort.STEP)){actions++;throw new IOException("no action producer in identity-only software fixture");}
            reads++;var packet=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","native:7").put("revision",7).put("read_request_id",request.requestId());
            packet.set("state",state);lastSnapshot=NativeWire.packet(StrictJson.canonical(packet));packets.add(lastSnapshot);
            var result=StrictJson.object().put("schema",NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id",request.requestId()).put("snapshot_id","native:7").put("revision",7);
            var ack=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",true);ack.set("result",result);packets.add(NativeWire.packet(StrictJson.canonical(ack)));
        }
        @Override public void close(){closed=true;}
    }
}
