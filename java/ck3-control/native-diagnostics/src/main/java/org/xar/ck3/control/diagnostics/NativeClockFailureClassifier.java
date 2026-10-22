package org.xar.ck3.control.diagnostics;

import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.diagnostics.ClockFailureAssessment.*;
import org.xar.ck3.control.diagnostics.NativeClockFailureObservation.*;

/** Pure classification of bounded observations. No clocks, files, network, or Game calls. */
public final class NativeClockFailureClassifier {
    private NativeClockFailureClassifier() { }

    public static ClockFailureAssessment classify(NativeClockFailureObservation observation, long stallThresholdMillis) {
        StrictJson.require(stallThresholdMillis > 0 && stallThresholdMillis <= Integer.MAX_VALUE,
                "explicit positive bounded stall threshold required");
        NativeClockFailureCodec.validate(observation);
        WaitProgress progress = observation.progress();
        boolean sourceFlagged = positive(progress.flags());
        boolean identityAligned = sameIdentity(observation) && observation.waitFinal().revision() >= observation.starting().revision()
                && observation.waitFinal().nativeRevision() >= observation.starting().nativeRevision();
        boolean sourceTimeOrdered = compare(observation.waitFinal().heartbeat().monotonicMillis(), observation.starting().heartbeat().monotonicMillis()) >= 0
                && compare(observation.cleanupTail().heartbeat().monotonicMillis(), observation.waitFinal().heartbeat().monotonicMillis()) >= 0;
        TransportAlive transport = sourceFlagged || !identityAligned || !sourceTimeOrdered || uncertain(progress.heartbeat()) ? TransportAlive.INDETERMINATE
                : positive(progress.heartbeat().delta()) ? TransportAlive.ALIVE_DURING_WAIT
                : TransportAlive.NO_HEARTBEAT_PROGRESS;
        long trailing = progress.elapsedMillis() - Math.max(lastChange(progress.owner()), lastChange(progress.verified()));
        boolean verifiedTailProgress = compare(observation.cleanupTail().owner().verifiedPumpEpochs(), progress.verified().last()) > 0;
        boolean ownerAligned = aligned(progress.owner(), observation.starting().owner().pumpEpochs(), observation.waitFinal().owner().pumpEpochs())
                && aligned(progress.verified(), observation.starting().owner().verifiedPumpEpochs(), observation.waitFinal().owner().verifiedPumpEpochs())
                && compare(observation.cleanupTail().owner().pumpEpochs(), progress.owner().last()) >= 0
                && compare(observation.cleanupTail().owner().verifiedPumpEpochs(), progress.verified().last()) >= 0;
        OwnerProgress owner;
        if (sourceFlagged || !identityAligned || !sourceTimeOrdered || !ownerAligned || uncertain(progress.owner()) || uncertain(progress.verified())) {
            owner = OwnerProgress.INDETERMINATE;
        } else if (transport == TransportAlive.ALIVE_DURING_WAIT && trailing >= stallThresholdMillis) {
            owner = verifiedTailProgress ? OwnerProgress.STALLED_AT_WAIT_END_WITH_TAIL_PROGRESS : OwnerProgress.STALLED_AT_WAIT_END;
        } else if (positive(progress.verified().delta())) {
            owner = OwnerProgress.PROGRESS_OBSERVED;
        } else if (positive(progress.owner().delta())) {
            owner = OwnerProgress.UNVERIFIED_PUMP_PROGRESS;
        } else {
            owner = OwnerProgress.NO_PROGRESS_OBSERVED;
        }
        PauseAcknowledgements acknowledgements = PauseAcknowledgements.NONE;
        if (!observation.cleanupAttempts().isEmpty()) {
            boolean allSubmitted = observation.cleanupAttempts().stream()
                    .allMatch(row -> Boolean.TRUE.equals(row.accepted()) && row.status() == PauseAckStatus.SUBMITTED);
            boolean allObserved = observation.cleanupAttempts().stream()
                    .allMatch(row -> Boolean.TRUE.equals(row.accepted()) && row.status() == PauseAckStatus.ALREADY_OBSERVED);
            acknowledgements = allSubmitted ? PauseAcknowledgements.ALL_SUBMITTED
                    : allObserved ? PauseAcknowledgements.ALL_ALREADY_OBSERVED : PauseAcknowledgements.MIXED_OR_UNCONFIRMED;
        }
        Boolean paused = observation.cleanupTail().pausedAfterCleanup();
        PauseObserved pause = paused == null ? PauseObserved.UNOBSERVED_AFTER_CLEANUP
                : paused ? PauseObserved.OBSERVED_PAUSED_AFTER_CLEANUP : PauseObserved.OBSERVED_RUNNING_AFTER_CLEANUP;
        Long observedUnchanged = owner == OwnerProgress.INDETERMINATE ? null : trailing;
        return new ClockFailureAssessment(transport, owner, acknowledgements, pause, observedUnchanged, stallThresholdMillis,
                observation.waitFinal().observer().readInProgress(), PermanentDeadlock.NOT_DETERMINABLE, 0, true, false);
    }

    private static boolean uncertain(Metric metric) { return metric.missing() > 0 || metric.resets() > 0; }
    private static boolean sameIdentity(NativeClockFailureObservation value) {
        return value.starting().bridge().equals(value.waitIdentity().bridge()) && value.waitFinal().bridge().equals(value.waitIdentity().bridge())
                && value.starting().episodeCharacterId() == value.waitIdentity().episodeCharacterId()
                && value.waitFinal().episodeCharacterId() == value.waitIdentity().episodeCharacterId();
    }
    private static boolean aligned(Metric metric, org.xar.ck3.control.contracts.CrossJsDecimalUInt64 first,
                                   org.xar.ck3.control.contracts.CrossJsDecimalUInt64 last) {
        return metric.first().equals(first) && metric.last().equals(last);
    }
    private static int compare(org.xar.ck3.control.contracts.CrossJsDecimalUInt64 first,
                               org.xar.ck3.control.contracts.CrossJsDecimalUInt64 last) {
        return NativeClockFailureCodec.number(first).compareTo(NativeClockFailureCodec.number(last));
    }
    private static int lastChange(Metric metric) { return metric.lastChangeMillis() == null ? 0 : metric.lastChangeMillis(); }
    private static boolean positive(org.xar.ck3.control.contracts.CrossJsDecimalUInt64 value) {
        return NativeClockFailureCodec.number(value).signum() > 0;
    }
}
