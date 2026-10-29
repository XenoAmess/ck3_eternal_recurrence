package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;

/** Actual same-writer archive producer/cold reader; full material never grants Native or Known authority. */
final class NativeOutcomeArchiveFullMaterialTest {
    @TempDir Path root;
    private static byte[] fullBytes() {
        return ("{\"opaque\":" + "7".repeat(70_000)
                + ",\"negative_zero\":-0.0,\"decimal\":1.0,\"nested\":{\"original\":\"opaque\"}}")
                .getBytes(StandardCharsets.UTF_8);
    }
    private static long files(Path root) throws Exception {
        try (var paths = Files.walk(root)) { return paths.filter(Files::isRegularFile).count(); }
    }
    private static ExactRef retainRaw(ActionWriterIntegrationFixture actual, byte[] bytes) throws Exception {
        return actual.writer.locked(same -> actual.archive.preserveArtifact(same, bytes, RawJson.MAXIMUM_BYTES));
    }
    @Test void actualFullMaterialProducerAndColdReaderPreserveLargeOpaqueNumericBytesWithoutWideningNative() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("full"), false)) {
            actual.ready(); byte[] bytes = fullBytes();
            assertThrows(IllegalArgumentException.class, () -> new RawJson(bytes));
            RawJson original = RawJson.fullMaterial(bytes);
            ExactRef retained = actual.archive.preserveMaterial(original);
            assertEquals(retained, actual.archive.materialReferenceOf(original));
            byte[] ledger = actual.ledgerBytes(); long count = files(actual.root);
            RawJson restored = actual.archive.loadFullMaterial(retained);
            assertEquals(original, restored); assertArrayEquals(bytes, restored.bytes());
            assertEquals(original.objectFieldNames(), restored.objectFieldNames());
            assertTrue(new String(restored.bytes(), StandardCharsets.UTF_8).contains("\"negative_zero\":-0.0,\"decimal\":1.0"));
            actual.writer.locked(same -> {
                assertArrayEquals(bytes, actual.archive.withSession(same).loadFullMaterial(retained).bytes());
                return null;
            });
            assertThrows(IllegalArgumentException.class, restored::requireProtocolBound);
            assertThrows(RuntimeException.class, () -> actual.archive.loadMaterial(retained));
            assertEquals(count, files(actual.root)); assertArrayEquals(ledger, actual.ledgerBytes());
            assertEquals(0, actual.nativeActionWrites()); assertEquals(0, actual.snapshot().ledgerSequence());
        }
    }
    @Test void fullRoleStillRequiresExistingCanonicalBytesAndDoesNotRepairMissingOriginals() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("missing"), false)) {
            actual.ready(); byte[] bytes = fullBytes();
            ExactRef retained = actual.archive.preserveMaterial(RawJson.fullMaterial(bytes));
            // An equal diagnostic file outside the existing immutable store is not its canonical original.
            Path alias = actual.root.resolve("same-bytes-unowned-DATA.json"); Files.write(alias, bytes);
            ExactRef other = new ExactRef(alias.toAbsolutePath().normalize().toString(), bytes.length, ActionCodec.sha256(bytes));
            byte[] ledger = actual.ledgerBytes(); long count = files(actual.root);
            assertThrows(RuntimeException.class, () -> actual.archive.loadFullMaterial(other));
            assertEquals(count, files(actual.root)); assertArrayEquals(ledger, actual.ledgerBytes());
            Path missing = Path.of(retained.path()); assertTrue(missing.normalize().startsWith(actual.root.normalize()));
            Files.delete(missing); long after = files(actual.root);
            assertThrows(RuntimeException.class, () -> actual.archive.loadFullMaterial(retained));
            assertFalse(Files.exists(missing)); assertEquals(after, files(actual.root));
            assertArrayEquals(ledger, actual.ledgerBytes()); assertEquals(0, actual.nativeActionWrites());
        }
    }
    @Test void explicitFullMaterialStillRejectsMalformedJsonAndFramedNativePacketRoles() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("strict"), false)) {
            actual.ready();
            for (byte[] invalid : List.of(
                    "{\"x\":1,\"x\":2}".getBytes(StandardCharsets.UTF_8),
                    "{} true".getBytes(StandardCharsets.UTF_8),
                    new byte[] { (byte) 0xc0, (byte) 0xaf })) {
                ExactRef original = retainRaw(actual, invalid); long count = files(actual.root);
                byte[] ledger = actual.ledgerBytes();
                assertThrows(RuntimeException.class, () -> actual.archive.loadFullMaterial(original));
                assertEquals(count, files(actual.root)); assertArrayEquals(ledger, actual.ledgerBytes());
            }
            // This is the actual retained READ before snapshot, not a caller-generated JSON packet.
            ExactRef nativePacket = actual.lastNestedRead.get().before().binding().nativeEvidence();
            byte[] original = actual.archive.loadNativeFrame(nativePacket);
            assertInstanceOf(NativeWire.Snapshot.class, NativeWire.decode(original));
            byte[] ledger = actual.ledgerBytes(); long count = files(actual.root);
            assertThrows(RuntimeException.class, () -> actual.archive.loadFullMaterial(nativePacket));
            assertArrayEquals(original, actual.archive.loadNativeFrame(nativePacket));
            assertEquals(count, files(actual.root)); assertArrayEquals(ledger, actual.ledgerBytes());
            assertEquals(0, actual.nativeActionWrites());
        }
    }
}
