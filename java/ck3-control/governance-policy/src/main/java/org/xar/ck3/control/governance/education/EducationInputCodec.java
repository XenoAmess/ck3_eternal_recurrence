package org.xar.ck3.control.governance.education;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.governance.education.EducationInputs.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Strict token validation for the fields reached by the education projection.
 * The legacy family container is extensible; unrelated lineage/window leaves remain with its original owner.
 */
public final class EducationInputCodec {
    public static final int INPUT_MAX_BYTES = 1_048_576;
    public static final int OUTPUT_MAX_BYTES = 4_194_304;
    private static final ObjectMapper WIRE = new ObjectMapper();
    private static final ObjectMapper READER = new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).disable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS).configure(JsonNodeFeature.USE_BIG_DECIMAL_FOR_FLOATS, false)
            .configure(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES, false);
    public static final List<String> CHILDHOOD = List.of("curious", "rowdy", "bossy", "pensive", "charming");
    public static final List<String> POINT_TRAITS = List.of("intellect_good_1", "intellect_good_2", "intellect_good_3",
            "intellect_bad_1", "intellect_bad_2", "intellect_bad_3", "shrewd", "dull", "inbred");
    private EducationInputCodec() { }

    /** Education retains the legacy JSON domain in unused SDK extension fields, including finite decimals. */
    static byte[] encode(JsonNode node) {
        try {
            unicode(node);
            byte[] bytes = WIRE.writeValueAsBytes(node);
            require(bytes.length <= OUTPUT_MAX_BYTES, "education output exceeds explicit family byte budget");
            return bytes;
        } catch (JsonProcessingException error) { throw new IllegalArgumentException("education JSON encoding failed", error); }
    }
    static JsonNode parse(byte[] bytes) {
        require(bytes != null && bytes.length > 0 && bytes.length <= INPUT_MAX_BYTES, "bounded nonempty education input required");
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
            JsonNode node = READER.readTree(text); require(node != null, "education JSON value required"); return node;
        } catch (IOException error) { throw new IllegalArgumentException("invalid UTF-8, duplicate, or trailing education JSON", error); }
    }
    private static void unicode(JsonNode node) {
        require(!node.isFloatingPointNumber() || Double.isFinite(node.doubleValue()), "finite legacy JSON floating-point value required");
        if (node.isTextual() && !node.textValue().isEmpty()) { StrictJson.text(node); }
        if (node.isObject()) { node.fieldNames().forEachRemaining(key -> { if (!key.isEmpty()) { StrictJson.text(key); } }); }
        if (node.isContainerNode()) { for (JsonNode child : node) { unicode(child); } }
    }

    public static Descendants decode(byte[] bytes) { return decode(parse(bytes)); }
    static Descendants decode(JsonNode input) {
        require(input != null, "explicit input required");
        if (input.isNull()) { return null; }
        object(input);
        Frame frame = frame(input);
        Status status = status(input, false);
        String reason = reason(input, status);
        boolean complete = bool(field(input, "roster_complete"));
        require(complete == (status == Status.AVAILABLE), "roster status disagrees with completeness");
        require(status == Status.UNAVAILABLE || frame.playedCharacterId() != null && frame.heirCharacterId() != null && frame.dateRaw() != null,
                "observed roster requires the complete owning frame");
        List<Occurrence> rows = new ArrayList<>();
        for (JsonNode row : array(field(input, "rows"))) {
            object(row);
            int index = (int) integer(field(row, "occurrence_index"), 0, Integer.MAX_VALUE);
            require(index == rows.size(), "occurrence order changed");
            rows.add(new Occurrence(index, integer(field(row, "raw_character_id"), 0, 0xffff_ffffL),
                    bool(field(row, "generation_valid")), nullableBool(row.get("alive")), nullableBool(row.get("child_of_heir"))));
        }
        require(complete || rows.isEmpty(), "incomplete roster contains occurrences");
        ChildInputs childInputs = null;
        if (input.has("child_inputs")) {
            JsonNode sidecar = field(input, "child_inputs"); object(sidecar);
            require("native_current_heir_child_inputs".equals(text(field(sidecar, "source"))), "child inputs source changed");
            Status sideStatus = status(sidecar, false);
            Frame sideFrame = frame(sidecar);
            List<ChildRead> children = new ArrayList<>();
            for (JsonNode child : array(field(sidecar, "rows"))) {
                object(child);
                require(child.has("values") && child.has("childhood_traits"), "required child input leaves missing");
                int id = (int) integer(field(child, "character_id"), Integer.MIN_VALUE, Integer.MAX_VALUE);
                List<Integer> indices = new ArrayList<>();
                for (JsonNode index : array(field(child, "occurrence_indices"))) {
                    indices.add((int) integer(index, 0, Integer.MAX_VALUE));
                }
                children.add(new ChildRead(id, indices, leaf(child, "values", LeafKind.VALUES),
                        leaf(child, "childhood_traits", LeafKind.CHILDHOOD_TRAITS), leaf(child, "native_focus", LeafKind.NATIVE_FOCUS),
                        leaf(child, "education_point_traits", LeafKind.EDUCATION_POINT_TRAITS),
                        leaf(child, "education_traits", LeafKind.EDUCATION_TRAITS), courtOwner(child)));
            }
            require(sideStatus != Status.UNAVAILABLE || children.isEmpty(), "unavailable child inputs contain rows");
            childInputs = new ChildInputs(sideFrame, sideStatus, reason(sidecar, sideStatus), children);
        }
        return new Descendants(frame, status, reason, complete, rows, childInputs);
    }

    private static Frame frame(JsonNode node) {
        return new Frame(StrictJson.integer(field(node, "native_revision"), BigInteger.ONE, StrictJson.UINT64_MAX),
                nullableInteger(field(node, "played_character_id"), 1, Integer.MAX_VALUE),
                nullableInteger(field(node, "heir_character_id"), 1, Integer.MAX_VALUE),
                nullableInteger(field(node, "date_raw"), Long.MIN_VALUE, Long.MAX_VALUE));
    }
    private static Leaf leaf(JsonNode child, String name, LeafKind kind) {
        if (!child.has(name)) { return null; }
        JsonNode node = field(child, name); object(node);
        Status status = status(node, true); String reason = reason(node, status);
        String source = text(field(node, "source"));
        LeafFacts facts;
        if (kind == LeafKind.VALUES) {
            require(source.equals("native_character_age_and_sex"), "values source changed");
            Integer age = nullableInt(field(node, "age_measure_raw"), Short.MIN_VALUE, Short.MAX_VALUE);
            Integer sex = nullableInt(field(node, "sex_selector_raw"), 0, 1);
            require(status == Status.AVAILABLE ? age != null && sex != null : age == null && sex == null, "values status disagreement");
            facts = new Values(age, sex);
        } else if (kind == LeafKind.NATIVE_FOCUS) {
            require(source.equals("native_character_current_focus"), "focus source changed");
            JsonNode presence = field(node, "presence"), key = field(node, "key");
            if (status == Status.UNAVAILABLE) {
                require(presence.isNull() && key.isNull(), "unavailable focus must retain unknown");
                facts = new Focus(null, null);
            } else {
                String value = text(presence); require(value.equals("present") || value.equals("absent"), "focus presence changed");
                boolean present = value.equals("present");
                require(present ? key.isTextual() && !key.textValue().isEmpty() : key.isNull(), "focus null semantics changed");
                facts = new Focus(present ? Presence.PRESENT : Presence.ABSENT, present ? text(key) : null);
            }
        } else {
            require(source.equals("native_character_has_trait"), "trait source changed");
            List<String> expected = kind == LeafKind.CHILDHOOD_TRAITS ? CHILDHOOD : kind == LeafKind.EDUCATION_POINT_TRAITS ? POINT_TRAITS : educationTraits();
            List<String> queried = strings(field(node, "queried_trait_keys"));
            require(queried.equals(expected), "queried trait order changed");
            JsonNode rawPresent = field(node, "present_trait_keys");
            List<String> present = rawPresent.isNull() ? null : strings(rawPresent);
            require(status == Status.AVAILABLE ? present != null : present == null, "trait status disagreement");
            if (present != null) { require(present.equals(expected.stream().filter(present::contains).toList()), "noncanonical trait subset"); }
            facts = new Traits(queried, present);
        }
        return new Leaf(status, reason, facts, encode(node));
    }

    private static CourtOwner courtOwner(JsonNode child) {
        if (!child.has("court_owner_source")) { return new CourtOwner(false, false, null, null, 0, null, null, null, false, false, false, false, null); }
        JsonNode node = field(child, "court_owner_source");
        if (node.isNull()) { return new CourtOwner(true, false, null, null, 0, null, null, null, false, false, false, false, null); }
        StrictJson.object(node, Set.of("schema", "status", "unavailable_reason", "child_character_id", "native_revision", "court_owner_present", "court_owner_id", "child_address", "court_owner_address", "getter_return_address", "fallback_address", "fallback_full_id_raw", "relation_owner_id_raw", "source_path", "fallback_reached", "getter_projection_complete", "identity_round_trip", "sample_stable", "source_qualified"));
        require(text(field(node, "schema")).equals("xar.ck3.current-child-court-owner-readonly/1.20.0.4/v1"), "court owner schema changed");
        for (String name : List.of("child_address", "court_owner_address", "getter_return_address", "fallback_address")) {
            JsonNode value = field(node, name); if (!value.isNull()) { StrictJson.integer(value, BigInteger.ZERO, StrictJson.UINT64_MAX); }
        }
        for (String name : List.of("fallback_full_id_raw", "relation_owner_id_raw")) { nullableInteger(field(node, name), 0, 0xffff_ffffL); }
        textAllowEmpty(field(node, "source_path")); bool(field(node, "fallback_reached"));
        String status = text(field(node, "status"));
        require(List.of("resolved", "known_null", "unavailable").contains(status), "court owner status changed");
        return new CourtOwner(true, true, status, textAllowEmpty(field(node, "unavailable_reason")),
                integer(field(node, "child_character_id"), 0, 0xffff_ffffL), StrictJson.integer(field(node, "native_revision"), BigInteger.ONE, StrictJson.UINT64_MAX),
                nullableBool(field(node, "court_owner_present")), nullableInteger(field(node, "court_owner_id"), 0, 0xffff_ffffL),
                bool(field(node, "source_qualified")), bool(field(node, "getter_projection_complete")), bool(field(node, "identity_round_trip")), bool(field(node, "sample_stable")), encode(node));
    }
    private static List<String> educationTraits() {
        List<String> result = new ArrayList<>();
        for (String skill : List.of("diplomacy", "martial", "stewardship", "intrigue", "learning")) {
            for (int rank = 1; rank <= 5; rank++) { result.add("education_" + skill + "_" + rank); }
        }
        return List.copyOf(result);
    }
    private static Status status(JsonNode node, boolean leaf) {
        Status result = Status.fromWire(text(field(node, "status")));
        require(result != Status.NOT_OBSERVED && (!leaf || result != Status.PARTIAL), "invalid input status"); return result;
    }
    private static String reason(JsonNode node, Status status) {
        JsonNode value = field(node, "unavailable_reason");
        if (status == Status.AVAILABLE) { require(value.isNull(), "available leaf must have null reason"); return null; }
        return text(value);
    }
    static JsonNode field(JsonNode node, String name) { require(node.has(name), "missing education field: " + name); return node.get(name); }
    private static void object(JsonNode node) { require(node != null && node.isObject(), "education object required"); }
    private static Iterable<JsonNode> array(JsonNode node) { require(node.isArray() && node.size() <= 2048, "bounded education array required"); return node; }
    private static String text(JsonNode node) { return StrictJson.text(node); }
    private static String textAllowEmpty(JsonNode node) { require(node.isTextual(), "text required"); return node.textValue().isEmpty() ? "" : text(node); }
    private static long integer(JsonNode node, long min, long max) { return StrictJson.integer(node, min, max); }
    private static Long nullableInteger(JsonNode node, long min, long max) { return node.isNull() ? null : integer(node, min, max); }
    private static Integer nullableInt(JsonNode node, int min, int max) { return node.isNull() ? null : (int) integer(node, min, max); }
    private static boolean bool(JsonNode node) { require(node.isBoolean(), "actual JSON boolean required"); return node.booleanValue(); }
    private static Boolean nullableBool(JsonNode node) { return node == null || node.isNull() ? null : bool(node); }
    private static List<String> strings(JsonNode node) {
        List<String> result = new ArrayList<>(); for (JsonNode item : array(node)) { result.add(text(item)); } return List.copyOf(result);
    }
}
