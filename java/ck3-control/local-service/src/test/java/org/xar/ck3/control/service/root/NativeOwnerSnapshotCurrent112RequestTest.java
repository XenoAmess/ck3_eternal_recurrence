package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Request DATA only. No owner/attachment, Native query, listener, SAVE or effect. */
final class NativeOwnerSnapshotCurrent112RequestTest {
    private static final ExactCk3Build CURRENT=ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final Instant DEADLINE=Instant.parse("2030-01-02T03:04:05.123456789Z");
    private static final BigInteger REVISION=new BigInteger("9007199254740993");
    private static final ExactRef MAPPED112=new ExactRef("software-no-dll-read112",12381696L,
            "2634e6408331426ab546f59c5efa62f3d6b257bc0f6a583cbcec2ed07f7009e6");

    @Test void currentClockUsesOriginalTupleRevisionAndDeadline()throws Exception {
        var request=NativeOwnerSnapshotMain268.preparedFullClockRequest("resume-map",state(CURRENT),
                "native:"+REVISION,REVISION,DEADLINE,Optional.empty());
        var fields=StrictJson.parse(request.additionalFields().bytes(),1<<20).path("full_snapshot_clock_control");
        assertEquals("1.21.0.3",fields.path("game_version").textValue());
        assertEquals(CURRENT.coreFullAdapterId(),fields.path("adapter_id").textValue());
        assertEquals(CURRENT.coreFullBackend(),fields.path("backend").textValue());
        assertEquals("native:"+REVISION,fields.path("snapshot_id").textValue());
        assertEquals(REVISION,fields.path("native_revision").bigIntegerValue());
        assertEquals(DEADLINE.toEpochMilli(),fields.path("deadline_unix_ms").longValue());
        assertEquals("resume-map",request.step());
    }

    @Test void currentMappedSaveRequiresItsBoundExact112Data()throws Exception {
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.preparedFullClockRequest(
                "save-checkpoint",state(CURRENT),"native:1",BigInteger.ONE,DEADLINE,Optional.empty()));
        var request=NativeOwnerSnapshotMain268.preparedFullClockRequest(
                "save-checkpoint",state(CURRENT),"native:1",BigInteger.ONE,DEADLINE,Optional.of(MAPPED112));
        var fields=StrictJson.parse(request.additionalFields().bytes(),1<<20).path("full_snapshot_clock_control");
        assertEquals("save-checkpoint",request.step());
        assertEquals(CURRENT.coreFullAdapterId(),fields.path("adapter_id").textValue());
        assertEquals(DEADLINE.toEpochMilli(),fields.path("deadline_unix_ms").longValue());
    }

    @Test void independent114AndWithdrawn111CannotBorrowCurrentSave() {
        for(var source:List.of(
                new ExactRef("software114",12382720L,"42cecc8a69bc5f6142e10b8d5bb044fab9a63d26bcfd3a01a6de25501f4a604a"),
                new ExactRef("withdrawn111",13792256L,"803da0130362c58bf8ba98c9e8bd41c3046c7dba4b12a0fa2fbbb29c6073eaa0")))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.preparedFullClockRequest(
                    "save-checkpoint",state(CURRENT),"native:1",BigInteger.ONE,DEADLINE,Optional.of(source)));
    }

    @Test void legacyClockRetainsItsExactBuildWithoutCurrentSourceBorrowing()throws Exception {
        for(var build:List.of(ExactCk3Build.CK3_1210,ExactCk3Build.CK3_1210_STEAM_26757580)) {
            var request=NativeOwnerSnapshotMain268.preparedFullClockRequest(
                    "pause-map",state(build),"native:1",BigInteger.ONE,DEADLINE,Optional.empty());
            var fields=StrictJson.parse(request.additionalFields().bytes(),1<<20).path("full_snapshot_clock_control");
            assertEquals(build.coreFullAdapterId(),fields.path("adapter_id").textValue());
            assertEquals(build.executableSha256().toUpperCase(java.util.Locale.ROOT),fields.path("executable_sha256").textValue());
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.preparedFullClockRequest(
                    "pause-map",state(build),"native:1",BigInteger.ONE,DEADLINE,Optional.of(MAPPED112)));
        }
    }

    @Test void partialAndMixedFullIdentityCannotPrepareAClockRequest() {
        var original=object(CURRENT);
        var invalidStates=List.of(
                original.deepCopy().put("schema","ck3_1210_core_frame_v1"),
                original.deepCopy().put("adapter_id",ExactCk3Build.CK3_121003_STEAM_26785313.coreFrameAdapterId()),
                original.deepCopy().put("backend","ck3-1.21.0-native-headless-main-thread"),
                original.deepCopy().put("game_version","1.21.0"));
        for(int index=0;index<invalidStates.size();index++) {
            var invalid=invalidStates.get(index);
            Class<? extends Exception> expected=(index==0||index==2)?IllegalArgumentException.class:IOException.class;
            assertThrows(expected,()->NativeOwnerSnapshotMain268.preparedFullClockRequest(
                    "pause-map",new RawJson(StrictJson.canonical(invalid)),"native:1",BigInteger.ONE,DEADLINE,Optional.empty()));
        }
    }

    private static RawJson state(ExactCk3Build build) {return new RawJson(StrictJson.canonical(object(build)));}
    private static com.fasterxml.jackson.databind.node.ObjectNode object(ExactCk3Build build) {
        return StrictJson.object().put("schema","ck3_1210_full_state_v1").put("game_version",build.version())
                .put("executable_sha256",build.executableSha256()).put("adapter_id",build.coreFullAdapterId())
                .put("backend",build.coreFullBackend());
    }
}
