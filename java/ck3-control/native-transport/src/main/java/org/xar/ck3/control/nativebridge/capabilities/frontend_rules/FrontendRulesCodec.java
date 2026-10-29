package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;

/** Strict transient JSON boundary; all public results are immutable typed domain values. */
public final class FrontendRulesCodec {
    private static final ObjectMapper JSON = new ObjectMapper();
    private FrontendRulesCodec() { }
    public static ObjectNode object(RawJson raw) {
        try { JsonNode node = JSON.readTree(raw.bytes()); require(node != null && node.isObject(), "native JSON object required"); return (ObjectNode) node; }
        catch (IOException failure) { throw new IllegalArgumentException("invalid native object", failure); }
    }
    static ObjectNode obj(JsonNode parent, String key) { JsonNode node = field(parent, key); require(node.isObject(), "object required: " + key); return (ObjectNode) node; }
    static JsonNode field(JsonNode parent, String key) { JsonNode node = parent.get(key); require(node != null, "missing field: " + key); return node; }
    static String text(JsonNode parent, String key) { JsonNode node = field(parent, key); require(node.isTextual(), "string required: " + key); return node.textValue(); }
    static boolean bool(JsonNode parent, String key) { JsonNode node = field(parent, key); require(node.isBoolean(), "boolean required: " + key); return node.booleanValue(); }
    static BigInteger integer(JsonNode parent, String key, BigInteger min, BigInteger max) {
        JsonNode node = field(parent, key); require(node.isIntegralNumber(), "integer token required: " + key); BigInteger result = node.bigIntegerValue();
        require(result.compareTo(min) >= 0 && (max == null || result.compareTo(max) <= 0), "integer outside native domain: " + key); return result;
    }
    static int count(JsonNode parent, String key, int min, int max) { return integer(parent, key, BigInteger.valueOf(min), BigInteger.valueOf(max)).intValueExact(); }
    static BigInteger u64(JsonNode parent, String key) { return integer(parent, key, BigInteger.ONE, U64_MAX); }
    static Optional<String> nullableText(JsonNode parent, String key) { JsonNode node = field(parent, key); if (node.isNull()) return Optional.empty(); require(node.isTextual(), "null or text required: " + key); return Optional.of(node.textValue()); }
    static void exact(JsonNode node, Set<String> names) { require(node.isObject(), "exact object required"); Set<String> actual = new HashSet<>(); node.fieldNames().forEachRemaining(actual::add); require(actual.equals(names), "closed native object fields changed"); }
    static void equalText(JsonNode node, String key, String expected) { require(text(node, key).equals(expected), "native source field drift: " + key); }
    static void expectedBool(JsonNode node, String key, boolean expected) { require(bool(node, key) == expected, "native boolean field drift: " + key); }
    static void schema(JsonNode node, String schema) { equalText(node, "schema", schema); require(count(node, "schema_version", 1, 1) == 1, "schema version drift"); }
    private static boolean contains(JsonNode node, String key, String wanted) {
        JsonNode values = node.get(key); if (values == null || !values.isArray()) return false;
        for (JsonNode value : values) if (value.isTextual() && value.textValue().equals(wanted)) return true;
        return false;
    }
    /** Original capabilities producer binding, including nested aggregate backends. No snapshot is required. */
    public static Source frontendSource(RawJson capabilities) {
        List<Source> candidates = new ArrayList<>(); visit(object(capabilities), candidates);
        Set<Source> unique = Set.copyOf(candidates); require(unique.size() == 1, "frontend requires one exact native process/connection/build"); return unique.iterator().next();
    }
    private static void visit(JsonNode row, List<Source> candidates) {
        if (!row.isObject()) return;
        if ("native-headless".equals(row.path("backend_id").asText()) && "native-headless".equals(row.path("mode").asText())
                && "injected-dll-named-pipe".equals(row.path("source").asText()) && row.path("visual_fallback").isBoolean() && !row.path("visual_fallback").booleanValue()
                && contains(row, "bridge_capabilities", "game.command.query-frontend-gui-route-v1") && row.path("diagnostics").isObject()) {
            JsonNode diagnostics = obj(row, "diagnostics"), hello = obj(diagnostics, "hello"); expectedBool(diagnostics, "connected", true);
            long pid = integer(diagnostics, "bridge_pid", BigInteger.ONE, BigInteger.valueOf(0xffff_ffffL)).longValueExact(); BigInteger generation = u64(diagnostics, "connection_generation");
            require(integer(hello, "pid", BigInteger.ONE, BigInteger.valueOf(0xffff_ffffL)).longValueExact() == pid && u64(hello, "connection_generation").equals(generation), "hello process/connection drift");
            Build build = Build.require(text(hello, "expected_ck3_version"), text(hello, "expected_ck3_sha256")); build.requireFrontend();
            // The original tuple uses the exact uppercase hash; it does not grant a new build via normalization.
            equalText(hello, "expected_ck3_sha256", build.sha256()); equalText(hello, "game_adapter_id", build.adapterId());
            equalText(hello, "game_adapter_status", "ready"); expectedBool(hello, "ck3_build_match", true);
            require(contains(hello, "capabilities", "game.command.query-frontend-gui-route-v1"), "original hello lacks frontend route capability");
            candidates.add(new Source(new Binding(pid, generation), build));
        }
        JsonNode backends = row.get("backends"); if (backends != null && backends.isArray()) for (JsonNode backend : backends) visit(backend, candidates);
    }
    public static ObservedRoute route(RawJson raw, Source source, BigInteger sequence) {
        ObjectNode value = object(raw); equalText(value, "step", "query-frontend-gui-route-v1"); expectedBool(value, "accepted", true);
        return new ObservedRoute(Route.require(text(value, "status")), source, sequence);
    }
    private static Build rulesCommon(ObjectNode value, Source source, String schema, String nativeSource, boolean readOnly, boolean applied) {
        schema(value, schema); Build build = Build.require(text(value, "game_version"), text(value, "executable_sha256")); build.requireRules();
        require(build == source.build(), "rules result came from another executable"); equalText(value, "executable_sha256", build.sha256());
        equalText(value, "source", nativeSource); nativeBackend(value); expectedBool(value, "read_only", readOnly);
        for (String key : List.of("uses_ocr", "uses_mouse", "uses_keyboard")) expectedBool(value, key, false);
        expectedBool(value, "applied_settings_proven", applied); return build;
    }
    private static String reason(ObjectNode value, boolean ready) {
        String reason = text(value, "unavailable_reason"); require(reason.isEmpty() || reason.matches("[a-z0-9_]{1,128}"), "invalid native reason");
        require(ready == reason.isEmpty(), "native readiness/reason disagreement"); return reason;
    }
    public static RuleSelections selections(RawJson raw, Source source, BigInteger sequence, boolean actualInstance) {
        ObjectNode value = object(raw); boolean ready = bool(value, "ready");
        rulesCommon(value, source, actualInstance ? "frontend_applied_game_rules_v1" : "frontend_game_rule_selections_v1",
                actualInstance ? "CGameRuleInstance.selected_settings" : "CJominiGameRulesGui.current_selections", true, actualInstance && ready);
        String reason = text(value, "unavailable_reason"); int count = count(value, "selection_count", 0, 4096); JsonNode rows = field(value, "selections");
        require(rows.isArray() && rows.size() == count, "rule selection count differs from full vector"); List<Selection> selections = new ArrayList<>();
        for (JsonNode row : rows) { exact(row, Set.of("rule_key", "selected_setting_key")); selections.add(new Selection(new ScriptKey(text(row, "rule_key")), new ScriptKey(text(row, "selected_setting_key")))); }
        return new RuleSelections(source, sequence, ready, reason, selections, actualInstance && ready);
    }
    public static RuleWindow window(RawJson raw, Source source, BigInteger sequence) {
        ObjectNode value = object(raw); rulesCommon(value, source, "frontend_game_rules_window_v1", "CJominiGameRulesGui.owner_root_and_stock_predicates", true, false);
        boolean ready = bool(value, "ready"); String reason = reason(value, ready);
        return new RuleWindow(source, sequence, ready, reason, bool(value, "window_visible"), bool(value, "window_enabled"), bool(value, "is_host"), bool(value, "game_has_started"), bool(value, "may_edit"), bool(value, "window_closed_proven"));
    }
    public static RulesAck rulesAck(RawJson raw, Source source, RulesAction action) {
        ObjectNode value = object(raw); Build build = rulesCommon(value, source, "frontend_game_rules_mutation_v1", "CJominiGameRulesGui.stock_methods", false, false);
        equalText(value, "action", action.wire()); expectedBool(value, "window_closed_proven", false); boolean ready = bool(value, "ready");
        return new RulesAck(action, build, ready, reason(value, ready), bool(value, "native_invoked"), bool(value, "selection_verified"), bool(value, "apply_invoked"), bool(value, "hide_invoked"), count(value, "native_next_calls", 0, 511));
    }
    public static GuiTree tree(RawJson raw, Source source, BigInteger sequence) {
        ObjectNode value = object(raw); equalText(value, "step", "inspect-frontend-gui-tree-v1"); expectedBool(value, "accepted", true);
        String status = text(value, "status"); require(status.equals("available") || status.equals("unavailable"), "tree availability unknown");
        boolean available = bool(value, "root_available"); require(status.equals("available") == available, "tree status/root contradiction");
        int count = count(value, "widget_count", 0, 2048); JsonNode rows = field(value, "widgets"); require(rows.isArray() && rows.size() == count, "tree count/vector mismatch");
        List<Widget> widgets = new ArrayList<>();
        for (JsonNode row : rows) widgets.add(new Widget(text(row, "runtime_name"), text(row, "child_path"), count(row, "depth", 0, 64), count(row, "child_count", 0, 4096), integer(row, "vtable_rva", BigInteger.ZERO, U64_MAX), bool(row, "effective_visible"), bool(row, "enabled")));
        return new GuiTree(source, sequence, text(value, "scope_root_name"), available, bool(value, "truncated"), widgets);
    }
    public static BookmarkModel bookmarkModel(RawJson raw, Source source, BigInteger sequence) {
        ObjectNode value = object(raw); JsonNode rows = field(value, "candidate_keys"); require(rows.isArray() && rows.size() <= 4096, "bounded bookmark keys required");
        List<String> keys = new ArrayList<>(); for (JsonNode row : rows) { require(row.isTextual(), "bookmark candidate key must be text"); keys.add(row.textValue()); }
        // selected_date_raw is the native qword diagnostic. Semantic campaign date is signed low32.
        return new BookmarkModel(source, sequence, bool(value, "accepted"), text(value, "status"), bool(value, "candidate_identity_ready"), nullableText(value, "selected_bookmark_group_key"), nullableText(value, "selected_bookmark_key"),
                integer(value, "selected_date_raw", BigInteger.valueOf(Long.MIN_VALUE), U64_MAX), count(value, "selected_date_low_raw", Integer.MIN_VALUE, Integer.MAX_VALUE), keys,
                count(value, "supported_1066_candidate_index", -1, 4095), count(value, "selected_character_index", -1, 4095), nullableText(value, "supported_1066_government_key"), bool(value, "supported_1066_feudal"), bool(value, "supported_1066_date_matches"));
    }
    public static NativeAck nativeAck(RawJson raw, String step) {
        ObjectNode value = object(raw); equalText(value, "step", step); expectedBool(value, "accepted", true);
        nativeBackend(value); return new NativeAck(step, "native-headless", text(value, "status"));
    }
    static void nativeBackend(JsonNode value) { if (value.has("backend_id")) equalText(value, "backend_id", "native-headless"); }
}
