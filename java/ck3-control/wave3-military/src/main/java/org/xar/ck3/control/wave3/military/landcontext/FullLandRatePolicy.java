package org.xar.ck3.control.wave3.military.landcontext;

import java.util.ArrayList;
import java.util.Objects;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.wave2.military.landstock.LandStockModel;
import org.xar.ck3.control.wave2.military.landstock.LandStockPolicy;

/** Exact same-query wrapper; all numeric operations belong to the shared LandStock kernel. */
public final class FullLandRatePolicy {
    private FullLandRatePolicy() {}
    public static FullLandRateProjection project(LandContextRow row, int selectedRefillUsageSoldiers) {
        Objects.requireNonNull(row);
        var missing = new ArrayList<String>();
        if (!row.available()) missing.add("available_same_query_strength");
        if (row.rateInputs() == null || !row.rateInputs().currentObservationReady()) missing.add("current_land_supply_rate_inputs_v1");
        if (row.resupply() == null || !row.resupply().currentObservationReady()) missing.add("current_land_resupply_v1");
        if (row.province() == null || row.province().nativeSupplyLimitSoldiers() == null) missing.add("current_province_native_limit");
        if (!missing.isEmpty()) return new FullLandRateProjection(selectedRefillUsageSoldiers,
                row.currentObservedTotalRateRaw(), null, missing);
        LandRateInputs rate = row.rateInputs();
        LandResupply gain = row.resupply();
        ProvinceContributors province = row.province();
        require(Objects.equals(rate.provinceId(), gain.provinceId()) && Objects.equals(rate.provinceId(), province.provinceId()), "same-query land rate province_id context differs");
        require(Objects.equals(rate.ownerCharacterId(), gain.ownerCharacterId()) && Objects.equals(rate.ownerCharacterId(), province.ownerCharacterId()), "same-query land rate owner_character_id context differs");
        require(Objects.equals(rate.subjectArmyId(), province.subjectArmyId()) && Objects.equals(rate.subjectArmyId(), row.armyId()), "same-query land rate subject_army_id context differs");
        require(Objects.equals(rate.subjectCarmyId(), province.subjectCarmyId()) && Objects.equals(rate.subjectCarmyId(), row.nativeCarmyId()), "same-query land rate subject_carmy_id context differs");
        LandStockModel.RateResult result = LandStockPolicy.projectRate(new LandStockModel.RateInput(
                (long) selectedRefillUsageSoldiers, province.nativeSupplyLimitSoldiers().longValue(),
                rate.provinceComponentRaw(), gain.nativeResupplyEligible(), gain.loadedGainRaw(),
                rate.loadedExcessSlopeRaw(), rate.loadedMinLossRaw(), rate.loadedMaxLossRaw(),
                rate.loadedDivisorFloorRaw(), rate.commanderModifier1a9Raw()));
        return new FullLandRateProjection(selectedRefillUsageSoldiers, row.currentObservedTotalRateRaw(), result, result.missingInputs());
    }
    private static void require(boolean condition, String message) { if (!condition) throw new ProjectionDomainRejection(message); }
}
