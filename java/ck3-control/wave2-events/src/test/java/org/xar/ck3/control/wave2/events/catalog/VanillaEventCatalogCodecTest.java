package org.xar.ck3.control.wave2.events.catalog;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.junit.jupiter.api.Assertions.*;

/** Strict resource DATA codec tests cannot construct the private source-pinned usable provider. */
final class VanillaEventCatalogCodecTest {
    private static final String KEY = "fixture.1";

    @Test void completeOpaqueTreesAndInsertionOrderSurviveWhileActualCatalogKeysetsStayDistinct() {
        var parsed = parse(fixture());
        for (String build : RegisteredEventKnowledge.EXE.keySet()) {
            var actual = parsed.builds().get(build);
            var original = actual.knowledge().get(KEY).original();
            assertTrue(original.contains("observations"));
            var observation = RetainedJson.object(original.get("observations"));
            assertTrue(observation.contains("not_used_by_old_policy_projection"));
            var nested = RetainedJson.object(observation.get("not_used_by_old_policy_projection"));
            assertTrue(nested.get("explicit_null") instanceof NullValue);
            assertTrue(nested.get("empty_object") instanceof ObjectValue);
            assertTrue(nested.get("empty_array") instanceof ArrayValue);
            var negative = assertInstanceOf(FloatingValue.class, nested.get("negative_zero"));
            assertEquals(Double.doubleToRawLongBits(-0.0), Double.doubleToRawLongBits(negative.value()));
            var paths = RetainedJson.object(actual.catalog().analysis().get(KEY).get("source_sha256"));
            assertEquals(List.of("events/z_last.txt", "events/a_first.txt"), new ArrayList<>(paths.fields().keySet()));
            assertEquals(build.equals("1.19.0.6") ? 1 : 0, actual.catalog().observations().size());
            assertTrue(actual.unregisteredQuery().get("analysis") instanceof ObjectValue,
                    "original unavailable metadata remains complete instead of a synthesized null projection");
            assertThrows(UnsupportedOperationException.class, () -> actual.catalog().contracts().put("extra", observation));
            assertThrows(UnsupportedOperationException.class, () -> nested.fields().put("extra", RetainedJson.NULL));
        }
    }

    @Test void requiredNullableKnowledgeFieldsCannotBeMissingAndVersionRejectsBooleanOrFloat() {
        var valid = fixture();
        var legacy = build(valid, "1.19.0.6");
        var knowledge = object(legacy.get("knowledge"));
        var row = object(knowledge.get(KEY));
        assertThrows(IllegalArgumentException.class, () -> parse(replaceBuild(valid, "1.19.0.6",
                legacy.with("knowledge", knowledge.with(KEY, without(row, "observations"))))));
        assertThrows(IllegalArgumentException.class, () -> parse(valid.with("schema_version", new BooleanValue(true))));
        assertThrows(IllegalArgumentException.class, () -> parse(valid.with("schema_version", new FloatingValue(1.0))));
        assertThrows(IllegalArgumentException.class, () -> parse(valid.with("schema_alias", new StringValue("v1"))));
        assertThrows(IllegalArgumentException.class, () -> parse(replaceBuild(valid, "1.19.0.6",
                legacy.with("knowledge", knowledge.with(KEY, row.with("analysis", new ArrayValue(List.of())))))));
        assertThrows(IllegalArgumentException.class, () -> parse(replaceBuild(valid, "1.19.0.6", without(legacy, "unregistered_query"))));
        assertThrows(IllegalArgumentException.class, () -> parse(replaceBuild(valid, "1.19.0.6", legacy.with("unregistered_query", row))));
    }

    @Test void originalUnavailableSourceOnlyKnowledgeRetainsAnalysisAndObservationsWithoutEnteringCatalog() {
        var valid = fixture();
        var legacy = build(valid, "1.19.0.6");
        var rows = object(legacy.get("knowledge"));
        var original = object(rows.get(KEY));
        var unavailable = original.with("event_definition_key", new StringValue("source.only"))
                .with("status", new StringValue("unavailable")).with("contract", RetainedJson.NULL)
                .with("unavailable_reason", new StringValue("source_analyzed_no_occurrence_contract"));
        var parsed = parse(replaceBuild(valid, "1.19.0.6", legacy.with("knowledge", rows.with("source.only", unavailable))));
        var row = parsed.builds().get("1.19.0.6").knowledge().get("source.only");
        assertEquals(VanillaEventCatalogCodec.Status.UNAVAILABLE, row.status());
        assertTrue(row.contract().isEmpty()); assertTrue(row.analysis().isPresent()); assertTrue(row.observations().isPresent());
        assertFalse(parsed.builds().get("1.19.0.6").catalog().contracts().containsKey("source.only"));
    }

    @Test void duplicateOrWrongCatalogKeysAndWrongExactExecutableAreRejected() {
        var valid = fixture(); var legacy = build(valid, "1.19.0.6"); var keys = object(legacy.get("catalog_keys"));
        assertThrows(IllegalArgumentException.class, () -> parse(replaceBuild(valid, "1.19.0.6", legacy.with("catalog_keys",
                keys.with("contracts", new ArrayValue(List.of(new StringValue(KEY), new StringValue(KEY))))))));
        assertThrows(IllegalArgumentException.class, () -> parse(replaceBuild(valid, "1.19.0.6", legacy.with("catalog_keys",
                keys.with("contracts", new ArrayValue(List.of(new StringValue("absent.1"))))))));
        assertThrows(IllegalArgumentException.class, () -> parse(replaceBuild(valid, "1.19.0.6",
                legacy.with("ck3_exe_sha256", new StringValue("0".repeat(64))))));
        var migrated = build(valid, "1.20.0.4"); var migratedKeys = object(migrated.get("catalog_keys"));
        assertThrows(IllegalArgumentException.class, () -> parse(replaceBuild(valid, "1.20.0.4", migrated.with("catalog_keys",
                migratedKeys.with("observations", new ArrayValue(List.of(new StringValue(KEY))))))));
    }

    @Test void UnicodeKeysRequireCanonicalScalarDecimalAndWhitespaceUsesOriginalExplicitTable() {
        var valid = fixture(); var rules = object(valid.get("text_rules")); var folds = object(rules.get("casefold"));
        for (String key : List.of("065", "+65", "55296", "1114112")) {
            var wrongCodepoint = folds.with(key, new StringValue("mapped"));
            assertThrows(IllegalArgumentException.class, () -> parse(valid.with("text_rules", rules.with("casefold", wrongCodepoint))));
        }
        var identity = folds.with("65", new StringValue("A"));
        assertThrows(IllegalArgumentException.class, () -> parse(valid.with("text_rules", rules.with("casefold", identity))));
        var integerWhitespace = new ArrayValue(List.of(new IntegerValue(BigInteger.valueOf(32))));
        assertThrows(IllegalArgumentException.class, () -> parse(valid.with("text_rules", rules.with("whitespace", integerWhitespace))));
        var duplicateWhitespace = new ArrayValue(List.of(new StringValue("32"), new StringValue("32")));
        assertThrows(IllegalArgumentException.class, () -> parse(valid.with("text_rules", rules.with("whitespace", duplicateWhitespace))));
        var actual = parse(valid).textRules();
        assertEquals("Ab", actual.strip("\u00a0 Ab\u00a0"));
        assertEquals("abss", actual.fold("Ab\u00df"));
        assertEquals("15.0.0", actual.unicodeVersion());
    }

    @Test void rawJsonDuplicateFieldsTrailingBytesAndMalformedUtf8AreRejectedBeforeModelConstruction() {
        byte[] original = RetainedJson.encode(fixture());
        byte[] duplicate = ("{\"schema\":\"duplicate\"," + new String(original, java.nio.charset.StandardCharsets.UTF_8).substring(1))
                .getBytes(java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> VanillaEventCatalogCodec.parse(duplicate));
        byte[] trailing = java.util.Arrays.copyOf(original, original.length + 1); trailing[trailing.length - 1] = 'x';
        assertThrows(IllegalArgumentException.class, () -> VanillaEventCatalogCodec.parse(trailing));
        assertThrows(IllegalArgumentException.class, () -> VanillaEventCatalogCodec.parse(new byte[] {'{', '"', (byte) 0xFF, '"', ':', '0', '}'}));
    }

    private static VanillaEventCatalogCodec.Document parse(ObjectValue value) { return VanillaEventCatalogCodec.parse(RetainedJson.encode(value)); }
    private static ObjectValue fixture() {
        var nested = obj("explicit_null", RetainedJson.NULL, "empty_object", obj(), "empty_array", new ArrayValue(List.of()),
                "negative_zero", new FloatingValue(-0.0), "opaque_float", new FloatingValue(1e-7));
        var observation = obj("not_used_by_old_policy_projection", nested);
        var analysis = obj("source_sha256", obj("events/z_last.txt", new StringValue("1".repeat(64)),
                "events/a_first.txt", new StringValue("2".repeat(64))), "non_consumed_analysis", nested);
        var contract = obj("opaque", nested, "options", new ArrayValue(List.of(new IntegerValue(BigInteger.ONE))));
        Map<String, Value> builds = new LinkedHashMap<>(), references = new LinkedHashMap<>();
        for (var identity : RegisteredEventKnowledge.EXE.entrySet()) {
            String build = identity.getKey(); boolean legacy = build.equals("1.19.0.6");
            var row = obj("schema", new StringValue(VanillaEventCatalogCodec.KNOWLEDGE_SCHEMA), "schema_version", new IntegerValue(BigInteger.ONE),
                    "status", new StringValue("available"), "event_definition_key", new StringValue(KEY),
                    "ck3_build", new StringValue(build), "ck3_exe_sha256", new StringValue(identity.getValue()),
                    "contract", contract, "analysis", analysis, "observations", observation, "unavailable_reason", RetainedJson.NULL);
            var one = new ArrayValue(List.of(new StringValue(KEY)));
            var unregistered = row.with("event_definition_key", new StringValue(VanillaEventCatalogCodec.UNREGISTERED_PROBE))
                    .with("status", new StringValue("unavailable")).with("contract", RetainedJson.NULL)
                    .with("unavailable_reason", new StringValue("event_definition_key_not_registered"));
            builds.put(build, obj("ck3_exe_sha256", new StringValue(identity.getValue()), "knowledge", obj(KEY, row), "unregistered_query", unregistered,
                    "catalog_keys", obj("contracts", one, "analysis", one, "observations", legacy ? one : new ArrayValue(List.of()))));
            references.put(build, obj("catalog_counts", obj("contracts", new IntegerValue(BigInteger.ONE), "analysis", new IntegerValue(BigInteger.ONE),
                    "observations", new IntegerValue(legacy ? BigInteger.ONE : BigInteger.ZERO)), "discovery_dataset_sha256", new StringValue("F".repeat(64))));
        }
        return obj("schema", new StringValue(VanillaEventCatalogCodec.SCHEMA), "schema_version", new IntegerValue(BigInteger.ONE),
                "default_build", new StringValue("1.19.0.6"), "current_build", new StringValue("1.20.0.4"),
                "builds", new ObjectValue(builds), "text_rules", obj("unicode_version", new StringValue("15.0.0"),
                        "casefold", obj("65", new StringValue("a"), "223", new StringValue("ss")),
                        "whitespace", new ArrayValue(List.of(new StringValue("32"), new StringValue("160")))),
                "migration_reference", new ObjectValue(references));
    }
    private static ObjectValue build(ObjectValue document, String build) { return object(object(document.get("builds")).get(build)); }
    private static ObjectValue replaceBuild(ObjectValue document, String build, ObjectValue replacement) {
        return document.with("builds", object(document.get("builds")).with(build, replacement));
    }
    private static ObjectValue without(ObjectValue original, String name) {
        var fields = new LinkedHashMap<>(original.fields()); fields.remove(name); return new ObjectValue(fields);
    }
    private static ObjectValue object(Value value) { return RetainedJson.object(value); }
    /** Test DATA builder has a closed alternating type domain; no production authority or provider is constructed. */
    private static ObjectValue obj(Object... fields) {
        assertEquals(0, fields.length % 2); Map<String, Value> result = new LinkedHashMap<>();
        for (int at = 0; at < fields.length; at += 2) {
            String key = assertInstanceOf(String.class, fields[at]); Value value = assertInstanceOf(Value.class, fields[at + 1]);
            assertNull(result.put(key, value), "duplicate fixture field");
        }
        return new ObjectValue(result);
    }
}
