package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.util.Map;
import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;

/** Provider/strict request regression; actual SAVE/UNKNOWN acceptance remains mandatory. */
public final class RootStartupPlannedCheckpointActualInputsTest {
    @Test public void persistentServiceSelectsOnlyTheRealMainBridge() {
        var providers=ServiceLoader.load(RootControllerPlannedCheckpointActualTest.InputsProducer.class).stream().toList();
        assertEquals(1,providers.size());
        assertEquals(RootStartupPlannedCheckpointActualInputs.class,providers.getFirst().type());
    }

    @Test public void genericOrOtherScenarioRequestsCannotSupplyTheRequiredNativeScenario() {
        var generic=Map.of(RootStartupInputsProducer.REQUEST_ENV,"D:/ck3-state/test/startup-inputs.json",
                RootStartupInputsProducer.REQUEST_ENV+"_BYTES","17",
                RootStartupInputsProducer.REQUEST_ENV+"_SHA256","a".repeat(64));
        for(var scenario:RootControllerPlannedCheckpointActualTest.Scenario.values()) {
            var missing=assertThrows(IOException.class,()->RootStartupPlannedCheckpointActualInputs.request(scenario,generic));
            assertTrue(missing.getMessage().contains("MISSING_ACTUAL_ROOT_PLANNED_SAVE_INPUTS_NOT_RUN"));
            assertTrue(missing.getMessage().contains(scenario.name()));
        }
        var onlyConfirmed=Map.of("XAR_ROOT_CONFIRMED_PLANNED_SAVE_INPUTS_REQUEST","D:/ck3-state/test/startup-inputs.json",
                "XAR_ROOT_CONFIRMED_PLANNED_SAVE_INPUTS_REQUEST_BYTES","17",
                "XAR_ROOT_CONFIRMED_PLANNED_SAVE_INPUTS_REQUEST_SHA256","a".repeat(64));
        assertThrows(IOException.class,()->RootStartupPlannedCheckpointActualInputs.request(
                RootControllerPlannedCheckpointActualTest.Scenario.UNKNOWN_PLANNED_SAVE,onlyConfirmed));
    }
}
