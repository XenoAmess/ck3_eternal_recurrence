package org.xar.ck3.control.wave2.development.constructioneconomy;

import java.math.BigInteger;
import java.util.Optional;

import static org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.*;

/** Existing producer entry points assembled through one injected read-only cash reader. */
public final class ConstructionEconomyAdapters {
    private ConstructionEconomyAdapters() { }

    @FunctionalInterface
    public interface CashReader {
        /** Existing normalized current-resources query; the adapter never submits an action. */
        CashPacket readCurrentResources(BigInteger expectedRevision);
    }

    public static PreparedFields prepare(Candidate candidate, CashPacket observedCash,
            BigInteger reserve, BigInteger commitments, int horizonMonths) {
        BigInteger cost = candidate.cost().orElseThrow(() -> new IllegalArgumentException("stock_gold_cost_raw is absent"));
        Budget budget = ConstructionEconomy.projectBudget(observedCash, new BudgetPolicy(cost, reserve, commitments, horizonMonths));
        return new PreparedFields(observedCash, budget);
    }

    public static CompletedFields completed(Receipt receipt, CashPacket observedCash, String exactBuild) {
        Receipt attached = ConstructionEconomyCodec.decodeReceipt(ConstructionEconomyCodec.receiptWithPostCash(receipt, observedCash));
        return new CompletedFields(attached, ConstructionEconomy.classify(
                new OutcomeRequest(attached, exactBuild, Optional.empty(), Optional.empty())));
    }

    public static Budget queryBudget(CashReader reader, BigInteger expectedRevision, BudgetPolicy policy) {
        if (expectedRevision == null || expectedRevision.signum() <= 0 || expectedRevision.bitLength() > 64)
            throw new IllegalArgumentException("expected revision must be a uint64 revision");
        CashPacket observed = reader.readCurrentResources(expectedRevision);
        Budget projected = ConstructionEconomy.projectBudget(observed, policy);
        return new Budget(projected.cash(), projected.policy(), projected.current(), projected.allRaised(), true);
    }

    public static QueryOutcome queryOutcome(CashReader reader, BigInteger expectedRevision, Receipt receipt,
            BigInteger reserve, BigInteger commitments, int horizonMonths) {
        Budget current = queryBudget(reader, expectedRevision, new BudgetPolicy(BigInteger.ZERO, reserve, commitments, horizonMonths));
        return new QueryOutcome(current, completed(receipt, current.cash(), current.cash().frame().gameVersion()));
    }

    /** Pure existing formal quote consumer: cash equality precedes reserve and wartime checks. */
    public static QuoteProjection projectQuote(ConstructionQuote quote, QuoteCashObservation observation,
            boolean wartime, boolean requireSameFrame) {
        if (observation instanceof NoCashObservation) return deferred(quote, Optional.empty(),
                wartime ? "current native cash is unavailable for this wartime spend" : null);
        if (!(observation instanceof ObservedCash observed)) return deferred(quote, Optional.empty(),
                "current cash and native construction quote are not jointly observed");
        CashPacket cash = observed.cash();
        Optional<BigInteger> treasury = cash.value(CashField.TREASURY).raw();
        if (treasury.isEmpty() || !treasury.equals(quote.candidate().goldBefore())) return deferred(quote, Optional.empty(),
                "current cash and native construction quote are not jointly observed");
        if ((wartime || requireSameFrame) && (quote.sourceFrame().isEmpty()
                || !cash.frame().actor().equals(quote.sourceFrame().orElseThrow().actor())
                || !cash.frame().snapshotRevision().equals(quote.sourceFrame().orElseThrow().revision())
                || !cash.frame().date().equals(quote.sourceFrame().orElseThrow().date())))
            return deferred(quote, Optional.empty(), "wartime cash and construction quote belong to different actor frames");
        PreparedFields prepared = prepare(quote.candidate(), cash, observed.reserve(), BigInteger.ZERO, 1);
        Optional<PreparedFields> fields = Optional.of(prepared);
        if (!prepared.budget().current().floorReady().orElse(false)) return deferred(quote, fields,
                "defer this quote because current one-month cash does not retain the reserve");
        if (wartime && !prepared.budget().allRaised().floorReady().orElse(false)) return deferred(quote, fields,
                "defer this quote because all-raised one-month cash does not retain the reserve");
        return deferred(quote, fields, null);
    }

    private static QuoteProjection deferred(ConstructionQuote quote, Optional<PreparedFields> prepared, String reason) {
        return new QuoteProjection(quote, prepared, Optional.ofNullable(reason));
    }

    /** M5 receives current scenarios independently; receipt replacement stays bound to the consumed action. */
    public static PlanCashEnrichment enrichM5Plan(M5Plan plan, QueryOutcome observation) {
        boolean sameAction = plan.consumedReceipt().isPresent()
                && plan.consumedReceipt().orElseThrow().actionRequestId().equals(observation.completed().receipt().actionRequestId());
        return new PlanCashEnrichment(plan, observation, sameAction);
    }
}
