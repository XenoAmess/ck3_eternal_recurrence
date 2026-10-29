package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.RawJson;

/** The domain owns actual ACK sidecar binding. This tests the sole physical digest lookup capability. */
final class NativeArchiveMaterialLookupTest {
    @TempDir Path root;
    @Test void producerOriginalReopensByDigestFromCommittedCasAfterExternalSidecarChangesWithoutWrites() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("reopen"), false)) {
            byte[] original = "{\"full_original\":{\"optional\":null,\"values\":[],\"scale\":1.0,\"filetime\":\"9007199254740993\"}}".getBytes(StandardCharsets.UTF_8);
            Path external = root.resolve("mutable-live-sidecar.json"); Files.write(external, original);
            var preserved = fixture.archive.preserveMaterial(new RawJson(Files.readAllBytes(external)));
            String producerDigest = ActionCodec.sha256(original); long producerBytes = original.length;
            assertEquals(producerDigest, preserved.sha256()); assertEquals(producerBytes, preserved.bytes());
            Files.writeString(external, "{\"changed_external_sidecar\":true}");
            byte[] ledger = fixture.ledgerBytes(); long retained = fixture.archive.artifactStore().retainedNativeBytes();
            var found = fixture.writer.locked(session -> fixture.archive.withSession(session).materialReference(producerDigest, producerBytes));
            assertEquals(preserved, found); assertArrayEquals(original, fixture.archive.loadMaterial(found).bytes());
            assertEquals(found, fixture.archive.materialReference(producerDigest, producerBytes));
            assertEquals(retained, fixture.archive.artifactStore().retainedNativeBytes()); assertArrayEquals(ledger, fixture.ledgerBytes());
            assertEquals("{\"changed_external_sidecar\":true}", Files.readString(external));
        }
    }
    @Test void absentWrongSizeInvalidDigestPacketRoleAndCorruptOriginalRefuseWithoutRepair() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("reject"), false)) {
            var material = fixture.archive.preserveMaterial(new RawJson("{\"actual_material\":true}".getBytes(StandardCharsets.UTF_8)));
            long retained = fixture.archive.artifactStore().retainedNativeBytes();
            assertThrows(UncheckedIOException.class, () -> fixture.archive.materialReference("0".repeat(64), 10));
            assertThrows(UncheckedIOException.class, () -> fixture.archive.materialReference(material.sha256(), material.bytes() + 1));
            assertThrows(IllegalArgumentException.class, () -> fixture.archive.materialReference("../foreign-sidecar", material.bytes()));
            assertThrows(IllegalArgumentException.class, () -> fixture.archive.materialReference(material.sha256(), -1));
            assertThrows(UncheckedIOException.class, () -> fixture.archive.materialReference(material.sha256(), RawJson.MAXIMUM_BYTES + 1L));
            assertEquals(retained, fixture.archive.artifactStore().retainedNativeBytes());
            var ready = fixture.ready(); byte[] packet = NativeArchiveSupportingMaterialsTest.frame(ready.request(), 18, false, Instant.now()).originalPacket();
            var rawPacket = fixture.writer.locked(session -> fixture.archive.preserveArtifact(session, packet, 65536));
            assertThrows(IllegalArgumentException.class, () -> fixture.archive.materialReference(rawPacket.sha256(), rawPacket.bytes()));
            Files.writeString(Path.of(material.path()), "{\"changed\":true}");
            assertThrows(UncheckedIOException.class, () -> fixture.archive.materialReference(material.sha256(), material.bytes()));
            assertEquals("{\"changed\":true}", Files.readString(Path.of(material.path())));
        }
    }
}
