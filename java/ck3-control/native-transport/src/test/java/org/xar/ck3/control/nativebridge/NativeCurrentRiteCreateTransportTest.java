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

/** Real private transport/custody with original C++ result tokens and explicitly labelled Java exchange/Core/draft DATA. */
final class NativeCurrentRiteCreateTransportTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    private static final class Time extends Clock {
        Instant now=Instant.now();public ZoneId getZone(){return ZoneOffset.UTC;}public Clock withZone(ZoneId z){if(!z.equals(ZoneOffset.UTC))throw new IllegalArgumentException();return this;}public Instant instant(){return now;}
        Instant until(){return now.plusSeconds(25);}
    }
    private static NativeWire.CommandResult cpp(String name)throws Exception {
        try(var in=NativeCurrentRiteCreateTransportTest.class.getResourceAsStream("/current267-rite-create-cpp-a01/"+name)){
            if(in==null)throw new IOException("Original C++ resource absent: "+name);
            return assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(in.readAllBytes())));
        }
    }
    private static CurrentRiteCreateResult frame(String name)throws Exception{return CurrentRiteCreateResult.decode(new RawJson(cpp(name).result().token().orElseThrow().value()));}
    private static NativeGameTransport transport(Replay replay,Time clock){return new NativeGameTransport(replay,new NativePipeEndpoint.Config("\\\\.\\pipe\\rite-create-DATA","rite-create-data",GAME,"rite-create-session-DATA","rite-create-DATA",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),64,64,List.of(),clock);}
    private static NativeActionPort.AckReceived ack(NativeActionPort.DispatchOutcome out){return assertInstanceOf(NativeActionPort.AckReceived.class,out,()->out instanceof NativeActionPort.Unknown u?u.reason():out.toString());}
    private record Setup(NativeGameTransport.CoreReceived core,NativeGameTransport.RiteCreateReceived query) { }
    private static Setup query(NativeGameTransport t,Time clock)throws Exception{
        var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(clock.until()));
        var draft=assertInstanceOf(NativeGameTransport.RiteDraftCostsReceived.class,t.readRiteDraftCostsReceived(core,47,core.validUntil()));
        return new Setup(core,assertInstanceOf(NativeGameTransport.RiteCreateReceived.class,t.readCurrentRiteCreate(draft,draft.validUntil())));
    }
    private static NativeGameTransport.RiteCreatePending create(NativeGameTransport t,Time clock)throws Exception{
        var prepared=t.prepareCurrentRiteCreate(query(t,clock).query());return t.retainCurrentRiteCreate(ack(t.submitCurrentRiteCreate(prepared)));
    }
    private static NativeGameTransport.CoreReceived fresh(NativeGameTransport t,NativeGameTransport.RiteCreatePending pending)throws Exception{return assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(pending.deadline()));}
    private static NativeGameTransport.RiteCreateReceived ready(NativeGameTransport t,NativeGameTransport.RiteCreatePending pending,NativeGameTransport.CoreReceived core)throws Exception{return assertInstanceOf(NativeGameTransport.RiteCreateReceived.class,t.readCurrentRiteCreateConfirmation(pending,core,pending.deadline()));}

    @Test void actualCreateAndAcceptNeedPrivateQueriesAndReturnEachVoidReceiptExactlyOnce()throws Exception{
        var clock=new Time();var r=new Replay("success",true);try(var t=transport(r,clock)){
            var q=query(t,clock).query();var prepared=t.prepareCurrentRiteCreate(q);assertEquals(0,r.creates);
            var created=ack(t.submitCurrentRiteCreate(prepared));assertSame(created,t.submitCurrentRiteCreate(prepared));
            assertArrayEquals(cpp("create-dispatched.json").result().token().orElseThrow().value(),created.originalResultToken().orElseThrow().bytes());
            var pending=t.retainCurrentRiteCreate(created);var modal=ready(t,pending,fresh(t,pending));var accept=t.prepareCurrentRiteCreateAcceptance(modal);
            assertEquals(pending.deadline(),accept.deadline());var accepted=ack(t.submitCurrentRiteCreate(accept));assertSame(accepted,t.submitCurrentRiteCreate(accept));
            var f=CurrentRiteCreateResult.decodeOutcome(accepted);assertTrue(f.nativeReturned());assertFalse(f.nativeHandled());assertFalse(f.riteCreated());assertFalse(f.initialBindingConfirmed());
            assertEquals(1,r.creates);assertEquals(1,r.accepts);
        }
    }
    @Test void cleanKnownPendingMayPollOnlyItsOriginalModalAndDeadlineWithoutRepeatingCreate()throws Exception{
        var clock=new Time();var r=new Replay("pending",true);try(var t=transport(r,clock)){
            var pending=create(t,clock);var core=fresh(t,pending);var wait=t.readCurrentRiteCreateConfirmation(pending,core,pending.deadline());
            var waiting=assertInstanceOf(NativeGameTransport.RiteCreateWaiting.class,wait);assertFalse(waiting.original().nativeOk());
            assertEquals(CurrentRiteCreateResult.Status.CONFIRMATION_PENDING,waiting.frame().status());
            assertThrows(NoSuchMethodException.class,()->NativeGameTransport.class.getMethod("prepareCurrentRiteCreateAcceptance",NativeGameTransport.RiteCreateWaiting.class));
            var actual=ready(t,pending,core);ack(t.submitCurrentRiteCreate(t.prepareCurrentRiteCreateAcceptance(actual)));
            assertEquals(1,r.creates);assertEquals(2,r.modalQueries);assertEquals(1,r.accepts);assertTrue(r.allModalDeadlinesSame);
        }
    }
    @Test void actualFalseCanCreateOrCanAcceptIsReadableDataWithoutActionAuthority()throws Exception{
        for(String mode:new String[]{"false-create","false-accept"}){
            var clock=new Time();var r=new Replay(mode,true);try(var t=transport(r,clock)){
                var q=query(t,clock).query();if(mode.equals("false-create")){assertFalse(q.frame().source().orElseThrow().draft().orElseThrow().nativeCanCreate());assertThrows(IOException.class,()->t.prepareCurrentRiteCreate(q));assertEquals(0,r.creates);}
                else{var p=t.retainCurrentRiteCreate(ack(t.submitCurrentRiteCreate(t.prepareCurrentRiteCreate(q))));var actual=ready(t,p,fresh(t,p));assertFalse(actual.frame().source().orElseThrow().confirmation().orElseThrow().nativeCanAccept());assertThrows(IOException.class,()->t.prepareCurrentRiteCreateAcceptance(actual));assertEquals(0,r.accepts);}
            }
        }
    }
    @Test void publicAckCloneAndForeignReceiverCannotMintOriginalCreateOrAccept()throws Exception{
        var clock=new Time();var a=new Replay("success",true);var b=new Replay("success",true);try(var t=transport(a,clock);var other=transport(b,clock)){
            var q=query(t,clock).query();assertThrows(IOException.class,()->other.prepareCurrentRiteCreate(q));var p=createFrom(t,q);
            var original=p.original();var clone=new NativeActionPort.AckReceived(original.requestId(),original.nativeOk(),original.originalResultToken(),original.originalFrame(),original.originalPacket(),original.outbound(),original.custody());assertEquals(original,clone);
            assertThrows(IOException.class,()->t.retainCurrentRiteCreate(clone));assertThrows(IOException.class,()->other.retainCurrentRiteCreate(original));
            var modal=ready(t,p,fresh(t,p));assertThrows(IOException.class,()->other.prepareCurrentRiteCreateAcceptance(modal));assertEquals(0,b.creates);assertEquals(0,b.accepts);
        }
    }
    private static NativeGameTransport.RiteCreatePending createFrom(NativeGameTransport t,NativeGameTransport.RiteCreateReceived q)throws Exception{return t.retainCurrentRiteCreate(ack(t.submitCurrentRiteCreate(t.prepareCurrentRiteCreate(q))));}
    @Test void beforeCreateCoreChangedCoreOrReboundModalSourceNeverAuthorizeAccept()throws Exception{
        for(String mode:new String[]{"old-core","changed-core","wrong-modal-owner","wrong-modal-source"}){
            var clock=new Time();var r=new Replay(mode,true);try(var t=transport(r,clock)){
                var s=query(t,clock);var p=createFrom(t,s.query());var core=mode.equals("old-core")?s.core():fresh(t,p);
                assertInstanceOf(NativeGameTransport.RiteCreateUnavailable.class,t.readCurrentRiteCreateConfirmation(p,core,p.deadline()));assertEquals(0,r.accepts);
                if(mode.equals("old-core")||mode.equals("changed-core"))assertEquals(0,r.modalQueries);
            }
        }
    }
    @Test void lostOrNativeIndeterminateCreateRemainsOriginalUnknownWithoutReplay()throws Exception{
        for(String mode:new String[]{"lost-create","unknown-create"}){
            var clock=new Time();var r=new Replay(mode,true);try(var t=transport(r,clock)){
                var prepared=t.prepareCurrentRiteCreate(query(t,clock).query());var unknown=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentRiteCreate(prepared));
                assertSame(unknown,t.submitCurrentRiteCreate(prepared));assertEquals(1,r.creates);assertEquals(0,r.modalQueries);assertEquals(0,r.accepts);
                if(mode.equals("unknown-create"))assertTrue(t.originalIndeterminateCoreAcknowledgement(unknown.requestId()).isPresent());
            }
        }
    }
    @Test void lostAcceptOrExpiredCreateDoesNotPermitNewDeadlineOrAnotherFinalWrite()throws Exception{
        for(String mode:new String[]{"lost-accept","expired"}){
            var clock=new Time();var r=new Replay(mode,true);try(var t=transport(r,clock)){
                var p=create(t,clock);var core=fresh(t,p);
                if(mode.equals("expired")){clock.now=clock.now.plusSeconds(60);assertInstanceOf(NativeGameTransport.RiteCreateUnavailable.class,t.readCurrentRiteCreateConfirmation(p,core,clock.until()));assertEquals(0,r.accepts);}
                else{var prepared=t.prepareCurrentRiteCreateAcceptance(ready(t,p,core));var unknown=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentRiteCreate(prepared));assertSame(unknown,t.submitCurrentRiteCreate(prepared));assertEquals(1,r.accepts);}
                assertEquals(1,r.creates);
            }
        }
    }
    @Test void knownZeroEffectCreateRefusalKeepsItsAckAndCannotBecomePending()throws Exception{
        var clock=new Time();var r=new Replay("stale-create",true);try(var t=transport(r,clock)){
            var prepared=t.prepareCurrentRiteCreate(query(t,clock).query());var actual=ack(t.submitCurrentRiteCreate(prepared));assertFalse(actual.nativeOk());
            assertEquals(CurrentRiteCreateResult.Status.STALE_SOURCE,CurrentRiteCreateResult.decodeOutcome(actual).status());assertThrows(IOException.class,()->t.retainCurrentRiteCreate(actual));assertSame(actual,t.submitCurrentRiteCreate(prepared));assertEquals(1,r.creates);assertEquals(0,r.accepts);
        }
    }
    @Test void absentNewCapabilityDoesNotBorrowOldEditCapabilityOrEmitNewQuery()throws Exception{
        var clock=new Time();var r=new Replay("success",false);try(var t=transport(r,clock)){
            var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(clock.until()));var draft=assertInstanceOf(NativeGameTransport.RiteDraftCostsReceived.class,t.readRiteDraftCostsReceived(core,47,core.validUntil()));
            assertInstanceOf(NativeGameTransport.RiteCreateUnavailable.class,t.readCurrentRiteCreate(draft,draft.validUntil()));assertEquals(0,r.queries);assertEquals(0,r.creates);
        }
    }

    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> queue=new ArrayDeque<>();final String mode;boolean closed;int cores,queries,creates,modalQueries,accepts;BigInteger createDeadline;boolean allModalDeadlinesSame=true;
        Replay(String mode,boolean createCapability)throws Exception{
            this.mode=mode;var f=frame("draft-ready.json");var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",f.owner().orElseThrow().connectionGeneration()).put("bridge_version","rite-create-DATA").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=h.putArray("capabilities").add(CoreFrame.CAPABILITY).add(RiteDoctrineFrameV1.CAPABILITY);if(createCapability)caps.add(CurrentRiteCreate.CAPABILITY);queue.add(NativeWire.packet(StrictJson.canonical(h)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("Replay DATA closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant d)throws IOException{verify();}
        public byte[] readPacket(Instant d)throws IOException{verify();if(queue.isEmpty())throw new IOException("No replay DATA result");return queue.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException{
            verify();var request=NativeWire.decodeExecuteRequest(packet);byte[] body;boolean ok=true;
            try{
                var f=frame("draft-ready.json");var core=new CoreFrame.Partial(BUILD,f.factsBefore().orElseThrow());
                if(request.step().equals(CoreFrame.STEP)){
                    cores++;if(mode.equals("changed-core")&&cores>1){var p=core.prefix();core=new CoreFrame.Partial(BUILD,new CoreFrame.Prefix(p.dateRaw()+24,p.speed(),p.paused(),p.localPlayerId(),p.mapReady(),p.hasPlayedCharacter(),p.playedCharacterId(),p.playedCharacterAlive()));}
                    body=CoreFramePublicCodec.encode(core).bytes();
                }else if(request.step().equals(RiteDraftCostsFrameV2.STEP)){
                    var d=f.source().orElseThrow().draft().orElseThrow();var w=f.owner().orElseThrow();
                    body=RiteDraftCostsFrameV2PublicCodec.encode(new RiteDraftCostsFrameV2.Partial(core,new RiteDraftCostsFrameV2.Draft(47,36423,false,d.pietyCostRaw(),d.pietyMissingRaw(),d.pietyMissingRaw()<=0),new GuiRootIndexFrame.OwnerWitness(w.connectionGeneration(),w.ticketSequence(),w.pumpEpoch(),w.threadId()))).bytes();
                }else{
                    assertEquals(CurrentRiteCreate.STEP,request.step());var fields=NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));var claim=NativeWire.object(fields.get("rite_create"));String action=claim.get("action").textValue(),file;
                    switch(action){
                        case "query"->{queries++;file=mode.equals("false-create")?"draft-native-can-false.json":"draft-ready.json";}
                        case "create"->{creates++;createDeadline=fields.get("core_control_deadline_unix_ms").bigIntegerValue();if(mode.equals("lost-create"))return;file=mode.equals("unknown-create")?"cleanup-unknown.json":mode.equals("stale-create")?"stale-source.json":"create-dispatched.json";}
                        case "query_confirmation"->{modalQueries++;allModalDeadlinesSame&=fields.get("core_control_deadline_unix_ms").bigIntegerValue().equals(createDeadline);file=mode.equals("pending")&&modalQueries==1?"confirmation-pending.json":mode.equals("false-accept")?"confirmation-native-can-false.json":"confirmation-ready.json";}
                        case "accept_confirmation"->{accepts++;allModalDeadlinesSame&=fields.get("core_control_deadline_unix_ms").bigIntegerValue().equals(createDeadline);if(mode.equals("lost-accept"))return;file="accept-dispatched.json";}
                        default->throw new IOException("Unexpected CREATE action");
                    }
                    var original=cpp(file);body=original.result().token().orElseThrow().value();ok=original.nativeOk();
                    if(action.equals("query_confirmation")&&(mode.equals("wrong-modal-source")||mode.equals("wrong-modal-owner"))){
                        // Labelled Java negative mutation, never an original Native frame.
                        var n=NativeWire.object(NativeWire.parse(body));if(mode.equals("wrong-modal-source"))NativeWire.object(n.get("source")).put("source_rite_id",48);else NativeWire.object(n.get("owner")).put("connection_generation","1");body=StrictJson.canonical(n);
                    }
                }
            }catch(Exception invalid){throw new IOException("Original CREATE token or labelled Java exchange DATA invalid",invalid);}
            var out=new ByteArrayOutputStream();out.writeBytes(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+request.requestId()+"\",\"ok\":"+ok+",\"result\":").getBytes(StandardCharsets.UTF_8));out.writeBytes(body);out.write('}');queue.add(NativeWire.packet(out.toByteArray()));
        }
        public void close(){closed=true;}
    }
}
