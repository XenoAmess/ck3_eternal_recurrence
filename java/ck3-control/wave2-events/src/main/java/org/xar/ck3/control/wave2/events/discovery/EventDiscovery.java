package org.xar.ck3.control.wave2.events.discovery;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog.Catalog;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog.TextRules;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;

/** Original offline discovery semantics over the sole complete, source-bound catalog. No Game authority. */
public final class EventDiscovery {
    public static final String SCHEMA = "xar.ck3.vanilla-event-knowledge-index";
    public static final Comparator<String> KEY_ORDER = EventDiscovery::compareCodePoints;
    private static final CanonicalBudget CANONICAL_BUDGET = new CanonicalBudget(64L * 1024 * 1024, 4_000_000, 128);
    @FunctionalInterface public interface CatalogSource { Catalog load(String build); }
    public enum EvidenceClass {
        ANY("any"), SOURCE_REVIEWED("source-reviewed"), MIGRATION_ONLY("migration-only");
        private final String wire; EvidenceClass(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static EvidenceClass optional(String wire) {
            for (var value : values()) if (value.wire.equals(wire)) return value; return null;
        }
    }
    public enum Reason {
        UNSUPPORTED_BUILD("unsupported_ck3_build"), INVALID_FILTER("invalid_filter"),
        INVALID_LIMIT("invalid_limit"), INVALID_CURSOR("invalid_cursor");
        private final String wire; Reason(String wire) { this.wire = wire; } public String wire() { return wire; }
    }
    public enum Parameter {
        BUILD("build"), QUERY("query"), NAMESPACE("namespace"), EVIDENCE_CLASS("evidence_class"),
        HAS_OBSERVATIONS("has_observations"), LIMIT("limit"), AFTER_KEY("after_key");
        private final String wire; Parameter(String wire) { this.wire = wire; } public String wire() { return wire; }
    }
    public record Failure(Reason reason, Parameter parameter) {
        public Failure {
            Objects.requireNonNull(reason); Objects.requireNonNull(parameter);
            StrictJson.require(switch (reason) {
                case UNSUPPORTED_BUILD -> parameter == Parameter.BUILD;
                case INVALID_FILTER -> Set.of(Parameter.QUERY, Parameter.NAMESPACE, Parameter.EVIDENCE_CLASS, Parameter.HAS_OBSERVATIONS).contains(parameter);
                case INVALID_LIMIT -> parameter == Parameter.LIMIT;
                case INVALID_CURSOR -> parameter == Parameter.AFTER_KEY;
            }, "discovery reason and original invalid parameter differ");
        }
    }
    /** Nullable fields deliberately retain the original invalid-response echo, including empty normalized strings. */
    public record Query(String ck3Build, String query, String namespace, EvidenceClass evidenceClass,
            Boolean hasObservations, String afterKey, Integer limit) { }
    public sealed interface Request permits Ready, Invalid { Query parameters(); }
    public record Ready(Query parameters) implements Request {
        public Ready {
            Objects.requireNonNull(parameters);
            StrictJson.require(parameters.ck3Build() != null && RegisteredEventKnowledge.EXE.containsKey(parameters.ck3Build())
                    && parameters.evidenceClass() != null && parameters.limit() != null
                    && parameters.limit() >= 1 && parameters.limit() <= 100,
                    "validated supported discovery parameters required");
            StrictJson.require(parameters.namespace() == null || !parameters.namespace().isEmpty(), "nonempty normalized namespace required");
            StrictJson.require(parameters.afterKey() == null || !parameters.afterKey().isEmpty(), "nonempty normalized cursor required");
        }
    }
    public record Invalid(Query parameters, Failure failure) implements Request {
        public Invalid { Objects.requireNonNull(parameters); Objects.requireNonNull(failure); }
    }
    public record Item(String eventDefinitionKey, String namespace, EvidenceClass evidenceClass, String reviewSummary,
            int sourceFileCount, int observationCount, int portableEvidenceCount) {
        public Item {
            StrictJson.text(eventDefinitionKey); StrictJson.text(namespace); Objects.requireNonNull(reviewSummary);
            StrictJson.require(evidenceClass != null && evidenceClass != EvidenceClass.ANY
                    && sourceFileCount >= 0 && observationCount >= 0 && portableEvidenceCount >= 0 && portableEvidenceCount <= 1,
                    "exact discovery row domain required");
            StrictJson.require((sourceFileCount > 0) == (evidenceClass == EvidenceClass.SOURCE_REVIEWED), "source count and evidence class differ");
        }
    }
    public record Summary(int totalEvents, int sourceReviewedEvents, int migrationOnlyEvents,
            int eventsWithObservations, int portableEvents) {
        public Summary {
            StrictJson.require(totalEvents >= 0 && sourceReviewedEvents >= 0 && migrationOnlyEvents >= 0
                    && eventsWithObservations >= 0 && portableEvents >= 0
                    && sourceReviewedEvents + migrationOnlyEvents == totalEvents
                    && eventsWithObservations <= totalEvents && portableEvents <= totalEvents, "complete discovery counters required");
        }
        public static Summary empty() { return new Summary(0, 0, 0, 0, 0); }
    }
    public record Response(Query parameters, String datasetSha256, Summary datasetSummary, Summary matchSummary,
            int totalMatches, List<Item> items, String nextAfterKey, Failure failure) {
        public Response {
            Objects.requireNonNull(parameters); Objects.requireNonNull(datasetSummary); Objects.requireNonNull(matchSummary);
            items = List.copyOf(items);
            StrictJson.require(totalMatches >= 0 && items.size() <= 100 && items.size() <= totalMatches, "bounded exact discovery page required");
            if (failure == null) {
                new Ready(parameters);
                StrictJson.require(datasetSha256 != null && datasetSha256.matches("[A-F0-9]{64}")
                        && totalMatches == matchSummary.totalEvents() && totalMatches <= datasetSummary.totalEvents()
                        && items.size() <= parameters.limit(), "available discovery identity/counters required");
                String previous = parameters.afterKey();
                for (Item item : items) {
                    StrictJson.require(previous == null || KEY_ORDER.compare(item.eventDefinitionKey(), previous) > 0, "page keys must be distinct and strictly after the original cursor");
                    previous = item.eventDefinitionKey();
                }
                StrictJson.require(nextAfterKey == null || !items.isEmpty() && nextAfterKey.equals(items.getLast().eventDefinitionKey()), "next cursor must identify the actual last returned row");
            }
            else StrictJson.require(datasetSha256 == null && items.isEmpty() && totalMatches == 0 && nextAfterKey == null
                    && datasetSummary.equals(Summary.empty()) && matchSummary.equals(Summary.empty()), "unavailable discovery must retain empty typed result");
        }
        public boolean available() { return failure == null; }
    }
    private record Searchable(Item item, String search) { }
    private final CatalogSource catalogs;
    private final TextRules text;
    public EventDiscovery(CatalogSource catalogs, TextRules actualTextRules) {
        this.catalogs = Objects.requireNonNull(catalogs); text = Objects.requireNonNull(actualTextRules);
    }
    public TextRules textRules() { return text; }
    public Response list(Request request, Set<String> portableKeys) {
        Objects.requireNonNull(request); Set<String> portable = Set.copyOf(portableKeys);
        portable.forEach(StrictJson::text);
        if (request instanceof Invalid invalid) return unavailable(invalid.parameters(), invalid.failure());
        Query query = request.parameters(); Catalog catalog = Objects.requireNonNull(catalogs.load(query.ck3Build()));
        StrictJson.require(query.ck3Build().equals(catalog.ck3Build()), "complete catalog returned another exact build");
        List<String> keys = catalog.contracts().keySet().stream().sorted(KEY_ORDER).toList();
        if (query.afterKey() != null && !catalog.contracts().containsKey(query.afterKey()))
            return unavailable(query, new Failure(Reason.INVALID_CURSOR, Parameter.AFTER_KEY));
        List<Searchable> all = new ArrayList<>(); List<Value> digestRows = new ArrayList<>();
        for (String key : keys) {
            ObjectValue analysis = catalog.analysis().getOrDefault(key, new ObjectValue(Map.of()));
            ObjectValue observations = catalog.observations().get(key);
            ObjectValue sources = analysis.get("source_sha256") instanceof ObjectValue object ? object : new ObjectValue(Map.of());
            int sourceCount = (int) sources.fields().entrySet().stream().filter(entry -> !entry.getKey().isEmpty()
                    && entry.getValue() instanceof StringValue digest && !digest.value().isEmpty()).count();
            String review = analysis.get("review_summary") instanceof StringValue value ? value.value() : "";
            int observationCount = observations == null || observations.fields().isEmpty() ? 0
                    : observations.get("exemplars") instanceof ArrayValue exemplars ? exemplars.values().size() : 1;
            int dot = key.lastIndexOf('.'); String namespace = dot < 0 ? key : key.substring(0, dot);
            Item item = new Item(key, namespace, sourceCount > 0 ? EvidenceClass.SOURCE_REVIEWED : EvidenceClass.MIGRATION_ONLY,
                    review, sourceCount, observationCount, portable.contains(key) ? 1 : 0);
            List<String> searchableParts = new ArrayList<>(List.of(key, namespace, review)); searchableParts.addAll(sources.fields().keySet());
            String search = String.join("\n", searchableParts);
            all.add(new Searchable(item, fold(search, text)));
            digestRows.add(EventDiscoveryCodec.item(item).with("contract_sha256", RetainedJson.value(digest(catalog.contracts().get(key))))
                    .with("analysis_sha256", RetainedJson.value(digest(analysis)))
                    .with("observations_sha256", RetainedJson.value(observations == null ? null : digest(observations))));
        }
        String needle = query.query() == null || query.query().isEmpty() ? null : fold(query.query(), text);
        List<Item> matches = all.stream().filter(row -> query.namespace() == null || row.item().namespace().equals(query.namespace()))
                .filter(row -> query.evidenceClass() == EvidenceClass.ANY || row.item().evidenceClass() == query.evidenceClass())
                .filter(row -> query.hasObservations() == null || (row.item().observationCount() > 0) == query.hasObservations())
                .filter(row -> needle == null || row.search().contains(needle)).map(Searchable::item).toList();
        List<Item> candidates = matches.stream().filter(item -> query.afterKey() == null
                || KEY_ORDER.compare(item.eventDefinitionKey(), query.afterKey()) > 0).toList();
        List<Item> page = candidates.subList(0, Math.min(query.limit(), candidates.size()));
        String next = candidates.size() > query.limit() && !page.isEmpty() ? page.getLast().eventDefinitionKey() : null;
        return new Response(query, digest(new ArrayValue(digestRows)), summary(all.stream().map(Searchable::item).toList()),
                summary(matches), matches.size(), page, next, null);
    }
    public static Response unavailable(Query query, Failure failure) {
        return new Response(query, null, Summary.empty(), Summary.empty(), 0, List.of(), null, failure);
    }
    private static Summary summary(List<Item> rows) {
        int source = 0, observed = 0, portable = 0;
        for (Item row : rows) { if (row.sourceFileCount() > 0) source++; if (row.observationCount() > 0) observed++; portable += row.portableEvidenceCount(); }
        return new Summary(rows.size(), source, rows.size() - source, observed, portable);
    }
    private static String digest(Value value) { return RetainedJson.pythonCanonical(value, CANONICAL_BUDGET).sha256().toUpperCase(Locale.ROOT); }
    public static String strip(String value, TextRules rules) {
        return Objects.requireNonNull(rules).strip(value);
    }
    public static String fold(String value, TextRules rules) {
        return Objects.requireNonNull(rules).fold(value);
    }
    private static int compareCodePoints(String left, String right) {
        int i = 0, j = 0;
        while (i < left.length() && j < right.length()) {
            int a = left.codePointAt(i), b = right.codePointAt(j); if (a != b) return Integer.compare(a, b);
            i += Character.charCount(a); j += Character.charCount(b);
        }
        return Integer.compare(left.length() - i, right.length() - j);
    }
}
