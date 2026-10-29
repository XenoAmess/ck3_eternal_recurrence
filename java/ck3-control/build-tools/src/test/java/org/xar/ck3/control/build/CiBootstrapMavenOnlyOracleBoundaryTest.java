package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Local software hosted-profile fixture; only the installed default Maven version probe is executed. */
final class CiBootstrapMavenOnlyOracleBoundaryTest {
    @TempDir Path temporary;
    private record Fixture(Path repository, Path runnerTemp, Path workRoot, Path pythonIdentity) { }
    private record Result(int exit, String output) { }

    @Test void mavenOnlyWithoutOracleUsesTheActualDefaultMavenWithoutRunningPipeline() throws Exception {
        Fixture fixture = fixture();
        Result result = launch(fixture, true, false);
        assertEquals(0, result.exit(), result.output());
        String actual = Files.readString(fixture.workRoot().resolve("logs/bootstrap-actual.json"));
        assertTrue(actual.contains("\"status\":\"MAVEN_READY_NO_PIPELINE_QUALIFICATION\""), actual);
        assertTrue(actual.contains("\"error\":null"), actual);
        assertTrue(actual.contains("\"plan_ref\":null"), actual);
        assertTrue(actual.contains("\"bootstrap_alone_grants_pipeline_qualification\":false"), actual);
        assertTrue(actual.contains("\"bootstrap_native_job_hard_bound\":false"), actual);
        Path versionLog = fixture.workRoot().resolve("logs/maven-version-1.log");
        assertTrue(Files.isRegularFile(versionLog), "The actual default mvn --version probe must run");
        CiBootstrap.DefaultMaven observed = CiBootstrap.requireDefaultMaven(Files.readString(versionLog));
        assertEquals("mvn", observed.command());
        assertTrue(Files.isRegularFile(fixture.workRoot().resolve("logs/maven-observation-1.json")));
        assertFalse(Files.exists(fixture.workRoot().resolve("scratch/bootstrap-verify.cmd")));
        assertFalse(Files.exists(fixture.workRoot().resolve("logs/bootstrap-verify.log")));
        assertFalse(Files.exists(fixture.workRoot().resolve("logs/bootstrap-plan.json")));
    }

    @Test void pipelineWithoutOracleStillRejectsBeforeAnyMavenProbe() throws Exception {
        Fixture fixture = fixture();
        Result result = launch(fixture, false, false);
        assertNotEquals(0, result.exit(), result.output());
        assertTrue(result.output().contains("NOT EXECUTED: explicit XAR_ORACLE_PYTHON required"), result.output());
        String actual = Files.readString(fixture.workRoot().resolve("logs/bootstrap-actual.json"));
        assertTrue(actual.contains("\"status\":\"RED\""), actual);
        assertTrue(actual.contains("\"maven_probe_refs\":[]"), actual);
        assertFalse(Files.exists(fixture.workRoot().resolve("logs/maven-version-1.log")));
        assertFalse(Files.exists(fixture.workRoot().resolve("scratch/bootstrap-verify.cmd")));
    }

    @Test void explicitOracleVerificationStillRequiresItsExplicitEnvironment() throws Exception {
        Fixture fixture = fixture();
        Result result = launch(fixture, false, true);
        assertNotEquals(0, result.exit(), result.output());
        assertTrue(result.output().contains("NOT EXECUTED: explicit XAR_ORACLE_PYTHON required"), result.output());
        assertFalse(Files.exists(fixture.workRoot()));
    }

    private Fixture fixture() throws IOException {
        String basedir = System.getProperty("basedir");
        assertNotNull(basedir, "Actual Maven project basedir is required");
        Path actualSource = Path.of(basedir).resolve("src/main/java/org/xar/ck3/control/build/CiBootstrap.java").toRealPath();
        Path repository = Files.createDirectory(temporary.resolve("software-repository")).toRealPath();
        Path module = Files.createDirectories(repository.resolve("java/ck3-control/build-tools"));
        Path source = module.resolve("src/main/java/org/xar/ck3/control/build/CiBootstrap.java");
        Files.createDirectories(source.getParent());
        Files.copy(actualSource, source);
        // This POM and Python identity are never executed; no reactor, interpreter or pipeline is invoked.
        Files.writeString(module.resolve("pom.xml"), "<project><modelVersion>4.0.0</modelVersion></project>\n");
        Files.createDirectories(repository.resolve("docs"));
        Files.writeString(repository.resolve("docs/storage-retention-policy.json"), """
                {"schema":"xar-storage-retention-policy-v1","policy_version":"1.0.0","capacity":{
                  "safety_floor_bytes":2147483648,"safety_ceiling_bytes":21474836480,"safety_volume_fraction":0.05,
                  "default_project_quota_ceiling_bytes":107374182400,"default_project_quota_volume_fraction":0.10,
                  "quota_override_max_hours":168}}
                """);
        Files.writeString(repository.resolve("java/ck3-control/ci-profile.json"), """
                {"schema":"xar.java-control-CI-profile/v1","owner":"software-fixture","task":"github-actions-java-ci",
                  "reason":"Local Maven-only oracle mode regression; no hosted CI qualification",
                  "max_project_bytes":8589934592,"review_minutes":90}
                """);
        Path runnerTemp = Files.createDirectory(temporary.resolve("software-runner-temp")).toRealPath();
        Path pythonIdentity = Files.writeString(temporary.resolve("nonexecuted-python-identity.exe"), "software identity fixture").toRealPath();
        return new Fixture(repository, runnerTemp, runnerTemp.resolve("maven-mode-probe"), pythonIdentity);
    }

    private Result launch(Fixture fixture, boolean mavenOnly, boolean verifyOracle) throws Exception {
        assertTrue(System.getProperty("os.name").startsWith("Windows"), "The production bootstrap requires Windows");
        assertEquals(21, Runtime.version().feature(), "The production bootstrap requires JDK21");
        Path java = Path.of(System.getProperty("java.home"), "bin/java.exe").toRealPath();
        Path classes = Path.of(CiBootstrap.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
        List<String> command = new ArrayList<>(List.of(java.toString(), "-Xms32m", "-Xmx128m", "-XX:ActiveProcessorCount=1",
                "-Djava.io.tmpdir=" + temporary, "-cp", classes.toString(), CiBootstrap.class.getName()));
        if (verifyOracle) command.add("--verify-canonical-oracle-environment");
        else {
            if (mavenOnly) command.add("--ensure-default-maven-only");
            command.addAll(List.of("--repo-root", fixture.repository().toString(), "--work-root", fixture.workRoot().toString(),
                    "--python-executable", fixture.pythonIdentity().toString(), "--system-growth-reserve-bytes", "2147483648",
                    "--max-project-bytes", "8589934592"));
        }
        Path log = temporary.resolve("bootstrap-child.log");
        ProcessBuilder builder = new ProcessBuilder(command).directory(fixture.runnerTemp().toFile())
                .redirectErrorStream(true).redirectOutput(log.toFile());
        Map<String, String> environment = builder.environment();
        for (String name : List.of("XAR_ORACLE_PYTHON", "XAR_ORACLE_REPO", "XAR_REPO_ROOT", "JAVA_TOOL_OPTIONS",
                "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS", "CLASSPATH")) environment.remove(name);
        environment.put("GITHUB_ACTIONS", "true");
        environment.put("RUNNER_TEMP", fixture.runnerTemp().toString());
        Process child = builder.start();
        boolean exited;
        try { exited = child.waitFor(60, TimeUnit.SECONDS); }
        finally {
            if (child.isAlive()) {
                child.descendants().forEach(ProcessHandle::destroyForcibly);
                child.destroyForcibly();
                assertTrue(child.waitFor(10, TimeUnit.SECONDS), "Bootstrap child did not terminate");
            }
        }
        assertTrue(exited, "Bootstrap child timed out");
        assertTrue(Files.size(log) <= 65536, "Bounded child diagnostics required");
        return new Result(child.exitValue(), Files.readString(log));
    }
}
