package org.xar.ck3.control.wave2.development.constructionvalue;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;

/** Native construction quote observations and authored values; no realised income or action state. */
public final class ConstructionValueModel {
    private ConstructionValueModel() { }
    public enum Presence { MISSING, NULL, VALUE }
    public record Field<T>(Presence presence, T value) {
        public Field {
            Objects.requireNonNull(presence);
            if ((presence == Presence.VALUE) != (value != null)) { throw new IllegalArgumentException("field presence mismatch"); }
        }
        public static <T> Field<T> missing() { return new Field<>(Presence.MISSING, null); }
        public static <T> Field<T> nil() { return new Field<>(Presence.NULL, null); }
        public static <T> Field<T> of(T value) { return new Field<>(Presence.VALUE, Objects.requireNonNull(value)); }
        public boolean known() { return presence == Presence.VALUE; }
        public boolean is(T expected) { return known() && value.equals(expected); }
    }
    public enum Build {
        V11906("1.19.0.6"), V12002("1.20.0.2"), V12003("1.20.0.3"), V12004("1.20.0.4"), UNSUPPORTED("");
        private final String wire;
        Build(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Build fromWire(String wire) {
            for (Build value : values()) { if (value != UNSUPPORTED && value.wire.equals(wire)) { return value; } }
            return UNSUPPORTED;
        }
    }
    public enum LookupKind { TARGET, EXISTING }
    public record LookupInput(LookupKind kind, Field<String> key, Build build) {
        public LookupInput { Objects.requireNonNull(kind); Objects.requireNonNull(key); Objects.requireNonNull(build); }
    }
    public record Active(Field<BigInteger> baronyId, Field<BigInteger> provinceId, Field<Boolean> active) {
        public Active {
            Objects.requireNonNull(baronyId); Objects.requireNonNull(provinceId); Objects.requireNonNull(active);
            nativeSigned(baronyId, 32); nativeSigned(provinceId, 32);
        }
    }
    public record Sample(Field<BigInteger> baronyId, Field<BigInteger> provinceId, Field<BigInteger> buildingTypeId,
            Field<BigInteger> slotIndex, Field<String> key, Field<Boolean> nativeCostObserved, Field<List<BigInteger>> costs) {
        public Sample {
            Objects.requireNonNull(baronyId); Objects.requireNonNull(provinceId); Objects.requireNonNull(buildingTypeId);
            Objects.requireNonNull(slotIndex); Objects.requireNonNull(key); Objects.requireNonNull(nativeCostObserved); Objects.requireNonNull(costs);
            nativeSigned(baronyId, 32); nativeSigned(provinceId, 32); nativeSigned(buildingTypeId, 32); nativeSigned(slotIndex, 32);
            if (costs.known()) {
                costs = Field.of(List.copyOf(costs.value())); for (BigInteger cost : costs.value()) { nativeSigned(cost, 64); }
            }
        }
    }
    public record Completed(Field<BigInteger> baronyId, Field<BigInteger> provinceId,
            Field<BigInteger> slotIndex, Field<String> key) {
        public Completed {
            Objects.requireNonNull(baronyId); Objects.requireNonNull(provinceId); Objects.requireNonNull(slotIndex); Objects.requireNonNull(key);
            nativeSigned(baronyId, 32); nativeSigned(provinceId, 32); nativeSigned(slotIndex, 32);
        }
    }
    public record World(Field<BigInteger> gold, Field<List<Active>> active, Field<List<Sample>> samples,
            Field<Boolean> inventoryObserved, Field<List<Completed>> completed, Field<Boolean> positiveIncomeCoverageComplete) {
        public World {
            Objects.requireNonNull(gold); Objects.requireNonNull(active); Objects.requireNonNull(samples);
            Objects.requireNonNull(inventoryObserved); Objects.requireNonNull(completed); Objects.requireNonNull(positiveIncomeCoverageComplete);
            nativeSigned(gold, 64);
            if (active.known()) { active = Field.of(List.copyOf(active.value())); }
            if (samples.known()) { samples = Field.of(List.copyOf(samples.value())); }
            if (completed.known()) { completed = Field.of(List.copyOf(completed.value())); }
        }
    }
    public record SelectionInput(World world, Build build) {
        public SelectionInput { Objects.requireNonNull(world); Objects.requireNonNull(build); }
    }
    public record Candidate(BigInteger baronyId, BigInteger provinceId, BigInteger buildingTypeId, BigInteger slotIndex,
            BigInteger stockGoldCost, BigInteger goldBefore, String buildingKey, int authoredIncomeHundredths,
            int authoredIncomeDeltaHundredths, int oldAuthoredIncomeHundredths, String oldBuildingKey, boolean slotWasEmpty) {
        public Candidate {
            Objects.requireNonNull(baronyId); Objects.requireNonNull(provinceId); Objects.requireNonNull(buildingTypeId);
            Objects.requireNonNull(slotIndex); Objects.requireNonNull(stockGoldCost); Objects.requireNonNull(goldBefore); Objects.requireNonNull(buildingKey);
            nativeSigned(stockGoldCost, 64); nativeSigned(goldBefore, 64);
            if (!positiveNativeId(baronyId) || !positiveNativeId(provinceId) || !positiveNativeId(buildingTypeId)
                    || slotIndex.signum() < 0 || slotIndex.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) > 0
                    || stockGoldCost.signum() <= 0 || goldBefore.compareTo(stockGoldCost) <= 0
                    || goldBefore.subtract(stockGoldCost).compareTo(ConstructionValuePolicy.RESERVE_RAW) < 0
                    || authoredIncomeHundredths <= 0 || authoredIncomeDeltaHundredths <= 0 || oldAuthoredIncomeHundredths < 0
                    || authoredIncomeHundredths - oldAuthoredIncomeHundredths != authoredIncomeDeltaHundredths
                    || slotWasEmpty != (oldBuildingKey == null) || (slotWasEmpty && oldAuthoredIncomeHundredths != 0)) {
                throw new IllegalArgumentException("invalid authored construction candidate");
            }
        }
    }
    static boolean positiveNativeId(BigInteger value) {
        return value.signum() > 0 && value.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0;
    }
    private static void nativeSigned(Field<BigInteger> field, int bits) { if (field.known()) { nativeSigned(field.value(), bits); } }
    private static void nativeSigned(BigInteger value, int bits) {
        if (value.compareTo(BigInteger.ONE.shiftLeft(bits - 1).negate()) < 0
                || value.compareTo(BigInteger.ONE.shiftLeft(bits - 1).subtract(BigInteger.ONE)) > 0) {
            throw new IllegalArgumentException("native signed" + bits + " integer width required");
        }
    }
    public sealed interface Selection permits NoCandidate, Selected { }
    public record NoCandidate() implements Selection { }
    public record Selected(Candidate candidate) implements Selection { public Selected { Objects.requireNonNull(candidate); } }
    public sealed interface ConsumerResult permits CandidateSelected, NoLegalBudgetedBuilding, EvidenceInsufficient { }
    public record CandidateSelected(Candidate candidate) implements ConsumerResult { public CandidateSelected { Objects.requireNonNull(candidate); } }
    public record NoLegalBudgetedBuilding() implements ConsumerResult { }
    public record EvidenceInsufficient() implements ConsumerResult { }
}
