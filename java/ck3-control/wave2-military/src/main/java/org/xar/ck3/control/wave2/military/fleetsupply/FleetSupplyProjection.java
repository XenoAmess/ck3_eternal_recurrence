package org.xar.ck3.control.wave2.military.fleetsupply;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel.ArmyBudget;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel.ArmyRow;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel.BudgetStatus;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel.FleetSupplyBudget;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel.FleetTick;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel.StockBasis;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossModel.SupplyComponent;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossPolicy;

/** One direct 24E32C0 getter; no updater, physical loss, future observation or authority. */
public final class FleetSupplyProjection {
    private FleetSupplyProjection() { }

    public static FleetSupplyBudget project(ArmyRow row) {
        return projectAtStock(row, row.currentSupplyRaw(), StockBasis.CAPTURED_CURRENT_STOCK_UNCHANGED);
    }

    public static FleetSupplyBudget projectAtStock(ArmyRow row, Long supplyStockRaw, StockBasis basis) {
        Objects.requireNonNull(row); Objects.requireNonNull(basis);
        FleetTick tick = row.fleetTick();
        Integer nextDate = row.nextFrame() == null ? null : row.nextFrame().nextDateRawI32();
        Boolean branch = tick == null ? null : tick.nativeFleetBranchApplicable();
        Integer fleetDay = tick == null ? null : tick.fleetDayRaw();
        Integer sentinel = tick == null ? null : tick.loadedFleetDaySentinelRaw();
        List<String> missing = new ArrayList<>();
        if (!"available".equals(row.status()) || row.nativeCarmyId() == null) {
            missing.add("available_typed_army_row");
            return result(row, basis, BudgetStatus.UNAVAILABLE, false, null, false, null, null, null, false, null, missing);
        }
        if (tick == null) {
            missing.add("current_fleet_supply_tick_inputs_v1");
            return result(row, basis, BudgetStatus.UNAVAILABLE, false, null, false, null, null, null, false, null, missing);
        }
        if (tick.subjectArmyId() != null && !tick.subjectArmyId().equals(row.armyId())) {
            throw new ProjectionDomainRejection("same-query next supply budget subject_army_id differs");
        }
        if (tick.subjectCarmyId() != null && !tick.subjectCarmyId().equals(row.nativeCarmyId())) {
            throw new ProjectionDomainRejection("same-query next supply budget subject_carmy_id differs");
        }
        if (branch == null) {
            missing.add("current_fleet_supply_tick_inputs_v1.native_fleet_branch_applicable");
            return result(row, basis, BudgetStatus.UNAVAILABLE, false, null, false, null, null, null, false, null, missing);
        }
        boolean suppressed = false;
        boolean globalUsed = false;
        if (branch) {
            if (fleetDay == null) missing.add("current_fleet_supply_tick_inputs_v1.fleet_day_raw");
            if (sentinel == null) missing.add("current_fleet_supply_tick_inputs_v1.loaded_fleet_day_sentinel_raw");
            if (!missing.isEmpty()) {
                return result(row, basis, BudgetStatus.UNAVAILABLE, false, null, false, null, null, null, false, null, missing);
            }
            if (!fleetDay.equals(sentinel)) {
                if (nextDate == null) {
                    missing.add("source_derived_next_daily_supply_frame_inputs_v1.source_derived_next_date_raw_i32");
                    return result(row, basis, BudgetStatus.UNAVAILABLE, false, null, false, null, null, null, false, null, missing);
                }
                globalUsed = true;
                suppressed = fleetDay > nextDate;
            }
        }
        if (suppressed) {
            return result(row, basis, BudgetStatus.AVAILABLE, true, true, globalUsed, null, null, null, true, 0, List.of());
        }
        if (supplyStockRaw == null) {
            return result(row, basis, BudgetStatus.PARTIAL, true, false, globalUsed, null, null, null, false, null,
                    List.of(basis.stockInputName()));
        }
        SupplyComponent component = MonthlyLossPolicy.deriveSupplyComponent(supplyStockRaw, row.supplyInputs(), row.lossInputs());
        return result(row, basis, component.ready() ? BudgetStatus.AVAILABLE : BudgetStatus.PARTIAL,
                true, false, globalUsed, component.stateIndex(), component.baseFractionRaw(), component.effectiveFractionRaw(),
                component.ready(), component.soldiers(), component.missingInputs().stream().distinct().toList());
    }

    /** The service's selected-row join; preserves order, duplicates and unavailable rows. */
    public static List<ArmyBudget> projectServiceRows(List<ArmyRow> selectedRows) {
        return selectedRows.stream().map(row -> new ArmyBudget(row.armyId(), project(row))).toList();
    }

    private static FleetSupplyBudget result(ArmyRow row, StockBasis basis, BudgetStatus status,
            boolean predicateReady, Boolean suppressed, boolean globalUsed, Integer index, Long base, Long effective,
            boolean ready, Integer soldiers, List<String> missing) {
        FleetTick tick = row.fleetTick();
        return new FleetSupplyBudget(status, row.armyId(), row.nativeCarmyId(), basis, row.currentSupplyRaw(),
                row.observedSuppressed(), row.observedBudget(), row.nextFrame(),
                row.nextFrame() == null ? null : row.nextFrame().nextDateRawI32(),
                tick == null ? null : tick.nativeFleetBranchApplicable(), tick == null ? null : tick.fleetDayRaw(),
                tick == null ? null : tick.loadedFleetDaySentinelRaw(), predicateReady, suppressed, globalUsed,
                index, base, effective, ready, soldiers, missing);
    }
}
