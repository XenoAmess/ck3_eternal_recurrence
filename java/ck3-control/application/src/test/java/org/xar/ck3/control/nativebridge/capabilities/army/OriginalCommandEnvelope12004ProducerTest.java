package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.OriginalCommandEnvelope12004.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.UInt64;
import org.xar.ck3.control.nativebridge.capabilities.army.LocalTargetScore12004.Scope;

/** Mandatory fresh native production-reader artifact; no skipped-input success or Java fallback. */
final class OriginalCommandEnvelope12004ProducerTest {
    private static Map<String,ObjectNode> actualCases() throws Exception {
        String file = System.getProperty("xar.originalCommand12004.nativeWire");
        String sha = System.getProperty("xar.originalCommand12004.nativeWireSha256");
        String machine = System.getProperty("xar.originalCommand12004.machineId");
        assertNotNull(file); assertNotNull(sha); assertNotNull(machine); assertFalse(machine.isBlank()); assertTrue(sha.matches("[0-9a-f]{64}"));
        Path path = Path.of(file); assertTrue(path.isAbsolute() && Files.isRegularFile(path));
        long size = Files.size(path); assertTrue(size > 0 && size <= 1_048_576); byte[] original = Files.readAllBytes(path);
        assertEquals(size, original.length); assertEquals(sha, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        ObjectNode root = closed(parse(original), "schema_version", "machine_id", "observed_at_utc", "proof_layer", "original_native_executions", "actual_game", "cases");
        assertEquals(1, i32(root.get("schema_version"))); assertEquals(machine, text(root.get("machine_id")));
        assertNotNull(Instant.parse(text(root.get("observed_at_utc"))));
        assertEquals("owned_immutable_command_reader_serializer_only", text(root.get("proof_layer")));
        assertEquals(0, i32(root.get("original_native_executions"))); assertFalse(bool(root.get("actual_game")));
        Map<String,ObjectNode> cases = new LinkedHashMap<>();
        for (ObjectNode row : array(root.get("cases"), value -> closed(value, "name", "observation")))
            assertNull(cases.put(text(row.get("name")), object(row.get("observation"))));
        assertEquals(Set.of("copied_path", "empty_path", "opaque_helper_result", "outer_argument_changed", "embedded_mode_changed", "unit_source_changed",
                "candidate_source_changed", "candidate_capacity_changed", "path_last_changed", "path_count_negative", "path_member_missing", "call_frame_changed", "prepared_frame_changed"), cases.keySet());
        return cases;
    }
    @Test void nativeProducerToCommandFieldsAndWireRoundTrip() throws Exception {
        for (var row : actualCases().entrySet()) {
            Observation read = decode(bytes(row.getValue())); assertEquals(read, decode(encode(read)), row.getKey());
            assertEquals("9007199254740997", read.scope().coordinatorIdentity());
            if (read instanceof Available available) {
                Facts f = assertInstanceOf(ObservedEnvelope.class, consume(read.scope(), available.facts().call(), read)).facts();
                assertEquals(2, f.embeddedModeRaw()); assertEquals(7, f.wrapperArgumentRaw());
                assertEquals(2, f.trailingModeRaw()); assertEquals(1, f.trailingOneRaw());
                assertEquals(17, f.unitFullIdRaw()); assertEquals(7, f.candidateFullIdRaw());
                assertEquals(8, f.candidateCapacityRaw());
                if (row.getKey().equals("empty_path")) {assertEquals(List.of(), f.pathFullIdsRaw()); assertEquals(0, f.pathLastFullIdRaw());}
                else {assertEquals(List.of(9, 11), f.pathFullIdsRaw()); assertEquals(11, f.pathLastFullIdRaw());}
                assertEquals(row.getKey().equals("opaque_helper_result") ? Integer.MIN_VALUE : 23, f.helperResultRaw());
            } else assertInstanceOf(Incomplete.class, read);
        }
    }
    @Test void currentScopeAndOriginalOccurrenceAreMandatory() throws Exception {
        Map<String,ObjectNode> cases = actualCases(); Available read = assertInstanceOf(Available.class, decode(bytes(cases.get("copied_path"))));
        CallKey key = read.facts().call(); Scope s = read.scope();
        for (ObjectNode wire : cases.values()) {
            Observation missing = decode(bytes(wire));
            if (missing instanceof Incomplete incomplete) assertEquals(new NotReady(incomplete.reason()), consume(missing.scope(), key, missing));
        }
        Scope next = new Scope(s.episode(), s.connectionGeneration(), s.nativeRevision(), s.coordinatorIdentity(), "8", s.dateRaw(), s.exeSha256());
        assertEquals(new NotReady("command_original_update_or_source_changed"), consume(next, key, read));
        CallKey other = new CallKey(key.moduleBaseIdentity(), key.unitOperandIdentity(),
                UInt64.positive(key.candidateOperandIdentity().value().add(BigInteger.valueOf(8))), key.commandAddress(), key.databaseIdentity());
        assertEquals(new NotReady("command_original_occurrence_changed"), consume(s, other, read));
    }
    private static void rejects(ObjectNode source, Consumer<ObjectNode> mutation) {
        ObjectNode altered = source.deepCopy(); mutation.accept(altered);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(altered)));
    }
    @Test void modesIdentitiesAndPathFieldsRemainStrictlyDistinct() throws Exception {
        ObjectNode base = actualCases().get("copied_path");
        rejects(base, n -> object(n.get("facts")).put("embedded_mode_raw", 7));
        rejects(base, n -> object(n.get("facts")).put("wrapper_argument_raw", 2));
        rejects(base, n -> object(n.get("facts")).put("helper_result_raw", true));
        rejects(base, n -> object(n.get("facts")).put("candidate_full_id_raw", 7.0));
        rejects(base, n -> object(n.get("facts")).put("candidate_capacity_raw", 7));
        rejects(base, n -> object(n.get("facts")).put("unit_full_id_raw", -1));
        rejects(base, n -> object(n.get("facts")).put("path_last_full_id_raw", 7));
        rejects(base, n -> object(n.get("facts")).putNull("path_full_ids_raw"));
        rejects(base, n -> object(object(n.get("facts")).get("call")).put("command_address", 1L));
        rejects(base, n -> object(n.get("facts")).remove("trailing_mode_raw"));
        rejects(base, n -> object(n.get("facts")).put("executed", true));
        rejects(base, n -> n.put("wrapper_rva", WRAPPER_RVA + 1));
    }
}
