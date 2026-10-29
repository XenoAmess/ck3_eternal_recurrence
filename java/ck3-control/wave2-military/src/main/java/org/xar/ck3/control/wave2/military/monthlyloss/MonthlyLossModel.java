package org.xar.ck3.control.wave2.military.monthlyloss;

import java.util.List;
import java.util.Objects;

/** Immutable operands for the source-bound 1.20.0.3 caller budget kernel. */
public final class MonthlyLossModel {
    private MonthlyLossModel() {}

    public enum Availability { AVAILABLE, UNAVAILABLE }
    public enum Status { AVAILABLE, PARTIAL, UNAVAILABLE }

    /** Null vectors are unknown; empty vectors are known and meaningful. */
    public record SupplyInputs(List<Integer> loadedSupplyStateLevels,
                               List<Long> loadedSupplyStateFractionsRaw,
                               Boolean commanderValid, Long commanderSupplyModifierRaw) {
        public SupplyInputs {
            loadedSupplyStateLevels = copyNullable(loadedSupplyStateLevels);
            loadedSupplyStateFractionsRaw = copyNullable(loadedSupplyStateFractionsRaw);
        }
    }

    public record LossInputs(Integer supplyEligibleSoldiers, Integer currentSupplyLossBudget,
                             Integer wholeSoldiers, Boolean siegeActive, Boolean raidActive,
                             Long siegeRateRaw, Long raidRateRaw) {
        public LossInputs(Integer supplyEligibleSoldiers, Integer currentSupplyLossBudget) {
            this(supplyEligibleSoldiers, currentSupplyLossBudget, null, null, null, null, null);
        }
    }

    public record AdmissionInputs(Integer unitNative170Raw, Boolean nativeUnitInCombat,
                                  Boolean nativeUnitGathering, Integer armyGatheringCountRaw,
                                  Boolean nativeFleetSupplyLossSuppressed) {}
    public record ClockInputs(Integer currentDateRaw, Integer graceAnchorDateRaw, Integer loadedGraceDays) {}

    /** Exact native family, including its independent publication readiness. */
    public record BudgetInputs(Availability status, boolean ready, String unavailableReason,
                               AdmissionInputs admission, SupplyInputs supply,
                               Integer commanderSupplyModifierId) {
        public BudgetInputs {
            Objects.requireNonNull(status, "status");
            Objects.requireNonNull(admission, "admission");
            Objects.requireNonNull(supply, "supply");
            require(ready == (status == Availability.AVAILABLE), "family status/readiness disagree");
            require(ready ? unavailableReason == null : unavailableReason != null && !unavailableReason.isEmpty(),
                    "family reason/readiness disagree");
            require(commanderSupplyModifierId == null || commanderSupplyModifierId >= 0
                    && commanderSupplyModifierId <= 65_535, "modifier ID must be uint16");
            require(!Boolean.FALSE.equals(supply.commanderValid()) || commanderSupplyModifierId == null
                    && supply.commanderSupplyModifierRaw() == null, "invalid commander cannot publish modifier operands");
            require(!ready || admission.unitNative170Raw() != null && admission.nativeUnitInCombat() != null
                    && admission.nativeUnitGathering() != null && admission.armyGatheringCountRaw() != null
                    && admission.nativeFleetSupplyLossSuppressed() != null
                    && supply.loadedSupplyStateLevels() != null && supply.loadedSupplyStateFractionsRaw() != null
                    && supply.commanderValid() != null && (!supply.commanderValid()
                    || commanderSupplyModifierId != null && supply.commanderSupplyModifierRaw() != null),
                    "ready native family is incomplete");
        }
    }

    /** A declared projection of a larger SDK army row; unrelated extensions stay outside this model. */
    public record Input(boolean available, AdmissionInputs admission, SupplyInputs supply, LossInputs losses,
                        ClockInputs clock, Long currentSupplyRaw, Long currentSupplyChangeMonthlyRaw,
                        Long currentSupplyCapacityRaw) {
        public Input {
            Objects.requireNonNull(admission, "admission"); Objects.requireNonNull(supply, "supply");
            Objects.requireNonNull(losses, "losses"); Objects.requireNonNull(clock, "clock");
        }
    }

    public record SupplyComponent(Integer stateIndex, Long baseFractionRaw, Long effectiveFractionRaw,
                                  boolean ready, Integer soldiers, List<String> missingInputs) {
        public SupplyComponent { missingInputs = List.copyOf(missingInputs); }
    }

    public record StockState(Integer stockInteger, Integer stateIndex, Long baseFractionRaw,
                             boolean ready, List<String> missingInputs) {
        public StockState { missingInputs = List.copyOf(missingInputs); }
    }

    /** Supply-only seam; independent siege/raid readiness never gates this computation. */
    public record SupplyEntry(Boolean admitted, List<AdmissionWitness> witnesses, String rejection,
                              Long postStockRaw, boolean postStockReady, SupplyComponent component,
                              List<String> missingInputs) {
        public SupplyEntry { witnesses = List.copyOf(witnesses); Objects.requireNonNull(component); missingInputs = List.copyOf(missingInputs); }
        public boolean ready() { return admitted != null && postStockReady && component.ready(); }
    }

    public sealed interface GateValue permits IntegerValue, BooleanValue, MissingValue {}
    public record IntegerValue(int value) implements GateValue {}
    public record BooleanValue(boolean value) implements GateValue {}
    public record MissingValue() implements GateValue {}
    public sealed interface AdmissionWitness permits GateWitness, GraceWitness {}
    public record GateWitness(String input, GateValue value, Boolean passed) implements AdmissionWitness {
        public GateWitness { Objects.requireNonNull(input); Objects.requireNonNull(value); }
    }
    public record GraceWitness(int elapsedDateRaw, int elapsedDays, int loadedGraceDays,
                               boolean passed) implements AdmissionWitness {}

    /** Typed downstream operands, not a physical-writer result or a native observation. */
    public record LossSequenceSeed(int currentSupplyLossBudget, int siegeLossBudget, int raidLossBudget) {}

    public record Result(Status status, boolean conditionalBudgetsReady, Integer currentReadonlySupplyLossBudget,
                         Boolean supplyUpdaterAdmitted, List<AdmissionWitness> admissionWitnesses,
                         String admissionRejection, Long conditionalPostSupplyRaw, boolean postSupplyReady,
                         SupplyComponent supplyComponent, Integer siegeBudgetSoldiers, boolean siegeBudgetReady,
                         Integer raidBudgetSoldiers, boolean raidBudgetReady, Integer combinedSiegeRaidBudgetSoldiers,
                         LossSequenceSeed lossSequenceSeed, List<String> missingInputs) {
        public Result {
            Objects.requireNonNull(status); Objects.requireNonNull(supplyComponent);
            admissionWitnesses = List.copyOf(admissionWitnesses); missingInputs = List.copyOf(missingInputs);
        }
        public boolean admissionReady() { return supplyUpdaterAdmitted != null; }
    }

    private static <T> List<T> copyNullable(List<T> values) { return values == null ? null : List.copyOf(values); }
    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }
}
