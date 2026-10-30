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
    @Test void fullSemanticUnsettledRetainsActualAckWithoutGrantingAfterOrReplay() throws Exception {
        Fixture f = fixture();
        var ack = new org.xar.ck3.control.application.action.NativeActionPort.AckReceived("unsettled-request", false,
                Optional.empty(), new org.xar.ck3.control.application.action.RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)), new byte[]{1});
        ExactRef retained = preserveLargeUnsettled(f, new OpportunityJson.IntegerValue(BigInteger.valueOf(41)),
                new OpportunityJson.Obj(java.util.Map.of("instance_id", new OpportunityJson.IntegerValue(BigInteger.valueOf(41)))), ack);
        JsonNode row = StrictJson.parse(Files.readAllBytes(Path.of(retained.path())));
        assertTrue(row.path("original_instance_present").booleanValue());
        assertEquals(BigInteger.valueOf(41), row.path("original_instance_id").bigIntegerValue());
        assertEquals("ACK_RECEIVED", row.path("dispatch_kind").textValue());
        assertFalse(row.path("native_ok").booleanValue());
        assertFalse(row.path("independent_postcondition_verified").booleanValue());
        assertFalse(row.path("replay_allowed").booleanValue());
        assertEquals(retained, preserveLargeUnsettled(f, new OpportunityJson.IntegerValue(BigInteger.valueOf(41)),
                new OpportunityJson.Obj(java.util.Map.of("instance_id", new OpportunityJson.IntegerValue(BigInteger.valueOf(41)))), ack));
        assertFalse(Files.exists(Path.of(retained.path().replace(".unsettled.json", ".after.json"))));
        assertEquals(1, f.journal().scan(bind(f.request())).incompleteAfter());
    }

    @Test void largeSemanticAfterNullKeepsUnknownDispatchAndExplicitAbsence() throws Exception {
        Fixture f = fixture();
        var unknown = new org.xar.ck3.control.application.action.NativeActionPort.Unknown(
                "unsettled-request", "synthetic unconfirmed return", new byte[]{1}, Optional.empty());
        ExactRef retained = preserveLargeUnsettled(f, new OpportunityJson.IntegerValue(BigInteger.valueOf(41)), OpportunityJson.Nil.INSTANCE, unknown);
        JsonNode row = StrictJson.parse(Files.readAllBytes(Path.of(retained.path())));
        assertFalse(row.path("original_instance_present").booleanValue());
        assertTrue(row.path("native_ok").isNull());
        assertEquals("UNKNOWN", row.path("dispatch_kind").textValue());
        assertFalse(row.path("independent_postcondition_verified").booleanValue());
        assertFalse(row.path("replay_allowed").booleanValue());
        assertTrue(retained.bytes() < StrictJson.INPUT_MAX_BYTES, "full SEM is read but never copied into the small diagnostic body");
    }

    @Test void largeSemanticDecimalAfterInstanceIsUnknownRatherThanRoundedToTheOldId() throws Exception {
        Fixture f = fixture();
        var unknown = new org.xar.ck3.control.application.action.NativeActionPort.Unknown(
                "unsettled-request", "synthetic unconfirmed return", new byte[]{1}, Optional.empty());
        ExactRef retained = preserveLargeUnsettled(f, new OpportunityJson.IntegerValue(BigInteger.valueOf(41)),
                new OpportunityJson.Obj(java.util.Map.of("instance_id", new OpportunityJson.DecimalValue("41.0"))), unknown);
        JsonNode row = StrictJson.parse(Files.readAllBytes(Path.of(retained.path())));
        assertTrue(row.path("original_instance_present").isNull());
        assertFalse(row.path("replay_allowed").booleanValue());
    }

    @Test void largeSemanticOriginalInstanceStillRejectsDecimalBooleanStringAndNull() throws Exception {
        Fixture f = fixture();
        var unknown = new org.xar.ck3.control.application.action.NativeActionPort.Unknown(
                "unsettled-request", "synthetic unconfirmed return", new byte[]{1}, Optional.empty());
        for (OpportunityJson.Value invalid : List.of(new OpportunityJson.DecimalValue("41.0"),
                new OpportunityJson.Bool(true), new OpportunityJson.Text("41"), OpportunityJson.Nil.INSTANCE)) {
            IOException failure = assertThrows(IOException.class, () -> preserveLargeUnsettled(f, invalid, OpportunityJson.Nil.INSTANCE, unknown));
            assertEquals("original full native instance required", failure.getMessage());
        }
        try (var files = Files.list(f.configured().incidentRoot())) {
            assertTrue(files.noneMatch(path -> path.getFileName().toString().endsWith(".unsettled.json")));
        }
    }

    @Test void completeSemanticIngressStillRejectsDuplicateFieldsAndReceiptLaneStaysSmall() {
        byte[] large = ("{\"padding\":\"" + "x".repeat(70_000) + "\"}").getBytes(java.nio.charset.StandardCharsets.UTF_8);
        assertTrue(DriverJson.object(large, DriverJson.MAX_NATIVE_BYTES).get("padding") instanceof OpportunityJson.Text);
        assertThrows(IllegalArgumentException.class, () -> StrictJson.parse(large));
        byte[] duplicate = "{\"active_event\":null,\"active_event\":{}}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> DriverJson.object(duplicate, DriverJson.MAX_NATIVE_BYTES));
        byte[] trailing = "{\"active_event\":null}{}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> DriverJson.object(trailing, DriverJson.MAX_NATIVE_BYTES));
    }

    /** Synthetic full semantic DATA exercises the real incident producer, never Native custody or Game outcomes. */
    private ExactRef preserveLargeUnsettled(Fixture f, OpportunityJson.Value originalInstance, OpportunityJson.Value afterForeground,
            org.xar.ck3.control.application.action.NativeActionPort.DispatchOutcome dispatch) throws Exception {
        ActionCommand command = command(f.request());
        f.journal().before(command).orElseThrow();
        ExactRef beforeNative = syntheticOriginal("unsettled-before-native.json"), beforeFacts = syntheticOriginal("unsettled-before-facts.json");
        ExactRef afterNative = syntheticOriginal("unsettled-after-native.json"), afterFacts = syntheticOriginal("unsettled-after-facts.json");
        ExactRef originalDispatch = syntheticOriginal("unsettled-dispatch.json");
        var old = command.before(); var frame = old.frame();
        var afterFrame = new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(
                new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(frame.identity().player(),
                        frame.identity().nativeRevision().add(BigInteger.ONE), frame.identity().dateRaw()),
                "snapshot-unsettled-after", frame.revision().add(BigInteger.ONE), frame.episodeRunId());
        var afterIdentity = new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(old.machineId(), old.game(), afterFrame, old.observationVersion());
        OpportunityJson.Obj beforeSemantic = largeUnsettledSemantic(new OpportunityJson.Obj(java.util.Map.of("instance_id", originalInstance)), beforeFacts);
        OpportunityJson.Obj afterSemantic = largeUnsettledSemantic(afterForeground, afterFacts);
        assertTrue(DriverJson.encode(beforeSemantic).length > StrictJson.INPUT_MAX_BYTES);
        assertTrue(DriverJson.encode(afterSemantic).length > StrictJson.INPUT_MAX_BYTES);
        var before = new org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete(old, command.source(), command.sessionId(),
                BigInteger.ONE, beforeSemantic, beforeNative, PlanningFixtures.NOW, "a".repeat(64));
        var after = new org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete(afterIdentity, command.source(), command.sessionId(),
                BigInteger.ONE, afterSemantic, afterNative, PlanningFixtures.NOW.plusSeconds(1), "b".repeat(64));
        var guard = new org.xar.ck3.control.application.action.GuardEvidence(old, command.source(), command.sessionId(), BigInteger.ONE,
                command.operation(), beforeNative, f.request().source().sourceRef(), "synthetic-unsettled-authority", PlanningFixtures.NOW, command.deadline());
        var attempt = new org.xar.ck3.control.application.action.ActionState.Attempt("unsettled-request", PlanningFixtures.NOW, guard,
                new org.xar.ck3.control.application.action.NativeRequest(command.operation().value(), Optional.empty(),
                        new org.xar.ck3.control.application.action.RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8))));
        var pair = new org.xar.ck3.control.application.effects.NativeEffectSnapshots.Pair(before, after);
        return f.journal().observedUnsettled(command, attempt,
                new org.xar.ck3.control.application.effects.NativeEventEffects.UnsettledObservation(pair, dispatch, "synthetic full SEM unresolved"), originalDispatch);
    }

    private static OpportunityJson.Obj largeUnsettledSemantic(OpportunityJson.Value foreground, ExactRef facts) {
        return new OpportunityJson.Obj(java.util.Map.of("active_event", foreground, "padding", new OpportunityJson.Text("x".repeat(70_000)),
                "opaque_decimal", new OpportunityJson.DecimalValue("1.2500"), "opaque_boolean", new OpportunityJson.Bool(true),
                "opaque_null", OpportunityJson.Nil.INSTANCE, "java_driver_facts_evidence",
                org.xar.ck3.control.application.driver.DriverObservationEvidenceReader.reference(facts)));
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

    @Test void identicalEmptyScanWritesNoBytesAndLaterObservationStillPublishesItsOwnIndex() throws Exception {
        Fixture f=fixture();Binding original=bind(f.request());var first=f.journal().scan(original);
        Path sameRecording=temporary.resolve("same-scan.jfr");
        try(jdk.jfr.Recording recording=new jdk.jfr.Recording()) {
            recording.enable("jdk.FileWrite").withThreshold(java.time.Duration.ZERO);recording.start();
            assertEquals(first.indexRef(),f.journal().scan(original).indexRef());recording.stop();recording.dump(sameRecording);
        }
        long same=scanWrites(sameRecording,f.configured().scanRoot());
        var before=original.before();var later=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(before.machineId(),before.game(),before.frame(),before.observationVersion()+1);
        Binding next=new Binding(later,original.source(),original.sessionId());Path nextRecording=temporary.resolve("later-scan.jfr");EpisodeIncidentJournal.Scan advanced;
        try(jdk.jfr.Recording recording=new jdk.jfr.Recording()) {
            recording.enable("jdk.FileWrite").withThreshold(java.time.Duration.ZERO);recording.start();
            advanced=f.journal().scan(next);recording.stop();recording.dump(nextRecording);
        }
        long changed=scanWrites(nextRecording,f.configured().scanRoot());
        System.out.println("INCIDENT_SCAN_BYTES same="+same+" later="+changed+" index="+advanced.indexRef().bytes());
        assertEquals(0,same);assertNotEquals(first.indexRef(),advanced.indexRef());assertEquals(advanced.indexRef().bytes(),changed);
        assertEquals(0,advanced.incidents());assertEquals(0,advanced.capturedIncidents());
        assertEquals(later,org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.decodeObservation(StrictJson.parse(Files.readAllBytes(Path.of(advanced.indexRef().path()))).get("origin")));
        assertEquals(advanced.indexRef(),f.journal().scan(next).indexRef());
    }
    private static long scanWrites(Path recording,Path root)throws IOException {
        long bytes=0;try(jdk.jfr.consumer.RecordingFile events=new jdk.jfr.consumer.RecordingFile(recording)) {
            while(events.hasMoreEvents()) {var event=events.readEvent();if(event.getEventType().getName().equals("jdk.FileWrite")&&event.getLong("bytesWritten")>0&&Path.of(event.getString("path")).toAbsolutePath().normalize().startsWith(root))bytes+=event.getLong("bytesWritten");}
        }return bytes;
    }

    @Test void newCapturedEventKeepsCurrentProgressAndPublishesTheRealBatch() throws Exception {
        Fixture f=fixture();Binding actual=bind(f.request());ExactRef progress=softwareProgress(f,"progress-a"),changed=softwareProgress(f,"progress-b");
        var empty=f.journal().scan(actual,Optional.of(progress));var same=f.journal().scan(actual,Optional.of(changed));assertEquals(empty.indexRef(),same.indexRef());
        var ticket=f.journal().before(command(f.request())).orElseThrow();var captured=f.journal().scan(actual,Optional.of(changed));
        assertNotEquals(empty.indexRef(),captured.indexRef());assertEquals(1,captured.capturedIncidents());assertEquals(1,captured.incidents());
        JsonNode body=StrictJson.parse(Files.readAllBytes(Path.of(captured.indexRef().path())));assertEquals("xar.episode-incident-scan/v3",body.path("schema").textValue());assertEquals(changed,ExactRef.fromJson(body.get("scan_observation_basis")));assertTrue(captured.originals().contains(changed));
        var batch=captured.batch().orElseThrow();assertTrue(batch.capturedRefs().contains(ticket.before()));
        var loaded=loadOriginalScan(f,batch);assertTrue(loaded.externalOriginals().stream().anyMatch(original->original.source().equals(changed)));
        assertEquals(captured.indexRef(),f.journal().scan(actual,Optional.of(changed)).indexRef());
        assertNotEquals(captured.indexRef(),f.journal().scan(actual,Optional.of(progress)).indexRef(),"captured incidents still retain each actual progress source");
    }
    private ExactRef softwareProgress(Fixture f,String name)throws IOException {
        ObjectNode body=StrictJson.object().put("schema","xar.java.incident-observation-original/v1").put("session_id",f.request().sessionId());
        body.set("origin",org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.observation(f.request().before()));body.set("source",org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.source(f.request().source()));
        ExactRef material=syntheticOriginal(name+"-driver.json");body.set("native_frame",f.request().source().sourceRef().toJson());body.set("driver_facts",material.toJson());
        Path path=temporary.resolve(name+".json");Files.write(path,StrictJson.canonical(body));return EpisodeIncidentJournal.measure(path);
    }

    @Test void deferredProgressIsNeverPreservedForEmptyInventoryAndIsRequiredForCapturedEvents() throws Exception {
        Fixture f=fixture();Binding actual=bind(f.request());ExactRef progress=softwareProgress(f,"deferred");var calls=new java.util.concurrent.atomic.AtomicInteger();
        var empty=f.journal().scanWithProgress(actual,()->{calls.incrementAndGet();throw new IOException("unused progress cannot be requested");});
        assertEquals(0,calls.get());assertEquals(0,empty.capturedIncidents());assertTrue(empty.batch().isEmpty());
        f.journal().before(command(f.request())).orElseThrow();
        var captured=f.journal().scanWithProgress(actual,()->{calls.incrementAndGet();return progress;});assertEquals(1,calls.get());
        assertEquals(1,captured.capturedIncidents());assertTrue(captured.batch().isPresent());
        JsonNode body=StrictJson.parse(Files.readAllBytes(Path.of(captured.indexRef().path())));assertEquals("xar.episode-incident-scan/v3",body.path("schema").textValue());assertEquals(progress,ExactRef.fromJson(body.get("scan_observation_basis")));
        long files;try(var entries=Files.list(f.configured().scanRoot())){files=entries.count();}
        assertThrows(IOException.class,()->f.journal().scanWithProgress(actual,()->{throw new IOException("actual required progress preservation failed");}));
        try(var entries=Files.list(f.configured().scanRoot())){assertEquals(files,entries.count(),"failed progress cannot publish another scan or batch");}
        var loaded=loadOriginalScan(f,captured.batch().orElseThrow());assertTrue(loaded.externalOriginals().stream().anyMatch(value->value.source().equals(progress)));
    }


    @Test void coldV3SourceReviewAcknowledgementConsumesTheActualAnalyzerReportAndKeepsIncompleteAfter() throws Exception {
        SourceReviewFixture source=sourceReviewFixture();Fixture f=source.episode();Binding actual=bind(f.request());
        var ticket=f.journal().before(source.command()).orElseThrow();ExactRef progress=softwareProgress(f,"review-progress");
        var scan=f.journal().scanWithProgress(actual,()->progress);var batch=scan.batch().orElseThrow();
        assertEquals("xar.episode-incident-scan/v3",StrictJson.parse(Files.readAllBytes(Path.of(scan.indexRef().path()))).path("schema").textValue());
        var loaded=loadOriginalScan(f,batch);assertTrue(loaded.externalOriginals().stream().anyMatch(value->value.source().equals(progress)));
        var request=new org.xar.ck3.control.wave2.events.unhandledevent.OfflineEventBatchAnalyzer.Request(batch.batchId(),batch.manifestRef(),batch.capturedRefs());
        var produced=org.xar.ck3.control.wave2.events.unhandledevent.OfflineEventBatchAnalyzer.run(source.analysis(),request);
        JsonNode report=StrictJson.parse(Files.readAllBytes(Path.of(produced.report().path())));assertEquals(1,report.path("entries").size());assertEquals(0,report.path("unresolved").size());
        Path reviewed=f.configured().incidentRoot().resolve(ticket.incidentId()+".review-index.json");
        ObjectNode wrong=report.deepCopy();wrong.put("session_id","another-source-review-session");Path wrongPath=temporary.resolve("wrong-source-review-owner.json");Files.write(wrongPath,StrictJson.canonical(wrong));
        var cold=EpisodeIncidentJournal.openOriginal(f.configured(),f.journal().episodeReference());
        assertThrows(IOException.class,()->cold.acknowledge(batch,EpisodeIncidentJournal.measure(wrongPath)));assertFalse(Files.exists(reviewed));
        cold.acknowledge(batch,produced.report());ExactRef originalReview=EpisodeIncidentJournal.measure(reviewed);
        JsonNode accepted=StrictJson.parse(Files.readAllBytes(reviewed));assertEquals(produced.report(),ExactRef.fromJson(accepted.get("report_ref")));assertEquals(ticket.before(),ExactRef.fromJson(accepted.get("before_ref")));
        var reopened=EpisodeIncidentJournal.openOriginal(f.configured(),f.journal().episodeReference());var after=reopened.scanWithProgress(actual,()->progress);
        assertEquals(0,after.incidents());assertEquals(1,after.capturedIncidents());assertEquals(1,after.incompleteAfter());assertEquals(0,after.diagnosticOnly());assertTrue(after.batch().isEmpty());
        assertFalse(Files.exists(f.configured().incidentRoot().resolve(ticket.incidentId()+".after.json")),"source analysis must not manufacture independent gameplay after");
        reopened.acknowledge(batch,produced.report());assertEquals(originalReview,EpisodeIncidentJournal.measure(reviewed));
        OfflineScanSource.recheck(f.configured().incidentRoot(),Optional.of(f.configured().scanRoot()),batch.manifestRef(),loaded);
        Files.writeString(Path.of(produced.report().path()),"{}");assertThrows(IOException.class,()->reopened.acknowledge(batch,produced.report()));assertEquals(originalReview,EpisodeIncidentJournal.measure(reviewed));
        System.out.println("V3_ACK_REAL_ANALYZER entries=1 unresolved=0 cold_review=1 remaining=0 incomplete_after=1");
    }
    private record SourceReviewFixture(Fixture episode,ActionCommand command,org.xar.ck3.control.wave2.events.unhandledevent.OfflineEventBatchAnalyzer.Configuration analysis) { }
    private SourceReviewFixture sourceReviewFixture() throws Exception {
        ObjectNode blobs=StrictJson.object();com.fasterxml.jackson.databind.node.ArrayNode cases=com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode();
        for(String cohort:List.of("generic","council","council-source-drift","liberty","liberty-source-drift","sway","sway-source-drift","factions")) {
            String name="/unhandledevent/source-review-"+cohort+"-golden-v1.json.gz";
            try(var packed=EpisodeIncidentJournalTest.class.getResourceAsStream(name)) {
                if(packed==null)throw new IOException("original stock source-review resource required: "+name);
                try(var input=new java.util.zip.GZIPInputStream(packed)) {
                    JsonNode corpus=StrictJson.parse(input.readNBytes(1_048_577),1_048_576);assertEquals("xar.ck3.source-review-golden/v1",corpus.path("schema").textValue());
                    for(var entry:corpus.path("blobs").properties()){JsonNode old=blobs.get(entry.getKey());if(old!=null)assertEquals(old,entry.getValue());blobs.set(entry.getKey(),entry.getValue());}
                    for(JsonNode row:corpus.path("cases"))cases.add(row);
                }
            }
        }
        JsonNode row=null;for(JsonNode value:cases)if(value.path("name").asText().equals("faction_demand.0101-exact-stock")){row=value;break;}assertNotNull(row);
        Path game=Files.createDirectory(temporary.resolve("stock-game"));Class<?> rebind=Class.forName("org.xar.ck3.control.wave2.events.unhandledevent.ReviewedLetterSourceRebind");var sources=rebind.getDeclaredMethod("installedSourceHashes");sources.setAccessible(true);
        Object sourceObject=sources.invoke(null);assertInstanceOf(java.util.Map.class,sourceObject);
        for(var entry:((java.util.Map<?,?>)sourceObject).entrySet()) {
            String relative=assertInstanceOf(String.class,entry.getKey()),sha=assertInstanceOf(String.class,entry.getValue());Path path=game.resolve(relative);Files.createDirectories(path.getParent());
            byte[] encoded=java.util.Base64.getDecoder().decode(blobs.path(sha).textValue());
            try(var input=new java.util.zip.GZIPInputStream(new java.io.ByteArrayInputStream(encoded))){byte[] raw=input.readNBytes(2_097_153);assertTrue(raw.length<=2_097_152);assertEquals(sha,java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw)));Files.write(path,raw);}
        }
        ObjectNode plan=(ObjectNode)row.get("plan"),capture=(ObjectNode)plan.get("unhandled_event_fallback");
        ObjectNode input=StrictJson.object().put("schema",UnhandledEventCodec.PLAN_SCHEMA);input.set("snapshot",row.get("snapshot"));input.set("event_context",capture.get("window_context"));input.set("event_summary",plan.get("active_event"));input.set("registry_decision",capture.get("original_registry_decision"));input.set("action_steps",row.get("action_steps"));
        var proposed=UnhandledEventFallback.plan(UnhandledEventCodec.decodePlan(StrictJson.canonical(input))).orElseThrow();OpportunityJson.Obj arguments=OpportunityJson.object(OpportunityJson.parse(UnhandledEventCodec.encode(Optional.of(proposed))),"actual software fallback producer");
        JsonNode binding=StrictJson.parse(DriverJson.encode(arguments)).path("unhandled_event_fallback").path("binding");
        var nativeFrame=new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(new BigInteger(binding.path("actor_character_id").asText()),new BigInteger(binding.path("native_revision").asText()),new BigInteger(binding.path("date_raw").asText()));
        var frame=new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(nativeFrame,binding.path("snapshot_id").textValue(),new BigInteger(binding.path("revision").asText()),binding.path("episode_run_id").textValue());
        var gameIdentity=new org.xar.ck3.control.contracts.GameGeneration(binding.path("bridge_pid").intValue(),new org.xar.ck3.control.contracts.PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var before=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity("portable-source-fixture",gameIdentity,frame,1);Path original=temporary.resolve("software-frame-source.json");Files.writeString(original,"{\"scope\":\"software-source-review-owner\"}");
        var originalSource=new G2Source(before.machineId(),PlanningFixtures.NOW.toString(),"SOFTWARE-SOURCE-REVIEW",EpisodeIncidentJournal.measure(original));
        Set<OperationKey> steps=new java.util.HashSet<>();for(JsonNode step:row.path("action_steps"))steps.add(new OperationKey(step.textValue()));
        ObjectNode ordinarySnapshot=((ObjectNode)row.get("snapshot")).deepCopy();ordinarySnapshot.putArray("active_wars");ordinarySnapshot.putArray("player_armies");
        var observations=new PlanningObservation(OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(ordinarySnapshot)),"software stock snapshot with explicit empty ordinary collections"),List.of(),steps,Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        var request=new PlanningRequest(before,originalSource,"software-source-review-session",PlanningFixtures.NOW.plusSeconds(60),observations);
        Path incidents=Files.createDirectory(temporary.resolve("review-incidents")),scans=Files.createDirectory(temporary.resolve("review-scans"));
        var configured=new EpisodeIncidentJournal.Configuration(incidents,scans,Clock.fixed(PlanningFixtures.NOW,ZoneOffset.UTC),pending->{if(pending<0||pending>(1<<20))throw new IOException("finite software journal cap");},Optional.empty());
        Fixture episode=new Fixture(request,EpisodeIncidentJournal.initialize(configured,bind(request)),configured);
        JsonNode producedPlan=StrictJson.parse(DriverJson.encode(arguments));ActionCommand command=PlanningFixtures.command(request,new OperationKey(producedPlan.path("selected_step").textValue()),arguments);
        Path state=Files.createDirectory(temporary.resolve("source-state")),knowledge=Files.createDirectory(temporary.resolve("source-knowledge")),manifest=knowledge.resolve("fixed-grants.json");
        org.xar.ck3.control.wave2.events.sourcecatalog.EvidenceGrantManifestPublisher.publish(manifest,List.of());
        org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrants grants=()->{try{return org.xar.ck3.control.contracts.projection.ProjectionEvidenceCodec.decode(Files.readAllBytes(manifest));}catch(IOException failure){throw new java.io.UncheckedIOException(failure);}};
        var context=new org.xar.ck3.control.contracts.projection.EventSourceReadContext(before.machineId(),state,game,grants);
        var analysis=new org.xar.ck3.control.wave2.events.unhandledevent.OfflineEventBatchAnalyzer.Configuration(context,incidents,knowledge,manifest,Optional.of(scans));return new SourceReviewFixture(episode,command,analysis);
    }
}
