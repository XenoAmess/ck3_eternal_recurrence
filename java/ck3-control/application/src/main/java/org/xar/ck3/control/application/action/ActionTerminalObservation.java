package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** An independently observed terminal domain disposition. It grants no release, payment or gameplay credit. */
public record ActionTerminalObservation(String commandBodySha256, String attemptRequestId, Disposition disposition,
        ObservationIdentity before, ObservationIdentity after, G2Source source, String sessionId,
        ObservationProvenance provenance, Instant observedAt, ExactRef originalEvidence, ExactRef originalSubmission,
        PlanningReadReceipt selectedCollection, PlanningReadReceipt afterCollection, List<ExactRef> supportingEvidence) {
    public sealed interface Disposition permits PrisonerTransferred, PrisonerTargetDead { BigInteger targetId(); }
    public record PrisonerTransferred(BigInteger targetId, BigInteger currentJailerId) implements Disposition {
        public PrisonerTransferred { character(targetId); character(currentJailerId); }
    }
    public record PrisonerTargetDead(BigInteger targetId) implements Disposition {
        public PrisonerTargetDead { character(targetId); }
    }
    public ActionTerminalObservation {
        StrictJson.require(commandBodySha256 != null && commandBodySha256.matches("[0-9a-f]{64}"), "exact original command digest required");
        StrictJson.text(attemptRequestId); Objects.requireNonNull(disposition); Objects.requireNonNull(before); Objects.requireNonNull(after);
        Objects.requireNonNull(source); StrictJson.text(sessionId); Objects.requireNonNull(provenance); Objects.requireNonNull(observedAt);
        Objects.requireNonNull(originalEvidence); Objects.requireNonNull(originalSubmission); Objects.requireNonNull(selectedCollection); Objects.requireNonNull(afterCollection);
        supportingEvidence = List.copyOf(supportingEvidence); StrictJson.require(!supportingEvidence.isEmpty() && supportingEvidence.size() <= 128, "actual domain terminal basis required");
        StrictJson.require(originalEvidence.bytes() > 0 && originalSubmission.bytes() > 0, "terminal needs original packet and original dispatch archive");
        provenance.validate(after, originalEvidence);
    }
    public void validate(ActionCommand command, ActionState.Attempt attempt) {
        StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay && commandBodySha256.equals(ActionCodec.bodySha256(command))
                && attemptRequestId.equals(attempt.requestId()) && before.equals(command.before()), "terminal observation changed the original command/attempt/before");
        StrictJson.require(source.equals(command.source()) && sessionId.equals(command.sessionId()), "terminal source/session changed");
        sameLife(before, after);
        StrictJson.require(!after.frame().snapshotId().equals(before.frame().snapshotId())
                && after.frame().identity().nativeRevision().compareTo(before.frame().identity().nativeRevision()) > 0
                && after.frame().identity().dateRaw().compareTo(before.frame().identity().dateRaw()) >= 0 && !observedAt.isBefore(attempt.submittedAt()), "terminal requires an independent actual later frame");
        StrictJson.require(provenance.independentOf(attemptRequestId) && !originalEvidence.equals(attempt.guard().nativeEvidence()), "original ACK/before packet cannot prove terminal disposition");
        for (PlanningReadReceipt read : List.of(selectedCollection, afterCollection)) {
            StrictJson.require(read.original().nativeOk() && read.request().source().equals(source) && read.request().sessionId().equals(sessionId)
                    && !read.requestId().equals(attemptRequestId), "terminal collection read failed, changed source/session or reused mutation identity");
            sameLife(before, read.after().binding().observed());
        }
        StrictJson.require(afterCollection.after().binding().observed().equals(after)
                && !selectedCollection.requestId().equals(afterCollection.requestId()), "terminal after collection must independently bind its actual later frame");
    }
    public List<ExactRef> references() {
        var refs = new ArrayList<ExactRef>(); refs.add(originalEvidence); refs.add(originalSubmission); refs.addAll(supportingEvidence);
        return List.copyOf(new java.util.LinkedHashSet<>(refs));
    }
    private static void sameLife(ObservationIdentity expected, ObservationIdentity actual) {
        StrictJson.require(expected.machineId().equals(actual.machineId()) && expected.game().equals(actual.game())
                && expected.frame().episodeRunId().equals(actual.frame().episodeRunId())
                && expected.frame().identity().player().equals(actual.frame().identity().player()), "terminal crossed the original Game/player/episode");
    }
    private static void character(BigInteger value) { StrictJson.require(value != null && value.signum() > 0 && value.compareTo(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER)) <= 0, "positive exact character ID required"); }
}

