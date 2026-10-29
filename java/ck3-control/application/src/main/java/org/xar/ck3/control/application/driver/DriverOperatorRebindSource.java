package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.util.List;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;

/** Installed private Root issuer for the actual same-episode operator transition. DATA never grants a rebind. */
public interface DriverOperatorRebindSource {
    String PUBLICATION_KEY="driver_operator_rebind_source";
    /** Exact implementation closure for the installed Root source/LoadedClass roster, including the private sole producer. */
    static List<Class<?>> implementationTypes() {
        return List.of(DriverOperatorRebindSource.class,DriverOperatorRebindProjection.class,DriverOperatorRebindOriginals.class,
                DriverOperatorRebindProducer.class,DriverStateAssembler.class,DriverSemanticReadState.class,
                DriverActionHistoryCodec.class,DriverActionHistoryPublisher.class,DriverActionHistoryState.class);
    }
    List<ExactRef> sources();
    Capture current(ContinuityStorePort.Session same,DriverStateAssembler expected) throws IOException;
    /** Requires this identical live private capture, original command/ACK, independent native after and actual Window commit. */
    void requireCurrent(ContinuityStorePort.Session same,DriverStateAssembler expected,Capture identical) throws IOException;
    /** Checks the same installed private issuer after CAS; it must not require the obsolete old actor to remain current. */
    void requirePublished(ContinuityStorePort.Session same,DriverStateAssembler expected,Capture identical,
            DriverSnapshotFacts.Known actualPublished) throws IOException;
    interface Capture {
        DriverSnapshotFacts.Known actualKnown();
        OperatorPlayerSwitch.Request request();
        ActionCommand originalCommand();
        DriverObservationAssembler.FullSnapshot actualBefore();
        DriverObservationAssembler.FullSnapshot actualAfter();
        ExactRef originalFreshReadProof();
        WriterContracts.Prepared originalPrepared();
        WriterContracts.Receipt actualReceipt();
    }
}
