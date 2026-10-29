package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.List;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;

/** Application-facing proof replay; the installed Native adapter must re-decode both complete original reads. */
@FunctionalInterface
public interface ArmyRetreatPreflightVerifier {
    void verify(ArmyRetreatMoveRequest request, Complete actualBefore, List<PlanningReadReceipt> originalReads, ActionPorts.OutcomeArchive sameArchive);
}
