package org.xar.ck3.control.wave2.military.forecast;

import static org.xar.ck3.control.wave2.military.forecast.CombatJson.*;
import static org.xar.ck3.control.wave2.military.forecast.CombatNumbers.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.wave2.military.combatwire.CombatSimulationInputs;
import org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputs;

/** Decision-facing whole-battle distribution; fidelity and unresolved outcomes remain explicit. */
public final class FixedContactForecast {
    private FixedContactForecast() { }
    public static final int DEFAULT_SAMPLE_COUNT = 256;
    public static final int DEFAULT_HORIZON_DAYS = 120;
    private static final List<String> ASSUMPTIONS = List.of("phase_events_disabled", "no_voluntary_retreat", "fixed_participants", "unobserved_modifiers_omitted", "future_daily_effective_stat_refresh_unmodeled", "future_daily_combat_width_refresh_unmodeled", "future_daily_non_roll_advantage_refresh_unmodeled");
    public record Request(BigInteger targetProvinceId, BigInteger attackerEntryProvinceId,
            List<BigInteger> attackerArmyIds, List<BigInteger> defenderArmyIds, CombatInputs.Capture capture,
            int sampleCount, int horizonDays) {
        public Request {
            require(targetProvinceId != null && positive(targetProvinceId) && (attackerEntryProvinceId == null || positive(attackerEntryProvinceId)), "positive contact province IDs required");
            attackerArmyIds = checkedIds(attackerArmyIds); defenderArmyIds = checkedIds(defenderArmyIds);
            require(attackerArmyIds.stream().noneMatch(defenderArmyIds::contains), "army repeated across contact sides");
            Objects.requireNonNull(capture);
            if (sampleCount < 1 || sampleCount > 4096 || horizonDays < 1 || horizonDays > 365) throw new IllegalArgumentException("forecast budget outside bounded strategy range");
        }
        public Request(BigInteger targetProvinceId, BigInteger attackerEntryProvinceId, List<BigInteger> attackerArmyIds, List<BigInteger> defenderArmyIds, CombatInputs.Capture capture) {
            this(targetProvinceId, attackerEntryProvinceId, attackerArmyIds, defenderArmyIds, capture, DEFAULT_SAMPLE_COUNT, DEFAULT_HORIZON_DAYS);
        }
        public ObjectNode toJson() {
            var row = object(); row.put("target_province_id", targetProvinceId); putNullable(row, "attacker_entry_province_id", attackerEntryProvinceId);
            row.set("attacker_army_ids", idArray(attackerArmyIds)); row.set("defender_army_ids", idArray(defenderArmyIds)); row.set("capture", capture.source()); row.put("sample_count", sampleCount); row.put("horizon_days", horizonDays); return row;
        }
        public static Request fromJson(JsonNode value) {
            var row = object(value, "forecast request");
            row.fieldNames().forEachRemaining(name -> require(List.of("target_province_id", "attacker_entry_province_id", "attacker_army_ids", "defender_army_ids", "capture", "sample_count", "horizon_days").contains(name), "unknown forecast request field: " + name));
            require(row.has("attacker_entry_province_id"), "attacker_entry_province_id must be explicit, including null");
            return new Request(positiveInteger(row.get("target_province_id"), "target province"), absentOrNull(row.get("attacker_entry_province_id")) ? null : positiveInteger(row.get("attacker_entry_province_id"), "attacker entry"),
                    ids(row.get("attacker_army_ids"), "attacker IDs"), ids(row.get("defender_army_ids"), "defender IDs"), new CombatInputs.Capture(object(row.get("capture"), "capture")),
                    row.has("sample_count") ? intValue(row.get("sample_count"), "sample_count") : DEFAULT_SAMPLE_COUNT,
                    row.has("horizon_days") ? intValue(row.get("horizon_days"), "horizon_days") : DEFAULT_HORIZON_DAYS);
        }
    }
    private static List<BigInteger> checkedIds(List<BigInteger> values) {
        Objects.requireNonNull(values); var result = List.copyOf(values);
        require(!result.isEmpty() && result.stream().distinct().count() == result.size(), "distinct public participant IDs required");
        for (BigInteger value : result) publicCunitId(value, "public participant ID"); return result;
    }
    public enum UnavailableReason {
        INPUT_OR_ENCOUNTER_MISMATCH("input_or_encounter_mismatch"), ACTIVE_COMBAT_REQUIRES_RESUME_INPUT("active_combat_requires_resume_input"), PARTICIPANT_ROLE_UNAVAILABLE("participant_role_unavailable"), MODEL_UNAVAILABLE("model_unavailable");
        private final String wire; UnavailableReason(String wire) { this.wire = wire; } public String wire() { return wire; }
    }
    public enum ModelError {
        COMBAT_INPUT_ERROR("CombatInputError"), VALUE_ERROR("ValueError"), RUNTIME_ERROR("RuntimeError"), TYPE_ERROR("TypeError");
        private final String wire; ModelError(String wire) { this.wire = wire; } public String wire() { return wire; }
    }
    public enum FallbackReason {
        PHASE_UNAVAILABLE("phase_event_inputs_unavailable"), PHASE_NOT_IN_PAYLOAD("native_phase_not_in_payload");
        private final String wire; FallbackReason(String wire) { this.wire = wire; } public String wire() { return wire; }
    }
    public record AdvantageInput(ConstructorAdvantage.Source source, BigInteger zeroRollRaw, String modelSha256,
            FallbackReason fallbackReason, ResearchEnvelope.SelectedCommanders selectedCommanderCharacterIds,
            List<BigInteger> selectedCommanderArmyIds) {
        public AdvantageInput {
            Objects.requireNonNull(source); selectedCommanderArmyIds = checkedIds(selectedCommanderArmyIds);
            require(selectedCommanderArmyIds.size() == 2, "commander army pair required");
            boolean nativeInput = source != ConstructorAdvantage.Source.GENERIC;
            require(nativeInput == (zeroRollRaw != null) && nativeInput == (modelSha256 != null) && nativeInput == (selectedCommanderCharacterIds != null) && nativeInput == (fallbackReason == null), "native advantage provenance is incomplete");
            if (nativeInput) {
                require(zeroRollRaw.bitLength() <= 63 && modelSha256.matches("[0-9A-F]{64}"), "native advantage raw/hash malformed");
                ConstructorAdvantage.requireSelectedCharacters(source, selectedCommanderCharacterIds);
            }
        }
        public ObjectNode toJson() {
            var row = object(); row.put("source", source.wire());
            if (source == ConstructorAdvantage.Source.V2_CONSTRUCTOR) { row.put("scope", "hypothetical_constructor_context"); row.put("complete_encounter_advantage_ready", false); }
            putNullable(row, "zero_roll_raw", zeroRollRaw); putNullable(row, "model_sha256", modelSha256); putNullable(row, "fallback_reason", fallbackReason == null ? null : fallbackReason.wire());
            if (selectedCommanderCharacterIds == null) row.putNull("selected_commander_character_ids");
            else { var selected = array(); addNullable(selected, selectedCommanderCharacterIds.attackerCharacterId()); addNullable(selected, selectedCommanderCharacterIds.defenderCharacterId()); row.set("selected_commander_character_ids", selected); }
            row.set("selected_commander_army_ids", idArray(selectedCommanderArmyIds)); row.put("future_daily_refresh_modeled", false); return row;
        }
    }
    public sealed interface Forecast permits Estimated, Unavailable {
        ObjectNode toJson();
        default ForecastWireCodec.Message toWire() { return ForecastWireCodec.fromForecast(this); }
    }
    public record Unavailable(UnavailableReason reason, ModelError errorType) implements Forecast {
        public Unavailable { Objects.requireNonNull(reason); require((reason == UnavailableReason.MODEL_UNAVAILABLE) == (errorType != null), "model unavailable error type must be explicit"); }
        public Unavailable(UnavailableReason reason) { this(reason, null); }
        @Override public ObjectNode toJson() { var row = object(); row.put("status", reason.wire()); if (errorType != null) row.put("error_type", errorType.wire()); return row; }
    }
    public record Estimated(CombatCore.Summary summary, int horizonDays, AdvantageInput advantageInput,
            Double playerP90HardLossFraction, CombatInputs.Capture capture) implements Forecast {
        public Estimated {
            Objects.requireNonNull(summary); Objects.requireNonNull(advantageInput); Objects.requireNonNull(capture);
            require(horizonDays > 0 && horizonDays <= 365, "invalid forecast horizon");
            require(summary.sampleCount() >= 1 && summary.sampleCount() <= 4096 && summary.playerWins() >= 0 && summary.playerLosses() >= 0 && summary.noResolution() >= 0
                    && (long) summary.playerWins() + summary.playerLosses() + summary.noResolution() == summary.sampleCount(), "forecast distribution census differs");
            require(playerP90HardLossFraction == null || Double.isFinite(playerP90HardLossFraction) && playerP90HardLossFraction >= 0, "finite nonnegative hard loss fraction required");
        }
        public List<String> assumptions() { return FixedContactForecast.assumptions(advantageInput); }
        @Override public ObjectNode toJson() {
            var row = object(); row.put("status", "estimated"); row.put("model_fidelity", summary.modelFidelity()); row.put("native_parity", summary.fidelityGate()); row.put("input_sha256", summary.inputSha256().toUpperCase(Locale.ROOT)); row.put("simulator_build", summary.simulatorBuild()); row.put("sample_count", summary.sampleCount()); row.put("horizon_days", horizonDays); row.set("advantage_input", advantageInput.toJson());
            row.put("player_wins", summary.playerWins()); row.put("player_losses", summary.playerLosses()); row.put("no_resolution", summary.noResolution()); putNullable(row, "player_win_probability_resolved", summary.playerWinProbabilityResolved());
            row.put("player_win_probability_unconditional_lower", (double) summary.playerWins() / summary.sampleCount()); row.put("player_win_probability_unconditional_upper", (double) (summary.playerWins() + summary.noResolution()) / summary.sampleCount());
            if (summary.playerWinWilson95() == null) row.putNull("resolved_win_wilson95"); else { var interval = object(); interval.put("lower", summary.playerWinWilson95().lower()); interval.put("upper", summary.playerWinWilson95().upper()); row.set("resolved_win_wilson95", interval); }
            putNullable(row, "player_p90_hard_loss_raw", summary.playerHardLossesRaw().p90()); putNullable(row, "player_p90_hard_loss_fraction", playerP90HardLossFraction); row.put("player_stack_wipe_probability", summary.playerStackWipeProbability());
            row.putNull("commander_or_knight_death_probability"); row.put("character_death_risk_status", "unmodeled_phase_events"); row.set("missing_required_domains", strings(summary.missingRequiredDomains())); row.set("assumptions", strings(assumptions())); row.set("capture", capture.source()); return row;
        }
    }
    static List<String> assumptions(AdvantageInput advantageInput) {
        Objects.requireNonNull(advantageInput); var result = new ArrayList<>(ASSUMPTIONS);
        if (advantageInput.zeroRollRaw() != null) result.add("same_frame_native_advantage_frozen_for_future_days");
        return List.copyOf(result);
    }
    private record CacheKey(CombatInputs.Frozen frozen, BigInteger attackerCommanderArmyId, BigInteger defenderCommanderArmyId,
            BigInteger nativeZeroRollRaw, ResearchEnvelope.SelectedCommanders nativeSelectedCommanders, int sampleCount, int horizonDays) { }
    private static final Map<CacheKey, CombatCore.Summary> CACHE = new LinkedHashMap<>(32, .75f, true);
    private static CombatCore.Summary runCached(CacheKey key) {
        synchronized (CACHE) {
            CombatCore.Summary previous = CACHE.get(key); if (previous != null) return previous;
            var experiment = new CombatCore.Experiment(key.frozen().inputSha256(), new BigInteger(key.frozen().inputSha256().substring(0, 16), 16), key.sampleCount(), key.horizonDays());
            var assumptions = new ResearchEnvelope.Assumptions(key.attackerCommanderArmyId(), key.defenderCommanderArmyId(), key.nativeZeroRollRaw(), key.nativeSelectedCommanders());
            var result = ResearchEnvelope.run(key.frozen(), experiment, assumptions, 1, 4); CACHE.put(key, result);
            if (CACHE.size() > 24) { var eldest = CACHE.keySet().iterator(); eldest.next(); eldest.remove(); } return result;
        }
    }
    private static boolean version(JsonNode payload, int version) { JsonNode value = field(payload, "schema_version"); return value != null && value.isIntegralNumber() && value.bigIntegerValue().equals(n(version)); }
    private static boolean sameId(JsonNode node, BigInteger expected) { return expected == null ? absentOrNull(node) : node != null && node.isIntegralNumber() && expected.equals(node.bigIntegerValue()); }
    private static boolean sameIds(JsonNode node, List<BigInteger> expected) { try { return node != null && node.isArray() && !node.isEmpty() && ids(node, "participant IDs").equals(expected); } catch (CombatInputException error) { return false; } }
    public static Forecast forecast(CombatSimulationInputs normalized, Request request) { return forecast(Objects.requireNonNull(normalized).toJson(), request); }
    public static Forecast forecast(CombatPhaseInputs normalized, Request request) { return forecast(Objects.requireNonNull(normalized).toJson(), request); }
    public static Forecast forecast(JsonNode payload, Request request) {
        Objects.requireNonNull(request);
        JsonNode declaredSchema = field(payload, "schema_version");
        if (declaredSchema != null && !declaredSchema.isIntegralNumber()) return new Unavailable(UnavailableReason.INPUT_OR_ENCOUNTER_MISMATCH);
        JsonNode base = field(payload, "base_inputs"), scenario = field(base, "scenario");
        boolean ready = yes(field(field(payload, "completeness"), "input_observation_ready"))
                || version(payload, 3) && is(field(payload, "contract_stage"), "production_exact_132_refs") && yes(field(field(base, "completeness"), "input_observation_ready"));
        if (!(ready && base != null && base.isObject() && scenario != null && scenario.isObject()
                && sameId(base.get("target_province_id"), request.targetProvinceId()) && sameId(scenario.get("attacker_entry_province_id"), request.attackerEntryProvinceId())
                && sameIds(scenario.get("attacker_army_ids"), request.attackerArmyIds()) && sameIds(scenario.get("defender_army_ids"), request.defenderArmyIds()) && no(scenario.get("actual_route_dependency")))) return new Unavailable(UnavailableReason.INPUT_OR_ENCOUNTER_MISMATCH);
        JsonNode ongoing = base.get("ongoing_combats"); if (ongoing == null || !ongoing.isArray()) return new Unavailable(UnavailableReason.INPUT_OR_ENCOUNTER_MISMATCH);
        if (!ongoing.isEmpty()) return new Unavailable(UnavailableReason.ACTIVE_COMBAT_REQUIRES_RESUME_INPUT);
        try {
            var frozen = CombatInputs.freeze(base, request.capture()); var nativeInput = ConstructorAdvantage.readV3(payload, frozen);
            if (nativeInput.isEmpty() && version(payload, 2)) nativeInput = ConstructorAdvantage.readV2(payload, frozen);
            List<BigInteger> leaders; BigInteger raw; ResearchEnvelope.SelectedCommanders selected; AdvantageInput advantage;
            if (nativeInput.isPresent()) {
                var observation = nativeInput.orElseThrow(); leaders = observation.leaderArmyIds(); raw = observation.zeroRollRaw(); selected = observation.selectedCommanders();
                advantage = new AdvantageInput(observation.source(), raw, observation.modelSha256(), null, selected, leaders);
            } else {
                var picked = new ArrayList<BigInteger>();
                for (var role : List.of(CombatInputs.Role.ATTACKER, CombatInputs.Role.DEFENDER)) {
                    var armies = frozen.armies().stream().filter(army -> army.encounterRole() == role).toList();
                    if (armies.isEmpty()) return new Unavailable(UnavailableReason.PARTICIPANT_ROLE_UNAVAILABLE);
                    var leader = armies.stream().max(Comparator.comparing(CombatInputs.Army::currentSoldiers).thenComparing(army -> army.publicArmyId().negate())).orElseThrow(); picked.add(leader.publicArmyId());
                }
                leaders = List.copyOf(picked); raw = null; selected = null;
                JsonNode phase = field(payload, "phase_event_inputs"); advantage = new AdvantageInput(ConstructorAdvantage.Source.GENERIC, null, null, phase != null && phase.isObject() ? FallbackReason.PHASE_UNAVAILABLE : FallbackReason.PHASE_NOT_IN_PAYLOAD, null, leaders);
            }
            var summary = runCached(new CacheKey(frozen, leaders.get(0), leaders.get(1), raw, selected, request.sampleCount(), request.horizonDays()));
            BigInteger playerSoldiers = ZERO; for (var army : frozen.armies()) if (army.coalitionSide() == CombatInputs.Coalition.PLAYER_OR_ALLIED) playerSoldiers = playerSoldiers.add(army.currentSoldiers());
            BigInteger p90 = summary.playerHardLossesRaw().p90(); Double fraction = p90 != null && positive(playerSoldiers) ? CombatCore.ratio(p90, playerSoldiers.multiply(SCALE)) : null;
            return new Estimated(summary, request.horizonDays(), advantage, fraction, request.capture());
        } catch (CombatInputException error) { return new Unavailable(UnavailableReason.MODEL_UNAVAILABLE, ModelError.COMBAT_INPUT_ERROR); }
        catch (IllegalArgumentException error) { return new Unavailable(UnavailableReason.MODEL_UNAVAILABLE, ModelError.VALUE_ERROR); }
        catch (IllegalStateException error) { return new Unavailable(UnavailableReason.MODEL_UNAVAILABLE, ModelError.RUNTIME_ERROR); }
    }
    public sealed interface Admission permits RejectedAdmission, BudgetAdmission { ObjectNode toJson(); boolean admitted(); }
    public enum RejectionReason {
        NO_CONTACT_ESTIMATE("no_contact_estimate"), INCOMPLETE_DISTRIBUTION("incomplete_distribution"), INVALID_CHARACTER_DEATH_RISK("invalid_character_death_risk");
        private final String wire; RejectionReason(String wire) { this.wire = wire; } public String wire() { return wire; }
    }
    public record RejectedAdmission(RejectionReason reason) implements Admission {
        public RejectedAdmission { Objects.requireNonNull(reason); }
        @Override public boolean admitted() { return false; }
        @Override public ObjectNode toJson() { var row = object(); row.put("admitted", false); row.put("reason", reason.wire()); return row; }
    }
    public record RiskLimits(double winLower, double hardLoss, double wipe, Double death) {
        public RiskLimits { require(unitInterval(winLower) && unitInterval(hardLoss) && unitInterval(wipe) && (death == null || unitInterval(death)), "risk limits must be finite probabilities"); }
        public ObjectNode toJson() { var row = object(); row.put("win_lower", winLower); row.put("hard_loss", hardLoss); row.put("wipe", wipe); putNullable(row, "death", death); return row; }
    }
    public record BudgetAdmission(boolean admitted, RiskLimits riskLimits, boolean characterDeathRiskModeled,
            List<String> unquantifiedRisks) implements Admission {
        public BudgetAdmission { Objects.requireNonNull(riskLimits); unquantifiedRisks = List.copyOf(unquantifiedRisks); require(characterDeathRiskModeled == (riskLimits.death() != null), "death risk limit and model status differ"); }
        @Override public ObjectNode toJson() { var row = object(); row.put("admitted", admitted); row.put("reason", admitted ? "within_bounded_model_risk_budget" : "bounded_model_risk_budget_exceeded"); row.set("risk_limits", riskLimits.toJson()); row.put("character_death_risk_modeled", characterDeathRiskModeled); row.set("unquantified_risks", strings(unquantifiedRisks)); row.put("native_parity_required", false); return row; }
    }
    public static Admission contactAdmission(Forecast forecast, boolean defensiveRelief) { Objects.requireNonNull(forecast); return contactAdmission(forecast.toJson(), defensiveRelief); }
    public static Admission contactAdmission(Forecast forecast) { return contactAdmission(forecast, false); }
    public static Admission contactAdmission(JsonNode forecast, boolean defensiveRelief) {
        if (!is(field(forecast, "status"), "estimated")) return new RejectedAdmission(RejectionReason.NO_CONTACT_ESTIMATE);
        JsonNode lowerNode = field(field(forecast, "resolved_win_wilson95"), "lower"), lossNode = field(forecast, "player_p90_hard_loss_fraction"), wipeNode = field(forecast, "player_stack_wipe_probability"), unresolvedNode = field(forecast, "no_resolution"), countNode = field(forecast, "sample_count"), deathNode = field(forecast, "commander_or_knight_death_probability");
        if (!finiteNumber(lowerNode) || !finiteNumber(lossNode) || !finiteNumber(wipeNode) || unresolvedNode == null || !unresolvedNode.isIntegralNumber() || countNode == null || !countNode.isIntegralNumber()) return new RejectedAdmission(RejectionReason.INCOMPLETE_DISTRIBUTION);
        boolean deathModeled = finiteNumber(deathNode);
        if (!absentOrNull(deathNode) && (!deathModeled || !unitInterval(deathNode.doubleValue()))) return new RejectedAdmission(RejectionReason.INVALID_CHARACTER_DEATH_RISK);
        double lower = lowerNode.doubleValue(), loss = lossNode.doubleValue(), wipe = wipeNode.doubleValue(); BigInteger unresolved = unresolvedNode.bigIntegerValue(), count = countNode.bigIntegerValue();
        // JSON is an external boundary. Negative risks/censuses must never grant admission.
        if (!unitInterval(lower) || loss < 0 || !unitInterval(wipe) || count.signum() <= 0
                || count.compareTo(BigInteger.valueOf(4096)) > 0 || unresolved.signum() < 0 || unresolved.compareTo(count) > 0)
            return new RejectedAdmission(RejectionReason.INCOMPLETE_DISTRIBUTION);
        double winLimit = defensiveRelief ? .70 : .65, lossLimit = defensiveRelief ? .20 : .25, wipeLimit = defensiveRelief ? .02 : .05, deathLimit = defensiveRelief ? .02 : .05;
        boolean admitted = count.signum() > 0 && CombatCore.ratio(unresolved, count) <= .10 && lower >= winLimit && loss <= lossLimit && wipe <= wipeLimit && (!deathModeled || deathNode.doubleValue() <= deathLimit);
        var unknown = new ArrayList<String>(); if (!deathModeled) unknown.add("commander_or_knight_death"); unknown.addAll(List.of("future_reinforcement_and_participant_exit", "voluntary_retreat", "future_daily_effective_stat_refresh", "future_daily_combat_width_refresh", "future_daily_non_roll_advantage_refresh"));
        return new BudgetAdmission(admitted, new RiskLimits(winLimit, lossLimit, wipeLimit, deathModeled ? deathLimit : null), deathModeled, unknown);
    }
    public static Admission contactAdmission(JsonNode forecast) { return contactAdmission(forecast, false); }
    private static boolean finiteNumber(JsonNode value) { return value != null && value.isNumber() && Double.isFinite(value.doubleValue()); }
    private static boolean unitInterval(double value) { return Double.isFinite(value) && value >= 0 && value <= 1; }
    private static ArrayNode strings(List<String> values) { var row = array(); values.forEach(row::add); return row; }
    private static ArrayNode idArray(List<BigInteger> values) { var row = array(); values.forEach(row::add); return row; }
    private static void addNullable(ArrayNode row, BigInteger value) { if (value == null) row.addNull(); else row.add(value); }
    private static void putNullable(ObjectNode row, String key, BigInteger value) { if (value == null) row.putNull(key); else row.put(key, value); }
    private static void putNullable(ObjectNode row, String key, String value) { if (value == null) row.putNull(key); else row.put(key, value); }
    private static void putNullable(ObjectNode row, String key, Double value) { if (value == null) row.putNull(key); else row.put(key, value); }
}
