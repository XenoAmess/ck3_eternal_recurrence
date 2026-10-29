package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.TreeMap;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Synthetic retained-byte boundary cases. These tests cannot qualify a source, SAVE, cold restore or Game. */
final class RootM7HistoricalSourceTest {
    private static final Instant AT = Instant.parse("2026-10-23T19:00:00Z");
    private static final String MACHINE = "m7-historical-software-fixture";

    @Test void retainsOriginalEpochAndExecutableWithoutASecondCurrentEpoch() throws Exception {
        Fixture f = new Fixture(1);
        var decoded = f.decode();
        assertEquals(f.manifestRef.sha256(), decoded.epoch());
        assertEquals(f.executable, decoded.executable());
        assertEquals(f.manifestRef, decoded.manifest());
        assertEquals(new BigInteger("18446744073709551615"), f.guard.observed().game().creationFiletime().value());
    }

    @Test void completeOriginalManifestUsesItsActualLargeRoleRatherThanDefault64KiBJson() throws Exception {
        Fixture f = new Fixture(1_000);
        assertTrue(f.manifestBytes.length > StrictJson.INPUT_MAX_BYTES);
        assertEquals(f.manifestRef.sha256(), f.decode().epoch());
    }

    @Test void rejectsHistoricalV1WrongRoleSourceSessionAndUnknownFields() throws Exception {
        Fixture f = new Fixture(1);
        ObjectNode legacy = f.proof.deepCopy(); legacy.put("schema", "xar.java-root-native-source-proof/v1");
        assertThrows(IllegalArgumentException.class, () -> f.decode(legacy, f.manifestBytes));
        ObjectNode changed = f.proof.deepCopy(); changed.put("session_id", "other-original-session");
        ObjectNode wrongSession = changed;
        assertThrows(IllegalArgumentException.class, () -> f.decode(wrongSession, f.manifestBytes));
        changed = f.proof.deepCopy(); changed.put("machine_id", "other-machine");
        ObjectNode wrongMachine = changed;
        assertThrows(IllegalArgumentException.class, () -> f.decode(wrongMachine, f.manifestBytes));
        changed = f.proof.deepCopy(); changed.set("source", ref("another-native-source", "different").toJson());
        ObjectNode wrongSource = changed;
        assertThrows(IllegalArgumentException.class, () -> f.decode(wrongSource, f.manifestBytes));
        changed = f.proof.deepCopy(); changed.put("current_epoch_fallback", true);
        ObjectNode extra = changed;
        assertThrows(IllegalArgumentException.class, () -> f.decode(extra, f.manifestBytes));
    }

    @Test void rejectsChangedOriginalBytesOrEpochWithNoCurrentSourceFallback() throws Exception {
        Fixture f = new Fixture(1);
        byte[] changedBytes = f.manifestBytes.clone(); changedBytes[0] ^= 1;
        assertThrows(IllegalArgumentException.class, () -> f.decode(f.proof, changedBytes));
        ObjectNode changed = f.proof.deepCopy(); changed.put("owner_source_epoch", "0".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> f.decode(changed, f.manifestBytes));
        byte[] proof = encode(f.proof); ExactRef original = refBytes("source-proof.json", proof); proof[0] ^= 1;
        assertThrows(IllegalArgumentException.class, () -> RootM7HistoricalSource.decode(original, proof, f.guard, f.manifestBytes));
    }

    @Test void rejectsMissingDuplicateUnsortedAndNonIntegerManifestInputs() throws Exception {
        Fixture f = new Fixture(1);
        ObjectNode missing = f.manifest.deepCopy(); missing.withArray("inputs").remove(0);
        assertThrows(IllegalArgumentException.class, () -> f.decodeManifest(missing));
        ObjectNode duplicate = f.manifest.deepCopy(); var rows = duplicate.withArray("inputs"); rows.add(rows.get(0).deepCopy());
        assertThrows(IllegalArgumentException.class, () -> f.decodeManifest(duplicate));
        ObjectNode unsorted = f.manifest.deepCopy(); rows = unsorted.withArray("inputs");
        var first = rows.get(0); var second = rows.get(1); rows.set(0, second); rows.set(1, first);
        assertThrows(IllegalArgumentException.class, () -> f.decodeManifest(unsorted));
        ObjectNode booleanSize = f.manifest.deepCopy(); ((ObjectNode) booleanSize.withArray("inputs").get(0).get("source")).put("bytes", true);
        assertThrows(IllegalArgumentException.class, () -> f.decodeManifest(booleanSize));
        ObjectNode floatSize = f.manifest.deepCopy(); ((ObjectNode) floatSize.withArray("inputs").get(0).get("source")).put("bytes", 1.0);
        assertThrows(IllegalArgumentException.class, () -> f.decodeManifest(floatSize));
    }

    @Test void rejectsAChangedExecutableAndMissingOriginalEvidenceClosure() throws Exception {
        Fixture f = new Fixture(1);
        ObjectNode changed = f.manifest.deepCopy();
        for (var row : changed.withArray("inputs")) if (row.get("role").textValue().equals("game_executable"))
            ((ObjectNode) row).set("source", ref("ck3.exe", "other-executable").toJson());
        assertThrows(IllegalArgumentException.class, () -> f.decodeManifest(changed));
        ObjectNode omitted = f.proof.deepCopy(); omitted.putArray("complete_evidence_closure").add(ref("unrelated-file", "unrelated").toJson());
        assertThrows(IllegalArgumentException.class, () -> f.decode(omitted, f.manifestBytes));
    }

    private static final class Fixture {
        private final ExactRef executable = ref("ck3.exe", "synthetic executable bytes");
        private final ExactRef nativeSource = ref("native-source.cpp", "synthetic native source");
        private final GuardEvidence guard;
        private final ObjectNode manifest = StrictJson.object();
        private final ObjectNode proof = StrictJson.object();
        private final byte[] manifestBytes;
        private final ExactRef manifestRef;

        private Fixture(int runtimeCount) throws Exception {
            var identity = new ObservationIdentity(MACHINE,
                    new GameGeneration(321, new PythonOnlyUInt64(new BigInteger("18446744073709551615"))),
                    new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(1), BigInteger.valueOf(9), BigInteger.valueOf(53_169_072)),
                            "synthetic-native-9", BigInteger.valueOf(12), "synthetic-episode"), 1);
            var source = new G2Source(MACHINE, AT.toString(), "synthetic/.4", nativeSource);
            guard = new GuardEvidence(identity, source, "original-session", BigInteger.ONE, new OperationKey("save-checkpoint"),
                    ref("native-packet", "synthetic native packet"), ref("hello", "synthetic hello"), "synthetic-authority", AT, AT.plusSeconds(60));
            manifest.put("schema", "xar.java-root-source-epoch/v1"); manifest.put("machine_id", MACHINE);
            TreeMap<String, ObjectNode> ordered = new TreeMap<>();
            add(ordered, "bridge_dll", ref("xar_ck3_bridge.dll", "synthetic bridge"));
            add(ordered, "game_executable", executable); add(ordered, "injector", ref("injector.exe", "synthetic injector"));
            for (int i = 0; i < runtimeCount; i++) add(ordered, "java_runtime", ref("runtime/part-" + i + ".jar", "synthetic java " + i));
            add(ordered, "launcher_settings", ref("launcher-settings.json", "synthetic settings")); add(ordered, "native_source", nativeSource);
            var inputs = manifest.putArray("inputs"); ordered.values().forEach(inputs::add);
            manifestBytes = encode(manifest); manifestRef = refBytes("original-epoch.json", manifestBytes);
            proof.put("schema", "xar.java-root-native-source-proof/v2"); proof.put("machine_id", MACHINE); proof.put("session_id", "original-session");
            proof.put("observed_at_utc", AT.toString()); proof.put("mode", "HTTP"); proof.set("host_configuration", ref("host.json", "synthetic host").toJson());
            proof.set("source", nativeSource.toJson()); proof.put("owner_source_epoch", manifestRef.sha256());
            proof.set("source_epoch_manifest", manifestRef.toJson()); proof.set("game_executable", executable.toJson());
            proof.putArray("complete_evidence_closure").add(executable.toJson()).add(nativeSource.toJson());
        }
        private RootM7HistoricalSource.Decoded decode() throws Exception { return decode(proof, manifestBytes); }
        private RootM7HistoricalSource.Decoded decode(ObjectNode originalProof, byte[] originalManifest) throws Exception {
            byte[] bytes = encode(originalProof);
            return RootM7HistoricalSource.decode(refBytes("source-proof.json", bytes), bytes, guard, originalManifest);
        }
        private RootM7HistoricalSource.Decoded decodeManifest(ObjectNode originalManifest) throws Exception {
            byte[] bytes = encode(originalManifest); ExactRef manifest = refBytes("original-epoch.json", bytes);
            ObjectNode alteredProof = proof.deepCopy(); alteredProof.put("owner_source_epoch", manifest.sha256()); alteredProof.set("source_epoch_manifest", manifest.toJson());
            return decode(alteredProof, bytes);
        }
    }
    private static void add(TreeMap<String, ObjectNode> rows, String role, ExactRef source) {
        ObjectNode row = StrictJson.object(); row.put("role", role); row.set("source", source.toJson()); rows.put(role + ":" + source.path(), row);
    }
    private static byte[] encode(ObjectNode value) throws Exception { return ControlBuild.strictMapper().writeValueAsBytes(value); }
    private static ExactRef ref(String name, String text) { return refBytes(name, text.getBytes(StandardCharsets.UTF_8)); }
    private static ExactRef refBytes(String name, byte[] bytes) {
        return new ExactRef(Path.of("synthetic-historical-source", name).toAbsolutePath().normalize().toString().replace('\\', '/').toLowerCase(java.util.Locale.ROOT),
                bytes.length, ActionCodec.sha256(bytes));
    }
}
