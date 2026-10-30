package org.xar.ck3.control.wave2.military.exitcomparison;

import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;

/** Complete SDK snapshots use the shared full-material budget; result receipts remain small. */
final class DefenderExitFullSnapshotTest {
    @Test void fullSnapshotExtensionsAboveTheReceiptBudgetStillReachNoWarProjection() {
        var snapshot=StrictJson.object();snapshot.put("paused",true);snapshot.putNull("active_event");
        snapshot.putNull("pending_character_interaction");snapshot.putArray("active_wars");
        snapshot.put("sdk_extension","x".repeat(StrictJson.INPUT_MAX_BYTES+1));
        byte[] raw=FullJsonTree.encode(snapshot,FullJsonTree.MAXIMUM_BYTES);
        assertTrue(raw.length>StrictJson.INPUT_MAX_BYTES);
        assertInstanceOf(DefenderExitObservation.NotApplicable.class,DefenderExitObservationCodec.decodeAndObserve(raw));
        assertTrue(StrictJson.parse(DefenderExitObservationCodec.evaluate(raw)).isNull());
    }

    @Test void malformedFullSnapshotsAndInputsAboveTheSharedLimitRemainRejected() {
        for(byte[] raw:List.of("{\"paused\":true,\"paused\":false}".getBytes(StandardCharsets.UTF_8),
                "{} {}".getBytes(StandardCharsets.UTF_8),new byte[]{(byte)0xc3,0x28},
                new byte[FullJsonTree.MAXIMUM_BYTES+1])) {
            assertThrows(ContractViolationException.class,()->DefenderExitObservationCodec.decodeAndObserve(raw));
        }
    }
}
