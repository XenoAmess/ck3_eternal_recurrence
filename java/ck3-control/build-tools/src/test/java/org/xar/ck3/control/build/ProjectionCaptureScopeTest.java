package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.core.JsonProcessingException;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Software contract regression only; actual capture artifact/Job qualification belongs to the build producer. */
final class ProjectionCaptureScopeTest {
    @TempDir Path temporary;

    @Test void actualScopeBytesAndCapturedInputsRemainBoundAtEveryBoundary() throws Exception {
        Path input = Files.writeString(temporary.resolve("capture-request.json"), "{\"request\":1}");
        var requested = request(ControlBuild.FileRef.measure(input), List.of("sample-operation"));
        Path scope = writeScope("scope.json", requested);
        var bound = ProjectionCaptureScope.read(scope, "software-fixture");
        assertEquals(requested, bound.request());
        assertEquals(bound, ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(bound),
                ProjectionCaptureScope.Bound.class));
        var forged = new ProjectionCaptureScope.Request(requested.schema(), requested.machineId(), requested.observedAtUtc(),
                requested.reviewAtUtc(), requested.requestRefs(), List.of("other-operation"));
        assertThrows(IOException.class, () -> new ProjectionCaptureScope.Bound(bound.scopeRef(), forged).verify());
        Files.writeString(input, "{\"request\":2}");
        assertThrows(IOException.class, bound::verify);
        Files.writeString(input, "{\"request\":1}");
        bound.verify();
        Files.writeString(scope, "{}");
        assertThrows(IOException.class, bound::verify);
        assertThrows(IOException.class, () -> ProjectionCaptureScope.read(writeScope("other-machine.json", requested), "different-machine"));
        var expired = new ProjectionCaptureScope.Request(requested.schema(), requested.machineId(), Instant.now().minusSeconds(60).toString(),
                Instant.now().minusSeconds(1).toString(), requested.requestRefs(), requested.operations());
        assertThrows(IOException.class, () -> ProjectionCaptureScope.read(writeScope("expired.json", expired), "software-fixture"));
        var future = new ProjectionCaptureScope.Request(requested.schema(), requested.machineId(), Instant.now().plusSeconds(60).toString(),
                Instant.now().plusSeconds(120).toString(), requested.requestRefs(), requested.operations());
        assertThrows(IOException.class, () -> ProjectionCaptureScope.read(writeScope("future.json", future), "software-fixture"));
    }

    @Test void strictFiniteScopeRejectsCoercionAliasesAndUnadvertisedOperations() throws Exception {
        var ref = ControlBuild.FileRef.measure(Files.writeString(temporary.resolve("request.json"), "{}"));
        var requested = request(ref, List.of("sample-operation"));
        var mapper = ControlBuild.strictMapper(); String json = mapper.writeValueAsString(requested);
        for (String token : List.of("true", "2.0", "\"2\"", "null")) {
            assertThrows(JsonProcessingException.class, () -> mapper.readValue(json.replace("\"bytes\":2", "\"bytes\":" + token),
                    ProjectionCaptureScope.Request.class));
        }
        assertThrows(JsonProcessingException.class, () -> mapper.readValue(json.replace("\"schema\":", "\"alias\":true,\"schema\":"),
                ProjectionCaptureScope.Request.class));
        assertThrows(JsonProcessingException.class, () -> mapper.readValue(json.replace("\"machine_id\":\"software-fixture\"",
                "\"machine_id\":\"software-fixture\",\"machine_id\":\"software-fixture\""), ProjectionCaptureScope.Request.class));
        assertThrows(IllegalArgumentException.class, () -> request(ref, List.of("sample-operation", "sample-operation")));
        assertThrows(IllegalArgumentException.class, () -> request(ref, List.of("ALIAS_OPERATION")));
        assertThrows(IllegalArgumentException.class, () -> new ProjectionCaptureScope.Request(requested.schema(), "unknown",
                requested.observedAtUtc(), requested.reviewAtUtc(), requested.requestRefs(), requested.operations()));
        var bound = ProjectionCaptureScope.read(writeScope("valid.json", requested), "software-fixture");
        // This constructor-only fixture tests allowlist comparison; it is never accepted as an actual deployment proof.
        var identity = new ProjectionDeploymentProof.Identity("xar.projection-host-identity/v1", ProjectionDeploymentProof.PRODUCER,
                ProjectionDeploymentProof.VERSION, ProjectionDeploymentProof.CALL_SCHEMA, ProjectionDeploymentProof.RESULT_SCHEMA,
                ProjectionDeploymentProof.MAX_ENVELOPE_BYTES, List.of(new ProjectionDeploymentProof.OperationProfile("sample-operation", 64, 64)));
        bound.requireCatalog(new ProjectionDeploymentProof.Attestation(identity, List.of()));
        var other = request(ref, List.of("other-operation"));
        var missing = ProjectionCaptureScope.read(writeScope("missing-operation.json", other), "software-fixture");
        assertThrows(IOException.class, () -> missing.requireCatalog(new ProjectionDeploymentProof.Attestation(identity, List.of())));
        Files.write(temporary.resolve("oversized.json"), new byte[ProjectionCaptureScope.MAX_SCOPE_BYTES + 1]);
        assertThrows(IOException.class, () -> ProjectionCaptureScope.read(temporary.resolve("oversized.json"), "software-fixture"));
    }

    @Test void captureStartupRefusesOfflinePublishingBeforeAnyReceiptOrProcessLookup() throws Exception {
        Path state = temporary.resolve("state"), stock = temporary.resolve("stock"), work = temporary.resolve("work");
        var config = new MapAdmissionServiceOwner.Config(temporary.resolve("absent-build.json"), work,
                temporary.resolve("absent-java.exe"), Instant.now().plusSeconds(60), 8089, state, stock,
                temporary.resolve("fixed-grants.json"), new ProjectionOfflineContext.Publishing(null, null));
        assertThrows(IllegalArgumentException.class, () -> MapAdmissionServiceOwner.startForCapture(config, temporary.resolve("scope.json")));
        assertFalse(Files.exists(work));
        var normal = new MapAdmissionServiceOwner.Config(config.buildReceipt(), work, config.javaExecutable(), config.leaseDeadline(), 8089);
        assertNull(normal.offlinePublishing());
        assertThrows(IllegalArgumentException.class, () -> new ControlBuild.NotRunTestCompilation(
                new ControlBuild.FileRef(temporary.resolve("Test.java").toString(), 1, "0".repeat(64)), List.of(), ControlBuild.CaptureTestState.NOT_RUN));
        assertThrows(JsonProcessingException.class, () -> ControlBuild.strictMapper().readValue(
                "\"FULL_SOFTWARE\"", ControlBuild.CaptureQualification.class));
    }

    @Test void declaredGrantExpansionIsExactly1024WithOriginalMetadataEnvelope() throws Exception {
        List<ProjectionRuntimeSources.EvidenceGrant> grants = new ArrayList<>();
        for (int index = 0; index < 1024; index++) {
            grants.add(new ProjectionRuntimeSources.EvidenceGrant("event-source-facts", temporary.resolve("facts-" + index + ".json").toString(),
                    12, "0".repeat(64), "unknown"));
        }
        var snapshot = new ProjectionRuntimeSources.GrantsSnapshot("xar.projection-host-evidence-grants/v1", "software-fixture",
                Instant.now().toString(), grants);
        byte[] raw = ControlBuild.strictMapper().writeValueAsBytes(snapshot);
        assertEquals((1 << 20) + 4096, ProjectionRuntimeSources.MAX_RESPONSE_BYTES);
        assertTrue(raw.length < ProjectionRuntimeSources.MAX_RESPONSE_BYTES);
        assertEquals(snapshot, ControlBuild.strictMapper().readValue(raw, ProjectionRuntimeSources.GrantsSnapshot.class));
        Path response = Files.write(temporary.resolve("initial-grants.json"), raw);
        var ref = ControlBuild.FileRef.measure(response);
        new ProjectionRuntimeSources.ConfiguredManifest(temporary.resolve("grants.json").toString(), ref, 1024);
        grants.add(new ProjectionRuntimeSources.EvidenceGrant("event-source-facts", temporary.resolve("facts-overflow.json").toString(),
                12, "0".repeat(64), "unknown"));
        assertThrows(IllegalArgumentException.class, () -> new ProjectionRuntimeSources.GrantsSnapshot(snapshot.schema(), snapshot.machineId(),
                snapshot.observedAtUtc(), grants));
        assertThrows(IllegalArgumentException.class, () -> new ProjectionRuntimeSources.ConfiguredManifest(
                temporary.resolve("grants.json").toString(), ref, 1025));
    }

    private ProjectionCaptureScope.Request request(ControlBuild.FileRef ref, List<String> operations) {
        return new ProjectionCaptureScope.Request(ProjectionCaptureScope.SCHEMA, "software-fixture", Instant.now().toString(),
                Instant.now().plusSeconds(120).toString(), List.of(ref), operations);
    }

    private Path writeScope(String name, ProjectionCaptureScope.Request request) throws IOException {
        return Files.write(temporary.resolve(name), ControlBuild.strictMapper().writeValueAsBytes(request));
    }
}
