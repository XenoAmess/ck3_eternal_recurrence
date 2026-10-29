package org.xar.ck3.control.g2.m0;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.g2.m0.RaiktorRawJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeInteractionRoles;
import org.xar.ck3.control.g2.m0.RaiktorRawOperations.Operation;
import org.xar.ck3.control.warpolicy.NativeTerminationTerms;

/** The sole raw M0 result codec. Validates existing receipts without file IO, scoring, queries or submission. */
final class RaiktorRawResultCodec {
    private static final Set<String> FEATURES = Set.of("primary_gold_transfer_raw", "attacker_prestige_delta_raw",
            "declared_claim_removed_count", "favor_hook_applied", "truce_day_count", "pow_release_count",
            "title_holder_change_count", "hostage_transfer_count", "war_bound_soldier_loss_count");
    private static final Set<String> SESSION_READY = Set.of("snapshot_binding_ready", "query_receipt_binding_ready",
            "same_frame_revision_ready", "episode_owner_ready", "process_binding_ready", "aggregate_session_binding_ready");
    private static final Set<String> WHITE_FIELDS = Set.of("schema", "provider", "status", "observation_ready", "production_live",
            "white_peace_observation", "source_evidence", "unobserved_dynamic_effects", "surrender_unobserved_dynamic_effects",
            "surrender_feature_observation", "blockers", "boundaries");
    private static final Set<String> MODEL_FIELDS = Set.of("schema_version", "contract", "status", "model_version", "activation",
            "model_id", "model_provenance", "utility_unit", "model_source_sha256", "budget_profile_binding",
            "domain_coefficients_q100000", "nonlinear_policy", "uncertainty_policy", "tail_risk_policy", "model_production_eligible");
    private static final Set<String> RECOMMENDATION_FIELDS = Set.of("schema", "provider", "status", "recommendation_ready",
            "production_recommendation_ready", "recommended_outcome", "action_ready", "action_literal",
            "recommendation_certificate", "postcondition_verified", "gen034_closed", "immediate_exit_evaluation", "blockers", "boundaries");
    private static final Set<String> OUTCOMES = Set.of("continue", "white_peace", "surrender");
    private RaiktorRawResultCodec() { }

    static JsonNode validate(Operation operation, ObjectNode request, JsonNode raw) {
        Objects.requireNonNull(operation, "raw M0 operation");
        require(raw != null, "raw M0 result is missing; explicit JSON null is distinct");
        if (request != null) require(operation.wire().equals(text(request.get("operation"), "original operation")),
                "raw M0 result operation differs from original request");
        JsonNode result = switch (operation) {
            case CAMPAIGN -> powerProvider(raw, false);
            case NORMALIZE_POWER -> RaiktorCampaignDominanceProducer.normalizeCertificate(raw);
            case REPLAY_POWER -> powerProvider(raw, true);
            case WHITE -> white(raw);
            case PROJECT -> raw.isNull() ? NullNode.instance : RaiktorSurrenderAggregateProducer.validateAggregate(raw);
            case BIND -> session(raw);
            case ATTACH -> attachment(request, raw);
            case BUDGET -> RaiktorImmediateInputCodec.normalizeBudget(raw);
            case MODEL -> model(raw);
            case PROVIDE_BUDGET -> budgetProvider(raw);
            case PROVIDE_MODEL -> modelProvider(raw);
            case CONFIGURATION -> {
                ObjectNode pair = exact(raw, Set.of("budget_provider", "model_provider"), "configuration result");
                budgetProvider(pair.get("budget_provider")); modelProvider(pair.get("model_provider")); yield pair;
            }
            case ACTUAL -> actual(raw);
        };
        if (request != null) bindRequest(operation, request, result);
        return result.deepCopy();
    }

    private static void bindRequest(Operation operation, ObjectNode request, JsonNode result) {
        switch (operation) {
            case NORMALIZE_POWER -> require(same(result, RaiktorCampaignDominanceProducer.normalizeCertificate(request.get("certificate"))),
                    "normalized power differs from original certificate");
            case CAMPAIGN -> {
                JsonNode certificate = result.get("campaign_dominance_certificate");
                powerFrame(request.get("before"), certificate.get("frame"), request.get("war_id"), request.get("opponent_character_id"));
                powerFrame(request.get("between"), certificate.get("frame"), request.get("war_id"), request.get("opponent_character_id"));
                powerFrame(request.get("after"), certificate.get("frame"), request.get("war_id"), request.get("opponent_character_id"));
                require(same(certificate.path("evidence").get("source_artifact_sha256"), request.get("source_artifact_sha256")), "campaign source artifact differs");
                for (String name : List.of("first", "second")) {
                    ObjectNode query = object(request.get(name), "original power query");
                    ObjectNode observation = object(query.get("war_entry_assessments"), "original power observation");
                    var assessments = array(observation.get("assessments"), "original power assessments");
                    require(assessments.size() == 1, "original power request has multiple targets");
                    JsonNode power = certificate.get("power");
                    for (String field : List.of("actor_power_base_raw", "actor_network_contribution_raw", "actor_power_total_raw", "target_power_base_raw",
                            "target_network_contribution_raw", "target_pre_adjustment_total_raw", "target_adjustment_delta_raw", "target_power_total_raw", "actual_power_ratio_raw"))
                        require(same(power.get(field), assessments.get(0).get(field)), "campaign result differs from original power sample");
                    require(same(power.get("fixed_point_scale"), observation.path("provenance").get("fixed_point_scale"))
                            && same(certificate.path("evidence").get(name.equals("first") ? "first_query_sequence" : "second_query_sequence"), query.get("query_sequence")),
                            "campaign original sample scale/sequence differs");
                }
            }
            case REPLAY_POWER -> {
                JsonNode certificate = result.get("campaign_dominance_certificate");
                ObjectNode source = RaiktorCampaignDominanceProducer.normalizeCertificate(request.get("source_certificate"));
                require(same(certificate.get("frame"), request.get("target_frame")), "replay target frame differs");
                JsonNode evidence = certificate.get("evidence");
                require(same(evidence.get("source_runtime_frame"), source.get("frame"))
                        && sha(evidence.get("source_certificate_sha256"), "source certificate hash").equals(hash(source)), "replay source certificate differs");
                require(same(certificate.get("power"), source.get("power")), "replay source power differs");
                for (String field : List.of("first_query_sequence", "second_query_sequence", "double_sample_stable", "source_artifact_sha256", "query_payload_sha256"))
                    require(same(evidence.get(field), source.path("evidence").get(field)), "replay original evidence differs");
                for (String[] pair : new String[][] {{"checkpoint_sha256", "source_checkpoint_sha256", "target_checkpoint_sha256"},
                        {"driver_state_sha256", "source_driver_state_sha256", "target_driver_state_sha256"}}) {
                    require(same(evidence.get(pair[0]), request.get(pair[1])) && same(evidence.get(pair[0]), request.get(pair[2])), "replay immutable hashes differ");
                }
            }
            case BUDGET -> {
                require(same(result.get("profile_source_sha256"), request.get("source_sha256")), "rendered budget source SHA differs");
                ObjectNode source = object(request.get("source"), "original budget source");
                for (String field : List.of("profile_id", "profile_provenance", "white_peace_limits")) require(same(result.get(field), source.get(field)), "rendered budget content differs");
                object(source.get("pairwise_limits"), "original pair limits").fields().forEachRemaining(entry ->
                        require(same(result.path("pairwise_limits").get(entry.getKey()), entry.getValue()), "rendered pair limit differs"));
            }
            case MODEL -> {
                require(same(result.get("model_source_sha256"), request.get("source_sha256")), "rendered model source SHA differs");
                object(request.get("source"), "original model source").fields().forEachRemaining(entry -> {
                    if (!entry.getKey().equals("contract")) require(same(result.get(entry.getKey()), entry.getValue()), "rendered model content differs");
                });
            }
            case PROVIDE_BUDGET -> fileSource(result, selectedRef(request, "budget_override", "default_budget"));
            case PROVIDE_MODEL -> fileSource(result, selectedRef(request, "model_override", "default_model"));
            case CONFIGURATION -> {
                ObjectNode sources = exact(request.get("configuration_sources"), Set.of("default_budget", "default_model", "budget_override", "model_override"), "original configuration sources");
                fileSource(result.get("budget_provider"), selectedRef(sources, "budget_override", "default_budget"));
                fileSource(result.get("model_provider"), selectedRef(sources, "model_override", "default_model"));
            }
            case WHITE -> {
                if (bool(result.get("observation_ready"), "white ready")) {
                    JsonNode snapshot = request.get("snapshot");
                    ObjectNode terms = object(request.path("terms_query").get("war_termination_terms"), "original white native terms");
                    JsonNode frame = result.path("white_peace_observation").get("frame");
                    warFrame(snapshot, frame, terms.get("war_id"), null);
                    require(same(frame.get("claimant_character_id"), terms.get("claimant_character_id"))
                            && same(frame.get("active_casus_belli_database_index"), terms.path("casus_belli").get("database_index")), "white original CB/claimant differ");
                }
            }
            case ACTUAL -> {
                if (text(result.get("status"), "actual status").equals("available"))
                    warFrame(request.get("current_snapshot"), result.path("recommendation").path("recommendation_certificate").get("frame"),
                            request.get("war_id"), request.get("opponent_character_id"));
            }
            case PROJECT -> {
                if (!result.isNull()) {
                    JsonNode frame = result.get("frame"); ObjectNode snapshot = object(request.get("snapshot"), "original aggregate snapshot");
                    ObjectNode terms = object(request.get("terms"), "original aggregate terms");
                    require(same(frame.get("snapshot_revision"), snapshot.get("revision")) && same(frame.get("native_revision"), snapshot.get("native_revision"))
                            && same(frame.get("date_raw"), snapshot.get("date_raw")) && same(frame.get("paused"), snapshot.get("paused"))
                            && same(frame.get("primary_attacker_character_id"), snapshot.get("episode_character_id"))
                            && same(frame.get("war_id"), terms.get("war_id")) && same(frame.get("claimant_character_id"), terms.get("claimant_character_id"))
                            && same(frame.get("active_casus_belli_database_index"), terms.path("casus_belli").get("database_index"))
                            && same(frame.get("active_casus_belli_key"), terms.path("casus_belli").get("canonical_key")), "projected aggregate original frame differs");
                    ObjectNode copied = object(result.path("claims_base").get("payload"), "aggregate claim payload");
                    for (String key : List.of("target_title_ids", "claims", "attacker_defeat")) require(same(copied.get(key), terms.get(key)), "aggregate claim disposition differs");
                }
            }
            case BIND -> {
                bindSessionFrame(request.get("snapshot"), result);
                if (text(result.get("status"), "session status").equals("available")) {
                    require(same(result.get("aggregate"), RaiktorSurrenderAggregateProducer.validateAggregate(request.get("aggregate"))),
                            "bound aggregate differs from original");
                    JsonNode binding = result.get("binding"); ObjectNode receipt = object(request.get("query_receipt"), "original query receipt");
                    for (String[] pair : new String[][] {{"snapshot_id", "queried_snapshot_id"}, {"snapshot_revision", "queried_revision"},
                            {"native_revision", "queried_native_revision"}, {"connection_generation", "queried_connection_generation"}, {"episode_run_id", "episode_run_id"}})
                        require(same(binding.get(pair[0]), receipt.get(pair[1])), "session differs from original query receipt");
                }
            }
            case ATTACH -> {
                JsonNode attachedSession = result.get("raiktor_surrender_aggregate_session");
                if (text(result.path("war_termination_terms").get("status"), "terms status").equals("unsupported"))
                    require(text(attachedSession.get("status"), "session status").equals("unavailable"), "unsupported native terms cannot yield an available session");
                bindSessionFrame(request.get("snapshot"), attachedSession);
            }
        }
    }

    private static ObjectNode selectedRef(ObjectNode request, String overrideKey, String defaultKey) {
        require(request.has(overrideKey) && request.has(defaultKey), "original configuration refs are missing");
        return exact(request.get(overrideKey).isNull() ? request.get(defaultKey) : request.get(overrideKey),
                Set.of("path", "bytes", "sha256"), "selected original FileRef");
    }

    private static void fileSource(JsonNode provider, ObjectNode ref) {
        String path = java.nio.file.Path.of(text(ref.get("path"), "original FileRef path")).toAbsolutePath().normalize().toString();
        number(ref.get("bytes"), 1, StrictJson.EXPLICIT_MAX_BYTES, "original FileRef bytes");
        String sha = text(ref.get("sha256"), "original FileRef SHA");
        require(sha.matches("[0-9A-Fa-f]{64}"), "original FileRef SHA malformed");
        JsonNode source = provider.get("source");
        require(path.equals(text(source.get("path"), "provider source path"))
                && sha.equalsIgnoreCase(text(source.get("sha256"), "provider source SHA")), "provider source differs from selected original FileRef");
    }

    private static void powerFrame(JsonNode snapshotRaw, JsonNode frame, JsonNode war, JsonNode opponent) {
        ObjectNode snapshot = object(snapshotRaw, "original campaign snapshot");
        require(bool(snapshot.get("paused"), "original campaign paused") && bool(snapshot.get("map_ready"), "original campaign map ready"), "original campaign frame is unavailable");
        for (String[] pair : new String[][] {{"snapshot_id", "snapshot_id"}, {"snapshot_revision", "revision"},
                {"native_revision", "native_revision"}, {"date_raw", "date_raw"}, {"episode_run_id", "episode_run_id"}})
            require(same(frame.get(pair[0]), snapshot.get(pair[1])), "campaign result crossed original frame");
        require(same(frame.get("connection_generation"), snapshot.path("diagnostics").get("connection_generation"))
                && same(frame.get("ck3_pid"), snapshot.path("diagnostics").get("bridge_pid"))
                && same(frame.get("actor_character_id"), snapshot.path("played_character").get("character_id"))
                && same(frame.get("war_id"), war) && same(frame.get("opponent_character_id"), opponent), "campaign original actor/war/process differs");
    }

    private static void warFrame(JsonNode snapshotRaw, JsonNode frame, JsonNode war, JsonNode opponent) {
        ObjectNode snapshot = object(snapshotRaw, "original war snapshot");
        require(bool(snapshot.get("paused"), "original paused"), "original war frame is not paused");
        for (String[] pair : new String[][] {{"snapshot_id", "snapshot_id"}, {"snapshot_revision", "revision"},
                {"native_revision", "native_revision"}, {"date_raw", "date_raw"}, {"episode_id", "episode_run_id"}})
            require(same(frame.get(pair[0]), snapshot.get(pair[1])), "result crossed original war frame");
        require(same(frame.get("ck3_pid"), snapshot.path("diagnostics").get("bridge_pid"))
                && same(frame.get("primary_attacker_character_id"), snapshot.path("played_character").get("character_id"))
                && same(frame.get("primary_attacker_character_id"), snapshot.get("episode_character_id"))
                && same(frame.get("war_id"), war), "original war actor/process/ID differs");
        String connection = "connection-generation:" + positive32(snapshot.path("diagnostics").get("connection_generation"), "original connection");
        require(connection.equals(text(frame.get("connection_id"), "result connection")), "original connection differs");
        JsonNode selected = null;
        for (JsonNode value : array(snapshot.get("active_wars"), "original active wars")) if (value instanceof ObjectNode && same(value.get("war_id"), war)) {
            require(selected == null, "duplicate original selected war"); selected = value;
        }
        require(selected != null && "attacker".equals(text(selected.get("player_side"), "original player side"))
                && bool(selected.get("player_is_primary_war_leader"), "original primary leader")
                && same(frame.get("primary_defender_character_id"), selected.get("primary_opponent_character_id")), "original war leadership/opponent differs");
        if (opponent != null) require(same(frame.get("primary_defender_character_id"), opponent), "explicit original opponent differs");
    }

    private static void bindSessionFrame(JsonNode snapshotRaw, JsonNode result) {
        if (!text(result.get("status"), "session status").equals("available")) return;
        ObjectNode snapshot = object(snapshotRaw, "original session snapshot");
        JsonNode binding = result.get("binding");
        ObjectNode expected = RaiktorWhitePeaceProjectionProducer.snapshotBinding(snapshot, positive32(binding.get("war_id"), "session war"));
        require(same(binding, expected), "session binding crossed original snapshot");
    }


    private static ObjectNode powerProvider(JsonNode raw, boolean replay) {
        ObjectNode row = exact(raw, Set.of("schema", "provider", "status", "certificate_available",
                "campaign_dominance_certificate", "blockers", "boundaries"), "power provider result");
        eq(row, "schema", replay ? "xar.ck3.raiktor_checkpoint_dominance_replay_provider.v1" : "xar.ck3.raiktor_campaign_dominance_provider.v1");
        eq(row, "provider", replay ? "raiktor-checkpoint-power-dominance-replay-provider-v1" : "raiktor-active-war-power-dominance-provider-v1");
        eq(row, "status", "available"); truth(row, "certificate_available", true); empty(row, "blockers"); strings(row.get("boundaries"), "power boundaries");
        ObjectNode certificate = RaiktorCampaignDominanceProducer.normalizeCertificate(row.get("campaign_dominance_certificate"));
        require(number(certificate.get("schema_version"), 2, 3, "power version") == (replay ? 3 : 2),
                "power provider and certificate version differ");
        return row;
    }

    private static ObjectNode white(JsonNode raw) {
        ObjectNode row = exact(raw, WHITE_FIELDS, "white projection result");
        eq(row, "schema", RaiktorExitObservationCodec.PROJECTION_SCHEMA);
        eq(row, "provider", RaiktorExitObservationCodec.PROJECTION_PROVIDER);
        boolean ready = bool(row.get("observation_ready"), "observation ready");
        boolean live = bool(row.get("production_live"), "production live");
        strings(row.get("unobserved_dynamic_effects"), "white uncertainty");
        strings(row.get("surrender_unobserved_dynamic_effects"), "surrender uncertainty");
        strings(row.get("boundaries"), "white boundaries");
        List<String> blockers = strings(row.get("blockers"), "white blockers");
        if (!row.get("source_evidence").isNull()) sourceEvidence(row.get("source_evidence"));
        if (!ready) {
            eq(row, "status", "evidence_required"); require(!live && !blockers.isEmpty(), "unready white result overclaims");
            nil(row, "white_peace_observation"); nil(row, "surrender_feature_observation");
            return row;
        }
        eq(row, "status", "available"); require(blockers.isEmpty(), "available white result has blockers");
        var projection = RaiktorExitObservationCodec.normalizeProjection(row);
        ObjectNode observation = projection.observation().toJson();
        RaiktorActualRecommendationFactory.decodeFrame(observation.get("frame"));
        require(bool(observation.path("producer").get("production_live"), "observation live") == live,
                "white live flags differ");
        execution(observation.get("option"), true);
        ObjectNode terms = exact(observation.get("terms"), Set.of("declared_target_title_ids", "retained_target_title_ids",
                "claim_disposition", "title_holder_change_count", "primary_gold_transfer_raw", "attacker_prestige_delta_raw",
                "truce_evaluated_days", "prisoner_release_pairs", "favor_hook_will_apply", "hostage_variant"), "white terms");
        ids(terms.get("declared_target_title_ids"), "declared titles"); ids(terms.get("retained_target_title_ids"), "retained titles");
        require(same(terms.get("declared_target_title_ids"), terms.get("retained_target_title_ids")), "white target retention differs");
        eq(terms, "claim_disposition", "retain_and_strengthen_weak"); eq(terms, "hostage_variant", "none");
        number(terms.get("title_holder_change_count"), 0, 0, "white title change");
        number(terms.get("primary_gold_transfer_raw"), 0, 0, "white primary gold");
        number(terms.get("attacker_prestige_delta_raw"), Long.MIN_VALUE, Long.MAX_VALUE, "white prestige");
        nonnegative(terms.get("truce_evaluated_days"), "white truce"); bool(terms.get("favor_hook_will_apply"), "white favor");
        for (JsonNode value : array(terms.get("prisoner_release_pairs"), "white POW pairs")) {
            ObjectNode pair = exact(value, Set.of("jailer_character_id", "prisoner_character_id"), "white POW pair");
            fullId(pair.get("jailer_character_id"), "jailer"); fullId(pair.get("prisoner_character_id"), "prisoner");
        }
        features(row.get("surrender_feature_observation"), false); require(!row.get("source_evidence").isNull(), "available white source absent");
        ObjectNode candidate = StrictJson.object(); candidate.set("frame", observation.get("frame")); candidate.set("white_peace_option", observation.get("option"));
        require(sha(observation.get("evaluated_candidate_sha256"), "white candidate hash").equals(hash(candidate)), "white candidate hash differs");
        return row;
    }

    private static void execution(JsonNode raw, boolean withSurrender) {
        Set<String> keys = new HashSet<>(Set.of("context_constructed", "available", "auto_accept", "recipient_response", "native_validator"));
        if (withSurrender) keys.add("same_frame_surrender");
        if (raw != null && raw.has(NativeInteractionRoles.FIELD)) keys.add(NativeInteractionRoles.FIELD);
        ObjectNode row = exact(raw, keys, "white execution option");
        NativeInteractionRoles roles = NativeInteractionRoles.fromOption(row);
        boolean context = bool(row.get("context_constructed"), "context constructed");
        require(context || !(roles instanceof NativeInteractionRoles.Observed), "observed roles lack constructed context");
        boolean available = bool(row.get("available"), "execution available");
        JsonNode validator = row.get("native_validator");
        if (!validator.isNull()) bool(validator, "native validator");
        if (!row.get("auto_accept").isNull()) bool(row.get("auto_accept"), "auto accept");
        require(!available || context && validator.isBoolean() && validator.booleanValue(), "available option lacks validated context");
        ObjectNode reply = exact(row.get("recipient_response"), Set.of("status", "decision_status_raw", "would_accept_now"), "recipient response");
        if (text(reply.get("status"), "recipient status").equals("unavailable")) { nil(reply, "decision_status_raw"); nil(reply, "would_accept_now"); }
        else {
            eq(reply, "status", "available"); require(context && validator.isBoolean() && validator.booleanValue(), "reply lacks validated context");
            long status = number(reply.get("decision_status_raw"), 0, 2, "decision status");
            require(bool(reply.get("would_accept_now"), "reply answer") == (status != 2), "reply answer/status differ");
        }
        require(!(roles instanceof NativeInteractionRoles.Unavailable)
                || text(reply.get("status"), "recipient status").equals("unavailable"), "unavailable roles cannot bind available answer");
        if (withSurrender) {
            execution(row.get("same_frame_surrender"), false);
            NativeInteractionRoles.requireSameProfile(roles, NativeInteractionRoles.fromOption(row.get("same_frame_surrender")), roles);
        }
    }

    private static void sourceEvidence(JsonNode raw) {
        ObjectNode source = exact(raw, Set.of("game_version", "executable_sha256", "event_war_script_sha256", "war_effects_script_sha256",
                "projection_rules", "copied_same_frame_domains"), "white source");
        eq(source, "game_version", "1.19.0.6");
        eq(source, "executable_sha256", "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86");
        eq(source, "event_war_script_sha256", "BD202AE41EBA3A0E1E7E4277D09ED1E8D8C7E66B378308BB417D974331F9C707");
        eq(source, "war_effects_script_sha256", "A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D");
        ObjectNode rules = exact(source.get("projection_rules"), Set.of("claims", "gold", "prestige", "prisoners", "favor", "truce", "hostages"), "projection rules");
        rules.fields().forEachRemaining(entry -> text(entry.getValue(), "projection rule"));
        strings(source.get("copied_same_frame_domains"), "copied domains");
    }

    private static ObjectNode session(JsonNode raw) {
        ObjectNode row = object(raw, "aggregate session"); String status = text(row.get("status"), "session status");
        if (status.equals("available")) {
            exact(row, Set.of("schema_version", "backend_id", "status", "failure", "binding", "aggregate", "readiness"), "available session");
            var expected = RaiktorExitObservationCodec.expectedBinding(row.get("binding"));
            RaiktorExitObservationCodec.normalizeSession(row, expected);
            RaiktorSurrenderAggregateProducer.validateAggregate(row.get("aggregate"), expected); return row;
        }
        exact(row, Set.of("schema_version", "backend_id", "status", "failure", "binding", "aggregate", "observed_binding", "readiness"),
                "unavailable session");
        eq(row, "status", "unavailable"); number(row.get("schema_version"), 1, 1, "session version");
        eq(row, "backend_id", RaiktorExitObservationCodec.SESSION_BACKEND); nil(row, "binding"); nil(row, "aggregate");
        ObjectNode failure = exact(row.get("failure"), Set.of("code", "fields"), "session failure");
        require(Set.of("missing_binding_fields", "invalid_binding_fields", "session_binding_mismatch", "aggregate_frame_unavailable",
                "aggregate_frame_mismatch", "aggregate_contract_unavailable").contains(text(failure.get("code"), "failure code")), "unknown session failure");
        require(!strings(failure.get("fields"), "failure fields").isEmpty(), "unavailable session needs failure fields");
        exact(row.get("observed_binding"), Set.of("snapshot.snapshot_id", "snapshot.revision", "snapshot.native_revision", "snapshot.date_raw",
                "snapshot.paused", "snapshot.episode_run_id", "snapshot.episode_character_id", "receipt.queried_snapshot_id",
                "receipt.queried_revision", "receipt.queried_native_revision", "receipt.queried_connection_generation", "receipt.episode_run_id",
                "diagnostics.connection_generation", "diagnostics.bridge_pid"), "observed binding diagnostics");
        ObjectNode readiness = exact(row.get("readiness"), SESSION_READY, "session readiness");
        for (String key : SESSION_READY) truth(readiness, key, false);
        return row;
    }

    private static ObjectNode attachment(ObjectNode request, JsonNode raw) {
        require(request != null, "ATTACH result requires its original request; complete query receipts have extensible fields");
        ObjectNode input = object(request.get("terms_query"), "original terms query");
        ObjectNode row = object(raw, "attached terms query");
        Set<String> expectedKeys = new HashSet<>(); input.fieldNames().forEachRemaining(expectedKeys::add);
        expectedKeys.add("raiktor_surrender_aggregate_session"); exact(row, expectedKeys, "attached query fields");
        ObjectNode retainedInput = input.deepCopy(); retainedInput.remove("raiktor_surrender_aggregate_session");
        ObjectNode retainedOutput = row.deepCopy(); retainedOutput.remove("raiktor_surrender_aggregate_session");
        require(same(retainedInput, retainedOutput), "ATTACH changed original query receipt");
        ObjectNode terms = object(row.get("war_termination_terms"), "attached native terms");
        NativeTerminationTerms.normalize(terms, positive32(terms.get("war_id"), "attached war"));
        session(row.get("raiktor_surrender_aggregate_session")); return row;
    }

    private static ObjectNode model(JsonNode raw) {
        ObjectNode row = exact(raw, MODEL_FIELDS, "inner model");
        truth(row, "model_production_eligible", true); eq(row, "status", "complete");
        String sourceSha = sha(row.get("model_source_sha256"), "model source SHA");
        ObjectNode source = row.deepCopy(); source.remove(List.of("status", "model_source_sha256", "model_production_eligible"));
        source.put("contract", "raiktor-strategy-exit-utility-model-source-v2");
        ObjectNode normalized = RaiktorStrategyConfiguration.renderModel(source, sourceSha);
        require(same(row, normalized), "normalized model differs"); return row;
    }

    private static ObjectNode budgetProvider(JsonNode raw) {
        ObjectNode row = exact(raw, Set.of("schema", "provider", "status", "source", "source_kind", "source_profile_version",
                "default_source_used", "profile_available", "profile_production_eligible", "owner_budget_profile", "blockers", "boundaries"),
                "budget provider result");
        eq(row, "schema", "xar.ck3.raiktor_owner_budget_profile_provider.v1"); eq(row, "provider", "raiktor-owner-budget-profile-provider-v1");
        ObjectNode profile = RaiktorImmediateInputCodec.normalizeBudget(row.get("owner_budget_profile"));
        boolean eligible = bool(profile.get("profile_production_eligible"), "inner profile eligible");
        require(bool(row.get("profile_production_eligible"), "provider eligible") == eligible, "profile eligibility differs");
        require(text(profile.get("status"), "inner budget status").equals(eligible ? "complete" : "incomplete"), "inner profile status differs");
        eq(row, "status", eligible ? "available" : "incomplete"); truth(row, "profile_available", true);
        String sourceHash = providerSource(row); require(sourceHash.equals(sha(profile.get("profile_source_sha256"), "profile SHA")), "budget source hashes differ");
        String kind = text(row.get("source_kind"), "budget source kind");
        require(Set.of("repository_default", "operator_override", "legacy_owner_artifact").contains(kind), "budget source kind unsupported");
        if (kind.equals("legacy_owner_artifact")) nil(row, "source_profile_version");
        else semantic(row.get("source_profile_version"));
        require(bool(row.get("default_source_used"), "budget default used") == kind.equals("repository_default"), "default budget kind differs");
        require(kind.equals("legacy_owner_artifact") || eligible, "versioned budget cannot be ineligible");
        List<String> blockers = strings(row.get("blockers"), "budget blockers");
        require(blockers.equals(eligible ? List.of() : List.of("owner_budget_profile_not_owner_approved")), "budget blockers differ");
        strings(row.get("boundaries"), "budget boundaries"); return row;
    }

    private static ObjectNode modelProvider(JsonNode raw) {
        ObjectNode row = exact(raw, Set.of("schema", "provider", "status", "source", "source_kind", "source_model_version",
                "default_source_used", "model_available", "model_production_eligible", "exit_utility_model", "provider_blockers",
                "downstream_readiness", "boundaries"), "model provider result");
        eq(row, "schema", "xar.ck3.raiktor_exit_utility_model_provider.v1"); eq(row, "provider", "raiktor-exit-utility-model-file-provider-v1");
        eq(row, "status", "available"); truth(row, "model_available", true); truth(row, "model_production_eligible", true); empty(row, "provider_blockers");
        ObjectNode model = model(row.get("exit_utility_model"));
        require(providerSource(row).equals(sha(model.get("model_source_sha256"), "model SHA")), "model source hashes differ");
        require(same(row.get("source_model_version"), model.get("model_version")), "model source version differs"); semantic(row.get("source_model_version"));
        String kind = text(row.get("source_kind"), "model source kind");
        require(Set.of("repository_default", "operator_override").contains(kind), "model source kind unsupported");
        require(bool(row.get("default_source_used"), "model default used") == kind.equals("repository_default"), "default model kind differs");
        ObjectNode readiness = exact(row.get("downstream_readiness"), Set.of("same_frame_utility_evaluation_ready", "white_peace_comparison_ready",
                "decision_ready", "automatic_surrender_ready", "gen034_closed"), "model downstream readiness");
        readiness.fieldNames().forEachRemaining(key -> truth(readiness, key, false));
        strings(row.get("boundaries"), "model boundaries"); return row;
    }

    private static String providerSource(ObjectNode provider) {
        ObjectNode source = exact(provider.get("source"), Set.of("path", "sha256"), "provider source");
        text(source.get("path"), "source path"); return sha(source.get("sha256"), "source SHA");
    }

    private static ObjectNode actual(JsonNode raw) {
        ObjectNode row = exact(raw, Set.of("schema", "status", "recommendation", "blockers", "diagnostics", "action_authority"), "actual result");
        eq(row, "schema", "xar.ck3.raiktor-actual-recommendation-result/v1"); truth(row, "action_authority", false);
        List<String> blockers = strings(row.get("blockers"), "actual blockers"); strings(row.get("diagnostics"), "actual diagnostics");
        String status = text(row.get("status"), "actual status");
        if (status.equals("unavailable")) {
            nil(row, "recommendation"); require(!blockers.isEmpty(), "unavailable actual result needs blockers");
            for (String blocker : blockers) {
                try { RaiktorActualRecommendationFactory.Blocker.valueOf(blocker); }
                catch (IllegalArgumentException failure) { throw new IllegalArgumentException("unknown actual blocker", failure); }
            }
        } else {
            eq(row, "status", "available"); require(blockers.isEmpty(), "available actual result has blockers"); empty(row, "diagnostics");
            recommendation(row.get("recommendation"));
        }
        return row;
    }

    private static void recommendation(JsonNode raw) {
        ObjectNode row = exact(raw, RECOMMENDATION_FIELDS, "actual recommendation");
        eq(row, "schema", "xar.ck3.raiktor_three_way_exit_recommendation.v6");
        eq(row, "provider", "raiktor-three-way-exit-recommendation-provider-v6");
        eq(row, "status", "production_recommendation_available");
        for (String key : List.of("recommendation_ready", "production_recommendation_ready", "action_ready")) truth(row, key, true);
        truth(row, "postcondition_verified", false); truth(row, "gen034_closed", false); empty(row, "blockers"); strings(row.get("boundaries"), "recommendation boundaries");
        ObjectNode c = exact(row.get("recommendation_certificate"), Set.of("schema_version", "contract", "status", "frame", "utility_unit",
                "input_sha256", "opponent_terminal_control", "options", "comparison", "production_live_inputs", "production_recommendation_ready",
                "recommended_outcome", "action_plan", "postcondition_plan", "boundaries", "certificate_sha256"), "recommendation certificate");
        number(c.get("schema_version"), 1, 1, "recommendation version"); eq(c, "contract", "raiktor-three-way-exit-recommendation-v7");
        eq(c, "status", "production_recommendation_available"); eq(c, "utility_unit", "strategy_utility_q100000");
        var frame = RaiktorActualRecommendationFactory.decodeFrame(c.get("frame"));
        hashed(c); hashes(c.get("input_sha256"), Set.of("immediate_exit_evaluation_sha256", "power_dominance_sha256", "utility_model_sha256", "opponent_terminal_control_sha256"));
        truth(c, "production_live_inputs", true); truth(c, "production_recommendation_ready", true);
        String outcome = outcome(c.get("recommended_outcome")); require(same(c.get("recommended_outcome"), row.get("recommended_outcome")), "recommendation outcomes differ");
        ObjectNode action = exact(c.get("action_plan"), Set.of("ready", "semantic_action", "literal", "war_id", "single_action_only"), "action plan");
        truth(action, "ready", true); truth(action, "single_action_only", true); eq(action, "semantic_action", outcome);
        String literal = outcome.equals("continue") ? "resume-map" : (outcome.equals("white_peace") ? "offer-white-peace-" : "surrender-war-") + frame.warId();
        eq(action, "literal", literal); eq(row, "action_literal", literal);
        require(fullId(action.get("war_id"), "action war") == frame.warId(), "action war differs");
        ObjectNode control = exact(c.get("opponent_terminal_control"), Set.of("active", "player_relative_war_score", "attacker_war_score", "defender_war_score", "war_duration_days"), "terminal control");
        bool(control.get("active"), "terminal active"); nonnegative(control.get("war_duration_days"), "war duration");
        for (String key : List.of("player_relative_war_score", "attacker_war_score", "defender_war_score")) integer(control.get(key), key);
        options(c.get("options")); comparison(c.get("comparison"), false); RaiktorUtilityComparisonTrace.fromCertificate(c);
        require(same(c.path("comparison").get("recommended_outcome"), c.get("recommended_outcome")), "comparison outcome differs");
        require(strings(c.path("comparison").get("eligible_options"), "eligible outcomes").contains(outcome)
                && bool(c.path("options").path(outcome).get("eligible"), "recommended option eligible"), "recommendation is not an eligible option");
        require(integer(control.get("player_relative_war_score"), "player score").equals(integer(control.get("attacker_war_score"), "attacker score"))
                && integer(control.get("defender_war_score"), "defender score").equals(integer(control.get("attacker_war_score"), "attacker score").negate()), "terminal scores differ");
        require(bool(control.get("active"), "terminal active") == (integer(control.get("player_relative_war_score"), "player score").compareTo(BigInteger.valueOf(-100)) <= 0),
                "terminal classification differs");
        ObjectNode boundaries = exact(c.get("boundaries"), Set.of("measured_power_is_not_campaign_forecast", "continue_is_strategy_baseline_minus_tail_penalty",
                "long_losing_war_may_scale_tail_penalty_by_power_ratio", "native_execution_availability_excludes_immediate_options",
                "opponent_terminal_control_excludes_continue", "checkpoint_replay_power_input", "action_submitted", "postcondition_verified", "gen034_closed"), "recommendation boundaries");
        boundaries.fieldNames().forEachRemaining(key -> bool(boundaries.get(key), key));
        for (String key : List.of("measured_power_is_not_campaign_forecast", "continue_is_strategy_baseline_minus_tail_penalty",
                "long_losing_war_may_scale_tail_penalty_by_power_ratio", "native_execution_availability_excludes_immediate_options",
                "opponent_terminal_control_excludes_continue")) truth(boundaries, key, true);
        for (String key : List.of("action_submitted", "postcondition_verified", "gen034_closed")) truth(boundaries, key, false);
        postcondition(c.get("postcondition_plan"), outcome, frame);
        immediate(row.get("immediate_exit_evaluation"), c);
    }

    private static void immediate(JsonNode raw, ObjectNode recommendation) {
        ObjectNode row = exact(raw, Set.of("schema", "provider", "status", "utility_evaluation_ready", "immediate_exit_comparison_ready", "production_live_inputs",
                "evaluation_certificate", "blockers", "full_three_way_recommendation_ready", "action_ready", "action_literal", "automatic_surrender_ready", "boundaries"), "immediate result");
        eq(row, "schema", "xar.ck3.raiktor_exit_utility_evaluator.v3"); eq(row, "provider", "raiktor-immediate-exit-utility-evaluator-v3");
        truth(row, "utility_evaluation_ready", true); truth(row, "immediate_exit_comparison_ready", true); truth(row, "production_live_inputs", true);
        for (String key : List.of("full_three_way_recommendation_ready", "action_ready", "automatic_surrender_ready")) truth(row, key, false);
        nil(row, "action_literal"); empty(row, "blockers"); strings(row.get("boundaries"), "immediate boundaries");
        ObjectNode c = exact(row.get("evaluation_certificate"), Set.of("schema_version", "contract", "status", "frame", "utility_unit", "input_sha256",
                "strategy_identity", "options", "comparison", "production_live_inputs", "boundaries", "certificate_sha256"), "immediate certificate");
        number(c.get("schema_version"), 4, 4, "immediate version"); eq(c, "contract", "raiktor-white-peace-vs-surrender-utility-evaluation-v4");
        require(Set.of("pairwise_preference_available", "pairwise_underdetermined").contains(text(c.get("status"), "immediate status")), "immediate status unsupported");
        require(same(row.get("status"), c.get("status")) && same(c.get("frame"), recommendation.get("frame")), "immediate receipt/frame differs");
        eq(c, "utility_unit", "strategy_utility_q100000"); truth(c, "production_live_inputs", true); hashed(c);
        require(sha(recommendation.path("input_sha256").get("immediate_exit_evaluation_sha256"), "immediate input hash").equals(hash(c)), "immediate certificate hash binding differs");
        hashes(c.get("input_sha256"), Set.of("white_peace_projection_sha256", "surrender_session_sha256", "budget_profile_sha256", "utility_model_sha256"));
        ObjectNode identity = exact(c.get("strategy_identity"), Set.of("profile_id", "profile_version", "model_id", "model_version"), "strategy identity");
        text(identity.get("profile_id"), "profile id"); text(identity.get("model_id"), "model id"); semantic(identity.get("profile_version")); semantic(identity.get("model_version"));
        ObjectNode exits = exact(c.get("options"), Set.of("white_peace", "surrender"), "immediate options");
        exit(exits.get("white_peace")); exit(exits.get("surrender")); comparison(c.get("comparison"), true);
        for (String key : List.of("white_peace", "surrender")) require(same(exits.get(key), recommendation.path("options").get(key)), "immediate and recommendation exit options differ");
        ObjectNode flags = exact(c.get("boundaries"), Set.of("immediate_exit_utility_ready", "execution_availability_gated_separately", "continue_utility_ready",
                "full_three_way_recommendation_ready", "action_ready", "action_literal"), "immediate boundaries");
        truth(flags, "immediate_exit_utility_ready", true); truth(flags, "execution_availability_gated_separately", true);
        for (String key : List.of("continue_utility_ready", "full_three_way_recommendation_ready", "action_ready")) truth(flags, key, false);
        nil(flags, "action_literal");
    }

    private static void options(JsonNode raw) {
        ObjectNode options = exact(raw, OUTCOMES, "three-way options");
        ObjectNode c = exact(options.get("continue"), Set.of("measured_power_relation", "base_utility_raw", "tail_risk_penalty_raw",
                "tail_risk_base_penalty_raw", "tail_risk_power_scale_applied", "tail_risk_long_war_scale_start_days", "observed_war_duration_days",
                "observed_player_relative_war_score", "measured_power_ratio_raw", "measured_power_ratio_scale", "utility_raw", "hard_budget_breaches",
                "execution_blockers", "eligible", "campaign_outcome_forecast_ready"), "continue option");
        require(Set.of("actor_stronger", "equal", "opponent_stronger").contains(text(c.get("measured_power_relation"), "power relation")), "unknown power relation");
        for (String key : List.of("base_utility_raw", "observed_player_relative_war_score", "utility_raw")) integer(c.get(key), key);
        for (String key : List.of("tail_risk_penalty_raw", "tail_risk_base_penalty_raw", "tail_risk_long_war_scale_start_days", "observed_war_duration_days")) nonnegative(c.get(key), key);
        positive64(c.get("measured_power_ratio_raw"), "power ratio"); positive64(c.get("measured_power_ratio_scale"), "power scale");
        bool(c.get("tail_risk_power_scale_applied"), "power scale applied"); bool(c.get("eligible"), "continue eligible"); truth(c, "campaign_outcome_forecast_ready", false);
        strings(c.get("hard_budget_breaches"), "continue breaches"); strings(c.get("execution_blockers"), "continue blockers");
        exit(options.get("white_peace")); exit(options.get("surrender"));
    }

    private static void exit(JsonNode raw) {
        ObjectNode row = exact(raw, Set.of("features", "contributions_raw", "base_utility_raw", "unobserved_dynamic_effects",
                "uncertainty_penalty_raw", "utility_raw", "hard_budget_breaches", "execution_blockers", "eligible"), "exit option");
        features(row.get("features"), false); features(row.get("contributions_raw"), true);
        for (String key : List.of("base_utility_raw", "utility_raw")) integer(row.get(key), key);
        nonnegative(row.get("uncertainty_penalty_raw"), "uncertainty penalty");
        for (String key : List.of("unobserved_dynamic_effects", "hard_budget_breaches", "execution_blockers")) strings(row.get(key), key);
        bool(row.get("eligible"), "exit eligible");
    }

    private static void features(JsonNode raw, boolean contributions) {
        ObjectNode features = exact(raw, FEATURES, "utility features");
        for (String key : FEATURES) {
            if (contributions) integer(features.get(key), key);
            else if (key.equals("attacker_prestige_delta_raw")) number(features.get(key), Long.MIN_VALUE, Long.MAX_VALUE, key);
            else nonnegative(features.get(key), key);
        }
    }

    private static void comparison(JsonNode raw, boolean immediate) {
        String outcomeKey = immediate ? "preferred_immediate_exit" : "recommended_outcome";
        String marginKey = immediate ? "preference_margin_raw" : "winning_margin_raw";
        ObjectNode row = exact(raw, Set.of("status", "eligible_options", outcomeKey, marginKey, "minimum_switch_margin_raw"), "utility comparison");
        require((immediate ? Set.of("pairwise_preference_available", "pairwise_underdetermined")
                : Set.of("static_recommendation_available", "three_way_underdetermined")).contains(text(row.get("status"), "comparison status")),
                "comparison status unsupported");
        for (String name : strings(row.get("eligible_options"), "eligible outcomes")) require(OUTCOMES.contains(name) && (!immediate || !name.equals("continue")), "eligible outcome unsupported");
        if (!row.get(outcomeKey).isNull()) { String name = outcome(row.get(outcomeKey)); require(!immediate || !name.equals("continue"), "immediate comparison recommends continue"); }
        if (!row.get(marginKey).isNull()) nonnegative(row.get(marginKey), "comparison margin");
        positive64(row.get("minimum_switch_margin_raw"), "switch margin");
    }

    private static void postcondition(JsonNode raw, String outcome, M0Frame frame) {
        ObjectNode row = exact(raw, Set.of("schema_version", "route", "requirements", "expectations", "verified", "gen034_completion_eligible"), "postcondition plan");
        number(row.get("schema_version"), 1, 1, "postcondition version"); eq(row, "route", outcome); strings(row.get("requirements"), "postcondition requirements");
        truth(row, "verified", false); truth(row, "gen034_completion_eligible", !outcome.equals("continue"));
        ObjectNode e = object(row.get("expectations"), "postcondition expectations");
        if (outcome.equals("continue")) {
            exact(e, Set.of("war_id", "played_character_id", "episode_id", "successor_revision_required"), "continue expectations");
            eq(e, "episode_id", frame.episodeId()); truth(e, "successor_revision_required", true);
        } else {
            exact(e, Set.of("war_id", "played_character_id", "opponent_character_id", "resources", "truce", "source_specific_loss", "checkpoint"), "exit expectations");
            require(fullId(e.get("opponent_character_id"), "expected opponent") == frame.primaryDefenderCharacterId(), "expected opponent differs");
            ObjectNode resources = exact(e.get("resources"), Set.of("scale", "gold", "prestige"), "expected resources");
            number(resources.get("scale"), 100_000, 100_000, "resource scale");
            for (String key : List.of("gold", "prestige")) {
                ObjectNode amount = exact(resources.get(key), Set.of("pre_raw", "delta_raw", "post_raw"), "resource expectation");
                for (String field : List.of("pre_raw", "delta_raw", "post_raw")) number(amount.get(field), Long.MIN_VALUE, Long.MAX_VALUE, field);
                require(integer(amount.get("pre_raw"), "pre").add(integer(amount.get("delta_raw"), "delta")).equals(integer(amount.get("post_raw"), "post")), "resource expectation arithmetic differs");
            }
            ObjectNode truce = exact(e.get("truce"), Set.of("owner_character_id", "toward_character_id", "evaluated_days", "persisted_expiry_required"), "truce expectation");
            require(fullId(truce.get("owner_character_id"), "truce owner") == frame.primaryAttackerCharacterId()
                    && fullId(truce.get("toward_character_id"), "truce target") == frame.primaryDefenderCharacterId(), "truce direction differs");
            nonnegative(truce.get("evaluated_days"), "expected truce days"); truth(truce, "persisted_expiry_required", true);
            ObjectNode loss = exact(e.get("source_specific_loss"), Set.of("war_id", "required_cleanup_status"), "loss expectation");
            require(fullId(loss.get("war_id"), "loss war") == frame.warId(), "loss war differs"); eq(loss, "required_cleanup_status", "destroyed");
            ObjectNode checkpoint = exact(e.get("checkpoint"), Set.of("cold_restore_required"), "checkpoint expectation"); truth(checkpoint, "cold_restore_required", true);
        }
        require(fullId(e.get("war_id"), "expected war") == frame.warId()
                && fullId(e.get("played_character_id"), "expected actor") == frame.primaryAttackerCharacterId(), "postcondition identities differ");
    }

    private static void hashed(ObjectNode certificate) {
        ObjectNode unhashed = certificate.deepCopy(); unhashed.remove("certificate_sha256");
        require(sha(certificate.get("certificate_sha256"), "certificate SHA").equals(hash(unhashed)), "certificate hash differs");
    }
    private static void hashes(JsonNode raw, Set<String> keys) { exact(raw, keys, "input hashes").fields().forEachRemaining(e -> sha(e.getValue(), e.getKey())); }
    private static void ids(JsonNode raw, String name) { for (JsonNode value : array(raw, name)) fullId(value, name); }
    private static void eq(ObjectNode row, String key, String expected) { require(text(row.get(key), key).equals(expected), key + " identity differs"); }
    private static void truth(ObjectNode row, String key, boolean expected) { require(bool(row.get(key), key) == expected, key + " flag differs"); }
    private static void nil(ObjectNode row, String key) { require(row.has(key) && row.get(key).isNull(), key + " must be explicit null"); }
    private static void empty(ObjectNode row, String key) { require(strings(row.get(key), key).isEmpty(), key + " must be empty"); }
    private static String semantic(JsonNode raw) { String value = text(raw, "semantic version"); require(value.matches("[1-9]\\d*\\.\\d+\\.\\d+"), "semantic version malformed"); return value; }
    private static String outcome(JsonNode raw) { String value = text(raw, "outcome"); require(OUTCOMES.contains(value), "outcome unsupported"); return value; }
}

