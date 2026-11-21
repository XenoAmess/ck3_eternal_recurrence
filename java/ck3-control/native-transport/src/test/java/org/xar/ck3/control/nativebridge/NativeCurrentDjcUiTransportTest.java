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
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** Actual C++ result tokens through real transport. Fresh envelopes and distinct witness sequences are explicit Java DATA. */
class NativeCurrentDjcUiTransportTest {
    static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    static final NativeCharacterId TARGET=new NativeCharacterId(888);
    static final CurrentDjcTargetWarQueryResult.CasusBelliKey CB=CurrentDjcTargetWarQueryResult.CasusBelliKey.DUCHY;
    static NativeGameTransport transport(Replay r){return new NativeGameTransport(r,new NativePipeEndpoint.Config("\\\\.\\pipe\\djc-ui-data","djc-ui-data",GAME,"djc-ui-session","djc-ui-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),64,32);}
    static NativeGameTransport.CoreReceived core(NativeGameTransport t)throws Exception{return assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(Instant.now().plusSeconds(20)));}
    static NativeGameTransport.DjcUiReceived query(NativeGameTransport t)throws Exception {var before=core(t);return assertInstanceOf(NativeGameTransport.DjcUiReceived.class,t.readCurrentDjcDeclarationUi(before,TARGET,CB,before.validUntil()));}
    @Test void falseNativeConfirmationRemainsAvailableAndOpenWritesZero()throws Exception {
        var replay=new Replay("confirmation-false");try(var t=transport(replay)){var q=query(t);assertTrue(q.frame().nativeOk());assertFalse(q.frame().source().orElseThrow().permitsOpen());assertThrows(IOException.class,()->t.prepareCurrentDjcUiOpen(q));assertEquals(0,replay.effects);}
    }
    @Test void actualOpenIsOnceAndDoesNotBecomeWarOrPaymentProof()throws Exception {
        var replay=new Replay("open");try(var t=transport(replay)){var q=query(t);var prepared=t.prepareCurrentDjcUiOpen(q);var actual=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentDjcUi(prepared));assertEquals(CurrentDjcDeclarationUiResult.Status.OPEN_DISPATCHED,CurrentDjcDeclarationUiResult.decodeOutcome(actual).status());assertSame(actual,t.submitCurrentDjcUi(prepared));assertEquals(1,replay.effects);assertTrue(prepared.originalPacket().value().length>0);}
    }
    @Test void selectionRequiresExactPrivateNativeRowNotAReconstructedTupleOrForeignReceiver()throws Exception {
        var replay=new Replay("resident");var otherReplay=new Replay("resident");try(var t=transport(replay);var other=transport(otherReplay)){
            var q=query(t);var row=q.frame().source().orElseThrow().choices().getFirst();var fake=new CurrentDjcDeclarationUiSource.Choice(row.nativeToken(),row.tuple());
            assertThrows(IOException.class,()->t.bindCurrentDjcChoice(q,fake));assertThrows(IOException.class,()->other.bindCurrentDjcChoice(q,row));
            var choice=t.bindCurrentDjcChoice(q,row);var prepared=t.prepareCurrentDjcUiSelection(choice);assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentDjcUi(prepared));assertEquals(1,replay.effects);assertEquals(0,otherReplay.effects);
        }
    }
    @Test void warningReadRetainsSendLeaseButAcceptanceUsesNewActualWitnessWithoutRefreshingDeadline()throws Exception {
        var replay=new Replay("resident");try(var t=transport(replay)){
            var q=query(t);var send=t.prepareCurrentDjcUiSend(q);var originalSend=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentDjcUi(send));var pending=t.retainCurrentDjcUiSend(originalSend);
            var waiting=assertInstanceOf(NativeGameTransport.DjcUiWarningWaiting.class,t.readCurrentDjcWarning(pending,pending.deadline().plusSeconds(1)));assertEquals(BigInteger.TWO,waiting.frame().querySequence());
            var ready=assertInstanceOf(NativeGameTransport.DjcUiWarningReady.class,t.readCurrentDjcWarning(pending,pending.deadline()));assertEquals(BigInteger.valueOf(3),ready.frame().querySequence());
            var prepared=t.prepareCurrentDjcWarningAcceptance(ready);var request=NativeWire.decodeExecuteRequest(prepared.originalPacket().value());var fields=NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));var claim=NativeWire.object(fields.get("djc_ui"));
            assertEquals("3",claim.get("query_sequence").textValue());assertEquals(replay.sendDeadline,fields.get("core_control_deadline_unix_ms").longValue());assertEquals(replay.sendClaim,claim.get("origin_claim_sequence").textValue());
            var accepted=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentDjcWarningAcceptance(prepared));assertEquals(CurrentDjcDeclarationUiResult.Status.WARNING_DISPATCHED,CurrentDjcDeclarationUiResult.decodeOutcome(accepted).status());assertSame(accepted,t.submitCurrentDjcWarningAcceptance(prepared));assertEquals(2,replay.effects);assertEquals(2,replay.warningReads);
        }
    }
    @Test void lostSendReplyIsRetainedGlobalUnknownAndNeverReplayedWithNewIntent()throws Exception {
        var replay=new Replay("lost-send");try(var t=transport(replay)){var before=core(t);var q=assertInstanceOf(NativeGameTransport.DjcUiReceived.class,t.readCurrentDjcDeclarationUi(before,TARGET,CB,before.validUntil()));var prepared=t.prepareCurrentDjcUiSend(q);var unknown=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentDjcUi(prepared));assertSame(unknown,t.submitCurrentDjcUi(prepared));assertSame(unknown,t.submitCoreNormalExit(before,q.validUntil()));assertEquals(1,replay.effects);}
    }
    @Test void missingCapabilityForeignCoreAndExtendedWindowRejectBeforeQueryWrite()throws Exception {
        var a=new Replay("missing-query");try(var t=transport(a)){var c=core(t);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.readCurrentDjcDeclarationUi(c,TARGET,CB,c.validUntil()).original());assertEquals(0,a.queries);}
        var b=new Replay("resident");var c=new Replay("resident");try(var t=transport(b);var other=transport(c)){var before=core(t);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.readCurrentDjcDeclarationUi(before,TARGET,CB,before.validUntil()).original());assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.readCurrentDjcDeclarationUi(before,TARGET,CB,before.validUntil().plusMillis(1)).original());assertEquals(0,b.queries);assertEquals(0,c.queries);}
    }
    @Test void malformedActualSourceAfterWriteBlocksEffectsAndPreservesCounterexample()throws Exception {
        var replay=new Replay("wrong-owner");try(var t=transport(replay)){var c=core(t);var unavailable=assertInstanceOf(NativeGameTransport.DjcUiUnavailable.class,t.readCurrentDjcDeclarationUi(c,TARGET,CB,c.validUntil()));var unknown=assertInstanceOf(NativeActionPort.Unknown.class,unavailable.original());assertTrue(t.originalIndeterminateCoreAcknowledgement(unknown.requestId()).isPresent());assertSame(unknown,t.submitCoreNormalExit(c,c.validUntil()));assertEquals(0,replay.effects);}
    }
    static final class Replay implements NativePacketPort {
        final String mode;final ArrayDeque<byte[]> packets=new ArrayDeque<>();boolean closed;int queries,effects,warningReads;long sendDeadline;String sendClaim;
        Replay(String mode)throws IOException{this.mode=mode;var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",7).put("bridge_version","djc-ui-data").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);var caps=h.putArray("capabilities");caps.add(CoreFrame.CAPABILITY);for(var a:CurrentDjcDeclarationUi.Action.values())if(!mode.equals("missing-query")||a!=CurrentDjcDeclarationUi.Action.QUERY_UI)caps.add(a.capability());packets.add(NativeWire.packet(StrictJson.canonical(h)));}
        public void verify()throws IOException{if(closed)throw new IOException("DJC UI DATA source closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant until)throws IOException{verify();}public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("DJC UI DATA reply missing");return packets.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException {
            verify();var r=NativeWire.decodeExecuteRequest(packet);ObjectNode token;boolean ok;
            if(r.step().equals(CoreFrame.STEP)){var core=new CoreFrame.Partial(BUILD,new CoreFrame.Prefix(53144328,1,true,0,true,true,777,true));token=NativeWire.object(NativeWire.parse(CoreFramePublicCodec.encode(core).bytes()));ok=true;}
            else {
                var fields=NativeWire.object(NativeWire.parse(r.normalizedAdditionalFields().value()));var claim=NativeWire.object(fields.get("djc_ui"));String action=claim.get("action").textValue();String name;
                if(action.equals("query_ui")){queries++;name=mode.equals("confirmation-false")?"confirmation-false-negative-SYNTHETIC-DATA":mode.equals("open")?"open-ready-SYNTHETIC-DATA":"resident-ready-SYNTHETIC-DATA";}
                else if(action.equals("query_warning")){warningReads++;assertEquals(NativeWire.UINT64_MAX.toString(),claim.get("query_sequence").textValue());assertEquals(sendDeadline,fields.get("core_control_deadline_unix_ms").longValue());assertEquals(sendClaim,claim.get("origin_claim_sequence").textValue());name=warningReads==1?"warning-pending-SYNTHETIC-DATA":"warning-ready-SYNTHETIC-DATA";}
                else {effects++;name=action+"-dispatched-SYNTHETIC-DATA";if(action.equals("send_ui")){sendDeadline=fields.get("core_control_deadline_unix_ms").longValue();if(mode.equals("lost-send"))return;}}
                var actual=NativeCurrentDjcUi26785313ProducerTest.envelope(name);token=NativeWire.object(actual.get("result"));ok=actual.get("ok").booleanValue();
                if(action.equals("send_ui"))sendClaim=token.get("claim_sequence").textValue();
                if(action.equals("query_warning"))token.put("query_sequence",String.valueOf(warningReads+1));
                if(action.equals("accept_warning")){assertEquals("3",claim.get("query_sequence").textValue());token.put("query_sequence","3");}
                if(mode.equals("wrong-owner"))((ObjectNode)token.get("owner_witness")).put("connection_generation","8");
            }
            var out=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",r.requestId()).put("ok",ok);out.set("result",token);packets.add(NativeWire.packet(StrictJson.canonical(out)));
        }
        public void close(){closed=true;}
    }
}
