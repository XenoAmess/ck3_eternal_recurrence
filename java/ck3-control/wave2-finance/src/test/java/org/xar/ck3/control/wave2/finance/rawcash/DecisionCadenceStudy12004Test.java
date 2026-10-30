package org.xar.ck3.control.wave2.finance.rawcash;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
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

    @Test void nativeProjectionAndSignedComparisonMatchOriginalMachineCodeCorpus() throws Exception {
        try (var input = getClass().getResourceAsStream("decision-precheck-12004-native-tail.txt")) {
            assertNotNull(input, "actual owned native-tail corpus");
            var lines = new String(input.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8).lines().toList();
            assertEquals(87, lines.size());
            for (String row : lines.subList(1, lines.size())) {
                String[] fields = row.split("\\|", -1);
                List<Long> costs = java.util.Arrays.stream(fields[1].split(",")).map(Long::valueOf).toList();
                List<Long> budget = java.util.Arrays.stream(fields[2].split(",")).map(Long::valueOf).toList();
                assertEquals(ResourcePrecheck.valueOf(fields[3]),
                        DecisionCadenceStudy12004.resourcePrecheck(costs, budget), fields[0]);
            }
        }
    }

    @Test void contextBudgetRequiresEightSlotsRatherThanTenResourceWallet() {
        List<Long> costs = java.util.Collections.nCopies(10, 0L);
        assertEquals(ResourcePrecheck.NATIVE_FINAL_GATES_REQUIRED,
                DecisionCadenceStudy12004.resourcePrecheck(costs, java.util.Collections.nCopies(8, 0L)));
        assertThrows(IllegalArgumentException.class, () -> DecisionCadenceStudy12004.resourcePrecheck(
                costs, java.util.Collections.nCopies(10, 0L)));
        assertThrows(IllegalArgumentException.class, () -> DecisionCadenceStudy12004.resourcePrecheck(
                java.util.Collections.nCopies(8, 0L), java.util.Collections.nCopies(8, 0L)));
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
