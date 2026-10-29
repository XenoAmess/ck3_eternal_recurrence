package org.xar.ck3.control.governance.lifestyle;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy.*;
import org.xar.ck3.control.governance.lifestyleperks.LifestylePerksCodec;
import org.xar.ck3.control.governance.lifestyleperks.LifestylePerksModel;

/** Strict small projection boundary; full native readbacks are projected by their qualified producer. */
public final class LifestyleMinCodec {
    public static final String SCHEMA = "lifestyle-min-request-v1";
    public static final String FIRST_FOCUS_SCHEMA = "lifestyle-first-focus-request-v1";
    public static final String ROUTED_SCHEMA = "lifestyle-min-routed-request-v1";
    public enum ProgressRoute { LIFE2, ALL_LIFESTYLE_V3 }
    public record RoutedRequest(Request minimum, ProgressRoute route, Field<LifestylePerksModel.Input> allLifestyle) {
        public RoutedRequest { java.util.Objects.requireNonNull(minimum); java.util.Objects.requireNonNull(route); java.util.Objects.requireNonNull(allLifestyle);
            StrictJson.require((route == ProgressRoute.LIFE2) == (allLifestyle.state() == FieldState.MISSING), "explicit progress route and V3 evidence mismatch"); }
    }
    private static final Set<String> REQUEST_FIELDS = Set.of("schema", "snapshot", "feudal_scope_admitted", "at_peace",
            "collect_taxes_active", "allow_wartime_perk", "allow_wartime_initial_focus", "preferred_focus_target_key",
            "pending_action", "focus_scope_admitted");
    private static final Set<String> SNAPSHOT_FIELDS = Set.of("status", "snapshot_id", "episode_run_id", "public_revision",
            "native_revision", "proof_epoch", "date_raw", "player_character_id", "current_focus", "current_lifestyle_progress",
            "target_lifestyle_progress", "owned_perk_keys", "legal_perk_candidates", "legal_focus_candidates", "readiness");
    private static final Set<String> PROGRESS_FIELDS = Set.of("presence", "lifestyle_key", "unspent_perk_points");
    private static final Set<String> READINESS_FIELDS = Set.of("current_focus_ready", "lifestyle_progress_ready", "owned_perks_ready",
            "same_frame_ready", "legal_perk_candidates_ready", "legal_focus_candidates_ready");
    private LifestyleMinCodec() { }

    public static Request decode(byte[] input) { return request(StrictJson.parse(input)); }
    public static FirstFocusRequest decodeFirstFocus(byte[] input) { return firstFocus(StrictJson.parse(input)); }
    public static byte[] encode(Request input) { return StrictJson.canonical(requestNode(input)); }
    public static byte[] encode(FirstFocusRequest input) { return StrictJson.canonical(firstFocusRequestNode(input)); }
    public static byte[] encode(Decision decision) { return StrictJson.canonical(decisionNode(decision)); }
    public static byte[] encode(FirstFocusDecision decision) { return StrictJson.canonical(firstFocusDecisionNode(decision)); }
    public static byte[] encode(RoutedDecision decision) {
        if (decision instanceof MinimumDecision minimum) { return encode(minimum.decision()); }
        AllLifestyleDecision all = (AllLifestyleDecision) decision;
        ObjectNode result = LifestylePerksCodec.decisionNode(all.decision());
        result.put("policy_id", all.policyId());
        if (!result.has("selected_action")) { result.putNull("selected_action"); }
        return StrictJson.canonical(result);
    }
    public static byte[] evaluate(byte[] input) { return encode(LifestyleMinPolicy.choose(decode(input))); }
    public static byte[] evaluateFirstFocus(byte[] input) { return encode(LifestyleMinPolicy.chooseFirstFocus(decodeFirstFocus(input))); }
    public static RoutedRequest decodeRouted(byte[] input) {
        ObjectNode root = StrictJson.object(StrictJson.parse(input), Set.of("schema", "minimum", "progress_route", "all_lifestyle"));
        StrictJson.require(ROUTED_SCHEMA.equals(string(root.get("schema"))), "wrong routed request schema");
        ProgressRoute route = switch (string(root.get("progress_route"))) {
            case "life2" -> ProgressRoute.LIFE2;
            case "all_lifestyle_v3" -> ProgressRoute.ALL_LIFESTYLE_V3;
            default -> throw new org.xar.ck3.control.contracts.ContractViolationException("unknown progress route");
        };
        JsonNode evidence = root.get("all_lifestyle");
        Field<LifestylePerksModel.Input> all;
        if (route == ProgressRoute.LIFE2) {
            StrictJson.require(evidence.isNull(), "LIFE2 route must explicitly carry null V3 evidence"); all = Field.missing();
        } else { all = evidence.isNull() ? Field.nullValue() : Field.of(LifestylePerksCodec.decode(StrictJson.canonical(evidence))); }
        return new RoutedRequest(request(root.get("minimum")), route, all);
    }
    public static byte[] evaluateRouted(byte[] input) {
        RoutedRequest request = decodeRouted(input);
        return encode(LifestyleMinPolicy.chooseRouted(request.minimum(), request.allLifestyle()));
    }

    public static Request request(JsonNode value) {
        ObjectNode row = StrictJson.object(value, REQUEST_FIELDS);
        StrictJson.require(SCHEMA.equals(string(row.get("schema"))), "wrong minimum request schema");
        Field<PendingAction> pending = field(row, "pending_action", entry -> {
            ObjectNode action = allowed(entry, Set.of("status"));
            // A pending mapping without a status is UNKNOWN, never permission to resubmit.
            return new PendingAction(field(action, "status", LifestyleMinCodec::string));
        });
        return new Request(field(row, "snapshot", LifestyleMinCodec::snapshot), field(row, "feudal_scope_admitted", LifestyleMinCodec::bool),
                field(row, "at_peace", LifestyleMinCodec::bool), field(row, "collect_taxes_active", LifestyleMinCodec::bool),
                bool(row.get("allow_wartime_perk")), bool(row.get("allow_wartime_initial_focus")),
                string(row.get("preferred_focus_target_key")), pending, field(row, "focus_scope_admitted", LifestyleMinCodec::bool));
    }
    public static FirstFocusRequest firstFocus(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("schema", "wealth", "martial", "actor_traits", "at_peace"));
        StrictJson.require(FIRST_FOCUS_SCHEMA.equals(string(row.get("schema"))), "wrong first-focus request schema");
        return new FirstFocusRequest(field(row, "wealth", LifestyleMinCodec::focusObservation),
                field(row, "martial", LifestyleMinCodec::focusObservation), field(row, "actor_traits", entry -> {
                    ObjectNode traits = allowed(entry, Set.of("status", "observed_keys"));
                    return new Traits(field(traits, "status", LifestyleMinCodec::string), field(traits, "observed_keys", LifestyleMinCodec::strings));
                }), bool(row.get("at_peace")));
    }
    private static Snapshot snapshot(JsonNode value) {
        ObjectNode row = allowed(value, SNAPSHOT_FIELDS);
        return new Snapshot(field(row, "status", LifestyleMinCodec::string), field(row, "snapshot_id", LifestyleMinCodec::string),
                field(row, "episode_run_id", LifestyleMinCodec::string), field(row, "public_revision", LifestyleMinCodec::integer),
                field(row, "native_revision", LifestyleMinCodec::integer), field(row, "proof_epoch", LifestyleMinCodec::integer),
                field(row, "date_raw", LifestyleMinCodec::integer), field(row, "player_character_id", LifestyleMinCodec::integer),
                field(row, "current_focus", entry -> { ObjectNode focus = allowed(entry, Set.of("presence", "key", "lifestyle_key"));
                    return new Focus(field(focus, "presence", LifestyleMinCodec::string), field(focus, "key", LifestyleMinCodec::string),
                            field(focus, "lifestyle_key", LifestyleMinCodec::string)); }),
                field(row, "current_lifestyle_progress", LifestyleMinCodec::progress),
                field(row, "target_lifestyle_progress", LifestyleMinCodec::progress), field(row, "owned_perk_keys", LifestyleMinCodec::strings),
                field(row, "legal_perk_candidates", LifestyleMinCodec::candidates), field(row, "legal_focus_candidates", LifestyleMinCodec::candidates),
                field(row, "readiness", entry -> { ObjectNode ready = allowed(entry, READINESS_FIELDS);
                    return new Readiness(field(ready, "current_focus_ready", LifestyleMinCodec::bool),
                            field(ready, "lifestyle_progress_ready", LifestyleMinCodec::bool), field(ready, "owned_perks_ready", LifestyleMinCodec::bool),
                            field(ready, "same_frame_ready", LifestyleMinCodec::bool), field(ready, "legal_perk_candidates_ready", LifestyleMinCodec::bool),
                            field(ready, "legal_focus_candidates_ready", LifestyleMinCodec::bool)); }));
    }
    private static Progress progress(JsonNode value) {
        ObjectNode row = allowed(value, PROGRESS_FIELDS);
        return new Progress(field(row, "presence", LifestyleMinCodec::string), field(row, "lifestyle_key", LifestyleMinCodec::string),
                field(row, "unspent_perk_points", LifestyleMinCodec::integer));
    }
    private static Candidates candidates(JsonNode value) {
        ObjectNode row = allowed(value, Set.of("status", "items"));
        return new Candidates(field(row, "status", LifestyleMinCodec::string), field(row, "items", entries -> {
            StrictJson.require(entries.isArray() && entries.size() <= 256, "bounded candidate array required");
            List<Candidate> candidates = new ArrayList<>();
            for (JsonNode entry : entries) {
                ObjectNode candidate = StrictJson.object(entry, Set.of("key", "lifestyle_key"));
                candidates.add(new Candidate(string(candidate.get("key")), string(candidate.get("lifestyle_key"))));
            }
            return List.copyOf(candidates);
        }));
    }
    private static FocusObservation focusObservation(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("status", "native_legal", "target_key", "target_lifestyle_key", "target_lifestyle_progress"));
        JsonNode rawProgress = row.get("target_lifestyle_progress");
        ObjectNode progress = allowed(rawProgress, Set.of("presence", "xp_total_raw", "xp_within_level_raw", "xp_per_level", "unspent_perk_points", "used_perk_points"));
        boolean complete = List.of("xp_total_raw", "xp_within_level_raw", "xp_per_level", "unspent_perk_points", "used_perk_points")
                .stream().allMatch(key -> progress.hasNonNull(key));
        StrictJson.object(progress, complete ? Set.of("presence", "xp_total_raw", "xp_within_level_raw", "xp_per_level", "unspent_perk_points", "used_perk_points")
                : Set.of("presence"));
        Field<FocusProgress> observed = complete ? Field.of(new FocusProgress(integer(progress.get("xp_total_raw")), integer(progress.get("xp_within_level_raw")),
                integer(progress.get("xp_per_level")), integer(progress.get("unspent_perk_points")), integer(progress.get("used_perk_points")))) : Field.missing();
        return new FocusObservation(string(row.get("status")), field(row, "native_legal", LifestyleMinCodec::bool),
                string(row.get("target_key")), string(row.get("target_lifestyle_key")),
                string(progress.get("presence")), observed);
    }
    private static <T> Field<T> field(ObjectNode object, String key, Function<JsonNode, T> parse) {
        JsonNode node = object.get(key);
        return node == null ? Field.missing() : node.isNull() ? Field.nullValue() : Field.of(parse.apply(node));
    }
    private static ObjectNode allowed(JsonNode node, Set<String> fields) {
        StrictJson.require(node instanceof ObjectNode, "JSON object required");
        ObjectNode object = (ObjectNode) node;
        object.fieldNames().forEachRemaining(key -> StrictJson.require(fields.contains(key), "unknown field: " + key));
        return object;
    }
    private static String string(JsonNode node) {
        StrictJson.require(node != null && node.isTextual(), "actual JSON string required");
        String value = node.textValue();
        if (!value.isEmpty()) { StrictJson.text(value); }
        return value;
    }
    private static BigInteger integer(JsonNode node) {
        StrictJson.require(node != null && node.isIntegralNumber(), "actual JSON integer required, no bool/float/string coercion");
        // This is an opaque Python-only policy integer, not a JavaScript numeric API.
        // Preserve its exact integer domain; the shared parser bounds the whole input.
        return node.bigIntegerValue();
    }
    private static boolean bool(JsonNode node) { StrictJson.require(node != null && node.isBoolean(), "actual JSON boolean required"); return node.booleanValue(); }
    private static List<String> strings(JsonNode node) {
        StrictJson.require(node != null && node.isArray() && node.size() <= 512, "bounded string array required");
        List<String> values = new ArrayList<>();
        for (JsonNode entry : node) { values.add(string(entry)); }
        return List.copyOf(values);
    }

    public static ObjectNode requestNode(Request value) {
        ObjectNode result = StrictJson.object().put("schema", SCHEMA);
        put(result, "snapshot", value.snapshot(), LifestyleMinCodec::snapshotNode);
        put(result, "feudal_scope_admitted", value.feudalScopeAdmitted(), LifestyleMinCodec::booleanNode);
        put(result, "at_peace", value.atPeace(), LifestyleMinCodec::booleanNode);
        put(result, "collect_taxes_active", value.collectTaxesActive(), LifestyleMinCodec::booleanNode);
        result.put("allow_wartime_perk", value.allowWartimePerk()).put("allow_wartime_initial_focus", value.allowWartimeInitialFocus())
                .put("preferred_focus_target_key", value.preferredFocusTargetKey());
        put(result, "pending_action", value.pendingAction(), action -> { ObjectNode pending = StrictJson.object();
            put(pending, "status", action.status(), LifestyleMinCodec::textNode); return pending; });
        put(result, "focus_scope_admitted", value.focusScopeAdmitted(), LifestyleMinCodec::booleanNode);
        return result;
    }
    private static ObjectNode snapshotNode(Snapshot value) {
        ObjectNode result = StrictJson.object();
        put(result, "status", value.status(), LifestyleMinCodec::textNode); put(result, "snapshot_id", value.snapshotId(), LifestyleMinCodec::textNode);
        put(result, "episode_run_id", value.episodeRunId(), LifestyleMinCodec::textNode); put(result, "public_revision", value.publicRevision(), LifestyleMinCodec::integerNode);
        put(result, "native_revision", value.nativeRevision(), LifestyleMinCodec::integerNode); put(result, "proof_epoch", value.proofEpoch(), LifestyleMinCodec::integerNode);
        put(result, "date_raw", value.dateRaw(), LifestyleMinCodec::integerNode); put(result, "player_character_id", value.playerCharacterId(), LifestyleMinCodec::integerNode);
        put(result, "current_focus", value.currentFocus(), focus -> { ObjectNode row = StrictJson.object();
            put(row, "presence", focus.presence(), LifestyleMinCodec::textNode); put(row, "key", focus.key(), LifestyleMinCodec::textNode);
            put(row, "lifestyle_key", focus.lifestyleKey(), LifestyleMinCodec::textNode); return row; });
        put(result, "current_lifestyle_progress", value.currentProgress(), LifestyleMinCodec::progressNode);
        put(result, "target_lifestyle_progress", value.targetProgress(), LifestyleMinCodec::progressNode);
        put(result, "owned_perk_keys", value.ownedPerks(), LifestyleMinCodec::stringsNode);
        put(result, "legal_perk_candidates", value.legalPerks(), LifestyleMinCodec::candidatesNode);
        put(result, "legal_focus_candidates", value.legalFocus(), LifestyleMinCodec::candidatesNode);
        put(result, "readiness", value.readiness(), ready -> { ObjectNode row = StrictJson.object();
            put(row, "current_focus_ready", ready.currentFocus(), LifestyleMinCodec::booleanNode);
            put(row, "lifestyle_progress_ready", ready.lifestyleProgress(), LifestyleMinCodec::booleanNode);
            put(row, "owned_perks_ready", ready.ownedPerks(), LifestyleMinCodec::booleanNode);
            put(row, "same_frame_ready", ready.sameFrame(), LifestyleMinCodec::booleanNode);
            put(row, "legal_perk_candidates_ready", ready.legalPerks(), LifestyleMinCodec::booleanNode);
            put(row, "legal_focus_candidates_ready", ready.legalFocus(), LifestyleMinCodec::booleanNode); return row; });
        return result;
    }
    private static ObjectNode progressNode(Progress progress) {
        ObjectNode row = StrictJson.object(); put(row, "presence", progress.presence(), LifestyleMinCodec::textNode);
        put(row, "lifestyle_key", progress.lifestyleKey(), LifestyleMinCodec::textNode);
        put(row, "unspent_perk_points", progress.unspentPoints(), LifestyleMinCodec::integerNode); return row;
    }
    private static ObjectNode candidatesNode(Candidates candidates) {
        ObjectNode row = StrictJson.object(); put(row, "status", candidates.status(), LifestyleMinCodec::textNode);
        put(row, "items", candidates.items(), values -> { ArrayNode array = row.arrayNode();
            for (Candidate value : values) { array.add(StrictJson.object().put("key", value.key()).put("lifestyle_key", value.lifestyleKey())); }
            return array; }); return row;
    }
    public static ObjectNode decisionNode(Decision decision) {
        ObjectNode row = StrictJson.object().put("policy_id", decision.policyId()).put("status", decision.status().wire());
        if (decision.selectedAction() == null) { row.putNull("selected_action"); }
        else { row.set("selected_action", actionNode(decision.selectedAction())); }
        if (decision.reason() != null) { row.put("reason", decision.reason()); }
        if (decision.unspentPoints() != null) { row.put("unspent_perk_points", decision.unspentPoints()); }
        return row;
    }
    public static ObjectNode bindingNode(Binding b) {
        return StrictJson.object().put("expected_snapshot_id", b.snapshotId()).put("expected_episode_run_id", b.episodeRunId())
                .put("expected_public_revision", b.publicRevision()).put("expected_native_revision", b.nativeRevision())
                .put("expected_proof_epoch", b.proofEpoch()).put("expected_date_raw", b.dateRaw()).put("expected_player_character_id", b.playerCharacterId());
    }
    public static ObjectNode actionNode(Action action) {
        ObjectNode row = StrictJson.object().put("kind", action.kind() == Kind.FOCUS ? "focus" : "perk")
                .put("target_key", action.targetKey()).put("target_lifestyle_key", action.targetLifestyleKey()).put("reason", action.reason());
        row.set("expected", bindingNode(action.expected())); return row;
    }
    public static ObjectNode firstFocusDecisionNode(FirstFocusDecision decision) {
        ObjectNode row = StrictJson.object().put("status", decision.selected() ? "selected" : "no_final_legal_focus_or_source_unavailable")
                .put("martial_education_rank", decision.martialEducationRank()).put("at_peace", decision.atPeace());
        if (decision.selected()) { row.put("target_key", decision.targetKey()).put("reason", decision.reason()).put("commitment_months", 60); }
        else { row.putNull("target_key"); }
        ObjectNode observed = StrictJson.object(); observed.set("wealth", observedNode(decision.wealth())); observed.set("martial", observedNode(decision.martial()));
        row.set("observed_target_progress", observed); return row;
    }
    public static ObjectNode firstFocusRequestNode(FirstFocusRequest request) {
        ObjectNode row = StrictJson.object().put("schema", FIRST_FOCUS_SCHEMA).put("at_peace", request.atPeace());
        put(row, "wealth", request.wealth(), LifestyleMinCodec::focusObservationNode);
        put(row, "martial", request.martial(), LifestyleMinCodec::focusObservationNode);
        put(row, "actor_traits", request.actorTraits(), traits -> { ObjectNode node = StrictJson.object();
            put(node, "status", traits.status(), LifestyleMinCodec::textNode);
            put(node, "observed_keys", traits.observedKeys(), LifestyleMinCodec::stringsNode); return node; });
        return row;
    }
    private static ObjectNode focusObservationNode(FocusObservation observation) {
        ObjectNode row = StrictJson.object().put("status", observation.status()).put("target_key", observation.targetKey())
                .put("target_lifestyle_key", observation.targetLifestyleKey());
        put(row, "native_legal", observation.nativeLegal(), LifestyleMinCodec::booleanNode);
        ObjectNode progress = StrictJson.object().put("presence", observation.progressPresence());
        if (observation.progress().present()) {
            FocusProgress value = observation.progress().value();
            progress.put("xp_total_raw", value.xpTotalRaw()).put("xp_within_level_raw", value.xpWithinLevelRaw())
                    .put("xp_per_level", value.xpPerLevel()).put("unspent_perk_points", value.unspentPoints()).put("used_perk_points", value.usedPoints());
        }
        row.set("target_lifestyle_progress", progress); return row;
    }
    private static JsonNode observedNode(ObservedTarget target) {
        if (target == null) { return StrictJson.object().nullNode(); }
        FocusProgress p = target.progress();
        ObjectNode row = StrictJson.object().put("native_legal", target.nativeLegal());
        row.set("progress", StrictJson.object().put("xp_total_raw", p.xpTotalRaw()).put("xp_within_level_raw", p.xpWithinLevelRaw())
                .put("xp_per_level", p.xpPerLevel()).put("unspent_perk_points", p.unspentPoints()).put("used_perk_points", p.usedPoints())); return row;
    }
    private static JsonNode textNode(String value) { return StrictJson.object().textNode(value); }
    private static JsonNode integerNode(BigInteger value) { return StrictJson.object().numberNode(value); }
    private static JsonNode booleanNode(boolean value) { return StrictJson.object().booleanNode(value); }
    private static JsonNode stringsNode(List<String> values) { ArrayNode result = StrictJson.object().arrayNode(); values.forEach(result::add); return result; }
    private static <T> void put(ObjectNode row, String key, Field<T> field, Function<T, JsonNode> encode) {
        if (field.state() == FieldState.NULL) { row.putNull(key); }
        else if (field.present()) { row.set(key, encode.apply(field.value())); }
    }
}
