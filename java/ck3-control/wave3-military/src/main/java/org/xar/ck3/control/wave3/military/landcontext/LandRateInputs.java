package org.xar.ck3.control.wave3.military.landcontext;

import java.util.Objects;

public record LandRateInputs(Status status, String unavailableReason, boolean currentObservationReady,
                             Integer provinceId, Integer subjectArmyId, Integer subjectCarmyId,
                             Integer ownerCharacterId, Integer commanderRawFullId, Integer commanderResolvedFullId,
                             Boolean commanderUsedNativeFallback, Boolean nativeLandBranchApplicable,
                             Boolean nativeProvinceComponentApplicable, Long provinceComponentRaw,
                             Long commanderModifier1a9Raw, Long loadedExcessSlopeRaw, Long loadedMinLossRaw,
                             Long loadedMaxLossRaw, Long loadedDivisorFloorRaw) {
    public enum Status { AVAILABLE, UNAVAILABLE, NOT_LAND }
    public LandRateInputs {
        Objects.requireNonNull(status);
        require(unavailableReason == null || !unavailableReason.isEmpty(), "land-rate reason must be nonempty/null");
        if (status == Status.AVAILABLE) {
            require(unavailableReason == null && currentObservationReady && Boolean.TRUE.equals(nativeLandBranchApplicable)
                    && provinceId != null && subjectArmyId != null && subjectCarmyId != null && ownerCharacterId != null
                    && commanderRawFullId != null && commanderResolvedFullId != null && commanderUsedNativeFallback != null
                    && nativeProvinceComponentApplicable != null && provinceComponentRaw != null && commanderModifier1a9Raw != null
                    && loadedExcessSlopeRaw != null && loadedMinLossRaw != null && loadedMaxLossRaw != null
                    && loadedDivisorFloorRaw != null, "available Land rate inputs are incomplete");
            if (Boolean.FALSE.equals(nativeProvinceComponentApplicable)) require(provinceComponentRaw == 0,
                    "absent Province component must be zero");
            if (Boolean.FALSE.equals(commanderUsedNativeFallback)) require(commanderRawFullId.equals(commanderResolvedFullId),
                    "direct resolved commander identity differs");
        } else require(!currentObservationReady, "nonavailable Land rate cannot be ready");
        if (status == Status.NOT_LAND) require(Boolean.FALSE.equals(nativeLandBranchApplicable) && unavailableReason == null
                && nativeProvinceComponentApplicable == null && provinceComponentRaw == null && commanderModifier1a9Raw == null,
                "not-land rate branch differs");
        if (status == Status.UNAVAILABLE) require(unavailableReason != null, "unavailable Land rate requires reason");
    }
    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }
}
