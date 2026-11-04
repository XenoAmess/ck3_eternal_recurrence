package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.locks.LockSupport;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativePacketPort;
import org.xar.ck3.control.nativebridge.NativePipeEndpoint;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.PostAckReadTransportTestSupport;

/** Real production read operation and held receiver over software packet DATA; no private Root/Game oracle. */
final class PostAckFreshReadAvailabilityTest {
    private static final String ERROR="fresh_full_state_native_read_unavailable";
    private static final String SHA="2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
    private static final String ADAPTER="ck3-1.19.0.6-msvc-x64";
    private static final String STATE="""
        {"date_raw":53144520,"speed":3,"paused":true,"map_ready":true,"played_character":{"character_id":73,"alive":true},
        "active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,"one_life_settlement":null,
        "played_character_gold":{"raw":0,"scale":100000},"played_character_prestige":{"raw":0,"scale":100000},"played_character_piety":{"raw":0,"scale":100000},"history":[],
        "active_wars":[],"player_armies":[],"diagnostics":{}}
        """;

    @TempDir Path root;

    @Test void exactNegativeAcksArePreservedBeforeNewReadonlyQueriesAndRealPausedFrameReturns()throws Exception {
        var replay=new Replay(Mode.TWO_NEGATIVE_THEN_SUCCESS);
        try(var transport=replay.open(16)) {
            var port=new RecordingPort(transport);Instant deadline=deadline();
            var preserved=new ArrayList<NativeFreshSnapshotPort.Unavailable>();
            var result=read(port,deadline,3,unavailable->{
                preserved.add(unavailable);replay.events.add("preserve"+preserved.size());
                var ack=assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.dispatch());
                assertFalse(ack.nativeOk());assertTrue(ack.custody().isPresent());
                try {
                    ack.custody().orElseThrow().verify(ack);
                    Files.write(root.resolve("negative-"+preserved.size()+".bin"),ack.originalPacket());
                    if(unavailable.originalFrame().isPresent())
                        Files.write(root.resolve("frame-"+preserved.size()+".bin"),unavailable.originalFrame().orElseThrow().originalPacket());
                } catch(IOException failure) {throw new UncheckedIOException(failure);}
            });
            var received=assertInstanceOf(NativeFreshSnapshotPort.Received.class,result);
            assertReceived(received,replay);
            assertEquals(List.of("write1","preserve1","write2","preserve2","write3"),replay.events);
            assertEquals(3,port.reads);assertTrue(port.collected.isEmpty());assertEquals(3,replay.ids.size());
            assertEquals(2,preserved.size());assertEquals(2,replay.negativePackets.size());
            for(int i=0;i<2;i++) {
                assertArrayEquals(replay.negativePackets.get(i),Files.readAllBytes(root.resolve("negative-"+(i+1)+".bin")));
                assertArrayEquals(replay.negativePackets.get(i),((NativeActionPort.AckReceived)preserved.get(i).dispatch()).originalPacket());
            }
            sameDeadline(port,replay,deadline);
            System.out.println("SOFTWARE_POST_ACK_READ_DATA exact_negative=2 preserved_before_next=true reads=3 paused=true date_raw=53144520 controls=0");
        }
    }

    @Test void unknownCollectsOnlyItsOriginalAndOtherFailuresNeverBecomeAvailabilityRetry()throws Exception {
        for(Mode mode:List.of(Mode.UNKNOWN_THEN_SUCCESS,Mode.PERSISTENT_UNKNOWN,Mode.UNKNOWN_THEN_NEGATIVE)) {
            var replay=new Replay(mode);
            try(var transport=replay.open(2)) {
                var port=new RecordingPort(transport);Instant deadline=deadline();
                var preserved=new ArrayList<NativeFreshSnapshotPort.Unavailable>();
                var result=read(port,deadline,3,preserved::add);
                assertInstanceOf(NativeActionPort.Unknown.class,preserved.getFirst().dispatch());
                assertEquals(List.of(preserved.getFirst().dispatch().requestId()),port.collected);
                assertEquals(preserved.getFirst().dispatch().requestId(),replay.ids.getFirst());
                if(mode==Mode.PERSISTENT_UNKNOWN) {
                    var unavailable=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,result);
                    assertInstanceOf(NativeActionPort.Unknown.class,unavailable.dispatch());
                    assertSame(preserved.getLast(),unavailable);assertEquals(2,preserved.size());
                } else {
                    assertReceived(assertInstanceOf(NativeFreshSnapshotPort.Received.class,result),replay);
                    assertEquals(mode==Mode.UNKNOWN_THEN_NEGATIVE?2:1,preserved.size());
                    if(mode==Mode.UNKNOWN_THEN_NEGATIVE)assertFalse(assertInstanceOf(NativeActionPort.AckReceived.class,preserved.getLast().dispatch()).nativeOk());
                }
                assertEquals(mode==Mode.UNKNOWN_THEN_NEGATIVE?2:1,replay.ids.size());
                assertEquals(replay.ids.size(),port.reads);sameDeadline(port,replay,deadline);
            }
        }
        for(Mode mode:List.of(Mode.OTHER_TEXT,Mode.OBJECT_ERROR,Mode.NULL_ERROR,Mode.ABSENT_ERROR,Mode.POSITIVE_WITHOUT_FRAME,Mode.ORIGINAL_IO)) {
            var replay=new Replay(mode);
            try(var transport=replay.open(16)) {
                var port=new RecordingPort(transport);Instant deadline=deadline();
                var preserved=new ArrayList<NativeFreshSnapshotPort.Unavailable>();
                if(mode==Mode.ORIGINAL_IO) {
                    assertSame(replay.emptyReadFailure,assertThrows(IOException.class,()->read(port,deadline,3,preserved::add)));
                    assertInstanceOf(NativeActionPort.Unknown.class,preserved.getFirst().dispatch());
                    assertEquals(List.of(replay.ids.getFirst()),port.collected);
                } else {
                    var unavailable=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,read(port,deadline,3,preserved::add));
                    assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.dispatch());
                    assertSame(preserved.getFirst(),unavailable);assertTrue(port.collected.isEmpty());
                }
                assertEquals(1,port.reads);assertEquals(1,replay.ids.size());assertEquals(1,preserved.size());
                sameDeadline(port,replay,deadline);
            }
        }
        System.out.println("SOFTWARE_POST_ACK_READ_DATA unknown_same_id_collect=true unresolved_no_resubmit=true other_error_io_no_retry=true controls=0");
    }

    @Test void originalDeadlineBoundArchiveFailureAndInterruptAreNeverRenewedOrRetried()throws Exception {
        var bounded=new Replay(Mode.NEGATIVE);
        try(var transport=bounded.open(16)) {
            var port=new RecordingPort(transport);Instant deadline=deadline();
            var preserved=new ArrayList<NativeFreshSnapshotPort.Unavailable>();
            var result=read(port,deadline,2,preserved::add);
            assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,result);assertSame(preserved.getLast(),result);
            assertEquals(2,port.reads);assertEquals(2,preserved.size());assertEquals(2,bounded.ids.size());
            assertTrue(port.collected.isEmpty());sameDeadline(port,bounded,deadline);
        }
        var expired=new Replay(Mode.NEGATIVE);
        try(var transport=expired.open(16)) {
            var port=new RecordingPort(transport);var preserved=new ArrayList<NativeFreshSnapshotPort.Unavailable>();
            assertThrows(IOException.class,()->read(port,Instant.now().minusMillis(1),3,preserved::add));
            assertEquals(0,port.reads);assertTrue(expired.ids.isEmpty());assertTrue(preserved.isEmpty());
        }
        var elapsed=new Replay(Mode.NEGATIVE);
        try(var transport=elapsed.open(16)) {
            transport.awaitHello(deadline());elapsed.deadlines.clear();
            var port=new RecordingPort(transport);Instant deadline=Instant.now().plusMillis(200);
            var preserved=new ArrayList<NativeFreshSnapshotPort.Unavailable>();
            var result=read(port,deadline,3,unavailable->{
                preserved.add(unavailable);
                while(Instant.now().isBefore(deadline))LockSupport.parkNanos(1_000_000);
            });
            assertSame(preserved.getFirst(),result);assertEquals(1,preserved.size());assertEquals(1,port.reads);
            assertEquals(1,elapsed.ids.size());sameDeadline(port,elapsed,deadline);
        }
        var failed=new Replay(Mode.NEGATIVE);
        try(var transport=failed.open(16)) {
            var port=new RecordingPort(transport);var primary=new IllegalStateException("actual preserving callback failed");
            var preserved=new ArrayList<NativeFreshSnapshotPort.Unavailable>();
            assertSame(primary,assertThrows(IllegalStateException.class,()->read(port,deadline(),3,unavailable->{preserved.add(unavailable);throw primary;})));
            assertEquals(1,preserved.size());assertEquals(1,port.reads);assertEquals(1,failed.ids.size());assertTrue(port.collected.isEmpty());
        }
        for(boolean duringPause:List.of(false,true)) {
            var replay=new Replay(Mode.NEGATIVE);
            try(var transport=replay.open(16)) {
                var port=new RecordingPort(transport);var preserved=new ArrayList<NativeFreshSnapshotPort.Unavailable>();
                try {
                    if(!duringPause)Thread.currentThread().interrupt();
                    assertThrows(InterruptedException.class,()->read(port,deadline(),3,unavailable->{
                        preserved.add(unavailable);Thread.currentThread().interrupt();
                    }));
                } finally {Thread.interrupted();}
                assertEquals(duringPause?1:0,preserved.size());assertEquals(duringPause?1:0,port.reads);
                assertEquals(duringPause?1:0,replay.ids.size());assertTrue(port.collected.isEmpty());
            }
        }
        System.out.println("SOFTWARE_POST_ACK_READ_DATA attempts_bounded=true original_deadline_exhaustion=true archive_primary=true interrupt_propagated=true controls=0");
    }

    private static NativeFreshSnapshotPort.Result read(RecordingPort port,Instant deadline,int maximum,Consumer<NativeFreshSnapshotPort.Unavailable> preserve)throws IOException,InterruptedException {
        return RootAdvanceInfrastructureFactory.readAvailableFreshSnapshot(port,deadline,Clock.systemUTC(),maximum,preserve);
    }
    private static void sameDeadline(RecordingPort port,Replay replay,Instant deadline) {
        assertFalse(port.deadlines.isEmpty());assertFalse(replay.deadlines.isEmpty());
        for(Instant original:port.deadlines)assertSame(deadline,original);
        for(Instant original:replay.deadlines)assertEquals(deadline,original);
    }
    private static void assertReceived(NativeFreshSnapshotPort.Received received,Replay replay)throws IOException {
        var ack=received.acknowledgement();var frame=received.originalFrame();
        NativeFreshSnapshotPort.verifyOriginal(ack,frame,received.snapshotReceived());
        var custody=ack.custody().orElseThrow();custody.verify(ack);
        assertEquals(custody.session(),frame.session());assertEquals(replay.ids.getLast(),ack.requestId());
        assertTrue(custody.writeCompleted().order().compareTo(received.snapshotReceived().order())<0);
        assertTrue(received.snapshotReceived().order().compareTo(custody.responseReceived().order())<0);
        assertArrayEquals(replay.snapshotPacket,frame.originalPacket());assertArrayEquals(replay.ackPacket,ack.originalPacket());
        var snapshot=assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(frame.originalPacket()));
        var state=NativeWire.object(NativeWire.parse(snapshot.state().value()));
        assertTrue(state.get("paused").booleanValue());assertEquals(53144520,state.get("date_raw").intValue());
    }
    private static Instant deadline(){return Instant.now().plusSeconds(10);}
    private static NativePipeEndpoint.Config config() {
        String slash=Character.toString(92);
        return new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"post-ack-read-test","source-test-machine",
                new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),"actual-held-session","source-test",SHA,ADAPTER);
    }
    private static ObjectNode object()throws IOException{return NativeWire.object(NativeWire.parse("{}".getBytes(StandardCharsets.UTF_8)));}
    private static ObjectNode hello()throws IOException {
        var row=object();row.put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",1)
                .put("bridge_version","source-test").put("expected_ck3_sha256",SHA).put("expected_ck3_version","1.19.0.6")
                .put("game_adapter_id",ADAPTER).put("game_adapter_status","ready").put("ck3_build_match",true);
        row.putArray("capabilities").add("game.state.snapshot").add(NativeFreshSnapshotPort.CAPABILITY);return row;
    }
    private static ObjectNode snapshot(String requestId)throws IOException {
        var row=object();row.put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","native:6").put("revision",6)
                .put("read_request_id",requestId).set("state",NativeWire.parse(STATE.getBytes(StandardCharsets.UTF_8)));return row;
    }
    private static ObjectNode ack(String requestId,boolean ok)throws IOException {
        var row=object();row.put("type","command_result").put("protocol_version",1).put("request_id",requestId).put("ok",ok);
        if(ok)row.putObject("result").put("schema",NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id",requestId).put("snapshot_id","native:6").put("revision",6);
        else row.put("error",ERROR);return row;
    }
    private enum Mode {TWO_NEGATIVE_THEN_SUCCESS,NEGATIVE,UNKNOWN_THEN_SUCCESS,PERSISTENT_UNKNOWN,UNKNOWN_THEN_NEGATIVE,OTHER_TEXT,OBJECT_ERROR,NULL_ERROR,ABSENT_ERROR,POSITIVE_WITHOUT_FRAME,ORIGINAL_IO}
    private static final class RecordingPort implements NativeFreshSnapshotPort {
        final NativeGameTransport transport;final List<Instant> deadlines=new ArrayList<>();final List<String> collected=new ArrayList<>();int reads;
        RecordingPort(NativeGameTransport actual){transport=actual;}
        @Override public Result readFreshFullState(Instant deadline)throws InterruptedException {reads++;deadlines.add(deadline);return transport.readFreshFullState(deadline);}
        @Override public Result collectFreshFullState(String id,Instant deadline)throws IOException,InterruptedException {collected.add(id);deadlines.add(deadline);return transport.collectFreshFullState(id,deadline);}
    }
    private static final class Replay implements NativePacketPort {
        final Mode mode;final ArrayDeque<byte[]> packets=new ArrayDeque<>();final List<String> ids=new ArrayList<>();
        final List<String> events=new ArrayList<>();final List<Instant> deadlines=new ArrayList<>();final List<byte[]> negativePackets=new ArrayList<>();
        final IOException emptyReadFailure=new IOException("original software packet read failed");byte[] snapshotPacket,ackPacket;
        Replay(Mode mode)throws IOException {this.mode=mode;add(hello());}
        NativeGameTransport open(int frames){return PostAckReadTransportTestSupport.create(this,config(),frames,64);}
        @Override public void verify() { }
        @Override public void awaitConnection(Instant deadline){deadlines.add(deadline);}
        @Override public byte[] readPacket(Instant deadline)throws IOException {deadlines.add(deadline);if(packets.isEmpty())throw emptyReadFailure;return packets.remove();}
        @Override public void writePacket(byte[] packet,Instant deadline)throws IOException {
            deadlines.add(deadline);var request=NativeWire.object(NativeWire.parse(java.util.Arrays.copyOfRange(packet,4,packet.length)));
            var keys=new HashSet<String>();for(var field:request.properties())keys.add(field.getKey());
            assertEquals(Set.of("type","protocol_version","request_id","step","expected_revision"),keys);
            assertEquals("execute_step",request.get("type").textValue());assertEquals(NativeFreshSnapshotPort.STEP,request.get("step").textValue());
            assertEquals(BigInteger.ONE,request.get("protocol_version").bigIntegerValue());assertEquals(BigInteger.ZERO,request.get("expected_revision").bigIntegerValue());
            String id=request.get("request_id").textValue();assertFalse(ids.contains(id));ids.add(id);events.add("write"+ids.size());
            if(mode==Mode.UNKNOWN_THEN_SUCCESS||mode==Mode.PERSISTENT_UNKNOWN||mode==Mode.UNKNOWN_THEN_NEGATIVE) {
                if(ids.size()==1) {
                    heartbeat(1);heartbeat(2);
                    if(mode==Mode.PERSISTENT_UNKNOWN){heartbeat(3);heartbeat(4);}
                    else if(mode==Mode.UNKNOWN_THEN_SUCCESS)success(id);else negative(ack(id,false));
                } else success(id);
            } else if(mode==Mode.TWO_NEGATIVE_THEN_SUCCESS&&ids.size()>2)success(id);
            else if(mode==Mode.POSITIVE_WITHOUT_FRAME)add(ack(id,true));
            else if(mode!=Mode.ORIGINAL_IO) {
                var row=ack(id,false);
                if(mode==Mode.OTHER_TEXT)row.put("error","prefix "+ERROR+" suffix");
                else if(mode==Mode.OBJECT_ERROR)row.putObject("error").put("message",ERROR);
                else if(mode==Mode.NULL_ERROR)row.putNull("error");
                else if(mode==Mode.ABSENT_ERROR)row.remove("error");
                negative(row);
            }
        }
        void negative(ObjectNode row)throws IOException {byte[] packet=packet(row);negativePackets.add(packet);packets.add(packet);}
        void success(String id)throws IOException {snapshotPacket=packet(snapshot(id));ackPacket=packet(ack(id,true));packets.add(snapshotPacket);packets.add(ackPacket);}
        void heartbeat(int sequence)throws IOException {var row=object();row.put("type","heartbeat").put("protocol_version",1).put("sequence",sequence);add(row);}
        void add(ObjectNode row)throws IOException {packets.add(packet(row));}
        static byte[] packet(ObjectNode row)throws IOException{return NativeWire.packet(StrictJson.canonical(row));}
        @Override public void close() { }
    }
}
