package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.OriginalQuantity12004.*;
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

/** Mandatory actual C++ production reader/serializer output; never Java-authored or silently skipped. */
final class OriginalQuantity12004ProducerTest {
    private static Map<String,ObjectNode> actualCases() throws Exception {
        String file = System.getProperty("xar.originalQuantity12004.nativeWire");
        String sha = System.getProperty("xar.originalQuantity12004.nativeWireSha256");
        String machine = System.getProperty("xar.originalQuantity12004.machineId");
        assertNotNull(file); assertNotNull(sha); assertNotNull(machine); assertFalse(machine.isBlank()); assertTrue(sha.matches("[0-9a-f]{64}"));
        Path path = Path.of(file); assertTrue(path.isAbsolute() && Files.isRegularFile(path));
        long size = Files.size(path); assertTrue(size > 0 && size <= 1_048_576); byte[] original = Files.readAllBytes(path);
        assertEquals(size, original.length); assertEquals(sha, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        ObjectNode root = closed(parse(original), "schema_version", "machine_id", "observed_at_utc", "proof_layer", "original_native_executions", "actual_game", "cases");
        assertEquals(1, i32(root.get("schema_version"))); assertEquals(machine, text(root.get("machine_id")));
        assertNotNull(Instant.parse(text(root.get("observed_at_utc"))));
        assertEquals("owned_memory_reader_serializer_only", text(root.get("proof_layer")));
        assertEquals(0, i32(root.get("original_native_executions"))); assertFalse(bool(root.get("actual_game")));
        Map<String,ObjectNode> cases = new LinkedHashMap<>();
        for (ObjectNode row : array(root.get("cases"), value -> closed(value, "name", "observation")))
            assertNull(cases.put(text(row.get("name")), object(row.get("observation"))));
        assertEquals(Set.of("raw_zero", "wide_positive", "negative_raw", "caller_changed", "mode_changed", "slot_not_member",
                "coordinator_source_changed", "return_changed", "output_unavailable", "update_changed", "occurrence_changed", "module_changed"), cases.keySet());
        return cases;
    }
    @Test void originalProducerToRawOutputAndCompleteRoundTrip() throws Exception {
        Map<String,Long> expected = Map.of("raw_zero", 0L, "wide_positive", Long.MAX_VALUE, "negative_raw", Long.MIN_VALUE);
        for (var row : actualCases().entrySet()) {
            Observation read = decode(bytes(row.getValue())); assertEquals(read, decode(encode(read)), row.getKey());
            assertEquals("9007199254740993", read.scope().connectionGeneration());
            if (expected.containsKey(row.getKey())) {
                Facts facts = assertInstanceOf(Available.class, read).facts();
                ObservedRawOutput value = assertInstanceOf(ObservedRawOutput.class, consume(read.scope(), facts.call(), read));
                assertEquals(expected.get(row.getKey()).longValue(), value.raw()); assertEquals(0, facts.originalModeRaw());
            } else {
                Incomplete missing = assertInstanceOf(Incomplete.class, read);
                UInt64 one = UInt64.positive(BigInteger.ONE);
                assertEquals(new NotReady(missing.reason()), consume(read.scope(), new CallKey(one, one, one, one, one), read));
            }
        }
    }
    @Test void noPriorQueryOrOtherLoopOccurrenceMaySupplyAnOutput() throws Exception {
        Map<String,ObjectNode> cases = actualCases(); Observation read = decode(bytes(cases.get("wide_positive")));
        Facts facts = assertInstanceOf(Available.class, read).facts(); Scope s = read.scope();
        Scope next = new Scope(s.episode(), s.connectionGeneration(), s.nativeRevision(), s.coordinatorIdentity(), "8", s.dateRaw(), s.exeSha256());
        assertEquals(new NotReady("quantity_original_update_or_source_changed"), consume(next, facts.call(), read));
        CallKey k = facts.call(); CallKey other = new CallKey(k.moduleBaseIdentity(), k.outerSlotIdentity(),
                new UInt64(k.innerSlotIdentity().value().add(BigInteger.valueOf(8))), k.unitOperandIdentity(), k.outputAddress());
        assertEquals(new NotReady("quantity_original_occurrence_changed"), consume(s, other, read));
        Observation unavailable = decode(bytes(cases.get("output_unavailable")));
        assertInstanceOf(NotReady.class, consume(unavailable.scope(), facts.call(), unavailable));
        assertInstanceOf(ObservedRawOutput.class, consume(s, facts.call(), read));
        assertInstanceOf(NotReady.class, consume(unavailable.scope(), facts.call(), unavailable));
    }
    @Test void strictWidthsFieldsTypesAndOriginalCallerBinding() throws Exception {
        Map<String,ObjectNode> cases = actualCases(); ObjectNode original = cases.get("wide_positive");
        ObjectNode numeric = original.deepCopy(); object(numeric.get("facts")).put("output_raw", Long.MAX_VALUE);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(numeric)));
        for (String value : new String[]{"-0", "00", "9223372036854775808"}) {
            ObjectNode invalid = original.deepCopy(); object(invalid.get("facts")).put("output_raw", value);
            assertThrows(IllegalArgumentException.class, () -> decode(bytes(invalid)));
        }
        ObjectNode mode = original.deepCopy(); object(mode.get("facts")).put("original_mode_raw", true);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(mode)));
        ObjectNode floatMode = original.deepCopy(); object(floatMode.get("facts")).put("original_mode_raw", 0.0);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(floatMode)));
        ObjectNode otherMode = original.deepCopy(); object(otherMode.get("facts")).put("original_mode_raw", 1);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(otherMode)));
        ObjectNode caller = original.deepCopy(); caller.put("caller_rva", CALLER_RVA + 1);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(caller)));
        ObjectNode pointer = original.deepCopy(); object(object(pointer.get("facts")).get("call")).put("unit_operand_identity", 9007199254740993L);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(pointer)));
        ObjectNode missing = original.deepCopy(); object(object(missing.get("facts")).get("call")).remove("inner_slot_identity");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(missing)));
        ObjectNode unit = original.deepCopy(); object(unit.get("facts")).put("soldiers", 1);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(unit)));
        ObjectNode absent = cases.get("output_unavailable").deepCopy(); absent.remove("facts");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(absent)));
    }
}
