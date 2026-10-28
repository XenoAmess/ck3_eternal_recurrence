package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Real child CLI/processes, but the default mvn is an authored CMD fixture, never installed Maven. */
final class LocalDefaultMavenObservationTest {
    private static final String SOURCE = "java/ck3-control/build-tools/src/main/java/org/xar/ck3/control/build/CiBootstrap.java";
    record Fixture(Path root, Path repo, Path home, Path evidence) { }

    private static Fixture fixture(Path root, String version, int exit) throws IOException {
        Path repo = Files.createDirectories(root.resolve("repo"));
        Path home = Files.createDirectories(root.resolve("home/bin")).getParent();
        Path source = repo.resolve(SOURCE); Files.createDirectories(source.getParent());
        Files.copy(Path.of(System.getProperty("candidate.source")), source);
        Path gav = Files.createDirectories(root.resolve("repository/org/xar/ck3/ck3-save-core/0.1.0"));
        Files.writeString(gav.resolve("ck3-save-core-0.1.0.jar"), "authored leaf bytes, no business qualification");
        Files.writeString(gav.resolve("ck3-save-core-0.1.0.pom"), "<project/>");
        String script = "@echo off\r\nif \"%~1\"==\"--version\" goto version\r\n"
                + "echo [DEBUG] Using manager EnhancedLocalRepositoryManager for " + root.resolve("repository") + "\r\n"
                + "echo [INFO] Installing authored.jar to " + gav.resolve("ck3-save-core-0.1.0.jar") + "\r\n"
                + "echo [INFO] Installing authored.pom to " + gav.resolve("ck3-save-core-0.1.0.pom") + "\r\nexit /b 0\r\n"
                + ":version\r\necho Apache Maven " + version + "\r\necho Maven home: " + home + "\r\nexit /b " + exit + "\r\n";
        Files.writeString(home.resolve("bin/mvn.cmd"), script, StandardCharsets.UTF_8);
        return new Fixture(root, repo, home, root.resolve("observation"));
    }

    private static ProcessBuilder child(Fixture fixture, String main, List<String> arguments, Path output) {
        List<String> command = new ArrayList<>(List.of(Path.of(System.getProperty("java.home"), "bin/java.exe").toString(),
                "-Xmx96m", "-Djava.io.tmpdir=" + System.getProperty("java.io.tmpdir"), "-cp",
                System.getProperty("java.class.path"), main));
        command.addAll(arguments);
        ProcessBuilder child = new ProcessBuilder(command).directory(fixture.repo().toFile())
                .redirectErrorStream(true).redirectOutput(output.toFile());
        // This isolated child selects the fake command. The real machine environment/PATH is untouched.
        child.environment().put("PATH", fixture.home().resolve("bin") + ";" + Path.of(System.getenv("SystemRoot"), "System32"));
        child.environment().put("PATHEXT", ".COM;.EXE;.BAT;.CMD");
        child.environment().remove("GITHUB_ACTIONS");
        child.environment().put("GITHUB_SHA", "0".repeat(40));
        child.environment().put("MAVEN_OPTS", "-Dfixture.inherited=true");
        return child;
    }

    private static int run(ProcessBuilder builder) throws Exception {
        Process process = builder.start();
        try {
            assertTrue(process.waitFor(60, TimeUnit.SECONDS), "authored child timed out");
            return process.exitValue();
        } finally {
            if (process.isAlive()) { process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); process.waitFor(); }
        }
    }

    private static int observe(Fixture f) throws Exception {
        return run(child(f, CiBootstrap.class.getName(), List.of("--observe-local-default-maven", "--repo-root",
                f.repo().toString(), "--work-root", f.evidence().toString()), f.root().resolve("observer-cli.log")));
    }
    private static Path terminal(Fixture f) { return f.evidence().resolve("logs/bootstrap-actual.json"); }
    private static String machine(Fixture f) throws IOException {
        var value = Pattern.compile("\"machine_id\"\\s*:\\s*\"([^\"]+)\"").matcher(Files.readString(terminal(f)));
        assertTrue(value.find()); return value.group(1);
    }

    @Test void runtimeMatrixUsesExplicitFixtureArgumentsAndActualCliUsesUnmodifiedRuntime() {
        for (int feature : List.of(21, 25)) CiBootstrap.requireWindowsJdk("Windows fixture", feature, true);
        assertThrows(IllegalStateException.class, () -> CiBootstrap.requireWindowsJdk("Windows fixture", 20, true));
        assertThrows(IllegalStateException.class, () -> CiBootstrap.requireWindowsJdk("Linux fixture", 25, true));
        CiBootstrap.requireWindowsJdk("Windows fixture", 21, false);
        assertThrows(IllegalStateException.class, () -> CiBootstrap.requireWindowsJdk("Windows fixture", 25, false));
        assertTrue(System.getProperty("os.name").startsWith("Windows"));
        assertTrue(Runtime.version().feature() >= 21);
        // No System.setProperty(os.name/java.version) is used to impersonate the executing host.
    }

    @Test void actualCliToVerifierAndActualDiagnosticEnvironmentWriterRoundTrip(@TempDir Path root) throws Exception {
        Fixture f = fixture(root, "3.10.0", 0);
        assertEquals(0, observe(f), Files.readString(root.resolve("observer-cli.log")));
        assertEquals(1, CiBootstrap.verifyMavenEvidence(f.evidence(), machine(f)));
        assertEquals(0, run(child(f, CiBootstrap.class.getName(),
                List.of("--verify-maven-evidence-root", f.evidence().toString()), root.resolve("verify-cli.log"))));
        Path diagnostic = Files.createDirectory(root.resolve("diagnostic"));
        Path extension = root.resolve("authored-not-loaded-extension.jar"); Files.writeString(extension, "not a real extension");
        Path env = diagnostic.resolve("prepare.env"); Files.createFile(env);
        for (String mode : List.of("leaf", "prepare")) {
            ProcessBuilder step = child(f, DiagnosticFixture.class.getName(), List.of(mode, f.repo().toString(),
                    diagnostic.toString(), f.evidence().toString(), machine(f), extension.toString()), root.resolve(mode + ".log"));
            step.environment().put("GITHUB_ENV", env.toString());
            assertEquals(0, run(step), Files.readString(root.resolve(mode + ".log")));
        }
        String emitted = Files.readString(env);
        assertTrue(emitted.contains("QUARKUS_LOCAL_REPO=" + root.resolve("repository").toRealPath()));
        assertTrue(emitted.contains("-Dfixture.inherited=true"));
        assertTrue(emitted.contains("xar.maven.repository.diagnostic.root"));
        assertEquals(2, emitted.lines().count());
        // This calls the real verifier and real Spy leaf/prepare writer. Its logs/leaf bytes are authored.
        // Actual provided-Maven spy compilation/classloader qualification stays in the existing 5 tests.
        assertTrue(Files.readString(diagnostic.resolve("repository-binding.actual.json")).contains("Original leaf wait0"));
    }

    public static final class DiagnosticFixture {
        private DiagnosticFixture() { }
        public static void main(String[] args) throws Exception {
            CiBootstrap.verifyMavenEvidence(Path.of(args[3]), args[4]);
            int result = MavenRepositorySpy.execute(args[0], Path.of(args[1]), Path.of(args[2]), args[4],
                    Path.of(args[5]), args[0].equals("leaf") ? new String[] {"install"} : new String[0]);
            System.exit(result);
        }
    }

    @Test void belowMinimumIsRejectedWithoutChangingLauncherOrInstalling(@TempDir Path root) throws Exception {
        Fixture f = fixture(root, "3.9.16", 0);
        var before = CiBootstrap.measure(f.home().resolve("bin/mvn.cmd"));
        assertEquals(1, observe(f));
        assertEquals(before, CiBootstrap.measure(f.home().resolve("bin/mvn.cmd")));
        assertTrue(Files.readString(terminal(f)).contains("\"status\":\"RED\""));
        assertThrows(IOException.class, () -> CiBootstrap.verifyMavenEvidence(f.evidence(), machine(f)));
        try (var files = Files.list(f.home())) { assertEquals(List.of("bin"), files.map(p -> p.getFileName().toString()).toList()); }
    }

    @Test void actualNonzeroExitRemainsOriginalNonzeroAndNotAdmission(@TempDir Path root) throws Exception {
        Fixture f = fixture(root, "3.10.0", 37);
        assertEquals(1, observe(f));
        assertTrue(Files.readString(f.evidence().resolve("logs/local-maven-process.actual.json")).contains("\"original_exit\":37"));
        assertThrows(IOException.class, () -> CiBootstrap.verifyMavenEvidence(f.evidence(), machine(f)));
    }

    @Test void wrongMachineSchemaTypesAndPathsAreRejected(@TempDir Path root) throws Exception {
        Fixture f = fixture(root, "3.10.0", 0); assertEquals(0, observe(f));
        assertThrows(IOException.class, () -> CiBootstrap.verifyMavenEvidence(f.evidence(), "different-machine"));
        String original = Files.readString(terminal(f));
        for (String altered : List.of(original.replace(CiBootstrap.LocalDefaultMaven.SCHEMA, "unknown-schema"),
                original.replace("\"observes_existing_only\":true", "\"observes_existing_only\":1"),
                original.replace("\"pipeline_qualification\":false", "\"pipeline_qualification\":true"),
                original.replace("\"status\":\"READY\"", "\"status\":null"),
                original.replace("\"probe_ref\":{", "\"unexpected_probe_ref\":{"))) {
            assertFalse(original.equals(altered));
            Files.writeString(terminal(f), altered);
            assertThrows(IOException.class, () -> CiBootstrap.verifyMavenEvidence(f.evidence(), machine(f)));
        }
        Files.writeString(terminal(f), original);
        Path outside = root.resolve("outside.json");
        Files.copy(f.evidence().resolve("logs/maven-observation-1.json"), outside);
        var before = CiBootstrap.measure(f.evidence().resolve("logs/maven-observation-1.json"));
        // Same bytes at a different absolute path must not satisfy the fixed evidence route.
        String oldPath = before.path().replace("\\", "\\\\");
        Files.writeString(terminal(f), original.replace(oldPath, outside.toString().replace("\\", "\\\\")));
        assertThrows(IOException.class, () -> CiBootstrap.verifyMavenEvidence(f.evidence(), machine(f)));
    }

    @Test void changedSourceAndLauncherPinsReject(@TempDir Path root) throws Exception {
        Fixture f = fixture(root, "3.10.0", 0); assertEquals(0, observe(f));
        Path source = f.repo().resolve(SOURCE); byte[] saved = Files.readAllBytes(source);
        Files.writeString(source, "changed"); assertThrows(IOException.class, () -> CiBootstrap.verifyMavenEvidence(f.evidence(), machine(f)));
        Files.write(source, saved);
        Files.writeString(f.home().resolve("bin/mvn.cmd"), "changed");
        assertThrows(IOException.class, () -> CiBootstrap.verifyMavenEvidence(f.evidence(), machine(f)));
    }

    @Test void outputLimitAndTimeoutAreRealFailedProcessObservations(@TempDir Path root) throws Exception {
        Fixture f = fixture(root, "3.10.0", 0);
        Map<String, String> environment = new java.util.HashMap<>(System.getenv());
        environment.put("PATH", f.home().resolve("bin") + ";" + Path.of(System.getenv("SystemRoot"), "System32"));
        environment.put("PATHEXT", ".CMD");
        Path system = Path.of(System.getenv("SystemRoot"));
        Files.writeString(f.home().resolve("bin/mvn.cmd"), "@echo off\r\nfor /L %%i in (1,1,10000) do @echo authored-output-limit\r\n");
        var limit = CiBootstrap.LocalDefaultMaven.capture(f.repo(), environment, root.resolve("limit.stdout"),
                root.resolve("limit.stderr"), Duration.ofSeconds(5), system);
        assertNotNull(limit.stopReason()); assertTrue(Files.size(root.resolve("limit.stdout")) <= 65_536);
        Files.writeString(f.home().resolve("bin/mvn.cmd"), "@echo off\r\n:again\r\ngoto again\r\n");
        var timeout = CiBootstrap.LocalDefaultMaven.capture(f.repo(), environment, root.resolve("timeout.stdout"),
                root.resolve("timeout.stderr"), Duration.ofMillis(100), system);
        assertTrue(timeout.timedOut()); assertEquals("TIMEOUT", timeout.stopReason());
        assertNotNull(timeout.originalExit());
        assertFalse(ProcessHandle.of(Long.parseLong(timeout.processIdDecimal())).map(ProcessHandle::isAlive).orElse(false));
    }
}
