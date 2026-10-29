package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.PairTargetScoreTerminal12004.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.OptionalInt;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.UInt64;
import org.xar.ck3.control.nativebridge.capabilities.army.LocalTargetScore12004.Scope;

/** Actual retained original instructions -> captured-operand producer -> strict Java stage. No synthetic fallback. */
final class PairTargetScoreTerminal12004ProducerTest {
    private enum Expected { APPEND_OPERANDS, INCOMPLETE, SCORE_MISMATCH }
    private record Case(Observation observation, OptionalInt nativeScore, Expected expected, ObjectNode original) { }
    private static Map<String,Case> cases() throws Exception {
        String file = System.getProperty("xar.pairScoreTerminal12004.nativeWire");
        String hash = System.getProperty("xar.pairScoreTerminal12004.nativeWireSha256");
        assertNotNull(file, "Root fresh standalone original terminal file required");
        assertNotNull(hash, "fresh terminal producer SHA required"); assertTrue(hash.matches("[0-9a-f]{64}"));
        Path path = Path.of(file); assertTrue(path.isAbsolute() && Files.isRegularFile(path));
        long size = Files.size(path); assertTrue(size > 0 && size <= 8 * 1024 * 1024);
        byte[] raw = Files.readAllBytes(path); assertEquals(size, raw.length);
        assertEquals(hash, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
        ObjectNode root = closed(parse(raw), "schema", "machine_id", "observed_at_utc", "actual_game_execution", "exe_sha256",
            "original_terminal_sha256", "owned_wrapper_sha256", "actual_native_executions", "cases", "negative_cases");
        assertEquals("xar.ck3.pair-target-score-terminal-fixture/v1", text(root.get("schema")));
        assertFalse(bool(root.get("actual_game_execution"))); assertEquals(LocalTargetScore12004.EXE_SHA256, text(root.get("exe_sha256")));
        assertTrue(text(root.get("machine_id")).matches("[a-z0-9-]{1,128}")); assertNotEquals("unknown", text(root.get("machine_id")));
        java.time.Instant.parse(text(root.get("observed_at_utc")));
        assertEquals("2976c2bcb5c5b08729685e20e95972bf68a69355c7288baa6e06a459fd2cea01", text(root.get("original_terminal_sha256")));
        assertEquals("1c2c8fd4f699a3dc0757e494fa3c5ce964cf165e3412a4bc2f12f451634cd07b", text(root.get("owned_wrapper_sha256")));
        assertEquals(21, i32(root.get("actual_native_executions")));
        Map<String,Case> all = new LinkedHashMap<>();
        for (ObjectNode row : array(root.get("cases"), v -> closed(v, "name", "observation", "native_result"))) {
            ObjectNode original = object(row.get("observation")); Observation observation = decode(bytes(original));
            assertInstanceOf(Available.class, observation);
            assertNull(all.put(text(row.get("name")), new Case(observation, OptionalInt.of(i32(row.get("native_result"))), Expected.APPEND_OPERANDS, original)));
        }
        for (ObjectNode row : array(root.get("negative_cases"), v -> closed(v, "name", "expected", "observation"))) {
            Expected expected = switch (text(row.get("expected"))) {
                case "incomplete" -> Expected.INCOMPLETE; case "not_ready" -> Expected.SCORE_MISMATCH;
                default -> throw new IllegalArgumentException("unknown negative expectation");
            };
            ObjectNode original = object(row.get("observation")); Observation observation = decode(bytes(original));
            assertEquals(expected == Expected.SCORE_MISMATCH, observation instanceof Available);
            assertNull(all.put(text(row.get("name")), new Case(observation, OptionalInt.empty(), expected, original)));
        }
        assertEquals(Set.of("min", "min_plus_one", "negative_int_wrap", "negative_int_edge", "negative_int_exact", "negative_fraction_below", "negative_exact",
            "negative_fraction_above", "negative_one", "zero", "one", "positive_fraction", "positive_exact", "positive_fraction_above", "int_max", "int_wrap",
            "last_positive_no_wrap", "first_positive_wrap", "max_minus_one", "max", "positive_half", "missing_frame", "missing_operand", "wrong_caller", "wrong_coordinator", "score_argument_mismatch"), all.keySet());
        return all;
    }
    @Test void originalTerminalToActualOperandsConsumerAndRoundTrip() throws Exception {
        Map<String,Case> all = cases(); PairKey fallback = ((Available) all.get("zero").observation()).facts().pair();
        for (var entry : all.entrySet()) {
            Case c = entry.getValue(); Observation observation = c.observation();
            assertEquals(observation, decode(encode(observation)), entry.getKey());
            PairKey key = observation instanceof Available ready ? ready.facts().pair() : fallback;
            Result result = consume(observation.scope(), key, observation);
            if (c.expected() == Expected.APPEND_OPERANDS) {
                ObservedAppendOperands append = assertInstanceOf(ObservedAppendOperands.class, result, entry.getKey());
                assertEquals(c.nativeScore().orElseThrow(), append.integerScore(), entry.getKey()); assertEquals(key, append.pair());
            } else assertInstanceOf(NotReady.class, result, entry.getKey());
        }
        Observation max = all.get("max").observation(); PairKey key = ((Available) max).facts().pair();
        ObservedAppendOperands result = assertInstanceOf(ObservedAppendOperands.class, consume(max.scope(), key, max));
        assertEquals(-9223372036854751616L, result.snappedRaw()); assertEquals(702313053, result.integerScore());
        assertNotEquals((int) (Long.MAX_VALUE / 100000 + 1), result.integerScore(), "second division after native multiplication wrap matters");
        Observation min = all.get("min").observation();
        assertEquals(702313053, assertInstanceOf(ObservedAppendOperands.class, consume(min.scope(), ((Available) min).facts().pair(), min)).integerScore());
        assertEquals(255, ((Available) all.get("positive_half").observation()).facts().pair().kindRaw());
    }
    @Test void sourceUpdateAndEveryOriginalPairOperandRemainBound() throws Exception {
        Observation observation = cases().get("positive_exact").observation(); Scope scope = observation.scope(); PairKey key = ((Available) observation).facts().pair();
        Scope changed = new Scope(scope.episode(), scope.connectionGeneration(), scope.nativeRevision(), scope.coordinatorIdentity(), "12", scope.dateRaw(), scope.exeSha256());
        assertEquals(new NotReady("coordinator_update_or_source_changed"), consume(changed, key, observation));
        UInt64 other = UInt64.positive(BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE));
        for (PairKey changedPair : new PairKey[]{
            new PairKey(other,key.stackObjectIdentity(),key.stackIndex(),key.provinceIdentity(),key.kindRaw(),key.reasonVectorIdentity()),
            new PairKey(key.stackEntryIdentity(),other,key.stackIndex(),key.provinceIdentity(),key.kindRaw(),key.reasonVectorIdentity()),
            new PairKey(key.stackEntryIdentity(),key.stackObjectIdentity(),key.stackIndex()+1,key.provinceIdentity(),key.kindRaw(),key.reasonVectorIdentity()),
            new PairKey(key.stackEntryIdentity(),key.stackObjectIdentity(),key.stackIndex(),other,key.kindRaw(),key.reasonVectorIdentity()),
            new PairKey(key.stackEntryIdentity(),key.stackObjectIdentity(),key.stackIndex(),key.provinceIdentity(),key.kindRaw()+1,key.reasonVectorIdentity()),
            new PairKey(key.stackEntryIdentity(),key.stackObjectIdentity(),key.stackIndex(),key.provinceIdentity(),key.kindRaw(),other)}) {
            assertEquals(new NotReady("original_pair_or_reason_source_changed"), consume(scope, changedPair, observation));
        }
    }
    @Test void strictBoundaryRejectsCoercionMissingAndInventedFields() throws Exception {
        ObjectNode original = cases().get("positive_exact").original();
        ObjectNode numeric = original.deepCopy(); object(numeric.get("facts")).put("original_rbx_raw",100000);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(numeric)));
        ObjectNode sign = original.deepCopy(); object(sign.get("facts")).put("original_rbx_raw","-0");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(sign)));
        ObjectNode leading = original.deepCopy(); object(leading.get("facts")).put("original_rbx_raw","0100000");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(leading)));
        ObjectNode overflow = original.deepCopy(); object(overflow.get("facts")).put("original_rbx_raw","9223372036854775808");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(overflow)));
        ObjectNode bool = original.deepCopy(); object(object(bool.get("facts")).get("pair")).put("stack_index",true);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(bool)));
        ObjectNode numberPointer = original.deepCopy(); object(object(numberPointer.get("facts")).get("pair")).put("province_identity",1);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(numberPointer)));
        ObjectNode pointerOverflow = original.deepCopy(); object(object(pointerOverflow.get("facts")).get("pair")).put("province_identity","18446744073709551616");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(pointerOverflow)));
        ObjectNode floating = original.deepCopy(); object(floating.get("facts")).put("original_score_argument",1.0);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(floating)));
        ObjectNode stage = original.deepCopy(); stage.put("stage_rva",APPEND_CALL_RVA+1);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(stage)));
        ObjectNode missing = original.deepCopy(); object(missing.get("facts")).remove("pair");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(missing)));
        ObjectNode missingNull = original.deepCopy(); missingNull.remove("reason");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(missingNull)));
        ObjectNode invented = original.deepCopy(); object(invented.get("facts")).put("win_probability",1);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(invented)));
    }
}
