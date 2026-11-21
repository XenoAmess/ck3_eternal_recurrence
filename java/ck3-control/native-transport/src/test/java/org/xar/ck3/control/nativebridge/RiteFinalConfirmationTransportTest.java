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
/** Real transport/custody, exact C++ effect/result tokens, labelled Java query/Core/Draft replay DATA. */
final class RiteFinalConfirmationTransportTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    private static final class MutableClock extends Clock {
        Instant value=Instant.now();public ZoneId getZone(){return ZoneOffset.UTC;}public Clock withZone(ZoneId zone){if(!zone.equals(ZoneOffset.UTC))throw new IllegalArgumentException("UTC fixture");return this;}public Instant instant(){return value;}
    }
    private static Instant until(MutableClock c){return c.instant().plusSeconds(25);}
    private static NativeGameTransport transport(Replay r,MutableClock c){return new NativeGameTransport(r,new NativePipeEndpoint.Config("\\\\.\\pipe\\rite-final-data","rite-final-data",GAME,"rite-final-session","rite-final-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),32,24,List.of(),c);}
    private static NativeActionPort.AckReceived ack(NativeActionPort.DispatchOutcome value){return assertInstanceOf(NativeActionPort.AckReceived.class,value,()->value instanceof NativeActionPort.Unknown u?u.reason():value.toString());}
    private static NativeGameTransport.RiteDoctrineReceived query(NativeGameTransport t,MutableClock c)throws Exception {
        var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(until(c)));
        var draft=assertInstanceOf(NativeGameTransport.RiteDraftCostsReceived.class,t.readRiteDraftCostsReceived(core,152,core.validUntil()));
        var read=t.readRiteDoctrineReceived(draft,draft.validUntil());return assertInstanceOf(NativeGameTransport.RiteDoctrineReceived.class,read,()->read.toString());
    }
    private static NativeGameTransport.RiteFinalPending open(NativeGameTransport t,MutableClock c)throws Exception {
        var q=query(t,c);var actual=ack(t.submitRiteFinalOpening(q,q.validUntil()));return t.retainRiteFinalPreparation(actual);
    }
    private static NativeGameTransport.RiteFinalReady ready(NativeGameTransport t,NativeGameTransport.RiteFinalPending p,MutableClock c)throws Exception {
        var read=t.readRiteFinalConfirmation(p,until(c));return assertInstanceOf(NativeGameTransport.RiteFinalReady.class,read,()->read.toString());
    }
    @Test void originalStageOneThenActualReadyPreparesAndWritesFinalExactlyOnce()throws Exception {
        var c=new MutableClock();var r=new Replay("success",true);try(var t=transport(r,c)){
            var p=open(t,c);assertArrayEquals(RiteFinalCppFrames.result("confirmation-dispatched-SYNTHETIC-DATA.json").bytes(),p.original().originalResultToken().orElseThrow().bytes());
            var observed=ready(t,p,c);var prepared=t.prepareRiteFinalConfirmation(observed);assertEquals(0,r.finals);
            var before=RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(p.original().outbound().orElseThrow().originalPacket());
            var after=RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(prepared.originalPacket().value());assertEquals(RiteDoctrineFrameV1PublicCodec.acceptFinal(before),after);assertEquals(p.deadline(),prepared.deadline());
            var actual=ack(t.submitRiteFinalConfirmation(prepared));actual.custody().orElseThrow().verify(actual);assertTrue(actual.nativeOk());
            assertArrayEquals(RiteFinalCppFrames.result("final-dispatched-SYNTHETIC-DATA.json").bytes(),actual.originalResultToken().orElseThrow().bytes());
            var frame=RiteDoctrineFrameV1PublicCodec.decodeOutcome(actual);assertTrue(frame.nativeReturned());assertFalse(frame.nativeHandled());
            assertSame(actual,t.submitRiteFinalConfirmation(prepared));assertEquals(1,r.openings);assertEquals(1,r.finals);
        }
    }
    @Test void onlyTypedKnownWaitingCanBeObservedAgainWithoutRepeatingOpeningOrExtendingBody()throws Exception {
        var c=new MutableClock();var r=new Replay("pending",true);try(var t=transport(r,c)){
            var p=open(t,c);var first=t.readRiteFinalConfirmation(p,until(c));var waiting=assertInstanceOf(NativeGameTransport.RiteFinalWaiting.class,first);
            assertEquals(RiteDoctrineFrameV1.Status.FINAL_CONFIRMATION_PENDING,waiting.frame().status());assertFalse(waiting.original().nativeOk());
            assertThrows(NoSuchMethodException.class,()->NativeGameTransport.class.getMethod("prepareRiteFinalConfirmation",NativeGameTransport.RiteFinalWaiting.class));
            var later=ready(t,p,c);var prepared=t.prepareRiteFinalConfirmation(later);ack(t.submitRiteFinalConfirmation(prepared));
            assertEquals(2,r.finalQueries);assertEquals(1,r.openings);assertEquals(1,r.finals);
            assertEquals(RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(p.original().outbound().orElseThrow().originalPacket()).deadlineUnixMs(),RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(prepared.originalPacket().value()).deadlineUnixMs());
        }
    }
    @Test void publicAckCloneAndForeignReceiverCannotMintPendingOrFinalAuthority()throws Exception {
        var c=new MutableClock();var a=new Replay("success",true);var b=new Replay("success",true);try(var t=transport(a,c);var other=transport(b,c)){
            var p=open(t,c);var one=p.original();var clone=new NativeActionPort.AckReceived(one.requestId(),one.nativeOk(),one.originalResultToken(),one.originalFrame(),one.originalPacket(),one.outbound(),one.custody());
            assertEquals(one,clone);assertThrows(IOException.class,()->t.retainRiteFinalPreparation(clone));assertThrows(IOException.class,()->other.retainRiteFinalPreparation(one));
            assertInstanceOf(NativeGameTransport.RiteFinalUnavailable.class,other.readRiteFinalConfirmation(p,until(c)));
            var actual=ready(t,p,c);assertThrows(IOException.class,()->other.prepareRiteFinalConfirmation(actual));assertEquals(0,a.finals);assertEquals(0,b.openings);assertEquals(0,b.finals);
        }
    }
    @Test void wrongOwnerSourceOrLeaseNeverBecomeTypedWaitingOrReady()throws Exception {
        for(String mode:new String[]{"wrong-owner","wrong-source","wrong-lease","unknown-ready"}){
            var c=new MutableClock();var r=new Replay(mode,true);try(var t=transport(r,c)){
                var p=open(t,c);var read=t.readRiteFinalConfirmation(p,until(c));assertInstanceOf(NativeGameTransport.RiteFinalUnavailable.class,read);
                assertEquals(1,r.openings);assertEquals(1,r.finalQueries);assertEquals(0,r.finals);
            }
        }
    }
    @Test void finalUnknownRetainsOriginalIdRawReceiptAndNeverReplaysOrOpensAgain()throws Exception {
        for(String mode:new String[]{"indeterminate","lost-final"}){
            var c=new MutableClock();var r=new Replay(mode,true);try(var t=transport(r,c)){
                var p=open(t,c);var before=ready(t,p,c);var prepared=t.prepareRiteFinalConfirmation(before);
                var unknown=assertInstanceOf(NativeActionPort.Unknown.class,t.submitRiteFinalConfirmation(prepared));assertEquals(prepared.requestId(),unknown.requestId());
                assertSame(unknown,t.submitRiteFinalConfirmation(prepared));assertSame(unknown,t.submitRiteFinalOpening(null,until(c)));assertEquals(1,r.openings);assertEquals(1,r.finals);
                if(mode.equals("indeterminate"))assertTrue(t.originalIndeterminateCoreAcknowledgement(unknown.requestId()).isPresent());
            }
        }
    }
    @Test void expiredOriginalPendingCannotBeGivenAFreshFinalWindow()throws Exception {
        var c=new MutableClock();var r=new Replay("success",true);try(var t=transport(r,c)){
            var p=open(t,c);var prepared=t.prepareRiteFinalConfirmation(ready(t,p,c));c.value=c.value.plusSeconds(60);
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.submitRiteFinalConfirmation(prepared));assertInstanceOf(NativeGameTransport.RiteFinalUnavailable.class,t.readRiteFinalConfirmation(p,until(c)));
            assertEquals(0,r.finals);assertEquals(1,r.openings);assertTrue(p.deadline().isBefore(c.instant()));
        }
    }
    @Test void oldEffectEntryCannotCarryEitherFinalAction()throws Exception {
        var c=new MutableClock();var r=new Replay("success",true);try(var t=transport(r,c)){
            var q=query(t,c);for(var action:new RiteDoctrineFrameV1.Action[]{RiteDoctrineFrameV1.Action.QUERY_FINAL_CONFIRMATION,RiteDoctrineFrameV1.Action.ACCEPT_FINAL_CONFIRMATION})assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.submitRiteDoctrineAction(q,action,q.validUntil()));
            assertEquals(0,r.openings);assertEquals(0,r.finalQueries);assertEquals(0,r.finals);
        }
    }
    @Test void absentFinalCapabilityRefusesBeforeOpeningAnyModal()throws Exception {
        var c=new MutableClock();var r=new Replay("success",false);try(var t=transport(r,c)){
            var q=query(t,c);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.submitRiteFinalOpening(q,q.validUntil()));assertEquals(0,r.openings);assertEquals(0,r.finals);
        }
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();final String mode;boolean closed;int openings,finalQueries,finals;
        Replay(String mode,boolean finalCapability)throws Exception {
            this.mode=mode;var before=RiteFinalCppFrames.frame("confirmation-dispatched-SYNTHETIC-DATA.json");
            var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",before.ownerWitness().orElseThrow().connectionGeneration()).put("bridge_version","rite-final-data").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=hello.putArray("capabilities").add(CoreFrame.CAPABILITY).add(RiteDoctrineFrameV1.CAPABILITY);if(finalCapability)caps.add(RiteDoctrineFrameV1.FINAL_CAPABILITY);packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("Replay DATA source closed");}
        public void verifyCoreControlWindowPolicy()throws IOException{verify();}
        public void awaitConnection(Instant until)throws IOException{verify();}
        public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("Replay result absent");return packets.removeFirst();}
        private byte[] queryBody()throws Exception {
            // Explicit Java query DATA derived from actual selected-before Stage1 facts, not a new C++ original.
            var row=NativeWire.object(NativeWire.parse(RiteFinalCppFrames.result("confirmation-dispatched-SYNTHETIC-DATA.json").bytes()));row.put("action","query").put("status","available").put("effect_attempted",false).put("native_returned",false).put("native_handled",false).put("post_selected_evaluated",false).put("post_selected",false).put("claim_sequence","0");return StrictJson.canonical(row);
        }
        public void writePacket(byte[] packet,Instant until)throws IOException {
            verify();var outgoing=NativeWire.decodeExecuteRequest(packet);byte[] body;boolean ok=true;
            try{
                var query=RiteDoctrineFrameV1.decode(new RawJson(queryBody()));
                if(outgoing.step().equals(CoreFrame.STEP))body=CoreFramePublicCodec.encode(query.coreFrame()).bytes();
                else if(outgoing.step().equals(RiteDraftCostsFrameV2.STEP)){
                    var core=assertInstanceOf(CoreFrame.Partial.class,query.coreFrame());var f=query.facts().orElseThrow();body=RiteDraftCostsFrameV2PublicCodec.encode(new RiteDraftCostsFrameV2.Partial(core,new RiteDraftCostsFrameV2.Draft(f.sourceRiteId(),core.prefix().playedCharacterId(),f.canEdit(),f.pietyCostRaw(),f.pietyMissingSignedRaw(),f.pietyMissingSignedRaw()<=0),query.ownerWitness().orElseThrow())).bytes();
                }else{
                    var request=RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(packet);String file;
                    if(request.action()==RiteDoctrineFrameV1.Action.QUERY){body=queryBody();}
                    else{
                        if(request.action()==RiteDoctrineFrameV1.Action.CONFIRM_EDIT){openings++;file="confirmation-dispatched-SYNTHETIC-DATA.json";}
                        else if(request.action()==RiteDoctrineFrameV1.Action.QUERY_FINAL_CONFIRMATION){finalQueries++;if(mode.equals("unknown-ready"))return;file=mode.equals("pending")&&finalQueries==1?"final-pending-SYNTHETIC-DATA.json":"final-ready-SYNTHETIC-DATA.json";}
                        else if(request.action()==RiteDoctrineFrameV1.Action.ACCEPT_FINAL_CONFIRMATION){finals++;if(mode.equals("lost-final"))return;file=mode.equals("indeterminate")?"final-incoherent-SYNTHETIC-DATA.json":"final-dispatched-SYNTHETIC-DATA.json";}
                        else throw new IOException("Unexpected fixed action");
                        var actual=RiteFinalCppFrames.response(file);body=actual.result().token().orElseThrow().value();ok=actual.nativeOk();
                        if(request.action()==RiteDoctrineFrameV1.Action.QUERY_FINAL_CONFIRMATION&&mode.startsWith("wrong-")){
                            var row=NativeWire.object(NativeWire.parse(body));if(mode.equals("wrong-owner"))NativeWire.object(row.get("owner_witness")).put("connection_generation","8");if(mode.equals("wrong-source"))NativeWire.object(row.get("facts")).put("source_rite_id",153);if(mode.equals("wrong-lease"))row.put("query_sequence","1");body=StrictJson.canonical(row);
                        }
                    }
                }
            }catch(Exception invalid){throw new IOException("Actual C++ token or labelled Java source DATA invalid",invalid);}
            var result=new ByteArrayOutputStream();result.writeBytes(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+outgoing.requestId()+"\",\"ok\":"+ok+",\"result\":").getBytes(StandardCharsets.UTF_8));result.writeBytes(body);result.write('}');packets.add(NativeWire.packet(result.toByteArray()));
        }
        public void close(){closed=true;}
    }
}
