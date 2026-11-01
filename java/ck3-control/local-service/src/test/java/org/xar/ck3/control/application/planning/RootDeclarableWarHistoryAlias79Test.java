package org.xar.ck3.control.application.planning;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Method;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Duration;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.RootOnlineDecisionSelector;
import org.xar.ck3.control.service.root.RootOrdinaryRuntimeConfiguration;
import static org.junit.jupiter.api.Assertions.*;

/** Literal contract tests; no model/server, Game, archive, or production candidate as an oracle. */
public final class RootDeclarableWarHistoryAlias79Test {
    private static final int LIMIT = 1024 * 1024;
    private static ObjectNode object() { return JsonNodeFactory.instance.objectNode(); }
    private static ArrayNode array() { return JsonNodeFactory.instance.arrayNode(); }
    private static JsonNode parse(String text) { return FullJsonTree.parse(text.getBytes(StandardCharsets.UTF_8), LIMIT); }
    private static ObjectNode row(int identity, String arrayText) {
        ObjectNode row = object(); row.put("index", identity); row.put("command", "query-declarable-wars"); row.put("ok", true);
        ObjectNode source = row.putObject("read_history_source");
        source.put("schema", "xar.driver-read-history-source/v1"); source.put("kind", "DECLARABLE_WARS");
        source.put("payload_field", "declarable_wars"); source.put("unknown_source", "receipt-" + identity);
        ObjectNode frame = source.putObject("source_frame"); frame.putObject("frame").put("revision", identity);
        frame.putObject("game").put("pid", 123); frame.put("machine_id", "fixture-machine");
        ObjectNode result = row.putObject("result"); result.put("status", "available");
        result.put("query_sequence", identity); result.put("unknown_result", "own-" + identity);
        result.set("declarable_wars", parse(arrayText)); return row;
    }
    private static boolean apply(ArrayNode history) throws Exception {
        Method method = RootOnlineDecisionSelector.class.getDeclaredMethod("applyDeclarableWarHistoryAlias", ArrayNode.class);
        method.setAccessible(true); return (boolean) method.invoke(null, history);
    }
    /** Independent decoder consumes only the final alias shape and full earlier rows. */
    private static ArrayNode restore(ArrayNode projected) {
        ArrayNode restored = projected.deepCopy();
        for (int i = 0; i < restored.size(); i++) {
            JsonNode raw = restored.get(i).get("result");
            if (raw == null || !raw.isObject() || !raw.has("declarable_wars_history_ref")) continue;
            ObjectNode result = (ObjectNode) raw; JsonNode reference = result.get("declarable_wars_history_ref");
            assertTrue(reference.isIntegralNumber() && reference.canConvertToInt());
            int position = reference.intValue(); assertTrue(position >= 0 && position < i);
            JsonNode sourceResult = restored.get(position).get("result");
            assertFalse(sourceResult.has("declarable_wars_history_ref")); assertTrue(sourceResult.path("declarable_wars").isArray());
            assertFalse(result.has("declarable_wars"));
            result.set("declarable_wars", sourceResult.get("declarable_wars").deepCopy());
            result.remove("declarable_wars_history_ref");
        }
        return restored;
    }
    @Test void referencesOriginalPositionsAndPreservesSeparateUnknownFacts() throws Exception {
        ArrayNode original = array(); original.addNull(); original.add("unrelated");
        original.add(row(373, "[{\"future\":{\"huge\":184467440737095516170001},\"order\":[1,2]}]"));
        original.add(object());
        original.add(row(379, "[{\"future\":{\"huge\":184467440737095516170001},\"order\":[1,2]}]"));
        original.add(row(900, "[{\"future\":{\"huge\":184467440737095516170001},\"order\":[1,2]}]"));
        byte[] immutableBefore = FullJsonTree.encode(original, LIMIT);
        ArrayNode projected = original.deepCopy(); assertTrue(apply(projected));
        assertTrue(projected.get(2).path("result").path("declarable_wars").isArray());
        assertEquals(2, projected.get(4).path("result").path("declarable_wars_history_ref").intValue());
        assertEquals(2, projected.get(5).path("result").path("declarable_wars_history_ref").intValue());
        assertEquals(original, restore(projected));
        for (int i : List.of(2, 4, 5)) {
            assertEquals(original.get(i).get("read_history_source"), projected.get(i).get("read_history_source"));
            assertEquals(original.get(i).path("result").get("query_sequence"), projected.get(i).path("result").get("query_sequence"));
            assertEquals(original.get(i).path("result").get("unknown_result"), projected.get(i).path("result").get("unknown_result"));
        }
        assertArrayEquals(immutableBefore, FullJsonTree.encode(original, LIMIT));
    }
    @Test void exactDecimalTokensIntegerTypesAndArrayOrderRemainDistinct() throws Exception {
        List<String> variants = List.of("[1]", "[1.0]", "[1e0]", "[1E0]", "[-0.0]", "[0.0]",
                "[184467440737095516170001]", "[1,2]", "[2,1]", "[{\"x\":1}]", "[{\"x\":1,\"unknown\":null}]");
        ArrayNode original = array(); original.add(false);
        for (int i = 0; i < variants.size(); i++) original.add(row(100 + i, variants.get(i)));
        for (int i = 0; i < variants.size(); i++) original.add(row(900 + i, variants.get(i)));
        ArrayNode projected = original.deepCopy(); assertTrue(apply(projected));
        for (int i = 0; i < variants.size(); i++) {
            assertTrue(projected.get(i + 1).path("result").has("declarable_wars"));
            assertEquals(i + 1, projected.get(variants.size() + i + 1).path("result").path("declarable_wars_history_ref").intValue());
            assertArrayEquals(FullJsonTree.encode(parse(variants.get(i)), LIMIT),
                    FullJsonTree.encode(restore(projected).get(i + 1).path("result").get("declarable_wars"), LIMIT));
        }
        assertEquals(original, restore(projected));
    }
    @Test void anyOccupiedReferenceNameDisablesTheWholeRequestBeforeMutation() throws Exception {
        for (JsonNode occupied : List.of(parse("null"), parse("2"), parse("{\"unknown\":true}"))) {
            ArrayNode original = array(); original.add(row(1, "[1]")); original.add(row(2, "[1]"));
            ObjectNode collision = object(); collision.putObject("result").set("declarable_wars_history_ref", occupied);
            original.add(collision); // Nonqualifying and AFTER duplicates: preflight must still prevent all mutation.
            ArrayNode projected = original.deepCopy(); assertFalse(apply(projected)); assertEquals(original, projected);
            assertArrayEquals(FullJsonTree.encode(original, LIMIT), FullJsonTree.encode(projected, LIMIT));
        }
        ArrayNode qualifyingCollision = array(); ObjectNode first = row(1, "[1]");
        ((ObjectNode) first.get("result")).putNull("declarable_wars_history_ref");
        qualifyingCollision.add(first); qualifyingCollision.add(row(2, "[1]")); qualifyingCollision.add(row(3, "[1]"));
        ArrayNode before = qualifyingCollision.deepCopy(); assertFalse(apply(qualifyingCollision)); assertEquals(before, qualifyingCollision);
    }
    @Test void unfamiliarFailedEmptyAndNonArrayRowsRemainComplete() throws Exception {
        List<ObjectNode> unsupported = new ArrayList<>();
        ObjectNode extra = row(1, "[1]"); extra.put("unknown_top", 1); unsupported.add(extra);
        ObjectNode failed = row(2, "[1]"); failed.put("ok", false); unsupported.add(failed);
        ObjectNode source = row(3, "[1]"); ((ObjectNode) source.get("read_history_source")).put("kind", "UNKNOWN"); unsupported.add(source);
        ObjectNode unavailable = row(4, "[1]"); ((ObjectNode) unavailable.get("result")).put("status", "unavailable"); unsupported.add(unavailable);
        unsupported.add(row(5, "[]")); unsupported.add(row(6, "{\"x\":1}"));
        for (ObjectNode unsupportedRow : unsupported) {
            ArrayNode history = array(); history.add(unsupportedRow); history.add(unsupportedRow.deepCopy());
            ArrayNode before = history.deepCopy(); assertFalse(apply(history)); assertEquals(before, history);
        }
    }
    private static JsonNode payload(ArrayNode history, boolean expectedChanged) throws Exception {
        List<OpportunityJson.Obj> frames = new ArrayList<>();
        for (JsonNode item : history) frames.add((OpportunityJson.Obj) OpportunityJson.parseComplete(FullJsonTree.encode(item, LIMIT), LIMIT));
        OperationKey operation = new OperationKey("DATE_ADVANCE");
        PlanningRequest request = PlanningFixtures.request(PlanningFixtures.snapshot(), frames, Set.of(operation));
        var command = PlanningFixtures.command(request, operation, new OpportunityJson.Obj(Map.of()));
        var draft = new OrdinaryPolicy.Draft("fixture", "fixture", "fixture", OrdinaryPolicy.Kind.ORDINARY,
                Optional.of(command), OrdinaryPolicy.Purpose.DATE_ADVANCE, Optional.empty(), new OpportunityJson.Obj(Map.of()));
        var proposal = new PlanningResult.ActionSelected(command, new PlanTrace(request.before(), List.of(), Optional.of(draft)));
        byte[] originalCommand = ActionCodec.encodeCommand(command); String sha = ActionCodec.bodySha256(command);
        byte[] originalHistory = FullJsonTree.encode(history, LIMIT);
        var config = new RootOrdinaryRuntimeConfiguration.DecisionProvider(URI.create("http://127.0.0.1:1"),
                "test", Duration.ofSeconds(10), 1, Duration.ZERO);
        var selector = new RootOnlineDecisionSelector(config, Clock.fixed(PlanningFixtures.NOW, ZoneOffset.UTC), raw -> {
            throw new AssertionError("Formatting must not archive or send anything");
        });
        Method method = RootOnlineDecisionSelector.class.getDeclaredMethod("requestPayload", PlanningRequest.class,
                PlanningResult.ActionSelected.class, String.class); method.setAccessible(true);
        JsonNode envelope = FullJsonTree.parse((byte[]) method.invoke(selector, request, proposal, sha), LIMIT);
        String policy = envelope.get("messages").get(0).get("content").textValue();
        JsonNode data = parse(envelope.get("messages").get(1).get("content").textValue());
        assertEquals(expectedChanged, data.has("history_declarable_wars_projection_schema"));
        assertEquals("xar.model-root-history-dictionary/v1", data.path("history_projection_schema").textValue());
        assertEquals(command.actionId(), data.path("proposal_id").textValue()); assertEquals(sha, data.path("body_sha256").textValue());
        assertEquals(FullJsonTree.parse(originalCommand, LIMIT), data.get("proposal"));
        assertArrayEquals(originalCommand, ActionCodec.encodeCommand(command)); assertEquals(sha, ActionCodec.bodySha256(command));
        assertArrayEquals(originalHistory, FullJsonTree.encode(history, LIMIT));
        assertTrue(policy.contains("history[history[i].result.declarable_wars_history_ref].result.declarable_wars"));
        assertTrue(policy.contains("exactly one compact JSON line containing exactly"));
        assertTrue(policy.contains("proposal_id and body_sha256 still identify the original unprojected command"));
        // Fixture put(int) uses IntNode; the real material parser represents all JSON integers as BigIntegerNode.
        // Parse the expected original bytes with the same exact-token boundary, preserving every JSON value/token.
        assertEquals(FullJsonTree.parse(originalHistory, LIMIT),
                expectedChanged ? restore((ArrayNode) data.get("history")) : data.get("history"));
        return data;
    }
    @Test void payloadAddsMarkerOnlyForRealAliasAndKeepsOriginalProposal() throws Exception {
        ArrayNode history = array(); history.add(row(373, "[{\"unknown\":1e0}]")); history.add(row(379, "[{\"unknown\":1e0}]"));
        JsonNode data = payload(history, true);
        assertEquals("xar.model-history-declarable-wars-alias/v1", data.path("history_declarable_wars_projection_schema").textValue());
        assertEquals(0, data.get("history").get(1).path("result").path("declarable_wars_history_ref").intValue());
    }
    @Test void payloadOmitsMarkerForUniqueArraysOrAnyCollision() throws Exception {
        ArrayNode unique = array(); unique.add(row(1, "[1]")); unique.add(row(2, "[2]")); payload(unique, false);
        ArrayNode collision = array(); collision.add(row(1, "[1]")); collision.add(row(2, "[1]"));
        ((ObjectNode) collision.get(1).get("result")).putNull("declarable_wars_history_ref"); payload(collision, false);
    }
}
