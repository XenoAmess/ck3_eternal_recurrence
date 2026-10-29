package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Arrays;
import java.util.concurrent.atomic.AtomicInteger;
import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.TreeMap;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class MavenArgumentFileTest {
    @TempDir Path temporary;
    private Path root(String name) throws IOException { return Files.createDirectory(temporary.resolve(name)); }
    private static List<String> longArguments() {
        List<String> arguments = new ArrayList<>(); arguments.add("--batch-mode");
        for (int i = 0; i < 140; i++) arguments.add("-Dxar.argument." + i + "=" + "a".repeat(64));
        arguments.add("-DargLine=-Xms32m -Xmx256m"); arguments.add("verify"); return List.copyOf(arguments);
    }
    @Test void longRealBatchUsesExactFrozenConfigAndPreservesOriginalConfig() throws Exception {
        Path source = root("source"), compiled = root("compiler");
        Files.createDirectories(source.resolve(".mvn")); Files.createDirectories(compiled.resolve(".mvn"));
        String original = "# existing Maven user property\n-Dexisting.property=two words\n";
        Files.writeString(source.resolve(MavenArgumentFile.CONFIG), original);
        Files.copy(source.resolve(MavenArgumentFile.CONFIG), compiled.resolve(MavenArgumentFile.CONFIG));
        var originalRef = ControlBuild.FileRef.measure(source.resolve(MavenArgumentFile.CONFIG));
        var arguments = longArguments(); assertTrue(MavenArgumentFile.required(null, arguments));
        MavenArgumentFile.prepare(source, compiled, null, arguments);
        var manifest = MavenArgumentFile.readManifest(compiled, arguments);
        assertEquals(originalRef, manifest.sourceConfigRef()); assertEquals(arguments, manifest.arguments());
        assertEquals(List.of("-Dexisting.property=two words"), manifest.inheritedArguments());
        assertEquals(original, Files.readString(source.resolve(MavenArgumentFile.CONFIG))); originalRef.verify();
        String batch = ControlBuild.mavenExecutionBatchText(null, arguments, compiled);
        assertTrue(batch.contains("\r\ncall mvn --batch-mode verify\r\n")); assertTrue(batch.contains(manifest.configRef().sha256()));
        assertFalse(batch.lines().anyMatch(line -> line.length() > MavenArgumentFile.CMD_LIMIT));
        assertEquals(manifest.inheritedArguments().size() + arguments.stream().filter(value -> value.startsWith("-D")).count(),
                Files.readAllLines(compiled.resolve(MavenArgumentFile.CONFIG)).size());
        assertTrue(Files.readAllLines(compiled.resolve(MavenArgumentFile.CONFIG)).stream().allMatch(value -> value.startsWith("-D")));
        assertFalse(Files.readString(compiled.resolve(MavenArgumentFile.CONFIG)).contains("verify\n"));
        assertTrue(Files.readString(compiled.resolve(MavenArgumentFile.CONFIG)).contains("-DargLine=-Xms32m -Xmx256m\n"));
        var compiledPins = List.of(manifest.configRef(), ControlBuild.FileRef.measure(compiled.resolve(MavenArgumentFile.MANIFEST)));
        var ordinary = MavenArgumentFile.ordinaryInventories(source, compiled, List.of(originalRef), compiledPins);
        assertEquals(List.of(), ordinary.source()); assertEquals(List.of(), ordinary.compiled());
        assertThrows(IOException.class, () -> MavenArgumentFile.ordinaryInventories(source, compiled, List.of(originalRef), List.of(manifest.configRef())));
        Files.writeString(source.resolve(MavenArgumentFile.CONFIG), "-Dexisting.property=changed\n");
        assertThrows(IOException.class, () -> ControlBuild.mavenExecutionBatchText(null, arguments, compiled));
    }
    @Test void existingArgumentsCannotOverrideOwnedPropertiesOrHideGoalsAndDuplicateKeys() throws Exception {
        Path source = root("source"), compiled = root("compiler");
        Files.createDirectories(source.resolve(".mvn")); Files.createDirectories(compiled.resolve(".mvn"));
        Path original = source.resolve(MavenArgumentFile.CONFIG), copy = compiled.resolve(MavenArgumentFile.CONFIG);
        Files.writeString(original, "-Dxar.argument.0=unchanged\n"); Files.copy(original, copy);
        assertThrows(IOException.class, () -> MavenArgumentFile.prepare(source, compiled, null, longArguments()));
        assertFalse(Files.exists(compiled.resolve(MavenArgumentFile.MANIFEST)));
        assertEquals(Files.readString(original), Files.readString(copy));
        for (String bad : List.of("verify\n", "-Dsame=1\n-Dsame=1\n", " -Dhidden=1\n", "-Dflag\n")) {
            Files.writeString(original, bad); assertThrows(IOException.class, () -> MavenArgumentFile.inheritedArguments(source));
        }
        Files.write(original, new byte[] {(byte)0xc3, (byte)0x28});
        assertThrows(IOException.class, () -> MavenArgumentFile.inheritedArguments(source));
    }
    @Test void configTamperArgvDriftAndMissingArtifactRejectPhysicalInvocation() throws Exception {
        Path source = root("source"), compiled = root("compiler"); var arguments = longArguments();
        assertThrows(IOException.class, () -> ControlBuild.mavenExecutionBatchText(null, arguments, compiled));
        assertThrows(IOException.class, () -> ControlBuild.writeMavenBatch(temporary.resolve("cannot.cmd"), null, arguments));
        MavenArgumentFile.prepare(source, compiled, null, arguments);
        var crossed = new ArrayList<>(arguments); crossed.set(1, "-Dxar.argument.0=other");
        assertThrows(IOException.class, () -> ControlBuild.mavenExecutionBatchText(null, crossed, compiled));
        Files.writeString(compiled.resolve(MavenArgumentFile.CONFIG), "-Dsilently.lost=true\nverify\n", StandardCharsets.UTF_8);
        assertThrows(IOException.class, () -> ControlBuild.mavenExecutionBatchText(null, arguments, compiled));
    }
    @Test void shortHistoricalBatchRetainsExactOldCommandAndHasNoDerivedArtifacts() throws Exception {
        Path source = root("source"), compiled = root("compiler"); List<String> shortArgs = List.of("--batch-mode", "verify");
        MavenArgumentFile.prepare(source, compiled, null, shortArgs);
        assertFalse(Files.exists(compiled.resolve(MavenArgumentFile.MANIFEST)));
        assertEquals(ControlBuild.mavenBatchText(null, shortArgs), ControlBuild.mavenExecutionBatchText(null, shortArgs, compiled));
    }
    @Test void sameLengthBodySwapIsRejectedEvenWhenBothFileWitnessesStillMatchA() throws Exception {
        Path source = root("aba-source"); Files.createDirectories(source.resolve(".mvn"));
        Path config = source.resolve(MavenArgumentFile.CONFIG);
        byte[] original = "-Dinput.key=good\n".getBytes(StandardCharsets.UTF_8);
        byte[] substituted = "-Dinput.key=evil\n".getBytes(StandardCharsets.UTF_8);
        assertEquals(original.length, substituted.length); Files.write(config, original);
        var pinnedA = ControlBuild.FileRef.measure(config); var captured = new ByteArrayOutputStream();
        IOException refusal = assertThrows(IOException.class, () -> MavenArgumentFile.inheritedArguments(source,
                path -> swapDuringActualRead(path, config, pinnedA, original, substituted, captured)));
        assertTrue(refusal.getMessage().contains("body SHA-256"), refusal.toString());
        // The actual decoder input was B, while both the measured and final file references are A.
        assertArrayEquals(substituted, captured.toByteArray());
        assertEquals(pinnedA, ControlBuild.FileRef.measure(config)); pinnedA.verify();
        assertEquals(List.of("-Dinput.key=good"), MavenArgumentFile.inheritedArguments(source));
    }
    @Test void growingAndTruncatedBodySwapsRejectAndReadAtMostExpectedBytesPlusOne() throws Exception {
        Path source = root("bounded-aba-source"); Files.createDirectories(source.resolve(".mvn"));
        Path config = source.resolve(MavenArgumentFile.CONFIG);
        byte[] original = "-Dinput.key=good\n".getBytes(StandardCharsets.UTF_8);
        byte[] grown = new byte[MavenArgumentFile.MAXIMUM_BYTES + 4096]; Arrays.fill(grown, (byte)'x');
        for (byte[] substituted : List.of(grown, Arrays.copyOf(original, original.length - 1))) {
            Files.write(config, original); var pinnedA = ControlBuild.FileRef.measure(config);
            var captured = new ByteArrayOutputStream();
            IOException refusal = assertThrows(IOException.class, () -> MavenArgumentFile.inheritedArguments(source,
                    path -> swapDuringActualRead(path, config, pinnedA, original, substituted, captured)));
            assertTrue(refusal.getMessage().contains("body length"), refusal.toString());
            assertEquals(Math.min(substituted.length, original.length + 1), captured.size());
            assertArrayEquals(Arrays.copyOf(substituted, captured.size()), captured.toByteArray());
            assertEquals(pinnedA, ControlBuild.FileRef.measure(config)); pinnedA.verify();
            assertEquals(List.of("-Dinput.key=good"), MavenArgumentFile.inheritedArguments(source));
        }
    }
    @Test void measuredArtifactAboveOneMiBRejectsBeforeOpeningTheDecodeBody() throws Exception {
        Path source = root("oversized-source"); Files.createDirectories(source.resolve(".mvn"));
        Files.write(source.resolve(MavenArgumentFile.CONFIG), new byte[MavenArgumentFile.MAXIMUM_BYTES + 1]);
        var opens = new AtomicInteger();
        assertThrows(IOException.class, () -> MavenArgumentFile.inheritedArguments(source, path -> {
            opens.incrementAndGet(); return Files.newInputStream(path);
        }));
        assertEquals(0, opens.get());
    }
    @Test void historicalV1WholeArgvManifestRemainsReadableWithoutRewritingItsFiles() throws Exception {
        Path source = root("legacy-source"), compiled = root("legacy-compiler");
        var arguments = longArguments(); Files.createDirectories(compiled.resolve(".mvn"));
        Files.writeString(compiled.resolve(MavenArgumentFile.CONFIG), String.join("\n", arguments) + "\n");
        var config = ControlBuild.FileRef.measure(compiled.resolve(MavenArgumentFile.CONFIG));
        var old = new MavenArgumentFile.Manifest(MavenArgumentFile.LEGACY_SCHEMA,
                WindowsJobProcess.currentMachineId(), Instant.now().toString(), source.toString(), compiled.toString(),
                null, List.of(), arguments, config);
        Files.write(compiled.resolve(MavenArgumentFile.MANIFEST), ControlBuild.strictMapper().writeValueAsBytes(old));
        var manifestPin = ControlBuild.FileRef.measure(compiled.resolve(MavenArgumentFile.MANIFEST));
        assertEquals(old, MavenArgumentFile.readManifest(compiled, arguments));
        assertEquals(List.of(), MavenArgumentFile.ordinaryInventories(source, compiled, List.of(),
                List.of(config, manifestPin)).compiled());
        config.verify(); manifestPin.verify();
        assertTrue(Files.readString(compiled.resolve(MavenArgumentFile.CONFIG)).endsWith("verify\n"));
    }
    @Test void actualDefaultMavenConsumesTypedFrozenPropertiesAndTheOriginalCliGoal() throws Exception {
        Path source = root("actual-source"), compiled = root("actual-compiler"), scratch = root("actual-scratch");
        ProjectStoragePolicy.requireBulkOutput(temporary.toAbsolutePath());
        String pom = "<project xmlns=\"http://maven.apache.org/POM/4.0.0\"><modelVersion>4.0.0</modelVersion>"
                + "<groupId>org.xar.fixture</groupId><artifactId>maven-argument-transport</artifactId>"
                + "<version>1</version><packaging>pom</packaging></project>\n";
        Files.writeString(source.resolve("pom.xml"), pom); Files.writeString(compiled.resolve("pom.xml"), pom);
        Path settings = temporary.resolve("actual-settings.xml");
        Files.writeString(settings, "<settings xmlns=\"http://maven.apache.org/SETTINGS/1.0.0\"/>\n");
        var arguments = new ArrayList<String>(List.of("--offline", "--show-version", "--no-transfer-progress",
                "-s", settings.toString(), "-gs", settings.toString(), "-f", compiled.resolve("pom.xml").toString(),
                "-Dmaven.repo.local=" + temporary.resolve("actual-m2"), "-Dstyle.color=never",
                "-D" + ControlBuild.LobbyVerifyTestInputs.PATH_PROPERTY + "=" + temporary.resolve("typed-input.json")));
        arguments.addAll(longArguments());
        MavenArgumentFile.prepare(source, compiled, null, arguments);
        var manifest = MavenArgumentFile.readManifest(compiled, arguments);
        assertEquals(MavenArgumentFile.SCHEMA, manifest.schema()); assertEquals(arguments, manifest.arguments());
        assertTrue(Files.readAllLines(compiled.resolve(MavenArgumentFile.CONFIG)).stream().allMatch(value -> value.startsWith("-D")));
        String batchText = ControlBuild.mavenExecutionBatchText(null, arguments, compiled);
        assertTrue(batchText.contains(" verify\r\n")); assertFalse(batchText.contains("-Dxar.argument.139="));
        Path batch = temporary.resolve("actual-default-maven.cmd");
        Files.writeString(batch, batchText, StandardCharsets.UTF_8);
        var pins = List.of(ControlBuild.FileRef.measure(source.resolve("pom.xml")),
                ControlBuild.FileRef.measure(compiled.resolve("pom.xml")), ControlBuild.FileRef.measure(settings),
                manifest.configRef(), ControlBuild.FileRef.measure(compiled.resolve(MavenArgumentFile.MANIFEST)),
                ControlBuild.FileRef.measure(batch));
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); environment.putAll(System.getenv());
        for (String key : List.of("MAVEN_ARGS", "MAVEN_DEBUG_OPTS", "MAVEN_BATCH_ECHO", "MAVEN_PROJECTBASEDIR",
                "MAVEN_EXT_CLASS_PATH", "JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS")) environment.remove(key);
        environment.put("JAVA_HOME", System.getProperty("java.home")); environment.put("MAVEN_SKIP_RC", "1");
        environment.put("MAVEN_BASEDIR", compiled.toString()); environment.put("MAVEN_USER_HOME", temporary.resolve("actual-user").toString());
        environment.put("TEMP", scratch.toString()); environment.put("TMP", scratch.toString());
        environment.put("MAVEN_OPTS", "-Xms16m -Xmx128m -XX:MaxMetaspaceSize=96m -XX:ReservedCodeCacheSize=32m"
                + " -XX:MaxDirectMemorySize=32m -Djava.io.tmpdir=\"" + scratch + "\"");
        environment.put("JAVA_TOOL_OPTIONS", environment.get("MAVEN_OPTS"));
        Path stdout = temporary.resolve("actual-maven.stdout"), stderr = temporary.resolve("actual-maven.stderr");
        var command = new WindowsJobProcess.CommandSpec(
                Path.of(environment.get("SystemRoot"), "System32", "cmd.exe"), List.of("/d", "/c", batch.toString()),
                compiled, environment, stdout, stderr, 384L << 20);
        WindowsJobProcess.CommandResult result;
        try (var child = WindowsJobProcess.start(command)) {
            result = child.await(Duration.ofSeconds(60), Instant.now().plusSeconds(90),
                    () -> {
                        try { for (var pin : pins) pin.verify(); }
                        catch (IOException failure) { throw new java.io.UncheckedIOException(failure); }
                    });
        }
        String output = Files.readString(stdout), errors = Files.readString(stderr);
        assertTrue(result.passed(), result + "\n" + output + "\n" + errors);
        assertTrue(output.contains("BUILD SUCCESS"), output);
        var toolchain = ControlBuild.measuredMavenToolchain(null, output, "3.10.0");
        assertEquals(ControlBuild.MavenSelection.DEFAULT_COMMAND, toolchain.selection());
        assertEquals("mvn", toolchain.requestedCommand()); toolchain.distributionLauncherRef().verify();
        for (var pin : pins) pin.verify(); assertEquals(manifest, MavenArgumentFile.readManifest(compiled, arguments));
        System.out.println("MAVEN_ARGUMENT_TRANSPORT_DEFAULT_ACTUAL machine_id=" + WindowsJobProcess.currentMachineId()
                + " toolchain=" + ControlBuild.strictMapper().writeValueAsString(toolchain)
                + " terminal=" + ControlBuild.strictMapper().writeValueAsString(result));
    }
    private static InputStream swapDuringActualRead(Path actual, Path expected, ControlBuild.FileRef pinnedA,
            byte[] original, byte[] substituted, ByteArrayOutputStream captured) throws IOException {
        assertEquals(expected, actual); assertEquals(pinnedA, ControlBuild.FileRef.measure(actual));
        Files.write(actual, substituted);
        InputStream input = Files.newInputStream(actual);
        return new InputStream() {
            @Override public int read() throws IOException {
                int value = input.read(); if (value >= 0) captured.write(value); return value;
            }
            @Override public int read(byte[] buffer, int offset, int length) throws IOException {
                int count = input.read(buffer, offset, length);
                if (count > 0) captured.write(buffer, offset, count);
                return count;
            }
            @Override public void close() throws IOException {
                try { input.close(); }
                finally { Files.write(actual, original); }
                assertEquals(pinnedA, ControlBuild.FileRef.measure(actual));
            }
        };
    }
}
