package org.xar.ck3.control.wave2.finance.rawcash;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave2.finance.rawcash.DecisionCadenceStudy12004.Due;
import org.xar.ck3.control.wave2.finance.rawcash.DecisionCadenceStudy12004.IndexPartition;
import org.xar.ck3.control.wave2.finance.rawcash.DecisionCadenceStudy12004.ResourcePrecheck;
import org.xar.ck3.control.wave2.finance.rawcash.DecisionCadenceStudy12004.ScheduleInputs;

class DecisionCadenceStudy12004Test {

    @Test void actorDayGatePreservesSignedNativeRemainderBeforeDefinitionMonthCadence() {
        for (long actor : new long[] {0, 1, 29829, 0x8000_0000L, 0xffff_ffe0L, 0xffff_fffeL}) {
            BigInteger signedId = BigInteger.valueOf(actor);
            if (actor >= 0x8000_0000L) { signedId = signedId.subtract(BigInteger.ONE.shiftLeft(32)); }
            for (int days : new int[] {28, 29, 30, 31}) {
                for (int day = 0; day < days; day++) {
                    var input = new DecisionCadenceStudy12004.ActorMonthGateInputs(actor, days, day);
                    boolean independentlyDue = signedId.remainder(BigInteger.valueOf(days)).equals(BigInteger.valueOf(day));
                    assertEquals(independentlyDue
                            ? DecisionCadenceStudy12004.ActorMonthGate.NATIVE_ACTOR_FLAGS_AND_REBUILD_REQUIRED
                            : DecisionCadenceStudy12004.ActorMonthGate.NOT_DUE,
                            DecisionCadenceStudy12004.actorMonthGate(input));
                }
            }
        }
        // Native signed -32 % 31 is -1. Unsigned/floor-mod substitutions would open a different day.
        assertEquals(DecisionCadenceStudy12004.ActorMonthGate.NOT_DUE, DecisionCadenceStudy12004.actorMonthGate(
                new DecisionCadenceStudy12004.ActorMonthGateInputs(0xffff_ffe0L, 31, 30)));
        assertEquals(DecisionCadenceStudy12004.ActorMonthGate.NATIVE_ACTOR_FLAGS_AND_REBUILD_REQUIRED,
                DecisionCadenceStudy12004.actorMonthGate(new DecisionCadenceStudy12004.ActorMonthGateInputs(0, 28, 0)));
        for (long actor : new long[] {-1, 0xffff_ffffL, 0x1_0000_0000L}) {
            assertThrows(IllegalArgumentException.class, () -> new DecisionCadenceStudy12004.ActorMonthGateInputs(actor, 31, 0));
        }
        assertThrows(IllegalArgumentException.class, () -> new DecisionCadenceStudy12004.ActorMonthGateInputs(1, 0, 0));
        assertThrows(IllegalArgumentException.class, () -> new DecisionCadenceStudy12004.ActorMonthGateInputs(1, 31, -1));
        assertThrows(IllegalArgumentException.class, () -> new DecisionCadenceStudy12004.ActorMonthGateInputs(1, 31, 31));
    }

    @Test void zeroAndNegativeIntervalsNeverScheduleOrdinaryButDoNotSuppressGoalPartition() {
        for (int interval : new int[] {Integer.MIN_VALUE, -1, 0}) {
            ScheduleInputs input = new ScheduleInputs(29829, 17, 12800, interval);
            assertEquals(Due.DISABLED_BY_INTERVAL, DecisionCadenceStudy12004.due(IndexPartition.INTERVAL_TIER, input));
            assertEquals(Due.NATIVE_EVALUATION_REQUIRED, DecisionCadenceStudy12004.due(IndexPartition.GOAL_PARTITION, input));
        }
    }

    @Test void arithmeticMatchesIndependentLow32ModelAcrossFullUnsignedIdsAndOverflow() {
        for (long actor : new long[] {0, 1, 29829, 0x8000_0000L, 0xffff_fffeL}) {
            for (int definition : new int[] {1, 377, Integer.MAX_VALUE, Integer.MIN_VALUE}) {
                for (int month : new int[] {0, 12800, Integer.MAX_VALUE, Integer.MIN_VALUE}) {
                    ScheduleInputs input = new ScheduleInputs(actor, definition, month, 72);
                    BigInteger mask = new BigInteger("ffffffff", 16);
                    BigInteger phase = BigInteger.valueOf(actor).multiply(BigInteger.valueOf(0x1115))
                            .add(BigInteger.valueOf(month).multiply(BigInteger.valueOf(0x16d3))).and(mask)
                            .and(BigInteger.valueOf(Integer.MAX_VALUE));
                    int signedNumerator = BigInteger.valueOf(definition).multiply(BigInteger.valueOf(0x1c73))
                            .add(phase).and(mask).intValue();
                    Due expected = signedNumerator % 72 == 0 ? Due.NATIVE_EVALUATION_REQUIRED : Due.NOT_DUE;
                    assertEquals(expected, DecisionCadenceStudy12004.due(IndexPartition.INTERVAL_TIER, input));
                }
            }
        }
        assertThrows(IllegalArgumentException.class, () -> new ScheduleInputs(0xffff_ffffL, 1, 1, 72));
    }

    @Test void nativeEightSlotPrecheckRejectsEqualityAndPreservesUninspectedSlots() {
        List<Long> resources = new ArrayList<>(List.of(100L,100L,100L,100L,100L,100L,100L,100L,0L,0L));
        List<Long> costs = new ArrayList<>(List.of(0L,0L,0L,0L,0L,0L,0L,0L,Long.MAX_VALUE,Long.MAX_VALUE));
        assertEquals(ResourcePrecheck.NATIVE_FINAL_GATES_REQUIRED,
                DecisionCadenceStudy12004.resourcePrecheck(costs, resources));
        costs.set(0, 100L);
        assertEquals(ResourcePrecheck.REJECTED, DecisionCadenceStudy12004.resourcePrecheck(costs, resources));
        costs.set(0, 99L);
        assertEquals(ResourcePrecheck.NATIVE_FINAL_GATES_REQUIRED,
                DecisionCadenceStudy12004.resourcePrecheck(costs, resources));
        costs.set(0, Long.MIN_VALUE);
        assertEquals(ResourcePrecheck.NATIVE_FINAL_GATES_REQUIRED,
                DecisionCadenceStudy12004.resourcePrecheck(costs, resources));
        assertThrows(IllegalArgumentException.class, () -> DecisionCadenceStudy12004.resourcePrecheck(List.of(0L), resources));
    }

    @Test void percentChanceAndFixedFloorDoNotTurnIntoCandidateRanking() {
        assertFalse(DecisionCadenceStudy12004.passesPercentageGate(0, 0));
        assertTrue(DecisionCadenceStudy12004.passesPercentageGate(50, 49));
        assertFalse(DecisionCadenceStudy12004.passesPercentageGate(50, 50));
        assertTrue(DecisionCadenceStudy12004.passesPercentageGate(100, 99));
        assertFalse(DecisionCadenceStudy12004.passesPercentageGate(-3, 0));
        assertEquals(-1, DecisionCadenceStudy12004.copiedScoreFromFixed(-99_999));
        assertEquals(-2, DecisionCadenceStudy12004.copiedScoreFromFixed(-100_001));
        assertThrows(IllegalArgumentException.class, () -> DecisionCadenceStudy12004.passesPercentageGate(50, 100));
    }
}
