package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.FileSystemException;
import java.nio.file.FileVisitResult;
import java.nio.file.FileVisitor;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Deterministic software fault injection at the real NIO post-directory boundary. */
final class ControlBuildScratchEnumerationTest {
    @TempDir Path temporary;

    @Test void disappearedScratchDirectoryRestartsTheEntireCensusWithoutDoubleChargingOrReturningZero() throws Exception {
        Path work = Files.createDirectory(temporary.resolve("removed"));
        Path scratch = Files.createDirectory(work.resolve("scratch"));
        Path race = Files.createDirectory(scratch.resolve("race"));
        Files.write(race.resolve("gone.bin"), new byte[3]);
        Files.write(scratch.resolve("keep.bin"), new byte[5]);
        AtomicInteger walks = new AtomicInteger();
        var io = failingWalk(race, walks, pass -> {
            if (pass != 1) return null;
            Files.delete(race.resolve("gone.bin")); Files.delete(race);
            return ended(race);
        });
        assertEquals(5L, ControlBuild.sizes(work, Map.of("scratch", 100L), () -> {}, io).get("scratch").longValue());
        assertEquals(2, walks.get());
    }

    @Test void independentlyEmptySameIdentityDirectoryAlsoRequiresAFreshCompleteCensus() throws Exception {
        Path work = Files.createDirectory(temporary.resolve("empty"));
        Path scratch = Files.createDirectory(work.resolve("scratch"));
        Path race = Files.createDirectory(scratch.resolve("race"));
        Files.write(scratch.resolve("keep.bin"), new byte[7]);
        ControlBuild.InventoryIo actualIdentity = new ControlBuild.InventoryIo() {};
        Object identity = actualIdentity.directoryIdentity(race);
        AtomicInteger walks = new AtomicInteger();
        var io = failingWalk(race, walks, pass -> pass == 1 ? ended(race) : null);
        assertEquals(7L, ControlBuild.sizes(work, Map.of("scratch", 100L), () -> {}, io).get("scratch").longValue());
        assertEquals(2, walks.get());
        assertEquals(identity, actualIdentity.directoryIdentity(race));
    }

    @Test void errorTextDoesNotGrantRetryForANonemptyDirectoryOrAnOrdinaryFileIoFailure() throws Exception {
        Path work = Files.createDirectory(temporary.resolve("nonempty"));
        Path scratch = Files.createDirectory(work.resolve("scratch"));
        Path race = Files.createDirectory(scratch.resolve("race"));
        Path file = Files.write(race.resolve("present.bin"), new byte[3]);
        AtomicInteger walks = new AtomicInteger();
        IOException original = ended(race);
        var io = failingWalk(race, walks, pass -> original);
        assertSame(original, assertThrows(FileSystemException.class,
                () -> ControlBuild.sizes(work, Map.of("scratch", 100L), () -> {}, io)));
        assertEquals(1, walks.get());
        IOException fileFailure = ended(file);
        ControlBuild.InventoryIo failedSize = new ControlBuild.InventoryIo() {
            @Override public long size(Path path) throws IOException { throw fileFailure; }
        };
        assertSame(fileFailure, assertThrows(FileSystemException.class,
                () -> ControlBuild.sizes(work, Map.of("scratch", 100L), () -> {}, failedSize)));
    }

    @Test void nonScratchScopeCannotBorrowTheScratchEnumerationRecovery() throws Exception {
        Path work = Files.createDirectory(temporary.resolve("strict-build"));
        Path build = Files.createDirectory(work.resolve("build"));
        Path race = Files.createDirectory(build.resolve("race"));
        Files.write(build.resolve("keep.bin"), new byte[5]);
        AtomicInteger walks = new AtomicInteger();
        IOException original = ended(race);
        var io = failingWalk(race, walks, pass -> { Files.delete(race); return original; });
        assertSame(original, assertThrows(FileSystemException.class,
                () -> ControlBuild.sizes(work, Map.of("build", 100L), () -> {}, io)));
        assertEquals(1, walks.get());
    }

    @Test void repeatedEnumerationLossExhaustsItsFiniteCensusBudgetAndKeepsTheOriginalCause() throws Exception {
        Path work = Files.createDirectory(temporary.resolve("finite"));
        Path scratch = Files.createDirectory(work.resolve("scratch"));
        Path race = Files.createDirectory(scratch.resolve("race"));
        Files.write(scratch.resolve("keep.bin"), new byte[5]);
        AtomicInteger walks = new AtomicInteger();
        IOException original = ended(race);
        var io = failingWalk(race, walks, pass -> original);
        IOException failure = assertThrows(IOException.class,
                () -> ControlBuild.sizes(work, Map.of("scratch", 100L), () -> {}, io));
        assertSame(original, failure.getCause());
        assertEquals(3, walks.get());
    }

    @Test void changedRootIdentityCannotAuthorizeASecondCensus() throws Exception {
        Path work = Files.createDirectory(temporary.resolve("identity"));
        Path scratch = Files.createDirectory(work.resolve("scratch"));
        Path race = Files.createDirectory(scratch.resolve("race"));
        AtomicInteger walks = new AtomicInteger();
        var changed = new java.util.concurrent.atomic.AtomicBoolean();
        var delegate = failingWalk(race, walks, pass -> { changed.set(true); return ended(race); });
        ControlBuild.InventoryIo io = new ControlBuild.InventoryIo() {
            @Override public void walk(Path root, FileVisitor<Path> visitor) throws IOException { delegate.walk(root, visitor); }
            @Override public Object directoryIdentity(Path path) throws IOException {
                Object actual = ControlBuild.InventoryIo.super.directoryIdentity(path);
                if (!path.equals(scratch) || !changed.get()) return actual;
                return Map.entry("injected-replacement-identity", actual);
            }
        };
        IOException failure = assertThrows(IOException.class,
                () -> ControlBuild.sizes(work, Map.of("scratch", 100L), () -> {}, io));
        assertTrue(failure.getMessage().contains("ancestor identity changed"));
        assertEquals(1, walks.get());
    }

    @Test void identityCaptureDisappearanceKeepsTheExistingLocalSkipAndDoesNotRescanSiblings() throws Exception {
        Path work = Files.createDirectory(temporary.resolve("capture-loss"));
        Path scratch = Files.createDirectory(work.resolve("scratch"));
        Path race = Files.createDirectory(scratch.resolve("race"));
        Files.write(race.resolve("gone.bin"), new byte[3]);
        Path sibling = Files.write(scratch.resolve("keep.bin"), new byte[5]);
        AtomicInteger walks = new AtomicInteger(), stableReads = new AtomicInteger();
        ControlBuild.InventoryIo io = new ControlBuild.InventoryIo() {
            @Override public void walk(Path root, FileVisitor<Path> visitor) throws IOException {
                if (!root.equals(scratch)) { ControlBuild.InventoryIo.super.walk(root, visitor); return; }
                walks.incrementAndGet(); visitor.preVisitDirectory(root, attributes(root));
                ControlBuild.InventoryIo.super.walk(sibling, visitor);
                ControlBuild.InventoryIo.super.walk(race, visitor);
                visitor.postVisitDirectory(root, null);
            }
            @Override public Object directoryIdentity(Path path) throws IOException {
                if (path.equals(race)) {
                    Files.delete(race.resolve("gone.bin")); Files.delete(race);
                    throw new IOException("native identity capture independently lost its directory");
                }
                return ControlBuild.InventoryIo.super.directoryIdentity(path);
            }
            @Override public long size(Path path) throws IOException {
                if (path.equals(sibling)) stableReads.incrementAndGet();
                return ControlBuild.InventoryIo.super.size(path);
            }
        };
        assertEquals(5L, ControlBuild.sizes(work, Map.of("scratch", 100L), () -> {}, io).get("scratch").longValue());
        assertEquals(1, walks.get()); assertEquals(1, stableReads.get());
    }

    @FunctionalInterface private interface FailureAtEnd { IOException at(int pass) throws IOException; }

    private static ControlBuild.InventoryIo failingWalk(Path race, AtomicInteger walks, FailureAtEnd failure) {
        return new ControlBuild.InventoryIo() {
            @Override public void walk(Path root, FileVisitor<Path> visitor) throws IOException {
                int pass = walks.incrementAndGet();
                Files.walkFileTree(root, new SimpleFileVisitor<>() {
                    @Override public FileVisitResult preVisitDirectory(Path path, BasicFileAttributes attributes) throws IOException {
                        return visitor.preVisitDirectory(path, attributes);
                    }
                    @Override public FileVisitResult visitFile(Path path, BasicFileAttributes attributes) throws IOException {
                        return visitor.visitFile(path, attributes);
                    }
                    @Override public FileVisitResult visitFileFailed(Path path, IOException error) throws IOException {
                        return visitor.visitFileFailed(path, error);
                    }
                    @Override public FileVisitResult postVisitDirectory(Path path, IOException error) throws IOException {
                        return visitor.postVisitDirectory(path, path.equals(race) ? failure.at(pass) : error);
                    }
                });
            }
        };
    }
    private static FileSystemException ended(Path path) {
        return new FileSystemException(path.toString(), null, "没有更多文件。 / no more files (injected)");
    }
}
