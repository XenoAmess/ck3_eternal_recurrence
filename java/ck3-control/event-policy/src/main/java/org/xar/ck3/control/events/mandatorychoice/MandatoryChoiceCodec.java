package org.xar.ck3.control.events.mandatorychoice;

import static org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
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
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;

/** Strict v1 JSON boundary. Native source/relation evidence is opaque, retained and never authority. */
public final class MandatoryChoiceCodec {
    private static final int MAX_BYTES = 65_536;
    private static final BigInteger SIGNED64_MIN = BigInteger.ONE.shiftLeft(63).negate();
    private static final BigInteger UINT64_MAX = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private static final Set<String> WINDOW_FIELDS = Set.of("schema", "query_id", "frame_binding", "window_id",
            "window_instance_id", "window_type", "source_identity", "typed_window_relation", "blocking_proof",
            "blocks_simulation", "exclusive_modal", "blocks_input", "choices_complete", "complete", "choices",
            "presentation_order_proof");
    private static final Set<String> FRAME_FIELDS = Set.of("game_pid", "connection_generation", "revision",
            "native_revision", "date_raw", "actor_character_id", "episode_run_id", "snapshot_id");
    private static final Set<String> CHOICE_FIELDS = Set.of("choice_id", "visible", "enabled", "is_choice",
            "role", "bounds", "rendered_index", "native_index", "action_token", "existing_typed_action",
            "label", "label_source");
    private MandatoryChoiceCodec() { }

    public static NativeWindow decode(byte[] raw) {
        ObjectNode row = object(parse(raw));
        allowed(row, WINDOW_FIELDS);
        if (row.has("schema")) {
            require("xar.native-mandatory-choice-window/v1".equals(text(row.get("schema"), false)), "native schema");
        }
        FrameBinding frame = frame(row.get("frame_binding"));
        Field<ChoiceIdentity> windowId = field(row, "window_id", MandatoryChoiceCodec::identity);
        String windowType = text(row.get("window_type"), false);
        Field<String> queryId = field(row, "query_id", value -> text(value, false));
        Field<ChoiceIdentity> instance = field(row, "window_instance_id", MandatoryChoiceCodec::identity);
        Field<EvidenceDocument> source = field(row, "source_identity", value -> document(object(value)));
        if (row.hasNonNull("typed_window_relation")) { object(row.get("typed_window_relation")); }
        field(row, "blocks_simulation", MandatoryChoiceCodec::bool);
        field(row, "exclusive_modal", MandatoryChoiceCodec::bool);
        field(row, "blocks_input", MandatoryChoiceCodec::bool);
        field(row, "complete", MandatoryChoiceCodec::bool);
        Optional<EvidenceDocument> blockingProof = blocking(row);
        Field<Boolean> complete = row.has("choices_complete")
                ? field(row, "choices_complete", MandatoryChoiceCodec::bool)
                : field(row, "complete", MandatoryChoiceCodec::bool);
        Field<String> presentation = Field.missing();
        if (row.has("presentation_order_proof")) {
            JsonNode proof = row.get("presentation_order_proof");
            if (proof.isNull()) { presentation = Field.nullValue(); }
            else { presentation = field(object(proof), "kind", value -> text(value, false)); }
        }
        JsonNode choices = row.get("choices");
        require(choices != null && choices.isArray() && choices.size() <= 256, "bounded native choice list required");
        List<ChoiceEntry> entries = new ArrayList<>();
        for (int index = 0; index < choices.size(); index++) {
            JsonNode choice = choices.get(index);
            entries.add(choice.isObject() ? choice(object(choice), index) : new NonChoiceRow(index));
        }
        return new NativeWindow(frame, windowId, windowType, queryId, instance, source, blockingProof,
                complete.hasValue() && complete.value(), presentation, entries, document(choices), document(row));
    }

    public static FrameBinding decodeFrame(byte[] raw) { return frame(parse(raw)); }

    public static byte[] encodeWindow(NativeWindow window) {
        return bounded(window.original().json().getBytes(StandardCharsets.UTF_8));
    }

    public static byte[] select(byte[] raw, Mode mode, Optional<FrameBinding> expectedFrame) {
        return encodeDecision(MandatoryChoicePolicy.select(decode(raw), expectedFrame, mode));
    }

    public static byte[] encodeDecision(Decision decision) {
        ObjectNode out = JSON.createObjectNode();
        out.put("status", decision.status().wire());
        out.put("reason", decision.reason());
        NativeWindow window = decision.evidence().window();
        if (decision.selectedChoice().isPresent()) {
            NativeChoice choice = decision.selectedChoice().orElseThrow();
            out.set("selected_choice_id", identityNode(choice.identity()));
            out.set("action_token", choice.actionToken().hasValue()
                    ? JSON.getNodeFactory().textNode(choice.actionToken().value()) : JSON.getNodeFactory().nullNode());
            out.set("selected_choice", read(choice.original()));
            if (choice.nativeIndex().hasValue()) {
                out.put("native_index", choice.nativeIndex().value());
                out.put("public_option_number", choice.nativeIndex().value().add(BigInteger.ONE));
            } else { out.putNull("native_index"); out.putNull("public_option_number"); }
            out.set("frame_binding", read(window.frame().original()));
            out.set("window_id", fieldIdentityNode(window.windowId()));
            out.put("semantic_optimal", false); out.put("material_effects_verified", false);
        } else { out.putNull("selected_choice_id"); out.putNull("action_token"); }
        out.set("evidence", evidence(decision.evidence()));
        return bounded(json(sorted(out)).getBytes(StandardCharsets.UTF_8));
    }

    private static ObjectNode evidence(Evidence evidence) {
        NativeWindow window = evidence.window();
        ObjectNode out = JSON.createObjectNode();
        out.set("frame_binding", read(window.frame().original()));
        out.set("window_id", fieldIdentityNode(window.windowId()));
        out.put("window_type", window.windowType());
        out.set("blocking_proof", window.blockingProof().map(MandatoryChoiceCodec::read)
                .orElseGet(() -> JSON.getNodeFactory().nullNode()));
        out.set("choices", read(window.originalChoices()));
        ArrayNode excluded = out.putArray("excluded");
        for (Excluded item : evidence.excluded()) {
            ObjectNode row = excluded.addObject(); row.put("index", item.index());
            item.choiceId().ifPresent(identity -> row.set("choice_id", identityNode(identity)));
            row.put("reason", item.reason());
        }
        ArrayNode duplicates = out.putArray("duplicates_removed");
        for (Duplicate item : evidence.duplicatesRemoved()) {
            ObjectNode row = duplicates.addObject(); row.put("index", item.index());
            row.set("choice_id", identityNode(item.choiceId()));
        }
        if (evidence.sortOrder().isPresent()) { out.put("sort_order", evidence.sortOrder().orElseThrow()); }
        else { out.putNull("sort_order"); }
        if (!evidence.orderedEligibleChoiceIds().isEmpty()) {
            ArrayNode ids = out.putArray("ordered_eligible_choice_ids");
            evidence.orderedEligibleChoiceIds().forEach(identity -> ids.add(identityNode(identity)));
        }
        out.put("material_effects_verified", false);
        return out;
    }

    private static NativeChoice choice(ObjectNode row, int index) {
        allowed(row, CHOICE_FIELDS);
        ChoiceIdentity identity = identity(row.get("choice_id"));
        Field<Boolean> visible = field(row, "visible", MandatoryChoiceCodec::bool);
        Field<Boolean> enabled = field(row, "enabled", MandatoryChoiceCodec::bool);
        Field<Boolean> isChoice = field(row, "is_choice", MandatoryChoiceCodec::bool);
        Field<String> role = field(row, "role", value -> text(value, true));
        Field<BigInteger> renderedIndex = field(row, "rendered_index", MandatoryChoiceCodec::integer);
        Field<BigInteger> nativeIndex = field(row, "native_index", MandatoryChoiceCodec::integer);
        Field<String> token = field(row, "action_token", value -> text(value, true));
        if (row.hasNonNull("label")) { text(row.get("label"), true); }
        if (row.hasNonNull("label_source")) { text(row.get("label_source"), true); }
        boolean existing = false;
        if (row.hasNonNull("existing_typed_action")) {
            Field<Boolean> available = field(object(row.get("existing_typed_action")), "available", MandatoryChoiceCodec::bool);
            existing = available.hasValue() && available.value();
        }
        return new NativeChoice(index, identity, visible, enabled, isChoice, role, geometry(row.get("bounds")),
                renderedIndex, nativeIndex, token, existing, document(row));
    }

    private static Optional<Geometry> geometry(JsonNode bounds) {
        if (bounds == null || bounds.isNull()) { return Optional.empty(); }
        ObjectNode row = object(bounds); allowed(row, Set.of("top", "left", "width", "height"));
        double[] values = new double[4]; String[] names = {"top", "left", "width", "height"};
        boolean complete = true;
        for (int index = 0; index < names.length; index++) {
            JsonNode number = row.get(names[index]);
            if (number == null || number.isNull()) { complete = false; continue; }
            require(number.isNumber(), "geometry must be numeric, no bool/string coercion");
            values[index] = number.doubleValue();
            if (!Double.isFinite(values[index])) { complete = false; }
        }
        return complete && values[2] > 0 && values[3] > 0
                ? Optional.of(new Geometry(values[0], values[1])) : Optional.empty();
    }

    private static FrameBinding frame(JsonNode node) {
        ObjectNode row = object(node); require(fieldNames(row).equals(FRAME_FIELDS), "exact complete native frame fields required");
        BigInteger pid = positive(row.get("game_pid")); require(pid.bitLength() <= 32, "game PID uint32");
        BigInteger revision = integer(row.get("revision")); require(revision.signum() >= 0, "revision nonnegative");
        return new FrameBinding(pid.longValueExact(), positive(row.get("connection_generation")), revision,
                positive(row.get("native_revision")), integer(row.get("date_raw")),
                positive(row.get("actor_character_id")), text(row.get("episode_run_id"), false),
                text(row.get("snapshot_id"), false), document(row));
    }

    private static Optional<EvidenceDocument> blocking(ObjectNode row) {
        if (row.hasNonNull("blocking_proof")) {
            ObjectNode proof = object(row.get("blocking_proof"));
            Field<Boolean> verified = field(proof, "verified", MandatoryChoiceCodec::bool);
            Field<String> kind = field(proof, "kind", value -> text(value, false));
            if (verified.hasValue() && verified.value() && kind.hasValue()
                    && Set.of("blocks_simulation", "exclusive_modal_blocks_input").contains(kind.value())) {
                return Optional.of(document(proof));
            }
        }
        if (trueField(row, "blocks_simulation")) {
            return Optional.of(new EvidenceDocument("{\"kind\":\"blocks_simulation\",\"verified\":true}"));
        }
        if (trueField(row, "exclusive_modal") && trueField(row, "blocks_input")) {
            return Optional.of(new EvidenceDocument("{\"kind\":\"exclusive_modal_blocks_input\",\"verified\":true}"));
        }
        return Optional.empty();
    }

    private static boolean trueField(ObjectNode row, String name) {
        Field<Boolean> value = field(row, name, MandatoryChoiceCodec::bool);
        return value.hasValue() && value.value();
    }
    private static <T> Field<T> field(ObjectNode row, String name, Function<JsonNode, T> decode) {
        if (!row.has(name)) { return Field.missing(); }
        JsonNode value = row.get(name);
        return value.isNull() ? Field.nullValue() : Field.of(decode.apply(value));
    }
    private static ChoiceIdentity identity(JsonNode node) {
        if (node != null && node.isTextual()) {
            String value = text(node, false); return new TextIdentity(value);
        }
        return new IntegerIdentity(integer(node));
    }
    private static JsonNode fieldIdentityNode(Field<ChoiceIdentity> field) {
        return field.hasValue() ? identityNode(field.value()) : JSON.getNodeFactory().nullNode();
    }
    private static JsonNode identityNode(ChoiceIdentity identity) {
        if (identity instanceof TextIdentity text) { return JSON.getNodeFactory().textNode(text.value()); }
        return JSON.getNodeFactory().numberNode(((IntegerIdentity) identity).value());
    }
    private static BigInteger positive(JsonNode node) {
        BigInteger value = integer(node); require(value.signum() > 0, "positive native identity required"); return value;
    }
    private static BigInteger integer(JsonNode node) {
        require(node != null && node.isIntegralNumber(), "exact integer token required; no bool/float/string");
        BigInteger value = node.bigIntegerValue();
        require(value.compareTo(SIGNED64_MIN) >= 0 && value.compareTo(UINT64_MAX) <= 0, "native integer 64-bit domain");
        return value;
    }
    private static boolean bool(JsonNode node) {
        require(node != null && node.isBoolean(), "actual boolean token required"); return node.booleanValue();
    }
    private static String text(JsonNode node, boolean allowEmpty) {
        require(node != null && node.isTextual(), "string token required");
        String value = node.textValue(); if (!value.isEmpty()) { StrictJson.text(value); }
        require(allowEmpty || !value.isEmpty(), "nonempty text required"); return value;
    }
    private static ObjectNode object(JsonNode node) {
        require(node instanceof ObjectNode, "JSON object required"); return (ObjectNode) node;
    }
    private static Set<String> fieldNames(ObjectNode row) {
        Set<String> fields = new TreeSet<>(); row.fieldNames().forEachRemaining(fields::add); return fields;
    }
    private static void allowed(ObjectNode row, Set<String> fields) {
        require(fields.containsAll(fieldNames(row)), "unknown native v1 field");
    }
    private static JsonNode parse(byte[] raw) {
        require(raw != null && raw.length > 0 && raw.length <= MAX_BYTES, "bounded UTF-8 native JSON required");
        try {
            String value = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            JsonNode node = JSON.readTree(value); require(node != null, "JSON value required");
            validateJsonDomain(node, 0); return node;
        } catch (CharacterCodingException error) {
            throw new IllegalArgumentException("invalid UTF-8", error);
        } catch (IOException error) { throw new IllegalArgumentException("invalid/duplicate/trailing JSON", error); }
    }
    private static JsonNode read(EvidenceDocument document) { return parse(document.json().getBytes(StandardCharsets.UTF_8)); }
    private static void validateJsonDomain(JsonNode node, int depth) {
        require(depth <= 64, "bounded native JSON nesting required");
        if (node.isTextual() && !node.textValue().isEmpty()) { StrictJson.text(node.textValue()); }
        if (node.isFloatingPointNumber()) { require(Double.isFinite(node.doubleValue()), "finite JSON number required"); }
        if (node.isObject()) {
            node.fieldNames().forEachRemaining(name -> { if (!name.isEmpty()) { StrictJson.text(name); } });
        }
        if (node.isContainerNode()) { node.forEach(child -> validateJsonDomain(child, depth + 1)); }
    }
    private static EvidenceDocument document(JsonNode node) { return new EvidenceDocument(json(sorted(node))); }
    private static JsonNode sorted(JsonNode node) {
        if (node.isObject()) {
            ObjectNode out = JSON.createObjectNode();
            new TreeSet<>(fieldNames((ObjectNode) node)).forEach(name -> out.set(name, sorted(node.get(name)))); return out;
        }
        if (node.isArray()) {
            ArrayNode out = JSON.createArrayNode(); node.forEach(value -> out.add(sorted(value))); return out;
        }
        return node.deepCopy();
    }
    private static String json(JsonNode node) {
        try { return JSON.writeValueAsString(node); }
        catch (IOException error) { throw new IllegalArgumentException("JSON serialization failed", error); }
    }
    private static byte[] bounded(byte[] raw) { require(raw.length <= MAX_BYTES, "native output byte budget exceeded"); return raw; }
    private static void require(boolean condition, String message) {
        if (!condition) { throw new IllegalArgumentException(message); }
    }
}
