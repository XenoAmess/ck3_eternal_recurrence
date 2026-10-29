package org.xar.ck3.control.wave2.events.nativepulse;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.OptionalInt;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Actual .4 random-on-action weight/picker arithmetic. The caller must supply
 * original ordered native rows and independent current predicate/evaluator
 * outcomes. This class does not implement chance gates, the AST evaluator,
 * loaded-script merge, native RNG mutation, dispatch or live event selection.
 */
public final class NativeOnActionWeightedIndex {
    private NativeOnActionWeightedIndex() { }
    public sealed interface Evaluation permits Excluded, Constant, Scripted, Unavailable { }
    /** Actual contextual trigger failed. */
    public record Excluded() implements Evaluation { }
    /** Trigger passed with no scripted weight modifier, or actual null-definition sentinel. */
    public record Constant() implements Evaluation { }
    /** Actual contextual trigger passed and the real evaluator returned this signed fixed-point raw value. */
    public record Scripted(long rawValue) implements Evaluation { }
    public record Unavailable(String diagnosis) implements Evaluation {
        public Unavailable { StrictJson.require(diagnosis != null && !diagnosis.isBlank(), "diagnosis required"); }
    }
    public record Row(int originalIndex, int baseWeight, Evaluation evaluation) {
        public Row {
            StrictJson.require(originalIndex >= 0, "original native row index required");
            Objects.requireNonNull(evaluation);
        }
    }
    public record Input(NativePlayableAnnualGate.Executable executable, List<Row> originalOrder, int random31) {
        public Input {
            Objects.requireNonNull(executable); originalOrder = List.copyOf(originalOrder);
            StrictJson.require(random31 >= 0, "native sign-bit-cleared random31 required");
            HashSet<Integer> indexes = new HashSet<>();
            for (Row row : originalOrder) StrictJson.require(indexes.add(row.originalIndex()), "native row index repeated");
        }
    }
    public record EffectiveRow(int originalIndex, int nativeWeight) { }
    public sealed interface Result permits Unresolved, Computed { }
    public record Unresolved(int originalIndex, String diagnosis) implements Result {
        public Unresolved { Objects.requireNonNull(diagnosis); }
    }
    public enum Status { NATIVE_INT32_SUM_ZERO, INDEX_CHOSEN, HELPER_DEFAULT }
    public record Computed(List<EffectiveRow> rows, int nativePositiveSum32, long positiveSum64,
                           long floatingTarget, OptionalInt originalRowIndex, Status status) implements Result {
        public Computed {
            rows = List.copyOf(rows); Objects.requireNonNull(originalRowIndex); Objects.requireNonNull(status);
        }
        public boolean eventDispatched() { return false; }
        public boolean liveSelectionCreditGranted() { return false; }
    }
    /**
     * 37CB189..37CB1AA: signed low64 multiplication, signed /100000, then native
     * int32 narrowing. Overflow is preserved rather than replaced with BigInteger.
     */
    public static int scriptedWeight(int baseWeight, long scriptedRaw) {
        long wrappedProduct = baseWeight * scriptedRaw;
        return (int) (wrappedProduct / 100000L);
    }
    public static Result evaluate(Input input) {
        Objects.requireNonNull(input);
        List<EffectiveRow> rows = new ArrayList<>(); int sum32 = 0; long sum64 = 0;
        for (Row row : input.originalOrder()) {
            Evaluation evaluation = row.evaluation();
            if (evaluation instanceof Unavailable unavailable) return new Unresolved(row.originalIndex(), unavailable.diagnosis());
            int weight;
            if (evaluation instanceof Excluded) weight = 0;
            else if (evaluation instanceof Scripted scripted) weight = scriptedWeight(row.baseWeight(), scripted.rawValue());
            else weight = row.baseWeight();
            // 37CB1AD/37CB1AF positive-only admission. Non-positive weights never enter the helper.
            if (weight <= 0) weight = 0;
            rows.add(new EffectiveRow(row.originalIndex(), weight));
            sum32 += weight; sum64 += weight;
        }
        // 37CB334 checks the wrapped int32 sum before invoking the positive64-sum helper.
        if (sum32 == 0) return new Computed(rows, sum32, sum64, 0, OptionalInt.empty(), Status.NATIVE_INT32_SUM_ZERO);
        // 3FAAB50 uses IEEE754 multiplication by exact 2^-31, not integer modulo.
        // Integer count and positive int32 weights bound sum64 below 2^62.
        long target = (long) (((double) input.random31() * 0x1.0p-31) * (double) sum64);
        long prefix = 0;
        for (EffectiveRow row : rows) {
            prefix += row.nativeWeight();
            if (row.nativeWeight() > 0 && prefix > target)
                return new Computed(rows, sum32, sum64, target, OptionalInt.of(row.originalIndex()), Status.INDEX_CHOSEN);
        }
        return new Computed(rows, sum32, sum64, target, OptionalInt.empty(), Status.HELPER_DEFAULT);
    }
}
