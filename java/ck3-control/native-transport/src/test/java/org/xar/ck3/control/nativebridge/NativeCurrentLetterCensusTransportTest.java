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

/** Real C++ result tokens through the existing transport; only fresh outer IDs are Java DATA. */
class NativeCurrentLetterCensusTransportTest {
    static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    static NativeGameTransport transport(Replay replay){return new NativeGameTransport(replay,new NativePipeEndpoint.Config("\\\\.\\pipe\\letter-set-data","letter-set-data",GAME,"letter-set-session","letter-set-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),64,32);}
    static NativeGameTransport.CoreReceived core(NativeGameTransport t)throws Exception{return assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(Instant.now().plusSeconds(20)));}
    static NativeGameTransport.LetterSetReceived query(NativeGameTransport t)throws Exception{var c=core(t);return assertInstanceOf(NativeGameTransport.LetterSetReceived.class,t.readCurrentLetterSet(c,c.validUntil()));}
    static int actualReplyInstance()throws IOException{return NativeCurrentLetterCensus26785313ProducerTest.frame("reply").instanceId().orElseThrow();}
    @Test void exactActualInstanceReplyIsOnceAndConsumesTheFullPrivateCensus()throws Exception {
        var replay=new Replay("known");try(var t=transport(replay)) {
            var q=query(t);int instance=actualReplyInstance();var prepared=t.prepareCurrentLetterInstanceReply(q,instance);
            assertEquals(q.validUntil(),prepared.deadline());assertEquals(instance,prepared.instanceId());assertEquals(q.frame().source().orElseThrow().exactInstance(instance),prepared.selected());
            var request=NativeWire.decodeExecuteRequest(prepared.originalPacket().value());var fields=NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));
            assertEquals(q.validUntil().toEpochMilli(),fields.get("core_control_deadline_unix_ms").longValue());assertEquals(instance,fields.get("letter_set").get("instance_id").intValue());
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentLetterInstanceReply(prepared));assertSame(ack,t.submitCurrentLetterInstanceReply(prepared));
            var frame=CurrentLetterSetResult.decodeOutcome(ack);assertEquals(CurrentLetterSetResult.Status.REPLY_DISPATCHED,frame.status());assertEquals(frame,prepared.latestFrame().orElseThrow());assertEquals(1,replay.replyWrites);
            int other=q.frame().source().orElseThrow().letters().stream().map(row->row.instanceId().orElseThrow()).filter(id->id!=instance).findAny().orElseThrow();
            assertThrows(IOException.class,()->t.prepareCurrentLetterInstanceReply(q,other));assertEquals(1,replay.replyWrites);
        }
    }
    @Test void absentDesiredInstanceAndNonadmissibleActualRowCannotMintReplies()throws Exception {
        for(String mode:new String[]{"known","nonadmissible"}){var replay=new Replay(mode);try(var t=transport(replay)){var q=query(t);int id=mode.equals("known")?Integer.MAX_VALUE:actualReplyInstance();assertThrows(IOException.class,()->t.prepareCurrentLetterInstanceReply(q,id));assertEquals(0,replay.replyWrites);}}
    }
    @Test void completeEmptyCensusDoesNotChooseAnotherRowOrCreateAnyReply()throws Exception {
        var replay=new Replay("empty");try(var t=transport(replay)){var q=query(t);assertTrue(q.frame().source().orElseThrow().letters().isEmpty());assertThrows(IOException.class,()->t.prepareCurrentLetterInstanceReply(q,actualReplyInstance()));assertEquals(0,replay.replyWrites);}
    }
    @Test void privatePreparationCannotChangeDesiredInstanceOrCrossReceivers()throws Exception {
        var a=new Replay("known");var b=new Replay("known");try(var t=transport(a);var other=transport(b)){
            var q=query(t);assertThrows(IOException.class,()->other.prepareCurrentLetterInstanceReply(q,actualReplyInstance()));
            var p=t.prepareCurrentLetterInstanceReply(q,actualReplyInstance());assertSame(p,t.prepareCurrentLetterInstanceReply(q,actualReplyInstance()));
            int id=q.frame().source().orElseThrow().letters().stream().map(row->row.instanceId().orElseThrow()).filter(n->n!=p.instanceId()).findAny().orElseThrow();
            assertThrows(IOException.class,()->t.prepareCurrentLetterInstanceReply(q,id));assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.submitCurrentLetterInstanceReply(p));assertEquals(0,a.replyWrites);assertEquals(0,b.replyWrites);
        }
    }
    @Test void absentActualCapabilityCannotBeReplacedByACompleteLookingCensus()throws Exception {
        var replay=new Replay("missing-reply");try(var t=transport(replay)){var q=query(t);assertTrue(q.frame().source().orElseThrow().exactInstance(actualReplyInstance()).knownReplyAdmissible());assertThrows(IOException.class,()->t.prepareCurrentLetterInstanceReply(q,actualReplyInstance()));assertEquals(0,replay.replyWrites);}
    }
    @Test void extendedCoreDeadlineRejectsBeforeAnyCensusWrite()throws Exception {
        var replay=new Replay("known");try(var t=transport(replay)){var c=core(t);var out=t.readCurrentLetterSet(c,c.validUntil().plusMillis(1));assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,out.original());assertEquals(0,replay.queries);assertEquals(0,replay.replyWrites);}
    }
    @Test void lostReplyRetainsStickyUnknownAndBlocksAnotherLetterAndOtherCoreEffects()throws Exception {
        var replay=new Replay("lost");try(var t=transport(replay)){var c=core(t);var q=assertInstanceOf(NativeGameTransport.LetterSetReceived.class,t.readCurrentLetterSet(c,c.validUntil()));var p=t.prepareCurrentLetterInstanceReply(q,actualReplyInstance());
            var unknown=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentLetterInstanceReply(p));assertSame(unknown,t.submitCurrentLetterInstanceReply(p));assertSame(unknown,t.submitCoreNormalExit(c,c.validUntil()));
            int other=q.frame().source().orElseThrow().letters().stream().map(row->row.instanceId().orElseThrow()).filter(id->id!=p.instanceId()).findAny().orElseThrow();assertThrows(IOException.class,()->t.prepareCurrentLetterInstanceReply(q,other));assertEquals(1,replay.replyWrites);}
    }
    @Test void changedReplyInstanceLeaseOrAnyCensusRowRetainsOriginalAckAsUnknown()throws Exception {
        for(String mode:new String[]{"wrong-instance","wrong-lease","changed-other-row"}){var replay=new Replay(mode);try(var t=transport(replay)){var q=query(t);var p=t.prepareCurrentLetterInstanceReply(q,actualReplyInstance());var u=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentLetterInstanceReply(p));assertTrue(t.originalIndeterminateCoreAcknowledgement(u.requestId()).isPresent());assertSame(u,t.submitCurrentLetterInstanceReply(p));assertEquals(1,replay.replyWrites);}}
    }
    @Test void malformedOwnerOrIncompleteCensusAfterReadonlyWriteBlocksAllEffects()throws Exception {
        for(String mode:new String[]{"wrong-owner","incomplete"}){var replay=new Replay(mode);try(var t=transport(replay)){var c=core(t);var read=t.readCurrentLetterSet(c,c.validUntil());var u=assertInstanceOf(NativeActionPort.Unknown.class,read.original());assertTrue(t.originalIndeterminateCoreAcknowledgement(u.requestId()).isPresent());assertSame(u,t.submitCoreNormalExit(c,c.validUntil()));assertEquals(0,replay.replyWrites);}}
    }
    @Test void actualEarlyRefusalKeepsSelectedInstanceAndOriginalLeaseWithoutDispatchCredit()throws Exception {
        var replay=new Replay("stale");try(var t=transport(replay)){var q=query(t);var p=t.prepareCurrentLetterInstanceReply(q,actualReplyInstance());var ack=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentLetterInstanceReply(p));assertFalse(ack.nativeOk());var frame=CurrentLetterSetResult.decodeOutcome(ack);assertEquals(CurrentLetterSetResult.Status.STALE_SOURCE,frame.status());assertEquals(p.instanceId(),frame.instanceId().orElseThrow());assertEquals(q.frame().providerGeneration(),frame.providerGeneration());assertEquals(q.frame().querySequence(),frame.querySequence());assertFalse(frame.effectAttempted());assertSame(ack,t.submitCurrentLetterInstanceReply(p));assertEquals(1,replay.replyWrites);}
    }
    static final class Replay implements NativePacketPort {
        final String mode;final ArrayDeque<byte[]> packets=new ArrayDeque<>();boolean closed;int queries,replyWrites;
        Replay(String mode)throws IOException {
            this.mode=mode;var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",7).put("bridge_version","letter-set-data")
                    .put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=h.putArray("capabilities").add(CoreFrame.CAPABILITY).add(CurrentLetterSet.Action.QUERY_LETTERS.capability());if(!mode.equals("missing-reply"))caps.add(CurrentLetterSet.Action.REPLY_KNOWN_INSTANCE.capability());packets.add(NativeWire.packet(StrictJson.canonical(h)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("Letter-set DATA closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant until)throws IOException{verify();}
        public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("Letter-set DATA reply missing");return packets.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException {
            verify();var request=NativeWire.decodeExecuteRequest(packet);ObjectNode token;boolean ok;
            if(request.step().equals(CoreFrame.STEP)){token=NativeWire.object(NativeWire.parse(CoreFramePublicCodec.encode(NativeCurrentLetterCensus26785313ProducerTest.actualCore()).bytes()));ok=true;}
            else {
                var fields=NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));var claim=fields.get("letter_set");String action=claim.get("action").textValue();String role;
                if(mode.equals("known"))retainActualRequest(action,packet);
                if(action.equals("query_letters")){queries++;assertTrue(claim.get("instance_id").isNull());role=mode.equals("empty")?"empty":"multiple";}
                else{replyWrites++;assertEquals(CurrentLetterSet.Action.REPLY_KNOWN_INSTANCE.step(),request.step());assertEquals(actualReplyInstance(),claim.get("instance_id").intValue());if(mode.equals("lost"))return;role=mode.equals("stale")?"stale_reply":"reply";}
                var e=NativeCurrentLetterCensus26785313ProducerTest.envelope(role);token=NativeWire.object(e.get("result"));ok=e.get("ok").booleanValue();
                if(mode.equals("wrong-owner"))((ObjectNode)token.get("owner")).put("connection_generation","8");
                if(mode.equals("incomplete"))((ObjectNode)token.get("source")).put("census_complete",false);
                if(mode.equals("nonadmissible"))for(var row:token.get("source").get("letters"))if(row.get("instance_id").intValue()==actualReplyInstance()){((ObjectNode)row).put("known_reply_admissible",false);((ObjectNode)row.get("options").get(0)).put("native_can_select",false);}
                if(action.equals("reply_known_instance")){
                    if(mode.equals("wrong-instance"))token.put("instance_id",Integer.MAX_VALUE);
                    if(mode.equals("wrong-lease"))token.put("query_sequence","1");
                    if(mode.equals("changed-other-row"))for(var row:token.get("source").get("letters"))if(row.get("instance_id").intValue()!=actualReplyInstance()){((ObjectNode)row).put("opening","explicit changed other census row counterexample");break;}
                }
            }
            var e=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",ok);e.set("result",token);packets.add(NativeWire.packet(StrictJson.canonical(e)));
        }
        public void close(){closed=true;}
        private static void retainActualRequest(String action,byte[] packet)throws IOException {
            String folder=System.getProperty("xar.current267.letter.set.java.requests");if(folder==null)return;
            var path=java.nio.file.Path.of(folder).toAbsolutePath().normalize();if(!path.getRoot().toString().equalsIgnoreCase("D:\\"))throw new IOException("D request artifact root required");
            java.nio.file.Files.createDirectories(path);path=path.resolve(action+".request.json");if(!java.nio.file.Files.exists(path))java.nio.file.Files.write(path,java.util.Arrays.copyOfRange(packet,4,packet.length),java.nio.file.StandardOpenOption.CREATE_NEW);
        }
    }
}
