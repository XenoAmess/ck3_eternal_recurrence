package org.xar.ck3.control.g2.m0;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.Outcome;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.PowerRelation;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.Status;

/** The formal planner's comparison-trace consumer. Copies the choice; never scores or submits it. */
public final class RaiktorUtilityComparisonTrace {
    public static final String OPERATION = "project-formal-exit-utility-trace";
    private static final JsonNodeFactory JSON = JsonNodeFactory.instance;
    private RaiktorUtilityComparisonTrace() { }

    public record OptionFacts(boolean eligible, BigInteger utilityRaw, List<String> hardBudgetBreaches,
            List<String> executionBlockers) {
        public OptionFacts {
            Objects.requireNonNull(utilityRaw);
            hardBudgetBreaches = List.copyOf(hardBudgetBreaches);
            executionBlockers = List.copyOf(executionBlockers);
        }
    }

    public sealed interface OptionTrace permits ContinueTrace, ExitTrace {
        OptionFacts facts();
    }

    public record ContinueTrace(OptionFacts facts, PowerRelation measuredPowerRelation,
            BigInteger tailRiskPenaltyRaw, BigInteger tailRiskBasePenaltyRaw, boolean tailRiskPowerScaleApplied,
            BigInteger observedWarDurationDays, BigInteger observedPlayerRelativeWarScore,
            BigInteger measuredPowerRatioRaw, BigInteger measuredPowerRatioScale) implements OptionTrace {
        public ContinueTrace {
            Objects.requireNonNull(facts); Objects.requireNonNull(measuredPowerRelation);
            Objects.requireNonNull(tailRiskPenaltyRaw); Objects.requireNonNull(tailRiskBasePenaltyRaw);
            Objects.requireNonNull(observedWarDurationDays); Objects.requireNonNull(observedPlayerRelativeWarScore);
            Objects.requireNonNull(measuredPowerRatioRaw); Objects.requireNonNull(measuredPowerRatioScale);
        }
    }

    public record ExitTrace(OptionFacts facts, BigInteger uncertaintyPenaltyRaw) implements OptionTrace {
        public ExitTrace { Objects.requireNonNull(facts); Objects.requireNonNull(uncertaintyPenaltyRaw); }
    }

    public record Options(ContinueTrace continuation, ExitTrace whitePeace, ExitTrace surrender) {
        public Options {
            Objects.requireNonNull(continuation); Objects.requireNonNull(whitePeace); Objects.requireNonNull(surrender);
        }
    }

    public record Comparison(Status status, List<Outcome> eligibleOptions, Optional<BigInteger> winningMarginRaw,
            BigInteger minimumSwitchMarginRaw) {
        public Comparison {
            Objects.requireNonNull(status); eligibleOptions = List.copyOf(eligibleOptions);
            Objects.requireNonNull(winningMarginRaw); Objects.requireNonNull(minimumSwitchMarginRaw);
        }
    }

    public record Trace(Options options, Comparison comparison) {
        public Trace { Objects.requireNonNull(options); Objects.requireNonNull(comparison); }
    }

    /** Ingress for the existing recommendation certificate, whose unused extensions remain opaque. */
    public static Trace fromCertificate(JsonNode certificate) {
        ObjectNode root = object(certificate, "recommendation certificate");
        require(text(root.get("utility_unit"), "utility_unit").equals("strategy_utility_q100000"),
                "formal exit trace utility unit differs");
        ObjectNode options = object(root.get("options"), "options");
        ObjectNode continuation = object(options.get("continue"), "options.continue");
        ContinueTrace continued = new ContinueTrace(facts(continuation),
                relation(continuation.get("measured_power_relation")),
                integer(continuation.get("tail_risk_penalty_raw"), "tail_risk_penalty_raw"),
                integer(continuation.get("tail_risk_base_penalty_raw"), "tail_risk_base_penalty_raw"),
                bool(continuation.get("tail_risk_power_scale_applied"), "tail_risk_power_scale_applied"),
                integer(continuation.get("observed_war_duration_days"), "observed_war_duration_days"),
                integer(continuation.get("observed_player_relative_war_score"), "observed_player_relative_war_score"),
                integer(continuation.get("measured_power_ratio_raw"), "measured_power_ratio_raw"),
                integer(continuation.get("measured_power_ratio_scale"), "measured_power_ratio_scale"));
        ObjectNode comparison = object(root.get("comparison"), "comparison");
        return new Trace(new Options(continued, exit(options.get("white_peace")), exit(options.get("surrender"))),
                new Comparison(status(comparison.get("status")), outcomes(comparison.get("eligible_options")),
                        nullableInteger(comparison.get("winning_margin_raw"), "winning_margin_raw"),
                        integer(comparison.get("minimum_switch_margin_raw"), "minimum_switch_margin_raw")));
    }

    /** Deserialize the persisted trace using the same typed fields that were emitted by the planner. */
    public static Trace fromTrace(JsonNode value) {
        ObjectNode root = exact(value, Set.of("schema_version", "utility_unit", "options", "comparison"), "trace");
        require(integer(root.get("schema_version"), "schema_version").equals(BigInteger.ONE), "trace schema differs");
        return fromCertificate(root);
    }

    public static ObjectNode toJson(Trace trace) {
        Objects.requireNonNull(trace);
        ObjectNode result = JSON.objectNode().put("schema_version", 1).put("utility_unit", "strategy_utility_q100000");
        ObjectNode options = result.putObject("options");
        ContinueTrace continued = trace.options().continuation();
        ObjectNode continuation = encodeFacts(continued.facts());
        continuation.put("measured_power_relation", continued.measuredPowerRelation().wire());
        continuation.put("tail_risk_penalty_raw", continued.tailRiskPenaltyRaw());
        continuation.put("tail_risk_base_penalty_raw", continued.tailRiskBasePenaltyRaw());
        continuation.put("tail_risk_power_scale_applied", continued.tailRiskPowerScaleApplied());
        continuation.put("observed_war_duration_days", continued.observedWarDurationDays());
        continuation.put("observed_player_relative_war_score", continued.observedPlayerRelativeWarScore());
        continuation.put("measured_power_ratio_raw", continued.measuredPowerRatioRaw());
        continuation.put("measured_power_ratio_scale", continued.measuredPowerRatioScale());
        options.set("continue", continuation);
        options.set("white_peace", encodeExit(trace.options().whitePeace()));
        options.set("surrender", encodeExit(trace.options().surrender()));
        Comparison value = trace.comparison();
        ObjectNode comparison = result.putObject("comparison").put("status", value.status().wire());
        var eligible = comparison.putArray("eligible_options"); value.eligibleOptions().forEach(outcome -> eligible.add(outcome.wire()));
        if (value.winningMarginRaw().isPresent()) comparison.put("winning_margin_raw", value.winningMarginRaw().orElseThrow());
        else comparison.putNull("winning_margin_raw");
        comparison.put("minimum_switch_margin_raw", value.minimumSwitchMarginRaw());
        return result;
    }

    public static byte[] execute(byte[] certificate) {
        return RaiktorExitObservationCodec.encodeWire(toJson(fromCertificate(RaiktorExitObservationCodec.parseWire(certificate))));
    }

    /** Internal M0 dispatcher adapter, retaining the original shared host and source envelope. */
    public static byte[] executeOperation(byte[] raw) {
        ObjectNode request = exact(RaiktorExitObservationCodec.parseWire(raw), Set.of("operation", "certificate"), "trace request");
        require(text(request.get("operation"), "operation").equals(OPERATION), "formal trace operation differs");
        return RaiktorExitObservationCodec.encodeWire(toJson(fromCertificate(request.get("certificate"))));
    }

    private static OptionFacts facts(ObjectNode option) {
        return new OptionFacts(bool(option.get("eligible"), "eligible"), integer(option.get("utility_raw"), "utility_raw"),
                strings(option.get("hard_budget_breaches"), "hard_budget_breaches"), option.has("execution_blockers")
                        ? strings(option.get("execution_blockers"), "execution_blockers") : List.of());
    }
    private static ExitTrace exit(JsonNode value) {
        ObjectNode option = object(value, "exit option");
        return new ExitTrace(facts(option), integer(option.get("uncertainty_penalty_raw"), "uncertainty_penalty_raw"));
    }
    private static ObjectNode encodeFacts(OptionFacts facts) {
        ObjectNode result = JSON.objectNode().put("eligible", facts.eligible()).put("utility_raw", facts.utilityRaw());
        var breaches = result.putArray("hard_budget_breaches"); facts.hardBudgetBreaches().forEach(breaches::add);
        var blockers = result.putArray("execution_blockers"); facts.executionBlockers().forEach(blockers::add);
        return result;
    }
    private static ObjectNode encodeExit(ExitTrace trace) {
        return encodeFacts(trace.facts()).put("uncertainty_penalty_raw", trace.uncertaintyPenaltyRaw());
    }
    private static List<Outcome> outcomes(JsonNode value) {
        require(value != null && value.isArray(), "eligible_options must be a list");
        List<Outcome> result = new ArrayList<>();
        for (JsonNode row : value) {
            String wire = text(row, "eligible outcome");
            result.add(switch (wire) {
                case "continue" -> Outcome.CONTINUE;
                case "white_peace" -> Outcome.WHITE_PEACE;
                case "surrender" -> Outcome.SURRENDER;
                default -> throw rejected("unknown eligible outcome");
            });
        }
        return List.copyOf(result);
    }
    private static PowerRelation relation(JsonNode value) {
        return switch (text(value, "measured_power_relation")) {
            case "opponent_stronger" -> PowerRelation.OPPONENT_STRONGER;
            case "equal" -> PowerRelation.EQUAL;
            case "actor_stronger" -> PowerRelation.ACTOR_STRONGER;
            default -> throw rejected("unknown measured power relation");
        };
    }
    private static Status status(JsonNode value) {
        return switch (text(value, "comparison.status")) {
            case "static_recommendation_available" -> Status.STATIC_RECOMMENDATION_AVAILABLE;
            case "three_way_underdetermined" -> Status.THREE_WAY_UNDERDETERMINED;
            default -> throw rejected("unknown three-way comparison status");
        };
    }
    private static List<String> strings(JsonNode value, String name) {
        require(value != null && value.isArray(), name + " must be a list");
        List<String> result = new ArrayList<>();
        for (JsonNode row : value) result.add(text(row, name + "[]"));
        return List.copyOf(result);
    }
    private static ObjectNode exact(JsonNode value, Set<String> fields, String name) {
        ObjectNode object = object(value, name);
        Set<String> actual = new java.util.HashSet<>(); object.properties().forEach(entry -> actual.add(entry.getKey()));
        require(actual.equals(fields), name + " fields differ"); return object;
    }
    private static ObjectNode object(JsonNode value, String name) {
        require(value instanceof ObjectNode, name + " must be an object"); return (ObjectNode) value;
    }
    private static String text(JsonNode value, String name) {
        require(value != null && value.isTextual(), name + " must be a string"); return value.textValue();
    }
    private static boolean bool(JsonNode value, String name) {
        require(value != null && value.isBoolean(), name + " must be a boolean"); return value.booleanValue();
    }
    private static BigInteger integer(JsonNode value, String name) {
        require(value != null && value.isIntegralNumber(), name + " must be an integer"); return value.bigIntegerValue();
    }
    private static Optional<BigInteger> nullableInteger(JsonNode value, String name) {
        require(value != null, name + " is required");
        return value.isNull() ? Optional.empty() : Optional.of(integer(value, name));
    }
    private static void require(boolean condition, String reason) { if (!condition) throw rejected(reason); }
    private static IllegalArgumentException rejected(String reason) { return new IllegalArgumentException(reason); }
}
