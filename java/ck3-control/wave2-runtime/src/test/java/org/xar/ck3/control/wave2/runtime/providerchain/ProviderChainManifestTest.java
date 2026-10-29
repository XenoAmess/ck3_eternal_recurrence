package org.xar.ck3.control.wave2.runtime.providerchain;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.providerchain.CreatorSourceManifest.CreatorSource;
import org.xar.ck3.control.wave2.runtime.providerchain.CreatorSourceManifest.ResolvedEntrySource;
import static org.junit.jupiter.api.Assertions.*;

final class ProviderChainManifestTest {
    static JsonNode golden() throws IOException {
        try (InputStream stream = ProviderChainManifestTest.class.getResourceAsStream("/providerchain/providerchain-golden.json")) {
            if (stream == null) { throw new IOException("original provider-chain producer golden required, never skipped"); }
            return StrictJson.parse(stream.readAllBytes(), 1_048_576);
        }
    }

    @Test void realOriginalCreatorDigestAndPythonAsciiManifestBytes() throws IOException {
        for (JsonNode sample : golden().get("manifest_cases")) {
            CreatorSourceManifest manifest = ProviderChainCodec.parseManifest(sample.get("input"));
            assertArrayEquals(sample.get("expected_manifest_json").textValue().getBytes(StandardCharsets.UTF_8),
                    manifest.originalManifestBytes(), sample.get("name").textValue());
            assertEquals(sample.get("expected_digest").textValue(), manifest.creatorDigest().value());
            assertEquals(manifest, ProviderChainCodec.decodeManifest(ProviderChainCodec.encodeManifestInput(manifest)));
            assertFalse(manifest.grantsProviderSourceQualification());
        }
    }

    @Test void sourceListsAreDetachedImmutableAndEntriesUseOriginalUnicodeOrder() throws IOException {
        CreatorSourceManifest original = ProviderChainCodec.parseManifest(golden().get("manifest_cases").get(1).get("input"));
        List<CreatorSource> creators = new ArrayList<>(original.creators());
        List<ResolvedEntrySource> entries = new ArrayList<>(original.entries());
        Collections.reverse(entries);
        CreatorSourceManifest reordered = new CreatorSourceManifest(creators, entries);
        entries.clear(); creators.clear();
        assertEquals(original, reordered);
        assertThrows(UnsupportedOperationException.class, () -> reordered.creators().clear());
        assertThrows(UnsupportedOperationException.class, () -> reordered.entries().clear());
        List<CreatorSource> wrongOrder = new ArrayList<>(original.creators()); Collections.reverse(wrongOrder);
        assertThrows(ContractViolationException.class, () -> new CreatorSourceManifest(wrongOrder, original.entries()));
        assertTrue(new String(original.originalManifestBytes(), StandardCharsets.UTF_8).contains("\\u007f"));
    }

    @Test void manifestInputRejectsMissingNullUnknownAndQualificationFlags() throws IOException {
        ObjectNode original = (ObjectNode) golden().get("manifest_cases").get(0).get("input");
        for (String field : List.of("schema", "creator_sources", "resolved_entry_sources")) {
            ObjectNode missing = original.deepCopy(); missing.remove(field);
            assertThrows(ContractViolationException.class, () -> ProviderChainCodec.parseManifest(missing));
            ObjectNode nullable = original.deepCopy(); nullable.putNull(field);
            assertThrows(ContractViolationException.class, () -> ProviderChainCodec.parseManifest(nullable));
        }
        ObjectNode forged = original.deepCopy(); forged.put("source_verified", true);
        assertThrows(ContractViolationException.class, () -> ProviderChainCodec.parseManifest(forged));
        ObjectNode future = original.deepCopy(); future.put("schema", ProviderChainCodec.INPUT_SCHEMA + "future");
        assertThrows(ContractViolationException.class, () -> ProviderChainCodec.parseManifest(future));
    }

    @Test void entriesKeepOneToEightDistinctAbsolutePathPinsAndExactDigests() throws IOException {
        ObjectNode original = (ObjectNode) golden().get("manifest_cases").get(0).get("input");
        ObjectNode empty = original.deepCopy(); empty.putArray("resolved_entry_sources");
        assertThrows(ContractViolationException.class, () -> ProviderChainCodec.parseManifest(empty));
        ObjectNode nine = original.deepCopy(); ArrayNode tooMany = nine.putArray("resolved_entry_sources");
        for (int i = 0; i < 9; i++) { ArrayNode pin = tooMany.addArray(); pin.add("D:/source/" + i + ".py"); pin.add("a".repeat(64)); }
        assertThrows(ContractViolationException.class, () -> ProviderChainCodec.parseManifest(nine));
        tooMany.remove(8); assertEquals(8, ProviderChainCodec.parseManifest(nine).entries().size());
        ObjectNode duplicate = original.deepCopy(); ArrayNode refs = (ArrayNode) duplicate.get("resolved_entry_sources");
        refs.set(1, refs.get(0).deepCopy());
        assertThrows(ContractViolationException.class, () -> ProviderChainCodec.parseManifest(duplicate));
        for (String bad : List.of("relative.py", "D:relative.py", "/rooted-but-no-Windows-drive.py")) {
            ObjectNode changed = original.deepCopy(); ((ArrayNode) changed.get("resolved_entry_sources").get(0)).set(0, StrictJson.parse(("\"" + bad + "\"").getBytes(StandardCharsets.UTF_8)));
            assertThrows(ContractViolationException.class, () -> ProviderChainCodec.parseManifest(changed));
        }
        for (String token : List.of("true", "1.0", "null", "\"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\"")) {
            ObjectNode changed = original.deepCopy(); ((ObjectNode) changed.get("creator_sources").get(0)).set("sha256", StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
            assertThrows(ContractViolationException.class, () -> ProviderChainCodec.parseManifest(changed));
        }
    }

    @Test void malformedWireAndOriginalManifestDigestChangesAreVisible() throws IOException {
        ObjectNode original = (ObjectNode) golden().get("manifest_cases").get(0).get("input");
        CreatorSourceManifest baseline = ProviderChainCodec.parseManifest(original);
        ObjectNode changed = original.deepCopy(); ((ObjectNode) changed.get("creator_sources").get(0)).put("sha256", "f".repeat(64));
        assertNotEquals(baseline.creatorDigest(), ProviderChainCodec.parseManifest(changed).creatorDigest());
        String encoded = new String(ProviderChainCodec.encodeManifestInput(baseline), StandardCharsets.UTF_8);
        String duplicate = encoded.substring(0, encoded.length() - 1) + ",\"schema\":\"" + ProviderChainCodec.INPUT_SCHEMA + "\"}";
        assertThrows(ContractViolationException.class, () -> ProviderChainCodec.decodeManifest(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> ProviderChainCodec.decodeManifest((encoded + "{}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> ProviderChainCodec.decodeManifest(new byte[] {(byte) 0xff}));
    }
}
