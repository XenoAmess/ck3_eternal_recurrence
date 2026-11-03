package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

class PublicDataJsonSortedPublicBoundaryTest {
    @Test
    void naturalKeysArraysAndNumberCallbacksKeepTheirPublicOrder() {
        var successCalls = new ArrayList<String>();
        var shared = new RecordingInteger("shared", "7", successCalls, 0, null);
        var nestedA = new RecordingInteger("nested-a", "3", successCalls, 0, null);
        var nestedZ = new RecordingInteger("nested-z", "4", successCalls, 0, null);
        var value = unorderedGraph(shared, nestedA, nestedZ, null);

        String expected = "{\"a\":[7,{\"a\":3,\"z\":4}],\"z\":7,\"\uD800\uDC00\":\"supp\",\"\uE000\":\"bmp\"}";
        assertArrayEquals(expected.getBytes(StandardCharsets.UTF_8),
                PublicDataJson.encodeTypedBytes(value, 4096));
        assertEquals(List.of("shared:1", "nested-a:1", "nested-z:1", "shared:2"), successCalls);

        var failureCalls = new ArrayList<String>();
        var cause = new IllegalArgumentException("caller-owned cause");
        var marker = new IllegalStateException("second number callback", cause);
        var throwingShared = new RecordingInteger("shared", "7", failureCalls, 2, marker);
        var failureValue = unorderedGraph(throwingShared,
                new RecordingInteger("nested-a", "3", failureCalls, 0, null),
                new RecordingInteger("nested-z", "4", failureCalls, 0, null),
                new RecordingInteger("later", "9", failureCalls, 0, null));

        var failure = assertThrows(IllegalStateException.class,
                () -> PublicDataJson.encodeTypedBytes(failureValue, 4096));
        assertSame(marker, failure);
        assertSame(cause, failure.getCause());
        assertEquals(List.of("shared:1", "nested-a:1", "nested-z:1", "shared:2"), failureCalls);
    }

    @Test
    void typedValidationPrecedesNumberCallbacksAndReportsTheFirstFailure() {
        var nullKeyCalls = new ArrayList<String>();
        var nullKeyNumber = new RecordingInteger("null-key-number", "7", nullKeyCalls, 1,
                new IllegalStateException("null key must fail first"));
        var nullKeyMembers = new LinkedHashMap<String, OpportunityJson.Value>();
        nullKeyMembers.put("ok", nested(new OpportunityJson.IntegerValue(nullKeyNumber), 65, false));
        nullKeyMembers.put(null, OpportunityJson.Nil.INSTANCE);
        var nullKeyObject = assertDoesNotThrow(() -> new OpportunityJson.Obj(nullKeyMembers));
        assertTrue(nullKeyObject.members().containsKey(null));

        var nullKeyFailure = assertThrows(NullPointerException.class,
                () -> PublicDataJson.encodeTypedBytes(nullKeyObject, 4096));
        assertEquals(NullPointerException.class, nullKeyFailure.getClass());
        assertEquals(List.of(), nullKeyCalls);

        var nullValueCalls = new ArrayList<String>();
        var nullValueMembers = new LinkedHashMap<String, OpportunityJson.Value>();
        nullValueMembers.put("z", null);
        nullValueMembers.put("a", new OpportunityJson.IntegerValue(new RecordingInteger(
                "null-value-number", "7", nullValueCalls, 1,
                new IllegalStateException("typed null must fail first"))));
        var nullValueObject = assertDoesNotThrow(() -> new OpportunityJson.Obj(nullValueMembers));
        assertTrue(nullValueObject.members().containsKey("z"));
        assertNull(nullValueObject.get("z"));

        var nullValueFailure = assertThrows(ContractViolationException.class,
                () -> PublicDataJson.encodeTypedBytes(nullValueObject, 4096));
        assertEquals("bounded typed public DATA required", nullValueFailure.getMessage());
        assertNull(nullValueFailure.getCause());
        assertEquals(List.of(), nullValueCalls);

        var unicodeCalls = new ArrayList<String>();
        var unicodeMembers = new LinkedHashMap<String, OpportunityJson.Value>();
        unicodeMembers.put("z", new OpportunityJson.Text("\uD800"));
        unicodeMembers.put("a", new OpportunityJson.IntegerValue(new RecordingInteger(
                "unicode-number", "7", unicodeCalls, 1,
                new IllegalStateException("Unicode must fail before the first number callback"))));
        var unicodeObject = new OpportunityJson.Obj(unicodeMembers);

        var unicodeFailure = assertThrows(ContractViolationException.class,
                () -> PublicDataJson.encodeTypedBytes(unicodeObject, 4096));
        assertEquals("unpaired JSON high surrogate", unicodeFailure.getMessage());
        assertNull(unicodeFailure.getCause());
        assertEquals(List.of(), unicodeCalls);
    }

    @Test
    void objectAndArrayValuesAtDepth64SucceedAndAt65FailBeforeCallbacks() {
        for (boolean objects : new boolean[] {false, true}) {
            String kind = objects ? "object" : "array";
            var acceptedCalls = new ArrayList<String>();
            var acceptedLeaf = new OpportunityJson.IntegerValue(new RecordingInteger(
                    kind + "-64", "7", acceptedCalls, 0, null));
            var acceptedValue = nested(acceptedLeaf, 64, objects);
            String expected = objects
                    ? "{\"n\":".repeat(64) + "7" + "}".repeat(64)
                    : "[".repeat(64) + "7" + "]".repeat(64);

            assertArrayEquals(expected.getBytes(StandardCharsets.UTF_8),
                    PublicDataJson.encodeTypedBytes(acceptedValue, 4096), kind);
            assertEquals(List.of(kind + "-64:1"), acceptedCalls, kind);

            var rejectedCalls = new ArrayList<String>();
            var rejectedLeaf = new OpportunityJson.IntegerValue(new RecordingInteger(
                    kind + "-65", "7", rejectedCalls, 1,
                    new IllegalStateException("depth must fail before the number callback")));
            var rejectedValue = nested(rejectedLeaf, 65, objects);

            var failure = assertThrows(ContractViolationException.class,
                    () -> PublicDataJson.encodeTypedBytes(rejectedValue, 4096), kind);
            assertEquals("bounded typed public DATA required", failure.getMessage(), kind);
            assertNull(failure.getCause(), kind);
            assertEquals(List.of(), rejectedCalls, kind);
        }
    }

    private static OpportunityJson.Obj unorderedGraph(RecordingInteger shared,
            RecordingInteger nestedA, RecordingInteger nestedZ, RecordingInteger later) {
        var nestedMembers = new LinkedHashMap<String, OpportunityJson.Value>();
        nestedMembers.put("z", new OpportunityJson.IntegerValue(nestedZ));
        nestedMembers.put("a", new OpportunityJson.IntegerValue(nestedA));
        var rootMembers = new LinkedHashMap<String, OpportunityJson.Value>();
        rootMembers.put("\uE000", new OpportunityJson.Text("bmp"));
        rootMembers.put("\uD800\uDC00", new OpportunityJson.Text("supp"));
        rootMembers.put("z", new OpportunityJson.IntegerValue(shared));
        rootMembers.put("a", new OpportunityJson.Arr(List.of(
                new OpportunityJson.IntegerValue(shared), new OpportunityJson.Obj(nestedMembers))));
        if (later != null) {
            rootMembers.put("zz", new OpportunityJson.IntegerValue(later));
        }
        return new OpportunityJson.Obj(rootMembers);
    }

    private static OpportunityJson.Value nested(OpportunityJson.Value leaf, int levels, boolean objects) {
        OpportunityJson.Value result = leaf;
        for (int index = 0; index < levels; index++) {
            result = objects
                    ? new OpportunityJson.Obj(Map.of("n", result))
                    : new OpportunityJson.Arr(List.of(result));
        }
        return result;
    }

    private static final class RecordingInteger extends BigInteger {
        private static final long serialVersionUID = 1L;
        private final String label;
        private final transient List<String> calls;
        private final int failAt;
        private final RuntimeException failure;
        private int occurrence;

        private RecordingInteger(String label, String decimal, List<String> calls,
                int failAt, RuntimeException failure) {
            super(decimal);
            this.label = label;
            this.calls = calls;
            this.failAt = failAt;
            this.failure = failure;
        }

        @Override
        public String toString() {
            occurrence++;
            calls.add(label + ":" + occurrence);
            if (occurrence == failAt) {
                throw failure;
            }
            return super.toString();
        }
    }
}
