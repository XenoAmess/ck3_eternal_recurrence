package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.QuantityFold12004.*;
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

/** Requires a new real C++ production reader/serializer artifact; missing input fails, never skips. */
final class QuantityFold12004ProducerTest {
    private static Map<String,ObjectNode> actualCases() throws Exception {
        String file = System.getProperty("xar.quantityFold12004.nativeWire");
        String sha = System.getProperty("xar.quantityFold12004.nativeWireSha256");
        String machine = System.getProperty("xar.quantityFold12004.machineId");
        assertNotNull(file); assertNotNull(sha); assertNotNull(machine); assertFalse(machine.isBlank()); assertTrue(sha.matches("[0-9a-f]{64}"));
        Path path = Path.of(file); assertTrue(path.isAbsolute() && Files.isRegularFile(path));
        long size = Files.size(path); assertTrue(size > 0 && size <= 1_048_576); byte[] original = Files.readAllBytes(path);
        assertEquals(size, original.length); assertEquals(sha, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        ObjectNode root = closed(parse(original), "schema_version", "machine_id", "observed_at_utc", "proof_layer", "original_native_executions", "actual_game", "cases");
        assertEquals(1, i32(root.get("schema_version"))); assertEquals(machine, text(root.get("machine_id")));
        assertNotNull(Instant.parse(text(root.get("observed_at_utc"))));
        assertEquals("owned_immutable_trace_reader_serializer_only", text(root.get("proof_layer")));
        assertEquals(0, i32(root.get("original_native_executions"))); assertFalse(bool(root.get("actual_game")));
        Map<String,ObjectNode> cases = new LinkedHashMap<>();
        for (ObjectNode row : array(root.get("cases"), value -> closed(value, "name", "observation")))
            assertNull(cases.put(text(row.get("name")), object(row.get("observation"))));
        assertEquals(Set.of("signature_zero", "matched_empty", "mixed_overflow", "negative_amount", "gate_missing", "member_missing",
                "skipped_call_present", "nested_call_missing", "return_snapshot_missing", "output_mismatch", "member_frame_changed", "signature_flags_changed"), cases.keySet());
        return cases;
    }
    @Test void realProducerToJavaFoldAndStrictRoundTrip() throws Exception {
        Map<String,Long> expected = Map.of("signature_zero", 0L, "matched_empty", 0L, "mixed_overflow", Long.MIN_VALUE, "negative_amount", Long.MIN_VALUE);
        for (var row : actualCases().entrySet()) {
            Observation read = decode(bytes(row.getValue())); assertEquals(read, decode(encode(read)), row.getKey());
            assertEquals("9007199254740993", read.scope().connectionGeneration());
            if (read instanceof Available available) {
                Result result = consume(read.scope(), available.facts().originalOutput().call(), read);
                if (row.getKey().equals("output_mismatch")) assertEquals(new NotReady("quantity_fold_original_output_mismatch"), result);
                else {
                    VerifiedRawFold folded = assertInstanceOf(VerifiedRawFold.class, result);
                    assertEquals(expected.get(row.getKey()).longValue(), folded.raw());
                    if (row.getKey().equals("mixed_overflow")) {
                        assertEquals(3, folded.memberCount()); assertEquals(2, folded.contributingCount());
                        assertEquals(Long.MAX_VALUE, available.facts().matchedMembers().orElseThrow().members().getFirst().amount().orElseThrow().raw());
                    }
                }
            } else assertInstanceOf(Incomplete.class, read);
        }
    }
    @Test void incompleteAndDifferentOccurrencesNeverReuseAnEarlierSum() throws Exception {
        Map<String,ObjectNode> cases = actualCases(); Available read = assertInstanceOf(Available.class, decode(bytes(cases.get("mixed_overflow"))));
        OriginalQuantity12004.CallKey key = read.facts().originalOutput().call(); Scope s = read.scope();
        for (ObjectNode value : cases.values()) {
            Observation missing = decode(bytes(value));
            if (missing instanceof Incomplete incomplete) assertEquals(new NotReady(incomplete.reason()), consume(missing.scope(), key, missing));
        }
        Scope next = new Scope(s.episode(), s.connectionGeneration(), s.nativeRevision(), s.coordinatorIdentity(), "8", s.dateRaw(), s.exeSha256());
        assertEquals(new NotReady("quantity_fold_update_or_source_changed"), consume(next, key, read));
        OriginalQuantity12004.CallKey other = new OriginalQuantity12004.CallKey(key.moduleBaseIdentity(), key.outerSlotIdentity(),
                UInt64.positive(key.innerSlotIdentity().value().add(BigInteger.valueOf(8))), key.unitOperandIdentity(), key.outputAddress());
        assertEquals(new NotReady("quantity_original_occurrence_changed"), consume(s, other, read));
    }
    private static void rejects(ObjectNode source, Consumer<ObjectNode> mutation) {
        ObjectNode altered = source.deepCopy(); mutation.accept(altered);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(altered)));
    }
    @Test void rejectsWrongTypesMissingFieldsAndUnreachedBranchInputs() throws Exception {
        Map<String,ObjectNode> cases = actualCases(); ObjectNode base = cases.get("mixed_overflow");
        rejects(base, n -> object(n.get("facts")).put("observed_signature_raw", true));
        rejects(base, n -> object(object(n.get("facts")).get("matched_members")).put("signed_count_raw", 3.0));
        rejects(base, n -> object(object(n.get("facts")).get("matched_members")).put("signed_count_raw", 2));
        rejects(base, n -> object(n.get("facts")).put("business_unit", "soldiers"));
        rejects(base, n -> object(n.get("facts")).remove("matched_members"));
        rejects(base, n -> n.put("nested_call_rva", NESTED_CALL_RVA + 1));
        rejects(base, n -> object(n.path("facts").path("matched_members").path("members").get(0)).put("ordinal", 1));
        rejects(base, n -> object(n.path("facts").path("matched_members").path("members").get(0)).put("primary_field18_raw", 1));
        rejects(base, n -> object(n.path("facts").path("matched_members").path("members").get(0).path("amount")).put("raw", 1L));
        rejects(base, n -> object(n.path("facts").path("matched_members").path("members").get(0).path("amount")).put("returned_address", 1L));
        rejects(base, n -> object(n.path("facts").path("matched_members").path("members").get(0).path("amount")).remove("raw"));
        rejects(cases.get("signature_zero"), n -> object(n.get("facts")).put("observed_signature_raw", SIGNATURE_RAW));
    }
}
