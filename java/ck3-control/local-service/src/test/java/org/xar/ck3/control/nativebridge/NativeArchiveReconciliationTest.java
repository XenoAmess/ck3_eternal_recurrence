package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;
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
final class NativeArchiveReconciliationTest {
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
        var identity = new ReconciliationIdentity(complete.identity(), guard.source(), guard.sessionId(), guard.connectionGeneration(),
                new ReconciliationIdentity.Pending(pending.command().actionId(), pending.bodySha256(), attempt.requestId(), pending.command().before(), keptPending, driver),
                evidence, complete.observedAt());
        assertTrue(identity.observedAt().isBefore(attempt.submittedAt()), "old raw frame is intentionally not relabeled as a fresh sample");
        assertThrows(IllegalArgumentException.class, () -> ReconciliationIdentity.fromCanonical(pending, identity.factual(), identity.source(), identity.sessionId(),
                identity.connectionGeneration(), keptPending, driver, evidence, identity.observedAt()));
        return new Recorded(pending, attempt, identity);
    }
    private static ReconciliationIdentity evidence(ReconciliationIdentity original, ReconciliationIdentity.Evidence replacement) {
        return new ReconciliationIdentity(original.factual(), original.source(), original.sessionId(), original.connectionGeneration(), original.pending(), replacement, original.observedAt());
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
    private static ActionReceipt recordedEffect(ActionWriterIntegrationFixture fixture, Recorded original, PlanningReadReceipt recordedRead) {
        var identity = original.identity(); var evidence = identity.evidence();
        ExactRef material = fixture.archive.preserveMaterial(raw("{\"recorded_data_only\":true}"));
        var basis = StrictJson.object().put("schema", "xar.java.native-effect-original-basis/v3")
                .put("command_body_sha256", original.pending().bodySha256()).put("request_id", original.attempt().requestId());
        var frame = StrictJson.object(); frame.set("native_frame", evidence.actualNativePacket().toJson()); frame.set("driver_facts", evidence.observationManifest().toJson());
        basis.set("before", frame); basis.set("after", frame.deepCopy()); basis.set("compatible_material", material.toJson());
        basis.putArray("independent_reads"); basis.putArray("supporting_materials");
        basis.set("reconciliation_guard", CommandOriginCodec.guard(recordedRead.before().binding()));
        ExactRef basisRef = fixture.archive.preserveMaterial(new RawJson(StrictJson.canonical(basis)));
        // A strict recorded row exercises the sole typed extractor. It is not a live proof producer,
        // canonical terminal publication or domain acceptance of an applied effect.
        var effect = new ActionState.EffectObservation(identity.factual(), identity.source(), identity.sessionId(), "recorded-custody-data-only/v1", List.of(),
                new ObservationProvenance.Push(identity.factual().frame().snapshotId(), identity.factual().frame().identity().nativeRevision(), evidence.actualNativePacket()),
                identity.observedAt(), evidence.actualNativePacket(), List.of(basisRef));
        return new ActionReceipt(1, original.pending().sequence(), original.pending().command(), original.pending().bodySha256(),
                new ActionState.Settled(original.attempt(), ActionTransitions.dispatch(original.pending().state()).orElseThrow(), new ActionState.Applied(effect)));
    }
    @Test void physicalColdRoundtripKeepsSixTypedRolesAndPendingOriginalsWithoutGrantingFreshness() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("roles"), true)) {
            var original = original(fixture, "reconciliation-custody"); var value = recordedRead(fixture, original.identity());
            byte[] ledger = fixture.ledgerBytes(); int actionWrites = fixture.nativeActionWrites(), readWrites = fixture.nativeReadWrites();
            ExactRef kept = fixture.writer.locked(session -> fixture.archive.inSession(session, archive -> archive.preserveRead(value)));
            PlanningReadReceipt restored = fixture.archive.loadRead(kept); assertEquals(value, restored);
            assertEquals(original.identity(), restored.request().origin().requireReconciliation());
            assertEquals(original.identity().evidence().originals(), restored.request().origin().requireReconciliation().evidence().originals());
            assertTrue(restored.original().custody().isEmpty()); assertTrue(restored.original().outbound().isEmpty());
            assertThrows(IllegalStateException.class, restored.request()::before);
            assertThrows(IllegalStateException.class, restored.before()::playerAlive);
            // The original heartbeat really is framed binary. It cannot be parsed as RawJson.
            assertThrows(IllegalArgumentException.class, () -> fixture.archive.loadMaterial(original.identity().evidence().originalHeartbeat()));
            assertEquals(original.pending(), fixture.archive.loadReceipt(original.identity().pending().originalReceipt()));
            var effectData = recordedEffect(fixture, original, value);
            assertEquals(effectData, fixture.archive.loadReceipt(fixture.archive.preserveReceipt(effectData)));
            assertFalse(effectData.visibleGameplay()); assertFalse(effectData.eligibleAdvance());
            var detached = (ActionState.Settled) effectData.state();
            assertThrows(IllegalArgumentException.class, () -> ActionEffects.validate(effectData.command(), detached.attempt(), detached.dispatch(), detached.settlement()));
            assertEquals(ActionReceipt.Outcome.UNRESOLVED, original.pending().outcome());
            assertFalse(original.pending().visibleGameplay()); assertFalse(original.pending().eligibleAdvance());
            assertArrayEquals(ledger, fixture.ledgerBytes()); assertEquals(actionWrites, fixture.nativeActionWrites()); assertEquals(readWrites, fixture.nativeReadWrites());
        }
    }
    @Test void wrongPacketRolesChangedFactualSnapshotAndMissingPendingOriginalRefuseWithoutRepairOrReplay() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("reject"), true)) {
            var original = original(fixture, "reconciliation-reject"); var identity = original.identity(); var roles = identity.evidence();
            byte[] ledger = fixture.ledgerBytes(); int actionWrites = fixture.nativeActionWrites(), readWrites = fixture.nativeReadWrites();
            ExactRef notAPacket = fixture.archive.preserveMaterial(raw("{\"not_a_native_heartbeat\":true}"));
            var badHeartbeat = new ReconciliationIdentity.Evidence(roles.actualNativePacket(), roles.actualHello(), notAPacket,
                    roles.observationManifest(), roles.currentOriginalDriver(), roles.completeSourceQualification());
            PlanningReadReceipt wrongRole = recordedRead(fixture, evidence(identity, badHeartbeat));
            assertThrows(UncheckedIOException.class, () -> fixture.archive.preserveRead(wrongRole));
            byte[] actual = fixture.archive.loadNativeFrame(roles.actualNativePacket());
            ObjectNode outer = (ObjectNode) StrictJson.parse(Arrays.copyOfRange(actual, 4, actual.length)); outer.put("snapshot_id", "different-recorded-snapshot");
            byte[] changed = NativeWire.packet(StrictJson.canonical(outer));
            ExactRef changedPacket = fixture.writer.locked(session -> fixture.archive.preserveArtifact(session, changed, 65536));
            var wrongFrame = new ReconciliationIdentity.Evidence(changedPacket, roles.actualHello(), roles.originalHeartbeat(),
                    roles.observationManifest(), roles.currentOriginalDriver(), roles.completeSourceQualification());
            PlanningReadReceipt changedRead = recordedRead(fixture, evidence(identity, wrongFrame));
            assertThrows(UncheckedIOException.class, () -> fixture.archive.preserveRead(changedRead));
            var data = recordedRead(fixture, identity); ExactRef kept = fixture.archive.preserveRead(data);
            ExactRef keptEffect = fixture.archive.preserveReceipt(recordedEffect(fixture, original, data));
            Path pendingPath = Path.of(identity.pending().originalReceipt().path()); byte[] damaged = "{}".getBytes(StandardCharsets.UTF_8); Files.write(pendingPath, damaged);
            assertThrows(UncheckedIOException.class, () -> fixture.archive.loadRead(kept));
            assertThrows(UncheckedIOException.class, () -> fixture.archive.loadReceipt(keptEffect));
            assertArrayEquals(damaged, Files.readAllBytes(pendingPath)); assertArrayEquals(ledger, fixture.ledgerBytes());
            assertEquals(actionWrites, fixture.nativeActionWrites()); assertEquals(readWrites, fixture.nativeReadWrites());
        }
    }
    @Test void longLivedProducerBorrowsOnlyItsActualHeldWriterSessionAndLeakedOrForeignScopesRefuse() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("producer-scope"), true);
                var foreign = new ActionWriterIntegrationFixture(root.resolve("foreign-scope"), false)) {
            var original = original(fixture, "held-producer"); var identity = original.identity();
            ExactRef manifestRef = identity.evidence().observationManifest(); var manifest = fixture.archive.loadMaterial(manifestRef);
            var actual = DriverObservationEvidenceReader.nativeFrame(manifestRef, manifest, fixture.archive.loadNativeFrame(identity.nativeEvidence()));
            RawJson material = raw("{\"long_lived_producer\":true}");
            java.util.function.Function<NativeObservationPort.ObservedFrame, ExactRef> originalProducer = fixture.archive::preserveNativeFrame;
            var leaked = new java.util.concurrent.atomic.AtomicReference<ActionPorts.OutcomeArchive>(); byte[] ledger = fixture.ledgerBytes();
            ExactRef kept = fixture.writer.locked(session -> {
                assertSame(session, fixture.writer.activeSession().orElseThrow());
                assertEquals(identity.nativeEvidence(), originalProducer.apply(actual));
                ExactRef value = fixture.archive.preserveMaterial(material);
                assertEquals(value, fixture.archive.materialReferenceOf(material));
                assertEquals(value, fixture.archive.materialReference(value.sha256(), value.bytes()));
                leaked.set(fixture.archive.withSession(session)); return value;
            });
            assertEquals(material, fixture.archive.loadMaterial(kept));
            assertThrows(UncheckedIOException.class, () -> leaked.get().preserveMaterial(material));
            foreign.writer.locked(session -> {
                assertThrows(UncheckedIOException.class, () -> fixture.archive.preserveMaterial(material));
                assertThrows(UncheckedIOException.class, () -> fixture.archive.materialReference(kept.sha256(), kept.bytes())); return null;
            });
            assertArrayEquals(ledger, fixture.ledgerBytes());
        }
    }
}
