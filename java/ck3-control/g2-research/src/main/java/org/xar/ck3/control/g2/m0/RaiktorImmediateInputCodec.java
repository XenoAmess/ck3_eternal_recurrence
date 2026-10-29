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
import org.xar.ck3.control.g2.m0.RaiktorExitObservationCodec.Projection;
import org.xar.ck3.control.g2.m0.RaiktorImmediateUtility.Features;
import org.xar.ck3.control.g2.m0.RaiktorImmediateUtility.Limits;
import org.xar.ck3.control.g2.m0.RaiktorImmediateUtility.Model;
import org.xar.ck3.control.g2.m0.RaiktorImmediateUtility.ObservedOption;
import org.xar.ck3.control.g2.m0.RaiktorImmediateUtility.Option;

/** Complete immediate-exit evaluator entry: original observed inputs, explicit limits, and checked utility. */
public final class RaiktorImmediateInputCodec {
    private static final List<String> FEATURE_NAMES = List.of("primary_gold_transfer_raw", "attacker_prestige_delta_raw",
            "declared_claim_removed_count", "favor_hook_applied", "truce_day_count", "pow_release_count",
            "title_holder_change_count", "hostage_transfer_count", "war_bound_soldier_loss_count");
    private static final String[] INPUTS = {"white_peace_projection", "surrender_session", "budget_provider", "model_provider"};
    private static final String[] MISSING = {"white_peace_narrow_projection_unavailable", "surrender_session_unavailable",
            "strategy_budget_profile_unavailable", "strategy_utility_model_unavailable"};
    private RaiktorImmediateInputCodec() { }

    public static byte[] executeOperation(byte[] raw) {
        require(raw != null && raw.length <= StrictJson.INPUT_MAX_BYTES, "bounded immediate request required");
        ObjectNode request = StrictJson.object(RaiktorExitObservationCodec.parseWire(raw), Set.of("operation", "white_peace_projection", "surrender_session", "budget_provider", "model_provider"));
        require(text(request.get("operation")).equals("evaluate-immediate-exit"), "immediate operation differs");
        ObjectNode payload = request.deepCopy(); payload.remove("operation");
        return execute(RaiktorExitObservationCodec.encodeWire(payload));
    }

    public static byte[] execute(byte[] raw) {
        require(raw != null && raw.length <= StrictJson.INPUT_MAX_BYTES, "bounded immediate request required");
        ObjectNode root = StrictJson.object(RaiktorExitObservationCodec.parseWire(raw), Set.of(INPUTS));
        List<String> missing = new ArrayList<>();
        for (int index = 0; index < INPUTS.length; index++) { if (root.get(INPUTS[index]).isNull()) { missing.add(MISSING[index]); } }
        if (!missing.isEmpty()) { return RaiktorExitObservationCodec.encodeWire(result(missing, null)); }
        Projection projection = RaiktorExitObservationCodec.normalizeProjection(root.get(INPUTS[0]));
        var observation = projection.observation();
        var session = RaiktorExitObservationCodec.normalizeSession(root.get(INPUTS[1]), observation);
        require(observation.evaluatedSurrenderTermsSha256().equals(hash(session.aggregate())),
                "white-peace projection and surrender aggregate hashes differ");
        ObjectNode provider = object(root.get(INPUTS[2]));
        require(text(provider.get("schema")).equals("xar.ck3.raiktor_owner_budget_profile_provider.v1")
                && text(provider.get("provider")).equals("raiktor-owner-budget-profile-provider-v1")
                && text(provider.get("status")).equals("available") && bool(provider.get("profile_available"))
                && bool(provider.get("profile_production_eligible")) && emptyList(provider.get("blockers")), "strategy budget unavailable");
        ObjectNode budget = normalizeBudget(provider.get("owner_budget_profile"));
        String budgetVersion = text(provider.get("source_profile_version"));
        ObjectNode modelProvider = object(root.get(INPUTS[3]));
        require(text(modelProvider.get("schema")).equals("xar.ck3.raiktor_exit_utility_model_provider.v1")
                && text(modelProvider.get("provider")).equals("raiktor-exit-utility-model-file-provider-v1")
                && text(modelProvider.get("status")).equals("available") && bool(modelProvider.get("model_available"))
                && bool(modelProvider.get("model_production_eligible")) && emptyList(modelProvider.get("provider_blockers")),
                "strategy utility model unavailable");
        ObjectNode model = object(modelProvider.get("exit_utility_model"));
        require(integer(model.get("schema_version")).equals(BigInteger.TWO)
                && text(model.get("contract")).equals("raiktor-strategy-exit-utility-model-v2")
                && text(model.get("status")).equals("complete")
                && text(model.get("utility_unit")).equals("strategy_utility_q100000")
                && bool(model.get("model_production_eligible")), "strategy utility model drifted");
        ObjectNode binding = StrictJson.object(model.get("budget_profile_binding"),
                Set.of("profile_id", "profile_version", "profile_source_sha256"));
        require(binding.get("profile_id").equals(budget.get("profile_id")) && text(binding.get("profile_version")).equals(budgetVersion)
                && binding.get("profile_source_sha256").equals(budget.get("profile_source_sha256")),
                "strategy model and budget profile bindings differ");
        ObjectNode nonlinear = object(model.get("nonlinear_policy"));
        require(text(nonlinear.get("rule_id")).equals("hard-budget-reject-v1")
                && StrictJson.object(nonlinear.get("parameters_raw"), Set.of()).isEmpty(), "nonlinear policy unsupported");
        ObjectNode uncertainty = object(model.get("uncertainty_policy"));
        require(text(uncertainty.get("rule_id")).equals("bounded-unobserved-effect-penalty-v1"), "uncertainty policy unsupported");
        ObjectNode parameters = StrictJson.object(uncertainty.get("parameters_raw"), Set.of("per_unobserved_effect_penalty_raw", "maximum_total_penalty_raw"));
        Model pureModel = new Model(features(model.get("domain_coefficients_q100000")),
                nonnegative64(parameters.get("per_unobserved_effect_penalty_raw")), nonnegative64(parameters.get("maximum_total_penalty_raw")));
        ObjectNode terms = observation.terms(); JsonNode pairs = terms.get("prisoner_release_pairs");
        require(pairs != null && pairs.isArray(), "white-peace release pairs malformed");
        Features whiteFeatures = new Features(nonnegative64(terms.get("primary_gold_transfer_raw")),
                int64(terms.get("attacker_prestige_delta_raw")), 0, bool(terms.get("favor_hook_will_apply")) ? 1 : 0,
                nonnegative64(terms.get("truce_evaluated_days")), pairs.size(), nonnegative64(terms.get("title_holder_change_count")), 0, 0);
        ObjectNode option = observation.option();
        ObservedOption white = new ObservedOption(whiteFeatures, projection.unobservedDynamicEffects(),
                limits(object(budget.get("white_peace_limits")), false), bool(option.get("available")));
        ObservedOption surrender = new ObservedOption(features(projection.raw().get("surrender_feature_observation")),
                projection.surrenderUnobservedDynamicEffects(), limits(object(budget.get("pairwise_limits")), true),
                bool(object(option.get("same_frame_surrender")).get("available")));
        BigInteger minimumMargin = integer(object(budget.get("pairwise_limits")).get("minimum_switch_margin_raw"));
        var evaluation = RaiktorImmediateUtility.evaluate(new RaiktorImmediateUtility.Input(white, surrender, pureModel, minimumMargin));
        ObjectNode certificate = StrictJson.object(); certificate.put("schema_version", 4);
        certificate.put("contract", "raiktor-white-peace-vs-surrender-utility-evaluation-v4");
        certificate.put("status", evaluation.comparison().status()); certificate.set("frame", observation.frame());
        certificate.put("utility_unit", "strategy_utility_q100000");
        ObjectNode hashes = certificate.putObject("input_sha256"); hashes.put("white_peace_projection_sha256", hash(projection.raw()));
        hashes.put("surrender_session_sha256", hash(session.raw())); hashes.put("budget_profile_sha256", hash(budget));
        hashes.put("utility_model_sha256", hash(model));
        ObjectNode identity = certificate.putObject("strategy_identity"); identity.set("profile_id", budget.get("profile_id"));
        identity.put("profile_version", budgetVersion); identity.put("model_id", text(model.get("model_id")));
        identity.put("model_version", text(model.get("model_version")));
        ObjectNode options = certificate.putObject("options"); options.set("white_peace", encode(evaluation.whitePeace()));
        options.set("surrender", encode(evaluation.surrender()));
        certificate.set("comparison", encode(evaluation.comparison()));
        certificate.put("production_live_inputs", projection.productionLive() && bool(observation.producer().get("production_live"))
                && bool(budget.get("profile_production_eligible")) && bool(model.get("model_production_eligible")));
        ObjectNode boundaries = certificate.putObject("boundaries"); boundaries.put("immediate_exit_utility_ready", true);
        boundaries.put("execution_availability_gated_separately", true); boundaries.put("continue_utility_ready", false);
        boundaries.put("full_three_way_recommendation_ready", false); boundaries.put("action_ready", false); boundaries.putNull("action_literal");
        certificate.put("certificate_sha256", hash(certificate));
        return RaiktorExitObservationCodec.encodeWire(result(List.of(), certificate));
    }

    /** Normalize the existing inner profile at both producer and transport consumer boundaries. */
    public static ObjectNode normalizeBudget(JsonNode value) {
        ObjectNode budget = StrictJson.object(value, Set.of("schema_version", "contract", "status", "profile_id", "profile_provenance",
                "profile_source_sha256", "profile_production_eligible", "pairwise_limits", "white_peace_limits")).deepCopy();
        require(integer(budget.get("schema_version")).equals(BigInteger.ONE)
                && text(budget.get("contract")).equals("raiktor-owner-budget-profile-v1")
                && Set.of("complete", "incomplete").contains(text(budget.get("status"))), "owner budget identity drifted");
        text(budget.get("profile_id")); text(budget.get("profile_provenance")); bool(budget.get("profile_production_eligible"));
        require(text(budget.get("profile_source_sha256")).matches("[0-9A-F]{64}"), "profile source SHA malformed");
        ObjectNode pair = StrictJson.object(budget.get("pairwise_limits"), Set.of("schema_version", "profile_id", "profile_provenance",
                "profile_production_eligible", "maximum_surrender_gold_transfer_raw", "maximum_surrender_prestige_loss_raw",
                "maximum_surrender_claims_removed", "allow_surrender_favor_hook", "maximum_surrender_truce_days",
                "maximum_continue_tail_loss_raw", "minimum_switch_margin_raw"));
        require(integer(pair.get("schema_version")).equals(BigInteger.ONE), "pairwise schema drifted");
        for (String key : List.of("profile_id", "profile_provenance", "profile_production_eligible")) {
            require(pair.get(key).equals(budget.get(key)), "owner and pairwise profile identity drifted");
        }
        require(StrictJson.integer(pair.get("minimum_switch_margin_raw"), 1, Long.MAX_VALUE) > 0, "positive switch margin required");
        nonnegative64(pair.get("maximum_continue_tail_loss_raw")); limits(pair, true);
        ObjectNode white = StrictJson.object(budget.get("white_peace_limits"), Set.of("maximum_gold_transfer_raw", "maximum_prestige_loss_raw",
                "maximum_claims_removed", "allow_favor_hook", "maximum_truce_days")); limits(white, false);
        return budget;
    }
    private static Limits limits(ObjectNode n, boolean surrender) {
        String p = surrender ? "maximum_surrender_" : "maximum_";
        return new Limits(nonnegative64(n.get(p + "gold_transfer_raw")), nonnegative64(n.get(p + "prestige_loss_raw")),
                StrictJson.integer(n.get(p + "claims_removed"), 0, Integer.MAX_VALUE),
                bool(n.get(surrender ? "allow_surrender_favor_hook" : "allow_favor_hook")),
                StrictJson.integer(n.get(p + "truce_days"), 0, Integer.MAX_VALUE));
    }
    private static Features features(JsonNode n) {
        ObjectNode f = StrictJson.object(n, Set.copyOf(FEATURE_NAMES));
        return new Features(int64(f.get(FEATURE_NAMES.get(0))), int64(f.get(FEATURE_NAMES.get(1))), int64(f.get(FEATURE_NAMES.get(2))),
                int64(f.get(FEATURE_NAMES.get(3))), int64(f.get(FEATURE_NAMES.get(4))), int64(f.get(FEATURE_NAMES.get(5))),
                int64(f.get(FEATURE_NAMES.get(6))), int64(f.get(FEATURE_NAMES.get(7))), int64(f.get(FEATURE_NAMES.get(8))));
    }
    private static ObjectNode encode(Features f) {
        ObjectNode n = StrictJson.object(); long[] values = {f.primaryGoldTransferRaw(), f.attackerPrestigeDeltaRaw(), f.declaredClaimRemovedCount(),
                f.favorHookApplied(), f.truceDayCount(), f.powReleaseCount(), f.titleHolderChangeCount(), f.hostageTransferCount(), f.warBoundSoldierLossCount()};
        for (int i = 0; i < FEATURE_NAMES.size(); i++) { n.put(FEATURE_NAMES.get(i), values[i]); } return n;
    }
    private static ObjectNode encode(Option o) {
        ObjectNode n = StrictJson.object(); n.set("features", encode(o.features())); n.set("contributions_raw", encode(o.contributionsRaw()));
        n.put("base_utility_raw", o.baseUtilityRaw()); strings(n, "unobserved_dynamic_effects", o.unobservedDynamicEffects());
        n.put("uncertainty_penalty_raw", o.uncertaintyPenaltyRaw()); n.put("utility_raw", o.utilityRaw());
        strings(n, "hard_budget_breaches", o.hardBudgetBreaches()); strings(n, "execution_blockers", o.executionBlockers());
        n.put("eligible", o.eligible()); return n;
    }
    private static ObjectNode encode(RaiktorImmediateUtility.Comparison c) {
        ObjectNode n = StrictJson.object(); n.put("status", c.status()); var a = n.putArray("eligible_options");
        c.eligibleOptions().forEach(value -> a.add(value.wire()));
        if (c.preferredImmediateExit().isPresent()) { n.put("preferred_immediate_exit", c.preferredImmediateExit().orElseThrow().wire()); }
        else { n.putNull("preferred_immediate_exit"); }
        if (c.preferenceMarginRaw().isPresent()) { n.put("preference_margin_raw", c.preferenceMarginRaw().orElseThrow()); }
        else { n.putNull("preference_margin_raw"); }
        n.put("minimum_switch_margin_raw", c.minimumSwitchMarginRaw()); return n;
    }
    private static ObjectNode result(List<String> blockers, ObjectNode certificate) {
        ObjectNode n = StrictJson.object(); n.put("schema", "xar.ck3.raiktor_exit_utility_evaluator.v3");
        n.put("provider", "raiktor-immediate-exit-utility-evaluator-v3"); n.put("status", certificate == null ? "evidence_required" : text(certificate.get("status")));
        n.put("utility_evaluation_ready", certificate != null); n.put("immediate_exit_comparison_ready", certificate != null);
        n.put("production_live_inputs", certificate != null && bool(certificate.get("production_live_inputs")));
        if (certificate == null) { n.putNull("evaluation_certificate"); } else { n.set("evaluation_certificate", certificate); }
        strings(n, "blockers", blockers); n.put("full_three_way_recommendation_ready", false); n.put("action_ready", false);
        n.putNull("action_literal"); n.put("automatic_surrender_ready", false);
        strings(n, "boundaries", List.of("white_peace_vs_surrender_only", "measured_power_is_not_relabelled_as_campaign_forecast",
                "unobserved_effects_receive_the_versioned_penalty", "generic_current_war_bound_soldiers_are_not_proven_loss",
                "hard_budget_rejects_ineligible_options", "native_execution_unavailability_rejects_only_that_option", "no_recommendation_or_action_submission"));
        return n;
    }
    private static String hash(JsonNode value) {
        // Use the qualified shared Python canonical form; the wire codec preserves finite Double and negative zero.
        byte[] raw = RaiktorExitObservationCodec.encodeWire(value);
        return RetainedJson.pythonCanonical(RetainedJson.parse(raw),
                new RetainedJson.CanonicalBudget(StrictJson.EXPLICIT_MAX_BYTES, 100_000, 128))
                .sha256().toUpperCase(Locale.ROOT);
    }
    private static void strings(ObjectNode n, String key, List<String> values) { var a = n.putArray(key); values.forEach(a::add); }
    private static ObjectNode object(JsonNode n) { require(n instanceof ObjectNode, "explicit JSON object required"); return (ObjectNode) n; }
    private static String text(JsonNode n) { String s = StrictJson.text(n); require(!s.strip().isEmpty(), "nonempty text required"); return s; }
    private static boolean bool(JsonNode n) { require(n != null && n.isBoolean(), "exact boolean required"); return n.booleanValue(); }
    private static boolean emptyList(JsonNode n) { require(n != null && n.isArray(), "explicit list required"); return n.isEmpty(); }
    private static BigInteger integer(JsonNode n) { require(n != null && n.isIntegralNumber(), "exact integer required"); return n.bigIntegerValue(); }
    private static long int64(JsonNode n) { return StrictJson.integer(n, Long.MIN_VALUE, Long.MAX_VALUE); }
    private static long nonnegative64(JsonNode n) { return StrictJson.integer(n, 0, Long.MAX_VALUE); }
}

