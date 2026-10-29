package org.xar.ck3.control.application.planning.military;

import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.ReadContract;

/** Root verifies its private canonical witness and replays the exact original contract before returning a model. */
public interface OriginalMilitaryReadPort extends PlanningReadPort {
    <T> T replayOriginal(ReadContract<T> currentContract,PlanningReadRequest currentRequest,PlanningReadResult.Known<T> actual);
}
