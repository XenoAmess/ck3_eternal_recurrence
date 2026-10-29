package org.xar.ck3.control.wave2.events.choiceplanning;

import static org.xar.ck3.control.wave2.events.choiceplanning.ChoicePlanningModel.*;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.Decision;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.EvidenceDocument;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.FrameBinding;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.NativeWindow;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.Status;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.TextIdentity;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoicePolicy;

/** Existing top-modal priority orchestration, with the already migrated selector reused in-process. */
public final class MandatoryChoicePlanner implements ChoicePlanningPort {
    public static final String QUERY_CAPABILITY = "game.state.native-mandatory-choice-window-v1";
    private static final String RELATION_SOURCE = "exact_12004_event_controller_gui_root_and_owner_tree";

    @Override public PlanningResult plan(PlanningInput input) {
        Objects.requireNonNull(input);
        if (input.snapshot().isEmpty()) { return new NoCandidate(); }
        Snapshot snapshot = input.snapshot().orElseThrow();
        if (snapshot.pendingInteractionPresent() || snapshot.hint().filter(NativeHint::eligible).isEmpty()) {
            return new NoCandidate();
        }
        NativeHint hint = snapshot.hint().orElseThrow();
        if (snapshot.frame().isEmpty()) {
            return snapshot.activeEventPresent() ? new NoCandidate() : basic(Phase.FRAME_UNAVAILABLE,
                    Optional.empty(), "Native top modal hint lacks a complete current owner frame", Optional.of(hint));
        }
        FrameBinding frame = snapshot.frame().orElseThrow();
        if (!input.actionSteps().contains(PublicStep.QUERY.wire()) || !input.bridgeCapabilities().contains(QUERY_CAPABILITY)) {
            return snapshot.activeEventPresent() ? new NoCandidate() : basic(Phase.MECHANISM_UNAVAILABLE,
                    Optional.empty(), "Native did not advertise both typed query and token action", Optional.of(hint));
        }
        Optional<HistoryRow> observed = latestQuery(input.commands());
        if (observed.isEmpty() || observed.orElseThrow().ok() && observed.orElseThrow().query().isPresent()
                && observed.orElseThrow().query().orElseThrow().stamp().filter(stamp -> stamp.matches(frame)).isEmpty()) {
            return basic(Phase.QUERY, Optional.of(PublicStep.QUERY),
                    "Read the complete current top exclusive modal choice catalogue before selecting", Optional.of(hint));
        }
        HistoryRow observation = observed.orElseThrow();
        if (!observation.ok() || observation.query().isEmpty()) {
            return snapshot.activeEventPresent() ? new NoCandidate() : new Proposal(Phase.QUERY_FAILED, Optional.empty(),
                    "The current typed query failed; do not repeat it or guess a button", Optional.empty(), Optional.empty(),
                    Optional.of(observation), Optional.empty(), Optional.empty(), Optional.empty(), false);
        }
        NativeQuery query = observation.query().orElseThrow();
        if (!query.queryStep() || !query.accepted() || query.window().isEmpty()) {
            return malformed(snapshot, query);
        }
        NativeWindow window = query.window().orElseThrow();
        if (!window.frame().equals(frame) || !window.queryId().hasValue() || !window.windowInstanceId().hasValue()) {
            return malformed(snapshot, query);
        }
        boolean fallback = false;
        Optional<EvidenceDocument> typedContext = Optional.empty();
        if (snapshot.activeEventPresent()) {
            boolean independent = relationMatches(snapshot, hint, window, query.relation(), RelationStatus.INDEPENDENT_TOP_MODAL);
            Optional<EventRead> eventRead = latestEventRead(input.commands(), frame, snapshot.eventInstanceId());
            fallback = relationMatches(snapshot, hint, window, query.relation(), RelationStatus.SAME_TYPED_ROOT)
                    && eventRead.filter(read -> read.kind() == EventContextKind.VALID_UNAVAILABLE).isPresent();
            if (!independent && !fallback) { return new NoCandidate(); }
            if (fallback) { typedContext = eventRead.orElseThrow().unavailableContext(); }
        }
        Optional<SubmittedSelection> previous = latestSelection(input.commands(), frame);
        if (previous.filter(selection -> selection.status() == SelectionStatus.PENDING
                && selection.windowId().equals(optional(window.windowId()))
                && selection.instanceId().equals(optional(window.windowInstanceId()))).isPresent()) {
            return new Proposal(Phase.PENDING_VERIFICATION, Optional.empty(),
                    "The same blocking Native instance remains after a submitted token; do not dispatch another",
                    Optional.empty(), Optional.of(query), Optional.empty(), previous, Optional.empty(), Optional.empty(), false);
        }
        Decision selection = MandatoryChoicePolicy.selectUnknownMandatory(window, Optional.of(frame));
        if (selection.status() != Status.RECOMMENDED) {
            return new Proposal(Phase.SELECTOR_UNAVAILABLE, Optional.empty(), selection.reason(), Optional.empty(),
                    Optional.empty(), Optional.empty(), Optional.empty(), Optional.of(selection), Optional.empty(), false);
        }
        return new Proposal(Phase.FIRST_ENABLED, Optional.of(PublicStep.SELECT), selection.reason(), Optional.empty(),
                Optional.of(query), Optional.empty(), Optional.empty(), Optional.of(selection), typedContext, fallback);
    }

    private static <T> Optional<T> optional(org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.Field<T> field) {
        return field.hasValue() ? Optional.of(field.value()) : Optional.empty();
    }
    private static Proposal basic(Phase phase, Optional<PublicStep> step, String reason, Optional<NativeHint> hint) {
        return new Proposal(phase, step, reason, hint, Optional.empty(), Optional.empty(), Optional.empty(),
                Optional.empty(), Optional.empty(), false);
    }
    private static PlanningResult malformed(Snapshot snapshot, NativeQuery query) {
        return snapshot.activeEventPresent() ? new NoCandidate() : new Proposal(Phase.QUERY_MALFORMED, Optional.empty(),
                "Typed query lacks exact source frame, window instance or query ID", Optional.empty(), Optional.of(query),
                Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty(), false);
    }
    private static Optional<HistoryRow> latestQuery(List<HistoryRow> commands) {
        for (int index = commands.size() - 1; index >= 0; index--) {
            HistoryRow row = commands.get(index); if (row.mandatoryQueryCommand()) { return Optional.of(row); }
        }
        return Optional.empty();
    }
    private static Optional<SubmittedSelection> latestSelection(List<HistoryRow> commands, FrameBinding frame) {
        for (int index = commands.size() - 1; index >= 0; index--) {
            HistoryRow row = commands.get(index);
            if (row.ok() && row.submittedSelection().filter(selection -> selection.binding().matches(frame)).isPresent()) {
                return row.submittedSelection();
            }
        }
        return Optional.empty();
    }
    private static Optional<EventRead> latestEventRead(List<HistoryRow> commands, FrameBinding frame, Optional<BigInteger> eventId) {
        if (eventId.isEmpty()) { return Optional.empty(); }
        for (int index = commands.size() - 1; index >= 0; index--) {
            HistoryRow row = commands.get(index);
            if (row.ok() && row.eventRead().filter(read -> read.matches(frame, eventId.orElseThrow())).isPresent()) {
                return row.eventRead();
            }
        }
        return Optional.empty();
    }
    private static boolean relationMatches(Snapshot snapshot, NativeHint hint, NativeWindow window,
            Optional<RootRelation> optional, RelationStatus status) {
        if (snapshot.eventInstanceId().isEmpty() || snapshot.eventInstanceId().orElseThrow().signum() <= 0
                || optional.isEmpty() || !window.windowInstanceId().hasValue()
                || !(window.windowInstanceId().value() instanceof TextIdentity instance)) { return false; }
        RootRelation relation = optional.orElseThrow();
        if (status != relation.status() || !relation.ownerVerified() || !RELATION_SOURCE.equals(relation.source())
                || !relation.typedDomain().equals(Optional.of("event"))
                || !relation.typedWindowInstanceId().equals(snapshot.eventInstanceId())
                || !relation.topRootId().equals(hint.opaqueRootId())
                || !relation.topRootId().equals(Optional.of(instance.value())) || relation.typedRootId().isEmpty()) {
            return false;
        }
        boolean sameRoot = relation.typedRootId().equals(relation.topRootId());
        return status == RelationStatus.SAME_TYPED_ROOT ? sameRoot
                : !sameRoot && !relation.typedRootId().orElseThrow().isEmpty();
    }
}
