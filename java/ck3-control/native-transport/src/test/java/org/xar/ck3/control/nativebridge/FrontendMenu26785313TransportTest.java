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
import org.xar.ck3.control.nativebridge.capabilities.registry.FrontendMenuFrameV1;
import org.xar.ck3.control.nativebridge.capabilities.registry.FrontendMenuFrameV1PublicCodec;

/** Actual transport/custody plus exact C++ menu tokens; replay envelopes and negative mutations are Java DATA. */
final class FrontendMenu26785313TransportTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    private static final class MutableClock extends Clock {
        Instant value=Instant.now();public ZoneId getZone(){return ZoneOffset.UTC;}public Clock withZone(ZoneId zone){if(!zone.equals(ZoneOffset.UTC))throw new IllegalArgumentException("UTC DATA fixture");return this;}public Instant instant(){return value;}
    }
    private static Instant until(MutableClock c){return c.instant().plusSeconds(25);}
    private static NativeGameTransport transport(Replay replay,MutableClock clock){return new NativeGameTransport(replay,new NativePipeEndpoint.Config("\\\\.\\pipe\\current-menu-data","current-menu-data",GAME,"current-menu-session","current-menu-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),32,24,List.of(),clock);}
    private static NativeGameTransport.FrontendMenuReceived menu(NativeGameTransport transport,MutableClock clock)throws Exception {
        var read=transport.readCurrentFrontendMenu(until(clock));return assertInstanceOf(NativeGameTransport.FrontendMenuReceived.class,read,()->read.toString());
    }
    @Test void actualMenuQueryWithoutCorePreparesOriginalDeadlineAndQuitsExactlyOnce()throws Exception {
        var c=new MutableClock();var r=new Replay("success",true);try(var t=transport(r,c)){
            var before=menu(t,c);var prepared=t.prepareCurrentFrontendMenuAction(before,FrontendMenuFrameV1.Action.QUIT_MENU);assertEquals(0,r.quits);
            var request=FrontendMenuFrameV1PublicCodec.decodeRequestPacket(prepared.originalPacket().value());assertEquals(before.validUntil(),prepared.deadline());assertEquals(before.frame().providerGeneration(),request.lease().providerGeneration());assertEquals(before.frame().querySequence(),request.lease().querySequence());
            var original=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentFrontendMenuAction(prepared));original.custody().orElseThrow().verify(original);
            assertArrayEquals(FrontendMenuCppFrames.result(FrontendMenuFrameV1.Action.QUIT_MENU,FrontendMenuFrameV1.Status.EXIT_REQUESTED).bytes(),original.originalResultToken().orElseThrow().bytes());
            assertEquals(FrontendMenuFrameV1.Status.EXIT_REQUESTED,FrontendMenuFrameV1PublicCodec.decodeOutcome(original).status());assertSame(original,t.submitCurrentFrontendMenuAction(prepared));
            assertEquals(1,r.queries);assertEquals(1,r.quits);assertEquals(0,r.cores);
        }
    }
    @Test void callerDataAndForeignReceiverCannotMintMenuActionAuthority()throws Exception {
        assertEquals(0,NativeGameTransport.FrontendMenuReceived.class.getConstructors().length);
        var c=new MutableClock();var a=new Replay("success",true);var b=new Replay("success",true);try(var t=transport(a,c);var other=transport(b,c)){
            var actual=menu(t,c);assertThrows(IOException.class,()->other.prepareCurrentFrontendMenuAction(actual,FrontendMenuFrameV1.Action.QUIT_MENU));
            var prepared=t.prepareCurrentFrontendMenuAction(actual,FrontendMenuFrameV1.Action.QUIT_MENU);assertThrows(IOException.class,()->other.submitCurrentFrontendMenuAction(prepared));assertEquals(0,a.quits);assertEquals(0,b.queries);assertEquals(0,b.quits);
        }
    }
    @Test void absentQuitOrRobertCapabilitiesAndLegacyFrontendEntryWriteZeroEffects()throws Exception {
        var c=new MutableClock();var r=new Replay("success",false);try(var t=transport(r,c)){
            var actual=menu(t,c);assertThrows(IOException.class,()->t.prepareCurrentFrontendMenuAction(actual,FrontendMenuFrameV1.Action.QUIT_MENU));
            assertThrows(IOException.class,()->t.prepareCurrentFrontendMenuAction(actual,FrontendMenuFrameV1.Action.SELECT_ROBERT_1066));
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.readFrontendRoute(until(c)));assertEquals(1,r.queries);assertEquals(0,r.quits);assertEquals(0,r.cores);
        }
    }
    @Test void oneOriginalMenuCannotPrepareDifferentEffectsOrRefreshExpiredDeadline()throws Exception {
        var c=new MutableClock();var r=new Replay("success",true);try(var t=transport(r,c)){
            var before=menu(t,c);var p=t.prepareCurrentFrontendMenuAction(before,FrontendMenuFrameV1.Action.QUIT_MENU);assertSame(p,t.prepareCurrentFrontendMenuAction(before,FrontendMenuFrameV1.Action.QUIT_MENU));
            assertThrows(IOException.class,()->t.prepareCurrentFrontendMenuAction(before,FrontendMenuFrameV1.Action.OPEN_BOOKMARKS));c.value=c.value.plusSeconds(60);
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.submitCurrentFrontendMenuAction(p));assertThrows(IOException.class,()->t.prepareCurrentFrontendMenuAction(before,FrontendMenuFrameV1.Action.QUIT_MENU));assertEquals(0,r.quits);
        }
    }
    @Test void foreignOwnerOrNoWorldFailureCannotBecomeAReceivedMenu()throws Exception {
        for(String mode:new String[]{"wrong-owner","world-present"}){
            var c=new MutableClock();var r=new Replay(mode,true);try(var t=transport(r,c)){
                var read=t.readCurrentFrontendMenu(until(c));assertInstanceOf(NativeGameTransport.FrontendMenuUnavailable.class,read);assertInstanceOf(NativeActionPort.Unknown.class,read.original());assertEquals(1,r.queries);assertEquals(0,r.quits);
            }
        }
    }
    @Test void lostOrIndeterminateQuitIsStickyAcrossNewQueriesAndCoreActions()throws Exception {
        for(String mode:new String[]{"lost-quit","indeterminate"}){
            var c=new MutableClock();var r=new Replay(mode,true);try(var t=transport(r,c)){
                var prepared=t.prepareCurrentFrontendMenuAction(menu(t,c),FrontendMenuFrameV1.Action.QUIT_MENU);var original=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentFrontendMenuAction(prepared));
                assertEquals(prepared.requestId(),original.requestId());assertSame(original,t.submitCurrentFrontendMenuAction(prepared));assertSame(original,t.submitCoreNormalExit(null,until(c)));
                var fresh=menu(t,c);assertThrows(IOException.class,()->t.prepareCurrentFrontendMenuAction(fresh,FrontendMenuFrameV1.Action.QUIT_MENU));assertEquals(1,r.quits);assertEquals(0,r.cores);
                if(mode.equals("indeterminate"))assertTrue(t.originalIndeterminateCoreAcknowledgement(original.requestId()).isPresent());
            }
        }
    }
    @Test void changedEffectLeaseOrOwnerPreservesRawAckAsUnknownWithoutReplay()throws Exception {
        for(String mode:new String[]{"wrong-effect-lease","wrong-effect-owner"}){
            var c=new MutableClock();var r=new Replay(mode,true);try(var t=transport(r,c)){
                var prepared=t.prepareCurrentFrontendMenuAction(menu(t,c),FrontendMenuFrameV1.Action.QUIT_MENU);var original=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentFrontendMenuAction(prepared));
                assertTrue(t.originalIndeterminateCoreAcknowledgement(original.requestId()).isPresent());assertSame(original,t.submitCurrentFrontendMenuAction(prepared));assertEquals(1,r.quits);
            }
        }
    }
    @Test void interruptedQueryAfterWriteBlocksEffectsAndRetainsItsOriginalId()throws Exception {
        var c=new MutableClock();var r=new Replay("interrupt-query",true);try(var t=transport(r,c)){
            var read=t.readCurrentFrontendMenu(until(c));assertInstanceOf(NativeGameTransport.FrontendMenuUnavailable.class,read);var unknown=assertInstanceOf(NativeActionPort.Unknown.class,read.original());
            assertTrue(Thread.interrupted());assertSame(unknown,t.submitCoreNormalExit(null,until(c)));assertEquals(1,r.queries);assertEquals(0,r.quits);
        }finally{Thread.interrupted();}
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();final String mode;boolean closed;int queries,quits,cores;
        Replay(String mode,boolean quitCapability)throws Exception {
            this.mode=mode;var actual=FrontendMenuCppFrames.available();
            var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",actual.ownerWitness().orElseThrow().connectionGeneration()).put("bridge_version","current-menu-data")
                    .put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=hello.putArray("capabilities").add(FrontendMenuFrameV1.Action.QUERY_MENU.capability());if(quitCapability)caps.add(FrontendMenuFrameV1.Action.QUIT_MENU.capability());packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("Menu replay DATA closed");}
        public void verifyCoreControlWindowPolicy()throws IOException{verify();}
        public void awaitConnection(Instant deadline)throws IOException{verify();}
        public byte[] readPacket(Instant deadline)throws IOException,InterruptedException {
            verify();if(mode.equals("interrupt-query")&&queries>0)throw new InterruptedException("Java DATA interrupted original query");if(packets.isEmpty())throw new IOException("Original replay response absent");return packets.removeFirst();
        }
        public void writePacket(byte[] packet,Instant deadline)throws IOException {
            verify();var outgoing=NativeWire.decodeExecuteRequest(packet);byte[] body;boolean ok;
            try {
                if(outgoing.step().equals("query-core-frame-v1")){cores++;throw new IOException("NoWorld DATA endpoint must never receive a Core request");}
                var request=FrontendMenuFrameV1PublicCodec.decodeRequestPacket(packet);NativeWire.CommandResult actual;
                if(request.action()==FrontendMenuFrameV1.Action.QUERY_MENU){queries++;actual=FrontendMenuCppFrames.response(FrontendMenuFrameV1.Action.QUERY_MENU,FrontendMenuFrameV1.Status.AVAILABLE);}
                else if(request.action()==FrontendMenuFrameV1.Action.QUIT_MENU){quits++;if(mode.equals("lost-quit"))return;actual=FrontendMenuCppFrames.response(FrontendMenuFrameV1.Action.QUIT_MENU,mode.equals("indeterminate")?FrontendMenuFrameV1.Status.INDETERMINATE:FrontendMenuFrameV1.Status.EXIT_REQUESTED);}
                else throw new IOException("Unexpected fixed menu operation");
                body=actual.result().token().orElseThrow().value();ok=actual.nativeOk();
                if(mode.equals("wrong-owner")||mode.equals("world-present")||request.action()==FrontendMenuFrameV1.Action.QUIT_MENU&&mode.startsWith("wrong-effect")) {
                    // Explicit Java negative DATA mutations, never relabelled as actual C++ originals.
                    var row=NativeWire.object(NativeWire.parse(body));
                    if(mode.equals("wrong-owner")||mode.equals("wrong-effect-owner"))NativeWire.object(row.get("owner_witness")).put("connection_generation",FrontendMenuCppFrames.available().ownerWitness().orElseThrow().connectionGeneration().add(BigInteger.ONE).toString());
                    if(mode.equals("world-present"))NativeWire.object(row.get("source")).put("no_world",false);
                    if(mode.equals("wrong-effect-lease"))row.put("query_sequence",FrontendMenuCppFrames.available().querySequence().equals(BigInteger.ONE)?"2":"1");
                    body=StrictJson.canonical(row);
                }
            }catch(Exception failure){throw new IOException("Actual menu token or labelled replay DATA invalid",failure);}
            var response=new ByteArrayOutputStream();response.writeBytes(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+outgoing.requestId()+"\",\"ok\":"+ok+",\"result\":").getBytes(StandardCharsets.UTF_8));response.writeBytes(body);response.write('}');packets.add(NativeWire.packet(response.toByteArray()));
        }
        public void close(){closed=true;}
    }
}
