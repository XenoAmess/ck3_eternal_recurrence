package org.xar.ck3.control.wave3.military.landcontext;

import java.util.Objects;

public record LandResupply(LandRateInputs.Status status, String unavailableReason, boolean currentObservationReady,
                           Integer provinceId, Integer ownerCharacterId, Boolean nativeLandBranchApplicable,
                           Boolean nativeResupplyEligible, Long loadedGainRaw) {
    public LandResupply {
        Objects.requireNonNull(status);
        require(unavailableReason == null || !unavailableReason.isEmpty(), "land-resupply reason must be nonempty/null");
        if (status == LandRateInputs.Status.AVAILABLE) {
            require(unavailableReason == null && currentObservationReady && Boolean.TRUE.equals(nativeLandBranchApplicable)
                    && provinceId != null && ownerCharacterId != null && nativeResupplyEligible != null && loadedGainRaw != null,
                    "available land resupply is incomplete");
        } else require(!currentObservationReady && nativeResupplyEligible == null, "nonavailable land resupply cannot publish admission");
        if (status == LandRateInputs.Status.NOT_LAND) require(Boolean.FALSE.equals(nativeLandBranchApplicable)
                && unavailableReason == null, "not-land resupply branch differs");
    }
    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }
}
