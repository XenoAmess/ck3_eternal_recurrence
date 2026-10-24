package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InterruptedIOException;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.AccessDeniedException;
import java.nio.file.LinkOption;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.nio.file.attribute.FileTime;
import java.time.Duration;
import java.time.Instant;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class CiBootstrapTest {
    private static final long GIB = 1L << 30;
    private static final String DEFAULT_WINDOWS_PATHEXT = ".COM;.EXE;.BAT;.CMD;.VBS;.VBE;.JS;.JSE;.WSF;.WSH;.MSC";
    private static final String POLICY = """
            {"schema":"xar-storage-retention-policy-v1","policy_version":"1.0.0","capacity":{
            "safety_floor_bytes":2147483648,"safety_ceiling_bytes":21474836480,"safety_volume_fraction":0.05,
            "default_project_quota_ceiling_bytes":107374182400,"default_project_quota_volume_fraction":0.10,
            "quota_override_max_hours":168}}
            """;

    private static CiBootstrap.Plan timingPlan(Instant observed, Instant review) {
        var pin = new CiBootstrap.FilePin(Path.of("synthetic-policy.json").toAbsolutePath().toString(), 1, "0".repeat(64));
        var override = new CiBootstrap.QuotaOverride("fixture-owner", "github-actions-java-ci", "synthetic finite quota",
                8 * GIB, review.toString(), pin);
        return new CiBootstrap.Plan(CiBootstrap.PLAN_SCHEMA, "fixture-machine", observed.toString(), review.toString(),
                "synthetic-repo", "synthetic-work", "synthetic-java", null, "synthetic-python", "github-actions-java-ci", pin,
                Map.of(), Map.of("fixture-volume", override), Map.of("scratch", 1024L), List.of(pin), List.of(pin), false, false);
    }

    @Test void pipelineDeadlineIncludesBootstrapAndNestedElapsedTimeWithoutRestarting() throws Exception {
        Instant initial = Instant.parse("2026-10-23T00:00:00Z");
        var plan = timingPlan(initial, initial.plus(Duration.ofMinutes(90)));
        var timing = CiBootstrap.pipelineTiming(plan);
        assertEquals(initial.plus(Duration.ofMinutes(45)), timing.outerDeadline());
        assertEquals(timing.outerDeadline().minusSeconds(30), timing.workDeadline());
        // Thirty minutes already spent in bootstrap/qualification leave one shared fourteen-and-a-half minutes.
        assertEquals(Duration.ofMinutes(14).plusSeconds(30), timing.remainingWork(initial.plus(Duration.ofMinutes(30))));
        assertEquals(timing, CiBootstrap.pipelineTiming(plan));
        assertThrows(IOException.class, () -> timing.remainingWork(timing.workDeadline()));
        assertEquals(Duration.ofSeconds(30), timing.remainingOuter(timing.workDeadline()));
        assertThrows(IOException.class, () -> timing.remainingOuter(timing.outerDeadline()));
    }

    @Test void pipelineDeadlineClipsToEarlierAuthorityAndRejectsFutureOrExhaustedAdmission() throws Exception {
        Instant initial = Instant.parse("2026-10-23T00:00:00Z");
        Instant review = initial.plus(Duration.ofMinutes(10));
        var timing = CiBootstrap.pipelineTiming(timingPlan(initial, review));
        assertEquals(review, timing.outerDeadline()); assertEquals(review.minusSeconds(30), timing.workDeadline());
        assertThrows(IOException.class, () -> timing.remainingWork(initial.minusNanos(1)));
        assertThrows(IllegalArgumentException.class, () -> CiBootstrap.pipelineTiming(timingPlan(initial, initial.plusSeconds(30))));
        assertThrows(IllegalArgumentException.class, () -> CiBootstrap.pipelineTiming(timingPlan(initial, initial.minusNanos(1))));
        assertThrows(IllegalArgumentException.class, () -> new CiBootstrap.PipelineTiming(initial,
                initial.plus(Duration.ofMinutes(45)), initial.plus(Duration.ofMinutes(45)).plusSeconds(30)));
    }

    @Test void executionLeaseNarrowsQuotaReviewWithoutExtendingOriginalPinsOrAuthority() throws Exception {
        Instant initial = Instant.parse("2026-10-23T00:00:00Z");
        var original = timingPlan(initial, initial.plus(Duration.ofMinutes(90)));
        var execution = CiBootstrap.pipelineExecutionPlan(original);
        String deadline = CiBootstrap.pipelineTiming(original).workDeadline().toString();
        assertEquals(deadline, execution.reviewAtUtc());
        assertEquals(deadline, execution.quotaOverrides().get("fixture-volume").reviewAtUtc());
        assertEquals(original.observedAtUtc(), execution.observedAtUtc());
        assertEquals(original.policyRef(), execution.policyRef()); assertEquals(original.sourcePins(), execution.sourcePins());
        assertEquals(original.bootstrapRuntimeClosure(), execution.bootstrapRuntimeClosure());
        assertEquals(original.parts(), execution.parts()); assertEquals(original.volumes(), execution.volumes());
        assertEquals(initial.plus(Duration.ofMinutes(90)).toString(), original.reviewAtUtc());
        assertEquals(original.reviewAtUtc(), original.quotaOverrides().get("fixture-volume").reviewAtUtc());
        var earlier = new CiBootstrap.QuotaOverride("fixture-owner", "github-actions-java-ci", "shorter original authority",
                8 * GIB, initial.plusSeconds(60).toString(), original.policyRef());
        var shortOverride = new CiBootstrap.Plan(original.schema(), original.machineId(), original.observedAtUtc(), original.reviewAtUtc(),
                original.repoRoot(), original.workRoot(), original.javaHome(), original.mavenCommand(), original.pythonExecutable(),
                original.ownerTask(), original.policyRef(), original.volumes(), Map.of("fixture-volume", earlier), original.parts(),
                original.sourcePins(), original.bootstrapRuntimeClosure(), false, false);
        assertEquals(earlier, CiBootstrap.pipelineExecutionPlan(shortOverride).quotaOverrides().get("fixture-volume"));
    }

    @Test
    void scratchMetadataDenialIsRereadThroughTheActualGuard(@TempDir Path temporary) throws Exception {
        Path file = guardedFile(temporary, "scratch");
        AtomicInteger reads = new AtomicInteger();
        CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10), () -> {}, path -> {
            if (path.equals(file) && reads.incrementAndGet() == 1) throw new AccessDeniedException(path.toString());
            return attributes(path);
        });
        assertEquals(2, reads.get());
        assertEquals("actual file", Files.readString(file));
    }

    @Test
    void scratchRemovalNeedsActualNoSuchFileNotAnExistenceGuess(@TempDir Path temporary) throws Exception {
        Path file = guardedFile(temporary, "scratch");
        AtomicInteger reads = new AtomicInteger();
        CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10), () -> {}, path -> {
            if (path.equals(file) && reads.incrementAndGet() == 1) {
                Files.delete(file);
                throw new AccessDeniedException(path.toString());
            }
            return attributes(path);
        });
        assertEquals(2, reads.get());
        assertTrue(Files.notExists(file));
    }

    @Test
    void vanishedScratchDirectoryDuringTraversalStillCountsSurvivingSiblings(@TempDir Path temporary) throws Exception {
        Path sibling = guardedFile(temporary, "scratch");
        Path vanished = Files.createDirectory(sibling.getParent().resolve("junit-removed"));
        AtomicInteger siblingReads = new AtomicInteger();
        CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10), () -> {}, path -> {
            if (path.equals(sibling)) siblingReads.incrementAndGet();
            return attributes(path);
        }, removeBeforeTraversal(vanished));
        assertTrue(Files.notExists(vanished));
        assertEquals(1, siblingReads.get());
        assertEquals("actual file", Files.readString(sibling));

        Files.createDirectory(vanished);
        IOException failure = assertThrows(IOException.class, () -> CiBootstrap.guard(temporary, Map.of(),
                Instant.now().plusSeconds(10), () -> {}, path -> {
                    BasicFileAttributes actual = attributes(path);
                    // Exercise the existing quota without allocating a half-GiB fixture.
                    return path.equals(sibling) ? new SizedAttributes(actual, (512L << 20) + 1) : actual;
                }, removeBeforeTraversal(vanished)));
        assertEquals("task part budget exceeded: scratch", failure.getMessage());
    }

    @Test
    void removedMavenUpdateMarkerDuringTraversalStillCountsSurvivingArtifacts(@TempDir Path temporary) throws Exception {
        Path sibling = guardedFile(temporary, "m2");
        Path marker = sibling.getParent().resolve("maven-resolver-named-locks-1.9.27.pom.lastUpdated");
        Files.writeString(marker, "actual update marker");
        AtomicInteger reads = new AtomicInteger();
        CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10), () -> {}, path -> {
            if (path.equals(sibling)) reads.incrementAndGet();
            return attributes(path);
        }, removeBeforeTraversal(marker));
        assertTrue(Files.notExists(marker)); assertEquals(1, reads.get());
        assertEquals("actual file", Files.readString(sibling));

        Files.writeString(marker, "actual update marker");
        IOException failure = assertThrows(IOException.class, () -> CiBootstrap.guard(temporary, Map.of(),
                Instant.now().plusSeconds(10), () -> {}, path -> {
                    BasicFileAttributes actual = attributes(path);
                    return path.equals(sibling) ? new SizedAttributes(actual, (2L << 30) + 1) : actual;
                }, removeBeforeTraversal(marker)));
        assertEquals("task part budget exceeded: m2", failure.getMessage());
    }

    @Test
    void mavenMarkerAttributeRemovalDoesNotRelaxMissingArtifactBodies(@TempDir Path temporary) throws Exception {
        Path sibling = guardedFile(temporary, "m2");
        Path marker = sibling.getParent().resolve("artifact.pom.lastUpdated");
        Files.writeString(marker, "actual marker");
        CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10), () -> {}, path -> {
            if (path.equals(marker)) Files.delete(marker);
            return attributes(path);
        });
        assertTrue(Files.notExists(marker));
        for (String name : List.of("artifact.pom", "artifact.jar")) {
            Path artifact = sibling.getParent().resolve(name); Files.writeString(artifact, "actual artifact");
            assertThrows(NoSuchFileException.class, () -> CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10),
                    () -> {}, CiBootstrapTest::attributes, removeBeforeTraversal(artifact)));
        }
    }

    @Test
    void mavenMarkerExceptionRequiresActualNoSuchFileInTheRealM2Part(@TempDir Path temporary) throws Exception {
        Path sibling = guardedFile(temporary, "m2");
        Path marker = sibling.getParent().resolve("artifact.pom.lastUpdated");
        Files.writeString(marker, "actual marker");
        for (IOException error : List.of(new AccessDeniedException(marker.toString()), new IOException("different I/O failure"))) {
            AtomicInteger reads = new AtomicInteger();
            IOException actual = assertThrows(IOException.class, () -> CiBootstrap.guard(temporary, Map.of(),
                    Instant.now().plusSeconds(10), () -> {}, path -> {
                        if (path.equals(marker)) { reads.incrementAndGet(); throw error; }
                        return attributes(path);
                    }));
            assertEquals(error, actual); assertEquals(1, reads.get());
        }
        Path foreignMarker = temporary.resolve("build/artifact.pom.lastUpdated");
        Files.writeString(foreignMarker, "other part");
        assertThrows(NoSuchFileException.class, () -> CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10),
                () -> {}, CiBootstrapTest::attributes, removeBeforeTraversal(foreignMarker)));
        Files.delete(marker); Files.delete(sibling); Files.delete(sibling.getParent());
        assertThrows(NoSuchFileException.class, () -> CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10),
                () -> {}, CiBootstrapTest::attributes));
    }

    @Test
    void actualDoxiaChecksumTemporaryRemovalStillCountsSurvivingArtifacts(@TempDir Path temporary) throws Exception {
        Path sibling = guardedFile(temporary, "m2");
        Path version = Files.createDirectories(sibling.getParent().resolve("org/apache/maven/doxia/doxia-sink-api/2.0.0"));
        Path pom = version.resolve("doxia-sink-api-2.0.0.pom"); Files.writeString(pom, "actual pom");
        Path checksum = version.resolve("doxia-sink-api-2.0.0.pom.md5.2381834368995664026.tmp");
        Files.writeString(checksum, "actual checksum temporary");
        AtomicInteger reads = new AtomicInteger();
        CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10), () -> {}, path -> {
            if (path.equals(checksum)) Files.delete(checksum);
            if (path.equals(sibling) || path.equals(pom)) reads.incrementAndGet();
            return attributes(path);
        });
        assertTrue(Files.notExists(checksum)); assertEquals(2, reads.get());
        assertEquals("actual pom", Files.readString(pom));
    }

    @Test
    void removedChecksumTemporaryDuringTraversalPreservesSiblingQuota(@TempDir Path temporary) throws Exception {
        Path sibling = guardedFile(temporary, "m2");
        Path checksum = sibling.resolveSibling("doxia-sink-api-2.0.0.pom.md5.2381834368995664026.tmp");
        Files.writeString(checksum, "actual checksum temporary");
        AtomicInteger reads = new AtomicInteger();
        CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10), () -> {}, path -> {
            if (path.equals(sibling)) reads.incrementAndGet();
            return attributes(path);
        }, removeBeforeTraversal(checksum));
        assertTrue(Files.notExists(checksum)); assertEquals(1, reads.get());
        Files.writeString(checksum, "actual checksum temporary");
        IOException failure = assertThrows(IOException.class, () -> CiBootstrap.guard(temporary, Map.of(),
                Instant.now().plusSeconds(10), () -> {}, path -> {
                    BasicFileAttributes actual = attributes(path);
                    return path.equals(sibling) ? new SizedAttributes(actual, (2L << 30) + 1) : actual;
                }, removeBeforeTraversal(checksum)));
        assertEquals("task part budget exceeded: m2", failure.getMessage());
    }

    @Test
    void checksumTemporaryRemovalRequiresResolverFilenameAndRealM2Descendant(@TempDir Path temporary) throws Exception {
        Path sibling = guardedFile(temporary, "m2");
        for (String name : List.of("artifact.pom.md5.2381834368995664026.tmp", "artifact.jar.sha1.18446744073709551615.tmp",
                "maven-metadata.xml.sha256.0.tmp", "artifact.pom.sha512.42.tmp")) {
            Path checksum = sibling.resolveSibling(name); Files.writeString(checksum, "actual checksum temporary");
            CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10), () -> {},
                    CiBootstrapTest::attributes, removeBeforeTraversal(checksum));
            assertTrue(Files.notExists(checksum));
        }
        for (String name : List.of("artifact.pom", "artifact.jar", "artifact.pom.md5", "artifact.pom.sha1",
                "artifact.pom.md5.random.tmp", "artifact.pom.md5.-1.tmp",
                "artifact.pom.md5.+1.tmp", "artifact.pom.md5.00.tmp", "artifact.pom.md5.18446744073709551616.tmp",
                "artifact.pom.md5.42.tmp.bak")) {
            Path file = sibling.resolveSibling(name); Files.writeString(file, "actual file");
            assertThrows(NoSuchFileException.class, () -> CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10),
                    () -> {}, CiBootstrapTest::attributes, removeBeforeTraversal(file)), name);
        }
        Path foreign = temporary.resolve("build/artifact.pom.md5.42.tmp"); Files.writeString(foreign, "other part");
        assertThrows(NoSuchFileException.class, () -> CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10),
                () -> {}, CiBootstrapTest::attributes, removeBeforeTraversal(foreign)));
        Files.delete(sibling); Files.delete(sibling.getParent());
        assertThrows(NoSuchFileException.class, () -> CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10),
                () -> {}, CiBootstrapTest::attributes));
    }

    @Test
    void checksumTemporaryStillCountsAndCannotHidePermissionOrOtherIoFailure(@TempDir Path temporary) throws Exception {
        Path sibling = guardedFile(temporary, "m2");
        Path checksum = sibling.resolveSibling("artifact.pom.md5.42.tmp"); Files.writeString(checksum, "actual checksum temporary");
        IOException quota = assertThrows(IOException.class, () -> CiBootstrap.guard(temporary, Map.of(),
                Instant.now().plusSeconds(10), () -> {}, path -> {
                    BasicFileAttributes actual = attributes(path);
                    return path.equals(checksum) ? new SizedAttributes(actual, (2L << 30) + 1) : actual;
                }));
        assertEquals("task part budget exceeded: m2", quota.getMessage());
        for (IOException error : List.of(new AccessDeniedException(checksum.toString()), new IOException("other I/O failure"))) {
            AtomicInteger reads = new AtomicInteger();
            IOException failure = assertThrows(IOException.class, () -> CiBootstrap.guard(temporary, Map.of(),
                    Instant.now().plusSeconds(10), () -> {}, path -> {
                        if (path.equals(checksum)) { reads.incrementAndGet(); throw error; }
                        return attributes(path);
                    }));
            assertEquals(error, failure); assertEquals(1, reads.get());
        }
    }

    @Test
    void actualQuarkusDownloadTemporaryRemovalStillCountsSurvivingArtifacts(@TempDir Path temporary) throws Exception {
        Path sibling = guardedFile(temporary, "m2");
        Path version = Files.createDirectories(sibling.getParent().resolve("io/quarkus/quarkus-mutiny/3.40.1.1"));
        Path jar = version.resolve("quarkus-mutiny-3.40.1.1.jar"); Files.writeString(jar, "actual jar");
        Path pom = version.resolve("quarkus-mutiny-3.40.1.1.pom"); Files.writeString(pom, "actual pom");
        Path download = version.resolve("quarkus-mutiny-3.40.1.1.jar.11782637843446623922.tmp.7356342921900080208.tmp");
        Files.writeString(download, "actual download temporary");
        AtomicInteger reads = new AtomicInteger();
        CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10), () -> {}, path -> {
            if (path.equals(download)) Files.delete(download);
            if (path.equals(sibling) || path.equals(jar) || path.equals(pom)) reads.incrementAndGet();
            return attributes(path);
        });
        assertTrue(Files.notExists(download)); assertEquals(3, reads.get());
        assertEquals("actual jar", Files.readString(jar)); assertEquals("actual pom", Files.readString(pom));
    }

    @Test
    void removedDownloadTemporaryDuringTraversalPreservesSiblingQuota(@TempDir Path temporary) throws Exception {
        Path sibling = guardedFile(temporary, "m2");
        Path download = sibling.resolveSibling("quarkus-mutiny-3.40.1.1.jar.11782637843446623922.tmp.7356342921900080208.tmp");
        Files.writeString(download, "actual download temporary");
        AtomicInteger reads = new AtomicInteger();
        CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10), () -> {}, path -> {
            if (path.equals(sibling)) reads.incrementAndGet();
            return attributes(path);
        }, removeBeforeTraversal(download));
        assertTrue(Files.notExists(download)); assertEquals(1, reads.get());
        Files.writeString(download, "actual download temporary");
        IOException quota = assertThrows(IOException.class, () -> CiBootstrap.guard(temporary, Map.of(),
                Instant.now().plusSeconds(10), () -> {}, path -> {
                    BasicFileAttributes actual = attributes(path);
                    return path.equals(sibling) ? new SizedAttributes(actual, (2L << 30) + 1) : actual;
                }, removeBeforeTraversal(download)));
        assertEquals("task part budget exceeded: m2", quota.getMessage());
    }

    @Test
    void downloadTemporaryRemovalRequiresResolverNameAndRealM2Descendant(@TempDir Path temporary) throws Exception {
        Path sibling = guardedFile(temporary, "m2");
        for (String name : List.of("artifact.jar.0.tmp", "artifact.pom.18446744073709551615.tmp",
                "artifact.jar.0.tmp.18446744073709551615.tmp", "artifact.pom.18446744073709551615.tmp.0.tmp")) {
            Path download = sibling.resolveSibling(name); Files.writeString(download, "actual download temporary");
            CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10), () -> {},
                    CiBootstrapTest::attributes, removeBeforeTraversal(download));
            assertTrue(Files.notExists(download));
        }
        for (String name : List.of("artifact.jar", "artifact.pom", "artifact.jar.tmp", "artifact.jar.00.tmp",
                "artifact.jar.-1.tmp", "artifact.jar.+1.tmp", "artifact.jar.18446744073709551616.tmp",
                "artifact.jar.1.tmp.00.tmp", "artifact.jar.1.tmp.18446744073709551616.tmp",
                "artifact.jar.18446744073709551616.tmp.1.tmp", "artifact.jar.1.tmp.1.tmp.1.tmp",
                "artifact.zip.1.tmp", "artifact.jar.1.tmp.bak", "artifact.pom.md5.1.tmp.1.tmp")) {
            Path file = sibling.resolveSibling(name); Files.writeString(file, "actual file");
            assertThrows(NoSuchFileException.class, () -> CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10),
                    () -> {}, CiBootstrapTest::attributes, removeBeforeTraversal(file)), name);
        }
        Path foreign = temporary.resolve("build/artifact.jar.1.tmp.2.tmp"); Files.writeString(foreign, "other part");
        assertThrows(NoSuchFileException.class, () -> CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10),
                () -> {}, CiBootstrapTest::attributes, removeBeforeTraversal(foreign)));
        Files.delete(sibling); Files.delete(sibling.getParent());
        assertThrows(NoSuchFileException.class, () -> CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10),
                () -> {}, CiBootstrapTest::attributes));
    }

    @Test
    void downloadTemporaryStillCountsAndCannotHidePermissionOrOtherIoFailure(@TempDir Path temporary) throws Exception {
        Path sibling = guardedFile(temporary, "m2");
        Path download = sibling.resolveSibling("artifact.jar.1.tmp.2.tmp"); Files.writeString(download, "actual download temporary");
        IOException quota = assertThrows(IOException.class, () -> CiBootstrap.guard(temporary, Map.of(),
                Instant.now().plusSeconds(10), () -> {}, path -> {
                    BasicFileAttributes actual = attributes(path);
                    return path.equals(download) ? new SizedAttributes(actual, (2L << 30) + 1) : actual;
                }));
        assertEquals("task part budget exceeded: m2", quota.getMessage());
        for (IOException error : List.of(new AccessDeniedException(download.toString()), new IOException("other I/O failure"))) {
            AtomicInteger reads = new AtomicInteger();
            IOException failure = assertThrows(IOException.class, () -> CiBootstrap.guard(temporary, Map.of(),
                    Instant.now().plusSeconds(10), () -> {}, path -> {
                        if (path.equals(download)) { reads.incrementAndGet(); throw error; }
                        return attributes(path);
                    }));
            assertEquals(error, failure); assertEquals(1, reads.get());
        }
    }

    @Test
    void vanishedPartRootAndNonScratchDescendantsRemainFatal(@TempDir Path temporary) throws Exception {
        Path file = guardedFile(temporary, "build");
        Path vanished = Files.createDirectory(file.getParent().resolve("removed-output"));
        assertThrows(NoSuchFileException.class, () -> CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10),
                () -> {}, CiBootstrapTest::attributes, removeBeforeTraversal(vanished)));
        Files.delete(temporary.resolve("scratch"));
        assertThrows(NoSuchFileException.class, () -> CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10),
                () -> {}, CiBootstrapTest::attributes));
    }

    @Test
    void traversalFailureCannotHidePermissionErrorsOrOriginalDeadline(@TempDir Path temporary) throws Exception {
        Path file = guardedFile(temporary, "scratch");
        for (IOException error : List.of(new AccessDeniedException(file.toString()), new IOException("directory stream failed"))) {
            IOException failure = assertThrows(IOException.class, () -> CiBootstrap.guard(temporary, Map.of(),
                    Instant.now().plusSeconds(10), () -> {}, CiBootstrapTest::attributes, (part, visitor) -> {
                        if (part.equals(file.getParent())) visitor.visitFileFailed(file, error);
                        else Files.walkFileTree(part, visitor);
                    }));
            assertEquals(error, failure);
        }
        AtomicInteger traversingScratch = new AtomicInteger();
        IOException failure = assertThrows(IOException.class, () -> CiBootstrap.guard(temporary, Map.of(),
                Instant.now().plusSeconds(10), () -> {
                    if (traversingScratch.get() > 0) throw new IOException("original child deadline");
                }, CiBootstrapTest::attributes, (part, visitor) -> {
                    if (part.equals(file.getParent())) {
                        traversingScratch.incrementAndGet();
                        visitor.visitFileFailed(file, new NoSuchFileException(file.toString()));
                    } else Files.walkFileTree(part, visitor);
                }));
        assertEquals("original child deadline", failure.getMessage());
    }

    private static CiBootstrap.TreeWalker removeBeforeTraversal(Path vanished) {
        return (part, visitor) -> {
            if (!part.equals(vanished.getParent())) {
                Files.walkFileTree(part, visitor); return;
            }
            // Fix the scheduler order around actual JDK traversal: the queued JUnit
            // directory disappears, then the JDK emits the real visitFileFailed.
            visitor.preVisitDirectory(part, attributes(part));
            Files.delete(vanished);
            Files.walkFileTree(vanished, visitor);
            try (var siblings = Files.newDirectoryStream(part)) {
                for (Path sibling : siblings) Files.walkFileTree(sibling, visitor);
            }
            visitor.postVisitDirectory(part, null);
        };
    }

    private record SizedAttributes(BasicFileAttributes actual, long size) implements BasicFileAttributes {
        @Override public FileTime lastModifiedTime() { return actual.lastModifiedTime(); }
        @Override public FileTime lastAccessTime() { return actual.lastAccessTime(); }
        @Override public FileTime creationTime() { return actual.creationTime(); }
        @Override public boolean isRegularFile() { return actual.isRegularFile(); }
        @Override public boolean isDirectory() { return actual.isDirectory(); }
        @Override public boolean isSymbolicLink() { return actual.isSymbolicLink(); }
        @Override public boolean isOther() { return actual.isOther(); }
        @Override public Object fileKey() { return actual.fileKey(); }
    }

    @Test
    void persistentScratchDenialRemainsFatalAfterFourReads(@TempDir Path temporary) throws Exception {
        Path file = guardedFile(temporary, "scratch");
        AtomicInteger reads = new AtomicInteger();
        assertThrows(AccessDeniedException.class, () -> CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10),
                () -> {}, path -> {
                    if (path.equals(file)) { reads.incrementAndGet(); throw new AccessDeniedException(path.toString()); }
                    return attributes(path);
                }));
        assertEquals(4, reads.get());
        assertTrue(Files.isRegularFile(file));
    }

    @Test
    void nonScratchDenialAndOtherIoFailuresAreNeverRetried(@TempDir Path temporary) throws Exception {
        Path file = guardedFile(temporary, "build");
        AtomicInteger reads = new AtomicInteger();
        assertThrows(AccessDeniedException.class, () -> CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10),
                () -> {}, path -> {
                    if (path.equals(file)) { reads.incrementAndGet(); throw new AccessDeniedException(path.toString()); }
                    return attributes(path);
                }));
        assertEquals(1, reads.get());
        Path scratch = temporary.resolve("scratch/other"); Files.writeString(scratch, "actual file");
        AtomicInteger otherReads = new AtomicInteger();
        IOException failure = assertThrows(IOException.class, () -> CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10),
                () -> {}, path -> {
                    if (path.equals(scratch)) { otherReads.incrementAndGet(); throw new IOException("different I/O failure"); }
                    return attributes(path);
                }));
        assertEquals("different I/O failure", failure.getMessage());
        assertEquals(1, otherReads.get());
    }

    @Test
    void scratchRetryCannotOutliveTheOriginalChildDeadline(@TempDir Path temporary) throws Exception {
        Path file = guardedFile(temporary, "scratch");
        AtomicInteger reads = new AtomicInteger();
        IOException failure = assertThrows(IOException.class, () -> CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10),
                () -> { if (reads.get() > 0) throw new IOException("original child deadline"); }, path -> {
                    if (path.equals(file)) { reads.incrementAndGet(); throw new AccessDeniedException(path.toString()); }
                    return attributes(path);
                }));
        assertEquals("original child deadline", failure.getMessage());
        assertEquals(1, reads.get());
    }

    @Test
    void expiredAuthorityAndCancellationRemainFatal(@TempDir Path temporary) throws Exception {
        guardedFile(temporary, "scratch");
        AtomicInteger reads = new AtomicInteger();
        assertThrows(IOException.class, () -> CiBootstrap.guard(temporary, Map.of(), Instant.EPOCH, () -> {}, path -> {
            reads.incrementAndGet(); return attributes(path);
        }));
        assertEquals(0, reads.get());
        Thread.currentThread().interrupt();
        try {
            assertThrows(InterruptedIOException.class, () -> CiBootstrap.guard(temporary, Map.of(), Instant.now().plusSeconds(10),
                    () -> {}, CiBootstrapTest::attributes));
            assertTrue(Thread.currentThread().isInterrupted());
        } finally { Thread.interrupted(); }
    }

    private static Path guardedFile(Path root, String part) throws IOException {
        for (String name : List.of("m2", "build", "tools", "scratch", "logs", "artifacts")) Files.createDirectory(root.resolve(name));
        Path file = root.resolve(part).resolve("file-312"); Files.writeString(file, "actual file"); return file;
    }

    private static BasicFileAttributes attributes(Path path) throws IOException {
        return Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
    }

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
        Path empty = Files.createDirectory(temporary.resolve("before-maven"));
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); environment.putAll(System.getenv());
        environment.put("PATH", empty + ";" + home.resolve("bin") + ";" + Path.of(System.getenv("SystemRoot"), "System32"));
        environment.put("PATHEXT", DEFAULT_WINDOWS_PATHEXT);
        Map<String, String> originalEnvironment = Map.copyOf(environment);
        Path batch = cwd.resolve("version.cmd"); ControlBuild.writeMavenBatch(batch, null, List.of("--version"));
        AtomicInteger probes = new AtomicInteger(), installations = new AtomicInteger();
        List<CiBootstrap.FilePin> observedRefs = new ArrayList<>();
        CiBootstrap.FilePin sourceRef = CiBootstrap.measure(batch);
        CiBootstrap.DefaultMaven actual = CiBootstrap.ensureDefaultMaven(
                () -> {
                    int ordinal = probes.incrementAndGet();
                    return CiBootstrap.recordedMavenProbe(
                            () -> actualVersionProbe(batch, cwd, environment, ordinal),
                            () -> CiBootstrap.defaultMavenLauncher(environment, cwd, true),
                            cwd.resolve("probe-" + ordinal + ".stdout"), cwd.resolve("maven-observation-" + ordinal + ".json"),
                            "fixture-only-machine", sourceRef, ordinal == 1 ? CiBootstrap.MavenProbePhase.BEFORE_ENSURE
                                    : CiBootstrap.MavenProbePhase.AFTER_IN_PLACE_UPGRADE, true, observedRefs);
                }, before -> {
                    installations.incrementAndGet(); assertEquals("3.9.16", before.reportedVersion());
                    assertEquals(oldLauncher.toRealPath(), CiBootstrap.defaultMavenLauncher(environment, cwd, true));
                    CiBootstrap.replaceMavenInstallation(before, staged, temporary.resolve("backup"), () -> {});
                });
        assertEquals(2, probes.get()); assertEquals(1, installations.get());
        assertEquals(2, observedRefs.size());
        CiBootstrap.MavenProbeActual beforeProbe = readMavenProbe(observedRefs.get(0));
        CiBootstrap.MavenProbeActual afterProbe = readMavenProbe(observedRefs.get(1));
        assertEquals("3.9.16", beforeProbe.observation().reportedVersion());
        assertEquals("3.10.0", afterProbe.observation().reportedVersion());
        assertEquals(CiBootstrap.MavenProbePhase.BEFORE_ENSURE, beforeProbe.phase());
        assertEquals(CiBootstrap.MavenProbePhase.AFTER_IN_PLACE_UPGRADE, afterProbe.phase());
        assertEquals(sourceRef, beforeProbe.bootstrapSourceRef());
        assertEquals(home.toRealPath().toString(), afterProbe.observation().reportedHome());
        assertEquals("3.10.0", actual.reportedVersion()); assertEquals(home.toRealPath().toString(), actual.reportedHome());
        assertEquals("active settings", Files.readString(home.resolve("conf/settings.xml")));
        assertEquals("old vendor", Files.readString(temporary.resolve("backup/lib/old.jar")));
        assertFalse(Files.exists(home.resolve("lib/old.jar"))); assertTrue(Files.exists(home.resolve("lib/new.jar")));
        CiBootstrap.ensureDefaultMaven(() -> actualVersionProbe(batch, cwd, environment, probes.incrementAndGet()),
                before -> { throw new IOException("compliant default must not be downloaded/replaced"); });
        assertEquals(3, probes.get());
        assertEquals(originalEnvironment, environment, "admission and in-place upgrade cannot rewrite PATH or PATHEXT");
    }

    @Test
    void actualCmdSelectionKeepsPathextOrderAndIgnoresAbsentScriptExtensions(@TempDir Path temporary) throws Exception {
        Path home = Files.createDirectories(temporary.resolve("home/bin")).getParent();
        Path cmd = home.resolve("bin/mvn.cmd"), bat = home.resolve("bin/mvn.bat");
        Files.writeString(cmd, versionCommand("3.10.0", home)); Files.writeString(bat, versionCommand("3.9.16", home));
        Path cwd = Files.createDirectory(temporary.resolve("cwd"));
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); environment.putAll(System.getenv());
        environment.put("PATH", home.resolve("bin") + ";" + Path.of(System.getenv("SystemRoot"), "System32"));
        Path batch = cwd.resolve("version.cmd"); ControlBuild.writeMavenBatch(batch, null, List.of("--version"));
        environment.put("PATHEXT", ".NET-TOOL;.FOO_BAR;.VBS;.CMD;.BAT;.EXE;.COM;.MSC");
        assertEquals(cmd.toRealPath(), CiBootstrap.defaultMavenLauncher(environment, cwd, true));
        assertTrue(actualVersionProbe(batch, cwd, environment, 1).contains("Apache Maven 3.10.0"));
        environment.put("PATHEXT", ".NET-TOOL;.FOO_BAR;.VBS;.BAT;.CMD;.EXE;.COM;.MSC");
        assertEquals(bat.toRealPath(), CiBootstrap.defaultMavenLauncher(environment, cwd, true));
        assertTrue(actualVersionProbe(batch, cwd, environment, 2).contains("Apache Maven 3.9.16"));
        environment.put("PATHEXT", ".\\nested;.CMD");
        assertThrows(IOException.class, () -> CiBootstrap.defaultMavenLauncher(environment, cwd, true));
    }

    @Test
    void unsupportedActualCandidateIsRejectedBeforeCommandAndItsNoOutputReceiptIsConsumable(@TempDir Path temporary) throws Exception {
        Path first = Files.createDirectory(temporary.resolve("first")); Files.writeString(first.resolve("mvn.vbs"), "must never execute");
        Path home = Files.createDirectories(temporary.resolve("later/bin")).getParent();
        Files.writeString(home.resolve("bin/mvn.cmd"), versionCommand("3.10.0", home));
        Path cwd = Files.createDirectory(temporary.resolve("cwd")), logs = Files.createDirectory(temporary.resolve("logs"));
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); environment.putAll(System.getenv());
        environment.put("PATH", first + ";" + home.resolve("bin")); environment.put("PATHEXT", DEFAULT_WINDOWS_PATHEXT);
        Path source = temporary.resolve("bootstrap.java"); Files.writeString(source, "bootstrap source fixture");
        Path stdout = logs.resolve("maven-version-1.log"); List<CiBootstrap.FilePin> refs = new ArrayList<>();
        AtomicInteger commands = new AtomicInteger();
        IOException rejected = assertThrows(IOException.class, () -> CiBootstrap.recordedMavenProbe(() -> {
            commands.incrementAndGet(); throw new AssertionError("an unsupported default candidate must not execute");
        }, () -> CiBootstrap.defaultMavenLauncher(environment, cwd, true), stdout, logs.resolve("maven-observation-1.json"),
                "fixture-only-machine", CiBootstrap.measure(source), CiBootstrap.MavenProbePhase.BEFORE_ENSURE, true, refs));
        assertTrue(rejected.getMessage().contains("unsupported actual default Maven launcher extension"));
        assertEquals(0, commands.get()); assertFalse(Files.exists(stdout)); assertEquals(1, refs.size());
        CiBootstrap.MavenProbeActual receipt = readMavenProbe(refs.getFirst());
        assertEquals(CiBootstrap.MavenProbeStatus.REJECTED, receipt.status());
        assertNull(receipt.outputRef()); assertNull(receipt.observation()); assertNull(receipt.selectedLauncherRef());
        CiBootstrap.publish(logs.resolve("bootstrap-actual.json"), new CiBootstrap.BootstrapActual(
                "xar.java-control-CI-bootstrap-actual/v3", "fixture-only-machine", Instant.now().toString(), Instant.now().toString(),
                "RED", rejected.getMessage(), null, null, refs, false, false));
        assertEquals(1, CiBootstrap.verifyMavenEvidence(temporary, "fixture-only-machine"));
    }

    @Test
    void launcherChangedDuringVersionProbeCannotBeReadmitted(@TempDir Path temporary) throws Exception {
        Path home = Files.createDirectories(temporary.resolve("home/bin")).getParent();
        Path launcher = home.resolve("bin/mvn.cmd"); Files.writeString(launcher, "before command");
        Path source = temporary.resolve("bootstrap.java"); Files.writeString(source, "source fixture");
        Path stdout = temporary.resolve("version.log"); List<CiBootstrap.FilePin> refs = new ArrayList<>();
        String output = versionOutput("3.10.0", home);
        IOException rejected = assertThrows(IOException.class, () -> CiBootstrap.recordedMavenProbe(() -> {
            Files.writeString(launcher, "changed during command"); Files.writeString(stdout, output); return output;
        }, () -> launcher, stdout, temporary.resolve("observation.json"), "fixture-only-machine", CiBootstrap.measure(source),
                CiBootstrap.MavenProbePhase.BEFORE_ENSURE, true, refs));
        assertTrue(rejected.getMessage().contains("changed during its version probe"));
        assertEquals(CiBootstrap.MavenProbeStatus.REJECTED, readMavenProbe(refs.getFirst()).status());
        assertEquals(CiBootstrap.measure(stdout), readMavenProbe(refs.getFirst()).outputRef());
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

    @Test
    void failedUpgradeRetainsOldObservationWhenAdmittedDefaultAndPlanRemainNull(@TempDir Path temporary) throws Exception {
        Path home = Files.createDirectories(temporary.resolve("old/bin")).getParent();
        Path launcher = home.resolve("bin/mvn.cmd"); Files.writeString(launcher, "old launcher");
        Path source = temporary.resolve("bootstrap-source.java"); Files.writeString(source, "observed source fixture");
        CiBootstrap.FilePin sourceRef = CiBootstrap.measure(source);
        Path logs = Files.createDirectory(temporary.resolve("logs"));
        Path stdout = logs.resolve("maven-version-1.log");
        Path receipt = logs.resolve("maven-observation-1.json");
        List<CiBootstrap.FilePin> refs = new ArrayList<>();
        String old = versionOutput("3.9.16", home);
        IOException failure = assertThrows(IOException.class, () -> CiBootstrap.ensureDefaultMaven(
                () -> CiBootstrap.recordedMavenProbe(() -> {
                    Files.writeString(stdout, old); return old;
                }, () -> launcher, stdout, receipt, "fixture-only-machine", sourceRef,
                        CiBootstrap.MavenProbePhase.BEFORE_ENSURE, true, refs),
                before -> { throw new IOException("actual update refused before replacement"); }));
        assertEquals(1, refs.size());
        CiBootstrap.MavenProbeActual observed = readMavenProbe(refs.getFirst());
        assertEquals(CiBootstrap.MavenProbeStatus.OBSERVED, observed.status());
        assertEquals("fixture-only-machine", observed.machineId()); Instant.parse(observed.observedAtUtc());
        assertEquals(sourceRef, observed.bootstrapSourceRef());
        assertEquals(CiBootstrap.measure(stdout), observed.outputRef());
        assertEquals(CiBootstrap.measure(launcher), observed.selectedLauncherRef());
        assertEquals("3.9.16", observed.observation().reportedVersion());
        assertEquals(home.toRealPath().toString(), observed.observation().reportedHome());
        CiBootstrap.BootstrapActual actual = new CiBootstrap.BootstrapActual(
                "xar.java-control-CI-bootstrap-actual/v3", "fixture-only-machine", Instant.now().toString(),
                Instant.now().toString(), "RED", failure.getMessage(), null, null, refs, false, false);
        Path terminal = logs.resolve("bootstrap-actual.json"); CiBootstrap.publish(terminal, actual);
        CiBootstrap.BootstrapActual readback = ControlBuild.strictMapper().readValue(Files.readAllBytes(terminal),
                CiBootstrap.BootstrapActual.class);
        assertEquals(actual, readback); assertNull(readback.defaultMaven()); assertNull(readback.planRef());
        assertEquals(refs, readback.mavenProbeRefs());
        assertEquals(1, CiBootstrap.verifyMavenEvidence(temporary, "fixture-only-machine"));
        assertThrows(IOException.class, () -> CiBootstrap.verifyMavenEvidence(temporary, "another-machine"));
        byte[] retained = Files.readAllBytes(receipt);
        assertThrows(IOException.class, () -> CiBootstrap.publish(receipt, observed));
        org.junit.jupiter.api.Assertions.assertArrayEquals(retained, Files.readAllBytes(receipt));
        Files.writeString(stdout, "tampered old stdout");
        assertThrows(IOException.class, () -> CiBootstrap.verifyMavenEvidence(temporary, "fixture-only-machine"));
    }

    @Test
    void rejectedPostUpgradeIdentityKeepsBothBeforeAndAfterObservations(@TempDir Path temporary) throws Exception {
        Path oldHome = Files.createDirectories(temporary.resolve("old/bin")).getParent();
        Path newHome = Files.createDirectories(temporary.resolve("unexpected/bin")).getParent();
        Files.writeString(oldHome.resolve("bin/mvn.cmd"), "old launcher");
        Files.writeString(newHome.resolve("bin/mvn.cmd"), "unexpected launcher");
        Path source = temporary.resolve("bootstrap-source.java"); Files.writeString(source, "source fixture");
        CiBootstrap.FilePin sourceRef = CiBootstrap.measure(source);
        Path logs = Files.createDirectory(temporary.resolve("logs"));
        List<CiBootstrap.FilePin> refs = new ArrayList<>(); AtomicInteger probes = new AtomicInteger();
        assertThrows(IOException.class, () -> CiBootstrap.ensureDefaultMaven(() -> {
            int ordinal = probes.incrementAndGet(); Path home = ordinal == 1 ? oldHome : newHome;
            String output = versionOutput(ordinal == 1 ? "3.9.16" : "3.10.0", home);
            Path stdout = logs.resolve("maven-version-" + ordinal + ".log");
            return CiBootstrap.recordedMavenProbe(() -> {
                Files.writeString(stdout, output); return output;
            }, () -> home.resolve("bin/mvn.cmd"), stdout, logs.resolve("maven-observation-" + ordinal + ".json"),
                    "fixture-only-machine", sourceRef, ordinal == 1 ? CiBootstrap.MavenProbePhase.BEFORE_ENSURE
                            : CiBootstrap.MavenProbePhase.AFTER_IN_PLACE_UPGRADE, true, refs);
        }, before -> {}));
        assertEquals(2, refs.size());
        assertEquals(oldHome.toRealPath().toString(), readMavenProbe(refs.get(0)).observation().reportedHome());
        assertEquals(newHome.toRealPath().toString(), readMavenProbe(refs.get(1)).observation().reportedHome());
        CiBootstrap.publish(logs.resolve("bootstrap-actual.json"), new CiBootstrap.BootstrapActual(
                "xar.java-control-CI-bootstrap-actual/v3", "fixture-only-machine", Instant.now().toString(),
                Instant.now().toString(), "RED", "actual default changed its installation", null, null, refs, false, false));
        assertEquals(2, CiBootstrap.verifyMavenEvidence(temporary, "fixture-only-machine"));
    }

    @Test
    void persistedConsumerAcceptsActualUpgradeAndRejectsMissingAfterWrongTokensAndSourceDrift(@TempDir Path temporary) throws Exception {
        Path home = Files.createDirectories(temporary.resolve("home/bin")).getParent();
        Path launcher = home.resolve("bin/mvn.cmd"); Files.writeString(launcher, "old launcher bytes");
        Path source = temporary.resolve("bootstrap-source.java"); Files.writeString(source, "source fixture");
        CiBootstrap.FilePin sourceRef = CiBootstrap.measure(source);
        Path logs = Files.createDirectory(temporary.resolve("logs"));
        List<CiBootstrap.FilePin> refs = new ArrayList<>();
        for (int ordinal = 1; ordinal <= 2; ordinal++) {
            int number = ordinal;
            if (number == 2) Files.writeString(launcher, "new launcher bytes after in-place update");
            String output = versionOutput(number == 1 ? "3.9.16" : "3.10.0", home);
            Path stdout = logs.resolve("maven-version-" + number + ".log");
            CiBootstrap.recordedMavenProbe(() -> {
                Files.writeString(stdout, output); return output;
            }, () -> launcher, stdout, logs.resolve("maven-observation-" + number + ".json"), "fixture-only-machine",
                    sourceRef, number == 1 ? CiBootstrap.MavenProbePhase.BEFORE_ENSURE
                            : CiBootstrap.MavenProbePhase.AFTER_IN_PLACE_UPGRADE, true, refs);
        }
        CiBootstrap.DefaultMaven admitted = CiBootstrap.requireDefaultMaven(versionOutput("3.10.0", home));
        Path terminal = logs.resolve("bootstrap-actual.json");
        CiBootstrap.publish(terminal, new CiBootstrap.BootstrapActual(
                "xar.java-control-CI-bootstrap-actual/v3", "fixture-only-machine", Instant.now().toString(),
                Instant.now().toString(), "PIPELINE_EXIT_0", null, null, admitted, refs, false, false));
        assertEquals(2, CiBootstrap.verifyMavenEvidence(temporary, "fixture-only-machine"));
        // The first launcher hash is deliberately historical and differs after the real in-place write.
        assertFalse(readMavenProbe(refs.getFirst()).selectedLauncherRef().equals(CiBootstrap.measure(launcher)));
        byte[] valid = Files.readAllBytes(terminal);
        var mapper = ControlBuild.strictMapper();
        var missingAfter = mapper.readTree(valid);
        ((com.fasterxml.jackson.databind.node.ArrayNode) missingAfter.get("maven_probe_refs")).remove(1);
        Files.write(terminal, mapper.writeValueAsBytes(missingAfter));
        assertThrows(IOException.class, () -> CiBootstrap.verifyMavenEvidence(temporary, "fixture-only-machine"));
        String validText = new String(valid, StandardCharsets.UTF_8);
        String marker = "\"bytes\":" + refs.getFirst().bytes();
        int tokenAt = validText.indexOf(marker, validText.indexOf("\"maven_probe_refs\""));
        assertTrue(tokenAt >= 0);
        for (String token : List.of("true", "1.0", "1e0", "\"1\"", "null")) {
            String edited = validText.substring(0, tokenAt) + "\"bytes\":" + token
                    + validText.substring(tokenAt + marker.length());
            Files.writeString(terminal, edited);
            assertThrows(IOException.class, () -> CiBootstrap.verifyMavenEvidence(temporary, "fixture-only-machine"), token);
        }
        var missingSource = mapper.readTree(valid);
        ((com.fasterxml.jackson.databind.node.ObjectNode) missingSource).remove("maven_probe_refs");
        Files.write(terminal, mapper.writeValueAsBytes(missingSource));
        assertThrows(IOException.class, () -> CiBootstrap.verifyMavenEvidence(temporary, "fixture-only-machine"));
        Files.write(terminal, valid); Files.writeString(source, "actual bootstrap source drift");
        assertThrows(IOException.class, () -> CiBootstrap.verifyMavenEvidence(temporary, "fixture-only-machine"));
        assertThrows(IOException.class, () -> CiBootstrap.verifyMavenEvidence(temporary.resolve("missing-root"), "fixture-only-machine"));
    }

    @Test
    void failedCommandAndForwardedLauncherStillPublishRejectedProbeEvidence(@TempDir Path temporary) throws Exception {
        Path source = temporary.resolve("bootstrap-source.java"); Files.writeString(source, "source fixture");
        CiBootstrap.FilePin sourceRef = CiBootstrap.measure(source);
        Path stdout = temporary.resolve("failed.log"); List<CiBootstrap.FilePin> failedRefs = new ArrayList<>();
        Path failedLauncher = temporary.resolve("mvn.cmd"); Files.writeString(failedLauncher, "actual selected command");
        AtomicInteger launcherChecks = new AtomicInteger();
        IOException failure = assertThrows(IOException.class, () -> CiBootstrap.recordedMavenProbe(() -> {
            Files.writeString(stdout, "actual partial child output"); throw new IOException("actual child exit 7");
        }, () -> { launcherChecks.incrementAndGet(); return failedLauncher; }, stdout,
                temporary.resolve("maven-observation-failed.json"), "fixture-only-machine", sourceRef,
                CiBootstrap.MavenProbePhase.BEFORE_ENSURE, true, failedRefs));
        assertEquals("actual child exit 7", failure.getMessage());
        assertEquals(1, launcherChecks.get(), "validate the default before execution; failed commands have no post-probe resolution");
        CiBootstrap.MavenProbeActual failed = readMavenProbe(failedRefs.getFirst());
        assertEquals(CiBootstrap.MavenProbeStatus.REJECTED, failed.status());
        assertTrue(failed.error().contains("actual child exit 7"));
        assertEquals(CiBootstrap.measure(stdout), failed.outputRef()); assertNull(failed.observation());
        Path home = Files.createDirectories(temporary.resolve("home/bin")).getParent();
        Files.writeString(home.resolve("bin/mvn.cmd"), "reported launcher");
        Path forwarded = temporary.resolve("forwarded.cmd"); Files.writeString(forwarded, "forwarded launcher");
        Path forwardedOutput = temporary.resolve("forwarded.log"); List<CiBootstrap.FilePin> forwardedRefs = new ArrayList<>();
        String output = versionOutput("3.9.16", home);
        assertThrows(IOException.class, () -> CiBootstrap.recordedMavenProbe(() -> {
            Files.writeString(forwardedOutput, output); return output;
        }, () -> forwarded, forwardedOutput, temporary.resolve("maven-observation-forwarded.json"), "fixture-only-machine",
                sourceRef, CiBootstrap.MavenProbePhase.BEFORE_ENSURE, true, forwardedRefs));
        CiBootstrap.MavenProbeActual forwardedProbe = readMavenProbe(forwardedRefs.getFirst());
        assertEquals(CiBootstrap.MavenProbeStatus.REJECTED, forwardedProbe.status());
        assertEquals(CiBootstrap.measure(forwarded), forwardedProbe.selectedLauncherRef());
        assertEquals("3.9.16", forwardedProbe.observation().reportedVersion());
    }

    private static CiBootstrap.MavenProbeActual readMavenProbe(CiBootstrap.FilePin ref) throws IOException {
        assertEquals(ref, CiBootstrap.measure(Path.of(ref.path())));
        return ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(ref.path())), CiBootstrap.MavenProbeActual.class);
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
