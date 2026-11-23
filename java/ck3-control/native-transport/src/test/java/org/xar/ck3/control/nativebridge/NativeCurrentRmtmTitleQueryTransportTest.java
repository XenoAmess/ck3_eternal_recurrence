package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** Explicit generated Java DATA port. Wrapping tokens for a Java test is not an original C++ exchange or live owner. */
final class NativeCurrentRmtmTitleQueryTransportTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    private static NativeGameTransport transport(DataPort p){return new NativeGameTransport(p,new NativePipeEndpoint.Config("\\\\.\\pipe\\rmtm-title-DATA","rmtm-data",GAME,"rmtm-session-DATA","rmtm-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),128,64);}
    private static NativeGameTransport.CoreReceived core(NativeGameTransport t)throws Exception{return assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(Instant.now().plusSeconds(30)));}
    private static NativeGameTransport.RmtmTitleQueryReceived query(NativeGameTransport t,NativeGameTransport.CoreReceived c)throws Exception{return assertInstanceOf(NativeGameTransport.RmtmTitleQueryReceived.class,t.readCurrentRmtmTitleQuery(c,c.validUntil()));}
    private static ObjectNode token(String name)throws IOException{
        try(var in=NativeCurrentRmtmTitleQueryTransportTest.class.getResourceAsStream("/current267-rmtm-title-query-cpp-a01/"+name)){
            if(in==null)throw new IOException("Actual C++ token template absent");return NativeWire.object(NativeWire.parse(in.readAllBytes()).get("result"));}
    }
    @Test void originalReadonlyReceiptRetainsFullActualJavaPacketCoreAndAckCustody()throws Exception{
        var port=new DataPort("known");try(var t=transport(port)){var c=core(t);var q=query(t,c);q.requireOriginal(t,q.validUntil());
            assertEquals(q.frame(),CurrentRmtmTitleQueryResult.decodeOutcome(q.original()));assertEquals(1,port.queryWrites);assertEquals(1,port.coreWrites);
            var request=NativeWire.decodeExecuteRequest(q.original().outbound().orElseThrow().originalPacket());var fields=NativeWire.parse(request.normalizedAdditionalFields().value());
            assertEquals(CurrentRmtmTitleQuery.STEP,request.step());assertEquals(7,fields.get("rmtm_title").size());assertFalse(fields.get("rmtm_title").has("title_id"));
            assertEquals(q.validUntil().toEpochMilli(),fields.get("core_control_deadline_unix_ms").longValue());
            assertEquals(BigInteger.ZERO,q.frame().claimSequence());assertFalse(q.frame().nativeReturned());assertFalse(q.frame().nativeHandled());assertFalse(q.frame().newDateObserved());assertFalse(q.frame().physicalSaveConfirmed());}
    }
    @Test void aCoreCanSubmitOnlyOneQueryAndItsFreshReplacementCreatesNoMutation()throws Exception{
        var port=new DataPort("known");try(var t=transport(port)){var c=core(t);query(t,c);assertInstanceOf(NativeGameTransport.RmtmTitleQueryUnavailable.class,t.readCurrentRmtmTitleQuery(c,c.validUntil()));
            assertEquals(1,port.queryWrites);query(t,core(t));assertEquals(2,port.queryWrites);assertEquals(2,port.coreWrites);}
    }
    @Test void foreignReceiverAndNewerQueryCannotBorrowOriginalPrivateRead()throws Exception{
        var a=new DataPort("known");var b=new DataPort("known");try(var t=transport(a);var other=transport(b)){var c=core(t);var q=query(t,c);
            assertThrows(IOException.class,()->q.requireOriginal(other,q.validUntil()));assertInstanceOf(NativeGameTransport.RmtmTitleQueryUnavailable.class,other.readCurrentRmtmTitleQuery(c,c.validUntil()));assertEquals(0,b.queryWrites);
            var newer=core(t);q.requireOriginal(t,q.validUntil());query(t,newer);assertThrows(IOException.class,()->q.requireOriginal(t,q.validUntil()));}
    }
    @Test void changedCoreConnectionOrMissingAckStaysStickyUnknownAndNeverRetransmits()throws Exception{
        for(String mode:List.of("changed-core","wrong-connection","lost")){var port=new DataPort(mode);try(var t=transport(port)){var c=core(t);var first=assertInstanceOf(NativeGameTransport.RmtmTitleQueryUnavailable.class,t.readCurrentRmtmTitleQuery(c,c.validUntil()));
            assertInstanceOf(NativeActionPort.Unknown.class,first.original());assertSame(first,t.readCurrentRmtmTitleQuery(c,c.validUntil()));assertSame(first,t.readCurrentRmtmTitleQuery(core(t),c.validUntil()));assertEquals(1,port.queryWrites);}}
    }
    @Test void knownRefusalAndEmptyReasonAreNotPromotedToUnknownOrKnownEmptySource()throws Exception{
        for(String mode:List.of("refusal","empty-reason")){var port=new DataPort(mode);try(var t=transport(port)){var c=core(t);var no=assertInstanceOf(NativeGameTransport.RmtmTitleQueryUnavailable.class,t.readCurrentRmtmTitleQuery(c,c.validUntil()));
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,no.original());assertTrue(CurrentRmtmTitleQueryResult.decodeOutcome(ack).source().isEmpty());
            if(mode.equals("empty-reason"))assertEquals("",no.reason());port.mode="known";query(t,core(t));assertEquals(2,port.queryWrites);}}
    }
    @Test void unknownCleanupCannotBeWashedAwayByLaterAvailableData()throws Exception{
        var port=new DataPort("indeterminate");try(var t=transport(port)){var c=core(t);var unknown=assertInstanceOf(NativeGameTransport.RmtmTitleQueryUnavailable.class,t.readCurrentRmtmTitleQuery(c,c.validUntil()));
            assertInstanceOf(NativeActionPort.Unknown.class,unknown.original());port.mode="known";assertSame(unknown,t.readCurrentRmtmTitleQuery(core(t),c.validUntil()));assertEquals(1,port.queryWrites);}
    }
    @Test void emptyPhysicalLawsAndActualDeadHolderRemainReadonlyData()throws Exception{
        for(String mode:List.of("empty","dead-holder")){var port=new DataPort(mode);try(var t=transport(port)){var q=query(t,core(t));var s=q.frame().source().orElseThrow();
            if(mode.equals("empty"))assertTrue(s.physicalOwnLaws().isEmpty());else assertFalse(s.holder().orElseThrow().alive());
            q.requireOriginal(t,q.validUntil());assertThrows(UnsupportedOperationException.class,()->s.physicalOwnLaws().clear());assertEquals(1,port.queryWrites);}}
    }
    @Test void originalDeadlineCannotBeExtendedAndUnavailableCapabilityWritesNothing()throws Exception{
        var port=new DataPort("known");var t=transport(port);var q=query(t,core(t));assertThrows(IOException.class,()->q.requireOriginal(t,q.validUntil().plusMillis(1)));t.close();assertThrows(IOException.class,()->q.requireOriginal(t,q.validUntil()));
        var absent=new DataPort("no-cap");try(var other=transport(absent)){var c=core(other);var no=assertInstanceOf(NativeGameTransport.RmtmTitleQueryUnavailable.class,other.readCurrentRmtmTitleQuery(c,c.validUntil()));assertFalse(no.original() instanceof NativeActionPort.Unknown);assertEquals(0,absent.queryWrites);}
    }
    private static final class DataPort implements NativePacketPort {
        String mode;boolean closed;int coreWrites,queryWrites;final ArrayDeque<byte[]> packets=new ArrayDeque<>();
        DataPort(String mode)throws IOException{this.mode=mode;var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",BigInteger.valueOf(2)).put("bridge_version","rmtm-data")
                .put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=h.putArray("capabilities");caps.add(CoreFrame.CAPABILITY);if(!mode.equals("no-cap"))caps.add(CurrentRmtmTitleQuery.CAPABILITY);packets.add(NativeWire.packet(StrictJson.canonical(h)));}
        public void verify()throws IOException{if(closed)throw new IOException("RMTM Java DATA port closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant until)throws IOException{verify();}
        public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("Explicit DATA response missing");return packets.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException{verify();var request=NativeWire.decodeExecuteRequest(packet);ObjectNode result;boolean ok=true;
            if(request.step().equals(CoreFrame.STEP)){coreWrites++;result=NativeWire.object(NativeWire.parse(CoreFramePublicCodec.encode(new CoreFrame.Partial(BUILD,new CoreFrame.Prefix(53144328,3,true,1,true,true,0,true))).bytes()));}
            else if(request.step().equals(CurrentRmtmTitleQuery.STEP)){queryWrites++;if(mode.equals("lost"))return;
                result=token(mode.equals("indeterminate")?"indeterminate.json":mode.equals("refusal")||mode.equals("empty-reason")?"unavailable.json":mode.equals("empty")?"available-empty-laws.json":mode.equals("dead-holder")?"available-dead-holder-data.json":"available-law.json");
                ok=result.get("status").textValue().equals("available");if(ok){((ObjectNode)result.get("owner")).put("connection_generation",mode.equals("wrong-connection")?"3":"2");if(mode.equals("changed-core"))((ObjectNode)result.get("facts_before")).put("date_raw",53144352);}
                if(mode.equals("empty-reason"))result.put("unavailable_reason","");}
            else throw new IOException("No mutation or other family exists in this Java DATA port");
            var envelope=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",ok);envelope.set("result",result);packets.add(NativeWire.packet(StrictJson.canonical(envelope)));
        }
        public void close(){closed=true;}
    }
}
