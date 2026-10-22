package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class CiBootstrapTest {
    private static final long GIB = 1L << 30;
    private static final String POLICY = """
            {"schema":"xar-storage-retention-policy-v1","policy_version":"1.0.0","capacity":{
            "safety_floor_bytes":2147483648,"safety_ceiling_bytes":21474836480,"safety_volume_fraction":0.05,
            "default_project_quota_ceiling_bytes":107374182400,"default_project_quota_volume_fraction":0.10,
            "quota_override_max_hours":168}}
            """;

    @Test
    void policyBoundaryRejectsMissingNullBooleanFloatExponentDuplicateAndTrailingFields() throws Exception {
        assertEquals(168, CiBootstrap.readPolicy(POLICY.getBytes(StandardCharsets.UTF_8)).quotaOverrideMaxHours());
        for (String token : new String[] {"null", "true", "[]", "\"168\"", "168.0", "168e0"}) {
            String raw = POLICY.replace("\"quota_override_max_hours\":168", "\"quota_override_max_hours\":" + token);
            assertThrows(IOException.class, () -> CiBootstrap.readPolicy(raw.getBytes(StandardCharsets.UTF_8)), token);
        }
        for (String raw : new String[] {
                POLICY.replace(",\n\"quota_override_max_hours\":168", ""),
                POLICY.replace("\"quota_override_max_hours\":168", "\"quota_override_max_hours\":168,\"quota_override_max_hours\":168"),
                POLICY + "false"}) {
            assertThrows(IOException.class, () -> CiBootstrap.readPolicy(raw.getBytes(StandardCharsets.UTF_8)));
        }
    }

    @Test
    void finiteQuotaOverrideCannotRelaxActualFreeSpaceOrOutliveAuthority(@TempDir Path temporary) throws Exception {
        CiBootstrap.Policy policy = new CiBootstrap.Policy(2 * GIB, 20 * GIB, new BigDecimal("0.05"),
                100 * GIB, new BigDecimal("0.10"), 168);
        Path profile = temporary.resolve("profile.json"); Files.writeString(profile, "actual profile");
        Instant observed = Instant.parse("2026-10-22T13:00:00Z"), review = observed.plusSeconds(5400);
        CiBootstrap.QuotaOverride override = new CiBootstrap.QuotaOverride("owner", "task", "finite CI", 8 * GIB,
                review.toString(), CiBootstrap.measure(profile));
        assertThrows(IllegalArgumentException.class, () -> CiBootstrap.calculate(policy, 14 * GIB, 12 * GIB, 4 * GIB, 0, 2 * GIB, GIB));
        CiBootstrap.VolumeBudget budget = CiBootstrap.calculate(policy, 14 * GIB, 12 * GIB, 4 * GIB, 0, 2 * GIB, GIB,
                override, observed, review);
        assertEquals(8 * GIB, budget.effectiveProjectQuota());
        assertEquals(8 * GIB, budget.requiredFree());
        assertThrows(IllegalArgumentException.class, () -> CiBootstrap.calculate(policy, 14 * GIB, 8 * GIB - 1, 4 * GIB, 0, 2 * GIB, GIB,
                override, observed, review));
        assertThrows(IllegalArgumentException.class, () -> CiBootstrap.calculate(policy, 14 * GIB, 12 * GIB, 4 * GIB, 0, 2 * GIB, GIB,
                override, review, review));
        assertThrows(IllegalArgumentException.class, () -> CiBootstrap.calculate(policy, 200 * GIB, 100 * GIB, 4 * GIB, 0, 2 * GIB, GIB,
                override, observed, review));
        assertThrows(IllegalArgumentException.class, () -> CiBootstrap.calculate(policy, 14 * GIB, 12 * GIB, 4 * GIB, 0, 2 * GIB, GIB,
                override, observed, review.minusSeconds(1)));
    }

    @Test
    void boundedBodyRejectsOversizeAndStallAfterSuccessfulHeaders() throws Exception {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        CiBootstrap.transferBounded(new ByteArrayInputStream(new byte[] {1, 2}), output, 2, Duration.ofSeconds(1));
        assertEquals(2, output.size());
        assertThrows(IOException.class, () -> CiBootstrap.transferBounded(new ByteArrayInputStream(new byte[3]),
                new ByteArrayOutputStream(), 2, Duration.ofSeconds(1)));
        try (BlockingInput input = new BlockingInput()) {
            long started = System.nanoTime();
            assertThrows(IOException.class, () -> CiBootstrap.transferBounded(input, new ByteArrayOutputStream(), 2, Duration.ofMillis(50)));
            assertTrue(input.closed);
            assertTrue(Duration.ofNanos(System.nanoTime() - started).compareTo(Duration.ofSeconds(2)) < 0);
        }
    }

    @Test
    void archiveExtractionRejectsTraversalAndPreservesActualBytes(@TempDir Path temporary) throws Exception {
        Path good = temporary.resolve("good.zip");
        writeZip(good, "apache-maven-3.10.0/bin/mvn.cmd");
        Path output = Files.createDirectory(temporary.resolve("tools"));
        CiBootstrap.extractMaven(good, output);
        assertEquals("actual", Files.readString(output.resolve("apache-maven-3.10.0/bin/mvn.cmd")));
        for (String name : new String[] {"../escape.txt", "nested/../../escape.txt", "C:/escape.txt", "nested\\escape.txt"}) {
            Path bad = temporary.resolve("bad" + Math.abs(name.hashCode()) + ".zip");
            writeZip(bad, name);
            assertThrows(IOException.class, () -> CiBootstrap.extractMaven(bad, output), name);
        }
        assertTrue(Files.notExists(temporary.resolve("escape.txt")));
    }

    @Test
    void planRoundtripRetainsExplicitBootstrapLimitationsAndRejectsMissingFlags(@TempDir Path temporary) throws Exception {
        Path source = temporary.resolve("source.json"); Files.writeString(source, "source");
        CiBootstrap.FilePin pin = CiBootstrap.measure(source);
        CiBootstrap.Plan plan = new CiBootstrap.Plan(CiBootstrap.PLAN_SCHEMA, "test-machine", "2026-10-22T13:00:00Z",
                "2026-10-22T14:30:00Z", temporary.toString(), temporary.toString(), temporary.toString(), source.toString(),
                source.toString(), "task", pin, Map.of(), Map.of(), Map.of(), List.of(pin), List.of(pin), false, false);
        var mapper = ControlBuild.strictMapper();
        byte[] raw = mapper.writeValueAsBytes(plan);
        assertEquals(plan, mapper.readValue(raw, CiBootstrap.Plan.class));
        var missing = mapper.readTree(raw);
        if (!(missing instanceof com.fasterxml.jackson.databind.node.ObjectNode object)) throw new IOException("object expected");
        object.remove("bootstrap_native_job_hard_bound");
        assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsBytes(object), CiBootstrap.Plan.class));
        object.put("bootstrap_native_job_hard_bound", true);
        assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsBytes(object), CiBootstrap.Plan.class));
    }

    @Test
    void existingDefaultMavenKeepsItsObservedHomeAndAcceptsNewerStableVersions(@TempDir Path temporary) throws Exception {
        Path home = Files.createDirectory(temporary.resolve("original-installation"));
        Path bin = Files.createDirectory(home.resolve("bin"));
        Path launcher = bin.resolve("mvn.cmd"); Files.writeString(launcher, "original launcher remains unchanged");
        CiBootstrap.FilePin pin = CiBootstrap.measure(launcher);
        var mapper = ControlBuild.strictMapper();
        for (String version : List.of("3.10.0", "3.10.1", "3.11.0", "4.0.0", "03.10.0", "30000000000000000000.0.0")) {
            CiBootstrap.DefaultMaven actual = CiBootstrap.requireDefaultMaven("Apache Maven " + version + " (actual)\r\nMaven home: " + home + "\r\n");
            assertEquals("mvn", actual.command());
            assertEquals(home.toRealPath().toString(), actual.reportedHome());
            assertEquals(pin, actual.distributionLauncherRef());
            assertEquals(actual, mapper.readValue(mapper.writeValueAsBytes(actual), CiBootstrap.DefaultMaven.class));
        }
        for (String version : List.of("3.9.16", "3.10.0-rc1", "3.10", "true", "3.10.0.1")) {
            assertThrows(IOException.class, () -> CiBootstrap.requireDefaultMaven("Apache Maven " + version + "\nMaven home: " + home + "\n"));
        }
        assertThrows(IOException.class, () -> CiBootstrap.requireDefaultMaven("Apache Maven 3.10.0\n"));
        assertThrows(IOException.class, () -> CiBootstrap.requireDefaultMaven("Apache Maven 3.10.0\nApache Maven 4.0.0\nMaven home: " + home));
        assertThrows(IOException.class, () -> CiBootstrap.requireDefaultMaven("Apache Maven 3.10.0\nMaven home: " + home + "\nMaven home: " + home));
        assertEquals(pin, CiBootstrap.measure(launcher));
    }

    @Test
    void actualOldDefaultCommandIsReplacedAtItsHomeThenSameCommandIsReadmitted(@TempDir Path temporary) throws Exception {
        Path home = Files.createDirectories(temporary.resolve("original-maven/bin")).getParent();
        Path oldLauncher = home.resolve("bin/mvn.cmd");
        Files.writeString(oldLauncher, versionCommand("3.9.16", home));
        Files.createDirectories(home.resolve("lib")); Files.writeString(home.resolve("lib/old.jar"), "old vendor");
        Files.createDirectories(home.resolve("conf")); Files.writeString(home.resolve("conf/settings.xml"), "active settings");
        Path staged = Files.createDirectories(temporary.resolve("verified-distribution/bin")).getParent();
        Files.writeString(staged.resolve("bin/mvn.cmd"), versionCommand("3.10.0", home));
        Files.createDirectories(staged.resolve("lib")); Files.writeString(staged.resolve("lib/new.jar"), "new vendor");
        Files.createDirectories(staged.resolve("conf")); Files.writeString(staged.resolve("conf/settings.xml"), "vendor default");
        Path cwd = Files.createDirectory(temporary.resolve("working"));
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); environment.putAll(System.getenv());
        environment.put("PATH", home.resolve("bin") + ";" + Path.of(System.getenv("SystemRoot"), "System32"));
        environment.put("PATHEXT", ".CMD;.BAT;.EXE;.COM");
        Path batch = cwd.resolve("version.cmd"); ControlBuild.writeMavenBatch(batch, null, List.of("--version"));
        AtomicInteger probes = new AtomicInteger(), installations = new AtomicInteger();
        CiBootstrap.DefaultMaven actual = CiBootstrap.ensureDefaultMaven(
                () -> actualVersionProbe(batch, cwd, environment, probes.incrementAndGet()), before -> {
                    installations.incrementAndGet(); assertEquals("3.9.16", before.reportedVersion());
                    assertEquals(oldLauncher.toRealPath(), CiBootstrap.defaultMavenLauncher(environment, cwd, true));
                    CiBootstrap.replaceMavenInstallation(before, staged, temporary.resolve("backup"), () -> {});
                });
        assertEquals(2, probes.get()); assertEquals(1, installations.get());
        assertEquals("3.10.0", actual.reportedVersion()); assertEquals(home.toRealPath().toString(), actual.reportedHome());
        assertEquals("active settings", Files.readString(home.resolve("conf/settings.xml")));
        assertEquals("old vendor", Files.readString(temporary.resolve("backup/lib/old.jar")));
        assertFalse(Files.exists(home.resolve("lib/old.jar"))); assertTrue(Files.exists(home.resolve("lib/new.jar")));
        CiBootstrap.ensureDefaultMaven(() -> actualVersionProbe(batch, cwd, environment, probes.incrementAndGet()),
                before -> { throw new IOException("compliant default must not be downloaded/replaced"); });
        assertEquals(3, probes.get());
    }

    @Test
    void failedUpgradeAndWrongDefaultForwardingStayRed(@TempDir Path temporary) throws Exception {
        Path home = Files.createDirectories(temporary.resolve("old/bin")).getParent();
        Path other = Files.createDirectories(temporary.resolve("other/bin")).getParent();
        Files.writeString(home.resolve("bin/mvn.cmd"), "old"); Files.writeString(other.resolve("bin/mvn.cmd"), "other");
        String old = versionOutput("3.9.16", home);
        assertThrows(IOException.class, () -> CiBootstrap.ensureDefaultMaven(() -> old,
                before -> { throw new IOException("actual in-place update failed"); }));
        AtomicInteger probes = new AtomicInteger();
        assertThrows(IOException.class, () -> CiBootstrap.ensureDefaultMaven(
                () -> probes.incrementAndGet() == 1 ? old : versionOutput("3.10.0", other), before -> {}));
        assertEquals(2, probes.get());
        Path badArchive = temporary.resolve("bad.zip"); Files.writeString(badArchive, "not the official reviewed archive");
        assertThrows(IOException.class, () -> CiBootstrap.requireMavenArchiveChecksum(badArchive, CiBootstrap.MAVEN_ZIP_SHA512));
        assertEquals("old", Files.readString(home.resolve("bin/mvn.cmd")));
    }

    @Test
    void unixObservationUsesTheActualUnixLauncherAndRejectsUnstableVersion(@TempDir Path temporary) throws Exception {
        Path home = Files.createDirectories(temporary.resolve("unix-maven/bin")).getParent();
        Path launcher = home.resolve("bin/mvn"); Files.writeString(launcher, "unix launcher");
        CiBootstrap.MavenObservation actual = CiBootstrap.observeDefaultMaven(versionOutput("3.9.16", home), false);
        assertEquals(CiBootstrap.measure(launcher), actual.launcherRef());
        assertThrows(IOException.class, () -> CiBootstrap.observeDefaultMaven(versionOutput("3.10.0-rc1", home), false));
    }

    private static String actualVersionProbe(Path batch, Path cwd, Map<String, String> environment, int ordinal)
            throws IOException, InterruptedException {
        Path output = cwd.resolve("probe-" + ordinal + ".stdout");
        try (WindowsJobProcess child = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(
                Path.of(System.getenv("SystemRoot"), "System32/cmd.exe"), List.of("/d", "/c", batch.toString()),
                cwd, environment, output, cwd.resolve("probe-" + ordinal + ".stderr"), 256L << 20))) {
            WindowsJobProcess.CommandResult result = child.await(Duration.ofSeconds(10), Instant.now().plusSeconds(15), () -> {});
            if (!result.passed() || result.accounting().activeProcesses() != 0) throw new IOException("actual default command failed");
        }
        return Files.readString(output);
    }

    private static String versionCommand(String version, Path home) {
        return "@echo off\r\necho Apache Maven " + version + "\r\necho Maven home: " + home + "\r\nexit /b 0\r\n";
    }

    private static String versionOutput(String version, Path home) {
        return "Apache Maven " + version + "\nMaven home: " + home + "\n";
    }

    private static void writeZip(Path archive, String entry) throws IOException {
        try (ZipOutputStream zip = new ZipOutputStream(Files.newOutputStream(archive))) {
            zip.putNextEntry(new ZipEntry(entry)); zip.write("actual".getBytes(StandardCharsets.UTF_8)); zip.closeEntry();
        }
    }

    private static final class BlockingInput extends InputStream {
        private volatile boolean closed;
        @Override public synchronized int read() throws IOException {
            while (!closed) {
                try { wait(); }
                catch (InterruptedException error) { Thread.currentThread().interrupt(); throw new IOException(error); }
            }
            throw new IOException("closed stalled body");
        }
        @Override public synchronized void close() { closed = true; notifyAll(); }
    }
}
