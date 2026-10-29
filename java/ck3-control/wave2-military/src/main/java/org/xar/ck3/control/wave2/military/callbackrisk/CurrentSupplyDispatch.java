package org.xar.ck3.control.wave2.military.callbackrisk;

import java.util.List;
import java.util.Objects;

/** Current selected-bucket observations; occurrences never mean repeated future callbacks. */
public record CurrentSupplyDispatch(Status status, String unavailableReason,
                                    Integer subjectArmyId, Integer subjectCarmyId,
                                    Integer currentDateRaw, Integer nativeDayIndex,
                                    Integer selectedBucketPhase, Integer selectedBucketCapacityRaw,
                                    Integer selectedBucketCountRaw, Boolean selectedBucketDataPresent,
                                    Integer subjectDispatchOccurrenceCount, List<Integer> subjectOccurrenceIndices) {
    public enum Status { AVAILABLE, UNAVAILABLE }
    public CurrentSupplyDispatch {
        Objects.requireNonNull(status);
        subjectOccurrenceIndices = subjectOccurrenceIndices == null ? null : List.copyOf(subjectOccurrenceIndices);
        boolean ready = status == Status.AVAILABLE;
        require(ready ? unavailableReason == null : unavailableReason != null && !unavailableReason.isEmpty(),
                "current dispatch reason disagrees with readiness");
        if (subjectOccurrenceIndices != null) {
            require(subjectOccurrenceIndices.stream().allMatch(index -> index >= 0), "dispatch indices must be nonnegative int32");
        }
        if (ready) {
            require(subjectArmyId != null && subjectCarmyId != null && currentDateRaw != null
                    && nativeDayIndex != null && selectedBucketPhase != null && selectedBucketCountRaw != null
                    && selectedBucketDataPresent != null && subjectDispatchOccurrenceCount != null
                    && subjectOccurrenceIndices != null, "ready current dispatch operands incomplete");
            require(selectedBucketPhase == Integer.toUnsignedLong(nativeDayIndex) % 30,
                    "dispatch phase must use unsigned stored native day modulo30");
            require(selectedBucketCountRaw >= 0 && (selectedBucketCountRaw == 0 || selectedBucketDataPresent),
                    "current selected bucket count or data pointer unavailable");
            require(subjectDispatchOccurrenceCount == subjectOccurrenceIndices.size(), "dispatch occurrence count differs from indices");
            int previous = -1;
            for (int index : subjectOccurrenceIndices) {
                require(index < selectedBucketCountRaw && index > previous, "dispatch indices must retain distinct traversal order");
                previous = index;
            }
        }
    }
    public boolean ready() { return status == Status.AVAILABLE; }
    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }
}
