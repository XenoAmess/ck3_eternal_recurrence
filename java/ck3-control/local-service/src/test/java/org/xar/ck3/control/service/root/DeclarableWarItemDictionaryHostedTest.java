package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.FullJsonTree;

/** Frozen request DATA only; no sockets, Root, writer, Native or action execution. */
final class DeclarableWarItemDictionaryHostedTest {
    @Test void actualOldPayloadAndAdversarialItemsRoundTripExactly() throws Exception {
        byte[] wire = Files.readAllBytes(Path.of(System.getProperty("xar.dictionary.request")));
        assertEquals(1724435, wire.length);
        assertEquals("b29ed6121b11a3d11eec209ef1c3c51b54570acc4ac6f61bf9c6b84ac59e81df",
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(wire)));
        JsonNode request = FullJsonTree.parse(wire, FullJsonTree.MAXIMUM_BYTES);
        byte[] user = request.path("messages").get(1).path("content").textValue().getBytes(StandardCharsets.UTF_8);
        assertEquals(1562013, user.length);
        ObjectNode original = (ObjectNode) FullJsonTree.parse(user, FullJsonTree.MAXIMUM_BYTES);
        assertArrayEquals(user, encode(original));
        ObjectNode projected = RootOnlineDecisionSelector.projectDeclarableWarItems(original);
        assertNotNull(projected);
        assertEquals(73, projected.path("history").size());
        assertEquals(780, projected.path("declarable_war_facts").size());
        int[] positions = {3, 12, 25, 40, 55};
        int[] counts = {774, 775, 771, 771, 770};
        for (int i = 0; i < positions.length; i++) {
            assertEquals(counts[i], projected.path("history").get(positions[i]).path("result")
                    .path("declarable_war_fact_refs").size());
        }
        int javaRows = 0;
        for (JsonNode row : projected.path("history")) if (row.has("java_action_history_source")) javaRows++;
        assertEquals(20, javaRows);
        assertArrayEquals(user, encode(expand(projected)));
        assertArrayEquals(user, encode(original), "pure consumer changed original DATA");

        ObjectNode a = parse("{\"unknown\":{\"z\":1,\"a\":2},\"n\":1.0,\"big\":9007199254740993}");
        ObjectNode b = parse("{\"n\":1.0,\"unknown\":{\"z\":1,\"a\":2},\"big\":9007199254740993}");
        ObjectNode c = parse("{\"unknown\":{\"z\":1,\"a\":2},\"n\":1.00,\"big\":9007199254740993}");
        ObjectNode small = JsonNodeFactory.instance.objectNode();
        small.put("history_projection_schema", "xar.model-root-history-dictionary/v1");
        small.putObject("unknown_root").put("retained", "all fields");
        ArrayNode history = small.putArray("history");
        ObjectNode first = original.path("history").get(3).deepCopy();
        ObjectNode second = original.path("history").get(12).deepCopy();
        ArrayNode firstItems = JsonNodeFactory.instance.arrayNode().add(a).add(b).add(a);
        ArrayNode secondItems = JsonNodeFactory.instance.arrayNode().add(c).add(b).add(a);
        ((ObjectNode) first.get("result")).set("declarable_wars", firstItems);
        ((ObjectNode) second.get("result")).set("declarable_wars", secondItems);
        history.add(first).add(second);
        byte[] smallBefore = encode(small);
        ObjectNode smallProjected = RootOnlineDecisionSelector.projectDeclarableWarItems(small);
        assertNotNull(smallProjected);
        assertEquals(3, smallProjected.path("declarable_war_facts").size(), "order/token variants merged");
        assertEquals("[0,1,0]", smallProjected.path("history").get(0).path("result").path("declarable_war_fact_refs").toString());
        assertEquals("[2,1,0]", smallProjected.path("history").get(1).path("result").path("declarable_war_fact_refs").toString());
        assertArrayEquals(smallBefore, encode(expand(smallProjected)));
        assertArrayEquals(smallBefore, encode(small));

        ObjectNode bad = small.deepCopy(); bad.putNull("declarable_war_facts");
        assertNull(RootOnlineDecisionSelector.projectDeclarableWarItems(bad));
        bad = small.deepCopy(); bad.put("history_declarable_wars_projection_schema", "occupied");
        assertNull(RootOnlineDecisionSelector.projectDeclarableWarItems(bad));
        bad = small.deepCopy(); ((ObjectNode) bad.path("history").get(0).get("result")).putNull("declarable_war_fact_refs");
        assertNull(RootOnlineDecisionSelector.projectDeclarableWarItems(bad));
        bad = small.deepCopy(); ((ObjectNode) bad.path("history").get(0).get("result")).put("declarable_wars_history_ref", 0);
        assertNull(RootOnlineDecisionSelector.projectDeclarableWarItems(bad));
        bad = small.deepCopy(); bad.put("history_projection_schema", "unknown-protocol");
        assertNull(RootOnlineDecisionSelector.projectDeclarableWarItems(bad));
        bad = small.deepCopy(); bad.set("history", JsonNodeFactory.instance.objectNode());
        assertNull(RootOnlineDecisionSelector.projectDeclarableWarItems(bad));
        bad = small.deepCopy(); ((ArrayNode) bad.path("history").get(0).path("result").get("declarable_wars")).set(0, JsonNodeFactory.instance.textNode("not-object"));
        assertNull(RootOnlineDecisionSelector.projectDeclarableWarItems(bad));
        bad = small.deepCopy(); ((ObjectNode) bad.path("history").get(1).get("result")).put("status", "unavailable");
        assertNull(RootOnlineDecisionSelector.projectDeclarableWarItems(bad));
        bad = small.deepCopy(); ((ArrayNode) bad.get("history")).remove(1);
        assertNull(RootOnlineDecisionSelector.projectDeclarableWarItems(bad));
        bad = small.deepCopy();
        ((ObjectNode) bad.path("history").get(0).get("result")).set("declarable_wars", JsonNodeFactory.instance.arrayNode().add(a));
        ((ObjectNode) bad.path("history").get(1).get("result")).set("declarable_wars", JsonNodeFactory.instance.arrayNode().add(c));
        assertNull(RootOnlineDecisionSelector.projectDeclarableWarItems(bad));
        System.out.println("DATA {\"schema\":\"xar.declarable-war-item-dictionary-test/v1\",\"original_wire_bytes\":1724435,"
                + "\"restored_user_bytes\":1562013,\"history_rows\":73,\"facts\":780,\"ordered_token_variants\":3,"
                + "\"consumer_denials\":10,\"original_unchanged\":true,\"private_model_or_root_claim\":false}");
    }

    private static ObjectNode parse(String value) {
        return (ObjectNode) FullJsonTree.parse(value.getBytes(StandardCharsets.UTF_8), FullJsonTree.MAXIMUM_BYTES);
    }
    private static byte[] encode(JsonNode value) { return FullJsonTree.encode(value, FullJsonTree.MAXIMUM_BYTES); }
    /** Independent format expansion; no interning or production-helper logic duplicated. */
    private static ObjectNode expand(ObjectNode projected) {
        ObjectNode expanded = JsonNodeFactory.instance.objectNode();
        JsonNode facts = projected.get("declarable_war_facts");
        for (var field : projected.properties()) {
            if (field.getKey().equals("declarable_war_facts") || field.getKey().equals("history_declarable_wars_projection_schema")) continue;
            if (!field.getKey().equals("history")) { expanded.set(field.getKey(), field.getValue()); continue; }
            ArrayNode rows = expanded.putArray("history");
            for (JsonNode actualRow : field.getValue()) {
                if (!actualRow.path("result").has("declarable_war_fact_refs")) { rows.add(actualRow); continue; }
                ObjectNode row = JsonNodeFactory.instance.objectNode();
                for (var rowField : ((ObjectNode) actualRow).properties()) {
                    if (!rowField.getKey().equals("result")) { row.set(rowField.getKey(), rowField.getValue()); continue; }
                    ObjectNode result = row.putObject("result");
                    for (var resultField : ((ObjectNode) rowField.getValue()).properties()) {
                        if (!resultField.getKey().equals("declarable_war_fact_refs")) { result.set(resultField.getKey(), resultField.getValue()); continue; }
                        ArrayNode wars = result.putArray("declarable_wars");
                        for (JsonNode reference : resultField.getValue()) {
                            assertTrue(reference.isIntegralNumber());
                            assertTrue(reference.canConvertToInt());
                            int index = reference.intValue();
                            assertTrue(index >= 0 && index < facts.size());
                            wars.add(facts.get(index));
                        }
                    }
                }
                rows.add(row);
            }
        }
        return expanded;
    }
}
