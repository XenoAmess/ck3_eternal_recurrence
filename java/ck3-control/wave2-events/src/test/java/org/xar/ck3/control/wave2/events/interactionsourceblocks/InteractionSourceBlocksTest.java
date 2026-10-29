package org.xar.ck3.control.wave2.events.interactionsourceblocks;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.interactionsourceblocks.InteractionSourceBlocks.*;

class InteractionSourceBlocksTest {
    private static final String RESOURCE = "/interactionsourceblocks/legacy-producer-golden-v1.json";

    @Test void actualOriginalBlockFunctionMatchesAllSourceCases() throws IOException {
        JsonNode golden = golden(); assertEquals(32, golden.get("cases").size());
        for (JsonNode row : golden.get("cases")) {
            String text = row.get("text").textValue(); String key = row.get("key").textValue(); String status = row.get("expected_status").textValue();
            if (status.equals("unterminated")) {
                var error = assertThrows(UnterminatedBlockException.class, () -> extract(text, key), row.get("name").textValue());
                assertEquals(row.get("expected_error").textValue(), error.getMessage());
            } else {
                Block result = extract(text, key);
                if (status.equals("found")) { assertEquals(row.get("expected_text").textValue(), assertInstanceOf(Found.class, result).text(), row.get("name").textValue()); }
                else { assertInstanceOf(Absent.class, result, row.get("name").textValue()); }
            }
        }
    }

    @Test void AuthoredEffectsKeepActualScopeBodiesAndMechanicalCategoryOrder() throws IOException {
        for (JsonNode row : golden().get("cases")) {
            String text = row.get("text").textValue(); String key = row.get("key").textValue();
            if (row.get("expected_status").textValue().equals("unterminated")) { assertThrows(UnterminatedBlockException.class, () -> catalogue(text, key)); continue; }
            var result = catalogue(text, key); JsonNode expected = row.get("expected_effects");
            if (expected.isNull()) { assertTrue(result.isEmpty()); continue; }
            AuthoredEffects actual = result.orElseThrow();
            assertEquals(expected.get("definition").textValue(), actual.definition());
            List<String> categories = new ArrayList<>(); expected.get("category").forEach(value -> categories.add(value.textValue()));
            assertEquals(categories, actual.category());
            assertEquals(nullable(expected.get("on_accept")), actual.onAccept()); assertEquals(nullable(expected.get("on_decline")), actual.onDecline());
            assertFalse(actual.materialEffectsVerified()); assertFalse(actual.semanticOptimal()); assertFalse(actual.nativeAiEquivalent());
        }
    }

    @Test void utf8SigMatchesOriginalProducerDecodeAndRejectsMalformedOrOversize() {
        byte[] bom = utf8("\ufeffx = {} ");
        assertEquals("x = {}", catalogueUtf8(bom, "x").orElseThrow().definition());
        assertInstanceOf(Absent.class, extract("\ufeffx = {}", "x"));
        assertTrue(catalogueUtf8(utf8("\ufeff\ufeffx = {}"), "x").isEmpty());
        assertThrows(ContractViolationException.class, () -> catalogueUtf8(new byte[] {(byte) 0xc0, (byte) 0xaf}, "x"));
        assertThrows(ContractViolationException.class, () -> catalogueUtf8(new byte[MAX_SOURCE_BYTES + 1], "x"));
    }

    @Test void strictRequestBoundaryRejectsWrongTypesMissingUnknownDuplicateAndInvalidUtf8() {
        String valid = "{\"schema\":\"xar.interaction-source-block-request/v1\",\"text\":\"x = {}\",\"key\":\"x\"}";
        for (String wrong : List.of("null", "true", "1", "1.0", "[]", "{}")) {
            String raw = valid.replace("\"text\":\"x = {}\"", "\"text\":" + wrong);
            assertThrows(ContractViolationException.class, () -> InteractionSourceBlocksCodec.parseRequest(utf8(raw)), wrong);
        }
        for (String wrong : List.of(valid.replace(",\"key\":\"x\"", ""), valid.replace("\"key\":\"x\"", "\"key\":null"),
                valid.replace("\"key\":\"x\"", "\"key\":\"x.*\""), valid.replaceFirst("\\{", "{\"reviewed\":true,"),
                valid.replaceFirst("\\{", "{\"schema\":\"duplicate\","), valid + " {}")) {
            assertThrows(ContractViolationException.class, () -> InteractionSourceBlocksCodec.parseRequest(utf8(wrong)));
        }
        assertThrows(ContractViolationException.class, () -> InteractionSourceBlocksCodec.parseRequest(new byte[] {(byte) 0xff}));
        assertThrows(ContractViolationException.class, () -> InteractionSourceBlocksCodec.parseRequest(new byte[InteractionSourceBlocksCodec.MAX_JSON_BYTES + 1]));
    }

    @Test void requestRoundTripKeepsEmptyTextUnicodeAndSourceBodyNullSemantics() throws IOException {
        for (JsonNode row : golden().get("cases")) {
            var request = new InteractionSourceBlocksCodec.Request(row.get("text").textValue(), row.get("key").textValue());
            assertEquals(request, InteractionSourceBlocksCodec.parseRequest(InteractionSourceBlocksCodec.encodeRequest(request)));
        }
        var authored = catalogue("x = {\n category = first\n on_accept = {}\n}", "x").orElseThrow();
        assertNotNull(authored.onAccept()); assertNull(authored.onDecline());
        assertThrows(UnsupportedOperationException.class, () -> authored.category().clear());
        JsonNode absent = StrictJson.parse(InteractionSourceBlocksCodec.encodeBlock(new Absent()));
        assertTrue(absent.get("text").isNull()); assertFalse(absent.get("material_effects_verified").booleanValue());
    }

    @Test void blankLineInputHasBoundedWorkInsteadOfRepeatedWhitespaceSuffixScans() {
        String text = " \n".repeat(MAX_SOURCE_BYTES / 2);
        assertTimeout(Duration.ofSeconds(5), () -> assertInstanceOf(Absent.class, extract(text, "x")));
    }

    @Test void oversizedCategoriesInvalidKeysAndUnpairedUnicodeCannotProduceCatalogue() {
        String source = "x = {\n" + " category = first\n".repeat(65) + "}";
        assertThrows(ContractViolationException.class, () -> catalogue(source, "x"));
        assertThrows(ContractViolationException.class, () -> extract("x = {}", "x|y"));
        String unpaired = new String(new char[] {'x', ' ', '=', ' ', '{', (char) 0xd800, '}'});
        assertThrows(ContractViolationException.class, () -> extract(unpaired, "x"));
    }

    private static String nullable(JsonNode node) { return node.isNull() ? null : node.textValue(); }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static JsonNode golden() throws IOException {
        try (var stream = InteractionSourceBlocksTest.class.getResourceAsStream(RESOURCE)) { assertNotNull(stream, "committed original producer golden required"); return StrictJson.parse(stream.readAllBytes()); }
    }
}
