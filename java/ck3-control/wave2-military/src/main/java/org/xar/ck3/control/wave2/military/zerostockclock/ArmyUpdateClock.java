package org.xar.ck3.control.wave2.military.zerostockclock;

import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Complete observed army_update_clock_v1 contract; no future clock is calculated. */
public record ArmyUpdateClock(Status status, boolean ready, String unavailableReason,
        Integer currentDateRaw, Integer nativeDayIndex, Integer selectedBucketPhase,
        Integer observedArmyBucketPhase, Integer lastSupplyUpdateDateRaw,
        Integer graceAnchorDateRaw, Integer loadedGraceDays,
        Long lastSupplyUpdateDateStorageRaw64, Long graceAnchorDateStorageRaw64) {
    public enum Status { AVAILABLE, NOT_REGISTERED, UNAVAILABLE }
    public ArmyUpdateClock {
        Objects.requireNonNull(status);
        StrictJson.require(ready == (status != Status.UNAVAILABLE), "army clock readiness differs from status");
        StrictJson.require(ready ? unavailableReason == null : unavailableReason != null && !unavailableReason.isEmpty(),
                "army clock reason differs from readiness");
        StrictJson.require(selectedBucketPhase == null || selectedBucketPhase >= 0 && selectedBucketPhase < 30,
                "selected bucket must be a native phase");
        StrictJson.require(observedArmyBucketPhase == null || observedArmyBucketPhase >= 0 && observedArmyBucketPhase < 30,
                "army bucket must be a native phase");
        StrictJson.require(!ready || currentDateRaw != null && nativeDayIndex != null && selectedBucketPhase != null
                && lastSupplyUpdateDateRaw != null && graceAnchorDateRaw != null && loadedGraceDays != null
                && lastSupplyUpdateDateStorageRaw64 != null && graceAnchorDateStorageRaw64 != null,
                "ready army clock incomplete");
        StrictJson.require(status != Status.AVAILABLE || observedArmyBucketPhase != null,
                "registered clock requires army phase");
        StrictJson.require(status != Status.NOT_REGISTERED || observedArmyBucketPhase == null,
                "not_registered clock cannot claim army phase");
    }
}
