package org.xar.ck3.control.wave3.military.landcontext;

import java.util.List;
import java.util.Objects;

public record ProvinceContributors(FullDataModel.Coverage status, String unavailableReason,
                                   boolean currentUsageReady, boolean contributorsReady,
                                   Integer provinceId, Integer subjectArmyId, Integer subjectCarmyId,
                                   Integer ownerCharacterId, Integer nativeProvinceUnitCount,
                                   Integer nativeSupplyLimitSoldiers, Integer nativeSupplyUsageSoldiers,
                                   List<Occurrence> occurrences) {
    public ProvinceContributors {
        Objects.requireNonNull(status); occurrences = List.copyOf(occurrences);
        require(status != FullDataModel.Coverage.AVAILABLE || unavailableReason == null, "available Province reason must be null");
        reason(unavailableReason);
        require(!currentUsageReady || nativeSupplyUsageSoldiers != null, "ready Province usage requires its scalar");
        for (int index = 0; index < occurrences.size(); index++) require(occurrences.get(index).storedIndex() == index,
                "Province occurrence order differs");
        if (contributorsReady) require(nativeProvinceUnitCount != null && nativeProvinceUnitCount >= 0
                && nativeProvinceUnitCount == occurrences.size()
                && occurrences.stream().allMatch(row -> row.status() == FullDataModel.RecordStatus.AVAILABLE),
                "ready Province contributor roster is incomplete");
    }
    public enum InclusionBasis { SAME_OWNER, NATIVE_COMMON_WAR_SIDE, NATIVE_NOT_COMMON_WAR_SIDE }
    public record Occurrence(int storedIndex, int armyId, FullDataModel.RecordStatus status, String unavailableReason,
                              Integer ownerCharacterId, Boolean included, InclusionBasis inclusionBasis,
                              Integer nativeCarmyId, Integer nativeEligibleCurrentSoldiers, List<Regiment> regiments) {
        public Occurrence {
            Objects.requireNonNull(status); regiments = List.copyOf(regiments);
            require(status != FullDataModel.RecordStatus.AVAILABLE || unavailableReason == null, "available occurrence reason must be null");
            reason(unavailableReason);
            if (Boolean.TRUE.equals(included)) require(inclusionBasis == InclusionBasis.SAME_OWNER
                    || inclusionBasis == InclusionBasis.NATIVE_COMMON_WAR_SIDE, "included occurrence lacks its witness");
            else if (Boolean.FALSE.equals(included)) require(inclusionBasis == InclusionBasis.NATIVE_NOT_COMMON_WAR_SIDE
                    && regiments.isEmpty() && nativeEligibleCurrentSoldiers == null, "excluded occurrence has contribution or wrong witness");
            else require(inclusionBasis == null, "unknown inclusion has a false witness");
            for (int index = 0; index < regiments.size(); index++) require(regiments.get(index).storedIndex() == index,
                    "Province regiment order differs");
            if (status == FullDataModel.RecordStatus.AVAILABLE) {
                require(included != null, "available Province occurrence lacks inclusion");
                if (included) require(nativeCarmyId != null && nativeEligibleCurrentSoldiers != null
                        && regiments.stream().allMatch(row -> row.status() == FullDataModel.RecordStatus.AVAILABLE),
                        "available included Province occurrence is incomplete");
            }
        }
    }
    public record Regiment(int storedIndex, int armyRegimentId, FullDataModel.RecordStatus status, String unavailableReason,
                            Integer currentSoldiers, Integer maximumSoldiers, Boolean nativeSupplyLossEligible,
                            FullDataModel.Snapshot replenishmentRecords) {
        public Regiment {
            Objects.requireNonNull(status); reason(unavailableReason);
            require(status != FullDataModel.RecordStatus.AVAILABLE || unavailableReason == null, "available regiment reason must be null");
            if (status == FullDataModel.RecordStatus.AVAILABLE) require(nativeSupplyLossEligible != null && currentSoldiers != null
                    && maximumSoldiers != null, "available Province regiment is incomplete");
            if (replenishmentRecords != null) require(replenishmentRecords.armyRegimentId() == armyRegimentId,
                    "Province DATA identity differs");
            if (Boolean.FALSE.equals(nativeSupplyLossEligible)) require(replenishmentRecords == null,
                    "ineligible Province regiment has DATA");
        }
    }
    private static void reason(String reason) { require(reason == null || !reason.isEmpty(), "Province reason must be nonempty/null"); }
    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }
}
