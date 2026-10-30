package org.xar.ck3.control.wave2.finance.rawcash;

import java.util.List;
import java.util.Objects;

/** Exact-image offline study. These predicates never qualify a native action, a quote, or funds. */
public final class DecisionCadenceStudy12004 {
    private DecisionCadenceStudy12004() { }

    private static final List<Integer> AI_COST_INDICES = List.of(0, 1, 2, 4, 5, 6, 8, 9);

    public enum IndexPartition { INTERVAL_TIER, GOAL_PARTITION }
    public enum Due { DISABLED_BY_INTERVAL, NOT_DUE, NATIVE_EVALUATION_REQUIRED }
    public enum ResourcePrecheck { REJECTED, NATIVE_FINAL_GATES_REQUIRED }


    public enum ActorMonthGate { NOT_DUE, NATIVE_ACTOR_FLAGS_AND_REBUILD_REQUIRED }

    /**
     * Exact native AI research parity only. Calendar days/day are copied native inputs.
     * This gate must never suppress legal opportunities in the player planner.
     */
    public record ActorMonthGateInputs(long actorFullId, int nativeMonthDays, int nativeZeroBasedDay) {
        public ActorMonthGateInputs {
            if (actorFullId < 0 || actorFullId >= 0xffff_ffffL
                    || nativeMonthDays < 1 || nativeMonthDays > Byte.MAX_VALUE
                    || nativeZeroBasedDay < 0 || nativeZeroBasedDay >= nativeMonthDays) {
                throw new IllegalArgumentException("exact full CharacterID/native calendar month/day required");
            }
        }
    }

    /**
     * Native 19EA5C0 -> 2BD7B90 uses signed32 IDIV, preserving high-bit CharacterIDs.
     * This actor gate precedes the separate per-definition interval gate in due().
     * 19EA5C0 itself mutates AI-brain counters and is never a read-only query.
     */
    public static ActorMonthGate actorMonthGate(ActorMonthGateInputs inputs) {
        Objects.requireNonNull(inputs, "inputs");
        int signedNativeFullId = (int) inputs.actorFullId();
        return signedNativeFullId % inputs.nativeMonthDays() == inputs.nativeZeroBasedDay()
                ? ActorMonthGate.NATIVE_ACTOR_FLAGS_AND_REBUILD_REQUIRED : ActorMonthGate.NOT_DUE;
    }

    /** Month ordinal must be supplied by the native calendar owner; this class does not invent one from date_raw. */
    public record ScheduleInputs(long actorFullId, int definitionOrdinal, int nativeMonthOrdinal,
            int intervalMonths) {
        public ScheduleInputs {
            if (actorFullId < 0 || actorFullId >= 0xffff_ffffL) {
                throw new IllegalArgumentException("current full unsigned CharacterID required");
            }
        }
    }

    /**
     * 1ACA5F0..606 and 1ACA6BA..6DC. Java int overflow is intentional x86 low32 arithmetic.
     * The GOAL_PARTITION branch bypasses this interval test, but must still run native eligibility and scoring.
     */
    public static Due due(IndexPartition partition, ScheduleInputs inputs) {
        Objects.requireNonNull(partition, "partition");
        Objects.requireNonNull(inputs, "inputs");
        if (partition == IndexPartition.GOAL_PARTITION) { return Due.NATIVE_EVALUATION_REQUIRED; }
        if (inputs.intervalMonths() <= 0) { return Due.DISABLED_BY_INTERVAL; }
        int actorMonthPhase = ((int) inputs.actorFullId() * 0x1115
                + inputs.nativeMonthOrdinal() * 0x16d3) & Integer.MAX_VALUE;
        int numerator = inputs.definitionOrdinal() * 0x1c73 + actorMonthPhase;
        return numerator % inputs.intervalMonths() == 0 ? Due.NATIVE_EVALUATION_REQUIRED : Due.NOT_DUE;
    }

    /**
     * 1ACAA25..ADE projects the ten signed costs into context budget order
     * [0,1,2,4,5,6,8,9]. The actual caller supplies eight context budgets,
     * not a ten-resource wallet. Positive costs must be strictly below budget;
     * nonpositive costs skip comparison. Final native gates remain required.
     */
    public static ResourcePrecheck resourcePrecheck(List<Long> nativeTenCosts, List<Long> nativeContextBudget) {
        List<Long> costs = slots(nativeTenCosts, 10), budget = slots(nativeContextBudget, 8);
        for (int index = 0; index < AI_COST_INDICES.size(); index++) {
            long cost = costs.get(AI_COST_INDICES.get(index));
            if (cost > 0 && cost >= budget.get(index)) { return ResourcePrecheck.REJECTED; }
        }
        return ResourcePrecheck.NATIVE_FINAL_GATES_REQUIRED;
    }

    /**
     * 1A2C7D1..7EF and 1AA9F20..F3A compare a seeded [0,99] draw with the native integer score.
     * This is a per-candidate percentage gate, not a highest-score sort and not a lender-selection rule.
     */
    public static boolean passesPercentageGate(int nativeScore, int nativeDraw0To99) {
        if (nativeDraw0To99 < 0 || nativeDraw0To99 > 99) {
            throw new IllegalArgumentException("native percentage draw must be in 0..99");
        }
        return nativeDraw0To99 < nativeScore;
    }

    /** 1ACABE7..1ACAC1B floors negative nonintegral fixed values before storing the low signed32. */
    public static int copiedScoreFromFixed(long nativeFixedRaw) {
        return (int) Math.floorDiv(nativeFixedRaw, 100_000L);
    }

    private static List<Long> slots(List<Long> values, int count) {
        Objects.requireNonNull(values, "native signed slots");
        if (values.size() != count) { throw new IllegalArgumentException("exact " + count + " signed slots required"); }
        return List.copyOf(values);
    }
}
