package org.xar.ck3.control.contracts.offline;

import java.io.IOException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest;

/** The actual incident journal acknowledges only the original batch's source-reviewed report. */
@FunctionalInterface
public interface BatchReviewCompletionPort {
    void complete(BatchRequest original, ExactRef actualSourceReviewReport) throws IOException;
}
