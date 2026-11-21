package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
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
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiControlsFrameV2;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiControlsFrameV2PublicCodec;

/** Genuine serializer frames through the real Java codec/transport; no Game or window-open claim. */
final class NativeLiteralNavigationV2Test {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    private static Instant until(){return Instant.now().plusSeconds(20);}
    private static String prefix(NativeGameTransport.NavigationAction action){return action==NativeGameTransport.NavigationAction.OPEN_FAITH?"open-faith":"open-rite";}
    private static NativeGameTransport transport(Replay r){return new NativeGameTransport(r,new NativePipeEndpoint.Config("\\\\.\\pipe\\literal-navigation-data","literal-navigation-data",GAME,"literal-navigation-session","literal-navigation-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),32,12);}
    private static NativeGameTransport.GuiControlsReceivedV2 query(NativeGameTransport t,NativeGameTransport.NavigationAction action)throws Exception {
        var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(until()));
        return assertInstanceOf(NativeGameTransport.GuiControlsReceivedV2.class,t.readNavigationGuiControlsV2(core,action,core.validUntil()));
    }
    @Test void bothActualCppPairsRoundtripWithoutInventedRiteOrFullProof()throws Exception {
        for(var action:NativeGameTransport.NavigationAction.values()){
            String p=prefix(action);
            for(String suffix:new String[]{"query-request-v2.json","activate-request-v2.json"}){
                var packet=LiteralNavigationCppFrames.json(p+"-"+suffix);var request=GuiControlsFrameV2PublicCodec.decodeRequestPacket(NativeWire.packet(packet));
                assertTrue(request.window().navigationRoot());assertTrue(request.expectedSourceRiteId().isEmpty());
                assertEquals(request,GuiControlsFrameV2PublicCodec.decodeRequestPacket(NativeWire.execute("roundtrip",request.operation().step(),BigInteger.ZERO,GuiControlsFrameV2PublicCodec.additionalFields(request).bytes())));
            }
            for(String state:new String[]{"available","submitted","indeterminate"}){
                var frame=GuiControlsFrameV2.decode(LiteralNavigationCppFrames.result(p+"-"+state+"-SYNTHETIC-DATA.json"));
                assertTrue(frame.window().navigationRoot());assertFalse(frame.riteSourceVerified());assertTrue(frame.sourceRiteId().isEmpty());
                assertEquals(frame,GuiControlsFrameV2.decode(GuiControlsFrameV2PublicCodec.encode(frame)));
            }
        }
    }
    @Test void actualPairUsesSamePrivateQueryAndOnlyOneLiteralWrite()throws Exception {
        for(var action:NativeGameTransport.NavigationAction.values()){
            var source=new Replay(action,"submitted");try(var t=transport(source)){
                var q=query(t,action);var row=q.frame().widgets().orElseThrow().stream().filter(GuiControlsFrameV2.Widget::nativeCallbackAdmissible).findFirst().orElseThrow();
                assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.submitGuiControlsActivationV2(q,row,q.validUntil()));assertEquals(0,source.activations);
                var ack=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitNavigationGuiControlV2(q,action,q.validUntil()));ack.custody().orElseThrow().verify(ack);
                assertArrayEquals(LiteralNavigationCppFrames.result(prefix(action)+"-submitted-SYNTHETIC-DATA.json").bytes(),ack.originalResultToken().orElseThrow().bytes());
                assertEquals(GuiControlsFrameV2.Status.SUBMITTED,GuiControlsFrameV2PublicCodec.decodeOutcome(ack).status());assertEquals(1,source.activations);
                assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.submitNavigationGuiControlV2(q,action,q.validUntil()));assertEquals(1,source.activations);
            }
        }
    }
    @Test void zeroOrMultipleAdmissibleLiteralRowsNeverWriteActivation()throws Exception {
        for(String kind:new String[]{"zero","multiple"}){
            var source=new Replay(NativeGameTransport.NavigationAction.OPEN_FAITH,kind);try(var t=transport(source)){
                var q=query(t,NativeGameTransport.NavigationAction.OPEN_FAITH);
                assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.submitNavigationGuiControlV2(q,NativeGameTransport.NavigationAction.OPEN_FAITH,q.validUntil()));assertEquals(0,source.activations);
            }
        }
    }
    @Test void wrongRootOrForeignQueryCannotBuyALiteralWrite()throws Exception {
        var a=new Replay(NativeGameTransport.NavigationAction.OPEN_FAITH,"submitted");var b=new Replay(NativeGameTransport.NavigationAction.OPEN_FAITH,"submitted");
        try(var t=transport(a);var other=transport(b)){
            var q=query(t,NativeGameTransport.NavigationAction.OPEN_FAITH);
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.submitNavigationGuiControlV2(q,NativeGameTransport.NavigationAction.OPEN_FAITH,q.validUntil()));
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.submitNavigationGuiControlV2(q,NativeGameTransport.NavigationAction.OPEN_RITE_EDITOR,q.validUntil()));assertEquals(0,a.activations);assertEquals(0,b.activations);
        }
    }
    @Test void actualIndeterminateRetainsOriginalAcrossLaterActions()throws Exception {
        var source=new Replay(NativeGameTransport.NavigationAction.OPEN_FAITH,"indeterminate");try(var t=transport(source)){
            var q=query(t,NativeGameTransport.NavigationAction.OPEN_FAITH);var unknown=assertInstanceOf(NativeActionPort.Unknown.class,t.submitNavigationGuiControlV2(q,NativeGameTransport.NavigationAction.OPEN_FAITH,q.validUntil()));
            assertSame(unknown,t.submitNavigationGuiControlV2(q,NativeGameTransport.NavigationAction.OPEN_RITE_EDITOR,q.validUntil()));assertTrue(t.originalIndeterminateCoreAcknowledgement(unknown.requestId()).isPresent());assertEquals(1,source.activations);
        }
    }
    @Test void historicalHudStaysReadonlyAndCannotBuyBottomActivation()throws Exception {
        var query=GuiControlsFrameV2PublicCodec.decodeRequestPacket(NativeWire.packet(LiteralNavigationCppFrames.json("historical-hud-query-request-v2.json")));
        assertEquals(GuiControlsFrameV2.Window.HUD_LAYER,query.window());assertFalse(query.window().navigationRoot());
        assertThrows(IllegalArgumentException.class,()->GuiControlsFrameV2PublicCodec.activate(query,until(),new GuiControlsFrameV2PublicCodec.SelectionToken(BigInteger.ONE,BigInteger.TWO)));
        assertThrows(IllegalArgumentException.class,()->GuiControlsFrameV2PublicCodec.decodeRequestPacket(NativeWire.packet(LiteralNavigationCppFrames.json("historical-hud-activate-request-v2.json"))));
        assertThrows(IllegalArgumentException.class,()->GuiControlsFrameV2.decode(LiteralNavigationCppFrames.result("historical-hud-available-SYNTHETIC-DATA.json")));
        // Explicit Java compatibility DATA derived from the old genuine source: readonly rows carry no callback admission.
        var readonly=NativeWire.object(NativeWire.parse(LiteralNavigationCppFrames.result("historical-hud-available-SYNTHETIC-DATA.json").bytes()));
        for(var row:readonly.path("widgets"))NativeWire.object(row).put("native_callback_admissible",false);
        var frame=GuiControlsFrameV2.decode(new org.xar.ck3.control.application.action.RawJson(StrictJson.canonical(readonly)));
        assertEquals(GuiControlsFrameV2.Window.HUD_LAYER,frame.window());assertTrue(frame.queryAvailable());
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();final NativeGameTransport.NavigationAction action;final String mode;boolean closed;int activations;
        Replay(NativeGameTransport.NavigationAction action,String mode)throws IOException {
            this.action=action;this.mode=mode;
            var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",7).put("bridge_version","literal-navigation-data").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            hello.putArray("capabilities").add(CoreFrame.CAPABILITY).add(GuiControlsFrameV2.QUERY_CAPABILITY).add(GuiControlsFrameV2.ACTIVATE_CAPABILITY);packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("Software source closed");}
        public void verifyCoreControlWindowPolicy()throws IOException{verify();}
        public void awaitConnection(Instant deadline)throws IOException{verify();}
        public byte[] readPacket(Instant deadline)throws IOException{verify();if(packets.isEmpty())throw new IOException("No actual software packet");return packets.removeFirst();}
        public void writePacket(byte[] packet,Instant deadline)throws IOException {
            verify();var request=NativeWire.decodeExecuteRequest(packet);byte[] body;boolean ok=true;
            try {
                String p=prefix(action),available=p+"-available-SYNTHETIC-DATA.json";
                if(request.step().equals(CoreFrame.STEP))body=CoreFramePublicCodec.encode(LiteralNavigationCppFrames.core(available)).bytes();
                else if(request.step().equals(GuiControlsFrameV2.QUERY_STEP)){
                    body=LiteralNavigationCppFrames.result(available).bytes();
                    if(mode.equals("zero")||mode.equals("multiple")){
                        // Derived Java negative DATA only. Genuine C++ originals are never changed.
                        var root=NativeWire.object(NativeWire.parse(body));
                        if(!(root.get("widgets") instanceof com.fasterxml.jackson.databind.node.ArrayNode rows))throw new IOException("Actual bounded rows array required");
                        if(mode.equals("zero"))for(var row:rows)NativeWire.object(row).put("native_callback_admissible",false);
                        else rows.add(NativeWire.object(rows.get(1)).deepCopy().put("widget_id","3").put("child_path","1"));
                        body=StrictJson.canonical(root);
                    }
                } else {
                    assertEquals(GuiControlsFrameV2.ACTIVATE_STEP,request.step());activations++;var actual=LiteralNavigationCppFrames.response(p+"-"+(mode.equals("indeterminate")?"indeterminate":"submitted")+"-SYNTHETIC-DATA.json");body=actual.result().token().orElseThrow().value();ok=actual.nativeOk();
                }
            }catch(Exception e){throw new IOException("Pinned actual C++ fixture unavailable",e);}
            var out=new ByteArrayOutputStream();out.writeBytes(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+request.requestId()+"\",\"ok\":"+ok+",\"result\":").getBytes(StandardCharsets.UTF_8));out.writeBytes(body);out.write('}');packets.add(NativeWire.packet(out.toByteArray()));
        }
        public void close(){closed=true;}
    }
}
