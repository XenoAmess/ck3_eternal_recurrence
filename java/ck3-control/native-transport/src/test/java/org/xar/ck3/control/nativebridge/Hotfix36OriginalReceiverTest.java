package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayDeque;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.FullSnapshotClockControl;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativeSemanticNormalizer;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Actual C++36 RAM Full/Core and DTO formatter bytes. HELLO, framing/correlation and peer IO
 * are explicit software fixtures, not actual Native IPC, dispatch, Root or live evidence. */
final class Hotfix36OriginalReceiverTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_1210_STEAM_26757580;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final String BRIDGE="software-hotfix36";
    private static byte[] original(String name,int bytes,String sha)throws Exception {
        String root=System.getProperty("xar.hotfix36.originals");
        assertNotNull(root,"required Native36 immutable originals directory");
        Path base=Path.of(root);assertTrue(base.isAbsolute());byte[] raw=Files.readAllBytes(base.resolve(name));
        assertEquals(bytes,raw.length);assertEquals(sha,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));return raw;
    }
    private static byte[] full()throws Exception {
        return original("full-ram36.json",1193,"07561b0988088aaf375c4460adbb3a84f64d3e1483b60f5fd71e36132f43120a");
    }
    private static byte[] clockResult()throws Exception {
        return original("clock-formatter36.json",543,"20f61ad9524749ef71beba162ded3f68b1b7e90d9483241706047ed1078da6bd");
    }
    @Test void actualRamFullAndCoreReachTheExactJavaReceiverAndClockParser()throws Exception {
        var core=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(original(
                "core-ram36.json",706,"d34f8245c65f24fda568e268a27545e3e91025c6ee50687b4026e847f7ec6901"))));
        var prefix=assertInstanceOf(CoreFrame.Partial.class,CoreFrame.decode(new RawJson(core.result().token().orElseThrow().value())));
        assertSame(BUILD,prefix.build());assertEquals(-2130706431,prefix.prefix().playedCharacterId());
        try(var fixture=new Fixture(false)) {
            var received=assertInstanceOf(NativeGameTransport.FullClockReceived.class,fixture.transport.readFullClockFrameReceived(fixture.deadline));
            var cpp=assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(NativeWire.packet(full())));
            assertArrayEquals(cpp.state().value(),received.frame().state().bytes());
            var raw=NativeWire.object(NativeWire.parse(cpp.state().value()));
            assertFalse(raw.has("has_active_event"),"do not require a field absent from the actual producer");
            var semantic=NativeSemanticNormalizer.normalize(NativeSemanticNormalizer.original(raw),cpp.snapshotId(),cpp.revision()).semantic();
            assertEquals(-2130706431,semantic.path("played_character").path("character_id").intValue());
            assertTrue(semantic.path("played_character").path("has_heir").isMissingNode(),"unobserved heir is not false");
            var save=FullSnapshotClockControl.request("save-checkpoint",received.frame().snapshotId(),received.frame().nativeRevision(),received.validUntil());
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,fixture.transport.submitFullClockControl(received,save,received.validUntil()));
            assertEquals(1,fixture.peer.writes,"even the software peer's false SAVE advertisement cannot qualify this profile");
            var request=FullSnapshotClockControl.request(BUILD,"pause-map",received.frame().snapshotId(),received.frame().nativeRevision(),received.validUntil());
            var outcome=fixture.transport.submitFullClockControl(received,request,received.validUntil());
            var unknown=assertInstanceOf(NativeActionPort.Unknown.class,outcome,String.valueOf(outcome));
            assertTrue(unknown.reason().contains("is uncertain: already_satisfied"));
            var ack=fixture.transport.originalIndeterminateFullClockAcknowledgement(unknown.requestId()).orElseThrow();
            var dto=FullSnapshotClockControlResult.decode(ack,"pause-map");
            assertEquals(FullSnapshotClockControlResult.Disposition.UNKNOWN,dto.disposition());
            assertFalse(dto.fullBeforeVerified());assertEquals("already_satisfied",dto.queueStatus());
            assertFalse(dto.effectAttempted());assertEquals(2,fixture.peer.writes);
        }
    }
    @Test void anOtherwiseValidOtherProfileClockAckBecomesRetainedUnknownAndCannotReplay()throws Exception {
        try(var fixture=new Fixture(true)) {
            var received=assertInstanceOf(NativeGameTransport.FullClockReceived.class,fixture.transport.readFullClockFrameReceived(fixture.deadline));
            var request=FullSnapshotClockControl.request(BUILD,"pause-map",received.frame().snapshotId(),received.frame().nativeRevision(),received.validUntil());
            var outcome=fixture.transport.submitFullClockControl(received,request,received.validUntil());
            var unknown=assertInstanceOf(NativeActionPort.Unknown.class,outcome,String.valueOf(outcome));
            assertTrue(fixture.transport.originalIndeterminateFullClockAcknowledgement(unknown.requestId()).isPresent());
            assertSame(unknown,fixture.transport.submitFullClockControl(received,request,received.validUntil()));
            assertEquals(2,fixture.peer.writes,"after-write uncertainty cannot create a third submission");
        }
    }
    @Test void actualExitNegativeFormatterDoesNotClaimAnExitOrNativeDispatch()throws Exception {
        byte[] raw=original("exit-negative-formatter36.json",548,"773868549663a173b1f0c240b6328122d23965c67bbec6305041ace2d941086d");
        var ack=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(raw)));
        assertFalse(ack.nativeOk());var value=NativeWire.object(NativeWire.parse(ack.result().token().orElseThrow().value()));
        assertEquals(BUILD.coreFullAdapterId(),value.path("adapter_id").textValue());
        assertEquals("unavailable",value.path("dispatch_status").textValue());
        assertFalse(value.path("normal_exit_confirmed").booleanValue());assertFalse(value.path("effect_attempted").booleanValue());
    }
    @Test void unavailableSoftwareBackgroundPolicyStillPreventsAnyControlWrite()throws Exception {
        try(var fixture=new Fixture(false)) {
            var received=assertInstanceOf(NativeGameTransport.FullClockReceived.class,fixture.transport.readFullClockFrameReceived(fixture.deadline));
            fixture.peer.backgroundReady=false;
            var request=FullSnapshotClockControl.request(BUILD,"pause-map",received.frame().snapshotId(),received.frame().nativeRevision(),received.validUntil());
            var outcome=fixture.transport.submitFullClockControl(received,request,received.validUntil());
            var zero=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,outcome,String.valueOf(outcome));
            assertTrue(zero.proof().reason().contains("software background guard unavailable"));
            assertEquals(1,fixture.peer.writes,"only the original Full query was written");
        }
    }
    private static final class Fixture implements AutoCloseable {
        final Clock clock=Clock.fixed(Instant.now(),ZoneOffset.UTC);
        final Instant deadline=clock.instant().plusSeconds(120);
        final Peer peer;final NativeGameTransport transport;
        Fixture(boolean foreign)throws Exception {
            peer=new Peer(full(),clockResult(),foreign);String slash=Character.toString(92);
            var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"hotfix36-software","hotfix36-software",GAME,"hotfix36-session",BRIDGE,BUILD.executableSha256(),BUILD.coreFullAdapterId());
            transport=new NativeGameTransport(peer,config,32,16,List.of(),clock);
        }
        @Override public void close()throws IOException{transport.close();}
    }
    private static final class Peer implements NativePacketPort {
        final ArrayDeque<byte[]> incoming=new ArrayDeque<>();final byte[] full,clockResult;final boolean foreign;
        int writes;boolean closed;boolean backgroundReady=true;
        Peer(byte[] full,byte[] clockResult,boolean foreign)throws IOException {
            this.full=full;this.clockResult=clockResult;this.foreign=foreign;
            var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",1)
                    .put("bridge_version",BRIDGE).put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256())
                    .put("game_adapter_id",BUILD.coreFullAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            // Deliberately false software SAVE advertisement tests the profile gate; Native36 has no SAVE capability.
            hello.putArray("capabilities").add("game.state.snapshot").add(NativeFreshSnapshotPort.CAPABILITY)
                    .add("game.command.pause-map").add("game.command.save-checkpoint");
            incoming.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        @Override public void verify()throws IOException{if(closed)throw new IOException("own software fixture closed");}
        /** Explicit software guard, matching the existing NativeFullSnapshotClockControlPortTest fixture; no OS observation. */
        @Override public void verifyCoreControlWindowPolicy()throws IOException{verify();if(!backgroundReady)throw new IOException("software background guard unavailable");}
        @Override public void awaitConnection(Instant deadline)throws IOException{verify();}
        @Override public byte[] readPacket(Instant deadline)throws IOException{verify();if(incoming.isEmpty())throw new IOException("software response missing");return incoming.removeFirst();}
        @Override public void writePacket(byte[] packet,Instant deadline)throws IOException {
            verify();writes++;var request=NativeWire.decodeExecuteRequest(packet);
            if(request.step().equals(NativeFreshSnapshotPort.STEP)) {
                assertEquals(BigInteger.ZERO,request.expectedRevision().orElseThrow());
                String body=replace(new String(full,StandardCharsets.UTF_8),"\"read_request_id\":\"hotfix36-ram-full\"","\"read_request_id\":\""+request.requestId()+"\"");
                byte[] snapshot=NativeWire.packet(body.getBytes(StandardCharsets.UTF_8));
                var parsed=assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(snapshot));
                var cpp=assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(NativeWire.packet(full)));
                assertArrayEquals(cpp.state().value(),parsed.state().value(),"actual C++ state token is unchanged");
                var ack=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",true);
                ack.putObject("result").put("schema",NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id",request.requestId()).put("snapshot_id",parsed.snapshotId()).put("revision",parsed.revision());
                incoming.add(snapshot);incoming.add(NativeWire.packet(StrictJson.canonical(ack)));return;
            }
            assertEquals("pause-map",request.step());
            var claim=NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value())).get("full_snapshot_clock_control");
            assertTrue(BUILD.executableSha256().equalsIgnoreCase(claim.path("executable_sha256").textValue()),"outbound claim must match selected current profile");
            assertEquals(BUILD.coreFullAdapterId(),claim.path("adapter_id").textValue());
            String body=replace(new String(clockResult,StandardCharsets.UTF_8),"\"request_id\":\"hotfix36-clock\"","\"request_id\":\""+request.requestId()+"\"");
            if(foreign) {
                var mutated=NativeWire.object(NativeWire.parse(body.getBytes(StandardCharsets.UTF_8)));
                // This foreign submitted ACK is explicit software corruption, not the C++ DTO artifact.
                ((ObjectNode)mutated.get("result")).put("executable_sha256",ExactCk3Build.CK3_1210.executableSha256())
                        .put("adapter_id",ExactCk3Build.CK3_1210.coreFullAdapterId()).put("queue_status","submitted")
                        .put("effect_attempted",true).put("full_snapshot_before_verified",true);
                incoming.add(NativeWire.packet(StrictJson.canonical(mutated)));
            } else incoming.add(NativeWire.packet(body.getBytes(StandardCharsets.UTF_8)));
        }
        private static String replace(String value,String old,String replacement) {
            int at=value.indexOf(old);assertTrue(at>=0);assertEquals(at,value.lastIndexOf(old));return value.substring(0,at)+replacement+value.substring(at+old.length());
        }
        @Override public void close(){closed=true;}
    }
}
