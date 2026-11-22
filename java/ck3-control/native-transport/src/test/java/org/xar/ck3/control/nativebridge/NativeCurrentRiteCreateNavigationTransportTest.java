package org.xar.ck3.control.nativebridge;
import static org.junit.jupiter.api.Assertions.*;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
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

/** Labelled Java new-literal DATA over original old navigation shapes; this is not a new Native producer. */
final class NativeCurrentRiteCreateNavigationTransportTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    private static Instant until(){return Instant.now().plusSeconds(25);}
    private static NativeGameTransport transport(Replay r){return new NativeGameTransport(r,new NativePipeEndpoint.Config("\\\\.\\pipe\\new-create-nav-DATA","new-create-nav-data",GAME,"new-create-nav-DATA","new-create-nav-DATA",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),64,32);}
    private static NativeGameTransport.GuiControlsReceivedV2 query(NativeGameTransport t,NativeGameTransport.RiteCreateNavigationAction action)throws Exception{
        var original=t.readCoreFrameReceived(until());var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,original,()->original instanceof NativeGameTransport.CoreReadUnavailable u?u.reason():original.toString());
        return assertInstanceOf(NativeGameTransport.GuiControlsReceivedV2.class,t.readCurrentRiteCreateNavigation(core,action,core.validUntil()));
    }
    @Test void twoNewFixedLiteralsHaveIndependentUniquenessWhileOldEnumRemainsTwo()throws Exception{
        assertArrayEquals(new String[]{"OPEN_FAITH","OPEN_RITE_EDITOR"},java.util.Arrays.stream(NativeGameTransport.NavigationAction.values()).map(Enum::name).toArray(String[]::new));
        for(var action:NativeGameTransport.RiteCreateNavigationAction.values()){
            var r=new Replay("all-three");try(var t=transport(r)){
                var q=query(t,action);assertEquals(3,q.frame().widgets().orElseThrow().size());var p=t.prepareCurrentRiteCreateNavigation(q,action);assertEquals(0,r.effects);
                var actual=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentRiteCreateNavigation(p));assertTrue(actual.nativeOk());assertSame(actual,t.submitCurrentRiteCreateNavigation(p));assertEquals(1,r.effects);
            }
        }
    }
    @Test void oldV15OrGenericFaithRowsCannotBuyNewCreateCallback()throws Exception{
        var r=new Replay("all-three");try(var t=transport(r)){
            var q=query(t,NativeGameTransport.RiteCreateNavigationAction.OPEN_RITE_CREATOR);var row=q.frame().widgets().orElseThrow().get(0);
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.submitGuiControlsActivationV2(q,row,q.validUntil()));
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.submitNavigationGuiControlV2(q,NativeGameTransport.NavigationAction.OPEN_RITE_EDITOR,q.validUntil()));assertEquals(0,r.effects);
            var p=t.prepareCurrentRiteCreateNavigation(q,NativeGameTransport.RiteCreateNavigationAction.OPEN_RITE_CREATOR);assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentRiteCreateNavigation(p));assertEquals(1,r.effects);
        }
    }
    @Test void zeroOrDuplicateSelectedLiteralRejectsButDoesNotConfuseOtherLiteral()throws Exception{
        for(String mode:new String[]{"zero-normal","duplicate-normal"}){
            var r=new Replay(mode);try(var t=transport(r)){
                var q=query(t,NativeGameTransport.RiteCreateNavigationAction.OPEN_RITE_CREATOR);assertThrows(IOException.class,()->t.prepareCurrentRiteCreateNavigation(q,NativeGameTransport.RiteCreateNavigationAction.OPEN_RITE_CREATOR));assertEquals(0,r.effects);
                var p=t.prepareCurrentRiteCreateNavigation(q,NativeGameTransport.RiteCreateNavigationAction.OPEN_PUPPET_RITE_CREATOR);assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentRiteCreateNavigation(p));assertEquals(1,r.effects);
            }
        }
    }
    @Test void foreignReceiptUnknownLiteralAndWrongWindowNeverGainNewCallback()throws Exception{
        var a=new Replay("all-three");var b=new Replay("all-three");try(var t=transport(a);var other=transport(b)){
            var q=query(t,NativeGameTransport.RiteCreateNavigationAction.OPEN_RITE_CREATOR);assertThrows(IOException.class,()->other.prepareCurrentRiteCreateNavigation(q,NativeGameTransport.RiteCreateNavigationAction.OPEN_RITE_CREATOR));assertEquals(0,b.effects);
        }
        for(String mode:new String[]{"unknown-name","wrong-window"}){
            var node=NativeWire.object(NativeWire.parse(Replay.queryBody(mode)));
            assertThrows(IllegalArgumentException.class,()->GuiControlsFrameV2.decode(new RawJson(StrictJson.canonical(node))));
        }
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> queue=new ArrayDeque<>();final String mode;boolean closed;int effects;
        Replay(String mode)throws Exception{
            this.mode=mode;var f=GuiControlsFrameV2.decode(LiteralNavigationCppFrames.result("open-rite-available-SYNTHETIC-DATA.json"));
            var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",f.ownerWitness().orElseThrow().connectionGeneration()).put("bridge_version","new-create-nav-DATA").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            h.putArray("capabilities").add(CoreFrame.CAPABILITY).add(GuiControlsFrameV2.QUERY_CAPABILITY).add(GuiControlsFrameV2.ACTIVATE_CAPABILITY).add(CurrentRiteCreate.CAPABILITY);queue.add(NativeWire.packet(StrictJson.canonical(h)));
        }
        static byte[] queryBody(String mode)throws Exception{
            var n=NativeWire.object(NativeWire.parse(LiteralNavigationCppFrames.result("open-rite-available-SYNTHETIC-DATA.json").bytes()));var rows=n.putArray("widgets");
            for(int i=0;i<3;i++){
                String name=i==0?"create_rite":i==1?"create_rite_puppet":mode.equals("duplicate-normal")?"create_rite":"edit_rite";
                boolean admitted=i<2||mode.equals("duplicate-normal");if(mode.equals("zero-normal")&&i==0)admitted=false;if(mode.equals("unknown-name")&&i==0)name="create_rite_unknown";
                rows.addObject().put("widget_id",Integer.toString(i+1)).put("runtime_name",name).put("child_path",Integer.toString(i)).put("effective_visible",true).put("enabled",true).put("native_callback_admissible",admitted);
            }
            if(mode.equals("wrong-window"))n.put("window_name","bottom");return StrictJson.canonical(n);
        }
        public void verify()throws IOException{if(closed)throw new IOException("Replay DATA closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant until)throws IOException{verify();}
        public byte[] readPacket(Instant until)throws IOException{verify();if(queue.isEmpty())throw new IOException("Replay DATA missing");return queue.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException{
            verify();var request=NativeWire.decodeExecuteRequest(packet);byte[] body;try{
                if(request.step().equals(CoreFrame.STEP)){var f=GuiControlsFrameV2.decode(LiteralNavigationCppFrames.result("open-rite-available-SYNTHETIC-DATA.json"));body=CoreFramePublicCodec.encode(f.coreFrame()).bytes();}
                else if(request.step().equals(GuiControlsFrameV2.QUERY_STEP))body=queryBody(mode);
                else{effects++;body=LiteralNavigationCppFrames.result("open-rite-submitted-SYNTHETIC-DATA.json").bytes();}
            }catch(Exception invalid){throw new IOException("Original navigation shape or labelled new-literal DATA invalid",invalid);}
            var out=new ByteArrayOutputStream();out.writeBytes(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+request.requestId()+"\",\"ok\":true,\"result\":").getBytes(StandardCharsets.UTF_8));out.writeBytes(body);out.write('}');queue.add(NativeWire.packet(out.toByteArray()));
        }
        public void close(){closed=true;}
    }
}
