package org.xar.ck3.control.wave3.development.wartimesequencing;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Modifier;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.planning.finance.ConstructionOriginalSource;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryCodec;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec.ObservedRequest;

/** Internal owned-query DATA only. Reflection below reads API modifiers or existing pure fixture builders;
 * it never constructs an owned token, invokes a Guard issuer, acquires a writer, or queries Native.
 */
final class ConstructionOwnedQuery120Test {
    private static final int FULL = FullJsonTree.MAXIMUM_BYTES;

    @Test void ownedRouteHasClosedMintAndIsolatedExactBytesAcrossInstances() throws Exception {
        Class<?> token = OrdinaryWartimeConstructionCodec.OwnedQueryProjection.class;
        assertTrue(Modifier.isFinal(token.getModifiers()));
        assertFalse(Modifier.isPublic(token.getModifiers()));
        for (var constructor : token.getDeclaredConstructors()) assertTrue(Modifier.isPrivate(constructor.getModifiers()));
        for (var field : token.getDeclaredFields()) {
            assertTrue(Modifier.isPrivate(field.getModifiers())); assertTrue(Modifier.isFinal(field.getModifiers()));
            assertEquals(byte[].class, field.getType(), "token retains only owned byte arrays, never DOM");
        }
        for (var method : OrdinaryWartimeConstructionCodec.class.getDeclaredMethods())
            if (!Modifier.isPrivate(method.getModifiers()))
                assertNotEquals(token, method.getReturnType(), "no externally callable arbitrary-node token mint");
        for (var constructor : NativeQuote.class.getDeclaredConstructors())
            if (constructor.getParameterCount() == 2) assertTrue(Modifier.isPrivate(constructor.getModifiers()));
        var facade = ConstructionQueryCodec.class.getDeclaredMethod("projectMaterialRole", JsonNode.class);
        assertEquals(byte[].class, facade.getReturnType());

        ObjectNode firstRoot = standardOuter();
        world(query(firstRoot)).set("opaque_owned120", parse("{\"last\":1.00,\"first\":-0.0,\"fraction\":0.123456789012345678901,\"exp\":1e+0,\"text\":\"\\ud83d\\ude80\\n\\\"\\\\\",\"rows\":[false,null,{},[]]}"));
        byte[] original = wire(firstRoot), caller = original.clone();
        byte[] oldQuery = wire(query((ObjectNode) FullJsonTree.parse(original, FULL)));
        NativeQuote reference = NativeQuote.fromFullMaterial(oldQuery);
        assertTrue(reference.selected().isPresent());
        var first = ObservedRequest.fromFullMaterial(caller); caller[0] = '!';
        NativeQuote firstQuote = first.input().quoted().orElseThrow().nativeQuote();
        assertNativeValue(reference, firstQuote);
        assertArrayEquals(oldQuery, firstQuote.original());
        assertArrayEquals(ConstructionOriginalSource.finalizeQuery(oldQuery), firstQuote.exactFullFinalizedBytes().orElseThrow());
        assertTrue(new String(firstQuote.exactFullFinalizedBytes().orElseThrow(), StandardCharsets.UTF_8).contains("0.123456789012345678901"));
        var typedReference = new Request(first.input().selection(), first.input().stage(), first.input().current(),
                Optional.of(new QuotedOutlay(reference, first.input().quoted().orElseThrow().currentCash())), first.input().financing());
        assertEquals(Disposition.QUOTED_CANDIDATE, compose(first.input()).disposition());
        assertArrayEquals(OrdinaryWartimeConstructionCodec.encode(compose(typedReference)), OrdinaryWartimeConstructionCodec.encode(compose(first.input())));
        byte[] rawGetter = firstQuote.original(), exactGetter = firstQuote.exactFullFinalizedBytes().orElseThrow(), outerGetter = first.original();
        rawGetter[0] = '!'; exactGetter[0] = '!'; outerGetter[0] = '!';
        assertArrayEquals(original, first.original()); assertArrayEquals(oldQuery, firstQuote.original());
        assertArrayEquals(reference.exactFullFinalizedBytes().orElseThrow(), firstQuote.exactFullFinalizedBytes().orElseThrow());

        ObjectNode secondRoot = (ObjectNode) FullJsonTree.parse(original, FULL);
        ((ObjectNode) query(secondRoot).path("native_envelope").path("result").path("private_probe")).put("proof_epoch", BigInteger.TWO);
        var second = ObservedRequest.fromFullMaterial(wire(secondRoot)); NativeQuote secondQuote = second.input().quoted().orElseThrow().nativeQuote();
        assertTrue(secondQuote.selected().isPresent());
        assertFalse(Arrays.equals(firstQuote.original(), secondQuote.original()));
        assertFalse(Arrays.equals(firstQuote.exactFullFinalizedBytes().orElseThrow(), secondQuote.exactFullFinalizedBytes().orElseThrow()));
        byte[] secondGetter = secondQuote.original(); secondGetter[0] = '!';
        assertArrayEquals(original, first.original()); assertArrayEquals(oldQuery, firstQuote.original());
        assertArrayEquals(wire(query(secondRoot)), secondQuote.original());
    }

    @Test void internalRoleBudgetStillPrecedesLaterCashDecode() throws Exception {
        ObjectNode outer = standardOuter(); ObjectNode q = query(outer);
        ((ObjectNode) q.get("native_envelope")).put("opaque_consumed120", "x".repeat(ConstructionQueryCodec.MAX_BYTES));
        // Existing full constructor computes the quoted query before decoding this deliberately invalid later field.
        outer.putNull("cash_input"); byte[] original = wire(outer);
        RuntimeException reference = assertThrows(RuntimeException.class, () -> ConstructionQueryCodec.deriveFullMaterialQuery(q));
        RuntimeException actual = assertThrows(RuntimeException.class, () -> ObservedRequest.fromFullMaterial(original));
        assertTrue(reference.getMessage().contains("explicit lease"));
        assertEquals(reference.getClass(), actual.getClass()); assertEquals(reference.getMessage(), actual.getMessage());
        assertTrue(Arrays.stream(actual.getStackTrace()).anyMatch(frame -> frame.getClassName().endsWith("$OwnedQueryProjection")));
        assertArrayEquals(original, wire(outer));
    }

    @Test void fullOuterRawWithin64MiBStillRejectsExpandedNestedQueryAtExistingDerivedBudget() throws Exception {
        ObjectNode outer = standardOuter(); ObjectNode q = query(outer);
        ObjectNode expansion = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode(); expansion.put("large", "P120-LARGE-NUMBER"); expansion.put("unicode", "P120-LITERAL-EMOJI");
        ((ObjectNode) q.get("starting_snapshot")).set("opaque_expansion120", expansion);
        byte[] queryBase = wire(q);
        ((ObjectNode) outer.get("quoted_outlay")).put("query_observation", "P120-QUERY-SLOT");
        byte[] outerBase = wire(outer), slot = ascii("\"P120-QUERY-SLOT\""); int at = uniqueIndex(outerBase, slot);
        int outerTarget = FULL - 1, queryTarget = outerTarget - (outerBase.length - slot.length);
        byte[] literalQuery = nearLimitLiteralQuery(queryBase, queryTarget);
        byte[] original = replaceAt(outerBase, at, slot.length, literalQuery);
        assertEquals(outerTarget, original.length); assertTrue(literalQuery.length < FULL);
        assertStandaloneBytePositive(literalQuery);
        int expanded = expandedQueryLength(literalQuery); assertTrue(expanded > FULL);
        RuntimeException oldDerived = assertOldPublicDerivedRefusal(literalQuery);
        RuntimeException actual = assertThrows(RuntimeException.class, () -> ObservedRequest.fromFullMaterial(original));
        assertEquals(oldDerived.getClass(), actual.getClass()); assertEquals(oldDerived.getMessage(), actual.getMessage());
        assertTrue(actual.getMessage().contains("explicit lease"));
        assertTrue(Arrays.stream(actual.getStackTrace()).anyMatch(frame -> frame.getClassName().endsWith("$OwnedQueryProjection")));
        System.out.println("P120 actualFullOuterRaw=" + original.length + " literalNestedQuery=" + literalQuery.length
                + " expandedNestedQuery=" + expanded + " oldByteSelected=true oldPublicDerived64Rejected=true ownedFullRoute64Rejected=true");
    }

    private static void assertStandaloneBytePositive(byte[] raw) {
        NativeQuote reference = NativeQuote.fromFullMaterial(raw); assertTrue(reference.selected().isPresent()); assertArrayEquals(raw, reference.original());
    }
    private static int expandedQueryLength(byte[] raw) {
        // Observation-only derived lease, never a production query budget change.
        return FullJsonTree.encode(FullJsonTree.parse(raw, FULL), FullJsonTree.MAXIMUM_DRIVER_BYTES).length;
    }
    private static RuntimeException assertOldPublicDerivedRefusal(byte[] raw) {
        RuntimeException failure = assertThrows(RuntimeException.class, () -> ConstructionQueryCodec.deriveFullMaterialQuery(FullJsonTree.parse(raw, FULL)));
        assertTrue(failure.getMessage().contains("explicit lease")); return failure;
    }
    private static byte[] nearLimitLiteralQuery(byte[] base, int target) {
        byte[] number = ascii("\"P120-LARGE-NUMBER\""), unicode = ascii("\"P120-LITERAL-EMOJI\"");
        int n = uniqueIndex(base, number), u = uniqueIndex(base, unicode); assertTrue(u > n);
        byte[] literal = ("\"" + new String(Character.toChars(0x1F600)).repeat(6000) + "\"").getBytes(StandardCharsets.UTF_8);
        int numberLength = target - (base.length - number.length - unicode.length + literal.length);
        assertTrue(numberLength > 60_000_000);
        byte[] raw = new byte[target]; int offset = 0;
        System.arraycopy(base, 0, raw, offset, n); offset += n; raw[offset++] = '1'; raw[offset++] = 'e'; raw[offset++] = '+';
        Arrays.fill(raw, offset, offset + numberLength - 3, (byte) '0'); offset += numberLength - 3;
        int middle = n + number.length; System.arraycopy(base, middle, raw, offset, u - middle); offset += u - middle;
        System.arraycopy(literal, 0, raw, offset, literal.length); offset += literal.length;
        int tail = u + unicode.length; System.arraycopy(base, tail, raw, offset, base.length - tail); offset += base.length - tail;
        assertEquals(raw.length, offset); return raw;
    }
    private static byte[] replaceAt(byte[] base, int at, int removed, byte[] inserted) {
        byte[] result = new byte[base.length - removed + inserted.length]; System.arraycopy(base, 0, result, 0, at);
        System.arraycopy(inserted, 0, result, at, inserted.length);
        System.arraycopy(base, at + removed, result, at + inserted.length, base.length - at - removed); return result;
    }
    private static int uniqueIndex(byte[] source, byte[] marker) {
        int found = -1;
        outer: for (int s = 0; s <= source.length - marker.length; s++) {
            for (int i = 0; i < marker.length; i++) if (source[s + i] != marker[i]) continue outer;
            assertEquals(-1, found, "one literal marker required"); found = s;
        }
        assertTrue(found >= 0); return found;
    }
    private static void assertNativeValue(NativeQuote before, NativeQuote after) {
        assertEquals(before.observation(), after.observation()); assertEquals(before.constructionKind(), after.constructionKind());
        assertEquals(before.selected().isPresent(), after.selected().isPresent());
        if (before.selected().isPresent()) {
            assertEquals(before.selected().orElseThrow().candidate(), after.selected().orElseThrow().candidate());
            assertEquals(before.selected().orElseThrow().sourceFrame(), after.selected().orElseThrow().sourceFrame());
            assertArrayEquals(before.selected().orElseThrow().original().bytes(), after.selected().orElseThrow().original().bytes());
        }
    }
    private static ObjectNode standardOuter() throws Exception { return (ObjectNode) FullJsonTree.parse(wire(fixture()), FULL); }
    private static JsonNode fixture() throws Exception {
        Class<?> type = Class.forName("org.xar.ck3.control.wave3.development.wartimesequencing.ConstructionFullOriginal113SdkTest");
        var method = type.getDeclaredMethod("complete"); method.setAccessible(true); return (JsonNode) method.invoke(null);
    }
    private static ObjectNode query(ObjectNode outer) { return (ObjectNode) outer.get("quoted_outlay").get("query_observation"); }
    private static ObjectNode world(ObjectNode q) { return (ObjectNode) q.path("native_envelope").path("result").path("private_probe").path("player_world_building_sources"); }
    private static JsonNode parse(String value) { return FullJsonTree.parse(value.getBytes(StandardCharsets.UTF_8), FULL); }
    private static byte[] ascii(String value) { return value.getBytes(StandardCharsets.US_ASCII); }
    private static byte[] wire(JsonNode value) { return FullJsonTree.encode(value, FULL); }
}
