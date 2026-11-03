package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * Independent DATA ownership oracle for the structural projection helper.
 * Fixtures enter through OpportunityJson.toNode, as the production full route does.
 * Reflection invokes only the existing private DATA helpers; it issues no authority,
 * creates no selector instance and uses no MaterialSink, HTTP or Game operation.
 * The small source-shaped rows qualify only this structural projection helper;
 * they do not claim complete ROOT normalization or a valid PlanningRequest.
 */
final class SelectorRootPrivateCopyOracleTest {
    private static final int LEASE = 16_384;
    private static final List<String> TECHNICAL = List.of(
            "decoder_source", "definition_source", "original_receipt", "supporting_evidence", "source");

    @Test void completeFactsAndInputIsolationSurvivePublication() throws Exception {
        OpportunityJson.Obj typed = row(7, 101, 102, "kept");
        byte[] typedBefore = OpportunityJson.encode(typed);
        ObjectNode original = (ObjectNode) OpportunityJson.toNode(typed);
        byte[] originalBefore = wire(original);
        ArrayNode dictionary = JsonNodeFactory.instance.arrayNode();
        assertTrue(qualifies(original));

        ObjectNode projected = project(original, dictionary);
        assertNotSame(original, projected);
        assertNotSame(original.get("result"), projected.get("result"));
        assertEquals(1, dictionary.size());
        ObjectNode facts = (ObjectNode) dictionary.get(0);
        JsonNode reference = projected.path("result").path("campaign_root_context");
        assertEquals(List.of("root_ref", "snapshot_revision", "player_heir_candidate_v1_snapshot_revision"), keys(reference));
        assertEquals(0, reference.path("root_ref").intValue());
        assertEquals(101, reference.path("snapshot_revision").intValue());
        assertEquals(102, reference.path("player_heir_candidate_v1_snapshot_revision").intValue());
        assertFalse(facts.has("snapshot_revision"));
        assertFalse(facts.path("player_heir_candidate_v1").has("snapshot_revision"));
        assertEquals(List.of("status", "player_heir_candidate_v1", "unknown"), keys(facts));
        assertEquals(List.of("status", "extra"), keys(facts.path("player_heir_candidate_v1")));
        assertEquals(original.path("result").path("campaign_root_context"), reconstruct(projected, dictionary));
        assertEquals("18446744073709551617", facts.path("unknown").path("wide").asText());
        assertEquals("-0.0", facts.path("player_heir_candidate_v1").path("extra").get(1).asText());
        assertEquals("1.2300e+4", facts.path("player_heir_candidate_v1").path("extra").get(2).asText());
        assertFalse(facts.path("unknown").has("missing"));
        assertTrue(facts.path("player_heir_candidate_v1").path("extra").get(3).isNull());
        ObjectNode expectedSource = ((ObjectNode) original.get("read_history_source")).deepCopy();
        expectedSource.remove(TECHNICAL);
        assertEquals(expectedSource, projected.get("read_history_source"));
        assertEquals(original.path("result").path("other_result"), projected.path("result").path("other_result"));

        ObjectNode envelope = JsonNodeFactory.instance.objectNode();
        envelope.putArray("history").add(projected);
        envelope.set("root_facts", dictionary);
        byte[] emitted = wire(envelope);
        assertArrayEquals(emitted, wire(FullJsonTree.parse(emitted, LEASE)));
        // The returned tree may be mutated by a later local consumer; originals stay isolated.
        ((ObjectNode) facts.path("unknown").path("nested").get(0)).put("word", "changed");
        ((ArrayNode) projected.path("result").path("other_result").path("array")).add(true);
        ((ObjectNode) projected.path("read_history_source").path("keep")).put("text", "changed");
        assertArrayEquals(originalBefore, wire(original));
        assertArrayEquals(typedBefore, OpportunityJson.encode(typed));
    }

    @Test void equalFactsShareReferenceButStampsAndUnknownDifferencesRemain() throws Exception {
        ObjectNode first = (ObjectNode) OpportunityJson.toNode(row(1, 201, 202, "same"));
        ObjectNode second = (ObjectNode) OpportunityJson.toNode(row(2, 301, 302, "same"));
        ObjectNode different = (ObjectNode) OpportunityJson.toNode(row(3, 401, 402, "different"));
        byte[] oneBefore = wire(first), twoBefore = wire(second), threeBefore = wire(different);
        ArrayNode dictionary = JsonNodeFactory.instance.arrayNode();
        ObjectNode one = project(first, dictionary), two = project(second, dictionary);
        assertEquals(1, dictionary.size());
        assertEquals(0, two.path("result").path("campaign_root_context").path("root_ref").intValue());
        assertEquals(201, one.path("result").path("campaign_root_context").path("snapshot_revision").intValue());
        assertEquals(301, two.path("result").path("campaign_root_context").path("snapshot_revision").intValue());
        assertEquals(302, two.path("result").path("campaign_root_context").path("player_heir_candidate_v1_snapshot_revision").intValue());
        assertEquals(first.path("read_history_source").path("source_frame"), one.path("read_history_source").path("source_frame"));
        assertEquals(second.path("read_history_source").path("source_frame"), two.path("read_history_source").path("source_frame"));
        assertEquals(first.path("result").path("campaign_root_context"), reconstruct(one, dictionary));
        assertEquals(second.path("result").path("campaign_root_context"), reconstruct(two, dictionary));
        ObjectNode three = project(different, dictionary);
        assertEquals(2, dictionary.size());
        assertEquals(1, three.path("result").path("campaign_root_context").path("root_ref").intValue());
        assertEquals(different.path("result").path("campaign_root_context"), reconstruct(three, dictionary));
        assertArrayEquals(oneBefore, wire(first));
        assertArrayEquals(twoBefore, wire(second));
        assertArrayEquals(threeBefore, wire(different));
    }

    @Test void unfamiliarRowsAreRejectedByTheOriginalStructuralGuard() throws Exception {
        ObjectNode original = (ObjectNode) OpportunityJson.toNode(row(4, 501, 502, "same"));
        List<ObjectNode> unfamiliar = new ArrayList<>();
        ObjectNode extraField = original.deepCopy(); extraField.put("future_row_field", true); unfamiliar.add(extraField);
        ObjectNode failed = original.deepCopy(); failed.put("ok", false); unfamiliar.add(failed);
        ObjectNode wrongCommand = original.deepCopy(); wrongCommand.put("command", "other"); unfamiliar.add(wrongCommand);
        ObjectNode wrongSource = original.deepCopy(); ((ObjectNode) wrongSource.get("read_history_source")).put("kind", "OTHER"); unfamiliar.add(wrongSource);
        ObjectNode noStamp = original.deepCopy(); ((ObjectNode) noStamp.path("result").path("campaign_root_context")).remove("snapshot_revision"); unfamiliar.add(noStamp);
        ObjectNode decimalStamp = original.deepCopy(); ((ObjectNode) decimalStamp.path("result").path("campaign_root_context")).set("snapshot_revision", FullJsonTree.parse("1.0".getBytes(StandardCharsets.UTF_8), LEASE)); unfamiliar.add(decimalStamp);
        ObjectNode noHeir = original.deepCopy(); ((ObjectNode) noHeir.path("result").path("campaign_root_context")).remove("player_heir_candidate_v1"); unfamiliar.add(noHeir);
        for (ObjectNode row : unfamiliar) {
            byte[] before = wire(row);
            assertFalse(qualifies(row));
            assertArrayEquals(before, wire(row));
        }
    }

    private static OpportunityJson.Obj row(int index, int rootStamp, int heirStamp, String word) {
        String text = """
                {"index":%d,"command":"query-campaign-root-context-v1","ok":true,
                 "read_history_source":{"schema":"xar.driver-read-history-source/v1","kind":"CAMPAIGN_ROOT_CONTEXT",
                   "payload_field":"campaign_root_context","source_frame":{"frame":{"snapshot_id":"frame-%d","revision":700},"game":{"pid":77},"machine_id":"source-only-fixture"},
                   "query_sequence":9,"decoder_source":{"p":"decoder"},"definition_source":{"p":"definition"},
                   "original_receipt":{"p":"receipt"},"supporting_evidence":[],"source":{"p":"source"},"keep":{"text":"retained"}},
                 "result":{"status":"available","campaign_root_context":{"status":"available","snapshot_revision":%d,
                   "player_heir_candidate_v1":{"status":"observed","snapshot_revision":%d,"extra":[1,-0.0,1.2300e+4,null]},
                   "unknown":{"wide":18446744073709551617,"nested":[{"word":"%s"}]}},"other_result":{"array":[false,null]}}}
                """.formatted(index, index, rootStamp, heirStamp, word);
        return OpportunityJson.object(OpportunityJson.parseComplete(text.getBytes(StandardCharsets.UTF_8), LEASE), "row");
    }

    private static JsonNode reconstruct(ObjectNode projected, ArrayNode dictionary) {
        JsonNode ref = projected.path("result").path("campaign_root_context");
        ObjectNode complete = dictionary.get(ref.path("root_ref").intValue()).deepCopy();
        complete.set("snapshot_revision", ref.get("snapshot_revision"));
        ((ObjectNode) complete.get("player_heir_candidate_v1")).set("snapshot_revision", ref.get("player_heir_candidate_v1_snapshot_revision"));
        return complete;
    }

    private static List<String> keys(JsonNode node) {
        List<String> fields = new ArrayList<>(); node.fieldNames().forEachRemaining(fields::add); return fields;
    }
    private static byte[] wire(JsonNode node) { return FullJsonTree.encode(node, LEASE); }
    private static boolean qualifies(JsonNode row) throws Exception {
        return (Boolean) invoke("isQualifyingRootContextRead", new Class<?>[] { JsonNode.class }, row);
    }
    private static ObjectNode project(ObjectNode row, ArrayNode dictionary) throws Exception {
        return (ObjectNode) invoke("projectRootContextRead", new Class<?>[] { ObjectNode.class, ArrayNode.class }, row, dictionary);
    }
    private static Object invoke(String name, Class<?>[] types, Object... args) throws Exception {
        Method method = RootOnlineDecisionSelector.class.getDeclaredMethod(name, types);
        method.setAccessible(true);
        try { return method.invoke(null, args); }
        catch (InvocationTargetException failure) {
            Throwable cause = failure.getCause();
            if (cause instanceof Exception exception) throw exception;
            if (cause instanceof Error error) throw error;
            throw new AssertionError(cause);
        }
    }
}
