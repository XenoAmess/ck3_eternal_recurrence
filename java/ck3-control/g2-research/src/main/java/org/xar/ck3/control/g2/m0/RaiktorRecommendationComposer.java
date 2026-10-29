package org.xar.ck3.control.g2.m0;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;

/** Complete recommendation receipt assembly around the sole Java utility evaluators.
 * The normalized power input retains the existing source certificate validator.
 * This receipt is not action authorization, a postcondition or a recovery ticket.
 */
public final class RaiktorRecommendationComposer {
    public static final String OPERATION = "compose-three-way-exit-recommendation";
    private static final List<String> CONTINUE = List.of("same_full_generation_war_id_remains_active",
            "same_played_character_and_episode_remain_bound", "map_resume_is_observed_on_a_successor_revision");
    private static final List<String> TERMINATE = List.of("old_full_generation_war_id_absent",
            "gold_matches_frozen_terms", "attacker_prestige_matches_frozen_terms",
            "directional_truce_days_and_expiry_observed", "source_specific_war_bound_regiments_absent",
            "postwar_checkpoint_cold_restore_rebinds_identity");
    private RaiktorRecommendationComposer() { }

    public static byte[] executeOperation(byte[] raw) {
        ObjectNode input = StrictJson.object(RaiktorExitObservationCodec.parseWire(raw),
                Set.of("operation", "white_peace_projection", "surrender_session", "normalized_power",
                        "budget_provider", "model_provider", "terminal_control"));
        require(OPERATION.equals(text(input.get("operation"))), "recommendation operation differs");
        ObjectNode immediateRequest = StrictJson.object();
        for (String key : List.of("white_peace_projection", "surrender_session", "budget_provider", "model_provider")) {
            immediateRequest.set(key, input.get(key));
        }
        ObjectNode immediate = object(RaiktorExitObservationCodec.parseWire(
                RaiktorImmediateInputCodec.execute(RaiktorExitObservationCodec.encodeWire(immediateRequest))));
        List<String> blockers = strings(immediate.get("blockers"));
        if (input.get("normalized_power").isNull()) blockers.add("measured_power_dominance_unavailable");
        if (input.get("terminal_control").isNull()) blockers.add("opponent_terminal_control_unavailable");
        if (!blockers.isEmpty()) return RaiktorExitObservationCodec.encodeWire(result(immediate, blockers, null));
        ObjectNode evaluation = object(immediate.get("evaluation_certificate"));
        ObjectNode power = object(input.get("normalized_power"));
        ObjectNode terminal = object(input.get("terminal_control"));
        ObjectNode model = object(object(input.get("model_provider")).get("exit_utility_model"));
        ObjectNode decisionRequest = StrictJson.object();
        decisionRequest.set("immediate_certificate", evaluation); decisionRequest.set("normalized_power", power);
        decisionRequest.set("model", model); decisionRequest.set("terminal_control", terminal);
        ObjectNode decision;
        try {
            decision = object(RaiktorExitObservationCodec.parseWire(
                    RaiktorRecommendationInputCodec.execute(RaiktorExitObservationCodec.encodeWire(decisionRequest))));
        } catch (IllegalArgumentException failure) {
            // Preserve the existing public recommendation diagnostic at this compatibility boundary.
            if (failure.getMessage().startsWith("power crossed paused frame:")) {
                throw new IllegalArgumentException("immediate-exit and power certificates crossed paused frames", failure);
            }
            if ("terminal-control input crossed the complete paused frame".equals(failure.getMessage())) {
                throw new IllegalArgumentException("immediate-exit and terminal-control inputs crossed paused frames", failure);
            }
            throw failure;
        }
        return RaiktorExitObservationCodec.encodeWire(result(immediate, List.of(),
                certificate(input, immediate, evaluation, power, terminal, model, decision)));
    }

    private static ObjectNode certificate(ObjectNode input, ObjectNode immediate, ObjectNode evaluation,
            ObjectNode power, ObjectNode terminal, ObjectNode model, ObjectNode decision) {
        ObjectNode frame = object(evaluation.get("frame"));
        ObjectNode options = StrictJson.object();
        options.set("continue", decision.get("continue_option"));
        ObjectNode exits = object(evaluation.get("options"));
        options.set("white_peace", exits.get("white_peace")); options.set("surrender", exits.get("surrender"));
        ObjectNode comparison = object(decision.get("comparison"));
        JsonNode outcome = comparison.get("recommended_outcome");
        boolean productionInputs = bool(immediate.get("production_live_inputs"))
                && bool(object(power.get("producer")).get("production_live_input"))
                && bool(object(terminal.get("producer")).get("production_live_input"));
        boolean ready = productionInputs && !outcome.isNull();
        String name = outcome.isNull() ? null : text(outcome);
        List<String> requirements = "continue".equals(name) ? CONTINUE
                : Set.of("white_peace", "surrender").contains(name == null ? "" : name) ? TERMINATE : List.of();
        ObjectNode c = StrictJson.object(); c.put("schema_version", 1);
        c.put("contract", "raiktor-three-way-exit-recommendation-v7");
        c.put("status", ready ? "production_recommendation_available" : text(comparison.get("status")));
        c.set("frame", frame.deepCopy()); c.put("utility_unit", "strategy_utility_q100000");
        ObjectNode hashes = c.putObject("input_sha256"); hashes.put("immediate_exit_evaluation_sha256", hash(evaluation));
        hashes.put("power_dominance_sha256", hash(power)); hashes.put("utility_model_sha256", hash(model));
        hashes.put("opponent_terminal_control_sha256", hash(terminal));
        ObjectNode control = c.putObject("opponent_terminal_control"); control.set("active", terminal.get("opponent_terminal_control"));
        for (String key : List.of("player_relative_war_score", "attacker_war_score", "defender_war_score", "war_duration_days")) {
            control.set(key, terminal.get(key));
        }
        c.set("options", options); c.set("comparison", comparison); c.put("production_live_inputs", productionInputs);
        c.put("production_recommendation_ready", ready); c.set("recommended_outcome", outcome);
        ObjectNode action = c.putObject("action_plan"); action.put("ready", ready);
        if (ready) { action.put("semantic_action", name); action.put("literal", literal(name, frame.get("war_id"))); }
        else { action.putNull("semantic_action"); action.putNull("literal"); }
        action.set("war_id", object(power.get("frame")).get("war_id")); action.put("single_action_only", true);
        c.set("postcondition_plan", postcondition(name, frame, options, input.get("surrender_session"), requirements));
        ObjectNode boundaries = c.putObject("boundaries");
        for (String key : List.of("measured_power_is_not_campaign_forecast", "continue_is_strategy_baseline_minus_tail_penalty",
                "long_losing_war_may_scale_tail_penalty_by_power_ratio", "native_execution_availability_excludes_immediate_options",
                "opponent_terminal_control_excludes_continue")) boundaries.put(key, true);
        boundaries.put("checkpoint_replay_power_input", integer(power.get("schema_version")).equals(BigInteger.valueOf(3)));
        boundaries.put("action_submitted", false); boundaries.put("postcondition_verified", false); boundaries.put("gen034_closed", false);
        c.put("certificate_sha256", hash(c)); return c;
    }

    private static ObjectNode postcondition(String outcome, ObjectNode frame, ObjectNode options,
            JsonNode session, List<String> requirements) {
        ObjectNode plan = StrictJson.object(); plan.put("schema_version", 1);
        if (outcome == null) plan.putNull("route"); else plan.put("route", outcome);
        strings(plan, "requirements", requirements); plan.putNull("expectations"); plan.put("verified", false);
        boolean exit = "white_peace".equals(outcome) || "surrender".equals(outcome);
        plan.put("gen034_completion_eligible", exit);
        if ("continue".equals(outcome)) {
            ObjectNode e = plan.putObject("expectations"); e.set("war_id", frame.get("war_id"));
            e.set("played_character_id", frame.get("primary_attacker_character_id")); e.set("episode_id", frame.get("episode_id"));
            e.put("successor_revision_required", true); return plan;
        }
        if (!exit) return plan;
        ObjectNode features = object(object(options.get(outcome)).get("features"));
        ObjectNode domains = object(object(object(session).get("aggregate")).get("domains"));
        BigInteger gold = balance(domains, "gold", "attacker_current_gold", frame.get("primary_attacker_character_id"));
        BigInteger prestige = balance(domains, "prestige", "attacker_current_prestige", frame.get("primary_attacker_character_id"));
        BigInteger goldDelta = nonnegative(features.get("primary_gold_transfer_raw")).negate();
        BigInteger prestigeDelta = integer(features.get("attacker_prestige_delta_raw"));
        BigInteger truceDays = nonnegative(features.get("truce_day_count"));
        ObjectNode e = plan.putObject("expectations"); e.set("war_id", frame.get("war_id"));
        e.set("played_character_id", frame.get("primary_attacker_character_id")); e.set("opponent_character_id", frame.get("primary_defender_character_id"));
        ObjectNode resources = e.putObject("resources"); resources.put("scale", 100_000);
        resources.set("gold", expectation(gold, goldDelta)); resources.set("prestige", expectation(prestige, prestigeDelta));
        ObjectNode truce = e.putObject("truce"); truce.set("owner_character_id", frame.get("primary_attacker_character_id"));
        truce.set("toward_character_id", frame.get("primary_defender_character_id")); truce.put("evaluated_days", truceDays);
        truce.put("persisted_expiry_required", true);
        ObjectNode loss = e.putObject("source_specific_loss"); loss.set("war_id", frame.get("war_id"));
        loss.put("required_cleanup_status", "destroyed"); e.putObject("checkpoint").put("cold_restore_required", true); return plan;
    }

    private static BigInteger balance(ObjectNode domains, String domain, String field, JsonNode actor) {
        ObjectNode payload = object(object(domains.get(domain)).get("payload"));
        ObjectNode balance = object(payload.get(field)); ObjectNode value = object(balance.get("value"));
        require(actor.equals(balance.get("character_id")), field + " character identity drifted");
        require(integer(value.get("scale")).equals(BigInteger.valueOf(100_000)), field + " scale drifted");
        return integer(value.get("raw"));
    }
    private static ObjectNode expectation(BigInteger before, BigInteger delta) {
        BigInteger after = before.add(delta);
        require(after.compareTo(BigInteger.valueOf(Long.MIN_VALUE)) >= 0 && after.compareTo(BigInteger.valueOf(Long.MAX_VALUE)) <= 0,
                "post-action resource balance overflows int64");
        ObjectNode n = StrictJson.object(); n.put("pre_raw", before); n.put("delta_raw", delta); n.put("post_raw", after); return n;
    }

    private static ObjectNode result(ObjectNode immediate, List<String> blockers, ObjectNode c) {
        ObjectNode n = StrictJson.object(); n.put("schema", "xar.ck3.raiktor_three_way_exit_recommendation.v6");
        n.put("provider", "raiktor-three-way-exit-recommendation-provider-v6");
        n.put("status", c == null ? "evidence_required" : text(c.get("status")));
        n.put("recommendation_ready", c != null && !c.get("recommended_outcome").isNull());
        n.put("production_recommendation_ready", c != null && bool(c.get("production_recommendation_ready")));
        if (c == null) n.putNull("recommended_outcome"); else n.set("recommended_outcome", c.get("recommended_outcome"));
        n.put("action_ready", c != null && bool(object(c.get("action_plan")).get("ready")));
        if (c == null) { n.putNull("action_literal"); n.putNull("recommendation_certificate"); }
        else { n.set("action_literal", object(c.get("action_plan")).get("literal")); n.set("recommendation_certificate", c); }
        n.put("postcondition_verified", false); n.put("gen034_closed", false); n.set("immediate_exit_evaluation", immediate);
        strings(n, "blockers", blockers);
        strings(n, "boundaries", List.of("measured_power_relation_is_a_strategy_input_not_a_forecast",
                "repository_tail_penalty_is_versioned_and_replaceable", "only_one_margin-winning_action_can_be_emitted",
                "action_ack_does_not_verify_postconditions", "gen034_requires_action_postcondition_checkpoint_and_cold_restore"));
        return n;
    }
    private static String literal(String name, JsonNode war) {
        if (name.equals("continue")) return "resume-map";
        long id = StrictJson.integer(war, 1, Integer.MAX_VALUE);
        return switch (name) {
            case "white_peace" -> "offer-white-peace-" + id;
            case "surrender" -> "surrender-war-" + id;
            default -> throw new IllegalArgumentException("recommended outcome is unavailable");
        };
    }
    private static String hash(JsonNode value) {
        byte[] raw = RaiktorExitObservationCodec.encodeWire(value);
        return RetainedJson.pythonCanonical(RetainedJson.parse(raw),
                new RetainedJson.CanonicalBudget(StrictJson.EXPLICIT_MAX_BYTES, 100_000, 128)).sha256().toUpperCase(Locale.ROOT);
    }
    private static ObjectNode object(JsonNode value) {
        require(value instanceof ObjectNode, "explicit JSON object required"); return (ObjectNode) value;
    }
    private static boolean bool(JsonNode value) {
        require(value != null && value.isBoolean(), "exact boolean required"); return value.booleanValue();
    }
    private static String text(JsonNode value) {
        String v = StrictJson.text(value); require(!v.isEmpty(), "nonempty text required"); return v;
    }
    private static BigInteger integer(JsonNode value) {
        require(value != null && value.isIntegralNumber(), "exact integer required"); return value.bigIntegerValue();
    }
    private static BigInteger nonnegative(JsonNode value) {
        BigInteger v = integer(value); require(v.signum() >= 0, "nonnegative integer required"); return v;
    }
    private static List<String> strings(JsonNode value) {
        require(value != null && value.isArray(), "explicit string list required");
        List<String> result = new ArrayList<>(); value.forEach(item -> result.add(text(item))); return result;
    }
    private static void strings(ObjectNode node, String key, List<String> values) {
        var a = node.putArray(key); values.forEach(a::add);
    }
}
