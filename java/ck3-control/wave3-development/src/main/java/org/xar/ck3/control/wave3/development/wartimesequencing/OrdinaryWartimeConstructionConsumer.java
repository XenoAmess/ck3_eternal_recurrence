package org.xar.ck3.control.wave3.development.wartimesequencing;

import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.locks.Lock;
import java.util.function.Function;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQuoteIdentity;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.Disposition;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.Request;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.Result;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.Reason;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.Stage;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec.ObservedRequest;

/** Host consumer. Current reads and the final existing-authority callback are never accepted from HTTP. */
public final class OrdinaryWartimeConstructionConsumer {
    private OrdinaryWartimeConstructionConsumer() { }
    @FunctionalInterface public interface CurrentRequest { ObservedRequest readCurrent(); }
    @FunctionalInterface public interface Evaluator { Result evaluate(ObservedRequest observed); }
    public sealed interface QuoteRead permits ObservedQuote, UnavailableQuote { }
    public record ObservedQuote(ObservedRequest request) implements QuoteRead { public ObservedQuote { Objects.requireNonNull(request); } }
    public enum UnavailableReason { NATIVE_PROVIDER_UNAVAILABLE, CURRENT_SOURCE_UNAVAILABLE }
    public record UnavailableQuote(UnavailableReason reason) implements QuoteRead { public UnavailableQuote { Objects.requireNonNull(reason); } }
    @FunctionalInterface public interface QuotedRequest { QuoteRead readQuote(); }
    public enum FinalStatus {
        PLANNED_CANDIDATE_UNAVAILABLE, CURRENT_SELECTION_CHANGED, CURRENT_FRAME_CHANGED,
        CURRENT_QUOTE_UNAVAILABLE, CURRENT_QUOTE_CHANGED, CURRENT_OPTIONAL_SPEND_DEFERRED, EXISTING_AUTHORITY_CALLED
    }
    public record FinalReview(FinalStatus status, Optional<Result> currentAssessment) {
        public FinalReview { Objects.requireNonNull(status); Objects.requireNonNull(currentAssessment); }
        public boolean existingAuthorityCalled() { return status == FinalStatus.EXISTING_AUTHORITY_CALLED; }
        public boolean nativeActionAppliedVerified() { return false; }
        public boolean continueOrdinaryPlanner() { return true; }
    }
    /** Calling the existing authority is recorded separately from its actual native/ledger outcome. */
    public record BeforeIntent<T>(FinalStatus status, Optional<Result> currentAssessment, Optional<T> existingAuthorityResult) {
        public BeforeIntent {
            Objects.requireNonNull(status); Objects.requireNonNull(currentAssessment); Objects.requireNonNull(existingAuthorityResult);
            if ((status == FinalStatus.EXISTING_AUTHORITY_CALLED) != existingAuthorityResult.isPresent())
                throw new IllegalArgumentException("existing authority callback branch differs");
        }
        public boolean continueOrdinaryPlanner() { return true; }
        public boolean nativeActionAppliedVerified() { return false; }
        public FinalReview review() { return new FinalReview(status, currentAssessment); }
    }

    /** The optional native quote is not queried when the current reserve gate defers it. */
    public static Result plan(CurrentRequest current, QuotedRequest quote) {
        return plan(current, quote, observed -> OrdinaryWartimeConstruction.compose(observed.input()));
    }
    public static Result plan(CurrentRequest current, QuotedRequest quote, Evaluator evaluator) {
        Objects.requireNonNull(current); Objects.requireNonNull(quote); Objects.requireNonNull(evaluator);
        ObservedRequest preObserved = Objects.requireNonNull(current.readCurrent()); Request pre = preObserved.input();
        if (pre.stage() != Stage.BEFORE_OPTIONAL_QUERY) throw new IllegalArgumentException("prequery request required");
        Result before = Objects.requireNonNull(evaluator.evaluate(preObserved));
        if (before.disposition() != Disposition.OPTIONAL_QUERY_ALLOWED) return before;
        QuoteRead read = Objects.requireNonNull(quote.readQuote());
        if (read instanceof UnavailableQuote) return new Result(pre.selection(), pre.stage(), Disposition.DEFER_OPTIONAL_CONSTRUCTION,
                Optional.of(Reason.QUERY_SOURCE_UNAVAILABLE), before.cash(), Optional.empty(), Optional.empty(), before.financing());
        ObservedRequest quotedObserved = ((ObservedQuote) read).request(); Request quoted = quotedObserved.input();
        if (quoted.stage() != Stage.QUOTED_OUTLAY || !quoted.selection().equals(pre.selection()))
            throw new IllegalArgumentException("quote must preserve the ordinary selection");
        return Objects.requireNonNull(evaluator.evaluate(quotedObserved));
    }

    /**
     * Call using the original single writer's lock and existing intent-creation callback.
     * No new writer, send route, ledger, or UNKNOWN retry is introduced here. A changed
     * quote or source frame needs a new plan; changed commitments are reevaluated now.
     */
    public static <T> BeforeIntent<T> withCurrentBeforeIntent(Result planned, Lock originalWriterLock,
            CurrentRequest current, Function<Result, T> originalAuthority) {
        return withCurrentBeforeIntent(planned, originalWriterLock, current, originalAuthority,
                observed -> OrdinaryWartimeConstruction.compose(observed.input()));
    }
    public static <T> BeforeIntent<T> withCurrentBeforeIntent(Result planned, Lock originalWriterLock,
            CurrentRequest current, Function<Result, T> originalAuthority, Evaluator evaluator) {
        Objects.requireNonNull(planned); Objects.requireNonNull(originalWriterLock);
        Objects.requireNonNull(current); Objects.requireNonNull(originalAuthority); Objects.requireNonNull(evaluator);
        if (planned.disposition() != Disposition.QUOTED_CANDIDATE) return finalResult(FinalStatus.PLANNED_CANDIDATE_UNAVAILABLE, Optional.of(planned));
        originalWriterLock.lock();
        try {
            ObservedRequest freshObserved = Objects.requireNonNull(current.readCurrent()); Request fresh = freshObserved.input();
            if (fresh.stage() != Stage.QUOTED_OUTLAY || !fresh.selection().equals(planned.originalSelection()))
                return finalResult(FinalStatus.CURRENT_SELECTION_CHANGED, Optional.empty());
            Result rechecked = Objects.requireNonNull(evaluator.evaluate(freshObserved));
            Optional<Result> assessment = Optional.of(rechecked);
            if (!fresh.current().context().snapshot().frame().equals(planned.cash().frame())) return finalResult(FinalStatus.CURRENT_FRAME_CHANGED, assessment);
            var before = planned.candidate().orElseThrow();
            var selected = fresh.quoted().orElseThrow().nativeQuote().selected();
            if (selected.isEmpty()) return finalResult(FinalStatus.CURRENT_QUOTE_UNAVAILABLE, assessment);
            var now = selected.orElseThrow();
            if (!before.candidate().equals(now.candidate()) || !before.sourceFrame().equals(now.sourceFrame())
                    || !ConstructionQuoteIdentity.same(before.original().bytes(), now.original().bytes())) return finalResult(FinalStatus.CURRENT_QUOTE_CHANGED, assessment);
            if (rechecked.disposition() != Disposition.QUOTED_CANDIDATE) return finalResult(FinalStatus.CURRENT_OPTIONAL_SPEND_DEFERRED, assessment);
            return new BeforeIntent<>(FinalStatus.EXISTING_AUTHORITY_CALLED, assessment, Optional.of(Objects.requireNonNull(originalAuthority.apply(rechecked))));
        } finally {
            originalWriterLock.unlock();
        }
    }
    private static <T> BeforeIntent<T> finalResult(FinalStatus status, Optional<Result> assessment) {
        return new BeforeIntent<>(status, assessment, Optional.empty());
    }
}
