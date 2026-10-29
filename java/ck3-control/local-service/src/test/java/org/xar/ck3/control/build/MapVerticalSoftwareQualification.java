package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.CampaignMapAdmission;
import org.xar.ck3.control.contracts.CampaignMapAdmissionComposer;
import org.xar.ck3.control.contracts.CampaignMapComposeRequest;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.SavedFrame;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionWire;

/** One actual existing Quarkus Owner; no @QuarkusTest-created second service. */
final class MapVerticalSoftwareQualification {
    public record Input(MapAdmissionServiceOwner.Config service, MapAdmissionCi.Config consumers,
            List<ControlBuild.FileRef> selectedMapSources, List<ControlBuild.FileRef> consumerSources,
            String outputRoot) { }

    @Test void actualOriginalMapProducerBothHttpPortsAndEveryOriginalConsumerShareOneFiniteOwner() throws Exception {
        String configured = System.getProperty("xar.map.vertical.config");
        if (configured == null) throw new IllegalStateException("mandatory exact software map fixture configuration missing");
        var inputRef = ControlBuild.strictMapper().readValue(configured, ControlBuild.FileRef.class);
        inputRef.verify();
        Input input = RootNativePlanJson.mapper().readValue(Files.readAllBytes(Path.of(inputRef.path())), Input.class);
        Path output = Path.of(input.outputRoot()).toAbsolutePath().normalize();
        assertEquals(output.toString(), Path.of(System.getProperty("xar.map.vertical.output")).toAbsolutePath().normalize().toString());
        assertEquals(output.resolve("host"), input.service().workRoot());
        assertEquals(output.resolve("consumers"), input.consumers().workRoot());
        assertFalse(Files.exists(input.service().workRoot()));

        try (var manifest = DelegatedGuard.begin(ControlBuild.FileRef.measure(input.service().buildReceipt()), output)) {
        assertEquals(input.service().buildReceipt().toString(), manifest.captureRef().path());
        // Software-only identities: these values are never presented as a live native game observation.
        var request = new CampaignMapComposeRequest(WindowsJobProcess.currentMachineId(),
                new GameGeneration(200332, new PythonOnlyUInt64(StrictJson.UINT64_MAX)), "map-software-fixture",
                new SavedFrame("native:1", 2, 1, 53279400, 40526, "software-fixture-episode"), Instant.now().toString());
        byte[] original = request.toCanonicalBytes();
        byte[] expected = CampaignMapAdmissionComposer.compose(original);
        var call = new ProjectionCall(new ProjectionCall.Identity("map-software-1", ProjectionOperation.MAP_ADMISSION_COMPOSE),
                ProjectionJson.object(original, StrictJson.INPUT_MAX_BYTES));
        ControlBuild.FileRef directRef = write(output.resolve("actual-map-request.json"), original);
        ControlBuild.FileRef callRef = write(output.resolve("actual-map-projection-request.json"), ProjectionWire.encodeCall(call));
        var scope = new ProjectionCaptureScope.Request(ProjectionCaptureScope.SCHEMA, WindowsJobProcess.currentMachineId(),
                Instant.now().toString(), input.service().leaseDeadline().toString(), List.of(directRef, callRef), List.of("map-admission-compose"));
        ControlBuild.FileRef scopeRef = write(output.resolve("actual-map-scope.json"), ControlBuild.strictMapper().writeValueAsBytes(scope));
        var config = new MapVerticalSoftwareHost.Config(input.service(), scopeRef, input.selectedMapSources(), input.consumerSources());
        MapVerticalSoftwareHost.Session limited = MapVerticalSoftwareHost.open(config);
        try (limited) {
            assertEquals(MapVerticalSoftwareHost.Purpose.MAP_VERTICAL_SOFTWARE_ONLY, limited.purpose());
            assertThrows(IllegalStateException.class, limited::qualification);
            var direct = limited.post(MapAdmissionServiceOwner.COMPOSE_PATH, directRef);
            assertArrayEquals(expected, direct.responseBytes());
            CampaignMapAdmission parsed = CampaignMapAdmission.fromJson(StrictJson.parse(direct.responseBytes()));
            assertEquals(new BigInteger("18446744073709551615"), parsed.game().creationFiletime().value());
            assertArrayEquals(direct.responseBytes(), parsed.toCanonicalBytes());
            var projected = limited.post("/v1/projections/call", callRef);
            var result = ProjectionWire.decodeResult(projected.responseBytes());
            var succeeded = org.junit.jupiter.api.Assertions.assertInstanceOf(ProjectionResult.Succeeded.class, result);
            assertArrayEquals(direct.responseBytes(), succeeded.result().bytes());
            assertEquals(call.identity(), succeeded.identity());
            var qualification = limited.qualify(input.consumers(), direct, projected);
            qualification.verifyCurrent();
            assertEquals(limited.captureRef(), qualification.captureRef());
            assertEquals(limited.programRef(), qualification.programRef());
            // Borrowed CI closure cannot kill the original host or grant a different generation.
            limited.requireCurrent(); limited.qualification().verifyCurrent(); inputRef.verify();
        }
        assertThrows(IllegalStateException.class, limited::requireCurrent);
        var closed = ControlBuild.strictMapper().readValue(Files.readAllBytes(input.service().workRoot().resolve("logs/service-closed.json")),
                MapAdmissionServiceOwner.ClosedReceipt.class);
        assertEquals(0, closed.jobActiveFinal()); assertEquals(0, closed.gameRpcOrCampaignLedgerWrites());
        assertEquals(MapAdmissionServiceOwner.ProcessWire.from(limited.identity()), closed.originalProcess());
        }
    }

    private record Counts(int sources, int compiled, int deployment, int runtime, int unique) { }
    private record Observation(String schema, String machineId, String observedAtUtc, String phase,
            ControlBuild.FileRef captureRef, Counts counts, List<SharedSourceFiles.Witness> witnesses) { }
    private record FailedPost(String machineId, String observedAtUtc, ControlBuild.FileRef captureRef,
            Counts counts, int checked, String error) { }
    private record DelegatedGuard(ControlBuild.FileRef captureRef, ControlBuild.CaptureBuildReceipt receipt,
            Path output, Counts counts, List<SharedSourceFiles.Witness> witnesses) implements AutoCloseable {
        static DelegatedGuard begin(ControlBuild.FileRef ref, Path output) throws java.io.IOException {
            var receipt = ControlBuild.verifiedCompletedCaptureReceipt(ref);
            var observed = observe(List.of(receipt.sourcePins(), receipt.compiledSourcePins(),
                    receipt.completeDeployment(), receipt.producerRuntimePins(), List.of(ref, receipt.testCompilationRef())));
            var counts = new Counts(receipt.sourcePins().size(), receipt.compiledSourcePins().size(),
                    receipt.completeDeployment().size(), receipt.producerRuntimePins().size(), observed.size());
            var guard = new DelegatedGuard(ref, receipt, output, counts, observed);
            guard.persist("PRE", observed);
            return guard;
        }
        private void persist(String phase, List<SharedSourceFiles.Witness> observed) throws java.io.IOException {
            write(output.resolve("delegated-manifest-" + phase.toLowerCase(java.util.Locale.ROOT) + ".json"),
                    ControlBuild.strictMapper().writeValueAsBytes(new Observation("xar.map-delegated-manifest/v1",
                            WindowsJobProcess.currentMachineId(), Instant.now().toString(), phase, captureRef, counts, observed)));
        }
        @Override public void close() throws java.io.IOException {
            int checked = 0;
            try {
                if (!receipt.equals(ControlBuild.verifiedCompletedCaptureReceipt(captureRef))) throw new java.io.IOException("complete capture changed");
                var after = new java.util.ArrayList<SharedSourceFiles.Witness>();
                for (var witness : witnesses) {
                    SharedSourceFiles.assertUnchanged(witness);
                    after.add(SharedSourceFiles.observe(Path.of(witness.source().path())));
                    checked++;
                }
                persist("POST", List.copyOf(after));
            } catch (java.io.IOException | RuntimeException failure) {
                try { write(output.resolve("delegated-manifest-post-failure.json"),
                        ControlBuild.strictMapper().writeValueAsBytes(new FailedPost(WindowsJobProcess.currentMachineId(),
                                Instant.now().toString(), captureRef, counts, checked, failure.toString()))); }
                catch (java.io.IOException | RuntimeException recording) { failure.addSuppressed(recording); }
                throw failure;
            }
        }
    }
    private static List<SharedSourceFiles.Witness> observe(List<List<ControlBuild.FileRef>> groups) throws java.io.IOException {
        var refs = new java.util.LinkedHashMap<Path, ControlBuild.FileRef>();
        for (var group : groups) for (var ref : group) {
            Path path = Path.of(ref.path()).toAbsolutePath().normalize();
            var previous = refs.putIfAbsent(path, ref);
            if (previous != null && !previous.equals(ref)) throw new java.io.IOException("conflicting exact manifest path");
        }
        var observed = new java.util.ArrayList<SharedSourceFiles.Witness>();
        for (var entry : refs.entrySet()) {
            var witness = SharedSourceFiles.observe(entry.getKey());
            if (!entry.getValue().equals(witness.source())) throw new java.io.IOException("manifest/native witness exact source differs");
            observed.add(witness);
        }
        return List.copyOf(observed);
    }
    @Test void delegatedWitnessRejectsConflictingContentAndSameByteIdentityReplacement() throws Exception {
        Path root = Path.of(System.getProperty("xar.map.vertical.guard-test-root")).toAbsolutePath().normalize();
        Files.createDirectory(root);
        Path file = root.resolve("source.txt");
        var ref = write(file, new byte[] {1, 2, 3});
        var observed = observe(List.of(List.of(ref), List.of(ref)));
        assertEquals(1, observed.size());
        assertThrows(java.io.IOException.class, () -> observe(List.of(List.of(ref,
                new ControlBuild.FileRef(ref.path(), ref.bytes(), "0".repeat(64))))));
        Files.write(file, new byte[] {3, 2, 1});
        assertThrows(java.io.IOException.class, () -> SharedSourceFiles.assertUnchanged(observed.getFirst()));
        Files.delete(file);
        Files.write(file, new byte[] {1, 2, 3}, StandardOpenOption.CREATE_NEW);
        assertThrows(java.io.IOException.class, () -> SharedSourceFiles.assertUnchanged(observed.getFirst()));
    }
    private static ControlBuild.FileRef write(Path path, byte[] raw) throws java.io.IOException {
        Files.write(path, raw, StandardOpenOption.CREATE_NEW); return ControlBuild.FileRef.measure(path);
    }
}
