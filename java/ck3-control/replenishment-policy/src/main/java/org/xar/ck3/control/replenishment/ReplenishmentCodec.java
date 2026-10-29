package org.xar.ck3.control.replenishment;

import static org.xar.ck3.control.replenishment.ReplenishmentModel.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/** Versioned projection boundary; native extensible containers must be explicitly projected first. */
public final class ReplenishmentCodec {
    public static final int MAX_INPUT_BYTES = 262_144;
    public static final int MAX_OUTPUT_BYTES = 1_048_576;
    public static final int MAX_ROWS = 4096;
    public static final String INPUT_SCHEMA = "xar.replenishment.observed-input/v1";
    public static final String CHUNK_SCHEMA = "xar.replenishment.chunk-input/v1";
    private static final ObjectMapper MAPPER = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(24)
                    .maxStringLength(MAX_INPUT_BYTES).maxNumberLength(40).build()).build());
    private static final Set<String> RECORD_FIELDS = Set.of("status", "unavailable_reason", "record_index",
            "persistent_regiment_id", "chunk_index", "maximum_soldiers", "effective_current_soldiers",
            "persistent_prepared_replenishment_fraction_raw", "persistent_prepared_replenishment_fraction_scale",
            "native_chunk_can_replenish");

    private ReplenishmentCodec() {}

    public static List<ArmyRow> decodeObservedInput(byte[] bytes) {
        JsonNode root = parse(bytes);
        exactFields(root, Set.of("schema", "army_rows"));
        requireSchema(root, INPUT_SCHEMA);
        List<ArmyRow> result = new ArrayList<>();
        for (JsonNode army : array(root.get("army_rows"), "army_rows")) {
            if (!army.isObject() || !army.has("army_id")) throw invalid("army row requires army_id");
            Set<String> fields = fields(army);
            if (!fields.equals(Set.of("army_id"))
                    && !fields.equals(Set.of("army_id", "regiment_replenishment_records_v1"))) {
                throw invalid("army row fields differ");
            }
            int armyId = int32(army.get("army_id"), "army_id");
            Snapshots snapshots;
            JsonNode raw = army.get("regiment_replenishment_records_v1");
            if (raw == null) snapshots = new MissingSnapshots();
            else if (raw.isNull()) snapshots = new NullSnapshots();
            else {
                List<FullDataSnapshot> values = new ArrayList<>();
                for (JsonNode snapshot : array(raw, "regiment_replenishment_records_v1")) {
                    exactFields(snapshot, Set.of("army_regiment_id", "status", "native_data_record_count",
                            "unavailable_reason", "records"));
                    List<FullDataRecord> records = new ArrayList<>();
                    for (JsonNode record : array(snapshot.get("records"), "records")) {
                        exactFields(record, RECORD_FIELDS);
                        records.add(new FullDataRecord(recordStatus(record.get("status")),
                                nullableText(record.get("unavailable_reason"), "unavailable_reason"),
                                int32(record.get("record_index"), "record_index"),
                                int32(record.get("persistent_regiment_id"), "persistent_regiment_id"),
                                int32(record.get("chunk_index"), "chunk_index"),
                                nullableInt32(record.get("maximum_soldiers"), "maximum_soldiers"),
                                nullableInt32(record.get("effective_current_soldiers"), "effective_current_soldiers"),
                                nullableInt64(record.get("persistent_prepared_replenishment_fraction_raw"),
                                        "persistent_prepared_replenishment_fraction_raw"),
                                int32(record.get("persistent_prepared_replenishment_fraction_scale"),
                                        "persistent_prepared_replenishment_fraction_scale"),
                                nullableBoolean(record.get("native_chunk_can_replenish"), "native_chunk_can_replenish")));
                    }
                    values.add(new FullDataSnapshot(int32(snapshot.get("army_regiment_id"), "army_regiment_id"),
                            coverageStatus(snapshot.get("status")),
                            nullableInt32(snapshot.get("native_data_record_count"), "native_data_record_count"),
                            nullableText(snapshot.get("unavailable_reason"), "unavailable_reason"), records));
                }
                snapshots = new PublishedSnapshots(values);
            }
            result.add(new ArmyRow(armyId, snapshots));
        }
        return List.copyOf(result);
    }

    public static ChunkInput decodeChunkInput(byte[] bytes) {
        JsonNode root = parse(bytes);
        exactFields(root, Set.of("schema", "maximum_soldiers", "effective_current_soldiers",
                "prepared_fraction_raw", "native_chunk_can_replenish"));
        requireSchema(root, CHUNK_SCHEMA);
        Boolean predicate = nullableBoolean(root.get("native_chunk_can_replenish"), "native_chunk_can_replenish");
        if (predicate == null) throw invalid("native_chunk_can_replenish must be bool");
        return new ChunkInput(int32(root.get("maximum_soldiers"), "maximum_soldiers"),
                int32(root.get("effective_current_soldiers"), "effective_current_soldiers"),
                int64(root.get("prepared_fraction_raw"), "prepared_fraction_raw"), predicate);
    }

    public static byte[] encodeCalculation(ChunkCalculation value) {
        return encode(calculationNode(value));
    }

    public static byte[] encodeObservedInput(List<ArmyRow> rows) {
        ObjectNode root = MAPPER.createObjectNode();
        root.put("schema", INPUT_SCHEMA);
        ArrayNode armies = root.putArray("army_rows");
        for (ArmyRow army : rows) {
            ObjectNode node = armies.addObject();
            node.put("army_id", army.armyId());
            if (army.snapshots() instanceof NullSnapshots) {
                node.putNull("regiment_replenishment_records_v1");
            } else if (army.snapshots() instanceof PublishedSnapshots published) {
                ArrayNode snapshots = node.putArray("regiment_replenishment_records_v1");
                for (FullDataSnapshot snapshot : published.values()) {
                    ObjectNode raw = snapshots.addObject();
                    raw.put("army_regiment_id", snapshot.armyRegimentId());
                    raw.put("status", wire(snapshot.status()));
                    nullable(raw, "native_data_record_count", snapshot.nativeDataRecordCount());
                    raw.put("unavailable_reason", snapshot.unavailableReason());
                    ArrayNode records = raw.putArray("records");
                    for (FullDataRecord record : snapshot.records()) {
                        ObjectNode item = records.addObject();
                        item.put("status", wire(record.status()));
                        item.put("unavailable_reason", record.unavailableReason());
                        item.put("record_index", record.recordIndex());
                        item.put("persistent_regiment_id", record.persistentRegimentId());
                        item.put("chunk_index", record.chunkIndex());
                        nullable(item, "maximum_soldiers", record.maximumSoldiers());
                        nullable(item, "effective_current_soldiers", record.effectiveCurrentSoldiers());
                        nullable(item, "persistent_prepared_replenishment_fraction_raw", record.preparedFractionRaw());
                        item.put("persistent_prepared_replenishment_fraction_scale", record.preparedFractionScale());
                        if (record.nativeChunkCanReplenish() == null) item.putNull("native_chunk_can_replenish");
                        else item.put("native_chunk_can_replenish", record.nativeChunkCanReplenish());
                    }
                }
            }
        }
        return encode(root);
    }

    /** Emits the legacy JSON value domain. No byte-for-byte native response identity is claimed. */
    public static byte[] encodeProjection(Projection value) {
        ObjectNode root = MAPPER.createObjectNode();
        root.put("status", wire(value.status()));
        root.put("source", "same_input_native_262c9d0");
        ArrayNode snapshots = root.putArray("source_snapshots");
        for (SourceSnapshot source : value.sourceSnapshots()) {
            ObjectNode node = snapshots.addObject();
            node.put("army_id", source.armyId());
            nullable(node, "army_regiment_id", source.armyRegimentId());
            node.put("status", wire(source.status()));
            nullable(node, "native_data_record_count", source.nativeDataRecordCount());
            node.put("unavailable_reason", source.unavailableReason());
        }
        ArrayNode outputs = root.putArray("persistent_outputs");
        for (PersistentOutput output : value.persistentOutputs()) {
            ObjectNode node = outputs.addObject();
            node.put("persistent_regiment_id", output.persistentRegimentId());
            ArrayNode quantities = node.putArray("same_input_q_by_chunk");
            for (Integer quantity : output.sameInputQByChunk()) {
                if (quantity == null) quantities.addNull(); else quantities.add(quantity);
            }
            ArrayNode deficits = node.putArray("effective_deficit_by_chunk");
            for (Long deficit : output.effectiveDeficitByChunk()) {
                if (deficit == null) deficits.addNull(); else deficits.add(deficit);
            }
            ArrayNode statuses = node.putArray("status_by_chunk");
            for (ChunkStatus status : output.statusByChunk()) statuses.add(wire(status));
            ArrayNode slots = node.putArray("observations_by_chunk");
            for (List<ChunkObservation> observations : output.observationsByChunk()) {
                ArrayNode slot = slots.addArray();
                for (ChunkObservation observation : observations) {
                    ObjectNode observed = slot.addObject();
                    observed.put("army_id", observation.armyId());
                    observed.put("army_regiment_id", observation.armyRegimentId());
                    observed.put("record_index", observation.recordIndex());
                    observed.put("status", wire(observation.status()));
                    observed.put("unavailable_reason", observation.unavailableReason());
                    if (observation.calculation() == null) observed.putNull("calculation");
                    else observed.set("calculation", calculationNode(observation.calculation()));
                }
            }
            node.put("all_seven_observed", output.allSevenObserved());
        }
        return encode(root);
    }

    private static ObjectNode calculationNode(ChunkCalculation value) {
        ObjectNode node = MAPPER.createObjectNode();
        node.put("same_input_q", value.sameInputQ());
        node.put("effective_deficit", value.effectiveDeficit());
        node.put("native_core_chunk_qualifies", value.nativeCoreChunkQualifies());
        nullable(node, "wrapped_product", value.wrappedProduct());
        nullable(node, "selected_scaled_numerator", value.selectedScaledNumerator());
        return node;
    }

    private static void nullable(ObjectNode node, String field, Number value) {
        if (value == null) node.putNull(field); else node.put(field, value.longValue());
    }
    private static byte[] encode(JsonNode node) {
        try {
            byte[] encoded = MAPPER.writeValueAsBytes(node);
            if (encoded.length > MAX_OUTPUT_BYTES) throw invalid("replenishment output byte budget exceeded");
            return encoded;
        }
        catch (IOException failure) { throw invalid("cannot encode replenishment value", failure); }
    }
    private static JsonNode parse(byte[] bytes) {
        if (bytes == null || bytes.length == 0 || bytes.length > MAX_INPUT_BYTES) {
            throw invalid("replenishment input byte budget exceeded or empty");
        }
        try {
            StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes));
        } catch (CharacterCodingException failure) { throw invalid("input must be UTF-8", failure); }
        try (JsonParser parser = MAPPER.createParser(bytes)) {
            JsonNode node = MAPPER.readTree(parser);
            if (node == null || parser.nextToken() != null) throw invalid("one JSON value is required");
            return node;
        } catch (IOException failure) { throw invalid("invalid replenishment JSON", failure); }
    }
    private static Set<String> fields(JsonNode node) {
        Set<String> result = new HashSet<>();
        node.fieldNames().forEachRemaining(result::add);
        return result;
    }
    private static void exactFields(JsonNode node, Set<String> expected) {
        if (node == null || !node.isObject() || !fields(node).equals(expected)) {
            throw invalid("JSON object fields differ from replenishment schema");
        }
    }
    private static void requireSchema(JsonNode node, String expected) {
        if (!node.get("schema").isTextual() || !expected.equals(node.get("schema").textValue())) {
            throw invalid("unsupported replenishment schema");
        }
    }
    private static Iterable<JsonNode> array(JsonNode node, String name) {
        if (node == null || !node.isArray() || node.size() > MAX_ROWS) throw invalid(name + " must be a bounded array");
        return node;
    }
    private static int int32(JsonNode node, String name) {
        BigInteger value = integer(node, name);
        if (value.bitLength() > 31) throw invalid(name + " must be signed int32");
        return value.intValue();
    }
    private static long int64(JsonNode node, String name) {
        BigInteger value = integer(node, name);
        if (value.bitLength() > 63) throw invalid(name + " must be signed int64");
        return value.longValue();
    }
    private static BigInteger integer(JsonNode node, String name) {
        if (node == null || !node.isIntegralNumber()) throw invalid(name + " must be an integer token");
        return node.bigIntegerValue();
    }
    private static Integer nullableInt32(JsonNode node, String name) {
        return node.isNull() ? null : int32(node, name);
    }
    private static Long nullableInt64(JsonNode node, String name) {
        return node.isNull() ? null : int64(node, name);
    }
    private static Boolean nullableBoolean(JsonNode node, String name) {
        if (node != null && node.isNull()) return null;
        if (node == null || !node.isBoolean()) throw invalid(name + " must be bool or null");
        return node.booleanValue();
    }
    private static String nullableText(JsonNode node, String name) {
        if (node != null && node.isNull()) return null;
        if (node == null || !node.isTextual()) throw invalid(name + " must be string or null");
        return node.textValue();
    }
    private static CoverageStatus coverageStatus(JsonNode node) {
        if (node == null || !node.isTextual()) throw invalid("status must be string");
        return switch (node.textValue()) {
            case "available" -> CoverageStatus.AVAILABLE;
            case "partial" -> CoverageStatus.PARTIAL;
            case "unavailable" -> CoverageStatus.UNAVAILABLE;
            default -> throw invalid("unknown coverage status");
        };
    }
    private static RecordStatus recordStatus(JsonNode node) {
        CoverageStatus status = coverageStatus(node);
        return switch (status) {
            case AVAILABLE -> RecordStatus.AVAILABLE;
            case UNAVAILABLE -> RecordStatus.UNAVAILABLE;
            case PARTIAL -> throw invalid("record status cannot be partial");
        };
    }
    private static String wire(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
    private static IllegalArgumentException invalid(String message) { return new IllegalArgumentException(message); }
    private static IllegalArgumentException invalid(String message, Exception cause) {
        return new IllegalArgumentException(message, cause);
    }
}
