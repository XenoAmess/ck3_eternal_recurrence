package org.xar.ck3.control.wave2.events.eventoutcome;

import java.math.BigInteger;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

/** The complete stress/gold/prestige plan/evaluate closure from vanilla_events/outcome.py. */
public final class ScalarEventOutcome {
    public static final String SCHEMA = "xar.ck3.vanilla-event-material-postcondition";
    private static final BigInteger INT32_MAX = BigInteger.valueOf(Integer.MAX_VALUE);
    private static final BigInteger INT64_MIN = BigInteger.valueOf(Long.MIN_VALUE);
    private static final BigInteger INT64_MAX = BigInteger.valueOf(Long.MAX_VALUE);
    private static final BigInteger SCALE = BigInteger.valueOf(100_000);
    private ScalarEventOutcome() { }

    public enum Metric {
        STRESS("played_character.stress_points", "stress_points", "stress"),
        GOLD("played_character_gold.raw", "gold_raw", "gold"),
        PRESTIGE("played_character_prestige.raw", "prestige_raw", "prestige");
        private final String wire;
        private final String valueField;
        private final String noun;
        Metric(String wire, String valueField, String noun) { this.wire = wire; this.valueField = valueField; this.noun = noun; }
        public String wire() { return wire; }
        public String valueField() { return valueField; }
        public String noun() { return noun; }
        public static Metric fromWire(String wire) {
            for (Metric value : values()) if (value.wire.equals(wire)) return value;
            throw new IllegalArgumentException("unsupported scalar metric");
        }
    }
    public enum Relation {
        NON_INCREASING("non_increasing"), NON_DECREASING("non_decreasing"),
        STRICTLY_INCREASING("strictly_increasing"), STRICTLY_DECREASING("strictly_decreasing");
        private final String wire;
        Relation(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Relation fromWire(String wire) {
            for (Relation value : values()) if (value.wire.equals(wire)) return value;
            throw new IllegalArgumentException("unsupported scalar relation");
        }
    }
    public enum ExpectationStatus { READY, UNAVAILABLE }
    public enum ResultStatus { UNAVAILABLE, FAILED, VERIFIED_CHANGE, VERIFIED_NO_CHANGE }
    public enum RunnerIssue { FAILED, UNAVAILABLE, NO_MATERIAL_CHANGE }

    public record EffectProfile(String schema, BigInteger schemaVersion, BigInteger selectedNativeOptionIndex,
                                String metric, String expectedRelation, Boolean materialChangeRequired) { }
    public record Decision(String status, String eventDefinitionKey, String ck3Build,
                           BigInteger selectedOptionNumber, BigInteger selectedNativeOptionIndex,
                           EffectProfile profile) { }
    public record Resource(BigInteger raw, BigInteger scale) { }
    public record PlanInput(Decision decision, BigInteger characterId, BigInteger stressPoints,
                            Resource gold, Resource prestige, String snapshotId, BigInteger revision) { }
    public record Expectation(String eventDefinitionKey, BigInteger selectedOptionNumber,
                              BigInteger selectedNativeOptionIndex, Metric metric, Relation relation,
                              ExpectationStatus status, String startingSnapshotId, BigInteger startingRevision,
                              BigInteger characterId, BigInteger startingValue, String unavailableReason) {
        public Expectation {
            Objects.requireNonNull(eventDefinitionKey, "eventDefinitionKey");
            Objects.requireNonNull(selectedNativeOptionIndex, "selectedNativeOptionIndex");
            Objects.requireNonNull(metric, "metric");
            Objects.requireNonNull(relation, "relation");
            Objects.requireNonNull(status, "status");
        }
    }
    public record Observation(String status, BigInteger characterId, BigInteger value, BigInteger scale) { }
    public record ObservationPair(Observation before, Observation after) { }
    public record Selection(Boolean postconditionVerified, String startingSnapshotId, BigInteger startingRevision,
                            String endingSnapshotId, BigInteger endingRevision,
                            ObservationPair stress, ObservationPair gold, ObservationPair prestige) {
        public Selection {
            stress = canonicalPair(stress); gold = canonicalPair(gold); prestige = canonicalPair(prestige);
        }
        public ObservationPair observations(Metric metric) {
            return switch (metric) { case STRESS -> stress; case GOLD -> gold; case PRESTIGE -> prestige; };
        }
    }
    public record Evaluation(Expectation expectation, ResultStatus status, Boolean relationSatisfied,
                             Boolean materialChangeObserved, BigInteger endingValue, BigInteger delta,
                             String unavailableReason) {
        public Evaluation {
            Objects.requireNonNull(expectation, "expectation");
            Objects.requireNonNull(status, "status");
        }
    }
    private record Choice(String eventKey, int nativeIndex) { }
    private record Specification(Metric metric, Relation relation) { }
    private static final Map<Choice, Specification> SUPPORTED = Map.of(
        new Choice("tgp_travel_events.0030", 1), new Specification(Metric.STRESS, Relation.NON_INCREASING),
        new Choice("trait_specific.8001", 1), new Specification(Metric.GOLD, Relation.STRICTLY_INCREASING),
        new Choice("epidemic_events.1020", 0), new Specification(Metric.GOLD, Relation.STRICTLY_DECREASING),
        new Choice("epidemic_events.5007", 2), new Specification(Metric.STRESS, Relation.STRICTLY_INCREASING),
        new Choice("death_management.1007", 0), new Specification(Metric.STRESS, Relation.NON_DECREASING),
        new Choice("fervor.1002", 2), new Specification(Metric.STRESS, Relation.NON_DECREASING),
        new Choice("stress_threshold_special.1001", 7), new Specification(Metric.STRESS, Relation.NON_INCREASING),
        new Choice("tgp_japan_yearly_events.1190", 1), new Specification(Metric.PRESTIGE, Relation.STRICTLY_DECREASING));

    /** Empty means this scalar leaf does not handle the decision; dedicated dispatch remains outside. */
    public static Optional<Expectation> plan(PlanInput input) {
        Objects.requireNonNull(input, "input");
        Decision decision = input.decision();
        if (decision == null || !"recommended".equals(decision.status()) || decision.selectedNativeOptionIndex() == null
                || decision.selectedNativeOptionIndex().bitLength() > 31) return Optional.empty();
        int nativeIndex = decision.selectedNativeOptionIndex().intValueExact();
        Specification spec = SUPPORTED.get(new Choice(decision.eventDefinitionKey(), nativeIndex));
        if ("trait_specific.9001".equals(decision.eventDefinitionKey()) && nativeIndex == 2 && "1.20.0.4".equals(decision.ck3Build())) {
            spec = new Specification(Metric.STRESS, Relation.STRICTLY_DECREASING);
        } else if ("feast.7002".equals(decision.eventDefinitionKey()) && nativeIndex == 0 && "1.20.0.3".equals(decision.ck3Build())) {
            spec = new Specification(Metric.PRESTIGE, Relation.STRICTLY_INCREASING);
        } else if ("feast_default.6231".equals(decision.eventDefinitionKey()) && nativeIndex == 0 && "1.20.0.3".equals(decision.ck3Build())) {
            spec = new Specification(Metric.GOLD, Relation.STRICTLY_DECREASING);
        }
        EffectProfile profile = decision.profile();
        if (spec == null || profile == null || !"xar.ck3.vanilla-event-choice-effect".equals(profile.schema())
                || !BigInteger.ONE.equals(profile.schemaVersion())
                || !decision.selectedNativeOptionIndex().equals(profile.selectedNativeOptionIndex())
                || !spec.metric().wire().equals(profile.metric()) || !spec.relation().wire().equals(profile.expectedRelation())
                || !Boolean.TRUE.equals(profile.materialChangeRequired())) return Optional.empty();
        Resource resource = spec.metric() == Metric.GOLD ? input.gold() : input.prestige();
        BigInteger start = spec.metric() == Metric.STRESS ? input.stressPoints() : resource == null ? null : resource.raw();
        boolean valid = positive(input.characterId()) && inRange(start, spec.metric())
            && (spec.metric() == Metric.STRESS || resource != null && SCALE.equals(resource.scale()))
            && input.snapshotId() != null && !input.snapshotId().isEmpty()
            && input.revision() != null && input.revision().signum() >= 0;
        return Optional.of(new Expectation(decision.eventDefinitionKey(), decision.selectedOptionNumber(), decision.selectedNativeOptionIndex(),
            spec.metric(), spec.relation(), valid ? ExpectationStatus.READY : ExpectationStatus.UNAVAILABLE,
            valid ? input.snapshotId() : null, valid ? input.revision() : null,
            valid ? input.characterId() : null, valid ? start : null,
            valid ? null : "same_frame_player_" + spec.metric().noun() + "_unavailable"));
    }

    public static Evaluation evaluate(Expectation expected, Selection selection) {
        Objects.requireNonNull(expected, "expected");
        if (expected.status() != ExpectationStatus.READY) return unavailable(expected, expected.unavailableReason());
        ObservationPair pair = selection == null ? null : selection.observations(expected.metric());
        Observation before = pair == null ? null : pair.before();
        Observation after = pair == null ? null : pair.after();
        if (selection == null || !Boolean.TRUE.equals(selection.postconditionVerified()) || before == null || after == null
                || !"available".equals(before.status()) || !"available".equals(after.status())) {
            return unavailable(expected, "native_event_" + expected.metric().noun() + "_observation_unavailable");
        }
        boolean binding = Objects.equals(selection.startingSnapshotId(), expected.startingSnapshotId())
            && Objects.equals(selection.startingRevision(), expected.startingRevision())
            && expected.characterId() != null && expected.characterId().equals(before.characterId())
            && expected.characterId().equals(after.characterId()) && expected.startingValue() != null
            && expected.startingValue().equals(before.value()) && inRange(before.value(), expected.metric()) && inRange(after.value(), expected.metric());
        if (expected.relation() == Relation.STRICTLY_DECREASING) {
            binding = binding && (expected.metric() == Metric.STRESS || SCALE.equals(before.scale()) && SCALE.equals(after.scale()))
                && newerFrame(expected, selection);
        }
        if ("epidemic_events.5007".equals(expected.eventDefinitionKey())) binding = binding && newerFrame(expected, selection);
        if (!binding) return new Evaluation(expected, ResultStatus.FAILED, false, false, null, null, "same_character_snapshot_binding_mismatch");
        // Values are int32/int64, but their difference can require 65 signed bits, as in Python.
        BigInteger delta = after.value().subtract(before.value());
        int sign = delta.signum();
        boolean relation = switch (expected.relation()) {
            case NON_INCREASING -> sign <= 0;
            case NON_DECREASING -> sign >= 0;
            case STRICTLY_INCREASING -> sign > 0;
            case STRICTLY_DECREASING -> sign < 0;
        };
        ResultStatus status = !relation ? ResultStatus.FAILED : sign == 0 ? ResultStatus.VERIFIED_NO_CHANGE : ResultStatus.VERIFIED_CHANGE;
        String reason = null;
        if (!relation) reason = switch (expected.relation()) {
            case NON_INCREASING -> "stress_increased";
            case NON_DECREASING -> "stress_decreased";
            case STRICTLY_INCREASING -> "epidemic_events.5007".equals(expected.eventDefinitionKey()) ? "stress_not_increased"
                : expected.metric() == Metric.PRESTIGE ? "prestige_not_increased" : "gold_not_increased";
            case STRICTLY_DECREASING -> expected.metric().noun() + "_not_decreased";
        };
        return new Evaluation(expected, status, relation, sign != 0, after.value(), delta, reason);
    }

    /** The actual native_auto_run scalar consumer rule; verified zero is not always material credit. */
    public static Optional<RunnerIssue> runnerIssue(Expectation expected, Evaluation observed) {
        if (expected == null || expected.status() != ExpectationStatus.READY) return Optional.empty();
        if (observed == null) return Optional.of(RunnerIssue.UNAVAILABLE);
        if (observed.status() == ResultStatus.FAILED) return Optional.of(RunnerIssue.FAILED);
        if ("stress_threshold_special.1001".equals(expected.eventDefinitionKey()) && positive(expected.startingValue())
                && observed.status() == ResultStatus.VERIFIED_NO_CHANGE) return Optional.of(RunnerIssue.NO_MATERIAL_CHANGE);
        if (observed.status() != ResultStatus.VERIFIED_CHANGE && observed.status() != ResultStatus.VERIFIED_NO_CHANGE) {
            return Optional.of(RunnerIssue.UNAVAILABLE);
        }
        return Optional.empty();
    }

    private static Evaluation unavailable(Expectation expected, String reason) {
        return new Evaluation(expected, ResultStatus.UNAVAILABLE, null, null, null, null, reason);
    }
    private static boolean newerFrame(Expectation expected, Selection selection) {
        return selection.endingSnapshotId() != null && !selection.endingSnapshotId().equals(selection.startingSnapshotId())
            && expected.startingRevision() != null && selection.endingRevision() != null
            && selection.endingRevision().compareTo(expected.startingRevision()) > 0;
    }
    private static boolean positive(BigInteger value) { return value != null && value.signum() > 0; }
    private static ObservationPair canonicalPair(ObservationPair pair) {
        return pair == null || pair.before() == null && pair.after() == null ? null : pair;
    }
    private static boolean inRange(BigInteger value, Metric metric) {
        if (value == null) return false;
        return metric == Metric.STRESS ? value.signum() >= 0 && value.compareTo(INT32_MAX) <= 0
            : value.compareTo(INT64_MIN) >= 0 && value.compareTo(INT64_MAX) <= 0;
    }
}
