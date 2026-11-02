package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;

/** Tiny real Windows files; public pair DATA grants no Root or Game authority. */
final class NativeCheckpointLease305Test {
    @TempDir Path temporary;

    @Test void initialSharingIsTheOnlyEmptyLeaseAndOldLeaseStillThrows() throws IOException {
        Path path = temporary.resolve("lease.bin").toAbsolutePath();
        byte[] content = bytes("tiny lease 305");
        Files.write(path, content);
        try (var writer = FileChannel.open(path, StandardOpenOption.READ, StandardOpenOption.WRITE)) {
            assertTrue(writer.isOpen());
            var blocked = IdentityBearingFileAttributes.tryLeaseBoundedWindows(path, 4096);
            try (var unexpected = blocked.orElse(null)) {
                assertNull(unexpected, "initial sharing must return empty");
            }
            assertThrows(IOException.class, () -> {
                try (var unexpected = IdentityBearingFileAttributes.leaseBoundedWindows(path, 4096)) {
                    fail("legacy lease accepted the stable writer: " + unexpected);
                }
            });
        }
        assertThrows(IOException.class, () -> {
            try (var unexpected = IdentityBearingFileAttributes.tryLeaseBoundedWindows(
                    temporary.resolve("missing.bin"), 4096).orElse(null)) {
                fail("missing path returned instead of failing: " + unexpected);
            }
        });
        assertThrows(IllegalArgumentException.class, () -> {
            try (var unexpected = IdentityBearingFileAttributes.tryLeaseBoundedWindows(path, -1).orElse(null)) {
                fail("negative cap returned instead of failing: " + unexpected);
            }
        });
        assertThrows(IllegalArgumentException.class, () -> {
            try (var unexpected = IdentityBearingFileAttributes.tryLeaseBoundedWindows(
                    path, Integer.MAX_VALUE).orElse(null)) {
                fail("unbounded cap returned instead of failing: " + unexpected);
            }
        });
        assertThrows(IOException.class, () -> {
            try (var unexpected = IdentityBearingFileAttributes.tryLeaseBoundedWindows(path, 0).orElse(null)) {
                fail("nonempty file exceeded its valid zero cap: " + unexpected);
            }
        });
        // This real write open fails if the rejected acquisition leaked its share-read handle.
        try (var writer = FileChannel.open(path, StandardOpenOption.READ, StandardOpenOption.WRITE)) {
            assertTrue(writer.isOpen());
        }
        var lease = IdentityBearingFileAttributes.tryLeaseBoundedWindows(path, 4096).orElseThrow();
        try (lease) {
            assertEquals(content.length, lease.verifyCurrent().size());
            assertArrayEquals(content, lease.read().bytes());
        }
        assertThrows(IOException.class, lease::verifyCurrent);
        assertThrows(IOException.class, lease::read);
        assertThrows(IOException.class, lease::originalRead);
        try (var writer = FileChannel.open(path, StandardOpenOption.READ, StandardOpenOption.WRITE)) {
            assertTrue(writer.isOpen());
        }
    }

    @Test void secondDriverSharingClosesSavedLeaseAndKeepsWholeScopeConservative() throws IOException {
        Fixture f = fixture();
        try (var driverWriter = FileChannel.open(f.driver(), StandardOpenOption.READ, StandardOpenOption.WRITE)) {
            assertTrue(driverWriter.isOpen());
            var scope = f.files().beginVerification(f.pair());
            try (scope) {
                // The first verify attempts Save custody before the already-open Driver writer.
                scope.verify(f.pair());
                try (var saveWriter = FileChannel.open(f.save(), StandardOpenOption.READ, StandardOpenOption.WRITE)) {
                    assertTrue(saveWriter.isOpen(), "second-file fallback must release Save custody");
                    // Both writers stay open: the entire following body uses the original route.
                    scope.verify(f.pair());
                    assertArrayEquals(f.driverBytes(), scope.read(f.pair().driver(), 4096));
                    byte[] changed = bytes("changed save 305");
                    replaceThrough(saveWriter, changed);
                    var actual = scope.observe(f.save()).orElseThrow();
                    assertNotEquals(f.pair().save().reference().sha256(), actual.reference().sha256());
                    assertEquals(changed.length, actual.reference().bytes());
                    assertEquals(f.files().observe(f.save()).orElseThrow(), actual);
                }
            }
            // A genuine current pair rules out stale Save data as the reason for closed verify's rejection.
            var currentPair = new CheckpointPair(f.files().observe(f.save()).orElseThrow(),
                    f.files().observe(f.driver()).orElseThrow(), f.pair().frame(), f.pair().lineageId(),
                    f.pair().historyIndex(), f.pair().saveActionId(), f.pair().nativeAckRef(), f.pair().observedAt());
            f.files().verify(currentPair);
            assertThrows(IOException.class, () -> scope.observe(f.save()));
            assertThrows(IOException.class, () -> scope.read(f.pair().driver(), 4096));
            assertThrows(IOException.class, () -> scope.verify(currentPair));
        }
    }

    @Test void ackObservationIsFreshAndReadFailureCannotReviveScope() throws IOException {
        Fixture f = fixture();
        var scope = f.files().beginVerification(f.pair());
        try (scope) {
            scope.verify(f.pair());
            assertEquals(f.pair().nativeAckRef(), scope.observe(f.ack()).orElseThrow().reference());
            Files.write(f.ack(), bytes("{\"ack\":2}"));
            var actual = scope.observe(f.ack()).orElseThrow();
            assertNotEquals(f.pair().nativeAckRef().sha256(), actual.reference().sha256());
            assertEquals(f.files().observe(f.ack()).orElseThrow(), actual);
            assertThrows(IOException.class, () -> scope.read(f.pair().driver(), 0));
            f.files().verify(f.pair());
            assertThrows(IOException.class, () -> scope.observe(f.ack()));
            assertThrows(IOException.class, () -> scope.read(f.pair().driver(), 4096));
            assertThrows(IOException.class, () -> scope.verify(f.pair()));
        }
        assertThrows(IOException.class, () -> scope.observe(f.ack()));
        assertThrows(IOException.class, () -> scope.read(f.pair().driver(), 4096));
        assertThrows(IOException.class, () -> scope.verify(f.pair()));
        // Closing a poisoned leased scope must release both real deny-write handles.
        try (var saveWriter = FileChannel.open(f.save(), StandardOpenOption.READ, StandardOpenOption.WRITE);
             var driverWriter = FileChannel.open(f.driver(), StandardOpenOption.READ, StandardOpenOption.WRITE)) {
            assertTrue(saveWriter.isOpen());
            assertTrue(driverWriter.isOpen());
        }
    }

    private record Fixture(NativeCheckpointFiles files, CheckpointPair pair, Path save,
            Path driver, Path ack, byte[] driverBytes) { }

    private static byte[] bytes(String value) {
        return value.getBytes(StandardCharsets.UTF_8);
    }

    private static ProposalLifecycle.ObservationIdentity frame() {
        return new ProposalLifecycle.ObservationIdentity("software-lease-305",
                new GameGeneration(123, new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE,
                        BigInteger.ONE, BigInteger.valueOf(240)), "software:1", BigInteger.ONE,
                        "software-lease-episode-305"), 1);
    }

    private Fixture fixture() throws IOException {
        var files = new NativeCheckpointFiles();
        Path save = temporary.resolve("save.bin").toAbsolutePath();
        Path driver = temporary.resolve("driver.bin").toAbsolutePath();
        Path ack = temporary.resolve("ack.json").toAbsolutePath();
        byte[] driverBytes = bytes("tiny driver 305");
        Files.write(save, bytes("tiny save 305"));
        Files.write(driver, driverBytes);
        Files.write(ack, bytes("{\"ack\":1}"));
        var pair = new CheckpointPair(files.observe(save).orElseThrow(),
                files.observe(driver).orElseThrow(), frame(), "software-lineage-305", 1,
                "software-save-305", files.observe(ack).orElseThrow().reference(),
                Instant.parse("2026-01-01T00:00:00Z"));
        return new Fixture(files, pair, save, driver, ack, driverBytes);
    }

    private static void replaceThrough(FileChannel sameOpenFile, byte[] value) throws IOException {
        sameOpenFile.position(0);
        sameOpenFile.truncate(0);
        ByteBuffer pending = ByteBuffer.wrap(value);
        while (pending.hasRemaining()) sameOpenFile.write(pending);
        sameOpenFile.force(true);
    }
}
