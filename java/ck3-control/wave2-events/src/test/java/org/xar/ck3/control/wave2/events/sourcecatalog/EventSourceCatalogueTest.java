package org.xar.ck3.control.wave2.events.sourcecatalog;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;

final class EventSourceCatalogueTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static JsonNode golden() throws IOException {
        try (InputStream input = EventSourceCatalogueTest.class.getResourceAsStream("/sourcecatalog/event-source-catalogue-golden-v1.json.gz")) {
            assertNotNull(input, "actual original source producer fixture is required; do not skip");
            try (GZIPInputStream uncompressed = new GZIPInputStream(input)) { return JSON.readTree(uncompressed); }
        }
    }
    private static SourceCatalogueCodec.Request request(JsonNode node) throws IOException {
        return SourceCatalogueCodec.decode(JSON.writeValueAsBytes(node));
    }

    @Test void matchesActualHelpersAndSourceCatalogueOnPinnedArchivedSource() throws IOException {
        JsonNode corpus = golden();
        assertEquals("xar.ck3.event-source-catalogue-golden/v1", corpus.get("schema").textValue());
        assertEquals(28, corpus.get("cases").size());
        assertEquals(1, corpus.get("archived_source").get("actual_catalogues").intValue());
        assertEquals("42b8b1e56c029054fbc4e0b3964511a980d9b5053c47bff980cd3f5f3924db37", corpus.get("archived_source").get("raw_sha256").textValue());
        for (JsonNode row : corpus.get("cases")) {
            SourceCatalogueCodec.Request input = request(row.get("request"));
            JsonNode expected = row.get("expected");
            if (expected.get("status").textValue().equals("rejected")) {
                IllegalArgumentException error = assertThrows(IllegalArgumentException.class, () -> SourceCatalogueCodec.evaluate(input));
                assertEquals(expected.get("message").textValue(), error.getMessage(), row.get("name").textValue());
            } else {
                SourceCatalogueCodec.Value result = SourceCatalogueCodec.evaluate(input);
                assertEquals(expected.get("value"), JSON.readTree(SourceCatalogueCodec.encode(result)), row.get("name").textValue());
                if (result instanceof SourceCatalogueCodec.CatalogueValue catalogue) {
                    assertFalse(catalogue.catalogue().materialEffectsVerified());
                    assertFalse(catalogue.catalogue().registryContractAccepted());
                }
            }
        }
    }

    @Test void typedRequestsRoundTripAndReturnedListsAreImmutable() throws IOException {
        for (JsonNode row : golden().get("cases")) {
            SourceCatalogueCodec.Request input = request(row.get("request"));
            assertEquals(input, SourceCatalogueCodec.decode(SourceCatalogueCodec.encode(input)));
        }
        List<String> children = EventSourceCatalogue.blocks("event={option={name=a}}", "option");
        assertThrows(UnsupportedOperationException.class, children::clear);
        assertThrows(UnsupportedOperationException.class, EventSourceCatalogue.scalars("option={name=a}", "name")::clear);
    }

    @Test void directChildEnumerationCannotBeReplacedByFirstLineAnchoredNamedBlock() {
        String source = "event={ option={ name=a } option={ name=b } nested={ option={name=ignored} } }";
        assertEquals(List.of("option={ name=a }", "option={ name=b }"), EventSourceCatalogue.blocks(source, "option"));
        assertEquals(List.of("a", "b"), EventSourceCatalogue.scalars("option={name=a name=b nested={name=ignored}}", "name"));
    }

    @Test void scalarHelperRetainsOriginalUnbalancedBehaviorWhileBlockHelperRejects() {
        assertEquals(List.of("a"), EventSourceCatalogue.scalars("option={name=a", "name"));
        assertThrows(EventSourceCatalogue.UnbalancedSourceException.class, () -> EventSourceCatalogue.blocks("option={name=a", "name"));
        assertEquals(List.of("option={name=\"oops }"), EventSourceCatalogue.blocks("event={option={name=\"oops } }", "option"));
    }

    @Test void conditionalNamesUsePythonWordBoundaryAndCodePointSortOrder() {
        String source = "fixture.1 = {\ntype = character_event\noption = {\nname = {\nαtext = ignored\n\u0301text = \"\ud800\udc00\"\ndesc = \"\ue000\"\n}\n trigger = { foo = yes }\n add_gold = 10 # literal\n}\n}";
        EventSourceCatalogue.Catalogue catalogue = EventSourceCatalogue.catalogue(source, 1);
        assertEquals(List.of("\ue000", "\ud800\udc00"), catalogue.options().get(0).sourceNameKeys());
        assertEquals(List.of(new EventSourceCatalogue.DirectEffectStatement("add_gold", "10 # literal")), catalogue.options().get(0).directEffectStatements());
        assertEquals(" trigger = { foo = yes }", catalogue.options().get(0).trigger());
        assertFalse(catalogue.materialEffectsVerified());
    }

    @Test void rawCountFloatsBooleansAndMissingFieldsAreRejected() throws IOException {
        String raw = "{\"schema\":\"xar.ck3.event-source-catalogue-input/v1\",\"operation\":\"catalogue\",\"source\":\"event={option={name=a}}\",\"wanted\":null,\"native_option_count\":1}";
        for (String token : List.of("1.0", "true", "\"1\"", "null")) {
            byte[] malformed = raw.replace("\"native_option_count\":1", "\"native_option_count\":" + token).getBytes(StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> SourceCatalogueCodec.decode(malformed));
        }
        ObjectNode missing = (ObjectNode) JSON.readTree(raw); missing.remove("wanted");
        byte[] missingBytes = JSON.writeValueAsBytes(missing);
        assertThrows(IllegalArgumentException.class, () -> SourceCatalogueCodec.decode(missingBytes));
        ObjectNode wrong = (ObjectNode) JSON.readTree(raw); wrong.put("wanted", "option");
        byte[] wrongBytes = JSON.writeValueAsBytes(wrong);
        assertThrows(IllegalArgumentException.class, () -> SourceCatalogueCodec.decode(wrongBytes));
    }

    @Test void emptySourceIsAValueAndNullOrDuplicateJsonIsNot() {
        String raw = "{\"schema\":\"xar.ck3.event-source-catalogue-input/v1\",\"operation\":\"blocks\",\"source\":\"\",\"wanted\":\"option\",\"native_option_count\":null}";
        assertEquals(new SourceCatalogueCodec.StringValues(List.of()), SourceCatalogueCodec.evaluate(SourceCatalogueCodec.decode(raw.getBytes(StandardCharsets.UTF_8))));
        String duplicate = raw.replace("\"operation\":\"blocks\"", "\"operation\":\"blocks\",\"operation\":\"blocks\"");
        assertTrue(duplicate.length() > raw.length());
        assertThrows(IllegalArgumentException.class, () -> SourceCatalogueCodec.decode(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> SourceCatalogueCodec.decode(raw.replace("\"source\":\"\"", "\"source\":null").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> SourceCatalogueCodec.decode((raw + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> SourceCatalogueCodec.decode(new byte[] {(byte) 0xc3, 0x28}));
    }
}
