package org.xar.ck3.control.g2.planning;

import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Evaluated;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Pure planning projection. Existing submitter, reservation owner and ledger writer remain external and unchanged. */
public final class ProposalLifecycle {
    public static final int POSTCONDITION_VERSION = 1;
    private ProposalLifecycle() { }

    /** Internal immutable projection of the common validated G2 frame; it does not attest native observation. */
    public record ObservationIdentity(String machineId, GameGeneration game, ProposalFrame frame, long observationVersion) {
        public ObservationIdentity {
            require(machineId != null && !machineId.equals("unknown") && machineId.matches("[a-z0-9][a-z0-9-]{0,63}"), "explicit machine identity required");
            Objects.requireNonNull(game); fullFrame(frame); require(observationVersion > 0 && observationVersion <= StrictJson.MAX_SAFE_INTEGER, "positive safe observation contract version required");
        }
    }
    public record FieldKey(String value) {
        public FieldKey { require(value != null && value.matches("[a-z][a-z0-9_]*(?:\\.[a-z][a-z0-9_]*)*"), "declared observation field key required"); }
    }
    public sealed interface ExpectedValue permits ExpectedBoolean, ExpectedInteger, ExpectedText, ExpectedNull, ExpectedAbsent { FieldKey field(); }
    public record ExpectedBoolean(FieldKey field, boolean value) implements ExpectedValue { public ExpectedBoolean { Objects.requireNonNull(field); } }
    public record ExpectedInteger(FieldKey field, BigInteger value) implements ExpectedValue {
        public ExpectedInteger { Objects.requireNonNull(field); Objects.requireNonNull(value); require(value.abs().compareTo(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER)) <= 0, "expected numeric integer must be JavaScript-safe"); }
    }
    public record ExpectedText(FieldKey field, String value) implements ExpectedValue { public ExpectedText { Objects.requireNonNull(field); Objects.requireNonNull(value); } }
    public record ExpectedNull(FieldKey field) implements ExpectedValue { public ExpectedNull { Objects.requireNonNull(field); } }
    public record ExpectedAbsent(FieldKey field) implements ExpectedValue { public ExpectedAbsent { Objects.requireNonNull(field); } }
    public record ExpectedPostcondition(int version, ObservationIdentity before, G2Source source, String observerSchema, List<ExpectedValue> values) {
        public ExpectedPostcondition {
            require(version == POSTCONDITION_VERSION, "unsupported expected-postcondition version"); Objects.requireNonNull(before); Objects.requireNonNull(source); text(observerSchema);
            values = List.copyOf(values); require(!values.isEmpty(), "explicit expected native observations required");
            Set<FieldKey> fields = new HashSet<>(); for (ExpectedValue value : values) require(fields.add(value.field()), "duplicate expected field refused");
        }
    }
    public record CandidateIntent(String actionId, String candidateId, ExpectedPostcondition expected) {
        public CandidateIntent { identifier(actionId); text(candidateId); Objects.requireNonNull(expected); }
    }
    public enum ExternalState { UNKNOWN, ACK_RECEIVED, APPLIED_CONFIRMED, SEND_CONFIRMED, REJECTED_CONFIRMED, TERMINAL_WITHOUT_EFFECT }
    public enum UnknownScope { GLOBAL, DOMAIN, CLAIMS }
    /** Existing authoritative facts are input only. This class creates no fact and performs no state transition. */
    public record ExternalFact(String actionId, String bodySha256, ObservationIdentity origin, ExternalState state, UnknownScope scope, Domain domain,
            Claims affectedClaims, ExactRef originalEvidenceRef) {
        public ExternalFact {
            identifier(actionId); digest(bodySha256); Objects.requireNonNull(origin); Objects.requireNonNull(state); Objects.requireNonNull(scope); Objects.requireNonNull(domain);
            Objects.requireNonNull(affectedClaims); Objects.requireNonNull(originalEvidenceRef); require(originalEvidenceRef.bytes() > 0, "original fact evidence required");
            affectedClaims.armyIds().forEach(ProposalLifecycle::safeResourceId); affectedClaims.allyCharacterIds().forEach(ProposalLifecycle::safeResourceId); affectedClaims.characterIds().forEach(ProposalLifecycle::safeResourceId);
            if (scope == UnknownScope.CLAIMS) require(!empty(affectedClaims), "claims isolation requires explicit affected resources");
        }
        /** A confirmed outgoing send is terminal for its exact action; relationship effects remain separate facts. */
        public boolean unresolved() {
            return switch (state) {
                case UNKNOWN, ACK_RECEIVED -> true;
                case APPLIED_CONFIRMED, SEND_CONFIRMED, REJECTED_CONFIRMED, TERMINAL_WITHOUT_EFFECT -> false;
            };
        }
    }
    public record Input(ObservationIdentity observed, G2Source source, JointBudgetSelector.Input evaluationInput,
            List<CandidateIntent> intents, List<ExternalFact> externalFacts) {
        public Input {
            Objects.requireNonNull(observed); Objects.requireNonNull(source); Objects.requireNonNull(evaluationInput);
            require(source.machineId().equals(observed.machineId()) && source.sourceRef().bytes() > 0, "common source must bind the planner machine and an original evaluation reference");
            intents = List.copyOf(intents); externalFacts = List.copyOf(externalFacts);
            Set<String> candidates = new HashSet<>(), actions = new HashSet<>(), facts = new HashSet<>();
            for (CandidateIntent intent : intents) require(candidates.add(intent.candidateId()) && actions.add(intent.actionId()), "one exact intent per candidate/action required");
            for (ExternalFact fact : externalFacts) {
                require(facts.add(fact.actionId()), "duplicate external fact must be reduced by the existing authority first");
                require(observed.machineId().equals(fact.origin().machineId()) && observed.game().equals(fact.origin().game())
                        && observed.frame().episodeRunId().equals(fact.origin().frame().episodeRunId()), "external action fact crossed Game generation or episode; existing authority must reconcile it");
            }
        }
    }
    public record ProposedBody(String actionId, ObservationIdentity observed, G2Source source, Evaluated candidate, ExpectedPostcondition expected) {
        public ProposedBody {
            identifier(actionId); Objects.requireNonNull(observed); Objects.requireNonNull(source); Objects.requireNonNull(candidate); Objects.requireNonNull(expected);
            require(candidate.reason() == JointBudgetSelector.Reason.ELIGIBLE, "only the original selector's eligible candidate can be proposed");
            require(observed.equals(expected.before()) && source.equals(expected.source()), "expected post-state crossed observation/source boundary");
        }
    }
    public record ProposedAction(ProposedBody body, String bodySha256) {
        public ProposedAction { Objects.requireNonNull(body); digest(bodySha256); }
        public boolean dispatchAllowed() { return false; }
        public boolean intentDurable() { return false; }
    }
    @FunctionalInterface interface CanonicalBodyDigest { String sha256(ProposedBody body); }
    public enum DeferredReason { MISSING_ASSESSMENTS, NO_SELECTED_CANDIDATE, MISSING_EXPECTED_POSTCONDITION, EXISTING_UNKNOWN, ALREADY_RECORDED }
    public sealed interface Plan permits Proposed, Deferred, Conflict { JointBudgetSelector.Result evaluation(); }
    public record Proposed(JointBudgetSelector.Result evaluation, ProposedAction action) implements Plan {
        public Proposed {
            Objects.requireNonNull(evaluation); Objects.requireNonNull(action);
            require(evaluation.status() == JointBudgetSelector.Status.SELECTED && action.body().candidate().candidateId().equals(evaluation.selectedCandidateId())
                    && evaluation.evaluated().contains(action.body().candidate()) && evaluation.frame().equals(action.body().observed().frame().identity()), "proposal must retain the complete original selected evaluation");
        }
    }
    public record Deferred(JointBudgetSelector.Result evaluation, DeferredReason reason, List<ExternalFact> blockingFacts) implements Plan {
        public Deferred { Objects.requireNonNull(evaluation); Objects.requireNonNull(reason); blockingFacts = List.copyOf(blockingFacts); }
    }
    public record Conflict(JointBudgetSelector.Result evaluation, String actionId, String priorBodySha256, String proposedBodySha256) implements Plan {
        public Conflict { Objects.requireNonNull(evaluation); identifier(actionId); digest(priorBodySha256); digest(proposedBodySha256); require(!priorBodySha256.equals(proposedBodySha256), "body conflict requires different exact bodies"); }
    }

    static Plan plan(Input input, CanonicalBodyDigest canonicalBodyDigest) {
        Objects.requireNonNull(input); Objects.requireNonNull(canonicalBodyDigest);
        ProposalFrame evaluatedFrame = switch (input.evaluationInput()) {
            case JointBudgetSelector.AssessedInput value -> value.intake().frame();
            case JointBudgetSelector.MissingAssessments value -> value.intake().frame();
        };
        require(input.observed().frame().equals(evaluatedFrame), "evaluation crossed the complete G2 observed frame");
        JointBudgetSelector.Result evaluation = JointBudgetSelector.select(input.evaluationInput());
        if (evaluation.status() == JointBudgetSelector.Status.MISSING_ASSESSMENTS) return new Deferred(evaluation, DeferredReason.MISSING_ASSESSMENTS, List.of());
        if (evaluation.selectedCandidateId() == null) return new Deferred(evaluation, DeferredReason.NO_SELECTED_CANDIDATE, List.of());
        CandidateIntent intent = input.intents().stream().filter(row -> row.candidateId().equals(evaluation.selectedCandidateId())).findFirst().orElse(null);
        if (intent == null) return new Deferred(evaluation, DeferredReason.MISSING_EXPECTED_POSTCONDITION, List.of());
        Evaluated selected = evaluation.evaluated().stream().filter(row -> row.candidateId().equals(evaluation.selectedCandidateId())).findFirst().orElseThrow();
        ProposedBody body = new ProposedBody(intent.actionId(), input.observed(), input.source(), selected, intent.expected());
        String sha = canonicalBodyDigest.sha256(body); digest(sha);
        ExternalFact sameAction = input.externalFacts().stream().filter(row -> row.actionId().equals(body.actionId())).findFirst().orElse(null);
        if (sameAction != null && !sameAction.bodySha256().equals(sha)) return new Conflict(evaluation, body.actionId(), sameAction.bodySha256(), sha);
        if (sameAction != null) return new Deferred(evaluation, sameAction.unresolved() ? DeferredReason.EXISTING_UNKNOWN : DeferredReason.ALREADY_RECORDED, List.of(sameAction));
        List<ExternalFact> blocked = input.externalFacts().stream().filter(ExternalFact::unresolved).filter(fact -> switch (fact.scope()) {
            case GLOBAL -> true;
            case DOMAIN -> fact.domain().name().equals(selected.domain());
            case CLAIMS -> fact.affectedClaims().overlaps(selected.claims());
        }).toList();
        return blocked.isEmpty() ? new Proposed(evaluation, new ProposedAction(body, sha)) : new Deferred(evaluation, DeferredReason.EXISTING_UNKNOWN, blocked);
    }

    public enum ObservationComparison { EXPECTED_FIELDS_MATCH, EXPECTED_FIELDS_DIFFER, STALE_VERSION, SOURCE_DRIFT, GAME_OR_EPISODE_DRIFT }
    /** Comparison is advisory. Even a complete match cannot settle a fact, unblock UNKNOWN or grant another dispatch. */
    public static ObservationComparison compare(ExpectedPostcondition expected, ObservationIdentity after, G2Source source, String observerSchema, List<ExpectedValue> actual) {
        Objects.requireNonNull(expected); Objects.requireNonNull(after); Objects.requireNonNull(source); Objects.requireNonNull(actual);
        if (after.observationVersion() != expected.before().observationVersion() || !expected.observerSchema().equals(observerSchema)) return ObservationComparison.STALE_VERSION;
        if (!expected.source().equals(source)) return ObservationComparison.SOURCE_DRIFT;
        if (!expected.before().machineId().equals(after.machineId()) || !expected.before().game().equals(after.game())
                || !expected.before().frame().episodeRunId().equals(after.frame().episodeRunId())
                || !expected.before().frame().identity().player().equals(after.frame().identity().player())) return ObservationComparison.GAME_OR_EPISODE_DRIFT;
        if (after.frame().identity().nativeRevision().compareTo(expected.before().frame().identity().nativeRevision()) < 0
                || after.frame().revision().compareTo(expected.before().frame().revision()) < 0
                || after.frame().identity().dateRaw().compareTo(expected.before().frame().identity().dateRaw()) < 0) return ObservationComparison.STALE_VERSION;
        Set<FieldKey> fields = new HashSet<>(); for (ExpectedValue value : actual) require(fields.add(value.field()), "duplicate actual observation field refused");
        return expected.values().stream().allMatch(actual::contains) ? ObservationComparison.EXPECTED_FIELDS_MATCH : ObservationComparison.EXPECTED_FIELDS_DIFFER;
    }
    private static boolean empty(Claims value) { return value.armyIds().isEmpty() && value.allyCharacterIds().isEmpty() && value.characterIds().isEmpty() && value.commitmentKeys().isEmpty(); }
    private static void fullFrame(ProposalFrame frame) {
        Objects.requireNonNull(frame); text(frame.snapshotId()); text(frame.episodeRunId());
        new org.xar.ck3.control.contracts.PublicRevision(frame.revision());
        org.xar.ck3.control.contracts.NativeCharacterId.of(frame.identity().player()); new CrossJsDecimalUInt64(frame.identity().nativeRevision().toString());
        new CrossJsDecimalUInt64(frame.identity().dateRaw().toString());
    }
    private static void safeResourceId(BigInteger value) { require(value != null && value.signum() >= 0 && value.compareTo(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER)) <= 0, "new external fact numeric ID must be JavaScript-safe"); }
    private static void text(String value) { require(value != null && !value.isEmpty(), "explicit nonempty text required"); }
    private static void identifier(String value) { require(value != null && value.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"), "bounded action identity required"); }
    private static void digest(String value) { require(value != null && value.matches("[0-9a-f]{64}"), "exact body SHA-256 required"); }
    private static void require(boolean condition, String message) { if (!condition) throw new IllegalArgumentException(message); }
}
