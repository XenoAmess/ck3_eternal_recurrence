package org.xar.ck3.control.wave2.military.projection;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.projection.*;

final class ArmyProjectionPortsTest {
    private static ProjectionResult dispatch(ProjectionOperation operation, String raw) {
        var call = new ProjectionCall(new ProjectionCall.Identity("army-port-test", operation),
                ProjectionJson.object(raw.getBytes(StandardCharsets.UTF_8), ProjectionJson.MAX_BYTES));
        return new ProjectionDispatcher(ArmyProjectionPorts.registrations()).dispatch(ProjectionWire.encodeCall(call));
    }

    @Test void nullableFamilyAndFullOriginalInnerLimitSurviveTheExactWrapper() {
        var absent = assertInstanceOf(ProjectionResult.Succeeded.class,
                dispatch(ProjectionOperation.MILITARY_ARMY_DAILY_QUEUE_INPUTS, "{\"value\":null}"));
        assertArrayEquals("null".getBytes(StandardCharsets.UTF_8), absent.result().bytes());
        String prefix = "{\"status\":\"unavailable\",\"ready\":false,\"unavailable_reason\":\"";
        // Duplicate IDs are independent queue occurrences. They carry the byte load without violating text limits.
        String ids = "[" + "0,".repeat(20_000) + "0]";
        String suffix = "\",\"manager_army_id_list_2a5a8\":" + ids + ",\"initial_army_resolution_rows\":null}";
        String reason = "x".repeat(65_536 - prefix.length() - suffix.length());
        assertTrue(reason.length() <= 32_768);
        String inner = prefix + reason + suffix;
        assertEquals(65_536, inner.length());
        var maximum = assertInstanceOf(ProjectionResult.Succeeded.class,
                dispatch(ProjectionOperation.MILITARY_ARMY_DAILY_QUEUE_INPUTS, "{\"value\":" + inner + "}"));
        assertEquals(65_536, maximum.result().bytes().length);
        var overflow = assertInstanceOf(ProjectionResult.Rejected.class,
                dispatch(ProjectionOperation.MILITARY_ARMY_DAILY_QUEUE_INPUTS, "{\"value\": " + inner + "}"));
        assertEquals(ProjectionError.Code.PAYLOAD_TOO_LARGE, overflow.error().code());
    }

    @Test void floatingIntegerAndWrongWrapperReachTheActualDomainDecoder() {
        String family = "{\"status\":\"unavailable\",\"ready\":false,\"unavailable_reason\":\"unknown\","
                + "\"manager_army_id_list_2a5a8\":[1.0],\"initial_army_resolution_rows\":null}";
        for (String raw : new String[] { "{}", "{\"value\":null,\"extra\":false}", "{\"value\":" + family + "}" }) {
            var result = assertInstanceOf(ProjectionResult.Rejected.class,
                    dispatch(ProjectionOperation.MILITARY_ARMY_DAILY_QUEUE_INPUTS, raw));
            assertEquals(ProjectionError.Code.INVALID_PAYLOAD, result.error().code());
        }
    }

    @Test void legacyOversizedReasonStillFailsTheUnchangedProductionStringGuard() {
        String prefix = "{\"status\":\"unavailable\",\"ready\":false,\"unavailable_reason\":\"";
        String suffix = "\",\"manager_army_id_list_2a5a8\":null,\"initial_army_resolution_rows\":null}";
        String inner = prefix + "x".repeat(65_536 - prefix.length() - suffix.length()) + suffix;
        var result = assertInstanceOf(ProjectionResult.Rejected.class,
                dispatch(ProjectionOperation.MILITARY_ARMY_DAILY_QUEUE_INPUTS, "{\"value\":" + inner + "}"));
        assertEquals(ProjectionError.Code.INVALID_RESULT, result.error().code());
    }
}
