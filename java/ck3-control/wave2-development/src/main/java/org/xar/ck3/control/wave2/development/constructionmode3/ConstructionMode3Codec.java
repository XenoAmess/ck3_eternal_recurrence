package org.xar.ck3.control.wave2.development.constructionmode3;

import static org.xar.ck3.control.wave2.development.constructionmode3.ConstructionMode3.*;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.DecimalNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.development.ConstructionInputValidation;

/** Strict copied native packet parser and the original independent world/province consumer projections. */
public final class ConstructionMode3Codec {
    public static final String REQUEST_SCHEMA = "xar.construction-mode3-input.v1";
    public static final int MAX_BYTES = 65_536;
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final Set<String> PACKET_FIELDS = Set.of("schema", "source_executable_sha256", "current_frame_observed", "failure",
            "snapshot_revision", "date_raw", "player_character_id", "holdings");
    private static final Set<String> INPUT_FIELDS = Set.of("snapshot_revision", "province_id", "unavailable_input", "context_predicate_2c25010",
            "inputs_observed", "all_reached_inputs_observed", "observed_native_producer_call", "per_building_attribution", "realized_holder_net",
            "loaded_publisher_718_raw", "loaded_key_3f_raw", "factor_before_context", "context_factor_raw", "owner_factor_raw", "conditional_aggregate_raw",
            "selected_a3_or_a4_key", "selected_a6_or_a7_key", "context_dynamic_key", "child_28be0b0_signed_eax", "child_28b9300_signed_eax", "components");
    private ConstructionMode3Codec() { }

    /** JSON-domain equality output. Unconsumed SDK extension numbers are retained outside the integer-only packet. */
    public static byte[] evaluate(byte[] raw) {
        return evaluateProjection(StrictJson.parse(raw, MAX_BYTES));
    }

    /** Codec composition only: retain parsed token categories; never reencode before native validation. */
    public static byte[] evaluateProjection(JsonNode parsedRequest) {
        JsonNode request = StrictJson.object(parsedRequest, Set.of("schema", "world", "source_frame", "build", "barony_title_id", "province_id"));
        StrictJson.require(REQUEST_SCHEMA.equals(StrictJson.text(request.get("schema"))), "construction mode3 request schema required");
        JsonNode world = sdkObject(request.get("world")); JsonNode source = sdkObject(request.get("source_frame"));
        JsonNode build = StrictJson.object(request.get("build"), Set.of("game_version", "executable_sha256"));
        BuildIdentity identity = new BuildIdentity(StrictJson.text(build.get("game_version")), StrictJson.text(build.get("executable_sha256")));
        int barony = Math.toIntExact(ConstructionInputValidation.read(() -> StrictJson.integer(request.get("barony_title_id"), Integer.MIN_VALUE, Integer.MAX_VALUE)));
        int province = Math.toIntExact(ConstructionInputValidation.read(() -> StrictJson.integer(request.get("province_id"), Integer.MIN_VALUE, Integer.MAX_VALUE)));
        Normalization normalized;
        if (!world.has(FIELD)) { normalized = new Absent(); }
        else if (world.get(FIELD).isNull()) { normalized = new ExplicitNull(); }
        else {
            try {
                exact(world.get(FIELD), PACKET_FIELDS, FIELD);
                require(identity.equals(new BuildIdentity("1.20.0.4", SHA))
                        && world.get(FIELD).get("schema").isTextual() && world.get(FIELD).get("schema").textValue().equals(SCHEMA)
                        && world.get(FIELD).get("source_executable_sha256").isTextual() && world.get(FIELD).get("source_executable_sha256").textValue().equals(SHA),
                        FIELD + " requires its exact actual4 source identity");
                Packet packet = parsePacket(world.get(FIELD));
                List<Identity> identities = new ArrayList<>(); JsonNode rows = world.get("active_constructions");
                if (packet.currentFrameObserved()) {
                    require(rows != null && rows.isArray(), FIELD + " lacks this query's held province identities");
                    for (JsonNode row : rows) {
                        if (row.isObject()) { identities.add(new Identity(optionalI32(row.get("barony_title_id")), optionalI32(row.get("province_id")))); }
                    }
                }
                normalized = normalize(packet, frame(source, "native_revision", "actor_character_id"),
                        new WorldFrame(frame(world, "snapshot_revision", "player_character_id"), identities), identity);
            } catch (InvalidSource invalid) { normalized = new SourceRed(invalid.getMessage()); }
        }
        ObjectNode copied = ((ObjectNode) world).deepCopy();
        if (normalized instanceof Normalized observed) { copied.set(FIELD, encodePacket(observed.packet())); }
        ObjectNode output = StrictJson.object(); output.set("world", copied); output.set("observation", state(normalized));
        ObjectNode projection = StrictJson.object();
        if (!(normalized instanceof Absent)) {
            ProvinceProjection selected = province(normalized, barony, province); ObjectNode observation = StrictJson.object();
            observation.put("status", selected.state().status().wire()); nullableText(observation, "reason", selected.state().reason());
            if (selected.inputs() == null) { observation.putNull("inputs"); } else { observation.set("inputs", encodeInputs(selected.inputs())); }
            observation.put("barony_title_id", barony); observation.put("province_id", province); observation.set("source_frame", source.deepCopy());
            observation.put("observed_native_producer_call", false); observation.put("per_building_attribution", false); observation.put("realized_holder_net", false);
            observation.put("conditional_aggregate_kind", "source_software_projection");
            if (selected.includePacketIdentity()) { observation.put("schema", SCHEMA); observation.put("source_executable_sha256", SHA); }
            projection.set(FIELD, observation);
        }
        output.set("province_observation", projection);
        try {
            byte[] encoded = JSON.writeValueAsBytes(retainFloatingTokenKind(output));
            StrictJson.require(encoded.length <= MAX_BYTES, "mode3 JSON-domain output exceeds bounded input/output budget"); return encoded;
        } catch (JsonProcessingException invalid) { throw new IllegalArgumentException("mode3 JSON serialization failed", invalid); }
    }
    private static JsonNode retainFloatingTokenKind(JsonNode node) {
        if (node.isFloatingPointNumber() && node.decimalValue().scale() == 0) {
            return DecimalNode.valueOf(node.decimalValue().setScale(1));
        }
        if (node.isObject()) {
            ObjectNode object = (ObjectNode) node;
            object.properties().forEach(entry -> object.set(entry.getKey(), retainFloatingTokenKind(entry.getValue())));
        } else if (node.isArray()) {
            ArrayNode array = (ArrayNode) node;
            for (int index = 0; index < array.size(); index++) { array.set(index, retainFloatingTokenKind(array.get(index))); }
        }
        return node;
    }

    public static Packet decodePacket(byte[] raw) { return parsePacket(StrictJson.parse(raw, MAX_BYTES)); }
    public static byte[] encode(Packet packet) { return StrictJson.canonical(encodePacket(packet), MAX_BYTES); }

    private static Packet parsePacket(JsonNode node) {
        exact(node, PACKET_FIELDS, FIELD);
        String schema = text(node.get("schema"), FIELD + ".schema"); String sha = text(node.get("source_executable_sha256"), FIELD + ".source_executable_sha256");
        boolean observed = bool(node.get("current_frame_observed"), FIELD + ".current_frame_observed");
        String failureText = text(node.get("failure"), FIELD + ".failure"); Failure failure = null;
        for (Failure value : Failure.values()) { if (value.wire().equals(failureText)) { failure = value; } }
        require(failure != null, FIELD + ".failure differs from the native model failure enum");
        Frame frame = new Frame(number(node.get("snapshot_revision"), FIELD + ".snapshot_revision", 64, true, true),
                i32(node.get("date_raw"), FIELD + ".date_raw", true), i32(node.get("player_character_id"), FIELD + ".player_character_id", true));
        JsonNode rows = node.get("holdings"); require(rows.isArray(), FIELD + ".holdings must retain the held source order"); List<Holding> holdings = new ArrayList<>();
        for (int index = 0; index < rows.size(); index++) {
            String path = FIELD + ".holdings[" + index + "]"; JsonNode row = rows.get(index); exact(row, Set.of("barony_title_id", "province_id", "inputs"), path);
            holdings.add(new Holding(i32(row.get("barony_title_id"), path + ".barony_title_id", false),
                    i32(row.get("province_id"), path + ".province_id", false), inputs(row.get("inputs"), path + ".inputs")));
        }
        return new Packet(schema, sha, observed, failure, frame, holdings);
    }
    private static Inputs inputs(JsonNode node, String path) {
        exact(node, INPUT_FIELDS, path);
        for (String flag : List.of("observed_native_producer_call", "per_building_attribution", "realized_holder_net")) {
            require(!bool(node.get(flag), path + "." + flag), path + " cannot grant a native producer invocation, building attribution or realized net");
        }
        RawValues raw = new RawValues(q64(node, "loaded_publisher_718_raw", path), q64(node, "loaded_key_3f_raw", path), q64(node, "factor_before_context", path),
                q64(node, "context_factor_raw", path), q64(node, "owner_factor_raw", path), q64(node, "conditional_aggregate_raw", path));
        Keys keys = new Keys(u16(node, "selected_a3_or_a4_key", path), u16(node, "selected_a6_or_a7_key", path), u16(node, "context_dynamic_key", path));
        Children children = new Children(i32(node.get("child_28be0b0_signed_eax"), path + ".child_28be0b0_signed_eax", true),
                i32(node.get("child_28b9300_signed_eax"), path + ".child_28b9300_signed_eax", true));
        JsonNode rows = node.get("components"); require(rows.isArray(), path + ".components must retain native component order"); List<Component> components = new ArrayList<>();
        for (int index = 0; index < rows.size(); index++) {
            String location = path + ".components[" + index + "]"; JsonNode row = rows.get(index);
            exact(row, Set.of("call_rva", "key_u16", "reached", "raw_q64", "unavailable_input"), location);
            components.add(new Component(number(row.get("call_rva"), location + ".call_rva", 32, true, false).longValueExact(),
                    number(row.get("key_u16"), location + ".key_u16", 16, true, false).intValueExact(), bool(row.get("reached"), location + ".reached"),
                    number(row.get("raw_q64"), location + ".raw_q64", 64, false, true), text(row.get("unavailable_input"), location + ".unavailable_input")));
        }
        return new Inputs(number(node.get("snapshot_revision"), path + ".snapshot_revision", 64, true, true), i32(node.get("province_id"), path + ".province_id", true),
                text(node.get("unavailable_input"), path + ".unavailable_input"), nullableBool(node.get("context_predicate_2c25010"), path + ".context_predicate_2c25010"),
                bool(node.get("inputs_observed"), path + ".inputs_observed"), bool(node.get("all_reached_inputs_observed"), path + ".all_reached_inputs_observed"), raw, keys, children, components);
    }
    private static ObjectNode encodePacket(Packet packet) {
        ObjectNode result = StrictJson.object(); result.put("schema", packet.schema()); result.put("source_executable_sha256", packet.sourceSha256());
        result.put("current_frame_observed", packet.currentFrameObserved()); result.put("failure", packet.failure().wire());
        nullableNumber(result, "snapshot_revision", packet.frame().revision()); nullableNumber(result, "date_raw", packet.frame().dateRaw());
        nullableNumber(result, "player_character_id", packet.frame().actorId()); ArrayNode rows = result.putArray("holdings");
        for (Holding holding : packet.holdings()) {
            ObjectNode row = rows.addObject(); row.put("barony_title_id", holding.baronyId()); row.put("province_id", holding.provinceId()); row.set("inputs", encodeInputs(holding.inputs()));
        }
        return result;
    }
    private static ObjectNode encodeInputs(Inputs inputs) {
        ObjectNode node = StrictJson.object(); nullableNumber(node, "snapshot_revision", inputs.revision()); nullableNumber(node, "province_id", inputs.provinceId());
        node.put("unavailable_input", inputs.unavailableInput());
        if (inputs.contextPredicate() == null) { node.putNull("context_predicate_2c25010"); } else { node.put("context_predicate_2c25010", inputs.contextPredicate()); }
        node.put("inputs_observed", inputs.inputsObserved()); node.put("all_reached_inputs_observed", inputs.allReachedInputsObserved());
        node.put("observed_native_producer_call", false); node.put("per_building_attribution", false); node.put("realized_holder_net", false);
        nullableNumber(node, "loaded_publisher_718_raw", inputs.raw().loadedPublisher718()); nullableNumber(node, "loaded_key_3f_raw", inputs.raw().loadedKey3f());
        nullableNumber(node, "factor_before_context", inputs.raw().factorBeforeContext()); nullableNumber(node, "context_factor_raw", inputs.raw().contextFactor());
        nullableNumber(node, "owner_factor_raw", inputs.raw().ownerFactor()); nullableNumber(node, "conditional_aggregate_raw", inputs.raw().conditionalAggregate());
        nullableNumber(node, "selected_a3_or_a4_key", inputs.keys().selectedA3OrA4()); nullableNumber(node, "selected_a6_or_a7_key", inputs.keys().selectedA6OrA7());
        nullableNumber(node, "context_dynamic_key", inputs.keys().contextDynamic()); nullableNumber(node, "child_28be0b0_signed_eax", inputs.children().child28be0b0());
        nullableNumber(node, "child_28b9300_signed_eax", inputs.children().child28b9300()); ArrayNode components = node.putArray("components");
        for (Component value : inputs.components()) {
            ObjectNode row = components.addObject(); row.put("call_rva", value.callRva()); row.put("key_u16", value.keyU16()); row.put("reached", value.reached());
            nullableNumber(row, "raw_q64", value.rawQ64()); row.put("unavailable_input", value.unavailableInput());
        }
        return node;
    }
    private static ObjectNode state(Normalization normalization) {
        ObjectNode result = StrictJson.object(); if (normalization instanceof Absent) { return result; }
        State state = switch (normalization) {
            case ExplicitNull ignored -> new State(Status.OBSERVATION_UNAVAILABLE, "native_mode3_inputs_explicitly_null");
            case Normalized present -> present.state();
            case SourceRed red -> new State(Status.SOURCE_RED, red.reason());
            case Absent ignored -> throw new IllegalStateException("handled absent state");
        };
        result.put("native_mode3_inputs_status", state.status().wire()); nullableText(result, "native_mode3_inputs_reason", state.reason()); return result;
    }
    private static Frame frame(JsonNode node, String revisionKey, String actorKey) {
        return new Frame(optionalU64(node.get(revisionKey)), optionalI32(node.get("date_raw")), optionalI32(node.get(actorKey)));
    }
    private static BigInteger optionalU64(JsonNode node) { return node == null || node.isNull() ? null : StrictJson.integer(node, BigInteger.ZERO, StrictJson.UINT64_MAX); }
    private static Integer optionalI32(JsonNode node) { return node == null || node.isNull() ? null : Math.toIntExact(StrictJson.integer(node, Integer.MIN_VALUE, Integer.MAX_VALUE)); }
    private static JsonNode sdkObject(JsonNode node) { StrictJson.require(node != null && node.isObject(), "declared SDK object projection required"); return node; }
    private static void exact(JsonNode node, Set<String> fields, String path) {
        Set<String> actual = new HashSet<>(); if (node != null && node.isObject()) { node.fieldNames().forEachRemaining(actual::add); }
        require(node != null && node.isObject() && actual.equals(fields), path + " requires exactly its native copied fields");
    }
    private static BigInteger number(JsonNode node, String path, int bits, boolean unsigned, boolean nullable) {
        if (nullable && node != null && node.isNull()) { return null; }
        BigInteger minimum = unsigned ? BigInteger.ZERO : BigInteger.ONE.shiftLeft(bits - 1).negate();
        BigInteger maximum = BigInteger.ONE.shiftLeft(unsigned ? bits : bits - 1).subtract(BigInteger.ONE);
        require(node != null && node.isIntegralNumber() && node.bigIntegerValue().compareTo(minimum) >= 0 && node.bigIntegerValue().compareTo(maximum) <= 0,
                path + " must retain a native " + (unsigned ? "unsigned" : "signed") + bits + " integer"); return node.bigIntegerValue();
    }
    private static Integer i32(JsonNode node, String path, boolean nullable) {
        BigInteger value = number(node, path, 32, false, nullable); return value == null ? null : value.intValueExact();
    }
    private static BigInteger q64(JsonNode node, String key, String path) { return number(node.get(key), path + "." + key, 64, false, true); }
    private static Integer u16(JsonNode node, String key, String path) { BigInteger value = number(node.get(key), path + "." + key, 16, true, true); return value == null ? null : value.intValueExact(); }
    private static boolean bool(JsonNode node, String path) { require(node != null && node.isBoolean(), path + " must retain a native boolean"); return node.booleanValue(); }
    private static Boolean nullableBool(JsonNode node, String path) { return node != null && node.isNull() ? null : bool(node, path); }
    private static String text(JsonNode node, String path) {
        require(node != null && node.isTextual(), path + " must retain its native source/failure text");
        if (!node.textValue().isEmpty()) { StrictJson.text(node.textValue()); } return node.textValue();
    }
    private static void nullableNumber(ObjectNode node, String key, BigInteger value) { if (value == null) { node.putNull(key); } else { node.put(key, value); } }
    private static void nullableNumber(ObjectNode node, String key, Integer value) { if (value == null) { node.putNull(key); } else { node.put(key, value); } }
    private static void nullableText(ObjectNode node, String key, String value) { if (value == null) { node.putNull(key); } else { node.put(key, value); } }
}
