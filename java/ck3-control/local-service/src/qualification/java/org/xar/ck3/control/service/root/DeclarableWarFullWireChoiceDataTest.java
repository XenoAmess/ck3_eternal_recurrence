package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.MissingNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.net.URI;
import java.net.http.HttpClient;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.contracts.FullJsonTree;

/** Complete-wire encoding DATA only. Never invokes select/requestPayload/HTTP, Root, Guard or Game. */
final class DeclarableWarFullWireChoiceDataTest {
    private static final String WHOLE = "xar.model-history-declarable-wars-alias/v1";
    private static final String ITEMS = "xar.model-history-declarable-war-items/v1";
    private static final String ROOTS = "xar.model-root-history-dictionary/v1";

    @Test void actualEvent13RestoresAliasBeforeComparingCompleteOriginalAndItemWires() throws Exception {
        Path input = Path.of(System.getProperty("xar.choice.event13.request"));
        byte[] originalWire = Files.readAllBytes(input);
        assertEquals(1838824, originalWire.length);
        assertEquals("614a3104234e4dc45ab5da6de2cb18c8264e11e88ea6f0ea16da6e4d2b84c1c4", sha(originalWire));
        ObjectNode request = (ObjectNode) FullJsonTree.parse(originalWire, FullJsonTree.MAXIMUM_BYTES);
        assertEquals(2, request.path("messages").size());
        byte[] aliasedUserBytes = request.path("messages").get(1).path("content").textValue().getBytes(StandardCharsets.UTF_8);
        assertEquals(1665178, aliasedUserBytes.length);
        ObjectNode aliased = parse(aliasedUserBytes);
        assertArrayEquals(aliasedUserBytes, encode(aliased));
        assertEquals(86, aliased.path("history").size());
        assertEquals(25, aliased.path("root_facts").size());
        assertEquals(WHOLE, aliased.path("history_declarable_wars_projection_schema").textValue());
        assertEquals(3, aliased.path("history").get(13).path("result").path("declarable_wars_history_ref").intValue());

        // Independent expansion precedes removal of the marker. No already-aliased item input.
        ObjectNode preAlias = expandWhole(aliased);
        assertFalse(preAlias.has("history_declarable_wars_projection_schema"));
        assertFalse(preAlias.path("history").get(13).path("result").has("declarable_wars_history_ref"));
        assertArrayEquals(encode(preAlias.path("history").get(3).path("result").get("declarable_wars")),
                encode(preAlias.path("history").get(13).path("result").get("declarable_wars")));
        byte[] preAliasBefore = encode(preAlias);
        try (var h = new Encoder(request.path("model").textValue())) {
            assertEquals(request.path("messages").get(0).path("content").textValue(), h.policy);
            ObjectNode wholeData = h.whole(preAlias);
            byte[] wholeWire = h.encode(wholeData, h.policy);
            assertArrayEquals(originalWire, wholeWire, "rebuild the entire original HTTP body, including policy and all envelope fields");
            assertArrayEquals(preAliasBefore, encode(expandWhole(wholeData)));

            ObjectNode itemData = RootOnlineDecisionSelector.projectDeclarableWarItems(preAlias);
            assertNotNull(itemData);
            assertEquals(ITEMS, itemData.path("history_declarable_wars_projection_schema").textValue());
            assertArrayEquals(preAliasBefore, encode(expandItems(itemData)), "independent complete item expansion");
            byte[] itemWire = h.encode(itemData, h.policy + h.itemPolicy);
            byte[] actualChoice = h.choose(preAlias);
            assertArrayEquals(itemWire.length < wholeWire.length ? itemWire : wholeWire, actualChoice);
            assertEnvelope(request, parse(actualChoice));
            ObjectNode chosenUser = user(actualChoice);
            assertArrayEquals(preAliasBefore, encode(expandSelected(chosenUser)));
            assertUnchangedFields(preAlias, chosenUser);
            var command = ActionCodec.decodeCommand(encode(preAlias.get("proposal")));
            assertEquals(preAlias.path("proposal_id").textValue(), command.actionId());
            assertEquals(preAlias.path("body_sha256").textValue(), ActionCodec.bodySha256(command));
            assertEquals(command.actionId(), chosenUser.path("proposal_id").textValue());
            assertEquals(ActionCodec.bodySha256(command), chosenUser.path("body_sha256").textValue());
            assertArrayEquals(preAliasBefore, encode(preAlias));
            assertArrayEquals(aliasedUserBytes, encode(aliased));
            System.out.println("EVENT13_CHOICE_DATA whole=" + wholeWire.length + " item=" + itemWire.length
                    + " chosen=" + actualChoice.length + " prealias_member_position=NOT_HELD");
        }
        assertArrayEquals(originalWire, Files.readAllBytes(input));
    }

    @Test void freshSyntheticFormatsRestoreAllOrderNumericTokensAndCollisionFallback() throws Exception {
        try (var h = new Encoder("data-only-model")) {
            ObjectNode itemWins = synthetic(2048, false);
            assertFormatChoice(h, itemWins, true);
            ObjectNode wholeWins = synthetic(2048, true);
            assertFormatChoice(h, wholeWins, false);

            // Independently represented object order and decimal-token variants cannot be interned as one fact.
            ObjectNode variants = synthetic(2048, false);
            ObjectNode a = parse("{\"unknown\":{\"z\":1,\"a\":2},\"n\":1.0,\"big\":9007199254740993}");
            ObjectNode b = parse("{\"n\":1.0,\"unknown\":{\"z\":1,\"a\":2},\"big\":9007199254740993}");
            ObjectNode c = parse("{\"unknown\":{\"z\":1,\"a\":2},\"n\":1.00,\"big\":9007199254740993}");
            ((ObjectNode) variants.path("history").get(0).get("result")).set("declarable_wars", array().add(a).add(b).add(a));
            ((ObjectNode) variants.path("history").get(1).get("result")).set("declarable_wars", array().add(c).add(b).add(a));
            byte[] variantsBefore = encode(variants);
            ObjectNode items = RootOnlineDecisionSelector.projectDeclarableWarItems(variants);
            assertNotNull(items);
            assertEquals(3, items.path("declarable_war_facts").size());
            assertArrayEquals(encode(array().add(0).add(1).add(0)), encode(items.path("history").get(0).path("result").get("declarable_war_fact_refs")));
            assertArrayEquals(encode(array().add(2).add(1).add(0)), encode(items.path("history").get(1).path("result").get("declarable_war_fact_refs")));
            assertArrayEquals(variantsBefore, encode(expandItems(items)));
            byte[] wholeWire = h.encode(h.whole(variants), h.policy);
            byte[] itemWire = h.encode(items, h.policy + h.itemPolicy);
            byte[] variantsChoice = h.choose(variants);
            assertArrayEquals(itemWire.length < wholeWire.length ? itemWire : wholeWire, variantsChoice);
            assertArrayEquals(variantsBefore, encode(expandWhole(user(wholeWire))));
            assertArrayEquals(variantsBefore, encode(expandSelected(user(variantsChoice))));
            assertArrayEquals(variantsBefore, encode(variants));

            ObjectNode collision = synthetic(2048, true);
            collision.putNull("declarable_war_facts");
            byte[] collisionBefore = encode(collision);
            assertNull(RootOnlineDecisionSelector.projectDeclarableWarItems(collision));
            byte[] ordinary = h.encode(h.whole(collision), h.policy);
            assertArrayEquals(ordinary, h.choose(collision));
            assertArrayEquals(collisionBefore, encode(expandSelected(user(ordinary))));
            assertArrayEquals(collisionBefore, encode(collision));
        }
    }

    @Test void equalCompleteWireLengthsKeepTheOriginalWholeWire() throws Exception {
        try (var h = new Encoder("data-only-model")) {
            ObjectNode zero = synthetic(0, false);
            byte[] whole0 = h.encode(h.whole(zero), h.policy);
            ObjectNode item0Data = RootOnlineDecisionSelector.projectDeclarableWarItems(zero);
            assertNotNull(item0Data);
            byte[] item0 = h.encode(item0Data, h.policy + h.itemPolicy);
            int tiePadding = item0.length - whole0.length;
            assertTrue(tiePadding > 0 && tiePadding <= 8192, "finite functional boundary, not a measurement calibration");
            ObjectNode one = synthetic(1, false);
            assertEquals(tiePadding - 1, h.encode(RootOnlineDecisionSelector.projectDeclarableWarItems(one), h.policy + h.itemPolicy).length
                    - h.encode(h.whole(one), h.policy).length, "one ASCII character is duplicated twice by ordinary wire and once by dictionary wire");
            ObjectNode tie = synthetic(tiePadding, false);
            byte[] before = encode(tie);
            byte[] whole = h.encode(h.whole(tie), h.policy);
            byte[] item = h.encode(RootOnlineDecisionSelector.projectDeclarableWarItems(tie), h.policy + h.itemPolicy);
            assertEquals(whole.length, item.length, "genuine tie includes every HTTP byte and the added system policy");
            assertFalse(Arrays.equals(whole, item));
            assertArrayEquals(whole, h.choose(tie), "only strictly shorter complete item wire may replace the original");
            assertArrayEquals(before, encode(expandSelected(user(whole))));
            assertArrayEquals(before, encode(expandItems(user(item))));
            assertArrayEquals(before, encode(tie));
        }
    }

    @Test void baselineStrictEncodingFailureEscapesTheOptionalProjectionCatch() throws Exception {
        try (var h = new Encoder("data-only-model")) {
            ObjectNode invalid = synthetic(0, false);
            invalid.set("unknown_root_original", MissingNode.getInstance());
            ObjectNode baseline = h.whole(invalid);
            var originalFailure = assertThrows(IllegalArgumentException.class, () -> h.encode(baseline, h.policy));
            var chosenFailure = assertThrows(IllegalArgumentException.class, () -> h.choose(invalid));
            assertEquals("bounded complete JSON tree required", originalFailure.getMessage());
            assertEquals(originalFailure.getClass(), chosenFailure.getClass());
            assertEquals(originalFailure.getMessage(), chosenFailure.getMessage());
            assertTrue(invalid.get("unknown_root_original").isMissingNode());
        }
    }

    private static void assertFormatChoice(Encoder h, ObjectNode original, boolean itemWins) throws Exception {
        byte[] before = encode(original);
        ObjectNode whole = h.whole(original);
        ObjectNode item = RootOnlineDecisionSelector.projectDeclarableWarItems(original);
        assertNotNull(item);
        byte[] wholeWire = h.encode(whole, h.policy);
        byte[] itemWire = h.encode(item, h.policy + h.itemPolicy);
        assertEquals(itemWins, itemWire.length < wholeWire.length);
        byte[] selected = h.choose(original);
        assertArrayEquals(itemWins ? itemWire : wholeWire, selected);
        assertArrayEquals(before, encode(expandWhole(whole)));
        assertArrayEquals(before, encode(expandItems(item)));
        assertArrayEquals(before, encode(expandSelected(user(selected))));
        assertEnvelope(parse(wholeWire), parse(selected));
        assertUnchangedFields(original, user(selected));
        assertArrayEquals(before, encode(original));
    }

    private static void assertEnvelope(ObjectNode original, ObjectNode changed) {
        assertEquals(List.of("model", "temperature", "stream", "max_tokens", "stream_options", "chat_template_kwargs", "response_format", "messages"), keys(original));
        assertEquals(keys(original), keys(changed));
        for (String name : keys(original)) if (!name.equals("messages")) assertArrayEquals(encode(original.get(name)), encode(changed.get(name)), name);
        assertEquals(2, changed.path("messages").size());
        assertEquals("system", changed.path("messages").get(0).path("role").textValue());
        assertEquals("user", changed.path("messages").get(1).path("role").textValue());
        for (JsonNode message : changed.path("messages")) assertEquals(List.of("role", "content"), keys((ObjectNode) message));
    }

    private static void assertUnchangedFields(ObjectNode original, ObjectNode projected) {
        for (var field : original.properties()) {
            if (field.getKey().equals("history")) continue;
            assertArrayEquals(encode(field.getValue()), encode(projected.get(field.getKey())), field.getKey());
        }
    }

    /** Fresh pure-DATA rows. Wars are last so the old whole-alias format can restore exact member order. */
    private static ObjectNode synthetic(int padding, boolean equalArrays) {
        ObjectNode data = object();
        ArrayNode history = data.putArray("history");
        ObjectNode common = parse("{\"tag\":\"shared\",\"padding\":\"" + "A".repeat(padding)
                + "\",\"n\":1.00,\"big\":9007199254740993,\"unknown\":{\"z\":1,\"a\":2}}");
        ObjectNode a = parse("{\"tail\":\"a\",\"n\":-0.00e+2}");
        ObjectNode b = parse("{\"tail\":\"b\",\"n\":1.2300E-7}");
        history.add(row(1, array().add(common).add(a)));
        history.add(row(2, array().add(common).add(equalArrays ? a : b)));
        data.putArray("root_facts");
        data.put("history_projection_schema", ROOTS);
        data.putObject("unknown_root").put("opaque", "retain-all");
        data.putObject("proposal").put("operation", "data-only-not-an-action");
        data.put("proposal_id", "data-only-proposal");
        data.put("body_sha256", "f".repeat(64));
        return data;
    }

    private static ObjectNode row(int index, ArrayNode wars) {
        ObjectNode row = object(); row.put("index", index); row.put("command", "query-declarable-wars"); row.put("ok", true);
        ObjectNode result = row.putObject("result"); result.put("status", "available"); result.put("row_marker", "row-" + index); result.set("declarable_wars", wars);
        ObjectNode source = row.putObject("read_history_source"); source.put("schema", "xar.driver-read-history-source/v1");
        source.put("kind", "DECLARABLE_WARS"); source.put("payload_field", "declarable_wars");
        ObjectNode frame = source.putObject("source_frame"); frame.put("machine_id", "data-only");
        frame.putObject("game").put("data_only", true); frame.putObject("frame").put("row_stamp", index);
        return row;
    }

    private static ObjectNode expandSelected(ObjectNode value) {
        String schema = value.path("history_declarable_wars_projection_schema").asText();
        return schema.equals(ITEMS) ? expandItems(value) : schema.equals(WHOLE) ? expandWhole(value) : value;
    }

    /** Independent wire-format expander. Never interns, chooses a representation or calls a producer helper. */
    private static ObjectNode expandWhole(ObjectNode value) {
        if (!WHOLE.equals(value.path("history_declarable_wars_projection_schema").asText())) return value;
        ObjectNode out = object();
        JsonNode sourceHistory = value.get("history");
        for (var field : value.properties()) {
            if (field.getKey().equals("history_declarable_wars_projection_schema")) continue;
            if (!field.getKey().equals("history")) { out.set(field.getKey(), field.getValue()); continue; }
            ArrayNode rows = out.putArray("history");
            for (JsonNode originalRow : sourceHistory) {
                if (!originalRow.path("result").has("declarable_wars_history_ref")) { rows.add(originalRow); continue; }
                ObjectNode row = object();
                for (var rowField : ((ObjectNode) originalRow).properties()) {
                    if (!rowField.getKey().equals("result")) { row.set(rowField.getKey(), rowField.getValue()); continue; }
                    ObjectNode result = row.putObject("result");
                    for (var member : ((ObjectNode) rowField.getValue()).properties()) {
                        if (!member.getKey().equals("declarable_wars_history_ref")) { result.set(member.getKey(), member.getValue()); continue; }
                        JsonNode ref = member.getValue();
                        assertTrue(ref.isIntegralNumber() && ref.canConvertToInt());
                        int index = ref.intValue(); assertTrue(index >= 0 && index < sourceHistory.size());
                        JsonNode wars = sourceHistory.get(index).path("result").get("declarable_wars");
                        assertNotNull(wars); assertTrue(wars.isArray()); result.set("declarable_wars", wars);
                    }
                }
                rows.add(row);
            }
        }
        return out;
    }

    /** Independent item-reference expansion retains the refs field's exact member position. */
    private static ObjectNode expandItems(ObjectNode value) {
        assertEquals(ITEMS, value.path("history_declarable_wars_projection_schema").asText());
        JsonNode facts = value.get("declarable_war_facts"); assertNotNull(facts); assertTrue(facts.isArray());
        ObjectNode out = object();
        for (var field : value.properties()) {
            if (field.getKey().equals("declarable_war_facts") || field.getKey().equals("history_declarable_wars_projection_schema")) continue;
            if (!field.getKey().equals("history")) { out.set(field.getKey(), field.getValue()); continue; }
            ArrayNode rows = out.putArray("history");
            for (JsonNode originalRow : field.getValue()) {
                if (!originalRow.path("result").has("declarable_war_fact_refs")) { rows.add(originalRow); continue; }
                ObjectNode row = object();
                for (var rowField : ((ObjectNode) originalRow).properties()) {
                    if (!rowField.getKey().equals("result")) { row.set(rowField.getKey(), rowField.getValue()); continue; }
                    ObjectNode result = row.putObject("result");
                    for (var member : ((ObjectNode) rowField.getValue()).properties()) {
                        if (!member.getKey().equals("declarable_war_fact_refs")) { result.set(member.getKey(), member.getValue()); continue; }
                        ArrayNode wars = result.putArray("declarable_wars");
                        for (JsonNode ref : member.getValue()) {
                            assertTrue(ref.isIntegralNumber() && ref.canConvertToInt());
                            int index = ref.intValue(); assertTrue(index >= 0 && index < facts.size()); wars.add(facts.get(index));
                        }
                    }
                }
                rows.add(row);
            }
        }
        return out;
    }

    private static ObjectNode object() { return JsonNodeFactory.instance.objectNode(); }
    private static ArrayNode array() { return JsonNodeFactory.instance.arrayNode(); }
    private static ObjectNode parse(String value) { return parse(value.getBytes(StandardCharsets.UTF_8)); }
    private static ObjectNode parse(byte[] value) { return (ObjectNode) FullJsonTree.parse(value, FullJsonTree.MAXIMUM_BYTES); }
    private static byte[] encode(JsonNode value) { return FullJsonTree.encode(value, FullJsonTree.MAXIMUM_BYTES); }
    private static ObjectNode user(byte[] wire) { return parse(parse(wire).path("messages").get(1).path("content").textValue()); }
    private static String sha(byte[] raw) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
    private static List<String> keys(ObjectNode value) { var result = new ArrayList<String>(); value.fieldNames().forEachRemaining(result::add); return result; }

    /** Reflects only real pure DATA encoding methods/strings, following the existing HostedTest pattern. */
    private static final class Encoder implements AutoCloseable {
        final RootOnlineDecisionSelector selector;
        final Method choose;
        final Method encode;
        final Method alias;
        final String policy;
        final String itemPolicy;
        final HttpClient http;
        Encoder(String model) throws Exception {
            choose = RootOnlineDecisionSelector.class.getDeclaredMethod("encodeDeclarableWarAlternatives", ObjectNode.class); choose.setAccessible(true);
            encode = RootOnlineDecisionSelector.class.getDeclaredMethod("encodeModelInput", ObjectNode.class, String.class); encode.setAccessible(true);
            alias = RootOnlineDecisionSelector.class.getDeclaredMethod("applyDeclarableWarHistoryAlias", ArrayNode.class); alias.setAccessible(true);
            Field policyField = RootOnlineDecisionSelector.class.getDeclaredField("POLICY"); policyField.setAccessible(true); policy = (String) policyField.get(null);
            Field itemField = RootOnlineDecisionSelector.class.getDeclaredField("WAR_ITEM_POLICY"); itemField.setAccessible(true); itemPolicy = (String) itemField.get(null);
            Field httpField = RootOnlineDecisionSelector.class.getDeclaredField("http"); httpField.setAccessible(true);
            var config = new RootOrdinaryRuntimeConfiguration.DecisionProvider(URI.create("http://127.0.0.1:1/v1"), model,
                    Duration.ofSeconds(1), 1, Duration.ZERO);
            selector = new RootOnlineDecisionSelector(config, Clock.fixed(Instant.EPOCH, ZoneOffset.UTC),
                    raw -> { throw new AssertionError("encoding cannot issue a material, select a proposal or send HTTP"); });
            http = (HttpClient) httpField.get(selector);
        }
        byte[] choose(ObjectNode data) throws Exception { return (byte[]) invoke(choose, selector, data); }
        byte[] encode(ObjectNode data, String systemPolicy) throws Exception { return (byte[]) invoke(encode, selector, data, systemPolicy); }
        ObjectNode whole(ObjectNode original) throws Exception {
            ObjectNode baseline = object(); baseline.setAll(original);
            ArrayNode history = array(); original.get("history").forEach(history::add); baseline.set("history", history);
            if ((boolean) invoke(alias, null, history)) baseline.put("history_declarable_wars_projection_schema", WHOLE);
            return baseline;
        }
        private static Object invoke(Method method, Object receiver, Object... args) throws Exception {
            try { return method.invoke(receiver, args); }
            catch (InvocationTargetException failure) {
                if (failure.getCause() instanceof Exception cause) throw cause;
                if (failure.getCause() instanceof Error cause) throw cause;
                throw failure;
            }
        }
        @Override public void close() { http.close(); }
    }
}
