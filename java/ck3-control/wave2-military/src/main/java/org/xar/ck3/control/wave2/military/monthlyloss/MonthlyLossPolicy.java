package org.xar.ck3.control.wave2.military.monthlyloss;

import static org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossModel.*;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.wave2.military.landstock.LandStockPolicy;

/** Pure pre-write budget computation. No updater, physical writer, Game or ledger call. */
public final class MonthlyLossPolicy {
    public static final int SCALE = 100_000;
    private MonthlyLossPolicy() {}

    /** Explicit stock is isolated from the captured row; shared by both fleet and LAND projections. */
    public static SupplyComponent deriveSupplyComponent(long stock, SupplyInputs inputs, LossInputs losses) {
        Objects.requireNonNull(inputs); Objects.requireNonNull(losses);
        StockState state = projectStockState(stock, inputs);
        Integer index = state.stateIndex(); Long knownBase = state.baseFractionRaw();
        if (!state.ready()) return new SupplyComponent(index, knownBase, null, false, null, state.missingInputs());
        long base = knownBase;
        long effective;
        if (base == 0) effective = 0;
        else if (Boolean.FALSE.equals(inputs.commanderValid())) effective = base;
        else if (Boolean.TRUE.equals(inputs.commanderValid())) {
            Long modifier = inputs.commanderSupplyModifierRaw();
            if (modifier == null) return component(index, base, null, null, "commander_supply_modifier_raw");
            effective = Math.min(SCALE, Math.max(0, LandStockPolicy.nativeFixedMultiply(base, SCALE + modifier)));
        } else return component(index, base, null, null, "commander_valid");
        if (effective <= 0) return component(index, base, effective, 0, null);
        if (losses.supplyEligibleSoldiers() == null) {
            return component(index, base, effective, null, "supply_eligible_soldiers");
        }
        return component(index, base, effective, wholeBudget(losses.supplyEligibleSoldiers(), effective), null);
    }

    /** One threshold/base computation shared by the getter and current callback risk wrapper. */
    public static StockState projectStockState(Long stock, SupplyInputs inputs) {
        Objects.requireNonNull(inputs);
        if (stock == null) return new StockState(null, null, null, false, List.of("current_or_conditional_supply_raw"));
        List<Integer> levels = inputs.loadedSupplyStateLevels();
        if (levels == null) return new StockState(null, null, null, false, List.of("loaded_supply_state_levels"));
        int stockInteger = (int) (stock / SCALE);
        int index = levels.size() - 1;
        for (int ordinal = 0; ordinal < levels.size(); ordinal++) {
            if (stockInteger >= levels.get(ordinal)) { index = ordinal; break; }
        }
        long base = 0;
        if (index >= 0) {
            List<Long> fractions = inputs.loadedSupplyStateFractionsRaw();
            if (fractions == null) return new StockState(stockInteger, index, null, false, List.of("loaded_supply_state_fractions_raw"));
            if (index < fractions.size()) base = fractions.get(index);
        }
        return new StockState(stockInteger, index, base, true, List.of());
    }

    /** Multiplication wraps low64, quotient truncates toward zero, then stores signed32. */
    public static int wholeBudget(int count, long fraction) {
        return Math.min(count, (int) ((count * fraction) / SCALE));
    }

    public static Result constructConditionalMonthlyLossBudgets(Input input) {
        Objects.requireNonNull(input);
        if (!input.available()) return new Result(Status.UNAVAILABLE, false, null, null, List.of(), null,
                null, false, component(null, null, null, null, null), null, false, null, false,
                null, null, List.of("available_same_query_army_strength"));
        List<String> missing = new ArrayList<>();
        LossInputs losses = input.losses();
        Integer siege = independentBudget("siege", losses.siegeActive(), losses.wholeSoldiers(), losses.siegeRateRaw(), missing);
        Integer raid = independentBudget("raid", losses.raidActive(), losses.wholeSoldiers(), losses.raidRateRaw(), missing);
        Integer combined = siege != null && raid != null ? siege + raid : null;
        SupplyEntry entry = projectSupplyEntry(input);
        SupplyComponent supply = entry.component(); missing.addAll(entry.missingInputs());
        boolean ready = supply.ready() && siege != null && raid != null;
        Status status = ready ? Status.AVAILABLE : supply.ready() || siege != null || raid != null
                || entry.admitted() != null ? Status.PARTIAL : Status.UNAVAILABLE;
        LossSequenceSeed seed = ready ? new LossSequenceSeed(supply.soldiers(), siege, raid) : null;
        return new Result(status, ready, losses.currentSupplyLossBudget(), entry.admitted(), entry.witnesses(),
                entry.rejection(), entry.postStockRaw(), entry.postStockReady(), supply, siege, siege != null, raid, raid != null,
                combined, seed, List.copyOf(new LinkedHashSet<>(missing)));
    }

    /** Complete supply-only entry. Known rejection need not validate or invent later operands. */
    public static SupplyEntry projectSupplyEntry(Input input) {
        Objects.requireNonNull(input);
        if (!input.available()) return new SupplyEntry(null, List.of(), null, null, false,
                component(null, null, null, null, null), List.of("available_same_query_army_strength"));
        List<String> missing = new ArrayList<>();
        Admission admission = admission(input.admission(), input.clock(), missing);
        Long post = null;
        SupplyComponent supply = component(null, null, null, null, null);
        if (Boolean.FALSE.equals(admission.admitted())) {
            post = input.currentSupplyRaw();
            supply = component(null, null, null, 0, null);
        } else if (Boolean.TRUE.equals(admission.admitted())) {
            Long stock = input.currentSupplyRaw(), rate = input.currentSupplyChangeMonthlyRaw();
            if (stock != null && rate != null) {
                long changed = stock + rate;
                if (changed < 0) post = 0L;
                else if (input.currentSupplyCapacityRaw() != null) post = Math.min(changed, input.currentSupplyCapacityRaw());
                else missing.add("current_supply_capacity_raw");
            } else {
                if (stock == null) missing.add("current_supply_raw");
                if (rate == null) missing.add("current_supply_change_monthly_raw");
            }
            Boolean suppressed = input.admission().nativeFleetSupplyLossSuppressed();
            if (Boolean.TRUE.equals(suppressed)) supply = component(null, null, null, 0, null);
            else if (suppressed == null) missing.add("native_fleet_supply_loss_suppressed");
            else if (post != null) supply = deriveSupplyComponent(post, input.supply(), input.losses());
        }
        missing.addAll(supply.missingInputs());
        return new SupplyEntry(admission.admitted(), admission.witnesses(), admission.rejection(), post, post != null,
                supply, List.copyOf(new LinkedHashSet<>(missing)));
    }

    private static Integer independentBudget(String name, Boolean active, Integer count, Long rate, List<String> missing) {
        if (Boolean.FALSE.equals(active)) return 0;
        if (active == null) { missing.add(name + "_active"); return null; }
        if (count == null) missing.add("whole_soldiers");
        if (rate == null) missing.add(name + "_rate_raw");
        return count == null || rate == null ? null : wholeBudget(count, Math.min(SCALE, Math.max(0, rate)));
    }

    private record Admission(Boolean admitted, String rejection, List<AdmissionWitness> witnesses) {}
    private static Admission admission(AdmissionInputs inputs, ClockInputs clock, List<String> missing) {
        List<AdmissionWitness> witnesses = new ArrayList<>();
        String[] names = {"unit_native_170_raw", "native_unit_in_combat", "native_unit_gathering", "army_gathering_count_raw"};
        List<GateValue> values = List.of(value(inputs.unitNative170Raw()), value(inputs.nativeUnitInCombat()),
                value(inputs.nativeUnitGathering()), value(inputs.armyGatheringCountRaw()));
        for (int index = 0; index < names.length; index++) {
            GateValue value = values.get(index);
            Boolean passed = switch (value) {
                case MissingValue ignored -> null;
                case BooleanValue predicate -> !predicate.value();
                case IntegerValue integer -> index == 0 ? integer.value() != 3 : integer.value() == 0;
            };
            witnesses.add(new GateWitness(names[index], value, passed));
            if (passed == null) { missing.add(names[index]); return new Admission(null, null, witnesses); }
            if (!passed) return new Admission(false, names[index], witnesses);
        }
        if (clock.currentDateRaw() == null || clock.graceAnchorDateRaw() == null || clock.loadedGraceDays() == null) {
            if (clock.currentDateRaw() == null) missing.add("current_date_raw");
            if (clock.graceAnchorDateRaw() == null) missing.add("grace_anchor_date_raw");
            if (clock.loadedGraceDays() == null) missing.add("loaded_grace_days");
            return new Admission(null, null, witnesses);
        }
        int elapsed = clock.currentDateRaw() - clock.graceAnchorDateRaw();
        int days = elapsed / 24;
        boolean passed = days > clock.loadedGraceDays();
        witnesses.add(new GraceWitness(elapsed, days, clock.loadedGraceDays(), passed));
        return new Admission(passed, passed ? null : "native_grace_strict_greater", witnesses);
    }
    private static GateValue value(Integer value) { return value == null ? new MissingValue() : new IntegerValue(value); }
    private static GateValue value(Boolean value) { return value == null ? new MissingValue() : new BooleanValue(value); }
    private static SupplyComponent component(Integer index, Long base, Long effective, Integer soldiers, String missing) {
        return new SupplyComponent(index, base, effective, soldiers != null, soldiers, missing == null ? List.of() : List.of(missing));
    }
}
