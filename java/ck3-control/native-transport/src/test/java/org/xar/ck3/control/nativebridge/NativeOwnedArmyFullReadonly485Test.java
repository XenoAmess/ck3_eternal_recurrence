package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/** NoGame exact69 Full4 RAM/serializer originals; GetState ABI is explicitly fake.
 * Software HELLO/fresh ACK/framing/correlation are not Native/live originals.
 * The package-private software source seam never creates Managed/Root/privateReceived.
 */
@org.junit.jupiter.api.condition.EnabledIfSystemProperty(named="xar.army485.inputs",matches=".+")
final class NativeOwnedArmyFullReadonly485Test {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_1210_STEAM_26757580;
    private static final String ADAPTER="ck3-1.21.0-26757580-msvc-x64",BRIDGE="army485-software";
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    @Test void twoOriginalFull4PacketsReachReadonlyReceiveAndCanonicalReplay()throws Exception {
        for(String name:List.of("full40","full62"))for(String profile:List.of("bridge75","bridge92"))try(var f=new Fixture(name,profile,null)){
            var observed=f.actual.readFreshFullState(f.deadline);var received=assertInstanceOf(NativeFreshSnapshotPort.Received.class,observed,String.valueOf(observed)+" REJECTION="+f.actual.diagnostics().production().flatMap(v->v.lastRejectedSnapshot()));
            NativeFreshSnapshotPort.verifyOriginal(received.acknowledgement(),received.originalFrame(),received.snapshotReceived());
            assertArrayEquals(f.port.state,received.originalFrame().state().bytes());assertArrayEquals(f.port.lastSnapshot,received.originalFrame().originalPacket());
            assertArrayEquals(f.port.lastAck,received.acknowledgement().originalPacket());
            var semantic=DriverObservationAssembler.canonicalNativeState(received.originalFrame()).semantic();var tree=DriverJson.toNode(semantic);
            assertEquals(2,tree.path("player_armies").size());assertEquals(-2130706431,tree.path("played_character").path("character_id").intValue());
            assertEquals(-2080374784,tree.path("player_armies").get(0).path("army_id").intValue());
            assertEquals(-2030043135,tree.path("player_armies").get(1).path("army_id").intValue());
            for(var army:tree.path("player_armies")){assertEquals(-2130706431,army.path("owner_character_id").intValue());assertEquals(2,army.path("route_source_count").intValue());assertEquals(7,army.path("army_state_code").intValue());assertTrue(army.path("soldiers").isNull());}
            var original=received.originalFrame();var replay=new ObservedFrame(original.session(),original.snapshotId(),original.nativeRevision(),new RawJson(original.state().bytes()),original.originalPacket(),original.observedAt());
            assertEquals(semantic,DriverObservationAssembler.canonicalNativeState(replay).semantic());
            f.actual.acceptedSnapshotRevision(original).requireOriginal(original);assertThrows(IOException.class,()->f.actual.acceptedSnapshotRevision(replay));
            assertEquals(1,f.port.reads);assertEquals(0,f.port.actions);
        }
    }
    @Test void missingUnsupportedAndForeignSoftwareSourcesStayClosed()throws Exception {
        try(var f=new Fixture("full40",null,null)){unavailable(f);}
        try(var f=new Fixture("full40",null,null);var other=new Fixture("full40",null,null)){
            assertThrows(IOException.class,()->f.actual.bindArmyReadonlySoftwareSource(other.port,inputRef("bridge92")));
            assertThrows(IOException.class,()->f.actual.bindArmyReadonlySoftwareSource(f.port,inputRef("bridge61")));
            assertEquals(0,f.port.reads);unavailable(f);
        }
    }
    @Test void signedOwnerSentinelAndRouteContradictionsNeverProduceReady()throws Exception {
        for(String fault:List.of("sentinel","owner","route","state")){
            var state=state("full40");var army=(ObjectNode)state.path("player_armies").get(0);
            switch(fault){case "sentinel"->army.put("army_id",-1);case "owner"->army.put("owner_character_id",1);case "route"->army.put("route_source_count",1);case "state"->army.put("army_state","regular");default->throw new AssertionError();}
            try(var f=new Fixture("full40","bridge92",StrictJson.canonical(state))){unavailable(f);}
        }
    }
    @Test void warEventAndTupleGatesRemainClosedWithOriginalAck()throws Exception {
        for(String fault:List.of("war","event","tuple","actorTuple")){
            var state=state("full40");
            switch(fault){case "war"->state.putArray("active_wars").addObject().put("war_id",1);case "event"->state.putObject("active_event").put("instance_id",1);case "tuple"->state.put("adapter_id","wrong");case "actorTuple"->((ObjectNode)state.get("played_character")).put("schema","wrong");default->throw new AssertionError();}
            try(var f=new Fixture("full40","bridge92",StrictJson.canonical(state))){unavailable(f);}
        }
    }
    @Test void nonemptyReadonlyFullCannotMintTheOldClockActionRole()throws Exception {
        try(var f=new Fixture("full40","bridge92",null)){
            var read=assertInstanceOf(NativeGameTransport.FullClockReadUnavailable.class,f.actual.readFullClockFrameReceived(f.deadline));
            assertInstanceOf(NativeFreshSnapshotPort.Received.class,read.original(),String.valueOf(read));
            assertTrue(f.actual.latestAcceptedSnapshotRevision().isPresent());assertEquals(1,f.port.reads);assertEquals(0,f.port.actions);
        }
    }
    @Test void genuineEmptyHotfixAndExpiredReadNeedNoArmySourceOptIn()throws Exception {
        try(var f=new Fixture("basic_full",null,null)){
            assertInstanceOf(NativeFreshSnapshotPort.Received.class,f.actual.readFreshFullState(f.deadline));assertEquals(1,f.port.reads);
        }
        try(var f=new Fixture("full40",null,null)){
            var absent=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,f.actual.readFreshFullState(Instant.EPOCH));
            var zero=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,absent.dispatch());assertEquals(0,zero.proof().requestBytesWritten());assertEquals(0,f.port.reads);
        }
    }
    private static void unavailable(Fixture f)throws Exception {
        var result=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,f.actual.readFreshFullState(f.deadline));
        var ack=assertInstanceOf(NativeActionPort.AckReceived.class,result.dispatch());assertArrayEquals(f.port.lastAck,ack.originalPacket());
        assertTrue(f.actual.latestAcceptedSnapshotRevision().isEmpty());assertEquals(1,f.port.reads);assertEquals(0,f.port.actions);
    }
    private static ExactRef inputRef(String name)throws Exception {
        String configured=System.getProperty("xar.army485.inputs");assertNotNull(configured);
        Path input=Path.of(configured);assertTrue(input.isAbsolute());
        var ref=NativeWire.object(NativeWire.object(NativeWire.parse(Files.readAllBytes(input))).get(name));
        String path=NativeWire.text(ref.get("path")),sha=NativeWire.text(ref.get("sha256"));
        var bytes=ref.get("bytes");assertTrue(bytes.isIntegralNumber()&&bytes.canConvertToLong());
        return new ExactRef(path,bytes.longValue(),sha);
    }
    private static byte[] exact(String name)throws Exception {
        var ref=inputRef(name);Path file=Path.of(ref.path());assertTrue(file.isAbsolute());
        assertEquals(ref.bytes(),Files.size(file));byte[] raw=Files.readAllBytes(file);
        assertEquals(ref.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));return raw;
    }
    private static ObjectNode state(String name)throws Exception {
        var original=assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(NativeWire.packet(exact(name))));
        return NativeWire.object(NativeWire.parse(original.state().value())).deepCopy();
    }
    private static ObjectNode hello(){
        var value=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",1)
                .put("bridge_version",BRIDGE).put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256())
                .put("game_adapter_id",ADAPTER).put("game_adapter_status","ready").put("ck3_build_match",true);
        value.putArray("capabilities").add("game.state.snapshot").add(NativeFreshSnapshotPort.CAPABILITY);return value;
    }
    private static final class Fixture implements AutoCloseable {
        final Instant deadline=Instant.now().plusSeconds(30);final Replay port;final NativeGameTransport actual;
        Fixture(String original,String profile,byte[] negativeState)throws Exception {
            port=new Replay(exact(original),negativeState);String slash=Character.toString(92);
            var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"army485-software","army485-software",GAME,"army485-session",BRIDGE,BUILD.executableSha256(),ADAPTER);
            actual=new NativeGameTransport(port,config,32,32,List.of(),Clock.systemUTC());
            if(profile!=null)actual.bindArmyReadonlySoftwareSource(port,inputRef(profile));
        }
        @Override public void close()throws IOException{actual.close();}
    }
    private static final class Replay implements NativePacketPort {
        final byte[] original,state;final NativeWire.Snapshot cpp;final byte[] negativeState;
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();int reads,actions;boolean closed;byte[] lastSnapshot,lastAck;
        Replay(byte[] original,byte[] negativeState)throws IOException {
            this.original=original.clone();this.negativeState=negativeState==null?null:negativeState.clone();
            cpp=assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(NativeWire.packet(original)));
            state=negativeState==null?cpp.state().value():negativeState.clone();packets.add(NativeWire.packet(StrictJson.canonical(hello())));
        }
        @Override public void verify()throws IOException{if(closed)throw new IOException("software endpoint closed");}
        @Override public void verifyCoreControlWindowPolicy()throws IOException{verify();}
        private void check(Instant deadline)throws IOException{verify();if(!Instant.now().isBefore(deadline))throw new IOException("software caller expired");}
        @Override public void awaitConnection(Instant deadline)throws IOException{check(deadline);}
        @Override public byte[] readPacket(Instant deadline)throws IOException{check(deadline);if(packets.isEmpty())throw new IOException("software response absent");return packets.removeFirst();}
        @Override public void writePacket(byte[] raw,Instant deadline)throws IOException {
            check(deadline);var request=NativeWire.decodeExecuteRequest(raw);
            if(!request.step().equals(NativeFreshSnapshotPort.STEP)){actions++;throw new IOException("no action producer in readonly Army fixture");}
            reads++;assertEquals(Optional.of(BigInteger.ZERO),request.expectedRevision());
            String body=new String(original,java.nio.charset.StandardCharsets.UTF_8);
            var parsed=NativeWire.object(NativeWire.parse(original));String readId=NativeWire.text(parsed.get("read_request_id"));
            body=replaceOnce(body,field("read_request_id",readId),field("read_request_id",request.requestId()));
            if(negativeState!=null)body=replaceOnce(body,new String(cpp.state().value(),java.nio.charset.StandardCharsets.UTF_8),new String(negativeState,java.nio.charset.StandardCharsets.UTF_8));
            // The positive state token remains byte exact. Only software outer correlation/framing is new.
            lastSnapshot=NativeWire.packet(body.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            assertArrayEquals(state,assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(lastSnapshot)).state().value());
            var result=StrictJson.object().put("schema",NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id",request.requestId()).put("snapshot_id",cpp.snapshotId()).put("revision",cpp.revision());
            var ack=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",true);ack.set("result",result);
            // This independent ACK is explicitly a software protocol producer, not a Native original.
            lastAck=NativeWire.packet(StrictJson.canonical(ack));packets.add(lastSnapshot.clone());packets.add(lastAck.clone());
        }
        private static String field(String name,String value){String q=Character.toString(34);return q+name+q+":"+q+value+q;}
        private static String replaceOnce(String body,String token,String replacement){int i=body.indexOf(token);assertTrue(i>=0);assertEquals(i,body.lastIndexOf(token));return body.substring(0,i)+replacement+body.substring(i+token.length());}
        @Override public void close(){closed=true;}
    }
}
