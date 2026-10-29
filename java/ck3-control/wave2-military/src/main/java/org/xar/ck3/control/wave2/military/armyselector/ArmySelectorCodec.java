package org.xar.ck3.control.wave2.military.armyselector;

import static org.xar.ck3.control.wave2.military.armyselector.ArmySelectorModel.*;

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
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/** Strict versioned selector projection. SDK containers admit unrelated extension fields by declaration. */
public final class ArmySelectorCodec {
    public static final String SCHEMA = "xar.current-replenishment-selector-input/v1";
    public static final int MAX_BYTES = 262_144;
    private static final int MAX_ROWS = 4096;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(32)
                    .maxNumberLength(24).maxStringLength(MAX_BYTES).build()).build());
    private ArmySelectorCodec() {}

    public static Input decode(byte[] bytes) {
        JsonNode root = parse(bytes);
        exact(root, Set.of("schema", "armies", "snapshot", "active_war_ids"));
        if (!SCHEMA.equals(text(root.get("schema"), "schema"))) throw invalid("unsupported selector schema");
        List<Army> armies = new ArrayList<>();
        for (JsonNode army : array(root.get("armies"), "armies")) {
            object(army, "army");
            armies.add(new Army(publicId(army.get("army_id")), nullable32(army.get("soldiers"), "soldiers"),
                    nullableText(army.get("army_state"), "army_state"), nullable32(army.get("move_target_province_id"), "move_target_province_id"),
                    nullableInts(army.get("route_province_ids"), "route_province_ids"), nullable32(army.get("current_province_id"), "current_province_id")));
        }
        JsonNode s = root.get("snapshot"); object(s, "snapshot");
        Slot<List<StrengthRow>> rows;
        JsonNode strengthRows = s.get("army_strengths");
        if (strengthRows == null) rows = Slot.missing();
        else if (strengthRows.isNull()) rows = Slot.nil();
        else {
            List<StrengthRow> values = new ArrayList<>();
            for (JsonNode row : array(strengthRows, "army_strengths")) values.add(strengthRow(row));
            rows = Slot.of(List.copyOf(values));
        }
        Snapshot snapshot = new Snapshot(nullableBool(s.get("paused"), "paused"), nullableText(s.get("snapshot_id"), "snapshot_id"),
                nullableSafe(s.get("revision"), "revision"), textSlot(s.get("army_strengths_status"), "army_strengths_status"),
                nullableText(s.get("army_strengths_queried_snapshot_id"), "army_strengths_queried_snapshot_id"),
                nullableSafe(s.get("army_strengths_queried_revision"), "army_strengths_queried_revision"), rows);
        return new Input(armies, snapshot, longs(root.get("active_war_ids"), "active_war_ids"));
    }

    private static StrengthRow strengthRow(JsonNode row) {
        object(row, "strength row");
        List<DataSnapshot> data = null;
        JsonNode raw = row.get("regiment_replenishment_records_v1");
        if (raw != null && !raw.isNull()) {
            data = new ArrayList<>();
            for (JsonNode snapshot : array(raw, "regiment_replenishment_records_v1")) {
                object(snapshot, "DATA snapshot"); List<DataRecord> records = null;
                JsonNode recordRows = snapshot.get("records");
                if (recordRows != null && !recordRows.isNull()) {
                    records = new ArrayList<>();
                    for (JsonNode record : array(recordRows, "records")) {
                        object(record, "DATA record");
                        records.add(new DataRecord(int32(record.get("record_index"), "record_index"),
                                int32(record.get("persistent_regiment_id"), "persistent_regiment_id"),
                                int32(record.get("chunk_index"), "chunk_index"), nullable32(record.get("state_raw"), "state_raw"),
                                nullable32(record.get("current_soldiers"), "current_soldiers"), nullable32(record.get("maximum_soldiers"), "maximum_soldiers")));
                    }
                }
                data.add(new DataSnapshot(int32(snapshot.get("army_regiment_id"), "army_regiment_id"),
                        coverage(snapshot.get("status")), nullableBool(snapshot.get("native_loss_writer_skipped"), "native_loss_writer_skipped"), records));
            }
        }
        List<Strength> observed = null;
        JsonNode strengths = row.get("regiment_strengths");
        if (strengths != null && !strengths.isNull()) {
            observed = new ArrayList<>();
            for (JsonNode strength : array(strengths, "regiment_strengths")) {
                object(strength, "regiment strength");
                observed.add(new Strength(int32(strength.get("army_regiment_id"), "army_regiment_id"),
                        int32(strength.get("current_soldiers"), "current_soldiers"), int32(strength.get("maximum_soldiers"), "maximum_soldiers")));
            }
        }
        JsonNode ordered = row.get("scoped_ordered_refill_inputs_v1");
        return new StrengthRow(publicId(row.get("army_id")), nullable32(row.get("native_carmy_id"), "native_carmy_id"),
                coverage(row.get("status")), nullableText(row.get("scope_role"), "scope_role"),
                nullable32(row.get("current_soldiers"), "current_soldiers"), nullableLongs(row.get("war_ids"), "war_ids"),
                nonnegativeNullable32(row.get("regiment_count"), "regiment_count"), data, observed,
                ordered == null || ordered.isNull() ? null : ordered(ordered));
    }
    private static OrderedInputs ordered(JsonNode node) {
        object(node, "ordered inputs");
        Integer occurrenceCount = nonnegativeNullable32(node.get("native_persistent_occurrence_count"), "native_persistent_occurrence_count");
        Integer refreshCount = nonnegativeNullable32(node.get("native_army_refresh_occurrence_count"), "native_army_refresh_occurrence_count");
        List<Occurrence> occurrences = new ArrayList<>(); int previous = -1;
        for (JsonNode occurrence : array(node.get("persistent_occurrences"), "persistent_occurrences")) {
            exact(occurrence, Set.of("stored_index", "persistent_regiment_id"));
            int index = int32(occurrence.get("stored_index"), "stored_index");
            if (index <= previous || occurrenceCount == null || index >= occurrenceCount) throw invalid("ordered occurrence index/count differs");
            occurrences.add(new Occurrence(index, int32(occurrence.get("persistent_regiment_id"), "persistent_regiment_id"))); previous = index;
        }
        List<Integer> refresh = ints(node.get("army_refresh_occurrence_indices"), "army_refresh_occurrence_indices"); previous = -1;
        for (int index : refresh) {
            if (index <= previous || refreshCount == null || index >= refreshCount) throw invalid("refresh occurrence index/count differs");
            previous = index;
        }
        List<Persistent> persistents = new ArrayList<>(); Set<Integer> ids = new HashSet<>();
        for (JsonNode p : array(node.get("persistent_regiments"), "persistent_regiments")) {
            object(p, "persistent"); int id = int32(p.get("persistent_regiment_id"), "persistent_regiment_id");
            if (!ids.add(id)) throw invalid("duplicated persistent physical identity");
            List<Chunk> chunks = new ArrayList<>();
            for (JsonNode c : array(p.get("chunks"), "chunks")) {
                object(c, "chunk"); int index = int32(c.get("physical_index"), "physical_index");
                if (index != chunks.size() || index >= 7) throw invalid("physical positions differ");
                chunks.add(new Chunk(index, int32(c.get("current_soldiers"), "current_soldiers"), int32(c.get("maximum_soldiers"), "maximum_soldiers"),
                        int32(c.get("q_ordinal_raw"), "q_ordinal_raw"), int32(c.get("army_regiment_id_raw"), "army_regiment_id_raw"),
                        byteValue(c.get("exclusion_byte_14_raw"), "exclusion_byte_14_raw", false), int32(c.get("state_raw"), "state_raw"),
                        nullable32(c.get("origin_province_788_raw"), "origin_province_788_raw"), nullable32(c.get("origin_province_73c_raw"), "origin_province_73c_raw"),
                        magic(c.get("associated_arrg_magic_raw"), "associated_arrg_magic_raw"), nullable32(c.get("associated_arrg_resolved_full_id"), "associated_arrg_resolved_full_id"),
                        byteValue(c.get("army_byte_1d4_raw"), "army_byte_1d4_raw", true), byteValue(c.get("army_byte_1ec_raw"), "army_byte_1ec_raw", true),
                        nullableBool(c.get("native_army_in_combat"), "native_army_in_combat"), nullable32(c.get("unit_170_raw"), "unit_170_raw"),
                        magic(c.get("unit_position_province_magic_raw"), "unit_position_province_magic_raw"),
                        nullable32(c.get("unit_position_owner_resolved_full_id"), "unit_position_owner_resolved_full_id"),
                        nullable32(c.get("unit_position_holder_resolved_full_id"), "unit_position_holder_resolved_full_id"),
                        nullableBool(c.get("native_unit_position_eligible"), "native_unit_position_eligible"),
                        nullable32(c.get("owner_guard_138_raw"), "owner_guard_138_raw"), magic(c.get("owner_definition_magic_38_raw"), "owner_definition_magic_38_raw")));
            }
            persistents.add(new Persistent(id, nullable64(p.get("prepared_fraction_raw"), "prepared_fraction_raw"), chunks));
        }
        return new OrderedInputs(int32(node.get("subject_army_id"), "subject_army_id"), int32(node.get("subject_carmy_id"), "subject_carmy_id"),
                occurrenceCount, refreshCount, occurrences, refresh, persistents);
    }

    public static byte[] select(byte[] bytes) { return encode(CurrentReplenishmentSelector.select(decode(bytes))); }
    /** Persistent receipt consumer: reconstructs against caller-owned observed armies, never inventing an army row. */
    public static Selection decodeReceipt(byte[] bytes, List<Army> observedArmies) {
        JsonNode node = parse(bytes);
        exact(node, Set.of("status", "selected_army_id", "policy_basis", "input_basis", "context_basis", "active_war_ids",
                "query_needed", "candidates", "actual_after", "full_monthly_ready"));
        if (!"actual_current_strength_then_least_current_refill_opportunity".equals(text(node.get("policy_basis"), "policy_basis"))
                || !"same_capture_prepared148_ordered_occurrences".equals(text(node.get("input_basis"), "input_basis"))
                || !"held_current_nonphysical_native_context".equals(text(node.get("context_basis"), "context_basis"))) throw invalid("receipt basis differs");
        if (!Boolean.FALSE.equals(nullableBool(node.get("actual_after"), "actual_after"))
                || !Boolean.FALSE.equals(nullableBool(node.get("full_monthly_ready"), "full_monthly_ready"))) throw invalid("conditional receipt cannot claim observed/full monthly effect");
        SelectionStatus status = switch (text(node.get("status"), "status")) {
            case "not_applicable" -> SelectionStatus.NOT_APPLICABLE;
            case "current_inputs_unavailable" -> SelectionStatus.CURRENT_INPUTS_UNAVAILABLE;
            case "available" -> SelectionStatus.AVAILABLE;
            default -> throw invalid("unknown selection status");
        };
        Boolean query = nullableBool(node.get("query_needed"), "query_needed");
        if (query == null || query && status != SelectionStatus.CURRENT_INPUTS_UNAVAILABLE) throw invalid("receipt query state differs");
        Integer selectedId = node.get("selected_army_id").isNull() ? null : publicId(node.get("selected_army_id"));
        Army selected = selectedId == null ? null : observedArmies.stream().filter(army -> army.armyId() == selectedId).findFirst()
                .orElseThrow(() -> invalid("selected army is absent from observed roster"));
        List<Long> wars = longs(node.get("active_war_ids"), "active_war_ids");
        if (!wars.equals(wars.stream().filter(id -> id > 0).distinct().sorted().toList())) throw invalid("receipt wars are not sorted positive identities");
        List<Candidate> candidates = new ArrayList<>();
        for (JsonNode row : array(node.get("candidates"), "candidates")) {
            object(row, "candidate"); Set<String> expected = new HashSet<>(Set.of("army_id", "current_soldiers", "status", "conditional_current_soldiers", "native_signed_current_delta", "positive_refill_opportunity"));
            if (row.has("missing_inputs")) expected.add("missing_inputs"); exact(row, expected);
            int armyId = publicId(row.get("army_id")); int current = int32(row.get("current_soldiers"), "current_soldiers");
            Integer conditional = nullable32(row.get("conditional_current_soldiers"), "conditional_current_soldiers");
            Long delta = nullable64(row.get("native_signed_current_delta"), "native_signed_current_delta");
            Long opportunity = nullable64(row.get("positive_refill_opportunity"), "positive_refill_opportunity");
            boolean available = switch (text(row.get("status"), "candidate status")) { case "available" -> true; case "unavailable" -> false; default -> throw invalid("invalid candidate status"); };
            if (available != (conditional != null) || available && (delta == null || delta != (long) conditional - current || opportunity == null || opportunity != Math.max(0, delta))) throw invalid("candidate arithmetic/status differs");
            Slot<List<String>> missing = Slot.missing();
            if (row.has("missing_inputs")) {
                List<String> items = new ArrayList<>(); for (JsonNode item : array(row.get("missing_inputs"), "missing_inputs")) items.add(text(item, "missing input"));
                missing = Slot.of(List.copyOf(items));
            }
            candidates.add(new Candidate(armyId, current, conditional, delta, opportunity, missing));
        }
        if (status == SelectionStatus.AVAILABLE && (selected == null || candidates.size() < 2 || candidates.stream().anyMatch(candidate -> !candidate.available()))) throw invalid("available selection lacks complete candidates");
        return new Selection(selected, status, wars, query, candidates);
    }
    public static byte[] encode(Selection value) {
        ObjectNode node = JSON.createObjectNode();
        node.put("status", value.status().name().toLowerCase(Locale.ROOT));
        if (value.selected() == null) node.putNull("selected_army_id"); else node.put("selected_army_id", value.selected().armyId());
        node.put("policy_basis", "actual_current_strength_then_least_current_refill_opportunity");
        node.put("input_basis", "same_capture_prepared148_ordered_occurrences");
        node.put("context_basis", "held_current_nonphysical_native_context");
        ArrayNode wars = node.putArray("active_war_ids"); value.activeWarIds().forEach(wars::add);
        node.put("query_needed", value.queryNeeded());
        ArrayNode candidates = node.putArray("candidates");
        for (Candidate candidate : value.candidates()) {
            ObjectNode row = candidates.addObject(); row.put("army_id", candidate.armyId()); row.put("current_soldiers", candidate.currentSoldiers());
            row.put("status", candidate.available() ? "available" : "unavailable");
            number(row, "conditional_current_soldiers", candidate.conditionalCurrent());
            number(row, "native_signed_current_delta", candidate.signedDelta()); number(row, "positive_refill_opportunity", candidate.positiveOpportunity());
            if (candidate.missingInputs().presence() == Presence.VALUE) {
                ArrayNode missing = row.putArray("missing_inputs"); candidate.missingInputs().value().forEach(missing::add);
            }
        }
        node.put("actual_after", false); node.put("full_monthly_ready", false);
        return bytes(node);
    }

    /** External selector envelope keeps its original bound; rich internal consumers use the same node producer. */
    public static byte[] encodeRefresh(RaisedRegimentRefresh.Result result) { return bytes(refreshNode(result)); }

    public static ObjectNode refreshNode(RaisedRegimentRefresh.Result result) {
        ObjectNode node = JSON.createObjectNode();
        node.put("projection_kind", "conditional_raised_regiment_refresh"); node.put("source_contract_game_version", "1.20.0.3");
        node.put("army_regiment_id", result.regimentId()); node.put("status", result.ready() ? "available" : "unavailable");
        node.put("current_maximum_ready", result.ready()); node.put("actual_refresh", false);
        number(node, "current_soldiers", result.current()); number(node, "maximum_soldiers", result.maximum()); node.put("soldiers_scale", 1);
        node.put("input_basis", result.conditionalChunks() ? "conditional_chunk_writeback" : "observed_same_frame_DATA");
        ArrayNode missing = node.putArray("missing_inputs"); result.missingInputs().forEach(missing::add);
        ArrayNode contributions = node.putArray("record_contributions");
        for (RaisedRegimentRefresh.Contribution value : result.contributions()) {
            ObjectNode row = contributions.addObject(); row.put("record_index", value.recordIndex());
            row.put("persistent_regiment_id", value.persistentId()); row.put("chunk_index", value.chunkIndex());
            row.put("physical_current_soldiers", value.physicalCurrent()); row.put("effective_current_contribution", value.effectiveCurrent());
            row.put("maximum_contribution", value.maximum());
        }
        if (result.characterOverride() != null) node.put("character_override", result.characterOverride());
        return node;
    }

    static JsonNode parse(byte[] bytes) {
        if (bytes == null || bytes.length == 0 || bytes.length > MAX_BYTES) throw invalid("selector byte budget exceeded or empty");
        try {
            StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes));
            try (JsonParser parser = JSON.createParser(bytes)) {
                JsonNode root = JSON.readTree(parser);
                if (root == null || parser.nextToken() != null) throw invalid("one JSON value required");
                return root;
            }
        } catch (IOException failure) { throw new IllegalArgumentException("invalid strict selector UTF-8/JSON", failure); }
    }
    private static byte[] bytes(JsonNode node) {
        try { byte[] value = JSON.writeValueAsBytes(node); if (value.length > MAX_BYTES) throw invalid("selector output exceeds budget"); return value; }
        catch (IOException failure) { throw new IllegalArgumentException("cannot encode selector", failure); }
    }
    private static void number(ObjectNode node, String field, Number value) { if (value == null) node.putNull(field); else node.put(field, value.longValue()); }
    private static void object(JsonNode node, String name) { if (node == null || !node.isObject()) throw invalid(name + " must be object"); }
    private static void exact(JsonNode node, Set<String> expected) {
        object(node, "schema"); Set<String> actual = new HashSet<>(); node.fieldNames().forEachRemaining(actual::add);
        if (!actual.equals(expected)) throw invalid("selector field contract differs");
    }
    private static Iterable<JsonNode> array(JsonNode node, String name) { if (node == null || !node.isArray() || node.size() > MAX_ROWS) throw invalid(name + " must be bounded array"); return node; }
    private static String text(JsonNode node, String name) { if (node == null || !node.isTextual()) throw invalid(name + " must be text"); return node.textValue(); }
    private static String nullableText(JsonNode node, String name) { return node == null || node.isNull() ? null : text(node, name); }
    private static Slot<String> textSlot(JsonNode node, String name) { return node == null ? Slot.missing() : node.isNull() ? Slot.nil() : Slot.of(text(node, name)); }
    private static BigInteger integer(JsonNode node, String name) { if (node == null || !node.isIntegralNumber()) throw invalid(name + " must be integer token"); return node.bigIntegerValue(); }
    private static int int32(JsonNode node, String name) { BigInteger n = integer(node, name); if (n.bitLength() > 31) throw invalid(name + " must be signed int32"); return n.intValue(); }
    private static int publicId(JsonNode node) { int id = int32(node, "army_id"); if (id < 0) throw invalid("army_id must be public nonnegative CUnit"); return id; }
    private static Integer nullable32(JsonNode node, String name) { return node == null || node.isNull() ? null : int32(node, name); }
    private static Integer nonnegativeNullable32(JsonNode node, String name) { Integer n = nullable32(node, name); if (n != null && n < 0) throw invalid(name + " must be nonnegative"); return n; }
    private static Long nullable64(JsonNode node, String name) { if (node == null || node.isNull()) return null; BigInteger n = integer(node, name); if (n.bitLength() > 63) throw invalid(name + " must be signed int64"); return n.longValue(); }
    private static Long nullableSafe(JsonNode node, String name) { Long n = nullable64(node, name); if (n != null && (n < -9_007_199_254_740_991L || n > 9_007_199_254_740_991L)) throw invalid(name + " exceeds safe integer domain"); return n; }
    private static Long magic(JsonNode node, String name) { Long n = nullable64(node, name); if (n != null && (n < 0 || n > 0xffff_ffffL)) throw invalid(name + " must be uint32 or null"); return n; }
    private static Integer byteValue(JsonNode node, String name, boolean nullable) { Integer n = nullable ? nullable32(node, name) : int32(node, name); if (n != null && (n < 0 || n > 255)) throw invalid(name + " must be byte"); return n; }
    private static Boolean nullableBool(JsonNode node, String name) { if (node == null || node.isNull()) return null; if (!node.isBoolean()) throw invalid(name + " must be bool or null"); return node.booleanValue(); }
    private static List<Integer> ints(JsonNode node, String name) { List<Integer> result = new ArrayList<>(); for (JsonNode n : array(node, name)) result.add(int32(n, name)); return List.copyOf(result); }
    private static List<Integer> nullableInts(JsonNode node, String name) { return node == null || node.isNull() ? null : ints(node, name); }
    private static List<Long> longs(JsonNode node, String name) { List<Long> result = new ArrayList<>(); for (JsonNode n : array(node, name)) result.add(nullableSafeRequired(n, name)); return List.copyOf(result); }
    private static long nullableSafeRequired(JsonNode node, String name) { Long n = nullableSafe(node, name); if (n == null) throw invalid(name + " requires integer"); return n; }
    private static List<Long> nullableLongs(JsonNode node, String name) { return node == null || node.isNull() ? null : longs(node, name); }
    private static Coverage coverage(JsonNode node) {
        return switch (text(node, "status")) { case "available" -> Coverage.AVAILABLE; case "partial" -> Coverage.PARTIAL;
            case "unavailable" -> Coverage.UNAVAILABLE; default -> throw invalid("unknown coverage status"); };
    }
    private static IllegalArgumentException invalid(String message) { return new IllegalArgumentException(message); }
}
