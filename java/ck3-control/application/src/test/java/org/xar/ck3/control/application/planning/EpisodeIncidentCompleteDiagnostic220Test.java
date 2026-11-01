package org.xar.ck3.control.application.planning;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal.Binding;
import org.xar.ck3.control.application.planning.events.NativeWindowDiagnostic;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Text;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Value;

/**
 * Complete incident role over 8MiB software DATA using real public producers; no Game/private Root authority credit.
 * Test1: Large payload (8MiB) in history, full preservation, no after/action.
 * Test2: Integrity checks for wrong binding and modified originals.
 */
final class EpisodeIncidentCompleteDiagnostic220Test {
    @TempDir Path temporary;

    private record Fixture(PlanningRequest request, EpisodeIncidentJournal journal, EpisodeIncidentJournal.Configuration configured) { }

    private Fixture fixture() throws Exception {
        Path evidence = temporary.resolve("actual-source.json");
        Files.writeString(evidence, "{\"scope\":\"synthetic-source-bound-journal-test\"}");
        var base = PlanningFixtures.request(PlanningFixtures.snapshot(), List.of(), Set.of(new OperationKey("select-event-option-1")));
        var source = new G2Source(base.before().machineId(), PlanningFixtures.NOW.toString(), "SYNTHETIC-JOURNAL-TEST", EpisodeIncidentJournal.measure(evidence));
        PlanningRequest request = new PlanningRequest(base.before(), source, base.sessionId(), base.deadline(), base.observations());
        Path incidents = Files.createDirectory(temporary.resolve("incidents"));
        Path scans = Files.createDirectory(temporary.resolve("scans"));
        var configured = new EpisodeIncidentJournal.Configuration(incidents, scans, Clock.fixed(PlanningFixtures.NOW, ZoneOffset.UTC), pending -> {
            if (pending < 0 || pending > (64L << 20) + 4096) throw new java.io.IOException("finite test write cap");
        }, Optional.empty());
        var journal = EpisodeIncidentJournal.initialize(configured, bind(request));
        return new Fixture(request, journal, configured);
    }

    @Test void completeDiagnosticPreservesLargeHistoryAndNoAfter() throws Exception {
        Fixture f = fixture();
        // Build Source with large history payload
        var snapshot = f.request().observations().snapshot();
        var history = new ArrayList<Value>();
        // Add large text payload (~8MiB) to history
        String largeText = "A".repeat(8 * 1024 * 1024);
        history.add(new Text(largeText));
        // Ensure active_event has instance_id for foregroundKind detection
        var event = new Obj(Map.of("instance_id", PlanningFixtures.integer(41)));
        var snapshotWithEvent = snapshot.with("active_event", event);
        Optional<Value> context = Optional.of(new Obj(Map.of("software_context", new Text("complete-context"))));
        Optional<Obj> originalPlan = Optional.of(new Obj(Map.of("software_original_plan", new Text("complete-original-plan"))));
        var reason = "synthetic complete diagnostic test";
        var source = new NativeWindowDiagnostic.Source(f.request().before(), snapshotWithEvent, history, context, originalPlan, reason);

        // Use real producer
        var planOpt = NativeWindowDiagnostic.plan(source);
        assertTrue(planOpt.isPresent(), "Producer must return plan");
        var plan = planOpt.get();

        // Verify plan size > 1MiB (proves complete handling)
        var planBytes = DriverJson.encode(plan);
        assertTrue(planBytes.length > 1024 * 1024, "Plan must exceed 1MiB to prove complete handling");

        // Capture with public API
        Path framePath = temporary.resolve("synthetic-frame.json");
        Files.writeString(framePath, "{\"scope\":\"synthetic-frame\"}");
        var frameRef = EpisodeIncidentJournal.measure(framePath);
        var ticket = f.journal().captureBlocked(f.request(), plan, frameRef);

        // Repeat capture returns same ticket
        var repeated = f.journal().captureBlocked(f.request(), plan, frameRef);
        assertEquals(ticket, repeated, "Repeated capture must return same ticket");

        // Read before body with FullJsonTree (64MiB)
        var beforeBytes = Files.readAllBytes(Path.of(ticket.before().path()));
        var beforeNode = FullJsonTree.parse(beforeBytes, FullJsonTree.MAXIMUM_BYTES);
        var beforeObj = (ObjectNode) beforeNode;

        // Assert preservation
        assertEquals("planning_diagnostic", beforeObj.get("stage").textValue());
        assertFalse(beforeObj.get("dispatch_attempted").booleanValue());
        assertTrue(beforeObj.get("selection").isNull());

        // Verify snapshot, history, context, originalPlan, reason, origin preserved
        JsonNode diag = beforeObj;
        JsonNode originalDiagnostic = DriverJson.toNode(plan.get("unhandled_native_window_diagnostic"));
        for (var field : originalDiagnostic.properties()) {
            assertEquals(field.getValue(), diag.get(field.getKey()), "complete producer field: " + field.getKey());
        }
        assertEquals("xar.unhandled-native-window-diagnostic/v1", diag.get("schema").textValue());
        assertEquals("unhandled_event", diag.get("kind").textValue());
        assertEquals(reason, diag.get("diagnostic_reason").textValue());
        assertTrue(diag.get("offline_followup_required").booleanValue());

        // Verify snapshot preserved
        var diagSnapshot = diag.get("snapshot");
        assertTrue(diagSnapshot.isObject());
        // Verify history preserved (large text)
        var diagHistory = diag.get("retained_history");
        assertTrue(diagHistory.isArray());
        assertEquals(1, diagHistory.size());
        assertEquals(largeText, diagHistory.get(0).textValue());

        // Verify complete optional context/originalPlan values
        assertEquals(DriverJson.toNode(context.orElseThrow()), diag.get("context"));
        assertEquals(DriverJson.toNode(originalPlan.orElseThrow()), diag.get("original_plan"));

        // Verify origin
        var diagOrigin = diag.get("origin");
        assertEquals(f.request().before(), org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.decodeObservation(diagOrigin));
        assertEquals(DriverJson.toNode(snapshotWithEvent), diagSnapshot);
        assertEquals(ticket.before(), EpisodeIncidentJournal.measure(Path.of(ticket.before().path())));
        assertTrue(ticket.before().bytes() > 8L * 1024 * 1024);

        // Verify no after file
        assertFalse(Files.exists(f.configured().incidentRoot().resolve(ticket.incidentId() + ".after.json")));

        // Scan with same binding
        var scan = f.journal().scan(bind(f.request()));
        assertEquals(1, scan.diagnosticOnly());
        assertEquals(0, scan.incompleteAfter());
        assertTrue(scan.batch().isPresent());
        var batch = scan.batch().get();
        assertTrue(batch.capturedRefs().contains(ticket.before()));

        // Verify index has original_frame_ref
        var indexBytes = Files.readAllBytes(Path.of(ticket.index().path()));
        var indexNode = StrictJson.parse(indexBytes, 1024 * 1024);
        var indexObj = (ObjectNode) indexNode;
        assertEquals("planning_diagnostic", indexObj.get("capture_stage").textValue());
        assertTrue(indexObj.get("action_id").isNull());
        assertEquals(frameRef, ExactRef.fromJson(indexObj.get("original_frame_ref")));
    }

    @Test void integrityChecksForWrongBindingAndModifiedOriginals() throws Exception {
        Fixture f = fixture();
        // Build small diagnostic
        var snapshot = f.request().observations().snapshot();
        var event = new Obj(Map.of("instance_id", PlanningFixtures.integer(41)));
        var snapshotWithEvent = snapshot.with("active_event", event);
        var history = new ArrayList<Value>();
        Optional<Value> context = Optional.of(new Obj(Map.of("software_context", new Text("complete-context"))));
        Optional<Obj> originalPlan = Optional.of(new Obj(Map.of("software_original_plan", new Text("complete-original-plan"))));
        var reason = "synthetic integrity test";
        var source = new NativeWindowDiagnostic.Source(f.request().before(), snapshotWithEvent, history, context, originalPlan, reason);
        var plan = NativeWindowDiagnostic.plan(source).get();

        Path framePath = temporary.resolve("synthetic-frame.json");
        Files.writeString(framePath, "{\"scope\":\"synthetic-frame\"}");
        var frameRef = EpisodeIncidentJournal.measure(framePath);

        long beforeWrongBinding = fileCount(f.configured().incidentRoot());
        // Wrong binding session causes IllegalArgumentException
        var wrongBinding = new Binding(f.request().before(), f.request().source(), "wrong-session");
        assertThrows(IllegalArgumentException.class, () -> f.journal().captureBlocked(wrongBinding, plan, frameRef, Optional.empty()));
        assertEquals(beforeWrongBinding, fileCount(f.configured().incidentRoot()));

        // True capture
        var ticket = f.journal().captureBlocked(f.request(), plan, frameRef);

        // Modify before original
        var beforePath = Path.of(ticket.before().path());
        var beforeBytes = Files.readAllBytes(beforePath);
        var beforeNode = FullJsonTree.parse(beforeBytes, FullJsonTree.MAXIMUM_BYTES);
        var beforeObj = (ObjectNode) beforeNode;
        beforeObj.put("tampered", true);
        Files.write(beforePath, FullJsonTree.encode(beforeObj, FullJsonTree.MAXIMUM_BYTES));
        byte[] changedBefore = Files.readAllBytes(beforePath);
        long changedCount = fileCount(f.configured().incidentRoot());

        // Repeated capture/scan must throw IOException
        assertThrows(IOException.class, () -> f.journal().captureBlocked(f.request(), plan, frameRef));
        assertThrows(IOException.class, () -> f.journal().scan(bind(f.request())));
        assertArrayEquals(changedBefore, Files.readAllBytes(beforePath));
        assertEquals(changedCount, fileCount(f.configured().incidentRoot()));

        // Restore exact bytes only in this software SHA-bound fixture
        Files.write(beforePath, beforeBytes);

        // Modify frame evidence
        Files.writeString(framePath, "{\"scope\":\"drifted-frame\"}");
        assertThrows(IOException.class, () -> f.journal().captureBlocked(f.request(), plan, frameRef));
        assertThrows(IOException.class, () -> f.journal().scan(bind(f.request())));
        assertEquals("{\"scope\":\"drifted-frame\"}", Files.readString(framePath));
    }

    private static long fileCount(Path root) throws IOException {
        try (var paths = Files.list(root)) { return paths.count(); }
    }

    private static Binding bind(PlanningRequest request) {
        return new Binding(request.before(), request.source(), request.sessionId());
    }
}
