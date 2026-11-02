package org.xar.ck3.control.continuity;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

final class ContinuityJsonQuoteContractTest {
    private static JsonNode text(String value) {
        return StrictJson.object().put("text", value).get("text");
    }
    private static byte[] decoded(String encoded) {
        return Base64.getDecoder().decode(encoded);
    }
    private static String fromUtf8(String encoded) {
        return new String(decoded(encoded), StandardCharsets.UTF_8);
    }

    @Test void stringCanonicalBytesAndDigestsMatchIndependentGoldens() {
        checkGolden(fromUtf8(""), decoded("IiI="), "12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126");
        String plain = "0123456789abcdef".repeat(1024);
        checkGolden(plain, ("\"" + plain + "\"").getBytes(StandardCharsets.UTF_8), "a436096bc601b7a997a557a29535c3318358d5ca6b2bffc04d3a8ed5dc461db4");
        checkGolden(fromUtf8("AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8="), decoded("Ilx1MDAwMFx1MDAwMVx1MDAwMlx1MDAwM1x1MDAwNFx1MDAwNVx1MDAwNlx1MDAwN1xiXHRcblx1MDAwYlxmXHJcdTAwMGVcdTAwMGZcdTAwMTBcdTAwMTFcdTAwMTJcdTAwMTNcdTAwMTRcdTAwMTVcdTAwMTZcdTAwMTdcdTAwMThcdTAwMTlcdTAwMWFcdTAwMWJcdTAwMWNcdTAwMWRcdTAwMWVcdTAwMWYi"), "f144bcffbdbaea0a670956fb0a3edd44ce6bc4dedc77c30cfc14f40034044739");
        checkGolden(fromUtf8("cGxhaW4tYmVmb3JlIm1pZGRsZVx0YWlsCAwKDQkvZW5k"), decoded("InBsYWluLWJlZm9yZVwibWlkZGxlXFx0YWlsXGJcZlxuXHJcdC9lbmQi"), "ffbaed4acf51d74bcb46e9820b0d5c18b3ae8eb56e0a6bd5691378df1cb1da3f");
        checkGolden(fromUtf8("L3/CgMO/xIDmsYnigKjigKntn7/ugIDvv73vv78="), decoded("Ii9/woDDv8SA5rGJ4oCo4oCp7Z+/7oCA77+977+/Ig=="), "e2f38ea64fee7ac2b3023f3056c6bc1d1ea0717c2470057c9a655e02528e9feb");
        checkGolden(fromUtf8("YmVmb3Jl8JCAgG1pZGRsZfCfmIBhZnRlcvSPv79lbmQ="), decoded("ImJlZm9yZfCQgIBtaWRkbGXwn5iAYWZ0ZXL0j7+/ZW5kIg=="), "55c7b4e1fc2777488b2a462adf61ec7bc1fe3ec9e2bf199de4be312dfea5ed4f");
        checkGolden(fromUtf8("Ilx4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHgKeXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXkJ"), decoded("IlwiXFx4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHhcbnl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5XHQi"), "0a41c984560f2d6b3d1522f36558f415ef4540f33e6015d5d8ed3da63052fc47");
    }

    @Test void nestedCanonicalHashRetainsCodePointKeyOrderAndEscapes() {
        ObjectNode value = ContinuityJson.parseObject(decoded("eyJcdWUwMDAiOiAiYm1wLWtleSIsICJcdWQ4MDBcdWRjMDAiOiAic3VwcGxlbWVudGFyeS1rZXkiLCAiYSI6IFsiXHUwMDAwXHUwMDAxXHUwMDAyXHUwMDAzXHUwMDA0XHUwMDA1XHUwMDA2XHUwMDA3XGJcdFxuXHUwMDBiXGZcclx1MDAwZVx1MDAwZlx1MDAxMFx1MDAxMVx1MDAxMlx1MDAxM1x1MDAxNFx1MDAxNVx1MDAxNlx1MDAxN1x1MDAxOFx1MDAxOVx1MDAxYVx1MDAxYlx1MDAxY1x1MDAxZFx1MDAxZVx1MDAxZiIsICJiZWZvcmVcdWQ4MDBcdWRjMDBtaWRkbGVcdWQ4M2RcdWRlMDBhZnRlclx1ZGJmZlx1ZGZmZmVuZCIsIHsicXVvdGVkXCJrZXkiOiAiXHUyMDI4L3JhdyJ9XX0="), ContinuityJson.DOCUMENT_MAX_BYTES);
        assertArrayEquals(decoded("eyJhIjpbIlx1MDAwMFx1MDAwMVx1MDAwMlx1MDAwM1x1MDAwNFx1MDAwNVx1MDAwNlx1MDAwN1xiXHRcblx1MDAwYlxmXHJcdTAwMGVcdTAwMGZcdTAwMTBcdTAwMTFcdTAwMTJcdTAwMTNcdTAwMTRcdTAwMTVcdTAwMTZcdTAwMTdcdTAwMThcdTAwMTlcdTAwMWFcdTAwMWJcdTAwMWNcdTAwMWRcdTAwMWVcdTAwMWYiLCJiZWZvcmXwkICAbWlkZGxl8J+YgGFmdGVy9I+/v2VuZCIseyJxdW90ZWRcImtleSI6IuKAqC9yYXcifV0sIu6AgCI6ImJtcC1rZXkiLCLwkICAIjoic3VwcGxlbWVudGFyeS1rZXkifQ=="), ContinuityJson.canonical(value));
        assertEquals("9ac08eb6c6433e59c82b89bc6c1e8b94e24d0e2c3f9ac9fc202a64a63f96a9a8", ContinuityJson.digest(value));
    }

    @Test void invalidUtf16ValuesAndKeysRetainExactRejection() {
        String[] invalid = {
            new String(new char[] {(char) 0xd800}),
            new String(new char[] {(char) 0xdc00}),
            new String(new char[] {(char) 0x0041, (char) 0xd800, (char) 0x0042}),
            new String(new char[] {(char) 0xd800, (char) 0xd800}),
            new String(new char[] {(char) 0xdc00, (char) 0xd800}),
            new String(new char[] {(char) 0xd800, (char) 0xdc00, (char) 0xdc00}),
            new String(new char[] {(char) 0x0061, (char) 0x0022, (char) 0xd800}),
        };
        for (String value : invalid) {
            var failure = assertThrows(ContractViolationException.class, () -> ContinuityJson.canonical(text(value)));
            assertEquals("unpaired continuity Unicode surrogate", failure.getMessage());
        }
        ObjectNode invalidKey = StrictJson.object().put(new String(new char[] {(char) 0xdc00}), "value");
        var failure = assertThrows(ContractViolationException.class, () -> ContinuityJson.canonical(invalidKey));
        assertEquals("unpaired continuity Unicode surrogate", failure.getMessage());
    }

    @Test void utf8BudgetAndNullFailuresRetainPublicContract() {
        var value = text(fromUtf8("L3/CgMO/xIDmsYnigKjigKntn7/ugIDvv73vv78="));
        byte[] expected = decoded("Ii9/woDDv8SA5rGJ4oCo4oCp7Z+/7oCA77+977+/Ig==");
        assertArrayEquals(expected, ContinuityJson.canonical(value, expected.length));
        var tooSmall = assertThrows(ContractViolationException.class, () -> ContinuityJson.canonical(value, expected.length - 1));
        assertEquals("continuity JSON exceeds byte budget", tooSmall.getMessage());
        for (int maximum : new int[] {0, ContinuityJson.DOMAIN_MAX_BYTES + 1}) {
            var invalidBound = assertThrows(ContractViolationException.class, () -> ContinuityJson.canonical(value, maximum));
            assertEquals("bounded continuity JSON", invalidBound.getMessage());
        }
        assertThrows(NullPointerException.class, () -> ContinuityJson.canonical(null));
    }

    @Test void mutableTreeIsReencodedOnEachInvocation() {
        ObjectNode value = StrictJson.object().put("value", "before\ud83d\ude00");
        byte[] first = ContinuityJson.canonical(value);
        assertArrayEquals(decoded("eyJ2YWx1ZSI6ImJlZm9yZfCfmIAifQ=="), first);
        assertEquals("215afe91a5d7b437a832b3013eece48afe359e604fec50061ab783bc6d8eac80", ContinuityJson.digest(value));
        value.put("value", "after\n");
        assertArrayEquals(decoded("eyJ2YWx1ZSI6ImFmdGVyXG4ifQ=="), ContinuityJson.canonical(value));
        assertEquals("469ded906453824cad34a5cac8cc222552e8a06025f0cd9a5a9b9346973d1e17", ContinuityJson.digest(value));
        first[0] = 0;
        assertEquals('{', ContinuityJson.canonical(value)[0]);
    }

    private static void checkGolden(String input, byte[] expected, String expectedDigest) {
        JsonNode value = text(input);
        assertArrayEquals(expected, ContinuityJson.canonical(value));
        assertEquals(expectedDigest, ContinuityJson.digest(value));
    }
}
