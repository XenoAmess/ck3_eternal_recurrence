package org.xar.ck3.control.wave3.military.siegecontribution;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.military.siegecontribution.SiegeContributionPolicy.Decision;
import org.xar.ck3.control.wave3.military.siegecontribution.SiegeContributionPolicy.Occurrence;
import org.xar.ck3.control.wave3.military.siegecontribution.SiegeContributionPolicy.Province;
import org.xar.ck3.control.wave3.military.siegecontribution.SiegeContributionPolicy.Request;
import org.xar.ck3.control.wave3.military.siegecontribution.SiegeContributionPolicy.Selection;
import org.xar.ck3.control.wave3.military.siegecontribution.SiegeContributionPolicy.Subject;

/** Strict canonical native occurrence/selection contracts around an explicit SDK province/army projection. */
public final class SiegeContributionCodec {
    private SiegeContributionCodec() { }
    public static byte[] evaluate(byte[] raw) { return encodeDecision(SiegeContributionPolicy.observe(decode(raw))); }
    public static Request decode(byte[] raw) { return decodeNode(StrictJson.parse(raw)); }
    public static Request decodeNode(JsonNode node) {
        ObjectNode wrapper = StrictJson.object(node, Set.of("schema", "province", "subject"));
        StrictJson.require(SiegeContributionPolicy.INPUT_SCHEMA.equals(StrictJson.text(wrapper.get("schema"))), "unsupported contribution schema");
        ObjectNode province = projection(wrapper.get("province")); Selection selection = selection(province.get("current_besieging_army_selection"));
        List<Occurrence> occurrences = null;
        if (present(province.get("active_siege"))) {
            ObjectNode siege = projection(province.get("active_siege"));
            if (present(siege.get("province_unit_occurrences"))) {
                occurrences = new ArrayList<>();
                for (JsonNode item : array(siege.get("province_unit_occurrences"))) {
                    ObjectNode row = projection(item);
                    occurrences.add(new Occurrence((int) StrictJson.integer(row.get("occurrence_index"), 0, Integer.MAX_VALUE),
                            id(row.get("public_unit_id"), false), id(row.get("native_carmy_id"), false), bool(row.get("eligible")), ids(row.get("qualified_regiment_ids"), false)));
                }
            }
        }
        Subject subject = null;
        if (present(wrapper.get("subject"))) {
            ObjectNode row = projection(wrapper.get("subject"));
            subject = new Subject(bool(row.get("controllable")), id(row.get("army_id"), false), id(row.get("current_province_id"), true),
                    id(row.get("move_target_province_id"), true), ids(row.get("route_province_ids"), true));
        }
        return new Request(new Province(id(province.get("province_id"), true), selection, occurrences), subject);
    }
    private static Selection selection(JsonNode node) {
        if (!present(node)) { return null; }
        ObjectNode value = projection(node);
        return new Selection(id(value.get("native_carmy_id"), false), id(value.get("public_unit_id"), false), bool(value.get("controllable")));
    }

    public static byte[] encodeRequest(Request request) {
        ObjectNode result = StrictJson.object(); result.put("schema", SiegeContributionPolicy.INPUT_SCHEMA);
        ObjectNode province = result.putObject("province"); province.put("province_id", request.province().provinceId());
        selectionNode(province, request.province().currentBesiegingArmySelection());
        ObjectNode siege = province.putObject("active_siege");
        if (request.province().provinceUnitOccurrences() == null) { siege.putNull("province_unit_occurrences"); }
        else {
            ArrayNode occurrences = siege.putArray("province_unit_occurrences");
            for (Occurrence occurrence : request.province().provinceUnitOccurrences()) {
                ObjectNode row = occurrences.addObject(); row.put("occurrence_index", occurrence.occurrenceIndex());
                row.put("public_unit_id", occurrence.publicUnitId()); row.put("native_carmy_id", occurrence.nativeCarmyId());
                row.put("eligible", occurrence.eligible()); integersNode(row, "qualified_regiment_ids", occurrence.qualifiedRegimentIds());
            }
        }
        if (request.subject() == null) { result.putNull("subject"); }
        else {
            Subject subject = request.subject(); ObjectNode row = result.putObject("subject"); row.put("controllable", subject.controllable());
            row.put("army_id", subject.armyId()); row.put("current_province_id", subject.currentProvinceId());
            row.put("move_target_province_id", subject.moveTargetProvinceId()); integersNode(row, "route_province_ids", subject.routeProvinceIds());
        }
        return StrictJson.canonical(result);
    }
    public static byte[] encodeDecision(Decision decision) {
        ObjectNode result = StrictJson.object(); result.put("status", decision.status().wire()); selectionNode(result, decision.currentBesiegingArmySelection());
        result.put("public_unit_id", decision.publicUnitId()); result.put("native_carmy_id", decision.nativeCarmyId());
        result.put("matches_current_selection", decision.matchesCurrentSelection()); result.put("reason", decision.reason().wire());
        if (decision.occurrenceIndices() != null) { integersNode(result, "occurrence_indices", decision.occurrenceIndices()); }
        return StrictJson.canonical(result, StrictJson.OUTPUT_MAX_BYTES);
    }
    private static void selectionNode(ObjectNode parent, Selection selection) {
        if (selection == null) { parent.putNull("current_besieging_army_selection"); }
        else {
            ObjectNode result = parent.putObject("current_besieging_army_selection"); result.put("native_carmy_id", selection.nativeCarmyId());
            result.put("public_unit_id", selection.publicUnitId()); result.put("controllable", selection.controllable());
        }
    }
    private static void integersNode(ObjectNode parent, String key, List<Integer> values) {
        if (values == null) { parent.putNull(key); }
        else { ArrayNode array = parent.putArray(key); values.forEach(array::add); }
    }
    private static ObjectNode projection(JsonNode node) { StrictJson.require(node instanceof ObjectNode, "native SDK projection object required"); return (ObjectNode) node; }
    private static boolean present(JsonNode node) { return node != null && !node.isNull(); }
    private static JsonNode array(JsonNode node) { StrictJson.require(node != null && node.isArray(), "array required"); return node; }
    private static Integer id(JsonNode node, boolean positive) {
        return !present(node) ? null : (int) StrictJson.integer(node, positive ? 1 : 0, Integer.MAX_VALUE);
    }
    private static Boolean bool(JsonNode node) {
        if (!present(node)) { return null; }
        StrictJson.require(node.isBoolean(), "actual JSON boolean required"); return node.booleanValue();
    }
    private static List<Integer> ids(JsonNode node, boolean positive) {
        if (!present(node)) { return null; }
        List<Integer> result = new ArrayList<>();
        for (JsonNode value : array(node)) { Integer parsed = id(value, positive); StrictJson.require(parsed != null, "ID array member cannot be null"); result.add(parsed); }
        return result;
    }
}
