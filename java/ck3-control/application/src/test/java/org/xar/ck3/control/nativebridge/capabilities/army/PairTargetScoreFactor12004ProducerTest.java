package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.PairTargetScoreFactor12004.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.OptionalLong;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.nativebridge.capabilities.army.LocalTargetScore12004.Scope;

/** Original exact machine-code leaf -> actual memory observer/serializer -> Java stage. Root must produce the wire. */
final class PairTargetScoreFactor12004ProducerTest {
    private record Case(Observation observation, OptionalLong originalNativeResult, ObjectNode original) { }
    private static Map<String,Case> cases() throws Exception {
        String file = System.getProperty("xar.pairScoreFactor12004.nativeWire");
        String expected = System.getProperty("xar.pairScoreFactor12004.nativeWireSha256");
        assertNotNull(file, "Root standalone original native-leaf producer output required");
        assertNotNull(expected, "fresh producer file SHA required"); assertTrue(expected.matches("[0-9a-f]{64}"));
        Path path = Path.of(file); assertTrue(path.isAbsolute() && Files.isRegularFile(path)); long size = Files.size(path);
        assertTrue(size > 0 && size <= 8 * 1024 * 1024); byte[] original = Files.readAllBytes(path); assertEquals(size, original.length);
        assertEquals(expected, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        ObjectNode n = closed(parse(original), "schema_version", "machine_id", "observed_at_utc", "actual_game", "original_leaf_sha256", "relocated_leaf_sha256", "relocated_bytes", "native_leaf_executions", "cases");
        assertEquals(1, i32(n.get("schema_version"))); assertFalse(bool(n.get("actual_game")));
        assertTrue(text(n.get("machine_id")).matches("[a-z0-9-]{1,128}")); assertNotEquals("unknown", text(n.get("machine_id")));
        java.time.Instant.parse(text(n.get("observed_at_utc")));
        assertEquals("a67c91f7a5e00be4f052967d60ce065c152d3ed848a9176ee9b23a084ce698a3", text(n.get("original_leaf_sha256")));
        assertEquals("f4a2141ae973266db68be3f00562b606f566bfbfa68ede047a770d36afe5ae4a", text(n.get("relocated_leaf_sha256")));
        assertEquals(4, i32(n.get("relocated_bytes"))); assertEquals(26, i32(n.get("native_leaf_executions")));
        Map<String,Case> cases = new LinkedHashMap<>();
        for (ObjectNode row : array(n.get("cases"), v -> closed(v, "name", "observation", "native_result_raw"))) {
            ObjectNode o = object(row.get("observation")); Observation observation = decode(bytes(o));
            OptionalLong actual = row.get("native_result_raw").isNull() ? OptionalLong.empty() : OptionalLong.of(signed64(text(row.get("native_result_raw"))));
            assertEquals(observation instanceof Available, actual.isPresent(), "missing native outcome cannot be synthesized");
            assertNull(cases.put(text(row.get("name")), new Case(observation, actual, o)));
        }
        assertEquals(Set.of("first_zero", "first_min", "second_zero", "second_min", "lower_blend", "at_ideal", "upper_gap", "at_original_amount",
                "over_original_amount", "zero_ideal_preserves_native_u32_max", "negative_ideal_below", "negative_ideal_above", "negative_definition", "zero_definition",
                "definition_min", "definition_max", "multiply_fast_boundary", "multiply_split_boundary", "divide_fast_boundary", "divide_split_boundary", "amount_max",
                "divide_decomposed", "divide_min_abs_wrap", "ideal_min", "ideal_max", "positive_single_quantum", "missing_runtime_global", "missing_original_context"), cases.keySet());
        return cases;
    }
    @Test void completeActualNativeLeafToTypedJavaStageAndRoundTrip() throws Exception {
        Map<String,Case> cases = cases();
        for (var entry : cases.entrySet()) {
            Case c = entry.getValue(); Observation observation = c.observation();
            assertEquals(observation, decode(encode(observation)), entry.getKey());
            assertEquals("9007199254740993", observation.scope().connectionGeneration());
            Result actual = consume(observation.scope(), observation.callSite(), observation);
            if (c.originalNativeResult().isPresent()) assertEquals(c.originalNativeResult().getAsLong(), assertInstanceOf(WeightedFactor.class, actual).amountRaw(), entry.getKey());
            else assertInstanceOf(NotReady.class, actual, entry.getKey());
        }
        Observation first = cases.get("first_zero").observation(); Inputs firstInputs = assertInstanceOf(Available.class, first).inputs();
        assertTrue(firstInputs.amountBRaw().isEmpty()); assertTrue(firstInputs.parameters().isEmpty());
        Observation second = cases.get("second_zero").observation(); Inputs secondInputs = assertInstanceOf(Available.class, second).inputs();
        assertEquals(0, secondInputs.amountBRaw().orElseThrow()); assertTrue(secondInputs.parameters().isEmpty());
    }
    @Test void threeActualCallersAndFullUpdateSourceRemainBound() throws Exception {
        Map<String,Case> cases = cases(); Set<CallSite> sites = cases.values().stream().map(c -> c.observation().callSite()).collect(java.util.stream.Collectors.toSet());
        assertEquals(Set.of(CallSite.FIRST, CallSite.SECOND, CallSite.THIRD), sites);
        Observation original = cases.get("lower_blend").observation(); Scope s = original.scope();
        Scope changed = new Scope(s.episode(), s.connectionGeneration(), s.nativeRevision(), s.coordinatorIdentity(), "8", s.dateRaw(), s.exeSha256());
        assertEquals(new NotReady("coordinator_update_caller_or_source_changed"), consume(changed, original.callSite(), original));
        CallSite other = original.callSite() == CallSite.FIRST ? CallSite.SECOND : CallSite.FIRST;
        assertEquals(new NotReady("coordinator_update_caller_or_source_changed"), consume(s, other, original));
    }
    @Test void demandedInputsAndCanonicalNumericBoundaryRejectMalformedOriginals() throws Exception {
        Map<String,Case> cases = cases(); ObjectNode original = cases.get("lower_blend").original();
        ObjectNode numeric = original.deepCopy(); object(numeric.get("facts")).put("amount_a_raw", 100000);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(numeric)));
        ObjectNode floatScore = original.deepCopy(); object(object(floatScore.get("facts")).get("parameters")).put("definition_score_raw", 1.0);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(floatScore)));
        ObjectNode boolCaller = original.deepCopy(); boolCaller.put("caller_rva", true);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(boolCaller)));
        ObjectNode wrongCaller = original.deepCopy(); wrongCaller.put("caller_rva", 0x1A09040);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(wrongCaller)));
        ObjectNode zeroSign = original.deepCopy(); object(zeroSign.get("facts")).put("amount_a_raw", "-0");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(zeroSign)));
        ObjectNode leading = original.deepCopy(); object(leading.get("facts")).put("amount_a_raw", "0100000");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(leading)));
        ObjectNode overflow = original.deepCopy(); object(overflow.get("facts")).put("amount_a_raw", "9223372036854775808");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(overflow)));
        ObjectNode missing = original.deepCopy(); object(missing.get("facts")).remove("parameters");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(missing)));
        ObjectNode nullParameters = original.deepCopy(); object(nullParameters.get("facts")).putNull("parameters");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(nullParameters)));
        ObjectNode inventedSecond = cases.get("first_zero").original().deepCopy(); object(inventedSecond.get("facts")).put("amount_b_raw", "123");
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(inventedSecond)));
        ObjectNode inventedParameters = cases.get("second_zero").original().deepCopy(); object(inventedParameters.get("facts")).set("parameters", object(original.get("facts")).get("parameters"));
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(inventedParameters)));
        ObjectNode probability = original.deepCopy(); object(probability.get("facts")).put("win_probability", 1);
        assertThrows(IllegalArgumentException.class, () -> decode(bytes(probability)));
    }
}
