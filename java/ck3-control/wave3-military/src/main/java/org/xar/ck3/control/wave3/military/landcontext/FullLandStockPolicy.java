package org.xar.ck3.control.wave3.military.landcontext;

import static org.xar.ck3.control.wave3.military.landcontext.FullLandStockProjection.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel.StockBasis;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyProjection;
import org.xar.ck3.control.wave2.military.landstock.LandStockModel;
import org.xar.ck3.control.wave2.military.landstock.LandStockPolicy;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterWriteProjection;

/** Exact LAND outer producer, composed with the actual shared updater, numeric kernel and Fleet getter. */
public final class FullLandStockPolicy {
    private FullLandStockPolicy() {}
    public static FullLandStockProjection project(FullLandStockInput input) {
        Objects.requireNonNull(input);
        var writes = UpdaterWriteProjection.project(input.updater());
        var admission = writes.nextAdmission();
        Boolean admitted = admission.admitted();
        Integer nextLow = writes.sourceNextDate() == null ? null : writes.sourceNextDate().nextDateRawI32();
        RateStage rate = new RateStage(admitted, false, null, null, null, null, null, List.of());
        StockStage stock = new StockStage(false, null, null, null, List.of());
        BudgetStage budget = new BudgetStage(admitted, admission.ready(), nextLow, false, null,
                BudgetBasis.CONDITIONAL_POST_UPDATER_STOCK, null, null, null, null, false, null, List.of());
        if (Boolean.FALSE.equals(admitted)) {
            rate = new RateStage(false, false, null, RateBasis.NOT_CALLED_REJECTED_UPDATER, null, null, null, List.of());
            stock = input.capturedStockRaw() == null
                    ? new StockStage(false, null, null, null, List.of("current_supply_raw"))
                    : new StockStage(true, input.capturedStockRaw(), null, ClampBranch.CAPTURED_STOCK_RETAINED_REJECTED_UPDATER, List.of());
            budget = new BudgetStage(false, admission.ready(), nextLow, false, null,
                    BudgetBasis.GETTER_NOT_CALLED_REJECTED_UPDATER, null, null, null, null, true, 0, List.of());
        } else if (Boolean.TRUE.equals(admitted)) {
            ProvinceContributors province = input.land().province();
            var missingRate = new ArrayList<String>();
            Integer usage = province == null ? null : province.nativeSupplyUsageSoldiers();
            Integer limit = province == null ? null : province.nativeSupplyLimitSoldiers();
            FullLandRateProjection fullRate = null;
            if (province == null) missingRate.add("current_province_supply_contributors_v1");
            else if (!province.currentUsageReady() || usage == null) missingRate.add("current_province_supply_contributors_v1.current_native_usage");
            else {
                fullRate = FullLandRatePolicy.project(input.land(), usage);
                missingRate.addAll(fullRate.missingInputs());
            }
            Long raw = fullRate != null && fullRate.numericResult() instanceof LandStockModel.AvailableRate available ? available.conditionalRate() : null;
            rate = new RateStage(true, raw != null, raw, raw == null ? null : RateBasis.SAME_QUERY_LAND_NUMERIC_KERNEL_AT_CAPTURED_NATIVE_USAGE,
                    usage, limit, fullRate, missingRate);
            if (raw != null) {
                LandStockModel.StockResult stockResult = LandStockPolicy.projectStockAfterRate(BigInteger.valueOf(raw), input.capturedStockRaw(), input.capturedCapacityRaw());
                if (stockResult instanceof LandStockModel.AvailableStock available) {
                    ClampBranch branch = switch (available.clampBranch()) {
                        case NEGATIVE_WRAPPED_ADD_TO_ZERO -> ClampBranch.NEGATIVE_WRAPPED_ADD_TO_ZERO;
                        case MIN_CHANGED_CAPTURED_CAPACITY -> ClampBranch.MIN_CHANGED_CAPTURED_CAPACITY;
                    };
                    stock = new StockStage(true, available.raw(), available.signed64Add(), branch, List.of());
                } else if (stockResult instanceof LandStockModel.MissingStock absent) {
                    stock = new StockStage(false, null, absent.signed64Add(), null, absent.missingInputs());
                }
            }
            var sharedBudget = FleetSupplyProjection.projectAtStock(input.fleet(), stock.raw(), StockBasis.CONDITIONAL_POST_UPDATER_STOCK);
            budget = new BudgetStage(true, admission.ready(), nextLow, sharedBudget.fleetDatePredicateReady(),
                    sharedBudget.conditionalNativeFleetSupplyLossSuppressed(), BudgetBasis.CONDITIONAL_POST_UPDATER_STOCK,
                    stock.raw(), sharedBudget.heldStockStateIndex(), sharedBudget.supplyBaseFractionRaw(), sharedBudget.supplyEffectiveFractionRaw(),
                    sharedBudget.ready(), sharedBudget.conditionalSupplyBudgetSoldiers(), sharedBudget.missingInputs());
        }
        var missing = new LinkedHashSet<>(writes.missingInputs());
        missing.addAll(rate.missingInputs()); missing.addAll(stock.missingInputs()); missing.addAll(budget.missingInputs());
        boolean ready = writes.ready() && admission.ready() && stock.ready() && budget.ready()
                && (Boolean.FALSE.equals(admitted) || rate.ready());
        Status status = ready ? Status.AVAILABLE : input.land().available() ? Status.PARTIAL : Status.UNAVAILABLE;
        return new FullLandStockProjection(status, ready, List.copyOf(missing), input, writes, rate, stock, budget);
    }
}
