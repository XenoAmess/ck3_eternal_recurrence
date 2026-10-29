package org.xar.ck3.control.wave2.military.fleetsupply;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossModel.LossInputs;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossModel.SupplyInputs;
import org.xar.ck3.control.wave2.military.updaterwrites.SourceNextFrame;

/** Same-query conditional inputs; none of these models grants future execution qualification. */
public final class FleetSupplyModel {
    private FleetSupplyModel() { }

    public enum TickStatus { AVAILABLE, UNAVAILABLE, NOT_FLEET }

    public record FleetTick(
            TickStatus status, boolean ready, String unavailableReason,
            Integer subjectArmyId, Integer subjectCarmyId, Integer provinceId,
            Integer currentNativeDateLow32, Integer fleetRawFullId, Integer fleetResolvedFullId,
            Integer fleetDayRaw, Integer loadedFleetDaySentinelRaw,
            Integer commanderRawFullId, Integer commanderResolvedFullId,
            Long terrainModifier772Raw, Long loadedFleetLossRaw, Long commanderModifier1a9Raw,
            Long loadedDivisorFloorRaw, Long loadedMaxLossRaw,
            Boolean nativeFleetBranchApplicable, Boolean fleetUsedNativeFallback,
            Boolean commanderUsedNativeFallback, Long terrainMagic38Raw, Integer terrainModifier772Id) {
        public FleetTick {
            Objects.requireNonNull(status);
            require(ready == (status != TickStatus.UNAVAILABLE), "fleet tick readiness disagrees with status");
            require(ready ? unavailableReason == null : unavailableReason != null && !unavailableReason.isEmpty(),
                    "fleet tick reason disagrees with readiness");
            require(terrainMagic38Raw == null || terrainMagic38Raw >= 0 && terrainMagic38Raw <= 0xffff_ffffL,
                    "fleet terrain magic outside uint32");
            require(terrainModifier772Id == null || terrainModifier772Id >= 0 && terrainModifier772Id <= 0xffff,
                    "fleet terrain modifier ID outside uint16");
            if (ready) {
                require(subjectArmyId != null && subjectCarmyId != null && provinceId != null
                        && nativeFleetBranchApplicable != null, "ready fleet tick subject incomplete");
                if (status == TickStatus.NOT_FLEET) {
                    require(Boolean.FALSE.equals(nativeFleetBranchApplicable), "not_fleet requires false native branch");
                } else {
                    require(Boolean.TRUE.equals(nativeFleetBranchApplicable), "available fleet tick requires true branch");
                    require(currentNativeDateLow32 != null && fleetRawFullId != null && fleetResolvedFullId != null
                            && fleetUsedNativeFallback != null && fleetDayRaw != null
                            && loadedFleetDaySentinelRaw != null && terrainMagic38Raw != null,
                            "ready fleet tick operands incomplete");
                    if (terrainMagic38Raw == 0x4744_624fL) {
                        require(terrainModifier772Id != null && terrainModifier772Raw != null
                                && commanderRawFullId != null && commanderResolvedFullId != null
                                && commanderUsedNativeFallback != null, "ready fleet terrain operands incomplete");
                        if (terrainModifier772Raw <= 0) {
                            require(loadedFleetLossRaw != null, "ready fleet loss missing");
                            if (loadedFleetLossRaw > 0 || loadedFleetLossRaw == Long.MIN_VALUE) {
                                require(commanderModifier1a9Raw != null && loadedDivisorFloorRaw != null
                                        && loadedMaxLossRaw != null, "ready fleet divisor operands incomplete");
                            }
                        }
                    }
                }
            }
        }
    }

    public enum StockBasis {
        CAPTURED_CURRENT_STOCK_UNCHANGED("captured_current_stock_unchanged", false, "current_supply_raw"),
        CONDITIONAL_POST_UPDATER_STOCK("conditional_post_updater_stock", true, "conditional_post_updater_stock_raw");
        private final String wire;
        private final boolean postUpdater;
        private final String inputName;
        StockBasis(String wire, boolean postUpdater, String inputName) {
            this.wire = wire; this.postUpdater = postUpdater; this.inputName = inputName;
        }
        public String wire() { return wire; }
        public boolean postUpdaterStockUsed() { return postUpdater; }
        public String stockInputName() { return inputName; }
    }

    public enum BudgetStatus { AVAILABLE, PARTIAL, UNAVAILABLE }

    public record ArmyRow(String status, Integer armyId, Integer nativeCarmyId, Long currentSupplyRaw,
                          FleetTick fleetTick, SourceNextFrame nextFrame, SupplyInputs supplyInputs,
                          LossInputs lossInputs, Boolean observedSuppressed, Integer observedBudget) {
        public ArmyRow {
            Objects.requireNonNull(supplyInputs); Objects.requireNonNull(lossInputs);
            if (nextFrame != null) {
                require(nextFrame.subjectArmyIdU32() == null || armyId == null
                        || nextFrame.subjectArmyIdU32() == Integer.toUnsignedLong(armyId),
                        "source-next subject differs from same-query army ID");
                require(nextFrame.subjectCarmyIdU32() == null || nativeCarmyId == null
                        || nextFrame.subjectCarmyIdU32() == Integer.toUnsignedLong(nativeCarmyId),
                        "source-next subject differs from same-query native CArmy ID");
            }
        }
    }

    public record FleetSupplyBudget(
            BudgetStatus status, Integer armyId, Integer nativeCarmyId, StockBasis stockBasis,
            Long heldCurrentSupplyStockRaw, Boolean observedCurrentNativeFleetSupplyLossSuppressed,
            Integer observedCurrentSupplyLossBudgetSoldiers, SourceNextFrame sourceNextGlobalClock,
            Integer sourceNextGlobalDateRawI32, Boolean nativeFleetBranchApplicable,
            Integer fleetDayRawI32, Integer loadedFleetDaySentinelRawI32,
            boolean fleetDatePredicateReady, Boolean conditionalNativeFleetSupplyLossSuppressed,
            boolean globalDateOperandUsed, Integer heldStockStateIndex,
            Long supplyBaseFractionRaw, Long supplyEffectiveFractionRaw,
            boolean ready, Integer conditionalSupplyBudgetSoldiers, List<String> missingInputs) {
        public FleetSupplyBudget {
            Objects.requireNonNull(status); Objects.requireNonNull(stockBasis);
            missingInputs = List.copyOf(missingInputs);
            require(ready == (conditionalSupplyBudgetSoldiers != null), "budget readiness disagrees with soldiers");
            require(ready == (status == BudgetStatus.AVAILABLE), "budget readiness disagrees with status");
            require(fleetDatePredicateReady == (conditionalNativeFleetSupplyLossSuppressed != null),
                    "fleet predicate readiness disagrees with result");
            require(!ready || fleetDatePredicateReady, "budget requires evaluated fleet predicate");
            require(!globalDateOperandUsed || sourceNextGlobalDateRawI32 != null && Boolean.TRUE.equals(nativeFleetBranchApplicable),
                    "fleet date comparison requires explicit operands");
            require(!Boolean.TRUE.equals(conditionalNativeFleetSupplyLossSuppressed)
                    || ready && conditionalSupplyBudgetSoldiers == 0, "suppressed budget must be ready zero");
            require(sourceNextGlobalDateRawI32 == null ? sourceNextGlobalClock == null
                    || sourceNextGlobalClock.nextDateRawI32() == null
                    : sourceNextGlobalClock != null && sourceNextGlobalDateRawI32.equals(sourceNextGlobalClock.nextDateRawI32()),
                    "budget next date differs from preserved source clock");
        }
        public boolean conditionalSupplyBudgetReady() { return ready; }
        public boolean postUpdaterStockUsed() { return stockBasis.postUpdaterStockUsed(); }
        public boolean sourceNextGlobalDateReady() { return sourceNextGlobalDateRawI32 != null; }
    }

    public record ArmyBudget(Integer armyId, FleetSupplyBudget projection) {
        public ArmyBudget { Objects.requireNonNull(projection); }
    }

    private static void require(boolean condition, String message) {
        org.xar.ck3.control.contracts.StrictJson.require(condition, message);
    }
}
