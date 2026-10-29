package org.xar.ck3.control.wave3.governance.educationoptions;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsModel.*;

/** Strict projection of the complete two legacy education-option validators, not the ordinary source qualifier. */
public final class EducationOptionsCodec {
    public static final String INPUT_SCHEMA = "xar.java.education-option-facts-input.v1";
    /** Transport budget, not an invented limit on the original unbounded requested-key list. */
    public static final int BYTE_BUDGET = 2_097_152;
    private static final ObjectMapper MAPPER = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private EducationOptionsCodec() { }
    public static Input decode(byte[] raw) {
        return projectParsedInput(parseBoundary(raw));
    }
    /** Shared leaf field contract only; owning context, roles and source qualification remain separate. */
    public static Materialization decodeMaterialization(byte[] raw) {
        return materialization(parseBoundary(raw));
    }
    /** Retains missing intent as null and explicit empty option intent as an empty array. */
    public static byte[] encodeMaterialization(Materialization value) {
        return encode(materializationNode(java.util.Objects.requireNonNull(value)));
    }
    static JsonNode parseBoundary(byte[] raw) {
        StrictJson.require(raw != null && raw.length > 0 && raw.length <= BYTE_BUDGET, "education option finite input transport budget");
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            JsonNode root = MAPPER.readTree(text); StrictJson.require(root != null, "JSON value required"); return root;
        } catch (IOException error) { throw new IllegalArgumentException("invalid education-option UTF-8, duplicate fields or JSON", error); }
    }
    /** Internal parser; no public raw-input path bypasses the leaf byte guard. */
    static Input projectParsedInput(JsonNode parsed) {
        StrictJson.object(parsed, Set.of("schema", "context"));
        StrictJson.require(text(parsed, "schema").equals(INPUT_SCHEMA), "education option input schema");
        JsonNode context = object(required(parsed, "context"));
        Optional<Rows> rows = context.has("education_option_rows") ? Optional.of(rows(context.get("education_option_rows"))) : Optional.empty();
        Optional<Materialization> materialization = context.has("education_request_materialization")
                ? Optional.of(materialization(context.get("education_request_materialization"))) : Optional.empty();
        Optional<Pair> roles = Optional.empty();
        if (materialization.isPresent() && materialization.get().status() == Availability.AVAILABLE && materialization.get().pair().isPresent()) {
            JsonNode node = object(required(context, "effective_roles"));
            roles = Optional.of(new Pair(id(node, "secondary_recipient_id"), id(node, "secondary_actor_id")));
        }
        return new Input(text(context, "exact_build"), text(context, "interaction_key"), status(context), rows, materialization, roles);
    }
    public static byte[] encodeInput(Input value) {
        ObjectNode root = StrictJson.object(); root.put("schema", INPUT_SCHEMA); root.set("context", contextNode(value));
        return encode(root);
    }
    public static byte[] encodeProjection(Input value) {
        ObjectNode root = StrictJson.object(); value.rows().ifPresent(rows -> root.set("education_option_rows", rowsNode(rows)));
        value.materialization().ifPresent(materialization -> root.set("education_request_materialization", materializationNode(materialization)));
        return encode(root);
    }
    static byte[] encode(JsonNode root) {
        try {
            byte[] raw = MAPPER.writeValueAsBytes(root); StrictJson.require(raw.length <= BYTE_BUDGET, "education option finite output transport budget"); return raw;
        } catch (IOException error) { throw new IllegalArgumentException("education option JSON serialization failed", error); }
    }
    static Rows rows(JsonNode node) {
        StrictJson.object(node, Set.of("status", "rows", "unavailable_reason")); JsonNode entries = required(node, "rows");
        StrictJson.require(entries.isArray() && entries.size() <= 4096, "ordered bounded education option rows required");
        List<Row> rows = new ArrayList<>();
        for (JsonNode entry : entries) {
            StrictJson.object(entry, Set.of("declared_ordinal", "flag_full_u32", "canonical_flag_key", "selected", "bank_value_u8", "ordinal_selected"));
            rows.add(new Row(integer(entry, "declared_ordinal", 0, 4_294_967_295L), integer(entry, "flag_full_u32", 0, 4_294_967_295L),
                    nullableText(entry, "canonical_flag_key"), bool(entry, "selected"), (int) integer(entry, "bank_value_u8", 0, 255), bool(entry, "ordinal_selected")));
        }
        return new Rows(status(node), rows, nullableText(node, "unavailable_reason"));
    }
    static Materialization materialization(JsonNode node) {
        StrictJson.object(node, Set.of("status", "child_full_id", "guardian_full_id", "requested_option_keys", "pair_matches", "option_keys_match", "unavailable_reason"));
        JsonNode child = required(node, "child_full_id"), guardian = required(node, "guardian_full_id");
        StrictJson.require(child.isNull() == guardian.isNull(), "complete materialized pair required");
        Optional<Pair> pair = child.isNull() ? Optional.empty() : Optional.of(new Pair(id(node, "child_full_id"), id(node, "guardian_full_id")));
        JsonNode keysNode = required(node, "requested_option_keys"); Optional<List<String>> keys = Optional.empty();
        if (!keysNode.isNull()) {
            StrictJson.require(keysNode.isArray(), "original requested option list required"); List<String> values = new ArrayList<>();
            for (JsonNode key : keysNode) { values.add(EducationOptionsModel.key(StrictJson.text(key))); } keys = Optional.of(values);
        }
        return new Materialization(status(node), pair, keys, nullableBool(node, "pair_matches"), nullableBool(node, "option_keys_match"), nullableText(node, "unavailable_reason"));
    }
    private static ObjectNode contextNode(Input input) {
        ObjectNode result = StrictJson.object(); result.put("exact_build", input.exactBuild()); result.put("interaction_key", input.interactionKey());
        result.put("status", input.contextStatus().wire()); input.rows().ifPresent(rows -> result.set("education_option_rows", rowsNode(rows)));
        input.materialization().ifPresent(materialization -> result.set("education_request_materialization", materializationNode(materialization)));
        input.finalRoles().ifPresent(pair -> { ObjectNode roles = result.putObject("effective_roles"); roles.put("secondary_recipient_id", pair.childFullId()); roles.put("secondary_actor_id", pair.guardianFullId()); });
        return result;
    }
    static ObjectNode rowsNode(Rows value) {
        ObjectNode result = StrictJson.object(); result.put("status", value.status().wire()); var rows = result.putArray("rows");
        for (Row row : value.rows()) {
            ObjectNode node = rows.addObject(); node.put("declared_ordinal", row.declaredOrdinal()); node.put("flag_full_u32", row.flagFullU32());
            node.put("canonical_flag_key", row.canonicalFlagKey()); node.put("selected", row.selected()); node.put("bank_value_u8", row.bankValueU8()); node.put("ordinal_selected", row.ordinalSelected());
        }
        result.put("unavailable_reason", value.unavailableReason()); return result;
    }
    static ObjectNode materializationNode(Materialization value) {
        ObjectNode result = StrictJson.object(); result.put("status", value.status().wire()); result.put("child_full_id", value.pair().map(Pair::childFullId).orElse(null));
        result.put("guardian_full_id", value.pair().map(Pair::guardianFullId).orElse(null));
        if (value.requestedOptionKeys().isEmpty()) { result.putNull("requested_option_keys"); }
        else { var keys = result.putArray("requested_option_keys"); value.requestedOptionKeys().get().forEach(keys::add); }
        result.put("pair_matches", value.pairMatches()); result.put("option_keys_match", value.optionKeysMatch()); result.put("unavailable_reason", value.unavailableReason()); return result;
    }
    static Availability status(JsonNode node) {
        String value = text(node, "status");
        for (Availability status : Availability.values()) { if (status.wire().equals(value)) { return status; } }
        throw new IllegalArgumentException("known availability status required");
    }
    static JsonNode object(JsonNode node) { StrictJson.require(node != null && node.isObject(), "context object required"); return node; }
    static JsonNode required(JsonNode node, String key) { JsonNode value = node.get(key); StrictJson.require(value != null, "required field: " + key); return value; }
    static String text(JsonNode node, String key) { return StrictJson.text(required(node, key)); }
    private static String nullableText(JsonNode node, String key) { JsonNode value = required(node, key); return value.isNull() ? null : StrictJson.text(value); }
    private static boolean bool(JsonNode node, String key) { JsonNode value = required(node, key); StrictJson.require(value.isBoolean(), "exact Boolean token required"); return value.booleanValue(); }
    private static Boolean nullableBool(JsonNode node, String key) { return required(node, key).isNull() ? null : bool(node, key); }
    private static long integer(JsonNode node, String key, long minimum, long maximum) { return StrictJson.integer(required(node, key), minimum, maximum); }
    static long id(JsonNode node, String key) { return integer(node, key, 1, 4_294_967_294L); }
}
