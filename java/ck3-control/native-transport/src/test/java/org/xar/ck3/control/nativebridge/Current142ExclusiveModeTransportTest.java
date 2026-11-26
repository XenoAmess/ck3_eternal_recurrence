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
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.xar.ck3.control.application.action.FullSnapshotClockControl;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.nativebridge.NativeGameTransport.NativeSourceMode.*;

/** NoGame software endpoint plus an actual static artifact/file witness. No DLL is loaded, Managed owner made or permission forged.
 * Payload rows are synthetic DATA, never observations of Native142 or of the user's CK3 session. */
@EnabledIfSystemProperty(named="xar.current142.dll",matches=".+")
final class Current142ExclusiveModeTransportTest {
    private static final ExactCk3Build FULL=ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final String BRIDGE="current142-software";
    private static ExactRef source(){return new ExactRef(Path.of(System.getProperty("xar.current142.dll")).toAbsolutePath().toString(),
            12396032L,"3601748c4d4824509416d61c779f16eda6f97b85cd5608786ecf5645215b733c");}
    private static NativeActionPort.RejectedBeforeDispatch zero(NativeActionPort.DispatchOutcome original){
        var rejected=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,original);
        assertEquals(0,rejected.proof().requestBytesWritten());assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,rejected.proof().stage());return rejected;
    }
    @Test void compatibilityChecksAndHelloDoNotBindButTheReal142ArtifactFreezesReadonlySelection()throws Exception {
        var witness=SharedSourceFiles.observe(Path.of(source().path()));
        assertEquals(source().bytes(),witness.source().bytes());assertEquals(source().sha256(),witness.source().sha256());SharedSourceFiles.assertUnchanged(witness);
        try(var f=new Fixture(full(true))){
            assertTrue(f.transport.sourceMode().isEmpty());f.transport.diagnostics();
            f.transport.requireSourceMode(DEFAULT_CONTROL);f.transport.requireSourceMode(CURRENT_IDENTITY_READONLY);
            assertTrue(f.transport.sourceMode().isEmpty());assertEquals(0,f.port.writes);
            f.transport.awaitHello(f.deadline);assertTrue(f.transport.sourceMode().isEmpty());
            f.bind();assertEquals(Optional.of(CURRENT_IDENTITY_READONLY),f.transport.sourceMode());
            f.transport.requireSourceMode(CURRENT_IDENTITY_READONLY);
            assertThrows(IOException.class,()->f.transport.requireSourceMode(DEFAULT_CONTROL));
            assertEquals(0,f.port.writes);
            var result=f.transport.readFreshArmyIdentity126(f.deadline);
            var received=assertInstanceOf(NativeGameTransport.ArmyIdentityReceived.class,result,result::toString);
            assertEquals(source(),received.source());f.transport.acceptedSnapshotRevision(received.frame()).requireOriginal(received.frame());
            NativeFreshSnapshotPort.verifyOriginal(received.acknowledgement(),received.frame(),received.snapshotReceived());
            var rows=DriverJson.toNode(received.semantic()).path("player_armies");assertEquals(2,rows.size());
            assertEquals(-2080374784,rows.get(0).path("army_id").intValue());assertEquals(0,rows.get(1).path("army_id").intValue());
            for(var row:rows){assertEquals(3,row.size());assertEquals(-2130706431,row.path("owner_character_id").intValue());assertTrue(row.path("controllable").booleanValue());}
            assertArrayEquals(f.port.lastSnapshot,received.frame().originalPacket());assertEquals(1,f.port.freshWrites);assertEquals(0,f.port.worldWrites);
        }
        SharedSourceFiles.assertUnchanged(witness);
    }
    @Test void foreignEndpointOrWrongArtifactCannotFreezeAnUnboundMode()throws Exception {
        try(var f=new Fixture(full(true));var foreign=new Fixture(full(true))){
            assertThrows(IOException.class,()->f.transport.bindArmyIdentity126SoftwareSource(foreign.port,source()));
            assertThrows(IOException.class,()->f.transport.bindArmyIdentity126SoftwareSource(f.port,new ExactRef(source().path(),source().bytes()-1,source().sha256())));
            assertTrue(f.transport.sourceMode().isEmpty());assertEquals(0,f.port.writes);
            f.transport.requireSourceMode(DEFAULT_CONTROL);f.transport.requireSourceMode(CURRENT_IDENTITY_READONLY);
            f.bind();assertEquals(Optional.of(CURRENT_IDENTITY_READONLY),f.transport.sourceMode());
        }
    }
    @Test void aRealWrittenCoreRequestCannotBeReclassifiedByALaterSourceBinding()throws Exception {
        try(var f=new Fixture(full(false))){
            var original=assertInstanceOf(NativeActionPort.AckReceived.class,f.transport.readCoreFrame(f.deadline));
            assertFalse(original.nativeOk(),"software negative ACK is actual request history, not a fabricated zero-write result");
            assertEquals(1,f.port.coreWrites);assertTrue(original.outbound().isPresent());assertTrue(original.custody().isPresent());
            assertThrows(IOException.class,f::bind);assertTrue(f.transport.sourceMode().isEmpty());
            assertEquals(1,f.port.writes);assertEquals(0,f.port.worldWrites);
        }
    }
    @Test void aReceivedUnboundSnapshotCannotBeRetroactivelyNormalizedAsIdentityOnly()throws Exception {
        try(var f=new Fixture(full(false))){
            f.port.unsolicited();
            // A current Full without its independently bound source is correctly rejected, not accepted.
            // Its original received packet is still history and cannot be reinterpreted under a later mode.
            assertThrows(java.io.UncheckedIOException.class,()->f.transport.observe(f.deadline));
            assertTrue(f.transport.latestAcceptedSnapshotRevision().isEmpty());assertTrue(f.transport.sourceMode().isEmpty());
            var rejected=assertThrows(IOException.class,f::bind);
            assertTrue(rejected.getMessage().contains("source mode cannot reinterpret"));
            assertTrue(f.transport.sourceMode().isEmpty());assertEquals(0,f.port.writes);
        }
    }
    @Test void pendingReadonlyFreshReadRetainsItsOriginalIdAndCollectsWithoutAnotherRequest()throws Exception {
        try(var f=new Fixture(full(true))){
            f.bind();f.port.holdAck=true;
            var first=assertInstanceOf(NativeGameTransport.ArmyIdentityUnavailable.class,f.transport.readFreshArmyIdentity126(f.deadline));
            var unknown=assertInstanceOf(NativeActionPort.Unknown.class,assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,first.original()).dispatch());
            String id=unknown.requestId();assertEquals(1,f.port.freshWrites);assertTrue(f.transport.originalOutboundPacket(id).isPresent());
            assertThrows(IOException.class,()->f.transport.requireSourceMode(DEFAULT_CONTROL));
            var repeated=assertInstanceOf(NativeGameTransport.ArmyIdentityUnavailable.class,f.transport.readFreshArmyIdentity126(f.deadline));
            assertEquals(id,assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,repeated.original()).dispatch().requestId());assertEquals(1,f.port.freshWrites);
            f.port.releaseAck();var collected=f.transport.collectFreshArmyIdentity126(id,f.deadline);
            var received=assertInstanceOf(NativeGameTransport.ArmyIdentityReceived.class,collected,collected::toString);
            assertEquals(source(),received.source());assertEquals(1,f.port.freshWrites);assertEquals(0,f.port.worldWrites);
            assertEquals(Optional.of(CURRENT_IDENTITY_READONLY),f.transport.sourceMode());
        }
    }
    @Test void readonlyModeAllowsCoreQueriesButRejectsCoreClockAndOrdinaryFullAuthorityBeforeWriting()throws Exception {
        try(var f=new Fixture(full(true))){
            f.bind();var query=assertInstanceOf(NativeActionPort.AckReceived.class,f.transport.readCoreFrame(f.deadline));
            assertFalse(query.nativeOk(),"intentional software unavailable Core reply remains its actual ACK");assertEquals(1,f.port.coreWrites);
            var control=zero(f.transport.submitCoreClockControl(null,CoreClockControl.Step.PAUSE_MAP,f.deadline));
            assertTrue(control.proof().reason().contains("identity-only"),control::toString);
            var ordinary=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,f.transport.readFreshFullState(f.deadline));zero(ordinary.dispatch());
            assertInstanceOf(NativeGameTransport.FullClockReadUnavailable.class,f.transport.readFullClockFrameReceived(f.deadline));
            assertThrows(java.io.UncheckedIOException.class,()->f.transport.observe(f.deadline));
            assertEquals(1,f.port.writes);assertEquals(0,f.port.worldWrites);
            var observed=f.transport.readFreshArmyIdentity126(f.deadline);assertInstanceOf(NativeGameTransport.ArmyIdentityReceived.class,observed,observed::toString);
            assertEquals(1,f.port.freshWrites);assertEquals(2,f.port.writes);assertEquals(0,f.port.worldWrites);
        }
    }
    private static ObjectNode identity(String schema){return StrictJson.object().put("schema",schema).put("game_version",FULL.version())
            .put("executable_sha256",FULL.executableSha256()).put("adapter_id",FULL.coreFullAdapterId()).put("backend",FULL.coreFullBackend());}
    private static ObjectNode full(boolean nonempty){
        var root=identity("ck3_1210_full_state_v1").put("date_raw",53179344).put("speed",5).put("paused",true).put("map_ready",true).put("local_player_id",1);
        var actor=identity("ck3_1210_played_character_v1").put("character_id",-2130706431).put("alive",true).put("stress_points",0);
        actor.putNull("betrothed_id");actor.putNull("primary_spouse_id");actor.putArray("spouse_ids");root.set("played_character",actor);
        for(String resource:List.of("gold","prestige","piety"))root.putObject("played_character_"+resource).put("raw",0).put("scale",100000);
        root.putNull("active_event");root.putNull("pending_character_interaction");root.putNull("one_life_settlement");root.putArray("active_wars");root.putArray("history");
        var rows=root.putArray("player_armies");if(nonempty)for(int unit:new int[]{-2080374784,0})
            rows.addObject().put("army_id",unit).put("owner_character_id",-2130706431).put("controllable",true);
        return root;
    }
    private static final class Fixture implements AutoCloseable {
        final Instant deadline=Instant.now().plusSeconds(30);final Replay port;final NativeGameTransport transport;
        Fixture(ObjectNode state)throws Exception{
            port=new Replay(state);String s=Character.toString(92);
            var config=new NativePipeEndpoint.Config(s+s+"."+s+"pipe"+s+"current142-software","current142-software",GAME,"current142-session",BRIDGE,FULL.executableSha256(),FULL.coreFullAdapterId());
            transport=new NativeGameTransport(port,config,32,32,List.of(),Clock.systemUTC());
        }
        void bind()throws IOException{transport.bindArmyIdentity126SoftwareSource(port,source());}
        @Override public void close()throws IOException{transport.close();}
    }
    private static final class Replay implements NativePacketPort {
        final ObjectNode state;final ArrayDeque<byte[]> packets=new ArrayDeque<>();int writes,freshWrites,coreWrites,worldWrites;
        boolean closed,holdAck;byte[] lastSnapshot,heldAck;
        Replay(ObjectNode state)throws IOException{
            this.state=state.deepCopy();var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",1)
                    .put("bridge_version",BRIDGE).put("expected_ck3_version",FULL.version()).put("expected_ck3_sha256",FULL.executableSha256())
                    .put("game_adapter_id",FULL.coreFullAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            hello.putArray("capabilities").add(NativeFreshSnapshotPort.CAPABILITY).add("game.state.snapshot").add("game.query.core-frame.v1");
            packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        private ObjectNode snapshot(){var packet=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","native:7").put("revision",7);packet.set("state",state);return packet;}
        void unsolicited()throws IOException{packets.add(NativeWire.packet(StrictJson.canonical(snapshot())));}
        void releaseAck()throws IOException{verify();if(heldAck==null)throw new IOException("no original software ACK held");packets.add(heldAck);heldAck=null;}
        @Override public void verify()throws IOException{if(closed)throw new IOException("software endpoint closed");}
        @Override public void verifyCoreControlWindowPolicy()throws IOException{verify();}
        @Override public void awaitConnection(Instant deadline)throws IOException{verify();}
        @Override public byte[] readPacket(Instant deadline)throws IOException{verify();if(packets.isEmpty())throw new IOException("software response absent");return packets.removeFirst();}
        @Override public void writePacket(byte[] raw,Instant deadline)throws IOException{
            verify();writes++;var request=NativeWire.decodeExecuteRequest(raw);
            var ack=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId());
            if(request.step().equals("query-core-frame-v1")){
                coreWrites++;ack.put("ok",false).put("error","software_core_unavailable");ack.putObject("result").put("step",request.step()).put("accepted",false);
                packets.add(NativeWire.packet(StrictJson.canonical(ack)));return;
            }
            if(!request.step().equals(NativeFreshSnapshotPort.STEP)){worldWrites++;throw new IOException("no world producer in this readonly software fixture");}
            freshWrites++;var frame=snapshot().put("read_request_id",request.requestId());lastSnapshot=NativeWire.packet(StrictJson.canonical(frame));packets.add(lastSnapshot);
            var result=StrictJson.object().put("schema",NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id",request.requestId()).put("snapshot_id","native:7").put("revision",7);
            ack.put("ok",true);ack.set("result",result);byte[] original=NativeWire.packet(StrictJson.canonical(ack));
            if(holdAck){heldAck=original;holdAck=false;}else packets.add(original);
        }
        @Override public void close(){closed=true;}
    }
}
