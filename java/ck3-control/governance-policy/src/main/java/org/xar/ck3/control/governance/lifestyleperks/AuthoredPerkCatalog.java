package org.xar.ck3.control.governance.lifestyleperks;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Collections;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.lifestyleperks.LifestylePerksModel.Lifestyle;

/** Immutable ordered identity projection; ownership/DLC/legality never inferred from this catalog. */
public final class AuthoredPerkCatalog {
    public static final String ORIGINAL_CATALOG_SHA256 = "bc74e9eee7e4902771c8018b2e69cded51b781e77323f0d3b936e82bbaf6a117";
    public static final String PROJECTION_SHA256 = "a23f5ea9d08d9624ee83dcd82b77eecc699c85d1b05cefb4d270baa5cfaad09b";
    private static final Map<String, Lifestyle> PERKS = load();
    private AuthoredPerkCatalog() { }
    public static Map<String, Lifestyle> perks() { return PERKS; }

    private static Map<String, Lifestyle> load() {
        try (InputStream stream = AuthoredPerkCatalog.class.getResourceAsStream("/lifestyleperks/authored-perks-12004.json")) {
            StrictJson.require(stream != null, "pinned lifestyle catalog resource missing");
            byte[] raw = stream.readNBytes(32_769);
            StrictJson.require(raw.length <= 32_768, "catalog projection byte budget");
            String digest = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
            StrictJson.require(digest.equals(PROJECTION_SHA256), "catalog projection bytes changed");
            JsonNode node = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "original_catalog_path",
                    "original_catalog_sha256", "tree_count", "perk_count", "lifestyle_keys", "perks"));
            StrictJson.require(StrictJson.text(node.get("schema")).equals("xar.java.lifestyle-authored-perks-projection.v1"), "catalog schema");
            StrictJson.require(StrictJson.text(node.get("original_catalog_sha256")).equals(ORIGINAL_CATALOG_SHA256), "catalog original source SHA");
            StrictJson.require(StrictJson.text(node.get("original_catalog_path")).equals("ck3_autonomous_player/src/xar_autoplayer/data/vanilla_lifestyle_catalog_12004.json"), "catalog original path");
            StrictJson.integer(node.get("tree_count"), 18, 18); StrictJson.integer(node.get("perk_count"), 162, 162);
            JsonNode keys = node.get("lifestyle_keys");
            StrictJson.require(keys != null && keys.isArray() && keys.size() == 6, "six catalog lifestyles required");
            Set<Lifestyle> found = new java.util.HashSet<>();
            for (JsonNode key : keys) { StrictJson.require(found.add(Lifestyle.fromWire(StrictJson.text(key))), "duplicate catalog lifestyle"); }
            JsonNode rows = node.get("perks");
            StrictJson.require(rows != null && rows.isArray() && rows.size() == 162, "162 authored perk identities required");
            LinkedHashMap<String, Lifestyle> result = new LinkedHashMap<>();
            for (JsonNode row : rows) {
                StrictJson.object(row, Set.of("key", "lifestyle_key"));
                String key = StrictJson.text(row.get("key"));
                StrictJson.require(key.endsWith("_perk"), "authored perk key required");
                StrictJson.require(result.putIfAbsent(key, Lifestyle.fromWire(StrictJson.text(row.get("lifestyle_key")))) == null,
                        "duplicate authored perk identity");
            }
            for (Lifestyle lifestyle : Lifestyle.values()) {
                StrictJson.require(result.values().stream().filter(lifestyle::equals).count() == 27, "27 perks per lifestyle required");
            }
            return Collections.unmodifiableMap(result);
        } catch (IOException | NoSuchAlgorithmException error) {
            throw new IllegalStateException("cannot load pinned authored perk catalog", error);
        }
    }
}
