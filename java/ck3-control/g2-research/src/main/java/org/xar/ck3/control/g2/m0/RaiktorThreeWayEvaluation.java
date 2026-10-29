package org.xar.ck3.control.g2.m0;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;

/** Exact pure decision leaves of production recommendation-v7; no command, writer or result verification. */
public final class RaiktorThreeWayEvaluation {
    public static final String SOURCE_CONTRACT = "raiktor-three-way-exit-recommendation-v7";
    private static final BigInteger INT64_MAX = BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE);
    private RaiktorThreeWayEvaluation() { }

    public enum Outcome {
        CONTINUE, WHITE_PEACE, SURRENDER;
        public String wire() { return name().toLowerCase(Locale.ROOT); }
    }
    public enum PowerRelation {
        OPPONENT_STRONGER, EQUAL, ACTOR_STRONGER;
        public String wire() { return name().toLowerCase(Locale.ROOT); }
    }
    public enum Status {
        STATIC_RECOMMENDATION_AVAILABLE, THREE_WAY_UNDERDETERMINED;
        public String wire() { return name().toLowerCase(Locale.ROOT); }
    }
    public record ImmediateOption(BigInteger utilityRaw, boolean eligible, List<String> hardBudgetBreaches) {
        public ImmediateOption {
            Objects.requireNonNull(utilityRaw); hardBudgetBreaches = textRows(hardBudgetBreaches);
        }
    }
    public record Immediate(M0Frame frame, ImmediateOption whitePeace, ImmediateOption surrender,
            BigInteger minimumSwitchMarginRaw, boolean productionLive) {
        public Immediate {
            Objects.requireNonNull(frame); Objects.requireNonNull(whitePeace); Objects.requireNonNull(surrender);
            nonnegative(minimumSwitchMarginRaw, "minimum_switch_margin_raw");
        }
    }
    public record Power(M0Frame frame, PowerRelation relation, BigInteger actualPowerRatioRaw,
            BigInteger fixedPointScale, boolean productionLive) {
        public Power {
            Objects.requireNonNull(frame); Objects.requireNonNull(relation);
            nonnegative(actualPowerRatioRaw, "actual_power_ratio_raw"); nonnegative(fixedPointScale, "fixed_point_scale");
            require(fixedPointScale.signum() > 0, "fixed_point_scale must be positive");
        }
    }
    public record TailParameters(BigInteger longWarScaleStartDays, BigInteger opponentStrongerContinuePenaltyRaw,
            BigInteger parityContinuePenaltyRaw, BigInteger playerStrongerContinuePenaltyRaw) {
        public TailParameters {
            nonnegative(longWarScaleStartDays, "long_war_scale_start_days");
            nonnegative(opponentStrongerContinuePenaltyRaw, "opponent_stronger_continue_penalty_raw");
            nonnegative(parityContinuePenaltyRaw, "parity_continue_penalty_raw");
            nonnegative(playerStrongerContinuePenaltyRaw, "player_stronger_continue_penalty_raw");
        }
    }
    public record Terminal(M0Frame frame, BigInteger playerRelativeWarScore, BigInteger attackerWarScore,
            BigInteger defenderWarScore, BigInteger warDurationDays, boolean opponentTerminalControl, boolean productionLive) {
        public Terminal {
            Objects.requireNonNull(frame); Objects.requireNonNull(playerRelativeWarScore);
            Objects.requireNonNull(attackerWarScore); Objects.requireNonNull(defenderWarScore);
            require(playerRelativeWarScore.equals(attackerWarScore) && defenderWarScore.equals(attackerWarScore.negate()),
                    "opponent terminal-control war scores disagree");
            nonnegative(warDurationDays, "war_duration_days");
            require(opponentTerminalControl == (playerRelativeWarScore.compareTo(BigInteger.valueOf(-100)) <= 0),
                    "opponent terminal-control classification drifted");
        }
    }
    public record Input(Immediate immediate, Power power, TailParameters model, Terminal terminal) {
        public Input {
            Objects.requireNonNull(immediate); Objects.requireNonNull(power); Objects.requireNonNull(model); Objects.requireNonNull(terminal);
            require(immediate.frame().equals(power.frame()), "immediate-exit and power certificates crossed paused frames");
            require(immediate.frame().equals(terminal.frame()), "immediate-exit and terminal-control inputs crossed paused frames");
        }
    }
    public record ContinueOption(PowerRelation measuredPowerRelation, BigInteger baseUtilityRaw,
            BigInteger tailRiskPenaltyRaw, BigInteger tailRiskBasePenaltyRaw, boolean tailRiskPowerScaleApplied,
            BigInteger tailRiskLongWarScaleStartDays, BigInteger observedWarDurationDays,
            BigInteger observedPlayerRelativeWarScore, BigInteger measuredPowerRatioRaw, BigInteger measuredPowerRatioScale,
            BigInteger utilityRaw, List<String> hardBudgetBreaches, List<String> executionBlockers,
            boolean eligible, boolean campaignOutcomeForecastReady) {
        public ContinueOption {
            Objects.requireNonNull(measuredPowerRelation); Objects.requireNonNull(baseUtilityRaw);
            Objects.requireNonNull(tailRiskPenaltyRaw); Objects.requireNonNull(tailRiskBasePenaltyRaw);
            Objects.requireNonNull(tailRiskLongWarScaleStartDays); Objects.requireNonNull(observedWarDurationDays);
            Objects.requireNonNull(observedPlayerRelativeWarScore); Objects.requireNonNull(measuredPowerRatioRaw);
            Objects.requireNonNull(measuredPowerRatioScale); Objects.requireNonNull(utilityRaw);
            hardBudgetBreaches = textRows(hardBudgetBreaches); executionBlockers = textRows(executionBlockers);
            require(baseUtilityRaw.signum() == 0 && tailRiskPenaltyRaw.signum() >= 0
                    && tailRiskPenaltyRaw.compareTo(INT64_MAX) <= 0 && utilityRaw.equals(tailRiskPenaltyRaw.negate())
                    && hardBudgetBreaches.isEmpty() && eligible == executionBlockers.isEmpty()
                    && !campaignOutcomeForecastReady, "continue option contradicts the original decision contract");
        }
    }
    public record Comparison(Status status, List<Outcome> eligibleOptions, Optional<Outcome> recommendedOutcome,
            Optional<BigInteger> winningMarginRaw, BigInteger minimumSwitchMarginRaw) {
        public Comparison {
            Objects.requireNonNull(status); eligibleOptions = List.copyOf(eligibleOptions);
            Objects.requireNonNull(recommendedOutcome); Objects.requireNonNull(winningMarginRaw);
            nonnegative(minimumSwitchMarginRaw, "minimum_switch_margin_raw");
            require(eligibleOptions.stream().distinct().count() == eligibleOptions.size()
                    && recommendedOutcome.map(eligibleOptions::contains).orElse(true)
                    && (status == Status.STATIC_RECOMMENDATION_AVAILABLE) == recommendedOutcome.isPresent()
                    && winningMarginRaw.isPresent() == (eligibleOptions.size() > 1), "comparison output is contradictory");
        }
    }
    public record Decision(ContinueOption continueOption, Comparison comparison) {
        public Decision { Objects.requireNonNull(continueOption); Objects.requireNonNull(comparison); }
    }
    private record Ranked(Outcome outcome, BigInteger utility) { }

    public static Decision evaluate(Input input) {
        Objects.requireNonNull(input);
        Power power = input.power(); TailParameters model = input.model(); Terminal terminal = input.terminal();
        BigInteger base = switch (power.relation()) {
            case OPPONENT_STRONGER -> model.opponentStrongerContinuePenaltyRaw();
            case EQUAL -> model.parityContinuePenaltyRaw();
            case ACTOR_STRONGER -> model.playerStrongerContinuePenaltyRaw();
        };
        boolean scaled = power.relation() == PowerRelation.OPPONENT_STRONGER
                && terminal.playerRelativeWarScore().signum() < 0
                && terminal.warDurationDays().compareTo(model.longWarScaleStartDays()) >= 0;
        BigInteger penalty = scaled ? base.multiply(power.actualPowerRatioRaw()).divide(power.fixedPointScale()) : base;
        require(penalty.compareTo(INT64_MAX) <= 0, "tail-risk penalty overflows int64");
        require(!scaled || penalty.compareTo(base) >= 0, "opponent-stronger power ratio reduced the tail-risk penalty");
        List<String> execution = terminal.opponentTerminalControl()
                ? List.of("opponent_has_enforceable_terminal_war_score") : List.of();
        ContinueOption continuation = new ContinueOption(power.relation(), BigInteger.ZERO, penalty, base, scaled,
                model.longWarScaleStartDays(), terminal.warDurationDays(), terminal.playerRelativeWarScore(),
                power.actualPowerRatioRaw(), power.fixedPointScale(), penalty.negate(), List.of(), execution, execution.isEmpty(), false);

        List<Ranked> eligible = new ArrayList<>();
        if (continuation.eligible()) { eligible.add(new Ranked(Outcome.CONTINUE, continuation.utilityRaw())); }
        if (input.immediate().whitePeace().eligible()) {
            eligible.add(new Ranked(Outcome.WHITE_PEACE, input.immediate().whitePeace().utilityRaw()));
        }
        if (input.immediate().surrender().eligible()) {
            eligible.add(new Ranked(Outcome.SURRENDER, input.immediate().surrender().utilityRaw()));
        }
        List<Outcome> originalOrder = eligible.stream().map(Ranked::outcome).toList();
        eligible.sort(Comparator.comparing(Ranked::utility, Comparator.reverseOrder()).thenComparing(row -> row.outcome().wire()));
        Optional<Outcome> recommendation = Optional.empty(); Optional<BigInteger> margin = Optional.empty();
        if (eligible.size() == 1) { recommendation = Optional.of(eligible.getFirst().outcome()); }
        else if (eligible.size() > 1) {
            BigInteger difference = eligible.getFirst().utility().subtract(eligible.get(1).utility());
            margin = Optional.of(difference);
            if (difference.compareTo(input.immediate().minimumSwitchMarginRaw()) >= 0) {
                recommendation = Optional.of(eligible.getFirst().outcome());
            }
        }
        return new Decision(continuation, new Comparison(recommendation.isPresent()
                ? Status.STATIC_RECOMMENDATION_AVAILABLE : Status.THREE_WAY_UNDERDETERMINED,
                originalOrder, recommendation, margin, input.immediate().minimumSwitchMarginRaw()));
    }

    private static List<String> textRows(List<String> rows) {
        List<String> result = List.copyOf(rows);
        result.forEach(row -> require(!row.isEmpty(), "nonempty budget/blocker text required"));
        return result;
    }
    private static void nonnegative(BigInteger value, String name) {
        Objects.requireNonNull(value, name); require(value.signum() >= 0, name + " must be nonnegative");
    }
    private static void require(boolean condition, String reason) {
        if (!condition) { throw new IllegalArgumentException(reason); }
    }
}
