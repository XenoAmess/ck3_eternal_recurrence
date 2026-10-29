package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.jar.Attributes;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;
import java.util.jar.Manifest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Real caller/codec/native Job evidence, without claiming a qualified Quarkus Session or HTTP authority. */
public final class MapAdmissionServiceOwnerUtf8Test {
    private static final String MACHINE = WindowsJobProcess.currentMachineId();

    @Test
    void admittedAsciiCommandRemainsTheIdenticalDirectCommandWithoutNewEvidence(@TempDir Path temporary) throws Exception {
        Path root = asciiRoot(temporary);
        var logical = command(root, root.resolve("quarkus-run.jar"), List.of("-Dxar.example=ascii"));
        var prepared = MapAdmissionServiceOwner.prepareJavaServiceInvocation(logical, MACHINE,
                root.resolve("not-created-output"), root.resolve("not-created-logs"));
        assertSame(logical, prepared.command());
        assertTrue(prepared.evidenceRef().isEmpty());
        assertTrue(prepared.logicalRequest().isEmpty());
        assertSame(prepared, prepared.withStartedPreparation(0));
        assertTrue(prepared.preparationRef().isEmpty());
        prepared.verify();
        assertFalse(Files.exists(root.resolve("not-created-output")));
        assertFalse(Files.exists(root.resolve("not-created-logs")));
    }

    @Test
    void unicodeJarAndPropertiesRoundtripThroughSoleEngineAndKeepOriginalJobContext(@TempDir Path temporary) throws Exception {
        var fixture = fixture(temporary);
        String text = "原生请求 𠀀 = C:\\目录\\回执 \"quoted\"\nline2";
        var logical = command(fixture.root(), fixture.jar(), List.of("-Dxar.example=" + text,
                "-Dquarkus.http.host=127.0.0.1", "-Dquarkus.http.port=28089", "-Dxar.empty="));
        var prepared = MapAdmissionServiceOwner.prepareJavaServiceInvocation(logical, MACHINE, fixture.root(), fixture.logs());
        var physical = prepared.command();
        assertNotEquals(logical.arguments(), physical.arguments());
        assertTrue(physical.arguments().stream().allMatch(MapAdmissionServiceOwnerUtf8Test::ascii));
        assertEquals(logical.executable(), physical.executable());
        assertEquals(logical.cwd(), physical.cwd());
        assertEquals(logical.environment(), physical.environment());
        assertEquals(logical.stdout(), physical.stdout());
        assertEquals(logical.stderr(), physical.stderr());
        assertEquals(logical.memoryLimitBytes(), physical.memoryLimitBytes());
        for (String option : List.of("-Xms32m", "-Xmx256m", "-XX:MaxMetaspaceSize=96m",
                "-XX:ReservedCodeCacheSize=48m", "-XX:MaxDirectMemorySize=32m", "-Xss512k",
                "-Djava.io.tmpdir=" + fixture.root().resolve("scratch"), "-Djna.tmpdir=" + fixture.root().resolve("scratch")))
            assertTrue(physical.arguments().contains(option), "original JVM startup setting must survive: " + option);
        assertFalse(physical.arguments().contains("-jar"), "the sole engine invokes the same-JVM Jar main");
        var request = prepared.logicalRequest().orElseThrow();
        assertTrue(request.target() instanceof CiBootstrap.JavaUtf8Invocation.JarTarget);
        var jar = (CiBootstrap.JavaUtf8Invocation.JarTarget) request.target();
        assertEquals(fixture.jar().toRealPath().toString(), jar.jar().path());
        assertEquals(FixtureMain.class.getName(), jar.mainClass());
        assertTrue(jar.manifestClasspath().stream().anyMatch(pin ->
                pin instanceof CiBootstrap.JavaUtf8Invocation.FileClasspath file
                        && file.file().path().equals(fixture.dependency().toString())));
        assertEquals(List.of(new CiBootstrap.JavaUtf8Invocation.Property("xar.example", text),
                new CiBootstrap.JavaUtf8Invocation.Property("quarkus.http.host", "127.0.0.1"),
                new CiBootstrap.JavaUtf8Invocation.Property("quarkus.http.port", "28089"),
                new CiBootstrap.JavaUtf8Invocation.Property("xar.empty", "")), request.properties());
        assertEquals(List.of(), request.arguments());
        var evidenceRef = prepared.evidenceRef().orElseThrow(); evidenceRef.verify();
        byte[] evidenceBytes = Files.readAllBytes(Path.of(evidenceRef.path()));
        var evidence = MapAdmissionServiceOwner.readJavaInvocationEvidence(evidenceBytes);
        assertEquals(MACHINE, evidence.machineId());
        assertEquals(logical.arguments(), evidence.logicalArguments());
        assertEquals(physical.arguments(), evidence.physicalArguments());
        assertEquals(ControlBuild.FileRef.measure(logical.executable()), evidence.javaExecutable());
        SharedSourceFiles.assertUnchanged(evidence.logicalRequest());
        var publication = new CiBootstrap.JavaUtf8Invocation.Publication(CiBootstrap.JavaUtf8Invocation.captureFile(
                Path.of(evidence.logicalRequest().source().path())));
        assertEquals(request, CiBootstrap.JavaUtf8Invocation.read(publication));
        assertFalse(new String(evidenceBytes, java.nio.charset.StandardCharsets.UTF_8).contains("jdk_metadata"));
        assertEquals(evidence, MapAdmissionServiceOwner.readJavaInvocationEvidence(
                ControlBuild.strictMapper().writeValueAsBytes(evidence)));
        assertTrue(prepared.preparationRef().isEmpty());
        assertThrows(IOException.class, () -> prepared.withStartedPreparation(0),
                "an invocation envelope cannot stand in for the original child preparation receipt");
        prepared.verify();
    }

    @Test
    void bothRequestAndOuterEvidenceAreReopenedAndRejectRealFileDrift(@TempDir Path temporary) throws Exception {
        var first = fixture(temporary.resolve("envelope")); var one = prepare(first);
        var evidence = MapAdmissionServiceOwner.readJavaInvocationEvidence(Files.readAllBytes(Path.of(one.evidenceRef().orElseThrow().path())));
        Files.write(Path.of(evidence.logicalRequest().source().path()), new byte[] {1}, StandardOpenOption.APPEND);
        assertThrows(IOException.class, one::verify);
        var second = fixture(temporary.resolve("evidence")); var two = prepare(second);
        Files.write(Path.of(two.evidenceRef().orElseThrow().path()), new byte[] {32}, StandardOpenOption.APPEND);
        assertThrows(IOException.class, two::verify);
        var third = fixture(temporary.resolve("target")); var three = prepare(third);
        Files.write(third.jar(), new byte[] {32}, StandardOpenOption.APPEND);
        assertThrows(IOException.class, three::verify);
        var fourth = fixture(temporary.resolve("dependency")); var four = prepare(fourth);
        Files.write(fourth.dependency(), new byte[] {32}, StandardOpenOption.APPEND);
        assertThrows(IOException.class, four::verify);
    }

    @Test
    void strictEvidenceConsumerRejectsUnknownMissingWrongTypeAndOversize(@TempDir Path temporary) throws Exception {
        var fixture = fixture(temporary); var prepared = prepare(fixture);
        byte[] actual = Files.readAllBytes(Path.of(prepared.evidenceRef().orElseThrow().path()));
        var mapper = ControlBuild.strictMapper();
        var unknown = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(actual);
        unknown.put("not_original", 1);
        assertThrows(IOException.class, () -> MapAdmissionServiceOwner.readJavaInvocationEvidence(mapper.writeValueAsBytes(unknown)));
        var missing = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(actual);
        missing.remove("logical_request");
        assertThrows(IOException.class, () -> MapAdmissionServiceOwner.readJavaInvocationEvidence(mapper.writeValueAsBytes(missing)));
        var wrong = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(actual);
        wrong.put("logical_arguments", false);
        assertThrows(IOException.class, () -> MapAdmissionServiceOwner.readJavaInvocationEvidence(mapper.writeValueAsBytes(wrong)));
        assertThrows(IOException.class, () -> MapAdmissionServiceOwner.readJavaInvocationEvidence(
                new byte[MapAdmissionServiceOwner.MAX_SMALL_RECEIPT_BYTES + 1]));
    }

    @Test
    void startupUnicodeUnsupportedEntryAndExistingPublicationRejectBeforeAnyStart(@TempDir Path temporary) throws Exception {
        var fixture = fixture(temporary);
        var unicodeStartup = command(fixture.root(), fixture.jar(), List.of("-Djava.io.tmpdir=目录"));
        assertThrows(IOException.class, () -> MapAdmissionServiceOwner.prepareJavaServiceInvocation(
                unicodeStartup, MACHINE, fixture.root(), fixture.logs()));
        assertFalse(Files.exists(fixture.logs().resolve("service-java-invocation.bin")));
        var withApplicationArgument = new ArrayList<>(command(fixture.root(), fixture.jar(), List.of()).arguments());
        withApplicationArgument.add("unexpected");
        var unsupported = withArguments(command(fixture.root(), fixture.jar(), List.of()), withApplicationArgument);
        assertThrows(IOException.class, () -> MapAdmissionServiceOwner.prepareJavaServiceInvocation(
                unsupported, MACHINE, fixture.root(), fixture.logs()));
        var prepared = prepare(fixture);
        assertThrows(IOException.class, () -> prepare(fixture));
        prepared.verify(); // CREATE_NEW refusal must leave the original successful publication intact.
    }

    @Test
    void outputOwnerAndOriginalSixteenMiBBudgetGuardTheEnvelope(@TempDir Path temporary) throws Exception {
        var outside = fixture(temporary.resolve("outside")); Path foreignLogs = Files.createDirectories(temporary.resolve("foreign-logs"));
        assertThrows(IOException.class, () -> MapAdmissionServiceOwner.prepareJavaServiceInvocation(
                command(outside.root(), outside.jar(), List.of()), MACHINE, outside.root(), foreignLogs));
        var full = fixture(temporary.resolve("full"));
        try (var file = new java.io.RandomAccessFile(full.root().resolve("existing-output.bin").toFile(), "rw")) {
            file.setLength(16L << 20);
        }
        assertThrows(IOException.class, () -> prepare(full));
        assertFalse(Files.exists(full.logs().resolve("service-java-invocation.bin")));
    }

    @Test
    void realNonzeroJobKeepsNativeCustodyAndRoundtripsTerminalSourcesWithoutGrantingServiceReadiness(@TempDir Path temporary) throws Exception {
        var produced = actualFailedJob(fixture(temporary));
        assertEquals(42, produced.evidence().terminal().exitCode());
        assertEquals(0, produced.evidence().terminal().accounting().activeProcesses());
        assertTrue(produced.prepared().preparationRef().isPresent(), "PREPARED exists even when actual main failed");
        SharedSourceFiles.assertUnchanged(produced.terminal());
        byte[] raw = Files.readAllBytes(Path.of(produced.terminal().source().path()));
        assertEquals(produced.evidence(), JavaUtf8NativeCustody.decodeEvidence(raw));
        assertEquals(produced.evidence(), produced.invocation().readNativeEvidence(raw));
        var encoded = JavaUtf8NativeCustody.encodeEvidence(produced.evidence());
        assertEquals(produced.evidence(), produced.invocation().readNativeEvidence(encoded));
        var commandEvidence = MapAdmissionServiceOwner.readJavaInvocationEvidence(Files.readAllBytes(
                Path.of(produced.invocation().evidenceRef().orElseThrow().path())));
        var prepReceipt = produced.prepared().preparedReceiptRef().orElseThrow(); prepReceipt.verify();
        var prep = MapAdmissionServiceOwner.readJavaPreparedEvidence(Files.readAllBytes(Path.of(prepReceipt.path())), commandEvidence);
        assertEquals(produced.prepared().preparationRef().orElseThrow(), prep.preparation());
        assertEquals(prep, MapAdmissionServiceOwner.readJavaPreparedEvidence(ControlBuild.strictMapper().writeValueAsBytes(prep), commandEvidence));
        produced.prepared().verify();
    }

    @Test
    void actualColdConsumerRejectsForeignMachineNativeIdWrongTerminalTypeAndSameBytesReplacement(@TempDir Path temporary) throws Exception {
        var produced = actualFailedJob(fixture(temporary));
        byte[] raw = JavaUtf8NativeCustody.encodeEvidence(produced.evidence());
        var mapper = ControlBuild.strictMapper();
        var foreign = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(raw);
        foreign.put("machine_id", "foreign-machine-for-cold-read-negative");
        assertThrows(IOException.class, () -> produced.invocation().readNativeEvidence(mapper.writeValueAsBytes(foreign)));
        var identity = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(raw);
        var nativeFile = (com.fasterxml.jackson.databind.node.ObjectNode) identity.path("files").get(0).path("native_file");
        String currentId = nativeFile.path("file_id_decimal").textValue();
        nativeFile.put("file_id_decimal", "1".equals(currentId) ? "2" : "1");
        assertThrows(IOException.class, () -> produced.invocation().readNativeEvidence(mapper.writeValueAsBytes(identity)));
        var wrongType = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(raw);
        ((com.fasterxml.jackson.databind.node.ObjectNode) wrongType.path("terminal")).put("exit_code", false);
        assertThrows(IOException.class, () -> produced.invocation().readNativeEvidence(mapper.writeValueAsBytes(wrongType)));
        var missing = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(raw); missing.remove("terminal");
        assertThrows(IOException.class, () -> produced.invocation().readNativeEvidence(mapper.writeValueAsBytes(missing)));
        var unknown = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(raw); unknown.put("not_original", 1);
        assertThrows(IOException.class, () -> produced.invocation().readNativeEvidence(mapper.writeValueAsBytes(unknown)));
        assertThrows(IOException.class, () -> produced.invocation().readNativeEvidence(new byte[JavaUtf8NativeCustody.MAXIMUM_EVIDENCE_BYTES + 1]));
        var commandEvidence = MapAdmissionServiceOwner.readJavaInvocationEvidence(Files.readAllBytes(
                Path.of(produced.invocation().evidenceRef().orElseThrow().path())));
        byte[] prepRaw = Files.readAllBytes(Path.of(produced.prepared().preparedReceiptRef().orElseThrow().path()));
        var wrongPrep = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(prepRaw); wrongPrep.remove("preparation");
        assertThrows(IOException.class, () -> MapAdmissionServiceOwner.readJavaPreparedEvidence(mapper.writeValueAsBytes(wrongPrep), commandEvidence));
        var foreignPrep = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(prepRaw); foreignPrep.put("machine_id", "foreign-machine");
        assertThrows(IOException.class, () -> MapAdmissionServiceOwner.readJavaPreparedEvidence(mapper.writeValueAsBytes(foreignPrep), commandEvidence));
        var mixedJdkPin = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(prepRaw);
        ((com.fasterxml.jackson.databind.node.ObjectNode) mixedJdkPin.path("preparation")).putObject("jdk_metadata");
        assertThrows(IOException.class, () -> MapAdmissionServiceOwner.readJavaPreparedEvidence(mapper.writeValueAsBytes(mixedJdkPin), commandEvidence));
        Path envelope = Path.of(commandEvidence.logicalRequest().source().path()); byte[] same = Files.readAllBytes(envelope);
        Files.move(envelope, envelope.resolveSibling("original-replaced-envelope.bin"));
        Files.write(envelope, same, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        assertNotEquals(commandEvidence.logicalRequest().nativeFile().identityKey(), SharedSourceFiles.observe(envelope).nativeFile().identityKey());
        assertThrows(IOException.class, produced.prepared()::verify);
        assertThrows(IOException.class, () -> produced.invocation().readNativeEvidence(raw));
    }

    private static Produced actualFailedJob(Fixture fixture) throws Exception {
        var invocation = MapAdmissionServiceOwner.prepareJavaServiceInvocation(
                command(fixture.root(), fixture.jar(), List.of("-Dxar.fixture.exit=42")), MACHINE, fixture.root(), fixture.logs());
        try (var sources = invocation.acquireNativeSources(fixture.root(), fixture.logs())) {
            sources.requireCurrent();
            assertThrows(IOException.class, () -> Files.write(fixture.jar(), new byte[] {1}, StandardOpenOption.APPEND));
            Path envelope = Path.of(MapAdmissionServiceOwner.readJavaInvocationEvidence(Files.readAllBytes(
                    Path.of(invocation.evidenceRef().orElseThrow().path()))).logicalRequest().source().path());
            assertThrows(IOException.class, () -> Files.write(envelope, new byte[] {1}, StandardOpenOption.APPEND));
            try (var child = WindowsJobProcess.start(invocation.command())) {
                sources.attach(child);
                var result = child.await(Duration.ofSeconds(20), Instant.now().plusSeconds(30), sources.guard(() -> {}));
                assertEquals(42, result.exitCode()); assertEquals(0, result.accounting().activeProcesses());
                sources.settle(result);
                assertThrows(IOException.class, () -> sources.settle(result), "actual terminal cannot be consumed twice");
                var prepared = invocation.withStartedPreparation(sources.reservedOutputBytes());
                return new Produced(invocation, prepared, sources.terminalEvidenceRef().orElseThrow(), sources.readTerminalEvidence());
            }
        }
    }
    private record Produced(MapAdmissionServiceOwner.ServiceJavaInvocation invocation,
            MapAdmissionServiceOwner.ServiceJavaInvocation prepared, SharedSourceFiles.Witness terminal,
            JavaUtf8NativeCustody.Evidence evidence) {}

    private static MapAdmissionServiceOwner.ServiceJavaInvocation prepare(Fixture fixture) throws IOException {
        return MapAdmissionServiceOwner.prepareJavaServiceInvocation(command(fixture.root(), fixture.jar(), List.of()),
                MACHINE, fixture.root(), fixture.logs());
    }

    private static WindowsJobProcess.CommandSpec command(Path root, Path jar, List<String> properties) {
        var arguments = new ArrayList<>(List.of("-Xms32m", "-Xmx256m", "-XX:MaxMetaspaceSize=96m",
                "-XX:ReservedCodeCacheSize=48m", "-XX:MaxDirectMemorySize=32m", "-Xss512k",
                "-Djava.io.tmpdir=" + root.resolve("scratch"), "-Djna.tmpdir=" + root.resolve("scratch")));
        arguments.addAll(properties); arguments.add("-jar"); arguments.add(jar.toString());
        Path executable = Path.of(ProcessHandle.current().info().command().orElseThrow()).toAbsolutePath();
        return new WindowsJobProcess.CommandSpec(executable, arguments, root,
                Map.of("TEMP", root.resolve("scratch").toString(), "TMP", root.resolve("scratch").toString(),
                        "XAR_TEST_VALUE", "原环境𠀀"), root.resolve("service.stdout.log"), root.resolve("service.stderr.log"), 512L << 20);
    }

    private static WindowsJobProcess.CommandSpec withArguments(WindowsJobProcess.CommandSpec original, List<String> arguments) {
        return new WindowsJobProcess.CommandSpec(original.executable(), arguments, original.cwd(), original.environment(),
                original.stdout(), original.stderr(), original.memoryLimitBytes());
    }

    private static Path asciiRoot(Path temporary) throws IOException {
        Path root = Files.createDirectories(temporary).toRealPath();
        assertTrue(ascii(root.toString()), "CI must supply the caller's already admitted ASCII evidence/carrier roots");
        return root;
    }

    private static Fixture fixture(Path temporary) throws IOException {
        Path root = asciiRoot(temporary), logs = Files.createDirectories(root.resolve("logs"));
        Files.createDirectories(root.resolve("scratch"));
        Path deployment = Files.createDirectories(root.resolve("部署 模块-𠀀"));
        Path dependency = Files.createDirectories(deployment.resolve("lib")).resolve("dependency.jar");
        try (var output = new JarOutputStream(Files.newOutputStream(dependency, StandardOpenOption.CREATE_NEW))) {
            output.putNextEntry(new JarEntry("original.txt")); output.write(new byte[] {1, 2, 3}); output.closeEntry();
        }
        Path jar = deployment.resolve("quarkus-run.jar");
        var manifest = new Manifest(); manifest.getMainAttributes().put(Attributes.Name.MANIFEST_VERSION, "1.0");
        manifest.getMainAttributes().put(Attributes.Name.MAIN_CLASS, FixtureMain.class.getName());
        manifest.getMainAttributes().put(Attributes.Name.CLASS_PATH, "lib/dependency.jar");
        try (var output = new JarOutputStream(Files.newOutputStream(jar, StandardOpenOption.CREATE_NEW), manifest)) {
            String entry = FixtureMain.class.getName().replace('.', '/') + ".class";
            output.putNextEntry(new JarEntry(entry));
            try (var input = FixtureMain.class.getResourceAsStream("/" + entry)) {
                if (input == null) throw new IOException("actual compiled fixture main bytes unavailable");
                input.transferTo(output);
            }
            output.closeEntry();
        }
        return new Fixture(root, logs, jar.toRealPath(), dependency.toRealPath());
    }
    private static boolean ascii(String text) { return text.chars().allMatch(character -> character <= 127); }
    private record Fixture(Path root, Path logs, Path jar, Path dependency) {}

    /** Genuine finite child main for source-continuity regression; it never provides Quarkus/HTTP readiness. */
    public static final class FixtureMain {
        public static void main(String[] arguments) {
            if ("42".equals(System.getProperty("xar.fixture.exit"))) System.exit(42);
            throw new IllegalStateException("no qualified Quarkus/HTTP fixture");
        }
    }
}
