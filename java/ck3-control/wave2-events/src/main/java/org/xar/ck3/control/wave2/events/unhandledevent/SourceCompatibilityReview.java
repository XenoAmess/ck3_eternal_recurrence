package org.xar.ck3.control.wave2.events.unhandledevent;

import java.io.IOException;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.TreeMap;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;

/** Reviewed authored-source DATA. No instance, native option mapping or action authority is created here. */
public final class SourceCompatibilityReview {
    public static final String BUILD = "1.21.0";
    public static final String EXE = "2F2B236A16223891C2DA8B167F5F3738D2AE3E6D69DE1B4FBE190A5402998ACC";
    public static final String RESOURCE = "/sourcecatalog/source-compatibility-1210-v1.json";
    public static final String RESOURCE_SHA256 = "b685bf37f960f837239de0efa223ef0cf294e5ec18c572747dcc82b0fce965d3";
    public static final int MAXIMUM_BYTES = 524288;
    private static volatile SourceCompatibilityReview cached;

    public enum Classification {
        DEPENDENCIES_IDENTICAL, DEFINITION_IDENTICAL_DEPENDENCIES_CHANGED,
        DEFINITION_CHANGED, LEGACY_SOURCE_UNAVAILABLE
    }
    public record FileReview(String relative, String baselineSha256, String targetSha256) {
        public FileReview { relativePath(relative); digest(baselineSha256); digest(targetSha256); }
        public boolean identical() { return baselineSha256.equals(targetSha256); }
        ObjectValue json() { return object(Map.of("relative", text(relative), "baseline_sha256", text(baselineSha256),
                "target_sha256", text(targetSha256))); }
    }
    public record DefinitionReview(String relative, String baselineTokenSha256, String targetTokenSha256,
            int baselineSourceOptions, int targetSourceOptions, List<List<String>> targetSourceNames) {
        public DefinitionReview {
            relativePath(relative); require(relative.startsWith("events/"), "event definition source required");
            digest(baselineTokenSha256); digest(targetTokenSha256);
            require(baselineSourceOptions > 0 && baselineSourceOptions <= 128
                    && targetSourceOptions > 0 && targetSourceOptions <= 128, "bounded authored option counts required");
            targetSourceNames = targetSourceNames.stream().map(List::copyOf).toList();
            require(targetSourceNames.size() == targetSourceOptions, "authored option name rows differ");
            for (List<String> names : targetSourceNames) for (String name : names)
                require(name != null && !name.isEmpty() && name.length() <= 1024, "bounded authored name key required");
        }
        public boolean identical() { return baselineTokenSha256.equals(targetTokenSha256); }
        ObjectValue json() {
            return object(Map.of("relative", text(relative), "baseline_token_sha256", text(baselineTokenSha256),
                    "target_token_sha256", text(targetTokenSha256),
                    "baseline_source_options", number(baselineSourceOptions), "target_source_options", number(targetSourceOptions),
                    "target_source_names", array(targetSourceNames.stream().map(names -> array(names.stream().map(SourceCompatibilityReview::text).toList())).toList())));
        }
    }
    public record EventReview(String eventKey, Classification classification, List<String> dependencyPaths,
            Optional<DefinitionReview> definition) {
        public EventReview {
            require(eventKey != null && eventKey.matches("[A-Za-z0-9_]+\\.[0-9]+"), "canonical event key required");
            Objects.requireNonNull(classification); dependencyPaths = List.copyOf(dependencyPaths); Objects.requireNonNull(definition);
            require(dependencyPaths.size() <= 32 && Set.copyOf(dependencyPaths).size() == dependencyPaths.size(), "bounded unique dependencies required");
            dependencyPaths.forEach(SourceCompatibilityReview::relativePath);
            require((classification == Classification.LEGACY_SOURCE_UNAVAILABLE) == definition.isEmpty(), "source-only classification/definition differs");
            require(classification != Classification.LEGACY_SOURCE_UNAVAILABLE || dependencyPaths.isEmpty(), "unreviewed legacy row cannot acquire source facts");
        }
        ObjectValue json() {
            return object(Map.of("event_key", text(eventKey), "classification", text(classification.name()),
                    "dependency_paths", array(dependencyPaths.stream().map(SourceCompatibilityReview::text).toList()),
                    "definition", definition.<Value>map(DefinitionReview::json).orElse(NULL)));
        }
    }

    private final Map<String, FileReview> files;
    private final Map<String, EventReview> events;
    private final Map<String, String> targetStock;

    SourceCompatibilityReview(Map<String, FileReview> files, Map<String, EventReview> events, Map<String, String> targetStock) {
        this.files = Map.copyOf(files); this.events = Map.copyOf(events); this.targetStock = Map.copyOf(targetStock);
        require(this.files.size() == 158 && this.events.size() == 198, "complete finite registered source review required");
        require(this.targetStock.keySet().equals(ReviewedLetterSourceRebind.installedSourceHashes().keySet()), "exact five stock review roles required");
        this.targetStock.forEach((path, sha) -> { relativePath(path); digest(sha); });
        this.files.forEach((path, value) -> require(path.equals(value.relative()), "source file key differs"));
        this.events.forEach((key, event) -> {
            require(key.equals(event.eventKey()), "event review key differs");
            for (String path : event.dependencyPaths()) require(this.files.containsKey(path), "unknown source dependency");
            if (event.definition().isPresent()) {
                require(!event.dependencyPaths().isEmpty()
                        && event.dependencyPaths().contains(event.definition().orElseThrow().relative()),
                        "selected definition must retain its actual source dependency");
                boolean same = event.dependencyPaths().stream().allMatch(path -> this.files.get(path).identical());
                Classification expected = !event.definition().orElseThrow().identical() ? Classification.DEFINITION_CHANGED
                        : same ? Classification.DEPENDENCIES_IDENTICAL : Classification.DEFINITION_IDENTICAL_DEPENDENCIES_CHANGED;
                require(event.classification() == expected, "source classification differs from actual fingerprints");
            }
        });
    }

    public Map<String, String> targetStockHashes() { return targetStock; }
    public Map<String, EventReview> events() { return events; }

    /** Static query remains unavailable for gameplay even when every authored source token is unchanged. */
    public ObjectValue query(String key) {
        Objects.requireNonNull(key); EventReview review = events.get(key);
        ObjectValue analysis = null;
        if (review != null) {
            Map<String, Value> values = new LinkedHashMap<>(review.json().fields());
            values.put("schema", text("xar.event-source-compatibility-analysis/v1"));
            values.put("status", text("source_only"));
            values.put("native_binding_status", text("unqualified"));
            values.put("material_effects_verified", new BooleanValue(false));
            values.put("dependencies", array(review.dependencyPaths().stream().map(path -> files.get(path).json()).toList()));
            analysis = object(values);
        }
        return unavailable(key, review == null ? "event_definition_key_not_source_reviewed"
                : "native_event_binding_not_qualified_for_1_21_0", analysis);
    }
    public static ObjectValue unavailable(String key) {
        return unavailable(key, "source_compatibility_review_unavailable", null);
    }
    private static ObjectValue unavailable(String key, String reason, ObjectValue analysis) {
        Map<String, Value> result = new LinkedHashMap<>();
        result.put("schema", text("xar.ck3.vanilla-event-knowledge")); result.put("schema_version", number(1));
        result.put("status", text("unavailable")); result.put("event_definition_key", text(key));
        result.put("ck3_build", text(BUILD)); result.put("ck3_exe_sha256", text(EXE)); result.put("contract", NULL);
        result.put("analysis", analysis == null ? NULL : analysis); result.put("observations", NULL);
        result.put("unavailable_reason", text(reason));
        return object(result);
    }

    public static SourceCompatibilityReview load() throws IOException {
        SourceCompatibilityReview result = cached;
        if (result != null) return result;
        synchronized (SourceCompatibilityReview.class) {
            result = cached;
            if (result == null) {
                byte[] raw;
                try (var input = SourceCompatibilityReview.class.getResourceAsStream(RESOURCE)) {
                    if (input == null) throw new IOException("pinned source compatibility review is absent");
                    raw = input.readNBytes(MAXIMUM_BYTES + 1);
                }
                require(raw.length <= MAXIMUM_BYTES && sha(raw).equals(RESOURCE_SHA256), "source compatibility review byte pin differs");
                result = parse(raw); cached = result;
            }
        }
        return result;
    }

    static SourceCompatibilityReview parse(byte[] raw) {
        require(raw.length > 0 && raw.length <= MAXIMUM_BYTES, "bounded source review required");
        ObjectValue root = requiredObject(RetainedJson.parse(raw, new ParseBudget(MAXIMUM_BYTES, 100000, 32)));
        fields(root, Set.of("schema", "schema_version", "baseline_build", "target_build", "target_exe_sha256", "baseline_resource_sha256", "native_binding_qualified", "files", "events", "target_stock"));
        require(string(root, "schema").equals("xar.event-source-compatibility-review/v1") && count(root.get("schema_version"), 1, 1) == 1, "strict source review schema/version required");
        require(string(root, "baseline_build").equals("1.20.0.4") && string(root, "target_build").equals(BUILD)
                && string(root, "target_exe_sha256").equals(EXE)
                && string(root, "baseline_resource_sha256").equals(org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge.INPUT_SHA256), "source review version/source identity differs");
        require(root.get("native_binding_qualified") instanceof BooleanValue value && !value.value(), "authored source data cannot authorize Native");
        Map<String, FileReview> files = new TreeMap<>();
        requiredObject(root.get("files")).fields().forEach((key, value) -> {
            ObjectValue row = requiredObject(value); fields(row, Set.of("relative", "baseline_sha256", "target_sha256"));
            files.put(key, new FileReview(string(row, "relative"), string(row, "baseline_sha256"), string(row, "target_sha256")));
        });
        Map<String, EventReview> events = new TreeMap<>();
        requiredObject(root.get("events")).fields().forEach((key, value) -> {
            ObjectValue row = requiredObject(value); fields(row, Set.of("event_key", "classification", "dependency_paths", "definition"));
            List<String> paths = strings(row.get("dependency_paths")); Value definition = row.get("definition");
            Optional<DefinitionReview> selected = Optional.empty();
            if (!(definition instanceof NullValue)) {
                ObjectValue body = requiredObject(definition);
                fields(body, Set.of("relative", "baseline_token_sha256", "target_token_sha256", "baseline_source_options", "target_source_options", "target_source_names"));
                List<List<String>> names = new ArrayList<>();
                require(body.get("target_source_names") instanceof ArrayValue, "authored name rows required");
                for (Value namesRow : ((ArrayValue) body.get("target_source_names")).values()) names.add(strings(namesRow));
                selected = Optional.of(new DefinitionReview(string(body, "relative"), string(body, "baseline_token_sha256"), string(body, "target_token_sha256"),
                        count(body.get("baseline_source_options"), 1, 128), count(body.get("target_source_options"), 1, 128), names));
            }
            events.put(key, new EventReview(string(row, "event_key"), Classification.valueOf(string(row, "classification")), paths, selected));
        });
        Map<String, String> stock = new TreeMap<>();
        requiredObject(root.get("target_stock")).fields().forEach((key, value) -> stock.put(key, requiredString(value)));
        return new SourceCompatibilityReview(files, events, stock);
    }

    ObjectValue json() {
        Map<String, Value> fileRows = new TreeMap<>(); files.forEach((key, value) -> fileRows.put(key, value.json()));
        Map<String, Value> eventRows = new TreeMap<>(); events.forEach((key, value) -> eventRows.put(key, value.json()));
        Map<String, Value> stockRows = new TreeMap<>(); targetStock.forEach((key, value) -> stockRows.put(key, text(value)));
        Map<String, Value> result = new LinkedHashMap<>();
        result.put("schema", text("xar.event-source-compatibility-review/v1")); result.put("schema_version", number(1));
        result.put("baseline_build", text("1.20.0.4")); result.put("target_build", text(BUILD)); result.put("target_exe_sha256", text(EXE));
        result.put("baseline_resource_sha256", text(org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge.INPUT_SHA256));
        result.put("native_binding_qualified", new BooleanValue(false)); result.put("files", object(fileRows));
        result.put("events", object(eventRows)); result.put("target_stock", object(stockRows)); return object(result);
    }

    static String sha(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException impossible) { throw new AssertionError(impossible); }
    }
    private static void relativePath(String value) {
        require(value != null && !value.isEmpty() && !value.contains("\\") && !value.contains(":")
                && !Path.of(value).isAbsolute() && !List.of(value.split("/", -1)).contains("..")
                && !List.of(value.split("/", -1)).contains(""), "bounded relative source path required");
    }
    private static void digest(String value) { require(value != null && value.matches("[0-9a-f]{64}"), "exact lowercase source SHA256 required"); }
    private static ObjectValue requiredObject(Value value) { require(value instanceof ObjectValue, "actual source object required"); return (ObjectValue) value; }
    private static String requiredString(Value value) { require(value instanceof StringValue, "actual source string required"); return ((StringValue) value).value(); }
    private static String string(ObjectValue object, String key) { return requiredString(object.get(key)); }
    private static List<String> strings(Value value) {
        require(value instanceof ArrayValue, "actual source array required");
        return ((ArrayValue) value).values().stream().map(SourceCompatibilityReview::requiredString).toList();
    }
    private static void fields(ObjectValue value, Set<String> fields) { require(value.fields().keySet().equals(fields), "closed source review fields required"); }
    private static ObjectValue object(Map<String, Value> values) { return new ObjectValue(values); }
    private static StringValue text(String value) { return new StringValue(value); }
    private static IntegerValue number(int value) { return new IntegerValue(java.math.BigInteger.valueOf(value)); }
    private static int count(Value value, int minimum, int maximum) {
        require(value instanceof IntegerValue, "actual integer source count required");
        var exact = ((IntegerValue) value).value();
        require(exact.compareTo(java.math.BigInteger.valueOf(minimum)) >= 0
                && exact.compareTo(java.math.BigInteger.valueOf(maximum)) <= 0, "bounded source count required");
        return exact.intValueExact();
    }
    private static ArrayValue array(List<? extends Value> values) { return new ArrayValue(new ArrayList<>(values)); }
    private static void require(boolean condition, String message) { StrictJson.require(condition, message); }
}
