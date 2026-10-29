package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.NestedQuantitySum12004.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.UInt64;
import org.xar.ck3.control.nativebridge.capabilities.army.LocalTargetScore12004.Scope;

/** Requires a fresh C++ production-reader artifact. No missing-input skip or Java-authored wire. */
final class NestedQuantitySum12004ProducerTest {
    private static Map<String,ObjectNode> actualCases() throws Exception {
        String file = System.getProperty("xar.nestedQuantity12004.nativeWire");
        String sha = System.getProperty("xar.nestedQuantity12004.nativeWireSha256");
        String machine = System.getProperty("xar.nestedQuantity12004.machineId");
        assertNotNull(file); assertNotNull(sha); assertNotNull(machine); assertFalse(machine.isBlank()); assertTrue(sha.matches("[0-9a-f]{64}"));
        Path path = Path.of(file); assertTrue(path.isAbsolute() && Files.isRegularFile(path));
        long size = Files.size(path); assertTrue(size > 0 && size <= 1_048_576); byte[] wire = Files.readAllBytes(path);
        assertEquals(size, wire.length); assertEquals(sha, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(wire)));
        ObjectNode root = closed(parse(wire), "schema_version", "machine_id", "observed_at_utc", "proof_layer", "original_native_executions", "actual_game", "cases");
        assertEquals(1, i32(root.get("schema_version"))); assertEquals(machine, text(root.get("machine_id")));
        assertNotNull(Instant.parse(text(root.get("observed_at_utc"))));
        assertEquals("owned_immutable_nested_quantity_reader_serializer_only", text(root.get("proof_layer")));
        assertEquals(0, i32(root.get("original_native_executions"))); assertFalse(bool(root.get("actual_game")));
        Map<String,ObjectNode> cases = new LinkedHashMap<>();
        for (ObjectNode row : array(root.get("cases"), value -> closed(value, "name", "observation")))
            assertNull(cases.put(text(row.get("name")), object(row.get("observation"))));
        assertEquals(Set.of("empty_helper", "one_selected", "signature_skip", "invalid_id_skip", "mixed_overflow", "negative_amount",
                "manager_null_fallback", "index_out_of_range_fallback", "null_slot_fallback", "id_mismatch_fallback", "missing_helper",
                "count_bound", "selected_changed", "wrong_flags", "returned_address_changed", "reload_missing", "source_handle_missing", "output_mismatch"), cases.keySet());
        return cases;
    }
    @Test void realNativeProducerToNestedConsumerAndStrictRoundTrip() throws Exception {
        Map<String,Long> expected = Map.of("empty_helper", 0L, "one_selected", 9L, "signature_skip", 0L, "invalid_id_skip", 0L,
                "mixed_overflow", Long.MIN_VALUE, "negative_amount", Long.MIN_VALUE, "manager_null_fallback", 4L,
                "index_out_of_range_fallback", 4L, "null_slot_fallback", 4L, "id_mismatch_fallback", 4L);
        for (var row : actualCases().entrySet()) {
            Observation observation = decode(bytes(row.getValue())); assertEquals(observation, decode(encode(observation)), row.getKey());
            assertEquals("9007199254740993", observation.scope().connectionGeneration());
            if (observation instanceof Available available) {
                Result result = consume(observation.scope(), available.facts().originalFold().originalOutput().call(), observation);
                if (row.getKey().equals("output_mismatch")) assertEquals(new NotReady("nested_quantity_original_output_mismatch"), result);
                else {
                    VerifiedNestedRawSum verified = assertInstanceOf(VerifiedNestedRawSum.class, result);
                    assertEquals(expected.get(row.getKey()).longValue(), verified.fold().raw()); assertEquals(1, verified.helperCount());
                    Helper helper = available.facts().helpers().getFirst(); assertTrue(helper.outputAddress().value().compareTo(BigInteger.ONE.shiftLeft(53)) > 0);
                    if (row.getKey().equals("empty_helper")) { assertEquals(0, verified.selectedCount()); assertTrue(helper.databaseIdentity().isEmpty()); }
                    if (row.getKey().equals("manager_null_fallback")) {
                        assertEquals(BigInteger.ZERO, helper.databaseIdentity().orElseThrow().value()); assertTrue(helper.members().getFirst().sourceHandleRaw().isEmpty());
                    }
                    if (row.getKey().equals("signature_skip")) assertTrue(helper.members().getFirst().selectedFullIdRaw().isEmpty());
                    if (row.getKey().equals("mixed_overflow")) { assertEquals(2, verified.selectedCount()); assertEquals(2, verified.contributingCount()); }
                }
            } else assertInstanceOf(Incomplete.class, observation);
        }
    }
    @Test void changedScopeOrOriginalOccurrenceAndMissingViewsNeverReuseAnAmount() throws Exception {
        Map<String,ObjectNode> cases = actualCases(); Available read = assertInstanceOf(Available.class, decode(bytes(cases.get("one_selected"))));
        Scope scope = read.scope(); OriginalQuantity12004.CallKey key = read.facts().originalFold().originalOutput().call();
        for (ObjectNode row : cases.values()) {
            Observation observation = decode(bytes(row));
            if (observation instanceof Incomplete missing) assertEquals(new NotReady(missing.reason()), consume(scope, key, missing));
        }
        Scope next = new Scope(scope.episode(), scope.connectionGeneration(), scope.nativeRevision(), scope.coordinatorIdentity(), "8", scope.dateRaw(), scope.exeSha256());
        assertEquals(new NotReady("nested_quantity_update_or_source_changed"), consume(next, key, read));
        OriginalQuantity12004.CallKey other = new OriginalQuantity12004.CallKey(key.moduleBaseIdentity(), key.outerSlotIdentity(),
                UInt64.positive(key.innerSlotIdentity().value().add(BigInteger.valueOf(8))), key.unitOperandIdentity(), key.outputAddress());
        assertEquals(new NotReady("quantity_original_occurrence_changed"), consume(scope, other, read));
    }
    private static void rejects(ObjectNode original, Consumer<ObjectNode> mutation) {
        ObjectNode changed = original.deepCopy(); mutation.accept(changed);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(changed)));
    }
    private static ObjectNode helper(ObjectNode root) { return object(root.path("facts").path("helpers").get(0)); }
    private static ObjectNode member(ObjectNode root) { return object(helper(root).path("members").get(0)); }
    @Test void rejectsWrongTypesMissingFieldsAndUnreachedData() throws Exception {
        Map<String,ObjectNode> cases = actualCases(); ObjectNode base = cases.get("one_selected");
        rejects(base, n -> helper(n).put("entry_flags_raw", true));
        rejects(base, n -> helper(n).put("entry_flags_raw", 1));
        rejects(base, n -> helper(n).put("signed_count_raw", 1.0));
        rejects(base, n -> helper(n).put("signed_count_raw", 65537));
        rejects(base, n -> helper(n).putNull("database_identity"));
        rejects(base, n -> helper(n).put("output_address", "09007199254741000"));
        rejects(base, n -> helper(n).put("output_address", 1L));
        rejects(base, n -> helper(n).put("parent_ordinal", 1));
        rejects(base, n -> member(n).put("source_handle_raw", true));
        rejects(base, n -> member(n).putNull("selected_full_id_raw"));
        rejects(base, n -> member(n).put("amount_raw", 9L));
        rejects(base, n -> member(n).remove("amount_raw"));
        rejects(base, n -> member(n).put("business_unit", "soldiers"));
        rejects(base, n -> n.put("entry_rva", ENTRY_RVA + 1));
        rejects(cases.get("signature_skip"), n -> member(n).put("selected_full_id_raw", 1));
        rejects(cases.get("manager_null_fallback"), n -> member(n).put("source_handle_raw", 0));
        rejects(cases.get("empty_helper"), n -> helper(n).put("database_identity", "0"));
    }
}
