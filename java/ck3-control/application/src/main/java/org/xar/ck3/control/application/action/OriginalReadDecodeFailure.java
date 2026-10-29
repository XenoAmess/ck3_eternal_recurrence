package org.xar.ck3.control.application.action;

/**
 * A source-owned failure from the live decoder of one actual received READ.
 * Implementations retain private producer custody; neither replay nor a reason string
 * can create this live failure. The exception object is never persistent evidence.
 */
public interface OriginalReadDecodeFailure {
    void requireOriginal(ReadContract<?> identicalInstalled, PlanningReadRequest actualRequest,
            PlanningReadReceipt actualReceipt);
}
