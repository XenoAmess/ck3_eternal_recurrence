package org.xar.ck3.control.wave2.finance.factionculture;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.DecimalNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;

import static org.xar.ck3.control.wave2.finance.factionculture.FactionCultureModel.*;

/** Shared all-four culture contract and declared normalized-alert projection. */
public final class FactionCultureCodec {
    public static final Set<String> CULTURE_FIELDS = Set.of("county_culture_id", "target_culture_id",
            "same_culture_as_target", "culture_relation_status");
    public static final int MAX_BYTES = 1_048_576;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(64)
                    .maxNumberLength(128).maxStringLength(65_536).build()).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .configure(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES, false);

    private FactionCultureCodec() { }

    public static Optional<CultureRelation> normalizeRelation(byte[] countyRow) {
        return normalizeRelation(countyRow, "county_member_observation");
    }

    public static Optional<CultureRelation> normalizeRelation(byte[] countyRow, String field) {
        if (field == null || field.isEmpty() || field.length() > 256) throw invalid("bounded field label required");
        return relation(object(parse(countyRow), field), field);
    }

    public static byte[] encodeRelation(Optional<CultureRelation> relation) {
        ObjectNode result = JSON.createObjectNode();
        addRelation(result, relation);
        return encode(result);
    }

    /** This consumes a previously normalized alert; it does not repeat or grant provider qualification. */
    public static AlertProjection decodeNormalizedAlert(byte[] bytes) {
        JsonNode alert = object(parse(bytes), "alert");
        BigInteger revision = requiredInteger(alert.get("snapshot_revision"), "snapshot_revision");
        Frame frame = new Frame(revision, signedInt(alert.get("date_raw"), "date_raw"),
                positiveInt(alert.get("player_character_id"), "player_character_id"));
        ProvenanceDocument provenance = new ProvenanceDocument(encode(object(alert.get("provenance"), "provenance")));
        JsonNode nativeFactions = array(alert.get("targeting_factions"), MAX_FACTIONS, "targeting_factions");
        List<FactionProjection> factions = new ArrayList<>();
        for (JsonNode faction : nativeFactions) {
            object(faction, "targeting faction");
            int factionId = positiveInt(faction.get("faction_id"), "faction_id");
            int target = positiveInt(faction.get("target_character_id"), "target_character_id");
            String key = text(faction.get("faction_type_key"), "faction_type_key");
            List<Integer> counties = new ArrayList<>();
            for (JsonNode county : array(faction.get("county_member_title_ids"), MAX_COUNTIES_PER_FACTION, "county ids")) {
                counties.add(positiveInt(county, "county_title_id"));
            }
            List<CountyMaterial> materials = new ArrayList<>();
            JsonNode observationRows = faction.get("county_member_observations");
            if (observationRows != null) {
                for (JsonNode material : array(observationRows, MAX_COUNTIES_PER_FACTION, "county_member_observations")) {
                    object(material, "county_member_observation");
                    materials.add(new CountyMaterial(positiveInt(material.get("county_title_id"), "county_title_id"),
                            relation(material, "normalized county_member_observation")));
                }
            }
            factions.add(new FactionProjection(factionId, key, target, counties, materials));
        }
        return new AlertProjection(frame, provenance, factions);
    }

    public static Context projectNormalizedAlert(byte[] bytes) {
        return FactionCulturePolicy.project(decodeNormalizedAlert(bytes));
    }

    public static byte[] encodeContext(Context context) {
        ObjectNode output = JSON.createObjectNode();
        output.put("status", context.status().wire());
        output.put("relation_input_ready", context.relationInputReady());
        output.put("source", "query-player-faction-alerts-v1");
        output.put("snapshot_revision", context.frame().snapshotRevision());
        output.put("date_raw", context.frame().dateRaw());
        output.put("player_character_id", context.frame().playerCharacterId());
        output.set("provenance", parse(context.provenance().json()));
        output.put("county_row_count", context.rows().size());
        output.put("available_relation_count", context.availableRelationCount());
        var rows = output.putArray("rows");
        for (ContextRow row : context.rows()) {
            ObjectNode item = JSON.createObjectNode();
            item.put("faction_id", row.factionId()); item.put("faction_type_key", row.factionTypeKey());
            item.put("target_character_id", row.targetCharacterId()); item.put("county_title_id", row.countyTitleId());
            item.putNull("county_culture_id"); item.putNull("target_culture_id"); item.putNull("same_culture_as_target");
            item.put("culture_relation_status", "unavailable");
            addRelation(item, row.relation());
            item.put("relation_input_ready", row.relationInputReady());
            if (row.unavailableReason().isPresent()) item.put("unavailable_reason", row.unavailableReason().get().wire());
            else item.putNull("unavailable_reason");
            rows.add(item);
        }
        return encode(output);
    }

    private static Optional<CultureRelation> relation(JsonNode row, String field) {
        long present = CULTURE_FIELDS.stream().filter(row::has).count();
        if (present == 0) return Optional.empty();
        if (present != CULTURE_FIELDS.size()) throw invalid(field + " must publish all four culture relation fields together");
        Optional<Integer> county = cultureId(row.get("county_culture_id"), field + ".county_culture_id");
        Optional<Integer> target = cultureId(row.get("target_culture_id"), field + ".target_culture_id");
        JsonNode sameNode = row.get("same_culture_as_target");
        Optional<Boolean> same = sameNode.isNull() ? Optional.empty() : Optional.of(bool(sameNode, field + ".same_culture_as_target"));
        String status = text(row.get("culture_relation_status"), field + ".culture_relation_status");
        if (status.equals("available")) {
            if (county.isEmpty() || target.isEmpty() || same.isEmpty()) throw invalid(field + " available culture requires full IDs and boolean");
            return Optional.of(new AvailableCulture(county.get(), target.get(), same.get()));
        }
        if (!status.equals("unavailable") || same.isPresent()) throw invalid(field + " invalid unavailable culture relation");
        return Optional.of(new UnavailableCulture(county, target));
    }

    private static void addRelation(ObjectNode result, Optional<CultureRelation> relation) {
        if (relation.isEmpty()) return;
        CultureRelation value = relation.get();
        if (value instanceof AvailableCulture available) {
            result.put("county_culture_id", available.countyCultureId());
            result.put("target_culture_id", available.targetCultureId());
            result.put("same_culture_as_target", available.sameCulture());
            result.put("culture_relation_status", "available");
        } else {
            UnavailableCulture unavailable = (UnavailableCulture) value;
            result.putNull("county_culture_id"); result.putNull("target_culture_id");
            unavailable.countyCultureId().ifPresent(id -> result.put("county_culture_id", id));
            unavailable.targetCultureId().ifPresent(id -> result.put("target_culture_id", id));
            result.putNull("same_culture_as_target"); result.put("culture_relation_status", "unavailable");
        }
    }

    private static Optional<Integer> cultureId(JsonNode node, String field) {
        if (node.isNull()) return Optional.empty();
        int value = signedInt(node, field);
        if (value == -1) throw invalid(field + " full CultureID -1 sentinel rejected");
        return Optional.of(value);
    }
    private static int positiveInt(JsonNode node, String field) {
        int value = signedInt(node, field); if (value <= 0) throw invalid(field + " positive identity required"); return value;
    }
    private static int signedInt(JsonNode node, String field) {
        if (node == null || !node.isIntegralNumber() || !node.canConvertToInt()) throw invalid(field + " signed int32 token required");
        return node.intValue();
    }
    private static BigInteger requiredInteger(JsonNode node, String field) {
        if (node == null || !node.isIntegralNumber()) throw invalid(field + " integer token required"); return node.bigIntegerValue();
    }
    private static boolean bool(JsonNode node, String field) {
        if (node == null || !node.isBoolean()) throw invalid(field + " boolean token required"); return node.booleanValue();
    }
    private static String text(JsonNode node, String field) {
        if (node == null || !node.isTextual()) throw invalid(field + " string token required"); return node.textValue();
    }
    private static JsonNode object(JsonNode node, String field) {
        if (node == null || !node.isObject()) throw invalid(field + " object required"); return node;
    }
    private static JsonNode array(JsonNode node, int maximum, String field) {
        if (node == null || !node.isArray() || node.size() > maximum) throw invalid(field + " bounded array required"); return node;
    }
    private static JsonNode parse(byte[] bytes) {
        if (bytes == null || bytes.length == 0 || bytes.length > MAX_BYTES) throw invalid("JSON byte limit");
        try {
            String utf8 = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
            JsonNode node = JSON.readTree(utf8); if (node == null) throw invalid("empty JSON"); return node;
        } catch (IOException failure) { throw new IllegalArgumentException("invalid county culture JSON", failure); }
    }
    private static byte[] encode(JsonNode node) {
        try {
            byte[] result = JSON.writeValueAsBytes(preserveFloatDomain(node));
            if (result.length > MAX_BYTES) throw invalid("encoded JSON byte limit");
            return result;
        }
        catch (IOException failure) { throw new IllegalStateException("culture encoding failed", failure); }
    }

    /** Preserve opaque decimal precision and floating token identity across downstream validation. */
    private static JsonNode preserveFloatDomain(JsonNode node) {
        if (node.isObject()) {
            ObjectNode copy = JSON.createObjectNode();
            node.properties().forEach(entry -> copy.set(entry.getKey(), preserveFloatDomain(entry.getValue())));
            return copy;
        }
        if (node.isArray()) {
            ArrayNode copy = JSON.createArrayNode();
            node.forEach(value -> copy.add(preserveFloatDomain(value)));
            return copy;
        }
        if (node.isFloatingPointNumber()) {
            var decimal = node.decimalValue();
            return DecimalNode.valueOf(decimal.scale() == 0 ? decimal.setScale(1) : decimal);
        }
        return node;
    }
    private static IllegalArgumentException invalid(String message) { return new IllegalArgumentException(message); }
}
