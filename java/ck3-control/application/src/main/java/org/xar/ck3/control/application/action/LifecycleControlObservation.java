package org.xar.ck3.control.application.action;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedValue;

/** Terminal-modal control retains both initial and independent later timeline reads; it grants no day/SAVE credit. */
public record LifecycleControlObservation(LifecycleIdentity after, G2Source source, String sessionId, String observerSchema,
        List<ExpectedValue> actual, PlanningReadReceipt beforeStatus, PlanningReadReceipt independentRead, List<ExactRef> supportingEvidence) {
    public LifecycleControlObservation {
        Objects.requireNonNull(after); Objects.requireNonNull(source); StrictJson.text(sessionId); StrictJson.text(observerSchema);
        actual = List.copyOf(actual); Objects.requireNonNull(beforeStatus); Objects.requireNonNull(independentRead);
        supportingEvidence = List.copyOf(supportingEvidence); StrictJson.require(!supportingEvidence.isEmpty() && supportingEvidence.size() <= 128, "source-qualified modal closure basis required");
    }
    public void validate(ActionCommand command, ActionState.Attempt attempt) {
        StrictJson.require(command.origin() instanceof CommandOrigin.LifecycleTerminal, "terminal modal control requires its actual lifecycle origin");
        var expected = command.lifecycleExpected(); var before = command.lifecycleBefore();
        StrictJson.require(expected.operation() == LifecycleExpectedPostcondition.Operation.CLOSE_DEATH_MODAL
                && source.equals(command.source()) && sessionId.equals(command.sessionId()) && observerSchema.equals(expected.observerSchema())
                && actual.equals(expected.values()), "modal closure changed its exact source/session/operation/expectation");
        StrictJson.require(before.sameSession(after) && after.subject().driverVersion() >= before.subject().driverVersion()
                && before.currentPlayer().equals(after.currentPlayer()) && before.terminalReason() == after.terminalReason()
                && after.frame().nativeRevision().compareTo(before.frame().nativeRevision()) >= 0
                && after.frame().revision().compareTo(before.frame().revision()) >= 0 && after.frame().dateRaw().equals(before.frame().dateRaw()), "modal closure crossed original subject/current player/episode/date or regressed");
        StrictJson.require(beforeStatus.original().nativeOk() && independentRead.original().nativeOk()
                && !beforeStatus.requestId().equals(independentRead.requestId()) && !beforeStatus.requestId().equals(attempt.requestId())
                && !independentRead.requestId().equals(attempt.requestId()), "modal closure needs independent successful timeline queries, never a close ACK");
        for (PlanningReadReceipt read : List.of(beforeStatus, independentRead)) {
            StrictJson.require(read.request().source().equals(source) && read.request().sessionId().equals(sessionId)
                    && read.after().binding().origin() instanceof CommandOrigin.LifecycleTerminal, "modal query changed source/session/origin");
        }
        StrictJson.require(before.sameGuardFrame(beforeStatus.after().binding().origin().requireLifecycleTerminal())
                && after.sameGuardFrame(independentRead.after().binding().origin().requireLifecycleTerminal())
                && !after.observedAt().isBefore(attempt.submittedAt()), "modal query must retain its actual initial and independent later frames");
    }
    public List<ExactRef> references() {
        var refs = new ArrayList<ExactRef>(); refs.add(after.nativeEvidence()); refs.add(after.capabilityEvidence()); refs.addAll(after.supportingEvidence()); refs.addAll(supportingEvidence);
        return List.copyOf(new java.util.LinkedHashSet<>(refs));
    }
}

