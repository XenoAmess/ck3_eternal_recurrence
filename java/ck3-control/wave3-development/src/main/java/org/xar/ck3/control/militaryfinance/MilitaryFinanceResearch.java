package org.xar.ck3.control.militaryfinance;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashPolicy;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionCash;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionModel;

/** Explanation over the shared M4 input/decision. This class has no IO, action or ledger port. */
public final class MilitaryFinanceResearch {
    public static final String VERSION = "1.20.0.4";
    public static final String EXE_SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    public enum NativePayment {
        OUTSIDE_ALLOWANCE(0), NATIVE_PERMITTED_DEBT(1), FULL_FUNDS(2);
        private final int raw;
        NativePayment(int raw) { this.raw = raw; }
        public int raw() { return raw; }
        public static NativePayment decode(int value) {
            for (NativePayment status : values()) if (status.raw == value) return status;
            throw new IllegalArgumentException("native payment must be 0/1/2");
        }
    }
    public enum NativeLegality { UNKNOWN, REJECTED, LEGAL_PERMITTED_DEBT, LEGAL_FULL_FUNDS }
    public enum StrengthScope { OBSERVED_LOCAL_NATIVE_MEMBERS, DEDUPLICATED_WAR_HEADCOUNTS }
    public enum ArrivalKind { UNBOUGHT_COMPANY_NO_CUNIT_ROUTE, NO_CURRENT_CUNIT_ROUTE_OBSERVATION,
        CURRENT_NATIVE_ROUTE_FORECAST }
    public enum FundingNeed { NO_NEW_FUNDING_REQUIRED_BY_CURRENT_GATE,
        INPUTS_INCOMPLETE_OPTIONAL_CONSTRUCTION_DEFERRED, REVIEW_CURRENT_FUNDING_OPTIONS }
    public enum LoanStatus { UNKNOWN, SOURCE_FRAME_MISMATCH, NATIVE_DECISION_REJECTED, DECISION_GATES_ONLY_COMPLETE_TERMS_MISSING }
    public enum CancellationStatus { EXACT_NATIVE_CANCEL_TERMS_INTERFACE_UNAVAILABLE }
    public enum Reason {
        NATIVE_TERMS_MISSING, NATIVE_TERMS_FRAME_MISMATCH, NATIVE_CAN_HIRE_UNKNOWN,
        NATIVE_CAN_HIRE_FALSE, NATIVE_PAYMENT_OUTSIDE_ALLOWANCE, NATIVE_DEBT_PERMISSION_IS_NOT_FULL_FUNDS,
        GENERIC_AFFORDABILITY_REMAINS_INDEPENDENT, CURRENT_RESERVE_QUOTE_PREDICATE_FAILED,
        CONDITIONAL_HEADCOUNT_ONLY, JOINT_ARRIVAL_UNVERIFIED, NO_OBSERVED_HEADCOUNT_SCOPE,
        LOAN_PRINCIPAL_AND_DEBT_READER_MISSING, REFUND_QUOTE_AND_CANCEL_RECEIVER_MISSING,
        UNKNOWN_COMMITMENT_PRESERVED_NO_REPLAY
    }
    /** Source build is checked independently of the public frame identity. */
    public record NativeTerms(GiftWarCashModel.SourceFrame frame, String executableSha256,
                              BigInteger companyId, NativePayment payment, BigInteger contractMonths) {
        public NativeTerms {
            Objects.requireNonNull(frame); Objects.requireNonNull(payment);
            nonnegative(companyId, "company"); positive(contractMonths, "duration");
            if (!EXE_SHA256.equals(executableSha256)) throw new IllegalArgumentException("exact .4 terms source required");
        }
    }
    public record StrengthObservation(GiftWarCashModel.SourceFrame frame, BigInteger warId,
            BigInteger playerSoldiers, BigInteger enemySoldiers, StrengthScope scope) {
        public StrengthObservation {
            Objects.requireNonNull(frame); Objects.requireNonNull(scope); positive(warId, "war");
            nonnegative(playerSoldiers, "own count"); nonnegative(enemySoldiers, "enemy count");
        }
    }
    /** A forecast requires an actually observed employed company and its real new Army ID. */
    public record RouteObservation(GiftWarCashModel.SourceFrame frame, BigInteger companyId,
            BigInteger observedEmployer, BigInteger actualArmyId, BigInteger destinationProvince,
            BigInteger nativePredictedDays) {
        public RouteObservation {
            Objects.requireNonNull(frame); nonnegative(companyId, "company"); positive(observedEmployer, "employer");
            nonnegative(actualArmyId, "army"); positive(destinationProvince, "destination"); nonnegative(nativePredictedDays, "ETA");
        }
    }
    /** The native loan leaf has actor/date/captureEpoch; its real owner supplies the full outer frame. */
    public record BoundLoan(GiftWarCashModel.SourceFrame frame, HolyLoanModel.Observation observation) {
        public BoundLoan {
            Objects.requireNonNull(frame); Objects.requireNonNull(observation);
            if (!frame.playedCharacterId().equals(BigInteger.valueOf(observation.source().playedCharacterId()))
                    || !frame.dateRaw().equals(BigInteger.valueOf(observation.source().dateRaw())))
                throw new IllegalArgumentException("loan owner frame differs from native copied leaf");
        }
    }
    public record Request(WartimeConstructionModel.Input constructionInput,
            Optional<StrengthObservation> strength, List<NativeTerms> nativeTerms,
            List<RouteObservation> routes, Optional<BoundLoan> loan) {
        public Request {
            Objects.requireNonNull(constructionInput); Objects.requireNonNull(strength); Objects.requireNonNull(loan);
            nativeTerms = List.copyOf(nativeTerms); routes = List.copyOf(routes);
            unique(nativeTerms.stream().map(NativeTerms::companyId).toList());
            unique(routes.stream().map(RouteObservation::companyId).toList());
        }
        public static Request currentGateOnly(WartimeConstructionModel.Input input) {
            return new Request(input, Optional.empty(), List.of(), List.of(), Optional.empty());
        }
    }
    public record ConditionalCounts(BigInteger warId, StrengthScope scope, BigInteger player,
            BigInteger enemy, BigInteger companySoldiers, BigInteger afterCompanyArrival,
            BigInteger observedDeficit, boolean closesObservedHeadcountDeficit) { }
    public record Arrival(ArrivalKind kind, Optional<BigInteger> actualArmyId,
            Optional<BigInteger> destinationProvince, Optional<BigInteger> forecastDays) {
        public boolean actualArrivalVerified() { return false; }
        public boolean arrivalBeforeLossGuaranteed() { return false; }
    }
    public record Offer(GiftWarCashModel.Read<BigInteger> companyId, NativeLegality nativeLegality,
            Optional<NativePayment> nativePayment, GiftWarCashModel.Read<Boolean> genericCanAfford,
            boolean sharedReserveQuoteUsable, Optional<BigInteger> nativeContractMonths,
            Optional<ConditionalCounts> conditionalCounts, Arrival arrival, List<Reason> reasons) {
        public Offer { reasons = List.copyOf(reasons); }
        public Optional<BigInteger> battleWinProbability() { return Optional.empty(); }
    }
    public record Funding(FundingNeed need, LoanStatus loanStatus, CancellationStatus cancellationStatus,
            boolean unresolvedCommitmentPreserved, List<Reason> reasons) {
        public Funding { reasons = List.copyOf(reasons); }
        public BigInteger fundingCreditRaw() { return BigInteger.ZERO; }
        public boolean newProcurementEpochOpened() { return false; }
        public boolean actionSubmissionQualified() { return false; }
    }
    public record Assessment(WartimeConstructionModel.Decision constructionDecision,
            List<Offer> offers, Funding funding) {
        public Assessment { offers = List.copyOf(offers); }
        public boolean fullNativeAiChooserReconstructed() { return false; }
    }
    private MilitaryFinanceResearch() { }

    public static Assessment assess(Request request) {
        Objects.requireNonNull(request);
        var input = request.constructionInput();
        // The sole M4 reserve producer remains authoritative for this observation.
        var decision = WartimeConstructionCash.observe(input);
        var snapshot = input.context().snapshot();
        Set<BigInteger> hostile = new HashSet<>();
        if (snapshot.wars().known()) for (var war : snapshot.wars().value())
            for (var province : war.enemyProvinces()) if (province.known()) hostile.add(province.value());
        Optional<StrengthObservation> counts = request.strength().filter(value -> value.frame().equals(snapshot.frame())
                && snapshot.wars().known() && snapshot.wars().value().stream().anyMatch(war -> war.warId().known()
                && war.warId().value().equals(value.warId())));
        List<Offer> offers = new ArrayList<>();
        for (var evidence : input.quotes()) {
            var quote = evidence.quote();
            Optional<NativeTerms> terms = quote.companyId().known() ? request.nativeTerms().stream()
                    .filter(value -> value.companyId().equals(quote.companyId().value())).findFirst() : Optional.empty();
            List<Reason> reasons = new ArrayList<>();
            NativeLegality legality = NativeLegality.UNKNOWN;
            Optional<NativeTerms> currentTerms = terms.filter(value -> value.frame().equals(snapshot.frame()));
            if (terms.isEmpty()) reasons.add(Reason.NATIVE_TERMS_MISSING);
            else if (currentTerms.isEmpty()) reasons.add(Reason.NATIVE_TERMS_FRAME_MISMATCH);
            else if (!quote.canHire().known()) reasons.add(Reason.NATIVE_CAN_HIRE_UNKNOWN);
            else if (!quote.canHire().value()) { legality = NativeLegality.REJECTED; reasons.add(Reason.NATIVE_CAN_HIRE_FALSE); }
            else if (currentTerms.orElseThrow().payment() == NativePayment.OUTSIDE_ALLOWANCE) {
                legality = NativeLegality.REJECTED; reasons.add(Reason.NATIVE_PAYMENT_OUTSIDE_ALLOWANCE);
            } else if (currentTerms.orElseThrow().payment() == NativePayment.NATIVE_PERMITTED_DEBT) {
                legality = NativeLegality.LEGAL_PERMITTED_DEBT; reasons.add(Reason.NATIVE_DEBT_PERMISSION_IS_NOT_FULL_FUNDS);
            } else legality = NativeLegality.LEGAL_FULL_FUNDS;
            if (!quote.canAfford().known() || !quote.canAfford().value()) reasons.add(Reason.GENERIC_AFFORDABILITY_REMAINS_INDEPENDENT);
            boolean reserveUsable = evidence.groups() == WartimeConstructionModel.GroupShape.ALL_OBJECTS
                    && GiftWarCashPolicy.usableEmergencyQuote(quote, hostile);
            if (!reserveUsable) reasons.add(Reason.CURRENT_RESERVE_QUOTE_PREDICATE_FAILED);
            Optional<ConditionalCounts> comparison = Optional.empty();
            if (counts.isPresent() && quote.currentSoldiers().known() && quote.currentSoldiers().value().signum() > 0) {
                var current = counts.orElseThrow(); var soldiers = quote.currentSoldiers().value();
                var deficit = current.enemySoldiers().subtract(current.playerSoldiers()).max(BigInteger.ZERO);
                comparison = Optional.of(new ConditionalCounts(current.warId(), current.scope(), current.playerSoldiers(),
                        current.enemySoldiers(), soldiers, current.playerSoldiers().add(soldiers), deficit,
                        soldiers.compareTo(deficit) >= 0));
                reasons.add(Reason.CONDITIONAL_HEADCOUNT_ONLY);
                if (current.scope() == StrengthScope.DEDUPLICATED_WAR_HEADCOUNTS) reasons.add(Reason.JOINT_ARRIVAL_UNVERIFIED);
            } else reasons.add(Reason.NO_OBSERVED_HEADCOUNT_SCOPE);
            Optional<RouteObservation> route = quote.companyId().known()
                    && quote.employer() == GiftWarCashModel.Presence.VALUE ? request.routes().stream().filter(value ->
                    value.companyId().equals(quote.companyId().value()) && value.frame().equals(snapshot.frame())
                    && snapshot.actor().known() && value.observedEmployer().equals(snapshot.actor().value())).findFirst() : Optional.empty();
            Arrival arrival = route.map(value -> new Arrival(ArrivalKind.CURRENT_NATIVE_ROUTE_FORECAST,
                    Optional.of(value.actualArmyId()), Optional.of(value.destinationProvince()), Optional.of(value.nativePredictedDays())))
                    .orElseGet(() -> new Arrival(quote.employer() == GiftWarCashModel.Presence.NULL
                            ? ArrivalKind.UNBOUGHT_COMPANY_NO_CUNIT_ROUTE : ArrivalKind.NO_CURRENT_CUNIT_ROUTE_OBSERVATION,
                            Optional.empty(), Optional.empty(), Optional.empty()));
            offers.add(new Offer(quote.companyId(), legality, currentTerms.map(NativeTerms::payment), quote.canAfford(),
                    reserveUsable, currentTerms.map(NativeTerms::contractMonths), comparison, arrival, reasons));
        }
        boolean deferred = decision.status() == WartimeConstructionModel.Status.DEFER;
        boolean needs = decision.reason().filter(value -> value == WartimeConstructionModel.Reason.NOT_AMPLE).isPresent();
        boolean pending = !input.context().mercenaryPending().known()
                || input.context().mercenaryPending().value() != GiftWarCashModel.Presence.NULL;
        LoanStatus loanStatus = loanStatus(request.loan(), snapshot);
        List<Reason> fundingReasons = new ArrayList<>();
        if (needs) {
            fundingReasons.add(Reason.REFUND_QUOTE_AND_CANCEL_RECEIVER_MISSING);
            fundingReasons.add(Reason.LOAN_PRINCIPAL_AND_DEBT_READER_MISSING);
        }
        if (pending) fundingReasons.add(Reason.UNKNOWN_COMMITMENT_PRESERVED_NO_REPLAY);
        Funding funding = new Funding(needs ? FundingNeed.REVIEW_CURRENT_FUNDING_OPTIONS
                : deferred ? FundingNeed.INPUTS_INCOMPLETE_OPTIONAL_CONSTRUCTION_DEFERRED
                : FundingNeed.NO_NEW_FUNDING_REQUIRED_BY_CURRENT_GATE, loanStatus,
                CancellationStatus.EXACT_NATIVE_CANCEL_TERMS_INTERFACE_UNAVAILABLE, pending, fundingReasons);
        return new Assessment(decision, offers, funding);
    }
    private static LoanStatus loanStatus(Optional<BoundLoan> read, GiftWarCashModel.Snapshot snapshot) {
        if (read.isEmpty()) return LoanStatus.UNKNOWN;
        var bound = read.orElseThrow(); var loan = bound.observation();
        if (!bound.frame().equals(snapshot.frame())) return LoanStatus.SOURCE_FRAME_MISMATCH;
        if (!snapshot.actor().known() || !BigInteger.valueOf(loan.source().playedCharacterId()).equals(snapshot.actor().value())
                || !BigInteger.valueOf(loan.source().dateRaw()).equals(snapshot.frame().dateRaw())) return LoanStatus.SOURCE_FRAME_MISMATCH;
        if (!(loan.borrowDecision() instanceof HolyLoanModel.ObservedDecision decision)) return LoanStatus.UNKNOWN;
        return decision.nativeGatesAllowDecision() ? LoanStatus.DECISION_GATES_ONLY_COMPLETE_TERMS_MISSING : LoanStatus.NATIVE_DECISION_REJECTED;
    }
    private static void unique(List<BigInteger> identities) {
        if (new HashSet<>(identities).size() != identities.size()) throw new IllegalArgumentException("duplicate side observation identity");
    }
    private static void nonnegative(BigInteger value, String name) {
        if (value == null || value.signum() < 0) throw new IllegalArgumentException(name + " must be nonnegative");
    }
    private static void positive(BigInteger value, String name) {
        nonnegative(value, name); if (value.signum() == 0) throw new IllegalArgumentException(name + " must be positive");
    }
}
