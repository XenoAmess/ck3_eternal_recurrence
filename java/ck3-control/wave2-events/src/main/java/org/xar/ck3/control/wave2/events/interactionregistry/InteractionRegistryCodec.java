package org.xar.ck3.control.wave2.events.interactionregistry;

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
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistry.*;

/** Strict immutable entry/facts boundary. Parsing alone does not produce VerifiedReview. */
public final class InteractionRegistryCodec {
    public static final int MAX_ENTRY_BYTES = 65_536;
    public static final int MAX_FACTS_BYTES = 1_048_576;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private InteractionRegistryCodec() { }

    public static Lookup parseLookup(byte[] raw) {
        ObjectNode row = object(parse(raw, 4096), "schema", "build", "definition", "gui_sha256");
        StrictJson.require("xar.interaction-registry-lookup/v1".equals(text(row, "schema")), "unsupported lookup schema");
        ObjectNode build = object(row.get("build"), "version", "exe_sha256");
        ObjectNode definition = object(row.get("definition"), "canonical_key", "deterministic_key_hash");
        return new Lookup(new BuildIdentity(text(build, "version"), text(build, "exe_sha256")),
                new Definition(text(definition, "canonical_key"), StrictJson.integer(definition.get("deterministic_key_hash"), 0, 0xffff_ffffL)), text(row, "gui_sha256"));
    }

    public static byte[] encodeLookup(Lookup value) {
        ObjectNode row = StrictJson.object(); row.put("schema", "xar.interaction-registry-lookup/v1");
        ObjectNode build = StrictJson.object(); build.put("version", value.build().version()); build.put("exe_sha256", value.build().exeSha256()); row.set("build", build);
        ObjectNode definition = StrictJson.object(); definition.put("canonical_key", value.definition().canonicalKey()); definition.put("deterministic_key_hash", value.definition().deterministicKeyHash());
        row.set("definition", definition); row.put("gui_sha256", value.guiSha256()); return StrictJson.canonical(row, 4096);
    }

    public static Entry parseEntry(byte[] raw) {
        ObjectNode row = object(parse(raw, MAX_ENTRY_BYTES), "schema", "fingerprint", "build", "canonical_key", "deterministic_key_hash",
                "source_sha256", "gui_sha256", "classification", "preferred_action", "source_path", "gui_path", "source_facts", "reason");
        StrictJson.require(ENTRY_SCHEMA.equals(text(row, "schema")), "unsupported registry entry schema");
        ObjectNode ref = object(row.get("source_facts"), "path", "sha256");
        return new Entry(text(row, "fingerprint"), binding(row), text(row, "classification"), text(row, "preferred_action"), paths(row),
                new SourceRef(text(ref, "path"), text(ref, "sha256")), text(row, "reason"));
    }

    public static Facts parseFacts(byte[] raw) {
        ObjectNode row = object(parse(raw, MAX_FACTS_BYTES), "schema", "fingerprint", "build", "canonical_key", "deterministic_key_hash",
                "source_sha256", "gui_sha256", "source_path", "gui_path", "source_relative", "category", "definition", "on_accept", "on_decline", "analysis", "material_effects_verified");
        StrictJson.require(FACTS_SCHEMA.equals(text(row, "schema")), "unsupported registry facts schema");
        JsonNode material = row.get("material_effects_verified");
        StrictJson.require(material.isBoolean() && !material.booleanValue(), "source catalogue cannot claim material execution");
        JsonNode categories = row.get("category"); StrictJson.require(categories.isArray() && categories.size() <= 64, "bounded categories required");
        List<String> category = new ArrayList<>(); categories.forEach(value -> category.add(StrictJson.text(value)));
        return new Facts(text(row, "fingerprint"), binding(row), paths(row), text(row, "source_relative"), category,
                sourceBody(row.get("definition")), nullableBody(row.get("on_accept")), nullableBody(row.get("on_decline")), sourceBody(row.get("analysis")));
    }

    public static String fingerprint(Binding binding) { return digest(StrictJson.canonical(bindingJson(binding))); }
    public static String digest(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException("JDK SHA-256 unavailable", error); }
    }
    public static byte[] encodeEntry(Entry value) {
        ObjectNode row = bindingJson(value.binding()); row.put("schema", ENTRY_SCHEMA); row.put("fingerprint", value.fingerprint());
        row.put("classification", value.classification()); row.put("preferred_action", value.preferredAction());
        row.put("source_path", value.paths().sourcePath()); row.put("gui_path", value.paths().guiPath()); row.put("reason", value.reason());
        ObjectNode ref = StrictJson.object(); ref.put("path", value.sourceFacts().path()); ref.put("sha256", value.sourceFacts().sha256()); row.set("source_facts", ref);
        return StrictJson.canonical(row, MAX_ENTRY_BYTES);
    }

    public static byte[] encodeFacts(Facts value) {
        ObjectNode row = bindingJson(value.binding()); row.put("schema", FACTS_SCHEMA); row.put("fingerprint", value.fingerprint());
        row.put("source_path", value.paths().sourcePath()); row.put("gui_path", value.paths().guiPath()); row.put("source_relative", value.sourceRelative());
        var categories = row.putArray("category"); value.category().forEach(categories::add); row.put("definition", value.definition());
        if (value.onAccept() == null) { row.putNull("on_accept"); } else { row.put("on_accept", value.onAccept()); }
        if (value.onDecline() == null) { row.putNull("on_decline"); } else { row.put("on_decline", value.onDecline()); }
        row.put("analysis", value.analysis()); row.put("material_effects_verified", false);
        try {
            byte[] raw = JSON.writeValueAsBytes(row); StrictJson.require(raw.length <= MAX_FACTS_BYTES, "facts encoding exceeds byte budget"); return raw;
        } catch (IOException error) { throw new ContractViolationException("facts encoding failed", error); }
    }

    private static Binding binding(ObjectNode row) {
        ObjectNode build = object(row.get("build"), "version", "exe_sha256");
        return new Binding(new BuildIdentity(text(build, "version"), text(build, "exe_sha256")),
                new Definition(text(row, "canonical_key"), StrictJson.integer(row.get("deterministic_key_hash"), 0, 0xffff_ffffL)), text(row, "source_sha256"), text(row, "gui_sha256"));
    }
    private static ObjectNode bindingJson(Binding value) {
        ObjectNode row = StrictJson.object(); ObjectNode build = StrictJson.object(); build.put("version", value.build().version()); build.put("exe_sha256", value.build().exeSha256());
        row.set("build", build); row.put("canonical_key", value.definition().canonicalKey()); row.put("deterministic_key_hash", value.definition().deterministicKeyHash());
        row.put("source_sha256", value.sourceSha256()); row.put("gui_sha256", value.guiSha256()); return row;
    }
    private static SourcePaths paths(ObjectNode row) { return new SourcePaths(text(row, "source_path"), text(row, "gui_path")); }
    private static JsonNode parse(byte[] raw, int maximum) {
        StrictJson.require(raw != null && raw.length > 0 && raw.length <= maximum, "bounded nonempty registry JSON required");
        try {
            String decoded = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT)
                    .decode(ByteBuffer.wrap(raw)).toString();
            JsonNode result = JSON.readTree(decoded); StrictJson.require(result != null, "registry JSON value required"); return result;
        } catch (IOException error) { throw new ContractViolationException("invalid UTF-8, duplicate fields or malformed registry JSON", error); }
    }
    private static ObjectNode object(JsonNode node, String... fields) { return StrictJson.object(node, Set.of(fields)); }
    private static String text(ObjectNode row, String field) { String value = StrictJson.text(row.get(field)); stable(value); return value; }
    private static String sourceBody(JsonNode node) { StrictJson.require(node != null && node.isTextual(), "source body string required"); String value = node.textValue(); body(value); return value; }
    private static String nullableBody(JsonNode node) { StrictJson.require(node != null, "required nullable source body missing"); return node.isNull() ? null : sourceBody(node); }
}
