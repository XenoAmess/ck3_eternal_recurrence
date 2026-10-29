package org.xar.ck3.control.wave3.governance.lifecycle;

import static org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding.require;

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
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

/** Exact six-field lifecycle ABI shared by the original restore and rebinder consumers. */
public final class SuccessionLifecycleCodec {
    public static final int MAX_BYTES = 16_384;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build()).enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private static final Set<String> KEYS = Set.of("schema", "lifecycle", "xar_enabled", "pact_contract", "source", "environment_sha256");
    private SuccessionLifecycleCodec() { }
    public static SuccessionLifecycleBinding decode(byte[] bytes) { return decodeNode(parse(bytes)); }
    public static byte[] normalize(byte[] bytes) { return encode(decode(bytes)); }
    static SuccessionLifecycleBinding decodeNode(JsonNode value) {
        exact(value, KEYS); require(text(field(value, "schema")).equals(SuccessionLifecycleBinding.SCHEMA), "lifecycle schema changed");
        String lifecycle = text(field(value, "lifecycle")), xar = nullableText(field(value, "xar_enabled"));
        String pact = text(field(value, "pact_contract")), source = text(field(value, "source"));
        String environment = nullableText(field(value, "environment_sha256"));
        for (SuccessionLifecycleBinding.Profile profile : SuccessionLifecycleBinding.Profile.values()) {
            if (profile.lifecycle().equals(lifecycle) && Objects.equals(profile.xarEnabled(), xar) && profile.pactContract().equals(pact)) {
                return new SuccessionLifecycleBinding(profile, source, environment);
            }
        }
        throw new IllegalArgumentException("lifecycle support profile is inconsistent");
    }
    public static byte[] encode(SuccessionLifecycleBinding binding) {
        ObjectNode value = JSON.createObjectNode(); value.put("schema", SuccessionLifecycleBinding.SCHEMA).put("lifecycle", binding.profile().lifecycle());
        nullable(value, "xar_enabled", binding.profile().xarEnabled()); value.put("pact_contract", binding.profile().pactContract()).put("source", binding.source()); nullable(value, "environment_sha256", binding.environmentSha256());
        return encodeNode(value);
    }
    static JsonNode parse(byte[] bytes) {
        require(bytes != null && bytes.length > 0 && bytes.length <= MAX_BYTES, "bounded lifecycle JSON required");
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
            JsonNode value = JSON.readTree(text); require(value != null, "JSON value required"); unicode(value); return value;
        } catch (IOException error) { throw new IllegalArgumentException("invalid lifecycle UTF8/JSON/duplicate/trailing fields", error); }
    }
    static byte[] encodeNode(JsonNode value) {
        unicode(value); try { byte[] bytes = JSON.writeValueAsBytes(value); require(bytes.length <= MAX_BYTES, "lifecycle byte limit exceeded"); return bytes; }
        catch (IOException error) { throw new IllegalArgumentException("lifecycle encoding failed", error); }
    }
    static void exact(JsonNode value, Set<String> expected) { require(value != null && value.isObject(), "lifecycle object required"); Set<String> actual = new HashSet<>(); value.fieldNames().forEachRemaining(actual::add); require(actual.equals(expected), "lifecycle fields changed"); }
    static JsonNode field(JsonNode value, String name) { require(value != null && value.isObject() && value.has(name), "missing lifecycle field: " + name); return value.get(name); }
    static String text(JsonNode value) { require(value != null && value.isTextual() && !value.textValue().isEmpty(), "nonempty lifecycle string required"); return value.textValue(); }
    private static String nullableText(JsonNode value) { return value.isNull() ? null : text(value); }
    private static void nullable(ObjectNode value, String key, String text) { if (text == null) { value.putNull(key); } else { value.put(key, text); } }
    private static void unicode(JsonNode value) { if (value.isTextual()) { unicode(value.textValue()); } if (value.isObject()) { value.fieldNames().forEachRemaining(SuccessionLifecycleCodec::unicode); } if (value.isContainerNode()) { value.forEach(SuccessionLifecycleCodec::unicode); } }
    private static void unicode(String text) { for (int i = 0; i < text.length(); i++) { char ch = text.charAt(i); if (Character.isHighSurrogate(ch)) { require(i + 1 < text.length() && Character.isLowSurrogate(text.charAt(++i)), "unpaired JSON surrogate"); } else { require(!Character.isLowSurrogate(ch), "unpaired JSON surrogate"); } } }
}
