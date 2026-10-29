package org.xar.ck3.control.wave2.military.stocksupply;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel.FleetTick;
import org.xar.ck3.control.wave2.military.landstock.LandStockPolicy;

/** Conditional same-context Fleet rate; it never observes or invokes a future callback. */
public final class NextFleetRate {
    public enum Status { AVAILABLE, UNAVAILABLE, NOT_FLEET }
    public enum Branch {
        NATIVE_NOT_FLEET, FUTURE_FLEET_DATE, TERRAIN_NOT_GDBO, POSITIVE_TERRAIN772_MODIFIER,
        NONNEGATIVE_BASE_COMPONENT, NEGATIVE_BASE_ADJUSTED
    }
    public enum DivisionPath {
        NOT_NEGATIVE, FAST, WIDE_DIVISOR, DECOMPOSED, FLEET_ZERO_DIVISOR_POSITIVE_U32_MAX
    }
    public record Input(boolean rowAvailable, Integer armyId, Integer nativeCarmyId,
                        Long observedTotalRate, FleetTick tick) {}
    public record Result(Status status, boolean ready, Integer currentDateLow32,
                         Integer nextDateLow32, BigInteger raw, Boolean fleetDateAdmitted,
                         Branch branch, DivisionPath divisionPath, Long commanderDivisor,
                         Long observedTotalRate, List<String> missingInputs) {
        public Result {
            Objects.requireNonNull(status);
            missingInputs = List.copyOf(missingInputs);
        }
    }
    private NextFleetRate() {}

    public static Result project(Input input) {
        Objects.requireNonNull(input);
        List<String> missing = new ArrayList<>();
        if (!input.rowAvailable()) {
            return unavailable(input, List.of("available_same_query_strength"));
        }
        FleetTick tick = input.tick();
        if (tick == null) return unavailable(input, List.of("current_fleet_supply_tick_inputs_v1"));
        if (tick.subjectArmyId() != null && !tick.subjectArmyId().equals(input.armyId())) {
            throw new ProjectionDomainRejection("same-query fleet rate subject_army_id context differs");
        }
        if (tick.subjectCarmyId() != null && !tick.subjectCarmyId().equals(input.nativeCarmyId())) {
            throw new ProjectionDomainRejection("same-query fleet rate subject_carmy_id context differs");
        }
        if (Boolean.FALSE.equals(tick.nativeFleetBranchApplicable())) {
            return new Result(Status.NOT_FLEET, false, null, null, null, null,
                    Branch.NATIVE_NOT_FLEET, null, null, input.observedTotalRate(), List.of());
        }
        require(tick.nativeFleetBranchApplicable(), "native_fleet_branch_applicable", missing);
        require(tick.currentNativeDateLow32(), "current_native_date_low32", missing);
        require(tick.fleetDayRaw(), "fleet_day_raw", missing);
        require(tick.loadedFleetDaySentinelRaw(), "loaded_fleet_day_sentinel_raw", missing);
        if (!missing.isEmpty()) return unavailable(input, missing);
        int current = tick.currentNativeDateLow32();
        int next = current + 24;
        boolean admitted = tick.fleetDayRaw().equals(tick.loadedFleetDaySentinelRaw()) || tick.fleetDayRaw() <= next;
        if (!admitted) return available(input, current, next, BigInteger.ZERO, false,
                Branch.FUTURE_FLEET_DATE, null, null);
        require(tick.terrainMagic38Raw(), "terrain_magic_38_raw", missing);
        if (!missing.isEmpty()) return partial(input, current, next, true, missing);
        if (tick.terrainMagic38Raw() != 0x4744624FL) return available(input, current, next,
                BigInteger.ZERO, true, Branch.TERRAIN_NOT_GDBO, null, null);
        require(tick.terrainModifier772Id(), "terrain_modifier_772_id", missing);
        require(tick.terrainModifier772Raw(), "terrain_modifier_772_raw", missing);
        if (!missing.isEmpty()) return partial(input, current, next, true, missing);
        if (tick.terrainModifier772Raw() > 0) return available(input, current, next,
                BigInteger.ZERO, true, Branch.POSITIVE_TERRAIN772_MODIFIER, null, null);
        require(tick.loadedFleetLossRaw(), "loaded_fleet_loss_raw", missing);
        if (!missing.isEmpty()) return partial(input, current, next, true, missing);
        long component = -tick.loadedFleetLossRaw();
        if (component >= 0) return available(input, current, next, BigInteger.valueOf(component), true,
                Branch.NONNEGATIVE_BASE_COMPONENT, DivisionPath.NOT_NEGATIVE, null);
        require(tick.commanderModifier1a9Raw(), "commander_modifier_1a9_raw", missing);
        require(tick.loadedDivisorFloorRaw(), "loaded_divisor_floor_raw", missing);
        require(tick.loadedMaxLossRaw(), "loaded_max_loss_raw", missing);
        if (!missing.isEmpty()) return partial(input, current, next, true, missing);
        long divisor = Math.max(tick.loadedDivisorFloorRaw(), 100_000L + tick.commanderModifier1a9Raw());
        var division = LandStockPolicy.nativeFixedDivide(component, divisor);
        DivisionPath path = divisor == 0 ? DivisionPath.FLEET_ZERO_DIVISOR_POSITIVE_U32_MAX
                : DivisionPath.valueOf(division.path().name());
        BigInteger raw = division.value().max(BigInteger.valueOf(-tick.loadedMaxLossRaw()));
        return available(input, current, next, raw, true, Branch.NEGATIVE_BASE_ADJUSTED, path, divisor);
    }

    private static void require(Object value, String name, List<String> missing) {
        if (value == null) missing.add(name);
    }
    private static Result unavailable(Input input, List<String> missing) {
        return new Result(Status.UNAVAILABLE, false, null, null, null, null, null,
                null, null, input.observedTotalRate(), missing);
    }
    private static Result partial(Input input, int current, int next, boolean admitted, List<String> missing) {
        return new Result(Status.UNAVAILABLE, false, current, next, null, admitted, null,
                null, null, input.observedTotalRate(), missing);
    }
    private static Result available(Input input, int current, int next, BigInteger raw, boolean admitted,
                                    Branch branch, DivisionPath path, Long divisor) {
        return new Result(Status.AVAILABLE, true, current, next, raw, admitted, branch,
                path, divisor, input.observedTotalRate(), List.of());
    }
}
