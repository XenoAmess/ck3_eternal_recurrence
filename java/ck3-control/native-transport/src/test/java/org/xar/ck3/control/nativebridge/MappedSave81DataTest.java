// Exact81 software selection only; all old61 ACK/old56 receipt DATA remains historical, never81 live custody.
package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayDeque;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Actual SAVE61 ACK bytes are cold DATA. The software HELLO/READ shell is explicitly not a managed Game. */
@org.junit.jupiter.api.condition.EnabledIfSystemProperty(named="xar.save81.inputs",matches=".+")
final class MappedSave81DataTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_1210_STEAM_26757580;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final String BRIDGE="software-save61";
    static byte[] exact(com.fasterxml.jackson.databind.JsonNode row)throws Exception {
        Path p=Path.of(row.path("path").textValue());byte[] b=Files.readAllBytes(p);
        assertEquals(row.path("bytes").longValue(),b.length);
        assertEquals(row.path("sha256").textValue(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b)));
        return b;
    }
    static com.fasterxml.jackson.databind.node.ObjectNode inputs()throws Exception {
        return NativeWire.object(NativeWire.parse(Files.readAllBytes(Path.of(System.getProperty("xar.save81.inputs")))));
    }
    static ExactRef bridge()throws Exception {
        var row=inputs().path("bridge");exact(row);
        return new ExactRef(row.path("path").textValue(),row.path("bytes").longValue(),row.path("sha256").textValue());
    }
    @Test void explicit81RequestDataDoesNotChangeDefaultOrLegacySaveRules()throws Exception {
        var dll=bridge();assertTrue(FullSnapshotClockControl.isMappedSave61Bridge(dll));
        var old=inputs().path("retained_bridge61");assertTrue(FullSnapshotClockControl.isMappedSave61Bridge(new ExactRef(old.path("path").textValue(),old.path("bytes").longValue(),old.path("sha256").textValue())));
        var excluded=inputs().path("unqualified_bridge75");assertFalse(FullSnapshotClockControl.isMappedSave61Bridge(new ExactRef(excluded.path("path").textValue(),excluded.path("bytes").longValue(),excluded.path("sha256").textValue())));
        var prefix=new CoreFrame.Prefix(123456,5,true,0,true,true,31254,true);
        var core=new CoreFrame.Partial(BUILD,prefix);var deadline=Instant.now().plusSeconds(30);
        assertThrows(IllegalArgumentException.class,()->CoreClockControl.request(CoreClockControl.Step.SAVE_CHECKPOINT,core));
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.request(BUILD,"save-checkpoint","native:61",BigInteger.valueOf(61),deadline));
        var full=FullSnapshotClockControl.requestMappedSave61(dll,"native:61",BigInteger.valueOf(61),deadline);
        var f=StrictJson.parse(full.additionalFields().bytes()).path("full_snapshot_clock_control");
        assertEquals(FullSnapshotClockControl.SCHEMA,f.path("schema").textValue());
        assertEquals(BUILD.executableSha256().toUpperCase(java.util.Locale.ROOT),f.path("executable_sha256").textValue());
        assertEquals("native:61",f.path("snapshot_id").textValue());
        var c=CoreClockControl.requestMappedSave61(dll,core);
        assertEquals(CoreClockControl.SCHEMA,StrictJson.parse(c.additionalFields().bytes()).path("core_clock_control").path("schema").textValue());
        assertEquals("game.command.save-checkpoint",c.requiredCapability().orElseThrow());
        assertEquals("save-checkpoint",CoreClockControl.request(CoreClockControl.Step.SAVE_CHECKPOINT,new CoreFrame.Partial(ExactCk3Build.CK3_1210,prefix)).step());
        for(var wrong:List.of(new ExactRef(dll.path(),dll.bytes()-1,dll.sha256()),new ExactRef(dll.path(),dll.bytes(),"0".repeat(64)))) {
            assertFalse(FullSnapshotClockControl.isMappedSave61Bridge(wrong));
            assertThrows(IllegalArgumentException.class,()->CoreClockControl.requestMappedSave61(wrong,core));
            assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.requestMappedSave61(wrong,"native:61",BigInteger.valueOf(61),deadline));
        }
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.requestMappedSave61(dll,"native:60",BigInteger.valueOf(61),deadline));
        assertThrows(IllegalArgumentException.class,()->CoreClockControl.requestMappedSave61(dll,new CoreFrame.Partial(ExactCk3Build.CK3_1210,prefix)));
    }
    @Test void evenExplicit81DataAndFalseHelloCannotSubmitFullSaveWithoutTheRealManagedOwner()throws Exception {
        try(var fixture=new Fixture()) {
            var before=assertInstanceOf(NativeGameTransport.FullClockReceived.class,fixture.transport.readFullClockFrameReceived(fixture.deadline));
            var request=FullSnapshotClockControl.requestMappedSave61(bridge(),before.frame().snapshotId(),before.frame().nativeRevision(),before.validUntil());
            var zero=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,fixture.transport.submitFullClockControl(before,request,before.validUntil()));
            assertTrue(zero.proof().reason().contains("managed source is not installed"));
            assertEquals(0,zero.proof().requestBytesWritten());assertEquals(1,fixture.peer.writes,"only the actual software Full READ shell was written");
        }
    }
    @Test void falseSaveCapabilityCannotSubmitCoreSaveWithoutTheRealManagedOwner()throws Exception {
        try(var fixture=new Fixture()) {
            var before=assertInstanceOf(NativeGameTransport.CoreReceived.class,fixture.transport.readCoreFrameReceived(fixture.deadline));
            var zero=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,fixture.transport.submitCoreClockControl(before,CoreClockControl.Step.SAVE_CHECKPOINT,before.validUntil()));
            assertTrue(zero.proof().reason().contains("managed source is not installed"));
            assertEquals(0,zero.proof().requestBytesWritten());assertEquals(1,fixture.peer.writes);
        }
    }
    @Test void allActual61AckBytesStayDataAndNeverClaimPhysicalSaveOrInventMissingOutboundCustody()throws Exception {
        var input=inputs();var manifest=NativeWire.object(NativeWire.parse(exact(input.path("originals"))));int count=0,submitted=0;
        for(var row:manifest.path("files")) {
            if(!row.path("path").textValue().endsWith(".json"))continue;
            byte[] raw=exact(row),packet=NativeWire.packet(raw);
            var frame=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(packet));
            var body=NativeWire.object(NativeWire.parse(frame.result().token().orElseThrow().value()));
            assertEquals(FullSnapshotClockControlResult.SCHEMA,body.path("schema").textValue());
            assertEquals(BUILD.executableSha256().toUpperCase(java.util.Locale.ROOT),body.path("executable_sha256").textValue());
            assertEquals(BUILD.coreFullAdapterId(),body.path("adapter_id").textValue());
            assertEquals("save-checkpoint",body.path("step").textValue());
            assertFalse(body.path("physical_save_confirmed").booleanValue());assertFalse(body.path("complete_snapshot").booleanValue());
            assertEquals(frame.nativeOk(),body.path("accepted").booleanValue());
            if(body.path("queue_status").textValue().equals("submitted")) {
                submitted++;assertTrue(frame.nativeOk());assertTrue(body.path("effect_attempted").booleanValue());
                assertTrue(body.path("full_snapshot_before_verified").booleanValue());
                assertEquals(61,body.path("submission").path("sequence").longValue());
                assertEquals(123456,body.path("submission").path("date_raw").intValue());
                assertEquals("xar_checkpoint",body.path("submission").path("requested_save_name").textValue());
            }
            // The package has ACKs, not actual retained outbound/receive chronology. Do not fabricate a receipt.
            var cold=new NativeActionPort.AckReceived(frame.requestId(),frame.nativeOk(),Optional.of(new RawJson(frame.result().token().orElseThrow().value())),
                    new RawJson(frame.payload().value()),packet);
            assertThrows(IOException.class,()->FullSnapshotClockControlResult.decode(cold,"save-checkpoint"));
            assertArrayEquals(raw,java.util.Arrays.copyOfRange(packet,4,packet.length));count++;
        }
        assertEquals(19,count);assertEquals(1,submitted);
    }
    private static final class Fixture implements AutoCloseable {
        final Clock clock=Clock.fixed(Instant.now(),ZoneOffset.UTC);final Instant deadline=clock.instant().plusSeconds(120);
        final Peer peer;final NativeGameTransport transport;
        Fixture()throws Exception {
            var data=inputs();peer=new Peer(exact(data.path("basic_full")),exact(data.path("basic_core")));
            String s=Character.toString(92);var config=new NativePipeEndpoint.Config(s+s+"."+s+"pipe"+s+"save61-software","save61-software",GAME,"save61-session",BRIDGE,BUILD.executableSha256(),BUILD.coreFullAdapterId());
            transport=new NativeGameTransport(peer,config,32,16,List.of(),clock);
        }
        public void close()throws IOException{transport.close();}
    }
    private static final class Peer implements NativePacketPort {
        final ArrayDeque<byte[]> incoming=new ArrayDeque<>();final byte[] full,core;int writes;boolean closed;
        Peer(byte[] full,byte[] core)throws IOException {
            this.full=full;this.core=core;
            var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",1)
                    .put("bridge_version",BRIDGE).put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256())
                    .put("game_adapter_id",BUILD.coreFullAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            hello.putArray("capabilities").add("game.state.snapshot").add(NativeFreshSnapshotPort.CAPABILITY).add("game.query.core-frame.v1").add("game.command.save-checkpoint");
            incoming.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("software peer closed");}
        public void verifyCoreControlWindowPolicy()throws IOException{verify();}
        public void awaitConnection(Instant deadline)throws IOException{verify();}
        public byte[] readPacket(Instant deadline)throws IOException{verify();if(incoming.isEmpty())throw new IOException("software response missing");return incoming.removeFirst();}
        public void writePacket(byte[] packet,Instant deadline)throws IOException {
            verify();writes++;var request=NativeWire.decodeExecuteRequest(packet);
            if(request.step().equals(NativeFreshSnapshotPort.STEP)) {
                String body=new String(full,StandardCharsets.UTF_8).replace("\"read_request_id\":\"hotfix36-ram-full\"","\"read_request_id\":\""+request.requestId()+"\"");
                byte[] snapshot=NativeWire.packet(body.getBytes(StandardCharsets.UTF_8));var parsed=(NativeWire.Snapshot)NativeWire.decode(snapshot);
                var actual=(NativeWire.Snapshot)NativeWire.decode(NativeWire.packet(full));assertArrayEquals(actual.state().value(),parsed.state().value());
                var ack=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",true);
                ack.putObject("result").put("schema",NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id",request.requestId()).put("snapshot_id",parsed.snapshotId()).put("revision",parsed.revision());
                incoming.add(snapshot);incoming.add(NativeWire.packet(StrictJson.canonical(ack)));return;
            }
            assertEquals("query-core-frame-v1",request.step(),"a SAVE must never reach this software endpoint");
            var original=(NativeWire.CommandResult)NativeWire.decode(NativeWire.packet(core));
            var ack=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",true);
            ack.set("result",NativeWire.parse(original.result().token().orElseThrow().value()));incoming.add(NativeWire.packet(StrictJson.canonical(ack)));
        }
        public void close(){closed=true;}
    }
}
