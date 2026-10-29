package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual sole writer -> receipt codec -> physical archive -> cold lookup.
 * Packet/process edges are the existing software fixture; no Managed/Game qualification is minted. */
final class ActionReceiptNumericArchiveTest {
    @TempDir Path root;
    private static OpportunityJson.Obj arguments(String token) {
        return DriverJson.object(("{\"event_resolution\":{\"strategy_score\":" + token
                + ",\"integer\":0,\"positive_zero\":0.0,\"nested\":[-0.0,1.0,1.2300,1E+3,"
                + "9".repeat(120) + ",\"😀\"],\"keys\":{\"\":1,\"😀\":2}}}")
                .getBytes(StandardCharsets.UTF_8), ActionCommand.MAX_ARGUMENT_BYTES);
    }
    private static ActionCommand withArguments(ActionCommand original, OpportunityJson.Obj arguments) {
        return new ActionCommand(original.actionId(), original.origin(), original.source(), original.sessionId(),
                original.operation(), arguments, original.expectation(), original.claims(), original.deadline());
    }
    private static void requireOriginalNumbers(ActionCommand actual, OpportunityJson.Obj expected) {
        assertEquals(expected, actual.arguments());
        assertEquals(PublicDataJson.encodeTyped(expected), PublicDataJson.encodeTyped(actual.arguments()));
        assertEquals(ActionCodec.bodySha256(actual), ActionCodec.sha256(ActionCodec.encodeCommand(actual)));
    }
    @Test void actualUnknownReceiptPreservesOriginalTokensThroughPhysicalArchiveAndColdSameIdLookup() throws Exception {
        int index = 0;
        for (String token : List.of("-0.0", "0.0", "1.0", "1e10000")) {
            try (var actual = new ActionWriterIntegrationFixture(root.resolve("unknown-" + index++), true)) {
                var input = arguments(token); var command = withArguments(actual.command("numeric-original"), input);
                var receipt = actual.coordinator.execute(command);
                assertInstanceOf(ActionState.Unknown.class, receipt.state());
                assertEquals(1, actual.nativeActionWrites());
                var ref = actual.archive.receiptReferenceOf(receipt);
                assertEquals(receipt, actual.archive.loadReceipt(ref));
                requireOriginalNumbers(actual.archive.loadReceipt(ref).command(), input);
                byte[] bytes = ActionReceiptCodec.encodeReceipt(receipt, actual.archive);
                var restored = ActionReceiptCodec.decodeReceipt(bytes, actual.archive);
                assertEquals(receipt, restored); assertArrayEquals(bytes, ActionReceiptCodec.encodeReceipt(restored, actual.archive));
                assertEquals(ActionCodec.bodySha256(command), restored.bodySha256());
                var cold = actual.reopenAndReturnExisting(command);
                assertEquals(receipt, cold); requireOriginalNumbers(cold.command(), input);
                assertEquals(1, actual.nativeActionWrites(), "cold same-ID lookup cannot resubmit UNKNOWN");
                var forged = withArguments(command, arguments(token.equals("-0.0") ? "0.0" : "-0.0"));
                assertThrows(IllegalArgumentException.class, () -> actual.reopenAndReturnExisting(forged));
                assertEquals(1, actual.nativeActionWrites());
            }
        }
    }
    @Test void realCanonicalBeforeWriteRejectionAlsoRetainsDecimalsAndRejectsCommandSubtreeTampering() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("zero"), false)) {
            actual.stopAtIntentBarrier.set(4);
            var input = arguments("-0.0"); var command = withArguments(actual.command("numeric-zero"), input);
            var receipt = actual.coordinator.execute(command);
            assertInstanceOf(ActionState.RejectedBeforeDispatch.class, receipt.state());
            assertEquals(0, actual.nativeActionWrites());
            var ref = actual.archive.receiptReferenceOf(receipt);
            var restored = actual.archive.loadReceipt(ref);
            assertEquals(receipt, restored); requireOriginalNumbers(restored.command(), input);
            String original = new String(ActionReceiptCodec.encodeReceipt(restored, actual.archive), StandardCharsets.UTF_8);
            assertTrue(original.contains("\"strategy_score\":-0.0"));
            String tampered = original.replace("\"strategy_score\":-0.0", "\"strategy_score\":0.0");
            assertNotEquals(original, tampered);
            assertThrows(IllegalArgumentException.class, () -> ActionReceiptCodec.decodeReceipt(tampered.getBytes(StandardCharsets.UTF_8), actual.archive));
            assertEquals(0, actual.nativeActionWrites());
        }
    }
}
