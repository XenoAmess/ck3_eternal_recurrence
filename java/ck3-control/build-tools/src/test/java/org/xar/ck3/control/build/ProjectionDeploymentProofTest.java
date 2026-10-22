package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.core.JsonProcessingException;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;
import javax.tools.ToolProvider;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Actual JDK-compiled, packaged fixtures; never substitutes a live-host or native-game qualification. */
final class ProjectionDeploymentProofTest {
    @TempDir Path temporary;
    private static final String PROVIDER = "org.fixture.ActualCatalog";

    private record Fixture(Path sourceRoot, Path providerSource, Path descriptorSource, Path providerJar,
            Path enumJar, List<ControlBuild.FileRef> sources, List<ControlBuild.FileRef> deployment) {}

    @Test void actualPackagedProviderBindsSourceDescriptorClassJarDigestAndSharedCompiledEnum() throws Exception {
        Fixture fixture = fixture(false);
        var proof = attest(fixture, inventory(fixture, PROVIDER, fixture.providerJar(), profile("sample-operation")));
        assertEquals(1, proof.catalogs().size());
        var catalog = proof.catalogs().getFirst();
        assertEquals(ControlBuild.FileRef.measure(fixture.providerJar()), catalog.artifactRef());
        assertEquals(ControlBuild.FileRef.measure(fixture.descriptorSource()).sha256(), catalog.packagedDescriptorSha256());
        assertEquals(ControlBuild.FileRef.measure(fixture.providerSource()), catalog.providerSourceRef());
        var mapper = ControlBuild.strictMapper();
        assertEquals(proof, mapper.readValue(mapper.writeValueAsBytes(proof), ProjectionDeploymentProof.Attestation.class));
    }

    @Test void actualDescriptorCannotDropProviderThatRemainsInTheExactSourceDescriptor() throws Exception {
        Fixture fixture = fixture(false);
        Files.writeString(fixture.descriptorSource(), PROVIDER + "\norg.fixture.OmittedProvider\n");
        Fixture changed = new Fixture(fixture.sourceRoot(), fixture.providerSource(), fixture.descriptorSource(),
                fixture.providerJar(), fixture.enumJar(), sourcePins(fixture.sourceRoot()), fixture.deployment());
        assertThrows(IOException.class, () -> attest(changed, inventory(changed, PROVIDER, changed.providerJar(), profile("sample-operation"))));
    }

    @Test void actualCatalogOriginCannotPointAtAnotherQualifiedJar() throws Exception {
        Fixture fixture = fixture(false);
        assertThrows(IOException.class, () -> attest(fixture, inventory(fixture, PROVIDER, fixture.enumJar(), profile("sample-operation"))));
        assertThrows(IOException.class, () -> attest(fixture, inventory(fixture, "org.fixture.AliasCatalog", fixture.providerJar(), profile("sample-operation"))));
    }

    @Test void duplicateProviderAcrossRealPackagedJarsAndMissingDescriptorAreRejected() throws Exception {
        Fixture fixture = fixture(false);
        Path duplicate = temporary.resolve("duplicate-provider.jar"); Files.copy(fixture.providerJar(), duplicate);
        var duplicateFiles = new ArrayList<>(fixture.deployment()); duplicateFiles.add(ControlBuild.FileRef.measure(duplicate));
        assertThrows(IOException.class, () -> ProjectionDeploymentProof.attestClosure(fixture.sourceRoot(), fixture.sources(), duplicateFiles,
                identity(profile("sample-operation")), inventory(fixture, PROVIDER, fixture.providerJar(), profile("sample-operation"))));
        assertThrows(IOException.class, () -> ProjectionDeploymentProof.attestClosure(fixture.sourceRoot(), fixture.sources(),
                List.of(ControlBuild.FileRef.measure(fixture.enumJar())), identity(profile("sample-operation")),
                inventory(fixture, PROVIDER, fixture.providerJar(), profile("sample-operation"))));
    }

    @Test void sharedCompiledEnumRejectsUnknownOperationsAndAliasedWires() throws Exception {
        Fixture fixture = fixture(false);
        assertThrows(IOException.class, () -> attest(fixture, inventory(fixture, PROVIDER, fixture.providerJar(), profile("unknown-operation"))));
        Fixture aliases = fixture(true);
        assertThrows(IOException.class, () -> attest(aliases, inventory(aliases, PROVIDER, aliases.providerJar(), profile("sample-operation"))));
        var mismatched = inventory(fixture, PROVIDER, fixture.providerJar(), new ProjectionDeploymentProof.OperationProfile("sample-operation", 7, 9));
        assertThrows(IOException.class, () -> ProjectionDeploymentProof.attestClosure(fixture.sourceRoot(), fixture.sources(), fixture.deployment(),
                identity(profile("sample-operation")), mismatched));
    }

    @Test void actualSourceAndArtifactTamperingRemainFailuresAfterFixtureProduction() throws Exception {
        Fixture source = fixture(false);
        Files.writeString(source.providerSource(), "package org.fixture; public class ActualCatalog { int changed; }\n");
        assertThrows(IOException.class, () -> attest(source, inventory(source, PROVIDER, source.providerJar(), profile("sample-operation"))));
        Fixture artifact = fixture(false);
        Files.write(artifact.providerJar(), new byte[] {1, 2, 3});
        assertThrows(IOException.class, () -> attest(artifact, inventory(artifact, PROVIDER, artifact.providerJar(), profile("sample-operation"))));
    }

    @Test void strictIdentityAndDescriptorBoundariesRejectCoercionUnknownFieldsAndAliases() throws Exception {
        var mapper = ControlBuild.strictMapper();
        String body = mapper.writeValueAsString(identity(profile("sample-operation")));
        for (String token : List.of("true", "1.0", "\"65536\"", "null")) {
            assertThrows(JsonProcessingException.class, () -> mapper.readValue(body.replace("\"input_max_bytes\":65536",
                    "\"input_max_bytes\":" + token), ProjectionDeploymentProof.Identity.class));
        }
        assertThrows(JsonProcessingException.class, () -> mapper.readValue(body.replace("\"envelope_max_bytes\":8392704",
                "\"envelope_max_bytes\":8392704,\"alias\":true"), ProjectionDeploymentProof.Identity.class));
        for (String invalid : List.of("", PROVIDER + "\n" + PROVIDER, "alias=" + PROVIDER, "# ignored alias\n" + PROVIDER, "\ufeff" + PROVIDER)) {
            assertThrows(IOException.class, () -> ProjectionDeploymentProof.parseDescriptor(invalid.getBytes(StandardCharsets.UTF_8)));
        }
        assertThrows(IOException.class, () -> ProjectionDeploymentProof.parseDescriptor(new byte[] {(byte) 0xff}));
    }

    @Test void projectionRunningHasItsOwnHalfMiBBudgetWhileLegacyMapStaysAt64KiB() throws Exception {
        Path source = temporary.resolve("measured.java"); Files.writeString(source, "source");
        var first = ControlBuild.FileRef.measure(source);
        List<ControlBuild.FileRef> sources = new ArrayList<>();
        for (int index = 0; index < 512; index++) {
            Path path = temporary.resolve("source-" + index + ".java"); Files.writeString(path, "source");
            sources.add(ControlBuild.FileRef.measure(path));
        }
        var context = new MapAdmissionServiceOwner.HostContext("xar.projection-host-context/v1", "software-fixture", Instant.now().toString(), null);
        Path contextPath = temporary.resolve("context.json"); Files.write(contextPath, ControlBuild.strictMapper().writeValueAsBytes(context));
        var observed = new MapAdmissionServiceOwner.ObservedHostContext(context, ControlBuild.FileRef.measure(contextPath));
        var receipt = new MapAdmissionServiceOwner.ProjectionRunningReceipt("xar.java-projection-service-running/v1", "software-fixture",
                Instant.now().toString(), "ACTUAL_RUNNING", ProjectionDeploymentProof.PRODUCER, ProjectionDeploymentProof.VERSION,
                "http://127.0.0.1:8089/v1/projections/call", first, sources,
                new MapAdmissionServiceOwner.ProcessWire(1, "18446744073709551615", first.path()), observed);
        assertThrows(IOException.class, () -> MapAdmissionServiceOwner.publish(temporary.resolve("legacy-map.json"), receipt));
        var produced = MapAdmissionServiceOwner.publishProjectionRunning(temporary.resolve("projection.json"), receipt);
        assertTrue(produced.bytes() > 65536); assertTrue(produced.bytes() <= 524288); produced.verify();
        assertEquals(receipt, ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(produced.path())),
                MapAdmissionServiceOwner.ProjectionRunningReceipt.class));
        String missing = ControlBuild.strictMapper().writeValueAsString(receipt).replace(
                ",\"host_context\":" + ControlBuild.strictMapper().writeValueAsString(observed), "");
        assertThrows(JsonProcessingException.class, () -> ControlBuild.strictMapper().readValue(missing, MapAdmissionServiceOwner.ProjectionRunningReceipt.class));
        assertThrows(IllegalArgumentException.class, () -> new MapAdmissionServiceOwner.ProjectionRunningReceipt(
                receipt.schema(), receipt.machineId(), receipt.observedAtUtc(), receipt.status(), receipt.producer(), receipt.producerVersion(),
                receipt.url(), first, List.of(first, first), receipt.process(), observed));
        Path rejected = temporary.resolve("too-large-projection.json");
        assertThrows(IOException.class, () -> MapAdmissionServiceOwner.publishProjectionRunning(rejected, "x".repeat(524289)));
        assertFalse(Files.exists(rejected));
    }


    @Test void explicitHostContextKeepsMissingNullAndTrustedRootsDistinct() throws Exception {
        Path state = Files.createDirectory(temporary.resolve("state")), stock = Files.createDirectory(temporary.resolve("stock"));
        var config = new MapAdmissionServiceOwner.Config(temporary.resolve("build.json"), temporary.resolve("work"), temporary.resolve("java.exe"),
                Instant.now().plusSeconds(300), 8089, state, stock);
        var roots = new MapAdmissionServiceOwner.EventSourceRoots(state.toString(), stock.toString());
        var context = new MapAdmissionServiceOwner.HostContext("xar.projection-host-context/v1", "software-fixture", Instant.now().toString(), roots);
        MapAdmissionServiceOwner.requireContext(config, "software-fixture", context);
        assertThrows(IOException.class, () -> MapAdmissionServiceOwner.requireContext(config, "other-machine", context));
        assertThrows(IOException.class, () -> MapAdmissionServiceOwner.requireContext(config, "software-fixture",
                new MapAdmissionServiceOwner.HostContext(context.schema(), context.machineId(), context.observedAtUtc(), null)));
        var mapper = ControlBuild.strictMapper();
        assertThrows(JsonProcessingException.class, () -> mapper.readValue(
                mapper.writeValueAsString(context).replace(",\"event_sources\":" + mapper.writeValueAsString(roots), ""),
                MapAdmissionServiceOwner.HostContext.class));
        assertThrows(IllegalArgumentException.class, () -> new MapAdmissionServiceOwner.Config(
                config.buildReceipt(), config.workRoot(), config.javaExecutable(), config.leaseDeadline(), 8089, state, null));
        var pure = new MapAdmissionServiceOwner.Config(config.buildReceipt(), config.workRoot(), config.javaExecutable(), config.leaseDeadline(), 8089);
        MapAdmissionServiceOwner.requireContext(pure, "software-fixture", new MapAdmissionServiceOwner.HostContext(
                context.schema(), context.machineId(), context.observedAtUtc(), null));
        assertThrows(IOException.class, () -> MapAdmissionServiceOwner.requireContext(pure, "software-fixture", context));
    }


    @Test void failedStartupPreservesActualCmdExitAndFinalJobZeroInTheOriginalOwnerReceipt() throws Exception {
        Path logs = Files.createDirectories(temporary.resolve("failed-owner/logs")), work = logs.getParent();
        Path command = Path.of(System.getenv("SystemRoot"), "System32/cmd.exe");
        var config = new MapAdmissionServiceOwner.Config(temporary.resolve("build.json"), work, command,
                Instant.now().plusSeconds(120), 8089);
        String machine = WindowsJobProcess.currentMachineId();
        Path batch = work.resolve("exit-41.cmd");
        Files.writeString(batch, "@echo off\r\nexit /b 41\r\n", StandardCharsets.US_ASCII,
                java.nio.file.StandardOpenOption.CREATE_NEW);
        try (WindowsJobProcess child = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(command,
                List.of("/d", "/c", batch.toString()), work, java.util.Map.copyOf(System.getenv()),
                logs.resolve("child.stdout"), logs.resolve("child.stderr"), 512L << 20))) {
            var terminal = child.await(java.time.Duration.ofSeconds(10), Instant.now().plusSeconds(15), () -> {});
            assertEquals(41, terminal.exitCode()); assertEquals(0, terminal.accounting().activeProcesses());
            MapAdmissionServiceOwner.closeFailedStartup(config, child, machine);
            var receipt = ControlBuild.strictMapper().readValue(Files.readAllBytes(logs.resolve("service-start-failed-closed.json")),
                    MapAdmissionServiceOwner.ClosedReceipt.class);
            assertEquals(machine, receipt.machineId()); assertEquals("START_FAILED_CLOSED", receipt.status());
            assertEquals(41, receipt.originalChildResult().exitCode()); assertEquals(0, receipt.jobActiveFinal());
            assertEquals(MapAdmissionServiceOwner.ProcessWire.from(child.identity()), receipt.originalProcess());
        }
    }

    private ProjectionDeploymentProof.Attestation attest(Fixture fixture, ProjectionDeploymentProof.CatalogInventory inventory) throws IOException {
        return ProjectionDeploymentProof.attestClosure(fixture.sourceRoot(), fixture.sources(), fixture.deployment(),
                identity(profile("sample-operation")), inventory);
    }

    private static ProjectionDeploymentProof.OperationProfile profile(String wire) {
        return new ProjectionDeploymentProof.OperationProfile(wire, 65536, 65536);
    }

    private static ProjectionDeploymentProof.Identity identity(ProjectionDeploymentProof.OperationProfile profile) {
        return new ProjectionDeploymentProof.Identity("xar.projection-host-identity/v1", ProjectionDeploymentProof.PRODUCER,
                ProjectionDeploymentProof.VERSION, ProjectionDeploymentProof.CALL_SCHEMA, ProjectionDeploymentProof.RESULT_SCHEMA,
                ProjectionDeploymentProof.MAX_ENVELOPE_BYTES, List.of(profile));
    }

    private static ProjectionDeploymentProof.CatalogInventory inventory(Fixture fixture, String provider, Path jar,
            ProjectionDeploymentProof.OperationProfile profile) {
        return new ProjectionDeploymentProof.CatalogInventory("xar.projection-host-catalogs/v1", "software-fixture",
                Instant.now().toString(), List.of(new ProjectionDeploymentProof.CatalogIdentity(provider, jar.toString(), List.of(profile))));
    }

    private Fixture fixture(boolean aliases) throws Exception {
        Path root = Files.createTempDirectory(temporary, "packaged-source-"), classes = Files.createDirectory(root.resolve("classes"));
        Path enumSource = root.resolve("contracts/src/main/java/org/xar/ck3/control/contracts/projection/ProjectionOperation.java");
        Files.createDirectories(enumSource.getParent());
        Files.writeString(enumSource, "package org.xar.ck3.control.contracts.projection; public enum ProjectionOperation { "
                + (aliases ? "FIRST,SECOND" : "FIRST") + "; public String wire(){return \"sample-operation\";} }\n");
        Path providerSource = root.resolve("fixture-domain/src/main/java/org/fixture/ActualCatalog.java");
        Files.createDirectories(providerSource.getParent()); Files.writeString(providerSource, "package org.fixture; public final class ActualCatalog {}\n");
        Path descriptor = root.resolve("fixture-domain/src/main/resources/" + ProjectionDeploymentProof.SERVICE_ENTRY);
        Files.createDirectories(descriptor.getParent()); Files.writeString(descriptor, PROVIDER + "\n");
        for (String module : List.of("contracts", "fixture-domain")) Files.writeString(root.resolve(module + "/pom.xml"),
                "<project xmlns=\"http://maven.apache.org/POM/4.0.0\"><modelVersion>4.0.0</modelVersion><artifactId>" + module + "</artifactId></project>");
        var compiler = ToolProvider.getSystemJavaCompiler(); assertNotNull(compiler, "actual JDK compiler required, no skip");
        assertEquals(0, compiler.run(null, null, null, "--release", "21", "-d", classes.toString(), enumSource.toString(), providerSource.toString()));
        Path enumJar = root.resolve("contracts.jar"), providerJar = root.resolve("fixture-domain.jar");
        try (JarOutputStream jar = new JarOutputStream(Files.newOutputStream(enumJar))) {
            entry(jar, ProjectionDeploymentProof.OPERATION_CLASS.replace('.', '/') + ".class",
                    Files.readAllBytes(classes.resolve(ProjectionDeploymentProof.OPERATION_CLASS.replace('.', '/') + ".class")));
        }
        try (JarOutputStream jar = new JarOutputStream(Files.newOutputStream(providerJar))) {
            entry(jar, PROVIDER.replace('.', '/') + ".class", Files.readAllBytes(classes.resolve(PROVIDER.replace('.', '/') + ".class")));
            entry(jar, ProjectionDeploymentProof.SERVICE_ENTRY, Files.readAllBytes(descriptor));
            entry(jar, "META-INF/maven/org.xar.ck3.control/fixture-domain/pom.properties",
                    "groupId=org.xar.ck3.control\nartifactId=fixture-domain\nversion=0.1.0-SNAPSHOT\n".getBytes(StandardCharsets.ISO_8859_1));
        }
        return new Fixture(root, providerSource, descriptor, providerJar, enumJar, sourcePins(root),
                List.of(ControlBuild.FileRef.measure(enumJar), ControlBuild.FileRef.measure(providerJar)));
    }

    private static List<ControlBuild.FileRef> sourcePins(Path root) throws IOException {
        try (var paths = Files.walk(root)) {
            List<ControlBuild.FileRef> refs = new ArrayList<>();
            for (Path path : paths.filter(Files::isRegularFile).filter(path -> path.toString().endsWith(".java")
                    || path.toString().endsWith("pom.xml") || path.toString().endsWith(ProjectionDeploymentProof.SERVICE_ENTRY.replace('/', java.io.File.separatorChar))).toList()) {
                refs.add(ControlBuild.FileRef.measure(path));
            }
            return List.copyOf(refs);
        }
    }

    private static void entry(JarOutputStream jar, String name, byte[] bytes) throws IOException {
        jar.putNextEntry(new JarEntry(name)); jar.write(bytes); jar.closeEntry();
    }
}
