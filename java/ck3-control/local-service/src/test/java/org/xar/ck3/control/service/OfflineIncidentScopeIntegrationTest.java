package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.ZoneOffset;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal;
import org.xar.ck3.control.contracts.offline.IncidentJournalLayout;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisWire;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;

/** Actual producer and host use the same complete identity-derived roots; no native or Game execution. */
final class OfflineIncidentScopeIntegrationTest {
    @TempDir Path temporary;
    @Test void derivedActualJournalIsConsumedByTheFixedBaseHostAndAcknowledgesOnlyItsOwnScope() throws Exception {
        var f = new OfflineInteractionCorpus(temporary.resolve("derived"));
        var identity = f.binding.before();
        var scope = IncidentJournalLayout.scope(f.incidents, f.scans, identity.machineId(), identity.game(), f.binding.sessionId(),
                identity.frame().episodeRunId(), f.binding.source().sourceRef());
        Files.createDirectory(scope.incidentRoot()); Files.createDirectory(scope.scanRoot());
        var config = new EpisodeIncidentJournal.Configuration(scope.incidentRoot(), scope.scanRoot(), Clock.fixed(OfflineInteractionCorpus.NOW, ZoneOffset.UTC),
                pending -> { if (pending < 0 || pending > (1 << 20)) throw new java.io.IOException("finite source scope test cap"); },
                Optional.of(TrustedEventSourceContext.open(f.sources)));
        var journal = EpisodeIncidentJournal.initialize(config, f.binding); var ticket = journal.before(f.command).orElseThrow();
        var batch = journal.scan(f.binding).batch().orElseThrow();
        assertEquals(scope.scanRoot(), Path.of(batch.manifestRef().path()).getParent()); assertEquals(scope.incidentRoot(), Path.of(ticket.before().path()).getParent());
        var settings = new OfflineEventAnalysisHost.Settings(true, false, Optional.of(f.grants), Optional.of(f.incidents), Optional.of(f.knowledge), Optional.of(f.scans));
        var host = new OfflineEventAnalysisHost(Optional.of(f.sources), settings, Optional.of(journal::acknowledge));
        var report = OfflineEventAnalysisWire.parseMetadataObject(host.batch(batch));
        assertEquals(1, report.path("report").path("entries").size()); assertTrue(journal.scan(f.binding).batch().isEmpty());
        assertEquals(1, journal.scan(f.binding).incompleteAfter()); assertFalse(Files.exists(f.incidents.resolve(ticket.incidentId() + ".before.json")), "the explicit flat journal does not inherit this scope's capture");
    }
    @Test void anotherDerivedParentCannotAdoptTheSameManifestEvenWithExactBodySha() throws Exception {
        var f = new OfflineInteractionCorpus(temporary.resolve("wrong-parent")); var id = f.binding.before();
        var scope = IncidentJournalLayout.scope(f.incidents, f.scans, id.machineId(), id.game(), f.binding.sessionId(), id.frame().episodeRunId(), f.binding.source().sourceRef());
        Files.createDirectory(scope.incidentRoot()); Files.createDirectory(scope.scanRoot());
        var config = new EpisodeIncidentJournal.Configuration(scope.incidentRoot(), scope.scanRoot(), Clock.fixed(OfflineInteractionCorpus.NOW, ZoneOffset.UTC), pending -> { }, Optional.of(TrustedEventSourceContext.open(f.sources)));
        var journal = EpisodeIncidentJournal.initialize(config, f.binding); journal.before(f.command); var batch = journal.scan(f.binding).batch().orElseThrow();
        Path wrongParent = Files.createDirectory(f.scans.resolve("a".repeat(64))); Path wrong = wrongParent.resolve(Path.of(batch.manifestRef().path()).getFileName());
        Files.copy(Path.of(batch.manifestRef().path()), wrong);
        var request = new BatchRequest("wrong-derived-parent", OfflineInteractionCorpus.pin(wrong), batch.capturedRefs());
        assertThrows(IllegalArgumentException.class, () -> f.host(true).batch(request)); assertFalse(Files.exists(f.knowledge));
    }
}
