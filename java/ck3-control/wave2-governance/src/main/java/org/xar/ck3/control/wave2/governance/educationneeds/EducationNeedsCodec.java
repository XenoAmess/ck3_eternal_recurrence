package org.xar.ck3.control.wave2.governance.educationneeds;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsModel.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.education.EducationInputs.Frame;
import org.xar.ck3.control.governance.education.EducationInputs.Status;

/** Strict new wrapper and declared projections of original independently-qualified SDK containers. */
final class EducationNeedsCodec {
    static final int MAX_BYTES = 8_388_608;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS).enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .disable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS).configure(JsonNodeFeature.USE_BIG_DECIMAL_FOR_FLOATS, false)
            .configure(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES, false);
    private EducationNeedsCodec() { }
    static JsonNode parse(byte[] bytes) {
        require(bytes != null && bytes.length > 0 && bytes.length <= MAX_BYTES, "bounded nonempty education-needs JSON required");
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
            JsonNode node = JSON.readTree(text); require(node != null, "JSON value required"); return node;
        } catch (IOException error) { throw new IllegalArgumentException("invalid education-needs UTF8/JSON/duplicate/trailing fields", error); }
    }
    static byte[] encode(JsonNode node) {
        unicode(node);
        try { byte[] bytes = JSON.writeValueAsBytes(node); require(bytes.length <= MAX_BYTES, "education-needs byte budget exceeded"); return bytes; }
        catch (IOException error) { throw new IllegalArgumentException("education-needs JSON encoding failed", error); }
    }
    static ObjectNode object() { return JSON.createObjectNode(); }
    static WireValue wire(JsonNode node) { return new WireValue(encode(node)); }
    static JsonNode unwire(WireValue value) { return parse(value.bytes()); }
    static Request request(byte[] bytes) {
        JsonNode root = parse(bytes); StrictJson.object(root, Set.of("schema", "decision_inputs", "child_relation_materials", "child_education_provider_inputs", "child_education_provider_source"));
        require(text(field(root, "schema")).equals("xar.education-needs.request/v1"), "education needs request schema changed");
        Decision decision = decision(field(root, "decision_inputs"));
        return new Request(decision, materials(field(root, "child_relation_materials")), provider(field(root, "child_education_provider_inputs"), field(root, "child_education_provider_source"), decision));
    }
    static Decision decision(JsonNode root) {
        if (root.isNull()) { return null; } object(root);
        require(text(field(root, "schema")).equals("family_generation_education_decision_inputs_v1"), "education decision schema changed");
        Frame frame = frame(field(root, "frame"));
        List<Child> rows = new ArrayList<>(); List<JsonNode> decisions = array(field(root, "education_rows"));
        for (JsonNode child : array(field(field(root, "children"), "rows"))) {
            long raw = uint32(field(child, "raw_character_id")); int id = (int) integer(field(child, "character_id"), Integer.MIN_VALUE, Integer.MAX_VALUE);
            require(id == (int) raw, "child full identity bits changed");
            JsonNode decision = null;
            // Original producer uses the last matching decision row. Preserve that reached semantics.
            for (JsonNode row : decisions) { if (uint32(field(row, "raw_character_id")) == raw) { decision = row; } }
            require(decision != null, "child education decision row missing");
            List<Integer> indices = indices(field(child, "occurrence_indices"));
            require(indices.equals(indices(field(decision, "occurrence_indices"))), "decision occurrence group changed");
            require(integer(field(decision, "character_id"), Integer.MIN_VALUE, Integer.MAX_VALUE) == id, "decision signed identity changed");
            List<LeafAvailability> availability = new ArrayList<>(); JsonNode availabilityWire = field(child, "leaf_availability"); object(availabilityWire);
            Set<String> keys = Set.of("values", "childhood_traits", "native_focus", "education_point_traits", "education_traits");
            Set<String> actual = new HashSet<>(); availabilityWire.fieldNames().forEachRemaining(actual::add); require(actual.equals(keys), "education leaf availability fields changed");
            availabilityWire.fieldNames().forEachRemaining(key -> {
                JsonNode value = field(availabilityWire, key); object(value); Status status = Status.fromWire(text(field(value, "status")));
                String reason = nullableText(field(value, "unavailable_reason"));
                require(status != Status.PARTIAL && (status == Status.AVAILABLE ? reason == null : reason != null && !reason.isEmpty()), "leaf availability status/reason changed");
                availability.add(new LeafAvailability(key, status, reason));
            });
            validateLeaf(field(child, "values"), true); validateLeaf(field(child, "childhood_traits"), false); validateLeaf(field(child, "education_point_traits"), false);
            JsonNode educationTraits = child.has("education_traits") ? child.get("education_traits") : com.fasterxml.jackson.databind.node.NullNode.getInstance(); validateLeaf(educationTraits, false);
            FocusManagement focus = focus(field(decision, "current_focus"));
            JsonNode options = field(decision, "stock_skill_options"); require(options.isArray() && options.size() == 5, "five stock source options required");
            for (int index = 0; index < options.size(); index++) {
                JsonNode option = options.get(index); object(option);
                String skill = org.xar.ck3.control.governance.education.EducationDecisionComposer.SKILLS.get(index).name();
                require(text(field(option, "skill_parameter")).equals(skill) && text(field(option, "focus_key")).equals("education_" + skill), "stock option identity/order changed");
                for (String term : List.of("childhood_affinity", "childhood_disaffinity")) {
                    JsonNode value = field(option, term); boolean available = bool(field(value, "available")); Boolean rawValue = nullableBool(field(value, "raw_value"));
                    require(available == (rawValue != null), "source affinity availability/value changed");
                }
            }
            JsonNode current = field(decision, "current_education_skill_inputs"); require(current.isNull() || current.isObject(), "current option must remain object/null");
            JsonNode court = field(decision, "current_court_owner"); object(court); bool(field(court, "available")); bool(field(court, "source_qualified"));
            nullableBool(field(court, "present")); nullableBool(field(court, "known_null")); nullableUint32(field(court, "owner_character_id_raw"));
            rows.add(new Child(new NeedsRowProjection(id, raw, indices, frame, focus), availability, wire(availabilityWire),
                    wire(field(child, "values")), wire(field(child, "childhood_traits")), wire(field(child, "education_point_traits")), wire(educationTraits), wire(options), wire(current), wire(court)));
        }
        return new Decision(frame, bool(field(root, "roster_complete")), bool(field(root, "living_child_classification_complete")), nullableBool(field(root, "known_empty")), rows);
    }
    private static void validateLeaf(JsonNode node, boolean values) {
        if (node.isNull()) { return; } object(node);
        Status status = Status.fromWire(text(field(node, "status"))); require(status == Status.AVAILABLE || status == Status.UNAVAILABLE, "invalid education observation status");
        nullableText(field(node, "unavailable_reason")); text(field(node, "source"));
        if (values) {
            JsonNode age = field(node, "age_measure_raw"), sex = field(node, "sex_selector_raw");
            if (status == Status.AVAILABLE) { integer(age, Short.MIN_VALUE, Short.MAX_VALUE); integer(sex, 0, 1); }
            else { require(age.isNull() && sex.isNull(), "unavailable values must remain null"); }
        } else { for (JsonNode key : array(field(node, "queried_trait_keys"))) { text(key); } JsonNode present = field(node, "present_trait_keys"); if (!present.isNull()) { for (JsonNode key : array(present)) { text(key); } } }
    }
    static FocusManagement focus(JsonNode value) {
        object(value); boolean available = bool(field(value, "available")); String reason = nullableText(field(value, "unavailable_reason"));
        if (!available) { for (String key : List.of("presence", "key", "known_null", "has_education_focus")) { require(field(value, key).isNull(), "unavailable focus must retain null operands"); } return new FocusManagement(false, FocusState.UNKNOWN, null, null, null, reason); }
        String presence = text(field(value, "presence")); require(presence.equals("absent") || presence.equals("present"), "focus presence changed");
        boolean absent = presence.equals("absent"), education = bool(field(value, "has_education_focus"));
        String key = nullableText(field(value, "key")); require(absent ? key == null && !education : key != null, "focus null semantics changed");
        require(reason == null && bool(field(value, "known_null")) == absent, "available focus known-null/reason changed");
        return new FocusManagement(true, absent ? FocusState.KNOWN_ABSENT : education ? FocusState.EDUCATION_FOCUS_PRESENT : FocusState.OTHER_FOCUS_PRESENT, key, absent, education, null);
    }
    private static Materials materials(JsonNode source) {
        if (source.isNull()) { return new Materials(false, false, null, List.of()); } object(source);
        require(integer(field(source, "schema_version"), 1, 1) == 1 && bool(field(source, "read_only"))
                && bool(field(source, "source_projection_only")) && !bool(field(source, "guardian_role_equivalence_qualified")), "generic child materials must retain projection-only status");
        require(text(field(source, "source")).equals("current_child_generic_named_material_projection"), "child materials source changed");
        boolean collected = bool(field(source, "collection_available")); String reason = nullableText(field(source, "unavailable_reason")); List<MaterialRow> rows = new ArrayList<>();
        for (JsonNode row : array(field(source, "rows"))) { object(row); rows.add(new MaterialRow(uint32(field(row, "child_character_id")), wire(row))); }
        return new Materials(true, collected, reason, rows);
    }
    private static Provider provider(JsonNode source, JsonNode proof, Decision decision) {
        if (source.isNull()) { return new Provider(false, null, false, null, List.of(), null, null); }
        object(source); object(proof);
        require(text(field(proof, "binding_scope")).equals("query_before_after"), "same-query provider source scope changed");
        text(field(proof, "request_id")); positive64(field(proof, "bridge_pid")); positive64(field(proof, "connection_generation")); StrictJson.trueValue(field(proof, "same_request_export_completed"));
        integer(field(proof, "sidecar_bytes"), 0, 4_194_304); require(text(field(proof, "sidecar_sha256")).matches("[0-9a-f]{64}"), "source SHA required");
        BigInteger proofRevision = positive64(field(proof, "native_revision")); long proofDate = integer(field(proof, "date_raw"), Long.MIN_VALUE, Long.MAX_VALUE);
        long actor = uint32(field(proof, "played_character_id"));
        Long heir = nullableUint32(field(proof, "heir_character_id"));
        long providerHeir = uint32(field(source, "heir_character_full_id"));
        require(heir == null ? providerHeir == 4_294_967_295L
                : heir != 4_294_967_295L && providerHeir == heir, "provider no-heir sentinel differs from explicit nullable source proof");
        require(integer(field(source, "schema_version"), 1, 1) == 1 && bool(field(source, "read_only"))
                && !bool(field(source, "m6_inputs_complete")) && !bool(field(source, "guardian_role_equivalence_qualified")), "provider must retain read-only incomplete authority flags");
        require(text(field(source, "source")).equals("same_query_actual4_child_education_inputs")
                && text(field(source, "request_id")).equals(text(field(proof, "request_id")))
                && positive64(field(source, "native_revision")).equals(proofRevision)
                && integer(field(source, "date_raw"), Long.MIN_VALUE, Long.MAX_VALUE) == proofDate
                && uint32(field(source, "played_character_full_id")) == actor
                && providerHeir == (heir == null ? 4_294_967_295L : heir), "provider input and source proof identity differ");
        if (decision != null && decision.frame() != null) {
            require(decision.frame().nativeRevision().equals(positive64(field(proof, "native_revision")))
                    && decision.frame().dateRaw() != null && decision.frame().dateRaw() == integer(field(proof, "date_raw"), Long.MIN_VALUE, Long.MAX_VALUE)
                    && decision.frame().playedCharacterId() != null && decision.frame().playedCharacterId() == uint32(field(proof, "played_character_id"))
                    && Objects.equals(decision.frame().heirCharacterId(), heir), "provider source frame differs from education source");
        }
        Status status = Status.fromWire(text(field(source, "status"))); require(status != Status.NOT_OBSERVED, "provider status changed");
        boolean collected = bool(field(source, "collection_available")); String reason = nullableText(field(source, "unavailable_reason"));
        boolean roster = bool(field(source, "roster_complete")), observed = bool(field(source, "child_observation_complete"));
        require(status == Status.AVAILABLE ? collected && roster && observed && reason == null
                : status == Status.PARTIAL ? collected && roster && !observed && reason != null && !reason.isEmpty()
                : !collected && !roster && !observed && reason != null && !reason.isEmpty(), "provider status/completeness changed");
        List<ProviderRow> rows = new ArrayList<>();
        for (JsonNode row : array(field(source, "rows"))) { object(row); rows.add(new ProviderRow(uint32(field(row, "child_full_id")), indices(field(row, "occurrence_indices")), wire(row))); }
        require(rows.size() <= 256 && (status != Status.UNAVAILABLE || rows.isEmpty()), "provider inventory bound changed");
        require(heir != null || rows.isEmpty() && (decision == null || decision.children().isEmpty()),
                "no-heir provider cannot carry living child rows");
        return new Provider(true, status, collected, reason, rows, wire(source), wire(proof));
    }
    static Frame frame(JsonNode node) {
        if (node.isNull()) { return null; } object(node);
        return new Frame(positive64(field(node, "native_revision")), nullableUint32(field(node, "played_character_id")), nullableUint32(field(node, "heir_character_id")), nullableLong(field(node, "date_raw")));
    }
    static OrdinaryContext ordinary(byte[] bytes) {
        JsonNode node = parse(bytes); object(node);
        Status status = Status.fromWire(text(field(node, "status"))); String key = text(field(node, "interaction_key"));
        JsonNode roles = field(node, "effective_roles"); object(roles);
        OrdinaryRoles typed = new OrdinaryRoles(nullableUint32(field(roles, "actor_id")), nullableUint32(field(roles, "recipient_id")), nullableUint32(field(roles, "secondary_actor_id")), nullableUint32(field(roles, "secondary_recipient_id")), nullableUint32(field(roles, "intermediary_id")), nullableUint32(field(roles, "sixth_role_id")));
        OrdinaryFrame frame = new OrdinaryFrame(positive64(field(node, "snapshot_revision")), integer(field(node, "date_raw"), Long.MIN_VALUE, Long.MAX_VALUE), uint32(field(node, "player_character_id")), integer(field(node, "game_pid"), 1, 0xffff_ffffL), positive64(field(node, "connection_generation")));
        return new OrdinaryContext(status, key, nullableText(field(node, "unavailable_reason")), typed, wire(roles), frame, bool(field(node, "can_send")), bool(field(node, "ready_to_initiate")));
    }
    static List<Integer> indices(JsonNode value) { List<Integer> result = new ArrayList<>(); for (JsonNode index : array(value)) { result.add((int) integer(index, 0, Integer.MAX_VALUE)); } require(!result.isEmpty(), "child occurrence group required"); return List.copyOf(result); }
    static JsonNode field(JsonNode node, String key) { require(node != null && node.isObject() && node.has(key), "missing education-needs field: " + key); return node.get(key); }
    static void object(JsonNode node) { require(node != null && node.isObject(), "education-needs object required"); }
    static List<JsonNode> array(JsonNode node) { require(node.isArray() && node.size() <= 4096, "bounded education-needs array required"); List<JsonNode> rows = new ArrayList<>(); node.forEach(rows::add); return rows; }
    static String text(JsonNode node) { return StrictJson.text(node); }
    static String nullableText(JsonNode node) { require(node != null, "explicit nullable text required"); return node.isNull() ? null : node.isTextual() && node.textValue().isEmpty() ? "" : text(node); }
    static boolean bool(JsonNode node) { require(node != null && node.isBoolean(), "exact boolean required"); return node.booleanValue(); }
    static Boolean nullableBool(JsonNode node) { return node.isNull() ? null : bool(node); }
    static long integer(JsonNode node, long low, long high) { return StrictJson.integer(node, low, high); }
    static BigInteger positive64(JsonNode node) { return StrictJson.integer(node, BigInteger.ONE, StrictJson.UINT64_MAX); }
    static long uint32(JsonNode node) { return integer(node, 0, 0xffff_ffffL); }
    static Long nullableUint32(JsonNode node) { return node.isNull() ? null : uint32(node); }
    static Long nullableLong(JsonNode node) { return node.isNull() ? null : integer(node, Long.MIN_VALUE, Long.MAX_VALUE); }
    private static void unicode(JsonNode node) { require(!node.isFloatingPointNumber() || Double.isFinite(node.doubleValue()), "finite legacy JSON float required"); if (node.isTextual() && !node.textValue().isEmpty()) { StrictJson.text(node); } if (node.isObject()) { node.fieldNames().forEachRemaining(key -> { if (!key.isEmpty()) { StrictJson.text(key); } }); } if (node.isContainerNode()) { node.forEach(EducationNeedsCodec::unicode); } }
}
