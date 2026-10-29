package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.util.List;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;

/** Installed Root port for the real committed preclock capture. Capture values alone grant no publication. */
public interface DriverPreclockExpectationSource {
    List<ExactRef> sources();
    Capture current(ContinuityStorePort.Session same,DriverStateAssembler expected) throws IOException;
    /** Must reject a detached/foreign token and recheck the private issuer, live scope, source, Game and committed domain. */
    void requireCurrent(ContinuityStorePort.Session same,DriverStateAssembler expected,Capture identical) throws IOException;
    interface Capture {
        DriverSnapshotFacts.Known actualKnown();
        DriverObservationAssembler.Complete actualComplete();
        PlanningReadReceipt originalRootReceipt();
        RawJson originalRootResult();
        ExactRef canonicalDomainRef();
        ExactRef parentCommandRef();
        ExactRef clockCommandRef();
        ActionCommand originalClock();
        DomainBodies.PreparedImport originalPrepared();
        WriterContracts.Receipt actualReceipt();
    }
}
