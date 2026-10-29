package org.xar.ck3.control.wave2.military.combatroles;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.NativeFixtureBuild;
import org.xar.ck3.control.build.NativeLifecycleTerminal;
import org.xar.ck3.control.build.WindowsJobProcess;
import static org.junit.jupiter.api.Assertions.*;

/** Opaque metadata unit fixtures only; no process or valid native wire is produced. */
final class CombatNativeReceiptTest {
    private static final ObjectMapper JSON = ControlBuild.strictMapper();
    private static final String MACHINE = "xenoamess-full-tower-eb9d2c1186";
    private static final String EXE = "xar_bridge_ck3_12003_army_combat_roles_phase_rule24_pins_test.exe";
    private static final String RAW = "ck3_12003_army_combat_roles_phase_rule24_pins_wire.json";
    @TempDir Path directory;
    private record Fixture(NativeFixtureBuild.Actual actual, Path receipt,
            CombatWholeWire.FileReference raw, List<Path> evidence) { }

    @Test void typedV2MetadataRoundTrip() throws Exception {
        Fixture f = fixture("roundtrip", EXE);
        assertEquals(f.actual(), NativeFixtureBuild.parseActual(Files.readAllBytes(f.receipt()),
                NativeFixtureBuild.ActualStage.COMBATROLES_PRODUCER));
        assertEquals(f.actual(), admit(f));
        assertThrows(IOException.class, () -> NativeFixtureBuild.parseActual(Files.readAllBytes(f.receipt()),
                NativeFixtureBuild.ActualStage.TWO_TARGET_BUILD));
    }

    @Test void missingSourceOutcomeAndOutputAliasesCannotBecomeNativeEvidence() throws Exception {
        Fixture f = fixture("missing", EXE); ObjectNode baseline = node(f);
        for (String field : List.of("stage_deadline_at_utc", "lifecycle", "owner_identity", "source_unchanged",
                "source_manifest_ref", "result", "command", "output_refs", "environment_ref", "configured_graph_ref")) {
            ObjectNode wrong = baseline.deepCopy(); wrong.remove(field); reject(f, wrong);
        }
        for (String stage : List.of("env-tool-probe", "two-target-build", "kinship-producer")) {
            ObjectNode wrong = baseline.deepCopy(); wrong.put("stage_id", stage); reject(f, wrong);
        }
        ObjectNode legacy = baseline.deepCopy(); legacy.put("schema", "xar.shared-native-stage-actual/v1"); reject(f, legacy);
        ObjectNode obsolete = baseline.deepCopy(); obsolete.set("source_manifest", obsolete.remove("source_manifest_ref")); reject(f, obsolete);
        ObjectNode duplicateName = baseline.deepCopy(); duplicateName.set("source_manifest", duplicateName.get("source_manifest_ref")); reject(f, duplicateName);
        ObjectNode alias = baseline.deepCopy(); alias.set("output_ref", alias.remove("output_refs").get(0)); reject(f, alias);
        ObjectNode unknown = baseline.deepCopy(); unknown.put("status", "UNKNOWN"); reject(f, unknown);
        ObjectNode nullable = baseline.deepCopy(); nullable.putNull("lifecycle"); reject(f, nullable);
    }

    @Test void exactRawReferenceAndFullJobCustodyAreRequired() throws Exception {
        Fixture f = fixture("job", EXE); ObjectNode baseline = node(f);
        for (String field : List.of("exit_code", "active_processes", "peak_job_memory_bytes", "memory_limit_bytes", "limit_flags")) {
            for (boolean booleanToken : List.of(false, true)) {
                ObjectNode wrong = baseline.deepCopy();
                ObjectNode target = field.equals("exit_code") ? (ObjectNode) wrong.get("result")
                        : (ObjectNode) wrong.path("result").path("accounting");
                if (booleanToken) target.put(field, true); else target.put(field, 0.0);
                reject(f, wrong);
            }
        }
        for (String field : List.of("active_processes", "peak_job_memory_bytes", "memory_limit_bytes", "limit_flags")) {
            ObjectNode wrong = baseline.deepCopy();
            ((ObjectNode) wrong.path("result").path("accounting")).put(field, switch (field) {
                case "active_processes" -> 1L;
                case "peak_job_memory_bytes" -> (512L << 20) + 1;
                default -> 0L;
            }); reject(f, wrong);
        }
        ObjectNode failed = baseline.deepCopy(); ((ObjectNode) failed.path("result")).put("exit_code", 1); reject(f, failed);
    }

    @Test void cleanupWithZeroChildrenAndWrongOwnerNeverBecomeNaturalSuccess() throws Exception {
        Fixture f = fixture("lifecycle", EXE); ObjectNode baseline = node(f);
        var terminal = f.actual().result();
        var cleanup = new WindowsJobProcess.CommandResult(terminal.identity(), 0, 0.1,
                terminal.accounting(), "timeout_or_release_expired");
        ObjectNode wrong = baseline.deepCopy(); wrong.set("result", JSON.valueToTree(cleanup));
        wrong.set("lifecycle", JSON.valueToTree(NativeLifecycleTerminal.assess(cleanup))); reject(f, wrong);
        ObjectNode owner = baseline.deepCopy(); ((ObjectNode) owner.path("owner_identity")).put("pid", 19); reject(f, owner);
        ObjectNode forged = baseline.deepCopy(); ((ObjectNode) forged.path("lifecycle")).put("successful", false); reject(f, forged);
        ObjectNode stopped = baseline.deepCopy(); ((ObjectNode) stopped.path("result")).put("stop_reason", "forced_cleanup"); reject(f, stopped);
    }

    @Test void executableAndOutputDirectoryRolesStayBoundToOriginalCommand() throws Exception {
        Fixture f = fixture("roles", EXE); ObjectNode baseline = node(f);
        ObjectNode flag = baseline.deepCopy(); flag.withArray("command").set(1, JSON.getNodeFactory().textNode("--other")); reject(f, flag);
        ObjectNode extra = baseline.deepCopy(); extra.withArray("command").add("--wire-dir"); reject(f, extra);
        ObjectNode output = baseline.deepCopy();
        output.withArray("command").set(2, JSON.getNodeFactory().textNode(directory.resolve("other").toAbsolutePath().toString())); reject(f, output);
        ObjectNode linked = baseline.deepCopy(); linked.putArray("linked_artifact_refs"); reject(f, linked);
        Fixture foreign = fixture("foreign", "another-producer.exe");
        assertEquals(foreign.actual(), NativeFixtureBuild.readActual(foreign.receipt(),
                NativeFixtureBuild.ActualStage.COMBATROLES_PRODUCER));
        assertThrows(IOException.class, () -> admit(foreign));
        write(f, baseline);
        var substituted = new CombatWholeWire.FileReference(f.raw().path(), f.raw().bytes(), "b".repeat(64));
        assertThrows(IOException.class, () -> CaptureCombatRolesGolden.verifyNativeProducer(f.receipt(), substituted));
    }

    @Test void oneExactRawOutputIsRequiredWithoutAliasesOrDuplicates() throws Exception {
        Fixture f = fixture("outputs", EXE); ObjectNode baseline = node(f);
        ObjectNode absent = baseline.deepCopy(); absent.putArray("output_refs"); reject(f, absent);
        ObjectNode duplicate = baseline.deepCopy(); duplicate.withArray("output_refs").add(baseline.path("output_refs").get(0)); reject(f, duplicate);
        ObjectNode mismatch = baseline.deepCopy();
        ((ObjectNode) mismatch.path("output_refs").get(0)).put("sha256", "b".repeat(64)); reject(f, mismatch);
        ObjectNode other = baseline.deepCopy();
        other.putArray("output_refs").add(JSON.valueToTree(ControlBuild.FileRef.measure(f.evidence().getFirst()))); reject(f, other);
        assertThrows(IllegalArgumentException.class, () -> new CombatWholeWire.FileReference(
                f.raw().path(), CombatWholeWire.RAW_MAX_BYTES + 1L, f.raw().sha256()));
    }

    @Test void directAndCompleteSourceToolRuntimeEvidenceAreReverified() throws Exception {
        Fixture f = fixture("drift", EXE);
        for (Path evidence : f.evidence()) {
            byte[] original = Files.readAllBytes(evidence); Files.writeString(evidence, "changed opaque unit marker");
            assertThrows(IOException.class, () -> admit(f), evidence.toString());
            Files.write(evidence, original); assertEquals(f.actual(), admit(f));
        }
    }

    @Test void strictFramingAndTokenTypesRemainRejected() throws Exception {
        Fixture f = fixture("tokens", EXE); ObjectNode baseline = node(f);
        ObjectNode wrong = baseline.deepCopy(); wrong.put("source_unchanged", 1); reject(f, wrong);
        ObjectNode machine = baseline.deepCopy(); machine.put("machine_id", 1); reject(f, machine);
        write(f, baseline);
        String valid = Files.readString(f.receipt());
        assertTrue(valid.contains("\"status\":"));
        for (String invalid : List.of(valid + " {}", valid.replaceFirst("\"status\":", "\"status\":\"PASS\",\"status\":"))) {
            Files.writeString(f.receipt(), invalid); assertThrows(IOException.class, () -> admit(f));
        }
    }

    private static NativeFixtureBuild.Actual admit(Fixture f) throws IOException {
        return CaptureCombatRolesGolden.verifyNativeProducer(f.receipt(), f.raw());
    }
    private static ObjectNode node(Fixture f) { return JSON.valueToTree(f.actual()); }
    private static void write(Fixture f, ObjectNode value) throws IOException { Files.write(f.receipt(), JSON.writeValueAsBytes(value)); }
    private static void reject(Fixture f, ObjectNode value) throws IOException {
        write(f, value); assertThrows(IOException.class, () -> admit(f));
    }
    private static Path marker(Path root, String name) throws IOException {
        Path file = root.resolve(name); Files.writeString(file, "opaque unit marker: " + name); return file;
    }
    private Fixture fixture(String name, String executableName) throws IOException {
        Path root = Files.createDirectory(directory.resolve(name)).toAbsolutePath().normalize();
        Path source = marker(root, "source"), tool = marker(root, "tool"), runtime = marker(root, "runtime");
        Path card = marker(root, "resource-card"), tools = marker(root, "tools-receipt");
        Files.writeString(card, "{\"schema\":\"xar.shared-native-stage-resource-card/v2\"}");
        Path env = marker(root, "environment"), graph = marker(root, "configured-graph");
        Path exe = marker(root, executableName), raw = marker(root, RAW);
        Path stdout = marker(root, "stdout"), stderr = marker(root, "stderr");
        var toolRef = ControlBuild.FileRef.measure(tool); Path manifest = root.resolve("source-manifest.json");
        Files.write(manifest, JSON.writeValueAsBytes(new NativeFixtureBuild.SourceManifest(
                "xar.native-stage-source-manifest/v1", MACHINE, "2026-10-23T00:00:00Z",
                List.of(ControlBuild.FileRef.measure(source)), List.of(toolRef), List.of(ControlBuild.FileRef.measure(runtime)))));
        var identity = new WindowsJobProcess.ProcessIdentity(17, "1", exe.toString());
        var terminal = new WindowsJobProcess.CommandResult(identity, 0, 0.1,
                new WindowsJobProcess.Accounting(1024, 0, 512L << 20, 8704), null);
        var actual = new NativeFixtureBuild.Actual("xar.shared-native-stage-actual/v2", MACHINE, "2026-10-23T00:00:00Z",
                NativeFixtureBuild.ActualStatus.PASS, "combatroles-producer", "2026-10-23T00:01:00Z",
                List.of(exe.toString(), "--wire-dir", root.toString()), root.toString(), ControlBuild.FileRef.measure(env),
                ControlBuild.FileRef.measure(card), ControlBuild.FileRef.measure(tools), ControlBuild.FileRef.measure(manifest),
                ControlBuild.FileRef.measure(graph), List.of(toolRef), List.of(ControlBuild.FileRef.measure(exe)), identity,
                terminal, NativeLifecycleTerminal.assess(terminal), true, ControlBuild.FileRef.measure(stdout),
                ControlBuild.FileRef.measure(stderr), List.of(ControlBuild.FileRef.measure(raw)), null);
        Path receipt = root.resolve("unit-actual.json"); Files.write(receipt, JSON.writeValueAsBytes(actual));
        return new Fixture(actual, receipt, new CombatWholeWire.FileReference(raw, Files.size(raw),
                ControlBuild.FileRef.measure(raw).sha256()),
                List.of(card, tools, env, graph, tool, source, runtime, raw, exe, stdout, stderr, manifest));
    }
}
