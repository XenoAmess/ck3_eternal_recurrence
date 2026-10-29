package org.xar.ck3.control.wave2.prisoners.releasepreview;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.NativeFixtureBuild;
import org.xar.ck3.control.build.NativeLifecycleTerminal;
import org.xar.ck3.control.build.WindowsJobProcess;

/** Synthetic admission metadata only. No native wire, EXE execution or genuine producer credit. */
final class ReleasePreviewNativeAdmissionTest {
    private static final ObjectMapper JSON = ControlBuild.strictMapper();
    private static final String MACHINE = "xenoamess-full-tower-eb9d2c1186";
    private static final String NOW = "2026-10-23T00:00:00Z";
    private static final List<String> CASES = List.of("nonchild_close_family", "unrelated",
            "sample_drift", "wrong_generation", "wrong_jailer", "not_paused");

    private record Fixture(Path root, Path input, Path actual, Path executable, Path source,
                           Path tool, Path runtime, ObjectNode receipt) { }

    @Test
    void sharedTypedProducerRoundTripAndExactSixBindings(@TempDir Path root) throws IOException {
        Fixture fixture = fixture(root);
        NativeFixtureBuild.Actual parsed = NativeFixtureBuild.parseActual(
                JSON.writeValueAsBytes(fixture.receipt()), NativeFixtureBuild.ActualStage.KINSHIP_PRODUCER);
        NativeFixtureBuild.Actual admitted = ReleasePreviewCompatibilityCapture.verifyNativeKinshipInput(
                MACHINE, fixture.input(), fixture.actual());
        assertEquals(parsed, admitted);
        assertEquals(6, admitted.outputRefs().size());
        assertEquals(NativeLifecycleTerminal.Settlement.NATURAL_SETTLED, admitted.lifecycle().settlement());
    }

    @Test
    void unsignedThreeArgumentRouteFailsBeforeOutput(@TempDir Path root) {
        Path output = root.resolve("output");
        assertThrows(IllegalArgumentException.class, () -> ReleasePreviewCompatibilityCapture.main(
                new String[] {MACHINE, output.toString(), root.resolve("raw").toString()}));
        assertFalse(Files.exists(output));
    }

    @Test
    void envBuildAndConfigureCannotMasqueradeAsProducer(@TempDir Path root) throws IOException {
        Fixture fixture = fixture(root);
        for (String stage : List.of("env-tool-probe", "two-target-build", "configure-next01")) {
            fixture.receipt().put("stage_id", stage);
            rejectBeforeOutput(fixture);
        }
    }

    @Test
    void v1ReceiptCannotAdmitRawDirectory(@TempDir Path root) throws IOException {
        Fixture fixture = fixture(root);
        fixture.receipt().put("schema", "xar.shared-native-stage-actual/v1");
        rejectBeforeOutput(fixture);
    }

    @Test
    void missingDeadlineOrLifecycleCannotAdmitRawDirectory(@TempDir Path root) throws IOException {
        Fixture fixture = fixture(root);
        for (String field : List.of("stage_deadline_at_utc", "lifecycle")) {
            ObjectNode original = fixture.receipt().deepCopy();
            fixture.receipt().remove(field);
            rejectBeforeOutput(fixture);
            fixture.receipt().setAll(original.deepCopy());
        }
    }

    @Test
    void failedActiveAndCleanupSettledResultsCannotAdmit(@TempDir Path root) throws IOException {
        Fixture fixture = fixture(root);
        ObjectNode original = fixture.receipt().deepCopy();
        ObjectNode result = (ObjectNode) fixture.receipt().get("result");
        result.put("exit_code", 1);
        fixture.receipt().set("lifecycle", JSON.valueToTree(NativeLifecycleTerminal.assess(
                JSON.treeToValue(result, WindowsJobProcess.CommandResult.class))));
        rejectBeforeOutput(fixture);
        fixture.receipt().setAll(original.deepCopy());
        result = (ObjectNode) fixture.receipt().get("result");
        ((ObjectNode) result.get("accounting")).put("active_processes", 1);
        fixture.receipt().set("lifecycle", JSON.valueToTree(NativeLifecycleTerminal.assess(
                JSON.treeToValue(result, WindowsJobProcess.CommandResult.class))));
        rejectBeforeOutput(fixture);
        fixture.receipt().setAll(original.deepCopy());
        result = (ObjectNode) fixture.receipt().get("result");
        result.put("stop_reason", "timeout_cleanup_job0");
        fixture.receipt().set("lifecycle", JSON.valueToTree(NativeLifecycleTerminal.assess(
                JSON.treeToValue(result, WindowsJobProcess.CommandResult.class))));
        rejectBeforeOutput(fixture);
    }

    @Test
    void missingTerminalOwnerOrUnchangedProofIsRejected(@TempDir Path root) throws IOException {
        Fixture fixture = fixture(root);
        ObjectNode original = fixture.receipt().deepCopy();
        for (String field : List.of("result", "owner_identity")) {
            fixture.receipt().putNull(field);
            rejectBeforeOutput(fixture);
            fixture.receipt().setAll(original.deepCopy());
        }
        fixture.receipt().put("source_unchanged", false);
        rejectBeforeOutput(fixture);
    }

    @Test
    void sameLengthRawDriftIsRejectedBeforeOutput(@TempDir Path root) throws IOException {
        Fixture fixture = fixture(root);
        Path raw = fixture.input().resolve(CASES.getFirst() + ".json");
        byte[] bytes = Files.readAllBytes(raw);
        bytes[0] ^= 1;
        Files.write(raw, bytes);
        rejectBeforeOutput(fixture);
    }

    @Test
    void sourceToolRuntimeAndExeDriftAreRechecked(@TempDir Path root) throws IOException {
        int ordinal = 0;
        for (String role : List.of("source", "tool", "runtime", "exe")) {
            Fixture fixture = fixture(Files.createDirectory(root.resolve("case-" + ordinal++)));
            Path selected = switch (role) {
                case "source" -> fixture.source();
                case "tool" -> fixture.tool();
                case "runtime" -> fixture.runtime();
                case "exe" -> fixture.executable();
                default -> throw new IllegalStateException(role);
            };
            Files.writeString(selected, "changed source identity");
            rejectBeforeOutput(fixture);
        }
    }

    @Test
    void missingDuplicateAndExtraNativeRefsAreRejected(@TempDir Path root) throws IOException {
        Fixture fixture = fixture(root);
        ArrayNode original = ((ArrayNode) fixture.receipt().get("output_refs")).deepCopy();
        ((ArrayNode) fixture.receipt().get("output_refs")).remove(5);
        rejectBeforeOutput(fixture);
        fixture.receipt().set("output_refs", original.deepCopy());
        ((ArrayNode) fixture.receipt().get("output_refs")).set(5, original.get(0));
        rejectBeforeOutput(fixture);
        fixture.receipt().set("output_refs", original.deepCopy());
        ((ArrayNode) fixture.receipt().get("output_refs")).add(original.get(0));
        rejectBeforeOutput(fixture);
    }

    @Test
    void foreignCaseRefCannotReplaceAMandatoryCase(@TempDir Path root) throws IOException {
        Fixture fixture = fixture(root);
        Path foreign = Files.writeString(root.resolve("foreign.json"), "synthetic admission marker");
        ((ArrayNode) fixture.receipt().get("output_refs")).set(5, JSON.valueToTree(ControlBuild.FileRef.measure(foreign)));
        rejectBeforeOutput(fixture);
    }

    @Test
    void oversizedBoundRawFileIsRejected(@TempDir Path root) throws IOException {
        Fixture fixture = fixture(root);
        Path raw = fixture.input().resolve(CASES.getFirst() + ".json");
        Files.write(raw, new byte[ReleaseCollectionProjection12003.MAX_BYTES + 1]);
        ((ArrayNode) fixture.receipt().get("output_refs")).set(0, JSON.valueToTree(ControlBuild.FileRef.measure(raw)));
        rejectBeforeOutput(fixture);
    }

    @Test
    void unrelatedDirectoryEntriesAreRejected(@TempDir Path root) throws IOException {
        Fixture fixture = fixture(root);
        Files.writeString(fixture.input().resolve("extra.json"), "unbound entry");
        rejectBeforeOutput(fixture);
    }

    @Test
    void mismatchedArgvDirectoryAndExecutableAreRejected(@TempDir Path root) throws IOException {
        Fixture fixture = fixture(root);
        ArrayNode command = (ArrayNode) fixture.receipt().get("command");
        command.set(1, JSON.valueToTree(root.resolve("different-input").toString()));
        rejectBeforeOutput(fixture);
        command.set(1, JSON.valueToTree(fixture.input().toString()));
        command.set(0, JSON.valueToTree(root.resolve("foreign.exe").toString()));
        rejectBeforeOutput(fixture);
        command.set(0, JSON.valueToTree(fixture.executable().toString()));
        command.add("unused-argument");
        rejectBeforeOutput(fixture);
    }

    @Test
    void linkedExeMustBePresentExactlyOnce(@TempDir Path root) throws IOException {
        Fixture fixture = fixture(root);
        ArrayNode linked = (ArrayNode) fixture.receipt().get("linked_artifact_refs");
        linked.removeAll();
        rejectBeforeOutput(fixture);
        linked.add(JSON.valueToTree(ControlBuild.FileRef.measure(fixture.executable())));
        linked.add(JSON.valueToTree(ControlBuild.FileRef.measure(fixture.executable())));
        rejectBeforeOutput(fixture);
    }

    @Test
    void oldReleaseWireCannotMasqueradeAsSchemaSevenKinship(@TempDir Path root) throws IOException {
        Fixture fixture = fixture(root);
        byte[] oldWire;
        try (var resource = ReleasePreviewCompatibilityCapture.class.getResourceAsStream(
                "/releasepreview/native12003/gate_true.json")) {
            if (resource == null) { throw new IOException("required retained original fixture is absent"); }
            oldWire = resource.readAllBytes();
        }
        ArrayNode refs = (ArrayNode) fixture.receipt().get("output_refs");
        for (int ordinal = 0; ordinal < CASES.size(); ordinal++) {
            Path raw = fixture.input().resolve(CASES.get(ordinal) + ".json");
            Files.write(raw, oldWire);
            refs.set(ordinal, JSON.valueToTree(ControlBuild.FileRef.measure(raw)));
        }
        writeReceipt(fixture);
        Path output = root.resolve("wrong-schema-output");
        assertThrows(IllegalArgumentException.class, () -> ReleasePreviewCompatibilityCapture.main(
                new String[] {MACHINE, output.toString(), fixture.input().toString(), fixture.actual().toString()}));
        assertFalse(Files.exists(output.resolve("CAPTURE.json")));
        assertFalse(Files.exists(output.resolve("kinship12003/nonchild_close_family.json")));
    }

    @Test
    void callerMachineMustMatchAcceptedActual(@TempDir Path root) throws IOException {
        Fixture fixture = fixture(root);
        writeReceipt(fixture);
        Path output = root.resolve("wrong-machine-output");
        assertThrows(IllegalArgumentException.class, () -> ReleasePreviewCompatibilityCapture.main(
                new String[] {"different-machine", output.toString(), fixture.input().toString(), fixture.actual().toString()}));
        assertFalse(Files.exists(output));
    }

    private static Fixture fixture(Path root) throws IOException {
        Path input = Files.createDirectory(root.resolve("native-six"));
        List<ControlBuild.FileRef> outputRefs = new ArrayList<>();
        for (String name : CASES) {
            // Opaque marker exercises admission only, deliberately not a fake native business envelope.
            Path raw = Files.writeString(input.resolve(name + ".json"), "synthetic admission marker:" + name);
            outputRefs.add(ControlBuild.FileRef.measure(raw));
        }
        Path executable = Files.writeString(root.resolve("ck3_12003_prisoner_native_kinship_test.exe"), "unit fixture only");
        Path source = Files.writeString(root.resolve("producer.cpp"), "unit source pin");
        Path tool = Files.writeString(root.resolve("compiler.exe"), "unit tool pin");
        Path runtime = Files.writeString(root.resolve("runtime.jar"), "unit runtime pin");
        Path metadata = Files.writeString(root.resolve("metadata.json"), "{}");
        Path stdout = Files.writeString(root.resolve("stdout.log"), "");
        Path stderr = Files.writeString(root.resolve("stderr.log"), "");
        NativeFixtureBuild.SourceManifest manifest = new NativeFixtureBuild.SourceManifest(
                "xar.native-stage-source-manifest/v1", MACHINE, NOW, List.of(ControlBuild.FileRef.measure(source)),
                List.of(ControlBuild.FileRef.measure(tool)), List.of(ControlBuild.FileRef.measure(runtime)));
        Path manifestPath = root.resolve("source-manifest.json");
        Files.write(manifestPath, JSON.writeValueAsBytes(manifest));
        WindowsJobProcess.ProcessIdentity identity = new WindowsJobProcess.ProcessIdentity(
                1234, "133000000000000000", executable.toString());
        WindowsJobProcess.CommandResult terminal = new WindowsJobProcess.CommandResult(identity, 0, 0.01,
                new WindowsJobProcess.Accounting(1048576, 0, 268435456, WindowsJobProcess.REQUIRED_FLAGS), null);
        ControlBuild.FileRef metadataRef = ControlBuild.FileRef.measure(metadata);
        NativeFixtureBuild.Actual actual = new NativeFixtureBuild.Actual(
                "xar.shared-native-stage-actual/v2", MACHINE, NOW, NativeFixtureBuild.ActualStatus.PASS,
                "kinship-producer", "2026-10-23T00:02:00Z", List.of(executable.toString(), input.toString()),
                root.toString(), metadataRef, metadataRef, metadataRef, ControlBuild.FileRef.measure(manifestPath),
                metadataRef, List.of(ControlBuild.FileRef.measure(tool)), List.of(ControlBuild.FileRef.measure(executable)),
                identity, terminal, NativeLifecycleTerminal.assess(terminal), true, ControlBuild.FileRef.measure(stdout),
                ControlBuild.FileRef.measure(stderr), outputRefs, null);
        Fixture fixture = new Fixture(root, input, root.resolve("native-actual.json"), executable, source, tool,
                runtime, JSON.valueToTree(actual));
        writeReceipt(fixture);
        return fixture;
    }

    private static void writeReceipt(Fixture fixture) throws IOException {
        Files.write(fixture.actual(), JSON.writeValueAsBytes(fixture.receipt()));
    }

    private static void rejectBeforeOutput(Fixture fixture) throws IOException {
        writeReceipt(fixture);
        Path output = fixture.root().resolve("must-remain-absent");
        boolean rejected = false;
        try {
            ReleasePreviewCompatibilityCapture.main(
                    new String[] {MACHINE, output.toString(), fixture.input().toString(), fixture.actual().toString()});
        } catch (IOException | IllegalArgumentException expected) {
            rejected = true;
        }
        assertTrue(rejected, "typed native admission must reject before output");
        assertFalse(Files.exists(output));
    }
}
