package org.xar.ck3.control.wave2.military.prestore;

import java.util.List;
import java.util.Objects;

/** Full existing current-route-edge DTO, retaining optional-member presence. No future frame qualification. */
public record CurrentMovement(Status status, Integer unitState, Long accumulatedWeight, Long cachedEdgeSpeed,
                              FixedPoint normalizedProgress, FixedPoint remainingDuration, String unavailableReason,
                              Field<Long> currentEdgeRate, Field<Boolean> nativeArmyAdmission, Field<Long> firstEdgeCost,
                              Field<Integer> arrivalProviderByte, Field<Long> targetProvinceType, Field<Long> currentProvinceType,
                              Field<Integer> unitKind, Field<Integer> currentDefinitionByte, Field<Integer> targetDefinitionByte,
                              Field<Integer> loadedDisembarkDays, Field<FixedPoint> loadedLockCutoff, Field<Timeline> timeline) {
    public CurrentMovement {
        Objects.requireNonNull(status); Objects.requireNonNull(currentEdgeRate); Objects.requireNonNull(nativeArmyAdmission);
        Objects.requireNonNull(firstEdgeCost); Objects.requireNonNull(arrivalProviderByte); Objects.requireNonNull(targetProvinceType);
        Objects.requireNonNull(currentProvinceType); Objects.requireNonNull(unitKind); Objects.requireNonNull(currentDefinitionByte);
        Objects.requireNonNull(targetDefinitionByte); Objects.requireNonNull(loadedDisembarkDays);
        Objects.requireNonNull(loadedLockCutoff); Objects.requireNonNull(timeline);
        if (unavailableReason != null && unavailableReason.isEmpty()) { throw new IllegalArgumentException("nonempty movement reason or null"); }
    }
    public enum Status { AVAILABLE, NOT_APPLICABLE, PARTIAL, UNAVAILABLE }
    public enum Presence { MISSING, NULL, VALUE }
    public record Field<T>(Presence presence, T value) {
        public Field {
            Objects.requireNonNull(presence);
            if ((presence == Presence.VALUE) != (value != null)) { throw new IllegalArgumentException("field presence/value mismatch"); }
        }
        public static <T> Field<T> missing() { return new Field<>(Presence.MISSING, null); }
        public static <T> Field<T> nullValue() { return new Field<>(Presence.NULL, null); }
        public static <T> Field<T> of(T value) { return new Field<>(Presence.VALUE, Objects.requireNonNull(value)); }
    }
    public record FixedPoint(long raw) { public static final int SCALE = 100_000; }
    public enum TimelineStatus { AVAILABLE, NOT_APPLICABLE, UNAVAILABLE }
    public record Timeline(TimelineStatus status, String unavailableReason, Long fullDuration,
                           List<Integer> provinces, List<Long> prefixDurations, List<Integer> arrivalDates) {
        public Timeline {
            Objects.requireNonNull(status);
            if (provinces != null) { provinces = List.copyOf(provinces); }
            if (prefixDurations != null) { prefixDurations = List.copyOf(prefixDurations); }
            if (arrivalDates != null) { arrivalDates = List.copyOf(arrivalDates); }
            if (status == TimelineStatus.UNAVAILABLE) {
                if (fullDuration != null || provinces != null || prefixDurations != null || arrivalDates != null
                        || unavailableReason == null || unavailableReason.isEmpty()) {
                    throw new IllegalArgumentException("unavailable timeline requires null predictions and reason");
                }
            } else {
                if (unavailableReason != null || provinces == null || prefixDurations == null || arrivalDates == null
                        || provinces.size() != prefixDurations.size() || provinces.size() != arrivalDates.size()) {
                    throw new IllegalArgumentException("aligned timeline arrays and null reason required");
                }
                for (int province : provinces) { if (province <= 0) { throw new IllegalArgumentException("positive int32 province required"); } }
                if (status == TimelineStatus.AVAILABLE) {
                    if (prefixDurations.isEmpty() || !Objects.equals(fullDuration, prefixDurations.getLast())) {
                        throw new IllegalArgumentException("available final duration must equal last prefix");
                    }
                } else if (!prefixDurations.isEmpty() || fullDuration != null) {
                    throw new IllegalArgumentException("not applicable timeline requires empty arrays/null final");
                }
            }
        }
    }
}
