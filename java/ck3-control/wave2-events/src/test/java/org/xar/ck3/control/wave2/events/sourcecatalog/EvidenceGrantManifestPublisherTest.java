package org.xar.ck3.control.wave2.events.sourcecatalog;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.FutureTask;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceCodec;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrant;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceRole;

final class EvidenceGrantManifestPublisherTest {
    @TempDir Path temporary;
    @Test void newSourceFactsPreserveExistingUiEvidenceAndPublicationIsIdempotent() throws Exception {
        Path manifest = temporary.resolve("fixed-grants.json");
        ProjectionEvidenceGrant ui = original("historical-before.json", ProjectionEvidenceRole.UI_RECOVERY_BEFORE);
        ProjectionEvidenceGrant facts = original("source-facts.json", ProjectionEvidenceRole.EVENT_SOURCE_FACTS);
        EvidenceGrantManifestPublisher.Publication first = EvidenceGrantManifestPublisher.publish(manifest, List.of(ui));
        assertEquals(1, first.added());
        EvidenceGrantManifestPublisher.Publication second = EvidenceGrantManifestPublisher.publish(manifest, List.of(facts));
        assertEquals(List.of(ui, facts), ProjectionEvidenceCodec.decode(Files.readAllBytes(manifest)));
        byte[] committed = Files.readAllBytes(manifest);
        EvidenceGrantManifestPublisher.Publication repeated = EvidenceGrantManifestPublisher.publish(manifest, List.of(facts));
        assertEquals(0, repeated.added()); assertEquals(second.sha256(), repeated.sha256()); assertArrayEquals(committed, Files.readAllBytes(manifest));
        Files.writeString(facts.path(), "different bytes");
        assertThrows(java.io.IOException.class, () -> EvidenceGrantManifestPublisher.publish(manifest, List.of(facts)));
        assertArrayEquals(committed, Files.readAllBytes(manifest));
    }
    @Test void simultaneousUiAndEventProducersQueueAtTheSameWriterAndRetainBothRoles() throws Exception {
        Path manifest = temporary.resolve("concurrent-grants.json");
        ProjectionEvidenceGrant ui = original("concurrent-ui.json", ProjectionEvidenceRole.UI_RECOVERY_BEFORE);
        ProjectionEvidenceGrant facts = original("concurrent-facts.json", ProjectionEvidenceRole.EVENT_SOURCE_FACTS);
        CountDownLatch holding = new CountDownLatch(1), release = new CountDownLatch(1), attempted = new CountDownLatch(1);
        AtomicReference<EvidenceGrantManifestPublisher.Writer> escaped = new AtomicReference<>();
        FutureTask<EvidenceGrantManifestPublisher.Publication> first = new FutureTask<>(() -> EvidenceGrantManifestPublisher.transaction(manifest, writer -> {
            escaped.set(writer); holding.countDown();
            try { if (!release.await(5, TimeUnit.SECONDS)) throw new java.io.IOException("test writer release timed out"); }
            catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new java.io.IOException(interrupted); }
            return writer.publish(List.of(ui));
        }));
        FutureTask<EvidenceGrantManifestPublisher.Publication> second = new FutureTask<>(() -> {
            attempted.countDown(); return EvidenceGrantManifestPublisher.publish(manifest, List.of(facts));
        });
        Thread uiProducer = new Thread(first, "offline-ui-producer"), eventProducer = new Thread(second, "offline-event-producer");
        uiProducer.start();
        try {
            assertTrue(holding.await(5, TimeUnit.SECONDS)); eventProducer.start(); assertTrue(attempted.await(5, TimeUnit.SECONDS));
            long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(2);
            while (eventProducer.getState() != Thread.State.BLOCKED && eventProducer.isAlive() && System.nanoTime() < deadline) Thread.sleep(1);
            assertEquals(Thread.State.BLOCKED, eventProducer.getState(), "same-JVM contention queues before opening another overlapping OS lock");
        } finally { release.countDown(); }
        assertEquals(1, first.get(5, TimeUnit.SECONDS).added()); assertEquals(1, second.get(5, TimeUnit.SECONDS).added());
        assertEquals(List.of(ui, facts), ProjectionEvidenceCodec.decode(Files.readAllBytes(manifest)));
        assertThrows(java.io.IOException.class, () -> escaped.get().publish(List.of(ui)), "a callback cannot retain writer authority after the transaction");
        uiProducer.join(5000); eventProducer.join(5000); assertFalse(uiProducer.isAlive()); assertFalse(eventProducer.isAlive());
    }
    private ProjectionEvidenceGrant original(String file, ProjectionEvidenceRole role) throws Exception {
        Path path = temporary.resolve(file); byte[] raw = ("{\"fixture\":\"" + file + "\"}").getBytes(java.nio.charset.StandardCharsets.UTF_8);
        Files.write(path, raw); String sha = HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw));
        return new ProjectionEvidenceGrant(path, raw.length, sha, "unknown", role);
    }
}
