package org.xar.ck3.dynastic.release;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.MapperFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.json.JsonMapper;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Set;

/** Concentrates strict JSON boundary validation before constructing internal records. */
public final class ManifestJson {
    private static final ObjectMapper MAPPER = JsonMapper.builder()
            .enable(JsonParser.Feature.STRICT_DUPLICATE_DETECTION)
            .enable(MapperFeature.SORT_PROPERTIES_ALPHABETICALLY)
            .enable(SerializationFeature.INDENT_OUTPUT)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
            .build();
    private static final Set<String> MANIFEST_FIELDS = Set.of("format_version", "product_id", "mod_version", "git_tag", "git_sha", "workshop_item_id", "files");
    private static final Set<String> ENTRY_FIELDS = Set.of("path", "size", "sha256");

    private ManifestJson() { }

    public static byte[] encode(ReleaseManifest manifest) throws IOException {
        return (MAPPER.writeValueAsString(manifest) + "\n").getBytes(StandardCharsets.UTF_8);
    }

    public static ReleaseManifest decode(byte[] bytes, ReleaseProduct product) throws IOException {
        JsonNode root = MAPPER.readTree(bytes);
        exactFields(root, MANIFEST_FIELDS);
        JsonNode format = root.get("format_version");
        if (!format.isIntegralNumber() || !format.canConvertToInt() || format.intValue() != 1) {
            throw new IllegalArgumentException("format_version must be integer 1");
        }
        requireText(root, "product_id", false);
        requireText(root, "mod_version", false);
        requireText(root, "git_sha", false);
        requireText(root, "git_tag", true);
        requireText(root, "workshop_item_id", true);
        JsonNode entries = root.get("files");
        if (!entries.isArray()) throw new IllegalArgumentException("manifest files must be an array");
        for (JsonNode entry : entries) {
            exactFields(entry, ENTRY_FIELDS);
            requireText(entry, "path", false);
            requireText(entry, "sha256", false);
            JsonNode size = entry.get("size");
            if (!size.isIntegralNumber() || !size.canConvertToLong() || size.longValue() < 0 || size.longValue() > 9_007_199_254_740_991L) {
                throw new IllegalArgumentException("file size must be a nonnegative safe integer");
            }
        }
        ReleaseManifest manifest = MAPPER.treeToValue(root, ReleaseManifest.class);
        if (!manifest.productId().equals(product.productId())
                || !manifest.files().stream().map(ReleaseManifest.FileEntry::path).toList().equals(product.runtimeFiles())
                || (manifest.gitTag() != null && !manifest.gitTag().equals(product.tagPrefix() + manifest.modVersion()))) {
            throw new IllegalArgumentException("manifest product, runtime inventory or tag mismatch");
        }
        return manifest;
    }

    private static void exactFields(JsonNode node, Set<String> expected) {
        if (node == null || !node.isObject()) throw new IllegalArgumentException("expected JSON object");
        Set<String> actual = new HashSet<>();
        node.fieldNames().forEachRemaining(actual::add);
        if (!actual.equals(expected)) throw new IllegalArgumentException("JSON fields mismatch; expected " + expected + ", got " + actual);
    }

    private static void requireText(JsonNode node, String field, boolean nullable) {
        JsonNode value = node.get(field);
        if (!value.isTextual() && !(nullable && value.isNull())) {
            throw new IllegalArgumentException(field + " must be " + (nullable ? "text or explicit null" : "text"));
        }
    }
}
