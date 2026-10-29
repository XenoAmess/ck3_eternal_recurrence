package org.xar.ck3.control.application.history;

import java.util.Objects;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Finite failed Army-read history DATA. None of these values proves an attempt, source custody or current state.
 * Only the sole publisher may consume its actual central opaque attempt and queue a canonical error row.
 * Failure has no after-frame, successful Known, Native result or READ-only lineage qualification. */
public final class DriverReadHistoryFailureMaterial {
    private DriverReadHistoryFailureMaterial() { }
    public enum Kind { ARMY_STRENGTHS }
    public enum Reason { NO_ORIGINAL_ATTEMPT, UNSUPPORTED_CAUSE, INACTIVE_SCOPE }
    public sealed interface Outcome permits Queued, Unrecorded, StorageDiagnostic { }
    /** Original row artifact is retained and queued; this does not claim writer commit or a business result. */
    public record Queued(ExactRef originalRow) implements Outcome {
        public Queued { Objects.requireNonNull(originalRow);StrictJson.require(originalRow.bytes()>0,"actual queued original error row required"); }
    }
    /** Explicit missing provenance remains a gap, never an empty successful history publication. */
    public record Unrecorded(Reason reason,String diagnostic) implements Outcome {
        public Unrecorded { Objects.requireNonNull(reason);bounded(diagnostic); }
    }
    /** Canonical history retention failure, distinct from the original Native read failure and legacy sidecar policy. */
    public record StorageDiagnostic(String failureType,String message) implements Outcome {
        public StorageDiagnostic { bounded(failureType);Objects.requireNonNull(message);StrictJson.require(message.length()<=8192,"finite actual storage failure message required"); }
    }
    /** The actual Java service surface for this finite cause. Public DATA construction grants no attempt authority. */
    public static IllegalStateException unavailableException(PlanningReadResult.Unavailable<?> actual) {
        Objects.requireNonNull(actual);return new IllegalStateException(actual.reason());
    }
    /** Same type/message as unavailableException, deterministically recomputed from the actual unavailable original. */
    public static String unavailableError(PlanningReadResult.Unavailable<?> actual) {
        Objects.requireNonNull(actual);return IllegalStateException.class.getSimpleName()+": "+actual.reason();
    }
    private static void bounded(String value) {
        StrictJson.text(value);StrictJson.require(value.length()<=8192,"finite history diagnostic required");
    }
}
