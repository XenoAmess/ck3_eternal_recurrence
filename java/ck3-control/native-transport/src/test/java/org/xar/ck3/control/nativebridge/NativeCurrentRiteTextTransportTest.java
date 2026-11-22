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

/** Actual private transport/custody with original C++ tokens. HELLO/Core/wrapper are labelled Java exchange DATA. */
final class NativeCurrentRiteTextTransportTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    private static final class Time extends Clock {
        Instant now=Instant.now();public ZoneId getZone(){return ZoneOffset.UTC;}public Clock withZone(ZoneId z){if(!z.equals(ZoneOffset.UTC))throw new IllegalArgumentException();return this;}public Instant instant(){return now;}
        Instant until(){return now.plusSeconds(25);}
    }
    private static NativeWire.CommandResult cpp(String name)throws Exception{
        try(var in=NativeCurrentRiteTextTransportTest.class.getResourceAsStream("/current267-rite-text-cpp-a01/"+name)){
            if(in==null)throw new IOException("Original C++ resource absent: "+name);
            return assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(in.readAllBytes())));
        }
    }
    private static CurrentRiteTextResult frame(String name)throws Exception{return CurrentRiteTextResult.decode(new RawJson(cpp(name).result().token().orElseThrow().value()));}
    private static NativeGameTransport transport(Replay r,Time time){return new NativeGameTransport(r,new NativePipeEndpoint.Config("\\\\.\\pipe\\rite-text-data","rite-text-data",GAME,"rite-text-session-data","rite-text-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),64,1024,List.of(),time);}
    private static NativeActionPort.AckReceived ack(NativeActionPort.DispatchOutcome out){return assertInstanceOf(NativeActionPort.AckReceived.class,out,()->out instanceof NativeActionPort.Unknown u?u.reason():out.toString());}
    private static NativeGameTransport.RiteTextReceived query(NativeGameTransport t,Time time,Replay r)throws Exception{
        var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(time.until()));
        return assertInstanceOf(NativeGameTransport.RiteTextReceived.class,t.readCurrentRiteText(core,r.base().source().orElseThrow().sourceRiteId(),core.validUntil()));
    }
    @Test void actualVoidNameReceiptIsOnceAndFreshQueryDoesNotInventAnAppliedText()throws Exception{
        var c=new Time();var r=new Replay("success",true);try(var t=transport(r,c)){
            var q=query(t,c,r);var p=t.prepareCurrentRiteText(q,CurrentRiteText.Action.SET_NAME,"中😀");assertEquals(0,r.setters);
            var actual=ack(t.submitCurrentRiteText(p));assertSame(actual,t.submitCurrentRiteText(p));
            assertArrayEquals(cpp("name-dispatched.json").result().token().orElseThrow().value(),actual.originalResultToken().orElseThrow().bytes());
            var f=CurrentRiteTextResult.decodeOutcome(actual);assertTrue(f.nativeReturned());assertFalse(f.nativeHandled());assertFalse(f.textApplied());
            var after=query(t,c,r);assertNotSame(q,after);assertEquals("Original name",after.frame().source().orElseThrow().name());assertNotEquals(p.text(),after.frame().source().orElseThrow().name());
            assertTrue(after.original().custody().orElseThrow().writeEntered().order().compareTo(actual.custody().orElseThrow().responseReceived().order())>0);assertEquals(1,r.setters);assertEquals(2,r.queries);
        }
    }
    @Test void emptyDescriptionIsRealClearInputButReturnedVoidStillNeedsIndependentReadback()throws Exception{
        var c=new Time();var r=new Replay("success",true);try(var t=transport(r,c)){
            var p=t.prepareCurrentRiteText(query(t,c,r),CurrentRiteText.Action.SET_DESCRIPTION,"");assertEquals("",p.text());var actual=ack(t.submitCurrentRiteText(p));
            assertArrayEquals(cpp("description-dispatched.json").result().token().orElseThrow().value(),actual.originalResultToken().orElseThrow().bytes());
            assertFalse(CurrentRiteTextResult.decodeOutcome(actual).textApplied());var after=query(t,c,r);assertEquals("Original description",after.frame().source().orElseThrow().description());assertEquals(1,r.setters);
        }
    }
    @Test void blockedAndNonCreatingSourcesRemainReadableDataWithoutSetterAuthority()throws Exception{
        for(String mode:new String[]{"blocked","not-creating"}){var c=new Time();var r=new Replay(mode,true);try(var t=transport(r,c)){
            var q=query(t,c,r);assertFalse(q.frame().source().orElseThrow().writeAdmissible());assertThrows(IOException.class,()->t.prepareCurrentRiteText(q,CurrentRiteText.Action.SET_NAME,"name"));assertEquals(0,r.setters);
        }}
    }
    @Test void foreignReceiverCannotUsePrivateQueryOrPreparedPacketAndPublicAckHasNoMintingApi()throws Exception{
        var c=new Time();var a=new Replay("success",true);var b=new Replay("success",true);try(var t=transport(a,c);var other=transport(b,c)){
            var q=query(t,c,a);assertThrows(IOException.class,()->other.prepareCurrentRiteText(q,CurrentRiteText.Action.SET_NAME,"name"));var p=t.prepareCurrentRiteText(q,CurrentRiteText.Action.SET_NAME,"name");
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.submitCurrentRiteText(p));assertEquals(0,b.setters);
            assertThrows(NoSuchMethodException.class,()->NativeGameTransport.class.getMethod("prepareCurrentRiteText",NativeActionPort.AckReceived.class,CurrentRiteText.Action.class,String.class));
            var actual=ack(t.submitCurrentRiteText(p));assertEquals(1,a.setters);
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.submitCurrentRiteText(p));
            assertSame(actual,t.submitCurrentRiteText(p));assertEquals(0,b.setters);
        }
    }
    @Test void preparedActionAndTextAreImmutableAndOriginalQueryCannotAuthorizeAnotherSetter()throws Exception{
        var c=new Time();var r=new Replay("success",true);try(var t=transport(r,c)){
            var q=query(t,c,r);var p=t.prepareCurrentRiteText(q,CurrentRiteText.Action.SET_NAME,"name");assertSame(p,t.prepareCurrentRiteText(q,CurrentRiteText.Action.SET_NAME,"name"));
            assertThrows(IOException.class,()->t.prepareCurrentRiteText(q,CurrentRiteText.Action.SET_NAME,"other"));assertThrows(IOException.class,()->t.prepareCurrentRiteText(q,CurrentRiteText.Action.SET_DESCRIPTION,"name"));
            ack(t.submitCurrentRiteText(p));assertThrows(IOException.class,()->q.requireOriginal(t,p.deadline()));assertThrows(IOException.class,()->t.prepareCurrentRiteText(q,CurrentRiteText.Action.SET_DESCRIPTION,"desc"));assertEquals(1,r.setters);
        }
    }
    @Test void expiredPreparedWriteRemainsBeforeWriteWithoutRefreshingOriginalDeadline()throws Exception{
        var c=new Time();var r=new Replay("success",true);try(var t=transport(r,c)){
            var p=t.prepareCurrentRiteText(query(t,c,r),CurrentRiteText.Action.SET_NAME,"name");var until=p.deadline();c.now=until.plusMillis(1);
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.submitCurrentRiteText(p));assertEquals(until,p.deadline());assertEquals(0,r.setters);
        }
    }
    @Test void lostOrIndeterminateSetterPreservesOriginalUnknownAndDoesNotReplay()throws Exception{
        for(String mode:new String[]{"lost","unknown"}){var c=new Time();var r=new Replay(mode,true);try(var t=transport(r,c)){
            var p=t.prepareCurrentRiteText(query(t,c,r),CurrentRiteText.Action.SET_NAME,"name");var actual=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentRiteText(p));assertSame(actual,t.submitCurrentRiteText(p));assertEquals(1,r.setters);
            if(mode.equals("unknown"))assertTrue(t.originalIndeterminateCoreAcknowledgement(p.requestId()).isPresent());
        }}
    }
    @Test void actualWrittenResultRebindingSourceLeaseOrFactsIsUnknownNotTextApplied()throws Exception{
        for(String mode:new String[]{"source-drift","lease-drift","facts-drift"}){var c=new Time();var r=new Replay(mode,true);try(var t=transport(r,c)){
            var p=t.prepareCurrentRiteText(query(t,c,r),CurrentRiteText.Action.SET_NAME,"name");assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentRiteText(p));assertEquals(1,r.setters);assertTrue(t.originalIndeterminateCoreAcknowledgement(p.requestId()).isPresent());
        }}
    }
    @Test void actualCapabilityAndFixedWriteTextGuardsRejectBeforeAnyNativeSetter()throws Exception{
        var c=new Time();var r=new Replay("success",false);try(var t=transport(r,c)){
            var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(c.until()));assertInstanceOf(NativeGameTransport.RiteTextUnavailable.class,t.readCurrentRiteText(core,47,core.validUntil()));assertEquals(0,r.queries);assertEquals(0,r.setters);
        }
        r=new Replay("success",true);try(var t=transport(r,c)){var q=query(t,c,r);assertThrows(IllegalArgumentException.class,()->t.prepareCurrentRiteText(q,CurrentRiteText.Action.SET_NAME,"bad\nname"));assertThrows(IOException.class,()->t.prepareCurrentRiteText(q,CurrentRiteText.Action.QUERY,""));assertEquals(0,r.setters);}
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> queue=new ArrayDeque<>();final String mode;boolean closed;int cores,queries,setters;
        Replay(String mode,boolean capability)throws Exception{
            this.mode=mode;var f=base();var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",f.owner().orElseThrow().connectionGeneration()).put("bridge_version","rite-text-data").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=h.putArray("capabilities").add(CoreFrame.CAPABILITY);if(capability)caps.add(CurrentRiteText.CAPABILITY);queue.add(NativeWire.packet(StrictJson.canonical(h)));
        }
        CurrentRiteTextResult base()throws Exception{return frame(mode.equals("blocked")?"query-blocked.json":mode.equals("not-creating")?"query-not-creating.json":"query-original-source.json");}
        public void verify()throws IOException{if(closed)throw new IOException("Replay DATA closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant d)throws IOException{verify();}
        public byte[] readPacket(Instant d)throws IOException{verify();if(queue.isEmpty())throw new IOException("No replay DATA packet");return queue.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException{
            verify();var request=NativeWire.decodeExecuteRequest(packet);byte[] body;boolean ok=true;
            try{
                if(request.step().equals(CoreFrame.STEP)){cores++;body=CoreFramePublicCodec.encode(new CoreFrame.Partial(BUILD,base().factsBefore().orElseThrow())).bytes();}
                else{
                    assertEquals(CurrentRiteText.STEP,request.step());var fields=NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));var claim=NativeWire.object(fields.get("rite_text"));String action=claim.get("action").textValue(),file;
                    switch(action){
                        case "query"->{queries++;file=mode.equals("blocked")?"query-blocked.json":mode.equals("not-creating")?"query-not-creating.json":"query-original-source.json";}
                        case "set_name","set_description"->{setters++;if(mode.equals("lost"))return;file=mode.equals("unknown")?"cleanup-unknown.json":action.equals("set_name")?"name-dispatched.json":"description-dispatched.json";}
                        default->throw new IOException("Unexpected TEXT action");
                    }
                    var original=cpp(file);body=original.result().token().orElseThrow().value();ok=original.nativeOk();
                    if(!action.equals("query")&&mode.endsWith("-drift")){
                        // Explicit negative Java DATA mutation; never an original Native frame.
                        var n=NativeWire.object(NativeWire.parse(body));if(mode.equals("source-drift"))NativeWire.object(n.get("source")).put("name","rebound");else if(mode.equals("lease-drift"))n.put("query_sequence","1");else NativeWire.object(n.get("facts_before")).put("date_raw",53144352);body=StrictJson.canonical(n);
                    }
                }
            }catch(Exception e){throw new IOException("Original TEXT token or labelled Java exchange DATA invalid",e);}
            var out=new ByteArrayOutputStream();out.writeBytes(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+request.requestId()+"\",\"ok\":"+ok+",\"result\":").getBytes(StandardCharsets.UTF_8));out.writeBytes(body);out.write('}');queue.add(NativeWire.packet(out.toByteArray()));
        }
        public void close(){closed=true;}
    }
}
