package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.context.RootSavedLoadReadiness;
import static org.junit.jupiter.api.Assertions.*;

/** Small original-producer inputs only; no session, Root review or actual proof authority is fabricated. */
class ColdModAbsenceProofTest {
    @TempDir java.nio.file.Path directory;
    private static final String ROOT="D:/synthetic-cold-profile";
    private static ExactRef ref(String name,long bytes,String hash) { return new ExactRef(ROOT+"/"+name,bytes,hash.repeat(64)); }
    private static ObjectNode launch() {
        var value=StrictJson.object();value.put("pid",123);value.put("creation_filetime_decimal","18446744073709551615");
        value.put("machine_id","synthetic-machine");return value;
    }
    private static ObjectNode manifest() {
        var value=StrictJson.object();value.put("machine_id","synthetic-machine");value.put("profile_dir",ROOT);
        value.put("environment_sha256","e".repeat(64));var load=value.putObject("load_profile");
        load.putArray("enabled_mods");load.put("dlc_load_sha256","d".repeat(64));return value;
    }
    private static ObjectNode mods() { var value=StrictJson.object();value.putArray("enabled_mods");return value; }
    private static ObjectNode build(ObjectNode launch,ObjectNode manifest,ObjectNode mods,ExactRef snapshot,String log) {
        return ColdModAbsenceProof.build(launch,manifest,mods,ref("actual-launch.json",100,"a"),
                ref("xar-autoplayer-environment.json",200,"b"),ref("dlc_load.json",20,"d"),snapshot,log,
                "2026-10-23T05:00:00Z",ref("actual-independent-root-review.json",300,"c"));
    }
    @Test void producerKeepsSemanticDigestSeparateFromExactManifestAndFiletimeAsString() {
        var output=build(launch(),manifest(),mods(),ref("snapshot.log",40,"f"),ROOT+"/logs/debug.log");
        var roundtrip=StrictJson.parse(StrictJson.canonical(output));
        assertEquals("xar.verified-xar-mod-absence/v2",roundtrip.get("schema").textValue());
        assertEquals("18446744073709551615",roundtrip.get("game_creation_filetime_decimal").textValue());
        assertEquals("e".repeat(64),roundtrip.get("environment_sha256").textValue());
        assertEquals("b".repeat(64),roundtrip.get("environment_manifest").get("sha256").textValue());
        assertEquals("c".repeat(64),roundtrip.get("root_stage_review").get("sha256").textValue());
        assertTrue(roundtrip.get("enabled_mods").isEmpty());assertTrue(roundtrip.get("loaded_mods").isEmpty());
        assertNull(roundtrip.get("native_admitted"));assertNull(roundtrip.get("grants_warm_attachment"));
    }
    @Test void wrongMachineEnabledModAndDifferentExactDlcHashReallyReject() {
        var machine=manifest();machine.put("machine_id","another-machine");
        assertThrows(RuntimeException.class,()->build(launch(),machine,mods(),ref("snapshot.log",40,"f"),ROOT+"/logs/debug.log"));
        var enabled=mods();enabled.withArray("enabled_mods").add("mod/synthetic.mod");
        assertThrows(RuntimeException.class,()->build(launch(),manifest(),enabled,ref("snapshot.log",40,"f"),ROOT+"/logs/debug.log"));
        var hash=manifest();((ObjectNode)hash.get("load_profile")).put("dlc_load_sha256","a".repeat(64));
        assertThrows(RuntimeException.class,()->build(launch(),hash,mods(),ref("snapshot.log",40,"f"),ROOT+"/logs/debug.log"));
    }
    @Test void boolPidNumericFiletimeOverflowAndMissingFieldReallyReject() {
        var pid=launch();pid.put("pid",true);
        assertThrows(RuntimeException.class,()->build(pid,manifest(),mods(),ref("snapshot.log",40,"f"),ROOT+"/logs/debug.log"));
        var numeric=launch();numeric.put("creation_filetime_decimal",134000000000000001L);
        assertThrows(RuntimeException.class,()->build(numeric,manifest(),mods(),ref("snapshot.log",40,"f"),ROOT+"/logs/debug.log"));
        for(String bad:java.util.List.of("01","0","18446744073709551616")) {
            var value=launch();value.put("creation_filetime_decimal",bad);
            assertThrows(RuntimeException.class,()->build(value,manifest(),mods(),ref("snapshot.log",40,"f"),ROOT+"/logs/debug.log"));
        }
        var missing=manifest();missing.remove("load_profile");
        assertThrows(RuntimeException.class,()->build(launch(),missing,mods(),ref("snapshot.log",40,"f"),ROOT+"/logs/debug.log"));
    }
    @Test void OutsideProfileLogEmptyOrOversizeSnapshotCannotProduceProof() {
        assertThrows(RuntimeException.class,()->build(launch(),manifest(),mods(),ref("snapshot.log",40,"f"),"D:/other/logs/debug.log"));
        assertThrows(RuntimeException.class,()->build(launch(),manifest(),mods(),ref("snapshot.log",262145,"f"),ROOT+"/logs/debug.log"));
        assertThrows(RuntimeException.class,()->build(launch(),manifest(),mods(),ref("snapshot.log",0,"f"),ROOT+"/logs/debug.log"));
    }
    @Test void actualSmallLogCopiesRecordedCompleteLinesAndAllowsLaterAppendWithoutInventingReadyAuthority() throws Exception {
        var log=directory.resolve("synthetic-debug.log");java.nio.file.Files.writeString(log,"first\nsecond\npartial");
        var ready=recorded(log);java.nio.file.Files.writeString(log,"-completed-later\n",java.nio.file.StandardOpenOption.APPEND);
        var result=ColdModAbsenceProof.snapshot(ready,directory.resolve("snapshot.log"));
        assertEquals("first\nsecond\n",java.nio.file.Files.readString(java.nio.file.Path.of(result.path())));
        assertEquals(13,result.bytes());
    }
    @Test void actualChangedPrefixAndSameBytesReplacementReallyFailRecordedLogCopy() throws Exception {
        var log=directory.resolve("synthetic-debug.log");java.nio.file.Files.writeString(log,"first\nsecond\n");var ready=recorded(log);
        java.nio.file.Files.writeString(log,"other\nsecond\n");
        assertThrows(RuntimeException.class,()->ColdModAbsenceProof.snapshot(ready,directory.resolve("changed.log")));
        java.nio.file.Files.move(log,directory.resolve("retained-original.log"));java.nio.file.Files.writeString(log,"first\nsecond\n");
        assertThrows(RuntimeException.class,()->ColdModAbsenceProof.snapshot(ready,directory.resolve("replaced.log")));
    }
    private static RootSavedLoadReadiness.Ready recorded(java.nio.file.Path log) throws Exception {
        var now=java.time.Instant.now();return new RootSavedLoadReadiness.Ready(ControlBuild.FileRef.measure(log),SharedSourceFiles.nativeFile(log),
                now,now,new RootSavedLoadReadiness.Marker(1,"first"),new RootSavedLoadReadiness.Marker(2,"second"));
    }
}
