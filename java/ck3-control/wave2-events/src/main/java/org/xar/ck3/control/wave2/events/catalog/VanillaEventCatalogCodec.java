package org.xar.ck3.control.wave2.events.catalog;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;

/** The complete legacy JSON domain is retained; this codec never clips analysis or observations. */
final class VanillaEventCatalogCodec {
    static final String SCHEMA = "xar.ck3.complete-vanilla-event-catalog/v1";
    static final String KNOWLEDGE_SCHEMA = "xar.ck3.vanilla-event-knowledge";
    static final String UNREGISTERED_PROBE = "xar_java_catalog_unregistered_probe.0";
    static final RetainedJson.ParseBudget PARSE_BUDGET = new RetainedJson.ParseBudget(64L << 20, 4_000_000, 128);
    private static final Set<String> KNOWLEDGE_FIELDS = Set.of("schema", "schema_version", "status",
            "event_definition_key", "ck3_build", "ck3_exe_sha256", "contract", "analysis", "observations", "unavailable_reason");
    private static final int MAXIMUM_ROWS = 100_000;

    private VanillaEventCatalogCodec() { }

    enum Status { AVAILABLE, UNAVAILABLE }
    record KnowledgeRow(Status status, ObjectValue original, Optional<ObjectValue> contract,
            Optional<ObjectValue> analysis, Optional<ObjectValue> observations) {
        KnowledgeRow {
            Objects.requireNonNull(status); Objects.requireNonNull(original); Objects.requireNonNull(contract);
            Objects.requireNonNull(analysis); Objects.requireNonNull(observations);
        }
    }
    record BuildData(String executableSha256, Map<String, KnowledgeRow> knowledge, ObjectValue unregisteredQuery, VanillaEventCatalog.Catalog catalog,
            VanillaEventCatalog.MigrationReference reference) {
        BuildData {
            Objects.requireNonNull(executableSha256); knowledge = immutable(knowledge); Objects.requireNonNull(unregisteredQuery);
            Objects.requireNonNull(catalog); Objects.requireNonNull(reference);
        }
    }
    record Document(String defaultBuild, String currentBuild, Map<String, BuildData> builds,
            VanillaEventCatalog.TextRules textRules) {
        Document {
            Objects.requireNonNull(defaultBuild); Objects.requireNonNull(currentBuild);
            builds = immutable(builds); Objects.requireNonNull(textRules);
        }
    }

    /** Returns validated DATA only. Only VanillaEventCatalog's pinned resource loader can construct its usable provider. */
    static Document parse(byte[] raw) {
        ObjectValue document = object(RetainedJson.parse(raw, PARSE_BUDGET));
        fields(document, Set.of("schema", "schema_version", "default_build", "current_build", "builds", "text_rules", "migration_reference"));
        equalText(document, "schema", SCHEMA); version(document);
        String defaultBuild = text(document.get("default_build"));
        String currentBuild = text(document.get("current_build"));
        need(defaultBuild.equals("1.19.0.6") && currentBuild.equals("1.20.0.4"),
                "original registry default and current build must remain separate exact identities");
        var rules = textRules(object(document.get("text_rules")));
        ObjectValue buildRows = object(document.get("builds"));
        ObjectValue references = object(document.get("migration_reference"));
        need(buildRows.fields().keySet().equals(RegisteredEventKnowledge.EXE.keySet())
                && references.fields().keySet().equals(buildRows.fields().keySet()), "exact complete supported build tables required");
        Map<String, BuildData> result = new LinkedHashMap<>();
        for (var entry : buildRows.fields().entrySet()) {
            String build = entry.getKey(); ObjectValue row = object(entry.getValue());
            fields(row, Set.of("ck3_exe_sha256", "knowledge", "unregistered_query", "catalog_keys"));
            String executable = text(row.get("ck3_exe_sha256"));
            need(executable.equals(RegisteredEventKnowledge.EXE.get(build)), "original exact build executable identity differs");
            ObjectValue originals = object(row.get("knowledge"));
            need(!originals.fields().isEmpty() && originals.fields().size() <= MAXIMUM_ROWS, "bounded complete query table required");
            Map<String, KnowledgeRow> knowledge = new LinkedHashMap<>();
            for (var original : originals.fields().entrySet()) {
                key(original.getKey(), rules);
                knowledge.put(original.getKey(), knowledge(build, executable, original.getKey(), object(original.getValue())));
            }
            need(!knowledge.containsKey(UNREGISTERED_PROBE), "original unregistered probe must remain outside registered query rows");
            KnowledgeRow unregistered = knowledge(build, executable, UNREGISTERED_PROBE, object(row.get("unregistered_query")));
            need(unregistered.status() == Status.UNAVAILABLE
                    && text(unregistered.original().get("unavailable_reason")).equals("event_definition_key_not_registered"),
                    "complete original notregistered response template required");
            ObjectValue keysets = object(row.get("catalog_keys"));
            fields(keysets, Set.of("contracts", "analysis", "observations"));
            var contracts = project(keys(keysets.get("contracts"), rules), knowledge, Component.CONTRACT);
            var analysis = project(keys(keysets.get("analysis"), rules), knowledge, Component.ANALYSIS);
            var observations = project(keys(keysets.get("observations"), rules), knowledge, Component.OBSERVATIONS);
            need(!contracts.isEmpty() && contracts.keySet().containsAll(analysis.keySet())
                    && contracts.keySet().containsAll(observations.keySet()), "actual catalog metadata must retain its original registered key domain");
            if (!build.equals(defaultBuild))
                need(observations.isEmpty() && analysis.keySet().equals(contracts.keySet()),
                        "actual migrated catalog uses available default keys and explicitly empty current observation table");
            var catalog = new VanillaEventCatalog.Catalog(build, contracts, analysis, observations);
            var reference = reference(object(references.get(build)), catalog);
            result.put(build, new BuildData(executable, knowledge, unregistered.original(), catalog, reference));
        }
        return new Document(defaultBuild, currentBuild, result, rules);
    }

    private enum Component { CONTRACT, ANALYSIS, OBSERVATIONS }

    private static Map<String, ObjectValue> project(List<String> keys, Map<String, KnowledgeRow> rows, Component component) {
        Map<String, ObjectValue> result = new LinkedHashMap<>();
        for (String key : keys) {
            KnowledgeRow row = rows.get(key); need(row != null, "catalog key is absent from the complete original query table");
            Optional<ObjectValue> value = switch (component) {
                case CONTRACT -> row.contract(); case ANALYSIS -> row.analysis(); case OBSERVATIONS -> row.observations();
            };
            need(row.status() == Status.AVAILABLE && value.isPresent(), "actual catalog key lost its available original object component");
            result.put(key, value.orElseThrow());
        }
        return immutable(result);
    }

    private static KnowledgeRow knowledge(String build, String executable, String key, ObjectValue row) {
        fields(row, KNOWLEDGE_FIELDS); equalText(row, "schema", KNOWLEDGE_SCHEMA); version(row);
        equalText(row, "ck3_build", build); equalText(row, "ck3_exe_sha256", executable);
        equalText(row, "event_definition_key", key);
        String status = text(row.get("status"));
        need(status.equals("available") || status.equals("unavailable"), "closed original knowledge status required");
        Optional<ObjectValue> contract = nullableObject(row.get("contract"));
        Optional<ObjectValue> analysis = nullableObject(row.get("analysis"));
        Optional<ObjectValue> observations = nullableObject(row.get("observations"));
        if (status.equals("available"))
            need(contract.isPresent() && row.get("unavailable_reason") instanceof NullValue,
                    "available original knowledge requires its complete contract and explicit null reason");
        else need(contract.isEmpty() && !text(row.get("unavailable_reason")).isEmpty(),
                "unavailable original knowledge retains explicit null contract and actual reason");
        return new KnowledgeRow(status.equals("available") ? Status.AVAILABLE : Status.UNAVAILABLE,
                row, contract, analysis, observations);
    }

    private static VanillaEventCatalog.MigrationReference reference(ObjectValue row, VanillaEventCatalog.Catalog catalog) {
        fields(row, Set.of("catalog_counts", "discovery_dataset_sha256"));
        ObjectValue counts = object(row.get("catalog_counts")); fields(counts, Set.of("contracts", "analysis", "observations"));
        int contracts = boundedInteger(counts.get("contracts"), 0, MAXIMUM_ROWS);
        int analysis = boundedInteger(counts.get("analysis"), 0, MAXIMUM_ROWS);
        int observations = boundedInteger(counts.get("observations"), 0, MAXIMUM_ROWS);
        need(contracts == catalog.contracts().size() && analysis == catalog.analysis().size()
                && observations == catalog.observations().size(), "actual original producer catalog counts differ");
        String digest = text(row.get("discovery_dataset_sha256"));
        need(digest.matches("[A-F0-9]{64}"), "canonical original discovery SHA256 required");
        return new VanillaEventCatalog.MigrationReference(contracts, analysis, observations, digest);
    }

    private static VanillaEventCatalog.TextRules textRules(ObjectValue row) {
        fields(row, Set.of("unicode_version", "casefold", "whitespace"));
        String version = text(row.get("unicode_version")); need(version.matches("[0-9]+\\.[0-9]+\\.[0-9]+"), "explicit producer Unicode version required");
        ObjectValue mappings = object(row.get("casefold"));
        need(!mappings.fields().isEmpty() && mappings.fields().size() <= 100_000, "bounded complete nonidentity Unicode mapping required");
        Map<Integer, String> fold = new LinkedHashMap<>();
        for (var mapping : mappings.fields().entrySet()) {
            int point = codepoint(mapping.getKey()); String value = text(mapping.getValue());
            need(!value.equals(new String(Character.toChars(point))) && value.length() <= 1024,
                    "casefold map contains an identity or unbounded expansion");
            need(fold.putIfAbsent(point, value) == null, "duplicate normalized codepoint");
        }
        ArrayValue whitespace = array(row.get("whitespace"));
        need(!whitespace.values().isEmpty() && whitespace.values().size() <= 1024, "bounded original whitespace table required");
        Set<Integer> spaces = new LinkedHashSet<>();
        for (Value value : whitespace.values()) need(spaces.add(codepoint(text(value))), "duplicate whitespace codepoint");
        return new VanillaEventCatalog.TextRules(version, fold, spaces);
    }

    static ObjectValue unavailable(String build, String executable, String key, String reason) {
        Map<String, Value> row = new LinkedHashMap<>();
        row.put("schema", new StringValue(KNOWLEDGE_SCHEMA)); row.put("schema_version", new IntegerValue(BigInteger.ONE));
        row.put("status", new StringValue("unavailable")); row.put("event_definition_key", RetainedJson.value(key));
        row.put("ck3_build", RetainedJson.value(build)); row.put("ck3_exe_sha256", RetainedJson.value(executable));
        row.put("contract", RetainedJson.NULL); row.put("analysis", RetainedJson.NULL); row.put("observations", RetainedJson.NULL);
        row.put("unavailable_reason", new StringValue(reason));
        return new ObjectValue(row);
    }

    private static List<String> keys(Value value, VanillaEventCatalog.TextRules rules) {
        ArrayValue rows = array(value); need(rows.values().size() <= MAXIMUM_ROWS, "bounded actual catalog keyset required");
        List<String> result = new ArrayList<>(); Set<String> unique = new HashSet<>();
        for (Value row : rows.values()) {
            String key = text(row); key(key, rules); need(unique.add(key), "duplicate actual catalog key"); result.add(key);
        }
        return List.copyOf(result);
    }
    private static void key(String value, VanillaEventCatalog.TextRules rules) {
        need(!rules.strip(value).isEmpty(), "nonblank original event definition key required");
    }
    private static Optional<ObjectValue> nullableObject(Value value) {
        need(value != null, "required nullable field is absent");
        return value instanceof NullValue ? Optional.empty() : Optional.of(object(value));
    }
    private static int codepoint(String value) {
        need(value.matches("0|[1-9][0-9]{0,6}"), "canonical decimal Unicode codepoint required");
        int point = Integer.parseInt(value);
        need(Character.isValidCodePoint(point) && !(point >= 0xD800 && point <= 0xDFFF), "Unicode scalar codepoint required");
        return point;
    }
    private static int boundedInteger(Value value, int minimum, int maximum) {
        BigInteger exact = RetainedJson.integer(value); need(exact != null && exact.compareTo(BigInteger.valueOf(minimum)) >= 0
                && exact.compareTo(BigInteger.valueOf(maximum)) <= 0, "bounded exact integer token required");
        return exact.intValueExact();
    }
    private static void version(ObjectValue value) { need(boundedInteger(value.get("schema_version"), 1, 1) == 1, "exact schema version required"); }
    private static String text(Value value) { String text = RetainedJson.string(value); need(text != null, "actual string token required"); return text; }
    private static ObjectValue object(Value value) { return RetainedJson.object(value); }
    private static ArrayValue array(Value value) { need(value instanceof ArrayValue, "actual JSON array required"); return (ArrayValue) value; }
    private static void fields(ObjectValue value, Set<String> fields) { need(value.fields().keySet().equals(fields), "closed complete catalog field contract required"); }
    private static void equalText(ObjectValue value, String field, String expected) { need(text(value.get(field)).equals(expected), "original catalog field differs: " + field); }
    private static void need(boolean condition, String message) { StrictJson.require(condition, message); }
    static <T> Map<String, T> immutable(Map<String, T> original) {
        Objects.requireNonNull(original); Map<String, T> result = new LinkedHashMap<>();
        original.forEach((key, value) -> result.put(Objects.requireNonNull(key), Objects.requireNonNull(value)));
        return Collections.unmodifiableMap(result);
    }
}
