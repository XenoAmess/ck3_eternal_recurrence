package org.xar.ck3.control.wave2.military.zerostockclock;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.landstock.LandStockModel.AvailableStock;
import org.xar.ck3.control.wave2.military.landstock.LandStockPolicy;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossModel.SupplyComponent;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossPolicy;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterAdmission;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterWriteProjection;
import org.xar.ck3.control.wave2.military.zerostockclock.ZeroStockModel.AvailableOpportunities;
import org.xar.ck3.control.wave2.military.zerostockclock.ZeroStockModel.Candidate;
import org.xar.ck3.control.wave2.military.zerostockclock.ZeroStockModel.Input;
import org.xar.ck3.control.wave2.military.zerostockclock.ZeroStockModel.Opportunities;
import org.xar.ck3.control.wave2.military.zerostockclock.ZeroStockModel.UnavailableOpportunities;
import org.xar.ck3.control.wave2.military.zerostockclock.ZeroStockModel.ZeroBudget;

/** Original clock/bucket/updater joins; never submits, cancels or advances an actual clock. */
public final class ZeroStockProjection {
    private ZeroStockProjection() { }

    public static Candidate projectNextCallbackCandidate(Input row) {
        var schedule = row.schedule(); var source = schedule == null ? null : schedule.sourceFrame();
        Boolean coherent = null;
        if (source != null && source.ready() && row.clock() != null && row.clock().ready()) {
            if (!(row.clock().currentDateRaw().equals(source.currentDateRawI32())
                    && row.clock().nativeDayIndex().equals(source.values().currentNativeDayIndexRawI32())))
                throw new org.xar.ck3.control.contracts.projection.ProjectionDomainRejection("zero-stock candidate clock differs from same-row native next seed");
            coherent = true;
        }
        var frames = schedule == null ? List.<org.xar.ck3.control.wave2.military.supplyschedule.FutureDailySupplyScheduleProjection.SelectedFrame>of()
                : schedule.scheduleProjection().prospectiveFrames();
        var selected = frames.size() == 1 && source != null && source.ready() ? frames.getFirst() : null;
        List<Integer> positions = selected != null && selected.conditionalBucketOccurrencesReady() ? selected.matchingPositions() : null;
        Integer count = positions == null ? null : positions.size();
        Boolean zero = row.stockRaw() == null ? null : row.stockRaw() == 0;
        UpdaterAdmission admission = UpdaterWriteProjection.project(row.updater()).nextAdmission();
        Boolean admitted = admission.ready() ? admission.admitted() : null;
        boolean typed = row.available() && row.armyId() != null && row.nativeCarmyId() != null;
        Boolean candidate = allKnown(typed, zero, count == null ? null : count > 0, admitted, coherent);
        Integer nextDate = selected == null ? null : selected.dateRawI32();
        Integer nextPhase = selected == null ? null : selected.selectedPhaseIndexI32();
        return new Candidate(candidate, zero, coherent, nextDate, selected == null ? null : selected.nativeDayIndexRawI32(),
                nextPhase, positions, admission, nextZeroBudget(row, coherent, count, positions, nextDate, nextPhase, admission));
    }

    private static ZeroBudget nextZeroBudget(Input row, Boolean coherent, Integer count, List<Integer> positions,
            Integer nextDate, Integer phase, UpdaterAdmission admission) {
        Draft result = new Draft(nextDate, phase, positions);
        if (Boolean.FALSE.equals(admission.admitted()) || Integer.valueOf(0).equals(count)) {
            result.positive = false; return result.finish();
        }
        if (!Boolean.TRUE.equals(admission.admitted())) result.missing.add("source_next_updater_admission");
        if (row.stockRaw() == null) result.missing.add("current_supply_raw");
        if (row.capacityRaw() == null) result.missing.add("current_supply_capacity_raw");
        if (row.monthlyRaw() == null) result.missing.add("current_supply_change_monthly_raw");
        if (!result.missing.isEmpty()) return result.finish();
        if (row.stockRaw() < 0 || row.capacityRaw() < 0) {
            result.missing.add("ordinary_nonnegative_stock_capacity"); return result.finish();
        }
        var stockResult = LandStockPolicy.projectStockAfterRate(BigInteger.valueOf(row.monthlyRaw()), row.stockRaw(), row.capacityRaw());
        if (!(stockResult instanceof AvailableStock post)) throw new IllegalStateException("validated stock inputs failed shared updater");
        result.post = post.raw(); result.wrapped = !BigInteger.valueOf(row.stockRaw()).add(BigInteger.valueOf(row.monthlyRaw()))
                .equals(BigInteger.valueOf(post.signed64Add()));
        result.firstZero = row.stockRaw() > 0 && post.raw() == 0;
        if (post.raw() != 0) { result.positive = false; return result.finish(); }
        var family = row.completeMonthlyFamily();
        if (family == null) { result.missing.add("complete_current_monthly_loss_budget_inputs_v1"); return result.finish(); }
        result.familyReached = true; result.modifierId = family.commanderSupplyModifierId();
        result.modifierRaw = family.supply().commanderSupplyModifierRaw();
        Boolean suppressed = family.admission().nativeFleetSupplyLossSuppressed();
        if (Boolean.TRUE.equals(suppressed)) {
            result.component = new SupplyComponent(null, null, null, true, 0, List.of()); result.positive = false; return result.finish();
        }
        if (suppressed == null) { result.missing.add("native_fleet_supply_loss_suppressed"); return result.finish(); }
        SupplyComponent component = MonthlyLossPolicy.deriveSupplyComponent(0, family.supply(), row.losses());
        if (component.baseFractionRaw() != null && component.baseFractionRaw() != 0
                && Boolean.TRUE.equals(family.supply().commanderValid()) && family.commanderSupplyModifierId() == null) {
            result.missing.add("current_Province_definition_supply_modifier_id"); return result.finish();
        }
        result.component = component; result.missing.addAll(component.missingInputs());
        result.positive = allKnown(coherent, count == null ? null : count > 0, admission.admitted(),
                component.ready() ? component.soldiers() > 0 : null);
        if (result.positive == null) {
            if (!Boolean.TRUE.equals(coherent)) result.missing.add("same_row_source_next_clock_seed");
            if (count == null) result.missing.add("source_next_selected_bucket_actual_positions");
        }
        return result.finish();
    }

    /** Count successful original callbacks for constant captured rate/cap; not calendar days. */
    public static Opportunities successfulOccurrencesToZero(Long stockRaw, Long capacityRaw, Long monthlyRaw) {
        List<String> missing = new ArrayList<>();
        if (stockRaw == null) missing.add("current_supply_raw");
        if (capacityRaw == null) missing.add("current_supply_capacity_raw");
        if (monthlyRaw == null) missing.add("current_supply_change_monthly_raw");
        if (!missing.isEmpty()) return new UnavailableOpportunities(missing);
        if (stockRaw < 0 || capacityRaw < 0) return new UnavailableOpportunities(List.of("nonnegative_actual_stock_and_capacity"));
        if (monthlyRaw >= 0) {
            if (capacityRaw != 0 && !(stockRaw == 0 && monthlyRaw == 0)) {
                return new UnavailableOpportunities(List.of("negative_rate_or_actual_zero_retaining_stock_capacity"));
            }
            return new AvailableOpportunities(stockRaw == 0 ? 0 : 1, 0);
        }
        BigInteger stock = BigInteger.valueOf(stockRaw); BigInteger loss = BigInteger.valueOf(monthlyRaw).negate();
        BigInteger afterOne = stock.subtract(loss).max(BigInteger.ZERO).min(BigInteger.valueOf(capacityRaw));
        BigInteger count = stockRaw == 0 ? BigInteger.ZERO : afterOne.signum() == 0 ? BigInteger.ONE
                : BigInteger.ONE.add(afterOne.add(loss).subtract(BigInteger.ONE).divide(loss));
        return new AvailableOpportunities(count.longValueExact(), afterOne.longValueExact());
    }

    private static Boolean allKnown(Boolean... values) {
        for (Boolean value : values) if (Boolean.FALSE.equals(value)) return false;
        for (Boolean value : values) if (value == null) return null;
        return true;
    }

    private static final class Draft {
        private final Integer date; private final Integer phase; private final List<Integer> positions;
        private final List<String> missing = new ArrayList<>();
        private Long post; private Boolean wrapped; private Boolean firstZero; private Boolean positive;
        private boolean familyReached; private Integer modifierId; private Long modifierRaw; private SupplyComponent component;
        private Draft(Integer date, Integer phase, List<Integer> positions) { this.date = date; this.phase = phase; this.positions = positions; }
        private ZeroBudget finish() {
            return new ZeroBudget(post, wrapped, firstZero, positive, date, phase, positions,
                    familyReached, modifierId, modifierRaw, component, missing);
        }
    }
}
