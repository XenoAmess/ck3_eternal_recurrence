package org.xar.ck3.control.application.lifecycle;

import java.io.IOException;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;

/** The actual private pending source must qualify each finite child; token DATA alone grants none. */
public interface NaturalSuccessionContinuationSource extends NaturalSuccessionPreparation {
    /** Historical canonical parent frame only, issued by the actual retained private source; no current-read or child authority. */
    LifecycleObservationPort.Snapshot requireRetainedOriginalFrame(ActionCommand originalParent,
            ContinuityStorePort.Session same,PendingToken identical)throws IOException;
    /** Mandatory actual Root/M3 private retained-finalization qualification; recorded DATA alone grants nothing. */
    void requireCommittedPendingEpisode(org.xar.ck3.control.application.action.ActionReceipt actualParent,
            ContinuityStorePort.Session same,LifecycleComposites.RecordedPendingEpisode identical)throws IOException;
    void requireChild(ActionCommand originalParent, ContinuityStorePort.Session same,
            PendingToken identical, ActionCommand actualChild) throws IOException;
}
