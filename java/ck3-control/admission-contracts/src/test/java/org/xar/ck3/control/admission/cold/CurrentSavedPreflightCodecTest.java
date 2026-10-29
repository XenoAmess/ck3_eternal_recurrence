package org.xar.ck3.control.admission.cold;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

final class CurrentSavedPreflightCodecTest {
    private static ObjectNode golden() throws IOException {
        try (InputStream stream = CurrentSavedPreflightCodecTest.class.getResourceAsStream("/cold/preflight-golden.json")) {
            if (stream == null) { throw new IOException("original producer golden is required, never skipped"); }
            return (ObjectNode) StrictJson.parse(stream.readAllBytes(), CurrentSavedPreflightCodec.RECEIPT_MAX_BYTES);
        }
    }

    private static ObjectNode fixture() throws IOException {
        return (ObjectNode) golden().get("preflight").get("wire").deepCopy();
    }

    private static CurrentSavedPreflightContract parse(JsonNode value) {
        return CurrentSavedPreflightCodec.parse(value, PathFlavor.WINDOWS);
    }

    @Test void originalProducerRoundTripAndQualificationScope() throws IOException {
        ObjectNode corpus = golden();
        ObjectNode wire = (ObjectNode) corpus.get("preflight").get("wire");
        CurrentSavedPreflightContract model = parse(wire);
        byte[] encoded = CurrentSavedPreflightCodec.encode(model);
        assertArrayEquals(corpus.get("preflight").get("canonical_json").textValue().getBytes(StandardCharsets.UTF_8), encoded);
        // Compare the exact JSON integer domain rather than Jackson's integer node widths.
        assertArrayEquals(StrictJson.canonical(wire),
                StrictJson.canonical(CurrentSavedPreflightCodec.toJson(model)));
        assertEquals(model, CurrentSavedPreflightCodec.decode(encoded, PathFlavor.WINDOWS));
        assertFalse(model.grantsFreshReadiness()); assertFalse(model.grantsWarmBinding());
        assertFalse(model.grantsFullLoop()); assertFalse(model.grantsReducerOrRecoveryQualification());
        assertEquals(CurrentSavedPreflightContract.ValidationScope.OFFLINE_RECEIPT_SHAPE_AND_BINDING_COMPARISON,
                model.validationScope());
        assertThrows(UnsupportedOperationException.class, () -> model.runtimeSourceRefs().clear());
    }

    @Test void everyRequiredFieldRejectsMissingAndNull() throws IOException {
        ObjectNode original = fixture();
        List<String> names = new ArrayList<>(); original.fieldNames().forEachRemaining(names::add);
        for (String name : names) {
            ObjectNode missing = original.deepCopy(); missing.remove(name);
            assertThrows(ContractViolationException.class, () -> parse(missing), "missing " + name);
            ObjectNode nullable = original.deepCopy(); nullable.putNull(name);
            assertThrows(ContractViolationException.class, () -> parse(nullable), "null " + name);
        }
        ObjectNode extra = original.deepCopy(); extra.putNull("unknown_field");
        assertThrows(ContractViolationException.class, () -> parse(extra));
        for (JsonNode wrongRoot : List.of(StrictJson.parse("null".getBytes(StandardCharsets.UTF_8)),
                StrictJson.parse("[]".getBytes(StandardCharsets.UTF_8)), StrictJson.parse("true".getBytes(StandardCharsets.UTF_8)))) {
            assertThrows(ContractViolationException.class, () -> parse(wrongRoot));
        }
    }

    @Test void numericAndBooleanTokenDomainsRemainExact() throws IOException {
        for (String field : List.of("current_next_sequence", "files_verified", "canonical_entry_count", "closure_count",
                "ordinary_cycle_credit", "game_day_credit")) {
            for (String value : List.of("true", "1.0", "\"1\"", "null", "-1", "9007199254740992")) {
                ObjectNode wire = fixture(); wire.set(field, StrictJson.parse(value.getBytes(StandardCharsets.UTF_8)));
                assertThrows(ContractViolationException.class, () -> parse(wire), field + "=" + value);
            }
        }
        for (String field : List.of("read_only_game_start_permitted", "full_loop_permitted", "original_actions_replayed",
                "live_semantic_accepted", "live_warm_bound")) {
            for (String value : List.of("1", "0", "1.0", "\"false\"", "null")) {
                ObjectNode wire = fixture(); wire.set(field, StrictJson.parse(value.getBytes(StandardCharsets.UTF_8)));
                assertThrows(ContractViolationException.class, () -> parse(wire), field + "=" + value);
            }
            ObjectNode inverse = fixture(); inverse.put(field, !inverse.get(field).booleanValue());
            assertThrows(ContractViolationException.class, () -> parse(inverse));
        }
        ObjectNode max = fixture(); max.put("current_next_sequence", StrictJson.MAX_SAFE_INTEGER);
        max.put("files_verified", StrictJson.MAX_SAFE_INTEGER); assertEquals(StrictJson.MAX_SAFE_INTEGER, parse(max).filesVerified());
    }

    @Test void historicalReplayRetainsStrictSourceAndZeroCreditScope() throws IOException {
        ObjectNode baseline = (ObjectNode) fixture().get("historical_replay");
        List<String> fields = new ArrayList<>(); baseline.fieldNames().forEachRemaining(fields::add);
        for (String field : fields) {
            ObjectNode missing = baseline.deepCopy(); missing.remove(field);
            assertThrows(ContractViolationException.class, () -> CurrentSavedPreflightCodec.parseHistorical(missing));
            ObjectNode nullable = baseline.deepCopy(); nullable.putNull(field);
            assertThrows(ContractViolationException.class, () -> CurrentSavedPreflightCodec.parseHistorical(nullable));
        }
        for (String field : List.of("actual_rpc_calls", "canonical_score_writes")) {
            ObjectNode credit = baseline.deepCopy(); credit.put(field, 1);
            assertThrows(ContractViolationException.class, () -> CurrentSavedPreflightCodec.parseHistorical(credit));
            credit.put(field, false);
            assertThrows(ContractViolationException.class, () -> CurrentSavedPreflightCodec.parseHistorical(credit));
        }
        ObjectNode altered = baseline.deepCopy(); altered.put("check_after_ast_sha256", "A".repeat(64));
        assertThrows(ContractViolationException.class, () -> CurrentSavedPreflightCodec.parseHistorical(altered));
        ObjectNode wire = fixture();
        ((ObjectNode) wire.get("historical_replay")).put("historical_sequence", wire.get("current_next_sequence").longValue());
        assertThrows(ContractViolationException.class, () -> parse(wire));
    }

    @Test void sourcePinsAndClosureAcceptExactlyTheCurrentEightToSixtySevenBoundary() throws IOException {
        ObjectNode wire = fixture();
        ObjectNode ref = (ObjectNode) wire.get("core_source_ref");
        ObjectNode zeroSized = fixture();
        ((ObjectNode) zeroSized.get("plan_ref")).put("bytes", 0);
        assertEquals(0, parse(zeroSized).planRef().bytes(), "current basis refs allow zero; A17 differs");
        ArrayNode sources = wire.putArray("runtime_source_refs");
        for (int i = 0; i < 67; i++) {
            ObjectNode item = ref.deepCopy(); item.put("path", "D:/fixture/source-" + i + ".py"); sources.add(item);
        }
        wire.put("closure_count", 67); assertEquals(67, parse(wire).runtimeSourceRefs().size());
        ObjectNode duplicate = wire.deepCopy();
        ((ArrayNode) duplicate.get("runtime_source_refs")).set(1, duplicate.get("runtime_source_refs").get(0).deepCopy());
        assertThrows(ContractViolationException.class, () -> parse(duplicate));
        sources.add(ref.deepCopy()); assertThrows(ContractViolationException.class, () -> parse(wire));
        sources.remove(sources.size() - 1);
        wire.put("closure_count", 68); assertThrows(ContractViolationException.class, () -> parse(wire));
        wire.put("closure_count", 67);
        while (sources.size() > 7) { sources.remove(sources.size() - 1); }
        assertThrows(ContractViolationException.class, () -> parse(wire));
    }

    @Test void revalidationIgnoresOnlyObservationTimeAndKeepsSourceOrderAndDigest() throws IOException {
        ObjectNode original = fixture(); CurrentSavedPreflightContract sealed = parse(original);
        ObjectNode later = original.deepCopy(); later.put("observed_at_utc", "2026-10-22T23:59:59Z");
        assertTrue(CurrentSavedPreflightCodec.sameRevalidatedBinding(sealed, parse(later)));
        for (String field : List.of("machine_id", "attempt_nonce", "task_nonce", "runtime_root")) {
            ObjectNode different = original.deepCopy();
            different.put(field, field.endsWith("nonce") ? "e".repeat(32) : original.get(field).textValue() + "x");
            assertFalse(CurrentSavedPreflightCodec.sameRevalidatedBinding(sealed, parse(different)), field);
        }
        ObjectNode digest = original.deepCopy();
        ((ObjectNode) digest.get("plan_ref")).put("sha256", "f".repeat(64));
        assertFalse(CurrentSavedPreflightCodec.sameRevalidatedBinding(sealed, parse(digest)));
        ObjectNode reordered = original.deepCopy(); ArrayNode array = (ArrayNode) reordered.get("runtime_source_refs");
        JsonNode first = array.get(0); array.set(0, array.get(1)); array.set(1, first);
        assertFalse(CurrentSavedPreflightCodec.sameRevalidatedBinding(sealed, parse(reordered)));
    }

    @Test void validReceiptAboveMapLimitUsesExplicitPreflightBudget() throws IOException {
        ObjectNode wire = fixture(); ObjectNode ref = (ObjectNode) wire.get("core_source_ref");
        ArrayNode refs = wire.putArray("runtime_source_refs");
        for (int i = 0; i < 67; i++) {
            ObjectNode item = ref.deepCopy(); item.put("path", "D:/" + "x".repeat(1100) + "/" + i); refs.add(item);
        }
        CurrentSavedPreflightContract model = parse(wire);
        byte[] encoded = CurrentSavedPreflightCodec.encode(model);
        assertTrue(encoded.length > StrictJson.INPUT_MAX_BYTES);
        assertEquals(model, CurrentSavedPreflightCodec.decode(encoded, PathFlavor.WINDOWS));
        assertThrows(ContractViolationException.class, () -> StrictJson.parse(encoded));
        byte[] over = new byte[CurrentSavedPreflightCodec.RECEIPT_MAX_BYTES + 1];
        assertThrows(ContractViolationException.class, () -> CurrentSavedPreflightCodec.decode(over, PathFlavor.WINDOWS));
    }

    @Test void duplicateKeysMalformedUtf8AndTrailingValuesAreRejected() throws IOException {
        String wire = new String(CurrentSavedPreflightCodec.encode(parse(fixture())), StandardCharsets.UTF_8);
        String duplicate = wire.substring(0, wire.length() - 1) + ",\"closure_count\":67}";
        assertThrows(ContractViolationException.class, () -> CurrentSavedPreflightCodec.decode(duplicate.getBytes(StandardCharsets.UTF_8), PathFlavor.WINDOWS));
        assertThrows(ContractViolationException.class, () -> CurrentSavedPreflightCodec.decode((wire + "{}").getBytes(StandardCharsets.UTF_8), PathFlavor.WINDOWS));
        assertThrows(ContractViolationException.class, () -> CurrentSavedPreflightCodec.decode(new byte[] {(byte) 0xff}, PathFlavor.WINDOWS));
    }
}
