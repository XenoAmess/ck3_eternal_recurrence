package org.xar.ck3.control.wave2.military.sharedwire;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.contracts.StrictJson.require;

/** Lossless ArmyManager transport boundary. No family business validation or game qualification.
 * JsonNode is deliberately confined to this codec: unknown SDK fields and original token kinds survive.
 */
public final class ArmyManagerSharedWire {
    public static final String SHARED_KEY = "army_manager_inputs_shared_v1";
    public enum Family {
        DAILY_ASSAULT_ROSTER_ADMISSION("current_daily_assault_roster_admission_v1", true),
        PRE_DATE_PENDING_UPDATE("current_pre_date_pending_update_inputs_v1", true),
        POST_ADMISSION_REFRESH("current_post_admission_refresh_inputs_v1", true),
        SELECTED_TITLE_HOLDER_OWNER_RELATION("current_selected_title_holder_owner_relation_v1", true),
        COMBAT_ROLES_PHASE("current_army_combat_roles_phase_inputs_v1", true),
        FLAG31("current_army_flag31_inputs_v1", true),
        CONDITION30("current_army_condition30_inputs_v1", false),
        FLAG20("current_army_flag20_inputs_v1", false),
        FLAG21("current_army_flag21_inputs_v1", false),
        PRE_DATE_CHARACTER_PREFIX("current_pre_date_character_prefix_inputs_v1", false);
        private final String wireName;
        private final boolean base;
        Family(String wireName, boolean base) { this.wireName = wireName; this.base = base; }
        public String wireName() { return wireName; }
        public boolean base() { return base; }
        public static Family fromWire(String value) {
            for (Family family : values()) if (family.wireName.equals(value)) return family;
            throw new org.xar.ck3.control.contracts.ContractViolationException("unsupported shared manager family: " + value);
        }
    }
    public record PublicCUnitId(int value) {
        public PublicCUnitId { require(value >= 0, "public CUnit id must be nonnegative signed32 including zero"); }
        public static PublicCUnitId decode(JsonNode value) { return new PublicCUnitId((int) StrictJson.integer(value, 0, Integer.MAX_VALUE)); }
    }
    public record BundleView(List<PublicCUnitId> armyIds, List<Family> families) {
        public BundleView { armyIds = List.copyOf(armyIds); families = List.copyOf(families); }
    }
    private ArmyManagerSharedWire() { }
    private static List<PublicCUnitId> publicIds(JsonNode value, boolean nonempty) {
        require(value instanceof ArrayNode && (!nonempty || !value.isEmpty()), "public CUnit ids array required");
        List<PublicCUnitId> result = new ArrayList<>(); Set<PublicCUnitId> unique = new HashSet<>();
        for (JsonNode item : value) { PublicCUnitId id = PublicCUnitId.decode(item);
            require(unique.add(id), "duplicate public CUnit ids"); result.add(id); }
        return List.copyOf(result);
    }
    private static List<PublicCUnitId> rowIds(ArrayNode rows, boolean nonempty) {
        ArrayNode ids = StrictJson.object().putArray("ids");
        for (JsonNode row : rows) { require(row instanceof ObjectNode, "ArmyStrength row object required");
            JsonNode id = row.get("army_id"); require(id != null, "public CUnit row id missing"); ids.add(id); }
        return publicIds(ids, nonempty);
    }
    private static ObjectNode shallow(ObjectNode node) { ObjectNode result = StrictJson.object(); result.setAll(node); return result; }
    private static boolean objectOrNull(JsonNode value) { return value != null && (value.isObject() || value.isNull()); }
    /** Preserve bool/int/float distinctions; malformed per-family tokens must reach their normalizer unchanged. */
    private static boolean sameTokens(JsonNode left, JsonNode right) {
        if (left == null || right == null) return left == right;
        if (left.isIntegralNumber() && right.isIntegralNumber()) return left.bigIntegerValue().equals(right.bigIntegerValue());
        if (left.getNodeType() != right.getNodeType()) return false;
        if (left.isNumber() && left.isIntegralNumber() != right.isIntegralNumber()) return false;
        if (left.isArray()) {
            if (left.size() != right.size()) return false;
            for (int i = 0; i < left.size(); i++) if (!sameTokens(left.get(i), right.get(i))) return false;
            return true;
        }
        if (left.isObject()) {
            if (left.size() != right.size()) return false;
            Iterator<String> fields = left.fieldNames();
            while (fields.hasNext()) { String field = fields.next(); if (!right.has(field) || !sameTokens(left.get(field), right.get(field))) return false; }
            return true;
        }
        return left.equals(right);
    }
    /** Equal valid source families are hoisted once. Ineligible/legacy payloads retain the original object. */
    public static ObjectNode pack(ObjectNode payload) {
        Objects.requireNonNull(payload);
        if (payload.has(SHARED_KEY)) return payload;
        JsonNode rawRows = payload.get("army_strengths");
        if (!(rawRows instanceof ArrayNode rows) || rows.size() < 2) return payload;
        for (JsonNode row : rows) if (!(row instanceof ObjectNode)) return payload;
        ObjectNode first = (ObjectNode) rows.get(0); List<Family> present = new ArrayList<>();
        for (Family family : Family.values()) if (family.base() && first.has(family.wireName())) present.add(family);
        if (present.isEmpty()) return payload;
        for (Family family : present) if (!objectOrNull(first.get(family.wireName()))) return payload;
        for (int i = 1; i < rows.size(); i++) {
            JsonNode row = rows.get(i);
            for (Family family : Family.values()) if (family.base()) {
                String name = family.wireName();
                if (row.has(name) != first.has(name) || first.has(name) && !sameTokens(row.get(name), first.get(name))) return payload;
            }
        }
        for (Family family : Family.values()) if (!family.base() && first.has(family.wireName()) && objectOrNull(first.get(family.wireName()))) {
            boolean equal = true;
            for (int i = 1; i < rows.size(); i++) equal &= rows.get(i).has(family.wireName())
                    && sameTokens(rows.get(i).get(family.wireName()), first.get(family.wireName()));
            if (equal) present.add(family);
        }
        List<PublicCUnitId> ids;
        try { ids = rowIds(rows, true); }
        catch (org.xar.ck3.control.contracts.ContractViolationException invalidId) { return payload; }
        ObjectNode result = shallow(payload); ArrayNode stripped = result.putArray("army_strengths");
        for (JsonNode row : rows) { ObjectNode item = shallow((ObjectNode) row);
            for (Family family : present) item.remove(family.wireName()); stripped.add(item); }
        ObjectNode bundle = result.putObject(SHARED_KEY); bundle.put("schema_version", 1);
        ArrayNode armyIds = bundle.putArray("army_ids"); ids.forEach(id -> armyIds.add(id.value()));
        ObjectNode fields = bundle.putObject("fields"); present.forEach(family -> fields.set(family.wireName(), first.get(family.wireName())));
        return result;
    }
    /** Validate the entire real shared capsule, including collisions in families not owned by this caller. */
    public static BundleView inspectBundle(ObjectNode payload) {
        Objects.requireNonNull(payload); require(payload.has(SHARED_KEY), "shared capsule absent");
        ObjectNode bundle = StrictJson.object(payload.get(SHARED_KEY), Set.of("schema_version", "army_ids", "fields"));
        StrictJson.integer(bundle.get("schema_version"), 1, 1);
        require(payload.get("army_strengths") instanceof ArrayNode, "ArmyStrength rows array required");
        ArrayNode rows = (ArrayNode) payload.get("army_strengths");
        List<PublicCUnitId> ids = publicIds(bundle.get("army_ids"), true);
        require(ids.equals(rowIds(rows, true)), "shared ids must exactly match ordered Army rows");
        require(bundle.get("fields") instanceof ObjectNode && !bundle.get("fields").isEmpty(), "nonempty shared fields object required");
        ObjectNode fields = (ObjectNode) bundle.get("fields"); List<Family> families = new ArrayList<>();
        Iterator<String> names = fields.fieldNames();
        while (names.hasNext()) {
            String name = names.next(); Family family = Family.fromWire(name); families.add(family);
            require(objectOrNull(fields.get(name)), "shared family must remain object or null");
            for (JsonNode row : rows) require(!row.has(name), "shared family collides with inline Army field");
        }
        return new BundleView(ids, families);
    }
    /** Detached=true gives external consumers independent mutable rows; false is the real Driver pre-normalization path. */
    public static ObjectNode expand(ObjectNode payload, boolean detached) {
        Objects.requireNonNull(payload);
        if (!payload.has(SHARED_KEY)) return detached ? payload.deepCopy() : payload;
        inspectBundle(payload);
        ObjectNode fields = (ObjectNode) payload.path(SHARED_KEY).path("fields");
        ObjectNode result = shallow(payload); result.remove(SHARED_KEY); result.remove("army_strengths");
        if (detached) result = result.deepCopy();
        ArrayNode rows = result.putArray("army_strengths");
        for (JsonNode rawRow : payload.path("army_strengths")) {
            ObjectNode row = detached ? rawRow.deepCopy() : shallow((ObjectNode) rawRow);
            row.setAll(detached ? fields.deepCopy() : fields); rows.add(row);
        }
        return result;
    }
}
