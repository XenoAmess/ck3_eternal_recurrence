package org.xar.ck3.control.wave2.planning.warcashprovenance;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel;
import org.xar.ck3.control.wave2.finance.holyloan.LoanFinancingCodec;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;
import static org.xar.ck3.control.wave2.planning.warcashprovenance.FinancingGapModels.*;

/** Current lawful financing review. There is no Game submitter, receipt issuer or ledger writer here. */
public final class EmergencyFinancingAssessment {
    private EmergencyFinancingAssessment() { }

    public enum LoanStatus {
        NOT_PROVIDED, CASH_FRAME_REFUSED, CURRENT_PLANNING_FRAME_UNAVAILABLE, SOURCE_FRAME_MISMATCH, NATIVE_INPUT_UNAVAILABLE,
        NATIVE_GATES_REJECTED, COMPLETE_LOAN_TERMS_MISSING
    }
    public enum Eligibility { UNKNOWN, DENIED, ALLOWED }
    public enum CancellationStatus { NATIVE_FINAL_GATE_REFUND_AND_RECEIVER_UNAVAILABLE }
    public enum FundingKind { HOLY_ORDER_LOAN, CONSTRUCTION_CANCELLATION }
    public enum SubmissionState { SUBMITTED, ACKNOWLEDGED, UNKNOWN }
    public enum ReplayGuard { LEDGER_UNAVAILABLE, NO_UNRESOLVED_ACTION_OBSERVED, UNRESOLVED_ACTION_NEVER_REPLAY }

    /** Read-only projection supplied by the existing writer. ACK is still unresolved; UNKNOWN is not retried. */
    public sealed interface PendingObservation permits PendingUnavailable, NoPendingAction, PendingAction {
        static PendingObservation seamUnavailable() { return new PendingUnavailable(); }
    }
    public record PendingUnavailable() implements PendingObservation { }
    public record NoPendingAction() implements PendingObservation { }
    public record PendingAction(FundingKind kind, String actionId, String procurementEpoch,
            SubmissionState state) implements PendingObservation {
        public PendingAction {
            Objects.requireNonNull(kind); text(actionId); text(procurementEpoch); Objects.requireNonNull(state);
        }
    }

    /** Retains every signed native cost slot; neither principal nor cost is a credit to the wallet. */
    public record LoanReview(LoanStatus status, Eligibility eligibility, OptionalLong prospectivePrincipalRaw,
            Optional<List<Long>> declaredCostsRaw) {
        public LoanReview {
            Objects.requireNonNull(status); Objects.requireNonNull(eligibility);
            Objects.requireNonNull(prospectivePrincipalRaw); Objects.requireNonNull(declaredCostsRaw);
            declaredCostsRaw = declaredCostsRaw.map(List::copyOf);
            declaredCostsRaw.ifPresent(costs -> {
                if (costs.size() != 10) throw new IllegalArgumentException("ten actual native cost slots required");
            });
            Eligibility required = switch (status) {
                case NATIVE_GATES_REJECTED -> Eligibility.DENIED;
                case COMPLETE_LOAN_TERMS_MISSING -> Eligibility.ALLOWED;
                default -> Eligibility.UNKNOWN;
            };
            if (eligibility != required) {
                throw new IllegalArgumentException("loan eligibility branch differs");
            }
            if (status == LoanStatus.NOT_PROVIDED || status == LoanStatus.CASH_FRAME_REFUSED
                    || status == LoanStatus.SOURCE_FRAME_MISMATCH || status == LoanStatus.CURRENT_PLANNING_FRAME_UNAVAILABLE) {
                if (eligibility != Eligibility.UNKNOWN || prospectivePrincipalRaw.isPresent() || declaredCostsRaw.isPresent()) {
                    throw new IllegalArgumentException("unqualified source cannot carry an observed loan value");
                }
            }
        }
        public boolean completeLoanTermsVerified() { return false; }
        public boolean typedDebtReadbackVerified() { return false; }
        public boolean independentlyAttributedReceivedFundsVerified() { return false; }
        public boolean submitPlanned() { return false; }
    }

    public record Assessment(ObservedFrame sourceFrame, Optional<LoanFinancingCodec.PlanningFrame> planningSourceFrame, Optional<Gap> gap,
            Optional<BigInteger> actualWalletRaw, LoanReview loan, CancellationStatus cancellation,
            PendingObservation pending, ReplayGuard replay) {
        public Assessment {
            Objects.requireNonNull(sourceFrame); Objects.requireNonNull(planningSourceFrame); Objects.requireNonNull(gap); Objects.requireNonNull(actualWalletRaw);
            Objects.requireNonNull(loan); Objects.requireNonNull(cancellation); Objects.requireNonNull(pending);
            Objects.requireNonNull(replay);
            planningSourceFrame.ifPresent(frame -> {
                if (!sameObservedFrame(sourceFrame, frame) || frame.bridgePid() == null || frame.bridgePid().signum() <= 0
                        || frame.connectionGeneration() == null || frame.connectionGeneration().signum() < 0) {
                    throw new IllegalArgumentException("current planning source is incomplete or crosses the observed frame");
                }
            });
            gap.ifPresent(value -> {
                if (!sourceFrame.equals(value.sourceFrame()) || !actualWalletRaw.equals(value.observedTreasuryRaw())) {
                    throw new IllegalArgumentException("financing gap crossed the source frame or actual wallet");
                }
            });
            if (replay != replayOf(pending)) throw new IllegalArgumentException("pending action replay branch differs");
        }
        public long unreceivedFundingCreditedRaw() { return 0; }
        public OptionalLong refundQuoteRaw() { return OptionalLong.empty(); }
        public boolean currentActiveProjectIndependentlyObserved() { return false; }
        public boolean submitPlanned() { return false; }
        public boolean continueExistingWarAction() { return true; }
        public boolean futureFundingReceiptMustKeepSameProcurementEpoch() { return true; }
        public boolean optionalConstructionMayUseProspectiveFunding() { return false; }
    }

    /** The original gap producer remains the only shortfall/crisis policy. No RPC or retry is performed. */
    public static Assessment assess(Input input, LoanFinancingCodec.LoanInput loan, PendingObservation pending,
            Optional<LoanFinancingCodec.PlanningFrame> currentPlanningFrame) {
        Objects.requireNonNull(input); Objects.requireNonNull(loan); Objects.requireNonNull(pending);
        Objects.requireNonNull(currentPlanningFrame);
        return new Assessment(input.frame(), currentPlanningFrame, WarFinancingCapabilityGap.observe(input), input.treasuryRaw(),
                reviewLoan(input.frame(), currentPlanningFrame, loan), CancellationStatus.NATIVE_FINAL_GATE_REFUND_AND_RECEIVER_UNAVAILABLE,
                pending, replayOf(pending));
    }

    private static LoanReview reviewLoan(ObservedFrame expected, Optional<LoanFinancingCodec.PlanningFrame> currentFrame,
            LoanFinancingCodec.LoanInput supplied) {
        if (supplied instanceof LoanFinancingCodec.NotProvided) return empty(LoanStatus.NOT_PROVIDED);
        if (supplied instanceof LoanFinancingCodec.Refused) return empty(LoanStatus.CASH_FRAME_REFUSED);
        LoanFinancingCodec.Projected projected = (LoanFinancingCodec.Projected) supplied;
        LoanFinancingCodec.PlanningFrame frame = projected.planningFrame();
        // Projected is created only by the existing full PID/connection and cash/native-frame validator.
        if (!sameObservedFrame(expected, frame)) return empty(LoanStatus.SOURCE_FRAME_MISMATCH);
        if (currentFrame.isEmpty()) return empty(LoanStatus.CURRENT_PLANNING_FRAME_UNAVAILABLE);
        if (!currentFrame.orElseThrow().equals(frame)) return empty(LoanStatus.SOURCE_FRAME_MISMATCH);
        RawCashCodec.LoanObservation observed = projected.observation();
        Eligibility eligible = switch (observed.borrowEligibility()) {
            case UNKNOWN -> Eligibility.UNKNOWN;
            case DENIED -> Eligibility.DENIED;
            case ALLOWED -> Eligibility.ALLOWED;
        };
        Optional<List<Long>> costs = observed.decisions().flatMap(decisions ->
                decisions.borrowDecision() instanceof HolyLoanModel.ObservedDecision borrow
                        ? Optional.of(borrow.declaredCostsRaw()) : Optional.empty());
        LoanStatus status = switch (eligible) {
            case UNKNOWN -> LoanStatus.NATIVE_INPUT_UNAVAILABLE;
            case DENIED -> LoanStatus.NATIVE_GATES_REJECTED;
            case ALLOWED -> LoanStatus.COMPLETE_LOAN_TERMS_MISSING;
        };
        return new LoanReview(status, eligible, observed.prospectivePrincipalRaw(), costs);
    }
    private static LoanReview empty(LoanStatus status) {
        return new LoanReview(status, Eligibility.UNKNOWN, OptionalLong.empty(), Optional.empty());
    }
    private static boolean sameObservedFrame(ObservedFrame expected, LoanFinancingCodec.PlanningFrame frame) {
        return expected.snapshotId().equals(frame.snapshotId()) && expected.revision().equals(frame.revision())
                && expected.nativeRevision().equals(frame.nativeRevision()) && expected.dateRaw().equals(frame.dateRaw())
                && expected.playedCharacterId().equals(frame.actorCharacterId()) && expected.episodeRunId().equals(frame.episodeRunId());
    }
    private static ReplayGuard replayOf(PendingObservation pending) {
        return pending instanceof PendingUnavailable ? ReplayGuard.LEDGER_UNAVAILABLE
                : pending instanceof NoPendingAction ? ReplayGuard.NO_UNRESOLVED_ACTION_OBSERVED
                : ReplayGuard.UNRESOLVED_ACTION_NEVER_REPLAY;
    }
    private static void text(String value) {
        if (value == null || value.isEmpty()) throw new IllegalArgumentException("nonempty action/epoch identity required");
    }
}
