package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.ByteArrayInputStream;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.service.OfflineEventAnalysisHost;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal;
import org.xar.ck3.control.application.planning.events.NativeWindowDiagnostic;
import org.xar.ck3.control.application.planning.events.PendingUiEvent;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisWire;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.wave2.events.unhandledevent.OfflineScanSource;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Existing original private read producer -> rejected first display -> real incident/scan/wire DATA.
 * The fixture supplies no ManagedGame, public Root callback, ordinary Ready, dispatch or after. */
final class RootBlockedPendingIncidentTest {
    private static com.fasterxml.jackson.databind.node.ObjectNode originals;
    @TempDir Path temporary;
    @BeforeAll static void originalInputs() throws Exception {
        PendingUiEventPreparationTest.originalProducers(); originals = PendingUiEventOriginalTestInputs.load();
    }

    @Test void actualFirstDisplayedDisabledRejectionRetainsReadAndCardForNoReadyBatch() throws Exception {
        try (var disk = new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("blocked-card"), 16 * 1024 * 1024)) {
            disk.writer.locked(same -> {
                var archive = disk.archive.withSession(same);
                var fixture = new PendingUiEventPreparationTest.Inputs(disk, archive, same);
                var current = fixture.event(false); String head = same.head().digest();
                var rejected = assertThrows(EventActionPreparation.PendingSelectionRejected.class,
                        () -> fixture.eventPreparation(current, fixture.eventContext(false), 1, "blocked-no-command"));
                var receipt = archive.loadRead(rejected.originalRead());
                var original = RootIncidentRuntime.replayPendingUiOriginal(current,
                        new DriverFrameEvidenceLoader(new DriverObservationAssembler()), archive);
                var configured = configuration(disk.directory, current, fixture);
                var origin = new EpisodeIncidentJournal.Binding(original.identity(), original.source(), original.sessionId());
                var journal = EpisodeIncidentJournal.initializeObserved(configured, origin,
                        archive.preserveMaterial(RootIncidentRuntime.originalObservationBasis(original)));
                var blocked = new RootIncidentRuntime.PendingBlocked(current, receipt, rejected.originalRead(), rejected.diagnosis());
                var ticket = RootIncidentRuntime.capturePendingUiBlockedOriginal(journal, blocked, original, archive, receipt.request().deadline());
                var body = StrictJson.parse(Files.readAllBytes(Path.of(ticket.before().path())));
                assertEquals("xar.unhandled-event-first-rendered/v1", body.path("schema").textValue());
                assertEquals("planning_diagnostic", body.path("stage").textValue());
                assertFalse(body.path("dispatch_attempted").booleanValue());
                assertFalse(body.path("selection").path("enabled").booleanValue());
                assertEquals(3, body.path("selection").path("native_option_index").intValue());
                var index = StrictJson.parse(Files.readAllBytes(Path.of(ticket.index().path())));
                assertEquals("xar.episode-incident-before-index/v2", index.path("schema").textValue());
                assertTrue(index.path("action_id").isNull());
                assertEquals(rejected.originalRead(), ExactRef.fromJson(index.get("original_read_ref")));
                var scan = journal.scan(origin); assertEquals(1, scan.diagnosticOnly()); assertEquals(0, scan.incompleteAfter());
                assertTrue(scan.originals().contains(rejected.originalRead()));
                var batch = scan.batch().orElseThrow();
                assertEquals(batch, OfflineEventAnalysisWire.decodeBatch(OfflineEventAnalysisWire.encode(batch)));
                assertEquals(List.of(ticket.before()), batch.capturedRefs());
                assertOfflineScan(journal, configured, origin, batch, rejected.originalRead(), ticket.incidentId());
                var reopened = EpisodeIncidentJournal.open(configured, origin, journal.episodeReference());
                assertEquals(List.of(batch), RootIncidentRuntime.retainedOriginalBatches(List.of(reopened)));
                assertEquals(ticket, RootIncidentRuntime.capturePendingUiBlockedOriginal(journal, blocked, original, archive,
                        receipt.request().deadline()), "same original blocked card/read is idempotent");
                assertEquals(head, same.head().digest()); return null;
            });
        }
    }

    @Test void actualDisabledAndUnavailableNativeReplyOriginalsBecomeNoCommandIncidents() throws Exception {
        for (String name : List.of("disabled", "no_native")) {
            try (var disk = new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("reply-" + name), 16 * 1024 * 1024)) {
                disk.writer.locked(same -> {
                    var archive = disk.archive.withSession(same);
                    var fixture = new PendingUiEventPreparationTest.Inputs(disk, archive, same);
                    com.fasterxml.jackson.databind.node.ObjectNode row = null;
                    for (var item : originals.path("pending")) if (name.equals(item.path("name").textValue())) {
                        row = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, item.deepCopy()); break;
                    }
                    assertNotNull(row, "original private pending fixture row required");
                    final var input = row; var current = fixture.pending(input); String head = same.head().digest();
                    var rejected = assertThrows(EventActionPreparation.PendingSelectionRejected.class,
                            () -> fixture.replyPreparation(current, input, 1, "blocked-reply-" + name));
                    var receipt = archive.loadRead(rejected.originalRead());
                    var original = RootIncidentRuntime.replayPendingUiOriginal(current,
                            new DriverFrameEvidenceLoader(new DriverObservationAssembler()), archive);
                    var configured = configuration(disk.directory, current, fixture);
                    var origin = new EpisodeIncidentJournal.Binding(original.identity(), original.source(), original.sessionId());
                    var journal = EpisodeIncidentJournal.initializeObserved(configured, origin,
                            archive.preserveMaterial(RootIncidentRuntime.originalObservationBasis(original)));
                    var ticket = RootIncidentRuntime.capturePendingUiBlockedOriginal(journal,
                            new RootIncidentRuntime.PendingBlocked(current, receipt, rejected.originalRead(), rejected.diagnosis()),
                            original, archive, receipt.request().deadline());
                    var body = StrictJson.parse(Files.readAllBytes(Path.of(ticket.before().path())));
                    assertEquals("xar.pending-interaction-left-reply/v1", body.path("schema").textValue());
                    assertEquals("planning_diagnostic", body.path("stage").textValue());
                    assertFalse(body.path("dispatch_attempted").booleanValue());
                    assertEquals(-2130706399, body.path("pending_interaction_id").intValue());
                    var scan = journal.scan(origin); assertEquals(1, scan.diagnosticOnly()); assertEquals(0, scan.incompleteAfter());
                    assertTrue(scan.originals().contains(rejected.originalRead())); assertTrue(scan.batch().isPresent());
                    assertOfflineScan(journal, configured, origin, scan.batch().orElseThrow(), rejected.originalRead(), ticket.incidentId());
                    assertEquals(head, same.head().digest()); return null;
                });
            }
        }
    }

    @Test void actualReadMismatchChangedSourceMetadataAndChangedReadOriginalCannotPass() throws Exception {
        try (var disk = new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("blocked-negative"), 16 * 1024 * 1024)) {
            disk.writer.locked(same -> {
                var archive = disk.archive.withSession(same);
                var fixture = new PendingUiEventPreparationTest.Inputs(disk, archive, same);
                var current = fixture.event(false); String head = same.head().digest();
                var rejected = assertThrows(EventActionPreparation.PendingSelectionRejected.class,
                        () -> fixture.eventPreparation(current, fixture.eventContext(false), 1, "negative-blocked"));
                var receipt = archive.loadRead(rejected.originalRead());
                var original = RootIncidentRuntime.replayPendingUiOriginal(current,
                        new DriverFrameEvidenceLoader(new DriverObservationAssembler()), archive);
                var configured = configuration(disk.directory, current, fixture);
                var origin = new EpisodeIncidentJournal.Binding(original.identity(), original.source(), original.sessionId());
                var journal = EpisodeIncidentJournal.initializeObserved(configured, origin,
                        archive.preserveMaterial(RootIncidentRuntime.originalObservationBasis(original)));
                var other = fixture.eventPreparation(current, fixture.eventContext(true), 2, "another-original-read");
                assertThrows(IllegalArgumentException.class, () -> RootIncidentRuntime.capturePendingUiBlockedOriginal(journal,
                        new RootIncidentRuntime.PendingBlocked(current, other.originalRead(), other.originalReadRef(), rejected.diagnosis()),
                        original, archive, receipt.request().deadline()));
                var meta = OpportunityJson.object(rejected.diagnosis().get("pending_ui_event_source"), "source");
                var wrong = rejected.diagnosis().with("pending_ui_event_source", meta.with("original_read", new OpportunityJson.Bool(true)));
                assertThrows(IllegalArgumentException.class, () -> RootIncidentRuntime.capturePendingUiBlockedOriginal(journal,
                        new RootIncidentRuntime.PendingBlocked(current, receipt, rejected.originalRead(), wrong),
                        original, archive, receipt.request().deadline()));
                assertTrue(RootIncidentRuntime.retainedOriginalBatches(List.of(journal)).isEmpty());
                var blocked = new RootIncidentRuntime.PendingBlocked(current, receipt, rejected.originalRead(), rejected.diagnosis());
                var ticket = RootIncidentRuntime.capturePendingUiBlockedOriginal(journal, blocked, original, archive, receipt.request().deadline());
                Path indexPath = Path.of(ticket.index().path()); byte[] indexBytes = Files.readAllBytes(indexPath);
                var index = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, StrictJson.parse(indexBytes));
                try {
                    for (var wrongRef : List.of(com.fasterxml.jackson.databind.node.NullNode.instance,
                            com.fasterxml.jackson.databind.node.BooleanNode.TRUE,
                            com.fasterxml.jackson.databind.node.DoubleNode.valueOf(1.0),
                            com.fasterxml.jackson.databind.node.TextNode.valueOf(""))) {
                        var changed = index.deepCopy(); changed.set("original_read_ref", wrongRef);
                        // Preserve malformed wire types until the actual journal reader validates them.
                        Files.writeString(indexPath, changed.toString(), java.nio.charset.StandardCharsets.UTF_8);
                        assertThrows(IOException.class, () -> RootIncidentRuntime.retainedOriginalBatches(List.of(journal)));
                    }
                    var missing = index.deepCopy(); missing.remove("original_read_ref");
                    Files.write(indexPath, StrictJson.canonical(missing));
                    assertThrows(IOException.class, () -> RootIncidentRuntime.retainedOriginalBatches(List.of(journal)));
                    var renamed = index.deepCopy(); renamed.set("original_read", renamed.remove("original_read_ref"));
                    Files.write(indexPath, StrictJson.canonical(renamed));
                    assertThrows(IOException.class, () -> RootIncidentRuntime.retainedOriginalBatches(List.of(journal)));
                    var legacyClaim = index.deepCopy(); legacyClaim.put("schema", "xar.episode-incident-before-index/v1");
                    Files.write(indexPath, StrictJson.canonical(legacyClaim));
                    assertThrows(IOException.class, () -> RootIncidentRuntime.retainedOriginalBatches(List.of(journal)));
                } finally { Files.write(indexPath, indexBytes); }
                var batch = journal.scan(origin).batch().orElseThrow();
                var loaded = assertOfflineScan(journal, configured, origin, batch, rejected.originalRead(), ticket.incidentId());
                Path readPath = Path.of(rejected.originalRead().path()); byte[] bytes = Files.readAllBytes(readPath);
                try {
                    byte[] changed = java.util.Arrays.copyOf(bytes, bytes.length + 1); changed[bytes.length] = ' ';
                    Files.write(readPath, changed);
                    assertThrows(IOException.class, () -> RootIncidentRuntime.retainedOriginalBatches(List.of(journal)),
                            "a captured actual read pin cannot disappear or be accepted after mutation");
                    var changedOriginal = assertThrows(ContractViolationException.class, () -> OfflineScanSource.recheck(
                            configured.incidentRoot(), Optional.of(configured.scanRoot()), batch.manifestRef(), loaded));
                    assertEquals("Actual external original changed identity, bytes or SHA", changedOriginal.getMessage());
                } finally { Files.write(readPath, bytes); }
                assertEquals(1, RootIncidentRuntime.retainedOriginalBatches(List.of(journal)).size());
                OfflineScanSource.recheck(configured.incidentRoot(), Optional.of(configured.scanRoot()), batch.manifestRef(), loaded);
                assertEquals(head, same.head().digest()); return null;
            });
        }
    }

    @Test void sharedComposerWithMissingContextPreservesOriginalPlanAndDoesNotInventKey() throws Exception {
        try (var disk = new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("blocked-diagnostic"), 16 * 1024 * 1024)) {
            disk.writer.locked(same -> {
                var archive = disk.archive.withSession(same);
                var fixture = new PendingUiEventPreparationTest.Inputs(disk, archive, same);
                var current = fixture.event(false);
                var rejected = assertThrows(EventActionPreparation.PendingSelectionRejected.class,
                        () -> fixture.eventPreparation(current, fixture.eventContext(false), 1, "original-diagnostic"));
                var source = new NativeWindowDiagnostic.Source(current.frame().identity(), current.frame().semantic(),
                        new ArrayList<>(current.history()), Optional.empty(), Optional.of(rejected.diagnosis()),
                        "actual native window definition unavailable");
                var plan = NativeWindowDiagnostic.plan(source).orElseThrow();
                assertEquals(OpportunityJson.Nil.INSTANCE, plan.get("selected_step"));
                var body = OpportunityJson.object(plan.get("unhandled_native_window_diagnostic"), "diagnostic");
                assertEquals(OpportunityJson.Nil.INSTANCE, body.get("selection"));
                assertEquals(OpportunityJson.Nil.INSTANCE, body.get("event_definition_key"));
                assertEquals(OpportunityJson.Nil.INSTANCE, body.get("context"));
                assertEquals(rejected.diagnosis(), body.get("original_plan"));
                assertEquals(current.frame().identity(), org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.decodeObservation(
                        org.xar.ck3.control.application.driver.DriverJson.toNode(body.get("origin"))));
                return null;
            });
        }
    }

    private static OfflineScanSource.Loaded assertOfflineScan(EpisodeIncidentJournal journal,
            EpisodeIncidentJournal.Configuration configured, EpisodeIncidentJournal.Binding binding,
            BatchRequest batch, ExactRef actualRead, String incidentId) throws IOException {
        var manifest = StrictJson.parse(Files.readAllBytes(Path.of(batch.manifestRef().path())));
        assertTrue(manifest.path("new_incidents").get(0).path("after").isNull());
        assertTrue(manifest.path("new_incidents").get(0).path("after_sha256").isNull());
        var loaded = OfflineScanSource.load(configured.incidentRoot(), Optional.of(configured.scanRoot()),
                binding.before().machineId(), batch.manifestRef(), batch.capturedRefs());
        assertTrue(loaded.externalOriginals().stream().anyMatch(role -> role.source().equals(actualRead)),
                "the actual Known READ original must remain in the downstream recheck closure");
        OfflineScanSource.recheck(configured.incidentRoot(), Optional.of(configured.scanRoot()), batch.manifestRef(), loaded);
        assertOfflineUnresolved(journal, configured, binding, batch, incidentId);
        return loaded;
    }

    /** Uses the real offline Host and journal completion on the original no-action batch. */
    static void assertOfflineUnresolved(EpisodeIncidentJournal journal, EpisodeIncidentJournal.Configuration configured,
            EpisodeIncidentJournal.Binding binding, BatchRequest batch, String incidentId) throws IOException {
        Path output = Files.createDirectories(configured.incidentRoot().getParent().resolve("offline-" + incidentId));
        var sources = offlineSources(output, binding.before().machineId());
        Path knowledge = Files.createDirectories(output.resolve("knowledge"));
        var host = new OfflineEventAnalysisHost(Optional.of(sources), new OfflineEventAnalysisHost.Settings(true, false,
                Optional.of(knowledge.resolve("fixed-grants.json")), Optional.of(configured.incidentRoot()),
                Optional.of(knowledge), Optional.of(configured.scanRoot())), Optional.of(journal::acknowledge));
        var response = StrictJson.parse(host.batch(batch));
        var report = response.path("report");
        assertEquals(0, report.path("entries").size()); assertEquals(0, report.path("already_known").size());
        assertEquals(1, report.path("unresolved").size());
        assertEquals(incidentId, report.path("unresolved").get(0).path("incident_id").textValue());
        assertEquals(0, response.path("grants_manifest").path("grants").intValue());
        assertEquals(0, response.path("grants_manifest").path("added").intValue());
        assertEquals(0, response.path("Game_MCP_OBS_calls").intValue());
        assertEquals(0, response.path("timeline_writer_calls").intValue());
        assertFalse(Files.exists(configured.incidentRoot().resolve(incidentId + ".review-index.json")),
                "an unresolved source report cannot complete this incident or create action/after credit");
    }

    @Test void actualCouncilBlobExceedsLabelLimitAndRetainsItsOriginalSha()throws Exception {
        try(var resource=getClass().getResourceAsStream("/offline-worker/source-review-council-golden-v1.json.gz")) {
            assertNotNull(resource);
            try(var gzip=new GZIPInputStream(resource)) {
                byte[] raw=gzip.readNBytes((1<<20)+1);assertTrue(raw.length<=1<<20);
                var corpus=StrictJson.parse(raw,1<<20);
                var largest=corpus.path("blobs").properties().stream().max(java.util.Comparator.comparingInt(row->row.getValue().textValue().length())).orElseThrow();
                assertTrue(largest.getValue().textValue().length()>32768);
                assertThrows(IllegalArgumentException.class,()->StrictJson.text(largest.getValue()));
                var relocated=offlineSources(temporary.resolve("council-large-blob"),"council-large-blob");
                for(var row:corpus.path("stock_refs"))if(largest.getKey().equals(StrictJson.text(row.get("sha256")))) {
                    String relative=StrictJson.text(row.get("relative"));assertTrue(relative.startsWith("game/"));
                    byte[] actual=Files.readAllBytes(relocated.stockGameRoot().resolve(relative.substring(5)));
                    assertEquals(largest.getKey(),DriverJson.sha256(actual));assertEquals(row.get("bytes").longValue(),actual.length);return;
                }
                fail("original largest council blob has no stock source reference");
            }
        }
    }
    /** Relocates only existing immutable golden source bytes; original Trusted checks still run. */
    static EventSourceReadContext offlineSources(Path output, String machineId) throws IOException {
        var blobs = new LinkedHashMap<String, String>();
        var originals = new LinkedHashMap<String, com.fasterxml.jackson.databind.JsonNode>();
        for (String cohort : List.of("liberty", "council", "sway")) {
            String name = "/offline-worker/source-review-" + cohort + "-golden-v1.json.gz";
            try (var resource = RootBlockedPendingIncidentTest.class.getResourceAsStream(name)) {
                if (resource == null) throw new IOException("mandatory actual source-review cohort missing; NOT RUN: " + cohort);
                try (var gzip = new GZIPInputStream(resource)) {
                    byte[] bytes = gzip.readNBytes((1 << 20) + 1);
                    if (bytes.length > (1 << 20)) throw new IOException("actual source-review cohort bound exceeded");
                    var corpus = StrictJson.parse(bytes, 1 << 20);
                    for(var blob:corpus.path("blobs").properties()) {
                        var encoded=blob.getValue();
                        if(!encoded.isTextual()||encoded.textValue().isEmpty()||encoded.textValue().length()>(1<<20))throw new IOException("bounded original base64 source blob required");
                        blobs.put(blob.getKey(),encoded.textValue());
                    }
                    for (var row : corpus.path("stock_refs")) originals.put(StrictJson.text(row.get("relative")), row);
                }
            }
        }
        Path stock = Files.createDirectories(output.resolve("stock"));
        for (var entry : originals.entrySet()) {
            String relative = entry.getKey(); assertTrue(relative.startsWith("game/"));
            Path target = stock.resolve(relative.substring("game/".length())).normalize();
            assertTrue(target.startsWith(stock) && !target.equals(stock));
            String sha = StrictJson.text(entry.getValue().get("sha256"));
            String encoded = blobs.get(sha); assertNotNull(encoded, "mandatory retained stock blob missing: " + relative);
            try (var gzip = new GZIPInputStream(new ByteArrayInputStream(Base64.getDecoder().decode(encoded)))) {
                byte[] bytes = gzip.readNBytes(2_097_153); assertTrue(bytes.length <= 2_097_152);
                assertEquals(sha, DriverJson.sha256(bytes));
                assertEquals(entry.getValue().get("bytes").longValue(), bytes.length);
                Files.createDirectories(target.getParent()); Files.write(target, bytes);
            }
        }
        return new EventSourceReadContext(machineId, Files.createDirectories(output.resolve("state")), stock);
    }

    private static EpisodeIncidentJournal.Configuration configuration(Path root, PendingUiEvent.Current actual,
            PendingUiEventPreparationTest.Inputs fixture) throws IOException {
        return new EpisodeIncidentJournal.Configuration(Files.createDirectory(root.resolve("incidents")),
                Files.createDirectory(root.resolve("scans")), Clock.fixed(actual.frame().observedAt(), ZoneOffset.UTC),
                size -> { if (size < 0 || size > (1 << 20)) throw new IOException("finite original blocked-card fixture output"); },
                Optional.of(fixture.trusted));
    }
}
