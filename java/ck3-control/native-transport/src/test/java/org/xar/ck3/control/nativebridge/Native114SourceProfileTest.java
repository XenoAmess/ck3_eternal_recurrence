package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.FullSnapshotClockControl;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** DATA and an in-memory endpoint only. No actual Managed owner, artifact read,
 * CK3, count observation, speed effect or mapped SAVE is created by these tests. */
final class Native114SourceProfileTest {
    private static final ExactCk3Build FULL=ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final String SHA114="42cecc8a69bc5f6142e10b8d5bb044fab9a63d26bcfd3a01a6de25501f4a604a";
    private static final ExactRef SOURCE114=new ExactRef("software-no-dll-read114",12382720L,SHA114);
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));

    @Test void independentArtifactDoesNotInterchangeWith112OrWithdrawn111() {
        assertTrue(Native114SourceProfile.matchesBridge(SOURCE114));
        assertFalse(Native114SourceProfile.matchesBridge(new ExactRef(SOURCE114.path(),12382719L,SHA114)));
        assertFalse(Native114SourceProfile.matchesBridge(new ExactRef("software112",12381696L,
                "2634e6408331426ab546f59c5efa62f3d6b257bc0f6a583cbcec2ed07f7009e6")));
        assertFalse(Native114SourceProfile.matchesBridge(new ExactRef("withdrawn111",13792256L,
                "803da0130362c58bf8ba98c9e8bd41c3046c7dba4b12a0fa2fbbb29c6073eaa0")));
    }

    @Test void matching114DataAndHelloCannotSelectAnUnboundDefaultSource()throws Exception {
        assertTrue(Native114SourceProfile.matchesBridge(SOURCE114));
        var until=Instant.now().plusSeconds(30);
        var source=new Replay();
        String slash=Character.toString(92);
        var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"source114-software","source114-software",GAME,
                "source114-software-session","source114-software",FULL.executableSha256(),FULL.coreFrameAdapterId());
        try(var actual=new NativeGameTransport(source,config,16,16,List.of(),Clock.systemUTC())) {
            assertThrows(NullPointerException.class,()->actual.bindFull114Source(null));
            var read=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,actual.readFreshFullState(until));
            var rejected=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,read.dispatch());
            assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,rejected.proof().stage());
            assertEquals(0,rejected.proof().requestBytesWritten());
            assertTrue(read.reason().contains("corrected112 independent actual Managed source is not bound or current"),read::reason);
            assertTrue(actual.latestAcceptedSnapshotRevision().isEmpty());
            assertEquals(0,source.writes);
        }
    }

    @Test void countBinderEvidenceDoesNotEnableDifferentSpeedData()throws Exception {
        assertTrue(Native114SourceProfile.matchesBridge(SOURCE114));
        var before=new RawJson(StrictJson.canonical(StrictJson.object().put("speed",3)));
        assertDoesNotThrow(()->NativeGameTransport.requireCurrent112SpeedData(FULL,"set-speed-3",before));
        var rejected=assertThrows(IOException.class,()->NativeGameTransport.requireCurrent112SpeedData(FULL,"set-speed-4",before));
        assertTrue(rejected.getMessage().contains("speed change is unqualified"));
    }

    @Test void explicit114SelectionCannotBorrowMapped112Save() {
        assertTrue(Native114SourceProfile.matchesBridge(SOURCE114));
        assertFalse(FullSnapshotClockControl.isMappedSave112Bridge(SOURCE114));
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.requestMappedSave112(
                SOURCE114,"native:1",BigInteger.ONE,Instant.parse("2030-01-02T03:04:05.123456789Z")));
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.request(
                FULL,"save-checkpoint","native:1",BigInteger.ONE,Instant.parse("2030-01-02T03:04:05.123456789Z")));
    }

    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();int writes;boolean closed;
        Replay()throws IOException {
            var row=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",1)
                    .put("bridge_version","source114-software").put("expected_ck3_version",FULL.version()).put("expected_ck3_sha256",FULL.executableSha256())
                    .put("game_adapter_id",FULL.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            row.putArray("capabilities").add(CoreFrame.CAPABILITY).add(NativeFreshSnapshotPort.CAPABILITY).add("game.state.snapshot")
                    .add("game.command.save-checkpoint").add("game.command.set-speed-4");
            packets.add(NativeWire.packet(StrictJson.canonical(row)));
        }
        @Override public void verify()throws IOException {if(closed)throw new IOException("software endpoint closed");}
        @Override public void awaitConnection(Instant until)throws IOException {verify();}
        @Override public byte[] readPacket(Instant until)throws IOException {
            verify();if(packets.isEmpty())throw new IOException("software packet absent");return packets.removeFirst();
        }
        @Override public void writePacket(byte[] packet,Instant until)throws IOException {
            writes++;throw new IOException("unbound114 DATA must not write a Full query or command");
        }
        @Override public void close(){closed=true;}
    }
}
