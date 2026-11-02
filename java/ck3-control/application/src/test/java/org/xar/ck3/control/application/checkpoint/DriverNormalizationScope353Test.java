package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotSame;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.function.Executable;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.HistoryEntry;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Missing;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.NullValue;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Session;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Value;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;

/** Original public DATA behavior; no private factory, reflection, store, authority or filesystem. */
class DriverNormalizationScope353Test {
    private static final List<String> SLOT_NAMES = List.of("last_checkpoint", "rollback_war_failure",
            "managed_restore_transaction", "succession_expectation", "succession_lifecycle",
            "campaign_goal", "rollback_war_failures");
    private static final Set<String> REQUIRED = Set.of("last_checkpoint", "rollback_war_failure",
            "managed_restore_transaction", "succession_expectation", "campaign_goal");
    private static final Set<String> ALLOWED = Set.of("format_version", "pipe_name", "bridge_pid",
            "episode_character_id", "episode_run_id", "command_history", "last_checkpoint",
            "rollback_war_failure", "managed_restore_transaction", "succession_expectation",
            "succession_lifecycle", "campaign_goal", "rollback_war_failures");

    @Test
    void finiteOpaqueAndUnicodeMaterialKeepsOriginalDecodeAndEncodeFailureBoundaries() {
        String high = "\\" + "uD800";
        String low = "\\" + "uDC00";
        List<Vector> vectors = List.of(
                new Vector("opaque-numbers", "{\"float_zero\":-0.000e+0,\"int_zero\":-0,\"wide\":18446744073709551616}", true),
                new Vector("opaque-exponents", "{\"huge\":1e2147483648,\"tiny\":-1e-2147483648}", true),
                new Vector("unicode-controls", "{\"雪é😀\":\"e\\u0301\\u0000\\n\\t\"}", true),
                new Vector("escaped-pair", "{\"" + high + low + "\":\"" + high + low + "\"}", true),
                new Vector("empty-string", "\"\"", true),
                new Vector("empty-array", "[]", true),
                new Vector("empty-object", "{}", true),
                new Vector("explicit-null", "null", true),
                new Vector("boolean", "false", true),
                new Vector("unpaired-high-value", "\"" + high + "\"", false),
                new Vector("unpaired-low-value", "\"" + low + "\"", false),
                new Vector("unpaired-high-key", "{\"" + high + "\":1}", false),
                new Vector("unpaired-low-key", "{\"" + low + "\":1}", false));
        List<String> observations = new ArrayList<>();
        for (Vector vector : vectors) {
            byte[] raw = utf8(envelope(vector.payload()));
            byte[] firstEncoding = null;
            for (int pass = 0; pass < 2; pass++) {
                String label = vector.name() + "/pass" + pass;
                final byte[] currentRaw = raw;
                final OldDecoded expected;
                try {
                    expected = oldDecode(currentRaw);
                } catch (RuntimeException originalFailure) {
                    sameFailure(originalFailure, () -> DriverStateSnapshot.decodeComplete(currentRaw), label);
                    observations.add(label + ":decode-rejected");
                    break;
                }
                Complete actual = DriverStateSnapshot.decodeComplete(currentRaw);
                final byte[] expectedEncoding;
                try {
                    expectedEncoding = expected.encode();
                } catch (RuntimeException originalFailure) {
                    sameFailure(originalFailure, actual::encode, label);
                    observations.add(label + ":encode-rejected");
                    break;
                }
                assertArrayEquals(expectedEncoding, actual.encode(), label);
                if (pass == 1 && vector.stable()) {
                    assertArrayEquals(firstEncoding, expectedEncoding, label + " finite original idempotence");
                }
                if (pass == 0) { firstEncoding = expectedEncoding; }
                observations.add(label + ":encoded");
                raw = expectedEncoding;
            }
        }
        System.out.println("353 original-pipeline observations: " + observations);
    }

    @Test
    void decoderSuccessAndLateFailureCannotTrustLaterPublicConstructorsOrDifferentRaw() {
        String valid = envelope("{\"opaque\":-0.020e+999}");
        Complete decoded = DriverStateSnapshot.decodeComplete(utf8(valid));
        strictPublicIngress(decoded);
        List<String> lateFailures = List.of(
                valid.replace("\"command_history\":[{\"index\":1,\"payload\":{\"opaque\":-0.020e+999}}]",
                        "\"command_history\":[{\"index\":1},{\"index\":2.0}]"),
                valid.replace(",\"campaign_goal\":{\"opaque\":-0.020e+999}", ""),
                valid.replace("\"index\":1", "\"index\":2"));
        for (String invalid : lateFailures) {
            RuntimeException original = assertThrows(RuntimeException.class, () -> oldDecode(utf8(invalid)));
            sameFailure(original, () -> DriverStateSnapshot.decodeComplete(utf8(invalid)), "late decoder failure");
            strictPublicIngress(decoded);
            Complete different = DriverStateSnapshot.decodeComplete(utf8(envelope("[]")));
            assertArrayEquals(utf8("[]"), ((Value) different.campaignGoal()).json());
        }

        byte[] sameCallerArray = utf8(envelope("false"));
        DriverStateSnapshot.decodeComplete(sameCallerArray);
        int indexDigit = envelope("false").indexOf("\"index\":1") + "\"index\":".length();
        assertEquals((byte) '1', sameCallerArray[indexDigit]);
        sameCallerArray[indexDigit] = (byte) '2';
        assertThrows(IllegalArgumentException.class, () -> DriverStateSnapshot.decodeComplete(sameCallerArray));
        sameCallerArray[indexDigit] = (byte) '1';
        assertEquals(1L, DriverStateSnapshot.decodeComplete(sameCallerArray).commandHistory().getFirst().index());
        strictPublicIngress(decoded);
    }

    @Test
    void decodedAndPublicMaterialStayDetachedAndKeepMissingNullAndEmptyDistinct() {
        byte[] caller = utf8(envelope("false"));
        byte[] expected = oldDecode(caller).encode();
        Complete decoded = DriverStateSnapshot.decodeComplete(caller);
        Value decodedRow = decoded.commandHistory().getFirst().originalRow();
        byte[] getter = decodedRow.json();
        byte[] otherGetter = decodedRow.json();
        assertNotSame(getter, otherGetter);
        Value equal = new Value(otherGetter);
        int oldHash = decodedRow.hashCode();
        Arrays.fill(caller, (byte) '!');
        Arrays.fill(getter, (byte) '!');
        assertEquals(equal, decodedRow);
        assertEquals(oldHash, decodedRow.hashCode());
        assertArrayEquals(otherGetter, decodedRow.json());
        assertArrayEquals(expected, decoded.encode());
        byte[] encoded = decoded.encode();
        Arrays.fill(encoded, (byte) '!');
        assertArrayEquals(expected, decoded.encode());

        byte[] publicInput = utf8("{\"index\":1,\"empty\":[]}");
        Value publicValue = new Value(publicInput);
        byte[] retained = publicValue.json();
        Arrays.fill(publicInput, (byte) '!');
        Arrays.fill(publicValue.json(), (byte) '!');
        assertArrayEquals(retained, publicValue.json());
        ArrayList<HistoryEntry> callerHistory = new ArrayList<>(List.of(new HistoryEntry(1, publicValue)));
        Complete copy = new Complete(decoded.session(), callerHistory, decoded.lastCheckpoint(),
                decoded.rollbackWarFailure(), decoded.managedRestoreTransaction(), decoded.successionExpectation(),
                new NullValue(), decoded.campaignGoal(), new Missing());
        callerHistory.clear();
        assertEquals(1, copy.commandHistory().size());
        assertThrows(UnsupportedOperationException.class, () -> copy.commandHistory().clear());
        assertInstanceOf(Missing.class, decoded.successionLifecycle());
        assertInstanceOf(Missing.class, decoded.rollbackWarFailures());
        assertInstanceOf(NullValue.class, decoded.rollbackWarFailure());
        assertArrayEquals(utf8("{}"), ((Value) decoded.lastCheckpoint()).json());
        assertArrayEquals(utf8("[]"), ((Value) decoded.managedRestoreTransaction()).json());
        assertArrayEquals(utf8("\"\""), ((Value) decoded.successionExpectation()).json());
        Complete withNull = DriverStateSnapshot.decodeComplete(copy.encode());
        assertInstanceOf(NullValue.class, withNull.successionLifecycle());
        assertInstanceOf(Missing.class, withNull.rollbackWarFailures());
        assertThrows(IllegalArgumentException.class, () -> new Value(utf8("null")));
        assertThrows(IllegalArgumentException.class, () -> new Complete(decoded.session(), List.of(),
                new Missing(), new NullValue(), new NullValue(), new NullValue(), new Missing(),
                new NullValue(), new Missing()));
    }

    private static void strictPublicIngress(Complete decoded) {
        Value original = decoded.commandHistory().getFirst().originalRow();
        assertThrows(IllegalArgumentException.class, () -> new HistoryEntry(99, original));
        assertThrows(IllegalArgumentException.class, () -> new HistoryEntry(1, new Value(utf8("{\"index\":1.0}"))));
        assertThrows(IllegalArgumentException.class, () -> new Value(utf8("null")));
        assertThrows(IllegalArgumentException.class, () -> new Value(utf8("{\"z\":0,\"z\":1}")));
        assertThrows(IllegalArgumentException.class, () -> new Value(new byte[] {(byte) 0xc3, 0x28}));
        HistoryEntry second = new HistoryEntry(2, new Value(utf8("{\"index\":2}")));
        assertThrows(IllegalArgumentException.class, () -> new Complete(decoded.session(), List.of(second),
                new NullValue(), new NullValue(), new NullValue(), new NullValue(), new Missing(),
                new NullValue(), new Missing()));
        assertThrows(IllegalArgumentException.class, () -> new Complete(decoded.session(), List.of(),
                new NullValue(), new NullValue(), new NullValue(), new Missing(), new Missing(),
                new NullValue(), new Missing()));
    }

    /* Frozen 339 pipeline, using only unchanged public raw JSON operations. In particular,
       Value normalization and HistoryEntry's subsequent reparse remain separate here. */
    private static OldDecoded oldDecode(byte[] raw) {
        ObjectNode root = object(parse(raw));
        root.fieldNames().forEachRemaining(key -> StrictJson.require(ALLOWED.contains(key), "unmigrated top-level Driver field: " + key));
        StrictJson.integer(root.get("format_version"), 2, 2);
        StrictJson.require(root.get("command_history") != null && root.get("command_history").isArray(), "full Driver history required");
        List<OldRow> rows = new ArrayList<>();
        for (JsonNode item : root.get("command_history")) {
            ObjectNode original = object(item);
            long index = StrictJson.integer(original.get("index"), 1, StrictJson.MAX_SAFE_INTEGER);
            byte[] normalized = oldValue(bytes(original));
            StrictJson.safe(index, 1);
            ObjectNode rechecked = object(parse(normalized));
            StrictJson.require(StrictJson.integer(rechecked.get("index"), 1, StrictJson.MAX_SAFE_INTEGER) == index,
                    "history entry typed index equals original integer token");
            rows.add(new OldRow(index, normalized));
        }
        Session session = new Session(StrictJson.text(root.get("pipe_name")),
                StrictJson.integer(root.get("bridge_pid"), 1, 0xffff_ffffL),
                NativeCharacterId.fromJson(root.get("episode_character_id")).asBigInteger(),
                StrictJson.text(root.get("episode_run_id")));
        Map<String, byte[]> slots = new LinkedHashMap<>();
        for (String key : SLOT_NAMES) {
            if (root.has(key)) {
                JsonNode node = root.get(key);
                slots.put(key, node.isNull() ? null : oldValue(bytes(node)));
            }
        }
        for (int index = 0; index < rows.size(); index++) {
            StrictJson.require(rows.get(index).index() == index + 1L, "complete ordered Driver history");
        }
        StrictJson.require(slots.keySet().containsAll(REQUIRED), "required original Driver fields may be null, never absent");
        return new OldDecoded(session, rows, slots);
    }

    private record OldRow(long index, byte[] material) { }

    private record OldDecoded(Session session, List<OldRow> rows, Map<String, byte[]> slots) {
        byte[] encode() {
            ObjectNode root = JsonNodeFactory.instance.objectNode();
            root.put("format_version", 2);
            root.put("pipe_name", session.pipeName());
            root.put("bridge_pid", session.bridgePid());
            root.put("episode_character_id", session.actorId());
            root.put("episode_run_id", session.episodeRunId());
            var history = root.putArray("command_history");
            rows.forEach(row -> history.add(parse(row.material())));
            for (String key : SLOT_NAMES) {
                if (slots.containsKey(key)) {
                    byte[] material = slots.get(key);
                    if (material == null) { root.putNull(key); }
                    else { root.set(key, parse(material)); }
                }
            }
            return bytes(root);
        }
    }

    private record Vector(String name, String payload, boolean stable) { }

    private static byte[] oldValue(byte[] raw) {
        JsonNode node = parse(raw);
        StrictJson.require(!node.isNull(), "null has its own explicit Driver slot");
        return bytes(node);
    }

    private static void sameFailure(RuntimeException expected, Executable operation, String label) {
        RuntimeException actual = assertThrows(RuntimeException.class, operation, label);
        assertEquals(expected.getClass(), actual.getClass(), label + " exception class");
        assertEquals(expected.getMessage(), actual.getMessage(), label + " first failure");
        Throwable expectedCause = expected.getCause();
        Throwable actualCause = actual.getCause();
        while (expectedCause != null || actualCause != null) {
            assertEquals(expectedCause == null ? null : expectedCause.getClass(),
                    actualCause == null ? null : actualCause.getClass(), label + " cause class");
            expectedCause = expectedCause == null ? null : expectedCause.getCause();
            actualCause = actualCause == null ? null : actualCause.getCause();
        }
    }

    private static String envelope(String payload) {
        return "{\"format_version\":2,\"pipe_name\":\"normalization-353-pipe\",\"bridge_pid\":7,"
                + "\"episode_character_id\":-2,\"episode_run_id\":\"normalization-353-episode\","
                + "\"command_history\":[{\"index\":1,\"payload\":" + payload + "}],"
                + "\"last_checkpoint\":{},\"rollback_war_failure\":null,\"managed_restore_transaction\":[],"
                + "\"succession_expectation\":\"\",\"campaign_goal\":" + payload + "}";
    }

    private static JsonNode parse(byte[] raw) { return FullJsonTree.parse(raw, DriverCheckpointStore.MAX_DRIVER_BYTES); }
    private static byte[] bytes(JsonNode node) { return FullJsonTree.encode(node, DriverCheckpointStore.MAX_DRIVER_BYTES); }
    private static ObjectNode object(JsonNode node) {
        StrictJson.require(node instanceof ObjectNode, "Driver object required");
        return (ObjectNode) node;
    }
    private static byte[] utf8(String text) { return text.getBytes(StandardCharsets.UTF_8); }
}
