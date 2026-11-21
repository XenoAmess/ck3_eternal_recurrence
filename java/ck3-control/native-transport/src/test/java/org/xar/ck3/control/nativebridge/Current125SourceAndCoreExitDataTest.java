package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayDeque;
import org.xar.ck3.control.application.action.FullSnapshotClockControl;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Request DATA only. No owner, transport, Native call, process or exit is created. */
final class Current125SourceAndCoreExitDataTest {
    private static final ExactCk3Build FULL=ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final ExactCk3Build CORE=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final CoreFrame.Prefix LIVE=new CoreFrame.Prefix(
            53179344,3,true,0,true,true,0x81000002,true);

    @Test void currentFullExitKeepsItsFullProducerIdentityAndCoreValues() {
        var request=CoreApplicationExit.request(new CoreFrame.Partial(FULL,LIVE));
        assertEquals("normal-exit-application-v1",request.step());
        assertEquals("game.command.normal-exit-application-v1",request.requiredCapability().orElseThrow());
        var fields=StrictJson.parse(request.additionalFields().bytes(),1<<20);
        var claim=fields.path("core_application_exit");
        assertEquals(CoreApplicationExit.SCHEMA,claim.path("schema").textValue());
        assertEquals(FULL.version(),claim.path("game_version").textValue());
        assertEquals(FULL.executableSha256(),claim.path("executable_sha256").textValue());
        assertEquals(FULL.coreFrameAdapterId(),claim.path("adapter_id").textValue());
        assertEquals("ck3-1.21.0.3-native-headless-main-thread",claim.path("backend").textValue());
        assertEquals(LIVE.playedCharacterId(),claim.path("played_character_id").intValue());
        assertEquals(LIVE.dateRaw(),claim.path("date_raw").intValue());
        assertTrue(claim.path("paused").booleanValue());
        assertFalse(fields.has("full_snapshot_clock_control"));
    }

    @Test void existingCoreOnlyAndLegacyExitIdentitiesRemainSeparate() {
        for(var build:List.of(CORE,ExactCk3Build.CK3_1210,ExactCk3Build.CK3_1210_STEAM_26757580)) {
            var request=CoreApplicationExit.request(new CoreFrame.Partial(build,LIVE));
            var claim=StrictJson.parse(request.additionalFields().bytes(),1<<20).path("core_application_exit");
            assertEquals(build.version(),claim.path("game_version").textValue());
            assertEquals(build.coreFrameAdapterId(),claim.path("adapter_id").textValue());
            assertEquals(build==CORE?"ck3-1.21.0.3-native-headless-main-thread":CoreClockControl.BACKEND,
                    claim.path("backend").textValue());
        }
    }

    @Test void invalidCurrentCoreIsRejectedDuringRequestPreparation() {
        for(var prefix:List.of(
                new CoreFrame.Prefix(53179344,3,false,0,true,true,31254,true),
                new CoreFrame.Prefix(53179344,3,true,0,false,true,31254,true),
                new CoreFrame.Prefix(53179344,3,true,-1,true,true,31254,true),
                new CoreFrame.Prefix(53179344,3,true,0,true,false,-1,false),
                new CoreFrame.Prefix(53179344,3,true,0,true,true,31254,false))) {
            assertThrows(IllegalArgumentException.class,
                    ()->CoreApplicationExit.request(new CoreFrame.Partial(FULL,prefix)));
        }
    }

    @Test void dedicatedExitDoesNotWidenLegacyCoreClockSelection() {
        assertTrue(ExactCk3Build.florinCoreFullBuild(FULL.version(),FULL.executableSha256()).isEmpty());
        assertDoesNotThrow(()->CoreApplicationExit.request(new CoreFrame.Partial(FULL,LIVE)));
        for(var step:List.of(CoreClockControl.Step.PAUSE_MAP,CoreClockControl.Step.SET_SPEED_4,
                CoreClockControl.Step.SAVE_CHECKPOINT))
            assertThrows(IllegalArgumentException.class,
                    ()->CoreClockControl.request(step,new CoreFrame.Partial(FULL,LIVE)));
    }

    private static final ExactRef SOURCE125=new ExactRef("software-no-dll-read125",12389376L,
            "863b4893611d1101e4f5e7f82b43f4fab2c7259bd0db6c0065a59a9a016c12f7");
    private static final ExactRef SOURCE112=new ExactRef("software-no-dll-read112",12381696L,
            "2634e6408331426ab546f59c5efa62f3d6b257bc0f6a583cbcec2ed07f7009e6");

    @Test void corrected125And112AreExactSourceDataWithoutAcceptingOtherArtifacts() {
        assertTrue(FullSnapshotClockControl.isMappedSave112Bridge(SOURCE125));
        assertTrue(FullSnapshotClockControl.isMappedSave112Bridge(SOURCE112));
        for(var bad:List.of(
                new ExactRef(SOURCE125.path(),12389375L,SOURCE125.sha256()),
                new ExactRef("wrong-sha",SOURCE125.bytes(),"0".repeat(64)),
                new ExactRef("independent114",12382720L,"42cecc8a69bc5f6142e10b8d5bb044fab9a63d26bcfd3a01a6de25501f4a604a"),
                new ExactRef("withdrawn111",13792256L,"803da0130362c58bf8ba98c9e8bd41c3046c7dba4b12a0fa2fbbb29c6073eaa0")))
            assertFalse(FullSnapshotClockControl.isMappedSave112Bridge(bad));
    }

    @Test void mapped125SaveKeepsCurrentTupleOriginalRevisionAndDeadline() {
        var revision=new BigInteger("9007199254740993");
        var deadline=Instant.parse("2030-01-02T03:04:05.123456789Z");
        var request=FullSnapshotClockControl.requestMappedSave112(
                SOURCE125,"native:"+revision,revision,deadline);
        var fields=StrictJson.parse(request.additionalFields().bytes(),1<<20).path("full_snapshot_clock_control");
        assertEquals("save-checkpoint",request.step());
        assertEquals(FULL.version(),fields.path("game_version").textValue());
        assertEquals(FULL.coreFullAdapterId(),fields.path("adapter_id").textValue());
        assertEquals(FULL.coreFullBackend(),fields.path("backend").textValue());
        assertEquals(revision,fields.path("native_revision").bigIntegerValue());
        assertEquals(deadline.toEpochMilli(),fields.path("deadline_unix_ms").longValue());
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.request(
                FULL,"save-checkpoint","native:1",BigInteger.ONE,deadline));
    }

    @Test void matching125DataAndHelloCannotReplaceActualManagedCustody()throws Exception {
        var source=new Replay();
        var game=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        String slash=Character.toString(92);
        var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"source125-software",
                "source125-software",game,"source125-software-session","source125-software",
                FULL.executableSha256(),FULL.coreFrameAdapterId());
        try(var actual=new NativeGameTransport(source,config,16,16,List.of(),Clock.systemUTC())) {
            assertThrows(NullPointerException.class,()->actual.bindFull112Source(null));
            var read=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,
                    actual.readFreshFullState(Instant.now().plusSeconds(30)));
            var rejected=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,read.dispatch());
            assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,rejected.proof().stage());
            assertEquals(0,rejected.proof().requestBytesWritten());
            assertTrue(read.reason().contains("actual Managed source is not bound"),read::reason);
            assertEquals(0,source.writes);
            assertTrue(actual.latestAcceptedSnapshotRevision().isEmpty());
        }
    }

    @Test void admissionFixDoesNotQualifyDifferentSpeedOrBorrowIndependent114Save()throws Exception {
        var before=new RawJson(StrictJson.canonical(StrictJson.object().put("speed",3)));
        assertDoesNotThrow(()->NativeGameTransport.requireCurrent112SpeedData(FULL,"set-speed-3",before));
        assertThrows(IOException.class,()->NativeGameTransport.requireCurrent112SpeedData(FULL,"set-speed-4",before));
        var independent=new ExactRef("independent114",12382720L,
                "42cecc8a69bc5f6142e10b8d5bb044fab9a63d26bcfd3a01a6de25501f4a604a");
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.requestMappedSave112(
                independent,"native:1",BigInteger.ONE,Instant.parse("2030-01-02T03:04:05Z")));
    }

    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();int writes;boolean closed;
        Replay()throws IOException {
            var row=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42)
                    .put("connection_generation",1).put("bridge_version","source125-software")
                    .put("expected_ck3_version",FULL.version()).put("expected_ck3_sha256",FULL.executableSha256())
                    .put("game_adapter_id",FULL.coreFullAdapterId()).put("game_adapter_status","ready")
                    .put("ck3_build_match",true);
            row.putArray("capabilities").add(CoreFrame.CAPABILITY).add(NativeFreshSnapshotPort.CAPABILITY)
                    .add("game.state.snapshot").add("game.command.save-checkpoint")
                    .add(CoreApplicationExit.CAPABILITY);
            packets.add(NativeWire.packet(StrictJson.canonical(row)));
        }
        @Override public void verify()throws IOException {if(closed)throw new IOException("software endpoint closed");}
        @Override public void awaitConnection(Instant until)throws IOException {verify();}
        @Override public byte[] readPacket(Instant until)throws IOException {
            verify();if(packets.isEmpty())throw new IOException("software packet absent");return packets.removeFirst();
        }
        @Override public void writePacket(byte[] packet,Instant until)throws IOException {
            writes++;throw new IOException("unbound125 DATA must not write a Full query or command");
        }
        @Override public void close(){closed=true;}
    }
}
