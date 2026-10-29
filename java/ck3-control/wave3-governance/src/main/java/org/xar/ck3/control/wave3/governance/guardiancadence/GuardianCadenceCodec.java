package org.xar.ck3.control.wave3.governance.guardiancadence;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsCodec;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsModel.FocusState;
import org.xar.ck3.control.wave3.governance.guardiancadence.GuardianCadenceModel.*;

/** Strict transport projection of actual legacy frames/queries. No file, Game or persistence access. */
public final class GuardianCadenceCodec {
    public static final String SCHEMA = "xar.java.guardian-negative-cadence-input.v1";
    private static final String RESULT_SCHEMA = "xar.ck3.family-guardian-negative-cadence/v1";
    private GuardianCadenceCodec() { }

    public static Input decode(byte[] raw) {
        return projectParsedInput(StrictJson.parse(raw));
    }

    /** Field projection after the owning reader validated its raw input and explicit source budget. */
    static Input projectParsedInput(JsonNode parsed) {
        JsonNode input = StrictJson.object(parsed, Set.of("schema", "frame", "needs", "heir_id", "state", "default_query", "attempts", "selected_step"));
        StrictJson.require(text(input, "schema").equals(SCHEMA), "guardian cadence wrapper schema");
        Frame parsedFrame = frame(required(input, "frame"));
        List<Attempt> attempts = attempts(required(input, "attempts"));
        return new Input(parsedFrame, materials(required(input, "needs")), nullableId(input, "heir_id"), state(required(input, "state")),
                query(required(input, "default_query")), attempts, text(input, "selected_step"));
    }

    static Frame frame(JsonNode value) {
        JsonNode frame = object(value);
        return new Frame(text(frame, "status"), pid(frame, "bridge_pid"), positiveU64(frame, "connection_generation"),
                text(frame, "episode_run_id"), positiveId(frame, "actor_character_id"), exactInteger(frame, "date_raw"),
                u64(frame, "native_revision"), u64(frame, "revision"));
    }
    static List<Attempt> attempts(JsonNode value) {
        List<Attempt> attempts = new ArrayList<>();
        for (JsonNode attempt : array(value)) {
            object(attempt); attempts.add(new Attempt(text(attempt, "variant"), query(required(attempt, "query"))));
        }
        return List.copyOf(attempts);
    }

    public static byte[] encodeEvaluation(Evaluation result) {
        return StrictJson.canonical(evaluationNode(result));
    }

    static ObjectNode evaluationNode(Evaluation result) {
        ObjectNode output = StrictJson.object();
        output.set("scope", result.scope().<JsonNode>map(GuardianCadenceCodec::scope).orElseGet(() -> StrictJson.object().nullNode()));
        output.set("deferred_before", result.deferredBefore().<JsonNode>map(GuardianCadenceCodec::deferred).orElseGet(() -> StrictJson.object().nullNode()));
        output.set("observation", result.after().observation().<JsonNode>map(GuardianCadenceCodec::observation).orElseGet(() -> StrictJson.object().nullNode()));
        output.set("state", state(result.after().state())); return output;
    }
    public static byte[] encodeState(State state) { return StrictJson.canonical(state(state)); }
    public static State decodeState(byte[] raw) { return state(StrictJson.parse(raw)); }

    static Optional<ScopeMaterials> materials(JsonNode needs) {
        if (needs.isNull()) { return Optional.empty(); } object(needs);
        JsonNode values = nullableObject(needs.get("values")), focus = nullableObject(needs.get("focus_management"));
        JsonNode court = nullableObject(needs.get("current_court_owner")), provider = nullableObject(needs.get("education_provider_inputs"));
        JsonNode relation = nullableObject(needs.get("relation_materials"));
        if (values == null || focus == null || court == null || provider == null || relation == null) { return Optional.empty(); }
        Optional<ProviderObservation> providerObservation = Optional.empty(); JsonNode rawProvider = nullableObject(provider.get("observation"));
        if (rawProvider != null) { providerObservation = Optional.of(new ProviderObservation(nullableIdOrMissing(rawProvider, "guardian_full_id"), nullableTextOrMissing(rawProvider, "role_source"))); }
        Optional<NamedGuardian> named = Optional.empty(); JsonNode relationObservation = nullableObject(relation.get("observation"));
        JsonNode guardian = relationObservation == null ? null : nullableObject(relationObservation.get("guardian_named_material"));
        if (guardian != null) {
            named = Optional.of(new NamedGuardian(bool(guardian, "available"), bool(guardian, "identity_round_trip"), bool(guardian, "sample_stable"),
                    nullableId(guardian, "matched_peer_full_id")));
        }
        List<String> missing = strings(required(needs, "missing_observations"));
        JsonNode rawAge = values.get("age_measure_raw");
        if (rawAge == null || rawAge.isNull()) { return Optional.empty(); }
        return Optional.of(new ScopeMaterials(positiveId(needs, "raw_character_id"), text(values, "status"), integer(rawAge),
                nullableIntegerOrMissing(values, "sex_selector_raw"), new Focus(bool(focus, "available"), focusState(nullableTextOrMissing(focus, "state")), nullableTextOrMissing(focus, "current_key")),
                new Court(bool(court, "available"), bool(court, "source_qualified"), nullableId(court, "owner_character_id_raw")),
                new Provider(text(provider, "status"), bool(provider, "collection_available"), providerObservation),
                new Relation(bool(relation, "observed"), bool(relation, "collection_available"), named), missing));
    }

    static QueryRead query(JsonNode raw) {
        if (raw.isNull()) { return new UnusableQuery("query_not_observed"); } object(raw);
        JsonNode context = nullableObject(raw.get("character_interaction_ordinary_context"));
        if (context == null) { return new UnusableQuery("ordinary_context_not_observed"); }
        if (!text(context, "status").equals("available")) { return new UnusableQuery("ordinary_context_unavailable"); }
        EnumSet<Flag> flags = EnumSet.noneOf(Flag.class);
        for (Flag flag : Flag.values()) { if (bool(context, flag.wire())) { flags.add(flag); } }
        JsonNode roles = object(required(context, "effective_roles"));
        Optional<Materialization> materialization = Optional.empty(); JsonNode material = nullableObject(context.get("education_request_materialization"));
        if (material != null) {
            materialization = Optional.of(Materialization.fromObservation(
                    EducationOptionsCodec.decodeMaterialization(StrictJson.canonical(material))));
        }
        Context parsed = new Context(text(context, "schema"), text(context, "status"), text(context, "source"), bool(context, "read_only"),
                pid(context, "game_pid"), u64(context, "connection_generation"), exactInteger(context, "date_raw"), u64(context, "snapshot_revision"),
                text(context, "interaction_key"), id(context, "player_character_id"), id(context, "recipient_id"), flags,
                nullableText(context, "unavailable_reason"), nullableText(context, "executable_sha256"), u32(context, "definition_stable_hash"),
                new Roles(nullableId(roles, "actor_id"), nullableId(roles, "recipient_id"), nullableId(roles, "secondary_actor_id"), nullableId(roles, "secondary_recipient_id")),
                u32(context, "selected_option_count"), materialization);
        return new ObservedQuery(text(raw, "step"), bool(raw, "accepted"), text(raw, "status"), bool(raw, "read_only"), pid(raw, "game_pid"),
                u64(raw, "connection_generation"), exactInteger(raw, "date_raw"), u64(raw, "queried_native_revision"), u64(raw, "queried_revision"), u64(raw, "query_sequence"), parsed);
    }

    static State state(JsonNode raw) {
        object(raw); HashMap<Long, NegativeRecord> records = new HashMap<>();
        var entries = raw.fieldNames();
        while (entries.hasNext()) {
            String key = entries.next();
            StrictJson.require(key.matches("[1-9][0-9]*"), "canonical positive decimal child key required");
            long child;
            try { child = Long.parseLong(key); } catch (NumberFormatException error) { throw new IllegalArgumentException("state child key exceeds native range", error); }
            StrictJson.require(child <= 4_294_967_294L, "state child key outside native ID domain");
            JsonNode record = StrictJson.object(raw.get(key), Set.of("scope", "count", "last_date_raw", "last_native_revision", "cooldown_until_date_raw", "last_executable_sha256", "last_definition_stable_hash"));
            SourceScope source = sourceScope(required(record, "scope"));
            StrictJson.require(source.childId() == child, "state child/scope mismatch");
            JsonNode until = required(record, "cooldown_until_date_raw");
            records.put(child, new NegativeRecord(source, Math.toIntExact(StrictJson.integer(required(record, "count"), 1, 2)), exactInteger(record, "last_date_raw"),
                    u64(record, "last_native_revision"), until.isNull() ? Optional.empty() : Optional.of(integer(until)),
                    text(record, "last_executable_sha256"), exactInteger(record, "last_definition_stable_hash")));
        }
        return new State(records);
    }
    static SourceScope sourceScope(JsonNode raw) {
        array(raw); StrictJson.require(raw.size() == 14, "exact legacy scope tuple length");
        return new SourceScope(pid(raw.get(0)), StrictJson.integer(raw.get(1), BigInteger.ONE, StrictJson.UINT64_MAX), StrictJson.text(raw.get(2)),
                positiveId(raw.get(3)), positiveId(raw.get(4)), positiveId(raw.get(5)), integer(raw.get(6)), nullableInteger(raw.get(7)),
                focusState(nullableText(raw.get(8))), nullableText(raw.get(9)), positiveId(raw.get(10)), positiveId(raw.get(11)), nullableId(raw.get(12)), nullableText(raw.get(13)));
    }
    static ObjectNode state(State state) {
        ObjectNode records = StrictJson.object(); state.records().forEach((child, record) -> {
            ObjectNode value = records.putObject(Long.toString(child)); value.set("scope", scope(record.scope())); value.put("count", record.count());
            value.put("last_date_raw", record.lastDateRaw()); value.put("last_native_revision", record.lastNativeRevision());
            value.put("cooldown_until_date_raw", record.cooldownUntilDateRaw().orElse(null)); value.put("last_executable_sha256", record.lastExecutableSha256());
            value.put("last_definition_stable_hash", record.lastDefinitionStableHash());
        }); return records;
    }
    static ArrayNode scope(SourceScope source) {
        ArrayNode tuple = StrictJson.object().arrayNode(); tuple.add(source.gamePid()); tuple.add(source.connectionGeneration()); tuple.add(source.episodeRunId());
        tuple.add(source.actorId()); tuple.add(source.heirId()); tuple.add(source.childId()); tuple.add(source.ageMeasureRaw()); tuple.add(source.sexSelectorRaw());
        tuple.add(source.focusState() == null ? null : source.focusState().wire()); tuple.add(source.focusKey()); tuple.add(source.courtOwnerId()); tuple.add(source.namedPeerId());
        if (source.providerGuardianId() == null) { tuple.addNull(); } else { tuple.add(source.providerGuardianId()); } tuple.add(source.providerRoleSource()); return tuple;
    }
    static ObjectNode deferred(Deferred deferred) {
        ObjectNode result = StrictJson.object(); result.put("schema", RESULT_SCHEMA); result.put("status", deferred.status().wire());
        result.put("child_full_id", deferred.childId()); result.put("guardian_full_id", deferred.guardianId());
        result.put("last_observed_date_raw", deferred.lastDateRaw()); result.put("last_observed_native_revision", deferred.lastNativeRevision());
        result.put("cooldown_until_date_raw", deferred.cooldownUntilDateRaw().orElse(null));
        result.put("current_native_legal_status", "unknown_without_fresh_query"); result.put("business_action_credit", false); return result;
    }
    static ObjectNode observation(NegativeObserved observation) {
        ObjectNode result = StrictJson.object(); result.put("schema", RESULT_SCHEMA); result.put("status", "negative_observed");
        result.put("child_full_id", observation.childId()); result.put("guardian_full_id", observation.guardianId());
        result.put("consecutive_observed_dates", observation.consecutiveObservedDates()); result.put("last_observed_date_raw", observation.lastObservedDateRaw());
        result.put("cooldown_until_date_raw", observation.cooldownUntilDateRaw().orElse(null)); result.put("business_action_credit", false); return result;
    }

    static JsonNode required(JsonNode parent, String key) { JsonNode value = parent.get(key); StrictJson.require(value != null, "required field: " + key); return value; }
    private static JsonNode object(JsonNode value) { StrictJson.require(value != null && value.isObject(), "required JSON object"); return value; }
    private static JsonNode nullableObject(JsonNode value) { return value == null || value.isNull() ? null : object(value); }
    private static JsonNode array(JsonNode value) { StrictJson.require(value != null && value.isArray(), "required JSON array"); return value; }
    static String text(JsonNode parent, String key) { return StrictJson.text(required(parent, key)); }
    private static String nullableText(JsonNode parent, String key) { return nullableText(required(parent, key)); }
    private static String nullableTextOrMissing(JsonNode parent, String key) { JsonNode value = parent.get(key); return value == null ? null : nullableText(value); }
    private static String nullableText(JsonNode value) { return value.isNull() ? null : value.isTextual() && value.textValue().isEmpty() ? "" : StrictJson.text(value); }
    private static boolean bool(JsonNode parent, String key) { JsonNode value = required(parent, key); StrictJson.require(value.isBoolean(), "exact Boolean required: " + key); return value.booleanValue(); }
    private static BigInteger integer(JsonNode value) { StrictJson.require(value != null && value.isIntegralNumber(), "exact integer required"); return value.bigIntegerValue(); }
    private static BigInteger exactInteger(JsonNode parent, String key) { return integer(required(parent, key)); }
    private static BigInteger nullableInteger(JsonNode value) { return value.isNull() ? null : integer(value); }
    private static BigInteger nullableIntegerOrMissing(JsonNode parent, String key) { JsonNode value = parent.get(key); return value == null ? null : nullableInteger(value); }
    private static BigInteger u64(JsonNode parent, String key) { return StrictJson.integer(required(parent, key), BigInteger.ZERO, StrictJson.UINT64_MAX); }
    private static BigInteger positiveU64(JsonNode parent, String key) { return StrictJson.integer(required(parent, key), BigInteger.ONE, StrictJson.UINT64_MAX); }
    private static BigInteger u32(JsonNode parent, String key) { return StrictJson.integer(required(parent, key), BigInteger.ZERO, BigInteger.valueOf(4_294_967_295L)); }
    private static long id(JsonNode parent, String key) { return StrictJson.integer(required(parent, key), 0, 4_294_967_294L); }
    private static long pid(JsonNode parent, String key) { return pid(required(parent, key)); }
    private static long pid(JsonNode value) { return StrictJson.integer(value, 1, 4_294_967_295L); }
    private static long positiveId(JsonNode parent, String key) { return positiveId(required(parent, key)); }
    private static long positiveId(JsonNode value) { return StrictJson.integer(value, 1, 4_294_967_294L); }
    static Long nullableId(JsonNode parent, String key) { return nullableId(required(parent, key)); }
    static Long nullableIdOrMissing(JsonNode parent, String key) { JsonNode value = parent.get(key); return value == null ? null : nullableId(value); }
    static Long nullableId(JsonNode value) { return value.isNull() ? null : StrictJson.integer(value, 0, 4_294_967_294L); }
    private static List<String> strings(JsonNode array) { List<String> result = new ArrayList<>(); for (JsonNode value : array(array)) { result.add(StrictJson.text(value)); } return List.copyOf(result); }
    private static FocusState focusState(String wire) {
        if (wire == null) { return null; }
        for (FocusState state : FocusState.values()) { if (state.wire().equals(wire)) { return state; } }
        throw new IllegalArgumentException("unknown focus-management state");
    }
}
