package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Strict historical fact reader consumes the same typed field contract; DATA grants no business qualification. */
final class ExternalSendFactCodecTest {
    @Test void existingFactReaderRoundtripsSendWithoutAppliedOrTimelineCredit() {
        var receipt = FamilySendCoreContractTest.vector().receipt(); var command = receipt.command();
        assertEquals(ActionReceipt.Outcome.SEND_CONFIRMED, receipt.outcome());
        var fact = new ProposalLifecycle.ExternalFact(command.actionId(), receipt.bodySha256(), command.before(),
                ProposalLifecycle.ExternalState.SEND_CONFIRMED, ProposalLifecycle.UnknownScope.GLOBAL, Domain.marriage,
                command.claims(), command.source().sourceRef());
        var encoded = ActionFactCodec.toJson(fact); var decoded = ActionFactCodec.fromJson(encoded);
        assertEquals(fact, decoded); assertEquals("SEND_CONFIRMED", encoded.get("state").textValue());
        assertFalse(decoded.unresolved()); assertNotEquals(ProposalLifecycle.ExternalState.APPLIED_CONFIRMED, decoded.state());
        assertTrue(receipt.settled()); assertTrue(receipt.applied().isEmpty());
        assertFalse(receipt.visibleGameplay()); assertFalse(receipt.eligibleAdvance());
        var historical = encoded.deepCopy(); historical.remove("schema");
        assertThrows(IllegalArgumentException.class, () -> ActionFactCodec.fromJson(historical));
        assertThrows(IllegalArgumentException.class, () -> ActionFactCodec.fromHistoricalV1Json(historical));
        historical.put("state", "UNKNOWN");
        assertEquals(ProposalLifecycle.ExternalState.UNKNOWN, ActionFactCodec.fromHistoricalV1Json(historical).state());
        encoded.put("state", "send_confirmed");
        assertThrows(IllegalArgumentException.class, () -> ActionFactCodec.fromJson(encoded));
    }
}
