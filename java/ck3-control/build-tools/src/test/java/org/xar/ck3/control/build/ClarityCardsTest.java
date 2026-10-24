package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class ClarityCardsTest {
    @TempDir Path directory;

    private ObjectNode specification() {
        ObjectMapper json = new ObjectMapper();
        ObjectNode root = json.createObjectNode().put("schema", "xar.clarity-cards.spec/v1").put("machine_id", "test-machine");
        root.putObject("ffmpeg").put("path", directory.resolve("ffmpeg").toString()).put("bytes", 0)
                .put("sha256", "0".repeat(64));
        ObjectNode card = root.putArray("cards").addObject().put("id", "cost-1").put("cue", "E02-V6-N17")
                .put("anchor_zh", "小额动态金币").put("title", "小额动态金币").put("kicker", "规则演算")
                .put("result", "").put("note", "").put("highlight", 0).putNull("icon");
        card.putArray("lines").add("3 × 10 × 1 = 30"); card.putArray("rows");
        return root;
    }

    private Path write(ObjectNode value, String name) throws Exception {
        Path file = directory.resolve(name); Files.writeString(file, value.toString()); return file;
    }

    @Test void preservesExactFormulaAndIdentityThroughJson() throws Exception {
        var actual = ClarityCards.parse(write(specification(), "valid.json"));
        assertEquals("test-machine", actual.machineId());
        assertEquals("3 × 10 × 1 = 30", actual.cards().getFirst().lines().getFirst());
        assertEquals("E02-V6-N17", actual.cards().getFirst().cue());
        assertEquals(0, actual.ffmpeg().bytes());
    }

    @Test void rejectsMissingFieldsAndBooleanOrFloatingPointIntegers() throws Exception {
        ObjectNode missing = specification(); ((ObjectNode) missing.path("cards").get(0)).remove("anchor_zh");
        Path missingFile = write(missing, "missing.json");
        assertThrows(IllegalArgumentException.class, () -> ClarityCards.parse(missingFile));
        ObjectNode floating = specification(); ((ObjectNode) floating.path("ffmpeg")).put("bytes", 0.0);
        Path floatingFile = write(floating, "floating.json");
        assertThrows(IllegalArgumentException.class, () -> ClarityCards.parse(floatingFile));
        ObjectNode bool = specification(); ((ObjectNode) bool.path("cards").get(0)).put("highlight", false);
        Path boolFile = write(bool, "bool.json");
        assertThrows(IllegalArgumentException.class, () -> ClarityCards.parse(boolFile));
    }

    @Test void rejectsDuplicateFieldsAndDuplicatePageIds() throws Exception {
        ObjectNode root = specification(); root.withArray("cards").add(root.path("cards").get(0).deepCopy());
        Path repeated = write(root, "repeated.json");
        assertThrows(IllegalArgumentException.class, () -> ClarityCards.parse(repeated));
        Path duplicate = directory.resolve("duplicate-field.json");
        Files.writeString(duplicate, "{\"schema\":\"a\",\"schema\":\"b\"}");
        assertThrows(java.io.IOException.class, () -> ClarityCards.parse(duplicate));
    }
}
