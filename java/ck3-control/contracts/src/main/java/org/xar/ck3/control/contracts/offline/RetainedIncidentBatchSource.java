package org.xar.ck3.control.contracts.offline;

import java.io.IOException;
import java.util.List;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest;

/** Source-review DATA from existing original incident journals, independent of Ready or a terminal actor.
 * The installed producer owns fixed roots and original custody. This port cannot query Native,
 * construct a planning frame, authorize an action, or report a gameplay effect. */
@FunctionalInterface
public interface RetainedIncidentBatchSource {
    int MAX_BATCHES = 256;

    /** Called at the actual batch boundary before writer custody is released. Empty means no pending
     * source-review batch in the scanned configured originals, not an absence of events in the Game.
     * Failures remain explicit; callers keep already-captured batches and never synthesize a Ready. */
    List<BatchRequest> scan() throws IOException;
}
