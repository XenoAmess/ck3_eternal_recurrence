package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.CoordinatorTimingCache12004.*;
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
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.UInt64;
import org.xar.ck3.control.nativebridge.capabilities.army.LocalTargetScore12004.Scope;

/** Requires original C++ production observer/serializer output, with no fabricated file or skip. */
final class CoordinatorTimingCache12004ProducerTest {
    private static Map<String,ObjectNode> actualCases() throws Exception {
        String file = System.getProperty("xar.coordinatorTiming12004.nativeWire");
        String sha = System.getProperty("xar.coordinatorTiming12004.nativeWireSha256");
        String machine = System.getProperty("xar.coordinatorTiming12004.machineId");
        assertNotNull(file, "run ck3_12004_coordinator_timing_cache_test first");
        assertNotNull(sha, "fresh producer SHA required"); assertNotNull(machine, "fresh execution machine ID required");
        assertTrue(sha.matches("[0-9a-f]{64}")); assertFalse(machine.isBlank());
        Path path = Path.of(file); assertTrue(path.isAbsolute() && Files.isRegularFile(path));
        long size = Files.size(path); assertTrue(size > 0 && size <= 1_048_576);
        byte[] original = Files.readAllBytes(path); assertEquals(size, original.length);
        assertEquals(sha, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        ObjectNode root = closed(parse(original), "schema_version", "machine_id", "observed_at_utc", "proof_layer",
                "original_native_executions", "actual_game", "cases");
        assertEquals(1, i32(root.get("schema_version"))); assertEquals(machine, text(root.get("machine_id")));
        assertNotNull(Instant.parse(text(root.get("observed_at_utc"))));
        assertEquals("owned_memory_reader_serializer_only", text(root.get("proof_layer")));
        assertEquals(0, i32(root.get("original_native_executions"))); assertFalse(bool(root.get("actual_game")));
        Map<String,ObjectNode> cases = new LinkedHashMap<>();
        for (ObjectNode raw : array(root.get("cases"), value -> closed(value, "name", "observation")))
            assertNull(cases.put(text(raw.get("name")), object(raw.get("observation"))));
        assertEquals(Set.of("mask_return_no_periodic_read", "negative_b0", "zero_b0", "pick_call", "not_periodic", "same_stamp",
                "changed_stamp", "negative_divisor", "divide_fault", "missing_frame", "wrong_caller", "wrong_coordinator",
                "missing_fields", "missing_divisor", "missing_stamp", "pointer_span_overflow"), cases.keySet());
        return cases;
    }
    private static Observation observation(Map<String,ObjectNode> cases, String name) { return decode(bytes(cases.get(name))); }
    private static UInt64 module(Observation observation) { return assertInstanceOf(Available.class, observation).inputs().moduleBaseIdentity(); }
    @Test void nativeProducerToTypedConsumerAndEveryFieldRoundTrip() throws Exception {
        Map<String,ObjectNode> cases = actualCases();
        Map<String,EntryBranch> expected = Map.of("mask_return_no_periodic_read", EntryBranch.FLAG_MASK_RETURNS,
                "negative_b0", EntryBranch.NEGATIVE_B0_SKIPS_DECREMENT, "zero_b0", EntryBranch.ZERO_B0_BECOMES_NEGATIVE,
                "pick_call", EntryBranch.PICK_CALLEE_REQUIRED, "not_periodic", EntryBranch.POSITIVE_B0_NOT_PERIODIC,
                "same_stamp", EntryBranch.PERIODIC_STAMP_UNCHANGED, "changed_stamp", EntryBranch.REBUILD_CALLEE_REQUIRED,
                "negative_divisor", EntryBranch.REBUILD_CALLEE_REQUIRED, "divide_fault", EntryBranch.ORIGINAL_DIVIDE_FAULT);
        for (var row : cases.entrySet()) {
            Observation read = decode(bytes(row.getValue())); assertEquals(read, decode(encode(read)), row.getKey());
            assertEquals("9007199254740993", read.scope().connectionGeneration());
            if (expected.containsKey(row.getKey())) {
                Available available = assertInstanceOf(Available.class, read); Inputs input = available.inputs();
                assertEquals(new BigInteger("18446744073709551615"), input.fields().cachedA8Raw().value());
                assertEquals(new BigInteger("9007199254740993"), input.fields().cachedB8Raw().value());
                assertEquals(Integer.MIN_VALUE, input.originalThirdRaw()); assertEquals(-13, input.fields().countdownC0Raw());
                ObservedEntry result = assertInstanceOf(ObservedEntry.class, consume(read.scope(), module(read), read));
                assertEquals(expected.get(row.getKey()), result.branch()); assertSame(input, result.inputs());
            } else {
                Incomplete incomplete = assertInstanceOf(Incomplete.class, read);
                assertEquals(new NotReady(incomplete.reason()), consume(read.scope(), new UInt64(BigInteger.ONE), read));
            }
        }
    }
    @Test void eachCoordinatorUpdateAndInstallationMustSupplyItsOwnOriginalRead() throws Exception {
        Observation read = observation(actualCases(), "same_stamp"); Scope s = read.scope();
        Scope next = new Scope(s.episode(), s.connectionGeneration(), s.nativeRevision(), s.coordinatorIdentity(), "4", s.dateRaw(), s.exeSha256());
        assertEquals(new NotReady("coordinator_update_or_source_changed"), consume(next, module(read), read));
        Scope revision = new Scope(s.episode(), s.connectionGeneration(), "9007199254740996", s.coordinatorIdentity(), s.updateSequence(), s.dateRaw(), s.exeSha256());
        assertEquals(new NotReady("coordinator_update_or_source_changed"), consume(revision, module(read), read));
        assertEquals(new NotReady("module_installation_changed"), consume(s, new UInt64(module(read).value().add(BigInteger.ONE)), read));
        assertInstanceOf(ObservedEntry.class, consume(s, module(read), read));
    }
    @Test void originalInputDemandPreservesNullAndTheNativeDivideFault() throws Exception {
        Map<String,ObjectNode> cases = actualCases();
        Inputs skip = assertInstanceOf(Available.class, observation(cases, "mask_return_no_periodic_read")).inputs();
        assertTrue(skip.periodic().divisorRaw().isEmpty()); assertTrue(skip.periodic().contextStampRaw().isEmpty());
        Inputs nonperiodic = assertInstanceOf(Available.class, observation(cases, "not_periodic")).inputs();
        assertEquals(2, nonperiodic.periodic().divisorRaw().orElseThrow()); assertTrue(nonperiodic.periodic().contextStampRaw().isEmpty());
        Observation fault = observation(cases, "divide_fault"); Inputs f = assertInstanceOf(Available.class, fault).inputs();
        assertEquals(0, f.periodic().divisorRaw().orElseThrow()); assertTrue(f.periodic().contextStampRaw().isEmpty());
        assertEquals(EntryBranch.ORIGINAL_DIVIDE_FAULT, assertInstanceOf(ObservedEntry.class, consume(f.scope(), f.moduleBaseIdentity(), fault)).branch());
        ObjectNode invented = cases.get("mask_return_no_periodic_read").deepCopy();
        object(object(invented.get("facts")).get("periodic")).put("divisor_raw", 0);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(invented)));
        ObjectNode demanded = cases.get("same_stamp").deepCopy();
        object(object(demanded.get("facts")).get("periodic")).putNull("context_stamp_raw");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(demanded)));
    }
    @Test void strictFieldsWidthsSourceBindingsAndSerializationTypes() throws Exception {
        Map<String,ObjectNode> cases = actualCases(); ObjectNode original = cases.get("same_stamp");
        ObjectNode wrong = original.deepCopy(); object(object(wrong.get("facts")).get("fields")).put("flags_raw", true);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(wrong)));
        ObjectNode floating = original.deepCopy(); object(object(floating.get("facts")).get("fields")).put("countdown_b0_raw", 5.0);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(floating)));
        ObjectNode missing = original.deepCopy(); object(object(missing.get("facts")).get("fields")).remove("countdown_c0_raw");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(missing)));
        ObjectNode numeric = original.deepCopy(); object(object(numeric.get("facts")).get("fields")).put("cached_b8_raw", 9007199254740993L);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(numeric)));
        for (String bad : new String[]{"00", "-0", "18446744073709551616"}) {
            ObjectNode invalid = original.deepCopy(); object(object(invalid.get("facts")).get("fields")).put("cached_a8_raw", bad);
            assertThrows(IllegalArgumentException.class, () -> decode(bytes(invalid)));
        }
        ObjectNode rcx = original.deepCopy(); object(rcx.get("facts")).put("original_rcx_identity", "1");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(rcx)));
        ObjectNode wrongCaller = original.deepCopy(); wrongCaller.put("caller_rva", CALLER_RVA + 1);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(wrongCaller)));
        ObjectNode alias = original.deepCopy(); object(alias.get("facts")).put("move_submitted", true);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(alias)));
        ObjectNode absent = cases.get("missing_stamp").deepCopy(); absent.remove("facts");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(absent)));
        ObjectNode falseNull = cases.get("missing_stamp").deepCopy(); falseNull.set("facts", original.get("facts"));
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(falseNull)));
    }
}
