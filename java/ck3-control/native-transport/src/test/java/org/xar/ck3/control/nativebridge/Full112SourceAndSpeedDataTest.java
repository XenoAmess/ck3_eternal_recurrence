package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** NoGame software endpoint and pure speed DATA. There is no fake Managed owner, Full receipt or action-ticket permission. */
final class Full112SourceAndSpeedDataTest {
    private static final ExactCk3Build FULL=ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));

    @Test void exactHelloWithoutAnActualManagedBindingCannotReadFullOrBindSave()throws Exception {
        try(var fixture=new Fixture(FULL)) {
            assertThrows(NullPointerException.class,()->fixture.actual.bindFull112Source(null));
            assertThrows(NullPointerException.class,()->fixture.actual.bindMappedSave112(null));
            var result=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,fixture.actual.readFreshFullState(fixture.until));
            zero(result.dispatch());assertTrue(result.reason().contains("not bound"));assertEquals(0,fixture.source.writes);
            assertTrue(fixture.actual.latestAcceptedSnapshotRevision().isEmpty());
        }
    }

    @Test void sameExecutableCoreOnlyAdapterRemainsPartialWithoutFullAuthority()throws Exception {
        try(var fixture=new Fixture(ExactCk3Build.CK3_121003_STEAM_26785313)) {
            var result=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,fixture.actual.readFreshFullState(fixture.until));
            zero(result.dispatch());assertEquals(0,fixture.source.writes);
            assertInstanceOf(NativeGameTransport.FullClockReadUnavailable.class,fixture.actual.readFullClockFrameReceived(fixture.until));
            assertEquals(0,fixture.source.writes);
        }
    }

    @Test void onlySameSpeedDataIsSupportedWithoutClaimingAnEffect()throws Exception {
        var state=new RawJson(StrictJson.canonical(StrictJson.object().put("speed",3)));
        assertDoesNotThrow(()->NativeGameTransport.requireCurrent112SpeedData(FULL,"set-speed-3",state));
        var rejected=assertThrows(IOException.class,()->NativeGameTransport.requireCurrent112SpeedData(FULL,"set-speed-4",state));
        assertTrue(rejected.getMessage().contains("speed change is unqualified"));
        // This does not submit or consume any ticket. The actual caller must first verify its original fresh/current Full proof.
        assertDoesNotThrow(()->NativeGameTransport.requireCurrent112SpeedData(ExactCk3Build.CK3_1210,"set-speed-4",state));
    }

    @Test void currentSpeedRequiresAnExactFinitePublicInteger()throws Exception {
        for(String raw:new String[]{"{\"speed\":true}","{\"speed\":3.0}","{\"speed\":0}","{\"speed\":6}","{}"})
            assertThrows(IOException.class,()->NativeGameTransport.requireCurrent112SpeedData(FULL,"set-speed-3",new RawJson(raw.getBytes(java.nio.charset.StandardCharsets.UTF_8))));
    }

    private static void zero(NativeActionPort.DispatchOutcome outcome) {
        var rejected=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,outcome);
        assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,rejected.proof().stage());assertEquals(0,rejected.proof().requestBytesWritten());
    }
    private static final class Fixture implements AutoCloseable {
        final Instant until=Instant.now().plusSeconds(120);final Replay source;final NativeGameTransport actual;
        Fixture(ExactCk3Build profile)throws Exception {
            source=new Replay(profile);String slash=Character.toString(92);
            var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"full112-software","full112-software",GAME,
                    "full112-software-session","full112-software",profile.executableSha256(),profile.coreFrameAdapterId());
            actual=new NativeGameTransport(source,config,16,16,List.of(),Clock.systemUTC());
        }
        @Override public void close()throws IOException{actual.close();}
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();int writes;boolean closed;
        Replay(ExactCk3Build profile)throws IOException {
            var row=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",1)
                    .put("bridge_version","full112-software").put("expected_ck3_version",profile.version()).put("expected_ck3_sha256",profile.executableSha256())
                    .put("game_adapter_id",profile.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            row.putArray("capabilities").add(CoreFrame.CAPABILITY).add(NativeFreshSnapshotPort.CAPABILITY).add("game.state.snapshot").add("game.command.save-checkpoint");
            packets.add(NativeWire.packet(StrictJson.canonical(row)));
        }
        @Override public void verify()throws IOException{if(closed)throw new IOException("software endpoint closed");}
        @Override public void awaitConnection(Instant until)throws IOException{verify();}
        @Override public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("software packet absent");return packets.removeFirst();}
        @Override public void writePacket(byte[] packet,Instant until)throws IOException{writes++;throw new IOException("unbound source must not write a Full query");}
        @Override public void close(){closed=true;}
    }
}
