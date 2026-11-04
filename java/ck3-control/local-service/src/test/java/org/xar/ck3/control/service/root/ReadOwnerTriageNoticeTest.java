package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.api.parallel.ResourceLock;
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

/** Real receiver DATA and process stdout operation; no Root/Session or gameplay authority is fabricated. */
@ResourceLock("java.lang.System.out")
final class ReadOwnerTriageNoticeTest {
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

    @Test void realNegativeNoticeFollowsAllPreservationAndPrecedesNextReadonlyWriteOnce() throws Exception {
        var replay=new Replay(Mode.UNKNOWN_NEGATIVES_THEN_SUCCESS);
        try(var transport=replay.open(2)) {
            var port=new RecordingPort(transport,replay);
            var archive=new Archive(root.resolve("first"),replay,Fault.NONE);
            var sink=new NoticeSink(replay,()->{
                assertEquals(1,archive.unknowns);assertEquals(1,archive.acks);assertEquals(1,archive.frames);
                archive.assertOriginals(0);
            },null);
            Instant until=deadline(),began=Instant.now();
            var result=capture(sink,()->read(port,until,archive));
            assertReceived(assertInstanceOf(NativeFreshSnapshotPort.Received.class,result),replay);
            assertEquals(List.of("write1","unknown1","collect1","dispatch1","frame1","notice",
                    "write2","dispatch2","frame2","write3"),replay.events);
            assertEquals(3,port.reads);assertEquals(3,replay.ids.size());assertEquals(3,new HashSet<>(replay.ids).size());
            assertEquals(List.of(replay.ids.getFirst()),port.collected);
            assertEquals(3,archive.originals.size());assertEquals(1,archive.unknowns);
            assertEquals(2,archive.acks);assertEquals(2,archive.frames);assertEquals(2,replay.negativePackets.size());
            archive.assertOriginals(0);archive.assertOriginals(1);
            assertArrayEquals(replay.requests.getFirst(),Files.readAllBytes(archive.directory.resolve("unknown-1.bin")));
            assertNotice(sink,replay,until,began,archive.acknowledgements.getFirst(),false);
            assertEquals(sink.lines.getFirst()+System.lineSeparator(),sink.buffer.toString(StandardCharsets.UTF_8));
            sameDeadline(port,replay,until);
        }
        System.out.println("SOFTWARE_READ_OWNER_NOTICE_DATA unknown_same_id=true archive_before_notice_before_next=true negatives=2 notice_attempts=1 received=true");
    }

    @Test void archivePrimaryFailuresEscapeButDiagnosticSinkFailureAndBoundedErrorsKeepOriginalResults() throws Exception {
        for(Fault fault:List.of(Fault.DISPATCH,Fault.FRAME)) {
            var replay=new Replay(Mode.NEGATIVE);
            try(var transport=replay.open(16)) {
                var port=new RecordingPort(transport,replay);
                var archive=new Archive(root.resolve(fault.name()),replay,fault);
                var sink=new NoticeSink(replay,()->fail("archive failure cannot reach notice"),null);
                Instant until=deadline();
                assertSame(archive.primary,assertThrows(UncheckedIOException.class,()->capture(sink,()->read(port,until,archive))));
                assertEquals(1,archive.faults);assertEquals(1,archive.originals.size());assertEquals(1,port.reads);
                assertEquals(1,replay.ids.size());assertTrue(port.collected.isEmpty());assertEquals(0,sink.attempts);
                assertTrue(sink.lines.isEmpty());assertEquals(0,archive.frames);
                assertEquals(fault==Fault.FRAME?1:0,archive.acks);
                assertEquals(fault==Fault.FRAME?List.of("write1","dispatch1"):List.of("write1"),replay.events);
                sameDeadline(port,replay,until);
            }
        }
        var failedSinkReplay=new Replay(Mode.NEGATIVES_THEN_SUCCESS);
        try(var transport=failedSinkReplay.open(16)) {
            var port=new RecordingPort(transport,failedSinkReplay);
            var archive=new Archive(root.resolve("sink"),failedSinkReplay,Fault.NONE);
            var sentinel=new IllegalStateException("actual notice stdout failure");
            var sink=new NoticeSink(failedSinkReplay,()->{
                assertEquals(1,archive.acks);assertEquals(1,archive.frames);archive.assertOriginals(0);
            },sentinel);
            Instant until=deadline();
            var result=capture(sink,()->read(port,until,archive));
            assertReceived(assertInstanceOf(NativeFreshSnapshotPort.Received.class,result),failedSinkReplay);
            assertSame(sentinel,sink.thrown);assertEquals(1,sink.attempts);assertEquals(0,sink.buffer.size());
            assertEquals(3,port.reads);assertTrue(port.collected.isEmpty());assertEquals(2,archive.acks);assertEquals(2,archive.frames);
            assertEquals(List.of("write1","dispatch1","frame1","notice","write2","dispatch2","frame2","write3"),failedSinkReplay.events);
            archive.assertOriginals(0);archive.assertOriginals(1);sameDeadline(port,failedSinkReplay,until);
        }
        for(Mode mode:List.of(Mode.PERSISTENT_UNKNOWN,Mode.POSITIVE_WITHOUT_FRAME)) {
            var replay=new Replay(mode);
            try(var transport=replay.open(mode==Mode.PERSISTENT_UNKNOWN?2:16)) {
                var port=new RecordingPort(transport,replay);
                var archive=new Archive(root.resolve(mode.name()),replay,Fault.NONE);
                var sink=new NoticeSink(replay,()->fail("uncompleted or positive original cannot trigger negative notice"),null);
                Instant until=deadline();
                var unavailable=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,capture(sink,()->read(port,until,archive)));
                assertSame(archive.originals.getLast(),unavailable);assertEquals(1,port.reads);assertEquals(1,replay.ids.size());
                assertEquals(0,sink.attempts);assertEquals(0,archive.frames);assertTrue(unavailable.originalFrame().isEmpty());
                if(mode==Mode.PERSISTENT_UNKNOWN) {
                    assertInstanceOf(NativeActionPort.Unknown.class,unavailable.dispatch());assertEquals(2,archive.unknowns);assertEquals(0,archive.acks);
                    assertEquals(List.of(replay.ids.getFirst()),port.collected);
                    assertEquals(List.of("write1","unknown1","collect1","unknown2"),replay.events);
                    for(int index=1;index<=2;index++)assertArrayEquals(replay.requests.getFirst(),Files.readAllBytes(archive.directory.resolve("unknown-"+index+".bin")));
                } else {
                    assertTrue(assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.dispatch()).nativeOk());
                    assertEquals(1,archive.acks);assertEquals(0,archive.unknowns);assertTrue(port.collected.isEmpty());
                    assertEquals(List.of("write1","dispatch1"),replay.events);
                }
                sameDeadline(port,replay,until);
            }
        }
        var longReplay=new Replay(Mode.LONG_ERROR);
        try(var transport=longReplay.open(16)) {
            var port=new RecordingPort(transport,longReplay);
            var archive=new Archive(root.resolve("long"),longReplay,Fault.NONE);
            var sink=new NoticeSink(longReplay,()->archive.assertOriginals(0),null);
            Instant until=deadline(),began=Instant.now();
            var unavailable=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,capture(sink,()->read(port,until,archive)));
            assertSame(archive.originals.getFirst(),unavailable);assertFalse(assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.dispatch()).nativeOk());
            assertEquals(1,port.reads);assertEquals(1,longReplay.ids.size());assertTrue(port.collected.isEmpty());
            assertEquals(1,archive.acks);assertEquals(1,archive.frames);assertEquals(List.of("write1","dispatch1","frame1","notice"),longReplay.events);
            assertNotice(sink,longReplay,until,began,archive.acknowledgements.getFirst(),true);sameDeadline(port,longReplay,until);
        }
        System.out.println("SOFTWARE_READ_OWNER_NOTICE_DATA archive_dispatch_and_frame_primary=true failed_sink_no_retry=true unknown_positive_no_notice=true long_error_bounded=true");
    }

    @FunctionalInterface private interface ReadCall { NativeFreshSnapshotPort.Result read() throws IOException,InterruptedException; }
    private static NativeFreshSnapshotPort.Result capture(NoticeSink sink,ReadCall call) throws IOException,InterruptedException {
        PrintStream original=System.out;
        try {System.setOut(sink);return call.read();} finally {System.setOut(original);}
    }
    private static NativeFreshSnapshotPort.Result read(RecordingPort port,Instant until,Consumer<NativeFreshSnapshotPort.Unavailable> archive) throws IOException,InterruptedException {
        return RootAdvanceInfrastructureFactory.readAvailableFreshSnapshot(port,until,Clock.systemUTC(),3,archive);
    }
    private static void assertNotice(NoticeSink sink,Replay replay,Instant until,Instant began,NativeActionPort.AckReceived ack,boolean longError) throws IOException {
        assertEquals(1,sink.attempts);assertEquals(1,sink.lines.size());String line=sink.lines.getFirst();
        assertFalse(line.contains("\n"));assertFalse(line.contains("\r"));assertTrue(line.getBytes(StandardCharsets.UTF_8).length<=8192);
        var row=NativeWire.object(NativeWire.parse(line.getBytes(StandardCharsets.UTF_8)));
        assertEquals("xar.root-read-owner-triage/v1",row.get("schema").textValue());assertEquals("OWNER_UI_TRIAGE_REQUIRED",row.get("status").textValue());
        assertEquals(replay.ids.getFirst(),row.get("read_request_id").textValue());assertEquals(ack.requestId(),row.get("read_request_id").textValue());
        Instant observed=Instant.parse(row.get("observed_at_utc").textValue());assertFalse(observed.isBefore(began));assertFalse(observed.isAfter(Instant.now()));
        assertEquals(until.toString(),row.get("observation_deadline_utc").textValue());assertEquals(3,row.get("maximum_attempts").intValue());assertEquals(1,row.get("read_attempt").intValue());
        assertTrue(row.get("action_scope_id").isNull());assertEquals("NOT_HELD_IN_THIS_READER",row.get("command_deadline_status").textValue());
        assertEquals("PRESERVED_BY_CALLBACK_NOT_EXPOSED_TO_READER",row.get("artifact_refs_status").textValue());
        assertTrue(row.get("archive_callbacks_completed").booleanValue());assertTrue(row.get("original_frame_present").booleanValue());
        assertFalse(row.get("native_ok").booleanValue());assertEquals("VALUE",row.get("native_error_presence").textValue());
        assertFalse(row.get("ui_block_confirmed").booleanValue());assertFalse(row.get("native_cause_confirmed").booleanValue());assertTrue(row.get("diagnostic_only").booleanValue());
        var original=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(ack.originalPacket()));
        byte[] token=original.error().token().orElseThrow().value();assertEquals(token.length,row.get("native_error_token_bytes").intValue());
        ack.custody().orElseThrow().verify(ack);
        if(longError){assertTrue(token.length>1024);assertTrue(row.get("native_error_omitted_over_bound").booleanValue());assertFalse(row.has("native_error"));}
        else {assertTrue(token.length<=1024);assertEquals(ERROR,row.get("native_error").textValue());assertFalse(row.has("native_error_omitted_over_bound"));}
    }
    private static void sameDeadline(RecordingPort port,Replay replay,Instant until) {
        assertFalse(port.deadlines.isEmpty());assertFalse(replay.deadlines.isEmpty());
        for(Instant original:port.deadlines)assertSame(until,original);
        for(Instant original:replay.deadlines)assertEquals(until,original);
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
        return new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"read-owner-notice-test","source-test-machine",
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
    private enum Mode {UNKNOWN_NEGATIVES_THEN_SUCCESS,NEGATIVES_THEN_SUCCESS,NEGATIVE,PERSISTENT_UNKNOWN,POSITIVE_WITHOUT_FRAME,LONG_ERROR}
    private enum Fault {NONE,DISPATCH,FRAME}
    private static final class RecordingPort implements NativeFreshSnapshotPort {
        final NativeGameTransport transport;final Replay replay;final List<Instant> deadlines=new ArrayList<>();final List<String> collected=new ArrayList<>();int reads;
        RecordingPort(NativeGameTransport actual,Replay script){transport=actual;replay=script;}
        @Override public Result readFreshFullState(Instant until)throws InterruptedException {reads++;deadlines.add(until);return transport.readFreshFullState(until);}
        @Override public Result collectFreshFullState(String id,Instant until)throws IOException,InterruptedException {
            collected.add(id);deadlines.add(until);replay.events.add("collect"+collected.size());return transport.collectFreshFullState(id,until);
        }
    }
    private static final class Replay implements NativePacketPort {
        final Mode mode;final ArrayDeque<byte[]> packets=new ArrayDeque<>();final List<String> ids=new ArrayList<>(),events=new ArrayList<>();
        final List<Instant> deadlines=new ArrayList<>();final List<byte[]> requests=new ArrayList<>(),negativePackets=new ArrayList<>(),negativeFrames=new ArrayList<>();
        byte[] snapshotPacket,ackPacket;
        Replay(Mode actual)throws IOException {mode=actual;add(hello());}
        NativeGameTransport open(int frames){return PostAckReadTransportTestSupport.create(this,config(),frames,64);}
        @Override public void verify() { }
        @Override public void awaitConnection(Instant until){deadlines.add(until);}
        @Override public byte[] readPacket(Instant until)throws IOException {deadlines.add(until);if(packets.isEmpty())throw new IOException("unexpected additional software packet read");return packets.remove();}
        @Override public void writePacket(byte[] packet,Instant until)throws IOException {
            deadlines.add(until);var request=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(packet,4,packet.length)));
            var keys=new HashSet<String>();for(var field:request.properties())keys.add(field.getKey());
            assertEquals(Set.of("type","protocol_version","request_id","step","expected_revision"),keys);
            assertEquals("execute_step",request.get("type").textValue());assertEquals(NativeFreshSnapshotPort.STEP,request.get("step").textValue());
            assertEquals(BigInteger.ONE,request.get("protocol_version").bigIntegerValue());assertEquals(BigInteger.ZERO,request.get("expected_revision").bigIntegerValue());
            String id=request.get("request_id").textValue();assertFalse(ids.contains(id));ids.add(id);requests.add(packet.clone());events.add("write"+ids.size());
            if(mode==Mode.PERSISTENT_UNKNOWN){heartbeat(1);heartbeat(2);heartbeat(3);heartbeat(4);}
            else if(mode==Mode.POSITIVE_WITHOUT_FRAME)add(ack(id,true));
            else if((mode==Mode.UNKNOWN_NEGATIVES_THEN_SUCCESS||mode==Mode.NEGATIVES_THEN_SUCCESS)&&ids.size()>2)success(id);
            else {
                if(mode==Mode.UNKNOWN_NEGATIVES_THEN_SUCCESS&&ids.size()==1){heartbeat(1);heartbeat(2);}
                var row=ack(id,false);if(mode==Mode.LONG_ERROR)row.putObject("error").put("message","x".repeat(2048));
                byte[] frame=packet(snapshot(id)),response=packet(row);negativeFrames.add(frame);negativePackets.add(response);packets.add(frame);packets.add(response);
            }
        }
        void success(String id)throws IOException {snapshotPacket=packet(snapshot(id));ackPacket=packet(ack(id,true));packets.add(snapshotPacket);packets.add(ackPacket);}
        void heartbeat(int sequence)throws IOException {var row=object();row.put("type","heartbeat").put("protocol_version",1).put("sequence",sequence);add(row);}
        void add(ObjectNode row)throws IOException {packets.add(packet(row));}
        static byte[] packet(ObjectNode row)throws IOException{return NativeWire.packet(StrictJson.canonical(row));}
        @Override public void close() { }
    }
    private static final class Archive implements Consumer<NativeFreshSnapshotPort.Unavailable> {
        final Path directory;final Replay replay;final Fault fault;
        final UncheckedIOException primary=new UncheckedIOException(new IOException("actual software archive failure"));
        final List<NativeFreshSnapshotPort.Unavailable> originals=new ArrayList<>();final List<NativeActionPort.AckReceived> acknowledgements=new ArrayList<>();
        int unknowns,acks,frames,faults;
        Archive(Path destination,Replay script,Fault failure){directory=destination;replay=script;fault=failure;}
        @Override public void accept(NativeFreshSnapshotPort.Unavailable unavailable) {
            originals.add(unavailable);
            try {
                Files.createDirectories(directory);
                if(unavailable.dispatch() instanceof NativeActionPort.Unknown unknown) {
                    Files.write(directory.resolve("unknown-"+(unknowns+1)+".bin"),unknown.originalRequestPacket());
                    replay.events.add("unknown"+(++unknowns));return;
                }
                var ack=assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.dispatch());ack.custody().orElseThrow().verify(ack);
                if(fault==Fault.DISPATCH){faults++;throw primary;}
                Files.write(directory.resolve("ack-"+(acks+1)+".bin"),ack.originalPacket());acknowledgements.add(ack);replay.events.add("dispatch"+(++acks));
                if(unavailable.originalFrame().isPresent()) {
                    if(fault==Fault.FRAME){faults++;throw primary;}
                    Files.write(directory.resolve("frame-"+acks+".bin"),unavailable.originalFrame().orElseThrow().originalPacket());replay.events.add("frame"+(++frames));
                }
            } catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        void assertOriginals(int index) {
            try {
                var ack=acknowledgements.get(index);ack.custody().orElseThrow().verify(ack);
                assertArrayEquals(replay.negativePackets.get(index),Files.readAllBytes(directory.resolve("ack-"+(index+1)+".bin")));
                assertArrayEquals(ack.originalPacket(),Files.readAllBytes(directory.resolve("ack-"+(index+1)+".bin")));
                assertArrayEquals(replay.negativeFrames.get(index),Files.readAllBytes(directory.resolve("frame-"+(index+1)+".bin")));
            } catch(IOException failure){throw new UncheckedIOException(failure);}
        }
    }
    private static final class NoticeSink extends PrintStream {
        final ByteArrayOutputStream buffer;final Replay replay;final Runnable before;final RuntimeException failure;
        final List<String> lines=new ArrayList<>();int attempts;RuntimeException thrown;
        NoticeSink(Replay script,Runnable verifyArchive,RuntimeException sentinel){this(new ByteArrayOutputStream(),script,verifyArchive,sentinel);}
        private NoticeSink(ByteArrayOutputStream bytes,Replay script,Runnable verifyArchive,RuntimeException sentinel){super(bytes,true,StandardCharsets.UTF_8);buffer=bytes;replay=script;before=verifyArchive;failure=sentinel;}
        @Override public void println(String line) {
            attempts++;before.run();lines.add(line);replay.events.add("notice");
            if(failure!=null){thrown=failure;throw failure;}super.println(line);
        }
    }
}
