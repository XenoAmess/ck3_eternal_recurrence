package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InterruptedIOException;
import java.nio.file.AccessDeniedException;
import java.nio.file.DirectoryStream;
import java.nio.file.FileVisitor;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.nio.file.attribute.FileTime;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.time.Duration;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class ControlBuildTest {
    @TempDir Path temporary;

    @Test void measuredProducerRoundTripsThroughStrictConsumerAndDetectsSameSizeTampering() throws Exception {
        Path source = temporary.resolve("evidence.txt"); Files.writeString(source, "one");
        ControlBuild.FileRef produced = ControlBuild.FileRef.measure(source.toAbsolutePath());
        ObjectMapper json = ControlBuild.strictMapper();
        ControlBuild.FileRef consumed = json.readValue(json.writeValueAsBytes(produced), ControlBuild.FileRef.class);
        consumed.verify(); assertEquals(produced, consumed);
        Files.writeString(source, "two");
        assertThrows(IOException.class, consumed::verify);
    }

    @Test void sameWindowsPathSpellingVerifiesButRealBytesAndDigestDriftStillFail() throws Exception {
        Path source = temporary.resolve("slash-evidence.txt"); Files.writeString(source, "one");
        ControlBuild.FileRef nativeRef = ControlBuild.FileRef.measure(source.toAbsolutePath());
        ControlBuild.FileRef forwardRef = new ControlBuild.FileRef(nativeRef.path().replace('\\', '/'), nativeRef.bytes(), nativeRef.sha256());
        var json = ControlBuild.strictMapper();
        ControlBuild.FileRef consumed = json.readValue(json.writeValueAsBytes(forwardRef), ControlBuild.FileRef.class);
        nativeRef.verify(); consumed.verify();
        assertThrows(IOException.class, () -> new ControlBuild.FileRef(forwardRef.path(), forwardRef.bytes() + 1, forwardRef.sha256()).verify());
        assertThrows(IOException.class, () -> new ControlBuild.FileRef(forwardRef.path(), forwardRef.bytes(), "0".repeat(64)).verify());
        Files.writeString(source, "two");
        assertThrows(IOException.class, consumed::verify); assertThrows(IOException.class, nativeRef::verify);
        Files.writeString(source, "longer"); assertThrows(IOException.class, consumed::verify);
    }

    @Test void mutableInventorySurvivesRealDeletionBeforeRealPathButRejectsOtherIoFailures() throws Exception {
        Path root = Files.createDirectory(temporary.resolve("mutable-outputs"));
        Path retained = root.resolve("retained.json"), removed = root.resolve("transient.json.tmp");
        Files.writeString(retained, "kept"); Files.writeString(removed, "gone");
        assertEquals(4, ControlBuild.mutableInventoryBytes(root, path -> {
            if (path.equals(removed)) Files.delete(path);
        }));
        assertFalse(Files.exists(removed));
        assertThrows(java.nio.file.AccessDeniedException.class, () -> ControlBuild.mutableInventoryBytes(root, path -> {
            if (path.equals(retained)) throw new java.nio.file.AccessDeniedException(path.toString());
        }));
        Path missing = root.resolve("missing-root");
        assertThrows(IOException.class, () -> ControlBuild.mutableInventoryBytes(missing, path -> {}));
    }

    @Test void actualPartAccountingRetriesScratchRealPathAndRetainsSiblingQuota() throws Exception {
        Path scratch = Files.createDirectory(temporary.resolve("scratch"));
        Path directory = Files.createDirectory(scratch.resolve("junit-org"));
        Files.writeString(directory.resolve("input"), "data");
        Files.writeString(scratch.resolve("sibling"), "kept");
        AtomicInteger reads = new AtomicInteger();
        ControlBuild.InventoryIo io = new ControlBuild.InventoryIo() {
            @Override public Path realPath(Path path) throws IOException {
                if (path.equals(directory) && reads.incrementAndGet() == 1) throw new AccessDeniedException(path.toString());
                return ControlBuild.InventoryIo.super.realPath(path);
            }
        };
        assertEquals(Map.of("scratch", 8L), ControlBuild.sizes(temporary, Map.of("scratch", 8L), () -> {}, io));
        assertEquals(2, reads.get());
        reads.set(0);
        IOException failure = assertThrows(IOException.class,
                () -> ControlBuild.sizes(temporary, Map.of("scratch", 7L), () -> {}, io));
        assertEquals("Workpackage cap exceeded: scratch", failure.getMessage());
        assertEquals(2, reads.get());
    }

    @Test void actualScratchSizeRereadRequiresSuccessOrRealRemoval() throws Exception {
        Path scratch = Files.createDirectory(temporary.resolve("scratch"));
        Path file = scratch.resolve("transient"), sibling = scratch.resolve("sibling");
        Files.writeString(file, "data"); Files.writeString(sibling, "kept");
        AtomicInteger reads = new AtomicInteger();
        ControlBuild.InventoryIo io = new ControlBuild.InventoryIo() {
            @Override public long size(Path path) throws IOException {
                if (path.equals(file) && reads.incrementAndGet() == 1) throw new AccessDeniedException(path.toString());
                return ControlBuild.InventoryIo.super.size(path);
            }
        };
        assertEquals(Map.of("scratch", 8L), ControlBuild.sizes(temporary, Map.of("scratch", 8L), () -> {}, io));
        assertEquals(2, reads.get());
        reads.set(0);
        ControlBuild.InventoryIo removing = new ControlBuild.InventoryIo() {
            @Override public long size(Path path) throws IOException {
                if (path.equals(file) && reads.incrementAndGet() == 1) {
                    Files.delete(file); throw new AccessDeniedException(path.toString());
                }
                return ControlBuild.InventoryIo.super.size(path);
            }
        };
        assertEquals(Map.of("scratch", 4L), ControlBuild.sizes(temporary, Map.of("scratch", 8L), () -> {}, removing));
        assertEquals(2, reads.get()); assertFalse(Files.exists(file));
    }

    @Test void actualScratchTraversalRecoveryNeverRescansConsumedSiblings() throws Exception {
        Path scratch = Files.createDirectory(temporary.resolve("scratch"));
        Path directory = Files.createDirectory(scratch.resolve("junit-org"));
        Files.writeString(directory.resolve("input"), "abc");
        Path sibling = scratch.resolve("sibling"); Files.writeString(sibling, "kept");
        AtomicInteger opens = new AtomicInteger(), recoveredAttributes = new AtomicInteger();
        ControlBuild.InventoryIo io = new ControlBuild.InventoryIo() {
            @Override public void walk(Path root, FileVisitor<Path> visitor) throws IOException {
                if (!root.equals(scratch)) { ControlBuild.InventoryIo.super.walk(root, visitor); return; }
                visitor.preVisitDirectory(root, attributes(root));
                ControlBuild.InventoryIo.super.walk(sibling, visitor);
                visitor.visitFileFailed(directory, new AccessDeniedException(directory.toString()));
                visitor.postVisitDirectory(root, null);
            }
            @Override public BasicFileAttributes attributes(Path path) throws IOException {
                if (path.equals(directory)) recoveredAttributes.incrementAndGet();
                return ControlBuild.InventoryIo.super.attributes(path);
            }
            @Override public DirectoryStream<Path> children(Path path) throws IOException {
                if (path.equals(directory) && opens.incrementAndGet() == 1) throw new AccessDeniedException(path.toString());
                return ControlBuild.InventoryIo.super.children(path);
            }
        };
        assertEquals(Map.of("scratch", 7L), ControlBuild.sizes(temporary, Map.of("scratch", 7L), () -> {}, io));
        assertEquals(1, recoveredAttributes.get()); assertEquals(2, opens.get());
    }

    @Test void scratchRetryRemainsBoundedAndCannotRelaxRootOrOtherPartPermissions() throws Exception {
        Path scratch = Files.createDirectory(temporary.resolve("scratch"));
        Path file = scratch.resolve("input"); Files.writeString(file, "data");
        Path build = Files.createDirectory(temporary.resolve("build"));
        Path other = build.resolve("input"); Files.writeString(other, "kept");
        for (Path denied : List.of(file, scratch, other)) {
            AtomicInteger reads = new AtomicInteger();
            ControlBuild.InventoryIo io = new ControlBuild.InventoryIo() {
                @Override public Path realPath(Path path) throws IOException {
                    if (path.equals(denied)) { reads.incrementAndGet(); throw new AccessDeniedException(path.toString()); }
                    return ControlBuild.InventoryIo.super.realPath(path);
                }
            };
            String part = denied.equals(other) ? "build" : "scratch";
            assertThrows(AccessDeniedException.class, () -> ControlBuild.sizes(temporary, Map.of(part, 8L), () -> {}, io));
            assertEquals(denied.equals(file) ? 4 : 1, reads.get());
        }
        AtomicInteger reads = new AtomicInteger();
        IOException failure = assertThrows(IOException.class, () -> ControlBuild.sizes(temporary, Map.of("scratch", 8L),
                () -> {}, new ControlBuild.InventoryIo() {
                    @Override public Path realPath(Path path) throws IOException {
                        if (path.equals(file)) { reads.incrementAndGet(); throw new IOException("different I/O failure"); }
                        return ControlBuild.InventoryIo.super.realPath(path);
                    }
                }));
        assertEquals("different I/O failure", failure.getMessage()); assertEquals(1, reads.get());
        AtomicInteger rootReads = new AtomicInteger();
        assertThrows(AccessDeniedException.class, () -> ControlBuild.sizes(temporary, Map.of("build", 8L), () -> {},
                new ControlBuild.InventoryIo() {
                    @Override public BasicFileAttributes attributes(Path path) throws IOException {
                        if (path.equals(build)) { rootReads.incrementAndGet(); throw new AccessDeniedException(path.toString()); }
                        return ControlBuild.InventoryIo.super.attributes(path);
                    }
                }));
        assertEquals(1, rootReads.get());
        Files.delete(file); Files.delete(scratch);
        assertThrows(IOException.class, () -> ControlBuild.sizes(temporary, Map.of("scratch", 8L), () -> {}, new ControlBuild.InventoryIo() {}));
    }

    @Test void scratchInventoryRetriesConsumeOriginalDeadlineAndCancellation() throws Exception {
        Path scratch = Files.createDirectory(temporary.resolve("scratch"));
        Path file = scratch.resolve("input"); Files.writeString(file, "data");
        AtomicInteger reads = new AtomicInteger();
        ControlBuild.InventoryIo denied = new ControlBuild.InventoryIo() {
            @Override public Path realPath(Path path) throws IOException {
                if (path.equals(file)) { reads.incrementAndGet(); throw new AccessDeniedException(path.toString()); }
                return ControlBuild.InventoryIo.super.realPath(path);
            }
        };
        IOException failure = assertThrows(IOException.class, () -> ControlBuild.sizes(temporary, Map.of("scratch", 8L),
                () -> { if (reads.get() > 0) throw new IOException("original command deadline"); }, denied));
        assertEquals("original command deadline", failure.getMessage()); assertEquals(1, reads.get());
        Thread.currentThread().interrupt();
        try {
            assertThrows(InterruptedIOException.class, () -> ControlBuild.sizes(temporary, Map.of("scratch", 8L), () -> {}, denied));
            assertTrue(Thread.currentThread().isInterrupted()); assertEquals(1, reads.get());
        } finally { Thread.interrupted(); }
    }

    @Test void recoveredScratchMetadataStillRejectsLinksAndCanonicalEscapes() throws Exception {
        Path scratch = Files.createDirectory(temporary.resolve("scratch"));
        Path file = scratch.resolve("input"); Files.writeString(file, "data");
        ControlBuild.InventoryIo linked = new ControlBuild.InventoryIo() {
            @Override public void walk(Path root, FileVisitor<Path> visitor) throws IOException {
                visitor.preVisitDirectory(root, attributes(root));
                visitor.visitFileFailed(file, new AccessDeniedException(file.toString()));
            }
            @Override public BasicFileAttributes attributes(Path path) throws IOException {
                BasicFileAttributes actual = ControlBuild.InventoryIo.super.attributes(path);
                return path.equals(file) ? new LinkedAttributes(actual) : actual;
            }
        };
        IOException linkFailure = assertThrows(IOException.class,
                () -> ControlBuild.sizes(temporary, Map.of("scratch", 8L), () -> {}, linked));
        assertEquals("Inventory link, extent or time limit", linkFailure.getMessage());
        IOException escapeFailure = assertThrows(IOException.class,
                () -> ControlBuild.sizes(temporary, Map.of("scratch", 8L), () -> {}, new ControlBuild.InventoryIo() {
                    @Override public Path realPath(Path path) throws IOException {
                        return path.equals(file) ? temporary.toRealPath() : ControlBuild.InventoryIo.super.realPath(path);
                    }
                }));
        assertEquals("Inventory path escaped root", escapeFailure.getMessage());
    }

    @Test void nativeJobPeriodicAccountingSurvivesTransientScratchDenial() throws Exception {
        Path scratch = Files.createDirectory(temporary.resolve("scratch"));
        Path file = scratch.resolve("junit-org"); Files.writeString(file, "data");
        Path batch = temporary.resolve("finite-child.cmd");
        Files.writeString(batch, "@echo off\r\nping -n 2 127.0.0.1 >nul\r\nexit /b 0\r\n");
        AtomicInteger reads = new AtomicInteger(), guards = new AtomicInteger();
        ControlBuild.InventoryIo io = new ControlBuild.InventoryIo() {
            @Override public Path realPath(Path path) throws IOException {
                if (path.equals(file) && reads.incrementAndGet() == 1) throw new AccessDeniedException(path.toString());
                return ControlBuild.InventoryIo.super.realPath(path);
            }
        };
        Instant authority = Instant.now().plusSeconds(10);
        try (WindowsJobProcess child = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(
                Path.of(System.getenv("SystemRoot"), "System32/cmd.exe"), List.of("/d", "/c", batch.toString()),
                temporary, Map.copyOf(System.getenv()), temporary.resolve("child.stdout"), temporary.resolve("child.stderr"), 256L << 20))) {
            WindowsJobProcess.CommandResult actual = child.await(Duration.ofSeconds(5), authority, () -> {
                guards.incrementAndGet();
                try {
                    ControlBuild.sizes(temporary, Map.of("scratch", 4L), () -> {
                        if (!Instant.now().isBefore(authority)) throw new IOException("original authority expired");
                    }, io);
                } catch (IOException error) { throw new IllegalStateException(error); }
            });
            assertTrue(actual.passed()); assertNull(actual.stopReason());
            assertEquals(0, actual.accounting().activeProcesses());
        }
        assertTrue(guards.get() > 0); assertTrue(reads.get() >= 2);
    }

    private record LinkedAttributes(BasicFileAttributes actual) implements BasicFileAttributes {
        @Override public FileTime lastModifiedTime() { return actual.lastModifiedTime(); }
        @Override public FileTime lastAccessTime() { return actual.lastAccessTime(); }
        @Override public FileTime creationTime() { return actual.creationTime(); }
        @Override public boolean isRegularFile() { return actual.isRegularFile(); }
        @Override public boolean isDirectory() { return actual.isDirectory(); }
        @Override public boolean isSymbolicLink() { return true; }
        @Override public boolean isOther() { return actual.isOther(); }
        @Override public long size() { return actual.size(); }
        @Override public Object fileKey() { return actual.fileKey(); }
    }

    @Test void actualRefParserRejectsTokenCoercionDuplicatesUnknownAndTrailingBodies() throws Exception {
        Path source = temporary.resolve("input.txt"); Files.writeString(source, "x");
        ObjectMapper json = ControlBuild.strictMapper();
        String valid = json.writeValueAsString(ControlBuild.FileRef.measure(source.toAbsolutePath()));
        for (String token : new String[]{"true", "1.0", "\"1\"", "null", "[]"}) {
            assertThrows(JsonProcessingException.class, () -> json.readValue(valid.replace("\"bytes\":1", "\"bytes\":" + token), ControlBuild.FileRef.class), token);
        }
        assertThrows(JsonProcessingException.class, () -> json.readValue(valid.substring(0, valid.length() - 1) + ",\"bytes\":1}", ControlBuild.FileRef.class));
        assertThrows(JsonProcessingException.class, () -> json.readValue(valid.substring(0, valid.length() - 1) + ",\"unknown\":1}", ControlBuild.FileRef.class));
        assertThrows(JsonProcessingException.class, () -> json.readValue(valid + " {}", ControlBuild.FileRef.class));
        String identity = "{\"pid\":1,\"creation_filetime_decimal\":18446744073709551615,\"executable\":\"C:/java.exe\"}";
        assertThrows(JsonProcessingException.class, () -> json.readValue(identity, WindowsJobProcess.ProcessIdentity.class));
    }

    @Test void commandReceiptCannotBecomeSuccessByDroppingExitOrCoercingTiming() throws Exception {
        ObjectMapper json = ControlBuild.strictMapper();
        WindowsJobProcess.CommandResult failed = new WindowsJobProcess.CommandResult(
                new WindowsJobProcess.ProcessIdentity(123, "18446744073709551615", "C:/java.exe"),
                42, 0.5, new WindowsJobProcess.Accounting(4096, 0, 8192, WindowsJobProcess.REQUIRED_FLAGS), null);
        String serialized = json.writeValueAsString(failed);
        assertFalse(json.readValue(serialized, WindowsJobProcess.CommandResult.class).passed());
        assertThrows(JsonProcessingException.class, () -> json.readValue(serialized.replace("\"exit_code\":42,", ""), WindowsJobProcess.CommandResult.class));
        assertThrows(JsonProcessingException.class, () -> json.readValue(serialized.replace("\"stop_reason\":null", "\"unused\":null"), WindowsJobProcess.CommandResult.class));
        for (String wrong : new String[]{"\"0.5\"", "true", "null", "-0.5"}) {
            assertThrows(JsonProcessingException.class, () -> json.readValue(serialized.replace("\"elapsed_seconds\":0.5", "\"elapsed_seconds\":" + wrong), WindowsJobProcess.CommandResult.class));
        }
    }

    @Test void postcheckReadsActualSourceAfterFailureAndKeepsUnknownDistinctFromMismatch() throws Exception {
        Path root = temporary.resolve("module"); Files.createDirectories(root.resolve("src/main"));
        Path pom = root.resolve("pom.xml");
        Files.writeString(pom, "<project xmlns=\"http://maven.apache.org/POM/4.0.0\"><modelVersion>4.0.0</modelVersion></project>");
        Path source = root.resolve("src/main/input.txt"); Files.writeString(source, "one");
        List<ControlBuild.FileRef> original = List.of(ControlBuild.FileRef.measure(pom), ControlBuild.FileRef.measure(source));
        assertEquals(ControlBuild.SourceState.MATCH, ControlBuild.postcheckSource(root, original).state());
        Files.writeString(source, "two");
        assertEquals(ControlBuild.SourceState.MISMATCH, ControlBuild.postcheckSource(root, original).state());
        Files.delete(pom);
        ControlBuild.SourcePostcheck unavailable = ControlBuild.postcheckSource(root, original);
        assertEquals(ControlBuild.SourceState.UNKNOWN, unavailable.state()); assertNotNull(unavailable.error());
        ObjectMapper json = ControlBuild.strictMapper();
        assertEquals(unavailable, json.readValue(json.writeValueAsBytes(unavailable), ControlBuild.SourcePostcheck.class));
        assertThrows(JsonProcessingException.class, () -> json.readValue("{\"state\":\"MATCH\",\"error\":\"not checked\"}", ControlBuild.SourcePostcheck.class));
        assertThrows(JsonProcessingException.class, () -> json.readValue("{\"state\":true,\"error\":null}", ControlBuild.SourcePostcheck.class));
        assertThrows(JsonProcessingException.class, () -> json.readValue("{\"state\":0,\"error\":null}", ControlBuild.SourcePostcheck.class));
    }

    @Test void defaultMvnUsesActualCmdPathAndPathextIgnoringExtensionlessWhereCandidate() throws Exception {
        Path home = temporary.resolve("maven-home"); Path bin = Files.createDirectories(home.resolve("bin"));
        Files.writeString(bin.resolve("mvn"), "EXTENSIONLESS_MUST_NOT_EXECUTE");
        Files.writeString(bin.resolve("mvn.bat"), "@echo WRONG_PATHEXT_ORDER\r\nexit /b 9\r\n");
        Files.writeString(bin.resolve("mvn.cmd"), "@echo off\r\necho Apache Maven 9.9.9 (fixture)\r\necho Maven home: " + home + "\r\necho SELECTED_CMD\r\nexit /b 0\r\n");
        Path working = Files.createDirectory(temporary.resolve("working")); Path batch = working.resolve("version.cmd");
        ControlBuild.writeMavenBatch(batch, null, List.of("-version"));
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); environment.putAll(System.getenv());
        environment.put("PATH", bin + ";" + Path.of(System.getenv("SystemRoot"), "System32"));
        environment.put("PATHEXT", ".CMD;.BAT;.EXE;.COM");
        Path output = working.resolve("version.stdout");
        try (WindowsJobProcess child = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(
                Path.of(System.getenv("SystemRoot"), "System32/cmd.exe"), List.of("/d", "/c", batch.toString()), working,
                environment, output, working.resolve("version.stderr"), 256L << 20))) {
            WindowsJobProcess.CommandResult actual = child.await(Duration.ofSeconds(10), Instant.now().plusSeconds(15), () -> {});
            assertTrue(actual.passed()); assertEquals(0, actual.accounting().activeProcesses());
        }
        String actual = Files.readString(output); assertTrue(actual.contains("SELECTED_CMD")); assertFalse(actual.contains("WRONG_PATHEXT"));
        ControlBuild.MavenToolchain evidence = ControlBuild.measuredMavenToolchain(null, actual, "9.9.9");
        assertEquals(ControlBuild.MavenSelection.DEFAULT_COMMAND, evidence.selection());
        assertEquals("mvn", evidence.requestedCommand()); assertNull(evidence.explicitOverrideRef());
        assertEquals(ControlBuild.FileRef.measure(bin.resolve("mvn.cmd")), evidence.distributionLauncherRef());
    }

    @Test void actualDefaultMavenReceivesFailAtEndAndRetainsItsNonzeroTerminalExit() throws Exception {
        Path bin = Files.createDirectories(temporary.resolve("command-home/bin"));
        Files.writeString(bin.resolve("mvn.cmd"), "@echo off\r\nif not \"%~1\"==\"--fail-at-end\" exit /b 91\r\n"
                + "echo FAIL_AT_END_RECEIVED\r\n:arguments\r\nif \"%~1\"==\"\" exit /b 92\r\n"
                + "if \"%~1\"==\"verify\" goto failed\r\nshift\r\ngoto arguments\r\n:failed\r\n"
                + "shift\r\nif not \"%~1\"==\"\" exit /b 93\r\necho VERIFY_RETURNED_FAILURE\r\nexit /b 37\r\n");
        Path working = Files.createDirectory(temporary.resolve("reactor working"));
        ControlBuild.Config config = new ControlBuild.Config(working, working, working.resolve("release.json"),
                "command-fixture", "test", null, working, "3.10.0", 60, ControlBuild.TargetKind.SERVICE_FAST_JAR, ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
        Path batch = temporary.resolve("reactor.cmd").toAbsolutePath();
        ControlBuild.writeMavenBatch(batch, null, ControlBuild.reactorVerifyArguments(config,
                working.resolve("direct settings.xml"), working, working.resolve("output directory")));
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); environment.putAll(System.getenv());
        environment.put("PATH", bin + ";" + Path.of(System.getenv("SystemRoot"), "System32"));
        environment.put("PATHEXT", ".CMD;.BAT;.EXE;.COM");
        Path output = temporary.resolve("reactor.stdout").toAbsolutePath();
        try (WindowsJobProcess child = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(
                Path.of(System.getenv("SystemRoot"), "System32/cmd.exe"), List.of("/d", "/c", batch.toString()), working,
                environment, output, temporary.resolve("reactor.stderr").toAbsolutePath(), 256L << 20))) {
            WindowsJobProcess.CommandResult actual = child.await(Duration.ofSeconds(10), Instant.now().plusSeconds(15), () -> {});
            assertEquals(37, actual.exitCode()); assertFalse(actual.passed()); assertNull(actual.stopReason());
            assertEquals(0, actual.accounting().activeProcesses());
        }
        String actual = Files.readString(output);
        assertTrue(actual.contains("FAIL_AT_END_RECEIVED")); assertTrue(actual.contains("VERIFY_RETURNED_FAILURE"));
    }

    @Test void minimumMavenVersionUsesNumericStableComponentsRatherThanStringEquality() {
        for (String accepted : new String[]{"3.10.0", "3.10.1", "3.11.0", "4.0.0", "3.100.0"}) {
            assertTrue(ControlBuild.mavenVersionAtLeast(accepted, "3.10.0"), accepted);
        }
        for (String rejected : new String[]{"3.9.16", "3.9.999", "2.99.99", "4.0.0-rc-1", "3.10", "true", "3.10.0.1"}) {
            assertFalse(ControlBuild.mavenVersionAtLeast(rejected, "3.10.0"), rejected);
        }
        Path root = temporary.toAbsolutePath();
        assertThrows(IllegalArgumentException.class, () -> new ControlBuild.Config(root.resolve("source"), root.resolve("work"),
                root.resolve("release.json"), "bad-minimum", "test", null, root.resolve("jdk"), "3.9.16", 60, ControlBuild.TargetKind.SERVICE_FAST_JAR, ControlBuild.SourceLimitProfile.STANDARD_8_MIB));
    }
}
