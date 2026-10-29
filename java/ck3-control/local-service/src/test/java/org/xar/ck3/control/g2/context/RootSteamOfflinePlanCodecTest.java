package org.xar.ck3.control.g2.context;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.RootNativePlanJson;
import org.xar.ck3.control.contracts.StrictJson;

final class RootSteamOfflinePlanCodecTest {
    @TempDir Path temporary;
    private RootSteamOfflineGate.Plan data() {
        return new RootSteamOfflineGate.Plan("software-only", new ControlBuild.FileRef(temporary.resolve("steam.exe").toString(), 1, "a".repeat(64)),
                temporary.resolve("evidence"), Instant.parse("2030-01-01T00:00:00Z"), Duration.ofSeconds(10), Duration.ofSeconds(2));
    }
    @Test void actualRootMapperAndStrictPlanConsumerRoundTripWithoutAProducerOrProcess() throws Exception {
        var plan = data(); byte[] raw = RootNativePlanJson.mapper().writeValueAsBytes(plan);
        assertEquals(plan, RootNativePlanJson.mapper().readValue(raw, RootSteamOfflineGate.Plan.class));
        assertEquals(plan, RootSteamOfflineGate.Plan.fromJson(StrictJson.parse(raw)));
        assertFalse(new String(raw, java.nio.charset.StandardCharsets.UTF_8).contains("python"));
    }
    @Test void oldPythonPlanFieldsMissingFieldsNullAndCoercedTimeoutsReject() {
        for (String mutation : List.of("python", "missing_executable", "null_executable", "float_timeout", "bool_timeout", "old_schema", "alias")) {
            ObjectNode wire = data().toJson();
            switch (mutation) {
                case "python" -> wire.put("pythonExecutable", "old-python");
                case "missing_executable" -> wire.remove("steam_executable");
                case "null_executable" -> wire.putNull("steam_executable");
                case "float_timeout" -> wire.put("cef_timeout_millis", 2000.0);
                case "bool_timeout" -> wire.put("observation_timeout_millis", true);
                case "old_schema" -> wire.put("schema", "xar.python-steam-gate-plan/v1");
                case "alias" -> wire.put("commandTimeout", "PT10S"); default -> throw new IllegalStateException(mutation);
            }
            assertThrows(IllegalArgumentException.class, () -> RootSteamOfflineGate.Plan.fromJson(wire), mutation);
        }
    }
    @Test void zeroAndOutOfRangeObservationBudgetsNeverReachNativeObservation() {
        for (long milliseconds : List.of(0L, 99L, 10001L)) {
            ObjectNode wire = data().toJson(); wire.put("cef_timeout_millis", milliseconds);
            assertThrows(IllegalArgumentException.class, () -> RootSteamOfflineGate.Plan.fromJson(wire));
        }
    }
}
