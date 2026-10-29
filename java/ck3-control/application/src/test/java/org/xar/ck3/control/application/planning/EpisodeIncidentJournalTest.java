package org.xar.ck3.control.application.planning;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal.Binding;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisWire;
import org.xar.ck3.control.contracts.offline.OfflineBatchBinding;
import org.xar.ck3.control.contracts.offline.IncidentReadIndex;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.OfflineScanSource;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventCodec;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback;

/** Synthetic current-frame inputs call the real fallback/body/journal/wire producers; no Native or Game credit. */
final class EpisodeIncidentJournalTest {
    @TempDir Path temporary;
    private record Fixture(PlanningRequest request, EpisodeIncidentJournal journal, EpisodeIncidentJournal.Configuration configured) { }
    private Fixture fixture() throws Exception {
        Path evidence = temporary.resolve("actual-source.json"); Files.writeString(evidence, "{\"scope\":\"synthetic-source-bound-journal-test\"}");
        var base = PlanningFixtures.request(PlanningFixtures.snapshot(), List.of(), Set.of(new OperationKey("select-event-option-1")));
        var source = new G2Source(base.before().machineId(), PlanningFixtures.NOW.toString(), "SYNTHETIC-JOURNAL-TEST", EpisodeIncidentJournal.measure(evidence));
        PlanningRequest request = new PlanningRequest(base.before(), source, base.sessionId(), base.deadline(), base.observations());
        Path incidents = Files.createDirectory(temporary.resolve("incidents")), scans = Files.createDirectory(temporary.resolve("scans"));
        var configured = new EpisodeIncidentJournal.Configuration(incidents, scans, Clock.fixed(PlanningFixtures.NOW, ZoneOffset.UTC), pending -> {
            if (pending < 0 || pending > (1 << 20)) throw new java.io.IOException("finite test write cap");
        }, Optional.empty());
        var journal = EpisodeIncidentJournal.initialize(configured, bind(request));
        return new Fixture(request, journal, configured);
    }
    @Test void originalEmptyDirectoryScanHasSourcePinsAndMissingOriginalIsNeverAnEmptyScan() throws Exception {
        Fixture f = fixture(); var scan = f.journal().scan(bind(f.request()));
        assertTrue(scan.batch().isEmpty()); assertEquals(0, scan.incidents()); assertTrue(scan.evidence().contains(scan.indexRef()));
        assertTrue(scan.evidence().contains(f.journal().episodeReference()));
        JsonNode index = StrictJson.parse(Files.readAllBytes(Path.of(scan.indexRef().path())));
        assertEquals(EpisodeIncidentJournal.SCAN_SCHEMA, index.get("schema").textValue()); assertEquals(0, index.get("incidents").intValue());
        assertEquals(scan.indexRef(), f.journal().scan(bind(f.request())).indexRef(), "same actual directory/frame is a stable scan, not another empty default");
        Files.delete(Path.of(f.journal().episodeReference().path()));
        assertThrows(java.io.IOException.class, () -> f.journal().scan(bind(f.request())));
        assertThrows(java.io.IOException.class, () -> EpisodeIncidentJournal.open(f.configured(), bind(f.request()), f.journal().episodeReference()));
    }
    @Test void actualFallbackAndBeforeBodyBecomeTheCapturedBatchOriginalsWithoutDriverHistory() throws Exception {
        Fixture f = fixture(); ActionCommand command = command(f.request());
        var ticket = f.journal().before(command).orElseThrow(); var repeated = f.journal().before(command).orElseThrow();
        assertEquals(ticket, repeated); var scan = f.journal().scan(bind(f.request())); var batch = scan.batch().orElseThrow();
        assertEquals(1, scan.incidents()); assertEquals(1, scan.incompleteAfter()); assertTrue(batch.capturedRefs().contains(ticket.before()));
        ObjectNode manifest = (ObjectNode)StrictJson.parse(Files.readAllBytes(Path.of(batch.manifestRef().path())));
        assertEquals(EpisodeIncidentJournal.MANIFEST_SCHEMA, manifest.get("schema").textValue()); assertFalse(manifest.has("completed_control_sequence"));
        assertEquals(ticket.incidentId(), manifest.path("new_incidents").get(0).path("incident_id").textValue());
        assertTrue(manifest.path("new_incidents").get(0).path("after").isNull(), "before and UNKNOWN do not invent a native after");
        assertTrue(Path.of(batch.manifestRef().path()).startsWith(f.configured().scanRoot()));
        ObjectNode wire = StrictJson.object().put("schema", "xar.offline-event-batch-request/v1").put("batch_id", batch.batchId());
        wire.set("manifest_ref", batch.manifestRef().toJson()); var refs = wire.putArray("captured_refs"); batch.capturedRefs().forEach(ref -> refs.add(ref.toJson()));
        assertEquals(batch, OfflineEventAnalysisWire.decodeBatch(StrictJson.canonical(wire)));
        assertEquals(scan.indexRef(), f.journal().scan(bind(f.request())).indexRef(), "published manifests do not pollute the incident source inventory");
        ObjectNode tampered = (ObjectNode)StrictJson.parse(Files.readAllBytes(Path.of(ticket.before().path()))); tampered.put("incident_id", "wrong-original");
        Files.write(Path.of(ticket.before().path()), StrictJson.canonical(tampered));
        assertThrows(java.io.IOException.class, () -> f.journal().scan(bind(f.request())));
    }
    @Test void onlySourceBoundCompletedReviewIdsLeaveThePendingIncidentSet() throws Exception {
        Fixture f = fixture(); var ticket = f.journal().before(command(f.request())).orElseThrow(); var batch = f.journal().scan(bind(f.request())).batch().orElseThrow();
        ObjectNode manifest = (ObjectNode)StrictJson.parse(Files.readAllBytes(Path.of(batch.manifestRef().path())));
        ObjectNode report = StrictJson.object().put("schema", OfflineBatchBinding.reportSchema(EpisodeIncidentJournal.requireBatchManifest(manifest))).put("machine_id", f.request().before().machineId()).put("session_id", f.request().sessionId());
        report.set("manifest", batch.manifestRef().toJson());
        for (String field : List.of("scan_observation", "scan_source", "index_ref")) report.set(field, manifest.get(field));
        report.putArray("entries").addObject().put("incident_id", ticket.incidentId()); report.putArray("already_known");
        report.putArray("unresolved").addObject().put("incident_id", ticket.incidentId()).put("reason", "synthetic pending source");
        Path pending = temporary.resolve("SYNTHETIC-PENDING-REPORT.json"); Files.write(pending, StrictJson.canonical(report));
        f.journal().acknowledge(batch, EpisodeIncidentJournal.measure(pending));
        assertTrue(f.journal().scan(bind(f.request())).batch().isPresent(), "unresolved takes priority over an entries row");
        report.putArray("unresolved"); ObjectNode wrong = report.deepCopy(); ((ObjectNode)wrong.get("scan_observation")).put("observation_version", 99);
        Path wrongPath = temporary.resolve("SYNTHETIC-WRONG-REPORT.json"); Files.write(wrongPath, StrictJson.canonical(wrong));
        assertThrows(java.io.IOException.class, () -> f.journal().acknowledge(batch, EpisodeIncidentJournal.measure(wrongPath)));
        Path completed = temporary.resolve("SYNTHETIC-COMPLETED-REPORT.json"); Files.write(completed, StrictJson.canonical(report));
        f.journal().acknowledge(batch, EpisodeIncidentJournal.measure(completed));
        var reviewedScan = f.journal().scan(bind(f.request()));
        assertTrue(reviewedScan.batch().isEmpty(), "actual reviewed-index/report pins account for this empty pending set");
        assertEquals(1, reviewedScan.capturedIncidents()); assertEquals(0, reviewedScan.incidents());
        assertEquals(1, reviewedScan.incompleteAfter(), "source review cannot erase the missing independent after of this actual incident");
        Files.writeString(completed, "{}"); assertThrows(java.io.IOException.class, () -> f.journal().scan(bind(f.request())));
    }
    @Test void unindexedBodiesAndWrongOperationCannotPassAsSourceBoundEmptyOrLegalFallback() throws Exception {
        Fixture f = fixture(); Files.writeString(f.configured().incidentRoot().resolve("a".repeat(32) + ".before.json"), "{}");
        assertThrows(java.io.IOException.class, () -> f.journal().scan(bind(f.request())));
        ActionCommand original = command(f.request()); ActionCommand wrong = new ActionCommand(original.actionId(), original.before(), original.source(), original.sessionId(),
                new OperationKey("accept-pending-character-interaction"), original.arguments(), original.expected(), original.claims(), original.deadline());
        assertThrows(IllegalArgumentException.class, () -> f.journal().before(wrong));
    }
    @Test void blockedActualPlanPersistsBeforeWithoutAnActionDispatchOrUnknownAfter() throws Exception {
        Fixture f = fixture(); ActionCommand candidate = command(f.request());
        ObjectNode plan = (ObjectNode)StrictJson.parse(DriverJson.encode(candidate.arguments())); plan.putNull("selected_step");
        var retained = OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(plan)), "unsubmitted actual candidate");
        Path frame = temporary.resolve("synthetic-original-frame.json"); Files.writeString(frame, "{\"scope\":\"synthetic-original-frame\"}");
        ExactRef frameRef = EpisodeIncidentJournal.measure(frame);
        var ticket = f.journal().captureBlocked(f.request(), retained, frameRef);
        assertEquals(ticket, f.journal().captureBlocked(f.request(), retained, frameRef));
        JsonNode index = StrictJson.parse(Files.readAllBytes(Path.of(ticket.index().path())));
        assertTrue(index.get("action_id").isNull()); assertEquals("planning_diagnostic", index.get("capture_stage").textValue());
        assertEquals(frameRef, ExactRef.fromJson(index.get("original_frame_ref")));
        ObjectNode wrongFrameType = frameRef.toJson(); wrongFrameType.put("bytes", true);
        assertThrows(IllegalArgumentException.class, () -> ExactRef.fromJson(wrongFrameType));
        ObjectNode floatFrameBytes = frameRef.toJson(); floatFrameBytes.put("bytes", (double) frameRef.bytes());
        assertThrows(IllegalArgumentException.class, () -> ExactRef.fromJson(floatFrameBytes));
        ObjectNode missingFrameField = frameRef.toJson(); missingFrameField.remove("sha256");
        assertThrows(IllegalArgumentException.class, () -> ExactRef.fromJson(missingFrameField));
        ObjectNode extraFrameField = frameRef.toJson(); extraFrameField.put("unexpected", true);
        assertThrows(IllegalArgumentException.class, () -> ExactRef.fromJson(extraFrameField));
        JsonNode before = StrictJson.parse(Files.readAllBytes(Path.of(ticket.before().path())));
        assertFalse(before.get("dispatch_attempted").booleanValue());
        var scan = f.journal().scan(bind(f.request())); assertEquals(1, scan.diagnosticOnly()); assertEquals(0, scan.incompleteAfter());
        assertEquals(1, scan.capturedIncidents()); assertEquals(1, scan.incidents()); assertTrue(scan.originals().contains(frameRef));
        JsonNode manifest = StrictJson.parse(Files.readAllBytes(Path.of(scan.batch().orElseThrow().manifestRef().path())));
        assertTrue(manifest.path("new_incidents").get(0).get("after").isNull());
        assertFalse(Files.exists(f.configured().incidentRoot().resolve(ticket.incidentId() + ".after.json")));
        Files.writeString(frame, "{\"scope\":\"drifted-frame\"}"); assertThrows(java.io.IOException.class, () -> f.journal().scan(bind(f.request())));
    }
    @Test void unavailableNativeProjectionKeepsRawDiagnosisWithNoFabricatedSelection() throws Exception {
        Fixture f = fixture(); ObjectNode body = StrictJson.object().put("schema", "xar.unhandled-native-window-diagnostic/v1")
                .put("kind", "unhandled_event").put("current_event_instance_id", 41).putNull("event_definition_key").putNull("selection")
                .putNull("context").put("diagnostic_reason", "synthetic unavailable native channel").put("offline_followup_required", true);
        body.set("origin", org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.observation(f.request().before()));
        body.set("snapshot", StrictJson.parse(DriverJson.encode(f.request().observations().snapshot())));
        ObjectNode plan = StrictJson.object().putNull("selected_step"); plan.set("unhandled_native_window_diagnostic", body);
        var retained = OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(plan)), "actual missing-channel diagnosis");
        var ticket = f.journal().captureBlocked(f.request(), retained, f.request().source().sourceRef());
        JsonNode before = StrictJson.parse(Files.readAllBytes(Path.of(ticket.before().path())));
        assertTrue(before.get("selection").isNull()); assertTrue(before.get("event_definition_key").isNull()); assertFalse(before.get("dispatch_attempted").booleanValue());
        var scan = f.journal().scan(bind(f.request())); assertEquals(1, scan.diagnosticOnly()); assertEquals(0, scan.incompleteAfter());
        assertTrue(scan.batch().isPresent(), "Missing source identity is unresolved input, never a silently empty scan");
    }
    @Test void implementationMetadataCanChangeOrDisappearWhileOriginalObservedBasisRemainsRequired() throws Exception {
        Fixture f = fixture(); Path incidents = Files.createDirectory(temporary.resolve("observed-incidents"));
        Path scans = Files.createDirectory(temporary.resolve("observed-scans"));
        var config = new EpisodeIncidentJournal.Configuration(incidents, scans, f.configured().clock(), f.configured().io(), Optional.empty());
        Path original = temporary.resolve("synthetic-typed-frame-basis.json"); Files.writeString(original, "{\"scope\":\"synthetic-typed-frame-basis\"}");
        ExactRef basis = EpisodeIncidentJournal.measure(original);
        Path implementation = Path.of(f.request().source().sourceRef().path());
        Files.writeString(implementation, "updated worker implementation metadata");
        var journal = EpisodeIncidentJournal.initializeObserved(config, bind(f.request()), basis);
        Files.delete(implementation);
        var reopened = EpisodeIncidentJournal.openOriginal(config, journal.episodeReference());
        assertEquals(bind(f.request()), reopened.origin()); assertEquals(Optional.of(basis), reopened.originalObservationBasis());
        assertEquals(f.request().source(), reopened.origin().source());
        assertEquals(journal.episodeReference(), EpisodeIncidentJournal.open(config, bind(f.request()), journal.episodeReference()).episodeReference());
        assertTrue(reopened.scan(bind(f.request())).originals().contains(basis));
        var foreign = new Binding(f.request().before(), f.request().source(), "another-live-session");
        assertThrows(IllegalArgumentException.class, () -> EpisodeIncidentJournal.open(config, foreign, journal.episodeReference()));
        Files.writeString(original, "{}"); assertThrows(java.io.IOException.class, () -> reopened.scan(bind(f.request())));
    }
    @Test void knownReadDiagnosticFlowsThroughJournalScanReaderAndReplayWithoutInventingAnAction() throws Exception {
        Fixture f = fixture();
        ExactRef frame = syntheticOriginal("known-frame.json"), receipt = syntheticOriginal("known-receipt.json");
        var plan = diagnostic(f.request());
        var ticket = f.journal().captureBlocked(bind(f.request()), plan, frame, Optional.of(receipt));
        JsonNode index = StrictJson.parse(Files.readAllBytes(Path.of(ticket.index().path())));
        assertEquals(new IncidentReadIndex.KnownReceipt(receipt), IncidentReadIndex.decode(index));
        assertEquals("xar.episode-incident-before-index/v2", index.path("schema").textValue());
        assertTrue(index.get("action_id").isNull());
        assertFalse(index.has("failed_read_originals"));
        assertEquals(ticket, f.journal().captureBlocked(bind(f.request()), plan, frame, Optional.of(receipt)));
        var scan = f.journal().scan(bind(f.request()));
        var batch = scan.batch().orElseThrow();
        assertTrue(scan.originals().contains(receipt));
        assertEquals(1, scan.diagnosticOnly());
        assertEquals(0, scan.incompleteAfter());
        var loaded = loadOriginalScan(f, batch);
        assertTrue(loaded.externalOriginals().stream().anyMatch(value -> value.source().equals(receipt)));
        OfflineScanSource.recheck(f.configured().incidentRoot(), Optional.of(f.configured().scanRoot()), batch.manifestRef(), loaded);
        ExactRef report = completedReport(f, batch, ticket.incidentId(), "known-report.json");
        f.journal().acknowledge(batch, report);
        assertTrue(f.journal().scan(bind(f.request())).batch().isEmpty());
        ExactRef different = syntheticOriginal("different-receipt.json");
        assertThrows(IOException.class, () -> f.journal().captureBlocked(bind(f.request()), plan, frame, Optional.of(different)));
        Files.writeString(Path.of(receipt.path()), "{\"synthetic\":\"changed-receipt\"}");
        assertThrows(IOException.class, () -> f.journal().scan(bind(f.request())));
        assertThrows(IOException.class, () -> f.journal().acknowledge(batch, report));
        assertThrows(IllegalArgumentException.class, () -> OfflineScanSource.recheck(
                f.configured().incidentRoot(), Optional.of(f.configured().scanRoot()), batch.manifestRef(), loaded));
    }

    @Test void failedReadDiagnosticKeepsExplicitNullableProofAndCompleteDependenciesAcrossPhysicalConsumers() throws Exception {
        Fixture f = fixture();
        ExactRef frame = syntheticOriginal("failed-frame.json"), outcome = syntheticOriginal("failed-outcome.json");
        ExactRef prepared = syntheticOriginal("failed-request.json"), dependency = syntheticOriginal("failed-dependency.json");
        var refs = new EpisodeIncidentJournal.FailedReadReferences(outcome, prepared, Optional.empty(), List.of(dependency, prepared, dependency));
        var ticket = f.journal().captureFailedRead(bind(f.request()), diagnostic(f.request()), frame, refs);
        JsonNode index = StrictJson.parse(Files.readAllBytes(Path.of(ticket.index().path())));
        var decoded = assertInstanceOf(IncidentReadIndex.FailedQuery.class, IncidentReadIndex.decode(index));
        assertEquals("xar.episode-incident-before-index/v3", index.path("schema").textValue());
        assertEquals(Optional.empty(), decoded.observedFailure());
        assertTrue(index.path("failed_read_originals").get("observed_failure_ref").isNull());
        assertFalse(index.has("original_read_ref"));
        assertEquals(List.of(dependency, prepared, dependency), decoded.dependencies());
        assertEquals(List.of(outcome, prepared, dependency), decoded.references());
        var scan = f.journal().scan(bind(f.request()));
        var batch = scan.batch().orElseThrow();
        assertTrue(scan.originals().containsAll(decoded.references()));
        var loaded = loadOriginalScan(f, batch);
        assertTrue(loaded.externalOriginals().stream().map(OfflineScanSource.ExternalOriginal::source).toList()
                .containsAll(decoded.references()));
        OfflineScanSource.recheck(f.configured().incidentRoot(), Optional.of(f.configured().scanRoot()), batch.manifestRef(), loaded);
        ExactRef report = completedReport(f, batch, ticket.incidentId(), "failed-report.json");
        f.journal().acknowledge(batch, report);
        assertTrue(f.journal().scan(bind(f.request())).batch().isEmpty());
        Files.writeString(Path.of(dependency.path()), "{\"synthetic\":\"changed-dependency\"}");
        assertThrows(IOException.class, () -> f.journal().scan(bind(f.request())));
        assertThrows(IOException.class, () -> f.journal().acknowledge(batch, report));
        assertThrows(IllegalArgumentException.class, () -> OfflineScanSource.recheck(
                f.configured().incidentRoot(), Optional.of(f.configured().scanRoot()), batch.manifestRef(), loaded));
    }

    @Test void malformedReadIndexCannotBeRescannedAndFailedReadCannotManufactureDisplayedSelection() throws Exception {
        Fixture f = fixture();
        ExactRef frame = syntheticOriginal("malformed-frame.json"), receipt = syntheticOriginal("malformed-receipt.json");
        var ticket = f.journal().captureBlocked(bind(f.request()), diagnostic(f.request()), frame, Optional.of(receipt));
        ObjectNode index = (ObjectNode) StrictJson.parse(Files.readAllBytes(Path.of(ticket.index().path())));
        index.put("original_read_ref", true);
        Files.write(Path.of(ticket.index().path()), StrictJson.canonical(index));
        assertThrows(IOException.class, () -> f.journal().scan(bind(f.request())));
        var fallback = (ObjectNode) StrictJson.parse(DriverJson.encode(command(f.request()).arguments()));
        fallback.putNull("selected_step");
        var plan = OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(fallback)), "synthetic blocked display");
        var refs = new EpisodeIncidentJournal.FailedReadReferences(frame, receipt, Optional.empty(), List.of());
        assertThrows(IOException.class, () -> f.journal().captureFailedRead(bind(f.request()), plan, frame, refs));
    }

    /** Physical synthetic DATA references; only cut-two's real archive tests establish failed READ semantics. */
    private ExactRef syntheticOriginal(String name) throws IOException {
        Path path = temporary.resolve(name);
        Files.writeString(path, "{\"scope\":\"synthetic-read-index\",\"name\":\"" + name + "\"}");
        return EpisodeIncidentJournal.measure(path);
    }
    private static OpportunityJson.Obj diagnostic(PlanningRequest request) {
        ObjectNode body = StrictJson.object().put("schema", "xar.unhandled-native-window-diagnostic/v1")
                .put("kind", "unhandled_event").put("current_event_instance_id", 41).putNull("event_definition_key")
                .putNull("selection").putNull("context").put("diagnostic_reason", "synthetic read-index boundary")
                .put("offline_followup_required", true);
        body.set("origin", org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.observation(request.before()));
        body.set("snapshot", StrictJson.parse(DriverJson.encode(request.observations().snapshot())));
        ObjectNode plan = StrictJson.object().putNull("selected_step");
        plan.set("unhandled_native_window_diagnostic", body);
        return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(plan)), "synthetic original diagnostic");
    }
    private static OfflineScanSource.Loaded loadOriginalScan(Fixture f,
            org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest batch) throws IOException {
        return OfflineScanSource.load(f.configured().incidentRoot(), Optional.of(f.configured().scanRoot()),
                f.request().before().machineId(), batch.manifestRef(), batch.capturedRefs());
    }
    private ExactRef completedReport(Fixture f,
            org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest batch,
            String incidentId, String name) throws IOException {
        ObjectNode manifest = (ObjectNode) StrictJson.parse(Files.readAllBytes(Path.of(batch.manifestRef().path())));
        ObjectNode report = StrictJson.object().put("schema", OfflineBatchBinding.reportSchema(EpisodeIncidentJournal.requireBatchManifest(manifest)))
                .put("machine_id", f.request().before().machineId()).put("session_id", f.request().sessionId());
        report.set("manifest", batch.manifestRef().toJson());
        for (String field : List.of("scan_observation", "scan_source", "index_ref")) report.set(field, manifest.get(field));
        report.putArray("entries").addObject().put("incident_id", incidentId);
        report.putArray("already_known");
        report.putArray("unresolved");
        Path path = temporary.resolve(name);
        Files.write(path, StrictJson.canonical(report));
        return EpisodeIncidentJournal.measure(path);
    }
    private static Binding bind(PlanningRequest request) { return new Binding(request.before(), request.source(), request.sessionId()); }
    private static ActionCommand command(PlanningRequest request) {
        var identity = request.before().frame();
        var binding = new UnhandledEventFallback.FrameBinding(identity.snapshotId(), identity.revision(), identity.identity().nativeRevision(), identity.identity().dateRaw(),
                identity.episodeRunId(), BigInteger.ONE, BigInteger.valueOf(request.before().game().pid()), true, true, identity.identity().player());
        ObjectNode context = StrictJson.object().put("schema", "current-event-window-context-v1").put("event_definition_key", "SYNTHETIC.1")
                .put("current_event_instance_id", 41).put("snapshot_revision", identity.identity().nativeRevision()).put("date_raw", identity.identity().dateRaw());
        var options = List.of(new UnhandledEventFallback.Option(BigInteger.ZERO, BigInteger.ZERO, true, true, "Synthetic parser source"));
        var input = new UnhandledEventFallback.Request(new UnhandledEventFallback.Snapshot(binding,
                new UnhandledEventFallback.ActiveEvent(BigInteger.valueOf(41), BigInteger.ONE), RetainedJson.object(RetainedJson.parse(DriverJson.encode(request.observations().snapshot())))),
                new UnhandledEventFallback.Context(BigInteger.valueOf(41), identity.identity().nativeRevision(), identity.identity().dateRaw(), "SYNTHETIC.1", options,
                        RetainedJson.object(RetainedJson.parse(StrictJson.canonical(context)))), RetainedJson.object(RetainedJson.parse("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8))),
                RetainedJson.NULL, List.of("select-event-option-1"));
        var plan = UnhandledEventFallback.plan(input); assertTrue(plan.isPresent());
        OpportunityJson.Obj arguments = OpportunityJson.object(OpportunityJson.parse(UnhandledEventCodec.encode(plan)), "actual fallback producer output");
        return PlanningFixtures.command(request, new OperationKey("select-event-option-1"), arguments);
    }
}
