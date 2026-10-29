package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedValue;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** First unsolicited SEM plus an independent actual campaign-root read and a source-bound Start proof. */
public record FrontendGameplayObservation(FrontendIdentity before, G2Source source,
        SessionIdentity gameplaySession, BigInteger connectionGeneration, String observerSchema,
        List<ExpectedValue> actual, SemanticEvidence semanticEvidence, PlanningReadReceipt campaignRootRead,
        List<ExactRef> supportingEvidence) {
    public FrontendGameplayObservation {
        Objects.requireNonNull(before); Objects.requireNonNull(source); Objects.requireNonNull(gameplaySession);
        FrontendFrame.positive(connectionGeneration); StrictJson.text(observerSchema);
        actual = List.copyOf(actual); Objects.requireNonNull(semanticEvidence); Objects.requireNonNull(campaignRootRead);
        supportingEvidence = List.copyOf(supportingEvidence);
        StrictJson.require(!supportingEvidence.isEmpty() && supportingEvidence.size() <= 64,
                "actual Start source and native campaign-root evidence closure required");
        var refs = new HashSet<ExactRef>(semanticEvidence.references());
        for (ExactRef ref : supportingEvidence) StrictJson.require(ref.bytes() > 0 && refs.add(ref), "empty or duplicate gameplay entry evidence");
        StrictJson.require(before.frame() instanceof FrontendFrame.Menu, "gameplay publication must originate at the actual menu");
        ObservationIdentity after = semanticEvidence.frame();
        StrictJson.require(before.machineId().equals(source.machineId()) && before.machineId().equals(after.machineId())
                && before.machineId().equals(gameplaySession.machineId()) && before.game().equals(after.game())
                && before.game().equals(gameplaySession.game()), "gameplay publication crossed the held machine or Game birth");
        StrictJson.require(before.connectionGeneration().equals(connectionGeneration), "gameplay entry connection generation drift");
        StrictJson.require(campaignRootRead.request().origin() instanceof CommandOrigin.Gameplay
                && campaignRootRead.request().before().equals(after)
                && campaignRootRead.before().binding().origin().requireGameplay().equals(after)
                && campaignRootRead.after().binding().origin().requireGameplay().equals(after)
                && campaignRootRead.request().source().equals(source)
                && campaignRootRead.request().sessionId().equals(gameplaySession.sessionId())
                && campaignRootRead.request().operation().value().equals("query-campaign-root-context-v1")
                && campaignRootRead.original().nativeOk()
                && campaignRootRead.after().binding().connectionGeneration().equals(connectionGeneration),
                "independent actual campaign-root read crossed the first SEM/source/session/connection");
        NativeCharacterId.of(after.frame().identity().player());
        var fields = new HashSet<FieldKey>();
        for (ExpectedValue value : actual) StrictJson.require(fields.add(value.field()), "duplicate gameplay entry actual field");
    }
    public ObservationIdentity after() { return semanticEvidence.frame(); }
    public Instant observedAt() { return semanticEvidence.observedAt(); }
    public ExactRef originalEvidence() { return semanticEvidence.originalNativePacket(); }
    public List<ExactRef> references() {
        List<ExactRef> refs = new ArrayList<>(semanticEvidence.references()); refs.addAll(supportingEvidence); return List.copyOf(refs);
    }
    /** Structural binding only; the installed source-bound entry verifier must replay the native root token and originals. */
    public void validate(ActionCommand command, ActionState.Attempt attempt) {
        FrontendGameplayExpectedPostcondition expected = command.expectation().requireGameplayEntry();
        FrontendIdentity origin = command.origin().requireFrontend();
        FrontendIdentity submitted = attempt.guard().origin().requireFrontend();
        StrictJson.require(before.equals(origin) && origin.sameSession(submitted)
                && submitted.connectionGeneration().equals(connectionGeneration), "gameplay publication crossed the submitted frontend origin");
        StrictJson.require(source.equals(command.source()) && source.equals(expected.source())
                && observerSchema.equals(expected.observerSchema()), "gameplay publication source or observer drift");
        StrictJson.require(after().frame().identity().dateRaw().equals(BigInteger.valueOf(expected.selectedDateRaw())), "gameplay publication selected date drift");
        StrictJson.require(!campaignRootRead.requestId().equals(attempt.requestId())
                && !campaignRootRead.before().binding().observedAt().isBefore(attempt.submittedAt()),
                "submission ACK or a prior read cannot become independent campaign-root proof");
        StrictJson.require(!observedAt().isBefore(attempt.submittedAt())
                && !originalEvidence().sha256().equals(attempt.guard().nativeEvidence().sha256()), "ACK or prior frontend packet is not a gameplay publication");
        StrictJson.require(expected.values().stream().allMatch(actual::contains), "gameplay entry actual postcondition did not match");
    }
}
