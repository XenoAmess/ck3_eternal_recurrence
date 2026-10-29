package org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions;

import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionTemporalFinance.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionDoctrineDraftReads.schema;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionDoctrineDraftReads.nullableBoolean;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionDoctrineDraftReads.nullableInteger;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionDoctrineDraftReads.nullableText;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerReligionContext.Build;

/** Validates the six original read-only reform/draft trees without deriving action legality. */
public final class ReligionReformDraftValidation {
    private ReligionReformDraftValidation() { }

    public static ObjectNode normalize(ReligionDoctrineDraftReads.Kind kind, ObjectNode original,
            ReligionTemporalFinance.Frame frame) {
        Objects.requireNonNull(kind);
        Objects.requireNonNull(frame);
        ObjectNode value = Objects.requireNonNull(original).deepCopy();
        switch (kind) {
            case REFORM_CONTEXT -> reform(value, frame);
            case AI_REFORM_INPUTS -> ai(value, frame);
            case DRAFT_GROUPS -> groups(value, frame);
            case DRAFT_DOCTRINE_CHOICES -> doctrines(value, frame);
            case DRAFT_TENET_CHOICES -> tenets(value, frame);
            case DRAFT_RESOURCE_COSTS -> resources(value, frame);
            default -> throw new IllegalArgumentException("not a reform/draft observation kind");
        }
        return value;
    }

    private static JsonNode optional(ObjectNode value, String key) {
        JsonNode node = value.get(key);
        return node == null ? NullNode.instance : node;
    }

    private static BigInteger integral(ObjectNode value, String key) {
        JsonNode node = field(value, key);
        need(node.isIntegralNumber(), "native reform integer required: " + key);
        return node.bigIntegerValue();
    }

    private static JsonNode array(ObjectNode value, String key) {
        JsonNode result = field(value, key);
        need(result.isArray(), "native reform array required: " + key);
        return result;
    }

    private static void strings(ObjectNode value, String key) {
        for (JsonNode node : array(value, key)) {
            need(node.isTextual(), "native reform string array required: " + key);
        }
    }

    private static void optionalBoolean(ObjectNode value, String key) {
        JsonNode node = optional(value, key);
        need(node.isNull() || node.isBoolean(), "native reform nullable boolean required: " + key);
    }

    private static void optionalInteger(ObjectNode value, String key, BigInteger low, BigInteger high) {
        JsonNode node = optional(value, key);
        if (!node.isNull()) {
            need(node.isIntegralNumber(), "native reform nullable integer required: " + key);
            range(node.bigIntegerValue(), low, high);
        }
    }

    private static void available(ObjectNode value, String reasonKey) {
        JsonNode reason = field(value, reasonKey);
        need(bool(value, "available") ? reason.isNull()
                : reason.isTextual() && !reason.textValue().isEmpty(),
                "native reform availability reason differs: " + reasonKey);
    }

    private static void frameWhenAvailable(ObjectNode value, ReligionTemporalFinance.Frame frame) {
        if (bool(value, "available")) {
            eq(value, "played_character_id", frame.actor());
            eq(value, "date_raw", frame.date());
        }
    }

    private static void queryFrame(ObjectNode value) {
        integer(value, "capture_epoch", BigInteger.ONE, U64);
        integer(value, "date_raw", I32_MIN, I32_MAX);
        integer(value, "played_character_id", BigInteger.ZERO, U32);
    }

    private static void reform(ObjectNode value, ReligionTemporalFinance.Frame frame) {
        String top = "schema game_version executable_sha256 available unavailable_reason scope capture_epoch date_raw played_character_id readiness current_context current_rite_model main_rite_unreformed current_creation_window current_draft_costs current_draft_eligibility current_popup_choices current_doctrine_selection";
        boolean terms = frame.build() == Build.CROZIER3
                || frame.build() == Build.CROZIER4 && value.has("current_draft_creation_terms");
        exact(value, top + (terms ? " current_draft_creation_terms" : ""));
        eq(value, "schema", schema("ck3_12002_player_religion_reform_query_v1", frame));
        build(value, frame);
        eq(value, "scope", "played_character_current_model_and_already_open_draft");
        integer(value, "capture_epoch", BigInteger.ONE, U64);
        integral(value, "date_raw");
        integral(value, "played_character_id");
        available(value, "unavailable_reason");
        frameWhenAvailable(value, frame);
        String[][] components = {
            {"current_context", "ck3_12002_religion_context_v1", "current_context_ready"},
            {"current_rite_model", "religion_reform12002_rite_model_v1", "current_rite_model_ready"},
            {"main_rite_unreformed", null, "main_rite_status_ready"},
            {"current_creation_window", "ck3_12002_current_rite_creation_window_v1", "current_window_observation_ready"},
            {"current_draft_costs", "ck3_12002_rite_creation_costs_v1", "current_draft_cost_ready"},
            {"current_draft_eligibility", "ck3_12002_rite_draft_eligibility_v1", "current_draft_final_eligibility_ready"},
            {"current_popup_choices", null, "current_popup_collection_ready"},
            {"current_doctrine_selection", "ck3_12002_current_draft_doctrine_selection_v1", "doctrine_final_selection_ready"}
        };
        ObjectNode readiness = object(field(value, "readiness"));
        String readyFields = "current_context_ready current_rite_model_ready main_rite_status_ready current_window_observation_ready current_draft_cost_ready current_draft_final_eligibility_ready current_popup_collection_ready doctrine_final_selection_ready final_choice_legality_readiness";
        exact(readiness, readyFields + (terms ? " current_draft_creation_terms_ready" : ""));
        for (String key : keys(readiness)) bool(readiness, key);
        no(readiness, "final_choice_legality_readiness");
        for (String[] component : components) component(value, readiness, component, frame);
        if (terms) component(value, readiness, new String[]{"current_draft_creation_terms",
                "ck3_12003_current_draft_creation_terms_v1", "current_draft_creation_terms_ready"}, frame);
        ObjectNode window = object(field(value, "current_creation_window"));
        for (String key : List.of("present", "visible", "draft_observed")) bool(window, key);
        need(!bool(window, "draft_observed") || bool(window, "available") && bool(window, "present")
                && bool(window, "visible"), "native reform draft has no actual visible window");
        if (!bool(window, "draft_observed")) {
            for (String key : List.of("current_draft_cost_ready", "current_draft_final_eligibility_ready",
                    "current_popup_collection_ready", "doctrine_final_selection_ready")) no(readiness, key);
            if (terms) no(readiness, "current_draft_creation_terms_ready");
        }
        if (terms) {
            ObjectNode creation = object(field(value, "current_draft_creation_terms"));
            creationTerms(creation, frame);
            eq(creation, "capture_epoch", integral(value, "capture_epoch"));
            eq(creation, "date_raw", integral(value, "date_raw"));
            eq(creation, "played_character_id", integral(value, "played_character_id").and(U32));
            if (bool(creation, "available")) {
                need(bool(value, "available") && bool(window, "draft_observed")
                        && field(creation, "source_rite_id").equals(optional(window, "source_rite_id")),
                        "native creation terms lost the actual current window");
            }
        }
        ObjectNode costs = object(field(value, "current_draft_costs"));
        for (String key : List.of("piety_cost_raw", "piety_missing_signed_raw")) optionalInteger(costs, key, I64_MIN, I64_MAX);
        for (String key : List.of("editing_owned_current_rite", "has_enough_piety")) optionalBoolean(costs, key);
        eq(costs, "raw_scale", BigInteger.valueOf(100000));
        no(costs, "final_creation_legality_observed");
        no(costs, "other_resource_costs_observed");
        ObjectNode eligibility = object(field(value, "current_draft_eligibility"));
        optionalInteger(eligibility, "draft_actor_id", BigInteger.ZERO, U32);
        for (String key : List.of("can_create_rite", "can_edit_rite")) {
            optionalBoolean(eligibility, key);
            need(bool(eligibility, "available") || optional(eligibility, key).isNull(), "unavailable native eligibility was filled");
        }
        ObjectNode popup = object(field(value, "current_popup_choices"));
        eq(popup, "scope", "already_materialized_current_popup_candidates");
        need(bool(popup, "collection_readiness") == bool(popup, "available"), "native popup readiness differs");
        no(popup, "final_choice_legality_readiness");
        for (String key : List.of("doctrines", "tenets")) {
            if (bool(popup, "available")) {
                for (JsonNode node : array(popup, key)) {
                    ObjectNode row = object(node);
                    need(optional(row, "final_can_pick").isNull(), "native popup inferred final choice legality");
                    no(row, "final_choice_legality_readiness");
                }
            } else need(optional(popup, key).isNull(), "unavailable native popup acquired a collection");
        }
        ObjectNode selection = object(field(value, "current_doctrine_selection"));
        eq(selection, "scope", "already_materialized_current_popup_candidates");
        bool(selection, "popup_observed");
        need(bool(selection, "selection_ready") == bool(readiness, "doctrine_final_selection_ready"), "native Doctrine readiness differs");
        array(selection, "selectable_doctrine_keys");
        for (JsonNode row : array(selection, "rows")) bool(object(row), "selectable");
    }

    private static void component(ObjectNode owner, ObjectNode readiness, String[] spec,
            ReligionTemporalFinance.Frame frame) {
        ObjectNode value = object(field(owner, spec[0]));
        boolean observed = bool(value, "available");
        if (spec[1] != null) eq(value, "schema", schema(spec[1], frame));
        need(bool(readiness, spec[2]) == observed, "native reform component readiness differs: " + spec[0]);
        JsonNode reason = optional(value, "unavailable_reason");
        if (observed) {
            need(spec[0].equals("current_creation_window") || reason.isNull(), "available native reform component retains failure");
            if (value.has("capture_epoch")) {
                for (String key : List.of("capture_epoch", "date_raw", "played_character_id"))
                    eq(value, key, integral(owner, key));
            }
        } else need(reason.isTextual() && !reason.textValue().isEmpty(), "unavailable native reform component lost reason");
        if (value.has("game_version")) build(value, frame);
    }

    private static void creationTerms(ObjectNode value, ReligionTemporalFinance.Frame frame) {
        need(frame.build() == Build.CROZIER3 || frame.build() == Build.CROZIER4, "creation terms require exact mapped build");
        exact(value, "schema game_version executable_sha256 available unavailable_reason capture_epoch date_raw played_character_id source_rite_id source_faith_id source_main_rite_id actor_faith_id draft_divergence_raw faith_creation_threshold_raw divergence_results_in_faith_creation native_create_faith_or_reform raw_scale");
        eq(value, "schema", schema("ck3_12003_current_draft_creation_terms_v1", frame));
        build(value, frame);
        queryFrame(value);
        eq(value, "raw_scale", BigInteger.valueOf(100000));
        List<String> references = List.of("source_rite_id", "source_faith_id", "source_main_rite_id", "actor_faith_id");
        List<String> raw = List.of("draft_divergence_raw", "faith_creation_threshold_raw");
        List<String> flags = List.of("divergence_results_in_faith_creation", "native_create_faith_or_reform");
        for (String key : references) nullableInteger(value, key, BigInteger.ZERO, U32);
        for (String key : raw) nullableInteger(value, key, I64_MIN, I64_MAX);
        for (String key : flags) nullableBoolean(value, key);
        available(value, "unavailable_reason");
        frameWhenAvailable(value, frame);
        for (String key : references) need(field(value, key).isNull() != bool(value, "available"), "native creation reference availability differs");
        for (String key : raw) need(field(value, key).isNull() != bool(value, "available"), "native creation scalar availability differs");
        for (String key : flags) need(field(value, key).isNull() != bool(value, "available"), "native creation flag availability differs");
        if (bool(value, "available")) need(bool(value, "divergence_results_in_faith_creation")
                == (integral(value, "draft_divergence_raw").compareTo(integral(value, "faith_creation_threshold_raw")) >= 0),
                "native creation terms lost signed UI comparison");
    }

    private static void ai(ObjectNode value, ReligionTemporalFinance.Frame frame) {
        exact(value, "schema available unavailable_reason capture_epoch date_raw played_character_id context_status controller_count gate_inputs_observation_complete controller_absence context schedule_base controllers");
        eq(value, "schema", schema("ck3_12002_player_religion_ai_reform_inputs_v1", frame));
        need(Set.of("bindings_unavailable", "actor_unavailable", "container_unavailable", "observed_no_ai", "observed_controllers").contains(text(value, "context_status")), "native AI context status differs");
        bool(value, "available"); bool(value, "gate_inputs_observation_complete");
        integer(value, "capture_epoch", BigInteger.ONE, U64);
        integer(value, "date_raw", I32_MIN, I32_MAX);
        integer(value, "played_character_id", I32_MIN, I32_MAX);
        nullableInteger(value, "controller_count", BigInteger.ZERO, U32);
        eq(value, "played_character_id", frame.actor()); eq(value, "date_raw", frame.date());
        available(value, "unavailable_reason");
        JsonNode absence = field(value, "controller_absence");
        need(absence.isNull() || absence.isTextual() && absence.textValue().equals("no_actual_controller"), "native AI absence differs");
        ObjectNode context = object(field(value, "context"));
        exact(context, "schema status available actor_id actual_holder_count controllers");
        eq(context, "schema", schema("ck3_12002_reform_ai_context_v1", frame));
        eq(context, "status", text(value, "context_status")); bool(context, "available");
        nullableInteger(context, "actor_id", BigInteger.ZERO, U32);
        integer(context, "actual_holder_count", BigInteger.ZERO, I32_MAX);
        for (JsonNode controller : array(context, "controllers")) controller(object(controller), false);
        schedule(object(field(value, "schedule_base")));
        if (!field(value, "controllers").isNull())
            for (JsonNode controller : array(value, "controllers")) controller(object(controller), true);
    }

    private static void controller(ObjectNode value, boolean scheduled) {
        exact(value, "kind active_raw special_raw" + (scheduled ? " context_index schedule" : ""));
        need(Set.of("ordinary", "player_special").contains(text(value, "kind")), "native AI controller kind differs");
        for (String key : List.of("active_raw", "special_raw")) integer(value, key, BigInteger.ZERO, BigInteger.valueOf(255));
        if (scheduled) { integer(value, "context_index", BigInteger.ZERO, U32); schedule(object(field(value, "schedule"))); }
    }

    private static void schedule(ObjectNode value) {
        exact(value, "status ai_status current_actor native_globals actual_ai_cache actual_ai_timer");
        need(Set.of("bindings_unavailable", "actor_unavailable", "configuration_unavailable", "observed").contains(text(value, "status")), "native AI schedule status differs");
        need(Set.of("not_supplied", "actor_mismatch", "invalid_state", "gates_only", "observed").contains(text(value, "ai_status")), "native AI schedule context differs");
        ObjectNode actor = object(field(value, "current_actor"));
        exact(actor, "actor_id highest_tier current_independent_ruler");
        nullableInteger(actor, "actor_id", BigInteger.ZERO, U32);
        nullableInteger(actor, "highest_tier", I32_MIN, I32_MAX); nullableBoolean(actor, "current_independent_ruler");
        ObjectNode globals = object(field(value, "native_globals"));
        exact(globals, "reformation_enabled rare_period_prepare_ticks");
        nullableBoolean(globals, "reformation_enabled"); nullableInteger(globals, "rare_period_prepare_ticks", I32_MIN, I32_MAX);
        ObjectNode cache = object(field(value, "actual_ai_cache"));
        exact(cache, "available ai_government_flags ai_independent_flags ai_active_raw ai_special_raw cached_independent_ruler cached_government_bit6 handler_cache_gates_pass");
        bool(cache, "available"); nullableInteger(cache, "ai_government_flags", BigInteger.ZERO, BigInteger.valueOf(65535));
        for (String key : List.of("ai_independent_flags", "ai_active_raw", "ai_special_raw")) nullableInteger(cache, key, BigInteger.ZERO, BigInteger.valueOf(255));
        for (String key : List.of("cached_independent_ruler", "cached_government_bit6", "handler_cache_gates_pass")) nullableBoolean(cache, key);
        ObjectNode timer = object(field(value, "actual_ai_timer"));
        exact(timer, "available rare_countdown_prepare_ticks rare_selected_raw units"); bool(timer, "available");
        nullableInteger(timer, "rare_countdown_prepare_ticks", I32_MIN, I32_MAX);
        nullableInteger(timer, "rare_selected_raw", BigInteger.ZERO, BigInteger.valueOf(255));
        eq(timer, "units", "prepare_invocations");
    }

    private static void groups(ObjectNode value, ReligionTemporalFinance.Frame frame) {
        exact(value, "schema executable_sha256 available unavailable_reason capture_epoch date_raw played_character_id founder_character_id source_rite_id draft_observed category_materialized current_category_slot current_group_key current_selected_definition_key all_group_materialized_choices_complete group_source_scope current_tenet_scope current_tenet_gate_complete current_doctrine_cache_count current_tenet_source_count current_tenet_group_count selected_slots current_tenet_choices");
        eq(value, "schema", schema("ck3_12002_current_draft_group_model_v1", frame));
        need(Build.exact(frame.build().version(), text(value, "executable_sha256")) == frame.build(), "native draft groups build differs");
        for (String key : List.of("available", "draft_observed", "category_materialized", "current_tenet_gate_complete")) bool(value, key);
        no(value, "all_group_materialized_choices_complete");
        eq(value, "group_source_scope", "actual_selected_slot_group_definition_sources");
        eq(value, "current_tenet_scope", "current_materialized_category_status_groups");
        queryFrame(value); integer(value, "founder_character_id", BigInteger.ZERO, U32);
        nullableInteger(value, "source_rite_id", BigInteger.ZERO, U32);
        available(value, "unavailable_reason"); frameWhenAvailable(value, frame);
        need(!bool(value, "draft_observed") || bool(value, "available")
                && integral(value, "founder_character_id").equals(integral(value, "played_character_id")), "native draft groups lost actual founder");
        integer(value, "current_category_slot", BigInteger.valueOf(-1), I32_MAX);
        for (String key : List.of("current_group_key", "current_selected_definition_key")) nullableText(value, key);
        for (String key : List.of("current_doctrine_cache_count", "current_tenet_source_count", "current_tenet_group_count")) integer(value, key, BigInteger.ZERO, U32);
        for (JsonNode node : array(value, "selected_slots")) {
            ObjectNode row = object(node); exact(row, "selected_array_index selected_definition_key group_key group_source_definition_keys");
            integer(row, "selected_array_index", BigInteger.ZERO, U32); text(row, "selected_definition_key"); text(row, "group_key"); strings(row, "group_source_definition_keys");
        }
        JsonNode choices = array(value, "current_tenet_choices");
        for (JsonNode node : choices) {
            ObjectNode row = object(node); exact(row, "tenet_key popup_group_index popup_item_index native_pick_source final_can_pick");
            text(row, "tenet_key");
            for (String key : List.of("popup_group_index", "popup_item_index")) integer(row, key, BigInteger.ZERO, U32);
            integer(row, "native_pick_source", BigInteger.ZERO, BigInteger.valueOf(255)); bool(row, "final_can_pick");
        }
        if (bool(value, "category_materialized")) need(bool(value, "draft_observed") && integral(value, "current_category_slot").signum() >= 0
                && !field(value, "current_group_key").isNull() && !field(value, "current_selected_definition_key").isNull(), "native materialized category lost identity");
        else need(!bool(value, "current_tenet_gate_complete") && choices.isEmpty(), "native final Tenet choices have no current category");
    }

    private static void doctrines(ObjectNode value, ReligionTemporalFinance.Frame frame) {
        exact(value, "schema game_version executable_sha256 scope available unavailable_reason capture_epoch date_raw played_character_id source_rite_id draft_observed doctrine_gates_complete slots");
        eq(value, "schema", schema("ck3_12002_current_draft_full_doctrine_choices_v1", frame)); build(value, frame);
        eq(value, "scope", "actual_current_draft_selected_slot_group_sources");
        for (String key : List.of("available", "draft_observed", "doctrine_gates_complete")) bool(value, key);
        queryFrame(value); nullableInteger(value, "source_rite_id", BigInteger.ZERO, U32);
        available(value, "unavailable_reason"); frameWhenAvailable(value, frame);
        need(!bool(value, "doctrine_gates_complete") || bool(value, "available") && bool(value, "draft_observed"), "native Doctrine gates have no actual current draft");
        for (JsonNode node : array(value, "slots")) {
            ObjectNode slot = object(node); exact(slot, "slot_index group_key selected_doctrine_key sources");
            integer(slot, "slot_index", BigInteger.ZERO, U32); text(slot, "group_key"); text(slot, "selected_doctrine_key");
            for (JsonNode source : array(slot, "sources")) {
                ObjectNode row = object(source); exact(row, "source_index doctrine_key currently_selected duplicate_excluded passed_shown native_can_pick native_knows_doctrine native_has_prophet final_selectable");
                integer(row, "source_index", BigInteger.ZERO, U32); text(row, "doctrine_key");
                for (String key : List.of("currently_selected", "duplicate_excluded", "final_selectable")) bool(row, key);
                for (String key : List.of("passed_shown", "native_can_pick", "native_knows_doctrine", "native_has_prophet")) nullableBoolean(row, key);
            }
        }
    }

    private static void tenets(ObjectNode value, ReligionTemporalFinance.Frame frame) {
        exact(value, "schema game_version executable_sha256 scope available unavailable_reason capture_epoch date_raw played_character_id source_rite_id source_faith_id source_main_rite_id draft_observed tenet_gates_complete raw_category_exemption_present raw_category_exemption_key slots_share_source_predicate slots sources");
        eq(value, "schema", schema("ck3_12002_current_draft_tenet_sources_v1", frame)); build(value, frame);
        eq(value, "scope", "actual_current_draft_all_tenet_sources_shared_slot_predicate"); yes(value, "slots_share_source_predicate");
        for (String key : List.of("available", "draft_observed", "tenet_gates_complete", "raw_category_exemption_present")) bool(value, key);
        queryFrame(value);
        for (String key : List.of("source_rite_id", "source_faith_id", "source_main_rite_id")) nullableInteger(value, key, BigInteger.ZERO, U32);
        available(value, "unavailable_reason"); frameWhenAvailable(value, frame);
        need(!bool(value, "tenet_gates_complete") || bool(value, "available") && bool(value, "draft_observed"), "native Tenet gates have no actual current draft");
        nullableText(value, "raw_category_exemption_key");
        need(bool(value, "raw_category_exemption_present") != field(value, "raw_category_exemption_key").isNull(), "native category exemption differs");
        for (JsonNode node : array(value, "slots")) {
            ObjectNode slot = object(node); exact(slot, "slot_index selected_tenet_key");
            integer(slot, "slot_index", BigInteger.ZERO, U32); nullableText(slot, "selected_tenet_key");
        }
        for (JsonNode node : array(value, "sources")) {
            ObjectNode row = object(node); exact(row, "source_index tenet_key already_selected duplicate_excluded source_can_materialize filtered_out native_status_raw actor_faith_status_raw native_extra_knowledge native_has_prophet knowledge passed_shown passed_selectable_trigger native_can_pick final_selectable");
            integer(row, "source_index", BigInteger.ZERO, U32); text(row, "tenet_key");
            for (String key : List.of("native_status_raw", "actor_faith_status_raw")) integer(row, key, BigInteger.ZERO, BigInteger.valueOf(255));
            for (String key : List.of("already_selected", "duplicate_excluded", "source_can_materialize", "filtered_out", "native_extra_knowledge", "native_has_prophet", "knowledge", "passed_shown", "passed_selectable_trigger", "native_can_pick", "final_selectable")) bool(row, key);
        }
    }

    private static void resources(ObjectNode value, ReligionTemporalFinance.Frame frame) {
        exact(value, "schema available window_present draft_observed failure capture_epoch date_raw played_character_id current_draft_window base_resource_cost_quote");
        eq(value, "schema", schema("ck3_12002_player_religion_draft_resource_costs_query_v1", frame));
        for (String key : List.of("available", "window_present", "draft_observed")) bool(value, key);
        queryFrame(value); available(value, "failure"); frameWhenAvailable(value, frame);
        ObjectNode window = object(field(value, "current_draft_window"));
        exact(window, "schema available unavailable_reason present visible draft_observed played_character_id source_rite_id date_raw capture_epoch");
        eq(window, "schema", schema("ck3_12002_current_rite_creation_window_v1", frame));
        for (String key : List.of("available", "present", "visible", "draft_observed")) bool(window, key);
        need(bool(window, "present") == bool(value, "window_present") && bool(window, "draft_observed") == bool(value, "draft_observed"), "native resource window differs");
        need(!bool(window, "draft_observed") || bool(window, "available") && bool(window, "present") && bool(window, "visible"), "native resource quote has no actual visible draft");
        if (bool(window, "available")) for (String key : List.of("capture_epoch", "date_raw", "played_character_id")) eq(window, key, integral(value, key));
        text(window, "unavailable_reason");
        ObjectNode base = object(field(value, "base_resource_cost_quote"));
        exact(base, "schema scope quote_source game_version executable_sha256 available base_resource_cost_vector_observed draft_kind raw_scale resource_slot_names native_base_fee_slots_raw actual_debit_observed post_action_net_resource_change_observed draft_quote");
        eq(base, "schema", schema("ck3_12002_rite_creation_base_resource_costs_v1", frame));
        eq(base, "scope", "native_command_draft_base_fee_quote");
        eq(base, "quote_source", "native_piety_getter_plus_exact_CCost_initialization");
        eq(base, "raw_scale", BigInteger.valueOf(100000));
        JsonNode names = array(base, "resource_slot_names");
        need(names.size() == 10 && names.get(0).isTextual() && names.get(0).textValue().equals("gold")
                && names.get(1).isTextual() && names.get(1).textValue().equals("prestige")
                && names.get(2).isTextual() && names.get(2).textValue().equals("piety"), "native resource slots differ");
        for (int index = 3; index < 10; index++) need(names.get(index).isNull(), "native reserved resource slot differs");
        no(base, "actual_debit_observed"); no(base, "post_action_net_resource_change_observed");
        need(bool(base, "base_resource_cost_vector_observed") == bool(base, "available"), "native base resource observation differs"); build(base, frame);
        ObjectNode cost = object(field(base, "draft_quote"));
        exact(cost, "schema game_version executable_sha256 available unavailable_reason capture_epoch date_raw played_character_id source_rite_id editing_owned_current_rite piety_cost_raw piety_missing_signed_raw has_enough_piety raw_scale final_creation_legality_observed other_resource_costs_observed");
        eq(cost, "schema", schema("ck3_12002_rite_creation_costs_v1", frame)); build(cost, frame); bool(cost, "available");
        eq(cost, "raw_scale", BigInteger.valueOf(100000)); no(cost, "final_creation_legality_observed"); no(cost, "other_resource_costs_observed");
        for (String key : List.of("piety_cost_raw", "piety_missing_signed_raw")) nullableInteger(cost, key, I64_MIN, I64_MAX);
        for (String key : List.of("editing_owned_current_rite", "has_enough_piety")) nullableBoolean(cost, key);
        JsonNode slots = field(base, "native_base_fee_slots_raw");
        if (bool(base, "available")) {
            need(bool(value, "available") && bool(value, "draft_observed") && bool(cost, "available")
                    && slots.isArray() && slots.size() == 10 && Set.of("edit_owned_current_rite", "create_rite_or_faith").contains(text(base, "draft_kind")), "native base fee vector has no observed draft");
            for (JsonNode raw : slots) { need(raw.isIntegralNumber(), "native base fee integer required"); range(raw.bigIntegerValue(), I64_MIN, I64_MAX); }
            need(field(cost, "piety_cost_raw").isIntegralNumber() && slots.get(2).bigIntegerValue().equals(integral(cost, "piety_cost_raw"))
                    && field(cost, "unavailable_reason").isNull(), "native base fees differ from piety quote");
        } else need(slots.isNull() && field(base, "draft_kind").isNull(), "unavailable native base fees were filled");
    }
}
