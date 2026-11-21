package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** Original C++ result tokens; only fresh request envelopes and explicit negative counterexamples are Java DATA. */
class NativeCurrentDjcSelectedCostTransportTest {
    static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    static NativeGameTransport transport(Replay r){return new NativeGameTransport(r,new NativePipeEndpoint.Config("\\\\.\\pipe\\djc-cost-data","djc-cost-data",GAME,"djc-cost-session","djc-cost-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),64,32);}
    record Point(NativeGameTransport.CoreReceived core,NativeGameTransport.DjcUiReceived query) { }
    static Point query(NativeGameTransport t)throws Exception {
        var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(Instant.now().plusSeconds(20)));
        var q=assertInstanceOf(NativeGameTransport.DjcUiReceived.class,t.readCurrentDjcDeclarationUi(core,new NativeCharacterId(39957),CurrentDjcTargetWarQueryResult.CasusBelliKey.DUCHY,core.validUntil()));return new Point(core,q);
    }
    @Test void readonlyCostUsesOriginalLeaseDeadlineAndLeavesOriginalUiAuthorityUnconsumed()throws Exception {
        var replay=new Replay("normal");try(var t=transport(replay)) {
            var p=query(t);var cost=assertInstanceOf(NativeGameTransport.DjcSelectedCostReceived.class,t.readCurrentDjcSelectedCost(p.query()));
            assertEquals("-9223372036854775808",cost.frame().costs().orElseThrow().getFirst().raw());p.query().requireOriginal(t,p.query().validUntil());
            assertEquals(1,replay.costReads);assertEquals(0,replay.effects);assertEquals(p.query().validUntil().toEpochMilli(),replay.costDeadline);assertNotEquals(p.query().original().requestId(),cost.original().requestId());
        }
    }
    @Test void missingCapabilityAndForeignReceiverCannotWriteACostRequest()throws Exception {
        var a=new Replay("missing-cap");try(var t=transport(a)){var p=query(t);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.readCurrentDjcSelectedCost(p.query()).original());assertEquals(0,a.costReads);}
        var b=new Replay("normal");var c=new Replay("normal");try(var t=transport(b);var other=transport(c)){var q=query(t);query(other);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.readCurrentDjcSelectedCost(q.query()).original());assertEquals(0,b.costReads);assertEquals(0,c.costReads);}
    }
    @Test void changedActualLeaseRetainsOriginalCounterexampleAndBlocksControl()throws Exception {
        var r=new Replay("wrong-lease");try(var t=transport(r)){var p=query(t);var refused=t.readCurrentDjcSelectedCost(p.query());var unknown=assertInstanceOf(NativeActionPort.Unknown.class,refused.original());assertTrue(t.originalIndeterminateCoreAcknowledgement(unknown.requestId()).isPresent());assertSame(unknown,t.submitCoreNormalExit(p.core(),p.core().validUntil()));assertEquals(1,r.costReads);assertEquals(0,r.effects);}
    }
    @Test void changedOrderedSelectedTupleCannotReturnAPrivatelyQualifiedPrice()throws Exception {
        var r=new Replay("wrong-selected");try(var t=transport(r)){var p=query(t);var read=t.readCurrentDjcSelectedCost(p.query());assertInstanceOf(NativeActionPort.Unknown.class,read.original());assertThrows(IOException.class,()->p.query().requireOriginal(t,p.query().validUntil()));assertEquals(0,r.effects);}
    }
    @Test void bothActualCppIndeterminateCasesBecomeGlobalUnknownAndNeverMintZeroPrices()throws Exception {
        for(String mode:List.of("indeterminate-cleanup","indeterminate-incomplete")) {
            var r=new Replay(mode);try(var t=transport(r)){var p=query(t);var read=t.readCurrentDjcSelectedCost(p.query());assertInstanceOf(NativeGameTransport.DjcSelectedCostUnavailable.class,read);assertInstanceOf(NativeActionPort.Unknown.class,read.original());assertThrows(IOException.class,()->p.query().requireOriginal(t,p.query().validUntil()));assertEquals(0,r.effects);}
        }
    }
    @Test void replacedPrivateQueryOrInvisibleSourceCannotImplicitlyOpenSelectOrSend()throws Exception {
        var a=new Replay("normal");try(var t=transport(a)){var p=query(t);assertInstanceOf(NativeGameTransport.DjcUiReceived.class,t.readCurrentDjcDeclarationUi(p.core(),new NativeCharacterId(39957),CurrentDjcTargetWarQueryResult.CasusBelliKey.DUCHY,p.core().validUntil()));assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.readCurrentDjcSelectedCost(p.query()).original());assertEquals(0,a.costReads);}
        var b=new Replay("invisible");try(var t=transport(b)){var p=query(t);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.readCurrentDjcSelectedCost(p.query()).original());assertEquals(0,b.costReads);assertEquals(0,b.effects);}
    }
    @Test void lostReadonlyReplyCannotBeRetriedIntoAnEffectAndKeepsOriginalRequest()throws Exception {
        var r=new Replay("lost");try(var t=transport(r)){var p=query(t);var unknown=assertInstanceOf(NativeActionPort.Unknown.class,t.readCurrentDjcSelectedCost(p.query()).original());assertInstanceOf(NativeGameTransport.DjcSelectedCostUnavailable.class,t.readCurrentDjcSelectedCost(p.query()));assertEquals(1,r.costReads);assertSame(unknown,t.submitCoreNormalExit(p.core(),p.core().validUntil()));assertEquals(0,r.effects);}
    }
    static final class Replay implements NativePacketPort {
        final String mode;final ArrayDeque<byte[]> packets=new ArrayDeque<>();boolean closed;int costReads,effects;long uiDeadline,costDeadline;
        Replay(String mode)throws IOException {
            this.mode=mode;var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",7).put("bridge_version","djc-cost-data").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=h.putArray("capabilities");caps.add(CoreFrame.CAPABILITY);for(var action:CurrentDjcDeclarationUi.Action.values())caps.add(action.capability());if(!mode.equals("missing-cap"))caps.add(CurrentDjcSelectedCost.CAPABILITY);packets.add(NativeWire.packet(StrictJson.canonical(h)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("DJC cost DATA port closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant until)throws IOException{verify();}public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("Original cost DATA reply absent");return packets.removeFirst();}
        public void writePacket(byte[] bytes,Instant until)throws IOException {
            verify();var request=NativeWire.decodeExecuteRequest(bytes);ObjectNode token;boolean ok;
            if(request.step().equals(CoreFrame.STEP)) {
                var facts=NativeCurrentDjcSelectedCost26785313ProducerTest.decode(NativeCurrentDjcSelectedCost26785313ProducerTest.token("available-fullrange")).factsBefore().orElseThrow();
                token=NativeWire.object(NativeWire.parse(CoreFramePublicCodec.encode(new CoreFrame.Partial(BUILD,facts)).bytes()));ok=true;
            } else {
                var fields=NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));ObjectNode original;
                if(request.step().equals(CurrentDjcDeclarationUi.Action.QUERY_UI.step())) {
                    uiDeadline=fields.get("core_control_deadline_unix_ms").longValue();original=NativeCurrentDjcSelectedCost26785313ProducerTest.envelope("source-v23-query");
                } else if(request.step().equals(CurrentDjcSelectedCost.STEP)) {
                    costReads++;costDeadline=fields.get("core_control_deadline_unix_ms").longValue();assertEquals(uiDeadline,costDeadline);assertEquals(until.toEpochMilli(),costDeadline);
                    var claim=fields.get("djc_selected_cost");assertEquals(11,claim.size());assertEquals(NativeWire.UINT64_MAX.toString(),claim.get("provider_generation").textValue());assertEquals(NativeWire.UINT64_MAX.toString(),claim.get("query_sequence").textValue());
                    String evidence=System.getProperty("xar.djc.selected.cost.request.output");
                    if(mode.equals("normal")&&evidence!=null) {
                        var root=java.nio.file.Path.of(evidence).toAbsolutePath().normalize();if(!root.getRoot().toString().equalsIgnoreCase("D:\\"))throw new IOException("Actual request evidence requires D");java.nio.file.Files.createDirectories(root);
                        var raw=root.resolve("selected-cost.request.packet");if(!java.nio.file.Files.exists(raw)) {
                            java.nio.file.Files.write(raw,bytes,java.nio.file.StandardOpenOption.CREATE_NEW);
                            java.nio.file.Files.write(root.resolve("selected-cost.request.json"),java.util.Arrays.copyOfRange(bytes,4,bytes.length),java.nio.file.StandardOpenOption.CREATE_NEW);
                        }
                    }
                    if(mode.equals("lost"))return;
                    original=NativeCurrentDjcSelectedCost26785313ProducerTest.envelope(mode.startsWith("indeterminate-")?mode:"available-fullrange");
                } else {effects++;throw new IOException("Unexpected action write in a readonly selected-cost test");}
                token=NativeWire.object(original.get("result"));ok=original.get("ok").booleanValue();
                if(request.step().equals(CurrentDjcSelectedCost.STEP)&&mode.equals("wrong-lease"))token.put("query_sequence",NativeWire.UINT64_MAX.subtract(BigInteger.ONE).toString());
                if(request.step().equals(CurrentDjcSelectedCost.STEP)&&mode.equals("wrong-selected"))((ObjectNode)token.get("source").get("selected")).putArray("target_title_ids").add(7).add(2264);
                if(request.step().equals(CurrentDjcDeclarationUi.Action.QUERY_UI.step())&&mode.equals("invisible")){((ObjectNode)token.get("source")).put("window_visible",false).put("window_enabled",false);}
            }
            var envelope=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",ok);envelope.set("result",token);packets.add(NativeWire.packet(StrictJson.canonical(envelope)));
        }
        public void close(){closed=true;}
    }
}
