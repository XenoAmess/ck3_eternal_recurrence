package org.xar.ck3.control.service;

import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceCodec;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrant;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceRole;
import org.xar.ck3.control.wave2.events.sourcecatalog.EvidenceGrantManifestPublisher;
import static org.junit.jupiter.api.Assertions.*;

class OfflineEventAnalysisInitializationTest {
    @TempDir Path directory;
    private EventSourceReadContext sources() throws Exception {
        return new EventSourceReadContext("fixture-machine", Files.createDirectories(directory.resolve("state")).toAbsolutePath(),
                Files.createDirectories(directory.resolve("stock")).toAbsolutePath());
    }
    private OfflineEventAnalysisHost.Settings settings(boolean enabled, Path manifest) {
        return new OfflineEventAnalysisHost.Settings(enabled, Optional.of(manifest.toAbsolutePath()), Optional.empty(), Optional.empty());
    }
    @Test void explicitOfflineStartupCreatesAValidEmptyManifestAndRetainsTheActualPublication() throws Exception {
        Path manifest = directory.resolve("grants.json").toAbsolutePath();
        var host = new OfflineEventAnalysisHost(Optional.of(sources()), settings(true, manifest));
        assertTrue(host.mandatoryScope().isPresent()); assertTrue(host.batchScope().isEmpty());
        assertEquals(List.of(), ProjectionEvidenceCodec.decode(Files.readAllBytes(manifest)));
        var initialized = host.initialization().orElseThrow(); assertEquals(manifest, initialized.path());
        assertEquals(Files.size(manifest), initialized.bytes()); assertEquals(0, initialized.grants());
    }
    @Test void explicitStartupPreservesExistingPinsAndNeverReplacesMalformedKnowledgeWithEmpty() throws Exception {
        Path manifest = directory.resolve("grants.json").toAbsolutePath();
        Path fact = directory.resolve("original-fact.json").toAbsolutePath(); byte[] original = "{}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        Files.write(fact, original);
        var grant = new ProjectionEvidenceGrant(fact, original.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)), "unknown", ProjectionEvidenceRole.EVENT_SOURCE_FACTS);
        EvidenceGrantManifestPublisher.publish(manifest, List.of(grant)); byte[] before = Files.readAllBytes(manifest);
        new OfflineEventAnalysisHost(Optional.of(sources()), settings(true, manifest));
        assertArrayEquals(before, Files.readAllBytes(manifest));
        Files.writeString(manifest, "{}");
        assertThrows(IllegalStateException.class, () -> new OfflineEventAnalysisHost(Optional.of(sources()), settings(true, manifest)));
        assertEquals("{}", Files.readString(manifest));
    }
    @Test void disabledStartupPerformsNoKnowledgeWrite() {
        Path manifest = directory.resolve("never-created.json").toAbsolutePath();
        var host = new OfflineEventAnalysisHost(Optional.empty(), settings(false, manifest));
        assertTrue(host.initialization().isEmpty()); assertTrue(host.mandatoryScope().isEmpty()); assertFalse(Files.exists(manifest));
    }
    @Test void captureOnlyStartupRejectsPublishingBeforeAnyManifestInitialization() {
        Path manifest = directory.resolve("capture-must-not-write.json").toAbsolutePath();
        var publishing = new OfflineEventAnalysisHost.Settings(true, true, Optional.of(manifest), Optional.empty(), Optional.empty());
        assertThrows(IllegalStateException.class, () -> new OfflineEventAnalysisHost(Optional.empty(), publishing));
        assertFalse(Files.exists(manifest));
        var capture = new OfflineEventAnalysisHost.Settings(false, true, Optional.of(manifest), Optional.empty(), Optional.empty());
        assertTrue(new OfflineEventAnalysisHost(Optional.empty(), capture).initialization().isEmpty());
        assertFalse(Files.exists(manifest));
    }
}
