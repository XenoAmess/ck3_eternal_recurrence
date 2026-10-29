package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.LocalTargetScore12004.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;

/** Requires the real C++ production observer/serializer output; no Java-authored substitute or skip. */
final class LocalTargetScore12004ProducerTest {
    private static Map<String,ObjectNode> actualCases() throws Exception {
        String file = System.getProperty("xar.localScore12004.nativeWire");
        String expected = System.getProperty("xar.localScore12004.nativeWireSha256");
        assertNotNull(file, "Root must run ck3_12004_local_target_score_test first");
        assertNotNull(expected, "fresh original producer SHA required");
        assertTrue(expected.matches("[0-9a-f]{64}")); Path path = Path.of(file);
        assertTrue(path.isAbsolute() && Files.isRegularFile(path));
        long size = Files.size(path); assertTrue(size > 0 && size <= 8 * 1024 * 1024);
        byte[] original = Files.readAllBytes(path); assertEquals(size, original.length);
        assertEquals(expected, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        ObjectNode root = closed(parse(original), "schema_version", "actual_game", "cases");
        assertEquals(2, i32(root.get("schema_version"))); assertFalse(bool(root.get("actual_game")));
        Map<String,ObjectNode> cases = new LinkedHashMap<>();
        for (var raw : array(root.get("cases"), value -> closed(value, "name", "observation")))
            assertNull(cases.put(text(raw.get("name")), object(raw.get("observation"))));
        assertEquals(Set.of("undesired", "resolved_one_combat", "unresolved", "rejected_before_lazy_gate", "same_target_close_adjacent",
                "duplicate_friendly_once", "primary_relation_blocks_secondary", "secondary_relation_allowed", "native_int32_squared_distance_wrap",
                "missing_supporting_getter", "missing_existing_relation"), cases.keySet());
        return cases;
    }
    @Test void actualNativeMemoryProducerToStageAndCompleteRoundTrip() throws Exception {
        Map<String,ObjectNode> cases = actualCases();
        Map<String,Integer> expected = Map.of("undesired", -1000, "resolved_one_combat", 40, "rejected_before_lazy_gate", -1_000_000,
                "same_target_close_adjacent", 110, "duplicate_friendly_once", -959, "primary_relation_blocks_secondary", -1000,
                "secondary_relation_allowed", -959, "native_int32_squared_distance_wrap", 85);
        for (var row : cases.entrySet()) {
            Observation observation = decode(bytes(row.getValue()));
            assertEquals(observation, decode(encode(observation)), row.getKey());
            assertEquals("9007199254740993", observation.scope().connectionGeneration());
            assertEquals("18446744073709551615", observation.scope().coordinatorIdentity());
            Result result = consume(observation.scope(), observation);
            if (expected.containsKey(row.getKey())) assertEquals(expected.get(row.getKey()).intValue(), assertInstanceOf(Scored.class, result).delta());
            else assertInstanceOf(NotReady.class, result, row.getKey());
        }
        Scored rejected = assertInstanceOf(Scored.class, consume(decode(bytes(cases.get("rejected_before_lazy_gate"))).scope(), decode(bytes(cases.get("rejected_before_lazy_gate")))));
        assertTrue(rejected.rejected()); assertEquals(-1_000_000, rejected.applyToPrior(5_000));
        Scored ordinary = new Scored(100, false); assertEquals(Integer.MIN_VALUE + 99, ordinary.applyToPrior(Integer.MAX_VALUE));
    }
    @Test void updateBoundaryAndLazyGateCannotReuseEarlierScore() throws Exception {
        Map<String,ObjectNode> cases = actualCases(); Observation prior = decode(bytes(cases.get("resolved_one_combat")));
        Scope s = prior.scope(); Scope next = new Scope(s.episode(), s.connectionGeneration(), s.nativeRevision(), s.coordinatorIdentity(), "4", s.dateRaw(), s.exeSha256());
        assertEquals(new NotReady("coordinator_update_or_source_changed"), consume(next, prior));
        Observation unresolved = decode(bytes(cases.get("unresolved")));
        assertEquals(new NotReady("native_local_gate_unresolved"), consume(unresolved.scope(), unresolved));
        assertInstanceOf(Scored.class, consume(prior.scope(), prior));
        // The class retains no cached facts. A previously scored same-update row cannot fill a later unresolved query.
        assertEquals(new NotReady("native_local_gate_unresolved"), consume(unresolved.scope(), unresolved));
    }
    @Test void allNativeBoundariesRejectWrongFieldsAndIdentityTypes() throws Exception {
        ObjectNode original = actualCases().get("resolved_one_combat");
        ObjectNode wrong = original.deepCopy(); object(wrong.get("facts")).put("flags_raw", true);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(wrong)));
        ObjectNode floating = original.deepCopy(); object(floating.get("facts")).put("support_depth", 1.0);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(floating)));
        ObjectNode missing = original.deepCopy(); object(missing.get("facts")).remove("local_gate_raw");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(missing)));
        ObjectNode numeric = original.deepCopy(); object(numeric.get("scope")).put("connection_generation", 9007199254740993L);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(numeric)));
        ObjectNode leadingZero = original.deepCopy(); object(leadingZero.get("scope")).put("update_sequence", "03");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(leadingZero)));
        ObjectNode unknown = original.deepCopy(); object(unknown.get("facts")).put("local_gate_raw", 3);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(unknown)));
        ObjectNode invented = original.deepCopy(); object(invented.get("facts")).put("win_probability", 1);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(invented)));
        ObjectNode oldSchema = original.deepCopy(); oldSchema.put("schema_version", 1);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(oldSchema)));
        ObjectNode oldField = original.deepCopy(); ObjectNode oldFacts = object(oldField.get("facts"));
        oldFacts.set("same_sieging_unit", oldFacts.remove("same_original_target"));
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(oldField)));
        ObjectNode incomplete = actualCases().get("missing_existing_relation").deepCopy(); incomplete.remove("facts");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(incomplete)));
        ObjectNode badNull = actualCases().get("missing_existing_relation").deepCopy(); badNull.set("facts", object(original.get("facts")));
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(badNull)));
    }
}
