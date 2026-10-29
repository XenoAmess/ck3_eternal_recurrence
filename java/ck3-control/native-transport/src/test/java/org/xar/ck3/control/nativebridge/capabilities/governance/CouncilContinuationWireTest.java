package org.xar.ck3.control.nativebridge.capabilities.governance;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.governance.council.CouncilPrivateCodec;
import org.xar.ck3.control.nativebridge.NativeWire;
import static org.junit.jupiter.api.Assertions.*;

final class CouncilContinuationWireTest {
    private static NativeActionPort.AckReceived retained(String name) throws Exception {
        String repository = System.getProperty("xar.repository.root"); assertNotNull(repository);
        byte[] raw = Files.readAllBytes(Path.of(repository, "ck3_autonomous_player/tests/fixtures/native_12002/governance/" + name + ".json"));
        var frame = (NativeWire.CommandResult) NativeWire.decode(NativeWire.packet(raw));
        return new NativeActionPort.AckReceived(frame.requestId(), frame.nativeOk(), Optional.of(new RawJson(frame.result().token().orElseThrow().value())),
                new RawJson(frame.payload().value()), frame.packet().value());
    }
    @Test void originalFullNativeHelperAndReceiptPacketsRetainDifferentSemanticResults() throws Exception {
        var helper = CouncilContinuationPolicy.result(retained("council-private-ack"));
        var receipt = CouncilContinuationPolicy.result(retained("council-private-receipt"));
        assertEquals("assign-councillor-v1", helper.get("step").textValue()); assertEquals("query-assign-councillor-receipt-v1", receipt.get("step").textValue());
        assertEquals("assign-13", helper.get("council_assign_councillor_ack").get("action_request_id").textValue());
        assertEquals("assign-13", receipt.get("council_assign_councillor_receipt").get("action_request_id").textValue());
        assertFalse(CouncilContinuationPolicy.isPending(helper, CouncilPrivateCodec.STATUS));
    }
    @Test void changedResultTokenCannotBorrowTheGenuineOriginalPacket() throws Exception {
        var original = retained("council-private-ack"); var changed = CouncilContinuationPolicy.result(original).deepCopy(); changed.put("snapshot_revision", 999);
        var forged = new NativeActionPort.AckReceived(original.requestId(), true, Optional.of(new RawJson(StrictJson.canonical(changed))), original.originalFrame(), original.originalPacket());
        assertThrows(IllegalArgumentException.class, () -> CouncilContinuationPolicy.result(forged));
    }
    @Test void pendingHasExactlyFourFieldsAndCannotBeIdleOrBorrowAnotherStep() {
        var pending = StrictJson.object().put("private_council_transport", true).put("advertised", false).put("step", CouncilPrivateCodec.STATUS).put("status", "pending");
        assertTrue(CouncilContinuationPolicy.isPending(pending, CouncilPrivateCodec.STATUS));
        assertThrows(IllegalArgumentException.class, () -> CouncilContinuationPolicy.isPending(pending, "private-query-assign-councillor-receipt-v1"));
        pending.put("status", "idle"); assertThrows(IllegalArgumentException.class, () -> CouncilContinuationPolicy.isPending(pending, CouncilPrivateCodec.STATUS));
        pending.put("status", "pending").put("expected_revision", 13);
        assertThrows(IllegalArgumentException.class, () -> CouncilContinuationPolicy.isPending(pending, CouncilPrivateCodec.STATUS));
    }
}
