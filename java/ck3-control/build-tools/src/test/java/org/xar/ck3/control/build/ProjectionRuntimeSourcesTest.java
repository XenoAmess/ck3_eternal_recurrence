package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.core.JsonProcessingException;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;
import javax.tools.ToolProvider;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class ProjectionRuntimeSourcesTest {
    @TempDir Path temporary;
    private static final String ROLE = "org.xar.ck3.control.contracts.projection.ProjectionEvidenceRole";

    @Test void strictSnapshotAndExplicitConfigRejectCoercionMissingFieldsDuplicatesAndUnpairedRoots() throws Exception {
        var mapper = ControlBuild.strictMapper(); var grant = grant("event-source-facts");
        var value = snapshot(grant); String json = mapper.writeValueAsString(value);
        assertEquals(value, mapper.readValue(json, ProjectionRuntimeSources.GrantsSnapshot.class));
        for (String token : List.of("true", "1.0", "\"12\"", "null")) {
            assertThrows(JsonProcessingException.class, () -> mapper.readValue(json.replace("\"bytes\":12", "\"bytes\":" + token),
                    ProjectionRuntimeSources.GrantsSnapshot.class));
        }
        assertThrows(JsonProcessingException.class, () -> mapper.readValue(json.replace("\"grants\":[", "\"alias\":true,\"grants\":["),
                ProjectionRuntimeSources.GrantsSnapshot.class));
        assertThrows(JsonProcessingException.class, () -> mapper.readValue(json.replace(",\"grants\":[" + mapper.writeValueAsString(grant) + "]", ""),
                ProjectionRuntimeSources.GrantsSnapshot.class));
        assertThrows(IllegalArgumentException.class, () -> new ProjectionRuntimeSources.GrantsSnapshot(value.schema(),
                value.machineId(), value.observedAtUtc(), List.of(grant, grant)));
        Path state = Files.createDirectory(temporary.resolve("state")), stock = Files.createDirectory(temporary.resolve("stock"));
        Path fixedManifest = temporary.resolve("future-offline-grants.json");
        var config = new MapAdmissionServiceOwner.Config(temporary.resolve("build.json"), temporary.resolve("work"),
                temporary.resolve("java.exe"), Instant.now().plusSeconds(120), 8089, state, stock, fixedManifest);
        assertEquals(fixedManifest, config.evidenceGrantsManifest());
        assertThrows(IllegalArgumentException.class, () -> new MapAdmissionServiceOwner.Config(config.buildReceipt(), config.workRoot(),
                config.javaExecutable(), config.leaseDeadline(), 8089, null, null, fixedManifest));
        assertNull(new MapAdmissionServiceOwner.Config(config.buildReceipt(), config.workRoot(), config.javaExecutable(),
                config.leaseDeadline(), 8089, state, stock).evidenceGrantsManifest());
    }

    @Test void actualSharedPackagedRoleEnumRejectsUnknownAliasedAndDriftedGrantDeclarations() throws Exception {
        Path jar = roleJar(false); var pins = List.of(ControlBuild.FileRef.measure(jar));
        ProjectionRuntimeSources.requireCurrentSnapshot(snapshot(grant("event-source-facts")), "software-fixture", pins);
        assertThrows(IOException.class, () -> ProjectionRuntimeSources.requireCurrentSnapshot(
                snapshot(grant("unregistered-role")), "software-fixture", pins));
        assertThrows(IOException.class, () -> ProjectionRuntimeSources.requireCurrentSnapshot(
                snapshot(grant("event-source-facts")), "other-machine", pins));
        var stale = new ProjectionRuntimeSources.GrantsSnapshot("xar.projection-host-evidence-grants/v1", "software-fixture",
                Instant.now().minusSeconds(60).toString(), List.of());
        assertThrows(IOException.class, () -> ProjectionRuntimeSources.requireCurrentSnapshot(stale, "software-fixture", pins));
        Path alias = roleJar(true);
        assertThrows(IOException.class, () -> ProjectionRuntimeSources.requireCurrentSnapshot(snapshot(grant("event-source-facts")),
                "software-fixture", List.of(ControlBuild.FileRef.measure(alias))));
        Files.write(jar, new byte[] {1,2,3});
        assertThrows(IOException.class, () -> ProjectionRuntimeSources.requireCurrentSnapshot(
                snapshot(grant("event-source-facts")), "software-fixture", pins));
    }

    @Test void mutableConfiguredKnowledgeIsSeparateFromItsImmutableInitialHttpObservation() throws Exception {
        Path fixed = temporary.resolve("fixed-knowledge-manifest.json"), observed = temporary.resolve("initial-http.json");
        Files.writeString(fixed, "{\"schema\":\"xar.projection-evidence-grants/v1\",\"grants\":[]}");
        Files.write(observed, ControlBuild.strictMapper().writeValueAsBytes(snapshot(grant("event-source-facts"))));
        var provenance = new ProjectionRuntimeSources.ConfiguredManifest(fixed.toString(), ControlBuild.FileRef.measure(observed), 1);
        Files.writeString(fixed, "{\"new\":\"offline publication changes this knowledge source\"}");
        provenance.initialSnapshotRef().verify();
        assertEquals(fixed.toString(), provenance.manifestPath());
        assertEquals(provenance, ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(provenance),
                ProjectionRuntimeSources.ConfiguredManifest.class));
        Files.writeString(observed, "changed initial HTTP observation");
        assertThrows(IOException.class, provenance.initialSnapshotRef()::verify);
    }

    @Test void offlinePublishingRequiresAnExplicitSameMachineFixedRootContextBeyondPureProjection() throws Exception {
        Path state = Files.createDirectory(temporary.resolve("offline-state")), stock = Files.createDirectory(temporary.resolve("offline-stock"));
        Path incident = Files.createDirectory(temporary.resolve("incidents")), knowledge = Files.createDirectory(temporary.resolve("knowledge"));
        Path manifest = temporary.resolve("offline-grants.json");
        var pure = new MapAdmissionServiceOwner.Config(temporary.resolve("build.json"), temporary.resolve("work"), temporary.resolve("java.exe"),
                Instant.now().plusSeconds(120), 8089, state, stock, manifest);
        String machine = "software-fixture", now = Instant.now().toString();
        var mandatory = new ProjectionOfflineContext.MandatoryReviews(state.resolve("evidence/unknown-mandatory-choice-reviews").toString(), manifest.toString());
        var uiContext = new ProjectionOfflineContext.Context("xar.offline-event-analysis-context/v1", machine, now, mandatory, null);
        assertThrows(IOException.class, () -> ProjectionOfflineContext.requireExpected(pure, machine, uiContext));
        var ui = new MapAdmissionServiceOwner.Config(pure.buildReceipt(), pure.workRoot(), pure.javaExecutable(), pure.leaseDeadline(), 8089,
                state, stock, manifest, new ProjectionOfflineContext.Publishing(null, null));
        ProjectionOfflineContext.requireExpected(ui, machine, uiContext);
        assertThrows(IOException.class, () -> ProjectionOfflineContext.requireExpected(ui, "other-machine", uiContext));
        assertThrows(IOException.class, () -> ProjectionOfflineContext.requireExpected(ui, machine,
                new ProjectionOfflineContext.Context(uiContext.schema(), machine, now,
                        new ProjectionOfflineContext.MandatoryReviews(knowledge.toString(), manifest.toString()), null)));
        var both = new MapAdmissionServiceOwner.Config(pure.buildReceipt(), pure.workRoot(), pure.javaExecutable(), pure.leaseDeadline(), 8089,
                state, stock, manifest, new ProjectionOfflineContext.Publishing(incident, knowledge));
        var batchContext = new ProjectionOfflineContext.Context(uiContext.schema(), machine, now, mandatory,
                new ProjectionOfflineContext.EventBatches(incident.toString(), knowledge.toString(), manifest.toString()));
        ProjectionOfflineContext.requireExpected(both, machine, batchContext);
        assertThrows(IOException.class, () -> ProjectionOfflineContext.requireExpected(ui, machine, batchContext));
        assertThrows(IllegalArgumentException.class, () -> new MapAdmissionServiceOwner.Config(pure.buildReceipt(), pure.workRoot(),
                pure.javaExecutable(), pure.leaseDeadline(), 8089, state, stock, null, new ProjectionOfflineContext.Publishing(null, null)));
        assertThrows(IllegalArgumentException.class, () -> new MapAdmissionServiceOwner.Config(pure.buildReceipt(), pure.workRoot(),
                pure.javaExecutable(), pure.leaseDeadline(), 8089, state, stock, stock.resolve("forbidden-write.json"), null));
        String raw = ControlBuild.strictMapper().writeValueAsString(uiContext);
        assertThrows(JsonProcessingException.class, () -> ControlBuild.strictMapper().readValue(
                raw.replace(",\"event_batches\":null", ""), ProjectionOfflineContext.Context.class));
    }

    private ProjectionRuntimeSources.EvidenceGrant grant(String role) {
        return new ProjectionRuntimeSources.EvidenceGrant(role, temporary.resolve("declared-evidence.json").toString(),
                12, "0".repeat(64), "unknown");
    }

    private static ProjectionRuntimeSources.GrantsSnapshot snapshot(ProjectionRuntimeSources.EvidenceGrant grant) {
        return new ProjectionRuntimeSources.GrantsSnapshot("xar.projection-host-evidence-grants/v1", "software-fixture",
                Instant.now().toString(), List.of(grant));
    }

    private Path roleJar(boolean aliases) throws Exception {
        Path root = Files.createTempDirectory(temporary, "actual-role-"), source = root.resolve("ProjectionEvidenceRole.java");
        Path classes = Files.createDirectory(root.resolve("classes"));
        Files.writeString(source, "package org.xar.ck3.control.contracts.projection; public enum ProjectionEvidenceRole { "
                + (aliases ? "FIRST,SECOND" : "FIRST")
                + "; public String wire(){return \"event-source-facts\";} }");
        var compiler = ToolProvider.getSystemJavaCompiler(); assertNotNull(compiler, "actual JDK required, no skipped fixture");
        assertEquals(0, compiler.run(null, null, null, "--release", "21", "-d", classes.toString(), source.toString()));
        Path result = root.resolve("actual-shared-role.jar");
        try (JarOutputStream jar = new JarOutputStream(Files.newOutputStream(result))) {
            jar.putNextEntry(new JarEntry(ROLE.replace('.', '/') + ".class"));
            jar.write(Files.readAllBytes(classes.resolve(ROLE.replace('.', '/') + ".class"))); jar.closeEntry();
        }
        return result;
    }
}
