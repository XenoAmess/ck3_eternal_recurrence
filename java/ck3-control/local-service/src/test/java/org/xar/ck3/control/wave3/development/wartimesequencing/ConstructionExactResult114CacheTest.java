package org.xar.ck3.control.wave3.development.wartimesequencing;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.planning.finance.ConstructionOriginalSource;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryCodec;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryModel;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryPolicy;

/** New cache DATA contract only. Reuses two qualified pure builders, never their old @Test methods.
 * No writer, CAS, clock, permission, Native or Game. Policy source integration and custody DATA
 * measurement are separate; the consumer harness does not invoke Policy.evaluate.
 * selected().original() is deliberately never a result-byte oracle.
 */
final class ConstructionExactResult114CacheTest {
    private static final int FULL = FullJsonTree.MAXIMUM_BYTES;
    private static final String PRECISE = "0.123456789012345678901";

    @Test void selectedSmallFullFactoryOwnsExactResultAndOldSmallFallbackStaysEmpty() throws Exception {
        ObjectNode input = complete();
        byte[] outer = wire(input), raw = wire(query(input));
        NativeQuote legacy = new NativeQuote(raw), full = NativeQuote.fromFullMaterial(raw);
        assertSelected(legacy); assertSelected(full);
        byte[] expected = fixed(raw);
        assertArrayEquals(expected, full.exactFullFinalizedBytes().orElseThrow());
        assertTrue(legacy.exactFullFinalizedBytes().isEmpty(), "old public constructor never opts into this cache");
        assertArrayEquals(expected, ConstructionOriginalSource.finalizeQuery(legacy.original()),
                "the unchanged production fallback still emits the existing fixed-codec result");
        var oldRequest = new OrdinaryWartimeConstructionCodec.ObservedRequest(outer);
        var fullRequest = OrdinaryWartimeConstructionCodec.ObservedRequest.fromFullMaterial(outer);
        Result before = compose(oldRequest.input()), after = compose(fullRequest.input());
        assertEquals(Disposition.QUOTED_CANDIDATE, before.disposition());
        assertEquals(Disposition.QUOTED_CANDIDATE, after.disposition());
        assertArrayEquals(OrdinaryWartimeConstructionCodec.encode(before), OrdinaryWartimeConstructionCodec.encode(after));
        assertArrayEquals(outer, wire(input)); assertArrayEquals(raw, full.original());
    }

    @Test void full139RowResultMatchesExistingFinalizerForPrecisionAndOrderedOpaqueWorld() throws Exception {
        ObjectNode input = complete();
        ArrayNode history = fixture("retainedHistory139", ArrayNode.class);
        assertEquals(139, history.size());
        assertTrue(wire(history).length > 3_000_000 && wire(history).length < 4_000_000);
        for (String field : List.of("starting_snapshot", "ending_snapshot"))
            ((ObjectNode) query(input).get(field)).set("native_command_history", history.deepCopy());
        world(input).set("opaque_result_cache114", parse("{\"z\":\"first\",\"a\":\"second\",\"precise\":"
                + PRECISE + ",\"scaled\":1.00,\"negative_zero\":-0.0,\"exponent\":1e+0,\"nested\":{\"last\":2,\"first\":1}}"));
        byte[] outer = wire(input), raw = wire(query(input));
        assertTrue(raw.length > 6_000_000 && raw.length < 9_000_000);
        String supplied = new String(raw, StandardCharsets.UTF_8);
        assertTrue(supplied.contains("\"precise\":" + PRECISE));
        assertTrue(supplied.contains("\"scaled\":1.00"));
        assertTrue(supplied.contains("\"negative_zero\":-0.0"));
        assertTrue(supplied.contains("\"exponent\":1e+0"));
        NativeQuote full = NativeQuote.fromFullMaterial(raw); assertSelected(full);
        var request = OrdinaryWartimeConstructionCodec.ObservedRequest.fromFullMaterial(outer);
        assertEquals(Disposition.QUOTED_CANDIDATE, compose(request.input()).disposition());
        byte[] expected = fixed(raw), actual = full.exactFullFinalizedBytes().orElseThrow();
        assertArrayEquals(expected, actual, "cache must own first fixed-codec bytes, including its established numeric normalization");
        assertArrayEquals(expected, request.input().quoted().orElseThrow().nativeQuote().exactFullFinalizedBytes().orElseThrow());
        assertTrue(new String(expected, StandardCharsets.UTF_8).contains(PRECISE), "exercise precision that a Double reencode cannot preserve");
        JsonNode opaque = parse(actual).get("world").get("opaque_result_cache114");
        assertEquals(List.of("z", "a", "precise", "scaled", "negative_zero", "exponent", "nested"), names(opaque));
        assertEquals(List.of("last", "first"), names(opaque.get("nested")));
        // The existing finalizer normalizes some 1.00/-0.0/1e+0 spellings. Its bytes above are
        // authoritative; only the full original must retain those exact supplied spellings.
        assertArrayEquals(raw, full.original()); assertArrayEquals(outer, request.original());
        assertArrayEquals(outer, wire(input));
    }

    @Test void inputAndReturnedArraysCannotMutateCacheOrAnotherLiveInstance() throws Exception {
        ObjectNode first = complete(), second = complete();
        world(first).set("opaque_result_cache114", parse("{\"marker\":\"first\",\"precise\":" + PRECISE + "}"));
        world(second).set("opaque_result_cache114", parse("{\"precise\":0.987654321098765432109,\"marker\":\"second\"}"));
        byte[] originalA = wire(query(first)), originalB = wire(query(second));
        byte[] expectedA = fixed(originalA), expectedB = fixed(originalB);
        assertFalse(Arrays.equals(expectedA, expectedB), "distinct real result bytes make static sharing observable");
        byte[] suppliedA = originalA.clone(); NativeQuote a = NativeQuote.fromFullMaterial(suppliedA); assertSelected(a);
        suppliedA[0] = '[';
        assertArrayEquals(originalA, a.original()); assertArrayEquals(expectedA, a.exactFullFinalizedBytes().orElseThrow());
        byte[] returnedA = a.exactFullFinalizedBytes().orElseThrow(); returnedA[0] = '!';
        byte[] returnedOriginalA = a.original(); returnedOriginalA[0] = '!';
        assertArrayEquals(expectedA, a.exactFullFinalizedBytes().orElseThrow()); assertArrayEquals(originalA, a.original());
        NativeQuote b = NativeQuote.fromFullMaterial(originalB); assertSelected(b);
        byte[] returnedB = b.exactFullFinalizedBytes().orElseThrow(); returnedB[0] = '!';
        assertArrayEquals(expectedB, b.exactFullFinalizedBytes().orElseThrow());
        assertArrayEquals(expectedA, a.exactFullFinalizedBytes().orElseThrow(), "a second live quote cannot overwrite the first instance");
        assertArrayEquals(originalA, a.original()); assertArrayEquals(originalB, b.original());
    }

    @Test void unselectedFullObjectHasNoCachedResultAndOldSmallPathRetainsFixedOutput() throws Exception {
        ObjectNode input = complete(); ObjectNode refused = query(input).deepCopy();
        refused.put("material_receipt", true).put("wartime_observation", true);
        NativeQuote unselected = NativeQuote.fromFullMaterial(wire(refused));
        assertTrue(unselected.selected().isEmpty());
        assertEquals(ConstructionQueryModel.Rejection.SOURCE_MODES,
                assertInstanceOf(ConstructionQueryModel.Rejected.class, ConstructionQueryPolicy.finalizeObservation(unselected.observation())).reason());
        assertTrue(unselected.exactFullFinalizedBytes().isEmpty(), "a full factory is not alone permission to retain a selected result");
        byte[] raw = wire(query(complete())); NativeQuote small = new NativeQuote(raw); assertSelected(small);
        assertTrue(small.exactFullFinalizedBytes().isEmpty());
        assertArrayEquals(ConstructionQueryCodec.finalizeObservation(raw), ConstructionOriginalSource.finalizeQuery(small.original()));
        assertArrayEquals(raw, small.original());
    }

    private static void assertSelected(NativeQuote quote) {
        assertTrue(quote.selected().isPresent(), "actual positive source must reach SELECTED before byte comparisons");
        assertEquals(ConstructionQueryModel.ReadyKind.SELECTED,
                assertInstanceOf(ConstructionQueryModel.Ready.class, ConstructionQueryPolicy.finalizeObservation(quote.observation())).kind());
    }
    private static byte[] fixed(byte[] raw) {
        return ConstructionQueryCodec.finalizeObservation(ConstructionQueryCodec.projectFullMaterialInput(raw));
    }
    private static ObjectNode complete() throws Exception { return fixture("complete", ObjectNode.class); }
    private static <T> T fixture(String method, Class<T> type) throws Exception {
        Class<?> source = Class.forName("org.xar.ck3.control.wave3.development.wartimesequencing.ConstructionFullOriginal113SdkTest");
        var builder = source.getDeclaredMethod(method); builder.setAccessible(true); return type.cast(builder.invoke(null));
    }
    private static ObjectNode query(ObjectNode input) {
        return (ObjectNode) input.get("quoted_outlay").get("query_observation");
    }
    private static ObjectNode world(ObjectNode input) {
        return (ObjectNode) query(input).get("native_envelope").get("result").get("private_probe").get("player_world_building_sources");
    }
    private static byte[] wire(JsonNode node) { return FullJsonTree.encode(node, FULL); }
    private static JsonNode parse(String text) { return parse(text.getBytes(StandardCharsets.UTF_8)); }
    private static JsonNode parse(byte[] bytes) { return FullJsonTree.parse(bytes, FULL); }
    private static List<String> names(JsonNode object) {
        assertTrue(object.isObject()); var result = new ArrayList<String>(); object.properties().forEach(entry -> result.add(entry.getKey())); return result;
    }
}
