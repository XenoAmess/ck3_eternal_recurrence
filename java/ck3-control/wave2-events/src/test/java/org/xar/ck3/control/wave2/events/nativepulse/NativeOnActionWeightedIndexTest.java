package org.xar.ck3.control.wave2.events.nativepulse;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;

class NativeOnActionWeightedIndexTest {
    private static NativeOnActionWeightedIndex.Row constant(int index, int weight) {
        return new NativeOnActionWeightedIndex.Row(index, weight, new NativeOnActionWeightedIndex.Constant());
    }
    private static NativeOnActionWeightedIndex.Result run(List<NativeOnActionWeightedIndex.Row> rows, int random) {
        return NativeOnActionWeightedIndex.evaluate(new NativeOnActionWeightedIndex.Input(
            NativePlayableAnnualGate.Executable.CURRENT_12004, rows, random));
    }
    private static NativeOnActionWeightedIndex.Computed computed(List<NativeOnActionWeightedIndex.Row> rows, int random) {
        return assertInstanceOf(NativeOnActionWeightedIndex.Computed.class, run(rows, random));
    }
    @Test void actualOrderedPositivePrefixSelectionDiffersFromModulo() {
        List<NativeOnActionWeightedIndex.Row> rows = List.of(constant(7, -2), constant(2, 1), constant(5, 3));
        assertEquals(2, computed(rows, 0).originalRowIndex().orElseThrow());
        assertEquals(5, computed(rows, 0x40000000).originalRowIndex().orElseThrow());
        var output = computed(rows, Integer.MAX_VALUE);
        assertEquals(3, output.floatingTarget()); assertEquals(5, output.originalRowIndex().orElseThrow());
        assertFalse(output.eventDispatched()); assertFalse(output.liveSelectionCreditGranted());
        assertNotEquals(0x40000000 % 4, computed(rows, 0x40000000).floatingTarget());
    }
    @Test void nativeInt32PreGateMayWrapToZeroBeforeTheInt64Helper() {
        var output = computed(List.of(constant(0, Integer.MAX_VALUE), constant(1, Integer.MAX_VALUE), constant(2, 2)), 123);
        assertEquals(0, output.nativePositiveSum32()); assertEquals(0x100000000L, output.positiveSum64());
        assertEquals(NativeOnActionWeightedIndex.Status.NATIVE_INT32_SUM_ZERO, output.status());
        assertTrue(output.originalRowIndex().isEmpty());
        var negativeWrappedGate = computed(List.of(constant(0, Integer.MAX_VALUE), constant(1, 1)), 0);
        assertEquals(Integer.MIN_VALUE, negativeWrappedGate.nativePositiveSum32());
        assertEquals(NativeOnActionWeightedIndex.Status.INDEX_CHOSEN, negativeWrappedGate.status());
    }
    @Test void signedProductWrapDivisionAndNarrowingMatchAnIndependentIntegerOracle() {
        int[] bases = {Integer.MIN_VALUE, -77, 0, 1, 999999, Integer.MAX_VALUE};
        long[] rawValues = {Long.MIN_VALUE, -100001, -1, 0, 1, 100000, Long.MAX_VALUE};
        BigInteger modulus = BigInteger.ONE.shiftLeft(64);
        for (int base : bases) for (long raw : rawValues) {
            BigInteger wrapped = BigInteger.valueOf(base).multiply(BigInteger.valueOf(raw)).mod(modulus);
            if (wrapped.testBit(63)) wrapped = wrapped.subtract(modulus);
            int expected = wrapped.divide(BigInteger.valueOf(100000)).intValue();
            assertEquals(expected, NativeOnActionWeightedIndex.scriptedWeight(base, raw));
        }
    }
    @Test void missingActualEvaluationCannotBeInventedAsZeroWeight() {
        var unavailable = new NativeOnActionWeightedIndex.Row(11, 100, new NativeOnActionWeightedIndex.Unavailable("actual AST result unavailable"));
        assertInstanceOf(NativeOnActionWeightedIndex.Unresolved.class, run(List.of(constant(3, 1), unavailable), 0));
        var excluded = new NativeOnActionWeightedIndex.Row(11, 100, new NativeOnActionWeightedIndex.Excluded());
        assertEquals(3, computed(List.of(constant(3, 1), excluded), 0).originalRowIndex().orElseThrow());
        assertThrows(IllegalArgumentException.class, () -> run(List.of(constant(3, 1), constant(3, 2)), 0));
        assertThrows(IllegalArgumentException.class, () -> run(List.of(constant(3, 1)), -1));
    }
    @Test void definedRowsApplyTheModifierBeforeThePositiveWeightTest() {
        var scripted = new NativeOnActionWeightedIndex.Row(9, -100, new NativeOnActionWeightedIndex.Scripted(-100000));
        var output = computed(List.of(constant(4, -100), scripted), 0);
        assertEquals(100, output.positiveSum64());
        assertEquals(9, output.originalRowIndex().orElseThrow());
    }
}
