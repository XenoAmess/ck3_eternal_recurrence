package org.xar.ck3.control.wave3.development.wartimesequencing;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyAdapters;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.ConstructionQuote;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.QuoteCashObservation;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.QuoteProjection;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.ObservedCash;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Read;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.SourceFrame;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessment;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessment.Assessment;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessmentCodec;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryCodec;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryModel;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryPolicy;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionCash;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionModel.Decision;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionModel.Input;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionModel.Status;

/** Ordinary construction sequence over the existing cash producers. It never submits an action. */
public final class OrdinaryWartimeConstruction {
    private OrdinaryWartimeConstruction() { }

    public enum Opportunity {
        CONTINUE_SELECTED_WORK, ORDINARY_ADVANCE, PREWAR_ARBITRATION, QUIET_ROUTE_ADVANCE;
        public boolean admitsOptionalQuote() { return this != CONTINUE_SELECTED_WORK; }
    }
    public enum Stage { BEFORE_OPTIONAL_QUERY, QUOTED_OUTLAY }
    public enum Disposition { CONTINUE_SELECTED_WORK, DEFER_OPTIONAL_CONSTRUCTION, OPTIONAL_QUERY_ALLOWED, QUOTED_CANDIDATE }
    public enum Reason {
        SELECTED_WORK_HAS_PRIORITY, RESERVE_NOT_RETAINED, QUERY_SOURCE_UNAVAILABLE, QUOTE_IDENTITY_UNAVAILABLE,
        QUOTE_COST_OR_WALLET_MISMATCH, QUOTE_FRAME_MISMATCH, MONTHLY_CASH_SOURCE_MISMATCH, CURRENT_OR_ALL_RAISED_CASH_NOT_RETAINED,
        FINANCING_ACTION_UNKNOWN, FINANCING_OBSERVATION_UNAVAILABLE
    }
    public enum FinancingStatus { UNAVAILABLE, SOURCE_FRAME_MISMATCH, CURRENT }
    public record FinancingReview(FinancingStatus status, Optional<Assessment> assessment) {
        public FinancingReview {
            Objects.requireNonNull(status); Objects.requireNonNull(assessment);
            if ((status == FinancingStatus.CURRENT) != assessment.isPresent()) throw new IllegalArgumentException("financing source branch");
        }
    }
    public record Selection(Optional<String> step, Optional<String> phase, Opportunity opportunity) {
        public Selection {
            Objects.requireNonNull(step); Objects.requireNonNull(phase); Objects.requireNonNull(opportunity);
            step.ifPresent(StrictJson::text); phase.ifPresent(StrictJson::text);
            if (!OrdinaryConstructionOpportunity.matches(step, phase, opportunity))
                throw new IllegalArgumentException("optional opportunity differs from the actual original selected step/phase");
        }
    }
    /** Original native observation, finalized by the real source validator and authored selector. */
    public static final class NativeQuote {
        private final byte[] original;
        private final ConstructionQueryModel.Observation observation;
        private final Optional<ConstructionQuote> selected;
        private final Optional<String> constructionKind;
        public NativeQuote(byte[] original) {
            this.observation = ConstructionQueryCodec.decode(original);
            this.original = original.clone();
            var result = ConstructionQueryPolicy.finalizeObservation(observation);
            if (result instanceof ConstructionQueryModel.Ready ready && ready.kind() == ConstructionQueryModel.ReadyKind.SELECTED) {
                byte[] finalized = ConstructionQueryCodec.finalizeObservation(this.original);
                if (finalized.length <= org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyCodec.MAX_BYTES) {
                    selected = Optional.of(org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyCodec.decodeQuote(finalized));
                    constructionKind = Optional.of(ready.candidate().slotWasEmpty() ? "new_building" : "upgrade_building");
                } else {
                    selected = Optional.empty(); constructionKind = Optional.empty();
                }
            } else {
                selected = Optional.empty(); constructionKind = Optional.empty();
            }
        }
        public byte[] original() { return original.clone(); }
        public ConstructionQueryModel.Observation observation() { return observation; }
        public Optional<ConstructionQuote> selected() {
            return selected;
        }
        public Optional<String> constructionKind() { return constructionKind; }
    }
    public record QuotedOutlay(NativeQuote nativeQuote, QuoteCashObservation currentCash) {
        public QuotedOutlay { Objects.requireNonNull(nativeQuote); Objects.requireNonNull(currentCash); }
    }
    public record Request(Selection selection, Stage stage, Input current, Optional<QuotedOutlay> quoted,
                          Optional<EmergencyFinancingAssessmentCodec.Request> financing) {
        public Request {
            Objects.requireNonNull(selection); Objects.requireNonNull(stage); Objects.requireNonNull(current); Objects.requireNonNull(quoted); Objects.requireNonNull(financing);
            if ((stage == Stage.QUOTED_OUTLAY) != quoted.isPresent()) throw new IllegalArgumentException("quoted stage shape");
        }
    }
    public record Result(Selection originalSelection, Stage stage, Disposition disposition,
                         Optional<Reason> reason, Decision cash, Optional<QuoteProjection> monthly,
                         Optional<ConstructionQuote> candidate, FinancingReview financing) {
        public Result {
            Objects.requireNonNull(originalSelection); Objects.requireNonNull(stage); Objects.requireNonNull(disposition);
            Objects.requireNonNull(reason); Objects.requireNonNull(cash); Objects.requireNonNull(monthly); Objects.requireNonNull(candidate);
            Objects.requireNonNull(financing);
            if ((disposition == Disposition.QUOTED_CANDIDATE) != candidate.isPresent()) throw new IllegalArgumentException("candidate result branch");
        }
        /** Optional input failure leaves the full ordinary planner's choice intact. */
        public Optional<String> selectedStep() { return originalSelection.step(); }
        public boolean continueOrdinaryPlanner() { return true; }
        public boolean canSubmitAction() { return false; }
        public BigInteger unreceivedFundingCreditedRaw() { return BigInteger.ZERO; }
    }

    public static Result compose(Request request) {
        Objects.requireNonNull(request);
        Input observed = request.current();
        Input cashInput = request.stage() == Stage.BEFORE_OPTIONAL_QUERY ? zeroSpend(observed) : observed;
        Decision cash = WartimeConstructionCash.observe(cashInput);
        if (!request.selection().opportunity().admitsOptionalQuote())
            return result(request, Disposition.CONTINUE_SELECTED_WORK, Reason.SELECTED_WORK_HAS_PRIORITY, cash, Optional.empty());
        if (!cash.newSpendAllowed())
            return result(request, Disposition.DEFER_OPTIONAL_CONSTRUCTION, Reason.RESERVE_NOT_RETAINED, cash, Optional.empty());
        FinancingReview financing = reviewFinancing(request);
        // Wartime optional spending needs a current financing observation. An unavailable
        // ledger is unknown, and must never stand in for an observed NoPendingAction.
        if (cash.status() != Status.PEACE && financing.assessment().map(value -> value.replay()
                == EmergencyFinancingAssessment.ReplayGuard.LEDGER_UNAVAILABLE).orElse(true))
            return result(request, Disposition.DEFER_OPTIONAL_CONSTRUCTION,
                    Reason.FINANCING_OBSERVATION_UNAVAILABLE, cash, Optional.empty());
        if (financing.assessment().filter(value -> value.replay()
                == EmergencyFinancingAssessment.ReplayGuard.UNRESOLVED_ACTION_NEVER_REPLAY).isPresent())
            return result(request, Disposition.DEFER_OPTIONAL_CONSTRUCTION, Reason.FINANCING_ACTION_UNKNOWN, cash, Optional.empty());
        if (request.stage() == Stage.BEFORE_OPTIONAL_QUERY)
            return result(request, Disposition.OPTIONAL_QUERY_ALLOWED, null, cash, Optional.empty());

        QuotedOutlay outlay = request.quoted().orElseThrow();
        Optional<ConstructionQuote> selected = outlay.nativeQuote().selected();
        if (selected.isEmpty()) return result(request, Disposition.DEFER_OPTIONAL_CONSTRUCTION,
                Reason.QUERY_SOURCE_UNAVAILABLE, cash, Optional.empty());
        ConstructionQuote quote = selected.orElseThrow();
        if (quote.candidate().barony().isEmpty() || quote.candidate().province().isEmpty()
                || quote.candidate().cost().isEmpty() || quote.candidate().goldBefore().isEmpty())
            return result(request, Disposition.DEFER_OPTIONAL_CONSTRUCTION, Reason.QUOTE_IDENTITY_UNAVAILABLE, cash, Optional.empty());
        if (!outlay.nativeQuote().constructionKind().equals(Optional.of(observed.kindWire()))
                || !observed.cost().known() || !observed.cost().value().equals(quote.candidate().cost().orElseThrow())
                || !observed.context().snapshot().walletRaw().known()
                || !observed.context().snapshot().walletRaw().value().equals(quote.candidate().goldBefore().orElseThrow()))
            return result(request, Disposition.DEFER_OPTIONAL_CONSTRUCTION, Reason.QUOTE_COST_OR_WALLET_MISMATCH, cash, Optional.empty());
        SourceFrame frame = cash.frame();
        var source = outlay.nativeQuote().observation().starting();
        if (!source.core().snapshotId().is(frame.snapshotId()) || !source.core().publicRevision().is(frame.revision())
                || !source.episode().is(frame.episodeRunId()) || quote.sourceFrame().isEmpty()
                || !quote.sourceFrame().orElseThrow().actor().equals(Optional.of(frame.playedCharacterId()))
                || !quote.sourceFrame().orElseThrow().revision().equals(Optional.of(frame.nativeRevision()))
                || !quote.sourceFrame().orElseThrow().date().equals(Optional.of(frame.dateRaw())))
            return result(request, Disposition.DEFER_OPTIONAL_CONSTRUCTION, Reason.QUOTE_FRAME_MISMATCH, cash, Optional.empty());
        if (outlay.currentCash() instanceof ObservedCash current) {
            var monthly = current.cash().frame(); var build = outlay.nativeQuote().observation().build();
            if (!monthly.queriedSnapshotId().equals(Optional.of(frame.snapshotId()))
                    || !monthly.queriedRevision().equals(Optional.of(frame.revision()))
                    || !monthly.queriedNativeRevision().equals(Optional.of(frame.nativeRevision()))
                    || !monthly.gameVersion().equals(build.build().wire())
                    || !monthly.executableSha256().equalsIgnoreCase(build.sha256()))
                return result(request, Disposition.DEFER_OPTIONAL_CONSTRUCTION, Reason.MONTHLY_CASH_SOURCE_MISMATCH, cash, Optional.empty());
            if (current.cash().currentMilitary().isEmpty() || current.cash().allRaisedMilitary().isEmpty())
                return result(request, Disposition.DEFER_OPTIONAL_CONSTRUCTION,
                        Reason.CURRENT_OR_ALL_RAISED_CASH_NOT_RETAINED, cash, Optional.empty());
        }
        // Preserve the existing current/all-raised one-month budget producer as well as
        // the stronger shared military/commitment/emergency reserve. Neither producer
        // receives future income, an assumed cancellation refund, or unreceived loans.
        QuoteProjection monthly = ConstructionEconomyAdapters.projectQuote(quote, outlay.currentCash(), cash.status() != Status.PEACE, true);
        if (monthly.deferredReason().isPresent())
            return result(request, Disposition.DEFER_OPTIONAL_CONSTRUCTION, Reason.CURRENT_OR_ALL_RAISED_CASH_NOT_RETAINED,
                    cash, Optional.of(monthly));
        return result(request, Disposition.QUOTED_CANDIDATE, null, cash, Optional.of(monthly));
    }

    private static Result result(Request request, Disposition disposition, Reason reason, Decision cash, Optional<QuoteProjection> monthly) {
        return new Result(request.selection(), request.stage(), disposition, Optional.ofNullable(reason), cash, monthly,
                disposition == Disposition.QUOTED_CANDIDATE ? request.quoted().orElseThrow().nativeQuote().selected() : Optional.empty(), reviewFinancing(request));
    }
    private static FinancingReview reviewFinancing(Request request) {
        if (request.financing().isEmpty()) return new FinancingReview(FinancingStatus.UNAVAILABLE, Optional.empty());
        Assessment assessment = EmergencyFinancingAssessmentCodec.assess(request.financing().orElseThrow());
        var finance = assessment.sourceFrame(); SourceFrame current = request.current().context().snapshot().frame();
        Optional<BigInteger> wallet = request.current().context().snapshot().walletRaw().known()
                ? Optional.of(request.current().context().snapshot().walletRaw().value()) : Optional.empty();
        if (!finance.playedCharacterId().equals(current.playedCharacterId()) || !finance.nativeRevision().equals(current.nativeRevision())
                || !finance.dateRaw().equals(current.dateRaw()) || !finance.snapshotId().equals(current.snapshotId())
                || !finance.revision().equals(current.revision()) || !finance.episodeRunId().equals(current.episodeRunId())
                || !assessment.actualWalletRaw().equals(wallet)) return new FinancingReview(FinancingStatus.SOURCE_FRAME_MISMATCH, Optional.empty());
        return new FinancingReview(FinancingStatus.CURRENT, Optional.of(assessment));
    }
    private static Input zeroSpend(Input observed) {
        return new Input(observed.kindWire(), Read.of(BigInteger.ZERO), observed.context(), observed.quotes(),
                observed.marketShape(), observed.procurement(), observed.focusRequest());
    }
}

