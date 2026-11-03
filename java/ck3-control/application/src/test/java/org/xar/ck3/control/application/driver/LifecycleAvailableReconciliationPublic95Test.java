package org.xar.ck3.control.application.driver;

import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.LifecyclePublicResultCodec;
import org.xar.ck3.control.wave2.governance.succession.SuccessionModel;
import org.junit.jupiter.api.Test;
import java.nio.charset.StandardCharsets;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertArrayEquals;

public final class LifecycleAvailableReconciliationPublic95Test {

    @Test
    void recognizesAvailabilityWithoutClaimingACompleteDtoAndKeepsOwnedBytes() {
        String schema = SuccessionModel.RECONCILIATION_SCHEMA;
        String json = "{\"schema\":\"" + schema
                + "\",\"status\":\"available\",\"extra\":{\"unrelated\":[null,1]}}";
        byte[] wire = json.getBytes(StandardCharsets.UTF_8);
        byte[] expected = wire.clone();
        RawJson input = new RawJson(wire);
        wire[0] = '[';
        assertTrue(LifecyclePublicResultCodec.isAvailableReconciliation(input));
        assertArrayEquals(expected, input.bytes());
        byte[] returned = input.bytes();
        returned[0] = '[';
        assertTrue(LifecyclePublicResultCodec.isAvailableReconciliation(input));
        assertArrayEquals(expected, input.bytes());
    }

    @Test
    void rejectsMissingWrongTypeOrNonAvailableFields() {
        String schema = SuccessionModel.RECONCILIATION_SCHEMA;
        String json1 = "{\"schema\":\"" + schema + "\"}";
        RawJson input1 = new RawJson(json1.getBytes(StandardCharsets.UTF_8));
        assertFalse(LifecyclePublicResultCodec.isAvailableReconciliation(input1));

        String json2 = "{\"schema\":\"" + schema + "\",\"status\":\"unavailable\"}";
        RawJson input2 = new RawJson(json2.getBytes(StandardCharsets.UTF_8));
        assertFalse(LifecyclePublicResultCodec.isAvailableReconciliation(input2));

        String json3 = "{\"schema\":\"wrong\",\"status\":\"available\"}";
        RawJson input3 = new RawJson(json3.getBytes(StandardCharsets.UTF_8));
        assertFalse(LifecyclePublicResultCodec.isAvailableReconciliation(input3));

        String json4 = "{\"schema\":123,\"status\":\"available\"}";
        RawJson input4 = new RawJson(json4.getBytes(StandardCharsets.UTF_8));
        assertFalse(LifecyclePublicResultCodec.isAvailableReconciliation(input4));

        String json5 = "{\"schema\":\"" + schema + "\",\"status\":123}";
        RawJson input5 = new RawJson(json5.getBytes(StandardCharsets.UTF_8));
        assertFalse(LifecyclePublicResultCodec.isAvailableReconciliation(input5));
    }

    @Test
    void rejectsNonObjectRootAtTheOriginalObjectBoundary() {
        String json = "[1,2,3]";
        RawJson input = new RawJson(json.getBytes(StandardCharsets.UTF_8));
        IllegalArgumentException failure = assertThrows(IllegalArgumentException.class,
                () -> LifecyclePublicResultCodec.isAvailableReconciliation(input));
        assertTrue(failure.getClass() == IllegalArgumentException.class);
        assertTrue("full JSON must be an object".equals(failure.getMessage()));
    }
}