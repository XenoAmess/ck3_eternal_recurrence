package org.xar.ck3.control.g2.m0;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.Comparison;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.ContinueOption;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.Decision;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.Immediate;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.ImmediateOption;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.Input;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.Power;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.PowerRelation;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.TailParameters;
import org.xar.ck3.control.g2.m0.RaiktorThreeWayEvaluation.Terminal;

/** Typed projection of the real recommendation's already-normalized input stage, with no submission API. */
public final class RaiktorRecommendationInputCodec {
    private static final BigInteger I64_MAX = BigInteger.valueOf(Long.MAX_VALUE);
    private static final BigInteger UINT64_MAX = StrictJson.UINT64_MAX;
    private static final Set<String> FRAME_KEYS = Set.of("snapshot_id", "snapshot_revision", "native_revision", "date_raw",
            "connection_id", "episode_id", "ck3_pid", "paused", "war_id", "active_casus_belli_database_index",
            "active_casus_belli_key", "primary_attacker_character_id", "primary_defender_character_id", "claimant_character_id");
    private RaiktorRecommendationInputCodec() { }

    public static Input decode(byte[] raw) {
        ObjectNode root = StrictJson.object(StrictJson.parse(raw), Set.of("immediate_certificate", "normalized_power", "model", "terminal_control"));
        ObjectNode immediate = object(root.get("immediate_certificate"));
        require(integer(immediate.get("schema_version")).equals(BigInteger.valueOf(4)), "immediate schema version drifted");
        require(text(immediate.get("contract")).equals("raiktor-white-peace-vs-surrender-utility-evaluation-v4"),
                "immediate contract drifted");
        require(text(immediate.get("utility_unit")).equals("strategy_utility_q100000"), "utility unit drifted");
        require(Set.of("pairwise_preference_available", "pairwise_underdetermined").contains(text(immediate.get("status"))),
                "immediate evaluation unavailable");
        ObjectNode frameNode = StrictJson.object(immediate.get("frame"), FRAME_KEYS);
        M0Frame frame = decodeFrame(frameNode);
        ObjectNode immediateOptions = StrictJson.object(immediate.get("options"), Set.of("white_peace", "surrender"));
        Immediate i = new Immediate(frame, option(immediateOptions.get("white_peace")), option(immediateOptions.get("surrender")),
                nonnegative(object(immediate.get("comparison")).get("minimum_switch_margin_raw")), bool(immediate.get("production_live_inputs")));

        ObjectNode normalized = RaiktorCampaignDominanceProducer.normalizeCertificate(root.get("normalized_power"));
        BigInteger powerVersion = integer(normalized.get("schema_version"));
        require(powerVersion.equals(BigInteger.TWO) || powerVersion.equals(BigInteger.valueOf(3)), "power schema drifted");
        String powerContract = powerVersion.equals(BigInteger.TWO) ? "raiktor-campaign-dominance-certificate-v2"
                : "raiktor-campaign-dominance-checkpoint-replay-certificate-v3";
        require(text(normalized.get("contract")).equals(powerContract) && text(normalized.get("status")).equals("complete"),
                "power certificate identity drifted");
        ObjectNode powerFrame = object(normalized.get("frame"));
        requirePowerFrame(frameNode, powerFrame);
        ObjectNode power = object(normalized.get("power"));
        BigInteger actor = positive64(power.get("actor_power_total_raw"));
        BigInteger target = positive64(power.get("target_power_total_raw"));
        BigInteger scale = BigInteger.valueOf(StrictJson.integer(power.get("fixed_point_scale"), 1, Integer.MAX_VALUE));
        BigInteger ratio = positive64(power.get("actual_power_ratio_raw"));
        require(ratio.equals(target.multiply(scale).divide(actor)), "measured power ratio disagrees with totals");
        PowerRelation relation = relation(text(power.get("relation")));
        PowerRelation expected = target.compareTo(actor) > 0 ? PowerRelation.OPPONENT_STRONGER
                : target.compareTo(actor) < 0 ? PowerRelation.ACTOR_STRONGER : PowerRelation.EQUAL;
        require(relation == expected && integer(power.get("target_minus_actor_raw")).equals(target.subtract(actor)),
                "measured power relation disagrees with totals");
        ObjectNode producer = object(normalized.get("producer"));
        Power p = new Power(frame, relation, ratio, scale, bool(producer.get("production_live_input")));

        ObjectNode model = object(root.get("model"));
        require(integer(model.get("schema_version")).equals(BigInteger.TWO)
                && text(model.get("contract")).equals("raiktor-strategy-exit-utility-model-v2")
                && text(model.get("status")).equals("complete")
                && text(model.get("utility_unit")).equals("strategy_utility_q100000")
                && bool(model.get("model_production_eligible")), "source strategy model unavailable");
        ObjectNode tail = object(model.get("tail_risk_policy"));
        require(text(tail.get("rule_id")).equals("measured-power-relation-long-war-penalty-v2"), "tail-risk rule unsupported");
        ObjectNode parameters = StrictJson.object(tail.get("parameters_raw"), Set.of("long_war_scale_start_days",
                "opponent_stronger_continue_penalty_raw", "parity_continue_penalty_raw", "player_stronger_continue_penalty_raw"));
        TailParameters m = new TailParameters(nonnegative(parameters.get("long_war_scale_start_days")),
                nonnegative(parameters.get("opponent_stronger_continue_penalty_raw")), nonnegative(parameters.get("parity_continue_penalty_raw")),
                nonnegative(parameters.get("player_stronger_continue_penalty_raw")));

        ObjectNode terminal = object(root.get("terminal_control"));
        require(integer(terminal.get("schema_version")).equals(BigInteger.TWO)
                && text(terminal.get("contract")).equals("raiktor-opponent-terminal-control-v2")
                && text(terminal.get("status")).equals("complete"), "terminal-control identity drifted");
        require(frameNode.equals(terminal.get("frame")), "terminal-control input crossed the complete paused frame");
        require(text(terminal.get("player_side")).equals("attacker") && bool(terminal.get("player_is_primary_war_leader"))
                && bool(terminal.get("absolute_war_scores_observable")), "primary attacker observation unavailable");
        String sourceHash = text(terminal.get("source_options_query_sha256"));
        require(sourceHash.matches("[0-9a-fA-F]{64}"), "terminal-control source hash malformed");
        BigInteger playerScore = integer(terminal.get("player_relative_war_score"));
        BigInteger attackerScore = integer(terminal.get("attacker_war_score"));
        BigInteger defenderScore = integer(terminal.get("defender_war_score"));
        require(playerScore.equals(attackerScore) && defenderScore.equals(attackerScore.negate()), "terminal-control scores disagree");
        boolean control = bool(terminal.get("opponent_terminal_control"));
        require(control == (playerScore.compareTo(BigInteger.valueOf(-100)) <= 0), "terminal-control classification drifted");
        Terminal t = new Terminal(frame, playerScore, attackerScore, defenderScore, nonnegative(terminal.get("war_duration_days")),
                control, bool(object(terminal.get("producer")).get("production_live_input")));
        return new Input(i, p, m, t);
    }

    public static byte[] execute(byte[] raw) {
        Decision value;
        try { value = RaiktorThreeWayEvaluation.evaluate(decode(raw)); }
        catch (IllegalArgumentException invalidInput) { throw new InputRejected(invalidInput.getMessage(), invalidInput); }
        ObjectNode result = StrictJson.object();
        result.set("continue_option", encode(value.continueOption()));
        result.set("comparison", encode(value.comparison()));
        return StrictJson.canonical(result);
    }

    /** Finite test transport: each request actually invokes the leaf; internal/encoding failures end the process. */
    public static void main(String[] args) throws Exception {
        require(args.length == 1 && args[0].equals("--stdio"), "only --stdio transport supported");
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                byte[] output;
                try { output = execute(line.getBytes(StandardCharsets.UTF_8)); }
                catch (InputRejected invalidInput) {
                    ObjectNode rejected = StrictJson.object(); rejected.put("rejected", true);
                    rejected.put("message", invalidInput.getMessage()); output = StrictJson.canonical(rejected);
                }
                System.out.write(output); System.out.write('\n'); System.out.flush();
            }
        }
    }

    public static final class InputRejected extends IllegalArgumentException {
        private static final long serialVersionUID = 1L;
        private InputRejected(String message, IllegalArgumentException cause) { super(message, cause); }
    }

    private static ObjectNode encode(ContinueOption c) {
        ObjectNode n = StrictJson.object();
        n.put("measured_power_relation", c.measuredPowerRelation().wire()); n.put("base_utility_raw", c.baseUtilityRaw());
        n.put("tail_risk_penalty_raw", c.tailRiskPenaltyRaw()); n.put("tail_risk_base_penalty_raw", c.tailRiskBasePenaltyRaw());
        n.put("tail_risk_power_scale_applied", c.tailRiskPowerScaleApplied());
        n.put("tail_risk_long_war_scale_start_days", c.tailRiskLongWarScaleStartDays());
        n.put("observed_war_duration_days", c.observedWarDurationDays()); n.put("observed_player_relative_war_score", c.observedPlayerRelativeWarScore());
        n.put("measured_power_ratio_raw", c.measuredPowerRatioRaw()); n.put("measured_power_ratio_scale", c.measuredPowerRatioScale());
        n.put("utility_raw", c.utilityRaw()); strings(n, "hard_budget_breaches", c.hardBudgetBreaches());
        strings(n, "execution_blockers", c.executionBlockers()); n.put("eligible", c.eligible());
        n.put("campaign_outcome_forecast_ready", c.campaignOutcomeForecastReady()); return n;
    }
    private static ObjectNode encode(Comparison c) {
        ObjectNode n = StrictJson.object(); n.put("status", c.status().wire());
        var eligible = n.putArray("eligible_options"); c.eligibleOptions().forEach(value -> eligible.add(value.wire()));
        if (c.recommendedOutcome().isPresent()) { n.put("recommended_outcome", c.recommendedOutcome().orElseThrow().wire()); }
        else { n.putNull("recommended_outcome"); }
        if (c.winningMarginRaw().isPresent()) { n.put("winning_margin_raw", c.winningMarginRaw().orElseThrow()); }
        else { n.putNull("winning_margin_raw"); }
        n.put("minimum_switch_margin_raw", c.minimumSwitchMarginRaw()); return n;
    }
    private static void strings(ObjectNode node, String key, List<String> values) {
        var array = node.putArray(key); values.forEach(array::add);
    }
    private static ImmediateOption option(JsonNode value) {
        ObjectNode option = object(value);
        strings(option.get("execution_blockers"));
        return new ImmediateOption(integer(option.get("utility_raw")), bool(option.get("eligible")), strings(option.get("hard_budget_breaches")));
    }
    static M0Frame decodeFrame(JsonNode value) {
        ObjectNode n = StrictJson.object(value, FRAME_KEYS);
        require(bool(n.get("paused")), "paused frame required");
        return new M0Frame(text(n.get("snapshot_id")), StrictJson.integer(n.get("snapshot_revision"), BigInteger.ONE, UINT64_MAX),
                StrictJson.integer(n.get("native_revision"), BigInteger.ONE, UINT64_MAX), int32(n.get("date_raw")),
                text(n.get("connection_id")), text(n.get("episode_id")), (int) StrictJson.integer(n.get("ck3_pid"), 1, Integer.MAX_VALUE),
                true, fullId(n.get("war_id")), (int) StrictJson.integer(n.get("active_casus_belli_database_index"), 0, Integer.MAX_VALUE),
                text(n.get("active_casus_belli_key")), fullId(n.get("primary_attacker_character_id")), fullId(n.get("primary_defender_character_id")),
                fullId(n.get("claimant_character_id")));
    }
    private static void requirePowerFrame(ObjectNode immediate, ObjectNode power) {
        String connection = text(immediate.get("connection_id"));
        require(connection.matches("connection-generation:[0-9]+"), "connection generation unavailable");
        BigInteger generation = new BigInteger(connection.substring("connection-generation:".length()));
        for (String key : List.of("snapshot_id", "snapshot_revision", "native_revision", "date_raw", "ck3_pid", "war_id")) {
            require(immediate.get(key).equals(power.get(key)), "power crossed paused frame: " + key);
        }
        require(generation.equals(positive64(power.get("connection_generation")))
                && immediate.get("episode_id").equals(power.get("episode_run_id"))
                && immediate.get("primary_attacker_character_id").equals(power.get("actor_character_id"))
                && immediate.get("primary_defender_character_id").equals(power.get("opponent_character_id"))
                && bool(power.get("paused")), "power crossed paused episode/actor/connection");
    }
    private static PowerRelation relation(String value) {
        for (PowerRelation candidate : PowerRelation.values()) { if (candidate.wire().equals(value)) { return candidate; } }
        throw new IllegalArgumentException("unsupported measured power relation");
    }
    private static ObjectNode object(JsonNode n) { require(n instanceof ObjectNode, "explicit JSON object required"); return (ObjectNode) n; }
    private static BigInteger integer(JsonNode n) { require(n != null && n.isIntegralNumber(), "exact JSON integer required"); return n.bigIntegerValue(); }
    private static BigInteger nonnegative(JsonNode n) { BigInteger v = integer(n); require(v.signum() >= 0, "nonnegative integer required"); return v; }
    private static BigInteger positive64(JsonNode n) { return StrictJson.integer(n, BigInteger.ONE, I64_MAX); }
    private static int int32(JsonNode n) { return (int) StrictJson.integer(n, Integer.MIN_VALUE, Integer.MAX_VALUE); }
    private static int fullId(JsonNode n) { int v = int32(n); require(v != -1, "null full-generation identity refused"); return v; }
    private static boolean bool(JsonNode n) { require(n != null && n.isBoolean(), "exact JSON boolean required"); return n.booleanValue(); }
    private static String text(JsonNode n) { String s = StrictJson.text(n); require(!s.strip().isEmpty(), "nonempty text required"); return s; }
    private static List<String> strings(JsonNode n) {
        require(n != null && n.isArray(), "explicit string list required"); List<String> result = new ArrayList<>();
        n.forEach(value -> result.add(text(value))); return List.copyOf(result);
    }
}
