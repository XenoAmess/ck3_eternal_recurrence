package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.BooleanNode;
import com.fasterxml.jackson.databind.node.DoubleNode;
import com.fasterxml.jackson.databind.node.IntNode;
import com.fasterxml.jackson.databind.node.LongNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class ClarityCardsTest {
    @TempDir Path directory;

    private ObjectNode specification() {
        ObjectMapper json = new ObjectMapper();
        ObjectNode root = json.createObjectNode().put("schema", "xar.clarity-cards.spec/v2").put("machine_id", "test-machine");
        root.putObject("ffmpeg").put("path", directory.resolve("ffmpeg").toString()).put("bytes", 0)
                .put("sha256", "0".repeat(64));
        ObjectNode card = root.putArray("cards").addObject().put("id", "cost-1").put("cue", "E02-V6-N17")
                .put("anchor_zh", "小额动态金币").put("title", "小额动态金币").put("kicker", "规则演算")
                .put("result", "").put("note", "").put("highlight", 0).putNull("icon");
        card.putArray("lines").add("3 × 10 × 1 = 30"); card.putArray("rows");
        card.putArray("illustrations");
        return root;
    }

    private ObjectNode card(ObjectNode root) { return (ObjectNode) root.path("cards").get(0); }

    private ObjectNode illustration(ObjectNode root, int row, String column) {
        ObjectNode illustration = card(root).withArray("illustrations").addObject()
                .put("row", row).put("column", column);
        illustration.set("source", root.path("ffmpeg").deepCopy());
        return illustration;
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
        assertEquals(List.of(), actual.cards().getFirst().illustrations());
    }

    @Test void preservesIllustrationsAndReceiptThroughJson() throws Exception {
        ObjectNode root = specification();
        illustration(root, 0, "LABEL");
        var line = ClarityCards.parse(write(root, "line-illustration.json")).cards().getFirst();
        assertEquals(ClarityCards.Column.LABEL, line.illustrations().getFirst().column());

        card(root).putArray("lines");
        card(root).withArray("rows").addObject().put("label", "Contemplative").put("value", "Reflection");
        illustration(root, 0, "VALUE");
        var actual = ClarityCards.parse(write(root, "row-illustrations.json"));
        var page = actual.cards().getFirst();
        var expected = new ClarityCards.Illustration(actual.ffmpeg(), 0, ClarityCards.Column.VALUE);
        assertEquals(expected, page.illustrations().get(1));
        assertThrows(UnsupportedOperationException.class, () -> page.illustrations().clear());

        ObjectMapper json = new ObjectMapper();
        assertEquals(expected, json.readValue(json.writeValueAsBytes(expected), ClarityCards.Illustration.class));
        var rendered = new ClarityCards.Rendered(page.id(), page.cue(), page.anchorZh(), actual.ffmpeg(),
                List.of(), true, true, null, page.illustrations());
        var receipt = new ClarityCards.Receipt("xar.clarity-cards.actual/v2", actual.machineId(), "observed",
                actual.ffmpeg(), List.of(rendered), false, false, false);
        var roundTrip = json.readValue(json.writeValueAsBytes(receipt), ClarityCards.Receipt.class);
        assertEquals(receipt, roundTrip);
        assertEquals(page.illustrations(), roundTrip.cards().getFirst().illustrations());
    }

    @Test void rejectsMissingIllustrationsAndIncompleteIllustrationFields() throws Exception {
        ObjectNode missing = specification(); card(missing).remove("illustrations");
        Path missingFile = write(missing, "missing-illustrations.json");
        assertThrows(IllegalArgumentException.class, () -> ClarityCards.parse(missingFile));
        ObjectNode notArray = specification(); card(notArray).putNull("illustrations");
        Path notArrayFile = write(notArray, "null-illustrations.json");
        assertThrows(IllegalArgumentException.class, () -> ClarityCards.parse(notArrayFile));
        for (String field : List.of("source", "row", "column")) {
            ObjectNode root = specification(); illustration(root, 0, "LABEL").remove(field);
            Path file = write(root, "missing-illustration-" + field + ".json");
            assertThrows(IllegalArgumentException.class, () -> ClarityCards.parse(file));
        }
    }

    @Test void rejectsBooleanFloatingPointAndOutOfRangeIllustrationRows() throws Exception {
        List<JsonNode> invalidRows = List.of(BooleanNode.FALSE, new DoubleNode(0.0), new IntNode(-1),
                new IntNode(1), new LongNode(2147483648L));
        for (int i = 0; i < invalidRows.size(); i++) {
            ObjectNode root = specification(); illustration(root, 0, "LABEL").set("row", invalidRows.get(i));
            Path file = write(root, "invalid-illustration-row-" + i + ".json");
            assertThrows(IllegalArgumentException.class, () -> ClarityCards.parse(file));
        }
        ObjectNode rows = specification(); card(rows).putArray("lines");
        card(rows).withArray("rows").addObject().put("label", "one").put("value", "two");
        illustration(rows, 1, "VALUE");
        Path file = write(rows, "row-layout-out-of-range.json");
        assertThrows(IllegalArgumentException.class, () -> ClarityCards.parse(file));
    }

    @Test void rejectsDuplicateIllustrationPositionsAndIllegalColumns() throws Exception {
        ObjectNode duplicate = specification();
        illustration(duplicate, 0, "LABEL"); illustration(duplicate, 0, "LABEL");
        Path duplicateFile = write(duplicate, "duplicate-illustration-position.json");
        assertThrows(IllegalArgumentException.class, () -> ClarityCards.parse(duplicateFile));
        for (String column : List.of("VALUE", "label", "OTHER")) {
            ObjectNode root = specification(); illustration(root, 0, column);
            Path file = write(root, "invalid-column-" + column + ".json");
            assertThrows(IllegalArgumentException.class, () -> ClarityCards.parse(file));
        }
        ObjectNode wrongType = specification(); illustration(wrongType, 0, "LABEL").put("column", false);
        Path wrongTypeFile = write(wrongType, "boolean-column.json");
        assertThrows(IllegalArgumentException.class, () -> ClarityCards.parse(wrongTypeFile));
    }

    @Test void rejectsOldSpecificationSchema() throws Exception {
        ObjectNode root = specification(); root.put("schema", "xar.clarity-cards.spec/v1");
        Path file = write(root, "old-schema.json");
        assertThrows(IllegalArgumentException.class, () -> ClarityCards.parse(file));
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
