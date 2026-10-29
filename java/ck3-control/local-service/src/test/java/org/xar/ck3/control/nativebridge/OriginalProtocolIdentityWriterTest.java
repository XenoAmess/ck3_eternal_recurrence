package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual software source producer -> sole coordinator/writer -> physical archive -> cold lookup. No Managed qualification. */
final class OriginalProtocolIdentityWriterTest {
    @TempDir Path root;
    @Test void originalCallerIdIsDurableAndUnknownCannotResubmitOrChangeBody() throws Exception {
        var expected = new AtomicReference<ExactRef>();
        var operation = ExplicitOriginalProtocolId.Contract.PUBLIC_COUNCIL_ASSIGNMENT.operation();
        var preparation = new ActionPorts.PreparationPort() {
            @Override public void requireProtocolIdentity(ActionCommand command) {
                StrictJson.require(command.protocolIdentity() instanceof ExplicitOriginalProtocolId, "explicit original ID required by this actual software producer");
                var id = (ExplicitOriginalProtocolId) command.protocolIdentity();
                StrictJson.require(id.contract() == ExplicitOriginalProtocolId.Contract.PUBLIC_COUNCIL_ASSIGNMENT
                        && id.producerSource().equals(expected.get()), "original ID changed its installed source policy");
            }
            @Override public NativeRequest prepare(ActionCommand command) { throw new IllegalStateException("actual coordinator request ID required"); }
            @Override public NativeRequest prepare(ActionCommand command, String id) {
                requireProtocolIdentity(command); assertEquals(RequestIds.forCommand(command), id);
                return new NativeRequest(operation.value(), "fixture.original-id", new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            }
        };
        var scenario = new ActionWriterIntegrationFixture.SoftwareActionScenario(operation, "fixture.original-id",
                (command, attempt, outcome) -> new ActionPorts.Pending("actual unknown software dispatch remains unknown", List.of()),
                () -> { }, Optional.empty(), Optional.empty(), false, Optional.of(preparation));
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("caller"), true, scenario)) {
            ActionCommand base = actual.command("original-caller"); expected.set(base.source().sourceRef());
            var identity = new ExplicitOriginalProtocolId(ExplicitOriginalProtocolId.Contract.PUBLIC_COUNCIL_ASSIGNMENT, "council-user-123", expected.get());
            var command = new ActionCommand(base.actionId(), base.origin(), base.source(), base.sessionId(), base.operation(), base.arguments(), base.expectation(), base.claims(), base.deadline(), identity);
            var receiptRef = new AtomicReference<ActionReceipt>();
            assertThrows(java.io.IOException.class, () -> actual.physicalInputs().transport().withMailbox(command.deadline(), scope -> { receiptRef.set(actual.coordinator.execute(command)); return null; }));
            assertNotNull(receiptRef.get());
            var receipt = receiptRef.get();
            assertInstanceOf(ActionState.Unknown.class, receipt.state()); assertEquals(1, actual.nativeActionWrites());
            assertEquals(identity.value(), ActionTransitions.attempt(receipt.state()).orElseThrow().requestId());
            assertEquals(command, ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
            assertEquals(receipt, actual.archive.loadReceipt(actual.archive.receiptReferenceOf(receipt)));
            assertEquals(receipt, actual.reopenAndReturnExisting(command)); assertEquals(1, actual.nativeActionWrites());
            var other = new ActionCommand("different-action", command.origin(), command.source(), command.sessionId(), command.operation(), command.arguments(), command.expectation(), command.claims(), command.deadline(), identity);
            assertThrows(IllegalArgumentException.class, () -> actual.coordinator.execute(other));
            assertThrows(IllegalArgumentException.class, () -> ProtocolIdentityAdmission.requireUnique(List.of(receipt), other));
            assertEquals(1, actual.nativeActionWrites());
        }
    }
    @Test void closedIdentityRejectsEmptyAndUnknownContractsAndPreservesDerivedBytes() {
        assertThrows(IllegalArgumentException.class, () -> new ExplicitOriginalProtocolId(ExplicitOriginalProtocolId.Contract.PUBLIC_COUNCIL_ASSIGNMENT, "", new ExactRef("fixture", 1, "0".repeat(64))));
        assertThrows(IllegalArgumentException.class, () -> new ExplicitOriginalProtocolId(ExplicitOriginalProtocolId.Contract.PUBLIC_COUNCIL_ASSIGNMENT, "bad id", new ExactRef("D:/software/original-source.java", 1, "0".repeat(64))));
    }
}
