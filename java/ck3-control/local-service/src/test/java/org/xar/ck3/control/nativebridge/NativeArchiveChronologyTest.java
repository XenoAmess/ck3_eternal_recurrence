package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual transport endpoint operations against controlled software packets, then physical archive.
 * A read ACK used as an ordering marker is DATA; it proves no Game command effect or runtime qualification.
 */
final class NativeArchiveChronologyTest {
    @TempDir Path root;
    private static PlanningReadReceipt read(ActionWriterIntegrationFixture fixture) throws Exception {
        fixture.ready(); var value = fixture.lastNestedRead.get();
        assertNotNull(value); assertTrue(value.original().custody().isPresent(), "selected actual transport must produce custody at endpoint operations");
        value.original().custody().orElseThrow().verify(value); return value;
    }
    private static NativeActionPort.AckReceived custody(NativeActionPort.AckReceived value, NativeRequestChronology replacement) {
        return new NativeActionPort.AckReceived(value.requestId(), value.nativeOk(), value.originalResultToken(), value.originalFrame(),
                value.originalPacket(), value.outbound(), Optional.of(replacement));
    }
    private static PlanningReadReceipt original(PlanningReadReceipt value, NativeActionPort.AckReceived replacement) {
        return new PlanningReadReceipt(value.request(), value.contractId(), value.requestId(), value.before(), value.after(), replacement);
    }
    private static ObjectNode row(ActionWriterIntegrationFixture fixture, ExactRef value) {
        return (ObjectNode) StrictJson.parse(fixture.archive.loadMaterial(value).bytes());
    }
    private static ExactRef metadata(ActionWriterIntegrationFixture fixture, ObjectNode value) {
        return fixture.archive.preserveMaterial(new RawJson(StrictJson.canonical(value)));
    }
    @Test void actualEndpointProducerAndSameWriterArchiveKeepOriginalOrderTimesAndPacketPinsOnColdReplay() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("roundtrip"), false)) {
            var value = read(fixture); var actual = value.original().custody().orElseThrow(); byte[] ledger = fixture.ledgerBytes();
            ExactRef kept = fixture.writer.locked(session -> fixture.archive.inSession(session, archive -> archive.preserveRead(value)));
            var restored = fixture.archive.loadRead(kept); assertEquals(value, restored);
            var cold = restored.original().custody().orElseThrow(); assertEquals(actual, cold); cold.verify(restored);
            ExactRef dispatch = fixture.archive.referenceOf(restored.original()); var wire = row(fixture, dispatch);
            assertEquals("xar.native-dispatch-archive/v3", wire.path("schema").textValue());
            assertEquals(NativeRequestChronologyCodec.encode(actual), wire.get("custody"));
            assertEquals(actual.originalRequest().sha256(), ExactRef.fromJson(wire.get("outbound_packet_ref")).sha256());
            assertEquals(actual.originalResponse().sha256(), ExactRef.fromJson(wire.get("packet_ref")).sha256());
            assertEquals(actual, fixture.archive.loadRead(kept).original().custody().orElseThrow());
            assertArrayEquals(ledger, fixture.ledgerBytes()); assertEquals(0, fixture.nativeActionWrites());
        }
    }
    @Test void realQueryOrderCanBeFreshOnTheSameRawSnapshotAndEarlierQueryCannotBecomeFresh() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("sample-order"), false)) {
            var before = read(fixture); var marker = read(fixture); var after = read(fixture);
            var submitted = marker.original().custody().orElseThrow();
            var sent = NativeWire.decodeExecuteRequest(marker.original().outbound().orElseThrow().originalPacket());
            var attempt = new ActionState.Attempt(marker.requestId(), submitted.writeEntered().observedAt(), marker.before().binding(),
                    new NativeRequest(sent.step(), Optional.empty(), new RawJson(sent.normalizedAdditionalFields().value())));
            assertEquals(before.before().binding().observed().frame().snapshotId(), after.before().binding().observed().frame().snapshotId());
            NativeRequestChronology.requireBeforeSubmission(before, attempt, marker.original());
            NativeRequestChronology.requireSampledAfter(after, attempt, marker.original());
            assertThrows(IllegalArgumentException.class, () -> NativeRequestChronology.requireSampledAfter(before, attempt, marker.original()));
            var cold = fixture.archive.loadRead(fixture.archive.preserveRead(after));
            NativeRequestChronology.requireSampledAfter(cold, attempt, marker.original());
            var originalEpoch = after.original().custody().orElseThrow();
            var otherEpoch = new NativeRequestChronology(originalEpoch.session(), java.util.UUID.randomUUID(), originalEpoch.requestId(),
                    originalEpoch.originalRequest(), originalEpoch.originalResponse(), originalEpoch.writeEntered(), originalEpoch.writeCompleted(), originalEpoch.responseReceived());
            var resetCounterDomain = fixture.archive.loadRead(fixture.archive.preserveRead(original(after, custody(after.original(), otherEpoch))));
            assertThrows(IllegalArgumentException.class, () -> NativeRequestChronology.requireSampledAfter(resetCounterDomain, attempt, marker.original()));
            var old = new NativeActionPort.AckReceived(after.requestId(), after.original().nativeOk(), after.original().originalResultToken(),
                    after.original().originalFrame(), after.original().originalPacket(), after.original().outbound());
            var historical = fixture.archive.loadRead(fixture.archive.preserveRead(original(after, old)));
            assertTrue(historical.original().custody().isEmpty());
            assertThrows(IllegalArgumentException.class, () -> NativeRequestChronology.requireSampledAfter(historical, attempt, marker.original()));
            assertEquals(0, fixture.nativeActionWrites());
        }
    }
    @Test void coldPacketDigestAndHeldSessionMismatchRefuseBeforeSamplingAuthority() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("mismatch"), false)) {
            var value = read(fixture); var actual = value.original().custody().orElseThrow();
            var changedPacket = new NativeRequestChronology(actual.session(), actual.custodyEpoch(), actual.requestId(),
                    new NativeRequestChronology.PacketIdentity(actual.originalRequest().bytes(), "0".repeat(64)), actual.originalResponse(),
                    actual.writeEntered(), actual.writeCompleted(), actual.responseReceived());
            assertThrows(IllegalArgumentException.class, () -> fixture.archive.preserve(custody(value.original(), changedPacket)));
            ExactRef kept = fixture.archive.preserveRead(value), dispatch = fixture.archive.referenceOf(value.original());
            var changedRow = row(fixture, dispatch); changedRow.set("custody", NativeRequestChronologyCodec.encode(changedPacket));
            ExactRef invalidPacket = metadata(fixture, changedRow);
            assertThrows(IllegalArgumentException.class, () -> fixture.archive.load(invalidPacket));
            var otherSession = new NativeObservationPort.TransportSession(actual.session().machineId(), actual.session().game(),
                    actual.session().connectionGeneration().add(BigInteger.ONE), actual.session().sessionId() + "-foreign");
            var changedSession = new NativeRequestChronology(otherSession, actual.custodyEpoch(), actual.requestId(), actual.originalRequest(), actual.originalResponse(),
                    actual.writeEntered(), actual.writeCompleted(), actual.responseReceived());
            var crossSession = custody(value.original(), changedSession);
            assertThrows(IllegalArgumentException.class, () -> fixture.archive.preserveRead(original(value, crossSession)));
            // A standalone dispatch is data; the typed read consumer must still bind its real guards.
            ExactRef crossDispatch = fixture.archive.preserve(crossSession); var readRow = row(fixture, kept);
            readRow.set("original_ref", crossDispatch.toJson()); ExactRef invalidSession = metadata(fixture, readRow);
            assertThrows(IllegalArgumentException.class, () -> fixture.archive.loadRead(invalidSession));
            assertEquals(value, fixture.archive.loadRead(kept));
        }
    }
    @Test void versionsRequireExactCustodyFieldsAndMutationReceiptKeepsItsOriginalGuardScope() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("versions"), false)) {
            var value = read(fixture); var ack = value.original(); ExactRef dispatch = fixture.archive.preserve(ack);
            var missing = row(fixture, dispatch); missing.remove("custody"); ExactRef missingRef = metadata(fixture, missing);
            assertThrows(IllegalArgumentException.class, () -> fixture.archive.load(missingRef));
            var aliased = row(fixture, dispatch); aliased.put("schema", "xar.native-dispatch-archive/v2"); ExactRef aliasRef = metadata(fixture, aliased);
            assertThrows(IllegalArgumentException.class, () -> fixture.archive.load(aliasRef));
            var actual = ack.custody().orElseThrow(); var sent = NativeWire.decodeExecuteRequest(ack.outbound().orElseThrow().originalPacket());
            var guard = value.before().binding();
            var expected = new ProposalLifecycle.ExpectedPostcondition(1, value.request().before(), value.request().source(), "controlled-query-marker-data/v1",
                    List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("controlled.read_marker"), true)));
            var command = new ActionCommand("query-marker-data", value.request().before(), value.request().source(), value.request().sessionId(), guard.operation(),
                    new OpportunityJson.Obj(Map.of()), expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), value.request().deadline());
            var prepared = new NativeRequest(sent.step(), Optional.empty(), new RawJson(sent.normalizedAdditionalFields().value()));
            var attempt = new ActionState.Attempt(ack.requestId(), actual.writeEntered().observedAt(), guard, prepared);
            var data = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.AckReceived(attempt, ack));
            assertEquals(data, fixture.archive.loadReceipt(fixture.archive.preserveReceipt(data)));
            assertEquals(ActionReceipt.Outcome.UNRESOLVED, data.outcome()); assertFalse(data.visibleGameplay()); assertFalse(data.eligibleAdvance());
            var wrongGuard = new GuardEvidence(guard.origin(), guard.source(), guard.sessionId() + "-wrong", guard.connectionGeneration(), guard.operation(),
                    guard.nativeEvidence(), guard.capabilityEvidence(), guard.authorityId(), guard.observedAt(), guard.validUntil(), guard.supportingEvidence());
            var crossed = new ActionReceipt(1, 1, command, data.bodySha256(), new ActionState.AckReceived(new ActionState.Attempt(ack.requestId(), attempt.submittedAt(), wrongGuard, prepared), ack));
            assertThrows(IllegalArgumentException.class, () -> fixture.archive.preserveReceipt(crossed));
        }
    }
}
