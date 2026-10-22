package org.xar.ck3.control.diagnostics;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/** An explicitly normalized failure projection. It never grants action or replay authority. */
public record NativeClockFailureObservation(
        String machineId, String observedAtUtc, SourceEvidence source,
        WaitIdentity waitIdentity, long targetDateRaw, ClockFrame starting,
        ClockFrame waitFinal, WaitProgress progress, List<PauseAttempt> cleanupAttempts,
        CleanupTail cleanupTail) {
    public static final String SCHEMA = "xar.native-clock-failure-observation/v1";
    public static final String SOURCE_SCHEMA = "xar.exact-day-clock-failure.v2";

    public NativeClockFailureObservation {
        StrictJson.text(machineId); StrictJson.utc(observedAtUtc);
        Objects.requireNonNull(source); Objects.requireNonNull(waitIdentity);
        Objects.requireNonNull(starting); Objects.requireNonNull(waitFinal);
        Objects.requireNonNull(progress); Objects.requireNonNull(cleanupTail);
        cleanupAttempts = List.copyOf(cleanupAttempts);
        StrictJson.require(cleanupAttempts.size() <= 8, "bounded cleanup attempts required");
        StrictJson.safe(targetDateRaw, 0);
    }

    public record SourcePin(String sha256, int controlSequence) {
        public SourcePin {
            sha(sha256);
            StrictJson.require(controlSequence > 0, "positive source control sequence required");
        }
    }

    public record SourceEvidence(String sourceSchema, String sourceSha256, int controlSequence,
                                 String projectionNotice) {
        public static final String NOTICE = "normalized_projection_not_original";
        public SourceEvidence {
            StrictJson.require(SOURCE_SCHEMA.equals(sourceSchema), "unsupported native failure schema");
            sha(sourceSha256);
            StrictJson.require(controlSequence > 0, "positive control sequence required");
            StrictJson.require(NOTICE.equals(projectionNotice), "projection must not impersonate its original");
        }
    }

    public record BridgeIdentity(long bridgePid, long connectionGeneration) {
        public BridgeIdentity {
            StrictJson.require(bridgePid > 0 && bridgePid <= 0xffff_ffffL && connectionGeneration > 0
                    && connectionGeneration <= StrictJson.MAX_SAFE_INTEGER, "exact bridge identity required");
        }
    }

    public record WaitIdentity(BridgeIdentity bridge, long episodeCharacterId, String episodeId) {
        public WaitIdentity {
            Objects.requireNonNull(bridge);
            StrictJson.safe(episodeCharacterId, 1);
            StrictJson.text(episodeId);
        }
    }

    public record Heartbeat(CrossJsDecimalUInt64 sequence, CrossJsDecimalUInt64 monotonicMillis) {
        public Heartbeat { Objects.requireNonNull(sequence); Objects.requireNonNull(monotonicMillis); }
    }

    public record Owner(CrossJsDecimalUInt64 pumpEpochs, CrossJsDecimalUInt64 verifiedPumpEpochs) {
        public Owner { Objects.requireNonNull(pumpEpochs); Objects.requireNonNull(verifiedPumpEpochs); }
    }

    public record Observer(CrossJsDecimalUInt64 startedMillis, CrossJsDecimalUInt64 completedMillis,
                           boolean readInProgress, boolean lastReadAvailable) {
        public Observer {
            Objects.requireNonNull(startedMillis); Objects.requireNonNull(completedMillis);
        }
    }

    public record ClockFrame(long dateRaw, long revision, long nativeRevision, int speed, boolean paused,
                             BridgeIdentity bridge, long episodeCharacterId, Heartbeat heartbeat,
                             Owner owner, Observer observer) {
        public ClockFrame {
            StrictJson.require(dateRaw >= 0 && dateRaw <= StrictJson.MAX_SAFE_INTEGER && revision > 0 && nativeRevision > 0
                    && revision <= StrictJson.MAX_SAFE_INTEGER && nativeRevision <= StrictJson.MAX_SAFE_INTEGER,
                    "bounded exact frame integers required");
            StrictJson.require(speed >= 1 && speed <= 5, "valid speed required");
            StrictJson.safe(episodeCharacterId, 1);
            Objects.requireNonNull(bridge); Objects.requireNonNull(heartbeat);
            Objects.requireNonNull(owner); Objects.requireNonNull(observer);
        }
    }

    public record Metric(CrossJsDecimalUInt64 first, CrossJsDecimalUInt64 last, Integer lastChangeMillis,
                         int changes, CrossJsDecimalUInt64 delta, int missing, int resets) {
        public Metric {
            Objects.requireNonNull(first); Objects.requireNonNull(last); Objects.requireNonNull(delta);
            StrictJson.require((lastChangeMillis == null || lastChangeMillis >= 0) && changes >= 0 && missing >= 0 && resets >= 0,
                    "nonnegative progress counters required");
        }
    }

    public record WaitProgress(CrossJsDecimalUInt64 armGeneration, CrossJsDecimalUInt64 flags,
                               int elapsedMillis, int heartbeatEvents, int maximumHeartbeatGapMillis,
                               Metric owner, Metric verified, Metric heartbeat, Metric observer,
                               boolean nativeEventTimeVerified, boolean atomicObservation) {
        public WaitProgress {
            Objects.requireNonNull(armGeneration); Objects.requireNonNull(flags);
            StrictJson.require(!"0".equals(armGeneration.decimal()), "positive armed generation required");
            StrictJson.require(elapsedMillis > 0 && heartbeatEvents >= 0
                    && maximumHeartbeatGapMillis >= 0 && maximumHeartbeatGapMillis <= elapsedMillis,
                    "bounded progress window required");
            Objects.requireNonNull(owner); Objects.requireNonNull(verified);
            Objects.requireNonNull(heartbeat); Objects.requireNonNull(observer);
        }
    }

    public enum PauseAckStatus { SUBMITTED, ALREADY_OBSERVED, REJECTED, UNAVAILABLE }

    /** accepted=null is an observed unknown ACK field, not missing or rejected. */
    public record PauseAttempt(String nativeRequestId, PauseAckStatus status, Boolean accepted) {
        public PauseAttempt { StrictJson.text(nativeRequestId); Objects.requireNonNull(status); }
    }

    /** pausedAfterCleanup=null means that no cleanup post-state was observed. */
    public record CleanupTail(Heartbeat heartbeat, Owner owner, CrossJsDecimalUInt64 observerCompletedMillis,
                              Boolean pausedAfterCleanup) {
        public CleanupTail {
            Objects.requireNonNull(heartbeat); Objects.requireNonNull(owner);
            Objects.requireNonNull(observerCompletedMillis);
        }
    }

    private static void sha(String value) {
        StrictJson.require(value != null && value.matches("[0-9a-f]{64}"), "lowercase SHA-256 required");
    }
}
