package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Executes the actual standalone entry, with no project classes or sibling source files available. */
final class CiBootstrapSourceFileTest {
    @TempDir Path temporary;
    private record Fixture(Path source, Path classPath, Map<String, String> environment) { }
    private record Result(int exit, String output) { }

    @Test void actualStandaloneSourceEntrypointValidatesCanonicalInputsWithoutPrecompiledSiblings() throws Exception {
        var fixture = fixture();
        Result result = launch(fixture, fixture.environment());
        assertEquals(0, result.exit(), result.output());
        assertTrue(result.output().contains("Verified explicit canonical oracle environment; no pipeline qualification"), result.output());
    }

    @Test void actualStandaloneSourceEntrypointRejectsMissingRepositoryRatherThanInferringIt() throws Exception {
        var fixture = fixture();
        var missing = new TreeMap<>(fixture.environment()); missing.remove("XAR_REPO_ROOT");
        Result result = launch(fixture, missing);
        assertNotEquals(0, result.exit(), result.output());
        assertTrue(result.output().contains("explicit XAR_REPO_ROOT required"), result.output());
        assertFalse(result.output().contains("cannot find symbol"), result.output());
    }

    @Test void packagedFacadePreservesTheSameMandatoryProducerReaderAndPathContracts() throws Exception {
        var fixture = fixture(); var expected = CiBootstrap.OracleEnvironment.require(fixture.environment());
        var actual = CanonicalOracleEnvironment.require(fixture.environment());
        assertEquals(expected.python(), actual.python()); assertEquals(expected.repositoryRoot(), actual.repositoryRoot());
        assertEquals(fixture.environment(), CanonicalOracleEnvironment.bind(Path.of(actual.repositoryRoot()), Path.of(actual.python()), Map.of()));
        for (String name : List.of("XAR_ORACLE_PYTHON", "XAR_ORACLE_REPO", "XAR_REPO_ROOT")) {
            var missing = new TreeMap<>(fixture.environment()); missing.remove(name);
            assertThrows(IOException.class, () -> CanonicalOracleEnvironment.require(missing));
        }
        var crossed = new TreeMap<>(fixture.environment());
        crossed.put("XAR_REPO_ROOT", Files.createDirectory(temporary.resolve("other-repository")).toRealPath().toString());
        assertThrows(IOException.class, () -> CanonicalOracleEnvironment.require(crossed));
        assertThrows(IllegalArgumentException.class, () -> new CanonicalOracleEnvironment.Inputs("relative.exe", actual.repositoryRoot()));
    }

    private Fixture fixture() throws IOException {
        String basedir = System.getProperty("basedir");
        assertNotNull(basedir, "Actual Maven project basedir is required; no repository fallback");
        Path actual = Path.of(basedir).resolve("src/main/java/org/xar/ck3/control/build/CiBootstrap.java").toRealPath();
        Path isolated = Files.createDirectory(temporary.resolve("standalone"));
        Path source = Files.copy(actual, isolated.resolve("CiBootstrap.java"));
        Path classPath = Files.createDirectory(isolated.resolve("empty-classpath"));
        Path repository = Files.createDirectory(temporary.resolve("repository")).toRealPath();
        Files.createDirectories(repository.resolve(".github/workflows"));
        Files.writeString(repository.resolve(".github/workflows/static-ci.yml"), "name: oracle-environment-fixture\n");
        Path python = Files.writeString(temporary.resolve("python-fixture.exe"), "nonexecuted interpreter identity fixture").toRealPath();
        var environment = CanonicalOracleEnvironment.bind(repository, python, Map.of());
        assertArrayEquals(Files.readAllBytes(actual), Files.readAllBytes(source));
        return new Fixture(source, classPath, environment);
    }

    private Result launch(Fixture fixture, Map<String, String> canonical) throws Exception {
        assertEquals(21, Runtime.version().feature(), "The real CI source-file entry requires JDK21");
        Path java = Path.of(System.getProperty("java.home"), "bin/java.exe").toRealPath();
        Path log = temporary.resolve("source-file.log");
        byte[] before = Files.readAllBytes(fixture.source());
        var command = List.of(java.toString(), "-Xms32m", "-Xmx128m", "-XX:MaxMetaspaceSize=96m",
                "-XX:ReservedCodeCacheSize=48m", "-XX:MaxDirectMemorySize=32m",
                "-Djava.io.tmpdir=" + temporary, "--class-path", fixture.classPath().toString(), "--source", "21",
                fixture.source().toString(), "--verify-canonical-oracle-environment");
        var builder = new ProcessBuilder(command).directory(fixture.source().getParent().toFile()).redirectErrorStream(true).redirectOutput(log.toFile());
        var environment = builder.environment();
        for (String name : List.of("CLASSPATH", "JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS",
                "XAR_ORACLE_PYTHON", "XAR_ORACLE_REPO", "XAR_REPO_ROOT")) environment.remove(name);
        environment.putAll(canonical);
        Process child = builder.start(); boolean exited;
        try { exited = child.waitFor(60, TimeUnit.SECONDS); }
        finally { if (child.isAlive()) { child.destroyForcibly(); assertTrue(child.waitFor(10, TimeUnit.SECONDS), "Source-file child did not terminate"); } }
        assertTrue(exited, "Actual standalone source-file entry timed out");
        assertTrue(Files.size(log) <= 65536, "Bounded source-file diagnostics required");
        assertArrayEquals(before, Files.readAllBytes(fixture.source()));
        try (var contents = Files.list(fixture.classPath())) { assertEquals(0, contents.count(), "No compiled project sibling is supplied"); }
        return new Result(child.exitValue(), Files.readString(log));
    }
}
