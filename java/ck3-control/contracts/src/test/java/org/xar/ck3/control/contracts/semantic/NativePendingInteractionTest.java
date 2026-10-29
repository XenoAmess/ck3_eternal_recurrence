package org.xar.ck3.control.contracts.semantic;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

/** Actual original producer differential; the shared contract remains below Driver and native transport. */
class NativePendingInteractionTest {
    private static final JsonNodeFactory F = JsonNodeFactory.instance;

    @Test void originalNullableProjectionSignedIdentityAndSenderIntegerHaveExactRoundTrips() {
        assertThrows(NullPointerException.class, () -> NativePendingInteraction.decode(null));
        assertEquals(Optional.empty(), NativePendingInteraction.decode(F.objectNode().path("missing")));
        assertEquals(Optional.empty(), NativePendingInteraction.decode(NullNode.getInstance()));
        assertTrue(NativePendingInteraction.encode(Optional.empty()).isNull());
        assertTrue(NativePendingInteraction.normalize(F.objectNode().path("missing")).isNull());
        assertTrue(NativePendingInteraction.normalize(NullNode.getInstance()).isNull());
        for (int id : List.of(Integer.MIN_VALUE, -2, 0, 1, Integer.MAX_VALUE)) {
            ObjectNode original = valid(id, new BigInteger("18446744073709551616123"), id != 0);
            original.put("source", "untrusted input").put("ignored_extra", true);
            var actual = NativePendingInteraction.decode(original);
            JsonNode encoded = NativePendingInteraction.encode(actual);
            assertEquals(new NativePendingInteraction.Pending(id, new BigInteger("18446744073709551616123"), id != 0), actual.orElseThrow());
            assertEquals("native", encoded.get("source").textValue());
            assertEquals(4, encoded.size());
            assertEquals(actual, NativePendingInteraction.decode(StrictJson.parse(StrictJson.canonical(encoded))));
            original.put("instance_id", 17);
            assertEquals(id, actual.orElseThrow().instanceId());
        }
        var negativeSender = NativePendingInteraction.decode(valid(-2, BigInteger.valueOf(-1), false));
        assertEquals(BigInteger.valueOf(-1), negativeSender.orElseThrow().senderCharacterId());
    }

    @Test void malformedPresentObjectsRejectMissingNullBooleanFloatAndWrongIdentityWidth() {
        for (JsonNode malformed : List.of(F.booleanNode(true), F.numberNode(1), F.numberNode(1.0), F.textNode("1"), F.arrayNode()))
            assertThrows(IllegalArgumentException.class, () -> NativePendingInteraction.decode(malformed));
        for (String field : List.of("instance_id", "sender_character_id", "auto_accept_notification")) {
            ObjectNode missing = valid(0, BigInteger.ZERO, false); missing.remove(field);
            assertThrows(IllegalArgumentException.class, () -> NativePendingInteraction.decode(missing));
            ObjectNode nil = valid(0, BigInteger.ZERO, false); nil.putNull(field);
            assertThrows(IllegalArgumentException.class, () -> NativePendingInteraction.decode(nil));
        }
        for (JsonNode wrong : List.of(F.booleanNode(true), F.numberNode(0.0), F.textNode("0"), F.arrayNode(), F.objectNode())) {
            for (String field : List.of("instance_id", "sender_character_id")) {
                ObjectNode malformed = valid(0, BigInteger.ZERO, false); malformed.set(field, wrong);
                assertThrows(IllegalArgumentException.class, () -> NativePendingInteraction.decode(malformed));
            }
        }
        for (JsonNode wrong : List.of(F.numberNode(-1), F.numberNode(new BigInteger("2147483648")), F.numberNode(new BigInteger("-2147483649")))) {
            ObjectNode malformed = valid(0, BigInteger.ZERO, false); malformed.set("instance_id", wrong);
            assertThrows(IllegalArgumentException.class, () -> NativePendingInteraction.decode(malformed));
        }
        for (JsonNode wrong : List.of(F.numberNode(0), F.numberNode(1), F.numberNode(1.0), F.textNode("true"))) {
            ObjectNode malformed = valid(0, BigInteger.ZERO, false); malformed.set("auto_accept_notification", wrong);
            assertThrows(IllegalArgumentException.class, () -> NativePendingInteraction.decode(malformed));
        }
        assertThrows(IllegalArgumentException.class, () -> new NativePendingInteraction.Pending(-1, BigInteger.ONE, true));
    }

    @Test void actualOriginalPythonProducerMatchesAllAcceptedAndRejectedSemanticInputs() throws Exception {
        String python = required("xar.python");
        Path repository = Path.of(required("xar.repository.root")).toRealPath();
        ArrayNode cases = corpus(); ArrayNode expected = F.arrayNode();
        for (JsonNode original : cases) expected.add(outcome(original));
        String script = """
                import json,sys
                from xar_autoplayer.bridge.native_driver import _pending_character_interaction
                result=[]
                for original in json.load(sys.stdin):
                    try:
                        result.append({'ok':True,'value':_pending_character_interaction(original)})
                    except ValueError as error:
                        result.append({'ok':False,'error':str(error)})
                json.dump(result,sys.stdout,ensure_ascii=False,separators=(',',':'),allow_nan=False)
                """;
        ProcessBuilder builder = new ProcessBuilder(python, "-c", script).directory(repository.toFile()).redirectErrorStream(true);
        builder.environment().put("XAR_SOURCE_REPOSITORY", repository.toString());
        builder.environment().put("PYTHONPATH", repository.resolve("ck3_autonomous_player/src").toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Process child = builder.start(); CompletableFuture<byte[]> bytes = new CompletableFuture<>();
        Thread reader = Thread.ofVirtual().start(() -> {
            try { bytes.complete(child.getInputStream().readNBytes(1024 * 1024 + 1)); }
            catch (java.io.IOException failure) { bytes.completeExceptionally(failure); }
        });
        try {
            child.getOutputStream().write(new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsBytes(cases)); child.getOutputStream().close();
            assertTrue(child.waitFor(30, TimeUnit.SECONDS), "original pending producer timed out");
            byte[] original = bytes.get(5, TimeUnit.SECONDS);
            assertTrue(original.length <= 1024 * 1024, "bounded original producer output required");
            assertEquals(0, child.exitValue(), new String(original, StandardCharsets.UTF_8));
            assertEquals(StrictJson.parse(StrictJson.canonical(expected)), StrictJson.parse(original));
        } finally {
            if (child.isAlive()) child.destroyForcibly();
            reader.join(5000);
        }
    }

    private static String required(String name) {
        String value = System.getProperty(name);
        assertNotNull(value, "required " + name + " property absent; original producer differential cannot skip");
        assertFalse(value.isBlank(), "required " + name + " property blank");
        return value;
    }
    private static ObjectNode valid(int id, BigInteger sender, boolean notification) {
        return F.objectNode().put("instance_id", id).put("sender_character_id", sender).put("auto_accept_notification", notification);
    }
    private static ObjectNode outcome(JsonNode original) {
        ObjectNode result = F.objectNode();
        try { result.put("ok", true).set("value", NativePendingInteraction.encode(NativePendingInteraction.decode(original))); }
        catch (IllegalArgumentException invalid) { result.removeAll(); result.put("ok", false).put("error", invalid.getMessage()); }
        return result;
    }
    private static ArrayNode corpus() {
        ArrayNode cases = F.arrayNode().addNull().add(true).add(1).add(1.0).add("x").add(F.arrayNode()).add(F.objectNode());
        for (int id : List.of(Integer.MIN_VALUE, -2, 0, 1, Integer.MAX_VALUE))
            for (boolean notification : List.of(false, true))
                for (BigInteger sender : List.of(BigInteger.valueOf(-1), BigInteger.ZERO, BigInteger.ONE, new BigInteger("18446744073709551616123")))
                    cases.add(valid(id, sender, notification).put("source", "discarded").put("extra", 42));
        for (String field : List.of("instance_id", "sender_character_id", "auto_accept_notification")) {
            ObjectNode missing = valid(0, BigInteger.ONE, false); missing.remove(field); cases.add(missing);
            ObjectNode nil = valid(0, BigInteger.ONE, false); nil.putNull(field); cases.add(nil);
            for (JsonNode wrong : List.of(F.numberNode(0.0), F.textNode("0"), F.arrayNode(), F.objectNode())) {
                ObjectNode invalid = valid(0, BigInteger.ONE, false); invalid.set(field, wrong); cases.add(invalid);
            }
        }
        for (String field : List.of("instance_id", "sender_character_id"))
            cases.add(valid(0, BigInteger.ONE, false).set(field, F.booleanNode(true)));
        cases.add(valid(-1, BigInteger.ONE, false));
        for (BigInteger id : List.of(new BigInteger("2147483648"), new BigInteger("-2147483649")))
            cases.add(valid(0, BigInteger.ONE, false).set("instance_id", F.numberNode(id)));
        cases.add(valid(0, BigInteger.ONE, false).set("auto_accept_notification", F.numberNode(1)));
        return cases;
    }
}
