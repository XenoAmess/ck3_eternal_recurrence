package org.xar.ck3.control.application.action;

import java.time.Instant;
import org.xar.ck3.control.contracts.ExactRef;

/** Read-only DATA view of one original-owner query. Only the installed Root's private issuer
 * and source-owned continuation gate may authorize consumption; implementing this interface
 * or decoding a receipt cannot authorize any query, action, reducer or replay. */
public interface DirectFixedWindowQueryContinuation {
    String actionId();
    PlanningReadReceipt queryReceipt();
    ExactRef queryRef();
    Instant deadline();
}
