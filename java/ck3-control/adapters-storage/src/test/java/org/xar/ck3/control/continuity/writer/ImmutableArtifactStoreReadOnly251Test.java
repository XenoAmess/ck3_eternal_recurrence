package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Arrays;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

final class ImmutableArtifactStoreReadOnly251Test {
    @TempDir Path temp;
    private record Fixture(WriterFixture original, ImmutableArtifactStore.Config config,
            ImmutableArtifactStore mutable, StorageWriteGuard denial,
            ImmutableArtifactStore reader, byte[] payload, Pin pin) implements AutoCloseable {
        @Override public void close() throws IOException { denial.close(); original.storage.close(); }
    }
    private Fixture fixture(String name) throws IOException {
        WriterFixture original = new WriterFixture(temp.resolve(name));
        ImmutableArtifactStore.Config config = new ImmutableArtifactStore.Config(
                original.layout.snapshot().getParent().resolve("artifacts"), original.layout.lock(), 2L << 20);
        ImmutableArtifactStore mutable = new ImmutableArtifactStore(config, original.storage);
        byte[] payload = new byte[] {11, 22, 33, 44};
        Pin pin = original.writer.locked(session -> mutable.publish(payload, 128));
        StorageWriteGuard denial = StorageWriteGuard.noWrites();
        ImmutableArtifactStore reader = ImmutableArtifactStore.readOnlyExisting(config, denial);
        return new Fixture(original, config, mutable, denial, reader, payload, pin);
    }

    @Test void existingReadOnlyObjectRetainsExactReadsAndDeniesAllWrites() throws IOException {
        try (Fixture f = fixture("existing")) {
            assertSame(f.denial(), f.reader().storageGuard());
            assertArrayEquals(f.payload(), f.reader().read(f.pin(), 128));
            assertArrayEquals(f.payload(), f.reader().read(f.pin().reference(), 128));
            assertEquals(f.pin(), f.reader().referenceOf(f.payload(), 128));
            assertEquals(f.pin(), f.reader().referenceOf(f.pin().reference().sha256(), 4, 128));
            byte[] detached = f.reader().read(f.pin(), 128); detached[0] = 99;
            assertArrayEquals(f.payload(), f.reader().read(f.pin(), 128));
            Path commit = f.config().root().resolve(f.pin().reference().sha256() + ".commit.json");
            var before = LedgerFiles.read(commit, 65536);
            f.original().writer.locked(session -> {
                assertThrows(IOException.class, () -> f.reader().publish(f.pin().reference(), 128));
                assertThrows(IOException.class, () -> f.reader().publish(f.payload(), 128));
                assertThrows(IOException.class, () -> f.reader().publishPlanningRead(f.payload(), 128));
                assertThrows(IOException.class, () -> f.reader().publish(new byte[] {8}, 128));
                assertThrows(IOException.class, () -> f.reader().requireDurable(f.pin().reference(), 128));
                return null;
            });
            assertEquals(f.pin(), LedgerFiles.exact(f.pin().reference(), 128).pin());
            var after = LedgerFiles.read(commit, 65536);
            assertEquals(before.pin(), after.pin()); assertArrayEquals(before.bytes(), after.bytes());
            f.denial().close();
            assertThrows(IOException.class, () -> f.reader().read(f.pin(), 128));
            assertThrows(IOException.class, f.reader()::identity);
            assertThrows(IOException.class, () -> ImmutableArtifactStore.readOnlyExisting(f.config(), f.denial()));
            assertThrows(IOException.class, () -> new ImmutableArtifactStore(f.config(), f.denial()));
        }
    }
    @Test void absentOrForeignBackingNeverInitializesAndReplacementIsRejected() throws IOException {
        Path base = Files.createDirectory(temp.resolve("missing"));
        Path lock = Files.write(base.resolve("source.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
        Path missingRoot = base.resolve("artifacts");
        try (StorageWriteGuard denial = StorageWriteGuard.noWrites()) {
            var absent = new ImmutableArtifactStore.Config(missingRoot, lock, 1);
            assertThrows(IOException.class, () -> ImmutableArtifactStore.readOnlyExisting(absent, denial));
            assertFalse(Files.exists(missingRoot));
            Path root = Files.createDirectory(missingRoot), missingLock = base.resolve("absent.lock");
            assertThrows(IOException.class, () -> ImmutableArtifactStore.readOnlyExisting(
                    new ImmutableArtifactStore.Config(root, missingLock, 1), denial));
            assertFalse(Files.exists(missingLock));
        }
        try (Fixture f = fixture("replacement")) {
            assertThrows(IOException.class, () -> ImmutableArtifactStore.readOnlyExisting(f.config(), f.original().storage));
            Path payload = Path.of(f.pin().reference().path());
            Files.move(payload, payload.resolveSibling("original-retained.bin"));
            Files.write(payload, f.payload(), StandardOpenOption.CREATE_NEW);
            assertNotEquals(f.pin().identity().fileIdDecimal(), LedgerFiles.identity(payload).fileIdDecimal());
            assertThrows(IOException.class, () -> f.reader().read(f.pin(), 128));
            assertArrayEquals(f.payload(), Files.readAllBytes(payload));
        }
    }
    @Test void caughtReadOnlyPublicationDenialPoisonsGenuineHistoryScope() throws IOException {
        try (Fixture f = fixture("poison")) {
            IOException failure = assertThrows(IOException.class, () -> f.original().writer.locked(session -> {
                try (var scope = f.reader().beginHistoricalReads(session, 2, 4096, 8,
                        () -> f.original().writer.requireSession(session))) {
                    assertArrayEquals(f.payload(), f.reader().read(f.pin(), 128));
                    assertThrows(IOException.class, () -> f.reader().publish(f.payload(), 128));
                    return null;
                }
            }));
            assertTrue(failure.getMessage().contains("historical CAS validation failed"));
            assertInstanceOf(IOException.class, failure.getCause());
            assertArrayEquals(f.payload(), f.reader().read(f.pin(), 128));
        }
    }
}
