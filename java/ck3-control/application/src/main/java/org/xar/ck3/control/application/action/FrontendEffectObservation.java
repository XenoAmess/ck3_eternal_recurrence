package org.xar.ck3.control.application.action;

import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedValue;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;

/** Independent native frontend read plus the exact domain proof closure. Construction grants no authority. */
public record FrontendEffectObservation(FrontendIdentity after, G2Source source, String sessionId,
        String observerSchema, List<ExpectedValue> actual, String readRequestId, Instant observedAt,
        ExactRef originalEvidence, List<ExactRef> supportingEvidence) {
    /** Historical v1 data stays readable; the registered domain verifier decides its actual qualification. */
    public FrontendEffectObservation(FrontendIdentity after, G2Source source, String sessionId,
            String observerSchema, List<ExpectedValue> actual, String readRequestId, Instant observedAt,
            ExactRef originalEvidence) {
        this(after, source, sessionId, observerSchema, actual, readRequestId, observedAt, originalEvidence, List.of());
    }
    public FrontendEffectObservation {
        Objects.requireNonNull(after); Objects.requireNonNull(source); StrictJson.text(sessionId); StrictJson.text(observerSchema);
        actual = List.copyOf(actual); StrictJson.text(readRequestId); Objects.requireNonNull(observedAt); Objects.requireNonNull(originalEvidence);
        supportingEvidence = List.copyOf(supportingEvidence);
        StrictJson.require(supportingEvidence.size() <= 64, "bounded frontend domain evidence required");
        var unique = new HashSet<ExactRef>(); unique.add(originalEvidence);
        for (ExactRef ref : supportingEvidence)
            StrictJson.require(ref.bytes() > 0 && unique.add(ref), "empty or duplicate frontend domain evidence");
        StrictJson.require(originalEvidence.bytes() > 0 && originalEvidence.equals(after.nativeEvidence()), "frontend original packet reference drift");
        StrictJson.require(after.machineId().equals(source.machineId()) && after.frontendSessionId().equals(sessionId),
                "frontend effect source machine or session drift");
        var fields = new HashSet<FieldKey>();
        for (ExpectedValue value : actual) StrictJson.require(fields.add(value.field()), "duplicate frontend observed field");
    }
    /** The framed native packet and JSON domain materials remain distinct physical artifacts. */
    public List<ExactRef> references() {
        List<ExactRef> refs = new ArrayList<>(); refs.add(originalEvidence); refs.addAll(supportingEvidence); return List.copyOf(refs);
    }
    /** Called again under the sole writer lock. Domain replay still must verify every physical original. */
    public void validate(ActionCommand command, ActionState.Attempt attempt) {
        FrontendIdentity before = command.origin().requireFrontend();
        FrontendExpectedPostcondition expected = command.expectation().requireFrontend();
        FrontendIdentity submitted = attempt.guard().origin().requireFrontend();
        StrictJson.require(before.sameSession(submitted) && before.sameSession(after), "frontend effect crossed process birth/session/connection");
        StrictJson.require(sessionId.equals(command.sessionId()) && after.frontendSessionId().equals(sessionId)
                && source.equals(command.source()) && source.equals(expected.source()) && observerSchema.equals(expected.observerSchema()), "frontend effect source/session/observer drift");
        StrictJson.require(!readRequestId.equals(attempt.requestId()) && !observedAt.isBefore(attempt.submittedAt()), "ACK or prior observation is not an independent frontend effect");
        StrictJson.require(after.frame().querySequence().compareTo(submitted.frame().querySequence()) > 0
                && !originalEvidence.sha256().equals(attempt.guard().nativeEvidence().sha256()), "frontend effect requires an independent later original native read");
        StrictJson.require(expected.values().stream().allMatch(actual::contains), "frontend actual postcondition did not match");
    }
}
