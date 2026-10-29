package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.effects.family.FamilySendObservation;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * Physical DATA custody only. Three actual software endpoint queries provide before/write-marker/
 * after chronology. The middle READ ACK is deliberately a DATA ordering marker, never a native
 * family send. Recorded reconciliation metadata receives no Root or native-domain authority.
 * No source-shaped family packet, fake domain callback, canonical send completion or Game is used.
 */
final class NativeArchiveFamilySendTest {
    @TempDir Path root;
    private record Recorded(ActionReceipt receipt, ExactRef kept, FamilySendObservation observation,
            ExactRef beforeRead, ExactRef afterRead) { }
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    private static PlanningReadReceipt actualRead(ActionWriterIntegrationFixture fixture) throws Exception {
        fixture.ready(); PlanningReadReceipt value = fixture.lastNestedRead.get();
        value.original().custody().orElseThrow().verify(value); return value;
    }
    private static ObjectNode body(ActionWriterIntegrationFixture fixture, ExactRef ref) {
        return (ObjectNode) StrictJson.parse(fixture.archive.loadMaterial(ref).bytes());
    }
    private static ObjectNode data(ObjectNode receipt) {
        return (ObjectNode) receipt.path("state").path("settlement").path("observation");
    }
    private static ExactRef metadata(ActionWriterIntegrationFixture fixture, ObjectNode value) {
        return fixture.archive.preserveMaterial(new RawJson(StrictJson.canonical(value)));
    }
    private static ActionReceipt replace(Recorded value, FamilySendObservation observation) {
        ActionState.Settled old = (ActionState.Settled) value.receipt().state();
        return new ActionReceipt(value.receipt().version(), value.receipt().sequence(), value.receipt().command(), value.receipt().bodySha256(),
                new ActionState.Settled(old.attempt(), old.dispatch(), new ActionState.FamilySendConfirmed(observation)));
    }
    private static FamilySendObservation preparation(FamilySendObservation value, List<ExactRef> refs) {
        return new FamilySendObservation(value.profile(), value.actionId(), value.commandBodySha256(), value.originalRequestId(),
                value.originalDispatchRef(), value.preparedRequestRef(), value.beforeFrame(), value.afterFrame(), value.before(), value.after(),
                value.source(), value.sessionId(), value.beforeStorage(), value.afterStorage(), refs, value.nativePendingFullId(), value.definitionStableHash(), value.actual());
    }
    private static Recorded recorded(ActionWriterIntegrationFixture fixture, FamilySendObservation.Profile profile) throws Exception {
        PlanningReadReceipt before = actualRead(fixture), marker = actualRead(fixture), sampled = actualRead(fixture);
        var guard = marker.before().binding(); var frame = guard.observed();
        assertEquals(frame, before.request().before()); assertEquals(frame, sampled.request().before());
        var values = FamilySendObservation.sendOnlyValues(profile, 0xFE000001L, 0x81000002L, 0);
        var command = new ActionCommand("family-send-recorded-" + profile, frame, guard.source(), guard.sessionId(), guard.operation(),
                new OpportunityJson.Obj(Map.of()), new ProposalLifecycle.ExpectedPostcondition(1, frame, guard.source(), profile.observerSchema(), values),
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), marker.request().deadline());
        ExactRef beforeRef = fixture.archive.readReferenceOf(before);
        ExactRef preparationMarker = fixture.archive.preserveMaterial(raw("{\"recorded_custody_marker\":true,\"native_preparation_qualified\":false}"));
        var sent = NativeWire.decodeExecuteRequest(marker.original().outbound().orElseThrow().originalPacket());
        var prepared = new NativeRequest(sent.step(), Optional.empty(), new RawJson(sent.normalizedAdditionalFields().value()), List.of(beforeRef, preparationMarker));
        var attempt = new ActionState.Attempt(marker.requestId(), marker.original().custody().orElseThrow().writeEntered().observedAt(), guard, prepared);
        var pending = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command),
                new ActionState.Unknown(Optional.of(attempt), Optional.of(marker.original()), "read-marker DATA; no native send or canonical membership", List.of()));
        ExactRef pendingRef = fixture.archive.preserveReceipt(pending);
        var afterGuard = sampled.before().binding(); var afterBasis = RootGuardEvidence.frameBasis(afterGuard, fixture.archive);
        var driver = DriverObservationEvidenceReader.currentDriverReference(afterBasis.driverFacts(), fixture.archive.loadMaterial(afterBasis.driverFacts()));
        ObjectNode originalGuard = body(fixture, afterGuard.supportingEvidence().getFirst());
        var evidence = new ReconciliationIdentity.Evidence(afterGuard.nativeEvidence(), afterGuard.capabilityEvidence(),
                ExactRef.fromJson(originalGuard.get("heartbeat")), afterBasis.driverFacts(), driver, RootGuardEvidence.sourceQualification(afterGuard, fixture.archive));
        // Recorded DATA retains the old SEM publication time. Actual query custody carries order.
        // This constructor intentionally does not call or impersonate Root.fromCanonical qualification.
        var identity = new ReconciliationIdentity(afterGuard.observed(), afterGuard.source(), afterGuard.sessionId(), afterGuard.connectionGeneration(),
                new ReconciliationIdentity.Pending(command.actionId(), pending.bodySha256(), attempt.requestId(), command.before(), pendingRef, driver), evidence, afterGuard.observedAt());
        var request = PlanningReadRequest.newReconciliation(identity, sampled.request().operation(), sampled.request().arguments(), sampled.request().deadline());
        var recordedBinding = new GuardEvidence(new CommandOrigin.Reconciliation(identity), identity.source(), identity.sessionId(), identity.connectionGeneration(),
                request.operation(), identity.nativeEvidence(), identity.capabilityEvidence(), "recorded-family-custody-no-Root-qualification", identity.observedAt(),
                afterGuard.validUntil(), identity.supportingEvidence());
        var recordedGuard = new PlanningReadGuard(recordedBinding, new PlanningReadGuard.Reconciliation(), identity.bindingSha256());
        var after = new PlanningReadReceipt(request, sampled.contractId(), sampled.requestId(), recordedGuard, recordedGuard, sampled.original());
        ExactRef afterRef = fixture.archive.preserveRead(after);
        var observation = new FamilySendObservation(profile, command.actionId(), pending.bodySha256(), attempt.requestId(), fixture.archive.referenceOf(marker.original()),
                fixture.archive.requestReferenceOf(prepared), RootGuardEvidence.frameBasis(guard, fixture.archive), afterBasis, frame, afterGuard.observed(),
                guard.source(), guard.sessionId(), before, after, prepared.preparationEvidence(), 0, 0xFFFF_FFFFL, values);
        observation.validate(command, attempt, marker.original(), fixture.archive);
        var receipt = new ActionReceipt(1, 1, command, pending.bodySha256(), new ActionState.Settled(attempt, marker.original(), new ActionState.FamilySendConfirmed(observation)));
        ExactRef kept = fixture.archive.preserveReceipt(receipt); return new Recorded(receipt, kept, observation, beforeRef, afterRef);
    }

    @Test void bothProfilesKeepExactSameSemOriginalsAcrossColdArchiveWithoutRelationDayOrSaveCredit() throws Exception {
        for (var profile : FamilySendObservation.Profile.values()) {
            try (var fixture = new ActionWriterIntegrationFixture(root.resolve(profile.name()), false)) {
                byte[] ledger = fixture.ledgerBytes(); Recorded value = recorded(fixture, profile);
                var cold = new NativeOutcomeArchive(fixture.archive.artifactStore(), fixture.writer);
                ActionReceipt restored = cold.loadReceipt(value.kept()); assertEquals(value.receipt(), restored);
                assertEquals(value.kept(), cold.receiptReferenceOf(restored)); assertEquals(ActionReceipt.Outcome.SEND_CONFIRMED, restored.outcome());
                assertTrue(restored.settled()); assertFalse(restored.visibleGameplay()); assertFalse(restored.eligibleAdvance());
                assertEquals(value.observation().before(), value.observation().after());
                assertEquals(value.observation().beforeFrame().nativeFrame(), value.observation().afterFrame().nativeFrame());
                assertEquals(value.observation().beforeStorage(), cold.loadRead(value.beforeRead()));
                assertEquals(value.observation().afterStorage(), cold.loadRead(value.afterRead()));
                assertEquals(ActionReceiptCodec.FAMILY_SEND_SCHEMA, body(fixture, value.kept()).path("schema").textValue());
                var state = (ActionState.Settled) restored.state();
                assertThrows(IllegalArgumentException.class, () -> ActionEffects.validate(restored.command(), state.attempt(), state.settlement()));
                assertEquals(0, fixture.nativeActionWrites(), "the marker is an actual software READ, never a family submission");
                assertArrayEquals(ledger, fixture.ledgerBytes(), "archival DATA cannot create canonical family completion");
            }
        }
    }

    @Test void receiptVersionsAndStrictFamilyWireRefuseMissingUnknownWrongTypeAndRelationCredit() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("strict"), false)) {
            Recorded value = recorded(fixture, FamilySendObservation.Profile.MARRIAGE); byte[] ledger = fixture.ledgerBytes();
            List<ObjectNode> refused = new ArrayList<>();
            for (String schema : List.of(ActionReceiptCodec.SCHEMA, ActionReceiptCodec.EVOLVED_SCHEMA, ActionReceiptCodec.PROVENANCE_SCHEMA))
                refused.add(body(fixture, value.kept()).put("schema", schema));
            ObjectNode missing = body(fixture, value.kept()); data(missing).remove("after_storage_ref"); refused.add(missing);
            ObjectNode extra = body(fixture, value.kept()); data(extra).put("relationship_completed", true); refused.add(extra);
            ObjectNode bool = body(fixture, value.kept()); data(bool).put("native_pending_full_id", true); refused.add(bool);
            ObjectNode floating = body(fixture, value.kept()); data(floating).put("native_pending_full_id", 0.0); refused.add(floating);
            ObjectNode text = body(fixture, value.kept()); data(text).put("native_pending_full_id", "0"); refused.add(text);
            ObjectNode omitted = body(fixture, value.kept()); data(omitted).putArray("complete_preparation"); refused.add(omitted);
            ObjectNode duplicate = body(fixture, value.kept()); data(duplicate).withArray("complete_preparation").add(value.beforeRead().toJson()); refused.add(duplicate);
            ObjectNode relation = body(fixture, value.kept());
            for (var row : data(relation).withArray("actual")) if (row.path("field").asText().equals("marriage_relation_verified")) ((ObjectNode) row).put("value", true);
            refused.add(relation);
            for (ObjectNode row : refused) {
                ExactRef bad = metadata(fixture, row);
                assertThrows(RuntimeException.class, () -> fixture.archive.loadReceipt(bad), row.toString());
            }
            assertEquals(value.receipt(), fixture.archive.loadReceipt(value.kept()));
            assertEquals(0, fixture.nativeActionWrites()); assertArrayEquals(ledger, fixture.ledgerBytes());
        }
    }

    @Test void changedCommandAttemptPreparationAndMissingReadMetadataRefuseOnProducerAndReferencePaths() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("binding"), false)) {
            Recorded value = recorded(fixture, FamilySendObservation.Profile.GUARDIAN); var before = value.receipt();
            var changedCommand = new ActionCommand(before.command().actionId() + "-other", before.command().origin(), before.command().source(), before.command().sessionId(),
                    before.command().operation(), before.command().arguments(), before.command().expectation(), before.command().claims(), before.command().deadline());
            var changed = new ActionReceipt(1, 1, changedCommand, ActionCodec.bodySha256(changedCommand), before.state());
            assertThrows(IllegalArgumentException.class, () -> fixture.archive.preserveReceipt(changed));
            assertThrows(IllegalArgumentException.class, () -> fixture.archive.receiptReferenceOf(changed));
            var wrongPreparation = replace(value, preparation(value.observation(), List.of(fixture.archive.preserveMaterial(raw("{\"unrelated\":true}")))));
            assertThrows(IllegalArgumentException.class, () -> fixture.archive.preserveReceipt(wrongPreparation));
            assertThrows(IllegalArgumentException.class, () -> fixture.archive.receiptReferenceOf(wrongPreparation));
            byte[] bytes = Files.readAllBytes(Path.of(value.afterRead().path())); Files.delete(Path.of(value.afterRead().path()));
            assertThrows(UncheckedIOException.class, () -> fixture.archive.preserveReceipt(before));
            assertThrows(UncheckedIOException.class, () -> fixture.archive.receiptReferenceOf(before));
            assertThrows(UncheckedIOException.class, () -> fixture.archive.loadReceipt(value.kept()));
            assertFalse(Files.exists(Path.of(value.afterRead().path())), "DATA must not repair a missing original query metadata object");
            assertTrue(bytes.length > 0); assertEquals(0, fixture.nativeActionWrites());
        }
    }

    @Test void missingOrChangedReferenceClosureRefusesColdReadWithoutRepairOrReplay() throws Exception {
        for (String role : List.of("before-read", "after-read", "prepared", "dispatch", "native", "driver", "preparation")) {
            try (var fixture = new ActionWriterIntegrationFixture(root.resolve(role), false)) {
                Recorded value = recorded(fixture, FamilySendObservation.Profile.MARRIAGE); var observation = value.observation();
                ExactRef ref = switch (role) {
                    case "before-read" -> value.beforeRead(); case "after-read" -> value.afterRead();
                    case "prepared" -> observation.preparedRequestRef(); case "dispatch" -> observation.originalDispatchRef();
                    case "native" -> observation.afterFrame().nativeFrame(); case "driver" -> observation.afterFrame().driverFacts();
                    case "preparation" -> observation.completePreparation().getLast();
                    default -> throw new AssertionError(role);
                };
                byte[] ledger = fixture.ledgerBytes(); byte[] damaged = "{}".getBytes(StandardCharsets.UTF_8);
                Files.write(Path.of(ref.path()), damaged);
                assertThrows(UncheckedIOException.class, () -> fixture.archive.loadReceipt(value.kept()), role);
                assertArrayEquals(damaged, Files.readAllBytes(Path.of(ref.path())), "no archive repair");
                assertArrayEquals(ledger, fixture.ledgerBytes()); assertEquals(0, fixture.nativeActionWrites());
            }
        }
    }

    @Test void sameBytesAtForeignReadLocatorCannotReplaceOwnedOriginal() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("locator"), false)) {
            Recorded value = recorded(fixture, FamilySendObservation.Profile.MARRIAGE); byte[] ledger = fixture.ledgerBytes();
            Path copied = fixture.root.resolve("copied-original-read.json"); Files.copy(Path.of(value.afterRead().path()), copied);
            ExactRef alias = new ExactRef(copied.toAbsolutePath().normalize().toString(), value.afterRead().bytes(), value.afterRead().sha256());
            ObjectNode changed = body(fixture, value.kept()); data(changed).set("after_storage_ref", alias.toJson());
            ExactRef changedRef = metadata(fixture, changed);
            assertThrows(UncheckedIOException.class, () -> fixture.archive.loadReceipt(changedRef));
            assertEquals(value.receipt(), fixture.archive.loadReceipt(value.kept()));
            assertArrayEquals(ledger, fixture.ledgerBytes()); assertEquals(0, fixture.nativeActionWrites());
        }
    }
}
