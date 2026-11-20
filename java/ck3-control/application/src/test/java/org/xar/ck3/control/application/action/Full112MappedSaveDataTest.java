package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual published artifact hashes used as caller DATA tags; no file witness, Managed owner or physical SAVE is fabricated. */
final class Full112MappedSaveDataTest {
    private static final Instant UNTIL=Instant.parse("2030-01-02T03:04:05.123456789Z");
    private static ExactRef corrected() {return tag("corrected112-data.dll",12381696L,"2634e6408331426ab546f59c5efa62f3d6b257bc0f6a583cbcec2ed07f7009e6");}
    private static ExactRef tag(String name,long bytes,String sha) {return new ExactRef(Path.of(name).toAbsolutePath().toString(),bytes,sha);}

    @Test void exactCorrected112BuildsOnlyCurrentCanonicalSaveData()throws Exception {
        var bridge=corrected();assertTrue(FullSnapshotClockControl.isMappedSave112Bridge(bridge));
        var request=FullSnapshotClockControl.requestMappedSave112(bridge,"native:10",BigInteger.TEN,UNTIL);
        assertEquals("save-checkpoint",request.step());assertEquals("game.command.save-checkpoint",request.requiredCapability().orElseThrow());
        var fields=StrictJson.parse(request.additionalFields().bytes());assertEquals(1,fields.size());
        var claim=fields.path("full_snapshot_clock_control");assertEquals(8,claim.size());
        var profile=ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
        assertEquals(profile.version(),claim.path("game_version").textValue());
        assertEquals(profile.coreFullAdapterId(),claim.path("adapter_id").textValue());assertEquals(profile.coreFullBackend(),claim.path("backend").textValue());
        assertEquals("native:10",claim.path("snapshot_id").textValue());assertEquals(BigInteger.TEN,claim.path("native_revision").bigIntegerValue());
        assertEquals(UNTIL.toEpochMilli(),claim.path("deadline_unix_ms").longValue());
    }

    @Test void withdrawn803daAndChangedTagsCannotSelectCorrected112() {
        // Real withdrawn111 bytes/SHA retained only as a negative DATA example, never source qualification.
        var withdrawn=tag("withdrawn111-data.dll",13792256L,"803da0130362c58bf8ba98c9e8bd41c3046c7dba4b12a0fa2fbbb29c6073eaa0");
        assertFalse(FullSnapshotClockControl.isMappedSave112Bridge(withdrawn));
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.requestMappedSave112(withdrawn,"native:10",BigInteger.TEN,UNTIL));
        var wrongSize=tag("changed-size-data.dll",corrected().bytes()+1,corrected().sha256());
        assertFalse(FullSnapshotClockControl.isMappedSave112Bridge(wrongSize));
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.requestMappedSave112(corrected(),"native:11",BigInteger.TEN,UNTIL));
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.request(ExactCk3Build.CK3_121003_STEAM_26785313,
                "save-checkpoint","native:10",BigInteger.TEN,UNTIL));
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.request(ExactCk3Build.CK3_121003_STEAM_26785313_FULL111,
                "save-checkpoint","native:10",BigInteger.TEN,UNTIL));
    }

    @Test void previousMapped61_81_92SelectorsAndTheirTupleAreUnchanged()throws Exception {
        var legacy=new ExactRef[]{
            tag("legacy61-data.dll",13451776L,"4376f38077794ba100349da7a8cc26f45fcab33d0ad525da9ea1836ca26747d6"),
            tag("legacy81-data.dll",13752832L,"75dc138eecec0719f6b7648a4dca3fa83332138c08a61c07403378ba17b54fd9"),
            tag("legacy92-data.dll",13761536L,"d9cb12a0e634e517ce6f72d9698e4ea9ab72fc3df606e8fcf34d3fee58c6805f")};
        for(var bridge:legacy) {
            assertTrue(FullSnapshotClockControl.isMappedSave61Bridge(bridge));assertFalse(FullSnapshotClockControl.isMappedSave112Bridge(bridge));
            var request=FullSnapshotClockControl.requestMappedSave61(bridge,"native:10",BigInteger.TEN,UNTIL);
            assertEquals(ExactCk3Build.CK3_1210_STEAM_26757580.coreFullAdapterId(),StrictJson.parse(request.additionalFields().bytes())
                    .path("full_snapshot_clock_control").path("adapter_id").textValue());
        }
        assertFalse(FullSnapshotClockControl.isMappedSave61Bridge(corrected()));
    }
}
