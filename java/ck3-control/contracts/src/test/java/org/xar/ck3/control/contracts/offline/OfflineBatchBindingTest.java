package org.xar.ck3.control.contracts.offline;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class OfflineBatchBindingTest {
    private static final String OBSERVATION = "{\"machine_id\":\"source-machine\",\"game\":{\"pid\":999,\"creation_filetime\":\"134000000000000001\"},\"observation_version\":1,"
            + "\"frame\":{\"played_character_id\":\"9007199254740993\",\"native_revision\":\"18446744073709551614\",\"date_raw\":\"0\",\"snapshot_id\":\"original\",\"revision\":\"9007199254740995\",\"episode_run_id\":\"episode\"}}";
    private static ObjectNode manifest() {
        var value = StrictJson.object().put("schema", OfflineBatchBinding.MANIFEST_V2).put("session_id", "actual-session");
        value.set("scan_observation", StrictJson.parse(OBSERVATION.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        var source = value.putObject("scan_source").put("machine_id", "source-machine").put("observed_at_utc", "2026-10-24T00:00:00Z").put("exact_build", "1.20.0.4");
        source.putObject("source_ref").put("path", "source-original").put("bytes", 12).put("sha256", "a".repeat(64));
        value.putObject("index_ref").put("path", "scan-original").put("bytes", 20).put("sha256", "b".repeat(64)); value.putArray("new_incidents"); return value;
    }
    @Test void exactOriginalObservationAndDecimalTextFiletimeRoundTripWithoutAControlSequence() {
        var original = manifest(); var binding = assertInstanceOf(OfflineBatchBinding.ObservedScan.class, OfflineBatchBinding.manifest(original));
        assertEquals("9007199254740993", binding.observation().frame().playedCharacterId().decimal());
        assertEquals(new BigInteger("134000000000000001"), binding.observation().game().creationFiletime().value());
        assertArrayEquals(StrictJson.canonical(original.get("scan_observation")), StrictJson.canonical(binding.observation().toJson()));
        var report = StrictJson.object().put("machine_id", "source-machine"); report.set("manifest", binding.indexRef().toJson());
        OfflineBatchBinding.addReportBinding(report, binding); OfflineBatchBinding.requireReport(report, binding, binding.indexRef());
        assertFalse(report.has("completed_control_sequence"));
        ObjectNode changed = report.deepCopy(); changed.put("completed_control_sequence", 1);
        assertThrows(IllegalArgumentException.class, () -> OfflineBatchBinding.requireReport(changed, binding, binding.indexRef()));
    }
    @Test void missingNullFloatBooleanNumericIdentityAndUnknownFieldsAreRejected() {
        for (String field : java.util.List.of("scan_observation", "scan_source", "index_ref", "session_id")) {
            ObjectNode missing = manifest(); missing.remove(field); assertThrows(IllegalArgumentException.class, () -> OfflineBatchBinding.manifest(missing));
            ObjectNode nil = manifest(); nil.putNull(field); assertThrows(IllegalArgumentException.class, () -> OfflineBatchBinding.manifest(nil));
        }
        ObjectNode wrong = manifest(); ((ObjectNode)wrong.path("scan_observation")).put("observation_version", true);
        assertThrows(IllegalArgumentException.class, () -> OfflineBatchBinding.manifest(wrong));
        ObjectNode number = manifest(); ((ObjectNode)number.path("scan_observation").path("frame")).put("played_character_id", 101);
        assertThrows(IllegalArgumentException.class, () -> OfflineBatchBinding.manifest(number));
        ObjectNode numeric = manifest(); ((ObjectNode)numeric.path("scan_observation").path("game")).put("creation_filetime", new BigInteger("134000000000000001"));
        assertThrows(IllegalArgumentException.class, () -> OfflineBatchBinding.manifest(numeric));
        ObjectNode floating = manifest(); ((ObjectNode)floating.path("scan_observation").path("game")).put("creation_filetime", 1.0);
        assertThrows(IllegalArgumentException.class, () -> OfflineBatchBinding.manifest(floating));
        ObjectNode unknown = manifest(); unknown.put("ledger_sequence", 1); assertThrows(IllegalArgumentException.class, () -> OfflineBatchBinding.manifest(unknown));
        ObjectNode machine = manifest(); ((ObjectNode)machine.path("scan_source")).put("machine_id", "different-machine");
        assertThrows(IllegalArgumentException.class, () -> OfflineBatchBinding.manifest(machine));
    }
    @Test void historicalActualCompletedSequenceIsRetainedAndNeverSubstitutedWithAVersion() {
        var legacy = StrictJson.object().put("completed_control_sequence", 37); legacy.putArray("new_incidents");
        var binding = assertInstanceOf(OfflineBatchBinding.LegacyCompleted.class, OfflineBatchBinding.manifest(legacy));
        assertEquals(BigInteger.valueOf(37), binding.completedControlSequence());
        ObjectNode booleanValue = legacy.deepCopy(); booleanValue.put("completed_control_sequence", true);
        assertThrows(IllegalArgumentException.class, () -> OfflineBatchBinding.manifest(booleanValue));
        ObjectNode version = StrictJson.object().put("observation_version", 37); version.putArray("new_incidents");
        assertThrows(IllegalArgumentException.class, () -> OfflineBatchBinding.manifest(version));
        ObjectNode alias = legacy.deepCopy(); alias.set("scan_observation", manifest().get("scan_observation"));
        assertThrows(IllegalArgumentException.class, () -> OfflineBatchBinding.manifest(alias));
        ObjectNode future = manifest(); future.put("schema", "xar.offline-episode-incident-batch/v4");
        assertThrows(IllegalArgumentException.class, () -> OfflineBatchBinding.manifest(future));
    }
}
