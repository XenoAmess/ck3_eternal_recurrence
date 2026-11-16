package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Pure retained-Driver byte consumer against the actual committed CAS; no cold-source or Game permission is minted. */
final class ColdRestoreDriverCasBoundTest {
    @TempDir Path root;

    @Test void fullMaterialDriverKeepsItsExactCommittedBytesAndRejectsWrongReferencesOrTamper() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("cold-driver-cas-bound"), false)) {
            int actions = fixture.nativeActionWrites(), reads = fixture.nativeReadWrites();
            fixture.writer.locked(same -> {
                var known = fixture.driverAuthority().withFrozenFacts(same, frozen -> (DriverSnapshotFacts.Known) frozen.state());
                var before = known.driver();
                var full = new DriverStateSnapshot.Complete(before.session(), before.commandHistory(), before.lastCheckpoint(),
                        before.rollbackWarFailure(), before.managedRestoreTransaction(), before.successionExpectation(),
                        before.successionLifecycle(), new DriverStateSnapshot.Value(("{\"retained_driver_payload\":\""
                                + "x".repeat(160 * 1024) + "\"}").getBytes(StandardCharsets.UTF_8)), before.rollbackWarFailures());
                byte[] expected = full.encode();
                assertTrue(expected.length > (128 << 10), "the retained Driver must stay in the full-material lane, beyond an ordinary 128KiB token");
                ExactRef original = fixture.archive.preserveMaterial(RawJson.fullMaterial(expected));
                byte[] actual = RootApplicationAssembly.Core.ColdRestoreSource.readRetainedDriverOriginal(fixture.archive, same, original);
                assertArrayEquals(expected, actual);
                assertArrayEquals(full.encode(), DriverStateSnapshot.decodeComplete(actual).encode());
                assertThrows(IOException.class, () -> RootApplicationAssembly.Core.ColdRestoreSource.readRetainedDriverOriginal(
                        fixture.archive, same, new ExactRef(original.path(), original.bytes() + 1, original.sha256())));
                assertThrows(IOException.class, () -> RootApplicationAssembly.Core.ColdRestoreSource.readRetainedDriverOriginal(
                        fixture.archive, same, new ExactRef(original.path(), original.bytes(), "0".repeat(64))));
                // No64MiB allocation is needed to exercise the real upper-bound rejection.
                assertThrows(IOException.class, () -> RootApplicationAssembly.Core.ColdRestoreSource.readRetainedDriverOriginal(
                        fixture.archive, same, new ExactRef(original.path(), (long) RawJson.MAXIMUM_BYTES + 1, original.sha256())));
                assertArrayEquals(expected, RootApplicationAssembly.Core.ColdRestoreSource.readRetainedDriverOriginal(fixture.archive, same, original));
                Files.write(Path.of(original.path()), "{}".getBytes(StandardCharsets.UTF_8));
                assertThrows(IOException.class, () -> RootApplicationAssembly.Core.ColdRestoreSource.readRetainedDriverOriginal(fixture.archive, same, original));
                return null;
            });
            assertEquals(actions, fixture.nativeActionWrites()); assertEquals(reads, fixture.nativeReadWrites());
        }
    }
}
