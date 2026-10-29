package org.xar.ck3.control.application.planning.campaign;

import java.io.IOException;
import java.time.Instant;
import java.util.List;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;

/**
 * The actual Readiness producer's held public DATA frame. The concrete producer implements
 * this on its privately constructed frame and rechecks its original writer callback,
 * source guard, canonical head, original pins and current packet in assertCurrent.
 * It is neither a persisted DTO nor a Ready, planning lease or action authority.
 */
public interface PublicTerminalDataContext {
    DriverObservationAssembler.FullSnapshot snapshot();
    Known driver();
    DriverStateSnapshot canonicalDriver();
    List<ActionReceipt> actions();
    java.util.Optional<ExactRef> originalSourceProof();
    ExactRef originalHello();
    ExactRef originalHeartbeat();
    ExactRef originalDriver();
    Instant validUntil();
    void assertCurrent(ContinuityStorePort.Session borrowed) throws IOException;
}
