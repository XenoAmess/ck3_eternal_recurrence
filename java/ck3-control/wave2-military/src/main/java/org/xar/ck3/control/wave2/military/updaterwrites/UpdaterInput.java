package org.xar.ck3.control.wave2.military.updaterwrites;

import java.util.Objects;

/** Declared projection of an extensible normalized Army row; no observation qualification implied. */
public record UpdaterInput(boolean rowAvailable, Integer armyId, Integer nativeCarmyId,
                           GateInputs gateInputs, ClockInputs clock, CallerInputs caller,
                           SourceNextFrame sourceNextDate) {
    public UpdaterInput { Objects.requireNonNull(gateInputs); Objects.requireNonNull(clock); Objects.requireNonNull(caller); }
    public record GateInputs(Integer unitNative170Raw, Boolean nativeUnitInCombat,
                             Boolean nativeUnitGathering, Integer armyGatheringCountRaw) {}
    public record ClockInputs(Integer currentDateRaw, Integer lastSupplyUpdateDateRaw,
                              Integer graceAnchorDateRaw, Integer loadedGraceDays,
                              Long lastSupplyUpdateDateStorageRaw64, Long graceAnchorDateStorageRaw64) {}
    public record CallerInputs(Long armyByte22Raw, Long currentDateStorageRaw64) {}
}
