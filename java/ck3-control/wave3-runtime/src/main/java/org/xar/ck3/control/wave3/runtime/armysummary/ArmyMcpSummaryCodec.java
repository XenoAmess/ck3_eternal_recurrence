package org.xar.ck3.control.wave3.runtime.armysummary;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Strict consumed-field projection of extensible Service payloads; no rich observations escape. */
public final class ArmyMcpSummaryCodec {
    public static final int MAX_INPUT_BYTES = StrictJson.EXPLICIT_MAX_BYTES;
    public static final int MAX_OUTPUT_BYTES = 65_536;
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final Set<String> TIMING_FIELDS = Set.of("read_total_ns", "owner_query_ns",
            "baseline_read_ns", "rich_attach_ns", "serialize_ns");
    private ArmyMcpSummaryCodec() { }

    public static ArmyMcpSummary.Query decodeQuery(byte[] bytes) { return query(StrictJson.parse(bytes, MAX_INPUT_BYTES)); }
    /** In-process Service boundary: visits only declared scalar fields, without cloning rich journals. */
    public static ArmyMcpSummary.Query fromServicePayload(ObjectNode payload) { return query(payload); }
    public static ArmyMcpSummary.AutoTurn decodeAutoTurn(byte[] bytes) {
        ObjectNode root = object(StrictJson.parse(bytes, MAX_INPUT_BYTES));
        ObjectNode plan = object(required(root, "plan"));
        return new ArmyMcpSummary.AutoTurn(text(root.get("status")), text(root.get("selected_step")),
                new ArmyMcpSummary.Plan(text(plan.get("selected_step")), text(plan.get("phase"))),
                query(required(root, "result")));
    }

    public static ObjectNode summary(ArmyMcpSummary.Query query) {
        ObjectNode out = StrictJson.object();
        out.put("accepted", query.accepted()); out.put("status", wire(query.status()));
        out.put("query_sequence", query.querySequence()); out.put("army_strengths_profile", wire(query.profile()));
        out.put("army_observed_phase_coverage", wire(query.coverage()));
        ObjectNode source = out.putObject("source"); source.put("revision", query.source().revision());
        source.put("native_revision", query.source().nativeRevision());
        switch (query.armyIds()) {
            case ArmyMcpSummary.NullArmyIds ignored -> out.putNull("army_ids");
            case ArmyMcpSummary.ExplicitArmyIds explicit -> ids(out.putArray("army_ids"), explicit.values());
            case ArmyMcpSummary.DerivedArmyIds ignored -> ids(out.putArray("army_ids"),
                    query.armies().stream().map(ArmyMcpSummary.ArmyRow::armyId).toList());
        }
        ArrayNode armies = out.putArray("armies");
        for (ArmyMcpSummary.ArmyRow row : query.armies()) {
            ObjectNode item = armies.addObject();
            item.put("status", wire(row.status())); item.put("army_id", row.armyId());
            item.put("native_carmy_id", row.nativeCarmyId()); item.put("regiment_count", row.regimentCount());
            item.put("current_soldiers", row.currentSoldiers()); item.put("maximum_soldiers", row.maximumSoldiers());
            item.put("ai_base_power_raw", row.aiBasePowerRaw()); item.put("ai_base_power_scale", row.aiBasePowerScale());
            item.put("current_supply_raw", row.currentSupplyRaw()); item.put("current_supply_scale", row.currentSupplyScale());
            item.put("current_attrition_fraction_raw", row.currentAttritionFractionRaw());
            item.put("current_attrition_fraction_scale", row.currentAttritionFractionScale());
            item.put("unavailable_reason", row.unavailableReason());
        }
        out.put("result_location", ArmyMcpSummary.RESULT_LOCATION);
        if (query.nativeTiming() != null) {
            ArmyMcpSummary.NativeTiming t = query.nativeTiming(); ObjectNode timing = out.putObject("army_native_timing_v1");
            timing.put("read_total_ns", t.readTotalNs()); timing.put("owner_query_ns", t.ownerQueryNs());
            timing.put("baseline_read_ns", t.baselineReadNs()); timing.put("rich_attach_ns", t.richAttachNs());
            timing.put("serialize_ns", t.serializeNs());
        }
        return out;
    }
    public static ObjectNode summary(ArmyMcpSummary.AutoTurn turn) {
        ObjectNode out = StrictJson.object(); out.put("status", turn.status()); out.put("selected_step", turn.selectedStep());
        ObjectNode plan = out.putObject("plan"); plan.put("selected_step", turn.plan().selectedStep());
        plan.put("phase", turn.plan().phase()); out.set("result", summary(turn.result()));
        out.put("result_location", ArmyMcpSummary.RESULT_LOCATION); return out;
    }

    /** MCP 2.0.0 complete CallToolResult wire; one summary in both channels and an explicit resultType. */
    public static byte[] encodeQueryResult(ArmyMcpSummary.Query query) { return result(summary(query)); }
    public static byte[] encodeAutoResult(ArmyMcpSummary.AutoTurn turn) { return result(summary(turn)); }
    public static byte[] projectQuery(byte[] bytes) { return encodeQueryResult(decodeQuery(bytes)); }
    public static byte[] projectAutoTurn(byte[] bytes) { return encodeAutoResult(decodeAutoTurn(bytes)); }

    private static byte[] result(ObjectNode summary) {
        ObjectNode wire = StrictJson.object(); ObjectNode text = wire.putArray("content").addObject();
        text.put("type", "text"); text.put("text", string(summary)); wire.set("structuredContent", summary);
        wire.put("isError", false); wire.put("resultType", "complete"); return bytes(wire);
    }
    private static byte[] bytes(JsonNode node) {
        try {
            byte[] bytes = JSON.writeValueAsBytes(node);
            StrictJson.require(bytes.length <= MAX_OUTPUT_BYTES, "compact MCP result exceeds bounded output"); return bytes;
        } catch (JsonProcessingException error) { throw new ContractViolationException("cannot serialize compact MCP result", error); }
    }
    private static String string(JsonNode node) { return new String(bytes(node), java.nio.charset.StandardCharsets.UTF_8); }

    private static ArmyMcpSummary.Query query(JsonNode node) {
        ObjectNode root = object(node); JsonNode rows = required(root, "army_strengths");
        StrictJson.require(rows.isArray(), "army_strengths must be an array");
        List<ArmyMcpSummary.ArmyRow> armies = new ArrayList<>();
        for (JsonNode value : rows) {
            ObjectNode row = object(value);
            armies.add(new ArmyMcpSummary.ArmyRow(rowStatus(row.get("status")), nonnegative(row.get("army_id")),
                    nonnegative(row.get("native_carmy_id")), nonnegative(row.get("regiment_count")),
                    nonnegative(row.get("current_soldiers")), nonnegative(row.get("maximum_soldiers")),
                    signed(row.get("ai_base_power_raw")), nonnegative(row.get("ai_base_power_scale")),
                    signed(row.get("current_supply_raw")), nonnegative(row.get("current_supply_scale")),
                    signed(row.get("current_attrition_fraction_raw")), nonnegative(row.get("current_attrition_fraction_scale")),
                    text(row.get("unavailable_reason"))));
        }
        // A present source object with a missing member produces null, never the queried_* fallback.
        JsonNode source = root.get("source");
        ArmyMcpSummary.SourceRevision revision = source != null && source.isObject()
                ? new ArmyMcpSummary.SourceRevision(nonnegative(source.get("revision")), nonnegative(source.get("native_revision")))
                : new ArmyMcpSummary.SourceRevision(nonnegative(root.get("queried_revision")), nonnegative(root.get("queried_native_revision")));
        ArmyMcpSummary.ArmyIds armyIds;
        if (!root.has("army_ids")) { armyIds = new ArmyMcpSummary.DerivedArmyIds(); }
        else if (root.get("army_ids").isNull()) { armyIds = new ArmyMcpSummary.NullArmyIds(); }
        else {
            StrictJson.require(root.get("army_ids").isArray(), "army_ids must be null or an array");
            List<Long> values = new ArrayList<>(); for (JsonNode value : root.get("army_ids")) { values.add(nonnegative(value)); }
            armyIds = new ArmyMcpSummary.ExplicitArmyIds(values);
        }
        return new ArmyMcpSummary.Query(bool(root.get("accepted")), queryStatus(root.get("status")),
                nonnegative(root.get("query_sequence")), profile(root.get("army_strengths_profile")),
                coverage(root.get("army_observed_phase_coverage")), revision, armyIds, armies,
                timing(root.get("army_native_timing_v1")));
    }
    /** Malformed optional diagnostics do not replace or reject the independent business result. */
    private static ArmyMcpSummary.NativeTiming timing(JsonNode node) {
        if (node == null || !node.isObject()) { return null; }
        try {
            ObjectNode value = StrictJson.object(node, TIMING_FIELDS);
            return new ArmyMcpSummary.NativeTiming(requiredLong(value, "read_total_ns"), requiredLong(value, "owner_query_ns"),
                    requiredLong(value, "baseline_read_ns"), requiredLong(value, "rich_attach_ns"), requiredLong(value, "serialize_ns"));
        } catch (ContractViolationException malformedDiagnostic) { return null; }
    }
    private static long requiredLong(ObjectNode node, String field) {
        return StrictJson.integer(required(node, field), 0, StrictJson.MAX_SAFE_INTEGER);
    }
    private static Boolean bool(JsonNode node) {
        if (absent(node)) { return null; } StrictJson.require(node.isBoolean(), "exact boolean required"); return node.booleanValue();
    }
    private static Long nonnegative(JsonNode node) {
        return absent(node) ? null : StrictJson.integer(node, 0, StrictJson.MAX_SAFE_INTEGER);
    }
    private static Long signed(JsonNode node) {
        return absent(node) ? null : StrictJson.integer(node, -StrictJson.MAX_SAFE_INTEGER, StrictJson.MAX_SAFE_INTEGER);
    }
    private static String text(JsonNode node) {
        if (absent(node)) { return null; } StrictJson.require(node.isTextual(), "exact string required");
        String result = node.textValue(); ArmyMcpSummary.nullableText(result); return result;
    }
    private static boolean absent(JsonNode node) { return node == null || node.isNull(); }
    private static JsonNode required(ObjectNode node, String field) {
        StrictJson.require(node.has(field), "required Army summary field missing: " + field); return node.get(field);
    }
    private static ObjectNode object(JsonNode node) {
        StrictJson.require(node instanceof ObjectNode, "Army summary object required"); return (ObjectNode) node;
    }
    private static <E extends Enum<E>> E choice(JsonNode node, E[] values, Function<E, String> wire) {
        String value = text(node); if (value == null) { return null; }
        for (E item : values) { if (wire.apply(item).equals(value)) { return item; } }
        throw new ContractViolationException("unsupported Army summary enum: " + value);
    }
    private static ArmyMcpSummary.QueryStatus queryStatus(JsonNode node) {
        return choice(node, ArmyMcpSummary.QueryStatus.values(), ArmyMcpSummary.QueryStatus::wire);
    }
    private static ArmyMcpSummary.RowStatus rowStatus(JsonNode node) {
        return choice(node, ArmyMcpSummary.RowStatus.values(), ArmyMcpSummary.RowStatus::wire);
    }
    private static ArmyMcpSummary.Profile profile(JsonNode node) {
        return choice(node, ArmyMcpSummary.Profile.values(), ArmyMcpSummary.Profile::wire);
    }
    private static ArmyMcpSummary.Coverage coverage(JsonNode node) {
        return choice(node, ArmyMcpSummary.Coverage.values(), ArmyMcpSummary.Coverage::wire);
    }
    private static String wire(ArmyMcpSummary.QueryStatus value) { return value == null ? null : value.wire(); }
    private static String wire(ArmyMcpSummary.RowStatus value) { return value == null ? null : value.wire(); }
    private static String wire(ArmyMcpSummary.Profile value) { return value == null ? null : value.wire(); }
    private static String wire(ArmyMcpSummary.Coverage value) { return value == null ? null : value.wire(); }
    private static void ids(ArrayNode out, List<Long> values) { for (Long value : values) { out.add(value); } }
}
