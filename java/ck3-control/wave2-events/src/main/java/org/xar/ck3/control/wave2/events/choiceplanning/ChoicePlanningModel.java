package org.xar.ck3.control.wave2.events.choiceplanning;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.ChoiceIdentity;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.Decision;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.EvidenceDocument;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.FrameBinding;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.NativeWindow;

/** Typed projections of existing snapshot/history containers. Opaque documents carry evidence only. */
public final class ChoicePlanningModel {
    private ChoicePlanningModel() { }
    public enum PublicStep {
        QUERY("query-mandatory-choice-v1"), SELECT("select-mandatory-choice-v1");
        private final String wire;
        PublicStep(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum Phase {
        FRAME_UNAVAILABLE("unknown_mandatory_choice_frame_unavailable"),
        MECHANISM_UNAVAILABLE("unknown_mandatory_choice_mechanism_unavailable"),
        QUERY("unknown_mandatory_choice_query"), QUERY_FAILED("unknown_mandatory_choice_query_failed"),
        QUERY_MALFORMED("unknown_mandatory_choice_query_malformed"),
        PENDING_VERIFICATION("unknown_mandatory_choice_pending_verification"),
        SELECTOR_UNAVAILABLE("unknown_mandatory_choice_unavailable"),
        FIRST_ENABLED("unknown_mandatory_choice_first_enabled");
        private final String wire;
        Phase(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum HintStatus { PRESENT, OTHER }
    public enum RelationStatus { INDEPENDENT_TOP_MODAL, SAME_TYPED_ROOT, OTHER }
    public enum SelectionStatus { PENDING, OTHER }
    public record NativeHint(HintStatus status, String source, boolean ownerVerified, BigInteger maxAgeMs,
            Optional<String> opaqueRootId, EvidenceDocument original) {
        public NativeHint {
            Objects.requireNonNull(status); Objects.requireNonNull(source); Objects.requireNonNull(maxAgeMs);
            Objects.requireNonNull(opaqueRootId); Objects.requireNonNull(original);
        }
        public boolean eligible() {
            return status == HintStatus.PRESENT && "application_main_pump_observed_modal_receiver".equals(source)
                    && ownerVerified && BigInteger.valueOf(2000).equals(maxAgeMs)
                    && opaqueRootId.filter(value -> !value.isEmpty()).isPresent();
        }
    }
    public record Snapshot(Optional<FrameBinding> frame, Optional<BigInteger> eventInstanceId,
            boolean activeEventPresent, boolean pendingInteractionPresent, Optional<NativeHint> hint) {
        public Snapshot {
            Objects.requireNonNull(frame); Objects.requireNonNull(eventInstanceId); Objects.requireNonNull(hint);
        }
    }
    public record QueryStamp(String snapshotId, BigInteger revision, BigInteger nativeRevision) {
        public QueryStamp { Objects.requireNonNull(snapshotId); Objects.requireNonNull(revision); Objects.requireNonNull(nativeRevision); }
        public boolean matches(FrameBinding frame) {
            return snapshotId.equals(frame.snapshotId()) && revision.equals(frame.revision())
                    && nativeRevision.equals(frame.nativeRevision());
        }
    }
    public record RootRelation(RelationStatus status, boolean ownerVerified, String source, Optional<String> typedDomain,
            Optional<BigInteger> typedWindowInstanceId, Optional<String> topRootId, Optional<String> typedRootId) {
        public RootRelation {
            Objects.requireNonNull(status); Objects.requireNonNull(source); Objects.requireNonNull(typedDomain);
            Objects.requireNonNull(typedWindowInstanceId); Objects.requireNonNull(topRootId); Objects.requireNonNull(typedRootId);
        }
    }
    public record NativeQuery(Optional<QueryStamp> stamp, boolean accepted, boolean queryStep,
            Optional<NativeWindow> window, Optional<RootRelation> relation, EvidenceDocument original) {
        public NativeQuery {
            Objects.requireNonNull(stamp); Objects.requireNonNull(window); Objects.requireNonNull(relation);
            Objects.requireNonNull(original);
        }
    }
    public record SubmissionBinding(BigInteger gamePid, BigInteger actorId, String episodeRunId) {
        public SubmissionBinding { Objects.requireNonNull(gamePid); Objects.requireNonNull(actorId); Objects.requireNonNull(episodeRunId); }
        public boolean matches(FrameBinding frame) {
            return gamePid.equals(BigInteger.valueOf(frame.gamePid())) && actorId.equals(frame.actorCharacterId())
                    && episodeRunId.equals(frame.episodeRunId());
        }
    }
    public record SubmittedSelection(SubmissionBinding binding, SelectionStatus status,
            Optional<ChoiceIdentity> windowId, Optional<ChoiceIdentity> instanceId,
            EvidenceDocument commandResult) {
        public SubmittedSelection {
            Objects.requireNonNull(binding); Objects.requireNonNull(status); Objects.requireNonNull(windowId);
            Objects.requireNonNull(instanceId); Objects.requireNonNull(commandResult);
        }
    }
    public enum EventContextKind { VALID_UNAVAILABLE, RETAIN_TYPED_PRIORITY }
    public record EventRead(QueryStamp stamp, BigInteger eventInstanceId, BigInteger snapshotRevision,
            BigInteger dateRaw, EventContextKind kind, Optional<EvidenceDocument> unavailableContext) {
        public EventRead {
            Objects.requireNonNull(stamp); Objects.requireNonNull(eventInstanceId); Objects.requireNonNull(snapshotRevision);
            Objects.requireNonNull(dateRaw); Objects.requireNonNull(kind); Objects.requireNonNull(unavailableContext);
            if ((kind == EventContextKind.VALID_UNAVAILABLE) != unavailableContext.isPresent()) {
                throw new IllegalArgumentException("unavailable context evidence required exactly for its branch");
            }
        }
        public boolean matches(FrameBinding frame, BigInteger eventId) {
            return stamp.matches(frame) && snapshotRevision.equals(frame.nativeRevision())
                    && dateRaw.equals(frame.dateRaw()) && eventInstanceId.equals(eventId);
        }
    }
    public record HistoryRow(boolean mandatoryQueryCommand, boolean ok, Optional<NativeQuery> query,
            Optional<SubmittedSelection> submittedSelection, Optional<EventRead> eventRead, EvidenceDocument original) {
        public HistoryRow {
            Objects.requireNonNull(query); Objects.requireNonNull(submittedSelection);
            Objects.requireNonNull(eventRead); Objects.requireNonNull(original);
        }
    }
    public record PlanningInput(Optional<Snapshot> snapshot, List<HistoryRow> commands,
            Set<String> actionSteps, Set<String> bridgeCapabilities) {
        public PlanningInput {
            Objects.requireNonNull(snapshot); commands = List.copyOf(commands);
            actionSteps = Set.copyOf(actionSteps); bridgeCapabilities = Set.copyOf(bridgeCapabilities);
        }
    }
    public sealed interface PlanningResult permits NoCandidate, Proposal { }
    public record NoCandidate() implements PlanningResult { }
    public record Proposal(Phase phase, Optional<PublicStep> selectedStep, String reason,
            Optional<NativeHint> hint, Optional<NativeQuery> query, Optional<HistoryRow> failedRead,
            Optional<SubmittedSelection> pending, Optional<Decision> selection,
            Optional<EvidenceDocument> typedEventContext, boolean typedEventFallback) implements PlanningResult {
        public Proposal {
            Objects.requireNonNull(phase); Objects.requireNonNull(selectedStep); Objects.requireNonNull(reason);
            Objects.requireNonNull(hint); Objects.requireNonNull(query); Objects.requireNonNull(failedRead);
            Objects.requireNonNull(pending); Objects.requireNonNull(selection); Objects.requireNonNull(typedEventContext);
            if (selectedStep.orElse(null) == PublicStep.SELECT && (selection.isEmpty() || query.isEmpty())) {
                throw new IllegalArgumentException("selection proposal requires exact query and selector evidence");
            }
        }
        public boolean dispatchAttempted() { return false; }
        public boolean replayAllowed() { return false; }
        public boolean materialEffectsVerified() { return false; }
    }
}
