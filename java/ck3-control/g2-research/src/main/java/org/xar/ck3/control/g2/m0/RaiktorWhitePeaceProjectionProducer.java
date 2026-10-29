package org.xar.ck3.control.g2.m0;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.g2.m0.RaiktorRawJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeInteractionRoles;
import org.xar.ck3.control.warpolicy.NativeTerminationOptions;
import org.xar.ck3.control.warpolicy.NativeTerminationTerms;

/** The actual original narrow projection over bound native query envelopes. No query or action is executed here. */
public final class RaiktorWhitePeaceProjectionProducer {
    public static final String OPERATION = "produce-white-peace-narrow-projection";
    private static final List<String> WHITE_UNKNOWN = List.of("attacker_trait_stress_delta", "defender_trait_stress_delta",
            "defender_accolade_glory_delta", "participant_ally_fame_deltas", "glory_hound_and_antagonistic_clan_opinion_rows",
            "attacker_accolade_white_peace_prestige_delta", "laamp_actual_settlement_outside_cb_effect");
    private static final Set<String> SURRENDER_UNKNOWN = Set.of("targeting_faction_discontent_delta", "glory_hound_vassal_opinion_rows",
            "antagonistic_clan_vassal_opinion_rows", "existing_house_feud_score_delta", "attacker_mandala_piety_experience_delta",
            "defender_mandala_serenity", "defender_accolade_glory", "laamp_actual_settlement_outside_cb_effect", "war_bound_army_losses");
    private static final List<String> COMPLETENESS = List.of("claim_disposition_ready", "favor_hook_ready", "final_recipient_response_ready",
            "gold_transfer_ready", "prestige_delta_ready", "prisoner_release_ready", "truce_ready");
    private RaiktorWhitePeaceProjectionProducer() { }
    public static JsonNode produce(JsonNode snapshotValue, JsonNode optionsValue, JsonNode termsValue, boolean productionLive) {
        List<String> missing = new ArrayList<>();
        if (snapshotValue == null || snapshotValue.isNull()) missing.add("paused_snapshot_unavailable");
        if (optionsValue == null || optionsValue.isNull()) missing.add("termination_options_query_unavailable");
        if (termsValue == null || termsValue.isNull()) missing.add("raiktor_terms_query_unavailable");
        if (!missing.isEmpty()) return result(missing, null, null, List.of(), null);
        ObjectNode snapshot = object(snapshotValue, "snapshot"); ObjectNode optionsQuery = object(optionsValue, "termination options query");
        ObjectNode termsQuery = object(termsValue, "Raiktor terms query");
        ObjectNode rawOptions = object(optionsQuery.get("war_termination_options"), "termination options result");
        int warId = positive32(rawOptions.get("war_id"), "war_id"); ObjectNode binding = snapshotBinding(snapshot, warId);
        require(bool(optionsQuery.get("accepted"), "options query accepted")
                && text(optionsQuery.get("status"), "options query status").equals("available"), "termination options query is not available");
        ObjectNode options = NativeTerminationOptions.normalizeNativePacket(rawOptions, warId).normalized();
        require(bool(termsQuery.get("accepted"), "terms query accepted")
                && text(termsQuery.get("status"), "terms query status").equals("available"), "Raiktor terms query is not available");
        ObjectNode terms = NativeTerminationTerms.normalize(termsQuery.get("war_termination_terms"), warId);
        require(text(terms.get("supported_slice"), "supported_slice").equals(NativeTerminationTerms.RAIKTOR),
                "terms query is not the Raiktor narrow slice");
        JsonNode sessionValue = termsQuery.get("raiktor_surrender_aggregate_session");
        if (!(sessionValue instanceof ObjectNode sessionRow) || !"available".equals(sessionRow.path("status").asText())) {
            String code = sessionValue != null && sessionValue.path("failure").isObject()
                    ? sessionValue.path("failure").path("code").asText("unavailable") : "unavailable";
            return result(List.of("surrender_aggregate_session_" + code), null, sourceEvidence(terms), List.of(), null);
        }
        var expected = RaiktorExitObservationCodec.expectedBinding(binding);
        var session = RaiktorExitObservationCodec.normalizeSession(sessionValue, expected);
        RaiktorSurrenderAggregateProducer.validateAggregate(session.aggregate(), expected);
        ObjectNode aggregate = session.aggregate(); ObjectNode aggregateFrame = object(aggregate.get("frame"), "aggregate frame");
        queryBinding(optionsQuery, binding, "queried_episode_run_id", "termination options query");
        queryBinding(termsQuery, binding, "episode_run_id", "Raiktor terms query");
        ObjectNode optionCb = object(options.get("active_casus_belli_identity"), "option CB");
        ObjectNode termsCb = object(terms.get("casus_belli"), "terms CB");
        require(same(options.get("war_id"), aggregateFrame.get("war_id"))
                && same(terms.get("war_id"), aggregateFrame.get("war_id"))
                && same(optionCb.get("database_index"), aggregateFrame.get("active_casus_belli_database_index"))
                && same(termsCb.get("database_index"), aggregateFrame.get("active_casus_belli_database_index"))
                && text(optionCb.get("canonical_key"), "option CB").equals("raiktor_claim_cb")
                && text(termsCb.get("canonical_key"), "terms CB").equals("raiktor_claim_cb"), "options, terms and aggregate identify different wars");
        require(text(options.get("player_side"), "player side").equals("attacker")
                && bool(options.get("player_is_primary_war_leader"), "primary leader"), "Raiktor projection requires the primary attacker");
        require(same(terms.get("claimant_character_id"), aggregateFrame.get("claimant_character_id")), "claimant identity drifted");
        List<String> blockers = new ArrayList<>();
        if (!isTrue(options.get("cb_allows_white_peace"))) blockers.add("casus_belli_forbids_white_peace");
        if (!isTrue(terms.path("attacker_fame").get("actual_delta_observable"))) blockers.add("white_peace_prestige_factor_unavailable");
        if (!isTrue(terms.path("truce").get("evaluated_days_observable"))) blockers.add("white_peace_truce_duration_unavailable");
        if (!isTrue(terms.path("prisoner_release").get("actual_pairs_observable"))) blockers.add("white_peace_prisoner_release_scan_unavailable");
        if (!isTrue(terms.path("conditional_favor_hook").get("actual_applies_observable"))) blockers.add("white_peace_favor_condition_unavailable");
        ObjectNode evidence = sourceEvidence(terms);
        if (!blockers.isEmpty()) return result(blockers, null, evidence, List.of(), null);
        ObjectNode frame = StrictJson.object(); frame.set("snapshot_id", binding.get("snapshot_id"));
        frame.set("snapshot_revision", binding.get("snapshot_revision")); frame.set("native_revision", binding.get("native_revision"));
        frame.set("date_raw", binding.get("date_raw")); frame.put("connection_id", "connection-generation:" + integer(binding.get("connection_generation"), "connection"));
        frame.set("episode_id", binding.get("episode_run_id")); frame.set("ck3_pid", binding.get("process_id"));
        frame.put("paused", true); frame.set("war_id", binding.get("war_id")); frame.put("active_casus_belli_key", "raiktor_claim_cb");
        for (String key : List.of("active_casus_belli_database_index", "primary_attacker_character_id",
                "primary_defender_character_id", "claimant_character_id")) frame.set(key, aggregateFrame.get(key));
        ObjectNode rawOptionMap = object(options.get("options"), "options");
        ObjectNode option = execution(rawOptionMap.get("white_peace")); option.set("same_frame_surrender", execution(rawOptionMap.get("surrender")));
        ObjectNode whiteTerms = StrictJson.object();
        whiteTerms.set("declared_target_title_ids", terms.get("target_title_ids").deepCopy());
        whiteTerms.set("retained_target_title_ids", terms.get("target_title_ids").deepCopy());
        whiteTerms.put("claim_disposition", "retain_and_strengthen_weak"); whiteTerms.put("title_holder_change_count", 0);
        whiteTerms.put("primary_gold_transfer_raw", 0);
        BigInteger prestige = integer(terms.path("attacker_fame").path("cb_prestige_factor").get("raw"), "prestige factor").multiply(BigInteger.valueOf(-5));
        require(prestige.compareTo(BigInteger.valueOf(Long.MIN_VALUE)) >= 0 && prestige.compareTo(BigInteger.valueOf(Long.MAX_VALUE)) <= 0,
                "white-peace prestige delta outside int64"); whiteTerms.put("attacker_prestige_delta_raw", prestige);
        whiteTerms.set("truce_evaluated_days", terms.path("truce").get("evaluated_days"));
        var release = whiteTerms.putArray("prisoner_release_pairs");
        for (JsonNode pair : array(terms.path("prisoner_release").get("release_pairs"), "release pairs")) {
            ObjectNode row = release.addObject(); row.set("jailer_character_id", pair.get("jailer_character_id"));
            row.set("prisoner_character_id", pair.get("prisoner_character_id"));
        }
        whiteTerms.set("favor_hook_will_apply", terms.path("conditional_favor_hook").get("will_apply")); whiteTerms.put("hostage_variant", "none");
        String aggregateSha = hash(aggregate); ObjectNode candidate = StrictJson.object(); candidate.set("frame", frame); candidate.set("white_peace_option", option);
        ObjectNode sourceBundle = StrictJson.object(); sourceBundle.set("frame", frame); sourceBundle.set("options_query", options);
        sourceBundle.set("terms_query", terms); sourceBundle.put("surrender_aggregate_sha256", aggregateSha); sourceBundle.set("source_evidence", evidence);
        ObjectNode observation = StrictJson.object(); observation.put("schema_version", 1);
        observation.put("contract", RaiktorExitObservationCodec.OBSERVATION_CONTRACT); observation.put("status", "complete");
        observation.set("frame", frame); observation.put("evaluated_candidate_sha256", hash(candidate));
        observation.put("evaluated_surrender_terms_sha256", aggregateSha);
        ObjectNode producer = observation.putObject("producer"); producer.put("producer_id", "raiktor-white-peace-narrow-projection-v3");
        producer.put("producer_version", "v3"); producer.put("source_artifact_sha256", hash(sourceBundle)); producer.put("production_live", productionLive);
        ObjectNode completeness = observation.putObject("completeness"); for (String key : COMPLETENESS) completeness.put(key, true);
        observation.set("option", option); observation.set("terms", whiteTerms); observation.put("same_frame_stable", true);
        observation = RaiktorExitObservationCodec.normalizeObservation(observation).toJson();
        List<String> unknown = new ArrayList<>();
        for (String value : strings(terms.get("unobserved_dynamic_effects"), "surrender uncertainty")) if (SURRENDER_UNKNOWN.contains(value)) unknown.add(value);
        require(new HashSet<>(unknown).equals(SURRENDER_UNKNOWN), "Raiktor surrender uncertainty set drifted");
        ObjectNode features = StrictJson.object();
        features.set("primary_gold_transfer_raw", terms.path("gold_reparations").path("actual_transfer").path("value").get("raw"));
        features.set("attacker_prestige_delta_raw", terms.path("attacker_fame").path("attacker_prestige_delta").path("value").get("raw"));
        features.put("declared_claim_removed_count", terms.get("target_title_ids").size());
        features.put("favor_hook_applied", bool(terms.path("conditional_favor_hook").get("will_apply"), "favor applies") ? 1 : 0);
        features.set("truce_day_count", terms.path("truce").get("evaluated_days"));
        features.put("pow_release_count", terms.path("prisoner_release").get("release_pairs").size());
        features.put("title_holder_change_count", 0); features.put("hostage_transfer_count", 0); features.put("war_bound_soldier_loss_count", 0);
        return result(List.of(), observation, evidence, unknown, features);
    }
    static ObjectNode snapshotBinding(ObjectNode snapshot, int warId) {
        ObjectNode diagnostics = object(snapshot.get("diagnostics"), "diagnostics"); ObjectNode played = object(snapshot.get("played_character"), "played character");
        BigInteger actor = positive(snapshot.get("episode_character_id"), "episode_character_id");
        require(integer(played.get("character_id"), "played character").equals(actor), "played character is not the episode character");
        int count = 0;
        for (JsonNode value : array(snapshot.get("active_wars"), "active_wars")) {
            if (value instanceof ObjectNode war && same(war.get("war_id"), com.fasterxml.jackson.databind.node.BigIntegerNode.valueOf(BigInteger.valueOf(warId)))
                    && "attacker".equals(war.path("player_side").asText()) && isTrue(war.get("player_is_primary_war_leader"))) count++;
        }
        require(count == 1 && bool(snapshot.get("paused"), "paused"), "snapshot must contain one selected primary-attacker war and be paused");
        ObjectNode binding = StrictJson.object(); binding.put("snapshot_id", text(snapshot.get("snapshot_id"), "snapshot_id"));
        binding.put("snapshot_revision", positive(snapshot.get("revision"), "revision"));
        binding.put("native_revision", positive(snapshot.get("native_revision"), "native_revision"));
        binding.put("date_raw", integer(snapshot.get("date_raw"), "date_raw"));
        binding.put("connection_generation", positive(diagnostics.get("connection_generation"), "connection_generation"));
        binding.put("episode_run_id", text(snapshot.get("episode_run_id"), "episode_run_id"));
        binding.put("episode_character_id", actor); binding.put("process_id", positive(diagnostics.get("bridge_pid"), "bridge_pid"));
        binding.put("war_id", warId); return binding;
    }
    private static void queryBinding(ObjectNode query, ObjectNode binding, String episodeField, String name) {
        for (String[] pair : new String[][] {{"queried_snapshot_id", "snapshot_id"}, {"queried_revision", "snapshot_revision"},
                {"queried_native_revision", "native_revision"}, {"queried_connection_generation", "connection_generation"},
                {episodeField, "episode_run_id"}}) require(same(query.get(pair[0]), binding.get(pair[1])), name + " crossed its paused session: " + pair[0]);
    }
    private static ObjectNode execution(JsonNode raw) {
        ObjectNode input = object(raw, "execution option"); ObjectNode result = StrictJson.object();
        for (String key : List.of("context_constructed", "available", "auto_accept", "recipient_response")) result.set(key, input.get(key).deepCopy());
        result.set("native_validator", input.get("native_validator_passed").deepCopy());
        NativeInteractionRoles.putOption(result, NativeInteractionRoles.fromOption(input)); return result;
    }
    private static ObjectNode sourceEvidence(ObjectNode terms) {
        ObjectNode provenance = object(terms.get("provenance"), "exact-build provenance");
        ObjectNode evidence = StrictJson.object();
        String[][] values = {{"game_version", "1.19.0.6"},
                {"executable_sha256", "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"},
                {"event_war_script_sha256", "BD202AE41EBA3A0E1E7E4277D09ED1E8D8C7E66B378308BB417D974331F9C707"},
                {"war_effects_script_sha256", "A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D"}};
        for (String[] pair : values) { require(text(provenance.get(pair[0]), pair[0]).equals(pair[1]), "Raiktor terms exact-build provenance drifted"); evidence.put(pair[0], pair[1]); }
        ObjectNode rules = evidence.putObject("projection_rules");
        rules.put("claims", "raiktor_claim_cb.on_white_peace retain; strengthen weak");
        rules.put("gold", "raiktor_claim_cb.on_white_peace has no primary transfer");
        rules.put("prestige", "setup_claim_cb(victory=no) factor multiplied by -5"); rules.put("prisoners", "shared show_pow_release_message_effect");
        rules.put("favor", "identical attacker-to-claimant conditional"); rules.put("truce", "shared standard_truce_duration_days expression");
        rules.put("hostages", "raiktor_claim_cb allow_hostages=no");
        strings(evidence, "copied_same_frame_domains", List.of("cb_prestige_factor", "prisoner_release_pairs", "conditional_favor_hook_application",
                "standard_truce_duration_days")); return evidence;
    }
    private static ObjectNode result(List<String> blockers, ObjectNode observation, ObjectNode evidence, List<String> unknown, ObjectNode features) {
        ObjectNode result = StrictJson.object(); result.put("schema", "xar.ck3.raiktor_white_peace_narrow_projection_provider.v3");
        result.put("provider", "raiktor-white-peace-narrow-projection-v3"); result.put("status", observation != null ? "available" : "evidence_required");
        result.put("observation_ready", observation != null); result.put("production_live", observation != null && isTrue(observation.path("producer").get("production_live")));
        result.set("white_peace_observation", observation); result.set("source_evidence", evidence);
        strings(result, "unobserved_dynamic_effects", WHITE_UNKNOWN); strings(result, "surrender_unobserved_dynamic_effects", unknown);
        result.set("surrender_feature_observation", features); strings(result, "blockers", blockers);
        // These tokens are the unchanged legacy receipt ABI; implementation provenance is recorded by the Java source graph.
        strings(result, "boundaries", List.of("read_only_python_projection_over_existing_safe_queries", "raiktor_claim_cb_only",
                "broad_loaded_effect_preview_remains_disabled", "copied_values_require_exact_shared_script_expressions",
                "unobserved_dynamic_effects_are_not_zero", "terms_observation_is_independent_of_current_execution_availability",
                "surrender_features_come_from_the_bound_normalized_terms_query", "provider_does_not_authorize_or_submit_an_action"));
        return result;
    }
    private static boolean isTrue(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
    private static BigInteger positive(JsonNode value, String name) {
        BigInteger number = integer(value, name); require(number.signum() > 0, name + " must be positive"); return number;
    }
}
