package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

/** Opaque unit fixtures only: no process, Native stage, compiler, settings write or genuine wire is produced. */
final class NativeActualReaderTest {
    private static final String MACHINE = "xenoamess-full-tower-eb9d2c1186";
    private static final NativeFixtureBuild.ActualStage COMBAT = NativeFixtureBuild.ActualStage.COMBATROLES_PRODUCER;
    @TempDir Path temporary;

    private record Fixture(NativeFixtureBuild.Actual actual, Path receipt, List<Path> evidence) { }

    @Test void typedProducerRoundTripsThroughTheSamePublicStageAndFileReader() throws Exception {
        Fixture fixture = fixture(temporary.resolve("typed"));
        byte[] wire = Files.readAllBytes(fixture.receipt());
        assertEquals(fixture.actual(), NativeFixtureBuild.parseActual(wire, COMBAT));
        assertEquals(fixture.actual(), NativeFixtureBuild.readActual(fixture.receipt(), COMBAT));
        assertThrows(IOException.class, () -> NativeFixtureBuild.parseActual(wire, NativeFixtureBuild.ActualStage.TWO_TARGET_BUILD));
    }

    @Test void legacyMissingWrongTypeWrongOwnerAndCleanupCannotBecomeProducerPass() throws Exception {
        Fixture fixture = fixture(temporary.resolve("bad-terminal"));
        var mapper = ControlBuild.strictMapper();
        ObjectNode original = mapper.valueToTree(fixture.actual());
        for (String field : List.of("stage_deadline_at_utc", "lifecycle", "result", "source_manifest_ref")) {
            ObjectNode wrong = original.deepCopy(); wrong.remove(field);
            assertThrows(IOException.class, () -> NativeFixtureBuild.parseActual(mapper.writeValueAsBytes(wrong), COMBAT), field);
        }
        ObjectNode legacy = original.deepCopy(); legacy.put("schema", "xar.shared-native-stage-actual/v1");
        assertThrows(IOException.class, () -> NativeFixtureBuild.parseActual(mapper.writeValueAsBytes(legacy), COMBAT));
        ObjectNode wrongStage = original.deepCopy(); wrongStage.put("stage_id", "two-target-build");
        assertThrows(IOException.class, () -> NativeFixtureBuild.parseActual(mapper.writeValueAsBytes(wrongStage), COMBAT));
        ObjectNode wrongType = original.deepCopy(); wrongType.put("source_unchanged", 1);
        assertThrows(IOException.class, () -> NativeFixtureBuild.parseActual(mapper.writeValueAsBytes(wrongType), COMBAT));
        ObjectNode wrongMemory = original.deepCopy();
        ((ObjectNode) wrongMemory.path("result").path("accounting")).put("memory_limit_bytes", true);
        assertThrows(IOException.class, () -> NativeFixtureBuild.parseActual(mapper.writeValueAsBytes(wrongMemory), COMBAT));
        ObjectNode wrongOwner = original.deepCopy(); ((ObjectNode) wrongOwner.path("owner_identity")).put("pid", 19);
        assertThrows(IOException.class, () -> NativeFixtureBuild.parseActual(mapper.writeValueAsBytes(wrongOwner), COMBAT));
        var terminal = fixture.actual().result();
        var cleanup = new WindowsJobProcess.CommandResult(terminal.identity(), 0, 0.1, terminal.accounting(), "timeout_or_release_expired");
        ObjectNode cleaned = original.deepCopy(); cleaned.set("result", mapper.valueToTree(cleanup));
        cleaned.set("lifecycle", mapper.valueToTree(NativeLifecycleTerminal.assess(cleanup)));
        assertThrows(IOException.class, () -> NativeFixtureBuild.parseActual(mapper.writeValueAsBytes(cleaned), COMBAT));
        var holyStage=NativeFixtureBuild.ActualStage.HOLY_FIXTURE_TARGET_BUILD;
        ObjectNode holy=original.deepCopy();holy.put("stage_id",holyStage.wireId());
        byte[] holyWire=mapper.writeValueAsBytes(holy);
        assertEquals(holyStage.wireId(),NativeFixtureBuild.parseActual(holyWire,holyStage).stageId());
        for(String field:List.of("environment_ref","configured_graph_ref")) {
            ObjectNode absent=holy.deepCopy();absent.putNull(field);
            String message=field.equals("environment_ref")?"stage environment reference required":"stage configured graph reference required";
            assertEquals(message,assertThrows(IOException.class,
                    ()->NativeFixtureBuild.parseActual(mapper.writeValueAsBytes(absent),holyStage)).getMessage());
        }
        Files.write(fixture.receipt(),holyWire);
        assertEquals("Legacy authority cannot build current fixture",assertThrows(IOException.class,
                ()->NativeFixtureBuild.readActual(fixture.receipt(),holyStage)).getMessage());
    }

    @Test void everyDirectAndManifestEvidenceFileRetainsItsOriginalBytes() throws Exception {
        Fixture fixture = fixture(temporary.resolve("drift"));
        for (Path file : fixture.evidence()) {
            byte[] original = Files.readAllBytes(file);
            Files.writeString(file, "changed opaque unit marker");
            assertThrows(IOException.class, () -> NativeFixtureBuild.readActual(fixture.receipt(), COMBAT), file.toString());
            Files.write(file, original);
            assertEquals(fixture.actual(), NativeFixtureBuild.readActual(fixture.receipt(), COMBAT));
        }
    }

    @Test void overlappingProductionToolRolesRoundTripOnceWhileConflictingOrDuplicateEvidenceFails() throws Exception {
        Fixture fixture = fixture(temporary.resolve("overlapping-tool-roles"));
        var mapper = ControlBuild.strictMapper();
        var base = fixture.actual().toolRefs().getFirst();
        var configuredOnly = ControlBuild.FileRef.measure(marker(temporary, "configured-archive-tool"));
        List<ControlBuild.FileRef> merged = NativeFixtureBuild.mergeToolRefs(List.of(base), List.of(base, configuredOnly));
        assertEquals(2, merged.size());
        assertEquals(merged, NativeFixtureBuild.mergeToolRefs(merged, List.of(base)));
        Path manifestPath = Path.of(fixture.actual().sourceManifestRef().path());
        var manifest = mapper.readValue(Files.readAllBytes(manifestPath), NativeFixtureBuild.SourceManifest.class);
        Files.write(manifestPath, mapper.writeValueAsBytes(new NativeFixtureBuild.SourceManifest(manifest.schema(),
                manifest.machineId(), manifest.observedAtUtc(), manifest.sourceRefs(), merged, manifest.operationRuntimeRefs())));
        ObjectNode wire = mapper.valueToTree(fixture.actual());
        wire.set("tool_refs", mapper.valueToTree(merged));
        wire.set("source_manifest_ref", mapper.valueToTree(ControlBuild.FileRef.measure(manifestPath)));
        Files.write(fixture.receipt(), mapper.writeValueAsBytes(wire));
        assertEquals(merged, NativeFixtureBuild.readActual(fixture.receipt(), COMBAT).toolRefs());
        var conflict = new ControlBuild.FileRef(base.path(), base.bytes() + 1, base.sha256());
        assertThrows(IOException.class, () -> NativeFixtureBuild.mergeToolRefs(List.of(base), List.of(conflict)));
        wire.set("tool_refs", mapper.valueToTree(List.of(base, base, configuredOnly)));
        Files.write(fixture.receipt(), mapper.writeValueAsBytes(wire));
        assertThrows(IOException.class, () -> NativeFixtureBuild.readActual(fixture.receipt(), COMBAT));
    }

    @Test void stageCardMayNarrowButCannotWidenTheProductionMemoryScratchOrTimeMaximum() throws Exception {
        Path marker = marker(temporary, "synthetic-card-input"); var ref = ControlBuild.FileRef.measure(marker);
        var card = new NativeFixtureBuild.ResourceCard("xar.shared-native-stage-resource-card/v2", MACHINE,
                "2026-10-23T00:00:00Z", "2026-10-23T00:01:00Z", "/root/native_fixture09",
                NativeFixtureBuild.ResourceStatus.ADMITTED_SINGLE_STAGE, NativeFixtureBuild.Stage.ENV,
                128L << 20, 4L << 20, 30, ref, ref, ref, ref, ref, ref, List.of(), List.of(temporary.toString()));
        assertEquals(128L << 20, card.memoryLimitBytes()); assertEquals(4L << 20, card.scratchLimitBytes());
        var mapper = ControlBuild.strictMapper(); ObjectNode wide = mapper.valueToTree(card);
        wide.put("memory_limit_bytes", (256L << 20) + 1);
        assertThrows(IOException.class, () -> mapper.treeToValue(wide, NativeFixtureBuild.ResourceCard.class));
        ObjectNode scratch = mapper.valueToTree(card); scratch.put("scratch_limit_bytes", (16L << 20) + 1);
        assertThrows(IOException.class, () -> mapper.treeToValue(scratch, NativeFixtureBuild.ResourceCard.class));
        ObjectNode timeout = mapper.valueToTree(card); timeout.put("timeout_seconds", 121);
        assertThrows(IOException.class, () -> mapper.treeToValue(timeout, NativeFixtureBuild.ResourceCard.class));
    }

    @Test void historicalToolFactsSurviveExpiryWithoutRenewingTheOldBuildExecutionLease() throws Exception {
        Path receiptPath = completedToolFixture(temporary.resolve("synthetic-expired-tools"));
        var expected = ControlBuild.verifiedCompletedReceipt(ControlBuild.FileRef.measure(receiptPath));
        assertThrows(IOException.class, () -> ControlBuild.acceptedReceipt(receiptPath));
        assertEquals(expected, NativeFixtureBuild.readCompletedToolsReceipt(receiptPath));
        Path source = Path.of(expected.sourceRoot()).resolve("src/main/java/ReceiptInput.java");
        Files.writeString(source, "final class ChangedUnitMarker {}");
        assertThrows(IOException.class, () -> NativeFixtureBuild.readCompletedToolsReceipt(receiptPath));
    }

    private static Path marker(Path root, String name) throws IOException {
        Files.createDirectories(root); Path file = root.resolve(name);
        Files.writeString(file, "opaque unit marker: " + name); return file;
    }

    private static Fixture fixture(Path root) throws IOException {
        Files.createDirectories(root);
        Path source = marker(root, "source-marker"), tool = marker(root, "tool-marker"), runtime = marker(root, "runtime-marker");
        Path card = marker(root, "resource-card-marker"), tools = marker(root, "tools-receipt-marker");
        Files.writeString(card,"{\"schema\":\"xar.shared-native-stage-resource-card/v2\"}");
        Path env = marker(root, "environment-marker"), graph = marker(root, "configured-graph-marker");
        Path exe = marker(root, "synthetic-producer.exe"), raw = marker(root, "synthetic-wire-marker");
        Path stdout = marker(root, "stdout-marker"), stderr = marker(root, "stderr-marker");
        var mapper = ControlBuild.strictMapper(); var toolRef = ControlBuild.FileRef.measure(tool);
        Path manifest = root.resolve("source-manifest.json");
        Files.write(manifest, mapper.writeValueAsBytes(new NativeFixtureBuild.SourceManifest("xar.native-stage-source-manifest/v1",
                MACHINE, Instant.now().toString(), List.of(ControlBuild.FileRef.measure(source)), List.of(toolRef),
                List.of(ControlBuild.FileRef.measure(runtime)))));
        var identity = new WindowsJobProcess.ProcessIdentity(17, "1", exe.toString());
        var terminal = new WindowsJobProcess.CommandResult(identity, 0, 0.1,
                new WindowsJobProcess.Accounting(1024, 0, 256L << 20, 8704), null);
        var actual = new NativeFixtureBuild.Actual("xar.shared-native-stage-actual/v2", MACHINE, Instant.now().toString(),
                NativeFixtureBuild.ActualStatus.PASS, COMBAT.wireId(), Instant.now().plusSeconds(60).toString(),
                List.of(exe.toString(), "--wire-dir", root.toString()), root.toString(), ControlBuild.FileRef.measure(env),
                ControlBuild.FileRef.measure(card), ControlBuild.FileRef.measure(tools), ControlBuild.FileRef.measure(manifest),
                ControlBuild.FileRef.measure(graph), List.of(toolRef), List.of(ControlBuild.FileRef.measure(exe)), identity, terminal,
                NativeLifecycleTerminal.assess(terminal), true, ControlBuild.FileRef.measure(stdout), ControlBuild.FileRef.measure(stderr),
                List.of(ControlBuild.FileRef.measure(raw)), null);
        Path receipt = root.resolve("synthetic-actual.json"); Files.write(receipt, mapper.writeValueAsBytes(actual));
        return new Fixture(actual, receipt, List.of(card, tools, env, graph, tool, source, runtime, raw, exe, stdout, stderr, manifest));
    }

    /** Same completed-receipt codec fixture as the shared tests, with explicit synthetic value objects and no CMD child. */
    private static Path completedToolFixture(Path root) throws Exception {
        Files.createDirectories(root); Path source = Files.createDirectory(root.resolve("source"));
        Path compiled = Files.createDirectory(root.resolve("compiled"));
        for (Path directory : List.of(source, compiled)) {
            Files.writeString(directory.resolve("pom.xml"), "<project><modelVersion>4.0.0</modelVersion><groupId>fixture</groupId><artifactId>receipt</artifactId><version>1</version></project>");
            Files.createDirectories(directory.resolve("src/main/java"));
            Files.writeString(directory.resolve("src/main/java/ReceiptInput.java"), "final class ReceiptInput {}");
        }
        Path deployment = Files.createDirectory(root.resolve("deployment")); Files.createDirectory(deployment.resolve("lib"));
        Path archive = marker(deployment, "ck3-control-build-tools-0.1.0-SNAPSHOT.jar"), dependency = marker(deployment.resolve("lib"), "fixture.jar");
        Path scratch = Files.createDirectory(root.resolve("scratch"));
        Instant opened = Instant.now().minusSeconds(3), completed = opened.plusSeconds(2), born = opened.plusSeconds(1);
        Path executable = Path.of(System.getProperty("java.home"), "bin/java.exe");
        String filetime = BigInteger.valueOf(born.getEpochSecond() + 11_644_473_600L).multiply(BigInteger.valueOf(10_000_000L))
                .add(BigInteger.valueOf(born.getNano() / 100)).toString();
        var terminal = new WindowsJobProcess.CommandResult(new WindowsJobProcess.ProcessIdentity(23, filetime, executable.toString()),
                0, 0.1, new WindowsJobProcess.Accounting(1024, 0, 64L << 20, 8704), null);
        var mapper = ControlBuild.strictMapper(); var release = mapper.createObjectNode();
        release.put("schema", "xar.java-phase1.manual-capacity-release/v1"); release.put("machine_id", WindowsJobProcess.currentMachineId());
        release.put("status", "RELEASED_JAVA_PHASE1_BOUNDED_BUILD_AND_LOCAL_SERVICE"); release.put("observed_at_utc", opened.toString());
        release.put("review_at_utc", completed.plusNanos(1).toString()); release.put("temporary_root", scratch.toString());
        Path releasePath = root.resolve("historical-release.json"); Files.write(releasePath, mapper.writeValueAsBytes(release));
        Path launcher = marker(root, "mvn.cmd");
        var toolchain = new ControlBuild.MavenToolchain(ControlBuild.MavenSelection.DEFAULT_COMMAND, "mvn", root.toString(), "3.10.0", "3.10.0", ControlBuild.FileRef.measure(launcher), null);
        var pins = new ArrayList<>(List.of(ControlBuild.FileRef.measure(archive), ControlBuild.FileRef.measure(dependency)));
        pins.sort(Comparator.comparing(ControlBuild.FileRef::path));
        var match = new ControlBuild.SourcePostcheck(ControlBuild.SourceState.MATCH, null);
        var receipt = new ControlBuild.BuildReceipt(ControlBuild.SCHEMA, WindowsJobProcess.currentMachineId(), completed.toString(), "PASS",
                source.toString(), compiled.toString(), deployment.toString(), match, match, ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME,
                ControlBuild.SourceLimitProfile.STANDARD_8_MIB, ControlBuild.sourceManifest(source), ControlBuild.sourceManifest(compiled), pins,
                List.of(ControlBuild.FileRef.measure(executable)), ControlBuild.FileRef.measure(releasePath), toolchain, ControlBuild.FileRef.measure(executable),
                terminal, terminal, Map.of("synthetic-codec-fixture", 0L), null);
        Path path = root.resolve("completed-build.json"); Files.write(path, mapper.writeValueAsBytes(receipt)); return path;
    }
}
