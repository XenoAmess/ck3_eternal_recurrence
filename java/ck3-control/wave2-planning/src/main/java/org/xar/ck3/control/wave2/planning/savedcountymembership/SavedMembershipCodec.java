package org.xar.ck3.control.wave2.planning.savedcountymembership;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.planning.scoretarget.PlayerWarDefenceCodec;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipInput.UnavailableKind;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipResult.Factor;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipResult.Truth;

/** Strict leaf wire, declared projections for existing saved-record extension objects. */
public final class SavedMembershipCodec {
    private SavedMembershipCodec() { }

    public static SavedMembershipInput decode(byte[] raw) {
        ObjectNode request = StrictJson.object(StrictJson.parse(raw), Set.of("actor", "house", "dynasty", "source_ref", "projection", "county_baronies"));
        ObjectNode projection = object(request.get("projection"));
        for (String field : Set.of("titles", "title_order", "houses", "character_houses", "character_house_unknown", "character_sources",
                "stream_complete", "unknown_key_fields", "root_keys", "metadata")) {
            StrictJson.require(projection.has(field), "required saved projection field missing: " + field);
        }
        Map<BigInteger, SavedMembershipInput.Title> titles = new LinkedHashMap<>();
        object(projection.get("titles")).properties().forEach(entry -> {
            ObjectNode row = object(entry.getValue());
            titles.put(identityKey(entry.getKey()), new SavedMembershipInput.Title(textField(row.get("key")),
                    PlayerWarDefenceCodec.scalar(row.get("holder")), PlayerWarDefenceCodec.scalar(row.get("de_facto_liege")),
                    row.has("nonunique:holder"), row.has("nonunique:de_facto_liege")));
        });
        JsonNode order = projection.get("title_order"); StrictJson.require(order.isArray(), "explicit source title-order array required");
        Map<BigInteger, SavedMembershipInput.Title> orderedTitles = new LinkedHashMap<>();
        for (JsonNode token : order) {
            BigInteger identity = integer(token);
            StrictJson.require(titles.containsKey(identity) && !orderedTitles.containsKey(identity), "title order must enumerate every title once");
            orderedTitles.put(identity, titles.get(identity));
        }
        StrictJson.require(orderedTitles.size() == titles.size(), "title-order/table closure mismatch");
        Map<BigInteger, SavedMembershipInput.House> houses = new LinkedHashMap<>();
        object(projection.get("houses")).properties().forEach(entry -> {
            ObjectNode row = object(entry.getValue());
            houses.put(identityKey(entry.getKey()), new SavedMembershipInput.House(PlayerWarDefenceCodec.scalar(row.get("dynasty")),
                    PlayerWarDefenceCodec.scalar(row.get("parent_dynasty_house")), row.has("nonunique:dynasty"), row.has("nonunique:parent_dynasty_house")));
        });
        Map<BigInteger, BigInteger> characterHouses = new LinkedHashMap<>();
        object(projection.get("character_houses")).properties().forEach(entry -> characterHouses.put(identityKey(entry.getKey()), integer(entry.getValue())));
        java.util.List<String> roots = new ArrayList<>(); JsonNode rootKeys = projection.get("root_keys");
        StrictJson.require(rootKeys.isArray(), "actual root-key array required");
        rootKeys.forEach(value -> roots.add(StrictJson.text(value)));
        JsonNode complete = projection.get("stream_complete");
        StrictJson.require(complete.isBoolean(), "actual stream-complete Boolean required");
        SavedMembershipInput.SavedProjection saved = new SavedMembershipInput.SavedProjection(orderedTitles, houses, characterHouses,
                identities(projection.get("character_house_unknown")), identities(projection.get("character_sources")), complete.booleanValue(),
                integer(projection.get("unknown_key_fields")), roots, textField(object(projection.get("metadata")).get("date")));
        return new SavedMembershipInput(integer(request.get("actor")), optionalInteger(request.get("house")),
                optionalInteger(request.get("dynasty")), StrictJson.text(request.get("source_ref")), saved, mapping(request.get("county_baronies")));
    }

    public static byte[] evaluate(byte[] raw) { return encode(SavedCountyMembership.audit(decode(raw))); }

    public static byte[] encode(SavedMembershipResult value) {
        ObjectNode result = StrictJson.object(); result.put("schema", "xar.ck3.saved-county-membership-audit/v1");
        result.put("source_ref", value.sourceRef()); putText(result, "date", value.date()); result.put("actor_id", value.actor());
        putId(result, "founding_house_id", value.house()); putId(result, "founding_dynasty_id", value.dynasty());
        result.put("title_census_complete", value.titleCensusComplete()); result.put("geography_complete", value.geographyComplete());
        result.set("realm", scope(value.realm())); result.set("dynasty", scope(value.family()));
        ObjectNode states = StrictJson.object();
        value.states().forEach((identity, state) -> {
            ObjectNode row = StrictJson.object(); putText(row, "key", state.key());
            if (state.geography() == SavedMembershipResult.Geography.KNOWN_COUNTY) {
                row.put("geographic", true); row.putNull("geography_reason");
            } else { row.putNull("geographic"); row.put("geography_reason", "county_geography_or_unique_key_unavailable"); }
            if (state.realm().membership() == Truth.UNKNOWN) { row.putNull("in_player_realm"); }
            else { row.put("in_player_realm", state.realm().membership() == Truth.YES); }
            row.put("realm_reason", state.realm().reason().wire()); row.put("realm_terminal_title_id", state.realm().terminal());
            Optional<Factor> factor = state.family().factor();
            if (factor.isPresent()) { row.put("family_factor", factor.orElseThrow().lexical()); } else { row.putNull("family_factor"); }
            row.put("family_reason", state.family().reason().wire()); states.set(identity.toString(), row);
        });
        result.set("states", states); return StrictJson.canonical(result);
    }

    private static ObjectNode scope(SavedMembershipResult.Scope value) {
        ObjectNode row = StrictJson.object(); row.put("complete", value.complete());
        var known = row.putArray("known_member_title_ids"); value.known().forEach(known::add);
        var unknown = row.putArray("unknown_title_ids"); value.unknown().forEach(unknown::add);
        row.put("count_lower", value.countLower());
        if (value.countUpper().isPresent()) { row.put("count_upper", value.countUpper().getAsInt()); } else { row.putNull("count_upper"); }
        return row;
    }

    private static SavedMembershipInput.CountyMapping mapping(JsonNode node) {
        if (!(node instanceof ObjectNode rows)) { return new SavedMembershipInput.UnavailableMapping(kind(node)); }
        Map<String, SavedMembershipInput.MappingRow> result = new LinkedHashMap<>();
        rows.properties().forEach(entry -> {
            if (entry.getValue() instanceof ObjectNode baronies) {
                Map<String, SavedMembershipInput.Province> provinces = new LinkedHashMap<>();
                baronies.properties().forEach(barony -> provinces.put(barony.getKey(), barony.getValue().isIntegralNumber()
                        ? new SavedMembershipInput.ProvinceId(barony.getValue().bigIntegerValue()) : new SavedMembershipInput.InvalidProvince(kind(barony.getValue()))));
                result.put(entry.getKey(), new SavedMembershipInput.Baronies(provinces));
            } else { result.put(entry.getKey(), new SavedMembershipInput.InvalidMappingRow(kind(entry.getValue()))); }
        });
        return new SavedMembershipInput.MappingRows(result);
    }
    private static UnavailableKind kind(JsonNode node) {
        return node.isNull() ? UnavailableKind.NULL : node.isBoolean() ? UnavailableKind.BOOLEAN
                : node.isIntegralNumber() ? UnavailableKind.INTEGER : node.isFloatingPointNumber() ? UnavailableKind.FRACTIONAL
                : node.isTextual() ? UnavailableKind.STRING : node.isArray() ? UnavailableKind.ARRAY : UnavailableKind.OBJECT;
    }
    private static ObjectNode object(JsonNode node) {
        StrictJson.require(node instanceof ObjectNode, "saved object container required"); return (ObjectNode) node;
    }
    private static BigInteger integer(JsonNode node) {
        StrictJson.require(node != null && node.isIntegralNumber(), "exact integer required; no Boolean/fraction/string coercion"); return node.bigIntegerValue();
    }
    private static Optional<BigInteger> optionalInteger(JsonNode node) { return node.isNull() ? Optional.empty() : Optional.of(integer(node)); }
    private static BigInteger identityKey(String key) {
        StrictJson.require(key.length() <= 4300 && key.matches("0|[1-9][0-9]*"), "canonical saved integer map key required"); return new BigInteger(key);
    }
    private static org.xar.ck3.control.wave2.planning.scoretarget.ScalarField textField(JsonNode node) {
        StrictJson.require(node == null || node.isNull() || node.isTextual(), "saved text, missing or explicit null required");
        return PlayerWarDefenceCodec.scalar(node);
    }
    private static Set<BigInteger> identities(JsonNode node) {
        StrictJson.require(node.isArray(), "exact identity array required"); Set<BigInteger> result = new HashSet<>();
        node.forEach(value -> { BigInteger identity = integer(value); StrictJson.require(result.add(identity), "duplicate source identity"); }); return result;
    }
    private static void putText(ObjectNode row, String key, Optional<String> value) {
        if (value.isPresent()) { row.put(key, value.orElseThrow()); } else { row.putNull(key); }
    }
    private static void putId(ObjectNode row, String key, Optional<BigInteger> value) {
        if (value.isPresent()) { row.put(key, value.orElseThrow()); } else { row.putNull(key); }
    }
}
