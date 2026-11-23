package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayDeque;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;

/** Original C++ result tokens; HELLO/Core/request-ID wrappers are explicitly Java exchange DATA. */
final class NativeCurrentRiteCreationBlockersTransportTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    private static final class Time extends Clock {
        Instant now=Instant.now();public ZoneId getZone(){return ZoneOffset.UTC;}
        public Clock withZone(ZoneId zone){if(!ZoneOffset.UTC.equals(zone))throw new IllegalArgumentException();return this;}
        public Instant instant(){return now;}Instant until(){return now.plusSeconds(25);}
    }
    private static NativeWire.CommandResult cpp(String name)throws Exception {
        try(var in=NativeCurrentRiteCreationBlockersTransportTest.class.getResourceAsStream("/current267-rite-creation-blockers-cpp-a1021/"+name)) {
            if(in==null)throw new IOException("Original C++ resource missing: "+name);
            return assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(in.readAllBytes())));
        }
    }
    private static CurrentRiteCreationBlockersResult frame(String name)throws Exception{return CurrentRiteCreationBlockersResult.decode(new RawJson(cpp(name).result().token().orElseThrow().value()));}
    private static NativeGameTransport transport(Replay replay,Time clock){return new NativeGameTransport(replay,new NativePipeEndpoint.Config("\\\\.\\pipe\\rite-blockers-data","rite-blockers-data",GAME,"rite-blockers-session-data","rite-blockers-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),64,1024,List.of(),clock);}
    private static NativeGameTransport.CoreReceived core(NativeGameTransport t,Time time)throws Exception{return assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(time.until()));}
    private static NativeGameTransport.RiteCreationBlockersReceived query(NativeGameTransport t,Time time,Replay replay)throws Exception {
        var before=core(t,time);return assertInstanceOf(NativeGameTransport.RiteCreationBlockersReceived.class,t.readCurrentRiteCreationBlockers(before,replay.base().source().orElseThrow().sourceRiteId(),before.validUntil()));
    }
    @Test void falseCanEmptyHiddenAndRichtextNulAreAvailableReadonlyData()throws Exception {
        for(String file:List.of("available-false-can-empty.json","available-hidden-notcreating.json","available-richtext-nul.json","available-actor-zero-rite-zero.json","available-actor-negative-rite-max.json")) {
            var clock=new Time();var replay=new Replay(file,"success",true);
            try(var t=transport(replay,clock)) {
                var q=query(t,clock,replay);q.requireOriginal(t,q.validUntil());var result=q.frame();
                assertArrayEquals(cpp(file).result().token().orElseThrow().value(),q.original().originalResultToken().orElseThrow().bytes());
                assertEquals(frame(file),result);assertFalse(result.source().orElseThrow().nativeCanCreate());
                assertEquals(BigInteger.ZERO,result.claimSequence());assertFalse(result.effectAttempted());assertFalse(result.nativeReturned());assertFalse(result.nativeHandled());assertFalse(result.physicalSaveConfirmed());
                assertEquals(1,replay.queries);
            }
        }
    }
    @Test void privateReceiptRejectsForeignReceiverExpiredDeadlineAndSupersededQuery()throws Exception {
        var clock=new Time();var a=new Replay("available-false-can-empty.json","success",true);var b=new Replay("available-false-can-empty.json","success",true);
        try(var t=transport(a,clock);var other=transport(b,clock)) {
            var first=query(t,clock,a);assertThrows(IOException.class,()->first.requireOriginal(other,first.validUntil()));assertEquals(0,b.queries);
            var latest=query(t,clock,a);assertThrows(IOException.class,()->first.requireOriginal(t,first.validUntil()));latest.requireOriginal(t,latest.validUntil());
            clock.now=latest.validUntil().plusMillis(1);assertThrows(IOException.class,()->latest.requireOriginal(t,latest.validUntil()));assertEquals(2,a.queries);
        }
    }
    @Test void actualQueryMismatchIsOriginalStickyFamilyUnknownWithoutNewRequest()throws Exception {
        for(String mode:List.of("guard-mismatch","facts-drift","owner-drift")) {
            var clock=new Time();var replay=new Replay("available-false-can-empty.json",mode,true);
            try(var t=transport(replay,clock)) {
                var before=core(t,clock);long guard=mode.equals("guard-mismatch")?48:47;
                var first=assertInstanceOf(NativeGameTransport.RiteCreationBlockersUnavailable.class,t.readCurrentRiteCreationBlockers(before,guard,before.validUntil()));
                assertInstanceOf(NativeActionPort.Unknown.class,first.original());
                assertSame(first,t.readCurrentRiteCreationBlockers(before,guard,before.validUntil()));assertEquals(1,replay.queries);
            }
        }
    }
    @Test void cleanupUnknownIsFamilyStickyAndDoesNotRewriteOtherCoreReadResult()throws Exception {
        for(String file:List.of("indeterminate-cleanup.json","indeterminate-partial-samples.json")) {
            var clock=new Time();var replay=new Replay("available-false-can-empty.json",file,true);
            try(var t=transport(replay,clock)) {
                var before=core(t,clock);var first=assertInstanceOf(NativeGameTransport.RiteCreationBlockersUnavailable.class,t.readCurrentRiteCreationBlockers(before,47,before.validUntil()));
                assertInstanceOf(NativeActionPort.Unknown.class,first.original());
                var newCore=core(t,clock);assertSame(first,t.readCurrentRiteCreationBlockers(newCore,47,newCore.validUntil()));assertEquals(1,replay.queries);assertEquals(2,replay.cores);
                assertFalse(frame(file).successful());assertEquals(BigInteger.ZERO,frame(file).claimSequence());
            }
        }
    }
    @Test void knownUnavailableIsPreservedAsOriginalAckNotSourceOrUnknown()throws Exception {
        for(String file:List.of("unavailable-definition.json","expired-before-source.json")) {
            var clock=new Time();var replay=new Replay("available-false-can-empty.json",file,true);
            try(var t=transport(replay,clock)) {
                var before=core(t,clock);var actual=assertInstanceOf(NativeGameTransport.RiteCreationBlockersUnavailable.class,t.readCurrentRiteCreationBlockers(before,47,before.validUntil()));
                var ack=assertInstanceOf(NativeActionPort.AckReceived.class,actual.original());
                assertArrayEquals(cpp(file).result().token().orElseThrow().value(),ack.originalResultToken().orElseThrow().bytes());
                assertFalse(CurrentRiteCreationBlockersResult.decodeOutcome(ack).sourceAvailable());assertEquals(1,replay.queries);
            }
        }
    }
    @Test void missingCapabilityAndInvalidRiteGuardRefuseBeforeReadonlyWrite()throws Exception {
        for(boolean capability:new boolean[]{false,true}) {
            var clock=new Time();var replay=new Replay("available-false-can-empty.json","success",capability);
            try(var t=transport(replay,clock)) {
                var before=core(t,clock);long guard=capability?0xffff_ffffL:47;
                var unavailable=assertInstanceOf(NativeGameTransport.RiteCreationBlockersUnavailable.class,t.readCurrentRiteCreationBlockers(before,guard,before.validUntil()));
                assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,unavailable.original());assertEquals(0,replay.queries);
            }
        }
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> queue=new ArrayDeque<>();final String baseFile,mode;boolean closed;int cores,queries;
        Replay(String baseFile,String mode,boolean capability)throws Exception {
            this.baseFile=baseFile;this.mode=mode;var base=base();var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",base.owner().orElseThrow().connectionGeneration()).put("bridge_version","rite-blockers-data").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=h.putArray("capabilities").add(CoreFrame.CAPABILITY);if(capability)caps.add(CurrentRiteCreationBlockers.CAPABILITY);queue.add(NativeWire.packet(StrictJson.canonical(h)));
        }
        CurrentRiteCreationBlockersResult base()throws Exception{return frame(baseFile);}
        public void verify()throws IOException{if(closed)throw new IOException("Replay DATA closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant d)throws IOException{verify();}
        public byte[] readPacket(Instant d)throws IOException{verify();if(queue.isEmpty())throw new IOException("No replay DATA packet");return queue.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException {
            verify();var request=NativeWire.decodeExecuteRequest(packet);byte[] body;boolean ok=true;
            try {
                if(request.step().equals(CoreFrame.STEP)){cores++;body=CoreFramePublicCodec.encode(new CoreFrame.Partial(BUILD,base().factsBefore().orElseThrow())).bytes();}
                else {
                    assertEquals(CurrentRiteCreationBlockers.STEP,request.step());queries++;
                    var fields=NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));
                    assertEquals(CurrentRiteCreationBlockers.ACTION,NativeWire.object(fields.get("rite_creation_blockers")).get("action").textValue());
                    String file=mode.endsWith(".json")?mode:baseFile;var original=cpp(file);body=original.result().token().orElseThrow().value();ok=original.nativeOk();
                    if(mode.equals("facts-drift")||mode.equals("owner-drift")) {
                        // Explicit negative Java DATA mutation, never a new C++ genuine token.
                        var n=NativeWire.object(NativeWire.parse(body));
                        if(mode.equals("facts-drift"))NativeWire.object(n.get("facts_before")).put("date_raw",53144352);
                        else NativeWire.object(n.get("owner")).put("connection_generation","1");
                        body=StrictJson.canonical(n);
                    }
                }
            }catch(Exception e){throw new IOException("Original blockers token or labelled Java exchange DATA invalid",e);}
            var out=new ByteArrayOutputStream();out.writeBytes(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+request.requestId()+"\",\"ok\":"+ok+",\"result\":").getBytes(StandardCharsets.UTF_8));out.writeBytes(body);out.write('}');queue.add(NativeWire.packet(out.toByteArray()));
        }
        public void close(){closed=true;}
    }
}
