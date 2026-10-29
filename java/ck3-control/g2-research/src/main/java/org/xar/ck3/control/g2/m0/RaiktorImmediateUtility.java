package org.xar.ck3.control.g2.m0;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** The original immediate-exit arithmetic only. Inputs do not confer action or observation authority. */
public final class RaiktorImmediateUtility {
    private RaiktorImmediateUtility() { }

    public enum Outcome {
        WHITE_PEACE("white_peace"), SURRENDER("surrender");
        private final String wire;
        Outcome(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    /** Fixed-point resources and seven original count features; signed values retain original semantics. */
    public record Features(long primaryGoldTransferRaw, long attackerPrestigeDeltaRaw,
                           long declaredClaimRemovedCount, long favorHookApplied, long truceDayCount,
                           long powReleaseCount, long titleHolderChangeCount, long hostageTransferCount,
                           long warBoundSoldierLossCount) { }
    public record Limits(long maximumGoldTransferRaw, long maximumPrestigeLossRaw,
                         long maximumClaimsRemoved, boolean allowFavorHook, long maximumTruceDays) {
        public Limits {
            require(maximumGoldTransferRaw >= 0 && maximumPrestigeLossRaw >= 0
                    && maximumClaimsRemoved >= 0 && maximumTruceDays >= 0, "nonnegative budget limits required");
        }
    }
    public record Model(Features coefficients, long perUnobservedEffectPenaltyRaw, long maximumTotalPenaltyRaw) {
        public Model {
            Objects.requireNonNull(coefficients);
            require(perUnobservedEffectPenaltyRaw >= 0 && maximumTotalPenaltyRaw >= 0,
                    "nonnegative uncertainty penalties required");
        }
    }
    public record ObservedOption(Features features, List<String> unobservedDynamicEffects,
                                 Limits limits, boolean nativeExecutionAvailable) {
        public ObservedOption {
            Objects.requireNonNull(features); Objects.requireNonNull(limits);
            unobservedDynamicEffects = strings(unobservedDynamicEffects);
        }
    }
    public record Input(ObservedOption whitePeace, ObservedOption surrender, Model model,
                        BigInteger minimumSwitchMarginRaw) {
        public Input {
            Objects.requireNonNull(whitePeace); Objects.requireNonNull(surrender); Objects.requireNonNull(model);
            require(minimumSwitchMarginRaw != null && minimumSwitchMarginRaw.signum() >= 0,
                    "nonnegative exact margin required");
        }
    }
    public record Option(Features features, Features contributionsRaw, long baseUtilityRaw,
                         List<String> unobservedDynamicEffects, long uncertaintyPenaltyRaw, long utilityRaw,
                         List<String> hardBudgetBreaches, List<String> executionBlockers, boolean eligible) {
        public Option {
            Objects.requireNonNull(features); Objects.requireNonNull(contributionsRaw);
            unobservedDynamicEffects = strings(unobservedDynamicEffects);
            hardBudgetBreaches = strings(hardBudgetBreaches); executionBlockers = strings(executionBlockers);
            require(eligible == (hardBudgetBreaches.isEmpty() && executionBlockers.isEmpty()),
                    "eligibility must follow original budget and native availability");
        }
    }
    public record Comparison(List<Outcome> eligibleOptions, Optional<Outcome> preferredImmediateExit,
                             Optional<BigInteger> preferenceMarginRaw, BigInteger minimumSwitchMarginRaw) {
        public Comparison {
            eligibleOptions = List.copyOf(eligibleOptions);
            Objects.requireNonNull(preferredImmediateExit); Objects.requireNonNull(preferenceMarginRaw);
            Objects.requireNonNull(minimumSwitchMarginRaw);
        }
        public String status() {
            return preferredImmediateExit.isPresent() ? "pairwise_preference_available" : "pairwise_underdetermined";
        }
    }
    public record Evaluation(Option whitePeace, Option surrender, Comparison comparison) { }

    public static Evaluation evaluate(Input input) {
        Objects.requireNonNull(input);
        Option white = option(Outcome.WHITE_PEACE, input.whitePeace(), input.model());
        Option surrender = option(Outcome.SURRENDER, input.surrender(), input.model());
        List<Outcome> eligible = new ArrayList<>();
        if (white.eligible()) { eligible.add(Outcome.WHITE_PEACE); }
        if (surrender.eligible()) { eligible.add(Outcome.SURRENDER); }
        Optional<Outcome> preferred = Optional.empty();
        Optional<BigInteger> margin = Optional.empty();
        if (eligible.size() == 1) { preferred = Optional.of(eligible.getFirst()); }
        else if (eligible.size() == 2) {
            // Python's comparison subtraction is unbounded, unlike its deliberately int64 utility arithmetic.
            BigInteger difference = BigInteger.valueOf(white.utilityRaw()).subtract(BigInteger.valueOf(surrender.utilityRaw()));
            if (difference.abs().compareTo(input.minimumSwitchMarginRaw()) >= 0) {
                preferred = Optional.of(difference.signum() > 0 ? Outcome.WHITE_PEACE : Outcome.SURRENDER);
                margin = Optional.of(difference.abs());
            }
        }
        return new Evaluation(white, surrender, new Comparison(eligible, preferred, margin, input.minimumSwitchMarginRaw()));
    }

    private static Option option(Outcome outcome, ObservedOption observed, Model model) {
        Features f = observed.features(); Features c = model.coefficients();
        Features contributions = new Features(fixed(f.primaryGoldTransferRaw(), c.primaryGoldTransferRaw()),
                fixed(f.attackerPrestigeDeltaRaw(), c.attackerPrestigeDeltaRaw()),
                multiply(f.declaredClaimRemovedCount(), c.declaredClaimRemovedCount()),
                multiply(f.favorHookApplied(), c.favorHookApplied()), multiply(f.truceDayCount(), c.truceDayCount()),
                multiply(f.powReleaseCount(), c.powReleaseCount()), multiply(f.titleHolderChangeCount(), c.titleHolderChangeCount()),
                multiply(f.hostageTransferCount(), c.hostageTransferCount()),
                multiply(f.warBoundSoldierLossCount(), c.warBoundSoldierLossCount()));
        // Preserve original sorted-feature accumulation order; intermediate overflow is a real refusal.
        long base = 0;
        for (long part : new long[] {contributions.attackerPrestigeDeltaRaw(), contributions.declaredClaimRemovedCount(),
                contributions.favorHookApplied(), contributions.hostageTransferCount(), contributions.powReleaseCount(),
                contributions.primaryGoldTransferRaw(), contributions.titleHolderChangeCount(), contributions.truceDayCount(),
                contributions.warBoundSoldierLossCount()}) { base = add(base, part); }
        long penalty = Math.min(multiply(observed.unobservedDynamicEffects().size(), model.perUnobservedEffectPenaltyRaw()),
                model.maximumTotalPenaltyRaw());
        long utility = add(base, -penalty);
        List<String> breaches = breaches(outcome, f, observed.limits());
        List<String> execution = observed.nativeExecutionAvailable() ? List.of()
                : List.of(outcome.wire() + "_native_execution_unavailable");
        return new Option(f, contributions, base, observed.unobservedDynamicEffects(), penalty, utility,
                breaches, execution, breaches.isEmpty() && execution.isEmpty());
    }
    private static List<String> breaches(Outcome outcome, Features features, Limits limits) {
        List<String> result = new ArrayList<>(); String prefix = outcome.wire();
        if (features.primaryGoldTransferRaw() > limits.maximumGoldTransferRaw()) { result.add(prefix + "_gold_budget_breached"); }
        BigInteger loss = BigInteger.valueOf(features.attackerPrestigeDeltaRaw()).negate().max(BigInteger.ZERO);
        if (loss.compareTo(BigInteger.valueOf(limits.maximumPrestigeLossRaw())) > 0) { result.add(prefix + "_prestige_budget_breached"); }
        if (features.declaredClaimRemovedCount() > limits.maximumClaimsRemoved()) { result.add(prefix + "_claim_budget_breached"); }
        if (features.favorHookApplied() != 0 && !limits.allowFavorHook()) { result.add(prefix + "_favor_hook_budget_breached"); }
        if (features.truceDayCount() > limits.maximumTruceDays()) { result.add(prefix + "_truce_budget_breached"); }
        return List.copyOf(result);
    }
    private static long fixed(long value, long coefficient) { return multiply(value, coefficient) / 100_000; }
    private static long multiply(long left, long right) {
        try { return Math.multiplyExact(left, right); }
        catch (ArithmeticException error) { throw new IllegalArgumentException("immediate-exit product overflowed int64", error); }
    }
    private static long add(long left, long right) {
        try { return Math.addExact(left, right); }
        catch (ArithmeticException error) { throw new IllegalArgumentException("immediate-exit sum overflowed int64", error); }
    }
    private static List<String> strings(List<String> values) {
        require(values != null, "explicit string list required");
        for (String value : values) { require(value != null && !value.strip().isEmpty(), "nonempty list item required"); }
        require(values.stream().distinct().count() == values.size(), "duplicate list items refused");
        return List.copyOf(values);
    }
    private static void require(boolean condition, String message) {
        if (!condition) { throw new IllegalArgumentException(message); }
    }
}
