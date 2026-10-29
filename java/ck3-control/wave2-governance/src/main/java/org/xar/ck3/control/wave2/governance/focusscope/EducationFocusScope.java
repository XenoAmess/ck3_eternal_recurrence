package org.xar.ck3.control.wave2.governance.focusscope;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

/** Independent current-focus fact and its three existing consumer rechecks; never an action permit. */
public final class EducationFocusScope {
    public static final String QUERY_SCHEMA = "child-education-focus-private-12004-v1";
    public static final String EXACT_BUILD = "1.20.0.4";
    public static final String EXE_SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    public static final String FACT_STATUS = "adult_lifestyle_not_applicable_current_education_focus";
    public static final Set<String> BINDING_ERRORS = Set.of(
            "native_lifestyle_current_state_current_lifestyle_getter_failed",
            "native_lifestyle_current_state_current_lifestyle_key_read_failed");
    public static final SourceReview SOURCE_REVIEW = new SourceReview(
            "common/focuses/00_education_focuses.txt", "f24d82c5d6d349bcd60f481ef10ccf711550f2738d2efa4f3b7829047e70ec5d",
            "education", "ck3_12004_child_current_focus_readonly.hpp", "22d6c72bbf2823ae7932d51d764f3a1585cd74bf035a1bbd6e811de9656657e6");
    private EducationFocusScope() { }

    public enum FocusKey {
        DIPLOMACY("education_diplomacy"), MARTIAL("education_martial"), STEWARDSHIP("education_stewardship"),
        INTRIGUE("education_intrigue"), LEARNING("education_learning");
        private final String wire;
        FocusKey(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Optional<FocusKey> observed(String key) {
            for (FocusKey value : values()) { if (value.wire.equals(key)) { return Optional.of(value); } }
            return Optional.empty();
        }
    }

    /** All nine projection keys are emitted. Null represents an actually missing/null native field. */
    public record Frame(String snapshotId, BigInteger revision, BigInteger nativeRevision, BigInteger dateRaw,
            String episodeRunId, Boolean paused, Boolean mapReady, BigInteger playerCharacterId, Boolean actorAlive) { }
    public record PlayedCharacter(BigInteger characterId, Boolean alive) { }
    public record SemanticSnapshot(String snapshotId, BigInteger revision, BigInteger nativeRevision, BigInteger dateRaw,
            String episodeRunId, Boolean paused, Boolean mapReady, PlayedCharacter playedCharacter) { }
    public record NativeSourceFrame(String snapshotId, String episodeRunId, BigInteger nativeRevision,
            BigInteger dateRaw, BigInteger controllerFullId, Boolean paused) { }
    public record SourceContext(NativeSourceFrame frame, BigInteger publicRevision, String exactBuild, String executableSha256) {
        public SourceContext { Objects.requireNonNull(frame); }
    }
    public record CurrentFocus(Boolean available, String unavailableReason, String presence, String key) { }
    /** Extensible native query is projected only onto the fields actually consumed by the original qualifier. */
    public record Query(String schema, String kind, String status, BigInteger childFullId, String targetKey,
            BigInteger sourcePublicRevision, NativeSourceFrame sourceFrame, SourceContext sourceContext,
            String requestId, CurrentFocus currentFocus) { }
    public record SourceReview(String definitionPath, String definitionSha256, String definitionType,
            String reader, String readerSha256) {
        public SourceReview { StrictJson.text(definitionPath); StrictJson.text(definitionSha256);
            StrictJson.text(definitionType); StrictJson.text(reader); StrictJson.text(readerSha256); }
    }
    public record CurrentEducationFact(FocusKey currentFocus, Frame sourceFrame, SourceReview sourceReview) {
        public CurrentEducationFact { Objects.requireNonNull(currentFocus); Objects.requireNonNull(sourceFrame); Objects.requireNonNull(sourceReview); }
        public boolean ageObserved() { return false; }
        // No action legality field is accepted from an input. Its wire representation is always JSON null.
    }
    public enum Rejection {
        MISSING_QUERY_OR_FRAME, FRAME_NOT_CURRENT_AND_PAUSED, QUERY_SOURCE_OR_FOCUS_INVALID,
        COMBINED_SOURCE_CHANGED, FALLBACK_NOT_APPLICABLE, RETAINED_FACT_CHANGED,
        FORMAL_SCOPE_CHANGED, OPENING_SOURCE_CHANGED, OPENING_PENDING_ACTION
    }
    public sealed interface Qualification permits Qualified, Unqualified { }
    public record Qualified(CurrentEducationFact fact) implements Qualification { public Qualified { Objects.requireNonNull(fact); } }
    public record Unqualified(Rejection reason) implements Qualification { public Unqualified { Objects.requireNonNull(reason); } }
    public record StateQuery(String status, String nativeError) { }
    public enum CurrentStateRoute { CONTINUE_STOCK_FOCUS_PATH, PROBE_EDUCATION_FOCUS, RETAIN_CURRENT_UNAVAILABLE }
    public enum CombinedStatus {
        EDUCATION_FOCUS_NOT_APPLICABLE("education_focus_not_applicable"), CURRENT_STATE_UNAVAILABLE("current_state_unavailable");
        private final String wire;
        CombinedStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record CombinedDecision(CombinedStatus status, Optional<CurrentEducationFact> fact) {
        public CombinedDecision { Objects.requireNonNull(status); Objects.requireNonNull(fact);
            StrictJson.require((status == CombinedStatus.EDUCATION_FOCUS_NOT_APPLICABLE) == fact.isPresent(), "combined decision/fact mismatch"); }
    }
    public record RetainedCombined(String status, StateQuery state, Frame sourceFrame,
            CurrentEducationFact retainedFact, Query educationQuery) { }
    /** Any observed pending object blocks the opening branch, regardless of whether its status is recognized. */
    public record PendingAction(String actionRequestId, String status) { }
    public record FormalScope(String status, BigInteger snapshotRevision, BigInteger playerCharacterId) { }
    public record OpeningInput(RetainedCombined combined, Frame before, Frame after, BigInteger expectedRevision,
            StateQuery formal, PendingAction pendingAction) { }

    public static Frame project(SemanticSnapshot snapshot) {
        Objects.requireNonNull(snapshot);
        PlayedCharacter played = snapshot.playedCharacter();
        return new Frame(snapshot.snapshotId(), snapshot.revision(), snapshot.nativeRevision(), snapshot.dateRaw(),
                snapshot.episodeRunId(), snapshot.paused(), snapshot.mapReady(), played == null ? null : played.characterId(),
                played == null ? null : played.alive());
    }

    public static Qualification qualify(Query query, Frame frame, BigInteger expectedRevision) {
        if (query == null || frame == null) { return new Unqualified(Rejection.MISSING_QUERY_OR_FRAME); }
        BigInteger actor = frame.playerCharacterId();
        if (!positive(actor) || !positive(frame.nativeRevision()) || !positive(expectedRevision)
                || !expectedRevision.equals(frame.revision()) || !Objects.equals(frame.snapshotId(), "native:" + frame.nativeRevision())
                || frame.episodeRunId() == null || !frame.episodeRunId().startsWith("native-" + actor + "-")
                || frame.dateRaw() == null || frame.dateRaw().signum() < 0 || !Boolean.TRUE.equals(frame.paused())
                || !Boolean.TRUE.equals(frame.mapReady()) || !Boolean.TRUE.equals(frame.actorAlive())) {
            return new Unqualified(Rejection.FRAME_NOT_CURRENT_AND_PAUSED);
        }
        NativeSourceFrame expectedSource = new NativeSourceFrame(frame.snapshotId(), frame.episodeRunId(), frame.nativeRevision(),
                frame.dateRaw(), actor, true);
        SourceContext expectedContext = new SourceContext(expectedSource, expectedRevision, EXACT_BUILD, EXE_SHA256);
        CurrentFocus focus = query.currentFocus();
        Optional<FocusKey> key = focus == null ? Optional.empty() : FocusKey.observed(focus.key());
        if (!QUERY_SCHEMA.equals(query.schema()) || !"query".equals(query.kind())
                || !("available".equals(query.status()) || "unavailable".equals(query.status()))
                || !actor.equals(query.childFullId()) || !"education_stewardship".equals(query.targetKey())
                || !expectedRevision.equals(query.sourcePublicRevision()) || !expectedSource.equals(query.sourceFrame())
                || !expectedContext.equals(query.sourceContext()) || query.requestId() == null || query.requestId().isEmpty()
                || focus == null || !Boolean.TRUE.equals(focus.available()) || focus.unavailableReason() != null
                || !"present".equals(focus.presence()) || key.isEmpty()) {
            return new Unqualified(Rejection.QUERY_SOURCE_OR_FOCUS_INVALID);
        }
        return new Qualified(new CurrentEducationFact(key.orElseThrow(), frame, SOURCE_REVIEW));
    }

    public static CurrentStateRoute routeCurrentState(StateQuery state) {
        if (state != null && "available".equals(state.status())) { return CurrentStateRoute.CONTINUE_STOCK_FOCUS_PATH; }
        return recognizedBindingFailure(state) ? CurrentStateRoute.PROBE_EDUCATION_FOCUS : CurrentStateRoute.RETAIN_CURRENT_UNAVAILABLE;
    }

    /** Combined reader's pure post-read seam. Actual read/callability/exception ownership stays with the single driver. */
    public static CombinedDecision combine(StateQuery state, Frame before, Frame after, Query query, BigInteger expectedRevision) {
        if (routeCurrentState(state) == CurrentStateRoute.CONTINUE_STOCK_FOCUS_PATH) {
            throw new ProjectionDomainRejection("available LIFE2 takes its existing stock-focus path outside the education fallback");
        }
        if (!recognizedBindingFailure(state) || before == null || !before.equals(after)) { return unavailableCombined(); }
        Qualification qualified = qualify(query, before, expectedRevision);
        return qualified instanceof Qualified observed
                ? new CombinedDecision(CombinedStatus.EDUCATION_FOCUS_NOT_APPLICABLE, Optional.of(observed.fact())) : unavailableCombined();
    }

    /** Existing ordinary-plan consumer requalifies the actual query instead of trusting a retained success flag. */
    public static Qualification consumeFormal(RetainedCombined evidence, FormalScope scope) {
        if (evidence == null || scope == null || !"admitted".equals(scope.status())
                || !CombinedStatus.EDUCATION_FOCUS_NOT_APPLICABLE.wire().equals(evidence.status()) || evidence.sourceFrame() == null) {
            return new Unqualified(Rejection.FALLBACK_NOT_APPLICABLE);
        }
        Qualification checked = qualify(evidence.educationQuery(), evidence.sourceFrame(), evidence.sourceFrame().revision());
        if (!(checked instanceof Qualified observed) || !observed.fact().equals(evidence.retainedFact()) || !recognizedBindingFailure(evidence.state())) {
            return new Unqualified(Rejection.RETAINED_FACT_CHANGED);
        }
        if (!Objects.equals(scope.snapshotRevision(), evidence.sourceFrame().nativeRevision())
                || !Objects.equals(scope.playerCharacterId(), evidence.sourceFrame().playerCharacterId())) {
            return new Unqualified(Rejection.FORMAL_SCOPE_CHANGED);
        }
        return observed;
    }

    /** Opening consumer's fact check only; this never mutates a gate or calls the ordinary planner. */
    public static Qualification consumeOpening(OpeningInput input) {
        if (input == null || input.combined() == null || !CombinedStatus.EDUCATION_FOCUS_NOT_APPLICABLE.wire().equals(input.combined().status())) {
            return new Unqualified(Rejection.FALLBACK_NOT_APPLICABLE);
        }
        RetainedCombined combined = input.combined();
        Qualification checked = qualify(combined.educationQuery(), input.before(), input.expectedRevision());
        if (!(checked instanceof Qualified observed) || !observed.fact().equals(combined.retainedFact())
                || !Objects.equals(combined.sourceFrame(), input.before()) || !Objects.equals(input.after(), input.before())
                || !recognizedBindingFailure(input.formal()) || !recognizedBindingFailure(combined.state())
                || !Objects.equals(input.formal().nativeError(), combined.state().nativeError())) {
            return new Unqualified(Rejection.OPENING_SOURCE_CHANGED);
        }
        if (input.pendingAction() != null) { return new Unqualified(Rejection.OPENING_PENDING_ACTION); }
        return observed;
    }

    private static boolean recognizedBindingFailure(StateQuery state) {
        return state != null && "native_query_unavailable".equals(state.status()) && state.nativeError() != null && BINDING_ERRORS.contains(state.nativeError());
    }
    private static boolean positive(BigInteger value) { return value != null && value.signum() > 0; }
    private static CombinedDecision unavailableCombined() { return new CombinedDecision(CombinedStatus.CURRENT_STATE_UNAVAILABLE, Optional.empty()); }
}
