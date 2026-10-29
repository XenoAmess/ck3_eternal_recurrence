package org.xar.ck3.control.admission.cold;

import java.util.List;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** The original eight historical source references; replay supplies no live credit. */
public record HistoricalSemanticReplay(
        ExactRef receiptRef, ExactRef helperRef, ExactRef semanticRef, ExactRef launchRef,
        ExactRef originalColdRef, ExactRef originalQueueRef, ExactRef scoreRef, ExactRef anchorRef,
        long historicalSequence, String checkAfterAstSha256) {
    public HistoricalSemanticReplay {
        StrictJson.require(receiptRef != null && helperRef != null && semanticRef != null
                        && launchRef != null && originalColdRef != null && originalQueueRef != null
                        && scoreRef != null && anchorRef != null, "all eight historical source references required");
        StrictJson.safe(historicalSequence, 1);
        StrictJson.require(checkAfterAstSha256 != null && checkAfterAstSha256.matches("[0-9a-f]{64}"),
                "exact method digest");
    }

    public List<ExactRef> references() {
        return List.of(receiptRef, helperRef, semanticRef, launchRef, originalColdRef,
                originalQueueRef, scoreRef, anchorRef);
    }
}
