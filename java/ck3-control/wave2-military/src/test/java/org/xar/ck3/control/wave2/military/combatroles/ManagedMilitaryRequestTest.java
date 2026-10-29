package org.xar.ck3.control.wave2.military.combatroles;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

final class ManagedMilitaryRequestTest {
    @TempDir Path directory;
    private ObjectNode ref(Path path) {
        return StrictJson.object().put("path",path.toAbsolutePath().normalize().toString())
                .put("bytes",1).put("sha256","0".repeat(64));
    }
    @Test void sourceReadyAndHoldCannotProduceAnExecutableSharedRequest() {
        ObjectNode profile = StrictJson.object().put("schema","xar.military-managed-request-profile/v1")
                .put("status","SOURCE_READY_UNCOMPILED").put("machine_id","explicit-test-machine")
                .put("observed_at_utc",Instant.now().toString()).put("lease_expires_at_utc",Instant.now().plusSeconds(60).toString())
                .put("id","explicit-test").put("entry","COMBAT_COMPILED_CONSUMERS")
                .put("java_executable",directory.resolve("java.exe").toString()).put("repository",directory.toString())
                .put("logs_root",directory.resolve("logs").toString()).put("task_root",directory.toString());
        profile.putArray("classpath").add(directory.resolve("test-classes").toString());
        profile.putArray("artifact_refs").add(ref(directory.resolve("probe.class")));
        profile.putArray("source_refs").add(ref(directory.resolve("probe.java")));
        profile.putArray("input_refs").add(ref(directory.resolve("qualification.json")));
        profile.set("qualification_ref",ref(directory.resolve("qualification.json")));
        assertThrows(IllegalArgumentException.class, () -> PrepareManagedMilitaryRequest.decode(profile));
        profile.put("status","HOLD_NATIVE_OR_COMPILED_INPUT_MISSING");
        assertThrows(IllegalArgumentException.class, () -> PrepareManagedMilitaryRequest.decode(profile));
    }
    @Test void defaultSurefireClassesNeverImpersonateThePostPackageMainJar() throws Exception {
        Path main = Path.of(CombatRolesCodec.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().normalize();
        // A normal reactor test loads main code from target/classes. The explicit post-package probe must reject it.
        assertTrue(Files.isDirectory(main));
        Path classes = Path.of(ProbeCompiledCombatConsumers.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().normalize();
        ObjectNode q=StrictJson.object().put("schema","xar.compiled-combat-probe-input/v1")
                .put("task_root",directory.toString()).put("logs_root",directory.resolve("logs").toString())
                .put("scratch_root",directory.resolve("scratch").toString()).put("repository",directory.toString())
                .put("python",directory.resolve("python.exe").toString()).put("test_classes",classes.toString())
                .put("original_wire_reference",directory.resolve("wire-ref.json").toString())
                .put("native_receipt_reference",directory.resolve("native-ref.json").toString())
                .put("fresh_output",directory.resolve("logs/probe.json.gz").toString());
        q.set("main_jar",ref(main)); q.set("golden",ref(directory.resolve("original-golden.gz")));
        q.set("original_wire",ref(directory.resolve("original-wire.json")));
        q.set("native_producer_receipt",ref(directory.resolve("native-actual.json")));
        q.putArray("test_class_files").add(ref(classes.resolve("org/xar/ck3/control/wave2/military/combatroles/ProbeCompiledCombatConsumers.class")));
        Path input=directory.resolve("qualification.json"); Files.write(input,q.toString().getBytes(StandardCharsets.UTF_8));
        assertThrows(IllegalArgumentException.class, () -> ProbeCompiledCombatConsumers.main(new String[] {input.toString()}));
        assertFalse(Files.exists(directory.resolve("logs/probe.json.gz")));
    }
}
