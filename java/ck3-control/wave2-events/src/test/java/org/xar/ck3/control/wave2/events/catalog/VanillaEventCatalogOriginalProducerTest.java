package org.xar.ck3.control.wave2.events.catalog;

import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.junit.jupiter.api.Assertions.*;

/** Actual existing producer -> complete Java resource -> all public query/catalog/Unicode accessors. No Game or fallback. */
final class VanillaEventCatalogOriginalProducerTest {
    private static final int MAXIMUM_ORACLE_BYTES = 64 << 20;
    private static final RetainedJson.CanonicalBudget CANONICAL = new RetainedJson.CanonicalBudget(64L << 20, 4_000_000, 128);
    private record QueryCase(String build, String key) { }

    @Test void completeQueryRowsAndActualCatalogsMatchTheRealExistingPythonProducer() throws Exception {
        VanillaEventCatalog actual = VanillaEventCatalog.load();
        List<QueryCase> cases = new ArrayList<>();
        for (String build : actual.supportedBuilds())
            for (String key : actual.queryKeys(build)) cases.add(new QueryCase(build, key));
        for (String build : actual.supportedBuilds())
            for (String key : Arrays.asList("", "\u00a0\u001c ", "not_a_registered_event.987654321", " health.1015 ", null))
                cases.add(new QueryCase(build, key));
        cases.add(new QueryCase("unsupported-test-build", "health.1015"));
        cases.add(new QueryCase(null, "health.1015"));
        ObjectValue original = original(actual, cases);
        var originalKeys = assertInstanceOf(ArrayValue.class, original.get("query_keys")).values().stream().map(RetainedJson::string).toList();
        for (String build : actual.supportedBuilds())
            assertEquals(java.util.Set.copyOf(originalKeys), actual.queryKeys(build), "complete original provider query universe");
        ArrayValue rows = assertInstanceOf(ArrayValue.class, original.get("queries"));
        assertEquals(cases.size(), rows.values().size());
        for (int index = 0; index < cases.size(); index++) {
            QueryCase query = cases.get(index); ObjectValue expected = RetainedJson.object(rows.values().get(index));
            ObjectValue observed = actual.fullQuery(query.build(), query.key());
            assertEquals(expected, observed, "complete original query row: " + query);
            requireObservableOrder(expected, observed, query.toString());
            assertEquals(RetainedJson.pythonCanonical(expected, CANONICAL).sha256(),
                    RetainedJson.pythonCanonical(observed, CANONICAL).sha256(), "complete canonical record content: " + query);
        }
        ObjectValue catalogs = RetainedJson.object(original.get("catalogs"));
        for (String build : actual.supportedBuilds()) {
            ObjectValue expected = RetainedJson.object(catalogs.get(build)); var observed = actual.catalog(build);
            compareTable(RetainedJson.object(expected.get("contracts")), observed.contracts(), build + "/contracts");
            compareTable(RetainedJson.object(expected.get("analysis")), observed.analysis(), build + "/analysis");
            compareTable(RetainedJson.object(expected.get("observations")), observed.observations(), build + "/observations");
        }
        ObjectValue ruleRows = RetainedJson.object(original.get("text_rules"));
        assertEquals(actual.textRules().unicodeVersion(), RetainedJson.string(ruleRows.get("unicode_version")));
        ObjectValue casefold = RetainedJson.object(ruleRows.get("casefold"));
        assertEquals(actual.textRules().casefold().size(), casefold.fields().size());
        casefold.fields().forEach((point, folded) -> {
            int codepoint = Integer.parseInt(point); String expected = RetainedJson.string(folded);
            assertEquals(expected, actual.textRules().casefold().get(codepoint));
            assertEquals(expected, actual.textRules().fold(new String(Character.toChars(codepoint))));
        });
        ArrayValue whitespace = assertInstanceOf(ArrayValue.class, ruleRows.get("whitespace"));
        assertEquals(actual.textRules().whitespace().size(), whitespace.values().size());
        for (Value point : whitespace.values()) {
            int codepoint = Integer.parseInt(RetainedJson.string(point)); assertTrue(actual.textRules().whitespace().contains(codepoint));
            String space = new String(Character.toChars(codepoint)); assertEquals("value", actual.textRules().strip(space + "value" + space));
        }
    }

    @Test void actualResourcePinsRejectChangedTruncatedOrAppendedBytesBeforeConstructingAProvider() throws Exception {
        var source = VanillaEventCatalog.sourceFacts(); byte[] original;
        try (InputStream input = VanillaEventCatalog.class.getResourceAsStream(source.resource())) {
            assertNotNull(input, "NOT_RUN: actual complete catalog resource is required"); original = input.readAllBytes();
        }
        assertDoesNotThrow(() -> VanillaEventCatalog.decode(original));
        byte[] changed = original.clone(); changed[changed.length / 2] ^= 1;
        assertThrows(IllegalArgumentException.class, () -> VanillaEventCatalog.decode(changed));
        assertThrows(IllegalArgumentException.class, () -> VanillaEventCatalog.decode(Arrays.copyOf(original, original.length - 1)));
        assertThrows(IllegalArgumentException.class, () -> VanillaEventCatalog.decode(Arrays.copyOf(original, original.length + 1)));
    }

    @Test void catalogAndQueryKeysetsRemainImmutableAndDoNotInventCurrentLiveObservations() throws Exception {
        var actual = VanillaEventCatalog.load();
        assertEquals("1.19.0.6", actual.defaultBuild()); assertEquals("1.20.0.4", actual.currentBuild());
        assertThrows(UnsupportedOperationException.class, () -> actual.supportedBuilds().clear());
        for (String build : actual.supportedBuilds()) {
            var catalog = actual.catalog(build); var reference = actual.migrationReference(build);
            assertEquals(reference.contracts(), catalog.contracts().size()); assertEquals(reference.analysis(), catalog.analysis().size());
            assertEquals(reference.observations(), catalog.observations().size());
            assertTrue(actual.queryKeys(build).containsAll(catalog.contracts().keySet()));
            assertThrows(UnsupportedOperationException.class, () -> actual.queryKeys(build).clear());
            if (!build.equals(actual.defaultBuild())) assertTrue(catalog.observations().isEmpty());
        }
    }

    private static void compareTable(ObjectValue original, Map<String, ObjectValue> observed, String path) {
        assertEquals(original.fields().keySet(), observed.keySet(), path + " actual producer keyset");
        for (var row : original.fields().entrySet()) {
            assertEquals(row.getValue(), observed.get(row.getKey()), path + "/" + row.getKey());
            requireObservableOrder(row.getValue(), observed.get(row.getKey()), path + "/" + row.getKey());
        }
    }
    /** Python discovery iterates source_sha256 insertion order for cross-newline source-path searches. */
    private static void requireObservableOrder(Value expected, Value actual, String path) {
        if (expected instanceof ObjectValue left) {
            ObjectValue right = assertInstanceOf(ObjectValue.class, actual);
            for (var field : left.fields().entrySet()) {
                Value other = right.get(field.getKey());
                if (field.getKey().equals("source_sha256") && field.getValue() instanceof ObjectValue sources)
                    assertEquals(new ArrayList<>(sources.fields().keySet()),
                            new ArrayList<>(RetainedJson.object(other).fields().keySet()), path + "/source_sha256 order");
                requireObservableOrder(field.getValue(), other, path + "/" + field.getKey());
            }
        } else if (expected instanceof ArrayValue left) {
            ArrayValue right = assertInstanceOf(ArrayValue.class, actual); assertEquals(left.values().size(), right.values().size());
            for (int index = 0; index < left.values().size(); index++)
                requireObservableOrder(left.values().get(index), right.values().get(index), path + "/" + index);
        }
    }

    private static ObjectValue original(VanillaEventCatalog actual, List<QueryCase> cases) throws Exception {
        String python = required("xar.python"); Path repository = Path.of(required("xar.repository.root")).toAbsolutePath().normalize();
        assertTrue(Files.isRegularFile(repository.resolve("ck3_autonomous_player/src/xar_autoplayer/vanilla_events/registry.py")),
                "NOT_RUN: actual original registry source is required");
        List<Value> requests = new ArrayList<>();
        for (QueryCase query : cases) requests.add(new ObjectValue(Map.of("build", RetainedJson.value(query.build()), "key", RetainedJson.value(query.key()))));
        List<Value> builds = actual.supportedBuilds().stream().<Value>map(StringValue::new).toList();
        var input = new ObjectValue(Map.of("queries", new ArrayValue(requests), "builds", new ArrayValue(builds)));
        String code = """
                import importlib, json, sys, unicodedata
                from xar_autoplayer import vanilla_events as ve
                from xar_autoplayer.vanilla_events import registry as reg, discovery as dis
                from xar_autoplayer.vanilla_events.migration_1_20_0_2 import current_migrated_catalogs
                from xar_autoplayer.vanilla_events.source_index import load_vanilla_event_source_index
                from xar_autoplayer.vanilla_events.portable_evidence import portable_event_keys_v1
                request = json.load(sys.stdin)
                result = {'queries': [reg.query_vanilla_event_knowledge_v1(row['key'], row['build']) for row in request['queries']]}
                universe = set(ve.DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS)
                for build in request['builds']:
                    universe.update(load_vanilla_event_source_index(build=build)['events'])
                    reg.query_vanilla_event_knowledge_v1(next(iter(ve.DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS)), build)
                universe.update(portable_event_keys_v1())
                for module_name, module in tuple(sys.modules.items()):
                    if not module_name.startswith('xar_autoplayer.vanilla_events.records_') or module is None: continue
                    for name, value in tuple(vars(module).items()):
                        if name.endswith('_RECORDS') and isinstance(value, dict):
                            universe.update(key for key, row in value.items() if isinstance(key, str) and isinstance(row, dict) and 'contract' in row)
                        if name.endswith('_RECORD') and isinstance(value, dict) and 'contract' in value and isinstance(getattr(module, 'EVENT_KEY', None), str): universe.add(module.EVENT_KEY)
                universe.update(importlib.import_module('xar_autoplayer.vanilla_events.records_pilgrimage_travel_source_only_12004').PILGRIMAGE_TRAVEL_SOURCE_ONLY_12004)
                result['query_keys'] = sorted(universe)
                catalogs = {}
                for build in request['builds']:
                    tables = dis._default_catalogs() if build == reg.EXACT_CK3_BUILD else current_migrated_catalogs(build)
                    current = {}
                    for field, table in zip(('contracts', 'analysis', 'observations'), tables):
                        current[field] = {key: reg._clone_json(value, path=field) if field == 'contracts' else reg._metadata_copy(value, path=field) for key, value in table.items()}
                    catalogs[build] = current
                result['catalogs'] = catalogs
                fold = {}
                space = []
                for cp in range(0x110000):
                    if 0xD800 <= cp <= 0xDFFF: continue
                    value = chr(cp)
                    if value.casefold() != value: fold[str(cp)] = value.casefold()
                    if value.isspace(): space.append(str(cp))
                result['text_rules'] = {'unicode_version': unicodedata.unidata_version, 'casefold': fold, 'whitespace': space}
                json.dump(result, sys.stdout, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
                """;
        ProcessBuilder builder = new ProcessBuilder(python, "-c", code).directory(repository.toFile()).redirectErrorStream(true);
        builder.environment().put("PYTHONPATH", repository.resolve("ck3_autonomous_player/src").toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.environment().put("PYTHONIOENCODING", "utf-8");
        Process process = builder.start();
        try (var reader = Executors.newSingleThreadExecutor(Thread.ofVirtual().factory())) {
            var output = reader.submit(() -> process.getInputStream().readNBytes(MAXIMUM_ORACLE_BYTES + 1));
            try {
                try (var stdin = process.getOutputStream()) { stdin.write(RetainedJson.encode(input)); }
                assertTrue(process.waitFor(45, TimeUnit.SECONDS), "NOT_RUN/FAIL: actual original catalog producer timed out");
                byte[] raw = output.get(5, TimeUnit.SECONDS);
                assertTrue(raw.length > 0 && raw.length <= MAXIMUM_ORACLE_BYTES, "bounded actual original producer output required");
                assertEquals(0, process.exitValue(), "actual original catalog producer must succeed: "
                        + new String(raw, 0, Math.min(raw.length, 4096), java.nio.charset.StandardCharsets.UTF_8));
                return RetainedJson.object(RetainedJson.parse(raw, VanillaEventCatalogCodec.PARSE_BUDGET));
            } finally {
                if (process.isAlive()) { process.destroyForcibly(); assertTrue(process.waitFor(5, TimeUnit.SECONDS), "original producer process cleanup is unproved"); }
            }
        }
    }
    private static String required(String property) {
        String value = System.getProperty(property); assertNotNull(value, "NOT_RUN: required original producer fixture property " + property);
        assertFalse(value.isBlank(), "NOT_RUN: required original producer fixture property " + property); return value;
    }
}
