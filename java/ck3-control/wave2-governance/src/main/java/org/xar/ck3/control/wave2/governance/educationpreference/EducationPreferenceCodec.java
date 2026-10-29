package org.xar.ck3.control.wave2.governance.educationpreference;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsModel.FocusManagement;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsModel.FocusState;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceModel.*;

/** Declared legacy projection + strict v1 wrapper; source query qualification remains with its owner. */
public final class EducationPreferenceCodec {
    public static final String INPUT_SCHEMA = "xar.java.education-request-preference-input.v1";
    private static final Set<String> PROFILE_REQUIRED = Set.of("schema", "role_source", "child_character_id", "character_id",
            "owning_native_revision", "binding_status", "unavailable_reason", "skills");
    private static final Set<String> PROFILE_OPTIONAL = Set.of("education_traits", "education_culture_parameters", "total_martial_callback_v1");
    private static final Set<String> VALUE_KEYS = Set.of("available", "value", "unavailable_reason");
    private EducationPreferenceCodec() { }

    /** Shared intrinsic profile decoder; complete ordinary-context source/role binding remains separate. */
    public static GuardianProfile decodeGuardianProfile(byte[] raw) {
        return profile(StrictJson.parse(raw));
    }

    public static PreservedJson focusFrameProjection(byte[] raw) {
        JsonNode frame = object(StrictJson.parse(raw)); validateFocusFrame(frame); return preserve(frame);
    }

    public static PreservedJson guardianFrameProjection(byte[] raw) {
        JsonNode frame = object(StrictJson.parse(raw)); validateQueryFrame(frame); return preserve(frame);
    }

    public static Input decode(byte[] raw) {
        return projectParsedInput(StrictJson.parse(raw));
    }

    /** Internal field parser. Public consumers enter through the bounded raw codec or typed records. */
    static Input projectParsedInput(JsonNode parsed) {
        JsonNode root = StrictJson.object(parsed, Set.of("schema", "observations"));
        StrictJson.require(text(root, "schema").equals(INPUT_SCHEMA), "education preference input schema");
        JsonNode observations = array(root.get("observations"));
        List<Observation> result = new ArrayList<>();
        for (JsonNode observation : observations) {
            object(observation);
            JsonNode intent = observation.get("default_request_intent");
            if (intent == null || intent.isNull()) { result.add(new Skipped()); continue; }
            object(intent); Pair pair = new Pair(id(intent, "child_full_id"), id(intent, "guardian_full_id"));
            JsonNode needs = object(observation.get("needs"));
            List<Integer> occurrences = new ArrayList<>();
            for (JsonNode index : array(needs.get("occurrence_indices"))) {
                occurrences.add(Math.toIntExact(StrictJson.integer(index, 0, Integer.MAX_VALUE)));
            }
            JsonNode focusNode = StrictJson.object(needs.get("focus_management"), Set.of("available", "state", "current_key",
                    "focus_absent", "education_focus_present", "unavailable_reason"));
            FocusManagement focus = new FocusManagement(bool(focusNode, "available"), focusState(text(focusNode, "state")),
                    nullableText(focusNode, "current_key"), nullableBool(focusNode, "focus_absent"),
                    nullableBool(focusNode, "education_focus_present"), nullableText(focusNode, "unavailable_reason"));
            JsonNode focusFrame = object(needs.get("frame")); validateFocusFrame(focusFrame);
            JsonNode queryFrame = object(object(observation.get("candidate")).get("frame")); validateQueryFrame(queryFrame);
            JsonNode context = object(object(observation.get("default_query")).get("character_interaction_ordinary_context"));
            BigInteger revision = uint64(context, "snapshot_revision");
            StrictJson.require(uint64(queryFrame, "snapshot_revision").equals(revision), "candidate frame differs from its ordinary query revision");
            JsonNode rawProfile = context.get("request_guardian_skill_inputs_v1");
            Optional<GuardianProfile> profile = rawProfile == null || rawProfile.isNull() ? Optional.empty() : Optional.of(profile(rawProfile));
            result.add(new RequestObservation(pair, occurrences, focus, preserve(focusFrame), preserve(queryFrame), revision, profile));
        }
        return new Input(result);
    }

    public static byte[] encodeInput(Input input) {
        ObjectNode root = StrictJson.object(); root.put("schema", INPUT_SCHEMA); ArrayNode observations = root.putArray("observations");
        for (Observation observation : input.observations()) {
            ObjectNode row = observations.addObject();
            if (observation instanceof Skipped) { row.putNull("default_request_intent"); continue; }
            RequestObservation request = (RequestObservation) observation;
            ObjectNode intent = row.putObject("default_request_intent"); intent.put("child_full_id", request.intent().childFullId());
            intent.put("guardian_full_id", request.intent().guardianFullId());
            ObjectNode needs = row.putObject("needs"); ArrayNode indices = needs.putArray("occurrence_indices"); request.occurrenceIndices().forEach(indices::add);
            needs.set("focus_management", focus(request.focusManagement())); needs.set("frame", restored(request.focusSourceFrame()));
            row.putObject("candidate").set("frame", restored(request.guardianQueryFrame()));
            ObjectNode context = row.putObject("default_query").putObject("character_interaction_ordinary_context");
            context.put("snapshot_revision", request.queryNativeRevision());
            context.set("request_guardian_skill_inputs_v1", request.profile().map(value -> restored(value.original())).orElseGet(() -> StrictJson.object().nullNode()));
        }
        return StrictJson.canonical(root);
    }

    public static byte[] encodeResult(Result result) {
        return StrictJson.canonical(resultNode(result));
    }

    static ObjectNode resultNode(Result result) {
        ObjectNode root = StrictJson.object(); root.put("schema", "family_education_request_preference_12004");
        root.put("policy", EducationRequestPreference.POLICY); root.put("qualification", "explicit_source_informed_request_preference");
        root.put("comparison", "descending known weighted numerator within identical availability and operand sources; other source/availability slots keep original occurrence order");
        root.put("tie", "original occurrence, full child ID, full guardian ID, original observation index");
        ArrayNode candidates = root.putArray("candidates");
        for (CandidateRecord record : result.candidates()) {
            ObjectNode item = candidates.addObject(); item.put("observation_index", record.observationIndex());
            item.put("child_full_id", record.pair().childFullId()); item.put("guardian_full_id", record.pair().guardianFullId());
            item.put("first_occurrence_index", record.firstOccurrenceIndex()); item.put("request_profile_identity_bound", record.requestProfileIdentityBound());
            item.put("focus_key", record.focusManagement().currentKey()); item.set("focus_management", focus(record.focusManagement()));
            item.set("focus_source_frame", restored(record.focusSourceFrame())); item.set("guardian_query_frame", restored(record.guardianQueryFrame()));
            item.set("raw_request_guardian_profile", record.rawProfile().map(value -> restored(value.original())).orElseGet(() -> StrictJson.object().nullNode()));
            ObjectNode components = item.putObject("components"); components.set("focus", component(record.focus())); components.set("learning", component(record.learning()));
            item.set("known_weighted_score", score(record.knownWeightedScore())); item.set("complete_weighted_score", score(record.completeWeightedScore()));
            ObjectNode availability = item.putObject("availability"); availability.put("focus", record.focus().available()); availability.put("learning", record.learning().available());
        }
        ArrayNode ordered = root.putArray("ordered_observation_indices"); result.orderedObservationIndices().forEach(ordered::add);
        root.put("unknown_operands_substituted", false); root.put("native_ai_replay", false);
        root.put("effect_educator_selection_observed", false); root.put("education_outcome_predicted", false);
        return root;
    }

    private static GuardianProfile profile(JsonNode raw) {
        object(raw); Set<String> keys = new HashSet<>(); raw.fieldNames().forEachRemaining(keys::add);
        StrictJson.require(keys.containsAll(PROFILE_REQUIRED), "guardian profile required fields");
        keys.removeAll(PROFILE_REQUIRED); StrictJson.require(PROFILE_OPTIONAL.containsAll(keys), "guardian profile unknown fields");
        StrictJson.require(text(raw, "schema").equals("request_guardian_skill_inputs_v1"), "guardian profile schema");
        StrictJson.require(text(raw, "role_source").equals("request_guardian_secondary_actor"), "guardian profile role source");
        Long child = nullableId(raw, "child_character_id"), guardian = nullableId(raw, "character_id");
        BigInteger revision = uint64(raw, "owning_native_revision"); BindingStatus binding = BindingStatus.fromWire(text(raw, "binding_status"));
        String unavailable = nullableText(raw, "unavailable_reason");
        if (binding == BindingStatus.RESOLVED) {
            StrictJson.require(child != null && child != 0 && guardian != null && guardian != 0 && unavailable == null, "resolved guardian IDs/reason");
        } else if (binding == BindingStatus.KNOWN_NULL) {
            StrictJson.require(guardian == null && "request_guardian_role_known_null".equals(unavailable), "known-null guardian binding");
        } else { StrictJson.require(EducationPreferenceModel.reason(unavailable), "unavailable guardian binding reason"); }
        JsonNode skillNode = StrictJson.object(raw.get("skills"), Set.of("diplomacy", "martial", "stewardship", "intrigue", "learning"));
        EnumMap<Skill, SkillObservation> skills = new EnumMap<>(Skill.class);
        for (Skill skill : Skill.values()) { skills.put(skill, skill(skillNode.get(skill.wire()), binding)); }
        Optional<TotalMartial> total = Optional.empty();
        if (raw.has("total_martial_callback_v1")) {
            JsonNode callback = StrictJson.object(raw.get("total_martial_callback_v1"), Set.of("source", "target_character_id", "available", "value", "unavailable_reason"));
            StrictJson.require(text(callback, "source").equals(SourceBasis.TOTAL_MARTIAL.wire()), "native total-martial source");
            Long target = nullableId(callback, "target_character_id"); StrictJson.require(java.util.Objects.equals(target, guardian), "total-martial target/profile mismatch");
            total = Optional.of(new TotalMartial(target, skillFields(callback, binding)));
        }
        if (raw.has("education_traits")) {
            JsonNode traits = StrictJson.object(raw.get("education_traits"), Set.of("intellect_good_3", "intellect_good_2", "intellect_good_1", "shrewd"));
            for (JsonNode field : traits) { validateBooleanValue(field, binding); }
        }
        if (raw.has("education_culture_parameters")) { validateCulture(raw.get("education_culture_parameters"), binding); }
        return new GuardianProfile(child, guardian, revision, binding, skills, total, preserve(raw));
    }

    private static SkillObservation skill(JsonNode node, BindingStatus binding) { StrictJson.object(node, VALUE_KEYS); return skillFields(node, binding); }
    private static SkillObservation skillFields(JsonNode node, BindingStatus binding) {
        boolean available = bool(node, "available"); JsonNode value = required(node, "value"); String reason = nullableText(node, "unavailable_reason");
        Integer number = value.isNull() ? null : Math.toIntExact(StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE));
        StrictJson.require(!available || binding == BindingStatus.RESOLVED, "available skill requires resolved profile");
        return new SkillObservation(available, number, reason);
    }
    private static void validateBooleanValue(JsonNode field, BindingStatus binding) {
        StrictJson.object(field, VALUE_KEYS); boolean available = bool(field, "available"); JsonNode value = required(field, "value"); String reason = nullableText(field, "unavailable_reason");
        StrictJson.require(available ? binding == BindingStatus.RESOLVED && value.isBoolean() && reason == null
                : value.isNull() && EducationPreferenceModel.reason(reason), "education trait Boolean availability");
    }
    private static void validateCulture(JsonNode node, BindingStatus binding) {
        StrictJson.object(node, Set.of("culture_full_id", "available", "better_ward_education", "unavailable_reason"));
        JsonNode id = required(node, "culture_full_id"); Long culture = id.isNull() ? null : StrictJson.integer(id, 0, 4_294_967_295L);
        boolean available = bool(node, "available"); JsonNode value = required(node, "better_ward_education"); String reason = nullableText(node, "unavailable_reason");
        StrictJson.require(available ? binding == BindingStatus.RESOLVED && culture != null && culture != 4_294_967_295L && value.isBoolean() && reason == null
                : value.isNull() && EducationPreferenceModel.reason(reason), "education Culture Boolean availability");
    }
    private static void validateFocusFrame(JsonNode frame) {
        StrictJson.object(frame, Set.of("native_revision", "played_character_id", "heir_character_id", "date_raw"));
        StrictJson.integer(required(frame, "native_revision"), BigInteger.ONE, StrictJson.UINT64_MAX);
        for (String field : List.of("played_character_id", "heir_character_id")) {
            JsonNode id = required(frame, field); if (!id.isNull()) { StrictJson.integer(id, 1, Integer.MAX_VALUE); }
        }
        JsonNode date = required(frame, "date_raw"); if (!date.isNull()) { StrictJson.integer(date, Long.MIN_VALUE, Long.MAX_VALUE); }
    }
    private static void validateQueryFrame(JsonNode frame) {
        StrictJson.object(frame, Set.of("snapshot_revision", "date_raw", "player_character_id", "game_pid", "connection_generation"));
        StrictJson.integer(required(frame, "snapshot_revision"), BigInteger.ONE, StrictJson.UINT64_MAX);
        StrictJson.integer(required(frame, "date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE);
        StrictJson.integer(required(frame, "player_character_id"), 1, Integer.MAX_VALUE);
        StrictJson.integer(required(frame, "game_pid"), 1, 4_294_967_295L);
        StrictJson.integer(required(frame, "connection_generation"), BigInteger.ONE, StrictJson.UINT64_MAX);
    }
    private static ObjectNode focus(FocusManagement focus) {
        ObjectNode node = StrictJson.object(); node.put("available", focus.available()); node.put("state", focus.state().wire()); node.put("current_key", focus.currentKey());
        if (focus.focusAbsent() == null) { node.putNull("focus_absent"); } else { node.put("focus_absent", focus.focusAbsent()); }
        if (focus.educationFocusPresent() == null) { node.putNull("education_focus_present"); } else { node.put("education_focus_present", focus.educationFocusPresent()); }
        node.put("unavailable_reason", focus.unavailableReason()); return node;
    }
    private static ObjectNode component(Component component) {
        ObjectNode node = StrictJson.object(); node.put("available", component.available()); node.put("raw_value", component.rawValue());
        node.put("source_basis", component.sourceBasis().wire()); ObjectNode weight = node.putObject("weight"); weight.put("numerator", component.weightNumerator()); weight.put("denominator", 5);
        node.put("weighted_numerator", component.weightedNumerator()); node.put("unavailable_reason", component.unavailableReason()); return node;
    }
    private static JsonNode score(Optional<Score> score) {
        if (score.isEmpty()) { return StrictJson.object().nullNode(); }
        ObjectNode node = StrictJson.object(); node.put("numerator", score.get().numerator()); node.put("denominator", 5); return node;
    }
    private static PreservedJson preserve(JsonNode value) { return new PreservedJson(new String(StrictJson.canonical(value), StandardCharsets.UTF_8)); }
    private static JsonNode restored(PreservedJson value) { return StrictJson.parse(value.canonicalJson().getBytes(StandardCharsets.UTF_8)); }
    private static JsonNode required(JsonNode parent, String key) { JsonNode value = parent.get(key); StrictJson.require(value != null, "required field: " + key); return value; }
    private static JsonNode object(JsonNode value) { StrictJson.require(value != null && value.isObject(), "required legacy projection object"); return value; }
    private static JsonNode array(JsonNode value) { StrictJson.require(value != null && value.isArray(), "required observation/occurrence array"); return value; }
    private static String text(JsonNode node, String key) { return StrictJson.text(required(node, key)); }
    private static String nullableText(JsonNode node, String key) { JsonNode value = required(node, key); return value.isNull() ? null : StrictJson.text(value); }
    private static boolean bool(JsonNode node, String key) { JsonNode value = required(node, key); StrictJson.require(value.isBoolean(), "exact Boolean required: " + key); return value.booleanValue(); }
    private static Boolean nullableBool(JsonNode node, String key) { return required(node, key).isNull() ? null : bool(node, key); }
    private static long id(JsonNode node, String key) { return StrictJson.integer(required(node, key), 0, 4_294_967_294L); }
    private static Long nullableId(JsonNode node, String key) { return required(node, key).isNull() ? null : id(node, key); }
    private static BigInteger uint64(JsonNode node, String key) { return StrictJson.integer(required(node, key), BigInteger.ZERO, StrictJson.UINT64_MAX); }
    private static FocusState focusState(String wire) {
        for (FocusState state : FocusState.values()) { if (state.wire().equals(wire)) { return state; } }
        throw new IllegalArgumentException("unknown focus-management state");
    }
}
