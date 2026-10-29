package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.offline.OfflineBatchBinding;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisWire;
import org.xar.ck3.control.contracts.projection.ProjectionProtocolException;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistry;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistryCodec;
import org.xar.ck3.control.wave2.events.unhandledevent.OfflineEventReviewGrantPublisher;
import org.xar.ck3.control.wave2.events.unhandledevent.OfflineInteractionSourceAnalyzer;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;

/** Real journal -> host -> original source analyzer -> registry -> completion -> next scan, on synthetic frames. */
final class OfflineInteractionHostIntegrationTest {
    @TempDir Path temporary;
    @Test void actualInteractionBeforeOnlyIsSourceReviewedAndAcknowledgedWithoutInventingItsAfter() throws Exception {
        var f = new OfflineInteractionCorpus(temporary.resolve("complete"));
        var ticket = f.journal.before(f.command).orElseThrow(); var batch = f.journal.scan(f.binding).batch().orElseThrow();
        JsonNode output = OfflineEventAnalysisWire.parseMetadataObject(f.host(true).batch(batch)); JsonNode report = output.get("report");
        assertEquals(OfflineBatchBinding.REPORT_V2, report.path("schema").textValue()); assertFalse(report.has("completed_control_sequence"));
        assertEquals(1, report.path("entries").size()); assertEquals(ticket.incidentId(), report.path("entries").get(0).path("incident_id").textValue());
        assertEquals(0, report.path("unresolved").size()); assertFalse(report.path("material_effects_verified").booleanValue());
        var scan = f.journal.scan(f.binding); assertTrue(scan.batch().isEmpty()); assertEquals(1, scan.capturedIncidents()); assertEquals(1, scan.incompleteAfter());
        assertFalse(Files.exists(f.incidents.resolve(ticket.incidentId() + ".after.json")), "source knowledge cannot produce a native after");
        var before = RetainedJson.object(RetainedJson.parse(Files.readAllBytes(Path.of(ticket.before().path()))));
        var known = assertInstanceOf(InteractionRegistry.Known.class, OfflineInteractionSourceAnalyzer.reviewed(before, TrustedEventSourceContext.open(f.sources)));
        assertFalse(known.review().materialEffectsVerified()); assertFalse(known.review().replayAllowed());
        assertTrue(known.review().facts().onAccept().contains("on_accept")); assertTrue(known.review().facts().onDecline().contains("on_decline"));
        var publisher = new OfflineEventReviewGrantPublisher.Configuration(f.sources, f.incidents, f.knowledge, f.grants, Optional.of(f.scans));
        assertEquals(0, OfflineEventReviewGrantPublisher.publish(publisher, Path.of(output.path("report_ref").path("path").textValue())).added());
        byte[] replay = f.host(true).batch(batch); assertTrue(OfflineEventAnalysisWire.parseMetadataObject(replay).path("idempotent").booleanValue());
        assertEquals(report, OfflineEventAnalysisWire.parseMetadataObject(replay).get("report"));
    }
    @Test void actualV2RequiresTheRootCompletionPortBeforeAnyAnalysisPublication() throws Exception {
        var f = new OfflineInteractionCorpus(temporary.resolve("no-root-completion")); f.journal.before(f.command);
        var batch = f.journal.scan(f.binding).batch().orElseThrow(); var host = f.host(false);
        assertThrows(ProjectionProtocolException.class, () -> host.batch(batch));
        assertFalse(Files.exists(f.knowledge)); assertFalse(Files.exists(f.state.resolve("evidence/interaction-source-registry")));
        assertTrue(f.journal.scan(f.binding).batch().isPresent());
    }
    @Test void ambiguousOriginalDefinitionStaysUnresolvedAndDoesNotAcknowledgeTheIncident() throws Exception {
        var f = new OfflineInteractionCorpus(temporary.resolve("ambiguous")); f.journal.before(f.command);
        Files.copy(f.game.resolve(OfflineInteractionCorpus.SOURCE), f.game.resolve("common/character_interactions/duplicate.txt"));
        var batch = f.journal.scan(f.binding).batch().orElseThrow(); var output = OfflineEventAnalysisWire.parseMetadataObject(f.host(true).batch(batch));
        assertEquals(0, output.path("report").path("entries").size()); assertEquals(1, output.path("report").path("unresolved").size());
        assertTrue(f.journal.scan(f.binding).batch().isPresent()); assertEquals(1, f.journal.scan(f.binding).incompleteAfter());
        assertFalse(Files.exists(f.state.resolve("evidence/interaction-source-registry")));
    }
    @Test void exactScanMachineSourceBodyAndCapturedInventoryAreRequiredBeforeWrites() throws Exception {
        var f = new OfflineInteractionCorpus(temporary.resolve("source-drift")); var ticket = f.journal.before(f.command).orElseThrow();
        var batch = f.journal.scan(f.binding).batch().orElseThrow(); var host = f.host(true);
        assertThrows(IllegalArgumentException.class, () -> host.batch(new BatchRequest(batch.batchId(), batch.manifestRef(), List.of())));
        ObjectNode manifest = (ObjectNode)StrictJson.parse(Files.readAllBytes(Path.of(batch.manifestRef().path())), 1 << 20);
        ObjectNode wrong = manifest.deepCopy(); ((ObjectNode)wrong.get("scan_observation")).put("machine_id", "other-machine");
        byte[] raw = StrictJson.canonical(wrong, 1 << 20); Path changed = f.scans.resolve("incidents-" + OfflineInteractionCorpus.sha(raw) + ".batch.json"); Files.write(changed, raw);
        assertThrows(IllegalArgumentException.class, () -> host.batch(new BatchRequest("wrong-machine", OfflineInteractionCorpus.pin(changed), batch.capturedRefs())));
        Files.writeString(Path.of(ticket.before().path()), "{}"); assertThrows(IllegalArgumentException.class, () -> host.batch(batch));
        assertFalse(Files.exists(f.knowledge));
    }
    @Test void v2NestedWireRejectsWrongTypesUnknownFieldsAndFabricatedControlSequence() throws Exception {
        var f = new OfflineInteractionCorpus(temporary.resolve("wire")); f.journal.before(f.command); var batch = f.journal.scan(f.binding).batch().orElseThrow();
        ObjectNode valid = OfflineEventAnalysisWire.parseMetadataObject(f.host(true).batch(batch));
        for (String field : List.of("index_ref", "scan_source", "scan_observation", "session_id", "manifest")) {
            ObjectNode malformed = valid.deepCopy(); ((ObjectNode)malformed.get("report")).putNull(field);
            assertThrows(IllegalArgumentException.class, () -> OfflineEventAnalysisWire.validateBatchResult(OfflineInteractionCorpus.bytes(malformed), batch.batchId()), field);
        }
        ObjectNode fake = valid.deepCopy(); ((ObjectNode)fake.get("report")).put("completed_control_sequence", 1);
        assertThrows(IllegalArgumentException.class, () -> OfflineEventAnalysisWire.validateBatchResult(OfflineInteractionCorpus.bytes(fake), batch.batchId()));
        ObjectNode numericIdentity = valid.deepCopy(); ((ObjectNode)numericIdentity.path("report").path("scan_observation").path("frame")).put("native_revision", 7);
        assertThrows(IllegalArgumentException.class, () -> OfflineEventAnalysisWire.validateBatchResult(OfflineInteractionCorpus.bytes(numericIdentity), batch.batchId()));
        assertArrayEquals(OfflineInteractionCorpus.bytes(valid), OfflineEventAnalysisWire.validateBatchResult(OfflineInteractionCorpus.bytes(valid), batch.batchId()));
    }
}
