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

    /** Run the two persistent timeout-contract tests with the real JUnit engine; default Surefire still runs all tests. */
    public static void main(String[] arguments) throws IOException {
        if (arguments.length != 0) throw new IOException("No timeout regression arguments are accepted");
        // Initialize dispatch in the shared caller native root before the CLI test rebinds its owned scratch.
        if (com.sun.jna.Native.POINTER_SIZE <= 0) throw new IOException("JNA native dispatch initialization required");
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request().selectors(
                org.junit.platform.engine.discovery.DiscoverySelectors.selectMethod(ControlBuildTest.class,
                        "explicitTargetTimeoutsSurviveStrictConfigAndKeepIntegerBoundariesClosed"),
                org.junit.platform.engine.discovery.DiscoverySelectors.selectMethod(ControlBuildTest.class,
                        "actualBuildCliKeepsDefault900AndAdmitsExplicitFiniteTarget3600")).build();
        var listener = new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        launcher.registerTestExecutionListeners(listener); launcher.execute(request);
        var summary = listener.getSummary(); var output = new java.io.PrintWriter(System.out, true);
        summary.printTo(output); summary.printFailuresTo(output);
        if (summary.getTestsFoundCount() != 2 || summary.getTestsStartedCount() != 2
                || summary.getTestsSucceededCount() != 2 || summary.getTestsFailedCount() != 0
                || summary.getTestsSkippedCount() != 0 || summary.getTestsAbortedCount() != 0
                || summary.getContainersFailedCount() != 0)
            throw new IOException("Both persistent timeout-contract JUnit tests must execute successfully without skips");
        System.out.println("CONTROL_BUILD_TARGET_TIMEOUT_REGRESSION_PASS tests=2");
    }

    @Test void explicitTargetTimeoutsSurviveStrictConfigAndKeepIntegerBoundariesClosed() throws Exception {
        var json = ControlBuild.strictMapper();
        var tools = new ControlBuild.Config(temporary.resolve("source"), temporary.resolve("work"),
                temporary.resolve("release.json"), "timeout-boundary", "/root", null, temporary,
                "3.10.0", 3600, ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME,
                ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
        assertEquals(tools, json.readValue(json.writeValueAsBytes(tools), ControlBuild.Config.class));
        for (int seconds : List.of(0, -1, 3601)) {
            var wrong = (com.fasterxml.jackson.databind.node.ObjectNode) json.valueToTree(tools);
            wrong.put("timeout_seconds", seconds);
            assertThrows(IOException.class, () -> json.treeToValue(wrong, ControlBuild.Config.class));
        }
        for (String corruption : List.of("missing", "null", "boolean", "floating", "service-overflow")) {
            var wrong = (com.fasterxml.jackson.databind.node.ObjectNode) json.valueToTree(tools);
            switch (corruption) {
                case "missing" -> wrong.remove("timeout_seconds");
                case "null" -> wrong.putNull("timeout_seconds");
                case "boolean" -> wrong.put("timeout_seconds", true);
                case "floating" -> wrong.put("timeout_seconds", 3600.5);
                case "service-overflow" -> { wrong.put("target_kind", "SERVICE_FAST_JAR"); wrong.put("timeout_seconds", 3601); }
                default -> throw new AssertionError(corruption);
            }
            assertThrows(IOException.class, () -> json.treeToValue(wrong, ControlBuild.Config.class), corruption);
        }
        var service = (com.fasterxml.jackson.databind.node.ObjectNode) json.valueToTree(tools);
        service.put("target_kind", "SERVICE_FAST_JAR");
        for (int seconds : List.of(1, 900, 901, 1800, 3600)) {
            service.put("timeout_seconds", seconds);
            var produced = json.treeToValue(service, ControlBuild.Config.class);
            assertEquals(seconds, produced.timeoutSeconds());
            assertEquals(produced, json.readValue(json.writeValueAsBytes(produced), ControlBuild.Config.class));
        }
        for (var kind : ControlBuild.TargetKind.values()) assertEquals(3600, ControlBuild.maximumBuildTimeoutSeconds(kind));
        assertThrows(IllegalArgumentException.class, () -> ControlBuild.maximumBuildTimeoutSeconds(null));
    }

    @Test void actualBuildCliKeepsDefault900AndAdmitsExplicitFiniteTarget3600() throws Exception {
        Path source = Files.createDirectory(temporary.resolve("cli-source"));
        Path work = Files.createDirectory(temporary.resolve("cli-work"));
        Path scratch = Files.createDirectory(work.resolve("scratch"));
        Path release = temporary.resolve("cli-release.json"); Files.writeString(release, "{}");
        var base = new java.util.ArrayList<>(List.of("--source-root", source.toString(), "--work-root", work.toString(),
                "--capacity-release", release.toString(), "--attempt", "cli-timeout", "--owner-task", "/root",
                "--java-home", System.getProperty("java.home")));
        String previous = System.getProperty("jna.tmpdir");
        try {
            System.setProperty("jna.tmpdir", scratch.toString());
            assertEquals(900, ControlBuild.parseArguments(base.toArray(String[]::new)).timeoutSeconds());
            var tools = new java.util.ArrayList<>(base);
            tools.addAll(List.of("--target-kind", "BUILD_TOOLS_RUNTIME", "--timeout-seconds", "3600"));
            assertEquals(3600, ControlBuild.parseArguments(tools.toArray(String[]::new)).timeoutSeconds());
            var service = new java.util.ArrayList<>(base);
            service.addAll(List.of("--target-kind", "SERVICE_FAST_JAR", "--timeout-seconds", "901"));
            assertEquals(901, ControlBuild.parseArguments(service.toArray(String[]::new)).timeoutSeconds());
            service.set(service.size() - 1, "3600");
            assertEquals(3600, ControlBuild.parseArguments(service.toArray(String[]::new)).timeoutSeconds());
            service.set(service.size() - 1, "3601");
            assertThrows(IllegalArgumentException.class, () -> ControlBuild.parseArguments(service.toArray(String[]::new)));
            tools.set(tools.size() - 1, "3601");
            assertThrows(IllegalArgumentException.class, () -> ControlBuild.parseArguments(tools.toArray(String[]::new)));
        } finally {
            if (previous == null) System.clearProperty("jna.tmpdir"); else System.setProperty("jna.tmpdir", previous);
        }
    }

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


    @Test void workpackageInventoryCountsRealDirectoriesSeparatelyFromRegularFiles() throws Exception {
        Path root = Files.createDirectory(temporary.resolve("counted-workpackage"));
        Path first = Files.createDirectory(root.resolve("first")), second = Files.createDirectory(root.resolve("second"));
        Files.writeString(first.resolve("a"), "A"); Files.writeString(second.resolve("b"), "BB");
        var limits = new ControlBuild.WorkpackageInventoryLimits(2, 3, 5);
        assertEquals(3L, ControlBuild.mutableInventoryBytes(root, path -> {}, limits));
        assertEquals(new ControlBuild.WorkpackageInventoryLimits(250000, 131072, 381072),
                ControlBuild.WORKPACKAGE_INVENTORY_LIMITS);
        // Three real directories no longer consume the two-file allowance.
        assertEquals(3L, ControlBuild.mutableInventoryBytes(root, path -> {}));
    }

    @Test void workpackageInventoryRejectsEachIndependentExtentWithExactDiagnostics() throws Exception {
        Path root = Files.createDirectory(temporary.resolve("bounded-workpackage"));
        Path first = Files.createDirectory(root.resolve("first")), second = Files.createDirectory(root.resolve("second"));
        Files.writeString(first.resolve("a"), "A"); Files.writeString(second.resolve("b"), "BB");
        List<ControlBuild.WorkpackageInventoryLimits> limits = List.of(
                new ControlBuild.WorkpackageInventoryLimits(1, 3, 5),
                new ControlBuild.WorkpackageInventoryLimits(2, 2, 5),
                new ControlBuild.WorkpackageInventoryLimits(2, 3, 4));
        List<String> categories = List.of("REGULAR_FILES", "DIRECTORIES", "TOTAL_ENTRIES");
        List<String> counters = List.of("counter=2 limit=1", "counter=3 limit=2", "counter=5 limit=4");
        for (int i = 0; i < limits.size(); i++) {
            var limit = limits.get(i);
            IOException rejected = assertThrows(IOException.class,
                    () -> ControlBuild.mutableInventoryBytes(root, path -> {}, limit));
            assertTrue(rejected.getMessage().contains("category=" + categories.get(i)), rejected::getMessage);
            assertTrue(rejected.getMessage().contains("path=" + root), rejected::getMessage);
            assertTrue(rejected.getMessage().contains(counters.get(i)), rejected::getMessage);
        }
        assertThrows(IllegalArgumentException.class, () -> new ControlBuild.WorkpackageInventoryLimits(-1, 3, 5));
        assertThrows(IllegalArgumentException.class, () -> new ControlBuild.WorkpackageInventoryLimits(2, 0, 5));
        assertThrows(IllegalArgumentException.class, () -> new ControlBuild.WorkpackageInventoryLimits(2, 3, 0));
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
        assertEquals("Workpackage inventory category=SYMBOLIC_LINK path=" + file + " counter=1 limit=0", linkFailure.getMessage());
        IOException escapeFailure = assertThrows(IOException.class,
                () -> ControlBuild.sizes(temporary, Map.of("scratch", 8L), () -> {}, new ControlBuild.InventoryIo() {
                    @Override public Path realPath(Path path) throws IOException {
                        return path.equals(file) ? temporary.toRealPath() : ControlBuild.InventoryIo.super.realPath(path);
                    }
                }));
        assertEquals("Workpackage inventory category=PATH_ESCAPE path=" + file + " counter=1 limit=0", escapeFailure.getMessage());
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

    @Test void ciStageUsesActualLeaseAndRejectsPendingMetadataBeforeArtifactCapIsExceeded() throws Exception {
        Path repo = Files.createDirectories(temporary.resolve("ci-resource-source"));
        Files.createDirectories(repo.resolve("java/ck3-control/build-tools"));
        Path work = Files.createDirectory(temporary.resolve("ci-resource-work"));
        for (String part : List.of("m2", "build", "tools", "scratch", "artifacts", "logs")) Files.createDirectory(work.resolve(part));
        Path evidence = work.resolve("artifacts/actual-input.json"); Files.writeString(evidence, "retained-real-artifact");
        ControlBuild.FileRef evidenceRef = ControlBuild.FileRef.measure(evidence);
        Map<String, Long> caps = Map.of("m2", 1L << 20, "build", 1L << 20, "tools", 1L << 20,
                "scratch", 1L << 20, "artifacts", 1L << 20, "logs", 1L << 20);
        Map<String, Long> measured = ControlBuild.sizes(work, caps, () -> {}, new ControlBuild.InventoryIo() {});
        Path policy = temporary.resolve("ci-resource-policy.json");
        Files.writeString(policy, "{\"schema\":\"xar-storage-retention-policy-v1\"}");
        var mapper = ControlBuild.strictMapper();
        var release = mapper.createObjectNode();
        release.put("schema", "xar.java-phase1.manual-capacity-release/v1");
        release.put("status", "RELEASED_JAVA_PHASE1_BOUNDED_BUILD_AND_LOCAL_SERVICE");
        String machine = WindowsJobProcess.currentMachineId(); Instant now = Instant.now();
        release.put("machine_id", machine); release.put("single_Maven_writer", "resource-test");
        release.put("review_at_utc", now.plusSeconds(60).toString());
        release.putArray("approved_output_roots").add(temporary.toString());
        release.put("Maven_repository", work.resolve("m2").toString()); release.put("build_root", work.resolve("build").toString());
        release.put("temporary_root", work.resolve("scratch").toString());
        var parts = release.putObject("parts");
        for (String part : List.of("m2", "build", "tools", "scratch")) parts.put(part, caps.get(part));
        parts.put("artifacts", measured.get("artifacts") + 1); parts.put("metadata_logs", caps.get("logs"));
        release.set("policy_ref", mapper.valueToTree(ControlBuild.FileRef.measure(policy)));
        var volume = release.putObject("volumes").putObject(work.getRoot().toString());
        volume.put("required_free", 4); volume.put("this_write_peak", 1); volume.put("other_unspent_reservations", 1);
        volume.put("system_growth_reserve", 1); volume.put("safety_reserve", 1);
        volume.put("current_project_usage_conservative_upper", 1); volume.put("effective_project_quota", 100);
        release.put("test_RAM_joint_hard_bytes", 256L << 20); release.put("Maven_heap_bytes", 96L << 20);
        Path releasePath = temporary.resolve("ci-resource-release.json");
        Files.write(releasePath, mapper.writeValueAsBytes(release));
        CiBootstrap.FilePin pin = CiBootstrap.measure(policy);
        CiBootstrap.Plan plan = new CiBootstrap.Plan(CiBootstrap.PLAN_SCHEMA, machine, now.toString(), now.plusSeconds(60).toString(),
                repo.toString(), work.toString(), temporary.toString(), null, temporary.resolve("python.exe").toString(),
                "resource-test", pin, Map.of(), Map.of(), Map.of(), List.of(pin), List.of(pin), false, false);
        ControlBuild.revalidateCiResources(plan, releasePath, 0);
        IOException failure = assertThrows(IOException.class, () -> ControlBuild.revalidateCiResources(plan, releasePath, 2));
        assertTrue(failure.getMessage().contains("pending CI metadata"));
        evidenceRef.verify();
    }

    @Test void ciPackageAllocationUsesIssuedPermitAboveMetadataLimitAndStillRejectsCurrentResourceFailures() throws Exception {
        Path repo = Files.createDirectories(temporary.resolve("ci-resource-source"));
        Files.createDirectories(repo.resolve("java/ck3-control/build-tools"));
        Path work = Files.createDirectory(temporary.resolve("ci-resource-work"));
        for (String part : List.of("m2", "build", "tools", "scratch", "artifacts", "logs")) Files.createDirectory(work.resolve(part));
        Path evidence = work.resolve("artifacts/actual-input.json"); Files.writeString(evidence, "retained-real-artifact");
        ControlBuild.FileRef evidenceRef = ControlBuild.FileRef.measure(evidence);
        Map<String, Long> caps = Map.of("m2", 1L << 20, "build", 1L << 20, "tools", 1L << 20,
                "scratch", 1L << 20, "artifacts", 1L << 20, "logs", 1L << 20);
        Map<String, Long> measured = ControlBuild.sizes(work, caps, () -> {}, new ControlBuild.InventoryIo() {});
        long issuedUpper = 20L << 20, accounted = 2L << 20, pending = issuedUpper - accounted;
        Path policy = temporary.resolve("ci-resource-policy.json");
        Files.writeString(policy, "{\"schema\":\"xar-storage-retention-policy-v1\"}");
        var mapper = ControlBuild.strictMapper();
        var release = mapper.createObjectNode();
        release.put("schema", "xar.java-phase1.manual-capacity-release/v1");
        release.put("status", "RELEASED_JAVA_PHASE1_BOUNDED_BUILD_AND_LOCAL_SERVICE");
        String machine = WindowsJobProcess.currentMachineId(); Instant now = Instant.now();
        release.put("machine_id", machine); release.put("single_Maven_writer", "resource-test");
        release.put("review_at_utc", now.plusSeconds(60).toString());
        release.putArray("approved_output_roots").add(temporary.toString());
        release.put("Maven_repository", work.resolve("m2").toString()); release.put("build_root", work.resolve("build").toString());
        release.put("temporary_root", work.resolve("scratch").toString());
        var parts = release.putObject("parts");
        for (String part : List.of("m2", "build", "tools", "scratch")) parts.put(part, caps.get(part));
        parts.put("artifacts", Math.addExact(measured.get("artifacts"), pending) + 1); parts.put("metadata_logs", caps.get("logs"));
        release.set("policy_ref", mapper.valueToTree(ControlBuild.FileRef.measure(policy)));
        var volume = release.putObject("volumes").putObject(work.getRoot().toString());
        volume.put("required_free", (32L << 20) + 3); volume.put("this_write_peak", 32L << 20); volume.put("other_unspent_reservations", 1);
        volume.put("system_growth_reserve", 1); volume.put("safety_reserve", 1);
        volume.put("current_project_usage_conservative_upper", 1); volume.put("effective_project_quota", 128L << 20);
        release.put("test_RAM_joint_hard_bytes", 256L << 20); release.put("Maven_heap_bytes", 96L << 20);
        Path releasePath = temporary.resolve("ci-resource-release.json");
        Files.write(releasePath, mapper.writeValueAsBytes(release));
        CiBootstrap.FilePin pin = CiBootstrap.measure(policy);
        CiBootstrap.Plan plan = new CiBootstrap.Plan(CiBootstrap.PLAN_SCHEMA, machine, now.toString(), now.plusSeconds(60).toString(),
                repo.toString(), work.toString(), temporary.toString(), null, temporary.resolve("python.exe").toString(),
                "resource-test", pin, Map.of(), Map.of(), Map.of(), List.of(pin), List.of(pin), false, false);
        var permit = new org.xar.ck3.control.build.runtime.JavaRuntimePackage.WritePermit(machine,
                work.resolve("artifacts/runtime-package").toString(), now.plusSeconds(60).toString(),
                issuedUpper, 4096, 4096, evidenceRef);
        var allocation = new ControlBuild.PackagePendingAllocation(permit, accounted);
        ControlBuild.revalidateCiPackageResources(plan, releasePath, allocation);
        IOException metadata = assertThrows(IOException.class, () -> ControlBuild.revalidateCiResources(plan, releasePath, pending));
        assertTrue(metadata.getMessage().contains("bounded pending metadata"));
        String foreignMachine = machine.equals("foreign-machine") ? "another-machine" : "foreign-machine";
        var foreign = new org.xar.ck3.control.build.runtime.JavaRuntimePackage.WritePermit(foreignMachine,
                permit.exactOutputRoot(), permit.expiresAtUtc(), issuedUpper, 4096, 4096, evidenceRef);
        assertThrows(IOException.class, () -> ControlBuild.revalidateCiPackageResources(plan, releasePath,
                new ControlBuild.PackagePendingAllocation(foreign, accounted)));
        var expired = new org.xar.ck3.control.build.runtime.JavaRuntimePackage.WritePermit(machine,
                permit.exactOutputRoot(), now.minusSeconds(1).toString(), issuedUpper, 4096, 4096, evidenceRef);
        assertThrows(IOException.class, () -> ControlBuild.revalidateCiPackageResources(plan, releasePath,
                new ControlBuild.PackagePendingAllocation(expired, accounted)));
        assertThrows(IllegalArgumentException.class, () -> new ControlBuild.PackagePendingAllocation(permit, -1));
        assertThrows(IllegalArgumentException.class, () -> new ControlBuild.PackagePendingAllocation(permit, issuedUpper + 1));
        Files.write(work.resolve("artifacts/after-admission.bin"), new byte[]{1, 2});
        IOException exhausted = assertThrows(IOException.class, () -> ControlBuild.revalidateCiPackageResources(plan, releasePath, allocation));
        assertTrue(exhausted.getMessage().contains("artifact cap"));
        evidenceRef.verify();
    }

    @Test void actualDefaultMavenReceivesFailAtEndAndRetainsItsNonzeroTerminalExit() throws Exception {
        Path bin = Files.createDirectories(temporary.resolve("command-home/bin"));
        Files.writeString(bin.resolve("mvn.cmd"), "@echo off\r\nif not \"%~1\"==\"--fail-at-end\" exit /b 91\r\n"
                + "echo FAIL_AT_END_RECEIVED\r\n:arguments\r\necho ARG:%~1\r\nif \"%~1\"==\"\" exit /b 92\r\n"
                + "if \"%~1\"==\"verify\" goto failed\r\nshift\r\ngoto arguments\r\n:failed\r\n"
                + "shift\r\nif not \"%~1\"==\"\" exit /b 93\r\necho VERIFY_RETURNED_FAILURE\r\nexit /b 37\r\n");
        Path working = Files.createDirectory(temporary.resolve("reactor working"));
        ControlBuild.Config config = new ControlBuild.Config(working, working, working.resolve("release.json"),
                "command-fixture", "test", null, working, "3.10.0", 60, ControlBuild.TargetKind.SERVICE_FAST_JAR, ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
        Path batch = temporary.resolve("reactor.cmd").toAbsolutePath();
        String selectedPython = working.resolve("selected Python/python.exe").toString();
        Map<String, String> selectedEnvironment = Map.of("XAR_ORACLE_PYTHON", selectedPython);
        assertThrows(IllegalArgumentException.class, () -> ControlBuild.reactorVerifyArguments(config,
                working, working, working, Map.of()));
        assertThrows(IllegalArgumentException.class, () -> ControlBuild.reactorVerifyArguments(config,
                working, working, working, Map.of("XAR_ORACLE_PYTHON", "relative/python.exe")));
        ControlBuild.writeMavenBatch(batch, null, ControlBuild.reactorVerifyArguments(config,
                working.resolve("direct settings.xml"), working, working.resolve("output directory"), selectedEnvironment));
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
        assertTrue(Files.readString(output).contains("ARG:-Dxar.rootContext.testRoot="
                + working.resolve("output directory/root-context-provider-test")));
        assertTrue(Files.readString(output).contains("ARG:-Dxar.rootContext.pythonExecutable=" + selectedPython));
        assertTrue(Files.readString(output).contains("ARG:-Dxar.g2.http.evidence-dir="
                + working.resolve("output directory/g2-http-evidence")));
        assertTrue(Files.readString(output).contains("ARG:-Dxar.scratch="
                + working.resolve("output directory/integration-test-scratch")));
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

    /** Synthetic archive fixture with a real native0/Job0 terminal; never production qualification. */
    static record CompletedReceiptFixture(Path receiptPath, ControlBuild.BuildReceipt receipt, Path releasePath,
            Path sourceRoot, Path compiledRoot, Path deploymentRoot) {
        ControlBuild.FileRef receiptRef() throws IOException { return ControlBuild.FileRef.measure(receiptPath); }
    }

    static CompletedReceiptFixture completedReceiptFixture(Path root) throws Exception {
        root = Files.createDirectories(root.toAbsolutePath());
        Path source = Files.createDirectory(root.resolve("source"));
        Path compiled = Files.createDirectory(root.resolve("compiled"));
        String pom = "<project><modelVersion>4.0.0</modelVersion><groupId>fixture</groupId><artifactId>receipt</artifactId><version>1</version></project>";
        for (Path dir : List.of(source, compiled)) {
            Files.writeString(dir.resolve("pom.xml"), pom);
            Files.createDirectories(dir.resolve("src/main/java"));
            Files.writeString(dir.resolve("src/main/java/ReceiptInput.java"), "final class ReceiptInput {}");
        }
        Path deployment = Files.createDirectory(root.resolve("deployment"));
        Files.createDirectory(deployment.resolve("lib"));
        Path archive = deployment.resolve("ck3-control-build-tools-0.1.0-SNAPSHOT.jar");
        Files.writeString(archive, "synthetic archive fixture");
        Path dependency = deployment.resolve("lib/fixture.jar"); Files.writeString(dependency, "synthetic dependency fixture");
        Path scratch = Files.createDirectory(root.resolve("scratch"));
        Path nativeRoot = Files.createDirectory(root.resolve("native"));
        Path cmd = Path.of(System.getenv("SystemRoot"), "System32/cmd.exe");
        Path batch = nativeRoot.resolve("fixture.cmd"); Files.writeString(batch, "@echo off\r\nexit /b 0\r\n");
        Instant opened = Instant.now().minusSeconds(1);
        WindowsJobProcess.CommandResult terminal;
        try (WindowsJobProcess child = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(cmd,
                List.of("/d", "/c", batch.toString()), root, Map.copyOf(System.getenv()),
                nativeRoot.resolve("stdout.log"), nativeRoot.resolve("stderr.log"), 64L << 20))) {
            terminal = child.await(Duration.ofSeconds(10), Instant.now().plusSeconds(15), () -> {});
        }
        assertTrue(terminal.passed()); assertEquals(0, terminal.accounting().activeProcesses());
        Instant completed = Instant.now();
        var mapper = ControlBuild.strictMapper(); var release = mapper.createObjectNode();
        release.put("schema", "xar.java-phase1.manual-capacity-release/v1");
        release.put("machine_id", WindowsJobProcess.currentMachineId());
        release.put("status", "RELEASED_JAVA_PHASE1_BOUNDED_BUILD_AND_LOCAL_SERVICE");
        release.put("observed_at_utc", opened.toString()); release.put("review_at_utc", completed.plusNanos(1).toString());
        release.put("temporary_root", scratch.toString());
        Path releasePath = root.resolve("historical-release.json");
        Files.write(releasePath, mapper.writeValueAsBytes(release));
        Path launcher = root.resolve("mvn.cmd"); Files.writeString(launcher, "@exit /b 0\r\n");
        var toolchain = new ControlBuild.MavenToolchain(ControlBuild.MavenSelection.DEFAULT_COMMAND, "mvn",
                root.toString(), "3.10.0", "3.10.0", ControlBuild.FileRef.measure(launcher), null);
        var deploymentPins = new java.util.ArrayList<>(List.of(ControlBuild.FileRef.measure(archive), ControlBuild.FileRef.measure(dependency)));
        deploymentPins.sort(java.util.Comparator.comparing(ControlBuild.FileRef::path));
        var match = new ControlBuild.SourcePostcheck(ControlBuild.SourceState.MATCH, null);
        var receipt = new ControlBuild.BuildReceipt(ControlBuild.SCHEMA, WindowsJobProcess.currentMachineId(), completed.toString(),
                "PASS", source.toString(), compiled.toString(), deployment.toString(), match, match,
                ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME, ControlBuild.SourceLimitProfile.STANDARD_8_MIB,
                ControlBuild.sourceManifest(source), ControlBuild.sourceManifest(compiled), deploymentPins,
                List.of(ControlBuild.FileRef.measure(cmd)), ControlBuild.FileRef.measure(releasePath), toolchain,
                ControlBuild.FileRef.measure(Path.of(System.getProperty("java.home"), "bin/java.exe")),
                terminal, terminal, Map.of("fixture", 0L), null);
        Path receiptPath = root.resolve("completed-build.json");
        Files.write(receiptPath, mapper.writeValueAsBytes(receipt));
        return new CompletedReceiptFixture(receiptPath, receipt, releasePath, source, compiled, deployment);
    }

    @Test void completedSoftwareRemainsVerifiedAfterItsBuildLeaseExpiresButLiveAcceptanceStillFails() throws Exception {
        var fixture = completedReceiptFixture(temporary.resolve("completed-expiry"));
        var ref = fixture.receiptRef();
        assertEquals(fixture.receipt(), ControlBuild.verifiedCompletedReceipt(ref));
        assertThrows(IOException.class, () -> ControlBuild.acceptedReceipt(fixture.receiptPath()));
        ref.verify();
    }

    @Test void completedReaderRejectsForgedCompletionAndFailedOrIncompleteNativeTerminals() throws Exception {
        var fixture = completedReceiptFixture(temporary.resolve("completed-rejections"));
        var mapper = ControlBuild.strictMapper();
        var base = mapper.valueToTree(fixture.receipt());
        var release = mapper.readTree(Files.readAllBytes(fixture.releasePath()));
        java.util.List<com.fasterxml.jackson.databind.node.ObjectNode> mutations = new java.util.ArrayList<>();
        for (String time : List.of(release.get("observed_at_utc").asText(), release.get("review_at_utc").asText(),
                Instant.now().plusSeconds(60).toString())) {
            var changed = ((com.fasterxml.jackson.databind.node.ObjectNode) base).deepCopy();
            changed.put("observed_at_utc", time); mutations.add(changed);
        }
        var red = ((com.fasterxml.jackson.databind.node.ObjectNode) base).deepCopy(); red.put("status", "RED"); mutations.add(red);
        var exit = ((com.fasterxml.jackson.databind.node.ObjectNode) base).deepCopy();
        ((com.fasterxml.jackson.databind.node.ObjectNode) exit.get("maven_result")).put("exit_code", 37); mutations.add(exit);
        var active = ((com.fasterxml.jackson.databind.node.ObjectNode) base).deepCopy();
        ((com.fasterxml.jackson.databind.node.ObjectNode) active.get("maven_result").get("accounting")).put("active_processes", 1); mutations.add(active);
        var timeout = ((com.fasterxml.jackson.databind.node.ObjectNode) base).deepCopy();
        ((com.fasterxml.jackson.databind.node.ObjectNode) timeout.get("maven_result")).put("stop_reason", "fixture timeout"); mutations.add(timeout);
        var compiler = ((com.fasterxml.jackson.databind.node.ObjectNode) base).deepCopy();
        ((com.fasterxml.jackson.databind.node.ObjectNode) compiler.get("java_executable_ref")).put("sha256", "0".repeat(64)); mutations.add(compiler);
        int index = 0;
        for (var changed : mutations) {
            Path rejected = temporary.resolve("rejected-completed-" + (++index) + ".json");
            Files.write(rejected, mapper.writeValueAsBytes(changed));
            assertThrows(IOException.class, () -> ControlBuild.verifiedCompletedReceipt(ControlBuild.FileRef.measure(rejected)));
        }
        var pinned = fixture.receiptRef();
        Files.writeString(fixture.receiptPath(), "{}");
        assertThrows(IOException.class, () -> ControlBuild.verifiedCompletedReceipt(pinned));
    }

    @Test void completedReaderRetainsOriginalCompiledDeploymentAndProducerPinGuards() throws Exception {
        var fixture = completedReceiptFixture(temporary.resolve("completed-drift"));
        var ref = fixture.receiptRef();
        for (Path path : List.of(fixture.sourceRoot().resolve("src/main/java/ReceiptInput.java"),
                fixture.compiledRoot().resolve("src/main/java/ReceiptInput.java"),
                fixture.deploymentRoot().resolve("ck3-control-build-tools-0.1.0-SNAPSHOT.jar"),
                Path.of(fixture.receipt().mavenToolchain().distributionLauncherRef().path()))) {
            byte[] original = Files.readAllBytes(path);
            Files.writeString(path, "same path changed fixture bytes");
            assertThrows(IOException.class, () -> ControlBuild.verifiedCompletedReceipt(ref));
            Files.write(path, original);
            assertEquals(fixture.receipt(), ControlBuild.verifiedCompletedReceipt(ref));
        }
        var mapper = ControlBuild.strictMapper();
        var changed = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.valueToTree(fixture.receipt());
        ((com.fasterxml.jackson.databind.node.ObjectNode) changed.get("producer_runtime_pins").get(0)).put("sha256", "0".repeat(64));
        Path rejected = temporary.resolve("producer-drift.json"); Files.write(rejected, mapper.writeValueAsBytes(changed));
        assertThrows(IOException.class, () -> ControlBuild.verifiedCompletedReceipt(ControlBuild.FileRef.measure(rejected)));
    }

}
