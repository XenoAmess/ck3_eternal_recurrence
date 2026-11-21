package org.xar.ck3.control.contracts.semantic;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.Set;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;

/** Florin owned-army base DATA only. No legacy PublicUnitId or army action eligibility is constructed. */
public final class FlorinPlayerArmies {
    private static final JsonNodeFactory JSON = JsonNodeFactory.instance;
    private static final int MAX_ARMIES = 16_384, MAX_ROUTE = 4096, MAX_TOTAL_ROUTE = 1_048_576;
    private static final BigInteger I32_MIN = BigInteger.valueOf(Integer.MIN_VALUE);
    private static final BigInteger I32_MAX = BigInteger.valueOf(Integer.MAX_VALUE);
    private static final String[] STATES = {
            "unknown", "regular", "combat", "sieging", "embarked", "gathering", "retreating", "moving", "raiding", "bartering"};
    private FlorinPlayerArmies() { }
    /** Explicit DATA projection, selected by an independently held source; never inferred from row omissions. */
    public enum ObservationMode { RICH, IDENTITY_ONLY126 }
    /** Source identity DATA only. Actual loaded-module/owner/endpoint custody is independently required by NT. */
    public static boolean identityOnly126SourceMatches(org.xar.ck3.control.contracts.ExactRef source) {
        return source != null && ((source.bytes() == 12_395_520L
                && "30c21218df7b9ca567b30f5a02fe31731c790db1397e0ecc45b89aa502e617ea".equals(source.sha256()))
                // Independent142 combines this same identity-only DATA contract with strict sentinel controls.
                // The transport must select exactly one mode; this predicate grants no command authority.
                || (source.bytes() == 12_396_032L
                && "3601748c4d4824509416d61c779f16eda6f97b85cd5608786ecf5645215b733c".equals(source.sha256())));
    }
    public static ArrayNode normalize(ObjectNode fullRoot, ObservationMode mode) {
        java.util.Objects.requireNonNull(mode);
        if (mode == ObservationMode.RICH) return normalize(fullRoot);
        need(selects(fullRoot), "explicit exact Florin full-state root required for identity-only126 armies");
        var build = org.xar.ck3.control.contracts.ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
        need(build.matches(fullRoot.path("game_version").textValue(), fullRoot.path("executable_sha256").textValue())
                && build.coreFullAdapterId().equals(fullRoot.path("adapter_id").textValue())
                && build.coreFullBackend().equals(fullRoot.path("backend").textValue()),
                "identity-only126 requires its exact current Full DATA tuple");
        JsonNode raw = fullRoot.get("player_armies");
        need(raw != null && raw.isArray() && raw.size() <= MAX_ARMIES,
                "bounded explicit identity-only126 owned-army array required");
        ArrayNode result = JSON.arrayNode();
        JsonNode actor = fullRoot.get("played_character");
        NativePlayedCharacter.requireFlorinIdentity(actor, NativePlayedCharacter.FLORIN_SCHEMA);
        need(build.matches(actor.path("game_version").textValue(), actor.path("executable_sha256").textValue())
                && build.coreFullAdapterId().equals(actor.path("adapter_id").textValue())
                && build.coreFullBackend().equals(actor.path("backend").textValue()),
                "identity-only126 played identity differs from its same current Full root tuple");
        NativeCharacterId owner = NativeCharacterId.fromJson(actor.get("character_id"));
        if (raw.isEmpty()) return result;
        Set<UnitFullId> units = new HashSet<>();
        for (JsonNode value : raw) {
            need(value instanceof ObjectNode, "identity-only126 army row must be an object");
            ObjectNode row = (ObjectNode) value;
            Set<String> fields = new HashSet<>(); row.fieldNames().forEachRemaining(fields::add);
            need(fields.equals(Set.of("army_id", "owner_character_id", "controllable")),
                    "identity-only126 army has missing or unobserved fields");
            UnitFullId unit = new UnitFullId(integer(row.get("army_id"), I32_MIN, I32_MAX));
            need(units.add(unit), "duplicate complete identity-only126 CUnit identity");
            NativeCharacterId actualOwner = NativeCharacterId.fromJson(row.get("owner_character_id"));
            need(owner.equals(actualOwner), "identity-only126 army owner differs from the same full-root played identity");
            need(flag(row.get("controllable")), "identity-only126 owned army must be observed controllable");
            ObjectNode out = JSON.objectNode();
            out.put("army_id", unit.value()); out.put("owner_character_id", actualOwner.value()); out.put("controllable", true);
            result.add(out);
        }
        return result;
    }

    /** A full-generation CUnit is a separate domain from an army component or legacy public unit. */
    private record UnitFullId(int value) {
        private UnitFullId { need(value != -1, "absent CUnit sentinel cannot identify an observed army"); }
    }

    /** Only the explicit full-root marker selects this decoder; a matching-looking row never does. */
    public static boolean selects(ObjectNode fullRoot) {
        JsonNode marker = fullRoot.get("schema");
        if (marker == null || !marker.isTextual()
                || !NativeSemanticNormalizer.FLORIN_SCHEMA.equals(marker.textValue())) return false;
        NativePlayedCharacter.requireFlorinIdentity(fullRoot, NativeSemanticNormalizer.FLORIN_SCHEMA);
        return true;
    }

    public static ArrayNode normalize(ObjectNode fullRoot) {
        need(selects(fullRoot), "explicit exact Florin full-state root required for owned armies");
        JsonNode raw = fullRoot.get("player_armies");
        need(raw != null && raw.isArray() && raw.size() <= MAX_ARMIES, "bounded explicit Florin owned-army array required");
        ArrayNode result = JSON.arrayNode();
        if (raw.isEmpty()) return result;
        JsonNode actor = fullRoot.get("played_character");
        NativePlayedCharacter.requireFlorinIdentity(actor, NativePlayedCharacter.FLORIN_SCHEMA);
        NativeCharacterId owner = NativeCharacterId.fromJson(actor.get("character_id"));
        Set<UnitFullId> units = new HashSet<>();
        int routeBudget = 0;
        for (JsonNode value : raw) {
            need(value instanceof ObjectNode, "Florin owned-army base row must be an object");
            ObjectNode row = (ObjectNode) value;
            UnitFullId unit = new UnitFullId(integer(row.get("army_id"), I32_MIN, I32_MAX));
            need(units.add(unit), "duplicate complete Florin CUnit identity");
            NativeCharacterId actualOwner = NativeCharacterId.fromJson(row.get("owner_character_id"));
            need(owner.equals(actualOwner), "Florin player-army owner must match the same full-root played identity");
            ObjectNode out = JSON.objectNode();
            out.put("army_id", unit.value()); out.put("owner_character_id", actualOwner.value());
            nullableInteger(row, out, "current_province_id", BigInteger.ONE, I32_MAX, false);
            nullableInteger(row, out, "move_target_province_id", BigInteger.ONE, I32_MAX, false);
            boolean observable = flag(row.get("move_target_observable"));
            out.put("move_target_observable", observable);
            out.put("controllable", flag(row.get("controllable")));
            boolean combat = flag(row.get("in_combat"));
            out.put("in_combat", combat); out.put("retreating", flag(row.get("retreating")));
            int code = integer(row.get("army_state_code"), BigInteger.ONE, BigInteger.valueOf(9));
            need(STATES[code].equals(StrictJson.text(row.get("army_state"))) && combat == (code == 2),
                    "Florin native state code/name/combat observations differ");
            out.put("army_state_code", code); out.put("army_state", STATES[code]);
            JsonNode route = row.get("route_province_ids");
            need(route != null && route.isArray() && route.size() <= MAX_ROUTE, "complete bounded Florin route required");
            int count = integer(row.get("route_source_count"), BigInteger.ZERO, BigInteger.valueOf(MAX_ROUTE));
            need(count == route.size() && count <= MAX_TOTAL_ROUTE - routeBudget, "Florin route count or collection budget differs");
            routeBudget += count;
            ArrayNode normalizedRoute = out.putArray("route_province_ids");
            for (JsonNode province : route) normalizedRoute.add(integer(province, BigInteger.ONE, I32_MAX));
            String status = StrictJson.text(row.get("route_read_status"));
            if (count == 0) {
                need("complete_empty".equals(status) && !observable && out.get("move_target_province_id").isNull(),
                        "empty Florin route must have no observable move target");
            } else {
                need("complete_nonempty".equals(status) && observable && !out.get("move_target_province_id").isNull()
                        && out.get("move_target_province_id").intValue() == normalizedRoute.get(count - 1).intValue(),
                        "complete Florin route must end at its observed move target");
            }
            out.put("route_source_count", count); out.put("route_read_status", status);
            // Soldier counts are outside this base producer, not an observed zero or an action input.
            need(!row.hasNonNull("soldiers") && !row.hasNonNull("soldier_count"),
                    "Florin base army has no qualified soldier-count source");
            out.putNull("soldiers");
            optionalInteger(row, out, "siege_days_left", BigInteger.ZERO, I32_MAX, false);
            optionalInteger(row, out, "siege_province_holder_character_id", I32_MIN, I32_MAX, true);
            if (row.has("siege_province_in_player_subrealm")) {
                JsonNode relation = row.get("siege_province_in_player_subrealm");
                if (relation.isNull()) out.putNull("siege_province_in_player_subrealm");
                else {
                    need(out.hasNonNull("siege_province_holder_character_id"), "observed siege relation requires its full holder identity");
                    out.put("siege_province_in_player_subrealm", flag(relation));
                }
            }
            out.put("source", "native"); result.add(out);
        }
        return result;
    }

    private static void nullableInteger(ObjectNode row, ObjectNode out, String key,
            BigInteger minimum, BigInteger maximum, boolean character) {
        need(row.has(key), "required Florin nullable base field missing: " + key);
        optionalInteger(row, out, key, minimum, maximum, character);
    }

    private static void optionalInteger(ObjectNode row, ObjectNode out, String key,
            BigInteger minimum, BigInteger maximum, boolean character) {
        if (!row.has(key)) return;
        JsonNode value = row.get(key);
        if (value.isNull()) out.putNull(key);
        else if (character) out.put(key, NativeCharacterId.fromJson(value).value());
        else out.put(key, integer(value, minimum, maximum));
    }

    private static int integer(JsonNode value, BigInteger minimum, BigInteger maximum) {
        return StrictJson.integer(value, minimum, maximum).intValueExact();
    }
    private static boolean flag(JsonNode value) {
        need(value != null && value.isBoolean(), "exact Florin army boolean token required"); return value.booleanValue();
    }
    private static void need(boolean condition, String message) { StrictJson.require(condition, message); }
}
