package org.xar.ck3.control.wave2.military.zerostockclock;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossModel.BudgetInputs;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossModel.LossInputs;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossModel.SupplyComponent;
import org.xar.ck3.control.wave2.military.supplyschedule.NativeNextDailySupplySchedule;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterAdmission;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterInput;

/** Capture-window forecasts are separate from writer observations and actual calendar progression. */
public final class ZeroStockModel {
    private ZeroStockModel() { }
    public record Input(boolean available, Integer armyId, Integer nativeCarmyId, Long stockRaw, Long capacityRaw,
            Long monthlyRaw, ArmyUpdateClock clock, NativeNextDailySupplySchedule schedule, UpdaterInput updater,
            BudgetInputs completeMonthlyFamily, LossInputs losses) {
        public Input {
            Objects.requireNonNull(updater); Objects.requireNonNull(losses);
            StrictJson.require(Objects.equals(armyId, updater.armyId()) && Objects.equals(nativeCarmyId, updater.nativeCarmyId())
                    && available == updater.rowAvailable(), "zero stock updater belongs to another row");
            if (schedule != null) {
                var observed = schedule.scheduleProjection().observedSchedule();
                StrictJson.require(armyId == null || observed.subjectArmyIdU32() == null
                        || observed.subjectArmyIdU32() == Integer.toUnsignedLong(armyId), "zero stock schedule army differs");
                StrictJson.require(nativeCarmyId == null || observed.subjectCarmyIdU32() == null
                        || observed.subjectCarmyIdU32() == Integer.toUnsignedLong(nativeCarmyId), "zero stock schedule CArmy differs");
                StrictJson.require(Objects.equals(schedule.sourceFrame(), updater.sourceNextDate()),
                        "zero stock schedule and updater source frames differ");
            }
        }
    }
    public record Candidate(Boolean conditionalZeroEntryCaptureCandidate, Boolean observedCurrentStockIsExactZero,
            Boolean sameRowClockSeedMatches, Integer nextDateRawI32, Integer nextNativeDayIndexRawI32,
            Integer nextSelectedPhaseI32, List<Integer> conditionalOriginalPointerPositions,
            UpdaterAdmission nextAdmission, ZeroBudget conditionalNextZeroSupplyBudget) {
        public Candidate {
            if (conditionalOriginalPointerPositions != null) conditionalOriginalPointerPositions = List.copyOf(conditionalOriginalPointerPositions);
            Objects.requireNonNull(nextAdmission); Objects.requireNonNull(conditionalNextZeroSupplyBudget);
        }
        public Integer conditionalCallbackOpportunityCount() {
            return conditionalOriginalPointerPositions == null ? null : conditionalOriginalPointerPositions.size();
        }
    }
    public record ZeroBudget(Long conditionalPostSupplyRaw, Boolean nativeAddOverflowWrapped,
            Boolean firstReachesZeroInThisConditionalCallback, Boolean conditionalPositiveBudgetCaptureCandidate,
            Integer nextDateRawI32, Integer nextSelectedPhaseI32, List<Integer> originalPointerPositions,
            boolean completeFamilyReached, Integer currentSupplyFractionModifierId, Long currentSupplyFractionModifierRaw,
            SupplyComponent component, List<String> missingInputs) {
        public ZeroBudget {
            if (originalPointerPositions != null) originalPointerPositions = List.copyOf(originalPointerPositions);
            missingInputs = List.copyOf(missingInputs);
            StrictJson.require((conditionalPostSupplyRaw != null) == (nativeAddOverflowWrapped != null)
                    && (conditionalPostSupplyRaw != null) == (firstReachesZeroInThisConditionalCallback != null),
                    "post-stock branch presence differs");
        }
        public boolean postSupplyReady() { return conditionalPostSupplyRaw != null; }
        public boolean supplyBudgetReady() { return component != null && component.ready(); }
        public Integer supplyBudgetSoldiers() { return component == null ? null : component.soldiers(); }
        public Integer candidateFirstOriginalPointerPosition() {
            return originalPointerPositions == null || originalPointerPositions.isEmpty() ? null : originalPointerPositions.getFirst();
        }
    }
    public sealed interface Opportunities permits UnavailableOpportunities, AvailableOpportunities { boolean ready(); }
    public record UnavailableOpportunities(List<String> requiredFields) implements Opportunities {
        public UnavailableOpportunities { requiredFields = List.copyOf(requiredFields); }
        @Override public boolean ready() { return false; }
    }
    public record AvailableOpportunities(long successfulBucketOccurrences, long firstSuccessfulPostStockRaw) implements Opportunities {
        public AvailableOpportunities {
            StrictJson.require(successfulBucketOccurrences >= 0 && firstSuccessfulPostStockRaw >= 0, "zero-stock estimate outside nonnegative domain");
        }
        @Override public boolean ready() { return true; }
        public long firstNewZeroWriterOpportunity() { return Math.max(1, successfulBucketOccurrences); }
    }
}
