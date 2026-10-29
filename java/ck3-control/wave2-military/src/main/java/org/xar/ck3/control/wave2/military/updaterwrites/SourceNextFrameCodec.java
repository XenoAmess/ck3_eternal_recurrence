package org.xar.ck3.control.wave2.military.updaterwrites;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Set;

/** Strict legacy19/extended23 native family boundary; extensible outer rows are not exact-key checked. */
public final class SourceNextFrameCodec {
    private static final String SOURCE = "native_source_derived_next_daily_supply_frame_inputs_12004";
    private static final String STAGE = "source_derived_conditional_next_date_pair";
    private static final Set<String> FALSE_FIELDS = Set.of("actual_future_date_stage_observed",
            "actual_future_callback_observed", "future_bucket_mutations_reconstructed", "future_stock_or_strength_ready",
            "full_daily_supply_transition_ready", "full_monthly_ready");
    private static final Set<String> LEGACY_FIELDS = Set.of("schema_version", "source", "stage", "status", "ready",
            "unavailable_reason", "current_date_storage_raw64", "current_date_raw_i32", "current_native_day_index_raw_i32",
            "source_derived_next_date_raw_i32", "source_derived_next_native_day_index_raw_i32", "subject_army_id_u32", "subject_carmy_id_u32",
            "actual_future_date_stage_observed", "actual_future_callback_observed", "future_bucket_mutations_reconstructed",
            "future_stock_or_strength_ready", "full_daily_supply_transition_ready", "full_monthly_ready");
    private static final Set<String> EXTENDED_FIELDS;
    static {
        Set<String> values = new HashSet<>(LEGACY_FIELDS);
        values.addAll(Set.of("source_derived_next_date_storage_raw64", "source_derived_next_calendar_day_u8",
                "source_derived_next_calendar_month_u8", "source_derived_full_cdate64_ready"));
        EXTENDED_FIELDS = Set.copyOf(values);
    }
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(16).maxNumberLength(24).build()).build());
    private SourceNextFrameCodec() {}

    /** Missing/null families have the legacy get(None) meaning and are returned as null. */
    public static SourceNextFrame decode(JsonNode node, Integer expectedArmyId, Integer expectedCarmyId) {
        if (node == null || node.isNull() || node.isMissingNode()) return null;
        Set<String> fields = new HashSet<>();
        if (node.isObject()) for (var property : node.properties()) fields.add(property.getKey());
        if (!node.isObject() || !fields.equals(LEGACY_FIELDS) && !fields.equals(EXTENDED_FIELDS)) {
            throw invalid("source-next family field contract differs");
        }
        if (!Integer.valueOf(1).equals(integer32(node, "schema_version"))) throw invalid("source-next schema version differs");
        requireText(node, "source", SOURCE); requireText(node, "stage", STAGE);
        for (String field : FALSE_FIELDS) {
            if (!node.get(field).isBoolean() || node.get(field).booleanValue()) throw invalid("source-next cannot claim future execution: " + field);
        }
        String rawStatus = text(node, "status", false);
        SourceNextFrame.Status status = switch (rawStatus) {
            case "available" -> SourceNextFrame.Status.AVAILABLE;
            case "unavailable" -> SourceNextFrame.Status.UNAVAILABLE;
            default -> throw invalid("unknown source-next status");
        };
        if (bool(node, "ready") != (status == SourceNextFrame.Status.AVAILABLE)) throw invalid("source-next status and ready differ");
        Long army = unsigned32(node, "subject_army_id_u32");
        Long carmy = unsigned32(node, "subject_carmy_id_u32");
        if (army != null && expectedArmyId != null && army.longValue() != Integer.toUnsignedLong(expectedArmyId)
                || carmy != null && expectedCarmyId != null && carmy.longValue() != Integer.toUnsignedLong(expectedCarmyId)) {
            throw invalid("source-next subject differs from same-query row");
        }
        SourceNextFrame.Values values = new SourceNextFrame.Values(status, text(node, "unavailable_reason", true),
                integer64(node, "current_date_storage_raw64"), integer32(node, "current_date_raw_i32"),
                integer32(node, "current_native_day_index_raw_i32"), integer32(node, "source_derived_next_date_raw_i32"),
                integer32(node, "source_derived_next_native_day_index_raw_i32"), army, carmy);
        if (fields.equals(LEGACY_FIELDS)) return new SourceNextFrame.Legacy19(values);
        return new SourceNextFrame.Extended23(values, bool(node, "source_derived_full_cdate64_ready"),
                integer64(node, "source_derived_next_date_storage_raw64"), unsigned8(node, "source_derived_next_calendar_day_u8"),
                unsigned8(node, "source_derived_next_calendar_month_u8"));
    }

    public static SourceNextFrame decode(JsonNode node) { return decode(node, null, null); }
    public static SourceNextFrame decode(byte[] bytes, Integer expectedArmyId, Integer expectedCarmyId) {
        return decode(parse(bytes), expectedArmyId, expectedCarmyId);
    }

    public static JsonNode encode(SourceNextFrame frame) {
        if (frame == null) return NullNode.getInstance();
        SourceNextFrame.Values values = frame.values();
        ObjectNode node = JSON.createObjectNode();
        node.put("schema_version", 1); node.put("source", SOURCE); node.put("stage", STAGE);
        node.put("status", frame.ready() ? "available" : "unavailable"); node.put("ready", frame.ready());
        node.put("unavailable_reason", values.unavailableReason());
        nullable(node, "current_date_storage_raw64", values.currentDateStorageRaw64());
        nullable(node, "current_date_raw_i32", values.currentDateRawI32());
        nullable(node, "current_native_day_index_raw_i32", values.currentNativeDayIndexRawI32());
        nullable(node, "source_derived_next_date_raw_i32", values.nextDateRawI32());
        nullable(node, "source_derived_next_native_day_index_raw_i32", values.nextNativeDayIndexRawI32());
        nullable(node, "subject_army_id_u32", values.subjectArmyIdU32()); nullable(node, "subject_carmy_id_u32", values.subjectCarmyIdU32());
        for (String field : FALSE_FIELDS) node.put(field, false);
        if (frame instanceof SourceNextFrame.Extended23 extended) {
            node.put("source_derived_full_cdate64_ready", extended.fullCdate64Ready());
            nullable(node, "source_derived_next_date_storage_raw64", extended.nextDateStorageRaw64());
            nullable(node, "source_derived_next_calendar_day_u8", extended.nextCalendarDayU8());
            nullable(node, "source_derived_next_calendar_month_u8", extended.nextCalendarMonthU8());
        }
        return node;
    }

    static JsonNode parse(byte[] bytes) {
        if (bytes == null || bytes.length == 0 || bytes.length > 65_536) throw invalid("source projection input budget exceeded or empty");
        try {
            StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes));
            try (JsonParser parser = JSON.createParser(bytes)) {
                JsonNode node = JSON.readTree(parser);
                if (node == null || parser.nextToken() != null) throw invalid("exactly one JSON value required");
                return node;
            }
        } catch (IOException failure) { throw new IllegalArgumentException("invalid strict JSON/UTF-8 projection", failure); }
    }
    static Integer integer32(JsonNode node, String field) {
        Long value = integer64(node, field);
        if (value == null) return null;
        if (value < Integer.MIN_VALUE || value > Integer.MAX_VALUE) throw invalid(field + " must be signed32 or null");
        return value.intValue();
    }
    static Long integer64(JsonNode node, String field) {
        JsonNode value = node.get(field);
        if (value == null || value.isNull()) return null;
        if (!value.isIntegralNumber() || value.bigIntegerValue().bitLength() > 63) throw invalid(field + " must be signed64 integer token or null");
        return value.longValue();
    }
    private static Long unsigned32(JsonNode node, String field) {
        Long value = integer64(node, field);
        if (value != null && (value < 0 || value > 0xffff_ffffL)) throw invalid(field + " must be uint32 or null");
        return value;
    }
    private static Integer unsigned8(JsonNode node, String field) {
        Integer value = integer32(node, field);
        if (value != null && (value < 0 || value > 255)) throw invalid(field + " must be uint8 or null");
        return value;
    }
    static boolean bool(JsonNode node, String field) {
        JsonNode value = node.get(field);
        if (value == null || !value.isBoolean()) throw invalid(field + " must be bool");
        return value.booleanValue();
    }
    static String text(JsonNode node, String field, boolean nullable) {
        JsonNode value = node.get(field);
        if (nullable && (value == null || value.isNull())) return null;
        if (value == null || !value.isTextual() || value.textValue().isEmpty()) throw invalid(field + " must be nonempty string");
        return value.textValue();
    }
    private static void requireText(JsonNode node, String field, String expected) {
        if (!expected.equals(text(node, field, false))) throw invalid(field + " differs");
    }
    static void nullable(ObjectNode node, String field, Number value) {
        if (value == null) node.putNull(field); else node.put(field, value.longValue());
    }
    private static IllegalArgumentException invalid(String message) { return new IllegalArgumentException(message); }
}
