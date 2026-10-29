package org.xar.ck3.control.g2.m6.nativeai;

import java.util.List;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.g2.m6.nativeai.NativeInteractionAi.*;

final class NativeInteractionAiTest {
    private static final int BASE = 0x29C55C0;

    @Test void phaseUsesUnsigned32SumAndPositiveRankFrequency() {
        assertTrue(phaseDue(0xFFFF_FFFEL, BASE + 365 * 24, 2));
        assertTrue(phaseDue(5, BASE, 5));
        assertFalse(phaseDue(5, BASE, 0));
        assertFalse(phaseDue(5, BASE, -5));
        assertThrows(IllegalArgumentException.class, () -> phaseDue(0xFFFF_FFFFL, BASE, 1));
    }

    @Test void senderScoresUseSignedTruncationAndEqualMarginRetainsFirst() {
        Result result = selectPreparedBlocks(List.of(new PreparedBlock(100000, 0,
                List.of(new Target(10, new Scored(1600000)), new Target(20, new Scored(4300000))))),
                new RandomState(0, 0));
        assertEquals(10, result.selectedTarget().orElseThrow());
        assertEquals(5, result.bestMargin());
        assertEquals(11, result.comparisons().get(0).marginDraw().orElseThrow());
        assertEquals(38, result.comparisons().get(1).marginDraw().orElseThrow());
        assertEquals(Disposition.NOT_BETTER, result.comparisons().get(1).disposition());
        assertEquals(4, result.randomAfter().counter());
        Result negative = selectPreparedBlocks(List.of(new PreparedBlock(100000, 0,
                List.of(new Target(10, new Scored(-99999))))), new RandomState(0, 0));
        assertTrue(negative.selectedTarget().isEmpty());
        assertEquals(-11, negative.comparisons().get(0).margin().orElseThrow());
    }

    @Test void nativeChanceIncludesEqualityAtZeroAndConsumesNoMarginForRejectedRows() {
        Result zero = selectPreparedBlocks(List.of(new PreparedBlock(0, 0,
                List.of(new Target(1, new Scored(10000000))))), new RandomState(115999, 0));
        assertEquals(0, zero.comparisons().get(0).chanceDraw());
        assertEquals(33, zero.bestMargin());
        Result rejected = selectPreparedBlocks(List.of(new PreparedBlock(-1, 0,
                List.of(new Target(1, new Scored(10000000))))), new RandomState(115999, 0));
        assertEquals(Disposition.CHANCE_REJECTED, rejected.comparisons().get(0).disposition());
        assertEquals(116000, rejected.randomAfter().counter());
        assertTrue(rejected.comparisons().get(0).margin().isEmpty());
    }

    @Test void trimUsesMaxTargetsAsModulusWhileCountIsLarger() {
        List<Target> targets = List.of(new Target(1, new Scored(20000000)),
                new Target(2, new Scored(20000000)), new Target(3, new Scored(20000000)),
                new Target(4, new Scored(20000000)), new Target(5, new Scored(20000000)));
        Result result = selectPreparedBlocks(List.of(new PreparedBlock(100000, 2, targets)),
                new RandomState(0, 0));
        assertEquals(List.of(5L, 3L), result.comparisons().stream().map(Comparison::targetFullId).toList());
        assertEquals(3, result.selectedTarget().orElseThrow());
        assertEquals(200, result.bestMargin());
        assertEquals(7, result.randomAfter().counter());
    }

    @Test void preparationRejectionAndEmptyInputNeverInventScoreOrSelection() {
        Result result = selectPreparedBlocks(List.of(new PreparedBlock(100000, 0,
                List.of(new Target(1, new Rejected())))), new RandomState(0, 0));
        assertEquals(Disposition.PREPARATION_REJECTED, result.comparisons().get(0).disposition());
        assertTrue(result.selectedTarget().isEmpty());
        assertEquals(1, result.randomAfter().counter());
        assertEquals(new RandomState(99, 7), selectPreparedBlocks(List.of(),
                new RandomState(99, 7)).randomAfter());
    }
}
