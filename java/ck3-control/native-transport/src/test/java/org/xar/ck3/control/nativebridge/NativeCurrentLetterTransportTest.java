package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayDeque;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** C++ result tokens through actual transport. Only fresh envelope IDs are Java DATA. */
class NativeCurrentLetterTransportTest {
    static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    static NativeGameTransport transport(Replay r){return new NativeGameTransport(r,new NativePipeEndpoint.Config("\\\\.\\pipe\\letter-data","letter-data",GAME,"letter-session","letter-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),64,32);}
    static NativeGameTransport.CoreReceived core(NativeGameTransport t)throws Exception{return assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(Instant.now().plusSeconds(20)));}
    static NativeGameTransport.LetterReceived query(NativeGameTransport t)throws Exception{var c=core(t);return assertInstanceOf(NativeGameTransport.LetterReceived.class,t.readCurrentLetter(c,c.validUntil()));}
    @Test void knownReplyIsOnceUsesExactOriginalDeadlineAndDoesNotClaimPoststate()throws Exception {
        var replay=new Replay("known");try(var t=transport(replay)){
            var q=query(t);var prepared=t.prepareCurrentLetterReply(q);var fields=NativeWire.object(NativeWire.parse(NativeWire.decodeExecuteRequest(prepared.originalPacket().value()).normalizedAdditionalFields().value()));
            assertEquals(q.validUntil().toEpochMilli(),fields.get("core_control_deadline_unix_ms").longValue());assertEquals(NativeWire.UINT64_MAX.toString(),fields.get("letter").get("query_sequence").textValue());
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentLetterReply(prepared));assertSame(ack,t.submitCurrentLetterReply(prepared));
            var frame=CurrentLetterResult.decodeOutcome(ack);assertEquals(CurrentLetterResult.Status.REPLY_DISPATCHED,frame.status());assertTrue(frame.nativeReturned());assertEquals(1,replay.effects);
            assertEquals(frame,prepared.latestFrame().orElseThrow());assertFalse(frame.encode().bytes().length==0);
        }
    }
    @Test void unknownOrNoLetterObservationCannotMintAnyReply()throws Exception {
        for(String mode:new String[]{"unknown-letter","no-letter","known-invalid"}){var replay=new Replay(mode);try(var t=transport(replay)){var q=query(t);assertThrows(IOException.class,()->t.prepareCurrentLetterReply(q));assertEquals(0,replay.effects);}}
    }
    @Test void foreignPrivateQueryAndExtendedCoreWindowRejectWithZeroWrites()throws Exception {
        var a=new Replay("known");var b=new Replay("known");try(var t=transport(a);var other=transport(b)){
            var q=query(t);assertThrows(IOException.class,()->other.prepareCurrentLetterReply(q));
            var c=core(t);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.readCurrentLetter(c,c.validUntil().plusMillis(1)).original());assertEquals(1,a.queries);assertEquals(0,b.effects);
        }
    }
    @Test void missingActualReplyCapabilityCannotBeReplacedByValidLookingDto()throws Exception {
        var replay=new Replay("missing-reply");try(var t=transport(replay)){var q=query(t);assertTrue(q.frame().source().orElseThrow().knownReplyAdmissible());assertThrows(IOException.class,()->t.prepareCurrentLetterReply(q));assertEquals(0,replay.effects);}
    }
    @Test void lostReplyIsStickyUnknownAndBlocksOtherCoreEffects()throws Exception {
        var replay=new Replay("lost");try(var t=transport(replay)){var c=core(t);var q=assertInstanceOf(NativeGameTransport.LetterReceived.class,t.readCurrentLetter(c,c.validUntil()));var prepared=t.prepareCurrentLetterReply(q);
            var unknown=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentLetterReply(prepared));assertSame(unknown,t.submitCurrentLetterReply(prepared));assertSame(unknown,t.submitCoreNormalExit(c,c.validUntil()));assertEquals(1,replay.effects);}
    }
    @Test void changedReplyLeasePreservesCounterexampleAndNeverReplays()throws Exception {
        var replay=new Replay("wrong-reply-lease");try(var t=transport(replay)){var q=query(t);var prepared=t.prepareCurrentLetterReply(q);var unknown=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentLetterReply(prepared));
            assertTrue(t.originalIndeterminateCoreAcknowledgement(unknown.requestId()).isPresent());assertSame(unknown,t.submitCurrentLetterReply(prepared));assertEquals(1,replay.effects);}
    }
    @Test void malformedOwnerAfterReadonlyWriteBlocksEffectsWithOriginalPacketHeld()throws Exception {
        var replay=new Replay("wrong-owner");try(var t=transport(replay)){var c=core(t);var u=assertInstanceOf(NativeGameTransport.LetterUnavailable.class,t.readCurrentLetter(c,c.validUntil()));var unknown=assertInstanceOf(NativeActionPort.Unknown.class,u.original());
            assertTrue(t.originalIndeterminateCoreAcknowledgement(unknown.requestId()).isPresent());assertSame(unknown,t.submitCoreNormalExit(c,c.validUntil()));assertEquals(0,replay.effects);}
    }
    @Test void actualEarlyExpiredReplyKeepsOriginalLeaseAndRefusalWithoutClaimingDispatch()throws Exception {
        var replay=new Replay("expired-reply");try(var t=transport(replay)){var q=query(t);var prepared=t.prepareCurrentLetterReply(q);var ack=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentLetterReply(prepared));
            assertFalse(ack.nativeOk());var frame=CurrentLetterResult.decodeOutcome(ack);assertEquals(CurrentLetterResult.Status.EXPIRED,frame.status());assertEquals(q.frame().providerGeneration(),frame.providerGeneration());
            assertEquals(q.frame().querySequence(),frame.querySequence());assertFalse(frame.effectAttempted());assertEquals(BigInteger.ZERO,frame.claimSequence());assertSame(ack,t.submitCurrentLetterReply(prepared));assertEquals(1,replay.effects);}
    }
    static final class Replay implements NativePacketPort {
        final String mode;final ArrayDeque<byte[]> packets=new ArrayDeque<>();boolean closed;int queries,effects;
        Replay(String mode)throws IOException {this.mode=mode;var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",7).put("bridge_version","letter-data")
                .put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=h.putArray("capabilities").add(CoreFrame.CAPABILITY).add(CurrentLetter.Action.QUERY_LETTER.capability());if(!mode.equals("missing-reply"))caps.add(CurrentLetter.Action.REPLY_KNOWN.capability());packets.add(NativeWire.packet(StrictJson.canonical(h)));}
        public void verify()throws IOException{if(closed)throw new IOException("Letter DATA closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant until)throws IOException{verify();}
        public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("Letter DATA reply missing");return packets.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException {
            verify();var request=NativeWire.decodeExecuteRequest(packet);ObjectNode token;boolean ok;
            if(request.step().equals(CoreFrame.STEP)){var actual=NativeCurrentLetter26785313ProducerTest.decode(NativeCurrentLetter26785313ProducerTest.token("available.result"));token=NativeWire.object(NativeWire.parse(CoreFramePublicCodec.encode(new CoreFrame.Partial(BUILD,actual.factsBefore().orElseThrow())).bytes()));ok=true;}
            else {
                var fields=NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));var claim=NativeWire.object(fields.get("letter"));String action=claim.get("action").textValue();String name;
                if(mode.equals("known"))retainActualJavaRequest(action,packet);
                if(action.equals("query_letter")){queries++;name=switch(mode){case "unknown-letter","no-letter","known-invalid"->mode+".result";default->"available.result";};}
                else {effects++;assertEquals(CurrentLetter.Action.REPLY_KNOWN.step(),request.step());if(mode.equals("lost"))return;name=mode.equals("expired-reply")?"expired.result":"reply-dispatched.result";}
                var e=NativeCurrentLetter26785313ProducerTest.envelope(name);token=NativeWire.object(e.get("result"));ok=e.get("ok").booleanValue();
                if(mode.equals("wrong-owner"))((ObjectNode)token.get("owner")).put("connection_generation","8");
                if(mode.equals("wrong-reply-lease")&&action.equals("reply_known"))token.put("query_sequence","1");
            }
            var e=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",ok);e.set("result",token);packets.add(NativeWire.packet(StrictJson.canonical(e)));
        }
        public void close(){closed=true;}
        private static void retainActualJavaRequest(String action,byte[] packet)throws IOException {
            String folder=System.getProperty("xar.current267.letter.java.requests");if(folder==null)return;
            var directory=java.nio.file.Path.of(folder).toAbsolutePath().normalize();
            if(!directory.getRoot().toString().equalsIgnoreCase("D:\\"))throw new IOException("D request artifact root required");
            var path=directory.resolve(action+".request.json");
            if(!java.nio.file.Files.exists(path))java.nio.file.Files.write(path,java.util.Arrays.copyOfRange(packet,4,packet.length),java.nio.file.StandardOpenOption.CREATE_NEW);
        }
    }
}
