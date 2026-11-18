package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
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
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact C++ Snapshot DATA through the real software receiver. ACKs and HELLOs are explicit
 * software protocol fixtures, never original C++ ACKs, live Game evidence or Driver/Root adoption. */
final class NativeFreshFullState1210CppProducerTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_1210;
    private static final String ADAPTER="ck3-1.21.0-msvc-x64",BRIDGE="software-full1210";
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private record Input(String name,int bytes,String sha256) { }
    private record Cpp(byte[] envelope,byte[] state,String snapshotId,BigInteger revision) { }
    private static final Input BASE=new Input("full-snapshot-producer-002.json",1171,"5eca02fea7c3f5095d675238f59b69b8d166ed17a0bd4c208b0e133700d7e550");
    private static final Input SIGNED=new Input("full-snapshot-producer-102.json",1322,"a27f2dd30ad69b8927a133509a25be216bf7ce250fdf0a9b325bece78d355ae5");
    private static final Input EXTREME=new Input("full-snapshot-producer-202.json",1180,"d0fc50433b8e3e30e35a81b44d87f307213692646613fdc371970e1d5784f12a");
    private static final Input MANIFEST=new Input("FULL-SNAPSHOT-PRODUCER02.json",1053,"be2a4004b0ad1312708fd3b393b8cedca85b14a6da64bb2d807aa7eba631298b");
    private static final Input GOLD=new Input("personal-gold-producer-partial01.json",1233,"06fcc7b418e46dff6a27ab72533ca7b8444077d33ccc7aaeadd07cfbc93d208f");
    private static final Input ACTOR=new Input("actor-foundation-producer-empty01.json",1582,"e7c66e80cd0f45e238de06957de5b7e9789bdfae51f0c7c3c5d2b85e0dff57a0");

    @Test void threeOriginalCppStatesRetainSignedFamiliesAndInt64ExtremesAcrossReceiveAndReplay() throws Exception {
        for(var input:List.of(BASE,SIGNED,EXTREME)) {
            var cpp=cpp(input);
            try(var f=new Fixture(cpp,hello(),BUILD.executableSha256(),ADAPTER,Mode.NORMAL,null)) {
                var received=f.received();original(received,f,cpp);
                var actual=received.originalFrame();
                var semantic=DriverObservationAssembler.canonicalNativeState(actual).semantic();
                var tree=DriverJson.toNode(semantic);var actor=tree.path("played_character");
                assertEquals(input==SIGNED?-2130706431:1,actor.path("character_id").intValue());
                assertEquals(42,actor.path("stress_points").intValue());assertEquals("native",actor.path("source").textValue());
                assertEquals(123456,tree.path("date_raw").intValue());assertEquals(5,tree.path("speed").intValue());
                assertTrue(tree.path("paused").booleanValue());assertTrue(tree.path("map_ready").booleanValue());
                if(input==EXTREME) {
                    assertTrue(actor.path("betrothed_id").isNull());assertTrue(actor.path("primary_spouse_id").isNull());
                    assertEquals(0,actor.path("spouse_ids").size());
                } else {
                    assertEquals(-2113929214,actor.path("betrothed_id").intValue());assertEquals(0,actor.path("primary_spouse_id").intValue());
                    assertEquals(2,actor.path("spouse_ids").size());assertEquals(0,actor.path("spouse_ids").get(0).intValue());
                    assertEquals(-16777213,actor.path("spouse_ids").get(1).intValue());
                }
                assertEquals(input==EXTREME?Long.MIN_VALUE:-1234567L,tree.path("played_character_gold").path("raw").longValue());
                assertEquals(input==EXTREME?Long.MAX_VALUE:2222222L,tree.path("played_character_prestige").path("raw").longValue());
                assertEquals(-333333L,tree.path("played_character_piety").path("raw").longValue());
                for(String resource:List.of("gold","prestige","piety"))assertEquals(100000,tree.path("played_character_"+resource).path("scale").intValue());
                if(input==SIGNED) {
                    assertEquals(42,tree.path("active_event").path("instance_id").intValue());
                    assertEquals(-2097152000,tree.path("pending_character_interaction").path("instance_id").intValue());
                    assertEquals(-16777213,tree.path("pending_character_interaction").path("sender_character_id").intValue());
                }
                // Public archived DATA copy only: no private Received or accepted occurrence is constructed.
                var replay=new ObservedFrame(actual.session(),actual.snapshotId(),actual.nativeRevision(),new RawJson(actual.state().bytes()),actual.originalPacket(),actual.observedAt());
                assertEquals(DriverObservationAssembler.originalNativeState(actual),DriverObservationAssembler.originalNativeState(replay));
                var replaySemantic=DriverObservationAssembler.canonicalNativeState(replay).semantic();
                assertEquals(semantic,replaySemantic);
                assertEquals(DriverObservationAssembler.bindingSha256(semantic),DriverObservationAssembler.bindingSha256(replaySemantic));
                f.actual.acceptedSnapshotRevision(actual).requireOriginal(actual);
                assertThrows(IOException.class,()->f.actual.acceptedSnapshotRevision(replay));
            }
        }
    }

    @Test void missingCapabilitiesAndMixedHelloTuplesRefuseBeforeAnyRequestWrite() throws Exception {
        var cpp=cpp(BASE);
        for(String changed:List.of("read-capability","snapshot-capability","version","hash","adapter","pid")) {
            var hello=hello();
            switch(changed) {
                case "read-capability" -> hello.putArray("capabilities").add("game.state.snapshot");
                case "snapshot-capability" -> hello.putArray("capabilities").add(NativeFreshSnapshotPort.CAPABILITY);
                case "version" -> hello.put("expected_ck3_version","1.21.0.0");
                case "hash" -> hello.put("expected_ck3_sha256",ExactCk3Build.CK3_12004.executableSha256());
                case "adapter" -> hello.put("game_adapter_id","ck3-1.20.0.4-msvc-x64");
                case "pid" -> hello.put("pid",GAME.pid()+1);
                default -> throw new AssertionError(changed);
            }
            try(var f=new Fixture(cpp,hello,BUILD.executableSha256(),ADAPTER,Mode.NORMAL,null)) {
                var unavailable=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,f.actual.readFreshFullState(f.deadline),changed);
                var zero=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,unavailable.dispatch(),changed);
                assertEquals(0,zero.proof().requestBytesWritten());assertTrue(unavailable.originalFrame().isEmpty());
                assertTrue(f.actual.latestAcceptedSnapshotRevision().isEmpty());counts(f,0);
            }
        }
    }

    @Test void wrongRootActorTuplesAndMissingMarkersRetainActualRejectedPacketWithoutAFullReceipt() throws Exception {
        var cpp=cpp(BASE);
        for(String location:List.of("root","actor"))for(String changed:List.of("schema","version","hash","adapter","backend","missing")) {
            var state=NativeWire.object(NativeWire.parse(cpp.state())).deepCopy();
            var target=location.equals("root")?state:(ObjectNode)state.get("played_character");
            switch(changed) {
                case "schema" -> target.put("schema","unqualified-full-state");
                case "version" -> target.put("game_version",ExactCk3Build.CK3_12004.version());
                case "hash" -> target.put("executable_sha256",ExactCk3Build.CK3_12004.executableSha256());
                case "adapter" -> target.put("adapter_id","ck3-1.20.0.4-msvc-x64");
                case "backend" -> target.put("backend","ck3-1.20.0.4-native-headless-main-thread");
                case "missing" -> target.remove("schema");
                default -> throw new AssertionError(changed);
            }
            // Explicit negative derivative; these changed bytes are never labelled as a C++ oracle.
            try(var f=new Fixture(cpp,hello(),BUILD.executableSha256(),ADAPTER,Mode.NORMAL,StrictJson.canonical(state))) {
                rejected(f);counts(f,1);
            }
        }
    }

    @Test void matchingReadIdRequiresIndependentSnapshotBeforeAckAndUnknownNeverResubmits() throws Exception {
        var cpp=cpp(BASE);
        try(var f=new Fixture(cpp,hello(),BUILD.executableSha256(),ADAPTER,Mode.NORMAL,null)) {
            var first=f.received();original(first,f,cpp);
            var second=f.received();NativeFreshSnapshotPort.verifyAfter(first.acknowledgement(),second);
            NativeFreshSnapshotPort.verifyAfterOriginal(first.acknowledgement(),second.acknowledgement(),second.originalFrame(),second.snapshotReceived());
            assertNotEquals(first.acknowledgement().requestId(),second.acknowledgement().requestId());
            assertArrayEquals(first.originalFrame().state().bytes(),second.originalFrame().state().bytes());counts(f,2);
        }
        for(var mode:List.of(Mode.BAD_READ_ID,Mode.ACK_ONLY,Mode.ACK_FIRST)) {
            try(var f=new Fixture(cpp,hello(),BUILD.executableSha256(),ADAPTER,mode,null)) {
                var unavailable=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,f.actual.readFreshFullState(f.deadline),mode.name());
                var ack=assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.dispatch());assertTrue(ack.nativeOk());
                assertArrayEquals(f.source.ack,ack.originalPacket());ack.custody().orElseThrow().verify(ack);
                assertTrue(unavailable.originalFrame().isEmpty());assertTrue(unavailable.snapshotReceived().isEmpty());
                counts(f,1);
            }
        }
        try(var f=new Fixture(cpp,hello(),BUILD.executableSha256(),ADAPTER,Mode.NO_RESPONSE,null)) {
            var unavailable=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,f.actual.readFreshFullState(f.deadline));
            var unknown=assertInstanceOf(NativeActionPort.Unknown.class,unavailable.dispatch());
            assertSame(unknown,assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,f.actual.readFreshFullState(f.deadline)).dispatch());
            counts(f,1);
        }
    }

    @Test void genuineCoreGoldAndActorPartialDataCannotBecomeFullSnapshotReceipts() throws Exception {
        var cpp=cpp(BASE);
        var gold=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(fixture(GOLD))));
        var actor=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(fixture(ACTOR))));
        byte[] goldToken=gold.result().token().orElseThrow().value();
        byte[] actorToken=actor.result().token().orElseThrow().value();
        byte[] coreToken=StrictJson.canonical(NativeWire.object(NativeWire.parse(goldToken)).get("core_frame"));
        // Negative envelopes only: real partial result DATA cannot be advertised as a full-state oracle.
        for(byte[] partial:List.of(coreToken,goldToken,actorToken)) {
            try(var f=new Fixture(cpp,hello(),BUILD.executableSha256(),ADAPTER,Mode.NORMAL,partial)) {
                rejected(f);counts(f,1);
            }
        }
    }

    @Test void legacyHelloGatesCannotAdmitFlorinMarkersOrMixedNewVersionTuples() throws Exception {
        var cpp=cpp(BASE);
        for(var tuple:List.of(new Tuple("1.19.0.6","2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86","ck3-1.19.0.6-msvc-x64"),
                new Tuple(ExactCk3Build.CK3_12004.version(),ExactCk3Build.CK3_12004.executableSha256(),"ck3-1.20.0.4-msvc-x64"))) {
            var old=hello().put("expected_ck3_version",tuple.version()).put("expected_ck3_sha256",tuple.hash()).put("game_adapter_id",tuple.adapter());
            try(var f=new Fixture(cpp,old,tuple.hash(),tuple.adapter(),Mode.NORMAL,null)) {rejected(f);counts(f,1);}
            var mixed=old.deepCopy().put("expected_ck3_version",BUILD.version());
            try(var f=new Fixture(cpp,mixed,tuple.hash(),tuple.adapter(),Mode.NORMAL,null)) {
                var unavailable=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,f.actual.readFreshFullState(f.deadline));
                assertEquals(0,assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,unavailable.dispatch()).proof().requestBytesWritten());counts(f,0);
            }
        }
    }
    private record Tuple(String version,String hash,String adapter) { }

    private static void original(NativeFreshSnapshotPort.Received received,Fixture f,Cpp cpp) throws Exception {
        var ack=received.acknowledgement();var frame=received.originalFrame();
        assertTrue(ack.nativeOk());assertEquals(f.source.id,ack.requestId());
        assertArrayEquals(cpp.state(),frame.state().bytes());assertArrayEquals(f.source.snapshot,frame.originalPacket());
        assertArrayEquals(f.source.ack,ack.originalPacket());assertArrayEquals(f.source.request,ack.outbound().orElseThrow().originalPacket());
        var decoded=assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(frame.originalPacket()));
        assertArrayEquals(cpp.state(),decoded.state().value());
        assertEquals(cpp.snapshotId(),frame.snapshotId());assertEquals(cpp.revision(),frame.nativeRevision());
        NativeFreshSnapshotPort.verifyOriginal(ack,frame,received.snapshotReceived());
        var custody=ack.custody().orElseThrow();custody.verify(ack);
        assertTrue(custody.writeEntered().order().compareTo(custody.writeCompleted().order())<0);
        assertTrue(custody.writeCompleted().order().compareTo(received.snapshotReceived().order())<0);
        assertTrue(received.snapshotReceived().order().compareTo(custody.responseReceived().order())<0);
        assertEquals(frame.observedAt(),received.snapshotReceived().observedAt());
        assertEquals(frame.session(),custody.session());counts(f,1);
    }
    private static void rejected(Fixture f) throws Exception {
        var unavailable=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,f.actual.readFreshFullState(f.deadline));
        var ack=assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.dispatch());assertTrue(ack.nativeOk());
        assertArrayEquals(f.source.ack,ack.originalPacket());assertArrayEquals(f.source.request,ack.outbound().orElseThrow().originalPacket());
        ack.custody().orElseThrow().verify(ack);
        assertTrue(unavailable.originalFrame().isEmpty());assertTrue(unavailable.snapshotReceived().isEmpty());
        var production=f.actual.diagnostics().production().orElseThrow();
        assertEquals(BigInteger.ONE,production.receivedSnapshotCount());assertEquals(BigInteger.ONE,production.rejectedSnapshotCount());
        var rejected=production.lastRejectedSnapshot().orElseThrow();assertFalse(rejected.errorType().isBlank());
        assertArrayEquals(f.source.snapshot,rejected.original().originalPacket().value());
        assertTrue(f.actual.latestAcceptedSnapshotRevision().isEmpty());assertTrue(f.actual.latestObservedSnapshot().isEmpty());
    }
    private static void counts(Fixture f,int writes) {
        assertEquals(writes,f.source.writes);assertEquals(writes,f.source.fullWrites);assertEquals(0,f.source.otherWrites);
    }
    private static Cpp cpp(Input input) throws Exception {
        var manifest=NativeWire.object(NativeWire.parse(fixture(MANIFEST)));assertFalse(manifest.path("live").booleanValue());
        var pins=manifest.path("packets");assertTrue(pins.isArray());assertEquals(3,pins.size());int matching=0;
        for(var pin:pins)if(pin.path("path").textValue().replace((char)92,'/').endsWith("/"+input.name())) {
            assertEquals(input.bytes(),pin.path("bytes").intValue());assertEquals(input.sha256(),pin.path("sha256").textValue());matching++;
        }
        assertEquals(1,matching);byte[] body=fixture(input);
        var decoded=assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(NativeWire.packet(body)));
        assertEquals("full-producer-original",NativeWire.object(NativeWire.parse(body)).path("read_request_id").textValue());
        return new Cpp(body,decoded.state().value(),decoded.snapshotId(),decoded.revision());
    }
    private static byte[] fixture(Input input) throws Exception {
        String directory=System.getProperty("xar.native.full1210.fixtures");byte[] body;
        if(directory==null||directory.isBlank()) {
            try(var stream=NativeFreshFullState1210CppProducerTest.class.getResourceAsStream("/newnative/full1210/"+input.name())) {
                if(stream==null)throw new IOException("exact C++ full1210 fixture missing: "+input.name());
                body=stream.readNBytes(input.bytes()+1);
            }
        } else {
            var root=Path.of(directory);if(!root.isAbsolute())throw new IOException("absolute exact C++ fixture directory required");
            try(var stream=Files.newInputStream(root.resolve(input.name()))) {body=stream.readNBytes(input.bytes()+1);}
        }
        assertEquals(input.bytes(),body.length);assertEquals(input.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body)));
        return body;
    }
    private static ObjectNode hello() {
        var row=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",1)
                .put("bridge_version",BRIDGE).put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256())
                .put("game_adapter_id",ADAPTER).put("game_adapter_status","ready").put("ck3_build_match",true);
        row.putArray("capabilities").add("game.state.snapshot").add(NativeFreshSnapshotPort.CAPABILITY);return row;
    }
    private enum Mode { NORMAL,BAD_READ_ID,ACK_ONLY,ACK_FIRST,NO_RESPONSE }
    private static final class Fixture implements AutoCloseable {
        final MutableClock clock=new MutableClock(Instant.now());final Instant deadline=clock.instant().plusSeconds(120);
        final Replay source;final NativeGameTransport actual;
        Fixture(Cpp cpp,ObjectNode hello,String hash,String adapter,Mode mode,byte[] negativeState) throws IOException {
            source=new Replay(cpp,hello,mode,negativeState,clock);String slash=Character.toString(92);
            var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"full1210-software","full1210-software",GAME,"full1210-session",BRIDGE,hash,adapter);
            actual=new NativeGameTransport(source,config,32,16,List.of(),clock);
        }
        NativeFreshSnapshotPort.Received received() throws InterruptedException {
            return assertInstanceOf(NativeFreshSnapshotPort.Received.class,actual.readFreshFullState(deadline));
        }
        @Override public void close() throws IOException {actual.close();}
    }
    private static final class MutableClock extends Clock {
        private final Instant now;MutableClock(Instant now){this.now=now;}
        @Override public ZoneId getZone(){return ZoneOffset.UTC;}
        @Override public Clock withZone(ZoneId zone){if(!ZoneOffset.UTC.equals(zone))throw new IllegalArgumentException("UTC software replay only");return this;}
        @Override public Instant instant(){return now;}
    }

    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();final Cpp cpp;final Mode mode;
        final byte[] negativeState;final Clock clock;int writes,fullWrites,otherWrites;boolean closed;
        String id;byte[] request,snapshot,ack;
        Replay(Cpp cpp,ObjectNode hello,Mode mode,byte[] negativeState,Clock clock) throws IOException {
            this.cpp=cpp;this.mode=mode;this.negativeState=negativeState==null?null:negativeState.clone();this.clock=clock;
            packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        @Override public void verify() throws IOException {if(closed)throw new IOException("software source closed");}
        private void check(Instant until) throws IOException {verify();if(!clock.instant().isBefore(until))throw new IOException("software operation deadline expired");}
        @Override public void awaitConnection(Instant until) throws IOException {check(until);}
        @Override public byte[] readPacket(Instant until) throws IOException {
            check(until);if(packets.isEmpty())throw new IOException("software source has no received original packet");return packets.removeFirst();
        }
        @Override public void writePacket(byte[] outbound,Instant until) throws IOException {
            check(until);var decoded=NativeWire.decodeExecuteRequest(outbound);writes++;
            if(decoded.step().equals(NativeFreshSnapshotPort.STEP))fullWrites++;else otherWrites++;
            assertEquals(NativeFreshSnapshotPort.STEP,decoded.step());assertEquals(Optional.of(BigInteger.ZERO),decoded.expectedRevision());
            assertTrue(decoded.expectedSnapshotRevision().isEmpty());
            assertEquals(0,NativeWire.object(NativeWire.parse(decoded.normalizedAdditionalFields().value())).size());
            id=decoded.requestId();request=outbound.clone();if(mode==Mode.NO_RESPONSE)return;
            String marker=mode==Mode.BAD_READ_ID?id+"-foreign":id;
            String quote=Character.toString(34);
            String oldMarker=quote+"read_request_id"+quote+":"+quote+"full-producer-original"+quote;
            String newMarker=quote+"read_request_id"+quote+":"+quote+marker+quote;
            String body=replaceOnce(new String(cpp.envelope(),StandardCharsets.UTF_8),oldMarker,newMarker);
            if(negativeState!=null)body=replaceOnce(body,new String(cpp.state(),StandardCharsets.UTF_8),new String(negativeState,StandardCharsets.UTF_8));
            snapshot=NativeWire.packet(body.getBytes(StandardCharsets.UTF_8));
            if(negativeState==null) {
                // Only read_request_id changes. The real C++ state token remains byte-for-byte original.
                var state=assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(snapshot));assertArrayEquals(cpp.state(),state.state().value());
            }
            // This is a software protocol ACK, not a Native-produced command_result oracle.
            var result=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);
            result.putObject("result").put("schema",NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id",id)
                    .put("snapshot_id",cpp.snapshotId()).put("revision",cpp.revision());
            ack=NativeWire.packet(StrictJson.canonical(result));
            if(mode==Mode.ACK_FIRST){packets.add(ack.clone());packets.add(snapshot.clone());}
            else {if(mode!=Mode.ACK_ONLY)packets.add(snapshot.clone());packets.add(ack.clone());}
        }
        private static String replaceOnce(String body,String oldToken,String replacement) {
            int index=body.indexOf(oldToken);assertTrue(index>=0);assertEquals(index,body.lastIndexOf(oldToken));
            return body.substring(0,index)+replacement+body.substring(index+oldToken.length());
        }
        @Override public void close(){closed=true;}
    }
}
