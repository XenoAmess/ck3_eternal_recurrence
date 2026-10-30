package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Existing independence-then-populist refusal policies; no new event strategy or result credit. */
final class ExistingFactionEventPolicies {
    private ExistingFactionEventPolicies() { }
    record Role(String name, String kind, String field) { }
    static final List<Role> POPULIST_IDENTITIES = List.of(new Role("faction", "faction", "faction_id"), new Role("target_title", "landed_title", "title_id"),
        new Role("peasant_leader", "character", "character_id"), new Role("peasant_county", "landed_title", "title_id"));
    private static final Map<String, String> POPULIST_ROLES = Map.of("faction", "faction", "faction_leader", "character", "faction_target", "character",
        "peasant_leader", "character", "peasant_county", "landed_title", "target_title", "landed_title", "new_title", "landed_title");
    private static final String INDEPENDENCE = "faction_demand.0001";
    private static final String INDEPENDENCE_OPTIONS = "6237b0c9f4e27ba6f1197d8cad68d41b58bfd64112cdb8705d80b626759f9192";
    private static final ObjectValue REVIEW = RetainedJson.object(RetainedJson.parse("""
        {"schema":"xar.independence0001-static-source-review/v1","event_definition_key":"faction_demand.0001","ck3_build":"1.20.0.4",
         "required_ck3_exe_sha256":"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
         "source_relative":"events/factions/faction_demands.txt","source_sha256":"eb17720ca9d48acfb8cc24e5f61edc62fd2d4d2d599561c92854fc762104eccd",
         "definition_block_sha256":"cd59166f6becea0e42f07d12c77a5a4fdfb5a3dccb55b3131d3ad62245a639f0",
         "source_dependencies":{"common/scripted_effects/00_war_effects.txt":"f811d12ccb11f3aae2f61b234e930e20880be9b7c065bb9f4557400bd711722b"},
         "option_catalogue_sha256":"6237b0c9f4e27ba6f1197d8cad68d41b58bfd64112cdb8705d80b626759f9192","readiness":"static-ready","new_live_evidence":false,"observations":[],
         "authored_options":[{"native_option_index":0,"source_name_key":"FACTION_DEMAND_ACCEPT","effect":"every_faction_member_change_liege_or_become_independent","add_claim_on_loss":false,"truce_days":1825},
          {"native_option_index":1,"source_name_key":"FACTION_DEMAND_BRIBE_CO_EMPEROR","effect":"offer_co_emperorship_via_faction_demand.0006","visibility_and_legality":"conditional_native_presentation"},
          {"native_option_index":2,"source_name_key":"FACTION_DEMAND_REFUSE","effect":"reject_demand_then_faction_demand.0003_faction_start_war"}],
         "source_review":"docs/ck3-native-ai/g2-m5-independence-ultimatum-policy-2026-10-19.md",
         "complete_source_options_and_effects":"docs/ck3-native-ai/evidence/g2-m5-independence-ultimatum-policy-2026-10-19.json","material_effects_verified":false,"live_qualification":false}
        """.getBytes(StandardCharsets.UTF_8)));

    static ObjectValue choose(ObjectValue plan, ObjectValue snapshot, List<String> actionSteps) {
        if (snapshot == null) return plan;
        ObjectValue independent = independence(plan, snapshot, actionSteps);
        return populist(independent, snapshot, actionSteps);
    }
    static Map<BigInteger, ObjectValue> byNative(List<ObjectValue> rows) {
        Map<BigInteger, ObjectValue> result = new HashMap<>();
        for (ObjectValue row : rows) result.put(number(row, "native_option_index"), row); return result;
    }
    private static BigInteger rawIdentity(ObjectValue scope, String kind, String field) {
        ObjectValue identity = o(scope, "typed_identity");
        return eq(scope, "status", s("available")) && eq(identity, "status", s("available")) && eq(identity, "kind", s(kind)) ? number(identity, field) : null;
    }
    static boolean recognizesPopulist(ObjectValue context, BigInteger actor, BigInteger count) {
        try {
            Map<String, ObjectValue> rows = roles(context, false, false); Map<String, ObjectValue> scopes = new HashMap<>();
            rows.forEach((name, row) -> scopes.put(name, o(row, "scope")));
            List<ObjectValue> options = objects(context, "options");
            BigInteger root = rawIdentity(o(context, "root_scope"), "character", "character_id"), leader = rawIdentity(scopes.get("peasant_leader"), "character", "character_id");
            BigInteger target = rawIdentity(scopes.get("faction_target"), "character", "character_id"), namedLeader = rawIdentity(scopes.get("faction_leader"), "character", "character_id");
            return Set.of("1.20.0.3", "1.20.0.4").contains(SourceReviewedEventConsumer.build(context)) && eq(context, "status", s("available"))
                && eq(context, "event_definition_key", s("faction_demand.1001")) && positive(actor) && actor.equals(root) && actor.equals(target)
                && positive(leader) && leader.equals(namedLeader) && !leader.equals(root) && scopes.keySet().equals(POPULIST_ROLES.keySet())
                && POPULIST_ROLES.entrySet().stream().allMatch(role -> eq(scopes.get(role.getKey()), "type_key", s(role.getValue())))
                && BigInteger.valueOf(4).equals(count) && options.size() == 2 && byNative(options).keySet().equals(Set.of(BigInteger.TWO, BigInteger.valueOf(3)))
                && options.stream().allMatch(row -> yes(row, "shown") && EventOptionAvailability.selectionAllowed(context,row));
        } catch (IllegalArgumentException error) { return false; }
    }
    private static ObjectValue reviewedIndependenceBinding(ObjectValue capture) {
        SourceReviewedEventConsumer.NativeBinding current;
        try { current = SourceReviewedEventConsumer.nativeBinding(capture); }
        catch (IllegalArgumentException error) { return null; }
        if (!current.build().equals("1.20.0.4") || !current.eventKey().equals(INDEPENDENCE) || !current.backend().equals(SourceReviewedEventConsumer.BACKEND)
                || !current.optionCount().equals(BigInteger.valueOf(3))) return null;
        ObjectValue binding = put(current.json(), f("source_sha256", s(SourceReviewedEventConsumer.FACTION_SOURCE)), f("option_catalogue_sha256", s(INDEPENDENCE_OPTIONS)));
        ObjectValue audit = o(capture, "source_knowledge");
        if (audit != null) {
            if (eq(audit, "status", s("offline-source-reviewed"))) {
                if (!eq(audit, "binding_mode", s("exact")) || !eq(audit, "fingerprint", s(fingerprint(binding)))) return null;
            } else if (!eq(audit, "status", s("unknown")) || truthy(v(audit, "rejected_entries"))) return null;
        }
        return binding;
    }
    private static boolean truthy(Value value) {
        return switch (value) {
            case NullValue ignored -> false;
            case BooleanValue flag -> flag.value();
            case StringValue text -> !text.value().isEmpty();
            case IntegerValue number -> number.value().signum() != 0;
            case FloatingValue number -> number.value() != 0;
            case ArrayValue rows -> !rows.values().isEmpty();
            case ObjectValue rows -> !rows.fields().isEmpty();
        };
    }
    private static boolean sameFields(ObjectValue first, ObjectValue second, List<String> fields) {
        return fields.stream().allMatch(key -> v(first, key).equals(v(second, key)));
    }
    private static ObjectValue independence(ObjectValue plan, ObjectValue snapshot, List<String> steps) {
        try {
            ObjectValue capture = o(plan, "unhandled_event_fallback");
            if (!eq(capture, "event_definition_key", s(INDEPENDENCE)) || text(plan, "phase") == null || !Set.of("active_event_unhandled_first_rendered_option", "active_event_source_reviewed_first_rendered_option").contains(text(plan, "phase"))) return plan;
            ObjectValue current = reviewedIndependenceBinding(capture), context = o(capture, "window_context"), frame = o(capture, "binding"), selection = o(capture, "selection");
            ObjectValue decision = o(plan, "event_decision"), summary = o(plan, "active_event"), diagnostics = o(snapshot, "diagnostics"), actor = o(snapshot, "played_character"), active = o(snapshot, "active_event"), prior = o(capture, "source_knowledge");
            if (eq(prior, "status", s("offline-source-reviewed")) && (!yes(capture, "registry_known") || !eq(decision, "status", s("source_reviewed_known")))) return plan;
            if (current == null || context == null || frame == null || selection == null || decision == null || summary == null || diagnostics == null || actor == null || active == null
                    || !eq(context, "status", s("available")) || !eq(context, "window_match_count", i(1)) || !EventOptionAvailability.supportedContext(context)
                    || !yes(snapshot, "paused") || !yes(snapshot, "map_ready") || !yes(actor, "alive") || !positive(number(actor, "character_id"))
                    || !v(frame, "actor_character_id").equals(v(actor, "character_id")) || !yes(frame, "paused") || !yes(frame, "map_ready")
                    || !positive(number(frame, "native_revision")) || !eq(frame, "snapshot_id", s("native:" + number(frame, "native_revision")))
                    || text(frame, "episode_run_id") == null || text(frame, "episode_run_id").isEmpty()
                    || !sameFields(snapshot, frame, List.of("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id"))
                    || List.of("bridge_pid", "connection_generation").stream().anyMatch(key -> !positive(number(frame, key)) || !v(diagnostics, key).equals(v(frame, key)))
                    || !v(context, "snapshot_revision").equals(v(frame, "native_revision")) || !v(context, "date_raw").equals(v(frame, "date_raw"))
                    || !positive(number(active, "instance_id")) || !v(active, "instance_id").equals(v(capture, "current_event_instance_id"))
                    || !v(context, "current_event_instance_id").equals(v(active, "instance_id")) || !eq(active, "option_count", i(3))) return plan;
            ObjectValue ready = o(context, "readiness"); BigInteger actorId = number(actor, "character_id");
            if (ready == null || List.of("event_definition_identity_ready", "root_scope_ready", "saved_scopes_ready", "option_presentation_ready").stream().anyMatch(key -> !yes(ready, key))
                    || !actorId.equals(identity(o(context, "root_scope"), "character", "character_id"))) return plan;
            Map<String, ObjectValue> roles = roles(context, true, false);
            BigInteger faction = identity(o(roles.get("faction"), "scope"), "faction", "faction_id"), leader = identity(o(roles.get("faction_leader"), "scope"), "character", "character_id");
            if (faction == null || leader == null || leader.equals(actorId) || !actorId.equals(identity(o(roles.get("faction_target"), "scope"), "character", "character_id"))) return plan;
            List<ObjectValue> shown = objects(context, "options").stream().filter(row -> yes(row, "shown")).toList();
            if (shown.isEmpty()) return plan;
            Set<BigInteger> natives = new HashSet<>(), rendered = new HashSet<>();
            for (ObjectValue row : shown) {
                BigInteger nativeIndex = number(row, "native_option_index"), renderedIndex = number(row, "rendered_index");
                if (nativeIndex == null || nativeIndex.signum() < 0 || nativeIndex.compareTo(BigInteger.valueOf(3)) >= 0 || renderedIndex == null || renderedIndex.signum() < 0
                        || !natives.add(nativeIndex) || !rendered.add(renderedIndex)) return plan;
            }
            for (int index = 0; index < shown.size(); index++) if (!rendered.contains(BigInteger.valueOf(index))) return plan;
            ObjectValue refuse = byNative(shown).get(BigInteger.TWO);
            ObjectValue first = shown.stream().filter(row -> EventOptionAvailability.selectionAllowed(context,row)).min(Comparator.comparing(row -> number(row, "rendered_index"))).orElse(null);
            String step = "select-event-option-3";
            if (refuse == null || !EventOptionAvailability.selectionAllowed(context,refuse) || text(refuse, "resolved_name") == null || text(refuse, "resolved_name").isEmpty() || first == null
                    || !eq(first, "native_option_index", i(0)) || !sameFields(selection, first, List.of("native_option_index", "rendered_index")) || !EventOptionAvailability.selectionAllowed(context,selection)
                    || !eq(selection, "option_number", i(1)) || !v(selection, "selected_step").equals(v(plan, "selected_step"))
                    || !eq(plan, "selected_step", s("select-event-option-1")) || !steps.contains(step)) return plan;
            Value renderedIndex = v(refuse, "rendered_index");
            ObjectValue outcome = obj(f("status", s("source_reviewed_expected_only")), f("event_definition_key", s(INDEPENDENCE)),
                f("saved_faction_id", RetainedJson.value(faction)), f("saved_faction_leader_character_id", RetainedJson.value(leader)),
                f("expected_effect", s("faction_demand.0003_faction_start_war")), f("rejected_effect", s("every_faction_member_change_liege_or_become_independent")),
                f("exact_lost_titles", NULL), f("war_started_verified", b(false)), f("victory_verified", b(false)), f("title_retention_verified", b(false)),
                f("decision_basis", s("preserve_realm_accept_faction_war_risk")), f("same_frame_faction_strength", s("not_available_in_bound_event_context")), f("counterfactual_optimality_verified", b(false)));
            summary = put(summary, f("selected_option_number", i(3)), f("selected_native_option_index", i(2)), f("selected_rendered_index", renderedIndex),
                f("source_registry_known", b(true)), f("source_knowledge_status", s("source_reviewed_known")), f("semantic_optimal", b(false)));
            decision = put(decision, f("status", s("source_reviewed_known")), f("registry_known", b(true)), f("source_registry_known", b(true)), f("selected_option_number", i(3)),
                f("selected_native_option_index", i(2)), f("selected_rendered_index", renderedIndex), f("classification", s("source-analyzed-independence-refusal-policy")),
                f("source_reviewed_policy", s("independence_refuse_preserve_realm_accept_war_risk")), f("semantic_optimal", b(false)), f("material_effects_verified", b(false)), f("registry_contract_accepted", b(false)));
            ObjectValue audit = obj(f("status", s("independence0001_source_reviewed_current_binding")), f("binding", current), f("binding_fingerprint", s(fingerprint(current))),
                f("source_review_fingerprint", s(fingerprint(REVIEW))), f("prior_source_knowledge", prior == null ? NULL : prior),
                f("review_kind", s("static_source_without_invented_incident")), f("loaded_definition_bytes_verified", b(false)), f("live_qualification", b(false)), f("material_effects_verified", b(false)), f("registry_contract_accepted", b(false)));
            selection = put(selection, f("rendered_index", renderedIndex), f("native_option_index", i(2)), f("option_number", i(3)), f("resolved_name", v(refuse, "resolved_name")),
                f("enabled", v(refuse, "enabled")), f("selected_step", s(step)), f("selection_order", s("source_analyzed_independence_refuse_preserve_realm")));
            if (refuse.contains("gui_availability")) selection = selection.with("gui_availability", refuse.get("gui_availability"));
            capture = put(capture, f("policy", s("source-analyzed-independence-refuse-preserve-realm")), f("registry_known", b(true)), f("offline_followup_required", b(false)), f("source_knowledge", audit), f("selection", selection));
            return put(plan, f("phase", s("active_event_source_reviewed_independence_refusal")), f("selected_step", s(step)),
                f("reason", s("Known .4 independence ultimatum: accepting releases faction members without claims on loss. Choose the currently enabled refusal; it triggers the faction-war chain. War outcome and land retention remain unverified.")),
                f("faction_demand_source_outcome", outcome), f("active_event", summary), f("event_decision", decision), f("unhandled_event_fallback", capture));
        } catch (IllegalArgumentException error) { return plan; }
    }
    static boolean sourceKnownPopulist(ObjectValue capture, ObjectValue audit) {
        if (!eq(audit, "status", s("offline-source-reviewed")) || text(audit, "binding_mode") == null || !Set.of("exact", "populist1001_source_rebound").contains(text(audit, "binding_mode"))) return false;
        SourceReviewedEventConsumer.NativeBinding current;
        try { current = SourceReviewedEventConsumer.nativeBinding(capture); } catch (IllegalArgumentException error) { return false; }
        if (!current.build().equals("1.20.0.4") || !current.eventKey().equals("faction_demand.1001") || !current.backend().equals(SourceReviewedEventConsumer.BACKEND) || !current.optionCount().equals(BigInteger.valueOf(4))) return false;
        ObjectValue binding = put(current.json(), f("source_sha256", s(SourceReviewedEventConsumer.FACTION_SOURCE)), f("option_catalogue_sha256", s(SourceReviewedEventConsumer.POPULIST_OPTIONS)));
        if (eq(audit, "binding_mode", s("exact"))) return eq(audit, "fingerprint", s(fingerprint(binding)));
        ObjectValue adapted = o(audit, "adapted_from"), shape = o(audit, "root_scope_shape");
        return eq(audit, "source_rebind_policy", s(SourceReviewedEventConsumer.POPULIST_POLICY)) && eq(shape, "source_event_type", s("letter_event"))
            && eq(shape, "source_rebind_policy", s(SourceReviewedEventConsumer.POPULIST_POLICY)) && eq(audit, "fresh_binding", binding) && eq(audit, "fresh_binding_fingerprint", s(fingerprint(binding)))
            && v(adapted, "fingerprint").equals(v(audit, "fingerprint")) && positive(number(adapted, "calculated_event_id")) && !v(adapted, "calculated_event_id").equals(v(binding, "calculated_event_id"));
    }
    private static ObjectValue populist(ObjectValue plan, ObjectValue snapshot, List<String> steps) {
        try {
            ObjectValue capture = o(plan, "unhandled_event_fallback"), audit = o(capture, "source_knowledge"), context = o(capture, "window_context"), selection = o(capture, "selection"), binding = o(capture, "binding"), decision = o(plan, "event_decision");
            if (!eq(plan, "phase", s("active_event_source_reviewed_first_rendered_option")) || capture == null || audit == null || context == null || selection == null || binding == null || decision == null
                    || !eq(capture, "event_definition_key", s("faction_demand.1001")) || !eq(context, "event_definition_key", s("faction_demand.1001"))
                    || !eq(o(context, "provenance"), "backend_id", s(SourceReviewedEventConsumer.BACKEND)) || !eq(context, "status", s("available")) || !eq(context, "window_match_count", i(1))
                    || !eq(capture, "snapshot_option_count", i(4)) || !sourceKnownPopulist(capture, audit) || text(audit, "entry_sha256") == null || text(audit, "entry_sha256").length() != 64
                    || !yes(capture, "registry_known") || !eq(decision, "status", s("source_reviewed_known")) || !eq(decision, "material_effects_verified", b(false))
                    || !eq(plan, "selected_step", s("select-event-option-3")) || !eq(selection, "native_option_index", i(2)) || !eq(selection, "rendered_index", i(0)) || !EventOptionAvailability.selectionAllowed(context,selection)
                    || !v(selection, "selected_step").equals(v(plan, "selected_step")) || !steps.contains("select-event-option-4")) return plan;
            if (!yes(snapshot, "paused") || !yes(snapshot, "map_ready") || !sameFields(snapshot, binding, List.of("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id"))
                    || !eq(binding, "snapshot_id", s("native:" + number(binding, "native_revision"))) || !v(context, "snapshot_revision").equals(v(snapshot, "native_revision")) || !v(context, "date_raw").equals(v(snapshot, "date_raw"))) return plan;
            ObjectValue diagnostics = o(snapshot, "diagnostics"), actor = o(snapshot, "played_character"), active = o(snapshot, "active_event");
            if (diagnostics == null || actor == null || active == null || !yes(actor, "alive") || !v(actor, "character_id").equals(v(binding, "actor_character_id"))
                    || !sameFields(diagnostics, binding, List.of("bridge_pid", "connection_generation")) || !v(active, "instance_id").equals(v(capture, "current_event_instance_id"))
                    || !eq(active, "option_count", i(4)) || !v(context, "current_event_instance_id").equals(v(active, "instance_id"))
                    || !recognizesPopulist(context, number(actor, "character_id"), BigInteger.valueOf(4))) return plan;
            Map<BigInteger, ObjectValue> byNative = byNative(objects(context, "options"));
            if (!byNative.keySet().equals(Set.of(BigInteger.TWO, BigInteger.valueOf(3))) || !eq(byNative.get(BigInteger.TWO), "rendered_index", i(0)) || !eq(byNative.get(BigInteger.valueOf(3)), "rendered_index", i(1))) return plan;
            Map<String, ObjectValue> roles = roles(context, false, false);
            BigInteger faction = identity(o(roles.get("faction"), "scope"), "faction", "faction_id"), target = identity(o(roles.get("target_title"), "scope"), "landed_title", "title_id"),
                leader = identity(o(roles.get("peasant_leader"), "scope"), "character", "character_id"), county = identity(o(roles.get("peasant_county"), "scope"), "landed_title", "title_id");
            if (faction == null || target == null || leader == null || county == null) return plan;
            ObjectValue summary = o(plan, "active_event"); if (summary == null) return plan;
            ObjectValue outcome = obj(f("status", s("source_reviewed_expected_only")), f("event_definition_key", s("faction_demand.1001")),
                f("saved_faction_id", RetainedJson.value(faction)), f("saved_target_title_id", RetainedJson.value(target)), f("saved_peasant_leader_character_id", RetainedJson.value(leader)),
                f("expected_effect", s("faction_start_war")), f("war_started_verified", b(false)), f("victory_verified", b(false)), f("title_retention_verified", b(false)),
                f("decision_basis", s("existing_preserve_realm_policy_accepts_faction_war_risk")), f("same_frame_faction_strength", s("not_available_in_bound_event_context")), f("counterfactual_optimality_verified", b(false)),
                f("visible_alternatives", new ArrayValue(List.of(obj(f("native_option_index", i(2)), f("expected_effect", s("grant_populist_independence")), f("selected", b(false))),
                    obj(f("native_option_index", i(3)), f("expected_effect", s("start_faction_war")), f("selected", b(true)))))));
            summary = put(summary, f("selected_option_number", i(4)), f("selected_native_option_index", i(3)), f("selected_rendered_index", i(1)), f("semantic_optimal", b(false)));
            decision = put(decision, f("selected_option_number", i(4)), f("selected_native_option_index", i(3)), f("selected_rendered_index", i(1)), f("semantic_optimal", b(false)),
                f("classification", s("offline-source-reviewed-populist-refusal-policy")), f("source_reviewed_policy", s("populist_refuse_preserve_realm_accept_war_risk")), f("material_effects_verified", b(false)), f("registry_contract_accepted", b(false)));
            selection = put(selection, f("rendered_index", i(1)), f("native_option_index", i(3)), f("option_number", i(4)), f("resolved_name", v(byNative.get(BigInteger.valueOf(3)), "resolved_name")),
                f("enabled", v(byNative.get(BigInteger.valueOf(3)), "enabled")), f("selected_step", s("select-event-option-4")), f("selection_order", s("exact_source_reviewed_populist_refuse_preserve_realm")));
            ObjectValue actualChoice = byNative.get(BigInteger.valueOf(3));
            if (!EventOptionAvailability.selectionAllowed(context,actualChoice)) return plan;
            if (actualChoice.contains("gui_availability")) selection = selection.with("gui_availability", actualChoice.get("gui_availability"));
            capture = put(capture, f("policy", s("exact-source-reviewed-populist-refuse-preserve-realm")), f("offline_followup_required", b(false)), f("selection", selection));
            return put(plan, f("phase", s("active_event_source_reviewed_populist_refusal")), f("selected_step", s("select-event-option-4")),
                f("reason", s("Exact .4 source: native 2 grants populist independence; enabled native 3 refuses and starts a faction war. Preserve land; victory is unverified.")),
                f("faction_demand_source_outcome", outcome), f("active_event", summary), f("event_decision", decision), f("unhandled_event_fallback", capture));
        } catch (IllegalArgumentException error) { return plan; }
    }
}
