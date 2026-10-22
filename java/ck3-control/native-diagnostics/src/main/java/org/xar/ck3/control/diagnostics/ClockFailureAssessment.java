package org.xar.ck3.control.diagnostics;

import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Diagnostic conclusions only. No recovery, replay, command, or saved-day credit is granted. */
public record ClockFailureAssessment(TransportAlive transportAlive, OwnerProgress ownerProgress,
        PauseAcknowledgements pauseAcknowledgements, PauseObserved pauseObserved,
        Long trailingOwnerUnchangedMillis, long stallThresholdMillis, boolean observerReadingAtWaitEnd,
        PermanentDeadlock permanentDeadlock, int credit, boolean neverReplay, boolean resumeAuthorized) {
    public ClockFailureAssessment {
        Objects.requireNonNull(transportAlive); Objects.requireNonNull(ownerProgress);
        Objects.requireNonNull(pauseAcknowledgements); Objects.requireNonNull(pauseObserved);
        Objects.requireNonNull(permanentDeadlock);
        StrictJson.require((trailingOwnerUnchangedMillis == null || trailingOwnerUnchangedMillis >= 0)
                && stallThresholdMillis > 0, "valid diagnostic window required");
        StrictJson.require(credit == 0 && neverReplay && !resumeAuthorized, "clock failure cannot grant execution authority");
    }

    public enum TransportAlive { ALIVE_DURING_WAIT, NO_HEARTBEAT_PROGRESS, INDETERMINATE }
    public enum OwnerProgress {
        PROGRESS_OBSERVED, NO_PROGRESS_OBSERVED, STALLED_AT_WAIT_END,
        STALLED_AT_WAIT_END_WITH_TAIL_PROGRESS, UNVERIFIED_PUMP_PROGRESS, INDETERMINATE
    }
    public enum PauseAcknowledgements { NONE, ALL_SUBMITTED, ALL_ALREADY_OBSERVED, MIXED_OR_UNCONFIRMED }
    public enum PauseObserved { OBSERVED_PAUSED_AFTER_CLEANUP, OBSERVED_RUNNING_AFTER_CLEANUP, UNOBSERVED_AFTER_CLEANUP }
    public enum PermanentDeadlock { NOT_DETERMINABLE }
}
