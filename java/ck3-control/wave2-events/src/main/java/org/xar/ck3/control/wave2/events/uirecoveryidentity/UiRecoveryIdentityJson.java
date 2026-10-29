package org.xar.ck3.control.wave2.events.uirecoveryidentity;

import static org.xar.ck3.control.wave2.events.uirecoveryidentity.UiRecoverySourceModel.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.ChoiceIdentity;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.Field;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.IntegerIdentity;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.TextIdentity;

/** Strict request wrapper plus a declared projection of existing native source/catalogue containers. */
public final class UiRecoveryIdentityJson {
    public static final String SCHEMA = "xar.java-ui-recovery-source-key-request/v1";
    private static final int MAX_BYTES = 65_536;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private UiRecoveryIdentityJson() { }

    public static Projection decode(byte[] raw) {
        ObjectNode row = object(parse(raw)); Set<String> names = new HashSet<>(); row.fieldNames().forEachRemaining(names::add);
        require(names.equals(Set.of("schema", "window", "backend_sha256")), "exact source-key wrapper fields");
        require(SCHEMA.equals(text(row.get("schema"), false)), "source-key schema");
        try {
            String backend = text(row.get("backend_sha256"), false);
            require(backend.matches("[0-9a-fA-F]{64}"), "backend SHA256 required");
            ObjectNode window = object(row.get("window"));
            JsonNode chosenSource = truthy(window.get("stable_source_identity"))
                    ? window.get("stable_source_identity") : window.get("source_identity");
            ObjectNode source = object(chosenSource);
            List<DisplayedChoice> displayed = new ArrayList<>();
            for (JsonNode choice : list(window.get("choices"), 256)) {
                ObjectNode shown = object(choice);
                displayed.add(new DisplayedChoice(identity(shown.get("choice_id")), nullableText(shown.get("label")), nullableText(shown.get("role"))));
            }
            List<CatalogueChoice> catalogue = new ArrayList<>();
            for (JsonNode choice : list(source.get("choice_catalogue"), 256)) {
                ObjectNode item = object(choice);
                List<Callback> callbacks = new ArrayList<>();
                for (JsonNode callback : list(item.get("callback_identities"), 256)) {
                    ObjectNode entry = object(callback);
                    callbacks.add(new Callback(address(entry.get("vtable_module_rva")), address(entry.get("function_module_rva"))));
                }
                catalogue.add(new CatalogueChoice(field(item, "choice_id", UiRecoveryIdentityJson::identity),
                        text(item.get("runtime_name"), false), address(item.get("widget_vtable_module_rva")),
                        field(item, "role", value -> text(value, true)), callbacks));
            }
            String gameSha = text(source.get("game_exe_sha256"), false); require(gameSha.matches("[0-9a-fA-F]{64}"), "game SHA256 required");
            SourceIdentity identity = new SourceIdentity(gameSha, nullableText(source.get("backend_sha256")),
                    text(source.get("native_adapter_id"), false), text(source.get("root_runtime_name"), false),
                    text(source.get("root_type"), false), address(source.get("root_vtable_module_rva")), catalogue);
            return new Ready(new Input(backend, identity, displayed));
        } catch (IllegalArgumentException error) { return new Unavailable(error.getMessage()); }
    }

    public static byte[] fingerprint(byte[] raw) { return fingerprint(raw, new UiRecoverySourceFingerprint()); }

    public static byte[] fingerprint(byte[] raw, UiRecoveryIdentityPort consumer) {
        java.util.Objects.requireNonNull(consumer);
        Projection projection = decode(raw);
        if (projection instanceof Unavailable) { return "null".getBytes(StandardCharsets.UTF_8); }
        return encode(consumer.identify(((Ready) projection).input()));
    }

    public static byte[] encode(Optional<Fingerprint> fingerprint) {
        java.util.Objects.requireNonNull(fingerprint);
        if (fingerprint.isEmpty()) { return "null".getBytes(StandardCharsets.UTF_8); }
        Fingerprint value = fingerprint.orElseThrow();
        byte[] result = ("{\"source_key\":\"" + value.sourceKey() + "\",\"stable_source\":"
                + StableSourceCanonical.source(value.stableSource()) + "}").getBytes(StandardCharsets.UTF_8);
        require(result.length <= MAX_BYTES, "source-key output byte bound"); return result;
    }

    private static RelativeAddress address(JsonNode node) {
        return node != null && node.isTextual() ? new SymbolicAddress(text(node, false)) : new NumericAddress(integer(node));
    }
    private static ChoiceIdentity identity(JsonNode node) {
        if (node != null && node.isTextual()) { return new TextIdentity(text(node, false)); }
        BigInteger value = integer(node);
        require(value.compareTo(BigInteger.ONE.shiftLeft(63).negate()) >= 0 && value.compareTo(BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE)) <= 0,
                "choice identity exact 64-bit domain"); return new IntegerIdentity(value);
    }
    private static boolean truthy(JsonNode node) {
        if (node == null || node.isNull()) { return false; }
        if (node.isBoolean()) { return node.booleanValue(); }
        if (node.isContainerNode()) { return !node.isEmpty(); }
        if (node.isTextual()) { return !node.textValue().isEmpty(); }
        if (node.isNumber()) { return node.decimalValue().signum() != 0; }
        return true;
    }
    private static <T> Field<T> field(ObjectNode node, String name, Function<JsonNode, T> decode) {
        return !node.has(name) ? Field.missing() : node.get(name).isNull() ? Field.nullValue() : Field.of(decode.apply(node.get(name)));
    }
    private static Optional<String> nullableText(JsonNode node) { return node == null || node.isNull() ? Optional.empty() : Optional.of(text(node, true)); }
    private static List<JsonNode> list(JsonNode node, int maximum) {
        require(node != null && node.isArray() && node.size() <= maximum, "bounded native list required");
        List<JsonNode> result = new ArrayList<>(); node.forEach(result::add); return result;
    }
    private static BigInteger integer(JsonNode node) { require(node != null && node.isIntegralNumber(), "integer token required; no bool/float/string coercion"); return node.bigIntegerValue(); }
    private static ObjectNode object(JsonNode node) { require(node instanceof ObjectNode, "native object required"); return (ObjectNode) node; }
    private static String text(JsonNode node, boolean emptyAllowed) {
        require(node != null && node.isTextual(), "string token required"); String value = node.textValue();
        require(emptyAllowed || !value.isEmpty(), "nonempty native text"); if (!value.isEmpty()) { StrictJson.text(value); } return value;
    }
    private static JsonNode parse(byte[] raw) {
        require(raw != null && raw.length > 0 && raw.length <= MAX_BYTES, "bounded UTF-8 source-key JSON required");
        try {
            String value = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            JsonNode node = JSON.readTree(value); require(node != null, "JSON value required"); validate(node, 0); return node;
        } catch (IOException error) { throw new IllegalArgumentException("invalid UTF-8/duplicate/trailing source JSON", error); }
    }
    private static void validate(JsonNode node, int depth) {
        require(depth <= 64, "bounded source-key nesting");
        if (node.isTextual() && !node.textValue().isEmpty()) { StrictJson.text(node.textValue()); }
        if (node.isFloatingPointNumber()) { require(Double.isFinite(node.doubleValue()), "finite JSON number required"); }
        if (node.isObject()) { node.fieldNames().forEachRemaining(name -> { if (!name.isEmpty()) { StrictJson.text(name); } }); }
        if (node.isContainerNode()) { node.forEach(child -> validate(child, depth + 1)); }
    }
    private static void require(boolean condition, String message) { if (!condition) { throw new IllegalArgumentException(message); } }
}
