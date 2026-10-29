package org.xar.ck3.control.wave3.governance.educationprovider;

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
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.governance.education.EducationInputs.Status;
import org.xar.ck3.control.wave3.governance.educationprovider.EducationProviderModel.*;
import static org.xar.ck3.control.wave3.governance.educationprovider.EducationProviderValidator.require;

/** One narrow dynamic boundary. The native provider itself retains its original 64 KiB UTF8 limit. */
public final class EducationProviderCodec {
    public static final String SCHEMA = "xar.education-provider.validation-request/v1";
    public static final int REQUEST_LIMIT = 8 * 1024 * 1024;
    public static final int PROVIDER_LIMIT = 65_536;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);
    private static final Set<String> TOP = Set.of("schema_version", "read_only", "source", "request_id", "native_revision", "date_raw",
            "played_character_full_id", "heir_character_full_id", "status", "unavailable_reason", "roster_complete", "collection_available",
            "child_observation_complete", "m6_inputs_complete", "guardian_role_equivalence_qualified", "queried_education_trait_keys", "rows");
    private static final Set<String> ROW = Set.of("child_full_id", "role_source", "occurrence_indices", "education_traits", "culture_parameter",
            "guardian_full_id", "guardian_culture_parameter", "guardian_unavailable_reason", "rite_parameters", "rite_unavailable_reason",
            "education_type", "education_progress", "education_variables_unavailable_reason");
    private EducationProviderCodec() { }

    public static Request decode(byte[] bytes) {
        require(bytes != null && bytes.length <= REQUEST_LIMIT, "provider request exceeds bounded input");
        JsonNode root;
        try {
            StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes));
            root = JSON.readTree(bytes);
        } catch (CharacterCodingException exception) { throw new IllegalArgumentException("provider request must be strict UTF8", exception);
        } catch (IOException exception) { throw new IllegalArgumentException("provider request must be strict JSON", exception); }
        jsonDomain(root);
        exact(root, Set.of("schema", "value", "family_result", "qualified", "request_id", "revision", "actor", "heir", "date"), "provider request");
        require(SCHEMA.equals(text(root.get("schema"), "schema")), "provider request schema changed");
        JsonNode value = root.get("value");
        // The original optional decoder returns None before examining any native/source prerequisites.
        if (value.isNull()) { return new Request(false, null, null, null); }
        exact(value, TOP, "education provider");
        require(write(value).length <= PROVIDER_LIMIT, "education provider exceeds 65536 UTF8 bytes");
        boolean qualified = flag(root.get("qualified"), "qualified");
        require(qualified, "education provider object lacks qualified captured source");
        JsonNode family = object(root.get("family_result"), "normalized family");
        require(family.has("heir_character_id"), "normalized heir binding missing");
        Integer familyHeir = family.get("heir_character_id").isNull() ? null : signed32(family.get("heir_character_id"), "normalized heir");
        Frame frame = new Frame(uint(root.get("revision"), 64, "revision"), signed64(root.get("date"), "date"),
                new Full32(signed32(root.get("actor"), "actor")), new Full32(signed32(root.get("heir"), "heir")));
        Binding binding = new Binding(text(root.get("request_id"), "request_id"), frame, familyHeir);
        same(integer(value.get("schema_version"), "schema_version"), BigInteger.ONE, "schema_version");
        same(flag(value.get("read_only"), "read_only"), true, "read_only");
        same(text(value.get("source"), "source"), EducationProviderValidator.SOURCE, "source");
        same(flag(value.get("m6_inputs_complete"), "m6_inputs_complete"), false, "m6_inputs_complete");
        same(flag(value.get("guardian_role_equivalence_qualified"), "guardian_role_equivalence_qualified"), false, "guardian_role_equivalence_qualified");
        String requestId = text(value.get("request_id"), "provider request_id");
        Frame providerFrame = new Frame(uint(value.get("native_revision"), 64, "provider native_revision"), signed64(value.get("date_raw"), "provider date_raw"),
                new Full32((int) uint(value.get("played_character_full_id"), 32, "played full ID").longValueExact()),
                new Full32((int) uint(value.get("heir_character_full_id"), 32, "heir full ID").longValueExact()));
        Status status = status(value.get("status"));
        List<ProviderChild> rows = new ArrayList<>();
        for (JsonNode row : array(value.get("rows"), 256, "provider rows")) {
            exact(row, ROW, "education provider child");
            for (String field : List.of("guardian_full_id", "guardian_culture_parameter", "rite_parameters", "education_type", "education_progress")) {
                require(row.get(field).isNull(), "unobserved authoritative field must retain null: " + field);
            }
            rows.add(new ProviderChild(uint(row.get("child_full_id"), 32, "child full ID").longValueExact(), text(row.get("role_source"), "role_source"),
                    indices(row.get("occurrence_indices")), traits(row.get("education_traits")), culture(row.get("culture_parameter")), null, null,
                    text(row.get("guardian_unavailable_reason"), "guardian reason"), text(row.get("rite_unavailable_reason"), "rite reason"),
                    text(row.get("education_variables_unavailable_reason"), "education variable reason")));
        }
        Provider provider = new Provider(requestId, providerFrame, status, nullableText(value.get("unavailable_reason"), "provider reason"),
                flag(value.get("roster_complete"), "roster_complete"), flag(value.get("collection_available"), "collection_available"),
                flag(value.get("child_observation_complete"), "child_observation_complete"), strings(value.get("queried_education_trait_keys"), 25, "queried traits"), rows);
        FamilyInventory inventory = status == Status.UNAVAILABLE ? null : family(family, binding);
        return new Request(qualified, binding, inventory, provider);
    }

    /** Serializes only the validated original leaf; no source proof or admission flag is manufactured. */
    static byte[] encode(Provider provider) {
        if (provider == null) { return "null".getBytes(StandardCharsets.UTF_8); }
        ObjectNode root = JSON.createObjectNode(); root.put("schema_version", 1).put("read_only", true).put("source", EducationProviderValidator.SOURCE);
        root.put("request_id", provider.requestId()).put("native_revision", provider.frame().nativeRevision()).put("date_raw", provider.frame().dateRaw());
        root.put("played_character_full_id", provider.frame().playedCharacter().raw()).put("heir_character_full_id", provider.frame().heirCharacter().raw());
        root.put("status", provider.status().wire()); nullable(root, "unavailable_reason", provider.unavailableReason());
        root.put("roster_complete", provider.rosterComplete()).put("collection_available", provider.collectionAvailable()).put("child_observation_complete", provider.childObservationComplete());
        root.put("m6_inputs_complete", false).put("guardian_role_equivalence_qualified", false);
        ArrayNode catalog = root.putArray("queried_education_trait_keys"); provider.queriedEducationTraitKeys().forEach(catalog::add);
        ArrayNode rows = root.putArray("rows");
        for (ProviderChild row : provider.rows()) {
            ObjectNode child = rows.addObject(); child.put("child_full_id", row.childFullId()).put("role_source", row.roleSource());
            ArrayNode indices = child.putArray("occurrence_indices"); row.occurrenceIndices().forEach(indices::add);
            ObjectNode traits = child.putObject("education_traits"); traits.put("available", row.educationTraits().available());
            nullable(traits, "unavailable_reason", row.educationTraits().unavailableReason());
            if (row.educationTraits().presentTraitKeys() == null) { traits.putNull("present_trait_keys"); }
            else { ArrayNode keys = traits.putArray("present_trait_keys"); row.educationTraits().presentTraitKeys().forEach(keys::add); }
            CultureParameter culture = row.cultureParameter(); ObjectNode parameter = child.putObject("culture_parameter");
            parameter.put("key", culture.key()).put("available", culture.available());
            if (culture.cultureFullId() == null) { parameter.putNull("culture_full_id"); } else { parameter.put("culture_full_id", culture.cultureFullId()); }
            if (culture.value() == null) { parameter.putNull("value"); } else { parameter.put("value", culture.value()); }
            nullable(parameter, "unavailable_reason", culture.unavailableReason());
            for (String field : List.of("guardian_full_id", "guardian_culture_parameter", "rite_parameters", "education_type", "education_progress")) { child.putNull(field); }
            child.put("guardian_unavailable_reason", row.guardianUnavailableReason()).put("rite_unavailable_reason", row.riteUnavailableReason())
                    .put("education_variables_unavailable_reason", row.educationVariablesUnavailableReason());
        }
        byte[] result = write(root); require(result.length <= PROVIDER_LIMIT, "provider encoded output exceeds original bound"); return result;
    }

    private static FamilyInventory family(JsonNode family, Binding binding) {
        JsonNode descendants = object(family.get("current_first_heir_descendants_v1"), "descendants");
        JsonNode selected = object(descendants.get("child_inputs"), "selected child inputs");
        Frame descendantsFrame = familyFrame(descendants, binding), selectedFrame = familyFrame(selected, binding);
        boolean available = "available".equals(text(descendants.get("status"), "descendants status"));
        boolean complete = flag(descendants.get("roster_complete"), "roster_complete"), present = flag(descendants.get("family_present"), "family_present");
        JsonNode pointer = descendants.get("data_pointer_present"); Boolean pointerPresent = pointer == null || pointer.isNull() ? null : flag(pointer, "data_pointer_present");
        int count = boundedInt(descendants.get("native_child_count_raw"), 0, 4096, "native child count");
        List<Occurrence> occurrences = new ArrayList<>();
        for (JsonNode row : array(descendants.get("rows"), 4096, "raw occurrences")) {
            object(row, "raw occurrence"); boolean alive = flag(row.get("alive"), "alive");
            // Dead occurrence child_of_heir was not read by the original provider validator.
            Boolean child = alive ? flag(row.get("child_of_heir"), "child_of_heir") : null;
            occurrences.add(new Occurrence(uint(row.get("raw_character_id"), 32, "raw character ID").longValueExact(),
                    flag(row.get("generation_valid"), "generation_valid"), alive, child,
                    boundedInt(row.get("occurrence_index"), 0, 4095, "occurrence_index")));
        }
        List<SelectedChild> children = new ArrayList<>();
        for (JsonNode child : array(selected.get("rows"), 256, "selected children")) {
            object(child, "selected child"); children.add(new SelectedChild(new Full32(signed32(child.get("character_id"), "selected child ID")), indices(child.get("occurrence_indices"))));
        }
        return new FamilyInventory(descendantsFrame, selectedFrame, available, complete, present, pointerPresent, count, status(selected.get("status")), occurrences, children);
    }
    private static Frame familyFrame(JsonNode value, Binding binding) {
        BigInteger revision = integer(value.get("native_revision"), "family native_revision");
        int actor = signed32(value.get("played_character_id"), "family played ID");
        JsonNode heirValue = value.get("heir_character_id"); require(heirValue != null, "family heir frame missing");
        int heir;
        if (binding.frame().heirCharacter().signed() == -1) { require(heirValue.isNull(), "family no-heir sentinel changed"); heir = -1; }
        else { heir = signed32(heirValue, "family heir ID"); }
        return new Frame(revision, signed64(value.get("date_raw"), "family date"), new Full32(actor), new Full32(heir));
    }
    private static EducationTraits traits(JsonNode value) {
        exact(value, Set.of("available", "unavailable_reason", "present_trait_keys"), "education traits");
        JsonNode present = value.get("present_trait_keys");
        return new EducationTraits(flag(value.get("available"), "traits available"), nullableText(value.get("unavailable_reason"), "traits reason"),
                present.isNull() ? null : strings(present, 25, "present education traits"));
    }
    private static CultureParameter culture(JsonNode value) {
        exact(value, Set.of("key", "available", "culture_full_id", "value", "unavailable_reason"), "culture parameter");
        return new CultureParameter(text(value.get("key"), "culture key"), flag(value.get("available"), "culture available"),
                value.get("culture_full_id").isNull() ? null : uint(value.get("culture_full_id"), 32, "culture full ID").longValueExact(),
                value.get("value").isNull() ? null : flag(value.get("value"), "culture value"), nullableText(value.get("unavailable_reason"), "culture reason"));
    }
    private static Status status(JsonNode value) { Status status = Status.fromWire(text(value, "status")); require(status != Status.NOT_OBSERVED, "provider status malformed"); return status; }
    private static List<Integer> indices(JsonNode value) {
        List<Integer> result = new ArrayList<>();
        for (JsonNode index : array(value, 4096, "occurrence indices")) { result.add(boundedInt(index, 0, Integer.MAX_VALUE, "occurrence index")); }
        EducationProviderValidator.indices(result); return List.copyOf(result);
    }
    private static List<String> strings(JsonNode value, int limit, String name) { List<String> result = new ArrayList<>(); for (JsonNode item : array(value, limit, name)) { result.add(text(item, name)); } return List.copyOf(result); }
    private static JsonNode object(JsonNode value, String name) { require(value != null && value.isObject(), name + " must be object"); return value; }
    private static JsonNode array(JsonNode value, int limit, String name) { require(value != null && value.isArray() && value.size() <= limit, name + " must be bounded array"); return value; }
    private static void exact(JsonNode value, Set<String> keys, String name) { object(value, name); Set<String> actual = new HashSet<>(); value.fieldNames().forEachRemaining(actual::add); require(actual.equals(keys), name + " field set changed"); }
    private static String text(JsonNode value, String name) { require(value != null && value.isTextual(), name + " must be string"); return value.textValue(); }
    private static String nullableText(JsonNode value, String name) { require(value != null, name + " missing"); return value.isNull() ? null : text(value, name); }
    private static boolean flag(JsonNode value, String name) { require(value != null && value.isBoolean(), name + " must be boolean"); return value.booleanValue(); }
    private static BigInteger integer(JsonNode value, String name) { require(value != null && value.isIntegralNumber(), name + " requires integer token"); return value.bigIntegerValue(); }
    private static BigInteger uint(JsonNode value, int bits, String name) { BigInteger number = integer(value, name); require(number.signum() >= 0 && number.bitLength() <= bits, name + " must be uint" + bits); return number; }
    private static int signed32(JsonNode value, String name) { BigInteger number = integer(value, name); require(number.bitLength() <= 31, name + " must be signed int32"); return number.intValueExact(); }
    private static long signed64(JsonNode value, String name) { BigInteger number = integer(value, name); require(number.bitLength() <= 63, name + " must be signed int64"); return number.longValueExact(); }
    private static int boundedInt(JsonNode value, int low, int high, String name) { BigInteger number = integer(value, name); require(number.compareTo(BigInteger.valueOf(low)) >= 0 && number.compareTo(BigInteger.valueOf(high)) <= 0, name + " outside bounded integer domain"); return number.intValueExact(); }
    private static void same(Object actual, Object expected, String name) { require(expected.equals(actual), name + " changed"); }
    private static void nullable(ObjectNode value, String key, String text) { if (text == null) { value.putNull(key); } else { value.put(key, text); } }
    private static byte[] write(JsonNode value) { try { return JSON.writeValueAsBytes(value); } catch (IOException exception) { throw new IllegalArgumentException("cannot encode provider JSON", exception); } }
    private static void jsonDomain(JsonNode value) {
        require(value != null && (!value.isFloatingPointNumber() || Double.isFinite(value.doubleValue())), "non-finite JSON value");
        if (value.isTextual()) { unicode(value.textValue()); }
        if (value.isObject()) { value.fieldNames().forEachRemaining(EducationProviderCodec::unicode); }
        value.forEach(EducationProviderCodec::jsonDomain);
    }
    private static void unicode(String value) {
        for (int index = 0; index < value.length(); index++) {
            char current = value.charAt(index);
            if (Character.isHighSurrogate(current)) { require(index + 1 < value.length() && Character.isLowSurrogate(value.charAt(++index)), "unpaired Unicode surrogate"); }
            else { require(!Character.isLowSurrogate(current), "unpaired Unicode surrogate"); }
        }
    }
}
