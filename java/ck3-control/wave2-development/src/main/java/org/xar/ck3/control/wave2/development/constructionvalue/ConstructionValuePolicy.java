package org.xar.ck3.control.wave2.development.constructionvalue;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.OptionalInt;
import org.xar.ck3.control.wave2.development.constructionvalue.ConstructionValueModel.*;

/** Complete original transport _candidate pure closure, including current occupant and all tie breakers. */
public final class ConstructionValuePolicy {
    public static final BigInteger RESERVE_RAW = BigInteger.valueOf(20_000_000);
    private static final Comparator<Candidate> ORDER = Comparator.comparingInt(Candidate::authoredIncomeDeltaHundredths).reversed()
            .thenComparing(Candidate::stockGoldCost).thenComparing(candidate -> !candidate.slotWasEmpty())
            .thenComparing(Candidate::baronyId).thenComparing(Candidate::provinceId).thenComparing(Candidate::buildingTypeId)
            .thenComparing(Candidate::slotIndex).thenComparing(Candidate::buildingKey).thenComparingInt(Candidate::authoredIncomeHundredths)
            .thenComparingInt(Candidate::oldAuthoredIncomeHundredths).thenComparing(Candidate::oldBuildingKey, Comparator.nullsFirst(Comparator.naturalOrder()));
    private ConstructionValuePolicy() { }

    public static Selection select(SelectionInput input) {
        World world = input.world();
        if (!world.gold().known() || !world.active().known() || !world.samples().known()) { return new NoCandidate(); }
        BigInteger gold = world.gold().value(); List<Candidate> choices = new ArrayList<>();
        boolean inventoryObserved = world.inventoryObserved().is(true) && world.completed().known();
        List<Completed> completed = world.completed().known() ? world.completed().value() : List.of();
        for (Sample row : world.samples().value()) {
            if (!positive(row.baronyId()) || !positive(row.provinceId()) || !positive(row.buildingTypeId())
                    || !row.slotIndex().known() || row.slotIndex().value().signum() < 0
                    || row.slotIndex().value().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) > 0
                    || !row.nativeCostObserved().is(true) || !row.costs().known() || row.costs().value().size() != 10) { continue; }
            List<BigInteger> costs = row.costs().value(); BigInteger cost = costs.getFirst();
            if (cost.signum() <= 0 || costs.subList(1, 10).stream().anyMatch(value -> value.signum() != 0)
                    || cost.compareTo(gold) >= 0 || gold.subtract(cost).compareTo(RESERVE_RAW) < 0
                    || world.active().value().stream().noneMatch(active -> active.active().is(false)
                        && same(active.baronyId(), row.baronyId()) && same(active.provinceId(), row.provinceId()))) { continue; }
            OptionalInt income = AuthoredConstructionIncome.target(row.key(), input.build());
            if (income.isEmpty() || income.getAsInt() <= 0) { continue; }
            List<Completed> occupants = completed.stream().filter(old -> same(old.baronyId(), row.baronyId())
                    && same(old.provinceId(), row.provinceId()) && same(old.slotIndex(), row.slotIndex())).toList();
            if (occupants.size() > 1 || (occupants.isEmpty() && !inventoryObserved)) { continue; }
            boolean empty = occupants.isEmpty(); Field<String> oldKey = empty ? Field.nil() : occupants.getFirst().key();
            OptionalInt oldIncome = empty ? OptionalInt.of(0) : AuthoredConstructionIncome.existing(oldKey, input.build());
            if (oldIncome.isEmpty()) { continue; }
            int delta = income.getAsInt() - oldIncome.getAsInt(); if (delta <= 0) { continue; }
            choices.add(new Candidate(row.baronyId().value(), row.provinceId().value(), row.buildingTypeId().value(), row.slotIndex().value(),
                    cost, gold, row.key().value(), income.getAsInt(), delta, oldIncome.getAsInt(), empty ? null : oldKey.value(), empty));
        }
        return choices.stream().min(ORDER).<Selection>map(Selected::new).orElseGet(NoCandidate::new);
    }

    /** Original query consumer projection after its independent source/frame validator; it grants no source qualification. */
    public static ConsumerResult consumeSelection(SelectionInput input) {
        Selection selected = select(input);
        if (selected instanceof Selected present) { return new CandidateSelected(present.candidate()); }
        return input.world().positiveIncomeCoverageComplete().is(true) ? new NoLegalBudgetedBuilding() : new EvidenceInsufficient();
    }
    private static boolean positive(Field<BigInteger> value) { return value.known() && ConstructionValueModel.positiveNativeId(value.value()); }
    private static <T> boolean same(Field<T> left, Field<T> right) { return left.known() && right.known() && left.value().equals(right.value()); }
}
