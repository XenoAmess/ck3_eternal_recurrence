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

/** Frozen request DATA only; no HTTP send, Root, writer, Native or action execution. */
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


    /** The real qualified producer's private pure encoder is invoked; no HTTP selection or Root is constructed. */
    @Test void actualE79bPayloadAndFullWireRoundTripUsingOriginalEncoder() throws Exception {
        Path input = Path.of(System.getProperty("xar.dictionary.e79b.request"));
        byte[] wire = Files.readAllBytes(input);
        assertEquals(2784926, wire.length);
        String inputSha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(wire));
        assertEquals("d5ba35a419234e9393ad94436c1ec8559bed7d2c941cc06cf277e80c968ea994", inputSha);
        try (var sourceClass = RootOnlineDecisionSelector.class.getResourceAsStream("RootOnlineDecisionSelector.class")) {
            assertNotNull(sourceClass);
            assertEquals("45e99484b2a6f4537234b3f2115199c5365d3600e4d9b061adb14b155dc569bf",
                    HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(sourceClass.readAllBytes())));
        }
        JsonNode request = FullJsonTree.parse(wire, FullJsonTree.MAXIMUM_BYTES);
        assertEquals(2, request.path("messages").size());
        String actualPolicy = request.path("messages").get(0).path("content").textValue();
        byte[] user = request.path("messages").get(1).path("content").textValue().getBytes(StandardCharsets.UTF_8);
        assertEquals(2523304, user.length);
        ObjectNode original = (ObjectNode) FullJsonTree.parse(user, FullJsonTree.MAXIMUM_BYTES);
        assertArrayEquals(user, encode(original));
        assertEquals("life-advance", original.path("proposal").path("operation").textValue());
        assertEquals("action-e79b40e91d64dc87a90bec6862662f87f9dc7c6ba4024b60837f36a58dde05f0", original.path("proposal_id").textValue());
        var command = org.xar.ck3.control.application.action.ActionCodec.decodeCommand(encode(original.path("proposal")));
        String body = org.xar.ck3.control.application.action.ActionCodec.bodySha256(command);
        assertEquals(original.path("body_sha256").textValue(), body);
        assertEquals(original.path("proposal_id").textValue(), command.actionId());

        ObjectNode projected = RootOnlineDecisionSelector.projectDeclarableWarItems(original);
        assertNotNull(projected);
        assertEquals("xar.model-history-declarable-war-items/v1", projected.path("history_declarable_wars_projection_schema").textValue());
        assertEquals(792, projected.path("declarable_war_facts").size());
        assertEquals(original.path("history").size(), projected.path("history").size());
        int arrays = 0, items = 0;
        for (int row = 0; row < original.path("history").size(); row++) {
            JsonNode wars = original.path("history").get(row).path("result").get("declarable_wars");
            if (wars == null) continue;
            arrays++; items += wars.size();
            JsonNode refs = projected.path("history").get(row).path("result").get("declarable_war_fact_refs");
            assertNotNull(refs); assertEquals(wars.size(), refs.size());
            for (int index = 0; index < wars.size(); index++) {
                int dictionaryIndex = refs.get(index).intValue();
                assertTrue(refs.get(index).isIntegralNumber() && refs.get(index).canConvertToInt());
                assertTrue(dictionaryIndex >= 0 && dictionaryIndex < projected.path("declarable_war_facts").size());
                assertArrayEquals(encode(wars.get(index)), encode(projected.path("declarable_war_facts").get(dictionaryIndex)));
            }
        }
        assertEquals(8, arrays); assertEquals(6175, items);
        ObjectNode expanded = expand(projected); // Existing independently written format expander; not an interning implementation.
        assertArrayEquals(user, encode(expanded), "all original member positions, fields, values, statuses, frames and occurrences must round-trip");
        assertArrayEquals(user, encode(original), "projection mutated the actual input");
        for (String field : java.util.List.of("proposal", "proposal_id", "body_sha256", "snapshot", "root_facts", "action_facts", "planning_deadline"))
            assertArrayEquals(encode(original.get(field)), encode(projected.get(field)), field);

        var policyField = RootOnlineDecisionSelector.class.getDeclaredField("POLICY"); policyField.setAccessible(true);
        var hintField = RootOnlineDecisionSelector.class.getDeclaredField("WAR_ITEM_POLICY"); hintField.setAccessible(true);
        String policy = (String) policyField.get(null), hint = (String) hintField.get(null);
        assertEquals(actualPolicy, policy);
        var config = new RootOrdinaryRuntimeConfiguration.DecisionProvider(java.net.URI.create("http://127.0.0.1:1/v1"),
                request.path("model").textValue(), java.time.Duration.ofSeconds(1), 1, java.time.Duration.ZERO);
        var selector = new RootOnlineDecisionSelector(config, java.time.Clock.fixed(java.time.Instant.EPOCH, java.time.ZoneOffset.UTC),
                raw -> { throw new AssertionError("pure encoding must not preserve material or enter decision selection"); });
        var httpField = RootOnlineDecisionSelector.class.getDeclaredField("http"); httpField.setAccessible(true);
        var http = (java.net.http.HttpClient) httpField.get(selector);
        try {
            var encoder = RootOnlineDecisionSelector.class.getDeclaredMethod("encodeModelInput", ObjectNode.class, String.class);
            encoder.setAccessible(true);
            byte[] beforeWire = (byte[]) encoder.invoke(selector, original, policy);
            byte[] afterWire = (byte[]) encoder.invoke(selector, projected, policy + hint);
            byte[] restoredWire = (byte[]) encoder.invoke(selector, expanded, policy);
            assertArrayEquals(wire, beforeWire, "real pure encoder must recreate the entire original HTTP body byte-for-byte");
            assertArrayEquals(wire, restoredWire, "expanded data through that real encoder must recreate the entire original body");
            assertTrue(afterWire.length < beforeWire.length, "actual producer size gate includes the added policy");
            JsonNode after = FullJsonTree.parse(afterWire, FullJsonTree.MAXIMUM_BYTES);
            for (String field : java.util.List.of("model", "temperature", "stream", "max_tokens", "stream_options", "chat_template_kwargs", "response_format"))
                assertArrayEquals(encode(request.get(field)), encode(after.get(field)), field);
            assertEquals(policy + hint, after.path("messages").get(0).path("content").textValue());
            ObjectNode afterUser = (ObjectNode) FullJsonTree.parse(after.path("messages").get(1).path("content").textValue().getBytes(StandardCharsets.UTF_8), FullJsonTree.MAXIMUM_BYTES);
            assertArrayEquals(encode(projected), encode(afterUser));
            assertArrayEquals(user, encode(expand(afterUser)));
            assertEquals(body, org.xar.ck3.control.application.action.ActionCodec.bodySha256(
                    org.xar.ck3.control.application.action.ActionCodec.decodeCommand(encode(afterUser.path("proposal")))));
            Path output = Path.of(System.getProperty("xar.dictionary.e79b.output")); Files.createDirectories(output);
            Files.write(output.resolve("ENCODED-BEFORE-WIRE.json"), beforeWire);
            Files.write(output.resolve("ENCODED-AFTER-WIRE.json"), afterWire);
            Files.write(output.resolve("EXPANDED-USER.json"), encode(expanded));
            ObjectNode summary = JsonNodeFactory.instance.objectNode();
            summary.put("schema", "xar.e79b-real-dictionary-full-wire-data/v1");
            summary.put("input_sha256", inputSha); summary.put("source_candidate_sha256", "4fc4c3698e7806b420142c2a3ee048aa5aa9bdc4df7e00ffb0b11025431ad5f7");
            summary.put("before_wire_bytes", beforeWire.length); summary.put("after_wire_bytes", afterWire.length);
            summary.put("saved_wire_bytes", beforeWire.length - afterWire.length);
            summary.put("before_wire_sha256", HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(beforeWire)));
            summary.put("after_wire_sha256", HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(afterWire)));
            summary.put("proposal_id", command.actionId()); summary.put("body_sha256", body);
            summary.set("source", original.path("proposal").get("source")); summary.set("before", original.path("proposal").get("before"));
            summary.put("arrays", arrays); summary.put("ordered_occurrences", items); summary.put("dictionary_facts", 792);
            summary.put("full_user_and_wire_roundtrip", true); summary.put("policy_inclusive_size_gate_passed", true);
            summary.put("select_or_requestPayload_invoked", false); summary.put("HTTP_sent", false); summary.put("private_Root_or_Role", false);
            Files.write(output.resolve("RESULT.json"), encode(summary));
            System.out.println("E79B_REAL_ENCODER_DATA_PASS " + new String(encode(summary), StandardCharsets.UTF_8));
        } finally { http.close(); }
        assertArrayEquals(wire, Files.readAllBytes(input), "frozen original changed");
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
