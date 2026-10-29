package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.wave2.military.combatwire.CombatRequest;
import org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputsCodec;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Original public presentation only. Domain encoders own full-width identity serialization. */
public final class OriginalMcpPresenters {
    public enum Entry { ARMY_QUERY, EXECUTE_STEP, AUTO_TURN }
    private static final String ARMY = "query-army-strengths-v1";
    private static final String MARKET = "query-player-mercenary-context-v1";
    private static final List<String> ARMY_FIELDS = List.of("status", "army_id", "native_carmy_id", "regiment_count",
            "current_soldiers", "maximum_soldiers", "ai_base_power_raw", "ai_base_power_scale", "current_supply_raw",
            "current_supply_scale", "current_attrition_fraction_raw", "current_attrition_fraction_scale", "unavailable_reason");
    private static final List<String> TIMING = List.of("read_total_ns", "owner_query_ns", "baseline_read_ns", "rich_attach_ns", "serialize_ns");
    private OriginalMcpPresenters() { }

    /** The actual original call is retained because execute_step chooses presentation from its request. */
    public static CallResult present(Entry entry, Arguments arguments, RawJson encodedPublicResult) {
        ObjectNode payload = McpJson.object(McpJson.parse(encodedPublicResult.bytes()));
        McpJson.publicNumbers(payload);
        return switch (entry) {
            case ARMY_QUERY -> compact(armySummary(payload));
            case EXECUTE_STEP -> ARMY.equals(McpJson.text(McpJson.object(McpJson.parse(arguments.objectOrEmpty().bytes())).get("step")))
                    ? compact(armySummary(payload)) : CallResult.fromBusinessJson(encodedPublicResult);
            case AUTO_TURN -> auto(payload, encodedPublicResult);
        };
    }
    private static CallResult envelopeOriginal(String text,ObjectNode structured,boolean error,RawJson original,List<String> retainedPath) {
        JsonNode retained=structured;
        for(String key:retainedPath)retained=retained==null?null:retained.get(key);
        McpJson.require(McpJson.object(McpJson.parse(original.bytes())).equals(retained),
                "retained AUTO original turn differs from actual producer");
        byte[] encoded=envelopeBytes(text,structured,error);
        var path=new java.util.ArrayList<String>();path.add("structuredContent");path.addAll(retainedPath);
        return new CallResult(replaceOriginal(encoded,List.copyOf(path),original.bytes()));
    }
    /** Only these source-owned presentation paths carry a retained complete original turn. */
    private static byte[] replaceOriginal(byte[] enclosing,List<String> path,byte[] original) {
        if(path.size()==1)return McpJson.member(enclosing,path.getFirst(),original);
        byte[] child=McpJson.token(enclosing,path.getFirst());
        return McpJson.member(enclosing,path.getFirst(),replaceOriginal(child,path.subList(1,path.size()),original));
    }
    private static CallResult auto(ObjectNode payload, RawJson original) {
        JsonNode result = payload.get("result"), plan = payload.get("plan");
        JsonNode persistence = result != null && result.isObject() ? result.get("driver_state_persistence_diagnostic") : null;
        if (is(result, "step", "continue-as-reconciled-successor") && yes(result, "accepted") && is(result, "status", "continued")
                && is(persistence, "status", "failed")) {
            ObjectNode retained = McpJson.object().put("logical_transition_state", "applied").put("durability_status", "unconfirmed");
            retained.set("persistence_attempt", persistence.deepCopy()); retained.set("original_turn", payload.deepCopy());
            ObjectNode diagnostics = McpJson.object(); diagnostics.set("natural_succession_driver_state_persistence_v1", retained);
            return diagnostic("Error executing tool ck3_auto_turn: natural continuation already applied; driver-state persistence attempt failed; durability unconfirmed; do not resend Continue",
                    "NaturalSuccessorPersistenceAttemptFailed", diagnostics,original,"natural_succession_driver_state_persistence_v1");
        }
        JsonNode obligation = payload.get("successor_ui_obligation_v1");
        if (is(obligation, "status", "handoff_unverified")) {
            ObjectNode retained = McpJson.object(); retained.set("obligation", obligation.deepCopy()); retained.set("original_turn", payload.deepCopy());
            ObjectNode diagnostics = McpJson.object(); diagnostics.set("successor_ui_obligation_v1", retained);
            return diagnostic("Natural Continue result retained; successor UI handoff is unverified; collect the original result, do not resend Continue",
                    "NaturalSuccessorUIRetentionUnverified", diagnostics,original,"successor_ui_obligation_v1");
        }
        if (is(plan, "selected_step", ARMY) && is(result, "step", ARMY) && array(result, "army_strengths")) {
            ObjectNode summary = McpJson.object(); copy(summary, payload, "status", "selected_step");
            ObjectNode selectedPlan = McpJson.object(); copy(selectedPlan, plan, "selected_step", "phase"); summary.set("plan", selectedPlan);
            summary.set("result", armySummary(McpJson.object(result))); summary.put("result_location", "compact_mcp_summary"); return compact(summary);
        }
        if (!is(payload, "status", "executed") || !object(result) || !object(plan)) return CallResult.fromBusinessJson(original);
        JsonNode selected = payload.get("selected_step");
        if (selected == null || !selected.isTextual() || !is(plan, "selected_step", selected.textValue()) || !is(result, "step", selected.textValue())
                || !yes(result, "accepted")) return CallResult.fromBusinessJson(original);
        String step = selected.textValue();
        JsonNode market = result.get("player_mercenary_context");
        if (MARKET.equals(step) && is(result, "backend_id", "native-headless") && is(result, "status", "completed")
                && yes(result, "read_only") && yes(market, "available") && yes(market, "read_only") && array(market, "rows")) {
            ObjectNode summary = fullSummary("xar.mercenary-query-auto-mcp-summary.v1", payload, step);
            copyAs(summary, "query_status", result, "status"); copy(summary, result, "query_sequence", "snapshot_revision", "date_raw");
            copy(summary, market, "actor_character_id", "capture_epoch"); summary.put("company_row_count", market.get("rows").size());
            summary.put("market_available", true).put("read_only", true); return summarizedOriginal(summary,payload,original);
        }
        if (!object(result.get("combat_simulation_inputs"))) return CallResult.fromBusinessJson(original);
        final int version;
        if (CombatRequest.parseStep(step).isPresent()) {
            if (!is(result, "status", "available") && !is(result, "status", "partial")) return CallResult.fromBusinessJson(original);
            version = 2;
        } else if (CombatPhaseInputsCodec.parseStep(step).isPresent()) {
            if (!is(result, "status", "available") && !is(result, "status", "unavailable")) return CallResult.fromBusinessJson(original);
            version = 3;
        } else return CallResult.fromBusinessJson(original);
        ObjectNode summary = fullSummary("xar.combat-query-auto-mcp-summary.v1", payload, step).put("query_version", version);
        copyAs(summary, "query_status", result, "status"); copy(summary, result, "query_sequence", "queried_snapshot_id", "queried_revision", "queried_native_revision");
        return summarizedOriginal(summary,payload,original);
    }
    private static ObjectNode armySummary(ObjectNode payload) {
        McpJson.require(array(payload, "army_strengths"), "original Army result requires an army_strengths array");
        ObjectNode summary = McpJson.object(); copy(summary, payload, "accepted", "status", "query_sequence", "army_strengths_profile", "army_observed_phase_coverage");
        ObjectNode source = McpJson.object(); JsonNode actualSource = payload.get("source");
        if (object(actualSource)) copy(source, actualSource, "revision", "native_revision");
        else { copyAs(source, "revision", payload, "queried_revision"); copyAs(source, "native_revision", payload, "queried_native_revision"); }
        summary.set("source", source); ArrayNode ids = summary.putArray("army_ids"), armies = summary.putArray("armies");
        for (JsonNode row : payload.get("army_strengths")) {
            McpJson.object(row); ObjectNode retained = McpJson.object(); copy(retained, row, ARMY_FIELDS.toArray(String[]::new)); armies.add(retained);
            if (row.has("army_id")) ids.add(row.get("army_id").deepCopy()); else ids.addNull();
        }
        if (payload.has("army_ids")) summary.set("army_ids", payload.get("army_ids").deepCopy());
        summary.put("result_location", "compact_mcp_summary");
        JsonNode timing = payload.get("army_native_timing_v1");
        if (validTiming(timing)) { ObjectNode retained = McpJson.object(); copy(retained, timing, TIMING.toArray(String[]::new)); summary.set("army_native_timing_v1", retained); }
        return summary;
    }
    private static boolean validTiming(JsonNode timing) {
        if (!object(timing) || timing.size() != TIMING.size()) return false;
        for (String field : TIMING) if (!timing.has(field) || !timing.get(field).isIntegralNumber() || timing.get(field).bigIntegerValue().signum() < 0) return false;
        BigInteger owner = timing.get("owner_query_ns").bigIntegerValue();
        return timing.get("baseline_read_ns").bigIntegerValue().max(timing.get("rich_attach_ns").bigIntegerValue()).compareTo(owner) <= 0
                && owner.compareTo(timing.get("read_total_ns").bigIntegerValue()) <= 0;
    }
    private static ObjectNode fullSummary(String schema, ObjectNode payload, String step) {
        ObjectNode out = McpJson.object().put("schema", schema).put("full_result_location", "structuredContent").put("text_contains_full_result", false);
        copy(out, payload, "status"); return out.put("selected_step", step);
    }
    private static CallResult diagnostic(String text, String type, ObjectNode diagnostics,RawJson original,String retainedKey) {
        ObjectNode structured = McpJson.object().put("error_type", type); structured.set("diagnostics", diagnostics); return envelopeOriginal(text,structured,true,original,List.of("diagnostics",retainedKey,"original_turn"));
    }
    private static CallResult compact(ObjectNode summary) { return summarized(summary, summary, false); }
    private static CallResult summarizedOriginal(ObjectNode summary,ObjectNode structured,RawJson original) {
        return envelopeOriginal(new String(McpJson.encode(summary),StandardCharsets.UTF_8),structured,false,original,List.of());
    }
    private static CallResult summarized(ObjectNode summary, ObjectNode structured, boolean error) {
        return envelope(new String(McpJson.encode(summary), StandardCharsets.UTF_8), structured, error);
    }
    private static CallResult envelope(String text, ObjectNode structured, boolean error) {
        return new CallResult(envelopeBytes(text,structured,error));
    }
    private static byte[] envelopeBytes(String text,ObjectNode structured,boolean error) {
        ObjectNode envelope = McpJson.object(); envelope.putArray("content").addObject().put("type", "text").put("text", text);
        envelope.set("structuredContent", structured.deepCopy()); envelope.put("isError", error).put("resultType", "complete"); return McpJson.encode(envelope);
    }
    private static boolean object(JsonNode value) { return value != null && value.isObject(); }
    private static boolean array(JsonNode value, String field) { return object(value) && value.has(field) && value.get(field).isArray(); }
    private static boolean is(JsonNode value, String field, String expected) { return object(value) && value.has(field) && value.get(field).isTextual() && expected.equals(value.get(field).textValue()); }
    private static boolean yes(JsonNode value, String field) { return object(value) && value.has(field) && value.get(field).isBoolean() && value.get(field).booleanValue(); }
    private static void copy(ObjectNode to, JsonNode from, String... fields) { for (String field : fields) copyAs(to, field, from, field); }
    private static void copyAs(ObjectNode to, String key, JsonNode from, String field) { if (from.has(field)) to.set(key, from.get(field).deepCopy()); else to.putNull(key); }
}
