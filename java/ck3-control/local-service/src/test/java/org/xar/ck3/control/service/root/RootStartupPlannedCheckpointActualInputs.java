package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.service.OrdinarySessionHost;
import org.xar.ck3.control.service.mcp.PublicMcpHost;

/** Enters the original production Main for each genuinely configured native scenario.
 * The request selects startup data; the existing actual test verifies what really occurred. */
public final class RootStartupPlannedCheckpointActualInputs implements RootControllerPlannedCheckpointActualTest.InputsProducer {
    @Override public void withActualInputs(RootControllerPlannedCheckpointActualTest.Scenario scenario,
            RootStartupInputsProducer.Work work)throws Exception {
        Objects.requireNonNull(work);
        var original=request(scenario,System.getenv());
        RootStartupInputsProducer.execute(original,new OrdinarySessionHost(),new PublicMcpHost(),work);
    }

    static RootStartupInputsProducer.Request request(RootControllerPlannedCheckpointActualTest.Scenario scenario,
            Map<String,String> environment)throws IOException {
        Objects.requireNonNull(scenario);Objects.requireNonNull(environment);
        String prefix=switch(scenario) {
            case CONFIRMED_PLANNED_SAVE->"XAR_ROOT_CONFIRMED_PLANNED_SAVE_INPUTS_REQUEST";
            case UNKNOWN_PLANNED_SAVE->"XAR_ROOT_UNKNOWN_PLANNED_SAVE_INPUTS_REQUEST";
        };
        String path=environment.get(prefix),bytes=environment.get(prefix+"_BYTES"),sha=environment.get(prefix+"_SHA256");
        if(path==null||bytes==null||sha==null)
            throw new IOException("MISSING_ACTUAL_ROOT_PLANNED_SAVE_INPUTS_NOT_RUN: exact request path/bytes/SHA required for "+scenario);
        return RootStartupInputsProducer.fromEnvironment(Map.of(
                RootStartupInputsProducer.REQUEST_ENV,path,
                RootStartupInputsProducer.REQUEST_ENV+"_BYTES",bytes,
                RootStartupInputsProducer.REQUEST_ENV+"_SHA256",sha));
    }
}
