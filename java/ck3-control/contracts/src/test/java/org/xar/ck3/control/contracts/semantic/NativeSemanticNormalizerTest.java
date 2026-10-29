package org.xar.ck3.control.contracts.semantic;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.DecimalTokenNode;

final class NativeSemanticNormalizerTest {
    private static JsonNode parse(String wire) { return FullJsonTree.parse(wire.getBytes(StandardCharsets.UTF_8), 65536); }
    @Test void rawAndCanonicalAreSeparateDomainsAndMissingFieldsBecomeExplicitSemanticNulls() {
        ObjectNode raw = (ObjectNode) parse("{\"active_event\":{},\"history\":false,\"top_exclusive_modal_choice_hint\":{\"pump_epoch\":1,\"thread_id\":2,\"root\":3}}");
        var captured = NativeSemanticNormalizer.original(raw);
        raw.put("active_event", false);
        ObjectNode result = NativeSemanticNormalizer.normalize(captured, "snapshot", BigInteger.TEN).semantic();
        assertNull(result.path("active_event").get("option_count").numberValue());
        assertTrue(result.path("active_event").path("option_count").isNull());
        assertEquals(0, result.path("active_event").path("options").size());
        for (String field : new String[]{"one_life_settlement", "played_character", "played_character_gold",
                "played_character_prestige", "played_character_piety", "pending_character_interaction"}) assertTrue(result.path(field).isNull(), field);
        assertTrue(result.path("history").isArray()); assertEquals(0, result.path("history").size());
        assertFalse(result.path("top_exclusive_modal_choice_hint").has("pump_epoch"));
        assertFalse(result.path("top_exclusive_modal_choice_hint").has("thread_id"));
        assertEquals(3, result.path("top_exclusive_modal_choice_hint").path("root").intValue());
        result.put("revision", 999);
        assertEquals(BigInteger.TEN, NativeSemanticNormalizer.normalize(captured, "snapshot", BigInteger.TEN).semantic().path("revision").bigIntegerValue());
        ObjectNode fresh = NativeSemanticNormalizer.normalize(captured, "snapshot", BigInteger.TEN).semantic();
        // This demonstrates the original non-idempotence; production only accepts an original ObservedFrame.
        assertEquals(0, NativeSemanticNormalizer.normalize(NativeSemanticNormalizer.original(fresh), "snapshot", BigInteger.TEN)
                .semantic().path("active_event").path("option_count").intValue());
    }
    @Test void revisionFingerprintUsesExactPythonNumericEqualityWithoutWeakeningInputTypes() {
        assertTrue(NativeSemanticFingerprint.equivalent(parse("{\"v\":1}"), parse("{\"v\":1.0}")));
        assertTrue(NativeSemanticFingerprint.equivalent(parse("{\"v\":-0.0}"), parse("{\"v\":0}")));
        assertTrue(NativeSemanticFingerprint.equivalent(parse("{\"v\":true}"), parse("{\"v\":1}")));
        assertFalse(NativeSemanticFingerprint.equivalent(parse("{\"v\":100000000000000000000000}"), parse("{\"v\":1e23}")));
        assertFalse(NativeSemanticFingerprint.equivalent(parse("{\"v\":9007199254740993}"), parse("{\"v\":9007199254740992.0}")));
        assertFalse(NativeSemanticFingerprint.equivalent(parse("{\"v\":null}"), parse("{}")));
        assertFalse(NativeSemanticFingerprint.equivalent(parse("{\"v\":[1,2]}"), parse("{\"v\":[2,1]}")));
        assertThrows(IllegalArgumentException.class, () -> NativePlayedCharacter.normalize(parse("{\"character_id\":true,\"alive\":true}"), BigInteger.ONE, parse("0")));
    }
    @Test void fullMaterialParserKeepsNormalizedFloatTokensAndEnforcesItsOwnBoundedLane() {
        String wire = "{\"large\":\"" + "x".repeat(1048580) + "\",\"float\":1.0,\"negative_zero\":-0.0,\"id\":18446744073709551615}";
        byte[] raw = wire.getBytes(StandardCharsets.UTF_8);
        JsonNode decoded = FullJsonTree.parse(raw, 2 * 1024 * 1024);
        assertTrue(raw.length > 1_048_576);
        assertEquals("1.0", assertInstanceOf(DecimalTokenNode.class, decoded.path("float")).originalToken());
        assertEquals("-0.0", assertInstanceOf(DecimalTokenNode.class, decoded.path("negative_zero")).originalToken());
        assertEquals(Double.doubleToRawLongBits(-0.0), Double.doubleToRawLongBits(decoded.path("negative_zero").doubleValue()));
        assertEquals(new BigInteger("18446744073709551615"), decoded.path("id").bigIntegerValue());
        assertEquals(decoded, FullJsonTree.parse(FullJsonTree.encode(decoded, 2 * 1024 * 1024), 2 * 1024 * 1024));
        assertThrows(IllegalArgumentException.class, () -> FullJsonTree.parse(raw, 1048576));
        byte[] wide = "{\"n\":1e400}".getBytes(StandardCharsets.UTF_8);
        JsonNode retained = FullJsonTree.parse(wide, 65536);
        assertEquals("1e400", assertInstanceOf(DecimalTokenNode.class, retained.path("n")).originalToken());
        assertArrayEquals(wide, FullJsonTree.encode(retained, 65536));
        for (String invalid : new String[]{" ", "{} {}", "{\"k\":1,\"k\":2}", "{\"n\":NaN}"})
            assertThrows(IllegalArgumentException.class, () -> parse(invalid));
        assertThrows(IllegalArgumentException.class, () -> FullJsonTree.parse(new byte[]{(byte)0xc3, (byte)0x28}, 1024));
        assertThrows(IllegalArgumentException.class, () -> FullJsonTree.encode(JsonNodeFactory.instance.numberNode(Double.NaN), 1024));
    }
}
