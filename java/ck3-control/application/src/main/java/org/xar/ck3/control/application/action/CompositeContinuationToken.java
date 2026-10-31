package org.xar.ck3.control.application.action;

import java.time.Instant;

/** A source-owned continuation handle. Implementing this interface grants no submission authority. */
public interface CompositeContinuationToken {
    enum Kind { SUCCESSOR_UI_CLOSE, SUCCESSOR_UI_EVENT, SUCCESSOR_UI_DATE_ADVANCE, FIXTURE_STARTUP, LIFE_SENTINEL_CANCEL }
    ActionCommand originalParent();
    Instant deadline();
    Kind kind();
}
