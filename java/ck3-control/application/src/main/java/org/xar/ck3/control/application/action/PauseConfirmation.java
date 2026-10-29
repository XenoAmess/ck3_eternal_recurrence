package org.xar.ck3.control.application.action;

import java.util.HashSet;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;

/** Pure DATA checks. Only the installed native source can replay the actual paused Push and its originals. */
public final class PauseConfirmation {
    public static final String OBSERVER = "xar.ck3.native-timeline-control/v1";
    private PauseConfirmation() { }
    public static List<ProposalLifecycle.ExpectedValue> expectedValues() {
        return List.of(value("paused", true));
    }
    public static List<ProposalLifecycle.ExpectedValue> actualValues() {
        return List.of(value("paused", true), value("control.paused", true), value("native.gameplay_verified", false),
                value("timeline.advance_verified", false), value("timeline.checkpoint_eligible", false));
    }
    private static ProposalLifecycle.ExpectedBoolean value(String field, boolean value) {
        return new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey(field), value);
    }
    public static void validate(ActionCommand command, ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch, ActionState.EffectObservation observation) {
        StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay
                && command.expectation() instanceof CommandExpectation.Gameplay
                && command.operation().value().equals("pause-map") && command.arguments().members().isEmpty()
                && command.expected().observerSchema().equals(OBSERVER) && command.expected().values().equals(expectedValues()),
                "pause completion requires the original exact native pause control contract");
        StrictJson.require(dispatch instanceof NativeActionPort.AckReceived ack && ack.nativeOk()
                && ack.requestId().equals(attempt.requestId()) && ack.outbound().isPresent(),
                "pause completion requires its actual positive original ACK and outbound");
        var ack = (NativeActionPort.AckReceived) dispatch;
        var custody = ack.custody().orElseThrow(() -> new IllegalArgumentException("pause original receive custody is unavailable"));
        custody.verify(ack, attempt.guard());
        StrictJson.require(observation.provenance() instanceof ObservationProvenance.Push
                && observation.provenance().independentOf(attempt.requestId())
                && observation.sessionId().equals(command.sessionId()) && observation.source().equals(command.source())
                && !observation.originalEvidence().equals(attempt.guard().nativeEvidence())
                && !observation.observedAt().isBefore(attempt.submittedAt())
                && !observation.observedAt().isBefore(custody.writeEntered().observedAt()),
                "pause needs an independently received source-bound native Push after the original write");
        observation.provenance().validate(observation.after(), observation.originalEvidence());
        StrictJson.require(!observation.after().frame().snapshotId().equals(command.before().frame().snapshotId())
                && observation.after().frame().identity().nativeRevision().compareTo(command.before().frame().identity().nativeRevision()) > 0,
                "pause needs an independently later actual native frame");
        StrictJson.require(observation.actual().size() == actualValues().size()
                && new HashSet<>(observation.actual()).equals(new HashSet<>(actualValues()))
                && !observation.supportingEvidence().isEmpty(),
                "pause confirms only paused control and explicitly grants no gameplay, advance or SAVE credit");
        StrictJson.require(ProposalLifecycle.compare(command.expected(), observation.after(), observation.source(), observation.observerSchema(), observation.actual())
                == ProposalLifecycle.ObservationComparison.EXPECTED_FIELDS_MATCH,
                "independent actual paused frame changed Game, source, session, player, episode or regressed");
    }
}
