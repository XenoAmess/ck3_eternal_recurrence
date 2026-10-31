package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Recorded DATA custody over an actual software-writer UNKNOWN and its original guard artifacts.
 * This deliberately reuses the old factual frame and has no query chronology or reconciliation
 * readiness. It never calls a native query, qualifies a source package or replays the mutation.
 * The Root reconciliation authority owns actual fresh observation and canonical qualification.
 */
final class NativeArchiveReconciliationReuse176Test {
    @TempDir Path root;
    private record Recorded(ActionReceipt pending, ActionState.Attempt attempt, ReconciliationIdentity identity) { }
    private static RawJson raw(String text) { return new RawJson(text.getBytes(StandardCharsets.UTF_8)); }
    private static Recorded original(ActionWriterIntegrationFixture fixture, String id) throws Exception {
        ActionReceipt pending = fixture.coordinator.execute(fixture.command(id));
        assertInstanceOf(ActionState.Unknown.class, pending.state()); assertFalse(pending.settled());
        var attempt = ActionTransitions.attempt(pending.state()).orElseThrow(); var guard = attempt.guard();
        var complete = RootGuardEvidence.loadFrame(guard, fixture.archive, new DriverFrameEvidenceLoader(new DriverObservationAssembler()));
        var basis = RootGuardEvidence.frameBasis(guard, fixture.archive);
        var driver = DriverObservationEvidenceReader.currentDriverReference(basis.driverFacts(), fixture.archive.loadMaterial(basis.driverFacts()));
        ObjectNode guardBody = (ObjectNode) StrictJson.parse(fixture.archive.loadMaterial(guard.supportingEvidence().getFirst()).bytes());
        var evidence = new ReconciliationIdentity.Evidence(guard.nativeEvidence(), guard.capabilityEvidence(), ExactRef.fromJson(guardBody.get("heartbeat")),
                basis.driverFacts(), driver, RootGuardEvidence.sourceQualification(guard, fixture.archive));
        var keptPending = fixture.archive.receiptReferenceOf(pending);
        var identity = ReconciliationIdentity.fromCanonical(pending, complete.identity(), guard.source(), guard.sessionId(),
                guard.connectionGeneration(), keptPending, driver, evidence, complete.observedAt());
        assertTrue(identity.observedAt().isBefore(attempt.submittedAt()), "old raw frame is intentionally not relabeled as a fresh sample");
        assertEquals(complete.observedAt(), identity.observedAt(), "current DATA factory preserves the actual cached publication time");
        assertEquals(pending.command().actionId(), identity.pending().actionId());
        assertEquals(keptPending, identity.pending().originalReceipt());
        return new Recorded(pending, attempt, identity);
    }
    private static PlanningReadReceipt recordedRead(ActionWriterIntegrationFixture fixture, ReconciliationIdentity identity) throws Exception {
        var operation = new OperationKey("query-ordinary-interaction-private-v1");
        var deadline = identity.observedAt().plusSeconds(25);
        var request = PlanningReadRequest.newReconciliation(identity, operation, new OpportunityJson.Obj(Map.of()), deadline);
        ExactRef marker = fixture.archive.preserveMaterial(raw("{\"recorded_data_only\":true,\"source_qualified\":false}"));
        var supports = new ArrayList<ExactRef>(); supports.add(marker); supports.addAll(identity.supportingEvidence());
        var binding = new GuardEvidence(new CommandOrigin.Reconciliation(identity), identity.source(), identity.sessionId(), identity.connectionGeneration(), operation,
                identity.nativeEvidence(), identity.capabilityEvidence(), "recorded-custody-data-only", identity.observedAt(), deadline, supports);
        var guard = new PlanningReadGuard(binding, new PlanningReadGuard.Reconciliation(), identity.bindingSha256());
        // Deliberately a historical DATA packet: absence of transport custody cannot grant freshness.
        String id = "recorded-reconciliation-data";
        byte[] packet = NativeWire.packet(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + id
                + "\",\"ok\":true,\"result\":{\"recorded_data_only\":true}}").getBytes(StandardCharsets.UTF_8));
        var decoded = assertInstanceOf(NativeWire.CommandResult.class, NativeWire.decode(packet));
        var ack = new NativeActionPort.AckReceived(id, true, decoded.result().token().map(value -> new RawJson(value.value())), new RawJson(decoded.payload().value()), packet);
        return new PlanningReadReceipt(request, "recorded-reconciliation-custody/v1", id, guard, guard, ack);
    }
    @Test void sameDriverRefReuseRejectsDamagedFileWithoutReplay() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("same-driver-damage"), true)) {
            var original = original(fixture, "same-driver-damage");
            var identity = original.identity();
            var driverRef = identity.evidence().currentOriginalDriver();
            var beforeDriverRef = identity.pending().originalBeforeDriver();
            assertEquals(driverRef, beforeDriverRef, "same FULL driver ref identity required");
            var value = recordedRead(fixture, identity);
            ExactRef kept = fixture.archive.preserveRead(value);
            PlanningReadReceipt restored = fixture.archive.loadRead(kept);
            assertEquals(value, restored);
            byte[] ledger = fixture.ledgerBytes();
            int actionWrites = fixture.nativeActionWrites();
            int readWrites = fixture.nativeReadWrites();
            Path driverPath = Path.of(driverRef.path());
            byte[] originalBytes = Files.readAllBytes(driverPath);
            byte[] damaged = "{}".getBytes(StandardCharsets.UTF_8);
            Files.write(driverPath, damaged);
            assertThrows(UncheckedIOException.class, () -> fixture.archive.preserveRead(value));
            assertThrows(UncheckedIOException.class, () -> fixture.archive.loadRead(kept));
            assertArrayEquals(damaged, Files.readAllBytes(driverPath));
            assertArrayEquals(ledger, fixture.ledgerBytes());
            assertEquals(actionWrites, fixture.nativeActionWrites());
            assertEquals(readWrites, fixture.nativeReadWrites());
            Files.write(driverPath, originalBytes);
        }
    }

    @Test void foreignDriverRefSameHashSizeRejectsOptimizationReuse() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("foreign-driver"), true)) {
            var original = original(fixture, "foreign-driver");
            var identity = original.identity(); var pending = identity.pending();
            ExactRef current = identity.evidence().currentOriginalDriver();
            assertEquals(current, pending.originalBeforeDriver());
            byte[] originalDriver = Files.readAllBytes(Path.of(current.path()));
            Path foreignPath = root.resolve("same-content-foreign-driver.json").toAbsolutePath().normalize();
            Files.write(foreignPath, originalDriver);
            ExactRef foreign = new ExactRef(foreignPath.toString(), originalDriver.length, ActionCodec.sha256(originalDriver));
            assertNotEquals(current, foreign); assertNotEquals(Path.of(current.path()).toAbsolutePath().normalize(), foreignPath);
            assertEquals(current.bytes(), foreign.bytes()); assertEquals(current.sha256(), foreign.sha256());
            var foreignPending = new ReconciliationIdentity.Pending(pending.actionId(), pending.bodySha256(), pending.requestId(),
                    pending.originalBefore(), pending.originalReceipt(), foreign);
            var foreignIdentity = new ReconciliationIdentity(identity.factual(), identity.source(), identity.sessionId(), identity.connectionGeneration(),
                    foreignPending, identity.evidence(), identity.observedAt(), identity.driverRelation(), identity.historyPoint());
            assertEquals(foreign, foreignIdentity.pending().originalBeforeDriver());
            assertEquals(current, foreignIdentity.evidence().currentOriginalDriver());
            var changedRead = recordedRead(fixture, foreignIdentity);
            byte[] ledger = fixture.ledgerBytes(); int actionWrites = fixture.nativeActionWrites(), readWrites = fixture.nativeReadWrites();
            var rejected = assertThrows(UncheckedIOException.class, () -> fixture.archive.preserveRead(changedRead));
            assertTrue(rejected.getCause().getMessage().contains("artifact reference is outside its exact content-addressed root"),
                    () -> "actual foreign locator rejection: " + rejected);
            assertArrayEquals(originalDriver, Files.readAllBytes(foreignPath));
            assertArrayEquals(originalDriver, Files.readAllBytes(Path.of(current.path())));
            assertArrayEquals(ledger, fixture.ledgerBytes());
            assertEquals(actionWrites, fixture.nativeActionWrites()); assertEquals(readWrites, fixture.nativeReadWrites());
        }
    }

    @Test void boundedFileReadObservationForReconciliationDriverReuse() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("file-read-observation"), true)) {
            var original = original(fixture, "reconciliation-file-read");
            var identity = original.identity(); var value = recordedRead(fixture, identity);
            assertEquals(identity.evidence().currentOriginalDriver(), identity.pending().originalBeforeDriver());
            ExactRef kept = fixture.archive.preserveRead(value);
            assertEquals(value, fixture.archive.loadRead(kept));
            Path driverPath = Path.of(identity.evidence().currentOriginalDriver().path()).toAbsolutePath().normalize();
            long currentThreadId = Thread.currentThread().threadId();
            byte[] ledger = fixture.ledgerBytes(); int actionWrites = fixture.nativeActionWrites(), readWrites = fixture.nativeReadWrites();
            Path evidenceDir = Path.of(System.getProperty("archive176.evidenceDir", root.toString()));
            Files.createDirectories(evidenceDir); Path recorded = evidenceDir.resolve("reconciliation-driver-read.jfr");
            try (var recording = new jdk.jfr.Recording()) {
                recording.setToDisk(true);
                recording.enable("jdk.FileRead").withThreshold(java.time.Duration.ZERO).withStackTrace();
                recording.start();
                assertEquals(value, fixture.archive.loadRead(kept));
                recording.stop(); recording.dump(recorded);
            }
            long matchingEvents = 0, positiveReads = 0, totalBytesRead = 0;
            for (var event : jdk.jfr.consumer.RecordingFile.readAllEvents(recorded)) {
                if (!event.getEventType().getName().equals("jdk.FileRead") || event.getThread() == null
                        || event.getThread().getJavaThreadId() != currentThreadId) continue;
                String path = event.getString("path");
                if (path == null || !Path.of(path).toAbsolutePath().normalize().equals(driverPath)) continue;
                var stack = event.getStackTrace();
                if (stack == null || stack.getFrames().stream().noneMatch(frame ->
                        frame.getMethod().getType().getName().equals("org.xar.ck3.control.continuity.writer.NativeOutcomeArchive")
                        && frame.getMethod().getName().equals("verifyReconciliationOriginals"))) continue;
                matchingEvents++;
                long bytes = event.getLong("bytesRead");
                if (bytes > 0) positiveReads++;
                totalBytesRead += Math.max(0, bytes);
            }
            assertTrue(matchingEvents > 0, "named current-thread Driver reads must be observed in the actual reconciliation verifier");
            assertTrue(positiveReads > 0); assertTrue(totalBytesRead >= identity.evidence().currentOriginalDriver().bytes());
            assertArrayEquals(ledger, fixture.ledgerBytes());
            assertEquals(actionWrites, fixture.nativeActionWrites()); assertEquals(readWrites, fixture.nativeReadWrites());
            System.out.printf(java.util.Locale.ROOT,
                    "ARCHIVE176_FILE_READ_COUNTS={\"matching_events\":%d,\"positive_reads\":%d,\"bytes_read\":%d}%n",
                    matchingEvents, positiveReads, totalBytesRead);
        }
    }

}
