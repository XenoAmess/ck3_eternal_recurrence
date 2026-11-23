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

/** Original C++ result tokens; HELLO/Core/response-ID wrappers are explicitly Java exchange DATA. */
final class NativeCurrentStockBookmark1070TransportTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    private static final class Time extends Clock {
        Instant now=Instant.now();public ZoneId getZone(){return ZoneOffset.UTC;}public Clock withZone(ZoneId zone){if(!zone.equals(ZoneOffset.UTC))throw new IllegalArgumentException();return this;}public Instant instant(){return now;}
        Instant until(){return now.plusSeconds(25);}
    }
    private static NativeWire.CommandResult cpp(String name)throws Exception {
        try(var in=NativeCurrentStockBookmark1070TransportTest.class.getResourceAsStream("/current267-stock-bookmark1070-cpp-a1070/"+name)){
            if(in==null)throw new IOException("Original stock C++ resource missing: "+name);
            return assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(in.readAllBytes())));
        }
    }
    private static CurrentStockBookmark1070Result frame(String name)throws Exception{return CurrentStockBookmark1070Result.decode(new RawJson(cpp(name).result().token().orElseThrow().value()));}
    private static NativeGameTransport transport(Replay r,Time time){return new NativeGameTransport(r,new NativePipeEndpoint.Config("\\\\.\\pipe\\stock-bookmark-data","stock-bookmark-data",GAME,"stock-bookmark-session-data","stock-bookmark-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),64,1024,List.of(),time);}
    private static NativeActionPort.AckReceived ack(NativeActionPort.DispatchOutcome value){return assertInstanceOf(NativeActionPort.AckReceived.class,value,()->value instanceof NativeActionPort.Unknown u?u.reason():value.toString());}
    private static NativeGameTransport.StockBookmark1070Received query(NativeGameTransport t,Time time)throws Exception {
        var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(time.until()));
        return assertInstanceOf(NativeGameTransport.StockBookmark1070Received.class,t.readCurrentStockBookmark1070(core,core.validUntil()));
    }
    @Test void actualFixedCReceiptIsOnceAndIndependentEmptyCensusDoesNotInventCallbackClosure()throws Exception {
        var c=new Time();var r=new Replay("empty-after",true,true);try(var t=transport(r,c)){
            var q=query(t,c);assertEquals(List.of(2,0,1),q.frame().source().orElseThrow().eventCensus().events().getFirst().options().stream().map(o->o.authoredOptionIndex()).toList());
            var p=t.prepareCurrentStockBookmark1070C(q);assertEquals(1,p.instanceId());assertEquals(0,r.selections);assertSame(p,t.prepareCurrentStockBookmark1070C(q));
            var actual=ack(t.submitCurrentStockBookmark1070C(p));assertSame(actual,t.submitCurrentStockBookmark1070C(p));
            assertArrayEquals(cpp("selection-c-dispatched.json").result().token().orElseThrow().value(),actual.originalResultToken().orElseThrow().bytes());
            var f=CurrentStockBookmark1070Result.decodeOutcome(actual);assertEquals(f,p.latestFrame().orElseThrow());assertTrue(f.nativeReturned());assertFalse(f.nativeHandled());assertFalse(f.eventClosed());assertEquals(q.frame().source(),f.source());
            var after=query(t,c);assertTrue(after.frame().source().orElseThrow().eventCensus().events().isEmpty());assertFalse(after.frame().eventClosed());
            assertTrue(after.original().custody().orElseThrow().writeEntered().order().compareTo(actual.custody().orElseThrow().responseReceived().order())>0);assertEquals(1,r.selections);assertEquals(2,r.queries);
        }
    }
    @Test void absentMultipleWrongDefinitionAndFalseCanAreDataWithoutFixedChoicePermission()throws Exception {
        for(String mode:new String[]{"empty","multiple","wrong-definition","native-can-false"}){var c=new Time();var r=new Replay(mode,true,true);try(var t=transport(r,c)){
            var q=query(t,c);assertFalse(q.frame().source().orElseThrow().selectCAdmissible());assertThrows(IOException.class,()->t.prepareCurrentStockBookmark1070C(q));assertEquals(0,r.selections);
        }}
    }
    @Test void foreignReceiverAndPublicAckCannotMintOrBorrowChoiceAuthority()throws Exception {
        var c=new Time();var r=new Replay("success",true,true);var otherReplay=new Replay("success",true,true);try(var t=transport(r,c);var other=transport(otherReplay,c)){
            var q=query(t,c);assertThrows(IOException.class,()->other.prepareCurrentStockBookmark1070C(q));var p=t.prepareCurrentStockBookmark1070C(q);
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.submitCurrentStockBookmark1070C(p));assertEquals(0,otherReplay.selections);
            assertThrows(NoSuchMethodException.class,()->NativeGameTransport.class.getMethod("prepareCurrentStockBookmark1070C",NativeActionPort.AckReceived.class));
            var actual=ack(t.submitCurrentStockBookmark1070C(p));assertSame(actual,t.submitCurrentStockBookmark1070C(p));assertEquals(1,r.selections);
        }
    }
    @Test void aCoreCanQueryOnlyOnceAndANewerActualQueryInvalidatesTheOldReceipt()throws Exception {
        var c=new Time();var r=new Replay("success",true,true);try(var t=transport(r,c)){
            var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(c.until()));
            var first=assertInstanceOf(NativeGameTransport.StockBookmark1070Received.class,t.readCurrentStockBookmark1070(core,core.validUntil()));
            assertInstanceOf(NativeGameTransport.StockBookmark1070Unavailable.class,t.readCurrentStockBookmark1070(core,core.validUntil()));assertEquals(1,r.queries);
            var second=query(t,c);assertThrows(IOException.class,()->t.prepareCurrentStockBookmark1070C(first));assertNotNull(t.prepareCurrentStockBookmark1070C(second));assertEquals(0,r.selections);
        }
    }
    @Test void expiredPreparedChoiceStaysBeforeWriteWithItsOriginalDeadline()throws Exception {
        var c=new Time();var r=new Replay("success",true,true);try(var t=transport(r,c)){
            var p=t.prepareCurrentStockBookmark1070C(query(t,c));var until=p.deadline();c.now=until.plusMillis(1);
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.submitCurrentStockBookmark1070C(p));assertEquals(until,p.deadline());assertEquals(0,r.selections);
        }
    }
    @Test void lostOrIndeterminateChoiceIsStickyAndNeverReplayed()throws Exception {
        for(String mode:new String[]{"lost","unknown"}){var c=new Time();var r=new Replay(mode,true,true);try(var t=transport(r,c)){
            var p=t.prepareCurrentStockBookmark1070C(query(t,c));var original=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentStockBookmark1070C(p));
            assertSame(original,t.submitCurrentStockBookmark1070C(p));assertSame(original,t.readCurrentStockBookmark1070(null,c.until()).original());assertEquals(1,r.selections);
            if(mode.equals("unknown"))assertTrue(t.originalIndeterminateCoreAcknowledgement(p.requestId()).isPresent());
        }}
    }
    @Test void writtenSourceLeaseFactsOrInstanceRebindingBecomesUnknown()throws Exception {
        for(String mode:new String[]{"source-drift","lease-drift","facts-drift","instance-drift"}){var c=new Time();var r=new Replay(mode,true,true);try(var t=transport(r,c)){
            var p=t.prepareCurrentStockBookmark1070C(query(t,c));assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentStockBookmark1070C(p));
            assertTrue(t.originalIndeterminateCoreAcknowledgement(p.requestId()).isPresent());assertEquals(1,r.selections);
        }}
    }
    @Test void aStillPresentOriginalEventIsObservedDataAndCannotBeSelectedAgain()throws Exception {
        var c=new Time();var r=new Replay("success",true,true);try(var t=transport(r,c)){
            var first=query(t,c);var p=t.prepareCurrentStockBookmark1070C(first);ack(t.submitCurrentStockBookmark1070C(p));assertThrows(IOException.class,()->first.requireOriginal(t,p.deadline()));
            var after=query(t,c);assertTrue(after.frame().source().orElseThrow().eventCensus().events().stream().anyMatch(e->e.instanceId()==p.instanceId()));
            assertThrows(IOException.class,()->t.prepareCurrentStockBookmark1070C(after));assertEquals(1,r.selections);
        }
    }
    @Test void eachActualCapabilityIsRequiredBeforeItsQueryOrChoiceWrite()throws Exception {
        var c=new Time();var r=new Replay("success",false,false);try(var t=transport(r,c)){
            var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(c.until()));assertInstanceOf(NativeGameTransport.StockBookmark1070Unavailable.class,t.readCurrentStockBookmark1070(core,core.validUntil()));assertEquals(0,r.queries);
        }
        r=new Replay("success",true,false);try(var t=transport(r,c)){var q=query(t,c);assertThrows(IOException.class,()->t.prepareCurrentStockBookmark1070C(q));assertEquals(0,r.selections);}
    }
    @Test void knownStaleReceiptRemainsKnownDataAndDoesNotAuthorizeASecondWrite()throws Exception {
        var c=new Time();var r=new Replay("stale",true,true);try(var t=transport(r,c)){
            var p=t.prepareCurrentStockBookmark1070C(query(t,c));var actual=ack(t.submitCurrentStockBookmark1070C(p));
            assertEquals(CurrentStockBookmark1070Result.Status.STALE_SOURCE,CurrentStockBookmark1070Result.decodeOutcome(actual).status());assertSame(actual,t.submitCurrentStockBookmark1070C(p));
            assertThrows(IOException.class,()->t.prepareCurrentStockBookmark1070C(query(t,c)));assertEquals(1,r.selections);
        }
    }
    @Test void indeterminateQueryRemainsOriginalFamilyUnknownAcrossFreshCoreData()throws Exception {
        var c=new Time();var r=new Replay("query-unknown",true,true);try(var t=transport(r,c)){
            var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(c.until()));var first=assertInstanceOf(NativeGameTransport.StockBookmark1070Unavailable.class,t.readCurrentStockBookmark1070(core,core.validUntil()));
            assertInstanceOf(NativeActionPort.Unknown.class,first.original());var fresh=assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(c.until()));
            assertSame(first,t.readCurrentStockBookmark1070(fresh,fresh.validUntil()));assertEquals(1,r.queries);assertEquals(0,r.selections);
        }
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> queue=new ArrayDeque<>();final String mode;boolean closed;int cores,queries,selections;
        Replay(String mode,boolean queryCapability,boolean selectCapability)throws Exception {
            this.mode=mode;var f=frame("available-original.json");
            var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",f.owner().orElseThrow().connectionGeneration()).put("bridge_version","stock-bookmark-data").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=h.putArray("capabilities").add(CoreFrame.CAPABILITY);if(queryCapability)caps.add(CurrentStockBookmark1070.Action.QUERY.capability());if(selectCapability)caps.add(CurrentStockBookmark1070.Action.SELECT_C.capability());queue.add(NativeWire.packet(StrictJson.canonical(h)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("Replay DATA closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant until)throws IOException{verify();}
        public byte[] readPacket(Instant until)throws IOException{verify();if(queue.isEmpty())throw new IOException("No replay DATA packet");return queue.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException {
            verify();var request=NativeWire.decodeExecuteRequest(packet);byte[] body;boolean ok=true;
            try {
                if(request.step().equals(CoreFrame.STEP)){cores++;body=CoreFramePublicCodec.encode(new CoreFrame.Partial(BUILD,frame("available-original.json").factsBefore().orElseThrow())).bytes();}
                else {
                    var fields=NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));var claim=NativeWire.object(fields.get("stock_bookmark1070"));String action=claim.get("action").textValue(),file;
                    if(action.equals("query")){
                        assertEquals(CurrentStockBookmark1070.Action.QUERY.step(),request.step());queries++;
                        file=switch(mode){case "empty"->"available-empty.json";case "multiple"->"available-multiple.json";case "wrong-definition"->"available-wrong-definition.json";case "native-can-false"->"available-native-can-false.json";case "query-unknown"->"indeterminate-incomplete.json";default->mode.equals("empty-after")&&selections>0?"available-empty.json":"available-original.json";};
                    }else if(action.equals("select_c")){
                        assertEquals(CurrentStockBookmark1070.Action.SELECT_C.step(),request.step());assertEquals(1,claim.get("instance_id").intValue());selections++;if(mode.equals("lost"))return;
                        file=mode.equals("unknown")?"indeterminate-cleanup.json":mode.equals("stale")?"stale-with-original-source.json":"selection-c-dispatched.json";
                    }else throw new IOException("Unexpected stock choice action");
                    var original=cpp(file);body=original.result().token().orElseThrow().value();ok=original.nativeOk();
                    if(action.equals("select_c")&&mode.endsWith("-drift")){
                        // Negative Java DATA mutation, not a Native genuine result.
                        var n=NativeWire.object(NativeWire.parse(body));
                        if(mode.equals("source-drift"))((com.fasterxml.jackson.databind.node.ObjectNode)n.get("source").get("event_census").get("events").get(0)).put("description","rebound source");
                        else if(mode.equals("lease-drift"))n.put("query_sequence","1");else if(mode.equals("facts-drift"))NativeWire.object(n.get("facts_before")).put("date_raw",53144352);else n.put("instance_id",2);
                        body=StrictJson.canonical(n);
                    }
                }
            }catch(Exception e){throw new IOException("Original stock token or labelled Java exchange DATA invalid",e);}
            var out=new ByteArrayOutputStream();out.writeBytes(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+request.requestId()+"\",\"ok\":"+ok+",\"result\":").getBytes(StandardCharsets.UTF_8));out.writeBytes(body);out.write('}');queue.add(NativeWire.packet(out.toByteArray()));
        }
        public void close(){closed=true;}
    }
}
