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
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.DateAdvanceFrameV1;
import org.xar.ck3.control.nativebridge.capabilities.registry.DateAdvanceFrameV1PublicCodec;

/** Genuine C++ result fields through real transport/custody; generated envelope/operation and Core are Java replay DATA. */
final class CurrentDateAdvanceTransportTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    private static final class MutableClock extends Clock {
        Instant value=Instant.now();
        public ZoneId getZone(){return ZoneOffset.UTC;}
        public Clock withZone(ZoneId zone){if(!ZoneOffset.UTC.equals(zone))throw new IllegalArgumentException("UTC DATA only");return this;}
        public Instant instant(){return value;}
        void advance(long seconds){value=value.plusSeconds(seconds);}
    }
    private static NativeGameTransport transport(Replay r,MutableClock clock) {
        var config=new NativePipeEndpoint.Config("\\\\.\\pipe\\current-date-data","current-date-data",GAME,"current-date-session","current-date-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId());
        return new NativeGameTransport(r,config,16,24,List.of(),clock);
    }
    private static NativeGameTransport.CoreReceived core(NativeGameTransport t,MutableClock c)throws Exception{var read=t.readCoreFrameReceived(c.instant().plusSeconds(30));return assertInstanceOf(NativeGameTransport.CoreReceived.class,read,()->read.toString());}
    private static NativeActionPort.AckReceived ack(NativeActionPort.DispatchOutcome actual){return assertInstanceOf(NativeActionPort.AckReceived.class,actual,()->actual instanceof NativeActionPort.Unknown unknown?unknown.reason():actual.toString());}
    @Test void sameActualCorePreparesOriginalBeforeOneActionAndRepeatedCallNeverWritesAgain()throws Exception {
        var c=new MutableClock();var r=new Replay("completed",true);
        try(var t=transport(r,c)) {
            var before=core(t,c);var p=t.prepareCurrentDateAdvance(before,c.instant().plusSeconds(10));
            assertSame(p,t.prepareCurrentDateAdvance(before,p.deadline()));assertEquals(0,r.actions);
            var decoded=DateAdvanceFrameV1PublicCodec.decodeRequestPacket(p.originalPacket().value());assertEquals(p.operationId(),decoded.operationId());
            var ack=ack(t.submitCurrentDateAdvance(p));ack.custody().orElseThrow().verify(ack);
            assertTrue(ack.nativeOk());assertEquals(DateAdvanceFrameV1.Status.SUBMITTED,p.latestFrame().orElseThrow().status());
            assertSame(ack,t.submitCurrentDateAdvance(p));assertEquals(1,r.actions);assertFalse(p.originalUnknown());
            assertThrows(IOException.class,()->t.prepareCurrentDateAdvance(before,before.validUntil()));
        }
    }
    @Test void readonlyStatusAfterOriginalDeadlineKeepsExactCoreOperationAndBodyDeadline()throws Exception {
        var c=new MutableClock();var r=new Replay("completed",true);
        try(var t=transport(r,c)) {
            var p=t.prepareCurrentDateAdvance(core(t,c),c.instant().plusSeconds(10));t.submitCurrentDateAdvance(p);c.advance(32);
            var ack=ack(t.queryCurrentDateAdvance(p,c.instant().plusSeconds(20)));assertTrue(ack.nativeOk());
            var action=DateAdvanceFrameV1PublicCodec.decodeRequestPacket(p.originalPacket().value());
            var lookup=DateAdvanceFrameV1PublicCodec.decodeRequestPacket(ack.outbound().orElseThrow().originalPacket());
            assertEquals(action.expectedCore(),lookup.expectedCore());assertEquals(action.operationId(),lookup.operationId());assertEquals(action.deadlineUnixMs(),lookup.deadlineUnixMs());
            assertTrue(lookup.deadlineUnixMs().longValueExact()<c.instant().toEpochMilli());assertNotEquals(p.requestId(),ack.requestId());
            assertEquals(DateAdvanceFrameV1.Status.COMPLETED,p.latestFrame().orElseThrow().status());assertFalse(p.originalUnknown());assertEquals(1,r.actions);assertEquals(1,r.queries);
        }
    }
    @Test void nativeUnknownRemainsOriginalEvenWhenLaterReadonlyDataClaimsCompleted()throws Exception {
        var c=new MutableClock();var r=new Replay("unknown-action",true);
        try(var t=transport(r,c)) {
            var before=core(t,c);var p=t.prepareCurrentDateAdvance(before,c.instant().plusSeconds(10));
            var unknown=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentDateAdvance(p));assertTrue(p.originalUnknown());
            assertTrue(t.originalIndeterminateCoreAcknowledgement(p.requestId()).isPresent());
            ack(t.queryCurrentDateAdvance(p,c.instant().plusSeconds(20)));
            assertTrue(p.originalUnknown());assertSame(unknown,t.submitCurrentDateAdvance(p));assertThrows(IOException.class,()->t.prepareCurrentDateAdvance(before,before.validUntil()));
            assertSame(unknown,t.submitCoreNormalExit(before,before.validUntil()));assertEquals(1,r.actions);
        }
    }
    @Test void changedClaimOrGenerationIsOriginalUnknownObservationAndCannotComplete()throws Exception {
        for(String mode:new String[]{"wrong-generation","wrong-claim","wrong-core"}) {
            var c=new MutableClock();var r=new Replay(mode,true);
            try(var t=transport(r,c)) {
                var p=t.prepareCurrentDateAdvance(core(t,c),c.instant().plusSeconds(10));t.submitCurrentDateAdvance(p);
                var observed=assertInstanceOf(NativeActionPort.Unknown.class,t.queryCurrentDateAdvance(p,c.instant().plusSeconds(20)));
                assertTrue(observed.rawReturn().isPresent());assertEquals(DateAdvanceFrameV1.Status.SUBMITTED,p.latestFrame().orElseThrow().status());
                assertThrows(IOException.class,()->t.prepareCurrentDateAdvance(core(t,c),c.instant().plusSeconds(10)));assertEquals(1,r.actions);
            }
        }
    }
    @Test void knownCompletionCanUseTrulyNewerActualCoreWithoutPermanentPerProcessBool()throws Exception {
        var c=new MutableClock();var r=new Replay("completed",true);
        try(var t=transport(r,c)) {
            var first=t.prepareCurrentDateAdvance(core(t,c),c.instant().plusSeconds(10));t.submitCurrentDateAdvance(first);t.queryCurrentDateAdvance(first,c.instant().plusSeconds(20));
            var after=core(t,c);assertEquals(first.sourceDateRaw()+24,((CoreFrame.Partial)after.frame()).prefix().dateRaw());
            var second=t.prepareCurrentDateAdvance(after,c.instant().plusSeconds(10));assertNotEquals(first.operationId(),second.operationId());assertNotEquals(first.requestId(),second.requestId());
            assertEquals(1,r.actions); // A new preparation is not a second write or a SAVE.
        }
    }
    @Test void foreignCoreCapabilityAndExtendedOriginalWindowRefuseBeforeActionWrite()throws Exception {
        var c=new MutableClock();var r=new Replay("completed",false);
        try(var t=transport(r,c)){var before=core(t,c);assertThrows(IOException.class,()->t.prepareCurrentDateAdvance(before,before.validUntil()));assertEquals(0,r.actions);}
        var a=new Replay("completed",true);var b=new Replay("completed",true);
        try(var t=transport(a,c);var other=transport(b,c)) {
            var before=core(t,c);assertThrows(IOException.class,()->other.prepareCurrentDateAdvance(before,before.validUntil()));
            assertThrows(IOException.class,()->t.prepareCurrentDateAdvance(before,before.validUntil().plusMillis(1)));
            var p=t.prepareCurrentDateAdvance(before,c.instant().plusSeconds(10));assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.submitCurrentDateAdvance(p));assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.queryCurrentDateAdvance(p,c.instant().plusSeconds(20)));assertEquals(0,a.actions);assertEquals(0,b.actions);
        }
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();final List<byte[]> writes=new ArrayList<>();final String mode;boolean closed;int actions,queries,coreReads;
        Replay(String mode,boolean capability)throws Exception {
            this.mode=mode;var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",DateAdvanceFrameV1.decode(CurrentDateCppFrames.result("submitted-SYNTHETIC-DATA")).ownerWitness().orElseThrow().connectionGeneration())
                    .put("bridge_version","current-date-data").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=hello.putArray("capabilities");caps.add(CoreFrame.CAPABILITY);if(capability)caps.add(DateAdvanceFrameV1.CAPABILITY);packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("DATA endpoint closed");}
        public void verifyCoreControlWindowPolicy()throws IOException{verify();}
        public void awaitConnection(Instant until)throws IOException{verify();}
        public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("DATA reply absent");return packets.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException {
            verify();writes.add(packet.clone());var envelope=NativeWire.decodeExecuteRequest(packet);byte[] body;boolean ok;
            try {
                if(envelope.step().equals(CoreFrame.STEP)) {
                    var p=CurrentDateCppFrames.core().prefix();int date=p.dateRaw()+(coreReads++>0?24:0);
                    var core=new CoreFrame.Partial(BUILD,new CoreFrame.Prefix(date,p.speed(),p.paused(),p.localPlayerId(),p.mapReady(),p.hasPlayedCharacter(),p.playedCharacterId(),p.playedCharacterAlive()));
                    body=CoreFramePublicCodec.encode(core).bytes();ok=true; // Explicit Java Core DATA; Native result core_after is always null.
                } else {
                    var request=DateAdvanceFrameV1PublicCodec.decodeRequestPacket(packet);boolean action=request.step()==DateAdvanceFrameV1.Step.ADVANCE;
                    if(action)actions++;else queries++;
                    String name=action?(mode.equals("unknown-action")?"indeterminate-SYNTHETIC-DATA":"submitted-SYNTHETIC-DATA"):"completed-SYNTHETIC-DATA";
                    var row=NativeWire.object(StrictJson.parse(CurrentDateCppFrames.result(name).bytes()));row.put("operation_id",request.operationId()).put("step",request.step().wire());
                    if(!action&&mode.equals("wrong-generation"))row.put("generation","999");if(!action&&mode.equals("wrong-claim"))row.put("claim_sequence","999");
                    if(!action&&mode.equals("wrong-core"))NativeWire.object(row.get("core_before")).put("local_player_id",999);
                    body=StrictJson.canonical(row);ok=action?row.get("accepted").booleanValue():row.get("claim_found").booleanValue();
                }
            }catch(Exception failure){throw new IOException("Pinned actual serializer DATA unavailable",failure);}
            var out=new ByteArrayOutputStream();out.writeBytes(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+envelope.requestId()+"\",\"ok\":"+ok+",\"result\":").getBytes(StandardCharsets.UTF_8));out.writeBytes(body);out.write('}');packets.add(NativeWire.packet(out.toByteArray()));
        }
        public void close(){closed=true;}
    }
}
