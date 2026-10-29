package org.xar.ck3.control.wave2.military.supplyschedule;

import java.util.List;
import java.util.Objects;

/** Current observed native all-phase bucket membership; never a future callback proof. */
public record FutureDailySupplySchedule(
        Status status, String unavailableReason, Long subjectArmyIdU32, Long subjectCarmyIdU32,
        Long currentDateStorageRaw64, Integer currentDateRawI32, Integer nativeDayIndexRawI32,
        Integer selectedPhaseIndexI32, List<Phase> phases) {
    public enum Status { AVAILABLE, PARTIAL, UNAVAILABLE }
    public enum PhaseStatus { AVAILABLE, UNAVAILABLE }

    public FutureDailySupplySchedule {
        Objects.requireNonNull(status, "status");
        reason(status == Status.AVAILABLE, unavailableReason);
        uint32(subjectArmyIdU32); uint32(subjectCarmyIdU32);
        phases = List.copyOf(phases);
        require(phases.size() == 0 || phases.size() == 30, "all thirty phases or unavailable pre-capture required");
        for (int index = 0; index < phases.size(); index++) {
            require(phases.get(index).phaseIndexI32() == index, "original phase order required");
        }
        if (status == Status.UNAVAILABLE) {
            require(phases.isEmpty(), "unavailable pre-capture cannot contain phase rows");
        } else {
            require(phases.size() == 30 && subjectArmyIdU32 != null && subjectCarmyIdU32 != null
                    && currentDateStorageRaw64 != null && currentDateRawI32 != null
                    && nativeDayIndexRawI32 != null && selectedPhaseIndexI32 != null,
                    "captured schedule operands incomplete");
            require(selectedPhaseIndexI32 == phaseIndex(nativeDayIndexRawI32), "unsigned stored day modulo thirty required");
            require((status == Status.AVAILABLE) == phases.stream().allMatch(Phase::ready), "all-phase readiness differs");
        }
    }

    public boolean ready() { return status == Status.AVAILABLE; }
    public static int phaseIndex(int nativeDayIndexRawI32) { return Integer.remainderUnsigned(nativeDayIndexRawI32, 30); }

    public record Phase(int phaseIndexI32, PhaseStatus status, String unavailableReason,
            Integer capacityRawI32, Integer countRawI32, Boolean dataPointerPresent,
            List<Integer> matchingPositions, Integer subjectOccurrenceCountI32) {
        public Phase {
            Objects.requireNonNull(status, "phase status");
            reason(status == PhaseStatus.AVAILABLE, unavailableReason);
            if (matchingPositions != null) {
                matchingPositions = List.copyOf(matchingPositions);
                matchingPositions.forEach(position -> require(position >= 0, "original nonnegative int32 slot required"));
            }
            if (status == PhaseStatus.AVAILABLE) {
                require(countRawI32 != null && countRawI32 >= 0 && dataPointerPresent != null
                        && (countRawI32 == 0 || dataPointerPresent) && matchingPositions != null,
                        "ready phase operands incomplete");
                require(subjectOccurrenceCountI32 != null && subjectOccurrenceCountI32 == matchingPositions.size(),
                        "occurrence count must retain every matching slot");
                int previous = -1;
                for (int position : matchingPositions) {
                    require(position > previous && position < countRawI32, "matching slots must retain original strictly increasing order");
                    previous = position;
                }
            }
        }
        public boolean ready() { return status == PhaseStatus.AVAILABLE; }
    }

    private static void uint32(Long value) {
        require(value == null || (value >= 0 && value <= 0xFFFF_FFFFL), "full uint32 or null required");
    }
    private static void reason(boolean ready, String reason) {
        require(ready ? reason == null : reason != null && !reason.isEmpty(), "reason disagrees with readiness");
    }
    static void require(boolean valid, String reason) { if (!valid) throw new IllegalArgumentException(reason); }
}
