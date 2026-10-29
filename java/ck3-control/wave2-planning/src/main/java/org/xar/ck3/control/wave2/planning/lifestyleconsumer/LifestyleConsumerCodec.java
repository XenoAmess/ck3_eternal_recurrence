package org.xar.ck3.control.wave2.planning.lifestyleconsumer;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinCodec;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy.Field;
import org.xar.ck3.control.governance.lifestyleperks.LifestylePerksCodec;
import org.xar.ck3.control.governance.lifestyleperks.LifestylePerksModel;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.governance.focusscope.EducationFocusScopeCodec;
import org.xar.ck3.control.wave2.planning.lifestyleconsumer.LifestyleConsumer.AvailableQuery;
import org.xar.ck3.control.wave2.planning.lifestyleconsumer.LifestyleConsumer.EducationQuery;
import org.xar.ck3.control.wave2.planning.lifestyleconsumer.LifestyleConsumer.ObservationStatus;
import org.xar.ck3.control.wave2.planning.lifestyleconsumer.LifestyleConsumer.Outcome;
import org.xar.ck3.control.wave2.planning.lifestyleconsumer.LifestyleConsumer.Request;
import org.xar.ck3.control.wave2.planning.lifestyleconsumer.LifestyleConsumer.Scope;
import org.xar.ck3.control.wave2.planning.lifestyleconsumer.LifestyleConsumer.ScopeStatus;

/** Original-plan JSON projection and rendering only. Typed domain owners compute all qualifications and recommendations. */
public final class LifestyleConsumerCodec {
    public static final String SCHEMA = "xar.java.lifestyle-consumer.v1";
    private static final ObjectMapper ENCODER = new ObjectMapper();
    private static final Set<String> SNAPSHOT_FIELDS = Set.of("status", "snapshot_id", "episode_run_id", "public_revision", "native_revision",
            "proof_epoch", "date_raw", "player_character_id", "current_focus", "current_lifestyle_progress", "target_lifestyle_progress",
            "owned_perk_keys", "legal_perk_candidates", "legal_focus_candidates", "readiness");
    private static final Set<String> READINESS_FIELDS = Set.of("current_focus_ready", "lifestyle_progress_ready", "owned_perks_ready", "same_frame_ready", "legal_perk_candidates_ready", "legal_focus_candidates_ready");
    private record Decoded(Request request, ObjectNode baseline, ObjectNode query) { }
    private LifestyleConsumerCodec() { }

    public static Request decode(byte[] raw) { return decoded(raw).request; }
    public static byte[] consume(byte[] raw) {
        Decoded decoded = decoded(raw); return render(decoded, LifestyleConsumer.consume(decoded.request));
    }

    private static Decoded decoded(byte[] raw) {
        require(raw != null && raw.length > 0 && raw.length <= 65536, "bounded nonempty consumer request required");
        ObjectNode input = StrictJson.object(OpportunityJson.toNode(OpportunityJson.parse(raw)),
                Set.of("schema", "baseline_plan", "scope", "query", "preferred_focus_target_key", "allow_wartime_initial_focus"));
        require(text(input.get("schema")).equals(SCHEMA), "consumer wrapper schema");
        ObjectNode baseline = object(input.get("baseline_plan"));
        if (!textEquals(baseline.get("selected_step"), "life-advance")) { return new Decoded(new Request(false, null, null), baseline, null); }
        ObjectNode rawScope = object(input.get("scope")); String scopeStatus = nullableText(rawScope.get("status"));
        ScopeStatus status = switch (scopeStatus == null ? "" : scopeStatus) {
            case "admitted" -> ScopeStatus.ADMITTED;
            case "outside_scene" -> ScopeStatus.OUTSIDE_SCENE;
            case "root_query_needed" -> ScopeStatus.ROOT_QUERY_NEEDED;
            default -> ScopeStatus.UNAVAILABLE;
        };
        if (status != ScopeStatus.ADMITTED) {
            Scope scope = new Scope(status, Field.missing(), Field.missing(), Field.missing(), null, null);
            return new Decoded(new Request(true, scope, null), baseline, null);
        }
        Scope scope = new Scope(status, fieldBoolean(rawScope, "at_peace", true), fieldBoolean(rawScope, "collect_taxes_active", null),
                fieldText(rawScope, "government_key"), nullableInteger(rawScope.get("snapshot_revision")), nullableInteger(rawScope.get("player_character_id")));
        JsonNode rawQuery = input.get("query");
        if (rawQuery.isNull()) { return new Decoded(new Request(true, scope, new LifestyleConsumer.Unavailable()), baseline, null); }
        ObjectNode query = object(rawQuery); String queryStatus = nullableText(query.get("status"));
        if ("education_focus_not_applicable".equals(queryStatus)) {
            ObjectNode formal = StrictJson.object().put("schema", EducationFocusScopeCodec.SCHEMA).put("operation", "formal");
            ObjectNode arguments = formal.putObject("input"); arguments.set("combined", query); arguments.set("scope", rawScope);
            EducationFocusScopeCodec.Request evidence = EducationFocusScopeCodec.decode(encodeJson(formal));
            require(evidence instanceof EducationFocusScopeCodec.FormalRequest, "actual formal education qualifier request required");
            return new Decoded(new Request(true, scope, new EducationQuery(((EducationFocusScopeCodec.FormalRequest) evidence).evidence())), baseline, query);
        }
        if (!"available".equals(queryStatus) && !"stock_focus_available".equals(queryStatus)) {
            return new Decoded(new Request(true, scope, new LifestyleConsumer.Unavailable()), baseline, query);
        }
        String preferred = textAllowEmpty(input.get("preferred_focus_target_key"));
        boolean allowWartimeFocus = bool(input.get("allow_wartime_initial_focus"));
        LifestyleMinCodec.RoutedRequest policy = projectPolicy(query.get("snapshot"), scope, preferred, allowWartimeFocus);
        AvailableQuery observation = new AvailableQuery(queryStatus.equals("available") ? ObservationStatus.AVAILABLE : ObservationStatus.STOCK_FOCUS_AVAILABLE,
                nullableText(query.get("formal_precondition_status")), policy);
        return new Decoded(new Request(true, scope, observation), baseline, query);
    }

    private static LifestyleMinCodec.RoutedRequest projectPolicy(JsonNode rawSnapshot, Scope scope, String preferred, boolean allowWartimeFocus) {
        ObjectNode minimum = StrictJson.object().put("schema", LifestyleMinCodec.SCHEMA);
        boolean v3 = rawSnapshot instanceof ObjectNode original && original.has("all_lifestyle_progress_v3");
        if (rawSnapshot == null || rawSnapshot.isNull()) { minimum.putNull("snapshot"); }
        else {
            ObjectNode snapshot = project(object(rawSnapshot), SNAPSHOT_FIELDS);
            projectNested(snapshot, "current_focus", Set.of("presence", "key", "lifestyle_key"));
            projectNested(snapshot, "current_lifestyle_progress", Set.of("presence", "lifestyle_key", "unspent_perk_points"));
            projectNested(snapshot, "target_lifestyle_progress", Set.of("presence", "lifestyle_key", "unspent_perk_points"));
            projectNested(snapshot, "readiness", READINESS_FIELDS);
            for (String key : List.of("legal_perk_candidates", "legal_focus_candidates")) {
                if (snapshot.get(key) instanceof ObjectNode candidates) {
                    ObjectNode projected = project(candidates, Set.of("status", "items"));
                    if (projected.get("items") instanceof ArrayNode rows) {
                        ArrayNode items = projected.arrayNode();
                        for (JsonNode row : rows) { items.add(project(object(row), Set.of("key", "lifestyle_key"))); }
                        projected.set("items", items);
                    }
                    snapshot.set(key, projected);
                }
            }
            minimum.set("snapshot", snapshot);
        }
        minimum.put("feudal_scope_admitted", true);
        if (scope.atPeace().present()) { minimum.put("at_peace", scope.atPeace().value()); } else { minimum.putNull("at_peace"); }
        if (scope.collectTaxes().present()) { minimum.put("collect_taxes_active", scope.collectTaxes().value()); } else { minimum.putNull("collect_taxes_active"); }
        minimum.put("allow_wartime_perk", scope.atPeace().is(false)).put("allow_wartime_initial_focus", allowWartimeFocus)
                .put("preferred_focus_target_key", preferred).putNull("pending_action")
                .put("focus_scope_admitted", !scope.governmentKey().present() || scope.governmentKey().is("feudal_government"));
        LifestyleMinPolicy.Request request = LifestyleMinCodec.request(minimum);
        Field<LifestylePerksModel.Input> allLifestyle = Field.missing();
        if (v3) {
            ObjectNode source = object(rawSnapshot);
            JsonNode progress = source.get("all_lifestyle_progress_v3");
            if (progress == null || progress.isNull() || !hasBinding(source)) { allLifestyle = Field.nullValue(); }
            else {
                ObjectNode wrapper = StrictJson.object().put("schema", LifestylePerksCodec.INPUT_SCHEMA); wrapper.set("snapshot", source);
                ObjectNode binding = wrapper.putObject("binding");
                for (String key : List.of("snapshot_id", "episode_run_id", "public_revision", "native_revision", "proof_epoch", "date_raw", "player_character_id")) {
                    binding.set("expected_" + key, source.get(key));
                }
                wrapper.set("owned", source.get("owned_perk_keys"));
                allLifestyle = Field.of(LifestylePerksCodec.decode(encodeJson(wrapper)));
            }
        }
        return new LifestyleMinCodec.RoutedRequest(request, v3 ? LifestyleMinCodec.ProgressRoute.ALL_LIFESTYLE_V3 : LifestyleMinCodec.ProgressRoute.LIFE2, allLifestyle);
    }

    private static byte[] render(Decoded decoded, Outcome outcome) {
        ObjectNode plan = decoded.baseline.deepCopy(); ObjectNode query = decoded.query;
        switch (outcome.route()) {
            case KEEP_BASELINE -> { return encodeJson(plan); }
            case QUERY_ROOT -> plan.put("phase", "lifestyle_scope_query").put("selected_step", "query-campaign-root-context-v1")
                    .put("reason", "read exact same-frame feudal government before LIFE action");
            case SCOPE_UNAVAILABLE -> plan.put("phase", "lifestyle_scope_unavailable").putNull("selected_step")
                    .put("reason", "feudal scope has no independent true observation");
            case EDUCATION_CONTINUE -> {
                plan.set("lifestyle_query", query); plan.set("lifestyle_query_status", query.get("status"));
                plan.set("lifestyle_native_error", query.get("state").get("native_error"));
                plan.set("lifestyle_decision", EducationFocusScopeCodec.factNode(outcome.educationFact()));
            }
            case NATIVE_QUERY_UNAVAILABLE -> {
                plan.put("phase", "lifestyle_native_query_unavailable").putNull("selected_step");
                if (query == null) { plan.put("lifestyle_query_status", "not_executed").putNull("lifestyle_query"); }
                else { plan.set("lifestyle_query_status", nodeOrNull(query.get("status"))); plan.set("lifestyle_query", query); }
                plan.set("lifestyle_native_error", nativeError(query));
                plan.put("reason", "LIFE2 state or LIFE4 final candidates did not bind this paused player");
            }
            case PERK_SUBMIT, FOCUS_SUBMIT -> {
                ObjectNode decision = object(StrictJson.parse(LifestyleMinCodec.encode(outcome.recommendation())));
                boolean perk = outcome.route() == LifestyleConsumer.Route.PERK_SUBMIT;
                plan.put("phase", perk ? "lifestyle_min_perk_action" : "lifestyle_min_focus_action")
                        .put("selected_step", perk ? "private-select-player-lifestyle-perk-v1" : "private-select-player-lifestyle-stock-focus-v1");
                plan.set("lifestyle_action", decision.get("selected_action")); plan.set("lifestyle_query", query); plan.set("lifestyle_decision", decision);
                plan.put("reason", perk ? "one native-final-legal lifestyle perk" : "one native-final-legal first focus");
            }
            case ACTION_NOT_FIREABLE -> {
                plan.put("phase", "lifestyle_action_not_fireable").putNull("selected_step");
                plan.set("lifestyle_decision", StrictJson.parse(LifestyleMinCodec.encode(outcome.recommendation())));
                plan.put("reason", "the private wire lacks a ready final-legal action");
            }
            case NO_LEGAL_MINIMUM -> plan.set("lifestyle_decision", StrictJson.parse(LifestyleMinCodec.encode(outcome.recommendation())));
            case OBSERVATION_UNAVAILABLE -> {
                plan.put("phase", "lifestyle_min_observation_unavailable").putNull("selected_step");
                plan.set("lifestyle_decision", StrictJson.parse(LifestyleMinCodec.encode(outcome.recommendation())));
                plan.put("reason", "the minimum governance action lacks a complete same-frame input");
            }
        }
        return encodeJson(plan);
    }

    private static JsonNode nativeError(ObjectNode query) {
        if (query == null) { return nodeOrNull(null); }
        JsonNode direct = query.get("native_error"); if (direct != null && !direct.isNull()) { return direct; }
        for (String key : List.of("state", "focus")) {
            if (query.get(key) instanceof ObjectNode component) {
                JsonNode error = component.get("native_error"); if (error != null && !error.isNull()) { return error; }
            }
        }
        return nodeOrNull(null);
    }
    private static boolean hasBinding(ObjectNode snapshot) { return List.of("snapshot_id", "episode_run_id", "public_revision", "native_revision", "proof_epoch", "date_raw", "player_character_id").stream().allMatch(snapshot::hasNonNull); }
    private static ObjectNode project(ObjectNode source, Set<String> fields) {
        ObjectNode result = StrictJson.object(); source.properties().forEach(entry -> { if (fields.contains(entry.getKey())) { result.set(entry.getKey(), entry.getValue()); } }); return result;
    }
    private static void projectNested(ObjectNode source, String key, Set<String> fields) { if (source.get(key) instanceof ObjectNode object) { source.set(key, project(object, fields)); } }
    private static Field<Boolean> fieldBoolean(ObjectNode source, String key, Boolean missingDefault) {
        JsonNode value = source.get(key); if (value == null) { return missingDefault == null ? Field.missing() : Field.of(missingDefault); }
        return value.isNull() ? Field.nullValue() : Field.of(bool(value));
    }
    private static Field<String> fieldText(ObjectNode source, String key) { JsonNode value = source.get(key); return value == null ? Field.missing() : value.isNull() ? Field.nullValue() : Field.of(textAllowEmpty(value)); }
    private static BigInteger nullableInteger(JsonNode node) { if (node == null || node.isNull()) { return null; } require(node.isIntegralNumber(), "integer token required"); return node.bigIntegerValue(); }
    private static String nullableText(JsonNode node) { return node == null || node.isNull() ? null : textAllowEmpty(node); }
    private static String text(JsonNode node) { String value = textAllowEmpty(node); require(!value.isEmpty(), "nonempty text required"); return value; }
    private static String textAllowEmpty(JsonNode node) { require(node != null && node.isTextual(), "string token required"); String value = node.textValue(); if (!value.isEmpty()) { StrictJson.text(value); } return value; }
    private static boolean textEquals(JsonNode node, String expected) { return node != null && node.isTextual() && node.textValue().equals(expected); }
    private static boolean bool(JsonNode node) { require(node != null && node.isBoolean(), "boolean token required"); return node.booleanValue(); }
    private static ObjectNode object(JsonNode node) { require(node instanceof ObjectNode, "JSON object required"); return (ObjectNode) node; }
    private static JsonNode nodeOrNull(JsonNode node) { return node == null ? StrictJson.object().nullNode() : node; }
    private static byte[] encodeJson(JsonNode node) {
        try { byte[] raw = ENCODER.writeValueAsBytes(node); require(raw.length <= 65536, "consumer output exceeds finite allowance"); return raw; }
        catch (IOException error) { throw new IllegalArgumentException("consumer JSON encoding failed", error); }
    }
    private static void require(boolean condition, String message) { if (!condition) { throw new IllegalArgumentException(message); } }
}
