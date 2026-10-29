package org.xar.ck3.control.wave2.military.commander;

import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

final class ObservedMilitaryConsumerBoundaryTest {
    @Test void newProbeUsesTheRealStrictRequestBoundaryAndPreservesRawTokens() {
        String prefix = "{\"schema\":\"xar.ck3.holy-hire-request-input.v1\",\"holy_order_id\":0,\"expected_revision\":";
        for (String token : new String[] {"true", "1.0", "1e0", "\"1\"", "-1", "null"}) {
            byte[] raw = (prefix + token + "}").getBytes(StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> ProbeCompiledObservedMilitaryConsumers.execute("hire_request", raw), token);
        }
        byte[] raw = (prefix + "1208925819614629174706176}").getBytes(StandardCharsets.UTF_8);
        var result = StrictJson.parse(ProbeCompiledObservedMilitaryConsumers.execute("hire_request", raw));
        assertEquals("1208925819614629174706176", result.path("expected_revision").bigIntegerValue().toString());
        assertTrue(result.path("holy_order_id").isIntegralNumber());
    }
    @Test void unknownProbeOperationsAndMissingFieldsNeverBecomeExpectedRejections() {
        byte[] input = "{}".getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> ProbeCompiledObservedMilitaryConsumers.execute("hire_unrecognized", input));
        assertThrows(IllegalArgumentException.class, () -> ProbeCompiledObservedMilitaryConsumers.execute("hire_request", input));
    }
}
