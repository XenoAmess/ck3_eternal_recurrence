package org.xar.ck3.control.wave2.planning.lifestyleconsumer;

import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinCodec.RoutedRequest;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy.Field;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy.RoutedDecision;
import org.xar.ck3.control.governance.lifestyleperks.LifestylePerksModel;
import org.xar.ck3.control.wave2.governance.focusscope.EducationFocusScope;
import org.xar.ck3.control.wave2.governance.focusscope.EducationFocusScope.CurrentEducationFact;
import org.xar.ck3.control.wave2.governance.focusscope.EducationFocusScope.FormalScope;
import org.xar.ck3.control.wave2.governance.focusscope.EducationFocusScope.RetainedCombined;
import org.xar.ck3.control.wave3.governance.lifestylehistory.LifestyleHistory;
import org.xar.ck3.control.wave3.governance.lifestylehistory.LifestyleHistoryConsumer;

/** Pure consumer routing for an already observed LIFE query. Domain owners retain every policy and history reducer. */
public final class LifestyleConsumer {
    private LifestyleConsumer() { }
    public enum ScopeStatus { ADMITTED, OUTSIDE_SCENE, ROOT_QUERY_NEEDED, UNAVAILABLE }
    public enum ObservationStatus { AVAILABLE, STOCK_FOCUS_AVAILABLE }
    public enum Route {
        KEEP_BASELINE, QUERY_ROOT, SCOPE_UNAVAILABLE, EDUCATION_CONTINUE, NATIVE_QUERY_UNAVAILABLE,
        PERK_SUBMIT, FOCUS_SUBMIT, ACTION_NOT_FIREABLE, NO_LEGAL_MINIMUM, OBSERVATION_UNAVAILABLE
    }
    public record Scope(ScopeStatus status, Field<Boolean> atPeace, Field<Boolean> collectTaxes,
                        Field<String> governmentKey, BigInteger snapshotRevision, BigInteger playerCharacterId) {
        public Scope { Objects.requireNonNull(status); Objects.requireNonNull(atPeace); Objects.requireNonNull(collectTaxes); Objects.requireNonNull(governmentKey); }
    }
    public sealed interface Query permits Unavailable, EducationQuery, AvailableQuery { }
    public record Unavailable() implements Query { }
    public record EducationQuery(RetainedCombined evidence) implements Query { }
    public record AvailableQuery(ObservationStatus status, String formalPreconditionStatus, RoutedRequest policyRequest) implements Query {
        public AvailableQuery { Objects.requireNonNull(status); Objects.requireNonNull(policyRequest); }
    }
    public record Request(boolean baselineLifeAdvance, Scope scope, Query query) {
        public Request {
            require(!baselineLifeAdvance || scope != null, "scope projection required for LIFE continuation");
            require(!baselineLifeAdvance || scope.status != ScopeStatus.ADMITTED || query != null, "observed query branch required");
        }
    }
    public record Outcome(Route route, RoutedDecision recommendation, CurrentEducationFact educationFact) {
        public Outcome {
            Objects.requireNonNull(route);
            require((route == Route.EDUCATION_CONTINUE) == (educationFact != null), "education route/fact mismatch");
            boolean decisionRoute = switch (route) {
                case PERK_SUBMIT, FOCUS_SUBMIT, ACTION_NOT_FIREABLE, NO_LEGAL_MINIMUM, OBSERVATION_UNAVAILABLE -> true;
                default -> false;
            };
            require(decisionRoute == (recommendation != null), "recommendation route mismatch");
        }
    }

    public static Outcome consume(Request input) { return consume(input, null); }

    /** Application entry consumes the sole governance history reducer, never a caller-supplied GREEN flag. */
    public static Outcome consumeWithHistory(Request input, LifestyleHistory.Input originalHistory) {
        Objects.requireNonNull(input); Objects.requireNonNull(originalHistory);
        if (input.query instanceof AvailableQuery query && query.policyRequest.minimum().snapshot().present()) {
            Field<String> episode = query.policyRequest.minimum().snapshot().value().episodeRunId();
            require(!episode.present() || Objects.equals(episode.value(), originalHistory.episodeRunId()), "history and current LIFE observation crossed episodes");
        }
        return consume(input, LifestyleHistory.select(originalHistory));
    }

    private static Outcome consume(Request input, LifestyleHistory.Selection history) {
        Objects.requireNonNull(input);
        if (!input.baselineLifeAdvance) { return simple(Route.KEEP_BASELINE); }
        switch (input.scope.status) {
            case OUTSIDE_SCENE -> { return simple(Route.KEEP_BASELINE); }
            case ROOT_QUERY_NEEDED -> { return simple(Route.QUERY_ROOT); }
            case UNAVAILABLE -> { return simple(Route.SCOPE_UNAVAILABLE); }
            case ADMITTED -> { /* Continue with actual query evidence. */ }
        }
        if (input.query instanceof EducationQuery education) {
            EducationFocusScope.Qualification qualified = EducationFocusScope.consumeFormal(education.evidence,
                    new FormalScope("admitted", input.scope.snapshotRevision, input.scope.playerCharacterId));
            return qualified instanceof EducationFocusScope.Qualified observed
                    ? new Outcome(Route.EDUCATION_CONTINUE, null, observed.fact()) : simple(Route.NATIVE_QUERY_UNAVAILABLE);
        }
        if (!(input.query instanceof AvailableQuery query)) { return simple(Route.NATIVE_QUERY_UNAVAILABLE); }
        RoutedRequest policy = query.policyRequest;
        LifestyleMinPolicy.Request minimum = history == null ? policy.minimum()
                : LifestyleHistoryConsumer.applyPendingGuard(policy.minimum(), history);
        RoutedDecision decision = LifestyleMinPolicy.chooseRouted(minimum, policy.allLifestyle());
        if (decision.status() == LifestyleMinPolicy.Status.RECOMMEND_ACTION) {
            boolean perk;
            if (decision instanceof LifestyleMinPolicy.MinimumDecision original) {
                perk = original.decision().selectedAction().kind() == LifestyleMinPolicy.Kind.PERK;
            } else {
                LifestyleMinPolicy.AllLifestyleDecision all = (LifestyleMinPolicy.AllLifestyleDecision) decision;
                require(all.decision() instanceof LifestylePerksModel.Recommendation, "V3 recommendation variant required");
                LifestylePerksModel.Recommendation selected = (LifestylePerksModel.Recommendation) all.decision();
                require("perk".equals(selected.action().kind()), "V3 policy only recommends its own perk kind"); perk = true;
            }
            if (perk && "ready".equals(query.formalPreconditionStatus)) { return new Outcome(Route.PERK_SUBMIT, decision, null); }
            if (!perk && query.status == ObservationStatus.STOCK_FOCUS_AVAILABLE
                    && "stock_focus_ready".equals(query.formalPreconditionStatus)) { return new Outcome(Route.FOCUS_SUBMIT, decision, null); }
            return new Outcome(Route.ACTION_NOT_FIREABLE, decision, null);
        }
        return new Outcome(decision.status() == LifestyleMinPolicy.Status.NO_LEGAL_MINIMUM ? Route.NO_LEGAL_MINIMUM : Route.OBSERVATION_UNAVAILABLE, decision, null);
    }
    private static Outcome simple(Route route) { return new Outcome(route, null, null); }
    private static void require(boolean condition, String message) { if (!condition) { throw new IllegalArgumentException(message); } }
}
