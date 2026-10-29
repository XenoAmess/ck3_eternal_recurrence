package org.xar.ck3.control.wave2.events.discovery;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog.TextRules;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.discovery.EventDiscovery.*;

/** One strict wire owner for original nullable response fields and typed filter-validation priority. */
public final class EventDiscoveryCodec {
    private static final Set<String> ARGUMENTS = Set.of("ck3_build", "query", "namespace", "evidence_class", "has_observations", "after_key", "limit");
    private static final Set<String> RESPONSE = Set.of("schema", "schema_version", "status", "ck3_build", "ck3_exe_sha256", "query", "namespace",
            "evidence_class", "has_observations", "after_key", "limit", "dataset_sha256", "dataset_summary", "match_summary", "total_matches",
            "items", "next_after_key", "unavailable_reason", "invalid_parameter");
    private static final Set<String> ITEM = Set.of("event_definition_key", "namespace", "evidence_class", "review_summary", "source_file_count", "observation_count", "portable_evidence_count");
    private static final Set<String> SUMMARY = Set.of("total_events", "source_reviewed_events", "migration_only_events", "events_with_observations", "portable_events");
    private EventDiscoveryCodec() { }
    public static Request decodeRequest(byte[] raw, TextRules text, String actualPublicDefaultBuild) {
        return decodeRequest(RetainedJson.object(RetainedJson.parse(raw)), text, actualPublicDefaultBuild);
    }
    public static Request decodeRequest(ObjectValue raw, TextRules text, String actualPublicDefaultBuild) {
        StrictJson.require(actualPublicDefaultBuild != null && RegisteredEventKnowledge.EXE.containsKey(actualPublicDefaultBuild),
                "actual original public declaration default build required");
        StrictJson.require(ARGUMENTS.containsAll(raw.fields().keySet()), "unknown event discovery argument");
        Value build = raw.fields().getOrDefault("ck3_build", v(actualPublicDefaultBuild));
        Value query = raw.getOrNull("query"), namespace = raw.getOrNull("namespace"), after = raw.getOrNull("after_key");
        Value evidence = raw.fields().getOrDefault("evidence_class", v("any"));
        Value observations = raw.getOrNull("has_observations"), limit = raw.fields().getOrDefault("limit", n(50));
        String buildText = stringOrNull(build), queryText = normalized(query, text), namespaceText = normalized(namespace, text), afterText = normalized(after, text);
        EvidenceClass evidenceClass = EvidenceClass.optional(stringOrNull(evidence));
        Boolean observed = observations instanceof BooleanValue bool ? bool.value() : null;
        Integer boundedLimit = limit instanceof IntegerValue number && number.value().compareTo(BigInteger.ONE) >= 0
                && number.value().compareTo(BigInteger.valueOf(100)) <= 0 ? number.value().intValueExact() : null;
        Query parameters = new Query(buildText, queryText, namespaceText, evidenceClass, observed, afterText, boundedLimit);
        Failure invalid = null;
        if (buildText == null || !RegisteredEventKnowledge.EXE.containsKey(buildText)) invalid = new Failure(Reason.UNSUPPORTED_BUILD, Parameter.BUILD);
        else if (!nil(query) && !(query instanceof StringValue)) invalid = new Failure(Reason.INVALID_FILTER, Parameter.QUERY);
        else if (!nil(namespace) && (!(namespace instanceof StringValue) || namespaceText.isEmpty())) invalid = new Failure(Reason.INVALID_FILTER, Parameter.NAMESPACE);
        else if (evidenceClass == null) invalid = new Failure(Reason.INVALID_FILTER, Parameter.EVIDENCE_CLASS);
        else if (!nil(observations) && !(observations instanceof BooleanValue)) invalid = new Failure(Reason.INVALID_FILTER, Parameter.HAS_OBSERVATIONS);
        else if (boundedLimit == null) invalid = new Failure(Reason.INVALID_LIMIT, Parameter.LIMIT);
        else if (!nil(after) && (!(after instanceof StringValue) || afterText.isEmpty())) invalid = new Failure(Reason.INVALID_CURSOR, Parameter.AFTER_KEY);
        return invalid == null ? new Ready(parameters) : new Invalid(parameters, invalid);
    }
    public static byte[] encode(Response response) { return RetainedJson.encode(response(response)); }
    public static ObjectValue response(Response value) {
        Query q = value.parameters(); Map<String, Value> row = new LinkedHashMap<>();
        row.put("schema", v(SCHEMA)); row.put("schema_version", n(1)); row.put("status", v(value.available() ? "available" : "unavailable"));
        row.put("ck3_build", v(q.ck3Build())); row.put("ck3_exe_sha256", v(q.ck3Build() == null ? null : RegisteredEventKnowledge.EXE.get(q.ck3Build())));
        row.put("query", v(q.query())); row.put("namespace", v(q.namespace())); row.put("evidence_class", v(q.evidenceClass() == null ? null : q.evidenceClass().wire()));
        row.put("has_observations", q.hasObservations() == null ? RetainedJson.NULL : new BooleanValue(q.hasObservations()));
        row.put("after_key", v(q.afterKey())); row.put("limit", q.limit() == null ? RetainedJson.NULL : n(q.limit()));
        row.put("dataset_sha256", v(value.datasetSha256())); row.put("dataset_summary", summary(value.datasetSummary())); row.put("match_summary", summary(value.matchSummary()));
        row.put("total_matches", n(value.totalMatches())); row.put("items", new ArrayValue(value.items().stream().map(EventDiscoveryCodec::item).map(Value.class::cast).toList()));
        row.put("next_after_key", v(value.nextAfterKey())); row.put("unavailable_reason", v(value.failure() == null ? null : value.failure().reason().wire()));
        row.put("invalid_parameter", v(value.failure() == null ? null : value.failure().parameter().wire())); return new ObjectValue(row);
    }
    public static Response decodeResponse(byte[] raw) { return decodeResponse(RetainedJson.object(RetainedJson.parse(raw))); }
    public static Response decodeResponse(ObjectValue input) {
        exact(input, RESPONSE); StrictJson.require(SCHEMA.equals(requiredString(input.get("schema"))) && integer(input.get("schema_version")) == 1,
                "exact discovery response schema/version required");
        String status = requiredString(input.get("status")); StrictJson.require(Set.of("available", "unavailable").contains(status), "discovery status invalid");
        String build = nullableString(input.get("ck3_build"));
        StrictJson.require(java.util.Objects.equals(build == null ? null : RegisteredEventKnowledge.EXE.get(build), nullableString(input.get("ck3_exe_sha256"))), "discovery executable build identity differs");
        String rawEvidence = nullableString(input.get("evidence_class")); EvidenceClass evidence = EvidenceClass.optional(rawEvidence);
        StrictJson.require(rawEvidence == null || evidence != null, "unknown discovery evidence class");
        Boolean observed = RetainedJson.bool(input.get("has_observations")); Integer limit = nil(input.get("limit")) ? null : integer(input.get("limit"));
        StrictJson.require(limit == null || limit >= 1 && limit <= 100, "discovery limit outside schema");
        Query query = new Query(build, nullableString(input.get("query")), nullableString(input.get("namespace")), evidence, observed,
                nullableString(input.get("after_key")), limit);
        Failure failure = null; String reason = nullableString(input.get("unavailable_reason")), parameter = nullableString(input.get("invalid_parameter"));
        if (status.equals("unavailable")) {
            Reason typedReason = null; Parameter typedParameter = null;
            for (Reason candidate : Reason.values()) if (candidate.wire().equals(reason)) typedReason = candidate;
            for (Parameter candidate : Parameter.values()) if (candidate.wire().equals(parameter)) typedParameter = candidate;
            StrictJson.require(typedReason != null && typedParameter != null, "unavailable discovery must identify its original reason/parameter");
            failure = new Failure(typedReason, typedParameter);
        } else { StrictJson.require(reason == null && parameter == null, "available discovery cannot carry an error"); new Ready(query); }
        StrictJson.require(input.get("items") instanceof ArrayValue, "discovery items array required");
        List<Item> items = new ArrayList<>();
        for (Value raw : ((ArrayValue) input.get("items")).values()) {
            ObjectValue row = RetainedJson.object(raw); exact(row, ITEM);
            items.add(new Item(requiredString(row.get("event_definition_key")), requiredString(row.get("namespace")),
                    EvidenceClass.optional(requiredString(row.get("evidence_class"))), requiredString(row.get("review_summary")),
                    integer(row.get("source_file_count")), integer(row.get("observation_count")), integer(row.get("portable_evidence_count"))));
        }
        return new Response(query, nullableString(input.get("dataset_sha256")), decodeSummary(input.get("dataset_summary")),
                decodeSummary(input.get("match_summary")), integer(input.get("total_matches")), items,
                nullableString(input.get("next_after_key")), failure);
    }
    public static ObjectValue item(Item value) {
        Map<String, Value> row = new LinkedHashMap<>(); row.put("event_definition_key", v(value.eventDefinitionKey())); row.put("namespace", v(value.namespace()));
        row.put("evidence_class", v(value.evidenceClass().wire())); row.put("review_summary", v(value.reviewSummary()));
        row.put("source_file_count", n(value.sourceFileCount())); row.put("observation_count", n(value.observationCount())); row.put("portable_evidence_count", n(value.portableEvidenceCount()));
        return new ObjectValue(row);
    }
    private static ObjectValue summary(Summary value) {
        return new ObjectValue(Map.of("total_events", n(value.totalEvents()), "source_reviewed_events", n(value.sourceReviewedEvents()),
                "migration_only_events", n(value.migrationOnlyEvents()), "events_with_observations", n(value.eventsWithObservations()), "portable_events", n(value.portableEvents())));
    }
    private static Summary decodeSummary(Value value) {
        ObjectValue row = RetainedJson.object(value); exact(row, SUMMARY);
        return new Summary(integer(row.get("total_events")), integer(row.get("source_reviewed_events")), integer(row.get("migration_only_events")),
                integer(row.get("events_with_observations")), integer(row.get("portable_events")));
    }
    private static void exact(ObjectValue value, Set<String> expected) { StrictJson.require(value.fields().keySet().equals(expected), "missing/unknown discovery fields"); }
    private static boolean nil(Value value) { return value == null || value instanceof NullValue; }
    private static String stringOrNull(Value value) { return value instanceof StringValue string ? string.value() : null; }
    private static String normalized(Value value, TextRules text) { return value instanceof StringValue string ? strip(string.value(), text) : null; }
    private static String nullableString(Value value) { return RetainedJson.string(value); }
    private static String requiredString(Value value) { String result = nullableString(value); StrictJson.require(result != null, "text token required"); return result; }
    private static int integer(Value value) { BigInteger number = RetainedJson.integer(value); StrictJson.require(number != null && number.signum() >= 0 && number.bitLength() <= 31, "nonnegative bounded exact integer required"); return number.intValueExact(); }
    private static Value v(String value) { return RetainedJson.value(value); }
    private static IntegerValue n(int value) { return new IntegerValue(BigInteger.valueOf(value)); }
}
