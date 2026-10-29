package org.xar.ck3.control.wave2.development.constructioneconomy;

import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

/** Immutable projections of the declared construction fields; no native or writer authority. */
public final class ConstructionEconomyModel {
    public static final int SCALE = 100_000;
    private ConstructionEconomyModel() { }

    /** Retained extensible JSON value; reencoding is not an original-byte identity proof. */
    public record OriginalJson(byte[] bytes) {
        public OriginalJson { bytes = bytes.clone(); }
        @Override public byte[] bytes() { return bytes.clone(); }
    }
    public enum ReceiptStatus { APPLIED, MISMATCHED, RESTORED_BEFORE_ACTION, OTHER }
    public enum CompletionStatus { COMPLETED, IN_PROGRESS, OTHER }
    public enum Phase {
        MISMATCHED("observed_mismatched_construction"), RESTORED("restored_before_action"),
        COMPLETED("completed"), ACTIVE("active"), PENDING("pending");
        private final String wire;
        Phase(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum CashField {
        GROSS("player_monthly_gross_income", "monthly_gross_income_ready", "monthly_gross_income_unavailable_reason"),
        EXPENSES("player_monthly_total_expenses", "monthly_total_expenses_ready", "monthly_total_expenses_unavailable_reason"),
        NET("player_monthly_net_income", "monthly_net_income_ready", "monthly_net_income_unavailable_reason"),
        TREASURY("current_treasury", "current_treasury_ready", "current_treasury_unavailable_reason");
        private final String wire;
        private final String flag;
        private final String reason;
        CashField(String wire, String flag, String reason) { this.wire = wire; this.flag = flag; this.reason = reason; }
        public String wire() { return wire; }
        public String flag() { return flag; }
        public String reason() { return reason; }
    }
    public enum MissingInput {
        SAME_FRAME("same_frame_ready"), TREASURY("current_treasury"), NET("player_monthly_net_income"),
        CURRENT_MILITARY("military_expenses.current"), ALL_RAISED_MILITARY("military_expenses.all_raised");
        private final String wire;
        MissingInput(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record FixedObservation(Optional<BigInteger> raw, boolean ready, Optional<String> unavailableReason) {
        public FixedObservation { Objects.requireNonNull(raw); Objects.requireNonNull(unavailableReason); }
    }
    public record SourceFrame(String gameVersion, String executableSha256, Optional<BigInteger> actor,
            Optional<BigInteger> snapshotRevision, Optional<BigInteger> date,
            Optional<String> queriedSnapshotId, Optional<BigInteger> queriedRevision,
            Optional<BigInteger> queriedNativeRevision) { }
    public record MilitaryObservation(Optional<BigInteger> gold, Optional<String> unavailableReason) { }
    public record CashPacket(SourceFrame frame, boolean sameFrameReady, Map<CashField, FixedObservation> values,
            Optional<MilitaryObservation> currentMilitary, Optional<MilitaryObservation> allRaisedMilitary,
            boolean normalizedReadOnly, OriginalJson original) {
        public CashPacket { values = Map.copyOf(values); }
        public FixedObservation value(CashField key) { return Objects.requireNonNull(values.get(key)); }
    }
    public record Candidate(Optional<BigInteger> barony, Optional<BigInteger> province,
            Optional<BigInteger> authoredIncomeHundredths, Optional<BigInteger> cost, Optional<BigInteger> goldBefore) { }
    public record ProvinceObservation(boolean observed, Optional<BigInteger> barony, Optional<BigInteger> province,
            Optional<BigInteger> monthlyIncomeRaw, Optional<BigInteger> date) { }
    public record StartReceipt(ReceiptStatus status, boolean postconditionVerified,
            Optional<String> actionRequestId, Optional<BigInteger> postPlayerGold) { }
    public record Receipt(ReceiptStatus status, boolean verified, CompletionStatus completion,
            Optional<BigInteger> completionDate, Optional<String> actionRequestId,
            Optional<BigInteger> actor, Optional<String> episodeRunId, Candidate candidate,
            Optional<BigInteger> preGross, Optional<BigInteger> postGross, Optional<BigInteger> incomeDate,
            Optional<BigInteger> preDate, Optional<ProvinceObservation> preProvince,
            Optional<ProvinceObservation> postProvince, Optional<StartReceipt> start,
            Optional<CashPacket> preCash, Optional<CashPacket> postCash,
            Optional<OriginalJson> observedMaterialTuple, OriginalJson original) { }
    public record OutcomeRequest(Receipt receipt, String exactBuild,
            Optional<CashPacket> preCashOverride, Optional<CashPacket> postCashOverride) { }
    public record Change(boolean ready, Optional<BigInteger> before, Optional<BigInteger> after,
            Optional<BigInteger> delta) { }
    public record AggregateChange(Change values, Optional<String> unavailableReason) { }
    public record CashChange(boolean observed, Optional<String> unavailableReason, List<SourceFrame> frames,
            Optional<BigInteger> elapsedGameHours, Map<CashField, Change> monthlyChanges,
            Optional<Change> personalGoldChange, Optional<BigInteger> verifiedDebit,
            Optional<BigInteger> residualAfterDebit) {
        public CashChange { frames = List.copyOf(frames); monthlyChanges = Map.copyOf(monthlyChanges); }
    }
    public record Outcome(Phase phase, Receipt receipt, String exactBuild, boolean materialCompleted,
            AggregateChange gross, AggregateChange province, Optional<String> nextObservationKind,
            CashChange cash) { }
    public record BudgetPolicy(BigInteger constructionCost, BigInteger reserve,
            BigInteger commitments, int horizonMonths) {
        public BudgetPolicy {
            Objects.requireNonNull(constructionCost); Objects.requireNonNull(reserve); Objects.requireNonNull(commitments);
            if (constructionCost.signum() < 0 || reserve.signum() < 0 || commitments.signum() < 0
                    || horizonMonths < 1 || horizonMonths > 24) throw new IllegalArgumentException("invalid construction budget policy");
        }
    }
    public record Scenario(Optional<BigInteger> netRate, Optional<BigInteger> cashAfterUpfront,
            Optional<BigInteger> projectedEnd, Optional<BigInteger> burnReservation,
            Optional<BigInteger> minimum, Optional<Boolean> floorReady,
            Optional<BigInteger> maximumOneOffSpend, Optional<Integer> firstReserveBreach,
            Map<MissingInput, String> missingInputs) {
        public Scenario { missingInputs = Map.copyOf(missingInputs); }
        public boolean ready() { return missingInputs.isEmpty(); }
    }
    public record Budget(CashPacket cash, BudgetPolicy policy, Scenario current, Scenario allRaised,
            boolean fromQuery) { }
    public record BudgetRequest(CashPacket cash, BudgetPolicy policy) { }
    public record PreparedFields(CashPacket preCash, Budget budget) { }
    public record CompletedFields(Receipt receipt, Outcome outcome) { }
    public record QueryOutcome(Budget currentScenarios, CompletedFields completed) { }
    public record QuoteFrame(Optional<BigInteger> actor, Optional<BigInteger> revision, Optional<BigInteger> date) { }
    public record ConstructionQuote(Candidate candidate, Optional<QuoteFrame> sourceFrame, OriginalJson original) { }
    public sealed interface QuoteCashObservation permits NoCashObservation, UnavailableCashObservation, ObservedCash { }
    public record NoCashObservation() implements QuoteCashObservation { }
    public record UnavailableCashObservation() implements QuoteCashObservation { }
    public record ObservedCash(CashPacket cash, BigInteger reserve) implements QuoteCashObservation { }
    public record QuoteProjection(ConstructionQuote quote, Optional<PreparedFields> prepared, Optional<String> deferredReason) { }
    public record M5Plan(Optional<Receipt> consumedReceipt, OriginalJson original) { }
    public record PlanCashEnrichment(M5Plan plan, QueryOutcome observation, boolean replaceConsumedReceipt) { }
}
