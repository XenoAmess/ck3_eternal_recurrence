package org.xar.ck3.control.wave2.runtime.providerchain;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.providerchain.CreatorSourceManifest.CreatorSource;
import org.xar.ck3.control.wave2.runtime.providerchain.CreatorSourceManifest.CreatorTool;
import org.xar.ck3.control.wave2.runtime.providerchain.CreatorSourceManifest.ResolvedEntrySource;

/** Strict data adapter; decoded values cannot reconstruct held resources or an issuer. */
public final class ProviderChainCodec {
    public static final String INPUT_SCHEMA = "xar.java.canonical-provider-creator-manifest-input/v1";
    private ProviderChainCodec() { }

    public static CreatorSourceManifest decodeManifest(byte[] raw) {
        return parseManifest(StrictJson.parse(raw, 1_048_576));
    }

    public static CreatorSourceManifest parseManifest(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("schema", "creator_sources", "resolved_entry_sources"));
        StrictJson.require(row.get("schema").isTextual() && row.get("schema").textValue().equals(INPUT_SCHEMA),
                "exact provider creator manifest input schema required");
        JsonNode creators = row.get("creator_sources"), entries = row.get("resolved_entry_sources");
        StrictJson.require(creators.isArray() && creators.size() == 3 && entries.isArray()
                        && entries.size() > 0 && entries.size() <= 8, "finite original source arrays required");
        List<CreatorSource> creatorPins = new ArrayList<>();
        for (JsonNode source : creators) {
            ObjectNode pin = StrictJson.object(source, Set.of("name", "sha256"));
            creatorPins.add(new CreatorSource(CreatorTool.fromFilename(StrictJson.text(pin.get("name"))),
                    new SourceSha256(StrictJson.text(pin.get("sha256")))));
        }
        List<ResolvedEntrySource> entryPins = new ArrayList<>();
        for (JsonNode entry : entries) {
            StrictJson.require(entry.isArray() && entry.size() == 2, "one entry path/SHA pair required");
            entryPins.add(new ResolvedEntrySource(StrictJson.text(entry.get(0)), new SourceSha256(StrictJson.text(entry.get(1)))));
        }
        return new CreatorSourceManifest(creatorPins, entryPins);
    }

    public static DirectScriptCommand parseCommand(JsonNode value) {
        StrictJson.require(value != null && value.isArray(), "actual argv array required");
        List<String> arguments = new ArrayList<>();
        for (JsonNode argument : value) {
            StrictJson.require(argument.isTextual(), "actual argv text required");
            arguments.add(argument.textValue());
        }
        return new DirectScriptCommand(arguments);
    }

    public static byte[] encodeManifestInput(CreatorSourceManifest manifest) {
        StrictJson.require(manifest != null, "creator manifest required");
        ObjectNode row = StrictJson.object(); row.put("schema", INPUT_SCHEMA);
        ArrayNode creators = row.putArray("creator_sources");
        for (CreatorSource creator : manifest.creators()) {
            ObjectNode pin = creators.addObject();
            pin.put("name", creator.tool().filename()); pin.put("sha256", creator.sha256().value());
        }
        ArrayNode entries = row.putArray("resolved_entry_sources");
        for (ResolvedEntrySource entry : manifest.entries()) {
            ArrayNode pin = entries.addArray(); pin.add(entry.path()); pin.add(entry.sha256().value());
        }
        return StrictJson.canonical(row, 1_048_576);
    }
}
