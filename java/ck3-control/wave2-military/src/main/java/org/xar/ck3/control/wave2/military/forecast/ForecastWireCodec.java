package org.xar.ck3.control.wave2.military.forecast;

import static org.xar.ck3.control.wave2.military.forecast.CombatJson.*;
import static org.xar.ck3.control.wave2.military.forecast.CombatNumbers.require;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * Strict persistence boundary for the existing Python forecast JSON domain.
 * Decoded messages are evidence DTOs, never a reconstructed simulation Summary
 * or permission to reuse an observation in another frame. Raw Q100000 values
 * and the original capture remain exact numbers here; a JavaScript transport
 * must use its separate identity/time encoder before crossing that boundary.
 */
public final class ForecastWireCodec {
    private ForecastWireCodec() { }
    public sealed interface Message permits Estimate, NotEstimated { ObjectNode toJson(); }
    public record NotEstimated(FixedContactForecast.Unavailable result) implements Message {
        public NotEstimated { Objects.requireNonNull(result); }
        @Override public ObjectNode toJson() { return result.toJson(); }
    }
    public record Metadata(String modelFidelity, boolean nativeParity, String inputSha256,
            String simulatorBuild, int horizonDays) {
        public Metadata {
            boundedText(modelFidelity, "model_fidelity"); boundedText(simulatorBuild, "simulator_build");
            require(inputSha256 != null && inputSha256.matches("[0-9A-F]{64}"), "uppercase input SHA256 required");
            require(horizonDays >= 1 && horizonDays <= 365, "bounded horizon required");
        }
    }
    public record Distribution(int sampleCount, int playerWins, int playerLosses, int noResolution,
            Double playerWinProbabilityResolved, double unconditionalLower, double unconditionalUpper,
            CombatCore.WilsonInterval resolvedWinWilson95, BigInteger p90HardLossRaw,
            Double p90HardLossFraction, double playerStackWipeProbability) {
        public Distribution {
            require(sampleCount >= 1 && sampleCount <= 4096 && playerWins >= 0 && playerLosses >= 0 && noResolution >= 0
                    && (long) playerWins + playerLosses + noResolution == sampleCount, "distribution census differs");
            int resolved = playerWins + playerLosses;
            require((resolved == 0) == (playerWinProbabilityResolved == null)
                    && (resolved == 0) == (resolvedWinWilson95 == null), "resolved probability and Wilson nullability differ");
            if (resolved > 0) {
                require(probability(playerWinProbabilityResolved) && Double.compare(playerWinProbabilityResolved, (double) playerWins / resolved) == 0,
                        "resolved probability differs from census");
                require(probability(resolvedWinWilson95.lower()) && probability(resolvedWinWilson95.upper())
                        && resolvedWinWilson95.lower() <= resolvedWinWilson95.upper(), "invalid Wilson interval");
            }
            require(probability(unconditionalLower) && probability(unconditionalUpper)
                    && Double.compare(unconditionalLower, (double) playerWins / sampleCount) == 0
                    && Double.compare(unconditionalUpper, (double) (playerWins + noResolution) / sampleCount) == 0,
                    "unconditional probability differs from census");
            require(p90HardLossRaw == null || p90HardLossRaw.signum() >= 0, "negative hard loss raw");
            require(p90HardLossFraction == null || Double.isFinite(p90HardLossFraction) && p90HardLossFraction >= 0,
                    "invalid hard loss fraction");
            require(p90HardLossRaw != null || p90HardLossFraction == null, "hard loss fraction has no raw observation");
            require(probability(playerStackWipeProbability), "invalid wipe probability");
        }
    }
    public record Estimate(Metadata metadata, Distribution distribution,
            FixedContactForecast.AdvantageInput advantageInput, List<String> missingRequiredDomains,
            CombatInputs.Capture capture) implements Message {
        public Estimate {
            Objects.requireNonNull(metadata); Objects.requireNonNull(distribution); Objects.requireNonNull(advantageInput);
            Objects.requireNonNull(capture); missingRequiredDomains = List.copyOf(missingRequiredDomains);
            missingRequiredDomains.forEach(value -> boundedText(value, "missing_required_domains item"));
        }
        @Override public ObjectNode toJson() {
            var row = object(); row.put("status", "estimated"); row.put("model_fidelity", metadata.modelFidelity());
            row.put("native_parity", metadata.nativeParity()); row.put("input_sha256", metadata.inputSha256());
            row.put("simulator_build", metadata.simulatorBuild()); row.put("sample_count", distribution.sampleCount());
            row.put("horizon_days", metadata.horizonDays()); row.set("advantage_input", advantageInput.toJson());
            row.put("player_wins", distribution.playerWins()); row.put("player_losses", distribution.playerLosses());
            row.put("no_resolution", distribution.noResolution()); nullable(row, "player_win_probability_resolved", distribution.playerWinProbabilityResolved());
            row.put("player_win_probability_unconditional_lower", distribution.unconditionalLower());
            row.put("player_win_probability_unconditional_upper", distribution.unconditionalUpper());
            if (distribution.resolvedWinWilson95() == null) row.putNull("resolved_win_wilson95");
            else { var interval = object(); interval.put("lower", distribution.resolvedWinWilson95().lower()); interval.put("upper", distribution.resolvedWinWilson95().upper()); row.set("resolved_win_wilson95", interval); }
            if (distribution.p90HardLossRaw() == null) row.putNull("player_p90_hard_loss_raw"); else row.put("player_p90_hard_loss_raw", distribution.p90HardLossRaw());
            nullable(row, "player_p90_hard_loss_fraction", distribution.p90HardLossFraction());
            row.put("player_stack_wipe_probability", distribution.playerStackWipeProbability());
            row.putNull("commander_or_knight_death_probability"); row.put("character_death_risk_status", "unmodeled_phase_events");
            row.set("missing_required_domains", stringArray(missingRequiredDomains));
            row.set("assumptions", stringArray(FixedContactForecast.assumptions(advantageInput)));
            row.set("capture", capture.source()); return row;
        }
    }
    private static final List<String> ESTIMATE_FIELDS = List.of("status", "model_fidelity", "native_parity", "input_sha256",
            "simulator_build", "sample_count", "horizon_days", "advantage_input", "player_wins", "player_losses", "no_resolution",
            "player_win_probability_resolved", "player_win_probability_unconditional_lower", "player_win_probability_unconditional_upper",
            "resolved_win_wilson95", "player_p90_hard_loss_raw", "player_p90_hard_loss_fraction", "player_stack_wipe_probability",
            "commander_or_knight_death_probability", "character_death_risk_status", "missing_required_domains", "assumptions", "capture");
    private static final List<String> ADVANTAGE_FIELDS = List.of("source", "zero_roll_raw", "model_sha256", "fallback_reason",
            "selected_commander_character_ids", "selected_commander_army_ids", "future_daily_refresh_modeled");
    public static Message decode(byte[] source) { return decode(CombatJson.parse(source)); }
    public static Message decode(JsonNode value) {
        var row = object(value, "forecast"); String status = text(row.get("status"), "status");
        if (!status.equals("estimated")) {
            FixedContactForecast.UnavailableReason reason = reason(status);
            exactFields(row, reason == FixedContactForecast.UnavailableReason.MODEL_UNAVAILABLE ? List.of("status", "error_type") : List.of("status"));
            return new NotEstimated(new FixedContactForecast.Unavailable(reason,
                    reason == FixedContactForecast.UnavailableReason.MODEL_UNAVAILABLE ? modelError(text(row.get("error_type"), "error_type")) : null));
        }
        exactFields(row, ESTIMATE_FIELDS);
        var metadata = new Metadata(text(row.get("model_fidelity"), "model_fidelity"), bool(row.get("native_parity"), "native_parity"),
                text(row.get("input_sha256"), "input_sha256"), text(row.get("simulator_build"), "simulator_build"),
                intValue(row.get("horizon_days"), "horizon_days"));
        var advantage = advantage(row.get("advantage_input"));
        JsonNode intervalNode = row.get("resolved_win_wilson95"); CombatCore.WilsonInterval interval = null;
        if (!intervalNode.isNull()) { var node = object(intervalNode, "resolved_win_wilson95"); exactFields(node, List.of("lower", "upper")); interval = new CombatCore.WilsonInterval(number(node.get("lower"), "lower"), number(node.get("upper"), "upper")); }
        BigInteger raw = row.get("player_p90_hard_loss_raw").isNull() ? null : integer(row.get("player_p90_hard_loss_raw"), "player_p90_hard_loss_raw");
        var distribution = new Distribution(intValue(row.get("sample_count"), "sample_count"), intValue(row.get("player_wins"), "player_wins"),
                intValue(row.get("player_losses"), "player_losses"), intValue(row.get("no_resolution"), "no_resolution"),
                nullableNumber(row.get("player_win_probability_resolved"), "player_win_probability_resolved"),
                number(row.get("player_win_probability_unconditional_lower"), "unconditional lower"),
                number(row.get("player_win_probability_unconditional_upper"), "unconditional upper"), interval, raw,
                nullableNumber(row.get("player_p90_hard_loss_fraction"), "player_p90_hard_loss_fraction"),
                number(row.get("player_stack_wipe_probability"), "player_stack_wipe_probability"));
        require(row.get("commander_or_knight_death_probability").isNull()
                && is(row.get("character_death_risk_status"), "unmodeled_phase_events"), "forecast must preserve unmodeled character death");
        require(stringList(row.get("assumptions"), "assumptions").equals(FixedContactForecast.assumptions(advantage)), "forecast assumptions differ");
        return new Estimate(metadata, distribution, advantage, stringList(row.get("missing_required_domains"), "missing_required_domains"),
                new CombatInputs.Capture(object(row.get("capture"), "capture")));
    }
    /** Validate the real producer's exact wire result without inventing omitted Summary fields. */
    public static Message fromForecast(FixedContactForecast.Forecast source) { return decode(Objects.requireNonNull(source).toJson()); }
    public static byte[] encode(Message value) { return CombatJson.canonical(Objects.requireNonNull(value).toJson()); }
    public static FixedContactForecast.Admission contactAdmission(Message source, boolean defensiveRelief) {
        return FixedContactForecast.contactAdmission(Objects.requireNonNull(source).toJson(), defensiveRelief);
    }
    private static FixedContactForecast.AdvantageInput advantage(JsonNode value) {
        var row = object(value, "advantage_input"); var source = source(text(row.get("source"), "advantage source"));
        var fields = new ArrayList<>(ADVANTAGE_FIELDS);
        if (source == ConstructorAdvantage.Source.V2_CONSTRUCTOR) { fields.add("scope"); fields.add("complete_encounter_advantage_ready"); }
        exactFields(row, fields);
        require(no(row.get("future_daily_refresh_modeled")), "future advantage refresh is unmodeled");
        if (source == ConstructorAdvantage.Source.V2_CONSTRUCTOR) require(is(row.get("scope"), "hypothetical_constructor_context")
                && no(row.get("complete_encounter_advantage_ready")), "v2 constructor scope differs");
        BigInteger raw = row.get("zero_roll_raw").isNull() ? null : ConstructorAdvantage.signedRaw(row.get("zero_roll_raw"), "zero_roll_raw");
        String sha256 = row.get("model_sha256").isNull() ? null : text(row.get("model_sha256"), "model_sha256");
        FixedContactForecast.FallbackReason fallback = row.get("fallback_reason").isNull() ? null : fallback(text(row.get("fallback_reason"), "fallback_reason"));
        ResearchEnvelope.SelectedCommanders selected = null; JsonNode selectedNode = row.get("selected_commander_character_ids");
        if (!selectedNode.isNull()) {
            var pair = elements(selectedNode, "selected_commander_character_ids"); require(pair.size() == 2, "selected commander pair required");
            selected = new ResearchEnvelope.SelectedCommanders(pair.get(0).isNull() ? null : characterId(pair.get(0), "attacker selected commander"),
                    pair.get(1).isNull() ? null : characterId(pair.get(1), "defender selected commander"));
        }
        return new FixedContactForecast.AdvantageInput(source, raw, sha256, fallback, selected, ids(row.get("selected_commander_army_ids"), "selected commander army IDs"));
    }
    private static ConstructorAdvantage.Source source(String wire) {
        for (var value : ConstructorAdvantage.Source.values()) if (value.wire().equals(wire)) return value;
        throw new CombatInputException("unknown advantage source");
    }
    private static FixedContactForecast.UnavailableReason reason(String wire) {
        for (var value : FixedContactForecast.UnavailableReason.values()) if (value.wire().equals(wire)) return value;
        throw new CombatInputException("unknown forecast status");
    }
    private static FixedContactForecast.ModelError modelError(String wire) {
        for (var value : FixedContactForecast.ModelError.values()) if (value.wire().equals(wire)) return value;
        throw new CombatInputException("unknown model error");
    }
    private static FixedContactForecast.FallbackReason fallback(String wire) {
        for (var value : FixedContactForecast.FallbackReason.values()) if (value.wire().equals(wire)) return value;
        throw new CombatInputException("unknown fallback reason");
    }
    private static void exactFields(ObjectNode row, List<String> fields) {
        require(row.size() == fields.size() && fields.stream().allMatch(row::has), "forecast fields differ: missing or unknown field");
    }
    private static double number(JsonNode node, String name) {
        require(node != null && node.isNumber() && Double.isFinite(node.doubleValue()), name + " must be finite numeric");
        return node.doubleValue();
    }
    private static Double nullableNumber(JsonNode node, String name) { return node.isNull() ? null : number(node, name); }
    private static boolean probability(double value) { return Double.isFinite(value) && value >= 0 && value <= 1; }
    private static void boundedText(String value, String name) { require(value != null && !value.isBlank() && value.length() <= 4096, name + " must be bounded text"); }
    private static List<String> stringList(JsonNode node, String name) { return elements(node, name).stream().map(value -> text(value, name)).toList(); }
    private static ArrayNode stringArray(List<String> values) { var row = array(); values.forEach(row::add); return row; }
    private static void nullable(ObjectNode row, String name, Double value) { if (value == null) row.putNull(name); else row.put(name, value); }
}
